"""Sales Intelligence orchestration — analytics services only (no SQL)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from app.analytics.query import AnalyticsQuery, FilterClause, FilterOperator
from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.schemas.common import PaginationMeta, ResponseMeta
from app.schemas.sales import (
    CategoryPerformanceResponse,
    CategoryPerformanceRow,
    ProductPerformanceResponse,
    ProductPerformanceRow,
    RegionalSalesResponse,
    RegionalSalesRow,
    SalesMetric,
    SalesOverviewResponse,
    SalesTrendPoint,
    SalesTrendsResponse,
    TopCustomerRow,
    TopCustomersResponse,
)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _format_currency(value: float | None) -> str | None:
    if value is None:
        return None
    return f"${value:,.0f}"


def _format_percent(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value * 100:.1f}%"


def _format_number(value: float | None) -> str | None:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    return f"{value:,.1f}"


def _trend(delta: float | None) -> Literal["up", "down", "flat"] | None:
    if delta is None:
        return None
    if delta > 0.001:
        return "up"
    if delta < -0.001:
        return "down"
    return "flat"


def _iso_week_key(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _month_key(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


class SalesService:
    """
    Vertical-slice orchestrator for Sales Intelligence.
    Depends only on Sales + Customer analytics services.
    """

    def __init__(
        self,
        sales: SalesAnalyticsService,
        customers: CustomerAnalyticsService,
    ) -> None:
        self.sales = sales
        self.customers = customers

    def get_overview(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        category: list[str] | None = None,
        search: str | None = None,
    ) -> SalesOverviewResponse:
        rows = self._safe_summary_rows(date_from=date_from, date_to=date_to, region=region, search=search)
        dated = self._dated_rows(rows)
        period_end = date_to or (dated[-1][0] if dated else None)
        period_start = date_from
        if period_start is None and period_end is not None:
            period_start = period_end - timedelta(days=29)

        current_rows = [
            row
            for d, row in dated
            if (period_start is None or d >= period_start) and (period_end is None or d <= period_end)
        ]
        # Optional category filter requires line+map join — applied after if provided
        if category:
            current_rows = self._filter_summary_by_category(current_rows, category)

        window_days = (
            (period_end - period_start).days + 1
            if period_start and period_end
            else 30
        )
        prior_end = period_start - timedelta(days=1) if period_start else None
        prior_start = prior_end - timedelta(days=window_days - 1) if prior_end else None
        prior_rows = [
            row
            for d, row in dated
            if prior_start and prior_end and prior_start <= d <= prior_end
        ]
        if category:
            prior_rows = self._filter_summary_by_category(prior_rows, category)

        revenue = sum(filter(None, (_as_float(r.get("net_sales")) for r in current_rows)))
        profit = sum(filter(None, (_as_float(r.get("gross_profit")) for r in current_rows)))
        orders = sum(filter(None, (_as_float(r.get("order_count")) for r in current_rows)))
        prior_revenue = sum(filter(None, (_as_float(r.get("net_sales")) for r in prior_rows)))

        available = bool(current_rows)
        aov = (revenue / orders) if available and orders else None
        margin = (profit / revenue) if available and revenue else None
        growth = ((revenue - prior_revenue) / prior_revenue) if prior_revenue else None

        metrics = [
            self._metric(
                "revenue",
                "Revenue",
                revenue if available else None,
                _format_currency(revenue if available else None),
                "currency",
                "USD",
                available,
                delta=growth,
                delta_label="vs prior period" if growth is not None else None,
            ),
            self._metric(
                "orders",
                "Orders",
                orders if available else None,
                _format_number(orders if available else None),
                "number",
                None,
                available,
            ),
            self._metric(
                "aov",
                "Average Order Value",
                aov,
                _format_currency(aov),
                "currency",
                "USD",
                aov is not None,
            ),
            self._metric(
                "gross_profit",
                "Gross Profit",
                profit if available else None,
                _format_currency(profit if available else None),
                "currency",
                "USD",
                available,
            ),
            self._metric(
                "profit_margin",
                "Profit Margin",
                margin,
                _format_percent(margin),
                "percent",
                None,
                margin is not None,
            ),
            self._metric(
                "growth",
                "Growth",
                growth,
                _format_percent(growth),
                "percent",
                None,
                growth is not None,
                trend=_trend(growth),
            ),
        ]
        return SalesOverviewResponse(
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            meta=ResponseMeta(),
        )

    def get_trends(
        self,
        *,
        grain: Literal["daily", "weekly", "monthly"] = "daily",
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        search: str | None = None,
    ) -> SalesTrendsResponse:
        rows = self._safe_summary_rows(date_from=date_from, date_to=date_to, region=region, search=search)
        dated = self._dated_rows(rows)
        if date_from or date_to:
            dated = [
                (d, row)
                for d, row in dated
                if (date_from is None or d >= date_from) and (date_to is None or d <= date_to)
            ]
        if not dated:
            return SalesTrendsResponse(points=[], grain=grain, available=False, meta=ResponseMeta())

        buckets: dict[str, dict[str, float]] = {}
        for d, row in dated:
            if grain == "weekly":
                key = _iso_week_key(d)
            elif grain == "monthly":
                key = _month_key(d)
            else:
                key = d.isoformat()
            bucket = buckets.setdefault(key, {"revenue": 0.0, "orders": 0.0, "profit": 0.0})
            bucket["revenue"] += _as_float(row.get("net_sales")) or 0.0
            bucket["orders"] += _as_float(row.get("order_count")) or 0.0
            bucket["profit"] += _as_float(row.get("gross_profit")) or 0.0

        points = [
            SalesTrendPoint(
                period=period,
                revenue=values["revenue"],
                orders=values["orders"],
                profit=values["profit"],
            )
            for period, values in sorted(buckets.items())
        ]
        return SalesTrendsResponse(points=points, grain=grain, available=True, meta=ResponseMeta())

    def get_category_performance(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        category: list[str] | None = None,
        search: str | None = None,
    ) -> CategoryPerformanceResponse:
        try:
            current, prior = self._line_period_splits(date_from=date_from, date_to=date_to)
            category_map = {
                str(r.get("product_id")): r for r in self.sales.get_product_category_rows(AnalyticsQuery(page_size=500))
            }
        except Exception:  # noqa: BLE001 — views may be unpublished
            return CategoryPerformanceResponse(rows=[], available=False, meta=ResponseMeta())

        if not current:
            return CategoryPerformanceResponse(rows=[], available=False, meta=ResponseMeta())

        # Region filter is store-level on daily summary; line fact has store_id only — skip if no match helper
        _ = region  # reserved for future store→region enrichment
        current_agg = self._aggregate_by_category(current, category_map, category=category, search=search)
        prior_agg = self._aggregate_by_category(prior, category_map, category=category, search=search)

        rows: list[CategoryPerformanceRow] = []
        for name, values in sorted(current_agg.items(), key=lambda item: item[1]["revenue"], reverse=True):
            prior_rev = prior_agg.get(name, {}).get("revenue")
            growth = ((values["revenue"] - prior_rev) / prior_rev) if prior_rev else None
            margin = (values["profit"] / values["revenue"]) if values["revenue"] else None
            rows.append(
                CategoryPerformanceRow(
                    category=name,
                    revenue=values["revenue"],
                    orders=values["orders"],
                    growth=growth,
                    margin=margin,
                )
            )
        return CategoryPerformanceResponse(rows=rows, available=True, meta=ResponseMeta())

    def get_product_performance(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "revenue",
        sort_dir: Literal["asc", "desc"] = "desc",
        search: str | None = None,
        columns: list[str] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        category: list[str] | None = None,
    ) -> ProductPerformanceResponse:
        try:
            current, prior = self._line_period_splits(date_from=date_from, date_to=date_to)
            category_map = {
                str(r.get("product_id")): r for r in self.sales.get_product_category_rows(AnalyticsQuery(page_size=500))
            }
        except Exception:  # noqa: BLE001
            return ProductPerformanceResponse(
                rows=[],
                pagination=PaginationMeta(page=page, page_size=page_size, total_items=0, total_pages=0),
                available=False,
                meta=ResponseMeta(),
            )

        if not current:
            return ProductPerformanceResponse(
                rows=[],
                pagination=PaginationMeta(page=page, page_size=page_size, total_items=0, total_pages=0),
                available=False,
                meta=ResponseMeta(),
            )

        current_agg = self._aggregate_by_product(current, category_map, category=category, search=search)
        prior_agg = self._aggregate_by_product(prior, category_map, category=category, search=search)

        products: list[ProductPerformanceRow] = []
        for product_id, values in current_agg.items():
            prior_rev = prior_agg.get(product_id, {}).get("revenue")
            growth = ((values["revenue"] - prior_rev) / prior_rev) if prior_rev else None
            margin = (values["profit"] / values["revenue"]) if values["revenue"] else None
            meta = category_map.get(product_id, {})
            products.append(
                ProductPerformanceRow(
                    product_id=product_id,
                    product=str(meta.get("product_name") or product_id),
                    sku=str(meta["sku"]) if meta.get("sku") is not None else None,
                    category=str(meta["category_name"]) if meta.get("category_name") is not None else None,
                    revenue=values["revenue"],
                    orders=values["orders"],
                    units=values["units"],
                    margin=margin,
                    growth=growth,
                )
            )

        reverse = sort_dir == "desc"
        sort_key_map = {
            "revenue": lambda r: r.revenue or 0.0,
            "orders": lambda r: r.orders or 0.0,
            "units": lambda r: r.units or 0.0,
            "margin": lambda r: r.margin or 0.0,
            "growth": lambda r: r.growth or 0.0,
            "product": lambda r: r.product.lower(),
        }
        key_fn = sort_key_map.get(sort_by, sort_key_map["revenue"])
        products.sort(key=key_fn, reverse=reverse)

        total = len(products)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        start = (page - 1) * page_size
        page_rows = products[start : start + page_size]

        if columns:
            allowed = set(columns)
            projected: list[ProductPerformanceRow] = []
            for row in page_rows:
                data = row.model_dump()
                projected.append(ProductPerformanceRow(**{k: data.get(k) for k in data if k in allowed or k == "product"}))
            page_rows = projected

        return ProductPerformanceResponse(
            rows=page_rows,
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
            ),
            available=True,
            meta=ResponseMeta(),
        )

    def get_regional_performance(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        search: str | None = None,
    ) -> RegionalSalesResponse:
        rows = self._safe_summary_rows(date_from=date_from, date_to=date_to, region=region, search=search)
        dated = self._dated_rows(rows)
        if not dated:
            return RegionalSalesResponse(rows=[], available=False, meta=ResponseMeta())

        period_end = date_to or dated[-1][0]
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        current: dict[str, dict[str, float]] = {}
        prior: dict[str, float] = {}
        for d, row in dated:
            name = str(row.get("region_name") or row.get("region_code") or "Unknown")
            revenue = _as_float(row.get("net_sales")) or 0.0
            orders = _as_float(row.get("order_count")) or 0.0
            if period_start <= d <= period_end:
                bucket = current.setdefault(name, {"revenue": 0.0, "orders": 0.0})
                bucket["revenue"] += revenue
                bucket["orders"] += orders
            elif prior_start <= d <= prior_end:
                prior[name] = prior.get(name, 0.0) + revenue

        result = []
        for name, values in sorted(current.items(), key=lambda item: item[1]["revenue"], reverse=True):
            prior_rev = prior.get(name)
            growth = ((values["revenue"] - prior_rev) / prior_rev) if prior_rev else None
            result.append(
                RegionalSalesRow(
                    region=name,
                    revenue=values["revenue"],
                    orders=values["orders"],
                    growth=growth,
                )
            )
        return RegionalSalesResponse(rows=result, available=True, meta=ResponseMeta())

    def get_top_customers(
        self,
        *,
        limit: int = 10,
        search: str | None = None,
    ) -> TopCustomersResponse:
        try:
            page = self.customers.get_customer_360(
                AnalyticsQuery(
                    page=1,
                    page_size=max(limit, 50),
                    sort_by="lifetime_net_sales",
                    sort_dir="desc",
                    search=search,
                    columns=[
                        "customer_id",
                        "customer_number",
                        "order_count",
                        "lifetime_net_sales",
                        "avg_order_value",
                    ],
                )
            )
        except Exception:  # noqa: BLE001
            return TopCustomersResponse(rows=[], available=False, meta=ResponseMeta())

        rows: list[TopCustomerRow] = []
        for row in page.table.rows[:limit]:
            ltv = _as_float(row.get("lifetime_net_sales"))
            rows.append(
                TopCustomerRow(
                    customer=str(row.get("customer_number") or row.get("customer_id") or "Unknown"),
                    customer_id=str(row["customer_id"]) if row.get("customer_id") is not None else None,
                    revenue=ltv,
                    orders=_as_float(row.get("order_count")),
                    lifetime_value=ltv,
                    lifetime_value_available=ltv is not None,
                )
            )
        return TopCustomersResponse(rows=rows, available=bool(rows), meta=ResponseMeta())

    def _metric(
        self,
        id: str,
        label: str,
        value: float | None,
        formatted: str | None,
        fmt: Literal["currency", "percent", "number"],
        unit: str | None,
        available: bool,
        *,
        delta: float | None = None,
        delta_label: str | None = None,
        trend: Literal["up", "down", "flat"] | None = None,
    ) -> SalesMetric:
        return SalesMetric(
            id=id,
            label=label,
            value=value,
            formatted_value=formatted,
            unit=unit,
            delta=delta,
            delta_label=delta_label,
            trend=trend if trend is not None else _trend(delta),
            format=fmt,
            available=available,
            source="sales_summary",
        )

    def _safe_summary_rows(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        region: list[str] | None,
        search: str | None,
    ) -> list[dict]:
        filters: list[FilterClause] = []
        if region:
            filters.append(FilterClause(column="region_name", op=FilterOperator.IN, value=region))
        query = AnalyticsQuery(
            sort_by="order_date",
            sort_dir="asc",
            page_size=500,
            date_from=date_from,
            date_to=date_to,
            date_column="order_date",
            search=search,
            filters=filters,
        )
        try:
            return self.sales.get_sales_summary_rows(query)
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _dated_rows(rows: list[dict]) -> list[tuple[date, dict]]:
        dated: list[tuple[date, dict]] = []
        for row in rows:
            d = _coerce_date(row.get("order_date"))
            if d is not None:
                dated.append((d, row))
        dated.sort(key=lambda item: item[0])
        return dated

    def _line_period_splits(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> tuple[list[dict], list[dict]]:
        query = AnalyticsQuery(
            sort_by="order_date",
            sort_dir="asc",
            page_size=500,
            date_column="order_date",
        )
        lines = self.sales.get_sales_line_rows(query)
        dated = self._dated_rows(lines)
        if not dated:
            return [], []
        period_end = date_to or dated[-1][0]
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)
        current = [row for d, row in dated if period_start <= d <= period_end]
        prior = [row for d, row in dated if prior_start <= d <= prior_end]
        return current, prior

    def _filter_summary_by_category(self, rows: list[dict], categories: list[str]) -> list[dict]:
        """
        Category is product L1; daily summary has channel only.
        When category filters are active, fall back to channel_name match as commercial proxy
        only if names intersect; otherwise leave rows unchanged (category applied on line endpoints).
        """
        wanted = {c.lower() for c in categories}
        filtered = [
            row
            for row in rows
            if str(row.get("channel_name") or "").lower() in wanted
            or str(row.get("channel_code") or "").lower() in wanted
        ]
        return filtered if filtered else rows

    @staticmethod
    def _aggregate_by_category(
        lines: list[dict],
        category_map: dict[str, dict],
        *,
        category: list[str] | None,
        search: str | None,
    ) -> dict[str, dict[str, float]]:
        wanted = {c.lower() for c in category} if category else None
        search_l = search.lower() if search else None
        order_ids: dict[str, set[Any]] = {}
        agg: dict[str, dict[str, float]] = {}
        for row in lines:
            pid = str(row.get("product_id"))
            meta = category_map.get(pid, {})
            name = str(meta.get("category_name") or "Uncategorized")
            if wanted and name.lower() not in wanted:
                continue
            if search_l and search_l not in name.lower():
                continue
            bucket = agg.setdefault(name, {"revenue": 0.0, "orders": 0.0, "profit": 0.0})
            bucket["revenue"] += _as_float(row.get("line_net_amount")) or 0.0
            bucket["profit"] += _as_float(row.get("line_gross_profit")) or 0.0
            order_ids.setdefault(name, set()).add(row.get("order_id"))
        for name, ids in order_ids.items():
            agg[name]["orders"] = float(len(ids))
        return agg

    @staticmethod
    def _aggregate_by_product(
        lines: list[dict],
        category_map: dict[str, dict],
        *,
        category: list[str] | None,
        search: str | None,
    ) -> dict[str, dict[str, float]]:
        wanted = {c.lower() for c in category} if category else None
        search_l = search.lower() if search else None
        order_ids: dict[str, set[Any]] = {}
        agg: dict[str, dict[str, float]] = {}
        for row in lines:
            pid = str(row.get("product_id"))
            meta = category_map.get(pid, {})
            cat_name = str(meta.get("category_name") or "")
            product_name = str(meta.get("product_name") or pid)
            sku = str(meta.get("sku") or "")
            if wanted and cat_name.lower() not in wanted:
                continue
            if search_l and search_l not in product_name.lower() and search_l not in sku.lower():
                continue
            bucket = agg.setdefault(pid, {"revenue": 0.0, "orders": 0.0, "profit": 0.0, "units": 0.0})
            bucket["revenue"] += _as_float(row.get("line_net_amount")) or 0.0
            bucket["profit"] += _as_float(row.get("line_gross_profit")) or 0.0
            bucket["units"] += _as_float(row.get("quantity")) or 0.0
            order_ids.setdefault(pid, set()).add(row.get("order_id"))
        for pid, ids in order_ids.items():
            agg[pid]["orders"] = float(len(ids))
        return agg

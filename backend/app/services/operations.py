"""Operations Intelligence orchestration — analytics services only (no SQL)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from app.analytics.query import AnalyticsQuery, FilterClause, FilterOperator
from app.analytics.services.operations import OperationsAnalyticsService
from app.analytics.services.sales import SalesAnalyticsService
from app.schemas.common import PaginationMeta, ResponseMeta
from app.schemas.operations import (
    InventoryResponse,
    InventoryRow,
    OperationalRiskRow,
    OperationalRisksResponse,
    OperationsMetric,
    OperationsOverviewResponse,
    ReturnsResponse,
    ReturnsRow,
    SupplierPerformanceResponse,
    SupplierPerformanceRow,
    WarehousePerformanceResponse,
    WarehousePerformanceRow,
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


def _supplier_risk(on_time: float | None, quality: float | None) -> str:
    score = None
    parts = [v for v in (on_time, quality) if v is not None]
    if parts:
        score = sum(parts) / len(parts)
    if score is None:
        return "Unknown"
    if score < 0.5:
        return "High"
    if score < 0.75:
        return "Medium"
    return "Low"


class OperationsService:
    """
    Vertical-slice orchestrator for Operations Intelligence.
    Depends on Operations + Sales analytics services only.
    """

    def __init__(
        self,
        operations: OperationsAnalyticsService,
        sales: SalesAnalyticsService,
    ) -> None:
        self.operations = operations
        self.sales = sales

    def get_overview(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        category: list[str] | None = None,
        supplier: list[str] | None = None,
        search: str | None = None,
    ) -> OperationsOverviewResponse:
        inventory = self._safe_inventory(category=category, search=search, region=region)
        suppliers = self._safe_suppliers(supplier=supplier, search=search)
        returns = self._safe_returns(date_from=date_from, date_to=date_to)
        shipments = self._safe_shipments(date_from=date_from, date_to=date_to)
        sales_units = self._sales_units(date_from=date_from, date_to=date_to, region=region)

        period_end = date_to
        period_start = date_from

        inv_value = sum(filter(None, (_as_float(r.get("inventory_value_cost")) for r in inventory)))
        inv_available = bool(inventory)
        healthy = sum(1 for r in inventory if str(r.get("stock_status") or "").lower() == "healthy")
        health_pct = (healthy / len(inventory)) if inventory else None

        on_hand = sum(filter(None, (_as_float(r.get("quantity_on_hand")) for r in inventory)))
        turnover = (sales_units / on_hand) if sales_units is not None and on_hand else None

        on_times = [_as_float(r.get("on_time_rate")) for r in suppliers]
        on_times = [v for v in on_times if v is not None]
        supplier_perf = (sum(on_times) / len(on_times)) if on_times else None

        returned_qty = sum(filter(None, (_as_float(r.get("quantity_returned")) for r in returns)))
        return_rate = (returned_qty / sales_units) if sales_units and returned_qty is not None else None
        if sales_units is None and returns:
            return_rate = None  # cannot compute without sales denominator

        fulfilled = 0
        total_ship = 0
        for row in shipments:
            total_ship += 1
            flag = str(row.get("delay_flag") or "").lower()
            status = str(row.get("shipment_status") or "").lower()
            if flag == "on track" or status in {"delivered", "completed", "shipped"}:
                fulfilled += 1
        fulfillment = (fulfilled / total_ship) if total_ship else None

        metrics = [
            self._metric(
                "inventory_value",
                "Inventory Value",
                inv_value if inv_available else None,
                _format_currency(inv_value if inv_available else None),
                "currency",
                inv_available,
                unit="USD",
                source="inventory_summary",
            ),
            self._metric(
                "inventory_health",
                "Inventory Health",
                health_pct,
                _format_percent(health_pct),
                "percent",
                health_pct is not None,
                source="inventory_summary",
            ),
            self._metric(
                "stock_turnover",
                "Stock Turnover",
                turnover,
                _format_number(turnover),
                "number",
                turnover is not None,
                source="inventory_summary+sales_summary",
            ),
            self._metric(
                "supplier_performance",
                "Supplier Performance",
                supplier_perf,
                _format_percent(supplier_perf),
                "percent",
                supplier_perf is not None,
                source="supplier_performance",
            ),
            self._metric(
                "return_rate",
                "Return Rate",
                return_rate,
                _format_percent(return_rate),
                "percent",
                return_rate is not None,
                source="fact_return_line+sales_summary",
            ),
            self._metric(
                "fulfillment_rate",
                "Fulfillment Rate",
                fulfillment,
                _format_percent(fulfillment),
                "percent",
                fulfillment is not None,
                source="shipment_performance",
            ),
        ]
        return OperationsOverviewResponse(
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            meta=ResponseMeta(),
        )

    def get_inventory(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "inventory_value",
        sort_dir: Literal["asc", "desc"] = "desc",
        search: str | None = None,
        columns: list[str] | None = None,
        category: list[str] | None = None,
        region: list[str] | None = None,
    ) -> InventoryResponse:
        rows = self._safe_inventory(category=category, search=search, region=region)
        sales_units = self._sales_units(date_from=None, date_to=None, region=region)
        total_on_hand = sum(filter(None, (_as_float(r.get("quantity_on_hand")) for r in rows))) or 0.0

        details: list[InventoryRow] = []
        for row in rows:
            on_hand = _as_float(row.get("quantity_on_hand"))
            # Allocate overall turnover proxy by share of on-hand when sales units exist
            turnover = None
            if sales_units is not None and total_on_hand and on_hand is not None:
                turnover = sales_units * (on_hand / total_on_hand) / on_hand if on_hand else None
                # simplifies to sales_units / total_on_hand for every row — use that global rate
                turnover = sales_units / total_on_hand
            details.append(
                InventoryRow(
                    product=str(row.get("product_name") or row.get("sku") or row.get("product_id") or "Unknown"),
                    product_id=str(row["product_id"]) if row.get("product_id") is not None else None,
                    sku=str(row["sku"]) if row.get("sku") is not None else None,
                    category=str(row["category_name"]) if row.get("category_name") is not None else None,
                    stock=on_hand,
                    safety_stock=_as_float(row.get("reorder_point")),
                    turnover=turnover,
                    inventory_value=_as_float(row.get("inventory_value_cost")),
                    stock_status=str(row["stock_status"]) if row.get("stock_status") is not None else None,
                )
            )

        if not details:
            return InventoryResponse(
                rows=[],
                pagination=PaginationMeta(page=page, page_size=page_size, total_items=0, total_pages=0),
                available=False,
                meta=ResponseMeta(),
            )

        sort_map = {
            "inventory_value": lambda r: r.inventory_value or 0.0,
            "stock": lambda r: r.stock or 0.0,
            "safety_stock": lambda r: r.safety_stock or 0.0,
            "turnover": lambda r: r.turnover or 0.0,
            "product": lambda r: r.product.lower(),
            "category": lambda r: (r.category or "").lower(),
        }
        key_fn = sort_map.get(sort_by, sort_map["inventory_value"])
        details.sort(key=key_fn, reverse=(sort_dir == "desc"))

        total = len(details)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        start = (page - 1) * page_size
        page_rows = details[start : start + page_size]

        if columns:
            keep = set(columns) | {"product"}
            page_rows = [
                InventoryRow(**{k: (v if k in keep else None) for k, v in row.model_dump().items()})
                for row in page_rows
            ]

        return InventoryResponse(
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

    def get_supplier_performance(
        self,
        *,
        supplier: list[str] | None = None,
        search: str | None = None,
    ) -> SupplierPerformanceResponse:
        rows = self._safe_suppliers(supplier=supplier, search=search)
        if not rows:
            return SupplierPerformanceResponse(rows=[], available=False, meta=ResponseMeta())

        result = []
        for row in rows:
            on_time = _as_float(row.get("on_time_rate"))
            quality = _as_float(row.get("reliability_score"))
            # reliability_score may be 0-100
            if quality is not None and quality > 1:
                quality = quality / 100.0
            result.append(
                SupplierPerformanceRow(
                    supplier=str(row.get("supplier_name") or row.get("supplier_code") or "Unknown"),
                    supplier_id=str(row["supplier_id"]) if row.get("supplier_id") is not None else None,
                    on_time_pct=on_time,
                    quality_score=quality,
                    lead_time=_as_float(row.get("avg_actual_lead_time_days") or row.get("contracted_lead_time_days")),
                    purchase_volume=_as_float(row.get("units_ordered")),
                    risk_level=_supplier_risk(on_time, quality),
                )
            )
        result.sort(key=lambda r: r.on_time_pct or 0.0, reverse=True)
        return SupplierPerformanceResponse(rows=result, available=True, meta=ResponseMeta())

    def get_returns(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        category: list[str] | None = None,
        search: str | None = None,
    ) -> ReturnsResponse:
        returns = self._safe_returns(date_from=date_from, date_to=date_to)
        if not returns:
            return ReturnsResponse(rows=[], available=False, meta=ResponseMeta())

        category_map = self._product_category_map()
        period_end = date_to or max((_coerce_date(r.get("return_date")) for r in returns), default=date.today())
        if period_end is None:
            period_end = date.today()
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        wanted = {c.lower() for c in category} if category else None
        search_l = search.lower() if search else None

        current: dict[str, dict[str, float]] = {}
        prior: dict[str, float] = {}
        for row in returns:
            pid = str(row.get("product_id"))
            meta = category_map.get(pid, {})
            name = str(meta.get("category_name") or "Uncategorized")
            if wanted and name.lower() not in wanted:
                continue
            if search_l and search_l not in name.lower():
                continue
            d = _coerce_date(row.get("return_date"))
            qty = _as_float(row.get("quantity_returned")) or 0.0
            cost = _as_float(row.get("refund_line_amount")) or 0.0
            if d and period_start <= d <= period_end:
                bucket = current.setdefault(name, {"count": 0.0, "cost": 0.0})
                bucket["count"] += qty
                bucket["cost"] += cost
            elif d and prior_start <= d <= prior_end:
                prior[name] = prior.get(name, 0.0) + qty

        total_count = sum(v["count"] for v in current.values()) or 0.0
        result: list[ReturnsRow] = []
        for name, values in sorted(current.items(), key=lambda item: item[1]["count"], reverse=True):
            prior_count = prior.get(name)
            growth = ((values["count"] - prior_count) / prior_count) if prior_count else None
            result.append(
                ReturnsRow(
                    category=name,
                    return_count=values["count"],
                    return_pct=(values["count"] / total_count) if total_count else None,
                    return_cost=values["cost"],
                    trend=_trend(growth),
                )
            )
        return ReturnsResponse(rows=result, available=True, meta=ResponseMeta())

    def get_warehouse_performance(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        search: str | None = None,
    ) -> WarehousePerformanceResponse:
        inventory = self._safe_inventory(category=None, search=search, region=region)
        shipments = self._safe_shipments(date_from=date_from, date_to=date_to)

        inv_by_wh: dict[str, dict[str, float]] = {}
        for row in inventory:
            name = str(row.get("dc_name") or row.get("store_name") or "Unknown")
            if region:
                # region filter already applied via store→region on inventory
                pass
            if search and search.lower() not in name.lower():
                continue
            bucket = inv_by_wh.setdefault(name, {"inventory": 0.0, "stockouts": 0.0})
            bucket["inventory"] += _as_float(row.get("inventory_value_cost")) or 0.0
            if str(row.get("stock_status") or "").lower() == "stockout":
                bucket["stockouts"] += 1

        ship_by_wh: dict[str, dict[str, float]] = {}
        for row in shipments:
            name = str(row.get("dc_name") or row.get("dc_code") or "Unknown")
            if search and search.lower() not in name.lower():
                continue
            bucket = ship_by_wh.setdefault(
                name, {"total": 0.0, "fulfilled": 0.0, "lead_sum": 0.0, "lead_n": 0.0}
            )
            bucket["total"] += 1
            flag = str(row.get("delay_flag") or "").lower()
            if flag == "on track":
                bucket["fulfilled"] += 1
            lead = _as_float(row.get("fulfillment_lead_time_days"))
            if lead is not None:
                bucket["lead_sum"] += lead
                bucket["lead_n"] += 1

        names = set(inv_by_wh) | set(ship_by_wh)
        if not names:
            return WarehousePerformanceResponse(rows=[], available=False, meta=ResponseMeta())

        result = []
        for name in sorted(names):
            inv = inv_by_wh.get(name, {})
            ship = ship_by_wh.get(name, {})
            fulfillment = (ship["fulfilled"] / ship["total"]) if ship.get("total") else None
            avg_lead = (ship["lead_sum"] / ship["lead_n"]) if ship.get("lead_n") else None
            result.append(
                WarehousePerformanceRow(
                    warehouse=name,
                    inventory=inv.get("inventory"),
                    fulfillment=fulfillment,
                    stockouts=inv.get("stockouts"),
                    average_processing_time=avg_lead,
                )
            )
        return WarehousePerformanceResponse(rows=result, available=True, meta=ResponseMeta())

    def get_operational_risks(
        self,
        *,
        category: list[str] | None = None,
        supplier: list[str] | None = None,
        search: str | None = None,
    ) -> OperationalRisksResponse:
        inventory = self._safe_inventory(category=category, search=search, region=None)
        suppliers = self._safe_suppliers(supplier=supplier, search=search)
        returns = self.get_returns(category=category, search=search)

        risks: list[OperationalRiskRow] = []

        stockouts = [r for r in inventory if str(r.get("stock_status") or "").lower() == "stockout"]
        if stockouts:
            risks.append(
                OperationalRiskRow(
                    risk=f"{len(stockouts)} stockout positions",
                    severity="critical" if len(stockouts) >= 10 else "high",
                    owner="Inventory Operations",
                    recommendation="Expedite replenishment for stocked-out SKUs and review safety stock.",
                )
            )
        below = [r for r in inventory if str(r.get("stock_status") or "").lower() == "below reorder"]
        if below:
            risks.append(
                OperationalRiskRow(
                    risk=f"{len(below)} SKUs below reorder point",
                    severity="medium",
                    owner="Inventory Planning",
                    recommendation="Trigger purchase orders for below-reorder items.",
                )
            )

        for row in suppliers:
            on_time = _as_float(row.get("on_time_rate"))
            if on_time is not None and on_time < 0.7:
                name = str(row.get("supplier_name") or "Supplier")
                risks.append(
                    OperationalRiskRow(
                        risk=f"Low on-time delivery: {name}",
                        severity="high" if on_time < 0.5 else "medium",
                        owner="Procurement",
                        recommendation="Engage supplier on lead-time recovery or dual-source critical SKUs.",
                    )
                )

        for row in returns.rows[:3]:
            if row.trend == "up":
                risks.append(
                    OperationalRiskRow(
                        risk=f"Rising returns in {row.category}",
                        severity="medium",
                        owner="Quality / CX",
                        recommendation="Inspect return reasons and tighten quality checks for the category.",
                    )
                )

        if not risks:
            return OperationalRisksResponse(rows=[], available=False, meta=ResponseMeta())
        return OperationalRisksResponse(rows=risks[:20], available=True, meta=ResponseMeta())

    def _metric(
        self,
        id: str,
        label: str,
        value: float | None,
        formatted: str | None,
        fmt: Literal["currency", "percent", "number"],
        available: bool,
        *,
        unit: str | None = None,
        source: str | None = None,
    ) -> OperationsMetric:
        return OperationsMetric(
            id=id,
            label=label,
            value=value,
            formatted_value=formatted,
            unit=unit,
            format=fmt,
            available=available,
            source=source,
        )

    def _store_region_map(self) -> dict[str, str]:
        try:
            rows = self.sales.get_sales_summary_rows(
                AnalyticsQuery(
                    page_size=500,
                    columns=["store_id", "region_name", "region_code"],
                    sort_by="order_date",
                    sort_dir="desc",
                )
            )
        except Exception:  # noqa: BLE001
            return {}
        mapping: dict[str, str] = {}
        for row in rows:
            if row.get("store_id") is None:
                continue
            mapping[str(row["store_id"])] = str(row.get("region_name") or row.get("region_code") or "Unknown")
        return mapping

    def _product_category_map(self) -> dict[str, dict]:
        try:
            rows = self.sales.get_product_category_rows(AnalyticsQuery(page_size=500))
        except Exception:  # noqa: BLE001
            return {}
        return {str(r.get("product_id")): r for r in rows if r.get("product_id") is not None}

    def _safe_inventory(
        self,
        *,
        category: list[str] | None,
        search: str | None,
        region: list[str] | None,
    ) -> list[dict]:
        filters: list[FilterClause] = []
        if category:
            filters.append(FilterClause(column="category_name", op=FilterOperator.IN, value=category))
        try:
            rows = self.operations.get_inventory_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="inventory_value_cost",
                    sort_dir="desc",
                    search=search,
                    filters=filters,
                )
            )
        except Exception:  # noqa: BLE001
            return []
        if region:
            store_region = self._store_region_map()
            wanted = {r.lower() for r in region}
            rows = [
                row
                for row in rows
                if store_region.get(str(row.get("store_id")), "Unknown").lower() in wanted
            ]
        return rows

    def _safe_suppliers(self, *, supplier: list[str] | None, search: str | None) -> list[dict]:
        filters: list[FilterClause] = []
        if supplier:
            filters.append(FilterClause(column="supplier_name", op=FilterOperator.IN, value=supplier))
        try:
            return self.operations.get_supplier_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="on_time_rate",
                    sort_dir="desc",
                    search=search,
                    filters=filters,
                )
            )
        except Exception:  # noqa: BLE001
            return []

    def _safe_returns(self, *, date_from: date | None, date_to: date | None) -> list[dict]:
        try:
            return self.operations.get_return_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="return_date",
                    sort_dir="desc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="return_date",
                )
            )
        except Exception:  # noqa: BLE001
            return []

    def _safe_shipments(self, *, date_from: date | None, date_to: date | None) -> list[dict]:
        try:
            return self.operations.get_shipment_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="order_date",
                    sort_dir="desc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="order_date",
                )
            )
        except Exception:  # noqa: BLE001
            return []

    def _sales_units(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        region: list[str] | None,
    ) -> float | None:
        filters: list[FilterClause] = []
        if region:
            filters.append(FilterClause(column="region_name", op=FilterOperator.IN, value=region))
        try:
            rows = self.sales.get_sales_summary_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="order_date",
                    sort_dir="asc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="order_date",
                    filters=filters,
                )
            )
        except Exception:  # noqa: BLE001
            return None
        if not rows:
            return None
        total = sum(filter(None, (_as_float(r.get("units_sold")) for r in rows)))
        return total if total else None

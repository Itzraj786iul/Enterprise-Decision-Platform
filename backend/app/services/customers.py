"""Customer Intelligence orchestration — analytics services only (no SQL)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from app.analytics.query import AnalyticsQuery, FilterClause, FilterOperator
from app.analytics.services.customer import CustomerAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.analytics.services.sales import SalesAnalyticsService
from app.schemas.common import PaginationMeta, ResponseMeta
from app.schemas.customers import (
    ChurnRiskResponse,
    ChurnRiskRow,
    CohortRetentionCell,
    CohortRow,
    CohortsResponse,
    CustomerDistributionResponse,
    CustomerDistributionRow,
    CustomerMetric,
    CustomerOverviewResponse,
    RfmSegmentRow,
    RfmSegmentsResponse,
    TopCustomerDetailRow,
    TopCustomersDetailResponse,
)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
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


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    return date(year, month, 1)


class CustomerService:
    """
    Vertical-slice orchestrator for Customer Intelligence.
    Depends on Customer, Sales (region map), and ML analytics services only.
    """

    def __init__(
        self,
        customers: CustomerAnalyticsService,
        sales: SalesAnalyticsService,
        machine_learning: MachineLearningService,
    ) -> None:
        self.customers = customers
        self.sales = sales
        self.machine_learning = machine_learning

    def get_overview(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        segment: list[str] | None = None,
        search: str | None = None,
    ) -> CustomerOverviewResponse:
        rows = self._safe_customer_rows(search=search)
        store_region = self._store_region_map()
        rfm_by_id = self._rfm_by_customer_id(segment=segment)
        rows = self._apply_customer_filters(rows, region=region, segment=segment, store_region=store_region, rfm_by_id=rfm_by_id)

        period_end = date_to or date.today()
        period_start = date_from or (period_end - timedelta(days=29))
        window = (period_end - period_start).days + 1
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=window - 1)

        if not rows:
            metrics = [
                self._metric("active_customers", "Active Customers", None, None, "number", False),
                self._metric("new_customers", "New Customers", None, None, "number", False),
                self._metric("repeat_customers", "Repeat Customers", None, None, "number", False),
                self._metric("avg_ltv", "Average Lifetime Value", None, None, "currency", False, unit="USD"),
                self._metric("retention_rate", "Retention Rate", None, None, "percent", False),
                self._metric("churn_risk_summary", "Churn Risk Summary", None, None, "percent", False),
            ]
            return CustomerOverviewResponse(
                metrics=metrics,
                period_start=period_start,
                period_end=period_end,
                meta=ResponseMeta(),
            )

        active = [r for r in rows if self._is_active(r)]
        new_customers = [
            r
            for r in rows
            if (d := _coerce_date(r.get("first_order_date") or r.get("registration_date")))
            and period_start <= d <= period_end
        ]
        prior_new = [
            r
            for r in rows
            if (d := _coerce_date(r.get("first_order_date") or r.get("registration_date")))
            and prior_start <= d <= prior_end
        ]
        repeat = [r for r in rows if (_as_float(r.get("order_count")) or 0) > 1]
        ltvs = [_as_float(r.get("lifetime_net_sales")) for r in rows]
        ltvs = [v for v in ltvs if v is not None]
        avg_ltv = (sum(ltvs) / len(ltvs)) if ltvs else None

        retained = [
            r
            for r in rows
            if (d := _coerce_date(r.get("last_order_date"))) is not None and d >= period_start
        ]
        base_for_retention = [
            r
            for r in rows
            if (d := _coerce_date(r.get("first_order_date"))) is not None and d < period_start
        ]
        retention = (len(retained) / len(base_for_retention)) if base_for_retention else None

        at_risk = [
            r
            for r in rows
            if str(r.get("lifecycle_status") or "").lower() in {"churn risk", "at risk"}
        ]
        churn_summary = (len(at_risk) / len(rows)) if rows else None

        new_growth = (
            ((len(new_customers) - len(prior_new)) / len(prior_new)) if prior_new else None
        )

        metrics = [
            self._metric(
                "active_customers",
                "Active Customers",
                float(len(active)),
                _format_number(float(len(active))),
                "number",
                True,
            ),
            self._metric(
                "new_customers",
                "New Customers",
                float(len(new_customers)),
                _format_number(float(len(new_customers))),
                "number",
                True,
                delta=new_growth,
                delta_label="vs prior period" if new_growth is not None else None,
            ),
            self._metric(
                "repeat_customers",
                "Repeat Customers",
                float(len(repeat)),
                _format_number(float(len(repeat))),
                "number",
                True,
            ),
            self._metric(
                "avg_ltv",
                "Average Lifetime Value",
                avg_ltv,
                _format_currency(avg_ltv),
                "currency",
                avg_ltv is not None,
                unit="USD",
            ),
            self._metric(
                "retention_rate",
                "Retention Rate",
                retention,
                _format_percent(retention),
                "percent",
                retention is not None,
            ),
            self._metric(
                "churn_risk_summary",
                "Churn Risk Summary",
                churn_summary,
                _format_percent(churn_summary),
                "percent",
                churn_summary is not None,
                source="customer_360",
            ),
        ]
        return CustomerOverviewResponse(
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            meta=ResponseMeta(),
        )

    def get_rfm_segments(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        segment: list[str] | None = None,
        search: str | None = None,
    ) -> RfmSegmentsResponse:
        try:
            rfm_rows = self.customers.get_customer_rfm_rows(
                AnalyticsQuery(page_size=500, sort_by="rfm_total", sort_dir="desc", search=search)
            )
            customers = {
                str(r.get("customer_id")): r
                for r in self.customers.get_customer_360_rows(
                    AnalyticsQuery(page_size=500, sort_by="lifetime_net_sales", sort_dir="desc")
                )
            }
        except Exception:  # noqa: BLE001
            return RfmSegmentsResponse(rows=[], available=False, meta=ResponseMeta())

        if not rfm_rows:
            return RfmSegmentsResponse(rows=[], available=False, meta=ResponseMeta())

        period_end = date_to or date.today()
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        wanted = {s.lower() for s in segment} if segment else None
        current: dict[str, dict[str, float]] = {}
        prior_revenue: dict[str, float] = {}

        for row in rfm_rows:
            name = str(row.get("rfm_segment") or "Unknown")
            if wanted and name.lower() not in wanted:
                continue
            cid = str(row.get("customer_id"))
            profile = customers.get(cid, {})
            revenue = _as_float(row.get("lifetime_net_sales")) or _as_float(profile.get("lifetime_net_sales")) or 0.0
            aov = _as_float(profile.get("avg_order_value"))
            orders = _as_float(row.get("order_count")) or _as_float(profile.get("order_count")) or 0.0
            if aov is None and orders:
                aov = revenue / orders

            last_order = _coerce_date(row.get("last_order_date") or profile.get("last_order_date"))
            bucket = current.setdefault(
                name, {"count": 0.0, "revenue": 0.0, "aov_sum": 0.0, "aov_n": 0.0}
            )
            bucket["count"] += 1
            bucket["revenue"] += revenue
            if aov is not None:
                bucket["aov_sum"] += aov
                bucket["aov_n"] += 1

            if last_order and prior_start <= last_order <= prior_end:
                prior_revenue[name] = prior_revenue.get(name, 0.0) + revenue

        # Growth: revenue of customers active in prior window vs current window (by last order)
        current_window_rev: dict[str, float] = {}
        for row in rfm_rows:
            name = str(row.get("rfm_segment") or "Unknown")
            if wanted and name.lower() not in wanted:
                continue
            cid = str(row.get("customer_id"))
            profile = customers.get(cid, {})
            revenue = _as_float(row.get("lifetime_net_sales")) or _as_float(profile.get("lifetime_net_sales")) or 0.0
            last_order = _coerce_date(row.get("last_order_date") or profile.get("last_order_date"))
            if last_order and period_start <= last_order <= period_end:
                current_window_rev[name] = current_window_rev.get(name, 0.0) + revenue

        result: list[RfmSegmentRow] = []
        for name, values in sorted(current.items(), key=lambda item: item[1]["revenue"], reverse=True):
            prior = prior_revenue.get(name)
            curr = current_window_rev.get(name)
            growth = ((curr - prior) / prior) if prior and curr is not None else None
            aov = (values["aov_sum"] / values["aov_n"]) if values["aov_n"] else None
            result.append(
                RfmSegmentRow(
                    segment=name,
                    customer_count=values["count"],
                    revenue=values["revenue"],
                    average_order_value=aov,
                    growth=growth,
                )
            )
        return RfmSegmentsResponse(rows=result, available=True, meta=ResponseMeta())

    def get_cohorts(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        segment: list[str] | None = None,
        search: str | None = None,
        max_months: int = 6,
    ) -> CohortsResponse:
        rows = self._safe_customer_rows(search=search)
        store_region = self._store_region_map()
        rfm_by_id = self._rfm_by_customer_id(segment=segment)
        rows = self._apply_customer_filters(rows, region=region, segment=segment, store_region=store_region, rfm_by_id=rfm_by_id)

        cohorts: dict[str, list[dict]] = {}
        for row in rows:
            first = _coerce_date(row.get("first_order_date"))
            if first is None:
                continue
            if date_from and first < date_from:
                continue
            if date_to and first > date_to:
                continue
            key = _month_start(first).isoformat()[:7]
            cohorts.setdefault(key, []).append(row)

        if not cohorts:
            return CohortsResponse(rows=[], available=False, meta=ResponseMeta())

        result: list[CohortRow] = []
        for key in sorted(cohorts.keys())[-12:]:
            members = cohorts[key]
            cohort_start = date.fromisoformat(f"{key}-01")
            retentions: list[CohortRetentionCell] = []
            for offset in range(max_months):
                threshold = _add_months(cohort_start, offset)
                still = [
                    m
                    for m in members
                    if (d := _coerce_date(m.get("last_order_date"))) is not None and d >= threshold
                ]
                pct = (len(still) / len(members)) if members else None
                retentions.append(
                    CohortRetentionCell(
                        month_offset=offset,
                        retention_pct=pct,
                        customer_count=float(len(still)),
                    )
                )
            result.append(
                CohortRow(
                    cohort=key,
                    cohort_size=float(len(members)),
                    retentions=retentions,
                )
            )
        return CohortsResponse(rows=result, available=True, meta=ResponseMeta())

    def get_customer_distribution(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        segment: list[str] | None = None,
        search: str | None = None,
    ) -> CustomerDistributionResponse:
        rows = self._safe_customer_rows(search=search)
        store_region = self._store_region_map()
        rfm_by_id = self._rfm_by_customer_id(segment=segment)
        rows = self._apply_customer_filters(rows, region=region, segment=segment, store_region=store_region, rfm_by_id=rfm_by_id)

        if not rows or not store_region:
            # Still allow Unknown bucket from preferred_store_id absence
            if not rows:
                return CustomerDistributionResponse(rows=[], available=False, meta=ResponseMeta())

        period_end = date_to or date.today()
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        current: dict[str, dict[str, float]] = {}
        prior_counts: dict[str, float] = {}

        for row in rows:
            store_id = row.get("preferred_store_id")
            name = store_region.get(str(store_id), "Unknown") if store_id is not None else "Unknown"
            if region and name not in region and name.lower() not in {r.lower() for r in region}:
                continue
            bucket = current.setdefault(name, {"count": 0.0, "revenue": 0.0})
            bucket["count"] += 1
            bucket["revenue"] += _as_float(row.get("lifetime_net_sales")) or 0.0

            first = _coerce_date(row.get("first_order_date") or row.get("registration_date"))
            if first and prior_start <= first <= prior_end:
                prior_counts[name] = prior_counts.get(name, 0.0) + 1

        current_new: dict[str, float] = {}
        for row in rows:
            store_id = row.get("preferred_store_id")
            name = store_region.get(str(store_id), "Unknown") if store_id is not None else "Unknown"
            first = _coerce_date(row.get("first_order_date") or row.get("registration_date"))
            if first and period_start <= first <= period_end:
                current_new[name] = current_new.get(name, 0.0) + 1

        result = []
        for name, values in sorted(current.items(), key=lambda item: item[1]["revenue"], reverse=True):
            prior = prior_counts.get(name)
            curr = current_new.get(name)
            growth = ((curr - prior) / prior) if prior and curr is not None else None
            result.append(
                CustomerDistributionRow(
                    region=name,
                    customer_count=values["count"],
                    revenue=values["revenue"],
                    growth=growth,
                )
            )
        return CustomerDistributionResponse(rows=result, available=bool(result), meta=ResponseMeta())

    def get_top_customers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "lifetime_value",
        sort_dir: Literal["asc", "desc"] = "desc",
        search: str | None = None,
        columns: list[str] | None = None,
        region: list[str] | None = None,
        segment: list[str] | None = None,
    ) -> TopCustomersDetailResponse:
        rows = self._safe_customer_rows(search=search)
        store_region = self._store_region_map()
        rfm_by_id = self._rfm_by_customer_id(segment=None)
        rows = self._apply_customer_filters(rows, region=region, segment=segment, store_region=store_region, rfm_by_id=rfm_by_id)

        if not rows:
            return TopCustomersDetailResponse(
                rows=[],
                pagination=PaginationMeta(page=page, page_size=page_size, total_items=0, total_pages=0),
                available=False,
                meta=ResponseMeta(),
            )

        details: list[TopCustomerDetailRow] = []
        for row in rows:
            cid = str(row.get("customer_id")) if row.get("customer_id") is not None else None
            store_id = row.get("preferred_store_id")
            rfm = rfm_by_id.get(cid or "", {})
            details.append(
                TopCustomerDetailRow(
                    customer_id=cid,
                    customer=str(row.get("customer_number") or cid or "Unknown"),
                    segment=str(rfm["rfm_segment"]) if rfm.get("rfm_segment") is not None else None,
                    region=store_region.get(str(store_id)) if store_id is not None else None,
                    lifetime_value=_as_float(row.get("lifetime_net_sales")),
                    orders=_as_float(row.get("order_count")),
                    average_order_value=_as_float(row.get("avg_order_value")),
                    lifecycle_status=str(row["lifecycle_status"]) if row.get("lifecycle_status") is not None else None,
                    last_order_date=_coerce_date(row.get("last_order_date")),
                )
            )

        sort_map = {
            "lifetime_value": lambda r: r.lifetime_value or 0.0,
            "orders": lambda r: r.orders or 0.0,
            "average_order_value": lambda r: r.average_order_value or 0.0,
            "customer": lambda r: r.customer.lower(),
            "segment": lambda r: (r.segment or "").lower(),
        }
        key_fn = sort_map.get(sort_by, sort_map["lifetime_value"])
        details.sort(key=key_fn, reverse=(sort_dir == "desc"))

        total = len(details)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        start = (page - 1) * page_size
        page_rows = details[start : start + page_size]

        if columns:
            keep = set(columns) | {"customer"}
            projected = []
            for row in page_rows:
                data = row.model_dump()
                projected.append(
                    TopCustomerDetailRow(
                        **{k: (v if k in keep else None) for k, v in data.items()}
                    )
                )
            page_rows = projected

        return TopCustomersDetailResponse(
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

    def get_churn_risk(
        self,
        *,
        search: str | None = None,
        segment: list[str] | None = None,
    ) -> ChurnRiskResponse:
        try:
            page = self.machine_learning.get_predictions(
                AnalyticsQuery(page_size=200, sort_by="score", sort_dir="desc", search=search)
            )
            rows = page.table.rows
        except Exception:  # noqa: BLE001
            # Fallback: lifecycle-based risk from customer 360 (no fabricated ML scores)
            return self._churn_from_lifecycle(segment=segment, search=search)

        if not rows:
            return self._churn_from_lifecycle(segment=segment, search=search)

        customers = {
            str(r.get("customer_id")): r
            for r in self._safe_customer_rows(search=None)
        }
        rfm_by_id = self._rfm_by_customer_id(segment=segment)

        buckets: dict[str, dict[str, float]] = {
            "High": {"count": 0.0, "revenue": 0.0, "confidence_sum": 0.0, "confidence_n": 0.0},
            "Medium": {"count": 0.0, "revenue": 0.0, "confidence_sum": 0.0, "confidence_n": 0.0},
            "Low": {"count": 0.0, "revenue": 0.0, "confidence_sum": 0.0, "confidence_n": 0.0},
        }
        matched = 0
        for row in rows:
            model = str(row.get("model_name") or row.get("model") or "").lower()
            label = str(row.get("label") or row.get("prediction") or "").lower()
            score = _as_float(row.get("score") or row.get("churn_probability") or row.get("risk_score"))
            is_churn = "churn" in model or "churn" in label or "risk" in model
            if not is_churn and score is None:
                continue
            if not is_churn and score is not None and score < 0.3:
                continue
            matched += 1
            entity = str(row.get("entity_id") or row.get("customer_id") or "")
            if segment and entity:
                rfm = rfm_by_id.get(entity)
                if not rfm:
                    continue
            level = self._risk_level(score)
            conf = _as_float(row.get("confidence") or row.get("prediction_confidence"))
            ltv = _as_float(row.get("estimated_impact") or row.get("revenue_at_risk"))
            if ltv is None and entity in customers:
                ltv = _as_float(customers[entity].get("lifetime_net_sales"))
            bucket = buckets[level]
            bucket["count"] += 1
            bucket["revenue"] += ltv or 0.0
            if conf is not None:
                bucket["confidence_sum"] += conf
                bucket["confidence_n"] += 1

        if matched == 0:
            return self._churn_from_lifecycle(segment=segment, search=search)

        result = []
        for level in ("High", "Medium", "Low"):
            values = buckets[level]
            conf = (
                values["confidence_sum"] / values["confidence_n"]
                if values["confidence_n"]
                else None
            )
            result.append(
                ChurnRiskRow(
                    risk_level=level,
                    customer_count=values["count"],
                    predicted_revenue_at_risk=values["revenue"] if values["count"] else None,
                    confidence=conf,
                    confidence_available=conf is not None,
                )
            )
        return ChurnRiskResponse(rows=result, available=True, meta=ResponseMeta())

    def _churn_from_lifecycle(
        self,
        *,
        segment: list[str] | None,
        search: str | None,
    ) -> ChurnRiskResponse:
        rows = self._safe_customer_rows(search=search)
        store_region = self._store_region_map()
        rfm_by_id = self._rfm_by_customer_id(segment=segment)
        rows = self._apply_customer_filters(
            rows, region=None, segment=segment, store_region=store_region, rfm_by_id=rfm_by_id
        )
        if not rows:
            return ChurnRiskResponse(rows=[], available=False, source="customer_360", meta=ResponseMeta())

        buckets = {
            "High": {"count": 0.0, "revenue": 0.0},
            "Medium": {"count": 0.0, "revenue": 0.0},
            "Low": {"count": 0.0, "revenue": 0.0},
        }
        for row in rows:
            status = str(row.get("lifecycle_status") or "").lower()
            if status == "churn risk":
                level = "High"
            elif status == "at risk":
                level = "Medium"
            else:
                level = "Low"
            buckets[level]["count"] += 1
            if level in {"High", "Medium"}:
                buckets[level]["revenue"] += _as_float(row.get("lifetime_net_sales")) or 0.0

        return ChurnRiskResponse(
            rows=[
                ChurnRiskRow(
                    risk_level=level,
                    customer_count=values["count"],
                    predicted_revenue_at_risk=values["revenue"] if level != "Low" else None,
                    confidence=None,
                    confidence_available=False,
                )
                for level, values in buckets.items()
            ],
            available=True,
            source="customer_360",
            meta=ResponseMeta(),
        )

    @staticmethod
    def _risk_level(score: float | None) -> str:
        if score is None:
            return "Medium"
        if score >= 0.7:
            return "High"
        if score >= 0.4:
            return "Medium"
        return "Low"

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
        delta: float | None = None,
        delta_label: str | None = None,
        source: str = "customer_360",
    ) -> CustomerMetric:
        return CustomerMetric(
            id=id,
            label=label,
            value=value,
            formatted_value=formatted,
            unit=unit,
            delta=delta,
            delta_label=delta_label,
            trend=_trend(delta),
            format=fmt,
            available=available,
            source=source,
        )

    def _safe_customer_rows(self, *, search: str | None) -> list[dict]:
        try:
            return self.customers.get_customer_360_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="lifetime_net_sales",
                    sort_dir="desc",
                    search=search,
                )
            )
        except Exception:  # noqa: BLE001
            return []

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
            store_id = row.get("store_id")
            if store_id is None:
                continue
            name = str(row.get("region_name") or row.get("region_code") or "Unknown")
            mapping[str(store_id)] = name
        return mapping

    def _rfm_by_customer_id(self, *, segment: list[str] | None) -> dict[str, dict]:
        try:
            filters = []
            if segment:
                filters.append(FilterClause(column="rfm_segment", op=FilterOperator.IN, value=segment))
            rows = self.customers.get_customer_rfm_rows(
                AnalyticsQuery(page_size=500, sort_by="rfm_total", sort_dir="desc", filters=filters)
            )
        except Exception:  # noqa: BLE001
            return {}
        return {str(r.get("customer_id")): r for r in rows if r.get("customer_id") is not None}

    @staticmethod
    def _is_active(row: dict) -> bool:
        status = str(row.get("lifecycle_status") or "").lower()
        if status == "active":
            return True
        flag = _as_bool(row.get("is_active"))
        if flag is True and status not in {"churn risk", "never purchased"}:
            return True
        return False

    @staticmethod
    def _apply_customer_filters(
        rows: list[dict],
        *,
        region: list[str] | None,
        segment: list[str] | None,
        store_region: dict[str, str],
        rfm_by_id: dict[str, dict],
    ) -> list[dict]:
        result = rows
        if segment:
            allowed = set(rfm_by_id.keys())
            result = [r for r in result if str(r.get("customer_id")) in allowed]
        if region:
            wanted = {r.lower() for r in region}
            filtered = []
            for row in result:
                store_id = row.get("preferred_store_id")
                name = store_region.get(str(store_id), "Unknown") if store_id is not None else "Unknown"
                if name.lower() in wanted:
                    filtered.append(row)
            result = filtered
        return result

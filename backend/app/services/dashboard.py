"""Executive dashboard orchestration — uses analytics services only (no SQL)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.analytics.query import AnalyticsQuery
from app.analytics.services.data_quality import DataQualityService
from app.analytics.services.executive import ExecutiveAnalyticsService
from app.analytics.services.ml import MachineLearningService
from app.schemas.common import ResponseMeta
from app.schemas.dashboard import (
    DashboardMetric,
    DashboardOverviewResponse,
    DashboardTrendPoint,
    DashboardTrendsResponse,
    OpportunitiesResponse,
    OpportunityItem,
    RegionalPerformanceResponse,
    RegionalPerformanceRow,
    RiskItem,
    TopRisksResponse,
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


def _trend(delta: float | None) -> str | None:
    if delta is None:
        return None
    if delta > 0.001:
        return "up"
    if delta < -0.001:
        return "down"
    return "flat"


def _priority_from_score(score: float | None) -> str:
    if score is None:
        return "medium"
    if score >= 0.85:
        return "critical"
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


class DashboardService:
    """
    Vertical-slice orchestrator for the Executive Dashboard.
    Depends only on Executive / DataQuality / MachineLearning services.
    """

    def __init__(
        self,
        executive: ExecutiveAnalyticsService,
        data_quality: DataQualityService,
        machine_learning: MachineLearningService,
    ) -> None:
        self.executive = executive
        self.data_quality = data_quality
        self.machine_learning = machine_learning

    def get_overview(self, *, days: int = 30) -> DashboardOverviewResponse:
        scorecard = self.executive.get_scorecard_rows(
            AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=max(days * 2, 60))
        )
        dated = []
        for row in scorecard:
            d = _coerce_date(row.get("order_date") or row.get("kpi_date"))
            if d is not None:
                dated.append((d, row))
        dated.sort(key=lambda item: item[0])

        period_end = dated[-1][0] if dated else None
        period_start = period_end - timedelta(days=days - 1) if period_end else None
        current_rows = [row for d, row in dated if period_start and d >= period_start]
        prior_start = period_start - timedelta(days=days) if period_start else None
        prior_end = period_start - timedelta(days=1) if period_start else None
        prior_rows = [
            row
            for d, row in dated
            if prior_start and prior_end and prior_start <= d <= prior_end
        ]

        revenue = sum(filter(None, (_as_float(r.get("net_sales")) for r in current_rows)))
        profit = sum(filter(None, (_as_float(r.get("gross_profit")) for r in current_rows)))
        prior_revenue = sum(filter(None, (_as_float(r.get("net_sales")) for r in prior_rows)))
        margin = (profit / revenue) if revenue else None
        growth = ((revenue - prior_revenue) / prior_revenue) if prior_revenue else None

        stockouts = sum(filter(None, (_as_float(r.get("stockout_positions")) for r in current_rows)))
        positions = sum(filter(None, (_as_float(r.get("snapshot_positions")) for r in current_rows)))
        inventory_health = (1 - (stockouts / positions)) if positions else None

        dq_score = self._extract_dq_score()
        churn_risk, active_customers = self._extract_ml_overview_signals()

        metrics = [
            DashboardMetric(
                id="revenue",
                label="Revenue",
                value=revenue if current_rows else None,
                formatted_value=_format_currency(revenue if current_rows else None),
                unit="USD",
                delta=growth,
                delta_label="vs prior period" if growth is not None else None,
                trend=_trend(growth),  # type: ignore[arg-type]
                format="currency",
                available=bool(current_rows),
                source="executive_scorecard",
            ),
            DashboardMetric(
                id="profit",
                label="Profit",
                value=profit if current_rows else None,
                formatted_value=_format_currency(profit if current_rows else None),
                unit="USD",
                format="currency",
                available=bool(current_rows),
                source="executive_scorecard",
            ),
            DashboardMetric(
                id="profit_margin",
                label="Profit Margin",
                value=margin,
                formatted_value=_format_percent(margin),
                format="percent",
                available=margin is not None,
                source="executive_scorecard",
            ),
            DashboardMetric(
                id="revenue_growth",
                label="Revenue Growth",
                value=growth,
                formatted_value=_format_percent(growth),
                trend=_trend(growth),  # type: ignore[arg-type]
                format="percent",
                available=growth is not None,
                source="executive_scorecard",
            ),
            DashboardMetric(
                id="active_customers",
                label="Active Customers",
                value=active_customers,
                formatted_value=_format_number(active_customers),
                format="number",
                available=active_customers is not None,
                source="machine_learning_predictions",
            ),
            DashboardMetric(
                id="inventory_health",
                label="Inventory Health",
                value=inventory_health,
                formatted_value=_format_percent(inventory_health),
                format="percent",
                available=inventory_health is not None,
                source="executive_scorecard",
            ),
            DashboardMetric(
                id="dq_score",
                label="DQ Score",
                value=dq_score,
                formatted_value=_format_percent(dq_score) if dq_score is not None and dq_score <= 1 else _format_number(dq_score),
                format="percent" if dq_score is not None and dq_score <= 1 else "number",
                available=dq_score is not None,
                source="data_quality_summary",
            ),
            DashboardMetric(
                id="overall_churn_risk",
                label="Overall Churn Risk",
                value=churn_risk,
                formatted_value=_format_percent(churn_risk),
                format="percent",
                available=churn_risk is not None,
                source="machine_learning_predictions",
            ),
        ]

        return DashboardOverviewResponse(
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            meta=ResponseMeta(),
        )

    def get_trends(self, *, days: int = 90) -> DashboardTrendsResponse:
        rows = self.executive.get_scorecard_rows(
            AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=max(days, 90))
        )
        points: list[DashboardTrendPoint] = []
        for row in rows[-days:]:
            d = _coerce_date(row.get("order_date") or row.get("kpi_date"))
            if d is None:
                continue
            points.append(
                DashboardTrendPoint(
                    date=d,
                    revenue=_as_float(row.get("net_sales")),
                    profit=_as_float(row.get("gross_profit")),
                    orders=_as_float(row.get("order_count")),
                )
            )
        return DashboardTrendsResponse(points=points, grain="day", meta=ResponseMeta())

    def get_regional_performance(self, *, days: int = 30) -> RegionalPerformanceResponse:
        detail = self.executive.get_commercial_detail(
            AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        )
        rows = detail.table.rows
        if not rows:
            return RegionalPerformanceResponse(rows=[], meta=ResponseMeta())

        # Split current vs prior windows when dates exist
        dated_rows: list[tuple[date, dict[str, Any]]] = []
        for row in rows:
            d = _coerce_date(row.get("order_date"))
            if d is not None:
                dated_rows.append((d, row))
        period_end = max((d for d, _ in dated_rows), default=None)
        period_start = period_end - timedelta(days=days - 1) if period_end else None
        prior_start = period_start - timedelta(days=days) if period_start else None
        prior_end = period_start - timedelta(days=1) if period_start else None

        current: dict[str, dict[str, float]] = {}
        prior: dict[str, float] = {}

        for d, row in dated_rows:
            region = str(row.get("region_name") or row.get("region_code") or "Unknown")
            revenue = _as_float(row.get("net_sales")) or 0.0
            profit = _as_float(row.get("gross_profit")) or 0.0
            orders = _as_float(row.get("order_count")) or 0.0
            if period_start and d >= period_start:
                bucket = current.setdefault(region, {"revenue": 0.0, "profit": 0.0, "orders": 0.0})
                bucket["revenue"] += revenue
                bucket["profit"] += profit
                bucket["orders"] += orders
            elif prior_start and prior_end and prior_start <= d <= prior_end:
                prior[region] = prior.get(region, 0.0) + revenue

        result_rows: list[RegionalPerformanceRow] = []
        for region, values in sorted(current.items(), key=lambda item: item[1]["revenue"], reverse=True):
            prior_rev = prior.get(region)
            growth = ((values["revenue"] - prior_rev) / prior_rev) if prior_rev else None
            result_rows.append(
                RegionalPerformanceRow(
                    region=region,
                    revenue=values["revenue"],
                    profit=values["profit"],
                    growth=growth,
                    order_count=values["orders"],
                )
            )
        return RegionalPerformanceResponse(rows=result_rows, meta=ResponseMeta())

    def get_top_risks(self, *, limit: int = 10) -> TopRisksResponse:
        items: list[RiskItem] = []

        # DQ severity → operational risk
        try:
            dq = self.data_quality.get_quality_summary(
                AnalyticsQuery(page_size=100, sort_by="score", sort_dir="asc")
            )
            for idx, row in enumerate(dq.table.rows):
                severity = str(row.get("severity") or row.get("status") or "").lower()
                score = _as_float(row.get("score"))
                if severity in {"critical", "high", "error", "fail"} or (score is not None and score < 0.7):
                    title = str(row.get("check_name") or row.get("entity_name") or "Data quality issue")
                    items.append(
                        RiskItem(
                            id=f"dq-{idx}-{title}"[:64],
                            title=title,
                            description=str(row.get("message") or row.get("description") or "Data quality finding"),
                            priority=_priority_from_score(1 - score if score is not None else 0.75),  # type: ignore[arg-type]
                            impact=severity or "data quality",
                            owner=str(row.get("owner") or "Data Platform"),
                            source="data_quality_summary",
                            raw=row,
                        )
                    )
        except Exception:  # noqa: BLE001 — view may be absent
            pass

        # ML churn / risk predictions
        try:
            preds = self.machine_learning.get_predictions(
                AnalyticsQuery(page_size=100, sort_by="score", sort_dir="desc")
            )
            for idx, row in enumerate(preds.table.rows):
                model = str(row.get("model_name") or row.get("model") or "").lower()
                score = _as_float(row.get("score") or row.get("churn_probability") or row.get("risk_score"))
                label = str(row.get("label") or row.get("prediction") or "")
                is_risk = "churn" in model or "risk" in model or label.lower() in {"churn", "high_risk", "at_risk"}
                if not is_risk and score is not None and score >= 0.7 and "churn" in str(row).lower():
                    is_risk = True
                if not is_risk:
                    continue
                entity = str(row.get("entity_id") or row.get("customer_id") or idx)
                items.append(
                    RiskItem(
                        id=f"ml-risk-{entity}"[:64],
                        title=str(row.get("title") or f"Elevated risk signal ({entity})"),
                        description=str(row.get("explanation") or row.get("description") or model or "ML risk prediction"),
                        priority=_priority_from_score(score),  # type: ignore[arg-type]
                        impact=_format_percent(score) if score is not None else None,
                        owner=str(row.get("owner") or "Customer Analytics"),
                        source="machine_learning_predictions",
                        raw=row,
                    )
                )
        except Exception:  # noqa: BLE001
            pass

        # Inventory pressure from executive scorecard (latest day)
        try:
            scorecard = self.executive.get_scorecard_rows(
                AnalyticsQuery(sort_by="order_date", sort_dir="desc", page_size=1)
            )
            if scorecard:
                latest = scorecard[0]
                stockouts = _as_float(latest.get("stockout_positions")) or 0
                positions = _as_float(latest.get("snapshot_positions")) or 0
                if positions and stockouts / positions >= 0.05:
                    ratio = stockouts / positions
                    items.append(
                        RiskItem(
                            id="inventory-stockout-pressure",
                            title="Inventory stockout pressure",
                            description=f"{stockouts:.0f} of {positions:.0f} positions stocked out on latest scorecard day",
                            priority=_priority_from_score(ratio),  # type: ignore[arg-type]
                            impact=_format_percent(ratio),
                            owner="Operations",
                            source="executive_scorecard",
                            raw=latest,
                        )
                    )
        except Exception:  # noqa: BLE001
            pass

        items = items[:limit]
        return TopRisksResponse(items=items, meta=ResponseMeta())

    def get_opportunities(self, *, limit: int = 10) -> OpportunitiesResponse:
        items: list[OpportunityItem] = []
        try:
            preds = self.machine_learning.get_predictions(
                AnalyticsQuery(page_size=100, sort_by="score", sort_dir="desc")
            )
            for idx, row in enumerate(preds.table.rows):
                model = str(row.get("model_name") or row.get("model") or "").lower()
                score = _as_float(row.get("score") or row.get("uplift") or row.get("propensity"))
                label = str(row.get("label") or row.get("prediction") or "").lower()
                is_opportunity = any(
                    token in model or token in label
                    for token in ("uplift", "propensity", "recommend", "opportunity", "growth", "cross_sell")
                )
                if not is_opportunity:
                    continue
                entity = str(row.get("entity_id") or row.get("customer_id") or idx)
                impact = row.get("estimated_impact") or row.get("impact") or _format_percent(score)
                items.append(
                    OpportunityItem(
                        id=f"ml-opp-{entity}"[:64],
                        title=str(row.get("title") or f"Growth opportunity ({entity})"),
                        description=str(row.get("explanation") or row.get("description") or model),
                        estimated_impact=str(impact) if impact is not None else None,
                        priority="high" if (score or 0) >= 0.7 else "medium" if (score or 0) >= 0.4 else "low",
                        source="machine_learning_predictions",
                        raw=row,
                    )
                )
        except Exception:  # noqa: BLE001
            pass

        # Margin expansion signal from scorecard (improving margin days)
        try:
            rows = self.executive.get_scorecard_rows(
                AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=14)
            )
            margins = [_as_float(r.get("margin_pct")) for r in rows]
            margins = [m for m in margins if m is not None]
            if len(margins) >= 4 and margins[-1] is not None and margins[0] is not None:
                if margins[-1] > margins[0]:
                    items.append(
                        OpportunityItem(
                            id="margin-expansion",
                            title="Margin expansion trajectory",
                            description="Recent scorecard margin exceeds the start of the trailing window",
                            estimated_impact=_format_percent(margins[-1] - margins[0]),
                            priority="medium",
                            source="executive_scorecard",
                            raw={"start_margin": margins[0], "end_margin": margins[-1]},
                        )
                    )
        except Exception:  # noqa: BLE001
            pass

        return OpportunitiesResponse(items=items[:limit], meta=ResponseMeta())

    def _extract_dq_score(self) -> float | None:
        try:
            page = self.data_quality.get_quality_summary(AnalyticsQuery(page_size=50))
        except Exception:  # noqa: BLE001
            return None
        rows = page.table.rows
        if not rows:
            return None
        # Prefer explicit overall score rows, else average numeric scores
        for row in rows:
            for key in ("overall_score", "dq_score", "quality_score"):
                value = _as_float(row.get(key))
                if value is not None:
                    return value / 100 if value > 1 else value
        scores = [_as_float(r.get("score")) for r in rows]
        scores = [s / 100 if s is not None and s > 1 else s for s in scores]
        scores = [s for s in scores if s is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def _extract_ml_overview_signals(self) -> tuple[float | None, float | None]:
        try:
            page = self.machine_learning.get_predictions(AnalyticsQuery(page_size=200))
        except Exception:  # noqa: BLE001
            return None, None
        rows = page.table.rows
        if not rows:
            return None, None

        churn_scores: list[float] = []
        customer_ids: set[str] = set()
        for row in rows:
            model = str(row.get("model_name") or "").lower()
            entity_type = str(row.get("entity_type") or "").lower()
            score = _as_float(row.get("score") or row.get("churn_probability"))
            if "churn" in model or "churn" in entity_type:
                if score is not None:
                    churn_scores.append(score)
            if entity_type in {"customer", "customers"} or row.get("customer_id") is not None:
                customer_ids.add(str(row.get("entity_id") or row.get("customer_id")))

        churn = (sum(churn_scores) / len(churn_scores)) if churn_scores else None
        active = float(len(customer_ids)) if customer_ids else None
        return churn, active

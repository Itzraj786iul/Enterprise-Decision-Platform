"""Finance Intelligence orchestration — analytics services only (no SQL)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from app.analytics.query import AnalyticsQuery, FilterClause, FilterOperator
from app.analytics.services.finance import FinanceAnalyticsService
from app.schemas.common import ResponseMeta
from app.schemas.finance import (
    BudgetVarianceResponse,
    BudgetVarianceRow,
    CashflowResponse,
    CashflowRow,
    CostBreakdownResponse,
    CostBreakdownRow,
    FinanceMetric,
    FinanceOverviewResponse,
    FinancialRiskRow,
    FinancialRisksResponse,
    ProfitabilityResponse,
    ProfitabilityRow,
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


def _trend(delta: float | None) -> Literal["up", "down", "flat"] | None:
    if delta is None:
        return None
    if delta > 0.001:
        return "up"
    if delta < -0.001:
        return "down"
    return "flat"


def _month_key(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


class FinanceService:
    """
    Vertical-slice orchestrator for Finance Intelligence.
    Depends only on FinanceAnalyticsService (sales / scorecard / payments / campaigns).
    """

    def __init__(self, finance: FinanceAnalyticsService) -> None:
        self.finance = finance

    def get_overview(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        search: str | None = None,
    ) -> FinanceOverviewResponse:
        sales = self._safe_sales(date_from=date_from, date_to=date_to, region=region, search=search)
        scorecard = self._safe_scorecard(date_from=date_from, date_to=date_to)

        dated = self._dated(sales, "order_date")
        period_end = date_to or (dated[-1][0] if dated else None)
        period_start = date_from
        if period_start is None and period_end is not None:
            period_start = period_end - timedelta(days=29)

        current = [
            row
            for d, row in dated
            if (period_start is None or d >= period_start) and (period_end is None or d <= period_end)
        ]
        available = bool(current)

        revenue = sum(filter(None, (_as_float(r.get("net_sales")) for r in current)))
        gross_profit = sum(filter(None, (_as_float(r.get("gross_profit")) for r in current)))
        cogs = sum(filter(None, (_as_float(r.get("cogs_amount")) for r in current)))
        discounts = sum(filter(None, (_as_float(r.get("discount_amount")) for r in current)))

        refunds = 0.0
        refunds_available = False
        for row in scorecard:
            d = _coerce_date(row.get("order_date") or row.get("kpi_date"))
            if d is None:
                continue
            if period_start and d < period_start:
                continue
            if period_end and d > period_end:
                continue
            amount = _as_float(row.get("refund_amount"))
            if amount is not None:
                refunds += amount
                refunds_available = True

        operating_cost = None
        if available:
            operating_cost = cogs + discounts + (refunds if refunds_available else 0.0)

        net_profit = None
        if available:
            net_profit = gross_profit - (refunds if refunds_available else 0.0)

        margin = (gross_profit / revenue) if available and revenue else None
        cost_ratio = (operating_cost / revenue) if operating_cost is not None and revenue else None

        metrics = [
            self._metric(
                "revenue",
                "Revenue",
                revenue if available else None,
                _format_currency(revenue if available else None),
                "currency",
                available,
                unit="USD",
            ),
            self._metric(
                "gross_profit",
                "Gross Profit",
                gross_profit if available else None,
                _format_currency(gross_profit if available else None),
                "currency",
                available,
                unit="USD",
            ),
            self._metric(
                "net_profit",
                "Net Profit",
                net_profit,
                _format_currency(net_profit),
                "currency",
                net_profit is not None,
                unit="USD",
            ),
            self._metric(
                "profit_margin",
                "Profit Margin",
                margin,
                _format_percent(margin),
                "percent",
                margin is not None,
            ),
            self._metric(
                "operating_cost",
                "Operating Cost",
                operating_cost,
                _format_currency(operating_cost),
                "currency",
                operating_cost is not None,
                unit="USD",
            ),
            self._metric(
                "cost_ratio",
                "Cost Ratio",
                cost_ratio,
                _format_percent(cost_ratio),
                "percent",
                cost_ratio is not None,
            ),
        ]
        return FinanceOverviewResponse(
            metrics=metrics,
            period_start=period_start,
            period_end=period_end,
            meta=ResponseMeta(),
        )

    def get_profitability(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        search: str | None = None,
    ) -> ProfitabilityResponse:
        sales = self._safe_sales(date_from=None, date_to=None, region=region, search=search)
        dated = self._dated(sales, "order_date")
        if not dated:
            return ProfitabilityResponse(rows=[], available=False, meta=ResponseMeta())

        period_end = date_to or dated[-1][0]
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        current: dict[str, dict[str, float]] = {}
        prior_rev: dict[str, float] = {}
        for d, row in dated:
            name = str(row.get("region_name") or row.get("region_code") or "Unknown")
            if search and search.lower() not in name.lower():
                continue
            revenue = _as_float(row.get("net_sales")) or 0.0
            cost = _as_float(row.get("cogs_amount")) or 0.0
            profit = _as_float(row.get("gross_profit")) or 0.0
            if period_start <= d <= period_end:
                bucket = current.setdefault(name, {"revenue": 0.0, "cost": 0.0, "profit": 0.0})
                bucket["revenue"] += revenue
                bucket["cost"] += cost
                bucket["profit"] += profit
            elif prior_start <= d <= prior_end:
                prior_rev[name] = prior_rev.get(name, 0.0) + revenue

        rows: list[ProfitabilityRow] = []
        for name, values in sorted(current.items(), key=lambda item: item[1]["profit"], reverse=True):
            prior = prior_rev.get(name)
            growth = ((values["revenue"] - prior) / prior) if prior else None
            margin = (values["profit"] / values["revenue"]) if values["revenue"] else None
            rows.append(
                ProfitabilityRow(
                    region=name,
                    revenue=values["revenue"],
                    cost=values["cost"],
                    profit=values["profit"],
                    margin=margin,
                    growth=growth,
                )
            )
        return ProfitabilityResponse(rows=rows, available=True, meta=ResponseMeta())

    def get_cost_breakdown(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
        cost_category: list[str] | None = None,
        search: str | None = None,
    ) -> CostBreakdownResponse:
        sales = self._safe_sales(date_from=None, date_to=None, region=region, search=None)
        scorecard = self._safe_scorecard(date_from=None, date_to=None)
        dated = self._dated(sales, "order_date")
        if not dated and not scorecard:
            return CostBreakdownResponse(rows=[], available=False, meta=ResponseMeta())

        period_end = date_to or (dated[-1][0] if dated else date.today())
        period_start = date_from or (period_end - timedelta(days=29))
        prior_end = period_start - timedelta(days=1)
        prior_start = prior_end - (period_end - period_start)

        def window_costs(start: date, end: date) -> dict[str, float]:
            costs = {"COGS": 0.0, "Discounts": 0.0, "Refunds": 0.0}
            for d, row in dated:
                if start <= d <= end:
                    costs["COGS"] += _as_float(row.get("cogs_amount")) or 0.0
                    costs["Discounts"] += _as_float(row.get("discount_amount")) or 0.0
            for row in scorecard:
                d = _coerce_date(row.get("order_date") or row.get("kpi_date"))
                if d and start <= d <= end:
                    costs["Refunds"] += _as_float(row.get("refund_amount")) or 0.0
            return costs

        current = window_costs(period_start, period_end)
        prior = window_costs(prior_start, prior_end)
        total = sum(current.values())
        if total <= 0:
            return CostBreakdownResponse(rows=[], available=False, meta=ResponseMeta())

        wanted = {c.lower() for c in cost_category} if cost_category else None
        search_l = search.lower() if search else None
        rows: list[CostBreakdownRow] = []
        for name, amount in sorted(current.items(), key=lambda item: item[1], reverse=True):
            if wanted and name.lower() not in wanted:
                continue
            if search_l and search_l not in name.lower():
                continue
            prior_amt = prior.get(name)
            growth = ((amount - prior_amt) / prior_amt) if prior_amt else None
            rows.append(
                CostBreakdownRow(
                    cost_category=name,
                    amount=amount,
                    percentage=(amount / total) if total else None,
                    trend=_trend(growth),
                )
            )
        return CostBreakdownResponse(rows=rows, available=bool(rows), meta=ResponseMeta())

    def get_cashflow(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        region: list[str] | None = None,
    ) -> CashflowResponse:
        payments = self._safe_payments(date_from=date_from, date_to=date_to)
        sales = self._safe_sales(date_from=date_from, date_to=date_to, region=region, search=None)

        # Prefer payment mix for inflows; fall back to net_sales by month
        inflows: dict[str, float] = {}
        if payments:
            for row in payments:
                d = _coerce_date(row.get("payment_month"))
                if d is None:
                    continue
                key = _month_key(d)
                inflows[key] = inflows.get(key, 0.0) + (_as_float(row.get("payment_amount")) or 0.0)
        else:
            for row in sales:
                d = _coerce_date(row.get("order_date"))
                if d is None:
                    continue
                key = _month_key(d)
                inflows[key] = inflows.get(key, 0.0) + (_as_float(row.get("net_sales")) or 0.0)

        outflows: dict[str, float] = {}
        profit_by_period: dict[str, float] = {}
        revenue_by_period: dict[str, float] = {}
        for row in sales:
            d = _coerce_date(row.get("order_date"))
            if d is None:
                continue
            key = _month_key(d)
            cost = (_as_float(row.get("cogs_amount")) or 0.0) + (_as_float(row.get("discount_amount")) or 0.0)
            outflows[key] = outflows.get(key, 0.0) + cost
            profit_by_period[key] = profit_by_period.get(key, 0.0) + (_as_float(row.get("gross_profit")) or 0.0)
            revenue_by_period[key] = revenue_by_period.get(key, 0.0) + (_as_float(row.get("net_sales")) or 0.0)

        scorecard = self._safe_scorecard(date_from=date_from, date_to=date_to)
        for row in scorecard:
            d = _coerce_date(row.get("order_date") or row.get("kpi_date"))
            if d is None:
                continue
            key = _month_key(d)
            outflows[key] = outflows.get(key, 0.0) + (_as_float(row.get("refund_amount")) or 0.0)

        periods = sorted(set(inflows) | set(outflows) | set(profit_by_period))
        if not periods:
            return CashflowResponse(rows=[], available=False, meta=ResponseMeta())

        rows = []
        for period in periods:
            revenue = revenue_by_period.get(period)
            profit = profit_by_period.get(period)
            margin = (profit / revenue) if revenue and profit is not None else None
            rows.append(
                CashflowRow(
                    period=period,
                    inflows=inflows.get(period, 0.0),
                    outflows=outflows.get(period, 0.0),
                    net_cashflow=inflows.get(period, 0.0) - outflows.get(period, 0.0),
                    profit=profit,
                    margin=margin,
                )
            )
        return CashflowResponse(rows=rows, available=True, meta=ResponseMeta())

    def get_financial_risks(
        self,
        *,
        region: list[str] | None = None,
        department: list[str] | None = None,
        search: str | None = None,
    ) -> FinancialRisksResponse:
        profitability = self.get_profitability(region=region, search=search)
        costs = self.get_cost_breakdown(region=region, search=search)
        budget = self.get_budget_variance(department=department, search=search)
        overview = self.get_overview(region=region, search=search)

        risks: list[FinancialRiskRow] = []

        for row in profitability.rows:
            if row.margin is not None and row.margin < 0.15:
                risks.append(
                    FinancialRiskRow(
                        risk=f"Low margin in {row.region}",
                        severity="high" if row.margin < 0.05 else "medium",
                        estimated_impact=row.profit,
                        owner="Finance / Regional Ops",
                        recommendation="Review pricing, mix, and COGS for the region.",
                    )
                )
            if row.growth is not None and row.growth < -0.1:
                risks.append(
                    FinancialRiskRow(
                        risk=f"Revenue contraction in {row.region}",
                        severity="high",
                        estimated_impact=row.revenue,
                        owner="Commercial Finance",
                        recommendation="Investigate demand and discounting pressure in the region.",
                    )
                )

        for row in costs.rows:
            if row.trend == "up" and (row.percentage or 0) >= 0.3:
                risks.append(
                    FinancialRiskRow(
                        risk=f"Rising {row.cost_category} share",
                        severity="medium",
                        estimated_impact=row.amount,
                        owner="Cost Controllers",
                        recommendation=f"Contain {row.cost_category} growth versus prior period.",
                    )
                )

        for row in budget.rows:
            if row.variance_pct is not None and row.variance_pct > 0.1:
                risks.append(
                    FinancialRiskRow(
                        risk=f"Budget overrun: {row.department}",
                        severity="critical" if row.variance_pct > 0.25 else "high",
                        estimated_impact=row.variance,
                        owner="FP&A",
                        recommendation="Re-forecast spend and enforce budget controls.",
                    )
                )

        margin = next((m for m in overview.metrics if m.id == "profit_margin"), None)
        if margin and margin.available and margin.value is not None and margin.value < 0.2:
            risks.append(
                FinancialRiskRow(
                    risk="Enterprise margin below 20%",
                    severity="medium",
                    estimated_impact=None,
                    owner="CFO Office",
                    recommendation="Prioritize margin expansion initiatives across regions.",
                )
            )

        if search:
            risks = [r for r in risks if search.lower() in r.risk.lower()]

        if not risks:
            return FinancialRisksResponse(rows=[], available=False, meta=ResponseMeta())
        return FinancialRisksResponse(rows=risks[:20], available=True, meta=ResponseMeta())

    def get_budget_variance(
        self,
        *,
        department: list[str] | None = None,
        search: str | None = None,
    ) -> BudgetVarianceResponse:
        try:
            rows = self.finance.get_campaign_rows(
                AnalyticsQuery(page_size=500, sort_by="actual_spend", sort_dir="desc", search=search)
            )
        except Exception:  # noqa: BLE001
            return BudgetVarianceResponse(rows=[], available=False, meta=ResponseMeta())

        if not rows:
            return BudgetVarianceResponse(rows=[], available=False, meta=ResponseMeta())

        wanted = {d.lower() for d in department} if department else None
        # Roll up by campaign_type as department grain (budget exists on campaigns)
        buckets: dict[str, dict[str, float]] = {}
        for row in rows:
            dept = str(row.get("campaign_type") or row.get("objective_code") or "Unassigned")
            if wanted and dept.lower() not in wanted:
                continue
            if search and search.lower() not in dept.lower() and search.lower() not in str(row.get("campaign_name") or "").lower():
                continue
            bucket = buckets.setdefault(dept, {"budget": 0.0, "actual": 0.0})
            bucket["budget"] += _as_float(row.get("budget_amount")) or 0.0
            bucket["actual"] += _as_float(row.get("actual_spend")) or 0.0

        if not buckets:
            return BudgetVarianceResponse(rows=[], available=False, meta=ResponseMeta())

        result = []
        for name, values in sorted(buckets.items(), key=lambda item: item[1]["actual"], reverse=True):
            budget = values["budget"]
            actual = values["actual"]
            variance = actual - budget
            variance_pct = (variance / budget) if budget else None
            result.append(
                BudgetVarianceRow(
                    department=name,
                    budget=budget,
                    actual=actual,
                    variance=variance,
                    variance_pct=variance_pct,
                )
            )
        return BudgetVarianceResponse(rows=result, available=True, meta=ResponseMeta())

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
    ) -> FinanceMetric:
        return FinanceMetric(
            id=id,
            label=label,
            value=value,
            formatted_value=formatted,
            unit=unit,
            format=fmt,
            available=available,
            source="sales_summary",
        )

    @staticmethod
    def _dated(rows: list[dict], key: str) -> list[tuple[date, dict]]:
        dated: list[tuple[date, dict]] = []
        for row in rows:
            d = _coerce_date(row.get(key))
            if d is not None:
                dated.append((d, row))
        dated.sort(key=lambda item: item[0])
        return dated

    def _safe_sales(
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
        try:
            return self.finance.get_sales_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="order_date",
                    sort_dir="asc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="order_date",
                    search=search,
                    filters=filters,
                )
            )
        except Exception:  # noqa: BLE001
            return []

    def _safe_scorecard(self, *, date_from: date | None, date_to: date | None) -> list[dict]:
        try:
            return self.finance.get_scorecard_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="order_date",
                    sort_dir="asc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="order_date",
                )
            )
        except Exception:  # noqa: BLE001
            return []

    def _safe_payments(self, *, date_from: date | None, date_to: date | None) -> list[dict]:
        try:
            return self.finance.get_payment_rows(
                AnalyticsQuery(
                    page_size=500,
                    sort_by="payment_month",
                    sort_dir="asc",
                    date_from=date_from,
                    date_to=date_to,
                    date_column="payment_month",
                )
            )
        except Exception:  # noqa: BLE001
            return []

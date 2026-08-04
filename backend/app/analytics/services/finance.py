"""Finance analytics orchestration (read-only view access)."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage, KpiCard, SummaryMetrics


class FinanceAnalyticsService(AnalyticsServiceBase):
    """
    Finance reads composition of sales + executive scorecard + payment + campaign views.
    No local financial calculations beyond repository SUM aggregates / orchestrator rollups.
    """

    def get_margin_summary_table(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.SALES_SUMMARY, query or AnalyticsQuery())

    def get_sales_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.SALES_SUMMARY, q)
        return rows

    def get_profit_summary(self, query: AnalyticsQuery | None = None) -> SummaryMetrics:
        return self.build_summary(
            AnalyticsViewKey.SALES_SUMMARY,
            query or AnalyticsQuery(),
            ["gross_sales", "net_sales", "cogs_amount", "gross_profit", "discount_amount"],
        )

    def get_finance_kpi_cards(self, query: AnalyticsQuery | None = None) -> list[KpiCard]:
        summary = self.get_profit_summary(query)
        m = summary.metrics
        return [
            self.metric_to_kpi(id="gross_sales", title="Gross Sales", value=m.get("gross_sales"), format="currency"),
            self.metric_to_kpi(id="cogs", title="COGS", value=m.get("cogs_amount"), format="currency"),
            self.metric_to_kpi(id="gross_profit", title="Gross Profit", value=m.get("gross_profit"), format="currency"),
            self.metric_to_kpi(id="discounts", title="Discounts", value=m.get("discount_amount"), format="currency"),
        ]

    def get_executive_finance_slice(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.EXECUTIVE_SCORECARD, query or AnalyticsQuery())

    def get_scorecard_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.EXECUTIVE_SCORECARD, q)
        return rows

    def get_payment_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="payment_month", sort_dir="asc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.PAYMENT_MIX, q)
        return rows

    def get_campaign_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_net_sales", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.CAMPAIGN_PERFORMANCE, q)
        return rows

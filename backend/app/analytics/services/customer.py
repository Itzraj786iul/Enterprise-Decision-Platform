"""Customer analytics orchestration (read-only)."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage, SummaryMetrics


class CustomerAnalyticsService(AnalyticsServiceBase):
    def get_customer_360(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.CUSTOMER_360, query or AnalyticsQuery())

    def get_customer_360_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="lifetime_net_sales", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.CUSTOMER_360, q)
        return rows

    def get_customer_rfm(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.CUSTOMER_RFM, query or AnalyticsQuery())

    def get_customer_rfm_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="rfm_total", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.CUSTOMER_RFM, q)
        return rows

    def get_customer_value_summary(self, query: AnalyticsQuery | None = None) -> SummaryMetrics:
        return self.build_summary(
            AnalyticsViewKey.CUSTOMER_360,
            query or AnalyticsQuery(),
            ["lifetime_net_sales", "lifetime_gross_profit", "order_count", "lifetime_units"],
        )

"""Operations analytics orchestration (read-only)."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage


class OperationsAnalyticsService(AnalyticsServiceBase):
    def get_inventory_summary(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.INVENTORY_SUMMARY, query or AnalyticsQuery())

    def get_inventory_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="inventory_value_cost", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.INVENTORY_SUMMARY, q)
        return rows

    def get_supplier_performance(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.SUPPLIER_PERFORMANCE, query or AnalyticsQuery())

    def get_supplier_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="on_time_rate", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.SUPPLIER_PERFORMANCE, q)
        return rows

    def get_return_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="return_date", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.FACT_RETURN_LINE, q)
        return rows

    def get_shipment_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="desc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.SHIPMENT_PERFORMANCE, q)
        return rows

    def get_campaign_performance(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.CAMPAIGN_PERFORMANCE, query or AnalyticsQuery())

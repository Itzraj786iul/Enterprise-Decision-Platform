"""Sales analytics orchestration (read-only)."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import (
    AnalyticsTablePage,
    KpiCard,
    SummaryMetrics,
    TimeSeriesResponse,
    TrendSeries,
)


class SalesAnalyticsService(AnalyticsServiceBase):
    def get_sales_summary(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.SALES_SUMMARY, query or AnalyticsQuery())

    def get_sales_summary_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.SALES_SUMMARY, q)
        return rows

    def get_sales_trends(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(AnalyticsViewKey.SALES_TRENDS, query or AnalyticsQuery())

    def get_sales_line_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        rows, _ = self.query_rows(AnalyticsViewKey.FACT_SALES_LINE, q)
        return rows

    def get_product_category_map(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        q = query or AnalyticsQuery(page_size=500, sort_by="product_name", sort_dir="asc")
        return self.query_table(AnalyticsViewKey.PRODUCT_CATEGORY_MAP, q)

    def get_product_category_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(page_size=500, sort_by="product_name", sort_dir="asc")
        rows, _ = self.query_rows(AnalyticsViewKey.PRODUCT_CATEGORY_MAP, q)
        return rows

    def get_sales_summary_metrics(self, query: AnalyticsQuery | None = None) -> SummaryMetrics:
        return self.build_summary(
            AnalyticsViewKey.SALES_SUMMARY,
            query or AnalyticsQuery(),
            ["net_sales", "gross_sales", "gross_profit", "order_count", "units_sold"],
        )

    def get_sales_kpi_cards(self, query: AnalyticsQuery | None = None) -> list[KpiCard]:
        summary = self.get_sales_summary_metrics(query)
        m = summary.metrics
        return [
            self.metric_to_kpi(id="net_sales", title="Net Sales", value=m.get("net_sales"), format="currency"),
            self.metric_to_kpi(id="gross_profit", title="Gross Profit", value=m.get("gross_profit"), format="currency"),
            self.metric_to_kpi(id="orders", title="Orders", value=m.get("order_count"), format="number"),
            self.metric_to_kpi(id="units", title="Units Sold", value=m.get("units_sold"), format="number"),
        ]

    def get_net_sales_time_series(self, query: AnalyticsQuery | None = None) -> TimeSeriesResponse:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=365)
        validated_rows, _ = self.query_rows(AnalyticsViewKey.SALES_SUMMARY, q)
        series: TrendSeries = self.rows_to_trend(
            validated_rows,
            series_id="net_sales",
            series_name="Net Sales",
            x_key="order_date",
            y_key="net_sales",
            unit="USD",
        )
        return TimeSeriesResponse(series=[series], grain="day")

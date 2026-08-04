"""Executive analytics orchestration (read-only)."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage, TimeSeriesResponse


class ExecutiveAnalyticsService(AnalyticsServiceBase):
    def get_scorecard(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=366)
        return self.query_table(AnalyticsViewKey.EXECUTIVE_SCORECARD, q)

    def get_scorecard_rows(self, query: AnalyticsQuery | None = None) -> list[dict]:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=366)
        rows, _ = self.query_rows(AnalyticsViewKey.EXECUTIVE_SCORECARD, q)
        return rows

    def get_commercial_detail(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        """
        Store/channel grain used for executive regional rollups.
        Still read-only analytics views via existing repository stack.
        """
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=500)
        return self.query_table(AnalyticsViewKey.SALES_SUMMARY, q)

    def get_scorecard_trend(self, query: AnalyticsQuery | None = None) -> TimeSeriesResponse:
        q = query or AnalyticsQuery(sort_by="order_date", sort_dir="asc", page_size=366)
        rows, _ = self.query_rows(AnalyticsViewKey.EXECUTIVE_SCORECARD, q)
        x_key = (
            "order_date"
            if rows and "order_date" in rows[0]
            else ("kpi_date" if rows and "kpi_date" in rows[0] else None)
        )
        if not x_key:
            return TimeSeriesResponse(series=[], grain="day")

        series = []
        for series_id, y_key, name, unit in (
            ("revenue", "net_sales", "Revenue", "USD"),
            ("profit", "gross_profit", "Profit", "USD"),
            ("orders", "order_count", "Orders", "count"),
        ):
            if rows and y_key in rows[0]:
                series.append(
                    self.rows_to_trend(
                        rows,
                        series_id=series_id,
                        series_name=name,
                        x_key=x_key,
                        y_key=y_key,
                        unit=unit,
                    )
                )
        return TimeSeriesResponse(series=series, grain="day")

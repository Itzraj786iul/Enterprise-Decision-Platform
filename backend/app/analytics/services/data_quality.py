"""Data quality analytics — read-only."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage


class DataQualityService(AnalyticsServiceBase):
    def get_quality_summary(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(
            AnalyticsViewKey.DATA_QUALITY_SUMMARY,
            query or AnalyticsQuery(),
        )

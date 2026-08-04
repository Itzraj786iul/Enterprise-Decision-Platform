"""Machine learning predictions — read-only view access, no inference."""

from __future__ import annotations

from app.analytics.config import AnalyticsViewKey
from app.analytics.query import AnalyticsQuery
from app.analytics.services.base import AnalyticsServiceBase
from app.schemas.analytics import AnalyticsTablePage


class MachineLearningService(AnalyticsServiceBase):
    """Reads persisted prediction rows from analytics views only."""

    def get_predictions(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        return self.query_table(
            AnalyticsViewKey.MACHINE_LEARNING_PREDICTIONS,
            query or AnalyticsQuery(),
        )

    def stream_predictions(self, query: AnalyticsQuery | None = None):
        return self.stream_rows(
            AnalyticsViewKey.MACHINE_LEARNING_PREDICTIONS,
            query or AnalyticsQuery(),
        )

"""Analytics repository factories bound to logical view keys."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.analytics.config import AnalyticsViewKey, AnalyticsViewRegistry
from app.analytics.repositories.view_repository import AnalyticsViewRepository


class AnalyticsRepositoryFactory:
    def __init__(
        self,
        session: Session,
        registry: AnalyticsViewRegistry | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or AnalyticsViewRegistry()

    def for_view(self, key: AnalyticsViewKey | str) -> AnalyticsViewRepository:
        definition = self.registry.get(key)
        return AnalyticsViewRepository(self.session, definition)

    def sales_summary(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.SALES_SUMMARY)

    def sales_trends(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.SALES_TRENDS)

    def customer_360(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.CUSTOMER_360)

    def customer_rfm(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.CUSTOMER_RFM)

    def inventory_summary(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.INVENTORY_SUMMARY)

    def supplier_performance(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.SUPPLIER_PERFORMANCE)

    def campaign_performance(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.CAMPAIGN_PERFORMANCE)

    def executive_scorecard(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.EXECUTIVE_SCORECARD)

    def machine_learning_predictions(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.MACHINE_LEARNING_PREDICTIONS)

    def data_quality_summary(self) -> AnalyticsViewRepository:
        return self.for_view(AnalyticsViewKey.DATA_QUALITY_SUMMARY)

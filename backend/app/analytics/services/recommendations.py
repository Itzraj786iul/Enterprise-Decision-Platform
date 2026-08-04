"""Recommendation service interface — no implementation yet."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.analytics.query import AnalyticsQuery
from app.schemas.analytics import AnalyticsTablePage


class RecommendationService(ABC):
    """
    Interface-only placeholder for future decision recommendations.
    Must not embed business rules in this phase.
    """

    @abstractmethod
    def list_recommendations(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        raise NotImplementedError

    @abstractmethod
    def get_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        raise NotImplementedError


class UnimplementedRecommendationService(RecommendationService):
    """Concrete stub that signals the feature is not wired."""

    def list_recommendations(self, query: AnalyticsQuery | None = None) -> AnalyticsTablePage:
        raise NotImplementedError("RecommendationService is interface-only in this phase")

    def get_recommendation(self, recommendation_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("RecommendationService is interface-only in this phase")

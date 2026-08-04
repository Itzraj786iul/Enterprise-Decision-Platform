"""Shared analytics service helpers."""

from __future__ import annotations

from typing import Any

from app.analytics.caching import AnalyticsCache, NullCache, build_cache_key
from app.analytics.config import AnalyticsViewDefinition, AnalyticsViewKey, AnalyticsViewRegistry
from app.analytics.query import AnalyticsQuery, total_pages, validate_query_against_view
from app.analytics.repositories.factory import AnalyticsRepositoryFactory
from app.analytics.repositories.view_repository import AnalyticsViewRepository
from app.schemas.analytics import (
    AnalyticsTablePage,
    KpiCard,
    SummaryMetrics,
    TableColumn,
    TableResult,
    TrendPoint,
    TrendSeries,
)
from app.schemas.common import PaginationMeta, ResponseMeta


class AnalyticsServiceBase:
    """Orchestrates validated reads through repositories. Contains no SQL."""

    def __init__(
        self,
        factory: AnalyticsRepositoryFactory,
        *,
        registry: AnalyticsViewRegistry | None = None,
        cache: AnalyticsCache | None = None,
        cache_ttl_seconds: int = 60,
    ) -> None:
        self.factory = factory
        self.registry = registry or factory.registry
        self.cache: AnalyticsCache = cache or NullCache()
        self.cache_ttl_seconds = cache_ttl_seconds

    def _repo(self, key: AnalyticsViewKey) -> AnalyticsViewRepository:
        return self.factory.for_view(key)

    def _view(self, key: AnalyticsViewKey) -> AnalyticsViewDefinition:
        return self.registry.get(key)

    def _validated(self, key: AnalyticsViewKey, query: AnalyticsQuery) -> AnalyticsQuery:
        return validate_query_against_view(query, self._view(key))

    def _cache_get(self, prefix: str, payload: dict[str, Any]) -> Any | None:
        return self.cache.get(build_cache_key(prefix, payload))

    def _cache_set(self, prefix: str, payload: dict[str, Any], value: Any) -> None:
        self.cache.set(build_cache_key(prefix, payload), value, self.cache_ttl_seconds)

    def query_table(self, key: AnalyticsViewKey, query: AnalyticsQuery) -> AnalyticsTablePage:
        validated = self._validated(key, query)
        cache_payload = {"view": key.value, "query": validated.model_dump(mode="json")}
        cached = self._cache_get(f"{key.value}:table", cache_payload)
        if cached is not None:
            return AnalyticsTablePage.model_validate(cached)

        repo = self._repo(key)
        rows, total = repo.fetch_page(validated)
        columns = [
            TableColumn(key=name, label=name.replace("_", " ").title())
            for name in (validated.columns or (rows[0].keys() if rows else []))
        ]
        page = AnalyticsTablePage(
            table=TableResult(columns=columns, rows=rows),
            pagination=PaginationMeta(
                page=validated.page,
                page_size=validated.page_size,
                total_items=total,
                total_pages=total_pages(total, validated.page_size),
            ),
            meta=ResponseMeta(),
        )
        self._cache_set(f"{key.value}:table", cache_payload, page.model_dump(mode="json"))
        return page

    def query_rows(self, key: AnalyticsViewKey, query: AnalyticsQuery) -> tuple[list[dict], int]:
        validated = self._validated(key, query)
        return self._repo(key).fetch_page(validated)

    def stream_rows(self, key: AnalyticsViewKey, query: AnalyticsQuery, **kwargs: Any):
        validated = self._validated(key, query)
        return self._repo(key).stream(validated, **kwargs)

    def build_summary(
        self,
        key: AnalyticsViewKey,
        query: AnalyticsQuery,
        metric_columns: list[str],
    ) -> SummaryMetrics:
        validated = self._validated(key, query)
        metrics = self._repo(key).summarize_numeric(validated, metric_columns)
        return SummaryMetrics(metrics=metrics)

    @staticmethod
    def rows_to_trend(
        rows: list[dict[str, Any]],
        *,
        series_id: str,
        series_name: str,
        x_key: str,
        y_key: str,
        unit: str | None = None,
    ) -> TrendSeries:
        points = [
            TrendPoint(x=row.get(x_key), y=row.get(y_key), dimensions={k: v for k, v in row.items() if k not in {x_key, y_key}})
            for row in rows
        ]
        return TrendSeries(id=series_id, name=series_name, unit=unit, points=points)

    @staticmethod
    def metric_to_kpi(
        *,
        id: str,
        title: str,
        value: float | int | str | None,
        unit: str | None = None,
        format: str | None = None,
    ) -> KpiCard:
        return KpiCard(id=id, title=title, value=value, unit=unit, format=format)

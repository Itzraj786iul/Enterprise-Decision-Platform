"""Analytics repository tests against local SQLite stand-ins (no writes to OLTP)."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import Column, Date, Float, Integer, MetaData, String, Table, create_engine, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.analytics.config import AnalyticsViewDefinition, AnalyticsViewKey
from app.analytics.query import (
    AnalyticsQuery,
    FilterClause,
    FilterOperator,
    validate_query_against_view,
)
from app.analytics.repositories.view_repository import AnalyticsViewRepository


@pytest.fixture()
def sqlite_sales_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    metadata = MetaData()
    table = Table(
        "vw_sales_daily",
        metadata,
        Column("order_date", Date),
        Column("store_code", String),
        Column("store_name", String),
        Column("channel_name", String),
        Column("net_sales", Float),
        Column("gross_sales", Float),
        Column("order_count", Integer),
        Column("units_sold", Integer),
        Column("gross_profit", Float),
    )
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            insert(table),
            [
                {
                    "order_date": date(2024, 1, 1),
                    "store_code": "S1",
                    "store_name": "Alpha",
                    "channel_name": "In-store",
                    "net_sales": 100.0,
                    "gross_sales": 120.0,
                    "order_count": 2,
                    "units_sold": 5,
                    "gross_profit": 40.0,
                },
                {
                    "order_date": date(2024, 1, 2),
                    "store_code": "S2",
                    "store_name": "Beta",
                    "channel_name": "Online",
                    "net_sales": 250.0,
                    "gross_sales": 300.0,
                    "order_count": 4,
                    "units_sold": 10,
                    "gross_profit": 90.0,
                },
                {
                    "order_date": date(2024, 1, 3),
                    "store_code": "S1",
                    "store_name": "Alpha",
                    "channel_name": "Online",
                    "net_sales": 80.0,
                    "gross_sales": 90.0,
                    "order_count": 1,
                    "units_sold": 2,
                    "gross_profit": 20.0,
                },
            ],
        )
    factory = sessionmaker(bind=engine, autoflush=False, future=True)
    session = factory()
    yield session
    session.close()
    engine.dispose()


def _sales_view() -> AnalyticsViewDefinition:
    return AnalyticsViewDefinition(
        key=AnalyticsViewKey.SALES_SUMMARY,
        schema=None,  # type: ignore[arg-type]
        name="vw_sales_daily",
        date_columns=("order_date",),
        searchable_columns=("store_code", "store_name", "channel_name"),
        sortable_columns=("order_date", "net_sales", "order_count"),
        default_sort="order_date",
        allowed_columns=(
            "order_date",
            "store_code",
            "store_name",
            "channel_name",
            "net_sales",
            "gross_sales",
            "order_count",
            "units_sold",
            "gross_profit",
        ),
    )


def test_repository_filter_sort_pagination(sqlite_sales_session) -> None:
    view = _sales_view()
    # SQLAlchemy Table with schema=None
    view = AnalyticsViewDefinition(
        key=view.key,
        schema=None,  # type: ignore[arg-type]
        name=view.name,
        date_columns=view.date_columns,
        searchable_columns=view.searchable_columns,
        sortable_columns=view.sortable_columns,
        default_sort=view.default_sort,
        allowed_columns=view.allowed_columns,
    )
    repo = AnalyticsViewRepository(sqlite_sales_session, view)
    query = validate_query_against_view(
        AnalyticsQuery(
            page=1,
            page_size=10,
            sort_by="net_sales",
            sort_dir="desc",
            filters=[FilterClause(column="store_code", op=FilterOperator.EQ, value="S1")],
        ),
        view,
    )
    rows, total = repo.fetch_page(query)
    assert total == 2
    assert rows[0]["net_sales"] == 100.0
    assert all(r["store_code"] == "S1" for r in rows)


def test_repository_date_range_and_projection(sqlite_sales_session) -> None:
    view = _sales_view()
    repo = AnalyticsViewRepository(sqlite_sales_session, view)
    query = validate_query_against_view(
        AnalyticsQuery(
            date_from=date(2024, 1, 2),
            date_to=date(2024, 1, 3),
            columns=["order_date", "net_sales"],
            sort_by="order_date",
            sort_dir="asc",
        ),
        view,
    )
    rows = repo.fetch(query)
    assert len(rows) == 2
    assert set(rows[0].keys()) == {"order_date", "net_sales"}


def test_repository_search(sqlite_sales_session) -> None:
    view = _sales_view()
    repo = AnalyticsViewRepository(sqlite_sales_session, view)
    query = validate_query_against_view(
        AnalyticsQuery(search="Beta", sort_by="order_date"),
        view,
    )
    rows, total = repo.fetch_page(query)
    assert total == 1
    assert rows[0]["store_name"] == "Beta"


def test_repository_stream_and_summary(sqlite_sales_session) -> None:
    view = _sales_view()
    repo = AnalyticsViewRepository(sqlite_sales_session, view)
    query = validate_query_against_view(AnalyticsQuery(sort_by="order_date"), view)
    streamed = list(repo.stream(query, max_rows=10))
    assert len(streamed) == 3
    summary = repo.summarize_numeric(query, ["net_sales", "order_count"])
    assert summary["net_sales"] == pytest.approx(430.0)
    assert summary["order_count"] == pytest.approx(7.0)

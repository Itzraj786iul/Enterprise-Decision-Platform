"""Feature registry tests."""

from __future__ import annotations

from app.auth.models import Permission
from app.platform.feature_registry import (
    FEATURE_REGISTRY,
    feature_for_api_path,
    get_feature,
    list_features,
    required_permissions_for_path,
)


def test_registry_contains_core_modules() -> None:
    ids = {f.id for f in FEATURE_REGISTRY}
    assert {"dashboard", "sales", "customers", "finance", "operations", "settings"} <= ids


def test_unavailable_modules_flagged() -> None:
    unavailable = {f.id for f in FEATURE_REGISTRY if not f.available}
    assert {"analytics", "predictions", "recommendations", "reports"} <= unavailable


def test_list_features_available_only() -> None:
    available = list_features(available_only=True)
    assert all(f.available for f in available)
    assert get_feature("analytics") is not None
    assert get_feature("analytics") not in available


def test_feature_for_api_path() -> None:
    feature = feature_for_api_path("/api/v1/sales/overview")
    assert feature is not None
    assert feature.id == "sales"


def test_required_permissions_for_path() -> None:
    required = required_permissions_for_path("/api/v1/finance/kpis")
    assert Permission.FINANCE_READ in required


def test_unknown_path_requires_nothing() -> None:
    assert required_permissions_for_path("/api/v1/unknown") == ()


def test_each_available_feature_has_permissions_and_route() -> None:
    for feature in list_features(available_only=True):
        assert feature.route.startswith("/")
        assert feature.permissions
        assert feature.navigation_label
        assert feature.icon

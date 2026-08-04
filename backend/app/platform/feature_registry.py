"""Central feature registry for analytics modules and platform surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.auth.models import Permission


FilterKey = Literal["date", "region", "category", "customer", "product", "segment", "department", "supplier", "search"]


@dataclass(frozen=True)
class FeatureDefinition:
    id: str
    route: str
    api_prefix: str | None
    navigation_label: str
    icon: str
    permissions: tuple[Permission, ...]
    supported_filters: tuple[FilterKey, ...] = ()
    export_support: bool = False
    available: bool = True
    section: str = "main"
    description: str = ""
    keywords: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


FEATURE_REGISTRY: tuple[FeatureDefinition, ...] = (
    FeatureDefinition(
        id="dashboard",
        route="/dashboard",
        api_prefix="/api/v1/dashboard",
        navigation_label="Dashboard",
        icon="LayoutDashboard",
        permissions=(Permission.DASHBOARD_READ,),
        supported_filters=("date",),
        export_support=False,
        available=True,
        description="Executive performance overview",
        keywords=("home", "overview"),
        tags=("executive",),
    ),
    FeatureDefinition(
        id="sales",
        route="/sales",
        api_prefix="/api/v1/sales",
        navigation_label="Sales Intelligence",
        icon="ShoppingCart",
        permissions=(Permission.SALES_READ,),
        supported_filters=("date", "region", "category", "search"),
        export_support=True,
        available=True,
        description="Commercial revenue and product performance",
        keywords=("revenue", "orders"),
        tags=("sales",),
    ),
    FeatureDefinition(
        id="customers",
        route="/customers",
        api_prefix="/api/v1/customers",
        navigation_label="Customer Intelligence",
        icon="Users",
        permissions=(Permission.CUSTOMERS_READ,),
        supported_filters=("date", "region", "segment", "search"),
        export_support=True,
        available=True,
        description="Lifecycle, RFM, cohorts, and churn",
        keywords=("segment", "churn"),
        tags=("customers",),
    ),
    FeatureDefinition(
        id="finance",
        route="/finance",
        api_prefix="/api/v1/finance",
        navigation_label="Finance Intelligence",
        icon="Wallet",
        permissions=(Permission.FINANCE_READ,),
        supported_filters=("date", "region", "department", "category", "search"),
        export_support=True,
        available=True,
        description="Profitability, costs, cashflow, and budget",
        keywords=("margin", "profit"),
        tags=("finance",),
    ),
    FeatureDefinition(
        id="operations",
        route="/operations",
        api_prefix="/api/v1/operations",
        navigation_label="Operations Intelligence",
        icon="Package",
        permissions=(Permission.OPERATIONS_READ,),
        supported_filters=("date", "region", "category", "supplier", "search"),
        export_support=True,
        available=True,
        description="Inventory, suppliers, returns, and warehouses",
        keywords=("inventory", "fulfillment"),
        tags=("operations",),
    ),
    FeatureDefinition(
        id="analytics",
        route="/analytics",
        api_prefix=None,
        navigation_label="Analytics",
        icon="BarChart3",
        permissions=(Permission.ANALYTICS_READ,),
        supported_filters=("date", "search"),
        export_support=False,
        available=False,
        description="Cross-module analytics explorer (coming soon)",
        keywords=("explore", "insights"),
        tags=("analytics",),
    ),
    FeatureDefinition(
        id="predictions",
        route="/predictions",
        api_prefix=None,
        navigation_label="AI Predictions",
        icon="Brain",
        permissions=(Permission.ML_READ,),
        supported_filters=("date", "search"),
        export_support=False,
        available=False,
        description="Machine learning predictions (coming soon)",
        keywords=("ml", "forecast", "models"),
        tags=("ml",),
    ),
    FeatureDefinition(
        id="recommendations",
        route="/recommendations",
        api_prefix=None,
        navigation_label="Business Recommendations",
        icon="Sparkles",
        permissions=(Permission.ANALYTICS_READ,),
        export_support=False,
        available=False,
        description="Decision recommendations (coming soon)",
        keywords=("decisions", "actions"),
        tags=("recommendations",),
    ),
    FeatureDefinition(
        id="reports",
        route="/reports",
        api_prefix=None,
        navigation_label="Reports",
        icon="FileText",
        permissions=(Permission.REPORTS_READ,),
        export_support=True,
        available=False,
        description="Report center (coming soon)",
        keywords=("export", "pdf"),
        tags=("reports",),
    ),
    FeatureDefinition(
        id="settings",
        route="/settings",
        api_prefix=None,
        navigation_label="Settings",
        icon="Settings",
        permissions=(Permission.SETTINGS_READ,),
        available=True,
        section="system",
        description="Workspace preferences",
        keywords=("preferences", "profile"),
        tags=("system",),
    ),
)


def list_features(*, available_only: bool = False) -> list[FeatureDefinition]:
    features = list(FEATURE_REGISTRY)
    if available_only:
        features = [f for f in features if f.available]
    return features


def get_feature(feature_id: str) -> FeatureDefinition | None:
    for feature in FEATURE_REGISTRY:
        if feature.id == feature_id:
            return feature
    return None


def feature_for_api_path(path: str) -> FeatureDefinition | None:
    matches = [
        f
        for f in FEATURE_REGISTRY
        if f.api_prefix and (path == f.api_prefix or path.startswith(f"{f.api_prefix}/"))
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda f: len(f.api_prefix or ""), reverse=True)[0]


def required_permissions_for_path(path: str) -> tuple[Permission, ...]:
    feature = feature_for_api_path(path)
    if feature is None:
        return ()
    return feature.permissions

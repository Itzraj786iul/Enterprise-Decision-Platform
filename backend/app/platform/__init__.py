"""Platform package."""

from app.platform.feature_registry import (
    FEATURE_REGISTRY,
    FeatureDefinition,
    feature_for_api_path,
    get_feature,
    list_features,
    required_permissions_for_path,
)

__all__ = [
    "FEATURE_REGISTRY",
    "FeatureDefinition",
    "feature_for_api_path",
    "get_feature",
    "list_features",
    "required_permissions_for_path",
]

"""Logical analytics view catalog — decoupled from physical PostgreSQL names."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.core.config import Settings, get_settings


class AnalyticsViewKey(str, Enum):
    """Stable logical keys used by services (not physical DB names)."""

    SALES_SUMMARY = "sales_summary"
    SALES_TRENDS = "sales_trends"
    FACT_SALES_LINE = "fact_sales_line"
    PRODUCT_CATEGORY_MAP = "product_category_map"
    CUSTOMER_360 = "customer_360"
    CUSTOMER_RFM = "customer_rfm"
    INVENTORY_SUMMARY = "inventory_summary"
    SUPPLIER_PERFORMANCE = "supplier_performance"
    FACT_RETURN_LINE = "fact_return_line"
    SHIPMENT_PERFORMANCE = "shipment_performance"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    PAYMENT_MIX = "payment_mix"
    EXECUTIVE_SCORECARD = "executive_scorecard"
    MACHINE_LEARNING_PREDICTIONS = "machine_learning_predictions"
    DATA_QUALITY_SUMMARY = "data_quality_summary"


@dataclass(frozen=True)
class AnalyticsViewDefinition:
    key: AnalyticsViewKey
    schema: str | None
    name: str
    """Physical relation name (view) inside the analytics schema."""

    date_columns: tuple[str, ...] = ()
    searchable_columns: tuple[str, ...] = ()
    sortable_columns: tuple[str, ...] = ()
    default_sort: str | None = None
    description: str = ""
    allowed_columns: tuple[str, ...] = field(default_factory=tuple)
    """
    When non-empty, column projection / filters / sort must be within this set.
    Empty means 'defer to reflected columns at runtime'.
    """

    @property
    def qualified_name(self) -> str:
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name


def default_view_catalog(schema: str = "analytics") -> dict[AnalyticsViewKey, AnalyticsViewDefinition]:
    """
    Maps logical keys → existing analytics.* views.
    Physical names can be overridden via Settings without changing services.
    """
    return {
        AnalyticsViewKey.SALES_SUMMARY: AnalyticsViewDefinition(
            key=AnalyticsViewKey.SALES_SUMMARY,
            schema=schema,
            name="vw_sales_daily",
            date_columns=("order_date",),
            searchable_columns=("store_code", "store_name", "region_name", "channel_name"),
            sortable_columns=(
                "order_date",
                "net_sales",
                "gross_sales",
                "order_count",
                "units_sold",
                "gross_profit",
            ),
            default_sort="order_date",
            description="Daily sales summary by store and channel",
            allowed_columns=(
                "order_date",
                "year_number",
                "quarter_number",
                "month_number",
                "store_id",
                "store_code",
                "store_name",
                "store_format",
                "region_id",
                "region_code",
                "region_name",
                "channel_id",
                "channel_code",
                "channel_name",
                "order_count",
                "units_sold",
                "gross_sales",
                "discount_amount",
                "net_sales",
                "cogs_amount",
                "gross_profit",
            ),
        ),
        AnalyticsViewKey.SALES_TRENDS: AnalyticsViewDefinition(
            key=AnalyticsViewKey.SALES_TRENDS,
            schema=schema,
            name="vw_sales_monthly",
            date_columns=(),  # monthly grain uses year/month — optional date filter via columns
            searchable_columns=("store_code", "channel_code"),
            sortable_columns=("year_number", "month_number", "net_sales", "order_count"),
            default_sort="year_number",
            description="Monthly sales trends",
            allowed_columns=(
                "year_number",
                "month_number",
                "store_id",
                "store_code",
                "channel_id",
                "channel_code",
                "order_count",
                "units_sold",
                "gross_sales",
                "discount_amount",
                "net_sales",
                "cogs_amount",
                "gross_profit",
            ),
        ),
        AnalyticsViewKey.FACT_SALES_LINE: AnalyticsViewDefinition(
            key=AnalyticsViewKey.FACT_SALES_LINE,
            schema=schema,
            name="vw_fact_sales_line",
            date_columns=("order_date",),
            searchable_columns=("order_number",),
            sortable_columns=(
                "order_date",
                "line_net_amount",
                "line_gross_profit",
                "quantity",
                "product_id",
            ),
            default_sort="order_date",
            description="Sales line fact for product / category rollups",
            allowed_columns=(
                "order_item_id",
                "order_id",
                "order_number",
                "order_date",
                "customer_id",
                "store_id",
                "channel_id",
                "product_id",
                "quantity",
                "discount_amount",
                "line_gross_amount",
                "line_net_amount",
                "line_cogs_amount",
                "line_gross_profit",
                "line_margin_pct",
                "year_number",
                "quarter_number",
                "month_number",
                "week_of_year",
            ),
        ),
        AnalyticsViewKey.PRODUCT_CATEGORY_MAP: AnalyticsViewDefinition(
            key=AnalyticsViewKey.PRODUCT_CATEGORY_MAP,
            schema=schema,
            name="vw_product_category_map",
            date_columns=(),
            searchable_columns=("sku", "product_name", "category_name", "brand_name"),
            sortable_columns=("product_id", "sku", "product_name", "category_name"),
            default_sort="product_name",
            description="Product to L1/L2 category attributes",
            allowed_columns=(
                "product_id",
                "sku",
                "product_name",
                "brand_name",
                "is_active",
                "current_list_price",
                "current_unit_cost",
                "primary_supplier_id",
                "subcategory_id",
                "subcategory_code",
                "subcategory_name",
                "category_id",
                "category_code",
                "category_name",
            ),
        ),
        AnalyticsViewKey.CUSTOMER_360: AnalyticsViewDefinition(
            key=AnalyticsViewKey.CUSTOMER_360,
            schema=schema,
            name="vw_customer_360",
            date_columns=("registration_date", "first_order_date", "last_order_date"),
            searchable_columns=("customer_number", "customer_type", "lifecycle_status", "loyalty_tier"),
            sortable_columns=(
                "customer_id",
                "lifetime_net_sales",
                "order_count",
                "last_order_date",
                "days_since_last_order",
            ),
            default_sort="lifetime_net_sales",
            description="Customer 360 profile metrics",
            allowed_columns=(
                "customer_id",
                "customer_number",
                "customer_type",
                "registration_date",
                "preferred_store_id",
                "is_active",
                "loyalty_tier",
                "points_balance",
                "order_count",
                "first_order_date",
                "last_order_date",
                "lifetime_net_sales",
                "lifetime_gross_profit",
                "lifetime_units",
                "avg_order_value",
                "days_since_last_order",
                "lifecycle_status",
            ),
        ),
        AnalyticsViewKey.CUSTOMER_RFM: AnalyticsViewDefinition(
            key=AnalyticsViewKey.CUSTOMER_RFM,
            schema=schema,
            name="vw_customer_rfm",
            date_columns=("last_order_date",),
            searchable_columns=("rfm_segment",),
            sortable_columns=("rfm_total", "r_score", "f_score", "m_score", "lifetime_net_sales"),
            default_sort="rfm_total",
            description="Customer RFM segmentation",
            allowed_columns=(
                "customer_id",
                "last_order_date",
                "order_count",
                "lifetime_net_sales",
                "days_since_last_order",
                "r_score",
                "f_score",
                "m_score",
                "rfm_total",
                "rfm_segment",
            ),
        ),
        AnalyticsViewKey.INVENTORY_SUMMARY: AnalyticsViewDefinition(
            key=AnalyticsViewKey.INVENTORY_SUMMARY,
            schema=schema,
            name="vw_inventory_health",
            date_columns=(),
            searchable_columns=("sku", "product_name", "category_name", "store_name", "dc_name"),
            sortable_columns=(
                "quantity_on_hand",
                "quantity_available",
                "inventory_value_cost",
                "product_name",
                "category_name",
            ),
            default_sort="inventory_value_cost",
            description="Inventory health summary",
            allowed_columns=(
                "inventory_id",
                "product_id",
                "sku",
                "product_name",
                "category_name",
                "location_type",
                "store_id",
                "store_name",
                "dc_id",
                "dc_name",
                "quantity_on_hand",
                "quantity_reserved",
                "quantity_available",
                "reorder_point",
                "max_stock",
                "inventory_value_cost",
                "stock_status",
            ),
        ),
        AnalyticsViewKey.SUPPLIER_PERFORMANCE: AnalyticsViewDefinition(
            key=AnalyticsViewKey.SUPPLIER_PERFORMANCE,
            schema=schema,
            name="vw_supplier_performance",
            date_columns=(),
            searchable_columns=("supplier_name", "supplier_code"),
            sortable_columns=(
                "on_time_rate",
                "fill_rate",
                "reliability_score",
                "supplier_name",
                "units_ordered",
            ),
            default_sort="on_time_rate",
            description="Supplier performance metrics",
            allowed_columns=(
                "supplier_id",
                "supplier_code",
                "supplier_name",
                "supplier_tier",
                "contracted_lead_time_days",
                "reliability_score",
                "po_count",
                "units_ordered",
                "units_received",
                "fill_rate",
                "on_time_rate",
                "avg_actual_lead_time_days",
            ),
        ),
        AnalyticsViewKey.FACT_RETURN_LINE: AnalyticsViewDefinition(
            key=AnalyticsViewKey.FACT_RETURN_LINE,
            schema=schema,
            name="vw_fact_return_line",
            date_columns=("return_date", "order_date"),
            searchable_columns=("return_reason_code", "return_status"),
            sortable_columns=("return_date", "refund_line_amount", "quantity_returned"),
            default_sort="return_date",
            description="Return line fact for returns analytics",
            allowed_columns=(
                "return_item_id",
                "return_id",
                "return_date",
                "order_id",
                "customer_id",
                "return_status",
                "order_item_id",
                "product_id",
                "quantity_returned",
                "unit_refund_amount",
                "refund_line_amount",
                "restock_flag",
                "return_reason_code",
                "order_date",
                "store_id",
                "channel_id",
                "days_to_return",
            ),
        ),
        AnalyticsViewKey.SHIPMENT_PERFORMANCE: AnalyticsViewDefinition(
            key=AnalyticsViewKey.SHIPMENT_PERFORMANCE,
            schema=schema,
            name="vw_shipment_performance",
            date_columns=("order_date", "ship_date", "delivery_date"),
            searchable_columns=("dc_name", "dc_code", "carrier_name", "shipment_status"),
            sortable_columns=(
                "order_date",
                "ship_date",
                "fulfillment_lead_time_days",
                "transit_days",
            ),
            default_sort="order_date",
            description="Shipment / warehouse fulfillment performance",
            allowed_columns=(
                "shipment_id",
                "order_id",
                "order_date",
                "dc_id",
                "dc_code",
                "dc_name",
                "store_id",
                "carrier_name",
                "shipment_status",
                "ship_date",
                "delivery_date",
                "fulfillment_lead_time_days",
                "transit_days",
                "delay_flag",
            ),
        ),
        AnalyticsViewKey.CAMPAIGN_PERFORMANCE: AnalyticsViewDefinition(
            key=AnalyticsViewKey.CAMPAIGN_PERFORMANCE,
            schema=schema,
            name="vw_campaign_performance",
            date_columns=("start_date", "end_date"),
            searchable_columns=("campaign_name", "campaign_code", "campaign_type", "objective_code"),
            sortable_columns=(
                "order_net_sales",
                "actual_spend",
                "budget_amount",
                "campaign_roi",
                "campaign_name",
            ),
            default_sort="order_net_sales",
            description="Marketing campaign performance / budget",
            allowed_columns=(
                "campaign_id",
                "campaign_code",
                "campaign_name",
                "campaign_type",
                "start_date",
                "end_date",
                "budget_amount",
                "actual_spend",
                "objective_code",
                "status_code",
                "sent_count",
                "open_count",
                "click_count",
                "convert_count",
                "response_attributed_revenue",
                "order_net_sales",
                "order_gross_profit",
                "attributed_orders",
                "attributed_customers",
                "conversion_rate",
                "campaign_roi",
            ),
        ),
        AnalyticsViewKey.PAYMENT_MIX: AnalyticsViewDefinition(
            key=AnalyticsViewKey.PAYMENT_MIX,
            schema=schema,
            name="vw_payment_mix",
            date_columns=("payment_month",),
            searchable_columns=("method_name", "method_code", "method_group"),
            sortable_columns=("payment_month", "payment_amount", "payment_count"),
            default_sort="payment_month",
            description="Captured payment mix by method and month",
            allowed_columns=(
                "payment_method_id",
                "method_code",
                "method_name",
                "method_group",
                "payment_month",
                "payment_count",
                "payment_amount",
            ),
        ),
        AnalyticsViewKey.EXECUTIVE_SCORECARD: AnalyticsViewDefinition(
            key=AnalyticsViewKey.EXECUTIVE_SCORECARD,
            schema=schema,
            name="vw_executive_daily_kpis",
            date_columns=("order_date", "kpi_date"),
            searchable_columns=(),
            sortable_columns=(
                "order_date",
                "kpi_date",
                "net_sales",
                "gross_profit",
                "order_count",
                "margin_pct",
            ),
            default_sort="order_date",
            description="Executive daily KPI scorecard",
            allowed_columns=(
                "order_date",
                "net_sales",
                "gross_profit",
                "margin_pct",
                "order_count",
                "units_sold",
                "aov",
                "refund_amount",
                "units_returned",
                "stockout_positions",
                "snapshot_positions",
            ),
        ),
        # Configurable placeholders for views that may be published later
        AnalyticsViewKey.MACHINE_LEARNING_PREDICTIONS: AnalyticsViewDefinition(
            key=AnalyticsViewKey.MACHINE_LEARNING_PREDICTIONS,
            schema=schema,
            name="vw_ml_predictions",
            date_columns=("prediction_date", "as_of_date"),
            searchable_columns=("model_name", "entity_type", "entity_id", "prediction_source"),
            sortable_columns=("prediction_date", "score", "model_name"),
            default_sort="prediction_date",
            description="Churn, profit, and sales-forecast predictions from analytics staging",
        ),
        AnalyticsViewKey.DATA_QUALITY_SUMMARY: AnalyticsViewDefinition(
            key=AnalyticsViewKey.DATA_QUALITY_SUMMARY,
            schema=schema,
            name="vw_data_quality_summary",
            date_columns=("check_date", "as_of_date"),
            searchable_columns=("check_name", "entity_name", "severity"),
            sortable_columns=("check_date", "score", "severity"),
            default_sort="check_date",
            description="Per-table and overall DQ metrics computed from oltp tables",
        ),
    }


class AnalyticsViewRegistry:
    """Resolves logical view keys to physical definitions (overridable)."""

    def __init__(
        self,
        catalog: dict[AnalyticsViewKey, AnalyticsViewDefinition] | None = None,
        *,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or get_settings()
        schema = getattr(cfg, "ANALYTICS_SCHEMA", "analytics")
        self._catalog = catalog or default_view_catalog(schema=schema)
        self._overrides = self._parse_overrides(getattr(cfg, "ANALYTICS_VIEW_OVERRIDES", "") or "")

    @staticmethod
    def _parse_overrides(raw: str) -> dict[str, str]:
        """
        Format: logical_key=physical_name,other_key=other_name
        Schema stays ANALYTICS_SCHEMA unless physical_name contains a dot.
        """
        result: dict[str, str] = {}
        for part in raw.split(","):
            item = part.strip()
            if not item or "=" not in item:
                continue
            key, value = item.split("=", 1)
            result[key.strip()] = value.strip()
        return result

    def get(self, key: AnalyticsViewKey | str) -> AnalyticsViewDefinition:
        view_key = AnalyticsViewKey(key) if isinstance(key, str) else key
        base = self._catalog[view_key]
        override = self._overrides.get(view_key.value)
        if not override:
            return base
        if "." in override:
            schema, name = override.split(".", 1)
            return AnalyticsViewDefinition(
                key=base.key,
                schema=schema,
                name=name,
                date_columns=base.date_columns,
                searchable_columns=base.searchable_columns,
                sortable_columns=base.sortable_columns,
                default_sort=base.default_sort,
                description=base.description,
                allowed_columns=base.allowed_columns,
            )
        return AnalyticsViewDefinition(
            key=base.key,
            schema=base.schema,
            name=override,
            date_columns=base.date_columns,
            searchable_columns=base.searchable_columns,
            sortable_columns=base.sortable_columns,
            default_sort=base.default_sort,
            description=base.description,
            allowed_columns=base.allowed_columns,
        )

    def all(self) -> list[AnalyticsViewDefinition]:
        return [self.get(key) for key in self._catalog]

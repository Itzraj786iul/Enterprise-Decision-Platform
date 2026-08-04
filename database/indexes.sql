-- =============================================================================
-- Enterprise Business Analytics & Decision Intelligence Platform
-- OLTP Indexes
-- =============================================================================
-- Apply after schema.sql. Indexes target high-cardinality join/filter columns
-- used by ETL, DQ checks, and foundational analytics views.
-- =============================================================================

SET search_path TO oltp, public;

-- -----------------------------------------------------------------------------
-- Customer domain
-- Why: CRM lookups, order joins, campaign attribution, CLV feature extracts
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_customers_registration_date
    ON customers (registration_date);

CREATE INDEX IF NOT EXISTS ix_customers_type_active
    ON customers (customer_type, is_active);

CREATE INDEX IF NOT EXISTS ix_customers_preferred_store
    ON customers (preferred_store_id);

CREATE INDEX IF NOT EXISTS ix_loyalty_accounts_tier
    ON loyalty_accounts (tier_code);

CREATE INDEX IF NOT EXISTS ix_customer_addresses_customer
    ON customer_addresses (customer_id);

-- -----------------------------------------------------------------------------
-- Product / supplier domain
-- Why: Merchandising joins, assortment filters, procurement analytics
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_products_category_id
    ON products (category_id);

CREATE INDEX IF NOT EXISTS ix_products_primary_supplier_id
    ON products (primary_supplier_id);

CREATE INDEX IF NOT EXISTS ix_products_active_popularity
    ON products (is_active, popularity_score DESC);

CREATE INDEX IF NOT EXISTS ix_product_suppliers_supplier_id
    ON product_suppliers (supplier_id);

CREATE INDEX IF NOT EXISTS ix_product_suppliers_product_id
    ON product_suppliers (product_id);

CREATE INDEX IF NOT EXISTS ix_suppliers_tier_active
    ON suppliers (supplier_tier, is_active);

-- -----------------------------------------------------------------------------
-- Store / employee domain
-- Why: Regional rollups, same-store filters, labor productivity joins
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_stores_region_id
    ON stores (region_id);

CREATE INDEX IF NOT EXISTS ix_stores_active_format
    ON stores (is_active, store_format);

CREATE INDEX IF NOT EXISTS ix_employees_store_id
    ON employees (store_id);

CREATE INDEX IF NOT EXISTS ix_store_labor_hours_store_date
    ON store_labor_hours (store_id, work_date);

-- -----------------------------------------------------------------------------
-- Orders / order items
-- Why: Highest query volume — date filters, customer history, store/channel mixes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_orders_customer_id
    ON orders (customer_id);

CREATE INDEX IF NOT EXISTS ix_orders_order_date
    ON orders (order_date);

CREATE INDEX IF NOT EXISTS ix_orders_store_id
    ON orders (store_id);

CREATE INDEX IF NOT EXISTS ix_orders_channel_id
    ON orders (channel_id);

CREATE INDEX IF NOT EXISTS ix_orders_campaign_id
    ON orders (campaign_id);

CREATE INDEX IF NOT EXISTS ix_orders_date_store
    ON orders (order_date, store_id);

CREATE INDEX IF NOT EXISTS ix_orders_date_channel
    ON orders (order_date, channel_id);

CREATE INDEX IF NOT EXISTS ix_order_items_order_id
    ON order_items (order_id);

CREATE INDEX IF NOT EXISTS ix_order_items_product_id
    ON order_items (product_id);

CREATE INDEX IF NOT EXISTS ix_order_items_promotion_id
    ON order_items (promotion_id);

-- Composite supports product performance by period via order join patterns
CREATE INDEX IF NOT EXISTS ix_order_items_product_order
    ON order_items (product_id, order_id);

-- -----------------------------------------------------------------------------
-- Payments / shipments / returns
-- Why: Finance reconciliation, fulfillment SLA, return-rate diagnostics
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_payments_order_id
    ON payments (order_id);

CREATE INDEX IF NOT EXISTS ix_payments_method_id
    ON payments (payment_method_id);

CREATE INDEX IF NOT EXISTS ix_payments_timestamp
    ON payments (payment_timestamp);

CREATE INDEX IF NOT EXISTS ix_shipments_order_id
    ON shipments (order_id);

CREATE INDEX IF NOT EXISTS ix_shipments_ship_date
    ON shipments (ship_date);

CREATE INDEX IF NOT EXISTS ix_shipments_dc_id
    ON shipments (dc_id);

CREATE INDEX IF NOT EXISTS ix_shipment_items_shipment_id
    ON shipment_items (shipment_id);

CREATE INDEX IF NOT EXISTS ix_shipment_items_product_id
    ON shipment_items (product_id);

CREATE INDEX IF NOT EXISTS ix_returns_order_id
    ON returns (order_id);

CREATE INDEX IF NOT EXISTS ix_returns_customer_id
    ON returns (customer_id);

CREATE INDEX IF NOT EXISTS ix_returns_return_date
    ON returns (return_date);

CREATE INDEX IF NOT EXISTS ix_return_items_return_id
    ON return_items (return_id);

CREATE INDEX IF NOT EXISTS ix_return_items_product_id
    ON return_items (product_id);

CREATE INDEX IF NOT EXISTS ix_return_items_order_item_id
    ON return_items (order_item_id);

-- -----------------------------------------------------------------------------
-- Inventory
-- Why: Stockout scans, valuation, snapshot time-series extracts
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_inventory_product_id
    ON inventory (product_id);

CREATE INDEX IF NOT EXISTS ix_inventory_store_id
    ON inventory (store_id);

CREATE INDEX IF NOT EXISTS ix_inventory_dc_id
    ON inventory (dc_id);

CREATE INDEX IF NOT EXISTS ix_inventory_txn_product_date
    ON inventory_transactions (product_id, txn_date);

CREATE INDEX IF NOT EXISTS ix_inventory_txn_store_date
    ON inventory_transactions (store_id, txn_date);

CREATE INDEX IF NOT EXISTS ix_inventory_snapshots_date
    ON inventory_snapshots (snapshot_date);

CREATE INDEX IF NOT EXISTS ix_inventory_snapshots_product_date
    ON inventory_snapshots (product_id, snapshot_date);

CREATE INDEX IF NOT EXISTS ix_inventory_snapshots_store_date
    ON inventory_snapshots (store_id, snapshot_date);

-- -----------------------------------------------------------------------------
-- Procurement
-- Why: Supplier fill-rate and lead-time analytics
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_purchase_orders_supplier_id
    ON purchase_orders (supplier_id);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_order_date
    ON purchase_orders (order_date);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_dc_id
    ON purchase_orders (dc_id);

CREATE INDEX IF NOT EXISTS ix_po_items_product_id
    ON purchase_order_items (product_id);

CREATE INDEX IF NOT EXISTS ix_po_items_po_id
    ON purchase_order_items (purchase_order_id);

CREATE INDEX IF NOT EXISTS ix_goods_receipts_po_id
    ON goods_receipts (purchase_order_id);

CREATE INDEX IF NOT EXISTS ix_goods_receipts_receipt_date
    ON goods_receipts (receipt_date);

CREATE INDEX IF NOT EXISTS ix_goods_receipt_items_product_id
    ON goods_receipt_items (product_id);

-- -----------------------------------------------------------------------------
-- Marketing
-- Why: Campaign ROI joins and customer engagement timelines
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_marketing_campaigns_dates
    ON marketing_campaigns (start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_campaign_responses_campaign_id
    ON campaign_responses (campaign_id);

CREATE INDEX IF NOT EXISTS ix_campaign_responses_customer_id
    ON campaign_responses (customer_id);

CREATE INDEX IF NOT EXISTS ix_campaign_responses_order_id
    ON campaign_responses (order_id);

CREATE INDEX IF NOT EXISTS ix_campaign_responses_ts
    ON campaign_responses (response_timestamp);

-- -----------------------------------------------------------------------------
-- Price / cost history
-- Why: Point-in-time margin reconstruction
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_price_history_product_dates
    ON price_history (product_id, effective_start, effective_end);

CREATE INDEX IF NOT EXISTS ix_cost_history_product_dates
    ON cost_history (product_id, effective_start, effective_end);

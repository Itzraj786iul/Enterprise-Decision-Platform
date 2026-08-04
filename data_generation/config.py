"""
Central configuration for synthetic retail data generation.

Scale targets align to the engagement brief:
  - ~850k customers, ~3M orders, ~9M order items
  - 12k products, 120 stores, 6 regions, 180 suppliers
  - 36 months of history with seasonal demand
"""

from __future__ import annotations

from pathlib import Path
from datetime import date

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "generated"
STATE_DIR = OUTPUT_DIR / "_state"

# -----------------------------------------------------------------------------
# Reproducibility
# -----------------------------------------------------------------------------
RANDOM_SEED = 42

# -----------------------------------------------------------------------------
# Time window (36 months ending at a fixed "as-of" date for reproducibility)
# -----------------------------------------------------------------------------
AS_OF_DATE = date(2026, 6, 30)
HISTORY_MONTHS = 36
# Start = first day of month, 36 months before AS_OF month
START_DATE = date(2023, 7, 1)

# -----------------------------------------------------------------------------
# Full-scale targets
# -----------------------------------------------------------------------------
N_REGIONS = 6
N_STORES = 120
N_DCS = 5
N_SUPPLIERS = 180
N_PRODUCTS = 12_000
N_CUSTOMERS = 850_000
N_ORDERS = 3_000_000
N_ORDER_ITEMS_TARGET = 9_000_000  # ~3 lines/order average
N_EMPLOYEES_PER_STORE = (25, 45)  # inclusive-ish range

# Assortment / inventory realism
SKUS_PER_STORE = 2_000          # stores do not stock full catalog
SKUS_PER_DC = 10_000
INVENTORY_SNAPSHOT_MODE = "weekly"  # "weekly" | "daily"
# Daily full snapshots at this assortment are very large; weekly is default.

# Marketing
N_CAMPAIGNS = 1_200
N_PROMOTIONS = 3_000

# Procurement volume (approximate)
N_PURCHASE_ORDERS = 300_000

# Chunking for memory safety
ORDER_CHUNK_SIZE = 100_000
SNAPSHOT_CHUNK_ROWS = 500_000

# Channel mix (must sum ~1)
CHANNEL_WEIGHTS = {
    "INSTORE": 0.62,
    "ONLINE": 0.28,
    "MARKETPLACE": 0.10,
}

# Customer type mix
CUSTOMER_TYPE_WEIGHTS = {
    "Loyalty": 0.55,
    "Guest": 0.40,
    "Corporate": 0.05,
}

# Store format mix
STORE_FORMAT_WEIGHTS = {
    "Flagship": 0.10,
    "Standard": 0.70,
    "Outlet": 0.20,
}

# Supplier tier mix
SUPPLIER_TIER_WEIGHTS = {
    "Strategic": 0.15,
    "Preferred": 0.35,
    "Standard": 0.50,
}

# Category L1 definitions: (code, name, base_return_rate)
CATEGORY_L1 = [
    ("APPAREL", "Apparel", 0.12),
    ("HOME", "Home & Living", 0.06),
    ("ELEC_ACC", "Electronics Accessories", 0.05),
    ("BEAUTY", "Beauty & Personal Care", 0.04),
    ("GROCERY", "Grocery Essentials", 0.02),
    ("SPORTS", "Sports & Outdoors", 0.07),
    ("KIDS", "Kids & Baby", 0.09),
    ("SEASONAL", "Seasonal / Limited", 0.08),
]

REGION_DEFS = [
    ("NE", "Northeast"),
    ("SE", "Southeast"),
    ("MW", "Midwest"),
    ("SW", "Southwest"),
    ("WE", "West"),
    ("ON", "Online/National"),
]

US_HOLIDAYS = {
    # month-day -> name (observed simply on calendar date; good enough for synth)
    (1, 1): "New Year's Day",
    (7, 4): "Independence Day",
    (11, 11): "Veterans Day",
    (12, 25): "Christmas Day",
}


def apply_demo_scale() -> None:
    """Shrink volumes for laptop smoke tests while preserving relationships."""
    global N_CUSTOMERS, N_ORDERS, N_ORDER_ITEMS_TARGET, N_PRODUCTS
    global N_SUPPLIERS, N_STORES, N_CAMPAIGNS, N_PROMOTIONS, N_PURCHASE_ORDERS
    global SKUS_PER_STORE, SKUS_PER_DC, ORDER_CHUNK_SIZE

    N_CUSTOMERS = 5_000
    N_ORDERS = 15_000
    N_ORDER_ITEMS_TARGET = 45_000
    N_PRODUCTS = 800
    N_SUPPLIERS = 40
    N_STORES = 24
    N_CAMPAIGNS = 60
    N_PROMOTIONS = 120
    N_PURCHASE_ORDERS = 2_000
    SKUS_PER_STORE = 200
    SKUS_PER_DC = 600
    ORDER_CHUNK_SIZE = 5_000

"""
Orchestrate full synthetic dataset generation with referential integrity.

Usage
-----
  # Demo (small, fast)
  python -m data_generation.generate_all --demo

  # Full engagement scale (~850k customers / 3M orders)
  python -m data_generation.generate_all

  # Daily inventory snapshots (large)
  python -m data_generation.generate_all --snapshot-mode daily

  # Skip heavy domains during iterative rebuilds
  python -m data_generation.generate_all --demo --skip inventory
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running as `python data_generation/generate_all.py` from project root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data_generation import config
from data_generation.utils import ensure_dirs, progress, save_state
from data_generation.generate_products import generate_products
from data_generation.generate_customers import generate_customers
from data_generation.generate_marketing import generate_marketing
from data_generation.generate_orders import generate_orders
from data_generation.generate_inventory import generate_inventory


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate enterprise retail synthetic CSVs")
    p.add_argument("--demo", action="store_true", help="Use reduced row counts for smoke tests")
    p.add_argument(
        "--snapshot-mode",
        choices=["weekly", "daily"],
        default=None,
        help="Inventory snapshot cadence (default: config.INVENTORY_SNAPSHOT_MODE)",
    )
    p.add_argument(
        "--skip",
        nargs="*",
        default=[],
        choices=["products", "customers", "marketing", "orders", "inventory", "responses"],
        help="Skip selected stages",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override RANDOM_SEED",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.demo:
        config.apply_demo_scale()
        progress("DEMO scale enabled")
    if args.snapshot_mode:
        config.INVENTORY_SNAPSHOT_MODE = args.snapshot_mode
    if args.seed is not None:
        config.RANDOM_SEED = args.seed

    ensure_dirs()
    t0 = time.time()
    skip = set(args.skip or [])

    progress("=" * 72)
    progress("Enterprise synthetic data generation starting")
    progress(f"Output: {config.OUTPUT_DIR}")
    progress(
        f"Targets: customers={config.N_CUSTOMERS:,}, orders={config.N_ORDERS:,}, "
        f"products={config.N_PRODUCTS:,}, stores={config.N_STORES}, snapshot={config.INVENTORY_SNAPSHOT_MODE}"
    )
    progress("=" * 72)

    # Dependency order is intentional for FK integrity
    if "products" not in skip:
        generate_products()
    if "customers" not in skip:
        generate_customers()
    if "marketing" not in skip:
        generate_marketing(include_responses=False)
    if "orders" not in skip:
        generate_orders()
    if "responses" not in skip and "marketing" not in skip:
        # Requires orders for Convert attribution
        generate_marketing(include_responses=True)
    if "inventory" not in skip:
        generate_inventory()

    elapsed = time.time() - t0
    save_state(
        "run_manifest",
        {
            "demo": bool(args.demo),
            "seed": config.RANDOM_SEED,
            "snapshot_mode": config.INVENTORY_SNAPSHOT_MODE,
            "n_customers": config.N_CUSTOMERS,
            "n_orders": config.N_ORDERS,
            "n_products": config.N_PRODUCTS,
            "elapsed_seconds": round(elapsed, 2),
            "output_dir": str(config.OUTPUT_DIR),
        },
    )
    progress("=" * 72)
    progress(f"DONE in {elapsed / 60:.1f} minutes")
    progress(f"CSV files written to {config.OUTPUT_DIR}")
    progress("=" * 72)


if __name__ == "__main__":
    main()

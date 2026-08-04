"""
Generate inventory, inventory_transactions, inventory_snapshots,
purchase_orders / items, goods_receipts / items, and store_labor_hours.

Snapshot strategy
-----------------
Full Cartesian daily snapshots (all SKUs × all stores × 36 months) is not
practical for a laptop-scale portfolio build. Instead we:

1. Assign each store a realistic assortment subset (~SKUS_PER_STORE).
2. Assign each DC a larger assortment (~SKUS_PER_DC).
3. Maintain current `inventory` balances.
4. Emit `inventory_snapshots` on a weekly cadence by default (daily optional).
5. Generate procurement POs/receipts with supplier-specific lead time & reliability.
6. Create inventory_transactions from receipts, sales depletion samples, and noise.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from . import config
from .utils import (
    append_csv,
    chunked_range,
    daterange,
    make_rng,
    progress,
    save_state,
    write_csv,
)


def generate_inventory() -> None:
    rng = make_rng(config.RANDOM_SEED + 41)
    progress("Generating inventory, procurement, labor ...")

    products = pd.read_csv(
        config.OUTPUT_DIR / "products.csv",
        usecols=["product_id", "primary_supplier_id", "current_unit_cost", "popularity_score", "is_active"],
    )
    stores = pd.read_csv(config.OUTPUT_DIR / "stores.csv", usecols=["store_id"])
    dcs = pd.read_csv(config.OUTPUT_DIR / "distribution_centers.csv", usecols=["dc_id", "region_id"])
    suppliers = pd.read_csv(
        config.OUTPUT_DIR / "suppliers.csv",
        usecols=["supplier_id", "lead_time_days_avg", "reliability_score"],
    )
    employees = pd.read_csv(config.OUTPUT_DIR / "employees.csv", usecols=["employee_id", "store_id"])

    active = products[products["is_active"]].copy()
    if active.empty:
        active = products.copy()
    prod_ids = active["product_id"].to_numpy()
    pop = active["popularity_score"].to_numpy().astype(float)
    pop = pop / pop.sum()
    cost_map = dict(zip(products["product_id"], products["current_unit_cost"]))
    supplier_map = dict(zip(products["product_id"], products["primary_supplier_id"]))
    lead_map = dict(zip(suppliers["supplier_id"], suppliers["lead_time_days_avg"]))
    rel_map = dict(zip(suppliers["supplier_id"], suppliers["reliability_score"]))

    # Assortment assignments (product popularity biased)
    store_assortment = {}
    for sid in stores["store_id"].tolist():
        k = min(config.SKUS_PER_STORE, len(prod_ids))
        store_assortment[int(sid)] = rng.choice(prod_ids, size=k, replace=False, p=pop)

    dc_assortment = {}
    for dcid in dcs["dc_id"].tolist():
        k = min(config.SKUS_PER_DC, len(prod_ids))
        dc_assortment[int(dcid)] = rng.choice(prod_ids, size=k, replace=False, p=pop)

    # Current inventory
    inv_rows = []
    inv_id = 1
    on_hand_state = {}  # (loc_type, loc_id, product_id) -> qty

    pop_by_pid = dict(zip(active["product_id"].astype(int), pop))

    for sid, sku_list in store_assortment.items():
        for pid in sku_list:
            # Deeper stock for more popular SKUs
            depth = 2 + int(80 * (pop_by_pid.get(int(pid), 0) ** 0.35) * 50)
            qty = int(np.clip(rng.integers(depth, depth + 40), 2, 120))
            reserved = int(rng.integers(0, min(5, qty) + 1))
            avail = qty - reserved
            inv_rows.append(
                {
                    "inventory_id": inv_id,
                    "product_id": int(pid),
                    "location_type": "STORE",
                    "store_id": int(sid),
                    "dc_id": None,
                    "quantity_on_hand": qty,
                    "quantity_reserved": reserved,
                    "quantity_available": avail,
                    "reorder_point": int(rng.integers(3, 15)),
                    "max_stock": int(rng.integers(40, 120)),
                    "as_of_timestamp": config.AS_OF_DATE.isoformat() + " 23:00:00",
                }
            )
            on_hand_state[("STORE", int(sid), int(pid))] = qty
            inv_id += 1

    for dcid, sku_list in dc_assortment.items():
        for pid in sku_list:
            depth = 50 + int(1500 * (pop_by_pid.get(int(pid), 0) ** 0.35) * 40)
            qty = int(np.clip(rng.integers(depth, depth + 400), 50, 5000))
            reserved = int(rng.integers(0, min(50, qty) + 1))
            inv_rows.append(
                {
                    "inventory_id": inv_id,
                    "product_id": int(pid),
                    "location_type": "DC",
                    "store_id": None,
                    "dc_id": int(dcid),
                    "quantity_on_hand": qty,
                    "quantity_reserved": reserved,
                    "quantity_available": qty - reserved,
                    "reorder_point": int(rng.integers(100, 400)),
                    "max_stock": int(rng.integers(1500, 5000)),
                    "as_of_timestamp": config.AS_OF_DATE.isoformat() + " 23:00:00",
                }
            )
            on_hand_state[("DC", int(dcid), int(pid))] = qty
            inv_id += 1

    write_csv(pd.DataFrame(inv_rows), "inventory")
    progress(f"  current inventory positions={len(inv_rows):,}")

    _generate_procurement(rng, store_assortment, dc_assortment, supplier_map, lead_map, rel_map, cost_map)
    _generate_snapshots(rng, store_assortment, dc_assortment, cost_map, on_hand_state)
    _generate_transactions_sample(rng, on_hand_state, cost_map)
    _generate_labor(rng, employees)

    save_state(
        "inventory",
        {
            "n_inventory": len(inv_rows),
            "snapshot_mode": config.INVENTORY_SNAPSHOT_MODE,
            "skus_per_store": config.SKUS_PER_STORE,
            "skus_per_dc": config.SKUS_PER_DC,
        },
    )
    progress("Inventory domain complete.")


def _generate_procurement(rng, store_assortment, dc_assortment, supplier_map, lead_map, rel_map, cost_map):
    progress("Generating purchase orders & receipts ...")
    for name in ["purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items"]:
        p = config.OUTPUT_DIR / f"{name}.csv"
        if p.exists():
            p.unlink()

    dc_ids = list(dc_assortment.keys())
    days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    # Spread POs across days
    n_po = config.N_PURCHASE_ORDERS
    day_idx = rng.integers(0, len(days), size=n_po)

    po_id = 1
    poi_id = 1
    receipt_id = 1
    ri_id = 1

    for start, end in chunked_range(n_po, 20_000):
        po_rows, poi_rows, gr_rows, gri_rows = [], [], [], []
        for i in range(start, end):
            d = days[int(day_idx[i])]
            dc_id = int(rng.choice(dc_ids))
            # pick 1-8 products from DC assortment
            sku_list = dc_assortment[dc_id]
            n_lines = int(rng.integers(1, 9))
            chosen = rng.choice(sku_list, size=min(n_lines, len(sku_list)), replace=False)
            # supplier from first product primary (simplified: one supplier per PO)
            supplier_id = int(supplier_map.get(int(chosen[0]), 1))
            lead = int(lead_map.get(supplier_id, 14))
            rel = float(rel_map.get(supplier_id, 0.9))
            expected = d + timedelta(days=lead)

            po_rows.append(
                {
                    "purchase_order_id": po_id,
                    "po_number": f"PO-{po_id:08d}",
                    "supplier_id": supplier_id,
                    "dc_id": dc_id,
                    "order_date": d.isoformat(),
                    "expected_receipt_date": expected.isoformat(),
                    "po_status": "Closed",
                    "created_at": d.isoformat() + " 08:00:00",
                }
            )

            line_meta = []
            for ln, pid in enumerate(chosen, start=1):
                qty = int(rng.integers(20, 500))
                unit_cost = float(cost_map.get(int(pid), 10.0))
                poi_rows.append(
                    {
                        "po_item_id": poi_id,
                        "purchase_order_id": po_id,
                        "line_number": ln,
                        "product_id": int(pid),
                        "quantity_ordered": qty,
                        "unit_cost": unit_cost,
                    }
                )
                line_meta.append((poi_id, int(pid), qty))
                poi_id += 1

            # Receipt occurs with reliability; delay noise by supplier quality
            if rng.random() < rel:
                delay = int(rng.integers(0, max(1, int((1.05 - rel) * 20))))
            else:
                delay = int(rng.integers(lead // 2, lead + 15))
            receipt_date = expected + timedelta(days=delay - lead)  # around expected
            # rewrite: ship from order_date + lead + noise
            receipt_date = d + timedelta(days=lead + int(rng.normal(0, max(1, (1 - rel) * 10))))
            if receipt_date < d:
                receipt_date = d + timedelta(days=lead)
            if receipt_date > config.AS_OF_DATE:
                # leave open without receipt
                po_rows[-1]["po_status"] = "Open"
            else:
                on_time = receipt_date <= expected
                gr_rows.append(
                    {
                        "receipt_id": receipt_id,
                        "purchase_order_id": po_id,
                        "dc_id": dc_id,
                        "receipt_date": receipt_date.isoformat(),
                        "is_on_time": bool(on_time),
                        "created_at": receipt_date.isoformat() + " 10:00:00",
                    }
                )
                for poi, pid, qty in line_meta:
                    # Under/over receive based on reliability
                    fill = float(np.clip(rng.normal(rel, 0.05), 0.6, 1.05))
                    qty_rec = max(1, int(round(qty * fill)))
                    gri_rows.append(
                        {
                            "receipt_item_id": ri_id,
                            "receipt_id": receipt_id,
                            "po_item_id": poi,
                            "product_id": pid,
                            "quantity_received": qty_rec,
                        }
                    )
                    ri_id += 1
                receipt_id += 1

            po_id += 1

        append_csv(pd.DataFrame(po_rows), "purchase_orders")
        append_csv(pd.DataFrame(poi_rows), "purchase_order_items")
        if gr_rows:
            append_csv(pd.DataFrame(gr_rows), "goods_receipts")
            append_csv(pd.DataFrame(gri_rows), "goods_receipt_items")
        progress(f"  POs {end:,}/{n_po:,}")


def _generate_snapshots(rng, store_assortment, dc_assortment, cost_map, on_hand_state):
    progress(f"Generating inventory_snapshots mode={config.INVENTORY_SNAPSHOT_MODE} ...")
    path = config.OUTPUT_DIR / "inventory_snapshots.csv"
    if path.exists():
        path.unlink()

    days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    if config.INVENTORY_SNAPSHOT_MODE == "weekly":
        days = [d for d in days if d.weekday() == 0]  # Mondays
    # else daily

    # Working qty state starts from a perturbed baseline and random-walks
    state = {k: max(0, int(v * rng.uniform(0.7, 1.3))) for k, v in on_hand_state.items()}
    snapshot_id = 1

    for d in days:
        rows = []
        # random walk inventory
        keys = list(state.keys())
        # update a subset each day for speed
        upd = rng.choice(len(keys), size=min(5000, len(keys)), replace=False)
        for idx in upd:
            k = keys[idx]
            delta = int(rng.integers(-5, 8))
            state[k] = max(0, state[k] + delta)

        for (loc_type, loc_id, pid), qty in state.items():
            reserved = int(min(qty, rng.integers(0, 6))) if qty > 0 else 0
            cost = float(cost_map.get(pid, 0))
            rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "snapshot_date": d.isoformat(),
                    "product_id": pid,
                    "location_type": loc_type,
                    "store_id": loc_id if loc_type == "STORE" else None,
                    "dc_id": loc_id if loc_type == "DC" else None,
                    "quantity_on_hand": qty,
                    "quantity_reserved": reserved,
                    "quantity_available": qty - reserved,
                    "inventory_value_cost": round(qty * cost, 2),
                }
            )
            snapshot_id += 1
            if len(rows) >= config.SNAPSHOT_CHUNK_ROWS:
                append_csv(pd.DataFrame(rows), "inventory_snapshots")
                rows = []
        if rows:
            append_csv(pd.DataFrame(rows), "inventory_snapshots")
        if snapshot_id % 2_000_000 < config.SNAPSHOT_CHUNK_ROWS:
            progress(f"  snapshots through {d.isoformat()} id={snapshot_id:,}")

    progress(f"  inventory_snapshots complete last_id={snapshot_id - 1:,}")


def _generate_transactions_sample(rng, on_hand_state, cost_map):
    """Sampled movement ledger (not every sale) for audit-style analytics."""
    progress("Generating inventory_transactions sample ...")
    path = config.OUTPUT_DIR / "inventory_transactions.csv"
    if path.exists():
        path.unlink()

    keys = list(on_hand_state.keys())
    n_txn = min(2_000_000, max(50_000, len(keys) * 20))
    if config.N_ORDERS < 100_000:
        n_txn = min(n_txn, 100_000)

    days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    txn_id = 1
    types = np.array(["SALE", "RECEIPT", "RETURN_RESTOCK", "ADJUSTMENT", "SHRINK", "TRANSFER_IN", "TRANSFER_OUT"])
    type_p = np.array([0.45, 0.20, 0.10, 0.10, 0.05, 0.05, 0.05])

    for start, end in chunked_range(n_txn, 100_000):
        rows = []
        for _ in range(start, end):
            loc_type, loc_id, pid = keys[int(rng.integers(0, len(keys)))]
            t = str(rng.choice(types, p=type_p))
            if t in ("SALE", "SHRINK", "TRANSFER_OUT"):
                delta = -int(rng.integers(1, 6))
            elif t == "ADJUSTMENT":
                delta = int(rng.integers(-3, 4))
                if delta == 0:
                    delta = 1
            else:
                delta = int(rng.integers(1, 20))
            d = days[int(rng.integers(0, len(days)))]
            rows.append(
                {
                    "inventory_txn_id": txn_id,
                    "product_id": pid,
                    "location_type": loc_type,
                    "store_id": loc_id if loc_type == "STORE" else None,
                    "dc_id": loc_id if loc_type == "DC" else None,
                    "txn_type": t,
                    "txn_date": d.isoformat(),
                    "quantity_delta": delta,
                    "unit_cost": float(cost_map.get(pid, 0)),
                    "reference_id": f"TXN-{txn_id}",
                    "created_at": d.isoformat() + " 12:00:00",
                }
            )
            txn_id += 1
        append_csv(pd.DataFrame(rows), "inventory_transactions")
    progress(f"  inventory_transactions={txn_id - 1:,}")


def _generate_labor(rng, employees: pd.DataFrame):
    progress("Generating store_labor_hours ...")
    path = config.OUTPUT_DIR / "store_labor_hours.csv"
    if path.exists():
        path.unlink()

    # Store-day aggregates (faster / smaller than employee-day full history)
    stores = employees["store_id"].unique()
    days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    # sample every day but store-level only
    labor_id = 1
    for start, end in chunked_range(len(days), 60):
        rows = []
        for d in days[start:end]:
            weekend = d.weekday() >= 5
            for sid in stores:
                base = 180 if not weekend else 140
                hours = float(np.round(rng.normal(base, 25), 2))
                hours = float(np.clip(hours, 60, 320))
                rows.append(
                    {
                        "labor_hours_id": labor_id,
                        "store_id": int(sid),
                        "employee_id": None,
                        "work_date": d.isoformat(),
                        "labor_hours": hours,
                        "labor_cost": round(hours * float(rng.uniform(16, 28)), 2),
                    }
                )
                labor_id += 1
        append_csv(pd.DataFrame(rows), "store_labor_hours")
    progress(f"  store_labor_hours={labor_id - 1:,}")


if __name__ == "__main__":
    generate_inventory()

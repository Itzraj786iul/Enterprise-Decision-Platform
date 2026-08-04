"""
Generate commercial transactions:
  orders, order_items, order_item_promotions, payments, shipments,
  shipment_items, returns, return_items

Realism levers
--------------
- Seasonal demand multipliers by day
- Product selection via long-tail popularity weights
- Campaign lift increases purchase odds for overlapping campaigns
- Channel mix In-Store / Online / Marketplace
- Returns vary by product category return propensity
- ~3 line items per order on average (configurable target)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .utils import (
    append_csv,
    chunked_range,
    daterange,
    load_state,
    make_rng,
    progress,
    save_state,
    seasonal_multiplier,
    ts_on_date,
    write_csv,
)


def generate_orders() -> None:
    progress("Generating orders ecosystem ...")
    rng = make_rng(config.RANDOM_SEED + 31)

    customers = pd.read_csv(config.OUTPUT_DIR / "customers.csv", usecols=["customer_id", "customer_type", "preferred_store_id", "registration_date"])
    products = pd.read_csv(
        config.OUTPUT_DIR / "products.csv",
        usecols=["product_id", "current_list_price", "current_unit_cost", "popularity_score", "is_active", "category_id"],
    )
    stores = pd.read_csv(config.OUTPUT_DIR / "stores.csv", usecols=["store_id", "region_id"])
    channels = pd.read_csv(config.OUTPUT_DIR / "channels.csv")
    employees = pd.read_csv(config.OUTPUT_DIR / "employees.csv", usecols=["employee_id", "store_id"])
    payment_methods = pd.read_csv(config.OUTPUT_DIR / "payment_methods.csv")
    campaigns = pd.read_csv(config.OUTPUT_DIR / "marketing_campaigns.csv", parse_dates=["start_date", "end_date"])
    promotions = pd.read_csv(config.OUTPUT_DIR / "promotions.csv", parse_dates=["start_date", "end_date"])
    dcs = pd.read_csv(config.OUTPUT_DIR / "distribution_centers.csv", usecols=["dc_id"])
    product_return_rate = {int(k): float(v) for k, v in load_state("products")["product_return_rate"].items()}

    active_products = products[products["is_active"]].copy()
    if active_products.empty:
        active_products = products
    prod_ids = active_products["product_id"].to_numpy()
    prod_price = active_products["current_list_price"].to_numpy()
    prod_cost = active_products["current_unit_cost"].to_numpy()
    weights = active_products["popularity_score"].to_numpy().astype(float)
    weights = weights / weights.sum()
    prod_index = {int(pid): i for i, pid in enumerate(prod_ids)}

    customer_ids = customers["customer_id"].to_numpy()
    cust_reg = pd.to_datetime(customers["registration_date"]).dt.date.to_numpy()
    cust_store = customers["preferred_store_id"].to_numpy()
    cust_type = customers["customer_type"].to_numpy()

    store_ids = stores["store_id"].to_numpy()
    channel_map = dict(zip(channels["channel_code"], channels["channel_id"]))
    channel_codes = list(config.CHANNEL_WEIGHTS.keys())
    channel_probs = np.array([config.CHANNEL_WEIGHTS[c] for c in channel_codes], dtype=float)
    channel_probs /= channel_probs.sum()

    emp_by_store = employees.groupby("store_id")["employee_id"].apply(list).to_dict()
    pay_ids = payment_methods["payment_method_id"].to_numpy()
    # In-store cash more likely
    pay_probs_store = np.array([0.35, 0.30, 0.10, 0.15, 0.05, 0.05])[: len(pay_ids)]
    pay_probs_store = pay_probs_store / pay_probs_store.sum()
    pay_probs_digital = np.array([0.40, 0.35, 0.10, 0.00, 0.10, 0.05])[: len(pay_ids)]
    pay_probs_digital = pay_probs_digital / pay_probs_digital.sum()

    dc_ids = dcs["dc_id"].to_numpy()
    promo_ids = promotions["promotion_id"].to_numpy()
    promo_start = promotions["start_date"].dt.date.to_numpy()
    promo_end = promotions["end_date"].dt.date.to_numpy()
    promo_pct = promotions["discount_percent"].fillna(0).to_numpy()
    promo_amt = promotions["discount_amount"].fillna(0).to_numpy()
    promo_type = promotions["promotion_type"].to_numpy()

    # Precompute daily campaign lifts (max lift among active campaigns)
    days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    daily_lift = {}
    daily_campaign_choices = {}
    for d in days:
        active = campaigns[(campaigns["start_date"].dt.date <= d) & (campaigns["end_date"].dt.date >= d)]
        if active.empty:
            daily_lift[d] = 1.0
            daily_campaign_choices[d] = np.array([])
        else:
            daily_lift[d] = float(active["lift_factor"].max())
            daily_campaign_choices[d] = active["campaign_id"].to_numpy()

    # Allocate orders across days using seasonal weights * campaign lift
    raw = np.array([seasonal_multiplier(d, rng) * daily_lift[d] for d in days], dtype=float)
    day_share = raw / raw.sum()
    orders_per_day = rng.multinomial(config.N_ORDERS, day_share)

    # Clear output files
    for name in [
        "orders",
        "order_items",
        "order_item_promotions",
        "payments",
        "shipments",
        "shipment_items",
        "returns",
        "return_items",
    ]:
        path = config.OUTPUT_DIR / f"{name}.csv"
        if path.exists():
            path.unlink()

    order_id = 1
    order_item_id = 1
    payment_id = 1
    shipment_id = 1
    shipment_item_id = 1
    return_id = 1
    return_item_id = 1
    oip_id = 1

    avg_lines = config.N_ORDER_ITEMS_TARGET / config.N_ORDERS

    for day_idx, d in enumerate(days):
        n_day = int(orders_per_day[day_idx])
        if n_day == 0:
            continue

        for start, end in chunked_range(n_day, config.ORDER_CHUNK_SIZE):
            chunk_n = end - start
            orders_rows = []
            items_rows = []
            oip_rows = []
            pay_rows = []
            ship_rows = []
            ship_item_rows = []
            ret_rows = []
            ret_item_rows = []

            # Sample customers registered on/before day
            # Efficiency: sample broadly then reject a portion of too-new customers
            cust_sample_idx = rng.integers(0, len(customer_ids), size=chunk_n)
            # Lines per order ~ Poisson around avg_lines, min 1 max 12
            lines_per = np.clip(rng.poisson(lam=max(avg_lines - 1, 0.8), size=chunk_n) + 1, 1, 12)

            for j in range(chunk_n):
                cid = int(customer_ids[cust_sample_idx[j]])
                # Ensure customer exists by registration date (soft)
                if cust_reg[cust_sample_idx[j]] > d:
                    # fallback: pick early customer
                    cid = int(customer_ids[int(rng.integers(0, max(1, len(customer_ids) // 10)))])

                ch_code = str(rng.choice(channel_codes, p=channel_probs))
                channel_id = int(channel_map[ch_code])
                if ch_code == "INSTORE":
                    store_id = int(cust_store[cust_sample_idx[j]]) if rng.random() < 0.7 else int(rng.choice(store_ids))
                    emp_list = emp_by_store.get(store_id, [])
                    employee_id = int(rng.choice(emp_list)) if emp_list else None
                else:
                    store_id = None if rng.random() < 0.7 else int(rng.choice(store_ids))
                    employee_id = None

                # Campaign attribution (~18% of orders during campaign days, boosted by lift)
                campaign_id = None
                choices = daily_campaign_choices[d]
                if len(choices) and rng.random() < min(0.35, 0.12 * daily_lift[d]):
                    campaign_id = int(rng.choice(choices))

                n_lines = int(lines_per[j])
                # Product draws
                chosen_idx = rng.choice(len(prod_ids), size=n_lines, replace=False if n_lines < len(prod_ids) else True, p=weights)

                gross = 0.0
                discount = 0.0
                net = 0.0
                cogs = 0.0
                line_buffer = []

                # Active promos that day
                active_promo_mask = (promo_start <= d) & (promo_end >= d)
                active_promo_idx = np.where(active_promo_mask)[0]

                for line_no, pidx in enumerate(chosen_idx, start=1):
                    qty = int(np.clip(rng.choice([1, 2, 3, 4], p=[0.72, 0.18, 0.07, 0.03]), 1, 4))
                    unit_price = float(prod_price[pidx])
                    unit_cost = float(prod_cost[pidx])
                    line_gross = round(unit_price * qty, 2)
                    line_disc = 0.0
                    promotion_id = None

                    if len(active_promo_idx) and rng.random() < 0.22:
                        pi = int(rng.choice(active_promo_idx))
                        promotion_id = int(promo_ids[pi])
                        if promo_type[pi] == "PercentOff" and promo_pct[pi] > 0:
                            line_disc = round(line_gross * float(promo_pct[pi]) / 100.0, 2)
                        elif promo_type[pi] == "AmountOff" and promo_amt[pi] > 0:
                            line_disc = round(min(float(promo_amt[pi]) * qty, line_gross * 0.5), 2)
                        elif promo_type[pi] == "BOGO" and qty >= 2:
                            line_disc = round(unit_price, 2)

                    line_net = round(line_gross - line_disc, 2)
                    line_cogs = round(unit_cost * qty, 2)

                    oid_item = order_item_id
                    order_item_id += 1
                    line_buffer.append(
                        {
                            "order_item_id": oid_item,
                            "order_id": order_id,
                            "line_number": line_no,
                            "product_id": int(prod_ids[pidx]),
                            "quantity": qty,
                            "unit_price": unit_price,
                            "unit_cost": unit_cost,
                            "discount_amount": line_disc,
                            "line_gross_amount": line_gross,
                            "line_net_amount": line_net,
                            "line_cogs_amount": line_cogs,
                            "promotion_id": promotion_id,
                            "is_gift": bool(rng.random() < 0.03),
                        }
                    )
                    if promotion_id is not None:
                        oip_rows.append(
                            {
                                "order_item_promotion_id": oip_id,
                                "order_item_id": oid_item,
                                "promotion_id": promotion_id,
                                "discount_allocated": line_disc,
                            }
                        )
                        oip_id += 1

                    gross += line_gross
                    discount += line_disc
                    net += line_net
                    cogs += line_cogs

                shipping = 0.0 if ch_code == "INSTORE" else float(rng.choice([0.0, 5.99, 7.99, 9.99], p=[0.45, 0.25, 0.2, 0.1]))
                tax = round(net * 0.08, 2)
                total = round(net + tax + shipping, 2)
                ots = ts_on_date(d, rng)

                orders_rows.append(
                    {
                        "order_id": order_id,
                        "order_number": f"ORD-{order_id:09d}",
                        "customer_id": cid,
                        "store_id": store_id,
                        "channel_id": channel_id,
                        "order_date": d.isoformat(),
                        "order_timestamp": ots.isoformat(sep=" "),
                        "order_status": "Completed",
                        "currency_code": "USD",
                        "gross_amount": round(gross, 2),
                        "discount_amount": round(discount, 2),
                        "tax_amount": tax,
                        "shipping_amount": shipping,
                        "net_amount": round(net, 2),
                        "total_amount": total,
                        "employee_id": employee_id,
                        "campaign_id": campaign_id,
                        "created_at": ots.isoformat(sep=" "),
                        "updated_at": ots.isoformat(sep=" "),
                    }
                )
                items_rows.extend(line_buffer)

                # Payment(s)
                method = int(rng.choice(pay_ids, p=pay_probs_store if ch_code == "INSTORE" else pay_probs_digital))
                if rng.random() < 0.08:
                    # split tender
                    a1 = round(total * float(rng.uniform(0.3, 0.7)), 2)
                    a2 = round(total - a1, 2)
                    for amt, mid in ((a1, method), (a2, int(rng.choice(pay_ids)))):
                        if amt <= 0:
                            continue
                        pay_rows.append(
                            {
                                "payment_id": payment_id,
                                "order_id": order_id,
                                "payment_method_id": mid,
                                "payment_timestamp": (ots + timedelta(seconds=int(rng.integers(5, 120)))).isoformat(sep=" "),
                                "payment_amount": amt,
                                "authorization_code": f"A{payment_id:08d}",
                                "payment_status": "Captured",
                                "created_at": ots.isoformat(sep=" "),
                            }
                        )
                        payment_id += 1
                else:
                    pay_rows.append(
                        {
                            "payment_id": payment_id,
                            "order_id": order_id,
                            "payment_method_id": method,
                            "payment_timestamp": (ots + timedelta(seconds=int(rng.integers(5, 120)))).isoformat(sep=" "),
                            "payment_amount": total if total > 0 else 0.01,
                            "authorization_code": f"A{payment_id:08d}",
                            "payment_status": "Captured",
                            "created_at": ots.isoformat(sep=" "),
                        }
                    )
                    payment_id += 1

                # Shipments for digital channels (~95%)
                if ch_code != "INSTORE" and rng.random() < 0.95:
                    ship_date = d + timedelta(days=int(rng.integers(1, 5)))
                    if ship_date > config.AS_OF_DATE:
                        ship_date = config.AS_OF_DATE
                    delivery = ship_date + timedelta(days=int(rng.integers(1, 6)))
                    if delivery > config.AS_OF_DATE:
                        delivery = config.AS_OF_DATE
                    sid = shipment_id
                    shipment_id += 1
                    ship_rows.append(
                        {
                            "shipment_id": sid,
                            "order_id": order_id,
                            "dc_id": int(rng.choice(dc_ids)),
                            "store_id": None,
                            "carrier_name": str(rng.choice(["UPS", "FedEx", "USPS", "OnTrac"])),
                            "tracking_number": f"1Z{sid:012d}",
                            "shipment_status": "Delivered" if delivery <= config.AS_OF_DATE else "Shipped",
                            "ship_date": ship_date.isoformat(),
                            "delivery_date": delivery.isoformat(),
                            "created_at": ship_date.isoformat() + " 09:00:00",
                        }
                    )
                    for lb in line_buffer:
                        ship_item_rows.append(
                            {
                                "shipment_item_id": shipment_item_id,
                                "shipment_id": sid,
                                "order_item_id": lb["order_item_id"],
                                "product_id": lb["product_id"],
                                "quantity_shipped": lb["quantity"],
                            }
                        )
                        shipment_item_id += 1

                # Returns — category-sensitive
                # Probability based on max line return rate
                line_rates = [product_return_rate.get(lb["product_id"], 0.06) for lb in line_buffer]
                p_return = min(0.35, float(np.mean(line_rates)) * 1.1)
                if rng.random() < p_return:
                    ret_date = d + timedelta(days=int(rng.integers(3, 28)))
                    if ret_date <= config.AS_OF_DATE:
                        # return 1 random line partially/fully
                        lb = line_buffer[int(rng.integers(0, len(line_buffer)))]
                        qty_ret = int(rng.integers(1, lb["quantity"] + 1))
                        unit_refund = round(lb["line_net_amount"] / lb["quantity"], 2)
                        rid = return_id
                        return_id += 1
                        refund = round(unit_refund * qty_ret, 2)
                        ret_rows.append(
                            {
                                "return_id": rid,
                                "order_id": order_id,
                                "customer_id": cid,
                                "return_date": ret_date.isoformat(),
                                "return_status": "Completed",
                                "refund_amount": refund,
                                "created_at": ret_date.isoformat() + " 12:00:00",
                            }
                        )
                        ret_item_rows.append(
                            {
                                "return_item_id": return_item_id,
                                "return_id": rid,
                                "order_item_id": lb["order_item_id"],
                                "product_id": lb["product_id"],
                                "quantity_returned": qty_ret,
                                "unit_refund_amount": unit_refund,
                                "restock_flag": bool(rng.random() < 0.8),
                                "return_reason_code": str(
                                    rng.choice(
                                        ["SIZE", "DEFECT", "CHANGED_MIND", "LATE", "WRONG_ITEM", "OTHER"],
                                        p=[0.28, 0.12, 0.35, 0.08, 0.07, 0.10],
                                    )
                                ),
                            }
                        )
                        return_item_id += 1

                order_id += 1

            append_csv(pd.DataFrame(orders_rows), "orders")
            append_csv(pd.DataFrame(items_rows), "order_items")
            if oip_rows:
                append_csv(pd.DataFrame(oip_rows), "order_item_promotions")
            append_csv(pd.DataFrame(pay_rows), "payments")
            if ship_rows:
                append_csv(pd.DataFrame(ship_rows), "shipments")
                append_csv(pd.DataFrame(ship_item_rows), "shipment_items")
            if ret_rows:
                append_csv(pd.DataFrame(ret_rows), "returns")
                append_csv(pd.DataFrame(ret_item_rows), "return_items")

        if (day_idx + 1) % 30 == 0:
            progress(f"  orders through {d.isoformat()} | order_id={order_id - 1:,}")

    save_state(
        "orders",
        {
            "n_orders": order_id - 1,
            "n_order_items": order_item_id - 1,
            "n_payments": payment_id - 1,
            "n_shipments": shipment_id - 1,
            "n_returns": return_id - 1,
        },
    )
    progress(
        f"Orders done: orders={order_id - 1:,}, items={order_item_id - 1:,}, "
        f"payments={payment_id - 1:,}, shipments={shipment_id - 1:,}, returns={return_id - 1:,}"
    )


if __name__ == "__main__":
    generate_orders()

"""
Generate marketing_campaigns, promotions, and (after orders) campaign_responses.

Campaigns influence order probability via lift_factor consumed by generate_orders.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from faker import Faker

from . import config
from .utils import (
    daterange,
    make_rng,
    progress,
    save_state,
    ts_on_date,
    write_csv,
    append_csv,
    chunked_range,
    read_csv,
)


def generate_marketing(include_responses: bool = False) -> None:
    """
    By default creates campaigns + promotions only.
    Responses are generated after orders when include_responses=True
    (also invoked from generate_all after order generation).
    """
    rng = make_rng(config.RANDOM_SEED + 21)
    fake = Faker()
    Faker.seed(config.RANDOM_SEED + 21)

    if not include_responses:
        _generate_campaigns_and_promotions(rng, fake)
    else:
        _generate_campaign_responses(rng)


def _generate_campaigns_and_promotions(rng: np.random.Generator, fake: Faker) -> None:
    progress("Generating marketing_campaigns & promotions ...")
    channels = pd.read_csv(config.OUTPUT_DIR / "channels.csv")
    channel_ids = channels["channel_id"].tolist()
    days = list(daterange(config.START_DATE, config.AS_OF_DATE))

    campaigns = []
    for i in range(1, config.N_CAMPAIGNS + 1):
        start = days[int(rng.integers(0, max(1, len(days) - 45)))]
        duration = int(rng.integers(7, 60))
        end = min(start + timedelta(days=duration), config.AS_OF_DATE)
        ctype = str(rng.choice(["Email", "SMS", "Social", "Display", "InStore", "Promo"], p=[0.35, 0.15, 0.2, 0.1, 0.1, 0.1]))
        # Lift between ~1.02 and 1.35 (campaigns increase purchase propensity)
        lift = float(np.round(rng.uniform(1.02, 1.35), 4))
        budget = float(np.round(rng.uniform(5_000, 400_000), 2))
        spend = float(np.round(budget * rng.uniform(0.75, 1.05), 2))
        status = "Closed" if end < config.AS_OF_DATE else "Active"
        campaigns.append(
            {
                "campaign_id": i,
                "campaign_code": f"CMP-{i:04d}",
                "campaign_name": f"{ctype} {fake.catch_phrase()}",
                "campaign_type": ctype,
                "channel_id": int(rng.choice(channel_ids)),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "budget_amount": budget,
                "actual_spend": spend,
                "objective_code": str(rng.choice(["Acquisition", "Retention", "Winback", "Awareness"])),
                "lift_factor": lift,
                "status_code": status,
                "created_at": start.isoformat() + " 00:00:00",
            }
        )
    write_csv(pd.DataFrame(campaigns), "marketing_campaigns")

    promos = []
    for i in range(1, config.N_PROMOTIONS + 1):
        start = days[int(rng.integers(0, max(1, len(days) - 20)))]
        end = min(start + timedelta(days=int(rng.integers(3, 40))), config.AS_OF_DATE)
        ptype = str(rng.choice(["PercentOff", "AmountOff", "BOGO", "Bundle", "FreeShipping"], p=[0.45, 0.25, 0.1, 0.1, 0.1]))
        disc_pct = float(np.round(rng.uniform(5, 40), 2)) if ptype == "PercentOff" else None
        disc_amt = float(np.round(rng.uniform(2, 25), 2)) if ptype == "AmountOff" else None
        promos.append(
            {
                "promotion_id": i,
                "promotion_code": f"PROMO-{i:04d}",
                "promotion_name": f"{ptype} {i}",
                "promotion_type": ptype,
                "discount_percent": disc_pct,
                "discount_amount": disc_amt,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "is_stackable": bool(rng.random() < 0.15),
                "is_active": end >= config.AS_OF_DATE,
            }
        )
    write_csv(pd.DataFrame(promos), "promotions")
    save_state("marketing", {"n_campaigns": len(campaigns), "n_promotions": len(promos)})
    progress(f"  campaigns={len(campaigns):,} promotions={len(promos):,}")


def _generate_campaign_responses(rng: np.random.Generator) -> None:
    """
    Build campaign_responses with referential integrity to customers/campaigns/orders.
    Volume: ~8-20 responses per campaign on average at full scale (scaled down in demo).
    Convert events preferentially attach to campaign-attributed orders.
    """
    progress("Generating campaign_responses ...")
    campaigns = read_csv("marketing_campaigns", parse_dates=["start_date", "end_date"])
    customers = read_csv("customers", usecols=["customer_id"])
    customer_ids = customers["customer_id"].to_numpy()

    # Prefer orders that already carry campaign_id
    orders = read_csv("orders", usecols=["order_id", "customer_id", "campaign_id", "order_date", "net_amount"])
    attributed = orders[orders["campaign_id"].notna()].copy()

    out_path = config.OUTPUT_DIR / "campaign_responses.csv"
    if out_path.exists():
        out_path.unlink()

    response_id = 1
    # Base non-convert responses
    responses_per_campaign = max(20, int(80 * (config.N_CUSTOMERS / 850_000)))
    for start, end in chunked_range(len(campaigns), 100):
        batch = []
        for _, camp in campaigns.iloc[start:end].iterrows():
            cid = int(camp["campaign_id"])
            n_resp = int(rng.poisson(responses_per_campaign) + 10)
            cust_sample = rng.choice(customer_ids, size=n_resp, replace=True)
            for cust in cust_sample:
                rtype = str(rng.choice(["Sent", "Open", "Click", "Unsubscribe"], p=[0.55, 0.28, 0.15, 0.02]))
                # Random timestamp within campaign window
                span = max(1, (camp["end_date"] - camp["start_date"]).days)
                ts_day = camp["start_date"] + timedelta(days=int(rng.integers(0, span + 1)))
                if ts_day.date() > config.AS_OF_DATE:
                    ts_day = pd.Timestamp(config.AS_OF_DATE)
                batch.append(
                    {
                        "campaign_response_id": response_id,
                        "campaign_id": cid,
                        "customer_id": int(cust),
                        "response_timestamp": ts_on_date(ts_day.date(), rng).isoformat(sep=" "),
                        "response_type": rtype,
                        "order_id": None,
                        "attributed_revenue": None,
                    }
                )
                response_id += 1
        append_csv(pd.DataFrame(batch), "campaign_responses")
        progress(f"  campaign response campaigns {end}/{len(campaigns)}")

    # Convert rows from attributed orders
    convert_batch = []
    for _, od in attributed.iterrows():
        convert_batch.append(
            {
                "campaign_response_id": response_id,
                "campaign_id": int(od["campaign_id"]),
                "customer_id": int(od["customer_id"]),
                "response_timestamp": f"{od['order_date']} 12:00:00",
                "response_type": "Convert",
                "order_id": int(od["order_id"]),
                "attributed_revenue": float(od["net_amount"]),
            }
        )
        response_id += 1
        if len(convert_batch) >= 50_000:
            append_csv(pd.DataFrame(convert_batch), "campaign_responses")
            convert_batch = []
    if convert_batch:
        append_csv(pd.DataFrame(convert_batch), "campaign_responses")

    progress(f"Campaign responses done. last_id={response_id - 1:,}")


if __name__ == "__main__":
    generate_marketing(include_responses=False)

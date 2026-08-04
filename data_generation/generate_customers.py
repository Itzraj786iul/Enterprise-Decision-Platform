"""
Generate customer master data: customers, loyalty_accounts, customer_addresses.

Distribution assumptions
------------------------
- ~850,000 customers over a 36-month acquisition ramp (not all registered on day 1)
- 55% Loyalty / 40% Guest / 5% Corporate
- Loyalty customers always receive a loyalty_accounts row
- Preferred store is drawn from active stores (Online/National customers skew online)
"""

from __future__ import annotations

import pandas as pd
from faker import Faker

from . import config
from .utils import (
    make_rng,
    progress,
    sha256_text,
    ts_on_date,
    weighted_category,
    write_csv,
    save_state,
    daterange,
)


def generate_customers() -> None:
    progress("Generating customers / loyalty / addresses ...")
    rng = make_rng(config.RANDOM_SEED + 11)
    fake = Faker()
    Faker.seed(config.RANDOM_SEED + 11)

    stores = pd.read_csv(config.OUTPUT_DIR / "stores.csv")
    channels = pd.read_csv(config.OUTPUT_DIR / "channels.csv")
    store_ids = stores["store_id"].tolist()
    channel_ids = channels["channel_id"].tolist()
    channel_code = dict(zip(channels["channel_id"], channels["channel_code"]))

    n = config.N_CUSTOMERS
    # Registration dates: ramp up over history (more recent customers slightly denser)
    all_days = list(daterange(config.START_DATE, config.AS_OF_DATE))
    day_idx = np_linspace_bias(len(all_days), n, rng)

    customer_types = weighted_category(config.CUSTOMER_TYPE_WEIGHTS, rng, size=n)

    rows = []
    loyalty_rows = []
    address_rows = []

    for i in range(n):
        cid = i + 1
        ctype = str(customer_types[i])
        reg_day = all_days[int(day_idx[i])]
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first}.{last}.{cid}@example.com".lower()
        phone = fake.numerify(text="##########")

        pref_store = int(rng.choice(store_ids))
        acq_channel = int(rng.choice(channel_ids))

        rows.append(
            {
                "customer_id": cid,
                "customer_number": f"CUST-{cid:09d}",
                "customer_type": ctype,
                "first_name": first if ctype != "Guest" else None,
                "last_name": last if ctype != "Guest" else None,
                "email_hash": sha256_text(email) if ctype != "Guest" else None,
                "phone_hash": sha256_text(phone) if rng.random() > 0.25 else None,
                "birth_year": int(rng.integers(1955, 2005)) if rng.random() > 0.3 else None,
                "gender_code": str(rng.choice(["M", "F", "U", "N"], p=[0.46, 0.46, 0.06, 0.02])),
                "registration_date": reg_day.isoformat(),
                "acquisition_channel_id": acq_channel,
                "preferred_store_id": pref_store,
                "is_active": bool(rng.random() > 0.04),
                "created_at": ts_on_date(reg_day, rng).isoformat(sep=" "),
                "updated_at": ts_on_date(reg_day, rng).isoformat(sep=" "),
            }
        )

        if ctype == "Loyalty":
            tier = str(rng.choice(["Bronze", "Silver", "Gold", "Platinum"], p=[0.55, 0.25, 0.15, 0.05]))
            loyalty_rows.append(
                {
                    "loyalty_account_id": len(loyalty_rows) + 1,
                    "customer_id": cid,
                    "loyalty_number": f"LY-{cid:09d}",
                    "tier_code": tier,
                    "enroll_date": reg_day.isoformat(),
                    "points_balance": int(rng.integers(0, 50000)),
                    "status_code": "Active" if rng.random() > 0.03 else "Suspended",
                    "created_at": ts_on_date(reg_day, rng).isoformat(sep=" "),
                    "updated_at": ts_on_date(reg_day, rng).isoformat(sep=" "),
                }
            )

        # 0-2 addresses; loyalty/corporate more likely to have address
        n_addr = int(rng.choice([0, 1, 2], p=[0.25, 0.60, 0.15] if ctype == "Guest" else [0.05, 0.70, 0.25]))
        for a in range(n_addr):
            address_rows.append(
                {
                    "address_id": len(address_rows) + 1,
                    "customer_id": cid,
                    "address_type": str(rng.choice(["Shipping", "Billing", "Both"], p=[0.6, 0.25, 0.15])),
                    "address_line1": fake.street_address(),
                    "city": fake.city(),
                    "state_code": fake.state_abbr(),
                    "postal_code": fake.postcode(),
                    "country_code": "US",
                    "is_primary": a == 0,
                    "created_at": ts_on_date(reg_day, rng).isoformat(sep=" "),
                }
            )

        if (i + 1) % 100_000 == 0:
            progress(f"  customers {i + 1:,}/{n:,}")

    write_csv(pd.DataFrame(rows), "customers")
    write_csv(pd.DataFrame(loyalty_rows), "loyalty_accounts")
    write_csv(pd.DataFrame(address_rows), "customer_addresses")

    save_state(
        "customers",
        {
            "n_customers": n,
            "n_loyalty": len(loyalty_rows),
            "n_addresses": len(address_rows),
            "channel_code_sample": channel_code,
        },
    )
    progress(f"Customers done: {n:,} customers, {len(loyalty_rows):,} loyalty, {len(address_rows):,} addresses")


def np_linspace_bias(n_days: int, n_samples: int, rng):
    """Sample day indices with mild recency bias."""
    import numpy as np

    x = np.linspace(0.0, 1.0, n_days)
    # Soft power bias toward recent days
    w = np.power(x + 0.05, 1.25)
    w /= w.sum()
    return rng.choice(np.arange(n_days), size=n_samples, p=w)


if __name__ == "__main__":
    generate_customers()

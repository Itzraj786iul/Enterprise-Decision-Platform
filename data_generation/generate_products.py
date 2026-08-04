"""
Generate merchandising & network master data.

Creates:
  calendar_date, regions, channels, payment_methods, distribution_centers,
  stores, product_categories, suppliers, products, product_suppliers,
  employees, price_history, cost_history

Business realism
----------------
- Product popularity ~ Zipf long-tail (few hero SKUs, many slow movers)
- Category hierarchy L1→L2 (L3 optional light)
- Suppliers have heterogeneous lead times and reliability by tier
- Stores assigned across 6 regions with format mix Flagship/Standard/Outlet
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from . import config
from .utils import (
    date_to_id,
    daterange,
    make_rng,
    progress,
    save_state,
    season_name,
    ts_on_date,
    weighted_category,
    write_csv,
    zipf_weights,
)


def generate_products() -> None:
    """Entry point used by generate_all — builds full product + network masters."""
    rng = make_rng(config.RANDOM_SEED + 1)
    fake = Faker()
    Faker.seed(config.RANDOM_SEED + 1)

    generate_calendar(rng)
    generate_channels()
    generate_payment_methods()
    generate_regions_stores_dcs(rng, fake)
    generate_categories()
    generate_suppliers(rng, fake)
    generate_product_catalog(rng, fake)
    generate_employees(rng, fake)
    progress("Product & network master data complete.")


def generate_calendar(rng: np.random.Generator) -> None:
    progress("Generating calendar_date ...")
    # Pad calendar beyond AS_OF for open-ended ETL safety
    start = config.START_DATE - timedelta(days=30)
    end = config.AS_OF_DATE + timedelta(days=60)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    rows = []
    for d in daterange(start, end):
        holiday = config.US_HOLIDAYS.get((d.month, d.day))
        # Approximate Thanksgiving: 4th Thursday in November
        if d.month == 11 and d.weekday() == 3 and 22 <= d.day <= 28:
            holiday = "Thanksgiving"
        rows.append(
            {
                "date_id": date_to_id(d),
                "full_date": d.isoformat(),
                "day_of_week": d.weekday() + 1,
                "day_name": day_names[d.weekday()],
                "week_of_year": int(d.isocalendar().week),
                "month_number": d.month,
                "month_name": month_names[d.month - 1],
                "quarter_number": (d.month - 1) // 3 + 1,
                "year_number": d.year,
                "fiscal_year": d.year,
                "fiscal_quarter": (d.month - 1) // 3 + 1,
                "is_weekend": d.weekday() >= 5,
                "is_holiday": holiday is not None,
                "holiday_name": holiday,
                "season_name": season_name(d),
            }
        )
    write_csv(pd.DataFrame(rows), "calendar_date")
    progress(f"  calendar rows={len(rows):,}")


def generate_channels() -> None:
    df = pd.DataFrame(
        [
            {"channel_id": 1, "channel_code": "INSTORE", "channel_name": "In-Store", "channel_group": "Physical", "is_active": True},
            {"channel_id": 2, "channel_code": "ONLINE", "channel_name": "Online", "channel_group": "Digital", "is_active": True},
            {"channel_id": 3, "channel_code": "MARKETPLACE", "channel_name": "Marketplace", "channel_group": "Digital", "is_active": True},
        ]
    )
    # created_at omitted optional; schema has default — include for CSV completeness
    df["created_at"] = "2023-01-01 00:00:00"
    write_csv(df, "channels")


def generate_payment_methods() -> None:
    df = pd.DataFrame(
        [
            {"payment_method_id": 1, "method_code": "VISA", "method_name": "Visa", "method_group": "Card", "is_active": True},
            {"payment_method_id": 2, "method_code": "MC", "method_name": "Mastercard", "method_group": "Card", "is_active": True},
            {"payment_method_id": 3, "method_code": "AMEX", "method_name": "Amex", "method_group": "Card", "is_active": True},
            {"payment_method_id": 4, "method_code": "CASH", "method_name": "Cash", "method_group": "Cash", "is_active": True},
            {"payment_method_id": 5, "method_code": "WALLET", "method_name": "Digital Wallet", "method_group": "Wallet", "is_active": True},
            {"payment_method_id": 6, "method_code": "GC", "method_name": "Gift Card", "method_group": "Other", "is_active": True},
        ]
    )
    write_csv(df, "payment_methods")


def generate_regions_stores_dcs(rng: np.random.Generator, fake: Faker) -> None:
    progress("Generating regions, DCs, stores ...")
    regions = []
    for i, (code, name) in enumerate(config.REGION_DEFS, start=1):
        regions.append(
            {
                "region_id": i,
                "region_code": code,
                "region_name": name,
                "country_code": "US",
                "is_active": True,
                "created_at": "2023-01-01 00:00:00",
                "updated_at": "2023-01-01 00:00:00",
            }
        )
    write_csv(pd.DataFrame(regions), "regions")

    dcs = []
    for i in range(1, config.N_DCS + 1):
        region_id = i if i <= config.N_REGIONS else config.N_REGIONS
        dcs.append(
            {
                "dc_id": i,
                "dc_code": f"DC-{i:02d}",
                "dc_name": f"Distribution Center {i}",
                "region_id": region_id,
                "city": fake.city(),
                "state_code": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "capacity_units": int(rng.integers(800_000, 2_000_000)),
                "is_active": True,
                "created_at": "2023-01-01 00:00:00",
                "updated_at": "2023-01-01 00:00:00",
            }
        )
    write_csv(pd.DataFrame(dcs), "distribution_centers")

    # Assign stores across regions 1-5 (physical); region 6 is Online/National hub
    physical_region_ids = list(range(1, 6))
    formats = weighted_category(config.STORE_FORMAT_WEIGHTS, rng, size=config.N_STORES)
    stores = []
    for i in range(1, config.N_STORES + 1):
        region_id = int(rng.choice(physical_region_ids))
        open_offset = int(rng.integers(365, 4000))
        open_date = config.START_DATE - timedelta(days=open_offset)
        fmt = str(formats[i - 1])
        sqft = {"Flagship": rng.integers(18000, 35000), "Standard": rng.integers(8000, 18000), "Outlet": rng.integers(5000, 10000)}[fmt]
        stores.append(
            {
                "store_id": i,
                "store_code": f"ST-{i:04d}",
                "store_name": f"{fake.city()} {fmt}",
                "region_id": region_id,
                "store_format": fmt,
                "address_line1": fake.street_address(),
                "city": fake.city(),
                "state_code": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "latitude": float(rng.uniform(25, 48)),
                "longitude": float(rng.uniform(-124, -68)),
                "selling_sq_ft": int(sqft),
                "open_date": open_date.isoformat(),
                "close_date": None,
                "is_active": True,
                "created_at": open_date.isoformat() + " 00:00:00",
                "updated_at": open_date.isoformat() + " 00:00:00",
            }
        )
    write_csv(pd.DataFrame(stores), "stores")


def generate_categories() -> None:
    progress("Generating product_categories ...")
    rows = []
    cat_id = 1
    l1_ids = {}
    for code, name, _ret in config.CATEGORY_L1:
        rows.append(
            {
                "category_id": cat_id,
                "category_code": code,
                "category_name": name,
                "parent_category_id": None,
                "category_level": 1,
                "is_active": True,
                "created_at": "2023-01-01 00:00:00",
            }
        )
        l1_ids[code] = cat_id
        cat_id += 1

    # ~4-6 L2 per L1
    l2_ids = []
    for code, name, _ in config.CATEGORY_L1:
        n_l2 = 5
        for j in range(1, n_l2 + 1):
            rows.append(
                {
                    "category_id": cat_id,
                    "category_code": f"{code}-L2-{j:02d}",
                    "category_name": f"{name} Subcat {j}",
                    "parent_category_id": l1_ids[code],
                    "category_level": 2,
                    "is_active": True,
                    "created_at": "2023-01-01 00:00:00",
                }
            )
            l2_ids.append((cat_id, code))
            cat_id += 1

    write_csv(pd.DataFrame(rows), "product_categories")
    save_state("categories", {"l2_ids": l2_ids, "return_rates": {c[0]: c[2] for c in config.CATEGORY_L1}})


def generate_suppliers(rng: np.random.Generator, fake: Faker) -> None:
    progress("Generating suppliers ...")
    tiers = weighted_category(config.SUPPLIER_TIER_WEIGHTS, rng, size=config.N_SUPPLIERS)
    rows = []
    for i in range(1, config.N_SUPPLIERS + 1):
        tier = str(tiers[i - 1])
        # Reliability & lead time by tier
        if tier == "Strategic":
            lead = int(rng.integers(5, 14))
            rel = float(rng.uniform(0.94, 0.99))
        elif tier == "Preferred":
            lead = int(rng.integers(10, 21))
            rel = float(rng.uniform(0.88, 0.96))
        else:
            lead = int(rng.integers(14, 45))
            rel = float(rng.uniform(0.75, 0.90))
        rows.append(
            {
                "supplier_id": i,
                "supplier_code": f"SUP-{i:03d}",
                "supplier_name": fake.company(),
                "supplier_tier": tier,
                "country_code": str(rng.choice(["US", "US", "US", "CN", "MX", "VN"], p=[0.55, 0.1, 0.05, 0.15, 0.1, 0.05])),
                "payment_terms_days": int(rng.choice([30, 45, 60, 90], p=[0.35, 0.35, 0.2, 0.1])),
                "lead_time_days_avg": lead,
                "reliability_score": round(rel, 4),
                "is_active": True,
                "created_at": "2023-01-01 00:00:00",
                "updated_at": "2023-01-01 00:00:00",
            }
        )
    write_csv(pd.DataFrame(rows), "suppliers")


def generate_product_catalog(rng: np.random.Generator, fake: Faker) -> None:
    progress("Generating products & sourcing ...")
    cats = pd.read_csv(config.OUTPUT_DIR / "product_categories.csv")
    l2 = cats[cats["category_level"] == 2]["category_id"].tolist()
    suppliers = pd.read_csv(config.OUTPUT_DIR / "suppliers.csv")
    supplier_ids = suppliers["supplier_id"].tolist()

    n = config.N_PRODUCTS
    popularity = zipf_weights(n, alpha=1.15)
    # Shuffle so ID order != popularity rank
    perm = rng.permutation(n)
    popularity = popularity[np.argsort(perm)]

    # Map category -> L1 code for return rates later
    cat_parent = cats.set_index("category_id")["parent_category_id"].to_dict()
    cat_code = cats.set_index("category_id")["category_code"].to_dict()
    l1_code_by_id = cats[cats["category_level"] == 1].set_index("category_id")["category_code"].to_dict()

    products = []
    product_suppliers = []
    price_hist = []
    cost_hist = []
    brands = [fake.unique.company().split()[0] for _ in range(80)]

    for i in range(1, n + 1):
        category_id = int(rng.choice(l2))
        primary_supplier = int(rng.choice(supplier_ids))
        list_price = float(np.round(rng.lognormal(mean=3.2, sigma=0.55), 2))
        list_price = float(np.clip(list_price, 2.99, 799.99))
        margin = float(rng.uniform(0.28, 0.62))
        unit_cost = float(np.round(list_price * (1 - margin), 2))
        launch = config.START_DATE - timedelta(days=int(rng.integers(0, 900)))
        active = bool(rng.random() > 0.08)
        disc = None if active else (launch + timedelta(days=int(rng.integers(180, 1000)))).isoformat()

        products.append(
            {
                "product_id": i,
                "sku": f"SKU-{i:06d}",
                "product_name": f"{rng.choice(brands)} {fake.word().title()} {i}",
                "brand_name": str(rng.choice(brands)),
                "category_id": category_id,
                "primary_supplier_id": primary_supplier,
                "unit_of_measure": "EA",
                "current_list_price": list_price,
                "current_unit_cost": unit_cost,
                "popularity_score": float(popularity[i - 1]),
                "is_active": active,
                "launch_date": launch.isoformat(),
                "discontinue_date": disc,
                "created_at": launch.isoformat() + " 00:00:00",
                "updated_at": launch.isoformat() + " 00:00:00",
            }
        )

        # Primary sourcing row
        product_suppliers.append(
            {
                "product_supplier_id": len(product_suppliers) + 1,
                "product_id": i,
                "supplier_id": primary_supplier,
                "is_primary": True,
                "supplier_sku": f"V-{primary_supplier}-{i}",
                "unit_cost": unit_cost,
                "effective_start": launch.isoformat(),
                "effective_end": None,
            }
        )
        # ~25% dual sourced
        if rng.random() < 0.25:
            alt = int(rng.choice([s for s in supplier_ids if s != primary_supplier]))
            product_suppliers.append(
                {
                    "product_supplier_id": len(product_suppliers) + 1,
                    "product_id": i,
                    "supplier_id": alt,
                    "is_primary": False,
                    "supplier_sku": f"V-{alt}-{i}",
                    "unit_cost": float(np.round(unit_cost * rng.uniform(0.95, 1.08), 2)),
                    "effective_start": launch.isoformat(),
                    "effective_end": None,
                }
            )

        price_hist.append(
            {
                "price_history_id": i,
                "product_id": i,
                "list_price": list_price,
                "effective_start": launch.isoformat(),
                "effective_end": None,
            }
        )
        cost_hist.append(
            {
                "cost_history_id": i,
                "product_id": i,
                "unit_cost": unit_cost,
                "effective_start": launch.isoformat(),
                "effective_end": None,
            }
        )

        if i % 3000 == 0:
            progress(f"  products {i:,}/{n:,}")

    write_csv(pd.DataFrame(products), "products")
    write_csv(pd.DataFrame(product_suppliers), "product_suppliers")
    write_csv(pd.DataFrame(price_hist), "price_history")
    write_csv(pd.DataFrame(cost_hist), "cost_history")

    # Persist L1 return rate mapping via category path for orders/returns
    return_by_l1 = {c[0]: c[2] for c in config.CATEGORY_L1}
    product_return_rate = {}
    for p in products:
        l2_id = p["category_id"]
        parent = cat_parent.get(l2_id)
        l1_code = l1_code_by_id.get(parent, "APPAREL")
        product_return_rate[str(p["product_id"])] = return_by_l1.get(l1_code, 0.06)

    save_state(
        "products",
        {
            "n_products": n,
            "product_return_rate": product_return_rate,
            "popularity_sum": float(popularity.sum()),
        },
    )


def generate_employees(rng: np.random.Generator, fake: Faker) -> None:
    progress("Generating employees ...")
    stores = pd.read_csv(config.OUTPUT_DIR / "stores.csv")
    rows = []
    eid = 1
    titles = ["Sales Associate", "Shift Lead", "Assistant Manager", "Store Manager", "Cashier"]
    for _, store in stores.iterrows():
        n_emp = int(rng.integers(*config.N_EMPLOYEES_PER_STORE))
        for _ in range(n_emp):
            hire = date.fromisoformat(store["open_date"]) + timedelta(days=int(rng.integers(0, 800)))
            rows.append(
                {
                    "employee_id": eid,
                    "employee_number": f"EMP-{eid:05d}",
                    "store_id": int(store["store_id"]),
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "job_title": str(rng.choice(titles, p=[0.55, 0.15, 0.12, 0.08, 0.10])),
                    "hire_date": hire.isoformat(),
                    "termination_date": None,
                    "is_active": True,
                    "created_at": hire.isoformat() + " 00:00:00",
                    "updated_at": hire.isoformat() + " 00:00:00",
                }
            )
            eid += 1
    write_csv(pd.DataFrame(rows), "employees")
    progress(f"  employees={len(rows):,}")


if __name__ == "__main__":
    generate_products()

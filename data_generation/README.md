# Synthetic Data Generation Guide

This folder produces **referentially consistent CSV extracts** for the OLTP schema in `database/schema.sql`.

Run commands from the **Enterprise Decision Platform repository root**.

## Prerequisites

```bash
cd enterprise-decision-platform
python -m pip install pandas numpy Faker
```

Python 3.10+ recommended.

## Quick start (demo scale)

Use demo mode first to validate the pipeline (minutes, not hours):

```bash
python -m data_generation.generate_all --demo
```

Outputs land in:

```text
data/generated/*.csv
data/generated/_state/*.json
```

## Full engagement scale

Targets:

| Entity | Approx rows |
|--------|-------------|
| Customers | 850,000 |
| Orders | 3,000,000 |
| Order items | ~9,000,000 |
| Products | 12,000 |
| Stores | 120 |
| Regions | 6 |
| Suppliers | 180 |
| Inventory snapshots | weekly stocked assortment × 36 months (default) |

```bash
python -m data_generation.generate_all
```

Optional daily snapshots (much larger disk/CPU):

```bash
python -m data_generation.generate_all --snapshot-mode daily
```

## Generation order (FK-safe)

`generate_all.py` runs stages in this order:

1. **products** — calendar, regions, channels, payment methods, DCs, stores, categories, suppliers, products, employees, price/cost history
2. **customers** — customers, loyalty accounts, addresses
3. **marketing** — campaigns + promotions
4. **orders** — orders, items, payments, shipments, returns (+ bridges)
5. **responses** — campaign_responses (needs orders for Convert events)
6. **inventory** — on-hand, snapshots, transactions, POs/receipts, labor hours

## Load into PostgreSQL

```bash
psql -U <user> -d <database> -f database/schema.sql
psql -U <user> -d <database> -f database/indexes.sql
psql -U <user> -d <database> -f database/views.sql
```

Then copy CSVs with `\copy oltp.<table> FROM 'data/generated/<table>.csv' CSV HEADER` (table-by-table in FK order), or use your preferred loader.

Suggested load order mirrors generation dependencies: reference masters → products/customers → marketing → orders ecosystem → inventory/procurement.

## Module map

| Script | Responsibility |
|--------|----------------|
| `config.py` | Scale knobs, dates, mix weights |
| `utils.py` | CSV I/O, seasonality, Zipf weights, RNG helpers |
| `generate_products.py` | Network + merchandising masters |
| `generate_customers.py` | Customer / loyalty / addresses |
| `generate_marketing.py` | Campaigns, promotions, responses |
| `generate_orders.py` | Commercial transaction graph |
| `generate_inventory.py` | Stock, snapshots, procurement, labor |
| `generate_all.py` | Orchestrator CLI |

## Design notes

See `docs/03_Synthetic_Data_Generation_Strategy.md` for per-table row counts, distributions, and realism rules.

## Smoke-test tip

```bash
python -m data_generation.generate_all --demo --skip inventory
```

Useful while iterating on order logic before paying for snapshot generation cost.

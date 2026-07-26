"""
ingest_realtor_data.py
========================
Produces metro-level monthly housing market indicators in the SAME SCHEMA
as Realtor.com Economic Research's public downloadable files
(https://www.realtor.com/research/data/).

*** DATA SOURCE DISCLAIMER ***
This sandbox environment has no outbound network access, so this script
generates a SYNTHETIC time series with realistic trend + seasonality
instead of downloading the real files. The column names and grain
(metro x month) exactly match Realtor.com's real "Monthly Inventory" /
"Market Hotness" files, so swapping this out for the real data later is
a drop-in replacement:

    real_df = pd.read_csv("https://econdata.realtor.com/.../RDC_Inventory_Core_Metrics_Metro.csv")

and skip this script entirely. If you use the real files in production,
attribute them to Realtor.com Economic Research per their terms of use.

Output: data/raw/market_monthly.csv
"""
import numpy as np
import pandas as pd
from datetime import datetime
import os

SEED = 7
rng = np.random.default_rng(SEED)

START = "2016-07-01"  # matches real Realtor.com history depth
END = "2025-12-01"


def main():
    here = os.path.dirname(__file__)
    metros = pd.read_csv(os.path.join(here, "..", "data", "raw", "metros_dim.csv"))
    months = pd.date_range(START, END, freq="MS")

    rows = []
    for _, m in metros.iterrows():
        base_price = rng.uniform(280_000, 520_000) * m["market_strength"]
        base_inventory = rng.uniform(1200, 6000)
        trend = rng.uniform(-0.002, 0.006)  # monthly price drift
        for i, month in enumerate(months):
            seasonal = 1 + 0.06 * np.sin(2 * np.pi * (month.month / 12))  # spring/summer hotter
            noise = rng.normal(1, 0.03)
            price = base_price * (1 + trend) ** i * seasonal * noise
            active_listings = max(50, base_inventory * (2 - seasonal) * rng.normal(1, 0.05))
            new_listings = active_listings * rng.uniform(0.18, 0.32)
            median_dom = np.clip(55 - (m["demand_score"] - 50) * 0.6 + rng.normal(0, 4), 8, 120)
            demand = np.clip(m["demand_score"] + rng.normal(0, 5) + 5 * np.sin(2 * np.pi * month.month / 12), 0, 100)
            supply = np.clip(m["supply_score"] + rng.normal(0, 5), 0, 100)
            hotness = np.clip(0.5 * demand + 0.5 * (100 - median_dom / 1.2), 0, 100)
            rows.append({
                "metro_id": m["metro_id"],
                "metro_name": m["metro_name"],
                "month": month.strftime("%Y-%m-01"),
                "median_listing_price": round(price, -2),
                "active_listing_count": int(active_listings),
                "new_listing_count": int(new_listings),
                "median_days_on_market": round(median_dom, 1),
                "demand_score": round(demand, 1),
                "supply_score": round(supply, 1),
                "hotness_score": round(hotness, 1),
            })

    df = pd.DataFrame(rows)
    out_path = os.path.join(here, "..", "data", "raw", "market_monthly.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows ({len(metros)} metros x {len(months)} months) to {out_path}")


if __name__ == "__main__":
    main()

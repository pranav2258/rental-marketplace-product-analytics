"""
load_to_snowflake.py
======================
Loads raw CSVs (the "S3 raw layer") into the analytical warehouse.

*** ENGINE NOTE ***
This sandbox has no network access, so Snowflake isn't reachable. This
script loads into SQLite instead -- the SQL in sql/ (CTEs, window
functions, QUALIFY-equivalents, etc.) is written in ANSI-compatible SQL
that runs on SQLite as-is and requires only trivial syntax changes
(e.g. QUALIFY -> subquery, DATEADD -> date()) to run on real Snowflake.
A `to_snowflake()` stub is included showing the swap.

Usage:
    python load_to_snowflake.py
"""
import sqlite3
import pandas as pd
import os

HERE = os.path.dirname(__file__)
RAW_DIR = os.path.join(HERE, "..", "data", "raw")
DB_PATH = os.path.join(HERE, "..", "data", "warehouse.db")

RAW_TABLES = {
    "raw_landlords": "landlords.csv",
    "raw_properties": "properties.csv",
    "raw_tenants": "tenants.csv",
    "raw_applications": "applications.csv",
    "raw_product_events": "product_events.csv",
    "raw_payments": "payments.csv",
    "raw_marketing_spend": "marketing_spend.csv",
    "raw_experiment_exposure": "experiment_exposure.csv",
    "raw_metros": "metros_dim.csv",
    "raw_market_monthly": "market_monthly.csv",
}


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)

    for table, csv_file in RAW_TABLES.items():
        path = os.path.join(RAW_DIR, csv_file)
        df = pd.read_csv(path)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Loaded {table:<28} {len(df):>8,} rows  <-  {csv_file}")

    # basic indexes to keep joins/window functions fast
    idx_stmts = [
        "CREATE INDEX IF NOT EXISTS ix_landlords_id ON raw_landlords(landlord_id)",
        "CREATE INDEX IF NOT EXISTS ix_properties_landlord ON raw_properties(landlord_id)",
        "CREATE INDEX IF NOT EXISTS ix_applications_property ON raw_applications(property_id)",
        "CREATE INDEX IF NOT EXISTS ix_events_user ON raw_product_events(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_payments_lease ON raw_payments(lease_id)",
        "CREATE INDEX IF NOT EXISTS ix_market_metro_month ON raw_market_monthly(metro_id, month)",
    ]
    for stmt in idx_stmts:
        conn.execute(stmt)
    conn.commit()
    conn.close()
    print(f"\nWarehouse ready at {os.path.abspath(DB_PATH)}")


def to_snowflake_example():
    """
    Reference only -- shows what swapping the destination looks like.
    Not executed in this sandbox (no network / credentials).
    """
    import snowflake.connector  # noqa
    example = """
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="ANALYTICS_WH", database="RENTAL_MARKETPLACE", schema="RAW",
    )
    for table, csv_file in RAW_TABLES.items():
        df = pd.read_csv(os.path.join(RAW_DIR, csv_file))
        write_pandas(conn, df, table.upper())
    """
    return example


if __name__ == "__main__":
    main()

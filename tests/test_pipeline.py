"""
tests/test_pipeline.py
=========================
Smoke tests for the SQL pipeline and generated marts. Run with:
    cd tests && python3 -m pytest test_pipeline.py -v
(or `python3 test_pipeline.py` to run without pytest)
"""
import sqlite3
import os
import sys

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "..", "data", "warehouse.db")


def get_conn():
    assert os.path.exists(DB_PATH), "warehouse.db not found -- run src/load_to_snowflake.py and src/run_sql_pipeline.py first"
    return sqlite3.connect(DB_PATH)


def test_landlords_row_count():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM stg_landlords").fetchone()[0]
    assert n > 1000, f"expected >1000 landlords, got {n}"


def test_no_duplicate_landlord_ids():
    conn = get_conn()
    n = conn.execute(
        "SELECT COUNT(*) FROM (SELECT landlord_id FROM stg_landlords GROUP BY landlord_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert n == 0, f"found {n} duplicate landlord_ids"


def test_activation_rate_in_plausible_range():
    conn = get_conn()
    rate = conn.execute("SELECT AVG(activated_7d) FROM stg_landlords").fetchone()[0]
    assert 0.05 < rate < 0.95, f"activation rate {rate} outside plausible range"


def test_funnel_steps_are_monotonic():
    """Each funnel step's landlord count should be <= the prior step's."""
    conn = get_conn()
    row = conn.execute("""
        SELECT
            SUM(CASE WHEN ts_property_added IS NOT NULL THEN 1 ELSE 0 END) AS a,
            SUM(CASE WHEN ts_listing_published IS NOT NULL THEN 1 ELSE 0 END) AS b,
            SUM(CASE WHEN ts_subscription_started IS NOT NULL THEN 1 ELSE 0 END) AS c
        FROM int_funnel_steps
    """).fetchone()
    assert row[0] >= row[1] >= row[2], f"funnel not monotonically decreasing: {row}"


def test_mart_market_opportunity_has_all_metros():
    conn = get_conn()
    n_metros = conn.execute("SELECT COUNT(*) FROM raw_metros").fetchone()[0]
    n_scored = conn.execute("SELECT COUNT(*) FROM mart_market_opportunity").fetchone()[0]
    assert n_metros == n_scored, f"expected {n_metros} scored metros, got {n_scored}"


def test_revenue_reconciliation_within_tolerance():
    conn = get_conn()
    mart_count = conn.execute("SELECT paying_landlords FROM mart_revenue ORDER BY month DESC LIMIT 1").fetchone()[0]
    source_count = conn.execute("SELECT COUNT(*) FROM stg_landlords WHERE is_paid = 1 AND churn_date IS NULL").fetchone()[0]
    diff_pct = abs(mart_count - source_count) / source_count
    assert diff_pct < 0.02, f"reconciliation diff {diff_pct:.1%} exceeds 2% tolerance"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failures += 1
    sys.exit(1 if failures else 0)

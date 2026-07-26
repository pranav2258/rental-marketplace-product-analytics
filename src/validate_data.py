"""
validate_data.py
===================
Runs the SQL quality tests in sql/04_quality_tests/ against the warehouse
and prints a pass/fail summary. Exits non-zero if any hard check fails,
so this can be wired into a CI job (see .github/workflows/pipeline.yml).
"""
import sqlite3
import re
import os
import sys
import glob

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "..", "data", "warehouse.db")
TEST_DIR = os.path.join(HERE, "..", "sql", "04_quality_tests")


def run_tests():
    conn = sqlite3.connect(DB_PATH)
    failures = 0
    print(f"{'TEST':<70} {'RESULT':<10}")
    print("-" * 82)

    for path in sorted(glob.glob(os.path.join(TEST_DIR, "*.sql"))):
        name = os.path.basename(path)
        sql = re.sub(r"--[^\n]*", "", open(path).read())
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        for i, stmt in enumerate(statements):
            rows = conn.execute(stmt).fetchall()
            label = f"{name} [{i+1}]"
            if "reconciliation" in name:
                # informational check, not a hard pass/fail gate
                diff = rows[0][2] if rows else None
                print(f"{label:<70} diff={diff}")
                continue
            ok = len(rows) == 0
            print(f"{label:<70} {'PASS' if ok else 'FAIL (' + str(len(rows)) + ' rows)'}")
            if not ok:
                failures += 1

    print("-" * 82)
    # row-count sanity checks
    for table, min_rows in [
        ("stg_landlords", 1000), ("stg_properties", 1000), ("stg_applications", 500),
        ("stg_payments", 500), ("stg_events", 1000),
    ]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        ok = n >= min_rows
        print(f"{'row_count_min: ' + table:<70} {'PASS' if ok else 'FAIL'} (n={n:,})")
        if not ok:
            failures += 1

    conn.close()
    print("-" * 82)
    if failures:
        print(f"\n{failures} check(s) FAILED.")
        sys.exit(1)
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    run_tests()

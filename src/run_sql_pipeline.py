"""
run_sql_pipeline.py
=====================
Applies every .sql file in sql/01_staging -> 02_intermediate -> 03_marts,
in order, against the warehouse (materializing each as a table). This is
the local stand-in for a dbt run / orchestrated SQL pipeline.
"""
import sqlite3
import os
import glob
import re

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "..", "data", "warehouse.db")
SQL_DIRS = ["01_staging", "02_intermediate", "03_marts"]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for d in SQL_DIRS:
        folder = os.path.join(HERE, "..", "sql", d)
        files = sorted(glob.glob(os.path.join(folder, "*.sql")))
        for f in files:
            name = os.path.basename(f)
            with open(f) as fh:
                sql_text = fh.read()
            # strip line comments, then split into statements
            sql_no_comments = re.sub(r"--[^\n]*", "", sql_text)
            for stmt in sql_no_comments.split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                m = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", stmt, re.IGNORECASE)
                if m:
                    cur.execute(f"DROP TABLE IF EXISTS {m.group(1)}")
                cur.execute(stmt)
            conn.commit()
            print(f"Applied {d}/{name}")
    conn.close()
    print("\nSQL pipeline complete.")


if __name__ == "__main__":
    main()

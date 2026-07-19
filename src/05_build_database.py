"""Step 4b - Build the SQLite database and verify SQL against pandas.

Loads the cleaned dataset into SQLite using sql/01_schema.sql, then runs the
same aggregations through both engines and asserts they agree. If the SQL and
the Python ever drift apart, this fails loudly rather than shipping two
deliverables that quietly disagree.

Run:  python src/05_build_database.py
"""

import sqlite3
import sys

import pandas as pd

from config import CLEAN_CSV, OUTPUT_DIR, ROOT, ensure_dirs

DB_PATH = OUTPUT_DIR / "ecommerce.db"
SCHEMA = ROOT / "sql" / "01_schema.sql"
TOLERANCE = 0.01  # rupees; guards against float round-trip noise


def build(df: pd.DataFrame) -> sqlite3.Connection:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    out = df.copy()
    out["Order_Date"] = out["Order_Date"].dt.strftime("%Y-%m-%d")
    out.to_sql("sales", conn, if_exists="append", index=False)
    conn.commit()

    n = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"Loaded {n:,} rows into {DB_PATH.name}\n")
    return conn


def verify(conn: sqlite3.Connection, df: pd.DataFrame) -> list[str]:
    """Run each check in both engines and compare."""
    failures: list[str] = []

    def check(label: str, sql_value: float, py_value: float) -> None:
        ok = abs(sql_value - py_value) <= TOLERANCE
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] {label:<34} sql={sql_value:>16,.2f}  py={py_value:>16,.2f}")
        if not ok:
            failures.append(f"{label}: sql={sql_value} vs py={py_value}")

    print("Cross-checking SQL against pandas")

    q = lambda s: conn.execute(s).fetchone()[0]  # noqa: E731
    check("Total sales", q("SELECT SUM(Sales_Amount) FROM sales"),
          df["Sales_Amount"].sum())
    check("Total profit", q("SELECT SUM(Profit) FROM sales"), df["Profit"].sum())
    check("Total orders", q("SELECT COUNT(DISTINCT Order_ID) FROM sales"),
          df["Order_ID"].nunique())
    check("Total quantity", q("SELECT SUM(Quantity) FROM sales"),
          df["Quantity"].sum())
    check("Average discount", q("SELECT AVG(Discount) FROM sales"),
          df["Discount"].mean())
    check("Unique customers", q("SELECT COUNT(DISTINCT Customer_ID) FROM sales"),
          df["Customer_ID"].nunique())

    # Group-level agreement, not just grand totals: a bad GROUP BY can still
    # sum to the right number overall.
    for col in ["State", "Product_Category", "Payment_Mode", "Product_Name"]:
        sql_group = pd.read_sql(
            f"SELECT {col} AS k, SUM(Sales_Amount) AS v FROM sales GROUP BY {col}",
            conn,
        ).set_index("k")["v"].sort_index()
        py_group = df.groupby(col)["Sales_Amount"].sum().sort_index()

        if list(sql_group.index) != list(py_group.index):
            failures.append(f"{col}: group keys differ")
            print(f"  [FAIL] {col:<34} group keys differ")
            continue

        worst = float((sql_group - py_group).abs().max())
        status = "OK  " if worst <= TOLERANCE else "FAIL"
        print(f"  [{status}] {col + ' group totals':<34} "
              f"max abs diff = {worst:.6f} across {len(sql_group)} groups")
        if worst > TOLERANCE:
            failures.append(f"{col}: max group diff {worst}")

    # Constraint enforcement actually works.
    try:
        conn.execute(
            "INSERT INTO sales (Order_ID, Order_Date, Customer_ID, "
            "Product_Category, Product_Name, State, City, Payment_Mode, "
            "Quantity, Sales_Amount, Discount, Profit, Order_Month, Order_Year) "
            "VALUES ('TEST', '2024-01-01', 'C', 'X', 'Y', 'S', 'C', 'P', "
            "-5, 100, 0.1, 10, '2024-01', 2024)"
        )
        conn.rollback()
        failures.append("CHECK constraint on Quantity did not fire")
        print("  [FAIL] Quantity CHECK constraint       accepted a negative value")
    except sqlite3.IntegrityError:
        print("  [OK  ] Quantity CHECK constraint       rejected negative quantity")

    return failures


def main() -> None:
    ensure_dirs()
    print("=" * 74)
    print("STEP 4b - SQLITE DATABASE BUILD & VERIFICATION")
    print("=" * 74 + "\n")

    df = pd.read_csv(CLEAN_CSV, parse_dates=["Order_Date"])
    conn = build(df)
    failures = verify(conn, df)
    conn.close()

    print()
    if failures:
        print("VERIFICATION FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("All checks passed - the SQL and Python pipelines agree.")
    print(f"\nDatabase: {DB_PATH.relative_to(ROOT)}")
    print("Run the analysis queries with:")
    print("  sqlite3 outputs/ecommerce.db < sql/02_analysis_queries.sql")


if __name__ == "__main__":
    main()

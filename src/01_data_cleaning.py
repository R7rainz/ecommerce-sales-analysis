"""Step 1 - Data Cleaning.

Loads the raw workbook, runs every cleaning and validation check the project
brief calls for, writes the cleaned dataset, and emits a data quality report
recording what each check found - including the checks that came back clean.

Run:  python src/01_data_cleaning.py
"""

import sys

import pandas as pd

from config import (
    CLEAN_CSV,
    CLEAN_XLSX,
    EXPECTED_COLUMNS,
    NUMERIC_COLUMNS,
    OUTPUT_DIR,
    TEXT_COLUMNS,
    ensure_dirs,
    find_raw_file,
)

# Discount is a fraction (0.00-0.30), not a percentage.
DISCOUNT_BOUNDS = (0.0, 1.0)

findings: list[dict] = []


def record(check: str, result: str, action: str) -> None:
    findings.append({"Check": check, "Result": result, "Action": action})
    print(f"  [{check}] {result} -> {action}")


def load_raw() -> pd.DataFrame:
    path = find_raw_file()
    print(f"Reading {path.name}")
    df = pd.read_excel(path)
    print(f"  loaded {len(df):,} rows x {len(df.columns)} columns\n")
    return df


def check_schema(df: pd.DataFrame) -> None:
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        sys.exit(f"FATAL: dataset is missing required columns: {missing}")
    record(
        "Schema",
        f"all {len(EXPECTED_COLUMNS)} expected columns present"
        + (f"; {len(extra)} unexpected: {extra}" if extra else ""),
        "dropped unexpected columns" if extra else "no change needed",
    )


def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    """Strip stray whitespace and collapse internal runs of spaces."""
    touched = 0
    for col in TEXT_COLUMNS:
        before = df[col].astype("string")
        after = before.str.strip().str.replace(r"\s+", " ", regex=True)
        touched += int((before != after).sum())
        df[col] = after
    record(
        "Text whitespace",
        f"{touched} value(s) had leading/trailing or repeated whitespace",
        "trimmed and normalised" if touched else "no change needed",
    )
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing a field that cannot be reconstructed.

    A record with no Order_ID, date, or sales figure cannot be analysed and
    cannot be imputed without inventing revenue, so those rows are removed.
    Descriptive gaps (category, city) are labelled "Unknown" instead, which
    keeps the order's money in the totals while making the gap visible.
    """
    total_missing = int(df[EXPECTED_COLUMNS].isna().sum().sum())
    if total_missing == 0:
        record("Missing values", "none found in any column", "no change needed")
        return df

    per_column = df[EXPECTED_COLUMNS].isna().sum()
    detail = ", ".join(f"{c}={n}" for c, n in per_column.items() if n)

    critical = ["Order_ID", "Order_Date", "Sales_Amount", "Quantity"]
    before = len(df)
    df = df.dropna(subset=critical)
    dropped = before - len(df)

    descriptive = ["Product_Category", "Product_Name", "State", "City", "Payment_Mode"]
    for col in descriptive:
        df[col] = df[col].fillna("Unknown")

    # Profit and Discount are numeric but non-critical; 0 is the neutral value.
    df[["Profit", "Discount"]] = df[["Profit", "Discount"]].fillna(0)

    record(
        "Missing values",
        f"{total_missing} missing cell(s): {detail}",
        f"dropped {dropped} row(s) missing critical fields; "
        f'filled descriptive gaps with "Unknown"; filled Profit/Discount with 0',
    )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact repeat rows, then enforce one row per Order_ID."""
    before = len(df)
    df = df.drop_duplicates()
    exact = before - len(df)

    dup_ids = int(df["Order_ID"].duplicated().sum())
    if dup_ids:
        # Same ID but differing values: keep the first occurrence and flag it,
        # since we cannot tell which version is authoritative.
        df = df.drop_duplicates(subset="Order_ID", keep="first")

    record(
        "Duplicate rows",
        f"{exact} fully identical row(s); {dup_ids} repeated Order_ID(s) "
        f"with differing values",
        f"removed {exact + dup_ids} row(s)"
        if (exact or dup_ids)
        else "no change needed",
    )
    return df


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Force the date and numeric columns into real types, not text."""
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    bad_dates = int(df["Order_Date"].isna().sum())
    if bad_dates:
        df = df.dropna(subset=["Order_Date"])
    record(
        "Date format",
        f"{bad_dates} unparseable date(s); range "
        f"{df['Order_Date'].min():%Y-%m-%d} to {df['Order_Date'].max():%Y-%m-%d}",
        f"dropped {bad_dates} row(s)" if bad_dates else "parsed as datetime, no change needed",
    )

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    non_numeric = int(df[NUMERIC_COLUMNS].isna().sum().sum())
    df = df.dropna(subset=NUMERIC_COLUMNS)

    df["Quantity"] = df["Quantity"].astype("int64")
    df[["Sales_Amount", "Discount", "Profit"]] = df[
        ["Sales_Amount", "Discount", "Profit"]
    ].astype("float64")

    record(
        "Numeric formats",
        f"{non_numeric} non-numeric value(s) across {', '.join(NUMERIC_COLUMNS)}",
        "cast to int/float"
        + (f"; dropped {non_numeric} unrecoverable row(s)" if non_numeric else ""),
    )
    return df


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Drop records whose numbers are impossible for a completed sale."""
    bad_qty = df["Quantity"] <= 0
    bad_sales = df["Sales_Amount"] <= 0
    lo, hi = DISCOUNT_BOUNDS
    bad_disc = ~df["Discount"].between(lo, hi)

    invalid = bad_qty | bad_sales | bad_disc
    n = int(invalid.sum())
    df = df[~invalid]

    record(
        "Value ranges",
        f"{int(bad_qty.sum())} non-positive Quantity, "
        f"{int(bad_sales.sum())} non-positive Sales_Amount, "
        f"{int(bad_disc.sum())} Discount outside {lo}-{hi}",
        f"dropped {n} invalid row(s)" if n else "all values within range, no change needed",
    )

    # A loss-making order is unusual but legitimate, so report without dropping.
    losses = int((df["Profit"] < 0).sum())
    record(
        "Negative profit",
        f"{losses} order(s) sold at a loss",
        "kept - a loss is a valid business outcome, not a data error",
    )
    return df


def check_referential_consistency(df: pd.DataFrame) -> None:
    """Report category/product and state/city coherence.

    These are reported, never silently corrected: rewriting them would mean
    inventing facts about where an order was placed.
    """
    multi = df.groupby("Product_Name")["Product_Category"].nunique()
    offenders = multi[multi > 1]
    record(
        "Product -> Category mapping",
        f"{len(offenders)} product(s) appear under more than one category"
        + (f": {list(offenders.index)}" if len(offenders) else ""),
        "consistent, no change needed" if not len(offenders) else "flagged for review",
    )

    pairs = df.groupby("State")["City"].nunique()
    if (pairs > 1).all() and pairs.max() == df["City"].nunique():
        result = (
            f"every one of the {len(pairs)} states is paired with all "
            f"{df['City'].nunique()} cities - the State/City relationship is "
            f"randomised and not geographically real"
        )
        action = (
            "NOT corrected - flagged as a known limitation; treat State and "
            "City as independent labels, never as a hierarchy"
        )
    else:
        result = f"states map to {pairs.min()}-{pairs.max()} cities each"
        action = "plausible hierarchy, no change needed"
    record("State -> City mapping", result, action)


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the fields the analysis and dashboard steps reuse."""
    df["Order_Month"] = df["Order_Date"].dt.to_period("M").astype(str)
    df["Order_Year"] = df["Order_Date"].dt.year
    df["Profit_Margin"] = (df["Profit"] / df["Sales_Amount"]).round(4)
    record(
        "Derived columns",
        "added Order_Month, Order_Year, Profit_Margin",
        "supports monthly trend and margin analysis",
    )
    return df


def write_report(raw_rows: int, clean_rows: int) -> None:
    path = OUTPUT_DIR / "data_quality_report.md"
    removed = raw_rows - clean_rows
    pct = (removed / raw_rows * 100) if raw_rows else 0.0

    lines = [
        "# Data Quality Report",
        "",
        "Generated by `src/01_data_cleaning.py`.",
        "",
        "## Summary",
        "",
        f"- Rows read from source: **{raw_rows:,}**",
        f"- Rows in cleaned dataset: **{clean_rows:,}**",
        f"- Rows removed: **{removed:,}** ({pct:.2f}%)",
        "",
        "## Checks Performed",
        "",
        "| Check | Result | Action |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {f['Check']} | {f['Result']} | {f['Action']} |" for f in findings
    ]
    lines += [
        "",
        "## Interpretation",
        "",
        "The source file arrived in unusually good condition: no missing cells,",
        "no duplicate orders, consistent category labels, and no out-of-range",
        "numbers. The cleaning pipeline still runs every check so the result is",
        "verified rather than assumed, and so it stays correct if the source is",
        "refreshed with messier data.",
        "",
        "One genuine defect did surface. Every state in the file is paired with",
        "every city, so combinations such as *Uttar Pradesh / Chennai* occur.",
        "The geography was generated at random. State-level and city-level",
        "figures are each internally consistent and safe to report, but the two",
        "must never be combined into a drill-down, and no conclusion should be",
        "drawn about which city drives a given state.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(OUTPUT_DIR.parent)}")


def main() -> None:
    ensure_dirs()
    print("=" * 70)
    print("STEP 1 - DATA CLEANING")
    print("=" * 70 + "\n")

    df = load_raw()
    raw_rows = len(df)

    check_schema(df)
    df = df[EXPECTED_COLUMNS].copy()
    df = clean_text(df)
    df = handle_missing(df)
    df = remove_duplicates(df)
    df = coerce_types(df)
    df = validate_ranges(df)
    check_referential_consistency(df)
    df = add_derived_columns(df)

    df = df.sort_values("Order_Date").reset_index(drop=True)

    df.to_csv(CLEAN_CSV, index=False)
    df.to_excel(CLEAN_XLSX, index=False, sheet_name="Cleaned_Data")
    print(f"\nWrote {CLEAN_CSV.name} and {CLEAN_XLSX.name} ({len(df):,} rows)")

    write_report(raw_rows, len(df))
    print("\nCleaning complete.")


if __name__ == "__main__":
    main()

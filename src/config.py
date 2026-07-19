"""Shared paths and constants for the e-commerce sales analysis project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
CHART_DIR = OUTPUT_DIR / "charts"
DASHBOARD_DIR = ROOT / "dashboard"
DOCS_DIR = ROOT / "docs"

# The raw file ships with a browser-mangled name ("...csv.xlsx" with a " (2)"
# suffix). Glob for it so the pipeline keeps working if it is ever renamed.
RAW_PATTERN = "*15000*.xlsx"

CLEAN_CSV = PROCESSED_DIR / "ecommerce_sales_cleaned.csv"
CLEAN_XLSX = PROCESSED_DIR / "ecommerce_sales_cleaned.xlsx"

EXPECTED_COLUMNS = [
    "Order_ID",
    "Order_Date",
    "Customer_ID",
    "Product_Category",
    "Product_Name",
    "State",
    "City",
    "Payment_Mode",
    "Quantity",
    "Sales_Amount",
    "Discount",
    "Profit",
]

TEXT_COLUMNS = [
    "Order_ID",
    "Customer_ID",
    "Product_Category",
    "Product_Name",
    "State",
    "City",
    "Payment_Mode",
]

NUMERIC_COLUMNS = ["Quantity", "Sales_Amount", "Discount", "Profit"]


def find_raw_file() -> Path:
    """Return the single raw workbook, failing loudly if it is missing."""
    matches = sorted(RAW_DIR.glob(RAW_PATTERN))
    if not matches:
        raise FileNotFoundError(
            f"No raw dataset matching {RAW_PATTERN!r} in {RAW_DIR}"
        )
    return matches[0]


def ensure_dirs() -> None:
    for directory in (PROCESSED_DIR, TABLE_DIR, CHART_DIR, DASHBOARD_DIR, DOCS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

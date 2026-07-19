"""Run the whole project end to end, in order.

    python run_all.py

Each step is independent and re-runnable; later steps read the outputs of
earlier ones, so the order matters. Any step that fails stops the run.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

STEPS = [
    ("01_data_cleaning.py", "Clean and validate the raw dataset"),
    ("02_data_analysis.py", "Compute KPIs and business insight tables"),
    ("03_significance_tests.py", "Test whether the rankings are real"),
    ("04_build_charts.py", "Render chart images"),
    ("05_build_database.py", "Build SQLite DB and verify SQL vs pandas"),
    ("06_build_excel.py", "Build the Excel analysis workbook"),
    ("07_build_dashboard.py", "Build the interactive HTML dashboard"),
]


def main() -> None:
    print("\n" + "#" * 74)
    print("#  E-COMMERCE SALES ANALYSIS - FULL PIPELINE")
    print("#" * 74)

    for i, (script, description) in enumerate(STEPS, start=1):
        print(f"\n>>> [{i}/{len(STEPS)}] {description}\n")
        result = subprocess.run([sys.executable, str(SRC / script)], cwd=ROOT)
        if result.returncode != 0:
            print(f"\nFAILED at step {i} ({script}). Stopping.")
            sys.exit(result.returncode)

    print("\n" + "#" * 74)
    print("#  PIPELINE COMPLETE")
    print("#" * 74)
    print("""
Deliverables:
  data/processed/ecommerce_sales_cleaned.csv    cleaned dataset
  data/processed/ecommerce_sales_cleaned.xlsx   cleaned dataset (Excel)
  outputs/ecommerce_analysis.xlsx               Excel analysis workbook
  outputs/ecommerce.db                          SQLite database
  outputs/data_quality_report.md                what cleaning found
  outputs/tables/*.csv                          every insight table
  outputs/charts/*.png                          chart images
  dashboard/index.html                          interactive dashboard
  docs/insights_summary.md                      the written summary
""")


if __name__ == "__main__":
    main()

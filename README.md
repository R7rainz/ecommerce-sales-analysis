# E-Commerce Sales Analysis

End-to-end analysis of 15,000 e-commerce sales records: cleaning, SQL, business
insight generation, and dashboards.

**The short version:** the aggregate figures are solid — Rs 4.94 Cr in sales,
Rs 73.78 L profit, 14.94% margin. But **none of the headline rankings survive
statistical testing.** Permutation and bootstrap tests show that "Rajasthan is the
top state", "Electronics is the most profitable category" and "Tablet is the
best-selling product" are all within random variation. The full reasoning is in
[`docs/insights_summary.md`](docs/insights_summary.md).

---

## Quick start

```bash
pip install -r requirements.txt
python run_all.py
```

Then open `dashboard/index.html` in any browser, or
`outputs/ecommerce_analysis.xlsx` in Excel.

Each stage can also be run on its own — they are independent and re-runnable:

```bash
python src/01_data_cleaning.py        # clean + validate, write quality report
python src/02_data_analysis.py        # KPIs and insight tables
python src/03_significance_tests.py   # are the rankings real?
python src/04_build_charts.py         # chart images
python src/05_build_database.py       # SQLite build + SQL-vs-pandas verification
python src/06_build_excel.py          # Excel workbook
python src/07_build_dashboard.py      # interactive HTML dashboard
```

---

## Project layout

```
├── data/
│   ├── raw/                       original source workbook (never modified)
│   └── processed/                 cleaned dataset (.csv and .xlsx)
├── src/
│   ├── config.py                  shared paths and column definitions
│   ├── viz_theme.py               chart theme and validated palette
│   ├── 01_data_cleaning.py        Step 1 — cleaning and validation
│   ├── 02_data_analysis.py        Steps 2 & 3 — KPIs and insights
│   ├── 03_significance_tests.py   Step 3b — permutation + bootstrap testing
│   ├── 04_build_charts.py         Step 4a — chart images
│   ├── 05_build_database.py       Step 4b — SQLite build and verification
│   ├── 06_build_excel.py          Step 4c — Excel workbook
│   └── 07_build_dashboard.py      Step 4d — interactive dashboard
├── sql/
│   ├── 01_schema.sql              table definitions, constraints, indexes
│   └── 02_analysis_queries.sql    every analysis query, commented
├── outputs/
│   ├── tables/                    each insight table as CSV
│   ├── charts/                    chart images (PNG)
│   ├── ecommerce_analysis.xlsx    10-sheet Excel workbook, 7 native charts
│   ├── ecommerce.db               SQLite database
│   ├── data_quality_report.md     what every cleaning check found
│   ├── analysis_summary.json      KPIs and question answers
│   └── significance_tests.json    full statistical test results
├── dashboard/index.html           self-contained interactive dashboard
├── docs/insights_summary.md       the written summary — read this one
└── run_all.py                     runs the whole pipeline in order
```

---

## Deliverables against the brief

| Brief requirement | Where it lives |
| --- | --- |
| Cleaned dataset file | `data/processed/ecommerce_sales_cleaned.csv` / `.xlsx` |
| Excel / SQL analysis file | `outputs/ecommerce_analysis.xlsx`, `sql/02_analysis_queries.sql` |
| Dashboard | `dashboard/index.html` (interactive) + Excel `KPI Dashboard` sheet |
| Summary of insights | `docs/insights_summary.md` |

**Step 1 — Data Cleaning.** Duplicate removal, missing-value handling, date and
numeric type coercion, range validation, referential consistency checks. Every
check is logged to `outputs/data_quality_report.md` with what it found and what
was done about it.

**Step 2 — Data Analysis.** Total sales, total profit, total orders, average
discount, total quantity sold, plus AOV, margin and customer count.

**Step 3 — Business Insights.** Sales by state, by category, by city; top 10
products; payment mode popularity; profit by category; monthly trend — each as a
CSV in `outputs/tables/` and a sheet in the Excel workbook.

**Step 4 — Dashboard.** KPI cards, sales by category, sales by state, top 10
products, monthly trend, payment mode distribution — in both the interactive
dashboard and the Excel workbook.

> **On Power BI:** the brief allows "Power BI **or** Excel". A `.pbix` file cannot
> be generated programmatically, so this project ships an Excel dashboard with
> native chart objects plus a self-contained interactive HTML dashboard. Every
> table in `outputs/tables/` is clean CSV and imports into Power BI directly if a
> `.pbix` is required.

---

## Notes on method

**Why there is a significance-testing step.** It is not in the brief. It was added
because the insight tables produce a "winner" for every dimension, and reporting
those winners without checking them would have been misleading — the whole dataset
turns out to be uniform random data. The test is what distinguishes a finding from
an artifact.

**SQL and Python are cross-verified.** `src/05_build_database.py` runs the same
aggregations through both engines and asserts they agree to within a paisa, at
both grand-total and per-group level. If they ever drift, the build fails rather
than shipping two deliverables that quietly disagree.

**Chart design decisions.**

- Bars for nominal categories (state, product, payment mode) all use a **single
  colour**. Shading them darker-where-taller would double-encode bar length as
  hue and waste the only free visual channel.
- The monthly trend uses a **zero-baseline axis**. Sales vary by under 4% month to
  month; a truncated axis would manufacture a dramatic trend that does not exist.
- The palette was checked with a colourblind-safety validator in both light and
  dark mode rather than chosen by eye.
- Every dashboard chart has a **data table view**, so no figure is reachable only
  through colour.

---

## Known limitation in the source data

Every one of the 7 states is paired with all 7 cities — all 49 combinations
appear, including impossible ones like *Uttar Pradesh / Chennai*. The geography
was randomly generated.

This is **flagged, not corrected**, since repairing it would mean inventing facts.
State-level and city-level figures are each valid on their own; **the two must
never be combined into a drill-down.**

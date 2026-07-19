"""Steps 2 and 3 - Data Analysis and Business Insights.

Computes the headline KPIs and every breakdown the brief asks for, writes each
one to outputs/tables/ as CSV, and saves a machine-readable summary that the
dashboard and Excel builders both consume.

Run:  python src/02_data_analysis.py
"""

import json

import pandas as pd

from config import CLEAN_CSV, OUTPUT_DIR, TABLE_DIR, ensure_dirs


def load_clean() -> pd.DataFrame:
    if not CLEAN_CSV.exists():
        raise FileNotFoundError(
            f"{CLEAN_CSV} not found - run src/01_data_cleaning.py first."
        )
    df = pd.read_csv(CLEAN_CSV, parse_dates=["Order_Date"])
    print(f"Loaded {len(df):,} cleaned rows\n")
    return df


def save(df: pd.DataFrame, name: str) -> pd.DataFrame:
    path = TABLE_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"  wrote tables/{name}.csv ({len(df)} rows)")
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    """Step 2 - the five headline numbers."""
    kpis = {
        "total_sales": float(df["Sales_Amount"].sum()),
        "total_profit": float(df["Profit"].sum()),
        "total_orders": int(df["Order_ID"].nunique()),
        "total_quantity": int(df["Quantity"].sum()),
        "average_discount": float(df["Discount"].mean()),
        "unique_customers": int(df["Customer_ID"].nunique()),
        "average_order_value": float(df["Sales_Amount"].mean()),
        "overall_profit_margin": float(df["Profit"].sum() / df["Sales_Amount"].sum()),
        "date_from": df["Order_Date"].min().strftime("%Y-%m-%d"),
        "date_to": df["Order_Date"].max().strftime("%Y-%m-%d"),
    }

    print("STEP 2 - KEY PERFORMANCE INDICATORS")
    print(f"  Total Sales          Rs {kpis['total_sales']:>15,.2f}")
    print(f"  Total Profit         Rs {kpis['total_profit']:>15,.2f}")
    print(f"  Total Orders            {kpis['total_orders']:>15,}")
    print(f"  Total Quantity Sold     {kpis['total_quantity']:>15,}")
    print(f"  Average Discount        {kpis['average_discount']:>14.2%}")
    print(f"  Profit Margin           {kpis['overall_profit_margin']:>14.2%}")
    print(f"  Unique Customers        {kpis['unique_customers']:>15,}")
    print(f"  Avg Order Value      Rs {kpis['average_order_value']:>15,.2f}")
    print()

    save(pd.DataFrame([kpis]), "kpi_summary")
    return kpis


def group_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Standard revenue/profit rollup used by most of the insight tables."""
    out = (
        df.groupby(by)
        .agg(
            Total_Sales=("Sales_Amount", "sum"),
            Total_Profit=("Profit", "sum"),
            Total_Orders=("Order_ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
            Avg_Discount=("Discount", "mean"),
        )
        .reset_index()
        .sort_values("Total_Sales", ascending=False)
    )
    out["Profit_Margin"] = out["Total_Profit"] / out["Total_Sales"]
    out["Sales_Share"] = out["Total_Sales"] / out["Total_Sales"].sum()
    return out.round(
        {
            "Total_Sales": 2,
            "Total_Profit": 2,
            "Avg_Discount": 4,
            "Profit_Margin": 4,
            "Sales_Share": 4,
        }
    )


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Month-by-month revenue with growth, on a gap-free calendar."""
    monthly = (
        df.groupby("Order_Month")
        .agg(
            Total_Sales=("Sales_Amount", "sum"),
            Total_Profit=("Profit", "sum"),
            Total_Orders=("Order_ID", "nunique"),
            Total_Quantity=("Quantity", "sum"),
        )
        .reset_index()
    )

    # Reindex onto a complete month range so a zero-sales month shows as a dip
    # rather than silently vanishing from the line.
    full = pd.period_range(
        df["Order_Date"].min(), df["Order_Date"].max(), freq="M"
    ).astype(str)
    monthly = (
        monthly.set_index("Order_Month")
        .reindex(full, fill_value=0)
        .rename_axis("Order_Month")
        .reset_index()
    )

    monthly["MoM_Growth"] = monthly["Total_Sales"].pct_change().round(4)
    return monthly.round({"Total_Sales": 2, "Total_Profit": 2})


def main() -> None:
    ensure_dirs()
    print("=" * 70)
    print("STEPS 2 & 3 - ANALYSIS AND BUSINESS INSIGHTS")
    print("=" * 70 + "\n")

    df = load_clean()
    kpis = compute_kpis(df)

    print("STEP 3 - BUSINESS INSIGHT TABLES")
    by_state = save(group_summary(df, "State"), "sales_by_state")
    by_category = save(group_summary(df, "Product_Category"), "sales_by_category")
    by_payment = save(group_summary(df, "Payment_Mode"), "sales_by_payment_mode")
    by_city = save(group_summary(df, "City"), "sales_by_city")

    products = group_summary(df, "Product_Name")
    save(products, "sales_by_product")
    top10 = save(products.head(10), "top_10_products")

    trend = save(monthly_trend(df), "monthly_sales_trend")

    save(
        group_summary(df, "Product_Category").sort_values(
            "Total_Profit", ascending=False
        ),
        "profit_by_category",
    )

    # Category x month, for the stacked view in the dashboard.
    save(
        df.pivot_table(
            index="Order_Month",
            columns="Product_Category",
            values="Sales_Amount",
            aggfunc="sum",
            fill_value=0,
        )
        .round(2)
        .reset_index(),
        "monthly_sales_by_category",
    )

    # ---- Answers to the five business questions -------------------------
    top_state = by_state.iloc[0]
    top_cat_profit = by_category.sort_values("Total_Profit", ascending=False).iloc[0]
    top_product = products.iloc[0]
    top_payment = by_payment.sort_values("Total_Orders", ascending=False).iloc[0]

    best_month = trend.loc[trend["Total_Sales"].idxmax()]
    worst_month = trend.loc[trend["Total_Sales"].idxmin()]
    first_half = trend.head(len(trend) // 2)["Total_Sales"].sum()
    second_half = trend.tail(len(trend) // 2)["Total_Sales"].sum()
    drift = (second_half - first_half) / first_half

    answers = {
        "q1_highest_sales_state": {
            "answer": top_state["State"],
            "total_sales": float(top_state["Total_Sales"]),
            "share_of_sales": float(top_state["Sales_Share"]),
            "runner_up": by_state.iloc[1]["State"],
            "gap_vs_runner_up": float(
                top_state["Total_Sales"] - by_state.iloc[1]["Total_Sales"]
            ),
        },
        "q2_most_profitable_category": {
            "answer": top_cat_profit["Product_Category"],
            "total_profit": float(top_cat_profit["Total_Profit"]),
            "profit_margin": float(top_cat_profit["Profit_Margin"]),
            "highest_margin_category": by_category.sort_values(
                "Profit_Margin", ascending=False
            ).iloc[0]["Product_Category"],
        },
        "q3_highest_revenue_products": {
            "answer": top_product["Product_Name"],
            "total_sales": float(top_product["Total_Sales"]),
            "top_10": top10["Product_Name"].tolist(),
            "top_10_share_of_sales": float(top10["Sales_Share"].sum()),
        },
        "q4_most_used_payment_method": {
            "answer": top_payment["Payment_Mode"],
            "orders": int(top_payment["Total_Orders"]),
            "share_of_orders": float(
                top_payment["Total_Orders"] / by_payment["Total_Orders"].sum()
            ),
        },
        "q5_monthly_sales_trend": {
            "best_month": str(best_month["Order_Month"]),
            "best_month_sales": float(best_month["Total_Sales"]),
            "worst_month": str(worst_month["Order_Month"]),
            "worst_month_sales": float(worst_month["Total_Sales"]),
            "first_half_vs_second_half_change": float(drift),
            "mean_abs_mom_growth": float(trend["MoM_Growth"].abs().mean()),
        },
    }

    print("\nANSWERS TO THE FIVE BUSINESS QUESTIONS")
    print(
        f"  1. Highest sales state ....... {answers['q1_highest_sales_state']['answer']}"
        f" (Rs {answers['q1_highest_sales_state']['total_sales']:,.0f}, "
        f"{answers['q1_highest_sales_state']['share_of_sales']:.1%})"
    )
    print(
        f"  2. Most profitable category .. {answers['q2_most_profitable_category']['answer']}"
        f" (Rs {answers['q2_most_profitable_category']['total_profit']:,.0f})"
    )
    print(
        f"  3. Top revenue product ....... {answers['q3_highest_revenue_products']['answer']}"
        f" (Rs {answers['q3_highest_revenue_products']['total_sales']:,.0f})"
    )
    print(
        f"  4. Most used payment mode .... {answers['q4_most_used_payment_method']['answer']}"
        f" ({answers['q4_most_used_payment_method']['share_of_orders']:.1%} of orders)"
    )
    print(
        f"  5. Monthly trend ............. peak {answers['q5_monthly_sales_trend']['best_month']}, "
        f"trough {answers['q5_monthly_sales_trend']['worst_month']}, "
        f"H2 vs H1 {answers['q5_monthly_sales_trend']['first_half_vs_second_half_change']:+.1%}"
    )

    payload = {"kpis": kpis, "answers": answers}
    (OUTPUT_DIR / "analysis_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print("\nWrote outputs/analysis_summary.json")
    print("Analysis complete.")


if __name__ == "__main__":
    main()

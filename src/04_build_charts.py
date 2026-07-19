"""Step 4a - Chart images for the dashboard and the written summary.

Run:  python src/04_build_charts.py
"""

import json

import pandas as pd

from config import CHART_DIR, OUTPUT_DIR, TABLE_DIR, ensure_dirs
from viz_theme import (
    DEEMPHASIS,
    GRID,
    PRIMARY,
    SERIES,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    finish,
    money_axis,
    new_axes,
    rupees,
)


def table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / f"{name}.csv")


def bar_labels(ax, bars, values, fmt=rupees, pad_frac=0.012):
    """Direct-label every bar - required relief for low-contrast fills."""
    span = max(values) if len(values) else 1
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + span * pad_frac,
            fmt(value),
            ha="center", va="bottom",
            fontsize=9, color=TEXT_SECONDARY,
        )


def chart_sales_by_category() -> None:
    df = table("sales_by_category").sort_values("Total_Sales", ascending=False)
    fig, ax = new_axes(
        "Sales by Product Category",
        "All five categories fall within 5% of each other - the ranking is not "
        "statistically meaningful (permutation p = 0.58).",
    )
    bars = ax.bar(df["Product_Category"], df["Total_Sales"],
                  color=PRIMARY, width=0.62, zorder=3)
    bar_labels(ax, bars, df["Total_Sales"].tolist())
    money_axis(ax)
    ax.set_ylim(0, df["Total_Sales"].max() * 1.16)
    ax.set_ylabel("")
    finish(fig, CHART_DIR / "sales_by_category.png")


def chart_sales_by_state() -> None:
    df = table("sales_by_state").sort_values("Total_Sales", ascending=False)
    fig, ax = new_axes(
        "Sales by State",
        "Rajasthan leads, but holds the top spot in only 39% of bootstrap "
        "resamples - treat the order as interchangeable.",
    )
    bars = ax.bar(df["State"], df["Total_Sales"], color=PRIMARY, width=0.62, zorder=3)
    bar_labels(ax, bars, df["Total_Sales"].tolist())
    money_axis(ax)
    ax.set_ylim(0, df["Total_Sales"].max() * 1.16)
    ax.tick_params(axis="x", labelrotation=0, labelsize=9)
    finish(fig, CHART_DIR / "sales_by_state.png")


def chart_top_products() -> None:
    df = table("top_10_products").sort_values("Total_Sales")
    fig, ax = new_axes(
        "Top 10 Products by Sales",
        "Revenue spread across the top ten is under 12%, consistent with "
        "uniform random demand rather than genuine bestsellers.",
        figsize=(10, 6.2),
    )
    bars = ax.barh(df["Product_Name"], df["Total_Sales"],
                   color=PRIMARY, height=0.66, zorder=3)
    span = df["Total_Sales"].max()
    for bar, value in zip(bars, df["Total_Sales"]):
        ax.text(value + span * 0.012, bar.get_y() + bar.get_height() / 2,
                rupees(value), va="center", ha="left",
                fontsize=9, color=TEXT_SECONDARY)
    money_axis(ax, "x")
    ax.set_xlim(0, span * 1.15)
    ax.grid(axis="x", color=GRID, linewidth=1, alpha=0.9)
    ax.grid(axis="y", visible=False)
    finish(fig, CHART_DIR / "top_10_products.png")


def chart_payment_modes() -> None:
    df = table("sales_by_payment_mode").sort_values("Total_Orders", ascending=False)
    total = df["Total_Orders"].sum()
    fig, ax = new_axes(
        "Orders by Payment Mode",
        "Five modes, each carrying ~20% of orders. An even split, not a "
        "customer preference.",
    )
    bars = ax.bar(df["Payment_Mode"], df["Total_Orders"],
                  color=PRIMARY, width=0.62, zorder=3)
    bar_labels(
        ax, bars, df["Total_Orders"].tolist(),
        fmt=lambda v, _p=None: f"{v:,.0f}\n({v / total:.1%})",
    )
    ax.axhline(total / len(df), color=TEXT_MUTED, linewidth=1.5,
               linestyle=(0, (4, 3)), zorder=4)
    ax.text(len(df) - 0.42, total / len(df), "  even split",
            va="center", ha="left", fontsize=8.5, color=TEXT_MUTED)
    ax.set_ylim(0, df["Total_Orders"].max() * 1.22)
    ax.set_ylabel("Orders", fontsize=9.5, color=TEXT_SECONDARY)
    finish(fig, CHART_DIR / "payment_mode_distribution.png")


def chart_monthly_trend() -> None:
    df = table("monthly_sales_trend")
    mean = df["Total_Sales"].mean()

    fig, ax = new_axes(
        "Monthly Sales Trend",
        "Zero-baseline axis. Sales hold flat across 24 months (linear fit "
        "R2 = 0.008); the wobble is noise, not seasonality.",
    )
    x = range(len(df))
    # +/-5% reference band makes the flatness visible rather than asserted.
    ax.fill_between(x, mean * 0.95, mean * 1.05,
                    color=PRIMARY, alpha=0.10, zorder=1)
    ax.axhline(mean, color=TEXT_MUTED, linewidth=1.5,
               linestyle=(0, (4, 3)), zorder=2)
    ax.plot(x, df["Total_Sales"], color=PRIMARY, linewidth=2,
            marker="o", markersize=5, markerfacecolor=PRIMARY,
            markeredgecolor="#fcfcfb", markeredgewidth=1.5, zorder=3)

    ax.text(len(df) - 0.5, mean * 1.05, " +/-5% band",
            fontsize=8.5, color=TEXT_MUTED, va="bottom", ha="right")
    ax.set_ylim(0, df["Total_Sales"].max() * 1.22)
    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels(df["Order_Month"][::2], rotation=45, ha="right", fontsize=8.5)
    money_axis(ax)
    finish(fig, CHART_DIR / "monthly_sales_trend.png")


def chart_profit_by_category() -> None:
    df = table("profit_by_category").sort_values("Total_Profit", ascending=False)
    fig, ax = new_axes(
        "Profit by Product Category",
        "Profit tracks revenue almost exactly - every category returns a "
        "~15% margin, so mix decisions cannot be made on margin here.",
    )
    bars = ax.bar(df["Product_Category"], df["Total_Profit"],
                  color=PRIMARY, width=0.62, zorder=3)
    for bar, profit, margin in zip(bars, df["Total_Profit"], df["Profit_Margin"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + df["Total_Profit"].max() * 0.012,
                f"{rupees(profit)}\n({margin:.1%} margin)",
                ha="center", va="bottom", fontsize=8.5, color=TEXT_SECONDARY)
    money_axis(ax)
    ax.set_ylim(0, df["Total_Profit"].max() * 1.24)
    finish(fig, CHART_DIR / "profit_by_category.png")


def chart_significance() -> None:
    """The chart that carries the project's real finding.

    A dot plot of each leader's bootstrap margin over its nearest rival. Any
    interval crossing zero means that leader is not reliably the leader.
    """
    df = table("significance_tests").iloc[::-1]

    fig, ax = new_axes(
        "Is any ranking real? Bootstrap margin of each leader over its rival",
        "95% confidence intervals. Every interval crosses zero, so no leader "
        "in this dataset is statistically distinguishable from its runner-up.",
        figsize=(10, 5.2),
    )

    y = range(len(df))
    ax.axvline(0, color=TEXT_PRIMARY, linewidth=1.5, zorder=2)
    for i, row in zip(y, df.itertuples()):
        ax.plot([row.Margin_CI_Low, row.Margin_CI_High], [i, i],
                color=DEEMPHASIS, linewidth=6, solid_capstyle="round", zorder=3)
        ax.plot(row.Observed_Margin, i, "o", markersize=9, color=PRIMARY,
                markeredgecolor="#fcfcfb", markeredgewidth=1.5, zorder=4)
        # Left-align at the interval start and sit the label on an opaque chip:
        # the zero rule runs through this band and would otherwise strike it out.
        ax.text(row.Margin_CI_Low, i + 0.26,
                f"{row.Leader} holds top in {row.Leader_Retention_Rate:.0%} of resamples",
                fontsize=8.5, color=TEXT_SECONDARY, va="bottom", ha="left", zorder=6,
                bbox=dict(facecolor="#fcfcfb", edgecolor="none",
                          boxstyle="round,pad=0.22"))

    ax.set_yticks(list(y))
    ax.set_yticklabels([d.replace("_", " ") for d in df["Dimension"]],
                       fontsize=10, color=TEXT_PRIMARY)
    ax.set_xlabel("Leader's sales margin over nearest rival", fontsize=9,
                  color=TEXT_MUTED, labelpad=8)
    money_axis(ax, "x")
    ax.grid(axis="x", color=GRID, linewidth=1, alpha=0.9)
    ax.grid(axis="y", visible=False)
    ax.margins(y=0.14)
    finish(fig, CHART_DIR / "significance_margins.png")


def chart_monthly_by_category() -> None:
    """Stacked view - the one place a categorical palette is warranted."""
    df = table("monthly_sales_by_category")
    cats = [c for c in df.columns if c != "Order_Month"]

    fig, ax = new_axes(
        "Monthly Sales by Category",
        "Category mix stays stable month to month. Segments are direct-labelled "
        "in the table view; no category gains or loses share over two years.",
        figsize=(10, 5.8),
    )
    bottom = pd.Series(0.0, index=df.index)
    for i, cat in enumerate(cats):
        ax.bar(df["Order_Month"], df[cat], bottom=bottom,
               color=SERIES[i % len(SERIES)], width=0.72,
               label=cat, linewidth=1.4, edgecolor="#fcfcfb", zorder=3)
        bottom += df[cat]

    ax.set_xticks(range(0, len(df), 2))
    ax.set_xticklabels(df["Order_Month"][::2], rotation=45, ha="right", fontsize=8.5)
    money_axis(ax)
    legend = ax.legend(frameon=False, ncol=5, fontsize=9,
                       loc="upper center", bbox_to_anchor=(0.5, 1.13))
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)
    finish(fig, CHART_DIR / "monthly_sales_by_category.png")


def main() -> None:
    ensure_dirs()
    print("=" * 70)
    print("STEP 4a - CHARTS")
    print("=" * 70 + "\n")

    if not (OUTPUT_DIR / "analysis_summary.json").exists():
        raise FileNotFoundError("Run src/02_data_analysis.py first.")

    chart_sales_by_category()
    chart_sales_by_state()
    chart_top_products()
    chart_payment_modes()
    chart_monthly_trend()
    chart_profit_by_category()
    chart_monthly_by_category()
    chart_significance()

    print(f"\n8 charts written to {CHART_DIR.relative_to(OUTPUT_DIR.parent)}/")


if __name__ == "__main__":
    main()

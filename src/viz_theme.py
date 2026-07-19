"""Shared chart theme.

Palette values come from the validated reference palette and were checked with
the data-viz validator before use:

    categorical slots 1-5, light  -> all checks pass
    categorical slots 1-5, dark   -> all checks pass

Design rules applied throughout, each one deliberate:

  * Nominal categories (state, product, category, payment mode) have no natural
    order, so every bar carries the SAME hue. Shading bars darker-where-bigger
    would double-encode bar length as colour and waste the only free channel.
  * Magnitude axes always start at zero. This dataset varies by under 4% month
    to month; a truncated axis would invent a trend that is not there.
  * Grid and axes stay recessive; the data is the only saturated thing.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --- palette ---------------------------------------------------------------
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8880"
GRID = "#e6e5e1"

SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a"]
PRIMARY = SERIES[0]
DEEMPHASIS = "#c9c8c2"  # for the "one series matters, rest are context" form

FIGSIZE = (10, 5.6)
DPI = 160


def rupees(value: float, _pos=None) -> str:
    """Compact Indian-rupee axis labels."""
    if abs(value) >= 1_00_00_000:
        return f"Rs {value / 1_00_00_000:.1f}Cr"
    if abs(value) >= 1_00_000:
        return f"Rs {value / 1_00_000:.1f}L"
    if abs(value) >= 1_000:
        return f"Rs {value / 1_000:.0f}K"
    return f"Rs {value:.0f}"


def new_axes(title: str, subtitle: str = "", figsize=FIGSIZE):
    """A titled, themed figure. Subtitle carries the honest caveat."""
    fig, ax = plt.subplots(figsize=figsize, dpi=DPI)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    fig.text(0.012, 0.965, title, ha="left", va="top",
             fontsize=15, fontweight="600", color=TEXT_PRIMARY)
    if subtitle:
        fig.text(0.012, 0.898, subtitle, ha="left", va="top",
                 fontsize=9.5, color=TEXT_SECONDARY)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1)

    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9.5, length=0)
    ax.grid(axis="y", color=GRID, linewidth=1, alpha=0.9)
    ax.set_axisbelow(True)
    return fig, ax


def finish(fig, path, subtitle: bool = True):
    fig.tight_layout(rect=(0, 0.02, 1, 0.87 if subtitle else 0.93))
    fig.savefig(path, facecolor=SURFACE, dpi=DPI)
    plt.close(fig)
    print(f"  wrote charts/{path.name}")


def money_axis(ax, axis: str = "y"):
    fmt = FuncFormatter(rupees)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)

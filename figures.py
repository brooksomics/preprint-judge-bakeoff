"""Two figures from the metrics dict. Static PNGs for the README and the post, so no hover layer.

Palette: categorical slots 1-2 of the validated default (blue = reasoning off, orange = reasoning
on); text in ink tokens, recessive grid, no dashed rules.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

BASE, REASONING = "#2a78d6", "#eb6834"
INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e1"


def _short(label: str) -> str:
    return label.split("/", 1)[-1]


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _legend(ax, **kw) -> None:
    handles = [
        Line2D([], [], marker="o", ls="", color=BASE, label="reasoning off"),
        Line2D([], [], marker="o", ls="", color=REASONING, label="reasoning on (@low / @medium)"),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8, labelcolor=INK2, **kw)


def _scatter_points(ax, pts: list[tuple[str, dict]]) -> None:
    for k, r in pts:
        color = REASONING if "@" in k else BASE
        xy = (r["cost_usd"], r["mae"])
        if not math.isnan(r["mae_lo"] + r["mae_hi"]):
            err = [[r["mae"] - r["mae_lo"]], [r["mae_hi"] - r["mae"]]]
            ax.errorbar(*xy, yerr=err, fmt="none", ecolor=color, elinewidth=1, alpha=0.6, zorder=2)
        ax.scatter(*xy, s=70, color=color, edgecolor=SURFACE, lw=2, zorder=3)
        ax.annotate(
            _short(k), xy, xytext=(6, 4), textcoords="offset points", fontsize=7.5, color=INK
        )


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_mae_vs_cost(m: dict, out: Path, ceiling: str) -> None:
    pts = [
        (k, r) for k, r in m.items() if k != ceiling and not math.isnan(r["mae"] + r["cost_usd"])
    ]
    fig, ax = plt.subplots(figsize=(7.5, 4.8), facecolor=SURFACE)
    _style(ax)
    _scatter_points(ax, pts)
    ax.set_xscale("log")
    ax.set_xlabel("$ per call, measured (log scale)", color=INK2)
    ax.set_ylabel(f"MAE vs {_short(ceiling)} (lower = closer to the ceiling)", color=INK2)
    ax.set_title(
        "Agreement with the ceiling vs. price per call", color=INK, fontsize=10, loc="left"
    )
    _legend(ax)
    _save(fig, out / "fig_mae_vs_cost.png")


def plot_coverage(m: dict, out: Path, ceiling: str) -> None:
    ks = sorted(m, key=lambda k: (-m[k]["cov"], k))
    fig, ax = plt.subplots(figsize=(7.5, 0.34 * len(ks) + 2.0), facecolor=SURFACE)
    _style(ax)
    colors = [REASONING if "@" in k else BASE for k in ks]
    bars = ax.barh([_short(k) for k in ks], [m[k]["cov"] for k in ks], color=colors, height=0.62)
    for b, k in zip(bars, ks, strict=True):
        y = b.get_y() + b.get_height() / 2
        ax.text(b.get_width() + 0.8, y, f"{m[k]['cov']:.1f}", va="center", fontsize=7.5, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.grid(False, axis="y")
    ax.set_xlabel("coverage: % of calls that returned a parseable score", color=INK2)
    ax.set_title("Coverage by model config", color=INK, fontsize=10, loc="left")
    _legend(ax, loc="upper center", bbox_to_anchor=(0.5, -0.12 - 0.5 / len(ks)), ncol=2)
    _save(fig, out / "fig_coverage.png")


def plot_all(m: dict, out: Path, ceiling: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    plot_mae_vs_cost(m, out, ceiling)
    plot_coverage(m, out, ceiling)

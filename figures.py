"""Two figures from the metrics dict. Static PNGs for the docs and the post, so no hover layer.

Palette: categorical slots 1-3 of the validated default (blue = reasoning off, orange = reasoning
on, aqua = strict structured output); derived rows (ens:, baseline:) are hollow markers; rows
that leave a preprint unscored in every repeat (analyze: usable) are hollow and MUTED (3.6:1
on the surface), so the eye does not land
on a model that cannot be used; text in ink tokens, recessive grid, no dashed rules. Each dot
carries a number, placed so none collide (_place_labels), and a key below the plot names it.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

from analyze import DERIVED

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

BASE, REASONING, SCHEMA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e1"
MUTED = "#86847e"
MARKER = 70  # scatter s, points^2
KEY_COLS = 2  # the ensemble names are long: three columns overflow 7.5 in
# label offsets in points from the marker, tried in order: beside it, then above/below, then
# further out, where a hairline leader ties the label back to its marker
OFFSETS = [(6, 4, "left"), (6, -11, "left"), (-6, 4, "right"), (-6, -11, "right")]
OFFSETS += [(0, 9, "center"), (0, -17, "center"), (6, 14, "left"), (-6, 14, "right")]
OFFSETS += [(14, 26, "left"), (-14, 26, "right"), (14, -32, "left"), (-14, -32, "right")]
LEADER = 5  # OFFSETS from this index on get a leader line


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


def _color(label: str, usable: bool = True) -> str:
    if not usable:
        return MUTED
    if "#schema" in label:
        return SCHEMA
    return REASONING if "@" in label else BASE


def _legend(ax, muted: bool = False, **kw) -> None:
    dot = dict(marker="o", ls="")
    unusable = "leaves a preprint unscored in 3 tries: not usable"
    handles = [
        *([Line2D([], [], color=MUTED, mfc=SURFACE, label=unusable, **dot)] if muted else []),
        Line2D([], [], color=BASE, label="reasoning off (or provider default)", **dot),
        Line2D([], [], color=REASONING, label="reasoning on (@low / @medium)", **dot),
        Line2D([], [], color=SCHEMA, label="strict structured output (#schema)", **dot),
        Line2D([], [], color=BASE, mfc=SURFACE, label="derived row (ens: median of 3)", **dot),
    ]
    ax.legend(handles=handles, frameon=False, fontsize=8, labelcolor=INK2, **kw)


def _scatter_points(ax, pts: list[tuple[str, dict]]) -> list[tuple[str, tuple, str]]:
    """Draw markers, error bars and the numbered key below the plot (one entry per dot, its
    marker repeated); return (number, xy, ink) for _place_labels."""
    labels, key = [], []
    for n, (k, r) in enumerate(pts, 1):
        color, xy = _color(k, r["usable"]), (r["cost_usd"], r["mae"])
        if not math.isnan(r["mae_lo"] + r["mae_hi"]):
            err = [[r["mae"] - r["mae_lo"]], [r["mae_hi"] - r["mae"]]]
            ax.errorbar(*xy, yerr=err, fmt="none", ecolor=color, elinewidth=1, alpha=0.6, zorder=2)
        face = SURFACE if r["derived"] or color == MUTED else color
        ax.scatter(*xy, s=MARKER, facecolor=face, edgecolor=color, lw=1.6, zorder=3)
        muted = color == MUTED
        name = f"{n}  {_short(k)}" + (f" ({r['unscored']} never scored)" if muted else "")
        key.append(Line2D([], [], marker="o", ls="", color=color, mfc=face, label=name))
        labels.append((str(n), xy, INK2 if muted else INK))
    kw = dict(frameon=False, fontsize=7.5, labelcolor=INK, handletextpad=0.3, columnspacing=1.5)
    ax.figure.legend(handles=key, loc="outside lower center", ncol=KEY_COLS, **kw)
    return labels


def _place_labels(ax, items: list[tuple[str, tuple, str]]) -> list:
    """Greedy direct labels: each takes the first offset whose box stays inside the axes and
    clears every marker, the legend and the labels already placed (else the least-bad one).
    Call after layout is final; boxes are in display space, so a later dpi change is fine."""
    r = ax.figure.canvas.get_renderer()
    half = math.sqrt(MARKER) / 2 * ax.figure.dpi / 72 + 1
    at = [ax.transData.transform(xy) for _, xy, _ in items]
    blocked = [Bbox.from_bounds(x - half, y - half, 2 * half, 2 * half) for x, y in at]
    blocked += [ax.get_legend().get_window_extent(r)] if ax.get_legend() else []
    frame, placed = ax.get_window_extent(r), []
    for text, xy, ink in items:
        tries = []
        for dx, dy, ha in OFFSETS:
            t = ax.annotate(
                text,
                xy,
                xytext=(dx, dy),
                textcoords="offset points",
                ha=ha,
                fontsize=7.5,
                color=ink,
            )
            bb = t.get_window_extent(r)
            out = not (frame.contains(bb.x0, bb.y0) and frame.contains(bb.x1, bb.y1))
            tries.append((sum(bb.overlaps(o) for o in blocked) + 10 * out, len(tries), t, bb))
            if tries[-1][0] == 0:
                break
        _, i, keep, bb = min(tries, key=lambda c: c[:2])
        for c in tries:
            c[2].remove()
        dx, dy, ha = OFFSETS[i]
        lead = dict(arrowstyle="-", color=INK2, lw=0.5, alpha=0.7, shrinkA=0, shrinkB=5)
        keep = ax.annotate(
            text,
            xy,
            xytext=(dx, dy),
            textcoords="offset points",
            ha=ha,
            fontsize=7.5,
            color=ink,
            arrowprops=lead if i >= LEADER else None,
        )
        blocked.append(bb)
        placed.append(keep)
    return placed


def _save(fig, path: Path) -> None:
    if fig.get_layout_engine() is None:  # the MAE chart is constrained: its key sits outside
        fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_mae_vs_cost(m: dict, out: Path, ceiling: str) -> None:
    pts = [
        (k, r) for k, r in m.items() if k != ceiling and not math.isnan(r["mae"] + r["cost_usd"])
    ]
    pts.sort(key=lambda kr: kr[1]["mae"])  # numbered closest-first: the results table's order
    size = (7.5, 4.8 + 0.18 * math.ceil(len(pts) / KEY_COLS))
    fig, ax = plt.subplots(figsize=size, facecolor=SURFACE, layout="constrained")
    _style(ax)
    numbers = _scatter_points(ax, pts)
    ax.set_xscale("log")
    ax.set_xlabel("$ per call, measured (log scale)", color=INK2)
    ax.set_ylabel(f"MAE vs {_short(ceiling)} (lower is better)", color=INK2)
    title = "Agreement with the ceiling vs. price per call"
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    _legend(ax, muted=not all(r["usable"] for _, r in pts))
    fig.canvas.draw()  # runs the layout and fixes the legend's spot before the numbers go in
    _place_labels(ax, numbers)
    _save(fig, out / "fig_mae_vs_cost.png")


def plot_coverage(m: dict, out: Path, ceiling: str) -> None:
    ks = sorted((k for k in m if not k.startswith(DERIVED)), key=lambda k: (-m[k]["cov"], k))
    fig, ax = plt.subplots(figsize=(7.5, 0.34 * len(ks) + 2.0), facecolor=SURFACE)
    _style(ax)
    colors = [_color(k) for k in ks]
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
    ax.legend_.legend_handles[-1].set_visible(False)  # no derived rows in the coverage chart
    ax.legend_.texts[-1].set_text("")
    _save(fig, out / "fig_coverage.png")


def plot_all(m: dict, out: Path, ceiling: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    plot_mae_vs_cost(m, out, ceiling)
    plot_coverage(m, out, ceiling)

"""Price data for the README comparison, and a plain-text yearly-cost table.

The numbers below were read from each vendor's official page on 2026-09-30/10-02
(see the README table for URLs). The chart image itself is rendered separately.
Run `python scripts/make_cost_chart.py` to print the table; `--json` for raw data.
`uv run --python 3.11 --with matplotlib python scripts/make_cost_chart.py --png` renders
docs/assets/cost-compare.png (the chart in the README).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKED = "2026-10-02"

# (name, plan, yearly cost in USD, note)
PRICES = [
    ("Video Trimmer", "free, open source", 0.00, ""),
    ("LosslessCut", "free, open source (GPL-2.0)", 0.00, "paid store builds optional"),
    ("Clipchamp", "free tier (1080p export)", 0.00, "4K needs Microsoft 365"),
    ("Premiere Elements 2027", "$99.99 once, 3-year license", round(99.99 / 3, 2),
     "per year over 3 years"),
    ("Wondershare Filmora", "Basic, annual", 49.99, ""),
    ("Movavi Video Editor", "Plus, 1 year", 69.95, ""),
    ("Adobe Premiere", "single app, annual billed monthly", round(22.99 * 12, 2), "$22.99/mo"),
]


# Cutting-room identity (same palette as docs/assets/banner.svg)
INK, CREAM, ORANGE, MUTED, GRID = "#0E2A2F", "#F3E9D2", "#FF7A1A", "#6FA3A0", "#1F4F57"
BAR_COLORS = ("#F3E9D2", "#C9BFA6")  # competitors: cream / muted cream, alternating
EDGE_PX = 48  # the longest label must end at least this far from the image edge
SUBLABELS = {  # plain-text sub-labels; only wording already in the README
    "Video Trimmer": "free, open source",
    "LosslessCut": "free, open source (GPL-2.0)",
    "Clipchamp": "free tier, 1080p; 4K price not verified",
    "Premiere Elements 2027": "$99.99 once, 3-year license",
    "Wondershare Filmora": "Basic, annual",
    "Movavi Video Editor": "Plus, 1 year",
    "Adobe Premiere": "annual, billed monthly ($22.99/mo)",
}


def money(v: float) -> str:
    return "$0" if v == 0 else f"${v:,.2f}"


def render_png(out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(PRICES, key=lambda r: (r[2], r[0] != "Video Trimmer"))[::-1]  # top = priciest
    dpi, w_in, h_in = 150, 12.0, 6.6
    fig = plt.figure(figsize=(w_in, h_in), dpi=dpi, facecolor=INK)
    ax = fig.add_axes([0.30, 0.17, 0.675, 0.60], facecolor=INK)
    sans = ["Segoe UI", "DejaVu Sans"]
    mono = ["Consolas", "DejaVu Sans Mono"]
    top = max(r[2] for r in rows)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(0, top * 1.3)
    ax.set_axisbelow(True)
    for gx in (0, 100, 200, 300):
        ax.axvline(gx, color=GRID, lw=1.2, zorder=0)
        ax.text(gx, -0.95, "$0" if gx == 0 else f"${gx}", color=MUTED, ha="center", va="top",
                family=mono, fontsize=11, clip_on=False, zorder=5)
    labels = []
    for i, (name, _plan, yearly, _note) in enumerate(rows):
        y = len(rows) - 1 - i
        free = yearly == 0
        if free:
            ax.plot([0], [y], marker="D", ms=11, color=ORANGE, zorder=3, clip_on=False)
        else:
            ax.barh(y, yearly, height=0.5, color=BAR_COLORS[i % 2], zorder=2)
        trans = ax.get_yaxis_transform()
        ax.text(-0.03, y + 0.1, name, transform=trans, ha="right", va="center",
                color=ORANGE if free else CREAM, family=sans, fontsize=14, fontweight="bold")
        ax.text(-0.03, y - 0.24, SUBLABELS[name], transform=trans, ha="right", va="center",
                color=MUTED, family=mono, fontsize=9.5)
        label = money(yearly) + ("" if free else " / yr")
        labels.append(ax.text(
            yearly + top * 0.03, y, label, ha="left", va="center", zorder=6,
            color=ORANGE if free else CREAM, family=mono, fontsize=15, fontweight="bold",
            bbox={"fc": INK, "ec": "none", "pad": 4}))
    # Computed right padding: widen xlim until the longest label ends >= EDGE_PX from the edge.
    fig.canvas.draw()
    for _ in range(40):
        right = max(t.get_window_extent().x1 for t in labels)
        if right <= fig.bbox.width - EDGE_PX * dpi / 100:
            break
        ax.set_xlim(0, ax.get_xlim()[1] * 1.04)
        for t, r in zip(labels, rows[::-1][::-1], strict=True):
            t.set_x(r[2] + ax.get_xlim()[1] * 0.025)
        fig.canvas.draw()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.text(0.04, 0.93, "What cutting a video costs per year", color=CREAM, family=sans,
             fontsize=24, fontweight="bold", ha="left", va="center")
    fig.text(0.04, 0.865, "cheapest individual plan that covers cutting video, USD per year",
             color=MUTED, family=mono, fontsize=11.5, ha="left", va="center")
    fig.text(0.04, 0.075, f"checked {CHECKED}  |  prices from each vendor's official page "
             "(URLs in the README)", color=MUTED, family=mono, fontsize=10, ha="left", va="center")
    fig.text(0.04, 0.035, "Filmora's perpetual option is not shown: its price was unclear on "
             "the page.", color=MUTED, family=mono, fontsize=10, ha="left", va="center")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, facecolor=INK)
    print(f"wrote {out}")


def main() -> None:
    if "--png" in sys.argv:
        render_png(Path(__file__).resolve().parent.parent / "docs" / "assets" / "cost-compare.png")
        return
    rows = sorted(PRICES, key=lambda r: r[2])
    if "--json" in sys.argv:
        print(json.dumps([{"name": n, "plan": p, "yearly_usd": y, "note": t}
                          for n, p, y, t in rows], indent=2))
        return
    print(f"Yearly cost in USD (checked {CHECKED})")
    for name, plan, yearly, note in rows:
        print(f"{name:<26} {yearly:>8.2f}  {plan}  {note}")


if __name__ == "__main__":
    main()

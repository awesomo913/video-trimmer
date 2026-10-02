"""Price data for the README comparison, and a plain-text yearly-cost table.

The numbers below were read from each vendor's official page on 2026-09-30/10-02
(see the README table for URLs). The chart image itself is rendered separately.
Run `python scripts/make_cost_chart.py` to print the table; `--json` for raw data.
"""
from __future__ import annotations

import json
import sys

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


def main() -> None:
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

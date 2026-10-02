"""Render the README SVGs to PNG, headless (no window opens).

    uv run --python 3.11 --with playwright python scripts/render_svg.py [OUT_DIR]

Writes docs/assets/social-preview.png (1280x640) from scripts/social-preview.svg.
With OUT_DIR, also writes preview renders of the banner and how-it-works there.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"


def render(page, svg: Path, png: Path, width: int, height: int, scale: int = 1) -> None:
    page.set_viewport_size({"width": width, "height": height})
    body = svg.read_text(encoding="utf-8")
    page.set_content(
        "<style>html,body{margin:0;background:#0E2A2F}svg{display:block;width:100%;height:auto}"
        f"</style>{body}"
    )
    page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": width, "height": height})
    print(f"wrote {png.name} ({width}x{height} @{scale}x)")


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            ctx = browser.new_context(device_scale_factor=1)
            page = ctx.new_page()
            render(page, ROOT / "scripts" / "social-preview.svg",
                   ASSETS / "social-preview.png", 1280, 640)
            if out:
                out.mkdir(parents=True, exist_ok=True)
                render(page, ASSETS / "banner.svg", out / "banner.png", 1280, 400)
                render(page, ASSETS / "how-it-works.svg", out / "how_1200.png", 1200, 372)
                ctx2 = browser.new_context(device_scale_factor=2)
                page2 = ctx2.new_page()
                render(page2, ASSETS / "how-it-works.svg", out / "how_358.png", 358, 111, 2)
                render(page2, ASSETS / "banner.svg", out / "banner_358.png", 358, 112, 2)
        finally:
            browser.close()


if __name__ == "__main__":
    main()

"""Generate the README SVGs (how-it-works, social-preview) in the cutting-room identity.

Pure vector output, no external fonts or URLs. The banner itself is hand-kept at
docs/assets/banner.svg; the social preview reuses its artwork on a 1280x640 canvas.

    python scripts/make_readme_visuals.py
    uv run --python 3.11 --with playwright python scripts/render_svg.py

Palette: ink #0E2A2F, surface #16393F, film-leader orange #FF7A1A, cream #F3E9D2,
amber #FFC24B, muted teal #6FA3A0.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

INK, SURFACE, BAND = "#0E2A2F", "#16393F", "#1F4F57"
ORANGE, CREAM, AMBER, MUTED = "#FF7A1A", "#F3E9D2", "#FFC24B", "#6FA3A0"
MONO = "Consolas,'Courier New',monospace"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"


def frame(i: int, x: float, y: float, w: float, h: float, op: float = 1.0) -> str:
    """One thumbnail frame, in the same three-variant style as the banner."""
    k = i % 3
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{CREAM}" fill-opacity="{op}"/>'
    if k == 0:
        out += (f'<circle cx="{x + w * .75:.1f}" cy="{y + h * .3:.1f}" r="{h * .15:.1f}" '
                f'fill="{AMBER}" fill-opacity="{op}"/>'
                f'<path d="M{x} {y + h} L{x + w * .35:.1f} {y + h * .55:.1f} '
                f'L{x + w * .6:.1f} {y + h * .78:.1f} L{x + w} {y + h * .6:.1f} V{y + h} Z" '
                f'fill="{INK}" fill-opacity=".55"/>')
    elif k == 1:
        out += (f'<path d="M{x} {y + h} V{y + h * .7:.1f} Q{x + w / 2:.1f} {y + h * .3:.1f} '
                f'{x + w} {y + h * .7:.1f} V{y + h} Z" fill="{INK}" fill-opacity=".5"/>'
                f'<circle cx="{x + w * .27:.1f}" cy="{y + h * .3:.1f}" r="{h * .12:.1f}" '
                f'fill="{AMBER}" fill-opacity="{op}"/>')
    else:
        out += (f'<rect x="{x + w * .18:.1f}" y="{y + h * .25:.1f}" width="{w * .64:.1f}" '
                f'height="{h * .5:.1f}" rx="2" fill="{INK}" fill-opacity=".45"/>'
                f'<circle cx="{x + w / 2:.1f}" cy="{y + h / 2:.1f}" r="{h * .14:.1f}" '
                f'fill="{AMBER}" fill-opacity="{op}"/>')
    return out


def strip(x: float, y: float, n: int, dim: tuple[int, int] | None = None) -> str:
    """A film strip n frames long (pitch 54, 54 tall). dim=(a,b): frames outside [a,b) fade."""
    w = n * 54
    out = f'<rect x="{x}" y="{y}" width="{w}" height="54" fill="{BAND}"/>'
    for j in range(int(w // 18)):
        hx = x + 5 + j * 18
        out += (f'<rect x="{hx}" y="{y + 4}" width="9" height="6" rx="2" fill="{INK}"/>'
                f'<rect x="{hx}" y="{y + 44}" width="9" height="6" rx="2" fill="{INK}"/>')
    for i in range(n):
        inside = dim is None or dim[0] <= i < dim[1]
        out += frame(i, x + 4 + i * 54, y + 10, 46, 34, 1.0 if inside else .28)
    return out


def handle(cx: float, top: float, bottom: float, inward: int) -> str:
    """Orange bracket cut-mark; inward=+1 caps point right, -1 point left."""
    cap_x = cx - 4 if inward > 0 else cx + 4 - 22
    return (f'<rect x="{cx - 4}" y="{top}" width="8" height="{bottom - top}" rx="2" fill="{ORANGE}"/>'
            f'<rect x="{cap_x}" y="{top}" width="22" height="8" rx="2" fill="{ORANGE}"/>'
            f'<rect x="{cap_x}" y="{bottom - 8}" width="22" height="8" rx="2" fill="{ORANGE}"/>')


def text(x, y, s, size, fill, fam=SANS, weight=500, anchor="start", extra="") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>')


def how_it_works() -> str:
    w, h = 1200, 372
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="How Video Trimmer works: open a video, '
         f'drag the IN and OUT handles, save the clip. Everything runs on your PC.">',
         f'<rect width="{w}" height="{h}" fill="{INK}"/>',
         text(36, 50, f'Everything runs on your PC — <tspan fill="{ORANGE}">your video never leaves it</tspan>',
              32, CREAM, weight=800)]
    xs = [36, 422, 808]
    titles = ["Open a video", "Mark IN and OUT", "Save the clip"]
    caps = [("Thumbnail timeline appears", "Ctrl+O, or drag the file in"),
            ("Drag the IN / OUT handles", "Frame-accurate preview"),
            ("Copy: fast, no re-encode", "Or re-encode to change format")]
    for i, px in enumerate(xs):
        o.append(f'<rect x="{px}" y="70" width="356" height="220" rx="6" fill="{SURFACE}"/>')
        o.append(text(px + 20, 108, str(i + 1), 30, ORANGE, MONO, 700))
        o.append(text(px + 52, 108, titles[i], 24, CREAM, weight=700))
        o.append(text(px + 20, 246, caps[i][0], 20, CREAM, weight=600))
        o.append(text(px + 20, 270, caps[i][1], 20, MUTED))
    # Stage 1: whole strip, ruler ticks
    x1 = xs[0] + 16
    o.append(strip(x1, 126, 6))
    for t in range(0, 324, 18):
        th = 12 if t % 54 == 0 else 7
        o.append(f'<rect x="{x1 + t}" y="192" width="2" height="{th}" fill="{MUTED}" fill-opacity=".7"/>')
    # Stage 2: dimmed outside IN..OUT, orange handles, timecodes
    x2 = xs[1] + 16
    o.append(strip(x2, 126, 6, dim=(1, 5)))
    o.append(f'<rect x="{x2 + 54}" y="126" width="216" height="54" fill="none" stroke="{AMBER}" stroke-width="2"/>')
    o.append(handle(x2 + 54, 118, 188, +1))
    o.append(handle(x2 + 270, 118, 188, -1))
    o.append(text(x2 + 54, 218, "IN 00:12.40", 18, CREAM, MONO, 700, "middle"))
    o.append(text(x2 + 270, 218, "OUT 00:31.05", 18, CREAM, MONO, 700, "middle"))
    # Stage 3: the cut clip -> new file
    x3 = xs[2] + 20
    o.append(strip(x3, 126, 3))
    o.append(handle(x3, 118, 188, +1))
    o.append(handle(x3 + 162, 118, 188, -1))
    ax = x3 + 190
    o.append(f'<path d="M{ax} 153 H{ax + 26}" stroke="{AMBER}" stroke-width="3"/>'
             f'<path d="M{ax + 36} 153 l-12 -8 v16Z" fill="{AMBER}"/>')
    fx = x3 + 236
    o.append(f'<rect x="{fx}" y="126" width="64" height="54" rx="4" fill="none" '
             f'stroke="{CREAM}" stroke-width="2"/>')
    o.append(text(fx + 32, 160, "clip", 18, CREAM, MONO, 700, "middle"))
    # Footer notes
    o.append(text(36, 320, "Batch: split a whole folder into 2-20 equal parts or fixed-length chunks.",
                  18, AMBER, MONO))
    o.append(text(36, 346, "Copy cuts snap to keyframes; pick a quality preset for an exact frame.",
                  18, MUTED, MONO))
    o.append("</svg>")
    return "\n".join(o)


def social_preview() -> str:
    """1280x640 variant: the approved banner artwork centred, plus a tagline."""
    banner = (ASSETS / "banner.svg").read_text(encoding="utf-8")
    inner = banner[banner.index(">") + 1: banner.rindex("</svg>")]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" '
        'role="img" aria-label="VideoTrimmer: cut the part you want, fast, offline, free">\n'
        f'<rect width="1280" height="640" fill="{INK}"/>\n'
        f'<g transform="translate(0,90)">{inner}</g>\n'
        + text(64, 580, "Offline  ·  No account  ·  Free and open source", 28, CREAM, MONO, 700)
        + "\n</svg>\n"
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "how-it-works.svg").write_text(how_it_works() + "\n", encoding="utf-8")
    (ROOT / "scripts" / "social-preview.svg").write_text(social_preview(), encoding="utf-8")
    print("wrote docs/assets/how-it-works.svg and scripts/social-preview.svg")


if __name__ == "__main__":
    main()

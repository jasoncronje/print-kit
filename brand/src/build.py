#!/usr/bin/env python3
"""Build the print-kit brand files: marks, lockups, icon, README banners, social preview.

    pip install fonttools cairosvg
    python3 brand/src/build.py

Downloads Geist (SIL OFL 1.1) into brand/src/fonts/ on first run. Every SVG it writes has the
text outlined, so nothing depends on the font being installed.
"""

import urllib.request
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SRC = Path(__file__).resolve().parent
BRAND = SRC.parent
REPO = BRAND.parent
FONTS = SRC / "fonts"
FONT_URL = "https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-sans/{}.ttf"

# Colour shift: one step per printed layer, bottom to top, like gradient filament.
SHIFT = ["#4263eb", "#7950f2", "#be4bdb", "#f06595"]   # indigo, violet, purple, pink
INK, INK_DARK = "#0f0f0f", "#f2f2f2"
PAPER, NIGHT = "#f4f4f3", "#141414"
MUTED, MUTED_DARK = "#626262", "#a3a3a3"


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def rrect(x0, y0, x1, y1, r):
    return (f"M{f(x0 + r)} {f(y0)}H{f(x1 - r)}A{f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)}V{f(y1 - r)}"
            f"A{f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(y1)}H{f(x0 + r)}A{f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)}"
            f"V{f(y0 + r)}A{f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)}Z")


def poly(pts):
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def bead(x0, x1, yc, h):
    return rrect(x0, yc - h / 2, x1, yc + h / 2, h / 2)


def mark_parts(small=False):
    """[(role, path)] on a 256 canvas. Roles: head (heater block), hot (nozzle + fresh layer), layer0.. (bottom up)."""
    if small:  # 16-32 px cut: two layers, thicker beads, wider gaps
        parts = [("head", rrect(84, 20, 172, 76, 10)),
                 ("hot", poly([(98, 84), (158, 84), (136, 126), (120, 126)]))]
        h, g, y = 34, 14, 150
        parts.append(("hot", bead(36, 128, y, h)))
        parts.append(("layer1", bead(36, 220, y + h + g, h)))
        parts.append(("layer0", bead(36, 220, y + 2 * (h + g), h)))
        return parts
    parts = [("head", rrect(90, 32, 166, 78, 8)),
             ("hot", poly([(102, 84), (154, 84), (134, 124), (122, 124)]))]
    h, g, y = 22, 8, 140
    parts.append(("hot", bead(40, 128, y, h)))
    for i, role in ((1, "layer2"), (2, "layer1"), (3, "layer0")):
        parts.append((role, bead(40, 216, y + i * (h + g), h)))
    return parts


def colours(scheme):
    """scheme: colour | colour-dark | black | white."""
    if scheme in ("black", "white"):
        c = INK if scheme == "black" else "#ffffff"
        return {"head": c, "hot": c, "layer0": c, "layer1": c, "layer2": c}
    head = INK if scheme == "colour" else INK_DARK
    return {"head": head, "layer0": SHIFT[0], "layer1": SHIFT[1], "layer2": SHIFT[2], "hot": SHIFT[3]}


def mark_group(scheme, x=0, y=0, s=1.0, small=False):
    col = colours(scheme)
    paths = "".join(f'<path d="{d}" fill="{col[r]}"/>' for r, d in mark_parts(small))
    return f'<g transform="translate({f(x)} {f(y)}) scale({f(s)})">{paths}</g>'


_fonts = {}


def font(weight):
    if weight not in _fonts:
        FONTS.mkdir(exist_ok=True)
        path = FONTS / f"Geist-{weight}.ttf"
        if not path.exists():
            urllib.request.urlretrieve(FONT_URL.format(f"Geist-{weight}"), path)
        _fonts[weight] = TTFont(path)
    return _fonts[weight]


def text(s, size, weight="SemiBold", tracking=-0.03):
    """(path d at origin baseline, advance width)."""
    ft = font(weight)
    gs, cmap, hmtx = ft.getGlyphSet(), ft.getBestCmap(), ft["hmtx"]
    k = size / ft["head"].unitsPerEm
    pen, x = SVGPathPen(gs), 0.0
    for ch in s:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, 0)))
        x += hmtx[g][0] * k + tracking * size
    return pen.getCommands(), x - tracking * size


def doc(w, h, body, bg=None, title="print-kit"):
    rect = f'<rect width="{f(w)}" height="{f(h)}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" width="{f(w)}" height="{f(h)}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{rect}{body}</svg>\n')


def write(rel, content, png=None):
    p = BRAND / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    if png:
        out, width = png
        cairosvg.svg2png(bytestring=content.encode(), write_to=str(out), output_width=width)
    return p


def main():
    word, ww = text("print-kit", 150)

    for scheme in ("colour", "colour-dark", "black", "white"):
        write(f"logo/mark-{scheme}.svg", doc(256, 256, mark_group(scheme)))
        write(f"logo/mark-small-{scheme}.svg", doc(256, 256, mark_group(scheme, small=True)))
        ink = {"colour": INK, "colour-dark": INK_DARK, "black": INK, "white": "#ffffff"}[scheme]
        # horizontal: mark 256 tall, 40 gap, wordmark centred on the mark's optical middle
        w = 256 + 40 + ww + 6
        write(f"logo/lockup-horizontal-{scheme}.svg",
              doc(w, 256, mark_group(scheme) + f'<path transform="translate(296 182)" d="{word}" fill="{ink}"/>'))
        # stacked: mark over wordmark, both centred
        sw = max(256, ww) + 12
        sm = (sw - 256) / 2
        write(f"logo/lockup-stacked-{scheme}.svg",
              doc(sw, 256 + 200, mark_group(scheme, x=sm) + f'<path transform="translate({f((sw - ww) / 2)} 400)" d="{word}" fill="{ink}"/>'))

    # Plugin icon: the small cut on a night tile, full bleed (the directory rounds corners itself).
    icon = doc(1024, 1024, mark_group("colour-dark", x=172, y=164, s=2.65, small=True), bg=NIGHT)
    write("icon/icon.svg", icon, png=(REPO / "plugins/print-kit/.claude-plugin/icon.png", 1024))
    cairosvg.svg2png(bytestring=icon.encode(), write_to=str(BRAND / "icon/icon-512.png"), output_width=512)

    # README banners, light and dark
    tag, tw = text("OpenSCAD parts for your own 3D printer", 34, "Medium", tracking=-0.01)
    sub, _ = text("Claude Code plugin  ·  rules  ·  fit tests  ·  model checks  ·  3D viewer", 22, "Medium", tracking=0)
    for name, bg, ink, muted, scheme in (("light", PAPER, INK, MUTED, "colour"), ("dark", NIGHT, INK_DARK, MUTED_DARK, "colour-dark")):
        body = (mark_group(scheme, x=72, y=56, s=0.80)
                + f'<path transform="translate(300 172) scale(0.62)" d="{word}" fill="{ink}"/>'
                + f'<path transform="translate(302 226)" d="{tag}" fill="{ink}"/>'
                + f'<path transform="translate(302 268)" d="{sub}" fill="{muted}"/>')
        # a printed layer running along the bottom edge, in the shift colours
        x = 0
        for i, c in enumerate(SHIFT):
            body += f'<rect x="{f(x)}" y="312" width="320" height="8" fill="{c}"/>'
            x += 320
        write(f"banner/banner-{name}.svg", doc(1280, 320, body, bg=bg))

    # GitHub social preview (upload by hand: repo Settings > Social preview)
    body = (mark_group("colour-dark", x=500, y=96, s=1.1)
            + f'<path transform="translate({f((1280 - ww * 0.72) / 2)} 470) scale(0.72)" d="{word}" fill="{INK_DARK}"/>'
            + f'<path transform="translate({f((1280 - tw) / 2)} 540)" d="{tag}" fill="{MUTED_DARK}"/>')
    x = 0
    for c in SHIFT:
        body += f'<rect x="{f(x)}" y="628" width="320" height="12" fill="{c}"/>'
        x += 320
    sp = doc(1280, 640, body, bg=NIGHT)
    write("banner/social-preview.svg", sp, png=(BRAND / "banner/social-preview.png", 1280))

    # palette swatch sheet
    sw = ""
    names = [("Indigo", SHIFT[0]), ("Violet", SHIFT[1]), ("Purple", SHIFT[2]), ("Pink", SHIFT[3]),
             ("Ink", INK), ("Paper", PAPER), ("Night", NIGHT), ("Light ink", INK_DARK)]
    for i, (n, c) in enumerate(names):
        x, y = 24 + (i % 4) * 200, 24 + (i // 4) * 200
        lbl, _ = text(n, 18, "SemiBold", 0)
        hx, _ = text(c, 16, "Medium", 0)
        dark = c in (INK, NIGHT) or c in SHIFT
        tc = "#ffffff" if dark else INK
        sw += (f'<rect x="{x}" y="{y}" width="184" height="184" rx="10" fill="{c}" stroke="#e3e3e1"/>'
               f'<path transform="translate({x + 16} {y + 146})" d="{lbl}" fill="{tc}"/>'
               f'<path transform="translate({x + 16} {y + 168})" d="{hx}" fill="{tc}"/>')
    pal = doc(824, 424, sw, bg="#ffffff", title="print-kit palette")
    write("palette.svg", pal, png=(BRAND / "palette.png", 824))
    print("brand files written to", BRAND)


if __name__ == "__main__":
    main()

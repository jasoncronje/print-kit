#!/usr/bin/env python3
"""Draw a traced outline over its photo, to check a trace by eye.

    python3 trace_overlay.py <project> [out.png]

Reads <project>/trace/config.json (photo) and the points to draw: trace/points.json
(`points_px`) when it exists, else the config's start_points_px. Writes
<project>/trace/overlay.png unless an output path is given. Needs Pillow.
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sys.exit("Pillow is needed (pip install pillow)")
    trace = Path(sys.argv[1]).resolve() / "trace"
    cfg = json.loads((trace / "config.json").read_text())
    saved = trace / "points.json"
    pts = json.loads(saved.read_text())["points_px"] if saved.exists() else cfg["start_points_px"]
    photo = Path(cfg["photo"])
    photo = photo if photo.is_absolute() else (trace / photo if (trace / photo).exists() else trace.parent / photo)
    im = Image.open(photo).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    px = [tuple(map(float, p)) for p in pts]
    d.line(px + [px[0]], fill=(255, 230, 0, 255), width=3)
    for x, y in px:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(0, 200, 255, 255))
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    m = 40
    im = im.crop((max(0, min(xs) - m), max(0, min(ys) - m), min(im.width, max(xs) + m), min(im.height, max(ys) + m)))
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else trace / "overlay.png"
    im.save(out)
    print(f"wrote {out} ({len(px)} points)")


if __name__ == "__main__":
    main()

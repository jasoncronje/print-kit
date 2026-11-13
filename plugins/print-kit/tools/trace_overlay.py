#!/usr/bin/env python3
"""Draw a traced outline over its photo, to check a trace by eye.

    python3 trace_overlay.py <project> [out.svg]

Reads <project>/trace/config.json (photo) and the points to draw: trace/points.json
(`points_px`) when it exists, else the config's start_points_px. Writes
<project>/trace/overlay.svg (the photo embedded, the outline and dots on top, cropped
to the outline) unless an output path is given. Open it in a browser, or read it as an
image. Standard library only.
"""

import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_trace import photo_size  # noqa: E402


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    trace = Path(sys.argv[1]).resolve() / "trace"
    cfg = json.loads((trace / "config.json").read_text(encoding="utf-8"))
    saved = trace / "points.json"
    pts = json.loads(saved.read_text(encoding="utf-8"))["points_px"] if saved.exists() else cfg["start_points_px"]
    photo = Path(cfg["photo"])
    photo = photo if photo.is_absolute() else (trace / photo if (trace / photo).exists() else trace.parent / photo)
    w, h = photo_size(photo)
    mime = "image/png" if photo.suffix.lower() == ".png" else "image/jpeg"
    href = f"data:{mime};base64," + base64.b64encode(photo.read_bytes()).decode()
    pts = [(p["x"], p["y"]) if isinstance(p, dict) else p for p in pts]  # saved {x, y} or config [x, y]
    xs, ys = [float(p[0]) for p in pts], [float(p[1]) for p in pts]
    m = 40
    x0, y0 = max(0, min(xs) - m), max(0, min(ys) - m)
    x1, y1 = min(w, max(xs) + m), min(h, max(ys) + m)
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"/>' for x, y in zip(xs, ys))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" '
           f'width="{x1 - x0:.0f}" height="{y1 - y0:.0f}">'
           f'<image href="{href}" x="0" y="0" width="{w}" height="{h}"/>'
           f'<polygon points="{line}" fill="none" stroke="#ffe600" stroke-width="3"/>'
           f'<g fill="#00c8ff">{dots}</g></svg>\n')
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else trace / "overlay.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(pts)} points)")


if __name__ == "__main__":
    main()

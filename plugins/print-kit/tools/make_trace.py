#!/usr/bin/env python3
"""Build a project's photo-trace editor from its trace/config.json.

    python3 make_trace.py <project-folder> [<project-folder> ...]

For each project this:
  1. reads trace/config.json (hand-written),
  2. starts the editor on trace/points.json when it exists (the last saved
     trace), else on the config's start_points_px,
  3. copies the photo to trace/photo.jpg and writes trace/index.html from the
     shared template trace/template.html.

Show it locally (the default): serve trace/ with viewer_server.py (through
Portless if you use it); Save writes trace/points.json straight into the project.
As a claude.ai Artifact (only when asked): publish trace/index.html with files
{"photo.jpg": "<project>/trace/photo.jpg"} and capabilities {"db": {}, "user": {}};
Save then goes to the artifact store doc instead.
"""

import json
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "trace" / "template.html"

REQUIRED = ["title", "photo", "px_per_in", "clearance_mm", "store_doc", "draft_key"]


def photo_size(path):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is needed to read the photo size (pip install pillow)")
    with Image.open(path) as im:
        return im.size


def build(project):
    project = Path(project).resolve()
    trace = project / "trace"
    cfg = json.loads((trace / "config.json").read_text())
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        sys.exit(f"{project.name}: config.json is missing {', '.join(missing)}")

    src_photo = (project / cfg["photo"]).resolve()
    w, h = photo_size(src_photo)
    shutil.copyfile(src_photo, trace / "photo.jpg")

    points_file = trace / "points.json"
    if points_file.exists():
        saved = json.loads(points_file.read_text())
        start = [[p["x"], p["y"]] for p in saved["points_px"]]
    else:
        start = cfg.get("start_points_px")
    if not start or len(start) < 3:
        sys.exit(f"{project.name}: no start points (trace/points.json or start_points_px)")

    page_cfg = {
        "title": cfg["title"],
        "photo": "photo.jpg",
        "photo_w": w,
        "photo_h": h,
        "px_per_in": cfg["px_per_in"],
        "clearance_mm": cfg["clearance_mm"],
        "start_points_px": start,
        "fit": cfg.get("fit"),
        "store_doc": cfg["store_doc"],
        "draft_key": cfg["draft_key"],
    }
    html = TEMPLATE.read_text()
    # "</" can't appear inside the inline JSON script tag.
    html = html.replace("__CONFIG__", json.dumps(page_cfg).replace("</", "<\\/"))
    html = html.replace("__TITLE__", cfg["title"].replace("<", "&lt;"))
    (trace / "index.html").write_text(html)
    print(f"{project.name}: trace/index.html ({len(start)} dots, photo {w}x{h})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        build(p)

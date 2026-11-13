#!/usr/bin/env python3
"""Build a project's pocket layout editor from its layout/config.json.

    python3 make_layout.py <project-folder> [<project-folder> ...]

For bins whose pockets are simple shapes (round holes, rectangular wells), so
there is nothing to trace from a photo. For each project this:
  1. reads layout/config.json (hand-written: bin, clearance, kinds, start_pockets),
  2. starts the editor on layout/saved.json when it exists (the last saved
     layout), else on start_pockets,
  3. writes layout/index.html from the shared template layout/template.html.

Show it locally (the default): serve layout/ with viewer_server.py (through
Portless if you use it); Save writes layout/saved.json straight into the project.
As a claude.ai Artifact (only when asked): publish layout/index.html with
capabilities {"db": {}, "user": {}}; Save then goes to the artifact store doc.
"""

import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "layout" / "template.html"

REQUIRED = ["title", "bin", "clearance_mm", "kinds", "start_pockets", "store_doc", "draft_key"]
POCKET_KEYS = ["id", "kind", "x", "y", "rot", "mode", "k", "len", "span"]


def build(project):
    project = Path(project).resolve()
    layout = project / "layout"
    cfg = json.loads((layout / "config.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        sys.exit(f"{project.name}: config.json is missing {', '.join(missing)}")

    saved = layout / "saved.json"
    if saved.exists():
        start = [{k: p[k] for k in POCKET_KEYS if k in p} for p in json.loads(saved.read_text(encoding="utf-8"))["pockets"]]
    else:
        start = cfg["start_pockets"]
    for p in start:
        if p["kind"] not in cfg["kinds"]:
            sys.exit(f"{project.name}: pocket {p['id']} has unknown kind {p['kind']}")

    page_cfg = {k: cfg[k] for k in REQUIRED}
    page_cfg["start_pockets"] = start
    html = TEMPLATE.read_text(encoding="utf-8")
    # "</" can't appear inside the inline JSON script tag.
    html = html.replace("__CONFIG__", json.dumps(page_cfg).replace("</", "<\\/"))
    html = html.replace("__TITLE__", cfg["title"].replace("<", "&lt;"))
    (layout / "index.html").write_text(html, encoding="utf-8")
    print(f"{project.name}: layout/index.html ({len(start)} pockets)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        build(p)

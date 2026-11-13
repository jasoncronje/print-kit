#!/usr/bin/env python3
"""Build a project's 3D viewer from its viewer/config.json.

    python3 make_viewer.py <project-folder> [<project-folder> ...]
    python3 make_viewer.py --page <project-folder>     # only rewrite viewer/index.html

A build:
  1. exports every mesh the config names (OpenSCAD `part`s, or existing STLs),
     as binary STL,
  2. packs them as base64 into viewer/data.json together with the config,
  3. writes viewer/index.html: the template with that data inline, a static page
     that opens straight from disk (no server) and is what gets published as a
     claude.ai Artifact (only when asked). It isn't kept in git.

viewer_server.py serves the shared template live instead, where one click opens
a plate in your slicer. --page rewrites index.html from the current data.json, e.g. after a
template change, without exporting meshes again.

The artifact host won't serve .stl files, which is why meshes travel inside JSON.
OpenSCAD runs need the sandbox disabled when Claude runs this.
"""

import base64
import datetime
import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TEMPLATE = TOOLS / "viewer" / "template.html"
VENDOR = TOOLS / "viewer" / "vendor"   # three.js r128 + OrbitControls + STLLoader (MIT)
sys.path.insert(0, str(TOOLS))
import kit_profile as kit  # noqa: E402
OPENSCAD = kit.openscad()


def ascii_to_binary(text):
    """ASCII STL -> binary STL bytes. Normals are left at zero; the viewer recomputes them."""
    nums = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)
    if len(nums) % 3:
        raise ValueError("ASCII STL has a vertex count that isn't a multiple of 3")
    tris = len(nums) // 3
    out = bytearray(b"\0" * 80)
    out += struct.pack("<I", tris)
    for t in range(tris):
        out += struct.pack("<3f", 0, 0, 0)
        for v in nums[t * 3:t * 3 + 3]:
            out += struct.pack("<3f", *map(float, v))
        out += b"\0\0"
    return bytes(out)


def to_binary_stl(data):
    # A binary STL can start with "solid" too, so check the size it claims.
    if len(data) >= 84:
        tris = struct.unpack_from("<I", data, 80)[0]
        if 84 + tris * 50 == len(data):
            return data
    return ascii_to_binary(data.decode("utf-8", "replace"))


def scad_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return json.dumps(v)


def export_scad(project, scad_file, spec, fn):
    """Run OpenSCAD for one mesh. spec is {"part": ..., "define": {...}}."""
    args = [OPENSCAD, "--export-format", "binstl"]
    defines = dict(spec.get("define", {}))
    if "part" in spec:
        defines["part"] = spec["part"]
    if fn:
        defines.setdefault("$fn", fn)
    for k, v in defines.items():
        args += ["-D", f"{k}={scad_value(v)}"]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "mesh.stl"
        args += ["-o", str(out), str(project / spec.get("file", scad_file))]
        res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0 or not out.exists():
            sys.exit(f"OpenSCAD failed for {spec}:\n{res.stderr[-2000:]}")
        return out.read_bytes()


def build(project):
    project = project.resolve()
    cfg_path = project / "viewer" / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if "bed" not in cfg:
        kit.require_bed(project)   # before any export: the plates are drawn on this bed
    scad_file = cfg.get("scad")
    fn = cfg.get("fn")

    meshes = {}      # key -> base64
    seen = {}        # source signature -> key

    def mesh_for(entry):
        if "shape" in entry:
            return None
        if "stl" in entry:
            sig = ("stl", entry["stl"])
        elif "scad" in entry:
            sig = ("scad", json.dumps(entry["scad"], sort_keys=True))
        else:
            sys.exit(f"{entry.get('id')}: needs one of stl, scad or shape")
        if sig in seen:
            return seen[sig]
        if sig[0] == "stl":
            raw = (project / entry["stl"]).read_bytes()
            label = entry["stl"]
        else:
            raw = export_scad(project, scad_file, entry["scad"], fn)
            label = "part=" + str(entry["scad"].get("part", "(default)"))
        data = to_binary_stl(raw)
        key = hashlib.sha1(data).hexdigest()[:12]
        meshes[key] = base64.b64encode(data).decode("ascii")
        seen[sig] = key
        print(f"  {label:<34} {len(data) / 1024:8.0f} KB")
        return key

    for section in ("assembly", "print"):
        for entry in cfg.get(section, []):
            key = mesh_for(entry)
            if key:
                entry["mesh"] = key
            for drop in ("stl", "scad"):
                entry.pop(drop, None)

    cfg["project"] = project.name
    prof = kit.load(project)
    cfg.setdefault("bed", list(kit.bed(project)[:2]))
    cfg.setdefault("printer", prof["printer"]["name"])
    cfg.setdefault("slicer", prof["slicer"]["name"] or "slicer")
    cfg["built"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cfg["meshes"] = meshes

    out_dir = project / "viewer"
    (out_dir / "data.json").write_text(json.dumps(cfg, separators=(",", ":")), encoding="utf-8")
    size = (out_dir / "data.json").stat().st_size / 1024 / 1024
    shown = shown_path(out_dir)
    print(f"  -> {shown}/data.json ({size:.1f} MB)")
    if size > 15.5:
        print("     too big for an Artifact (16 MB): fine locally, coarsen meshes to publish")
    write_page(project)


def shown_path(p):
    root = kit.workspace(p)
    return p.relative_to(root) if p.is_relative_to(root) else p


def write_page(project):
    """viewer/index.html: the template with the title filled in and data.json inline."""
    out_dir = project / "viewer"
    cfg = json.loads((out_dir / "config.json").read_text(encoding="utf-8"))
    data = (out_dir / "data.json").read_text(encoding="utf-8").replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__TITLE__", cfg.get("title", project.name))
    html = html.replace("<!--VIEWER_DATA-->", f'<script id="viewer-data" type="application/json">{data}</script>', 1)
    # the 3D library goes inline too, so the page works from disk and offline
    html = re.sub(r'<script src="vendor/([\w.-]+)"></script>',
                  lambda m: "<script>" + (VENDOR / m[1]).read_text(encoding="utf-8").replace("</script", "<\\/script") + "</script>", html)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    shown = shown_path(out_dir)
    print(f"  -> {shown}/index.html (static, opens from disk; not kept in git)")


def main():
    args = sys.argv[1:]
    page = "--page" in args
    args = [a for a in args if a != "--page"]
    if not args:
        sys.exit(__doc__)
    for p in args:
        print(Path(p).resolve().name)
        if page:
            write_page(Path(p))
        else:
            build(Path(p))


if __name__ == "__main__":
    main()

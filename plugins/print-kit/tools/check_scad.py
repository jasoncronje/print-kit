#!/usr/bin/env python3
"""Check a project's printable OpenSCAD parts before handoff.

    python3 check_scad.py <project> [<project> ...]
    python3 check_scad.py --all      # every project folder in the workspace
        --part a,b     only these parts (part values or stl file stems)
        --fn N         pass -D '$fn=N' (default: viewer config "fn", if any)
        --json         machine-readable output
        -j N           parallel OpenSCAD exports (default: CPU count)
        --timeout S    seconds per part (default 600)

Default parts: the `print` entries in viewer/config.json (stl/*.stl without one). A `scad`
entry exports as in make_viewer.py; an `stl` entry uses the README line that regenerates it,
else the part named like it. `clash_*` values in the `part = ...; // [...]` list run too.

Checks per part, each PASS / WARN / FAIL (exit 1 on any FAIL):
  export    ASCII STL, --hardwarnings: non-zero exit, empty geometry, WARNING / repair /
            "Simple: no" / 2-manifold on stderr, or summary simple=false fails
  manifold  every edge shared by exactly two faces
  bed       lowest point at z = 0 +/- 0.01, fits the bed in print-kit.json (printer.bed_mm); WARN for a body in the air
  layer1    regions in the slice at z = 0.1; WARN on islands under 1 cm2 beside one over 5 cm2
  feet      Gridfinity bins (X, Y = n*42 - 0.5 +/- 0.3, taller than a 5 mm bare base): FAIL
            when the first layer has fewer than nx*ny regions (feet buried in a block)
  overhang  downward faces past 45 deg from vertical, centroid above z = 0.6 (bridges
            included); WARN over OVERHANG_WARN_MM2, naming the biggest patches
  clash     clash_* parts must export empty; any geometry fails with its bounding box

Exports go to a temp dir, never into the project. OpenSCAD runs need the sandbox disabled.

Mesh checks (stderr patterns, manifold edges, first-layer regions, overhang) are ported from
verify-model.py in Wilson Waters' 3d-printing repo (.claude/skills/3d-print-designer/),
MIT License, Copyright (c) 2026 Wilson Waters.
"""

import argparse
import concurrent.futures
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_profile as kit  # noqa: E402

OPENSCAD = shutil.which("openscad") or "openscad"

Z_TOL = 0.01                  # flat bed faces sit exactly at z = 0
LAYER_Z = 0.1                 # half of a 0.2 mm first layer
SLIVER_MM2 = 0.2              # first-layer regions under one extrusion width squared never print
ISLAND_MM2, BIG_MM2 = 100.0, 500.0
GF_PITCH, GF_GAP, GF_TOL = 42.0, 0.5, 0.3
GF_MIN_H = 5.0                # a bare Gridfinity base is 4.75 mm; flat fit-test frames are thinner
OVERHANG_Z = 0.6              # skips the bed face and the foot's 0.8 mm bottom chamfer
OVERHANG_DEG = 45.5           # 45 deg chamfers print fine; the 0.5 absorbs facet noise
BRIDGE_DEG = 89.0             # flatter than this the slicer bridges it
# 25 cm2, calibrated on the author's prints (Bambu P2S, PLA, 0.4 nozzle, 2026-10-22). The two parts whose READMEs call for supports
# are over it: tessan plate 3850 (supports on) and apple-watch body 2892 (enforcer at the bore
# top). Every part printed without supports is under 1900: arches, small round channels and
# short bridges add up fast (filament hook 1006, iPhone body 1627, LCD case 1847). A 1 cm2
# sloped-only limit flagged three of those known-good parts. Info for the reviewer, not a gate.
OVERHANG_WARN_MM2 = 2500.0

BAD_RE = re.compile(r"^(WARNING|ERROR|EXPORT-WARNING)|may need repair|Simple:\s*no"
                    r"|not be a valid 2-manifold", re.I)
EMPTY_RE = re.compile(r"top level object is empty", re.I)
VERTEX_RE = re.compile(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)")


class Sets:
    """Union-find over hashable keys."""
    def __init__(self):
        self.p = {}

    def find(self, k):
        while self.p.setdefault(k, k) != k:
            self.p[k] = k = self.p[self.p[k]]   # path halving
        return k

    def join(self, a, b):
        self.p[self.find(a)] = self.find(b)


# ---------- which parts to check ----------

def part_list(src):
    """Names in the comment after `part = "...";`: `// [a, b]` or `// a | b`."""
    m = re.search(r'^\s*part\s*=\s*"[^"]*"\s*;\s*//(.*)$', src, re.M)
    if not m:
        return []
    b = re.search(r"\[(.*?)\]", m.group(1))
    return [t for t in re.split(r"[\s,|]+", b.group(1) if b else m.group(1))
            if re.fullmatch(r"[A-Za-z_]\w*", t)]


def readme_defines(project):
    """{"stl/x.stl": [-D values]} from the README's `openscad ... -o stl/x.stl` lines."""
    out, readme = {}, project / "README.md"
    for line in readme.read_text().splitlines() if readme.exists() else []:
        i = line.find("openscad ")
        if i < 0 or ".stl" not in line:
            continue
        try:
            toks = shlex.split(line[i:].split("`")[0])
        except ValueError:
            continue
        flag = lambda f: [toks[k + 1] for k, t in enumerate(toks[:-1]) if t == f]
        dest = flag("-o")
        if dest and dest[0].endswith(".stl") and "$" not in dest[0]:
            out.setdefault(os.path.normpath(dest[0]), flag("-D"))
    return out


def spec_defines(spec):
    """make_viewer.py's {"part", "define"} spec as -D values."""
    d = dict(spec.get("define", {}), **({"part": spec["part"]} if "part" in spec else {}))
    val = lambda v: ("true" if v else "false") if isinstance(v, bool) else (
        repr(v) if isinstance(v, (int, float)) else json.dumps(v))
    return [f"{k}={val(v)}" for k, v in d.items()]


def stl_defines(rel, parts, readme):
    """(-D values that export stl `rel`, where they came from)."""
    rel, stem = os.path.normpath(rel), Path(rel).stem
    if rel in readme:
        return readme[rel], "README"
    if stem in parts:
        return [f'part="{stem}"'], "file name"
    hits = [p for p in parts if f"_{p}_" in f"_{stem}_"]
    if len(hits) == 1:
        return [f'part="{hits[0]}"'], "guessed from file name"
    return None, "no README line or part named like it"


def label_of(defines):
    part = next((d.split("=", 1)[1].strip('"') for d in defines if d.startswith("part=")), "(default)")
    extra = [d for d in defines if not d.startswith("part=")]
    return part + (f" [{', '.join(extra)}]" if extra else "")


def project_jobs(project, only, fn, strict):
    cfg_path = project / "viewer" / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    scad = project / cfg["scad"] if cfg.get("scad") else sorted(project.glob("*.scad"))[0]
    parts, readme = part_list(scad.read_text()), readme_defines(project)
    fn = fn if fn is not None else cfg.get("fn")

    entries = []
    for e in cfg.get("print") or [{"stl": str(p.relative_to(project))}
                                  for p in sorted(project.glob("stl/*.stl"))]:
        if "scad" in e:
            entries.append({"defines": spec_defines(e["scad"]), "source": "viewer config",
                            "file": e["scad"].get("file"), "stl": None})
        elif "stl" in e:
            d, src = stl_defines(e["stl"], parts, readme)
            entries.append({"defines": d, "source": src, "stl": e["stl"]})
    entries += [{"defines": [f'part="{p}"'], "source": "part list", "stl": None}
                for p in parts if p.startswith("clash_")]
    if only:
        picked = []
        for name in only:
            hit = [e for e in entries if (e["stl"] and Path(e["stl"]).stem == name)
                   or (e["defines"] and label_of(e["defines"]).split(" ")[0] == name)]
            if not hit and (name in parts or not strict):   # --all skips projects without it
                hit = [{"defines": [f'part="{name}"'], "source": "--part", "stl": None}]
            picked += hit
        entries = picked

    jobs, seen = [], set()
    for e in entries:
        file, defines = str(project / (e.get("file") or scad.name)), e["defines"]
        if defines is not None and fn:
            defines = defines + [f"$fn={fn}"]
        sig = (file, tuple(defines or [e["stl"]]))
        if sig not in seen:
            seen.add(sig)
            label = label_of(e["defines"]) if defines is not None else Path(e["stl"]).stem
            jobs.append({"project": project.name, "dir": str(project), "file": file, "label": label,
                         "defines": defines, "stl": e["stl"], "source": e["source"],
                         "clash": label.startswith("clash_")})
    return jobs


# ---------- mesh analysis (ASCII STL) ----------

def read_mesh(path):
    """ASCII STL -> (vertices, triangles as index triples). Vertices are keyed by their exact
    ASCII text: Manifold leaves distinct vertices well under 1e-5 mm apart (pliers bin pocket
    floor), so float32 binary STL, or even rounding to 1e-5 mm, merges them and fakes bad edges."""
    keys, verts, tris, cur = {}, [], [], []
    with open(path, "rb") as f:
        for m in VERTEX_RE.finditer(f.read()):
            k = tuple(b"0" if x == b"-0" else x for x in m.groups())
            if k not in keys:
                keys[k] = len(verts)
                verts.append((float(k[0]), float(k[1]), float(k[2])))
            cur.append(keys[k])
            if len(cur) == 3:
                if len(set(cur)) == 3:
                    tris.append(tuple(cur))
                cur = []
    return verts, tris


def measure(verts, tris):
    """Bad edges, bodies off the bed, overhang area and its biggest patches."""
    n, edges, bodies = len(verts), {}, Sets()
    s_over, s_bridge = math.sin(math.radians(OVERHANG_DEG)), math.sin(math.radians(BRIDGE_DEG))
    bridge, over = 0.0, []
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            k = u * n + v if u < v else v * n + u
            edges[k] = edges.get(k, 0) + 1
        bodies.join(a, b)
        bodies.join(a, c)
        A, B, C = verts[a], verts[b], verts[c]
        if (A[2] + B[2] + C[2]) / 3 <= OVERHANG_Z:
            continue
        ux, uy, uz = B[0] - A[0], B[1] - A[1], B[2] - A[2]
        wx, wy, wz = C[0] - A[0], C[1] - A[1], C[2] - A[2]
        nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        if norm < 1e-12 or nz >= 0:
            continue
        if -nz / norm > s_over:
            over.append(((a, b, c), norm / 2, math.degrees(math.asin(min(1.0, -nz / norm)))))
            bridge += norm / 2 if -nz / norm > s_bridge else 0
    zmin = {}
    for i, p in enumerate(verts):
        r = bodies.find(i)
        zmin[r] = min(zmin.get(r, math.inf), p[2])
    patches, faces = {}, Sets()   # overhang faces joined through shared vertices
    for i, (tri, _, _) in enumerate(over):
        for v in tri:
            faces.join(("v", v), i)
    for i, (tri, area, deg) in enumerate(over):
        pts = [verts[v] for v in tri]
        p = patches.setdefault(faces.find(i), {"area": 0.0, "deg": 0.0, "lo": list(pts[0]), "hi": list(pts[0])})
        p["area"] += area
        p["deg"] = max(p["deg"], deg)
        for q in pts:
            p["lo"] = [min(x, y) for x, y in zip(p["lo"], q)]
            p["hi"] = [max(x, y) for x, y in zip(p["hi"], q)]
    return {"bad_edges": sum(1 for k in edges.values() if k != 2), "bodies": len(zmin),
            "floating": sorted(z for z in zmin.values() if z > Z_TOL),
            "overhang_mm2": round(sum(f[1] for f in over)), "bridge_mm2": round(bridge),
            "patches": sorted(patches.values(), key=lambda p: -p["area"])[:3]}


def slice_regions(verts, tris, z):
    """[(area mm2, (x, y))], largest first, of the separate regions in the cross-section at z.
    A triangle crossing z gives a segment between points on two of its edges; keyed by those
    edges, segments join into closed loops. Oriented by the face normal, a loop's shoelace area
    is positive round material and negative round a hole; a region is an outline plus the holes
    directly inside it."""
    loops_of, segs = Sets(), []
    for tri in tris:
        v = [verts[i] for i in tri]
        up = [p[2] > z for p in v]
        if all(up) or not any(up):
            continue
        keys, pts = [], []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if up[i] != up[j]:
                ka, kb, pa, pb = tri[i], tri[j], v[i], v[j]
                if kb < ka:
                    ka, kb, pa, pb = kb, ka, pb, pa
                f = (z - pa[2]) / (pb[2] - pa[2])
                keys.append((ka, kb))
                pts.append((pa[0] + f * (pb[0] - pa[0]), pa[1] + f * (pb[1] - pa[1])))
        nx = (v[1][1] - v[0][1]) * (v[2][2] - v[0][2]) - (v[1][2] - v[0][2]) * (v[2][1] - v[0][1])
        ny = (v[1][2] - v[0][2]) * (v[2][0] - v[0][0]) - (v[1][0] - v[0][0]) * (v[2][2] - v[0][2])
        (p, q), (kp, kq) = pts, keys
        if (q[0] - p[0]) * -ny + (q[1] - p[1]) * nx < 0:   # material on the left, outline CCW
            p, q = q, p
        segs.append((kp, p, q))
        loops_of.join(kp, kq)
    loops = {}
    for k, p, q in segs:
        lp = loops.setdefault(loops_of.find(k), {"area": 0.0, "segs": [], "box": [p[0], p[1], p[0], p[1]]})
        lp["area"] += (p[0] * q[1] - q[0] * p[1]) / 2
        lp["segs"].append((p, q))
        b = lp["box"]
        b[:] = [min(b[0], p[0], q[0]), min(b[1], p[1], q[1]), max(b[2], p[0], q[0]), max(b[3], p[1], q[1])]
    loops = [lp for lp in loops.values() if abs(lp["area"]) > 1e-6]
    if sum(lp["area"] for lp in loops) < 0:   # the mesh winds the other way
        for lp in loops:
            lp["area"] = -lp["area"]
    outer = sorted((lp for lp in loops if lp["area"] > 0), key=lambda lp: lp["area"])
    areas = {id(lp): lp["area"] for lp in outer}
    for hole in (lp for lp in loops if lp["area"] < 0):
        hb, (x, y) = hole["box"], hole["segs"][0][0]
        for lp in outer:   # the smallest outline containing the hole is its parent
            b = lp["box"]
            if b[0] <= hb[0] and b[1] <= hb[1] and b[2] >= hb[2] and b[3] >= hb[3] and sum(
                    1 for p, q in lp["segs"] if (p[1] > y) != (q[1] > y)
                    and p[0] + (y - p[1]) * (q[0] - p[0]) / (q[1] - p[1]) > x) % 2:
                areas[id(lp)] += hole["area"]
                break
    return sorted(((areas[id(lp)], ((lp["box"][0] + lp["box"][2]) / 2, (lp["box"][1] + lp["box"][3]) / 2))
                   for lp in outer if areas[id(lp)] >= SLIVER_MM2), reverse=True)


def gridfinity_cells(size):
    n = round((size + GF_GAP) / GF_PITCH)
    return n if n >= 1 and abs(n * GF_PITCH - GF_GAP - size) <= GF_TOL else 0


# ---------- one part ----------

def check_part(job, tmp, timeout):
    t0, res = time.time(), dict(job, checks=[], size=None)
    check = lambda name, status, msg: res["checks"].append({"check": name, "status": status, "msg": msg})

    def done():
        res["status"] = max((c["status"] for c in res["checks"]), key=("PASS", "WARN", "FAIL").index)
        res["seconds"] = round(time.time() - t0, 1)
        return res

    if job["defines"] is None:
        check("export", "WARN", f"not checked: no export found for {job['stl']} ({job['source']}); "
              "add a README regenerate line or a viewer `scad` spec")
        return done()
    tag = re.sub(r"\W+", "_", f"{job['project']}_{job['label']}")
    stl, summ = os.path.join(tmp, tag + ".stl"), os.path.join(tmp, tag + ".json")
    cmd = [OPENSCAD, "--hardwarnings", "--summary", "all", "--summary-file", summ,
           "--export-format", "asciistl", "-o", stl] + [x for d in job["defines"] for x in ("-D", d)]
    try:
        p = subprocess.run(cmd + [job["file"]], capture_output=True, text=True, timeout=timeout, cwd=job["dir"])
    except subprocess.TimeoutExpired:
        check("export", "FAIL", f"timed out after {timeout} s")
        return done()
    lines = [ln.strip() for ln in (p.stderr + p.stdout).splitlines() if ln.strip() and not ln.startswith("ECHO:")]
    empty = any(EMPTY_RE.search(ln) for ln in lines) or not os.path.exists(stl) or os.path.getsize(stl) < 100
    bad = [ln for ln in lines if BAD_RE.search(ln) and not EMPTY_RE.search(ln)]
    geo = json.loads(Path(summ).read_text()).get("geometry", {}) if os.path.exists(summ) else {}
    box = geo.get("bounding_box", {})

    if job["clash"]:
        if bad or (p.returncode and not empty):
            check("clash", "FAIL", "; ".join(bad[:3] or lines[-1:]) or f"exit {p.returncode}")
        elif empty:
            check("clash", "PASS", "empty")
        else:
            span = ", ".join(f"{a} {lo:.2f}..{hi:.2f}" for a, lo, hi in zip("xyz", box["min"], box["max"]))
            check("clash", "FAIL", f"overlap {' x '.join(f'{s:.2f}' for s in box['size'])} mm at {span}")
        return done()
    if p.returncode or bad or empty or geo.get("simple") is False:
        why = bad[:3] or (["empty geometry"] if empty else ["summary: simple false"] if p.returncode == 0
                          else lines[-1:] or [f"exit {p.returncode}"])
        check("export", "FAIL", "; ".join(why)[:300])
        return done()
    check("export", "PASS", f"{geo.get('facets', '?')} facets")

    verts, tris = read_mesh(stl)
    m = measure(verts, tris)
    res["metrics"] = {k: v for k, v in m.items() if k != "patches"}
    check("manifold", "FAIL" if m["bad_edges"] else "PASS",
          f"{m['bad_edges']} edge(s) not shared by exactly two faces")

    lo = box["min"] if box else [min(v[i] for v in verts) for i in range(3)]
    size = res["size"] = box["size"] if box else [max(v[i] for v in verts) - lo[i] for i in range(3)]
    if abs(lo[2]) > Z_TOL:
        check("bed", "FAIL", f"lowest point at z = {lo[2]:.3f}, not 0")
    elif any(s > b + Z_TOL for s, b in zip(size, job["bed"])):
        check("bed", "FAIL", "%.1f x %.1f x %.1f mm is bigger than the %g x %g x %g bed" % (*size, *job["bed"]))
    elif m["floating"]:
        check("bed", "WARN", f"{len(m['floating'])} of {m['bodies']} bodies never touch the bed "
              f"(lowest at z = {m['floating'][0]:.2f})")
    else:
        check("bed", "PASS", "on z = 0, fits the bed")

    regions = slice_regions(verts, tris, lo[2] + LAYER_Z)
    res["layer1_mm2"] = [round(a, 1) for a, _ in regions]
    islands = [(a, c) for a, c in regions if a < ISLAND_MM2]
    if islands and regions[0][0] >= BIG_MM2:
        where = ", ".join(f"{a:.1f} mm2 at ({x:.1f}, {y:.1f})" for a, (x, y) in islands[:6])
        check("layer1", "WARN", f"{len(regions)} regions; {len(islands)} island(s) under 1 cm2 beside "
              f"a {regions[0][0] / 100:.1f} cm2 one: {where}")
    else:
        check("layer1", "PASS", f"{len(regions)} region(s)")

    nx, ny = gridfinity_cells(size[0]), gridfinity_cells(size[1])
    if nx and ny and size[2] > GF_MIN_H:
        res["feet"] = [len(regions), nx * ny]
        check("feet", "FAIL" if len(regions) < nx * ny else "PASS",
              f"{nx}x{ny} Gridfinity: expected {nx * ny} feet, found {len(regions)} first-layer regions")

    big = m["overhang_mm2"] > OVERHANG_WARN_MM2
    msg = f"{m['overhang_mm2']} mm2 past 45 deg, {m['bridge_mm2']} of it flat bridges"
    if big:
        msg += "; biggest: " + "; ".join(
            f"{p['area']:.0f} mm2 up to {p['deg']:.0f} deg at "
            + ", ".join(f"{a} {lo:.1f}..{hi:.1f}" for a, lo, hi in zip("xyz", p["lo"], p["hi"]))
            for p in m["patches"])
    check("overhang", "WARN" if big else "PASS", msg)
    return done()


# ---------- report ----------

def summary_line(r):
    if r["clash"]:
        return r["checks"][0]["msg"].split(" mm at ")[0] + (" mm" if r["status"] == "FAIL" else "")
    if "metrics" not in r:
        return "not checked" if r["status"] == "WARN" else "export failed"
    bits = [" x ".join(f"{s:.1f}" for s in r["size"]) + " mm", f"layer1 {len(r['layer1_mm2'])}"]
    bits += ["feet %d/%d" % tuple(r["feet"])] if r.get("feet") else []
    return "  ".join(bits + [f"overhang {r['metrics']['overhang_mm2']} mm2"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("projects", nargs="*")
    ap.add_argument("--all", action="store_true", help="every project folder with a .scad")
    ap.add_argument("--part", help="comma-separated part values or stl stems")
    ap.add_argument("--fn", type=int, help="pass -D '$fn=N'")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-j", type=int, default=os.cpu_count() or 4, help="parallel exports")
    ap.add_argument("--timeout", type=int, default=600, help="seconds per part")
    a = ap.parse_args()
    root = kit.workspace()
    dirs = (sorted(d for d in root.iterdir() if d.is_dir() and any(d.glob("*.scad"))) if a.all
            else [Path(p).resolve() for p in a.projects])
    if not dirs:
        sys.exit(__doc__)
    only = [s.strip() for s in a.part.split(",")] if a.part else None
    jobs = [j for d in dirs for j in project_jobs(d, only, a.fn, a.all)]
    for j in jobs:
        j["bed"] = kit.bed(j["dir"])
    if not jobs:
        sys.exit("no parts to check")

    t0, results = time.time(), []
    tmp = tempfile.mkdtemp(prefix="check_scad_")
    try:
        with concurrent.futures.ProcessPoolExecutor(max(1, a.j)) as ex:
            for f in concurrent.futures.as_completed([ex.submit(check_part, j, tmp, a.timeout) for j in jobs]):
                results.append(f.result())
                if sys.stderr.isatty():
                    r = results[-1]
                    print(f"  {r['status']:<4} {r['project']}/{r['label']} ({r['seconds']} s)", file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    order = {(j["project"], j["label"]): i for i, j in enumerate(jobs)}
    results.sort(key=lambda r: order[(r["project"], r["label"])])
    elapsed, failed = round(time.time() - t0, 1), any(r["status"] == "FAIL" for r in results)

    if a.json:
        print(json.dumps({"ok": not failed, "seconds": elapsed,
                          "parts": [{k: v for k, v in r.items() if k != "dir"} for r in results]}, indent=1))
        sys.exit(1 if failed else 0)
    w = max(len(f"{r['project']}/{r['label']}") for r in results)
    for r in results:
        print(f"{r['status']:<4}  {r['project'] + '/' + r['label']:<{w}}  {summary_line(r)}  ({r['seconds']:.0f} s)")
    for r in (r for r in results if r["status"] != "PASS"):
        print(f"\n{r['project']}/{r['label']}" + (f"  ({r['stl']})" if r["stl"] else ""))
        for c in r["checks"]:
            if c["status"] != "PASS":
                print(f"  {c['status']:<4} {c['check']:<9} {c['msg']}")
    n = {s: sum(r["status"] == s for r in results) for s in ("PASS", "WARN", "FAIL")}
    print(f"\n{len(results)} parts: {n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail in {elapsed:.0f} s")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

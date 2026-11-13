#!/usr/bin/env python3
"""Check what print-kit needs, and install what's missing.

    python3 doctor.py              # report: what's there, what's missing
    python3 doctor.py --json       # the same, machine-readable (the setup skill reads this)
    python3 doctor.py --install    # install OpenSCAD if missing, with the platform's package manager

Needs: Python 3.9+ (you're running it) and OpenSCAD. Everything else is optional and only
reported: a slicer (for the viewer's Open in <slicer> button) and Portless (https URLs).
Standard library only.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SYSTEM = platform.system()  # Darwin, Linux, Windows

# name -> (mac app bundle names, linux/windows executables)
SLICERS = {
    "Bambu Studio": (["BambuStudio"], ["bambu-studio", "BambuStudio"]),
    "OrcaSlicer": (["OrcaSlicer"], ["orca-slicer", "OrcaSlicer"]),
    "PrusaSlicer": (["PrusaSlicer", "Original Prusa Drivers/PrusaSlicer"], ["prusa-slicer", "PrusaSlicer"]),
    "Cura": (["UltiMaker Cura", "Ultimaker Cura"], ["cura", "UltiMaker-Cura"]),
}
WIN_DIRS = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None


def find_openscad():
    """(path, version) or (None, None). Also finds the macOS app when it isn't on PATH."""
    cands = [shutil.which("openscad")]
    if SYSTEM == "Darwin":
        cands += [str(p / "Contents/MacOS/OpenSCAD") for p in sorted(Path("/Applications").glob("OpenSCAD*.app"))]
    if SYSTEM == "Windows":
        cands += [str(Path(d) / "OpenSCAD" / "openscad.exe") for d in WIN_DIRS]
    for c in cands:
        if c and Path(c).exists():
            r = run([c, "--version"])
            if r:
                return c, (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "?"
    return None, None


def find_slicers():
    found = {}
    for name, (apps, exes) in SLICERS.items():
        if SYSTEM == "Darwin":
            for a in apps:
                app = Path("/Applications") / f"{a}.app"
                if app.exists():
                    found[name] = ["open", "-n", "-a", app.stem, "--args", "{file}"]
                    break
        else:
            for e in exes:
                p = shutil.which(e)
                if not p and SYSTEM == "Windows":
                    hits = [q for d in WIN_DIRS for q in Path(d).glob(f"*/{e}.exe")]
                    p = str(hits[0]) if hits else None
                if p:
                    found[name] = [p, "{file}"]
                    break
    return found


def install_command():
    """The command that installs OpenSCAD here, or None."""
    if SYSTEM == "Darwin" and shutil.which("brew"):
        return ["brew", "install", "--cask", "openscad@snapshot"]   # the stable cask is disabled
    if SYSTEM == "Windows" and shutil.which("winget"):
        return ["winget", "install", "-e", "--id", "OpenSCAD.OpenSCAD"]
    if SYSTEM == "Linux":
        for pm, cmd in (("apt-get", ["sudo", "apt-get", "install", "-y", "openscad"]),
                        ("dnf", ["sudo", "dnf", "install", "-y", "openscad"]),
                        ("pacman", ["sudo", "pacman", "-S", "--noconfirm", "openscad"]),
                        ("flatpak", ["flatpak", "install", "-y", "flathub", "org.openscad.OpenSCAD"])):
            if shutil.which(pm):
                return cmd
    return None


def report():
    scad, ver = find_openscad()
    on_path = bool(shutil.which("openscad"))
    return {
        "platform": SYSTEM,
        "python": {"ok": sys.version_info >= (3, 9), "version": platform.python_version()},
        "openscad": {"ok": bool(scad), "path": scad, "version": ver, "on_path": on_path,
                     "install": install_command()},
        "slicers": find_slicers(),
        "portless": bool(shutil.which("portless")),
        "ready": bool(scad) and sys.version_info >= (3, 9),
    }


def link_openscad(path):
    """macOS app found but not on PATH: link it next to brew's binaries."""
    if SYSTEM != "Darwin" or shutil.which("openscad"):
        return
    r = run(["brew", "--prefix"]) if shutil.which("brew") else None
    bindir = Path(r.stdout.strip()) / "bin" if r and r.returncode == 0 else Path("/usr/local/bin")
    try:
        (bindir / "openscad").symlink_to(path)
        print(f"linked {bindir / 'openscad'} -> {path}")
    except OSError as e:
        print(f"couldn't link openscad into {bindir}: {e}")


def main():
    args = sys.argv[1:]
    rep = report()
    if "--install" in args:
        if not rep["openscad"]["ok"]:
            cmd = rep["openscad"]["install"]
            if not cmd:
                sys.exit("No package manager found. Install OpenSCAD from https://openscad.org/downloads.html")
            print("running:", " ".join(cmd), flush=True)
            if subprocess.run(cmd).returncode:
                sys.exit("OpenSCAD install failed; see the output above.")
        scad, _ = find_openscad()
        if scad:
            link_openscad(scad)
        rep = report()
    if "--json" in args:
        print(json.dumps(rep, indent=2))
        return
    o = rep["openscad"]
    print(f"python    {'ok' if rep['python']['ok'] else 'TOO OLD (need 3.9+)'}  {rep['python']['version']}")
    if o["ok"]:
        print(f"openscad  ok  {o['version']}" + ("" if o["on_path"] else f"  (not on PATH: {o['path']})"))
    else:
        print("openscad  MISSING  run: python3 doctor.py --install" + (f"  ({' '.join(o['install'])})" if o["install"] else ""))
    print("slicer    " + (", ".join(rep["slicers"]) or "none found (optional: the viewer saves .3mf files instead)"))
    print("portless  " + ("yes" if rep["portless"] else "no (optional)"))
    print("\nready" if rep["ready"] else "\nnot ready")
    sys.exit(0 if rep["ready"] else 1)


if __name__ == "__main__":
    main()

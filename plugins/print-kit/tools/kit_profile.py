#!/usr/bin/env python3
"""The user's print-kit profile: printer, slicer, materials, house rules.

    python3 kit_profile.py [<path>]          # print the profile that applies to <path> (default: cwd)
    python3 kit_profile.py --where [<path>]  # print which file it came from

Lookup, first hit wins:
  1. print-kit.json in <path> or any folder above it (the workspace profile),
  2. $PRINT_KIT_PROFILE,
  3. ~/.config/print-kit/print-kit.json (the user-wide profile).
Missing keys fall back to DEFAULTS, so an old or partial profile still works. The bed size is the
exception: tools that size parts against it call require_bed(), which stops when no profile sets it.
The /print-kit:setup skill writes the file.
"""

import copy
import glob
import json
import os
import platform
import shutil
import sys
from pathlib import Path

# Windows consoles and pipes default to a legacy code page that can't print every character.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

NAME = "print-kit.json"
SYSTEM = platform.system()  # Darwin, Linux, Windows
USER_FILE = Path.home() / ".config" / "print-kit" / NAME

DEFAULTS = {
    "version": 1,
    "user": {"name": "", "reply_style": "short"},
    "printer": {
        "name": "",
        "bed_mm": [220, 220, 250],
        "nozzle_mm": 0.4,
        "other_nozzles_mm": [],
        "plate": "",
    },
    "slicer": {
        "name": "",
        "open_command": [],          # e.g. ["open", "-n", "-a", "BambuStudio", "--args", "{file}"]
        "presets": {},               # e.g. {"default": "0.20mm Standard", "gridfinity": "..."}
    },
    "materials": {"default": "PLA", "owned": ["PLA"]},
    "server": {"launcher": "plain"},  # "portless" when https://<name>.localhost URLs are wanted
    "rules": {
        "ask_before_print": True,
        "open_slicer_only_when_asked": True,
        "gridfinity_outline_gate": True,
        "fit_test_first": True,
        "supports": "avoid, but use them rather than distort a shape",
        "commit_after_changes": True,
    },
    "openscad": "",                 # path to the OpenSCAD binary; "" finds it (see openscad())
    "data_dir": "data",
    "taste": [],
    "notes": [],
}


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def find_workspace(start=None):
    """print-kit.json in `start` or a folder above it, or None."""
    p = Path(start or os.getcwd()).resolve()
    for d in [p, *p.parents] if p.is_dir() else [*p.parents]:
        if (d / NAME).is_file():
            return d / NAME
    return None


def find(start=None):
    """Path of the profile that applies to `start`, or None."""
    ws = find_workspace(start)
    if ws:
        return ws
    env = os.environ.get("PRINT_KIT_PROFILE")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser()
    return USER_FILE if USER_FILE.is_file() else None


def load(start=None):
    """The merged profile, with `_file` and `_root` (the workspace folder) filled in."""
    path = find(start)
    prof = merge(DEFAULTS, json.loads(path.read_text(encoding="utf-8")) if path else {})
    prof["_file"] = str(path) if path else None
    ws = find_workspace(start)
    prof["_root"] = str(ws.parent) if ws else None
    return prof


def workspace(start=None):
    """The workspace root: the folder holding print-kit.json, else `start` itself."""
    prof = load(start)
    return Path(prof["_root"] or start or os.getcwd()).resolve()


def bed(start=None):
    b = load(start)["printer"]["bed_mm"]
    return tuple(float(x) for x in (list(b) + [b[-1]] * 3)[:3])


def require_bed(start=None):
    """Stop unless a profile sets the bed size: a guessed bed passes parts that don't fit the real one."""
    path = find(start)
    if path and (json.loads(path.read_text(encoding="utf-8")).get("printer") or {}).get("bed_mm"):
        return
    where = f"{path} has no printer.bed_mm" if path else f"no {NAME} here, above, or in {USER_FILE.parent}"
    sys.exit(f"print-kit: {where}, so the bed size is unknown.\n"
             "Run /print-kit:setup in Claude Code (it asks about the printer and writes the file), "
             "then run this again.")


def data_home():
    """Per-user folder for things print-kit installs (OpenSCAD when no package manager did)."""
    if SYSTEM == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "print-kit"
    if SYSTEM == "Darwin":
        return Path.home() / "Library" / "Application Support" / "print-kit"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "print-kit"


def _console(path):
    """On Windows, openscad.exe is a GUI program that prints nothing; openscad.com is its console twin."""
    com = Path(path).with_suffix(".com")
    return str(com) if SYSTEM == "Windows" and com.is_file() else str(path)


def openscad_candidates():
    """Where OpenSCAD may be, most likely first: PATH, print-kit's own install, the usual app folders."""
    found = [shutil.which("openscad")]
    if SYSTEM == "Darwin":
        for apps in (Path.home() / "Applications", Path("/Applications")):
            found += sorted(glob.glob(str(apps / "OpenSCAD*.app" / "Contents" / "MacOS" / "OpenSCAD")))
    elif SYSTEM == "Windows":
        found += sorted(glob.glob(str(data_home() / "openscad" / "*" / "openscad.com")), reverse=True)
        for env in ("ProgramFiles", "ProgramFiles(x86)"):
            if os.environ.get(env):
                found += sorted(glob.glob(os.path.join(os.environ[env], "OpenSCAD*", "openscad.exe")))
    else:
        found.append(str(data_home() / "openscad" / "openscad"))
    return [_console(f) for f in found if f and Path(f).is_file()]


def openscad(start=None):
    """The OpenSCAD binary to run: the profile's `openscad` if set, else the first candidate, else "openscad"."""
    own = load(start).get("openscad")
    if own and Path(own).expanduser().is_file():
        return _console(Path(own).expanduser())
    found = openscad_candidates()
    return found[0] if found else "openscad"


def main():
    args = sys.argv[1:]
    where = "--where" in args
    args = [a for a in args if a != "--where"]
    start = args[0] if args else None
    if where:
        print(find(start) or "no profile (defaults; run /print-kit:setup)")
    else:
        print(json.dumps(load(start), indent=2))


if __name__ == "__main__":
    main()

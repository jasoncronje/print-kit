#!/usr/bin/env python3
"""SessionStart hook: load the house rules and the user's profile into the session.

With a workspace print-kit.json (in the project folder or above it), it adds the rules, the
profile and the tools path. A user-wide profile ($PRINT_KIT_PROFILE or ~/.config/print-kit/)
does the same, but only in folders with .scad files. With no profile it stays silent unless
the folder has .scad files, and then only suggests /print-kit:setup.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT / "tools"))
import kit_profile as kit  # noqa: E402


def emit(text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))


def profile_summary(p):
    pr, sl, rules = p["printer"], p["slicer"], p["rules"]
    lines = [
        f"- Profile file: {p['_file']}" + (f" (workspace {p['_root']})" if p["_root"] else " (user-wide)"),
        f"- User: {p['user']['name'] or '(unnamed)'}; replies: {p['user']['reply_style']}",
        f"- Printer: {pr['name'] or '(not set)'}, bed {' x '.join(str(x) for x in pr['bed_mm'])} mm, "
        f"nozzle {pr['nozzle_mm']} mm" + (f" (also owns {pr['other_nozzles_mm']})" if pr["other_nozzles_mm"] else "")
        + (f", plate {pr['plate']}" if pr["plate"] else ""),
        f"- Slicer: {sl['name'] or '(not set)'}" + (f"; presets {json.dumps(sl['presets'])}" if sl["presets"] else "")
        + ("" if sl["open_command"] else "; no open_command, so the viewer saves the .3mf instead"),
        f"- Materials: default {p['materials']['default']}, owned {', '.join(p['materials']['owned'])}",
        f"- Data folder: {p['data_dir']}; pages served with launcher '{p['server']['launcher']}'",
        "- Rules: " + ", ".join(f"{k}={v}" for k, v in rules.items()),
    ]
    if p["taste"]:
        lines.append("- Taste (beats the default taste list):\n" + "\n".join(f"  - {t}" for t in p["taste"]))
    if p["notes"]:
        lines.append("- Notes:\n" + "\n".join(f"  - {t}" for t in p["notes"]))
    return "\n".join(lines)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    tools = ROOT / "tools"
    has_scad = any(cwd.glob("*.scad")) or any(cwd.glob("*/*.scad")) or any(cwd.glob("*/*/*.scad"))
    p = kit.load(cwd)
    if p["_file"] and not p["_root"] and not has_scad:
        return  # user-wide profile, but this folder has no models: stay out of the way
    if not p["_file"]:
        if has_scad:
            emit("print-kit is installed but has no profile here. If the user wants help with these "
                 "OpenSCAD models, suggest /print-kit:setup (it asks about their printer and slicer).")
        return
    rules = (ROOT / "rules" / "house-rules.md").read_text()
    emit(f"{rules}\n\n## This user's profile\n\n{profile_summary(p)}\n\n"
         f"`<tools>` above is {tools} (run its scripts with python3; `doctor.py` checks and installs "
         "OpenSCAD).")


if __name__ == "__main__":
    main()

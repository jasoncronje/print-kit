---
name: setup
description: Set up or change the print-kit profile (printer, bed size, nozzle, slicer and how to open it, materials, house rules, taste) and the workspace's data folder. Use when the user runs /print-kit:setup, starts their first print-kit project, says their printer or slicer changed, or when the session says print-kit has no profile here.
argument-hint: "[workspace folder]"
---

# Set up print-kit

The profile is one JSON file, `print-kit.json`. Every tool and skill reads it. Defaults and the
lookup order live in `${CLAUDE_PLUGIN_ROOT}/tools/kit_profile.py`; the template with every field is
`${CLAUDE_PLUGIN_ROOT}/templates/print-kit.json`.

## 1. Where

- **Workspace profile** (default): `print-kit.json` at the root of the folder that holds their
  projects (the argument, else the current folder). It can be committed with the projects.
- **User-wide**: `~/.config/print-kit/print-kit.json`, for people who keep projects in many places.
  A workspace profile overrides it.

If a profile already exists (`python3 ${CLAUDE_PLUGIN_ROOT}/tools/kit_profile.py --where`), read it
and change only what the user asks.

## 2. Ask (one short round, AskUserQuestion when available)

Ask only what you can't find out. Detect first with one command (it finds a working Python on
macOS, Linux and Windows/Git Bash, where `python3` often isn't one):

```bash
sh ${CLAUDE_PLUGIN_ROOT}/scripts/py.sh ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --json
```

- **Exit 127: no Python 3.9+.** Every print-kit tool needs it (standard library only, no
  packages). Say so in one line and offer the install, then rerun the command:
  - macOS: `brew install python` if `brew` exists; else `xcode-select --install`, which opens a
    system dialog the user clicks through (about 5 min).
  - Windows: `winget install -e --id Python.Python.3.13 --scope user` (no admin). PATH only
    updates in new shells: tell them to restart Claude Code, then run setup again.
  - Ubuntu/Debian: it's almost always there; if not, the user runs `sudo apt install -y python3`
    in a terminal (you can't answer sudo's password prompt).
- **OpenSCAD missing:** say so in one line with the `openscad.install.describe` text it reports,
  and ask once (in the question round below) whether to install it. On yes, run
  `sh ${CLAUDE_PLUGIN_ROOT}/scripts/py.sh ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --install`.
  It needs no admin rights: Homebrew on a Mac that has it, otherwise the official snapshot from
  files.openscad.org (about 80-100 MB, SHA-256 checked) into a per-user folder. The download
  takes a minute or two; run it with a 10 minute timeout. Only Linux on a non-x86 CPU falls back
  to apt/dnf/pacman with sudo: if that fails, give the user the command to run in a terminal.
  Ubuntu Server and minimal installs may lack graphics libraries (`libegl1` and friends) the
  snapshot needs: `--install` installs them when sudo needs no password, else it prints the
  exact `sudo apt-get install` line. Give the user that line to run in a terminal, then rerun
  `--install` (`openscad.missing_libs` in the JSON lists what's missing).
  `install` is null: point to https://openscad.org/downloads.html. Don't stop setup for it.
- **Slicers:** use the detected ones to preselect the slicer question and fill `open_command`.
  None found: the viewer saves `.3mf` files instead; don't install one.
- **Portless** present: offer `server.launcher = "portless"`. Absent: leave `"plain"`, don't mention it.
- Use the reported `python.path` and `openscad.path` for the rest of setup. When OpenSCAD isn't
  on PATH (`on_path` false), commands in the skills that say `openscad` mean that path; new
  sessions are told so automatically.

Then ask:

1. **Printer**: model, bed size X × Y × Z mm (look it up from the model and confirm), nozzle they
   use for real parts, other nozzles they own, build plate.
2. **Slicer**: which one, and the process preset names they use (default, and Gridfinity if they make bins).
3. **Materials**: default and others they own.
4. **Rules** (all on by default; show them as a list to switch off): ask before any print, open the
   slicer only when asked, Gridfinity outline-first gate, offer fit tests first, commit after changes.
5. **Taste** (optional): anything they always or never want in a design. Leave empty for the
   default taste list in the `scad-design` skill.
6. Their name and whether they like short or detailed replies (optional).

## 3. Slicer open command

`slicer.open_command` is the command list the viewer's "Open in <slicer>" button runs, with
`{file}` replaced by the plate's `.3mf`. Leave it `[]` to make the button save the file instead.

| Slicer | macOS | Linux | Windows |
|---|---|---|---|
| Bambu Studio | `["open", "-n", "-a", "BambuStudio", "--args", "{file}"]` | `["bambu-studio", "{file}"]` | `["C:\\Program Files\\Bambu Studio\\bambu-studio.exe", "{file}"]` |
| OrcaSlicer | `["open", "-n", "-a", "OrcaSlicer", "--args", "{file}"]` | `["orca-slicer", "{file}"]` | `["C:\\Program Files\\OrcaSlicer\\orca-slicer.exe", "{file}"]` |
| PrusaSlicer | `["open", "-n", "-a", "PrusaSlicer", "--args", "{file}"]` | `["prusa-slicer", "{file}"]` | `["C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe", "{file}"]` |
| Cura | `["open", "-n", "-a", "UltiMaker Cura", "--args", "{file}"]` | `["cura", "{file}"]` | path to `UltiMaker-Cura.exe` |

`open -n` starts a separate window so their open project isn't replaced. Prefer the command the
doctor reported for a detected slicer; otherwise check the path exists before writing it.

## 4. Write

1. Write `print-kit.json` from the template with their answers. Keep every key.
2. Workspace profile only: create the data folder from `${CLAUDE_PLUGIN_ROOT}/templates/data/`
   if it doesn't exist (`cp -Rn`, never overwrite their data). Leave an existing one alone.
3. Add `viewer/index.html`, `trace/index.html`, `trace/photo.jpg`, `layout/index.html` (built
   files) to the workspace `.gitignore` if it's a git repo.
4. Check: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/kit_profile.py <workspace>` prints the merged profile.
5. Tell the user the profile takes effect in new sessions (or after `/clear`), and show the
   few values they set in one short list.

## Notes

- Never guess a bed size silently: a wrong one makes `check_scad.py` pass parts that don't fit.
- The clearances in the `scad-design` skill come from one person's Bambu P2S with PLA on a 0.4
  nozzle. Say so once, and say their own `data/fits.csv` replaces them as they test fits.

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

Ask only what you can't find out. Detect first with one command:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --json
```

It reports Python, OpenSCAD (also the macOS app when it isn't on PATH), installed slicers with
their `open_command`, and Portless. Every print-kit tool is standard-library Python; OpenSCAD is
the only real dependency.

- **OpenSCAD missing, or found but not on PATH:** say so in one line, show the `openscad.install`
  command it reports, and ask once (in the same question round below) whether to install it. On
  yes, run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py --install` (it installs, then links the
  binary onto PATH on macOS). `sudo` on Linux prompts in their terminal: if it can't, give them the
  command to run. No package manager: point to https://openscad.org/downloads.html. Don't stop
  setup for it.
- **Slicers:** use the detected ones to preselect the slicer question and fill `open_command`.
  None found: the viewer saves `.3mf` files instead; don't install one.
- **Portless** present: offer `server.launcher = "portless"`. Absent: leave `"plain"`, don't mention it.

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

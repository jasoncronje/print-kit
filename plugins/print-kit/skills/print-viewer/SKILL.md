---
name: print-viewer
description: Build, update or publish a project's interactive 3D viewer (assembled view, pull-apart, split view, measure, X-ray, colour and opacity per part, print plates on the user's bed with overhangs, Open in the user's slicer), and say which nozzle each plate needs. Use whenever the user asks to see a model in 3D, wants a viewer for a new project, or after a model change that the viewer should show.
---

# 3D print viewer

One shared page serves every project. The tools live in `${CLAUDE_PLUGIN_ROOT}/tools/` (below, `T`).

- `T/viewer/template.html`: the page. `T/viewer_server.py` serves it **live** to every local viewer,
  so a plugin update shows on reload, with nothing to rebuild.
- `<project>/viewer/config.json`: hand-written, per project.
- `T/make_viewer.py <project>`: exports the meshes into `viewer/data.json` (built; never hand-edit) and
  writes `viewer/index.html`, a static copy with the data inline (gitignore it). It opens straight from
  disk with no server; there the slicer button saves the `.3mf` instead.
- The bed size, printer and slicer name come from the user's `print-kit.json` (`kit_profile.py`);
  `config.json` can override them with `bed`, `printer`, `slicer`.

## Steps

1. Write or update `<project>/viewer/config.json` (format below).
2. Build after a model or config change: `python3 T/make_viewer.py <project>` (sandbox off when
   sandboxed: it runs OpenSCAD). It prints each mesh and the data size. `make_viewer.py --page
   <project>` refreshes the static `index.html` without re-exporting meshes.
3. Serve it and show the URL:
   - Profile launcher `plain`: run `python3 T/viewer_server.py <project>/viewer` in the background;
     it prints `http://127.0.0.1:<port>/`. Set `PORT=<n>` for a fixed port.
   - Launcher `portless`: `portless <project>-viewer sh -c 'python3 T/viewer_server.py <project>/viewer'`,
     URL `https://<project>-viewer.localhost`.
   - Open it in the app's browser if there is one (T3 Code `preview_open`, Claude desktop
     `preview_start` with a `.claude/launch.json` entry, or the Chrome tools); otherwise give the URL.
   The server exits about 5 minutes after the last viewer tab closes (each open tab pings it every
   minute). Never a plain `python3 -m http.server`: the served page needs the helper.
   The helper backs the slicer button: it saves the plate's `.3mf` and runs the profile's
   `slicer.open_command`. The button is the user's to press; agents don't click it.
4. Publish a claude.ai Artifact **only when the user asks** (a link, a share, "publish"). Artifacts cap
   at 16 MB and big meshes overrun it; the build warns when data.json is too big. Publish the static
   `viewer/index.html` with the Artifact tool; it carries its data, so no `files` are needed. If the
   project already has an artifact, pass its `url` so the link stays the same. Declare
   `capabilities: {"downloads": true}` so the plate button works (it saves a `.zip` there).
5. Commit the config and `data.json` if the workspace is a git repo.

## config.json

Coordinates are the model's own millimetres, as in the `.scad` file.

```json
{
  "title": "Power Strip Pod",
  "scad": "power_strip_box.scad",
  "up": "y",                     // which model axis points up when assembled: "z" (default) or "y"
  "explode_mm": 120,             // default pull-apart distance when a part has no "explode"
  "print_color": "#1d8a93",      // default colour for print parts
  "facts": [["Outside", "124.8 × 143.8 × 116.7 mm"]],   // shown when nothing is selected
  "assembly": [ /* parts as assembled */ ],
  "plates": [ { "id": "cover", "name": "Cover", "note": "0.4 nozzle. Front face down, no supports" } ],
  "print": [ /* parts in print orientation, one plate each */ ]
}
```

Each assembly or print part needs exactly one mesh source:

- `"scad": {"part": "cover_in_place", "define": {"upright": true}}` runs OpenSCAD on the project's `.scad`.
  Add a `part` to the model when a placed assembly copy is missing (e.g. `asm_hook`).
- `"stl": "stl/cover.stl"` uses an existing file (ASCII or binary).
- `"shape": {...}` draws context: `box {size}` (centred), `cylinder {r, h, axis, center}`,
  `tube {ro, ri, h, axis, center}`, `lathe {points: [[r, h], ...], axis}`.

Optional part fields:

- `id`, `name`, `color`, `qty`, `material`, `facts: [[k, v]]`.
- `context: true` marks things that aren't printed (wall, tool, spools). Framing and the split view ignore them.
- `hidden: true` starts the part switched off. `opacity` fades it.
- `explode: [x, y, z]` is the pull-apart offset in mm at 100%.
- `instances: [{pos, rot, color}]` places copies. `rot` is in degrees.
- `repeat: {count, start, step, rot, colors}` places evenly spaced copies.
- Print parts: `plate` (a plate id), `count` (copies on the plate), `settings` (one line), `check`
  (what to look for on a test print; shown highlighted).

Keep the copy short: labels and values, no paragraphs.

## Nozzle

Every plate uses the profile's `printer.nozzle_mm` unless the user asks otherwise. Fits are tuned on
that nozzle and don't carry to another.

- Plate `settings` starts with the nozzle and the slicer preset, e.g.
  `"0.4 nozzle, 0.20mm Standard, no supports"`. Gridfinity bins use the profile's `gridfinity` preset
  if it has one.
- Plate `note` starts with it too (`"0.4 nozzle. Flat, no supports."`), so the plate list shows it.
- The project README's print settings name the nozzle.
- A plate for another nozzle is labelled "0.6 nozzle (prototype)" (or whichever) and kept separate.

## Notes

- Look: one sans font (Geist), ink on neutral grey chrome, flat panels, 1px borders, no shadows, blur
  or gradients. Colour belongs to the parts, the bed and overhang red. UI strings are labels and
  values ("Point 1", "Overruns the 256 × 256 bed"). `settings` renders as tags split on commas.
- Controls: scroll or pinch zooms toward the cursor, `+`/`−` step 10%. Colour and opacity per part in
  the part's card, or "All parts" in the parts panel; Reset returns to the config. View-only.
- The viewer lays each plate out on the bed and warns when parts overrun it.
- Overhangs: faces pointing down past 45° and above the bed, shown red, with the area in cm².
- Slicer button: local helper with an `open_command` → opens the slicer; otherwise saves the `.3mf`.
  In claude.ai the downloads capability only accepts `.zip`, so it saves the `.3mf` inside a `.zip`.
- "Copy load request for Claude" copies a prompt for loading that plate into the slicer with its settings.

## Slicer settings in a 3MF (Bambu Studio / OrcaSlicer)

For supports or any per-object setting on a plate, build a 3MF rather than clicking in the slicer.

- Per-object keys go in `Metadata/model_settings.config`: `<metadata key="enable_support" value="1"/>`,
  `support_type` = `tree(manual)`, `support_on_build_plate_only` = `1` or `0`. An enforcer is a
  `<part subtype="support_enforcer">`. Per-object brim: `brim_type` = `outer_only`, `brim_width`.
- Stamp the installed slicer version into `3D/3dmodel.model` `Application` (macOS:
  `CFBundleShortVersionString` in the app's `Contents/Info.plist`). An older stamp makes Bambu load the
  geometry and drop the settings.
- Also write `Metadata/project_settings.config`. Without it Bambu says "old version, loading geometry
  data only" and drops the supports even with the right stamp.
- Overriding presets in a project: keep every list at the base project's length, set `inherits_group`
  and `print_compatible_printers` to match, and list every override in `different_settings_to_system`,
  or Bambu resets it.
- Check by slicing it in the app: no "floating cantilever" warning where supports were meant.
- Opening a 3MF with File > Open Project replaces the user's current plate: say so.

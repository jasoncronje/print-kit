# Changelog

## 2026-11-13
- Tests: `tests/editors_test.py` and a sample `bit-bin` build the photo-trace and layout editors,
  serve them, save through the server and rebuild from the saved trace. Runs in CI on all three
  systems. The pages' own drawing code still has no browser test.
- README: private-repo login notes removed from the install guides; the slicer button's tested
  scope (Bambu Studio on macOS only) is stated in the viewer section.
- `check_scad.py` and `make_viewer.py` stop with "run /print-kit:setup" when no profile sets
  `printer.bed_mm`, instead of quietly checking against the default 220 mm bed (a part could pass
  for a bed the user doesn't have). A viewer config with its own `bed` still builds. `doctor.py`
  and the viewer server need no profile, as before.
- Viewer: the redesign from 3d-printz ported in. Open side columns around a framed stage, crease lines
  on parts, floor grid in the assembled view (G), flat bed in `bed_color` with an exact 10 mm grid,
  whole-bed framing for big plates, Show all in both modes, phone and tablet layouts, mode and plate
  kept in the address.
- Viewer: three.js r128 bundled in `tools/viewer/vendor/` (MIT) instead of a CDN; `make_viewer.py`
  inlines it into the static page, so viewers work offline.
- `viewer_server.py`: `/api/slicer` replaces `/api/bambu`. Slicer from `VIEWER_SLICER`, else the
  profile's `slicer.open_command`, else Bambu Studio, OrcaSlicer, PrusaSlicer or Cura if installed.
  Non-macOS slicers start detached, so the request no longer waits for the slicer to quit. "Copy load
  request" is hidden unless `VIEWER_LOAD_REQUEST=1`.
- README: install is one numbered guide per system, folded by default; a 3D viewer section with a
  screenshot.

## 2026-11-12
- Windows and Ubuntu support, tested in CI (`.github/workflows/platforms.yml`: fresh macOS, Windows/Git Bash
  and Ubuntu runners install OpenSCAD, check and view `tests/sample/coaster`, run the session hook).
- `scripts/py.sh` finds a working Python 3.9+ (python3, python, py -3), skipping macOS's pre-CLT stub and
  Windows' Store aliases; the session hook runs through it and, with no Python, tells Claude how to install one.
- `doctor.py --install` needs no admin: brew on a Mac that has it, else the official files.openscad.org
  snapshot (SHA-256 checked) as a .dmg into ~/Applications, a .zip into %LOCALAPPDATA%, or an unpacked
  AppImage (no FUSE) linked as ~/.local/bin/openscad.
- `kit_profile.openscad()` finds OpenSCAD off PATH (profile `openscad`, app folders, print-kit's own install;
  `openscad.com` on Windows so output is captured); check_scad and make_viewer use it. The session context
  names this machine's Python and OpenSCAD.
- Linux: `doctor.py` finds system libraries the OpenSCAD AppImage lacks (CI's Ubuntu had no `libEGL.so.1`)
  with ldd and installs the apt packages when sudo is passwordless, else prints the exact command.
- All text files read and written as UTF-8, OpenSCAD output decoded as UTF-8 (Windows defaults to cp1252).
- Install cut to two plugin commands plus `/print-kit:setup`. New `tools/doctor.py` checks Python,
  OpenSCAD (and the macOS app off PATH), slicers and Portless, and `--install` installs OpenSCAD with
  brew, winget, apt, dnf, pacman or flatpak. Setup runs it and offers the install in its one question round.
- Pillow dropped: the trace editor reads photo sizes from the file header, and `trace_overlay.py` writes
  an SVG. Every tool is now standard-library Python; OpenSCAD is the only dependency.
- README: install steps folded into collapsible sections.
- README: short feature list instead of the parts table; step-by-step install with every command.
- README: "Made with print-kit" gallery of 36 printed parts (9 x 4 grid).
- Brand kit: nozzle-and-layers mark in Colour shift (indigo to pink), lockups, one-colour and small cuts,
  plugin icon, README banners (light/dark), social preview, palette and usage guide in `brand/`.
- 0.1.0: first version, generalized from the 3d-printz repo. Profile (`print-kit.json`) for printer, bed,
  nozzle, slicer, materials, rules and taste; `/print-kit:setup`; SessionStart rules hook; skills
  scad-design, measure-and-fit, gridfinity-bin, print-viewer; design-reviewer agent; check_scad, viewer,
  trace and layout tools reading the profile (bed size, slicer open command).

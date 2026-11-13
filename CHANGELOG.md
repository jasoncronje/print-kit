# Changelog

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

# print-kit house rules

Parametric OpenSCAD designs for things the user prints at home. One folder per project inside the
workspace (the folder holding `print-kit.json`). The profile below says which printer, slicer and
materials they use, and which rules they switched off. Profile values win over anything here.

## Skills (use them)

- `print-kit:scad-design`: how to design and write any model: clearances, taste, printability,
  mechanisms, checks, self-critique.
- `print-kit:measure-and-fit`: getting object sizes, fit-test pieces and ladders, recording results.
- `print-kit:gridfinity-bin`: the outline-first gate, trace and layout editors, base numbers, pocket finish.
- `print-kit:print-viewer`: build and show the 3D viewer.
- `print-kit:design-reviewer` agent: fresh-eyes review before handoff of a new design or a big change.
- `print-kit:setup`: create or change the profile.
- The workspace's data folder (`data/` unless the profile says otherwise): measurements and test
  results (`objects/`, `fits.csv`, `prints.csv`, `hardware.json`). Read it before picking a number;
  add to it after every measurement or print.
- `python3 <tools>/check_scad.py <project>`: checks every printable part before handoff.

## Project layout

- `<name>.scad`: the parametric model. A `part` variable picks what to render (assembly, each
  printable part, test pieces, `clash_*` checks).
- `stl/`: ready-to-slice parts, exported already in print orientation. One copy only.
- `renders/`: reference renders.
- `viewer/`: 3D viewer. `config.json` is hand-written; `index.html` and `data.json` are built.
- `trace/` / `layout/`: outline editors. `config.json` and saved points are kept; `index.html` and
  `photo.jpg` are built.
- `README.md`: parts table, design notes, print settings, regenerate commands. Update it with every
  design change.
- `CHANGELOG.md`: newest first, one dated heading per day, one line per change (what and why).
  Log print results and the user's feedback too. Read it before git log for a project's history.

## Printing

- Fits are tuned on the profile's default nozzle. Other nozzles get no fit guarantees: label those
  plates with their nozzle and keep them separate.
- Every plate's `settings` and `note` start with the nozzle and the slicer preset.
- Split long jobs across separate plates rather than one very long plate.
- Never start a print, or send one to the printer, without an explicit go-ahead.
- If `rules.open_slicer_only_when_asked` is on: never open or load anything in the slicer unless the
  user's current message says to. Show models in the 3D viewer. Slicer-setting requests mean: build
  the STL/3MF, say where it is, stop.

## Working with the user

- The user's caliper measurements beat spec sheets. Record them in the data folder and cite them in
  the `.scad` comments.
- Don't double-count clearances: add each once, in one named variable.
- Looks matter: no plain square boxes, crisp edges, match the host object's edge language.
- Support-free by default, but supports beat a distorted shape or a functional face sagging over air.
  Flat bed faces sit exactly at z = 0.
- Test pieces print flat on the plate, never standing on edge.
- For fit-critical features (snaps, bezels, plugs), offer a small, fast test piece first, and show a
  render of what to check on it.
- End each design round with a short self-critique: risks, unverified claims, guesses, confidence.
- If `rules.gridfinity_outline_gate` is on: Gridfinity bins get their outline approved first (trace
  or layout editor), and nothing else (pocket, STL, render) until the user says it's right.

## OpenSCAD

- Export: `openscad -D 'part="cover"' -o stl/cover.stl model.scad`. In a sandboxed session, OpenSCAD
  and the tools need the sandbox off.
- zsh does not word-split `$VAR`. Pass flags inline, or loop through a shell function using `"$@"`.
- After any model change: `check_scad.py`, re-export the STLs, rebuild the viewer, redo the renders
  that changed.

## Pages (viewer, trace, layout, caliper asks)

- Serve them with `<tools>/viewer_server.py <folder>`, never a plain `http.server`: it serves the
  shared viewer template live, backs Open in <slicer>, and lets editor pages save straight into the
  project. It exits about 5 minutes after its last tab closes.
- `server.launcher = "portless"`: run it as `portless <name> sh -c 'python3 <tools>/viewer_server.py
  <folder>'` and give the `https://<name>.localhost` URL. `"plain"`: run it directly and give the
  `http://127.0.0.1:<port>/` URL it prints.
- Open in <slicer> is the user's button to press, never the agent's.

## Git

- If `rules.commit_after_changes` is on and the workspace is a git repo, commit after changes with a
  clear message. Stage only the project you changed (`git add <project>/`), plus rows you added to
  the data folder; never `git add -A`. Several sessions may share one checkout.

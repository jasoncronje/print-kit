---
name: scad-design
description: Design or change a parametric OpenSCAD model for the user's 3D prints (stands, docks, enclosures, holders, mounts, cases, hooks, Gridfinity bins). Covers how to write the .scad file, picking clearances from the user's own fit-test data, walls, orientation, supports, edge style, mechanisms (snaps, keys, screws, inserts, adhesive, cables), checking the model before handoff, and the self-critique to give every round. Use whenever writing or editing a .scad file, sizing a fit, or answering a 3D-print design question.
---

# OpenSCAD design for the user's prints

What the user has learned on real prints outranks generic rules, and their calipers outrank spec
sheets. Their data lives in the workspace data folder (`data/`, see its `README.md`). Read it before
you pick a number, and add to it after. Their printer, nozzle, bed, slicer and taste are in the
print-kit profile (loaded at session start; `python3 ${CLAUDE_PLUGIN_ROOT}/tools/kit_profile.py`
prints it). No profile? Run the `setup` skill first.

## Every design, in order

0. **Know the history.** On an existing project, read its `CHANGELOG.md` first.
1. **Know the object.** Look in `data/objects/` first. Missing? Look up specs, drawings or a
   vendor model online, then ask the user to caliper only the sizes that decide the fit
   (`measure-and-fit` skill). Model with marked `// GUESS` values rather than block on them.
2. **Know the use.** Model the object as it's used: with its case, band, cable, accessories, and
   only the parts their unit actually has. Confirm which way it faces (crown up? port down?) with a
   labelled render before building on it.
3. **Nozzle is the profile's.** Fits are tuned per nozzle. Another nozzle only when the user asks;
   fits don't carry across.
4. **Pick clearances** from `data/fits.csv` ([clearances.md](references/clearances.md)).
5. **Write the model** to the house layout below, in print orientation per part.
6. **Check it**: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/check_scad.py <project>` plus the checks in
   [checks.md](references/checks.md). Look at every render from several angles for stray geometry.
7. **Review**: for a new design or a big change, run the `design-reviewer` agent.
8. **Hand off** with a short self-critique (below), then export STLs, rebuild the viewer
   (`print-viewer` skill), update the README, add a `CHANGELOG.md` entry, commit.

## House layout for a .scad file

- Header comment: what it is, which object, where the numbers came from.
- `part = "assembly"; // [assembly, body, lid, fit_test, ...]` picks what renders. Printable parts
  render in print orientation, flat face at exactly z = 0. Context parts (the object itself, cables)
  are separate `part`s, and `%` ghosts in the assembly.
- A `print_pose` flag when a part prints in a different pose than it assembles: print pose for STLs,
  assembled pose for the viewer (reusing the print shift once sank a body 3 mm into its lid).
- Parameters at the top, grouped (`/* [Object: calipered 2026-10-20] */`), every value commented
  with its source: `// calipered`, `// spec, vendor.com`, `// GUESS`, or a `data/` path.
- Clearance added once, in one named variable, per side. Never baked into an object size.
- Derived values computed, not hand-typed. `assert()` every limit you rely on (wall behind a
  scoop ≥ 3, floor ≥ base + 1, part fits the bed), `echo()` the walls and key sizes.
- Fit-test parts are `intersection(){ real_part(); box; }` so they carry the real geometry.
- Interference checks live in the file as `clash_<a>_<b>` parts that must render empty
  (`check_scad.py` runs them).
- Plain OpenSCAD, no libraries: every file stands alone. Copy a helper in if needed.
- $fn: 64 default; 96–192 for a visible round that must stay true; 16–24 for minkowski cones
  and spheres; 128 for interference checks.

Techniques and known traps: [openscad-patterns.md](references/openscad-patterns.md).
Read it before using `hull()`, `minkowski()`, offsets, sweeps or coincident faces.

## Taste, short version

The profile's `taste` list wins over this one. Default house taste:

- Refined, like a good phone or watch dock: a low plinth, a tapered wedge backrest, 8–14 mm top
  corner radii. Never a plain square block.
- Crisp, not puffy: flat faces with ~1 mm edge breaks. No hull-of-spheres balloon shapes.
- Functional faces (sensor, button, display) are flat planes, tilted if needed, never domed.
- No lips, steps or ledges where two surfaces meet.
- Centre things on what they belong to: labels, holes, lips, cable exits.
- Hide cables and mechanics. Cables leave through the middle of the back.
- Solid, not hollow: infill saves the plastic. Spend spare room on thicker walls, not bigger pockets.
- Add-ons match the host's edge language (chamfers stay chamfers). Square-cut tape gets square
  recesses.
- Cradle, don't trap: open sculpted seats the object lifts straight out of.

Full list with the reasons: [taste.md](references/taste.md).

## Printability

- Support-free by default (teardrops, 45° lead-ins, chamfered undersides, true flat bridges up to
  ~13 mm). But a functional or visible surface over air gets supports: never distort a shape, or
  leave a fitted face sagging, to avoid them.
- A shallow slope sags worse than a flat bridge. Level it or support it.
- A support enforcer that stops flush at a surface gives no support. Overlap the ceiling layer by about 1 mm.
- Load paths in XY. Flexing features bend within the layer plane.
- Walls in whole perimeters: about 0.42–0.45 mm each on a 0.4 nozzle (two = ~0.9, four = ~1.7).

More, including generic FDM fallback numbers: [printability.md](references/printability.md).

## Mechanisms

Snaps, cradles, bowtie keys, screws, heat-set inserts, adhesive pads, cables, hinges:
[mechanisms.md](references/mechanisms.md). Hardware the user owns: `data/hardware.json`.
Design for what they have; ask before specifying anything else.

## Working with the user

- Use judgement on details and just fix them. Ask only about what changes the design.
- Lead with the fix most likely to work, not the easiest one.
- Each round, say exactly what changed: which dimension, which direction, by how much.
- Their observation of a real print is data. Don't argue with it. Reason from the contact points.
- Change only what they asked for, on only the items they named. Never alter an approved or traced
  shape without asking.
- Fit-critical feature? Offer a small, fast test piece first (`measure-and-fit` skill).
- Side research (pinouts, part compatibility) can go to a subagent so the design keeps moving.

## Self-critique at handoff

Users ask "anything you don't like?" or "are you sure?" a lot. Answer it before they ask.
End every design round with:

- **Risks:** what is most likely to fail on the first print, and why.
- **Unverified:** claims not checked on the geometry (bridges, clearances, assembly path).
- **Guesses:** dimensions still marked `GUESS`, and which measurement would settle each.
- **Confidence:** high / medium / low that it prints and fits first time.

## After a print

Record it the same day:
- Each fit result goes in `data/fits.csv` (one row per variant), and in the `.scad` comment.
- A failure or surprise goes in `data/prints.csv` with the rule it taught.
- New object sizes go in `data/objects/`.

---
name: gridfinity-bin
description: Design a Gridfinity bin or container (tool pockets traced from a photo, round or rectangular pocket layouts, split long bins with bowtie keys). Covers the outline-first gate, the photo-trace and layout editors, tested Gridfinity base numbers, grid choice, walls, pocket finish (chamfers, scoops, lift pads), floor labels, and the underside check. Use for any Gridfinity bin, drawer insert or tool holder on a 42 mm grid.
---

# Gridfinity bins

Use with the `scad-design` skill (clearances, taste, checks). This page adds what's specific to bins.
Tools: `${CLAUDE_PLUGIN_ROOT}/tools/`.

## Required order (when the profile's `gridfinity_outline_gate` is on, the default)

1. **Outline first.**
   - Tool-shaped pocket: trace it from a photo ([trace-editor.md](trace-editor.md)),
     `python3 ${CLAUDE_PLUGIN_ROOT}/tools/make_trace.py <project>`, serve it, open it for the user.
   - Simple shapes (round holes, rectangular wells): the layout editor,
     `python3 ${CLAUDE_PLUGIN_ROOT}/tools/make_layout.py <project>` from `layout/config.json`
     (`title, bin, clearance_mm, kinds, start_pockets, store_doc, draft_key`). Serve `layout/` with
     `viewer_server.py` like the trace; Save writes `layout/saved.json`. As a claude.ai Artifact
     (only when asked): `capabilities: {"db": {}, "user": {}}`.
2. **Gate.** Stop until the user says the outline is right (they save it with "Save for Claude").
   No `.scad` pocket, STL or render before that. Agents skip this step when it isn't a hard rule.
   Exception: the user asks to see a model in 3D before approving.
3. **Then the model.** Read the saved points (`trace/points.json` or `layout/saved.json`) into the
   `.scad`, render, check (underside!), export STLs, build the viewer (`print-viewer` skill), open it.

Never change an approved outline (mirror, smooth, re-trace) without asking.

## Base (no library)

Copy [gridfinity-base.scad](gridfinity-base.scad) into the model.

- Pitch 42. Bin = units × 42 − 0.5. Outer radius 3.75.
- One foot per cell: hull of 35.6 r0.8 at z 0 → 37.2 r1.6 from 0.8 to 2.6 → 41.5 r3.75 at 4.75
  (0.8 chamfer + 1.8 straight + 2.15 chamfer). Matches kennetek/gridfinity-rebuilt-openscad.
- Height units of 7 mm; `extra_h` adds wall on top. No stacking lip unless asked.
- Every hull or wall starts at `base_h`, never z = 0: a hull from z = 0 once buried all 8 feet.
- Floor: `assert(floor ≥ base_h + 1)`. Plain bins use a 7 mm inside floor.
- Magnets (if wanted): 6.5 × 2.4 mm, 26 mm spacing.

## Grid and bed

- Pick the grid from the **traced** length, not a photo estimate (pliers went 4×2 → 5×2 at 168 mm).
- Rotating the pocket can save a unit: a 171 mm knife fits 4×2 at −18.5°. Sweep the angle against
  the 2D wall check.
- Longest bin that fits the bed: units × 42 − 0.5 ≤ the profile's bed X (or Y). On a 256 mm bed,
  6u = 251.5 just fits; on a 220 mm bed, 5u = 209.5. Longer bins split at a cell boundary, joined with
  bowtie keys (`${CLAUDE_PLUGIN_ROOT}/skills/scad-design/references/mechanisms.md`).

## Walls

- ≥ 3 mm behind a scoop (assert it), measured at the rim **after** the rim chamfer: the chamfer
  widens the scoop at the top (an assert that ignored it left 3 mm low down and 1.5 at the rim).
  Rim minimum ~1.6 mm on tight rotated pockets.
- Drawer bins: 1.6 side walls, 1.2 end walls (0.4 nozzle). A family of bins shares one wall style.
- Dividers ≥ 2.5. A divider rib between stacks: 1.6 × 15 mm with a round top; widen the pocket by the rib.
- After any outline change, run the 2D wall check: `difference(){ offset(r=t) pocket(); bin_outline(); }`
  must render empty.

## Pocket finish

- **Clearance once**, as an offset of the traced outline: start at 1.0–1.2 per side for traced
  tools, 0.75 for calipered rectangles, 0.5 for round holes
  (`${CLAUDE_PLUGIN_ROOT}/skills/scad-design/references/clearances.md`; the user's `data/fits.csv`
  wins). Calipers win over the trace where they disagree.
- **Rim chamfer** scaled to the wall: 1.5 on thick walls, 1.0 on medium, 0.6–0.8 on 1.6–2.6 mm
  walls, leaving 0.4–1 mm flat on top. Cone minkowski on the top outline.
- **Floor-to-wall chamfer** 0.5–1.0, always smaller than the clearance so the object sits flat.
- **Inside vertical corners** ~0.5 radius (closing with `offset(r=-R) offset(r=R)`).
- **Floor follows the object**: deeper under fat ends, a lift pad under thin or angled sections
  (5 mm under a knife's lower third; a raised shaft floor so the shaft doesn't hang).
- **Depth** from the measured height, not a retailer's figure. Stack pockets are as deep as the stack.

## Grab room and scoops

- Tools must stand proud of the rim or get a scoop. Upright items (vials, bags) sit in shallow
  holders with a third to half sticking out: **no scoops** for those.
- Scoops are round half-ellipsoid bowls, never square slots. Put them where the wall has the most
  spare room (usually a narrow part of the object), with ≥ 3 mm of wall behind.
- Round the joint where a scoop meets the pocket wall (2D closing per slice;
  `${CLAUDE_PLUGIN_ROOT}/skills/scad-design/references/openscad-patterns.md`).
- Two scoops can hull into one trough across the middle. A scoop stops at the top of any lift pad it
  crosses. A U-scoop through both walls gets 1 mm chamfers on every edge.
- Reach-through grab points where the object allows (joined scissor finger holes).

## Labels

Engraved 0.6 deep in the **pocket floor**, centred at the outline's area centroid, visible when the
tool is out. Short words, two lines across the middle if long. ≥ 1.2 mm floor under the text, ≥ 2 mm
inside the flat floor. A 45° label lip on a back wall (8 deep, 1 mm flat top, flush with the rim)
works where the floor is covered.

## Before handoff

- `python3 ${CLAUDE_PLUGIN_ROOT}/tools/check_scad.py <project>`: it counts one first-layer foot per cell.
- Render the underside and look at the feet.
- A fit-test frame (a 2–6 mm tall ring of the real pocket, `intersection` with the bin) prints in
  10–15 min. Offer it before the full bin.
- Print settings: the profile's nozzle and its `gridfinity` preset if it has one. Baseplates that
  lift at the front edge: exhaust fan off and an auto brim (a full brim stops baseplates butting flush).

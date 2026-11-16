# Calibrating to the user's printer

One small print that replaces the starting clearances with the user's own. It is optional and
always the user's choice. `setup` offers it; offer it again when a fit matters and the session
says calibration is not done.

The piece is ready-made: `${CLAUDE_PLUGIN_ROOT}/templates/calibration/` (a plate with six round
holes and six square sockets, and one key). Don't redesign it. Gaps per side, 1 dot to 6 dots:
0.05, 0.10, 0.15, 0.20, 0.30, 0.40 mm. The key is 8 mm; the plate is 80 × 32 × 4 mm.

## Hand it over

1. Copy the folder into the workspace as `calibration/` (`cp -Rn`, never overwrite).
2. Set every `"material"` in `calibration/viewer/config.json` to the profile's default material.
3. `check_scad.py calibration`, export `stl/gauge.stl` and `stl/key.stl`, `make_viewer.py calibration`.
4. Show it with the `print-viewer` skill, and say:
   - Print both parts with the nozzle, filament and settings they normally use. Changing
     settings for this print defeats it.
   - The key prints standing, square end on the bed.
   - "Tell me when it's printed."
5. Stop. Don't start a print (profile rule `ask_before_print`).

## When it's printed

Ask in plain chat, one question per message. No calipers are needed for the first four.

1. "Take the key's **round** end. Starting at 1 dot, which is the first round hole it pushes
   into by hand?"
2. "Which is the first round hole where it drops in on its own and falls out when you tip the
   plate?"
3. The same first question for the **square** end and the square sockets (the end that was on
   the bed goes in first).
4. The same second question for the square end.
5. "Do you have calipers?" Only if yes, ask one at a time: plate length (80), plate width (32),
   plate thickness (4), the key's round diameter (8), the key's square width (8).

Odd answers:

- **Nothing goes in, even at 6 dots**: the printer over-extrudes or the first layers are
  squashed. Record every step as `forced`, suggest the slicer's flow calibration, and offer a
  reprint. Don't invent a clearance.
- **Drops through at 1 dot**: record 0.05 as `loose`. Their snug value is below 0.05; use 0.05
  and say the true limit is untested.
- **Pushes in at one end of a hole but not the other, or only from one side**: ask which face
  was on the bed. A fit that only fails bed-side is first-layer squish; note it in `prints.csv`.

## Record it

- `data/fits.csv`: one row per position they tried or passed, project `calibration`, nominal 8,
  basis `per_side`, the profile's nozzle and material. Round holes are kind `round-hole`,
  square sockets `key-socket`. Results: `forced` below the first that pushes in, `snug` for the
  first that pushes in (`chosen` = yes), `good` between, `loose` from the first that drops free.
- Caliper sizes: `data/objects/calibration-gauge.json`, each with its nominal in the note.
- Profile `notes`, one line, so every session has it:
  `Calibrated <date> (<nozzle>, <material>): round snug <a>, round free <b>, shaped snug <c>, shaped free <d> mm per side.`
  Add the caliper error when measured: `Outer sizes print <+0.08> mm, holes <-0.12> mm.`

Then tell the user their four numbers in one short list and what they mean: snug holds a part
in place, free lets it drop in and lift out.

## Using it in a design

`references/clearances.md` in the `scad-design` skill ("After calibration") says how these
numbers move the starting table. A direct row in `data/fits.csv` for the same kind of fit
always beats the calibration. Calibrate again after a nozzle or material change: fits don't
carry across.

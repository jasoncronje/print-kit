# data

Everything you've measured or learned from a real print. Plain files, so git keeps the history.
Your own numbers beat spec sheets and generic tables. Add to these files as you go; don't wait to be asked.

| File | One entry per |
|---|---|
| `objects/<slug>.json` | Real object you design around (tool, board, phone, cable) |
| `fits.csv` | Clearance tried on a real print, and how it felt |
| `prints.csv` | Print outcome worth remembering (failure, surprise, setting that worked) |
| `hardware.json` | Screws, inserts and tape you own |

## objects/<slug>.json

```json
{
  "name": "Bosch GLM 42 laser measure",
  "used_in": ["bosch-glm42-gridfinity"],
  "dims": {
    "tool_length": {"mm": 106.0, "source": "caliper", "date": "2026-10-20", "note": "Bosch spec says 105"}
  },
  "notes": ["Spec sheet was 4 mm short on height."]
}
```

- `trace`: path to the saved outline when the object was photo-traced (`pliers-gridfinity/trace/points.json`).
- `dims` keys are snake_case and match the `.scad` variable when there is one.
- `source`: `caliper`, `spec` (add `ref`), `trace`, `derived` (say how), or `guess` (an open ask).
- Vectors are fine: `{"mm": [17.78, 21.08, 1.2], "axes": "across, along, PCB"}`.
- A `.scad` value that comes from here cites it: `puck_d = 27.75; // data/objects/apple-watch-puck.json`.

## fits.csv

`date, project, feature, kind, nominal_mm, clearance_mm, basis, nozzle, material, result, chosen, note, source`

- `kind`: round-hole, round-pocket, rect-pocket, traced-pocket, shaped-pocket, key-socket, snap, proud,
  slip-fit, counterbore, countersink, screw-pilot, insert-hole, depth, corner-radius, keep-out.
- `basis`: `per_side` (gap on one side), `diametral` (total across a bore), `proud` (how far it stands out),
  `interference` (negative clearance), `hole_d`, `radius`, `depth`.
- `result`: `snug` (tightest that goes in by hand), `good`, `loose`, `tight`, `forced`,
  `worse`, `untested` (a value in a model that was never fit-tested; a guess, not a fact).
- `chosen`: `yes` for the value the model uses now.
- One row per variant on a ladder, so the losers are on record too.
- Quote any field that contains a comma.

## prints.csv

`date, project, part, nozzle, material, plate, outcome, lesson, source`

`outcome`: `ok`, `partial`, `failed`, `note`. The `lesson` is the rule that came out of it.

## Reading it from OpenSCAD

Recent OpenSCAD development snapshots can import JSON with `--enable=import-function`:

```openscad
glm = import("../data/objects/bosch-glm42.json");
echo(glm.dims.tool_length.mm);   // 106
```

The viewer and check tools do not pass that flag, so models that use it need copied values instead.

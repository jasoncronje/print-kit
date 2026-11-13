# Printability

The user's printer, bed, nozzle, plate and materials are in the print-kit profile. The numbers below
were learned on the author's Bambu Lab P2S (0.4 nozzle, PLA); treat them as good starting points on
any well-tuned FDM printer, and log anything that differs in `data/prints.csv`.

## Orientation

- Decide the print orientation before you design features. Model each printable part in it.
- The flat bed face sits at exactly z = 0.
- Loads in XY, along the layers. Flexing features (snap arms, clips) bend within the layer plane;
  bending across layers splits them.
- Flip test pieces so the face being tested is on the bed (xiao_test ceiling down; watch_test on
  its back).
- Test pieces print flat on the plate, never standing on edge.

## Supports

- Support-free by default, using: teardrop bores, 45° lead-ins (a cover prints face-down with a
  45° lead-in before its front radius), chamfered undersides, 45° lip undersides, upright louver
  slats, ducts no more than 30° off vertical.
- **But supports beat a distorted shape.** Real cases where supports won:
  a round puck pocket instead of a pointed roof, sagging pocket ceilings that ruined strip depth,
  a sensor shaft over air. Rule: a functional or visible surface over air gets supports
  (paint them, or a `support_enforcer` part, tree/manual).
- Command-strip pockets came out clean with supports at 0.2 mm top interface spacing.

## Bridges and overhangs

- A true flat bridge up to ~13–14 mm printed fine (saw jig 13 mm; sensor roof 13.6 mm). Bambu's
  "floating cantilever" warning on the saw jig was harmless.
- A **shallow slope sags worse than a flat bridge**: a 13 mm roof leaned 15° off flat drooped.
  Level it into a bridge or support it.
- Viewer flags faces past 45°. Test pieces get their own overhang check: one had a 20 × 26 mm
  ceiling over air.
- Check bridge and overhang claims on the actual geometry before stating them.

## Walls, shells, nozzles

- Wall = whole perimeters: ~0.42–0.45 mm each on the 0.4.
- Moving a part from a 0.6 to a 0.4 nozzle: 4 walls / 5 top / 4 bottom on the 0.6 match about
  5 / 6 / 5 on the 0.4.
- Small parts need a minimum-wall check: a plug keeper and 0.8 mm insert posts came out too thin.
  Prefer solid blocks for small parts.
- Fit frames and keys print at 100% infill. Jigs print fast in PLA with low infill.
- Gridfinity bins use the profile's `gridfinity` preset when it has one; everything else the default.
- Percentage settings (ironing, etc.) don't carry over between nozzles: re-set them, don't drop the
  feature.

## Plate and adhesion

- Gridfinity baseplates lifted at the front edge: exhaust fan 0%, Auto brim. No full brim; it
  stops baseplates butting flush.
- Bambu: leave clumping detection off (it adds a prime tower that collides with parts).

## Materials

- PLA softens around 55 °C. Suggest PETG for hot-car kits .
- ASA for the load-bearing filament-rack hook and flange (40% gyroid, 5 mm outer brim).
- IR sensor housings in **black**: light PLA bounces IR around the window, and the board's red LED
  glows through a 1.2 mm skin.
- PLA is brittle for snaps and living hinges ([mechanisms.md](mechanisms.md)).

## Generic FDM fallback

Use only when the user has no number of their own, and log the result in `data/` afterwards.

| Rule | Value | Source |
|---|---|---|
| Min wall | ≥ 0.9 mm (2 perimeters); 1.2–1.6 for strength | Hydra Research design rules (CC BY-SA 4.0); text-to-cad dfam-check (MIT) |
| Overhang without support | ≤ 45° from vertical; up to ~60° with good cooling | Prusa KB "Modeling with 3D printing in mind" |
| Bridge | ≤ 10 mm safe (13.6 has printed fine) | Hydra Research |
| Elephant foot | 0.3–0.5 mm 45° chamfer on bottom edges where a fit matters | wilsonwaters/3d-printing (MIT) |
| Internal corners | ≥ 1 mm fillet where it takes load | wilsonwaters/3d-printing |
| Downward-facing rounds | Chamfer instead of fillet | Hydra Research |
| Ribs | A 1.6 mm rib beats a 5 mm solid wall per gram | wilsonwaters/3d-printing |
| Printed metric threads | Avoid: inserts, captive nuts or self-tap holes | wilsonwaters/3d-printing |

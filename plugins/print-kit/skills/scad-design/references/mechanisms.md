# Mechanisms

Tested values first (the author's PLA prints on a 0.4 nozzle); generic formulas where there are none.
The user's fit numbers live in `data/fits.csv`, their hardware in `data/hardware.json`.

## Snaps and detents

- Tested detent: ridge r 0.55 over a 0.3 wall gap = **0.25 mm interference**, tuned on PLA (power
  strip cover). 0.4 suggested for PETG, untested.
- A snap test piece must include the thing it snaps against. A lone slice tests nothing.
- Cantilever strain: **ε = 3·y·t / (2·L²)** (y = deflection, t = arm thickness at the root,
  L = arm length). Keep PLA under **1.5%**, so `L ≥ sqrt(3·y·t / (2·0.015))`.
  Example: t 1.2, y 0.5 → L ≥ 7.8 mm. Arms flex in the layer plane only. (Formula: Fictiv snap-fit
  guide; PLA limit: wilsonwaters/3d-printing, MIT.)
- PLA can't do living hinges (breaks in 50–100 cycles). PETG can at ~0.4 mm.

## Cradles that clip a round object

- Wrap over 180° to retain at all; ~220° gives a real snap.
- Opening width = `2·R·sin(wrap/2)` with `R = r + clearance`. At 220°: 1.88 R.
  (From evnchn-agentic/agentic-3d-modeling, MIT.)
- Prefer open cradles the object lifts out of; use a clip only when it must hold on.

## Bowtie keys (joining split bins)

- Drop-in key 20 × 12 × 3 with a 7 mm neck, in 3 mm floor sockets. No overhangs, and the
  baseplate keeps the halves level.
- Split long bins at a cell boundary. Check units × 42 − 0.5 against the profile's bed (6 units = 251.5 mm just fits a 256 bed).
- Lead-in on the key: union a shorter full-size layer with an `offset(delta=-0.3)` top layer. Not
  `hull()`: it fills the neck.
- Same nozzle: 0.15 per side. Key on the 0.4 into a socket on the 0.6: grow the key +0.15 per side
  (net 0). Print keys at 100% infill.

## Screws

- M2 self-tapping into PLA: pilot 1.7 mm, depth = thread + 1.5 (6.5 for 5 mm of thread). Fine
  for lids that rarely come off.
- Countersink: calipered head + 0.4, 90° (3.8 for the 3.4 mm M2 head). Heads sit flush.
- M2 × 4 socket head counterbore: head Ø + 0.5, head height + 0.23 (untested).
- Scale to the part: M2 on small stands. Use what's in `data/hardware.json`.

## Heat-set inserts

- M3 × 5 inserts (4.5 OD, calipered): a 4.0 hole has worked; CNC Kitchen's pull tests
  found ~4.2 best for M3 (printed holes come out ~0.25 small). Depth = insert + 1.5 for the
  displaced plastic.
- The boss needs real wall: 0.8 mm around the insert was too thin. Aim for 1.6+ (four perimeters
  on the 0.4; untested guess). No room for that? Use plain screws.
- Inserts only where the part is opened often.

## Adhesive

- Compressible pads must stand **proud after compression**. A locked Command-strip pair (4.0 mm)
  needs 0.9 mm proud (pocket 3.1 deep); 0.3 ended flush and didn't stick.
- VHB recess depth = tape thickness − 0.3…0.5, 0.3 mm wider per side, **square corners**, ~5 mm in
  from the edges so it doesn't show. (Caliper the tape; record it in `data/hardware.json`.)
- Wall-mounted parts sit flush with negative cutouts, never feet.

## Cables and connectors

- Assume cables are stiff (ask about the user's). Leave straight-out room behind every connector and no
  tight U-turns: the 2.75 mm braided watch cable couldn't U-turn under the puck rim, so ducts bend
  at most 30°.
- Leave cable gaps around boards mounted upside down.
- Seat a rigid plug on its thick reference faces (two pads); let the tapered tail and boot hang
  free. Anything under the boot levers the head over.
- A connector that mates through a phone case stands 0.6 proud: the case's rubber gives, PLA
  doesn't.
- **Walk the insertion path** of every rigid part before printing: sweep its calipered box along
  the path and intersect with the body ([checks.md](checks.md)). A 26 mm rigid plug head couldn't
  pass a 15 mm opening. If it can't go in from the top, load it from below with a keeper.
- Every enclosure has an assembly order, and the handoff says what it is.

## Keep-outs

Model what lives around the object as keep-out volumes: watch band metal arms (they fouled the
cradle horns), case lips, cable boots. Check the body against each keep-out grown by the margin.

## Magnets (Gridfinity)

6.5 mm across × 2.4 mm deep, 26 mm spacing (gridfinity-rebuilt spec). 

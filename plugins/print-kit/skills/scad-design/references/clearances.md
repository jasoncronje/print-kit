# Picking a clearance

The source of truth is `data/fits.csv`. Filter it for the same `kind` and nozzle and use the `chosen`
row. This page is the summary and the rules for when there's no row yet.

## Conventions

- **Per side** unless a variable says otherwise. Name diametral values `*_dia` or say so in the comment.
- Add clearance **once**, as one offset or one `+ 2*clr`. Never inside the object size, the trace
  or a second variable. (A box once came out too tall because plug reach was counted twice.)
- The traced outline sits on the object's outer edge. Photos run slightly **oversize** (camera
  above the object), so keep traced clearances modest.
- Caliper size beats a traced size beats a spec size. When they disagree, use the caliper value.

## Starting values (PLA, 0.4 nozzle, before calibration)

Use these only until the user's own `data/fits.csv` has a row for the same kind, nozzle and
material. They were measured on one printer (a Bambu P2S); others differ. Offer the calibration
print (`measure-and-fit` skill, `calibration.md`) or a ladder for anything critical. To the
user, call them "typical starting values", not someone else's.

## After calibration

Rows with project `calibration` in `data/fits.csv` (and the "Calibrated ..." line in the
profile notes) give this printer's own gaps for an 8 mm key: round snug, round free, shaped
snug, shaped free. Use them like this:

- **Same kind of fit**: use the calibrated number directly. Round peg or object that must hold:
  round snug. Round object that drops in and lifts out: round free. Key, plug or other shaped
  part that must hold: shaped snug. Shaped part that drops in: shaped free.
- **Other rows of the table below**: shift them. Round rows move by (round snug − 0.05), every
  other row by (shaped snug − 0.15). Never go below 0.05. This is an estimate from one small
  key, so still offer a fit test for anything critical or much larger than 8 mm.
- A direct row for the same kind of fit always beats both.
- Calibration is per nozzle and material. No calibration rows for the nozzle in use: treat the
  printer as uncalibrated for that part and say so.

| Fit | Start at | Evidence |
|---|---|---|
| Round object, snug, must hold (puck) | 0.05 per side | Tested: 0.05 snug, 0.15 loose |
| Rigid shaped part, snug (plug head) | 0.15 per side | Tested: 0.15 snug, 0.25 / 0.35 loose |
| Cylinder dropped into a round hole (vial, bottle) | 0.5 per side | Tested: 0.5 best, 0.75 / 1.0 loose |
| Rectangular tool pocket, calipered | 0.75 per side | Tested on a laser measure |
| Traced outline pocket (tool lies in it) | 1.0–1.2 per side | 0.6 printed tight; 1.2 "decent" |
| Stacked tools in one traced pocket | 2.0 per side | Untested; stacks don't line up |
| Bowtie key in socket, same nozzle | 0.15 per side | Printed, result not logged |
| Key printed on 0.4 into a socket printed on 0.6 | 0 net (grow key +0.15) | Ladder: snuggest that pressed in |
| Board in corner sockets | 0.15 per side | Untested |
| Snap detent | 0.25 interference | Tuned on PLA (power strip cover) |
| Compressible pad (Command strip pair) | 0.9 proud | 0.3 proud went flush and didn't stick |
| Connector through a phone case | 0.6 proud | 0.3 was worse: PLA doesn't give like rubber |

Never fit-tested yet (starting guesses only): scissors 1.0, LCD glass 0.25, M2 counterbore
head + 0.5 / + 0.23, M2 pilot 1.7, countersink head + 0.4, M3 insert hole 4.0
(CNC Kitchen's pull tests favour 4.2 for M3), filament-rack slip fits 0.3–0.6 diametral (ASA).

## Rules that came from prints

- Default to **snug** unless the user says otherwise: on a ladder, choose the tightest one that still goes in by hand.
- "Nice and tight" / "snug" = choose it. "A little loose" = reject it. Keys "press in by hand and
  hold". Pockets "drop in without forcing" and "lift straight out".
- Extra room only where it makes sense: loose packaging (syringes, needle packs) gets more. Rigid
  items get tight pockets and thicker walls.
- Ladders must **bracket** the answer: include one step tighter than you expect to win. The key
  ladder's winner was its tightest step, so the true limit is still unknown.
- Fits **don't carry across nozzles**. A 0.15 gap that's right on the 0.4 was loose with a
  0.6-printed socket. A prototype on another nozzle gets no fit guarantees.
- When a fit is tight at one end and loose at the other, suspect **swapped measurements** before
  you nudge clearances. (An IR thermometer stand lost two prints: the model named its legs backwards,
  so each width sat on the wrong end.)
- Pocket depth needs the object's **height measured**, not a retailer's figure (a utility-knife pocket
  came out 4 mm shallow).
- Corners of a pocket that locates a rigid part: small radius (0.75). An r 2 corner held the plug
  head 1.25 mm off its wall.
- Seat a curved or tapered part on two pads at known-thick points; let the tail and cable boot
  hang free. A full floor that follows the profile tips it over.
- Objects with an angled underside rock on a flat floor: add a lift pad under the thin end.

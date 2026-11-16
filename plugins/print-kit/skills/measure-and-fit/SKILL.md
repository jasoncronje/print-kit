---
name: measure-and-fit
description: Get the real sizes of an object to print for (spec lookup, then caliper requests on a local page with one drawing per measurement), design small fit-test pieces and clearance ladders, and record measurements and fit results in the workspace data folder (objects/, fits.csv, prints.csv). Use when a design needs dimensions of a real object, when a fit is critical (snaps, pockets, plugs, keys, bezels), when the user reports how a test print fit, when the user wants to calibrate print-kit to their printer or says the calibration piece is printed, or when a print came out wrong.
---

# Measuring and fit testing

The user's numbers live in the workspace data folder (`data/` unless the profile says otherwise;
format in its `README.md`). Calipers beat a trace, which beats a spec sheet. Spec sheets are often
wrong: in the author's projects a laser measure was 4 mm taller than listed, a PCB 1.2 not 1.6 thick,
a standoff 11.75 not 11.5.

## Getting sizes

1. **Check `data/objects/`** for the object.
2. **Look online first.** Find specs, drawings, a vendor STEP/STL or a teardown. Note the source
   (`"source": "spec", "ref": "<url>"`).
3. **Don't block.** Model with `// GUESS` values and keep a list of what's still needed.
4. **Ask for calipers only on the sizes that decide the fit**: pocket width and height, plug heads,
   board thickness, anything a spec might get wrong. Always measure the object's height before setting
   pocket depth.
5. **Make the ask a page**, not a wall of text: `<project>/measurements/index.html`, served with
   `python3 ${CLAUDE_PLUGIN_ROOT}/tools/viewer_server.py <project>/measurements`. For saves, load
   `<script src="/api/local-db.js"></script>` and use
   `db = window.claude ? await window.claude.use("db") : window.localDb ? await window.localDb() : null;`
   so a doc named `measure/watch` lands in `measurements/saved/measure-watch.json`. Read that file
   back; no download step. The same page still works as a claude.ai Artifact if the user asks for one.
   - one picture per measurement, with the dimension drawn on it where it applies;
   - plain words, no jargon;
   - tie each number to a named feature ("width at the **grip** end", "front = the side with the
     screen"), so ends can't get swapped;
   - measure practically: total height from the bare PCB back to the component top, not from a tiny part.
   - Saves must be reliable: save each field with `update()`, not a whole-form `set()` (that can wipe
     values), confirm the save on screen, and test it before handing it over.
6. **Record the answers** in `data/objects/<slug>.json` with `source` and `date`, then cite the file in
   the `.scad` comment.

Outline-shaped objects (tools in Gridfinity bins): the photo-trace editor, in the `gridfinity-bin` skill.
Side profiles and inner contours (between handles) can be traced the same way.

## Calibrating the printer

The ready-made calibration gauge gives the user's own snug and free gaps for round and shaped
fits, with no calipers. Offering it, the questions to ask after the print and how to record the
answers: `calibration.md` in this folder.

## Fit-test pieces

Offer one before the full part whenever a fit is critical (profile rule `fit_test_first`). The user
may skip it: that's their call.

- **It tests something calipers can't**: a clearance, a snap, a proud height, a seat. If calipers would
  answer it, don't print it.
- **Cut from the real part**: `intersection(){ real_part(); box; }`, so it carries the real geometry,
  including every feature it's meant to check (a sensor jig without the sensor holes tests nothing).
- **Small and fast**: trim to the minimum height; 10–30 min is the target. Fill bays and ceilings solid
  and re-cut only what's tested, so it prints without overhangs.
- **Flat on the plate**, with the face being tested on the bed. Never standing on edge.
- **A ladder brackets the answer**: 3–4 steps, including one tighter than you expect to win. Engrave
  dots or numbers to tell steps apart and mark the current value.
- **Same nozzle and material as the real part.** Fits don't carry across nozzles.
- **Show a render of what to check** on it, and say which pieces are throwaway and which are reusable.
- After a full print fails, isolate the hardest fit in a jig and iterate the jig, not the whole part
  (six 30-minute jig versions beat reprinting a whole dock).
- Offer jigs that check compatibility with parts the user already owns before committing to a design.

## When the user reports a fit

1. **Take their words as data.** "Nice and tight" / "snug" = choose it. "A little loose" = reject.
   "Had to force it" = too tight.
2. **Check the direction** before changing anything: which feature, which end, tighter or looser.
3. **Tight at one end, loose at the other?** Suspect a number on the wrong end first, from swapped
   values or swapped names.
4. **Add one row per variant** to `data/fits.csv` (losers too), with `chosen = yes` on the winner.
   Basis per side unless it's a bore (`diametral`) or a height (`proud`). Nozzle and material on every row.
5. **Update the model**: the value, and a comment with the date and result
   (`round_clearance = 0.5; // fit test 2026-10-22: best of 0.5/0.75/1.0`).
6. **Say exactly what changed**: which dimension, which direction, by how much.

## When a print comes out wrong

Add a row to `data/prints.csv`: what failed, and the rule it taught. If the rule is general, also add
it to the profile's `notes` so every session sees it.

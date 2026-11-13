# Checking a model before handoff

Never hand off, or claim anything about, geometry you haven't built and checked. In a sandboxed
session, run OpenSCAD and the tools with the sandbox off.

## 1. The automatic check

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/tools/check_scad.py <project>
```

Exports every printable part and checks it: clean stderr (no warnings, no "may need repair"),
manifold (every edge on exactly two faces), flat face at z = 0, fits the profile's bed, first-layer
islands, one Gridfinity foot per cell, overhang area, and that every `clash_*` part renders empty.
`--part a,b` for some parts; `--fn 128` for finer facets. Fix every FAIL before handoff.

## 2. Clash parts

Put interference checks in the model so they run every time:

```openscad
part = "assembly"; // [assembly, body, lid, clash_body_lid, clash_body_plug_path]
...
if (part == "clash_body_lid") intersection(){ body(); lid(); }
if (part == "clash_body_plug_path") intersection(){ body(); plug_path(); }
```

- Empty = clear. Use `$fn=128` so facets don't cause false hits.
- A zero-volume or ~0.01 mm³ sliver means the parts **touch**: fine for faces meant to meet
  (lid on body), a fail anywhere else. Pose parts that rest on each other 0.01 apart.
- **Margin check**: intersect the body with the context part grown by the margin
  (`minkowski(){ watch(); sphere(0.4); }` must be empty).
- **Keep-out check**: intersect with keep-out boxes (band arms, cable boots, case lips).
- **Insertion path**: sweep the calipered rigid part along its loading path
  (`hull(){ part(); translate(path_end) part(); }` for convex parts) and intersect with the body.
  This found a 1 mm sliver at a duct mouth before printing.

## 3. 2D wall check (pockets in bins)

`difference(){ offset(r=t) pocket_outline(); bin_outline(); }` renders empty (or "not a 2D
object") when every wall is at least `t`. Run it after any outline change.

## 4. Look at the renders

Stray geometry is easy to miss (a cable through the base, fill out of a sensor hole,
fill through rounded corners). Before showing anything:

- Render the assembly and each printable part from at least front, back, top and **underside**.
  Gridfinity bins: always the underside, and count the feet.
- Section views (`part = "section"`) through every pocket, duct and fit.
- Look for: geometry poking through, missing feet, thin skins, gaps where parts should meet,
  context ghosts in the wrong place, features cutting into each other.
- Orientation-sensitive objects: a labelled render (arrow + "crown up") before building on it.

## 5. Derived values

`openscad -o - --export-format echo -D 'part="bin"' model.scad` prints the `echo()` and
`assert()` output without a full render. Every limit you rely on should be an `assert()`.

## 6. Then

- Re-export the STLs into `stl/` (one copy only; delete stale `.3mf` built from older STLs).
- Rebuild the viewer (`print-viewer` skill) and the renders that changed.
- Update the README (parts table, fits, print settings).
- New design or big change: run the `design-reviewer` agent before handing off.

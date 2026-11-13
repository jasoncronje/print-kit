# OpenSCAD patterns and traps

Everything here happened on real models while print-kit was built.

## Known traps

| Trap | What happened | Do this instead |
|---|---|---|
| `hull()` from z = 0 | Buried all 8 Gridfinity feet in a solid block | Start every hull part at `base_h`. Check the underside render |
| `hull()` fills hollows | Merged a plug seat's two pads into one floor; filled a bowtie key's neck | Sweep non-convex shapes with `minkowski()` and a thin segment; build lead-ins as a union of layers |
| Coincident faces | Non-manifold STL that Bambu flagged: a fill sat exactly in its cavity, a cut started on the face | Grow fills 0.1 mm (`minkowski` with `cube(0.1)`), start cuts 0.02 mm behind the face |
| Cut started too deep | A relief cut 1 mm behind the face broke the visible puck circle | Start face cuts at the face (+0.02) |
| Fill pokes out | Test-piece fill poked past the relief floor; pill-bin fills came through the rounded corners | Trim fills to the surface they sit under; clip internal fills to mid-wall with `rrect(outer_r − wall/2)` |
| Subtracting a rounded sweep | Left rims too thin to print; the keeper became a hollow shell | Build the solid as an unbounded seat profile intersected with the sweep |
| Spheres off the bed | `sphere()` has no pole vertex, so hulled-sphere bottoms sit ~0.03 mm up | `scale(1/cos(180/$fn)) sphere(r)`, or better, flat bottoms |
| Print pose reused in the viewer | Body sank 3 mm into the lid, z-fighting | A `print_pose` flag: print pose for STLs, assembled pose for viewers |
| Ghosts in the wrong place | A context cable ran through the bed and lid | Route context ghosts along the real path so checks mean something |
| Ported pattern reversed | A copied screw pattern was mirrored and pushed a cable hole 5 mm off-centre | Check mirroring when porting from a reference model |
| New feature cuts an old one | A finger scoop cut into the lift wedge | Re-check each new feature against all existing ones |
| Slow minkowski sweep | Hatch export crawled | Intersect with a profile instead; export went under a second |

## Patterns that work

**Clearance with rounded inside corners, one step:** `offset(r=-cr) offset(r=clr+cr) outline`,
with `cr ≤ clr`.

**Soften a traced outline:** `offset(r=2) offset(delta=-2) offset(r=clr) polygon(pts)`.

**Rim chamfer on a concave outline:** `minkowski(){ linear_extrude(0.01) top_outline();
cylinder(r1=0, r2=c, h=c, $fn=16); }` placed at `bin_h − c`.
Get the top outline (pocket + scoops) with `projection(cut=true)` just under the top face.

**Floor-to-wall chamfer:** minkowski of `offset(delta=-ch) outline` with an upward cone, then
straight walls from `floor + ch`. Keep `ch < clearance` so the object still sits flat.

**Half-ellipsoid scoop with a rounded joint:** 0.25–0.3 mm slices; each slice is a 2D closing
(`offset(r=-R) offset(r=R)`) of pocket ∪ ellipse scaled by `k = sqrt(1 − t²)`. Use the slice's
**top** for k so slices never undercut; run the last slice 2 mm past the top.

**Rounded top edge without spheres:** hull of ~6 thin `rrect` slices along a quarter circle.

**1 mm edge break on a convex prism** (`broken_slab`): hull of bottom `offset(delta=-e)`, middle,
top `offset(delta=-e)`. Non-convex: minkowski of the shrunk shape with `sphere(e)`.

**Lift-out sweep of a 2D profile:** `minkowski(){ offset(delta=clr) profile; square([0.01, 200]); }`.

**Sweep a convex part down its loading path:** `hull(){ children(); translate([0,0,-d]) children(); }`.
Convex shapes only.

**Feature frames:** modules like `rest_frame()` / `puck_frame()` that place children on a tilted
face. One source of truth for every feature on that face.

**Body/lid split:** the lid owns everything below `lid_t`; cut the body below the seam so they
meet face to face.

**Teardrop bores:** flat-topped `teardrop2d` for horizontal holes.
Not for a visible round that must stay true: support that instead.

**Labels:** place at the polygon **area centroid**, not the bbox centre.
Read an outline's real half-width over a range with a helper like `half_w_at()` so scoops and
wall asserts follow the pocket edge.

**Straighten a crooked trace:** search rotation + centre-line offset for the smallest
outline ∪ mirror area (−1.3°, 1.05 mm cut the extra area from 417 to 49 mm²).

**Rotate a pocket to fit a smaller grid:** rotate the points, centre the rotated bbox, wrap the
pocket's geometry in `placed()`. Sweep the angle against a 2D wall check (−18.5° gave a 1.7 mm
minimum rim).

**Louvers you can't see through:** `depth·tan(angle) ≥ pitch` (52°, 5 mm frame, 6.35 pitch).
Split long slots into segments with ties so fins don't stand tall and wobble.

**Fit ladders:** a parametric trim (`key_trim`, negative grows the part) plus engraved dots
(1.6 mm, 0.6 deep) to tell variants apart; mark the current value with a dot. Export loop:
`-D "key_trim=-$(( (n - 1) * 5 ))/100" -D "key_dots=$n"`.

## Export and render

- `openscad -D 'part="bin"' --export-format binstl -o stl/bin.stl model.scad`. Sandbox off.
- Several renders at once: start them with `&`, then `wait` (mind the CPU).
- `--hardwarnings` turns warnings into failures. A non-manifold result can still exit 0, so
  read stderr (`check_scad.py` does).
- `--summary all --summary-file -` prints the bounding box and `"simple": true` as JSON.
- `-o - --export-format echo` returns just the `echo()`/`assert()` output: a fast way to read
  derived values.
- zsh doesn't word-split `$VAR`: pass flags inline or loop through a function with `"$@"`.
- Bambu 3MF from a script: meshes are centred on their bbox and the build item places them.
  Support enforcers are `subtype="support_enforcer"` parts. Per-object settings need the extra
  metadata in the `print-viewer` skill (Slicer settings in a 3MF).
- When an STL changes, regenerate or delete any `.3mf` built from it. A stale one got printed.

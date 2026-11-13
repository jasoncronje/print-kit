# Photo-trace editor (outline pockets)

For pockets shaped like a tool (knife, pliers, scissors): trace its outline from a photo, let the
user tune the dots in the editor page, then read the dots back. Also works for side profiles and
inner contours (between handles).

## Photo

Object flat on a gridded cutting mat (or next to a ruler), phone held flat and level well above it,
zoomed in (about 4x from about 1 m) so the shot is near-orthographic. Calibrate px/in (or px/mm × 25.4)
from the grid lines both ways. The photo still runs slightly oversize (camera above), so keep
clearances modest.

## First trace

- Place dots in photo pixels on the object's **outer edge**. Clearance is added once in the `.scad`
  as an offset, never in the trace.
- Aim for ~40–55 dots: simplify a dense trace with RDP at ~3 px (0.5 mm, well under the
  clearance). 159 dots were tedious to tune.
- Overlay the dots on the photo and look before going further:
  `python3 ${CLAUDE_PLUGIN_ROOT}/tools/trace_overlay.py <project>` writes `trace/overlay.png`.
  A first trace once put the tip 32 mm too long.
- Lopsided trace? The object was probably crooked in the photo: straighten it (rotate + shift the
  centre line, smallest outline ∪ mirror area) before any mirroring.

## Build and show

- `python3 ${CLAUDE_PLUGIN_ROOT}/tools/make_trace.py <project>` from `<project>/trace/config.json`
  (`title, photo, px_per_in, clearance_mm, store_doc, draft_key`, optional
  `fit {label, bin_x, bin_y, angle, margin}`, `artifact`). It starts from `trace/points.json` when
  present, else `start_points_px`.
- **Bump `draft_key`** whenever the start points change, or an old browser draft hides the new trace.
- Serve it: `python3 ${CLAUDE_PLUGIN_ROOT}/tools/viewer_server.py <project>/trace` (or through
  `portless <project>-trace sh -c '...'` when the profile's launcher is portless) and open the URL
  in the app's browser. Never a plain `http.server`: Save needs the helper.
- claude.ai Artifact (only when the user asks, claude.ai sessions only): publish `trace/index.html`
  with `files: {"photo.jpg": ...}` and `capabilities: {"db": {}, "user": {}}`. Sources must be under
  the working directory or the scratchpad, so copy both there first. Store the URL in `config.json`
  `artifact`; never make a second artifact.
- Template: `${CLAUDE_PLUGIN_ROOT}/tools/trace/template.html`. A plugin update changes it; rebuild a
  project's trace to pick it up.

## Read back

"Save for Claude" writes `trace/points.json` (`points_px`, `points_mm`, `saved_at`) straight into the
project when served locally. (From an Artifact it writes db doc `trace/current` instead: pull it with
`ArtifactData` get into `trace/points.json`.) Check `saved_at`, paste `points_mm` into the `.scad`,
and rebuild the editor. Record the outline size in `data/objects/<slug>.json` (`"source": "trace"`,
`"trace": "<project>/trace/points.json"`).

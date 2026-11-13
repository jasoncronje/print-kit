# print-kit

A Claude Code plugin for designing parametric OpenSCAD parts for your own 3D printer.

It gives Claude a set of house rules, a profile of your printer and slicer, and the workflow and tools
that came out of designing and printing dozens of real parts: stands, docks, enclosures, mounts and
Gridfinity bins.

## What's in it

| Piece | What it does |
|---|---|
| `/print-kit:setup` | Asks about your printer, bed, nozzle, slicer, materials and rules; writes `print-kit.json` and a `data/` folder |
| Session rules | Loaded automatically in folders with a profile: project layout, fit and print rules, your profile |
| `scad-design` skill | How to write a model: clearances from your own fit data, taste, printability, mechanisms, checks, self-critique |
| `measure-and-fit` skill | Spec lookups, caliper-request pages, fit-test pieces and ladders, recording results |
| `gridfinity-bin` skill | Outline-first workflow, tested base geometry, walls, scoops, labels |
| `print-viewer` skill | Interactive 3D viewer: assembly, pull-apart, measure, X-ray, print plates on your bed with overhangs, Open in your slicer |
| `design-reviewer` agent | Fresh-eyes review that builds and checks the parts before you print |
| `check_scad.py` | Exports every printable part and checks manifold, bed fit, first layer, Gridfinity feet, overhangs, clash parts |
| Trace and layout editors | Trace a tool's outline from a photo, or lay out round and square pockets, and save straight into the project |

## Install

```
/plugin marketplace add <github-user>/print-kit
/plugin install print-kit@print-kit
```

Then, in the folder where you keep your print projects:

```
/print-kit:setup
```

Start a new session (or `/clear`) after setup so the rules load.

## Needs

- [OpenSCAD](https://openscad.org) on your PATH (`openscad`).
- Python 3.9+. Pillow only for the photo-trace editor (`pip install pillow`).
- A slicer, if you want the viewer's "Open in <slicer>" button: Bambu Studio, OrcaSlicer, PrusaSlicer
  or Cura. Without one, the button saves the plate's `.3mf`.
- Optional: [Portless](https://github.com/vercel-labs/portless) for `https://<name>.localhost` URLs.

macOS is the tested platform. Linux and Windows should work with the matching `open_command`
(setup fills it in).

## Your profile

`print-kit.json` sits at the root of your projects folder (or in `~/.config/print-kit/` for all
folders). Every tool reads it:

```json
{
  "printer": { "name": "Prusa MK4", "bed_mm": [250, 210, 220], "nozzle_mm": 0.4 },
  "slicer": { "name": "PrusaSlicer", "open_command": ["open", "-n", "-a", "PrusaSlicer", "--args", "{file}"] },
  "materials": { "default": "PLA", "owned": ["PLA", "PETG"] },
  "rules": { "ask_before_print": true, "gridfinity_outline_gate": true },
  "taste": ["Rounded corners everywhere, 3 mm minimum"]
}
```

Full template with every field: `plugins/print-kit/templates/print-kit.json`.

## Your data

`data/` holds what you learn from real prints: object sizes (`objects/`), fit results (`fits.csv`),
print outcomes (`prints.csv`) and the hardware you own (`hardware.json`). Claude reads it before
picking a number and adds to it after each print. The clearance starting values in the skills come
from the author's Bambu P2S with PLA on a 0.4 nozzle; your own rows replace them as you test.

## A project

```
my-prints/
  print-kit.json
  data/
  phone-stand/
    phone_stand.scad     part = "assembly" | "body" | "fit_test" | "clash_*"
    stl/                 ready to slice, in print orientation
    viewer/config.json   the 3D viewer's parts and plates
    README.md
    CHANGELOG.md
```

## Credits

Mesh checks in `check_scad.py` are ported from `verify-model.py` in Wilson Waters' 3d-printing repo
(MIT). Gridfinity base geometry matches kennetek/gridfinity-rebuilt-openscad. The viewer uses
three.js.

## License

MIT

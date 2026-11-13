<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand/banner/banner-dark.svg">
  <img alt="print-kit: OpenSCAD parts for your own 3D printer" src="brand/banner/banner-light.svg" width="100%">
</picture>

A Claude Code plugin for designing parametric OpenSCAD parts for your own 3D printer.

It gives Claude a set of house rules, a profile of your printer and slicer, and the workflow and tools
that came out of designing and printing dozens of real parts: stands, docks, enclosures, mounts and
Gridfinity bins.

## What you get

- **Setup for your printer.** One command asks about your printer, slicer and materials, then every part is sized for them.
- **Design rules.** Claude follows tested clearances, printable shapes and a self-check before handing a part over.
- **Fit tests.** Small, fast test prints for snaps, pockets and plugs, with the results remembered for next time.
- **Model checks.** Every part is checked for bed fit, a flat first layer, overhangs and collisions.
- **3D viewer.** Spin, explode and measure your model, see print plates on your bed, and open them in your slicer.
- **Gridfinity bins.** Trace a tool from a photo and get a bin with a pocket shaped to fit it.

## Made with print-kit

![36 parts designed in code and printed at home](brand/prints-gallery.png)

Stands, docks, enclosures, mounts, Gridfinity bins and keyboard parts, all designed with Claude and printed on a Bambu Lab P2S.

## Install

You need [Claude Code](https://claude.com/claude-code). Then, inside it:

```
/plugin marketplace add jasoncronje/print-kit
/plugin install print-kit@print-kit
```

Open the folder you keep your prints in (any folder, ideally a git repo) and run:

```
/print-kit:setup
```

Setup finds OpenSCAD and your slicer, offers to install OpenSCAD if it's missing, asks about your
printer, and writes `print-kit.json` and a `data/` folder. Start a new session (or `/clear`) and try:

```
Design a stand for my phone. Start with a fit test for the cradle.
```

The only dependency is OpenSCAD. The tools are plain Python 3.9+ with no packages. A slicer is
optional: without one, the viewer saves the plate's `.3mf` instead of opening it.

While the repo is private, you need read access and a GitHub login git can use (`gh auth login`).

<details>
<summary><b>Check or install by hand</b></summary>

To see what's installed, ask Claude to "run the print-kit doctor".

Install OpenSCAD yourself:

```bash
brew install --cask openscad@snapshot   # macOS (the stable cask is disabled)
sudo apt install openscad               # Debian/Ubuntu
winget install OpenSCAD.OpenSCAD        # Windows
```

For `https://<name>.localhost` viewer URLs, install [Portless](https://github.com/vercel-labs/portless)
(`npm install -g portless`) and say yes when setup offers it.

</details>

<details>
<summary><b>Updating</b></summary>

```
/plugin marketplace update print-kit
```

Then restart Claude Code.

</details>

macOS is the tested platform. Linux and Windows should work; setup fills in the slicer command.

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

## Brand

Logo, palette and usage: [brand/](brand/README.md).

## Credits

Mesh checks in `check_scad.py` are ported from `verify-model.py` in Wilson Waters' 3d-printing repo
(MIT). Gridfinity base geometry matches kennetek/gridfinity-rebuilt-openscad. The viewer uses
three.js.

## License

MIT

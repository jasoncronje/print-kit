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

Pick your system. Each guide is the whole install, first step to first part.

<details>
<summary><b>Install on macOS</b></summary>

1. Install [Claude Code](https://claude.com/claude-code) and open it.

2. Add the plugin. Type these two lines into Claude Code:

   ```
   /plugin marketplace add jasoncronje/print-kit
   /plugin install print-kit@print-kit
   ```

   While the repo is private, you need read access and a GitHub login git can use (`gh auth login`).

3. Open the folder you keep your prints in (any folder, ideally a git repo) and run:

   ```
   /print-kit:setup
   ```

   Setup installs Python (via Homebrew or Apple's Command Line Tools) and OpenSCAD (Homebrew if you have
   it, otherwise the official snapshot from openscad.org into your user folder), with no admin rights. Then it finds your slicer, asks about your printer, and
   writes `print-kit.json` and a `data/` folder. A slicer is optional: without one, the viewer
   saves the plate's `.3mf`.

4. Start a new session (or `/clear`) and try:

   ```
   Design a stand for my phone. Start with a fit test for the cradle.
   ```

5. See it in 3D:

   ```
   Show me the stand in the 3D viewer.
   ```

   In the Claude Code desktop app it opens beside the chat. In the terminal you get a link.

Rather install OpenSCAD yourself? Do it before step 3 and setup will use it:

```bash
brew install --cask openscad@snapshot   # the stable cask is disabled
```

</details>

<details>
<summary><b>Install on Windows</b></summary>

1. Install [Git for Windows](https://git-scm.com/downloads/win). Claude Code needs its Bash.

2. Install [Claude Code](https://claude.com/claude-code) and open it.

3. Add the plugin. Type these two lines into Claude Code:

   ```
   /plugin marketplace add jasoncronje/print-kit
   /plugin install print-kit@print-kit
   ```

   While the repo is private, you need read access and a GitHub login git can use (`gh auth login`).

4. Open the folder you keep your prints in (any folder, ideally a git repo) and run:

   ```
   /print-kit:setup
   ```

   Setup installs Python (`winget`) and OpenSCAD (the official snapshot from openscad.org into your user
   folder), with no admin rights. Then it finds your slicer, asks about your printer, and
   writes `print-kit.json` and a `data/` folder. A slicer is optional: without one, the viewer
   saves the plate's `.3mf`.

5. Start a new session (or `/clear`) and try:

   ```
   Design a stand for my phone. Start with a fit test for the cradle.
   ```

5. See it in 3D:

   ```
   Show me the stand in the 3D viewer.
   ```

   In the Claude Code desktop app it opens beside the chat. In the terminal you get a link.

Rather install OpenSCAD yourself? Do it before step 4 and setup will use it:

```bash
winget install OpenSCAD.OpenSCAD
```

</details>

<details>
<summary><b>Install on Ubuntu / Linux</b></summary>

1. Check Python 3 is there: `python3 --version`. Ubuntu already has it.

2. Install [Claude Code](https://claude.com/claude-code) and open it.

3. Add the plugin. Type these two lines into Claude Code:

   ```
   /plugin marketplace add jasoncronje/print-kit
   /plugin install print-kit@print-kit
   ```

   While the repo is private, you need read access and a GitHub login git can use (`gh auth login`).

4. Open the folder you keep your prints in (any folder, ideally a git repo) and run:

   ```
   /print-kit:setup
   ```

   Setup installs OpenSCAD on x86-64 (the official snapshot from openscad.org into your user folder; on
   other CPUs, install it with your package manager first), with no admin rights. Then it finds your slicer, asks about your printer, and
   writes `print-kit.json` and a `data/` folder. A slicer is optional: without one, the viewer
   saves the plate's `.3mf`.

5. Start a new session (or `/clear`) and try:

   ```
   Design a stand for my phone. Start with a fit test for the cradle.
   ```

5. See it in 3D:

   ```
   Show me the stand in the 3D viewer.
   ```

   In the Claude Code desktop app it opens beside the chat. In the terminal you get a link.

Rather install OpenSCAD yourself? Do it before step 4 and setup will use it:

```bash
sudo apt install openscad   # Debian/Ubuntu: older 2021 release, slower
```

</details>

Already installed? These are for later:

<details>
<summary><b>Something isn't working</b></summary>

1. Ask Claude to "run the print-kit doctor". It lists what's installed and what's missing.
2. If OpenSCAD is missing, get it from https://openscad.org/downloads.html.
3. If OpenSCAD is installed but not found, set `"openscad": "/full/path/to/openscad"` in `print-kit.json`.

</details>

<details>
<summary><b>Update print-kit</b></summary>

1. In Claude Code, run:

   ```
   /plugin marketplace update print-kit
   ```

2. Restart Claude Code.

</details>

<details>
<summary><b>Optional: named viewer addresses</b></summary>

For `https://<name>.localhost` viewer URLs instead of a port number:

1. Install [Portless](https://github.com/vercel-labs/portless): `npm install -g portless`
2. Run `/print-kit:setup` again and say yes when it offers Portless.

</details>

Every push is tested on fresh macOS, Windows and Ubuntu machines: OpenSCAD install, model checks,
viewer build and the session hook.

## The 3D viewer

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand/viewer-dark.jpg">
  <img alt="The 3D viewer showing an Apple Watch nightstand stand pulled apart, with its parts list and sizes" src="brand/viewer-light.jpg" width="100%">
</picture>

Every design gets an interactive 3D page, built by Claude and opened inside Claude Code. Ask for it
in plain words:

```
Show me the phone stand in the 3D viewer.
```

- **In the Claude Code desktop app** it opens in the preview pane, beside the chat.
- **In the terminal** Claude gives you a link to open in your browser.

What you can do there:

- **Look at the assembled model.** Spin it, pull the parts apart, cut through it, X-ray it, and measure between two points.
- **Check the print plates.** Each plate is laid out on your printer's bed, with overhangs marked in red.
- **Send a plate to your slicer.** One button opens it there. Without a slicer, it saves the plate's `.3mf`.

It works offline: nothing loads from the internet.

The viewer closes itself about 5 minutes after you close its tab. Ask again to bring it back.

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

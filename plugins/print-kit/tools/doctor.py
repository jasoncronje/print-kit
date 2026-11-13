#!/usr/bin/env python3
"""Check what print-kit needs, and install what's missing.

    python3 doctor.py              # report: what's there, what's missing
    python3 doctor.py --json       # the same, machine-readable (the setup skill reads this)
    python3 doctor.py --install    # install OpenSCAD if it's missing

Needs: Python 3.9+ (you're running it) and OpenSCAD. Everything else is optional and only
reported: a slicer (for the viewer's Open in <slicer> button) and Portless (https URLs).

--install never needs admin rights, except on Linux without an x86-64 AppImage:
  macOS with Homebrew   brew install --cask openscad@snapshot
  macOS without it      the official snapshot .dmg, copied to ~/Applications
  Windows               the official snapshot .zip, unpacked into %LOCALAPPDATA%\\print-kit
  Linux x86-64          the official snapshot AppImage, unpacked into ~/.local/share/print-kit
                        (no FUSE needed), linked as ~/.local/bin/openscad
  Linux, other CPUs     apt, dnf, pacman or flatpak (asks for sudo)
Snapshots come from files.openscad.org and are checked against their published SHA-256.
Standard library only.
"""

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_profile as kit  # noqa: E402

SYSTEM = kit.SYSTEM
SNAPSHOTS = "https://files.openscad.org/snapshots/"
SNAPSHOT_FILE = {  # what to download per platform, as a regex over the snapshot index
    "Darwin": r"OpenSCAD-(\d{4}\.\d\d\.\d\d)\.dmg",
    "Windows": r"OpenSCAD-(\d{4}\.\d\d\.\d\d)-x86-64\.zip",
    "Linux": r"OpenSCAD-(\d{4}\.\d\d\.\d\d)-x86_64\.AppImage",
}
OWN_DIR = kit.data_home() / "openscad"

# name -> (mac app bundle names, linux/windows executables)
SLICERS = {
    "Bambu Studio": (["BambuStudio"], ["bambu-studio", "BambuStudio"]),
    "OrcaSlicer": (["OrcaSlicer"], ["orca-slicer", "OrcaSlicer"]),
    "PrusaSlicer": (["PrusaSlicer", "Original Prusa Drivers/PrusaSlicer"], ["prusa-slicer", "PrusaSlicer"]),
    "Cura": (["UltiMaker Cura", "Ultimaker Cura"], ["cura", "UltiMaker-Cura"]),
}
WIN_DIRS = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, **kw)
    except (OSError, subprocess.TimeoutExpired):
        return None


def find_openscad():
    """(path, version) of the first OpenSCAD that runs, or (None, None)."""
    for c in kit.openscad_candidates():
        r = run([c, "--version"])
        out = (r.stdout + r.stderr).strip() if r else ""
        if r and r.returncode == 0:
            return c, out.splitlines()[-1] if out else "?"
    return None, None


def find_slicers():
    found = {}
    for name, (apps, exes) in SLICERS.items():
        if SYSTEM == "Darwin":
            for a in apps:
                app = Path("/Applications") / f"{a}.app"
                if app.exists():
                    found[name] = ["open", "-n", "-a", app.stem, "--args", "{file}"]
                    break
        else:
            for e in exes:
                p = shutil.which(e)
                if not p and SYSTEM == "Windows":
                    hits = [q for d in WIN_DIRS for q in Path(d).glob(f"*/{e}.exe")]
                    p = str(hits[0]) if hits else None
                if p:
                    found[name] = [p, "{file}"]
                    break
    return found


def install_plan():
    """{"method", "describe", "command"}: how --install would get OpenSCAD here, or None."""
    if SYSTEM == "Darwin" and shutil.which("brew"):
        cmd = ["brew", "install", "--cask", "openscad@snapshot"]   # the stable cask is disabled
        return {"method": "brew", "describe": " ".join(cmd), "command": cmd}
    if SYSTEM in ("Darwin", "Windows") or (SYSTEM == "Linux" and platform.machine() in ("x86_64", "AMD64")):
        where = {"Darwin": "~/Applications", "Windows": str(OWN_DIR), "Linux": str(OWN_DIR)}[SYSTEM]
        return {"method": "download", "command": None,
                "describe": f"download the latest OpenSCAD snapshot (about 80-100 MB) from files.openscad.org into {where}"}
    for pm, cmd in (("apt-get", ["sudo", "apt-get", "install", "-y", "openscad"]),
                    ("dnf", ["sudo", "dnf", "install", "-y", "openscad"]),
                    ("pacman", ["sudo", "pacman", "-S", "--noconfirm", "openscad"]),
                    ("flatpak", ["flatpak", "install", "-y", "flathub", "org.openscad.OpenSCAD"])):
        if shutil.which(pm):
            return {"method": "package", "describe": " ".join(cmd), "command": cmd}
    return None


def report():
    scad, ver = find_openscad()
    return {
        "platform": SYSTEM,
        "python": {"ok": sys.version_info >= (3, 9), "version": platform.python_version(), "path": sys.executable},
        "openscad": {"ok": bool(scad), "path": scad, "version": ver, "on_path": bool(shutil.which("openscad")),
                     "install": install_plan()},
        "slicers": find_slicers(),
        "portless": bool(shutil.which("portless")),
        "ready": bool(scad) and sys.version_info >= (3, 9),
    }


# --- downloading ------------------------------------------------------------------------------

def fetch(url, dest=None):
    """GET url; bytes, or saved to dest. curl first (it has the system's certificates), then urllib."""
    if shutil.which("curl"):
        cmd = ["curl", "-fsSL", "--retry", "2"] + (["-o", str(dest), url] if dest else [url])
        r = subprocess.run(cmd, capture_output=not dest)
        if r.returncode == 0:
            return None if dest else r.stdout
    with urllib.request.urlopen(url, timeout=120) as resp:
        if not dest:
            return resp.read()
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp, f, 1 << 20)
    return None


def latest_snapshot():
    """(file name, url) of the newest snapshot for this platform."""
    index = fetch(SNAPSHOTS).decode("utf-8", "replace")
    hits = sorted(set(re.findall(SNAPSHOT_FILE[SYSTEM], index)))
    if not hits:
        sys.exit(f"No OpenSCAD snapshot for {SYSTEM} found at {SNAPSHOTS}")
    name = re.sub(r"\(.*?\)", hits[-1], SNAPSHOT_FILE[SYSTEM]).replace("\\", "")
    return name, SNAPSHOTS + name


def download_snapshot(tmp):
    name, url = latest_snapshot()
    dest = Path(tmp) / name
    print(f"downloading {url}", flush=True)
    fetch(url, dest)
    want = fetch(url + ".sha256").decode().split()[0].lower()
    h = hashlib.sha256()
    with open(dest, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != want:
        sys.exit(f"{name}: SHA-256 mismatch (got {h.hexdigest()}, expected {want}); not installing")
    print(f"checked SHA-256 of {name}", flush=True)
    return dest


def install_dmg(dmg):
    mnt = Path(tempfile.mkdtemp(prefix="openscad-dmg-"))
    subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(mnt), str(dmg)],
                   check=True, capture_output=True)
    try:
        app = next(mnt.glob("OpenSCAD*.app"))
        dest = Path.home() / "Applications" / "OpenSCAD.app"
        dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            sys.exit(f"{dest} already exists but doesn't run; remove it and try again")
        subprocess.run(["cp", "-R", str(app), str(dest)], check=True)   # keeps the bundle's symlinks
        print(f"installed {dest}")
    finally:
        subprocess.run(["hdiutil", "detach", str(mnt)], capture_output=True)


def install_zip(zpath):
    OWN_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(OWN_DIR)
    print(f"installed into {OWN_DIR}")


def install_appimage(img):
    OWN_DIR.mkdir(parents=True, exist_ok=True)
    img = Path(shutil.move(str(img), str(OWN_DIR / "OpenSCAD.AppImage")))   # /tmp may be noexec
    img.chmod(0o755)
    # Unpack instead of running the AppImage: Ubuntu 22.04+ ships without the FUSE 2 it mounts with.
    old = OWN_DIR / "squashfs-root"
    if old.exists():
        shutil.rmtree(old)
    subprocess.run([str(img), "--appimage-extract"], cwd=OWN_DIR, check=True, capture_output=True)
    wrapper = OWN_DIR / "openscad"
    wrapper.write_text("#!/bin/sh\n"
                       "# print-kit: run the unpacked OpenSCAD AppImage. Headless sessions get Qt's offscreen platform.\n"
                       '[ -n "$DISPLAY$WAYLAND_DISPLAY" ] || export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"\n'
                       f'exec "{OWN_DIR / "squashfs-root" / "AppRun"}" "$@"\n', encoding="utf-8")
    wrapper.chmod(0o755)
    img.unlink()
    link = Path.home() / ".local" / "bin" / "openscad"
    if not link.exists():
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(wrapper)
        print(f"linked {link}")
    print(f"installed into {OWN_DIR}")


def link_on_mac(path):
    """macOS app found but not on PATH: link it next to brew's binaries so `openscad` works in a shell."""
    if SYSTEM != "Darwin" or shutil.which("openscad") or not shutil.which("brew"):
        return
    r = run(["brew", "--prefix"])
    if r and r.returncode == 0:
        link = Path(r.stdout.strip()) / "bin" / "openscad"
        try:
            link.symlink_to(path)
            print(f"linked {link} -> {path}")
        except OSError as e:
            print(f"couldn't link {link}: {e}")


def install():
    plan = install_plan()
    if not plan:
        sys.exit("No way to install OpenSCAD here. Get it from https://openscad.org/downloads.html")
    if plan["command"]:
        print("running:", plan["describe"], flush=True)
        if subprocess.run(plan["command"]).returncode:
            sys.exit(f"OpenSCAD install failed. Run it yourself in a terminal: {plan['describe']}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        f = download_snapshot(tmp)
        {"Darwin": install_dmg, "Windows": install_zip, "Linux": install_appimage}[SYSTEM](f)


def main():
    args = sys.argv[1:]
    rep = report()
    if "--install" in args:
        if not rep["openscad"]["ok"]:
            install()
        scad, _ = find_openscad()
        if scad:
            link_on_mac(scad)
        rep = report()
        if not rep["openscad"]["ok"]:
            for c in kit.openscad_candidates():   # show why each one fails
                r = run([c, "--version"])
                print(f"{c}: " + (f"exit {r.returncode}\n{(r.stdout + r.stderr).strip()[-1500:]}" if r else "would not start"))
            sys.exit("OpenSCAD installed but doesn't run; see the output above.")
    if "--json" in args:
        print(json.dumps(rep, indent=2))
        return
    o = rep["openscad"]
    print(f"python    {'ok' if rep['python']['ok'] else 'TOO OLD (need 3.9+)'}  {rep['python']['version']}  {rep['python']['path']}")
    if o["ok"]:
        print(f"openscad  ok  {o['version']}  {o['path']}")
    else:
        how = f"  (it will {o['install']['describe']})" if o["install"] else ""
        print(f"openscad  MISSING  run: doctor.py --install{how}")
    print("slicer    " + (", ".join(rep["slicers"]) or "none found (optional: the viewer saves .3mf files instead)"))
    print("portless  " + ("yes" if rep["portless"] else "no (optional)"))
    print("\nready" if rep["ready"] else "\nnot ready")
    sys.exit(0 if rep["ready"] else 1)


if __name__ == "__main__":
    main()

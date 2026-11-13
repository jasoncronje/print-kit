#!/usr/bin/env python3
"""Serve a 3D viewer or editor page locally: open plates in your slicer, and saves into the project.

    python3 viewer_server.py <project>/viewer            # port from $PORT, else a free one
    python3 viewer_server.py <project>/trace             # also layout/, measurements/
    portless <name> sh -c 'python3 viewer_server.py <project>/viewer'   # https://<name>.localhost

Serves the folder like `python3 -m http.server` (127.0.0.1 only) and adds:
  GET  / and /index.html -> for a viewer folder (has data.json): the shared template, read
                    fresh on every load with the title from config.json, so a template change
                    shows up on reload everywhere. Other folders serve their own index.html.
  GET  /vendor/<f>  -> viewer/vendor/<f>: three.js and its helpers, so no viewer needs a CDN
  GET  /api/slicer  -> {"slicer": "<name>" or null, "loadRequest": bool}, so the page knows what
                    the helper can do (also its heartbeat)
  POST /api/slicer  body = the plate's .3mf, header X-Filename; saves it and opens it in the
                    slicer ({file} in the command is the plate, else it goes on the end)
  GET  /api/local-db.js -> tools/local_db.js, the page-side stand-in for the artifact store
  GET  /api/store   -> {"store": true} (helper check and heartbeat)
  GET  /api/store?file=<f>  -> {"exists", "data"} for <f>, a .json file inside the served folder
  POST /api/store?file=<f>  body {"mode": "set" | "update", "data": {...}}; set replaces the
                    file, update merges top-level keys into it. Written atomically.

Only requests from a localhost page are accepted, only .3mf zips are opened, and saves
can't touch config.json or data.json or leave the served folder.

An open viewer tab pings /api/slicer every minute (editor pages ping /api/store).
After IDLE_SECONDS with no request at all (every tab closed), the server exits, so none
are left running.

Which slicer the viewer's main button opens, first match wins:
  VIEWER_SLICER     "bambu", "orca", "prusa" or "cura"; "none" for a plain download; or your own
                    command or .app path
  print-kit.json    slicer.open_command (with slicer.name on the button)
  otherwise         the first of those four found installed
VIEWER_LOAD_REQUEST=1 adds a button that copies a "load this plate" prompt for an AI assistant
that drives the slicer.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import kit_profile as kit  # noqa: E402

TEMPLATE = TOOLS / "viewer" / "template.html"
VENDOR = TOOLS / "viewer" / "vendor"
LOCAL_DB = TOOLS / "local_db.js"
STORE_FILE = re.compile(r"[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*\.json")
PROTECTED = {"config.json", "data.json"}
OUT = Path(tempfile.gettempdir()) / "print-kit-plates"
MAX_BYTES = 300 * 1024 * 1024
IDLE_SECONDS = int(os.environ.get("VIEWER_IDLE", "300"))
last_request = time.monotonic()


# id: (name, macOS app names, commands on PATH, Windows paths under Program Files)
SLICERS = {
    "bambu": ("Bambu Studio", ["BambuStudio"], ["bambu-studio"], ["Bambu Studio/bambu-studio.exe"]),
    "orca": ("OrcaSlicer", ["OrcaSlicer"], ["orca-slicer", "OrcaSlicer"], ["OrcaSlicer/orca-slicer.exe"]),
    "prusa": ("PrusaSlicer", ["PrusaSlicer", "Original Prusa Drivers/PrusaSlicer"], ["prusa-slicer", "PrusaSlicer"],
              ["Prusa3D/PrusaSlicer/prusa-slicer.exe"]),
    "cura": ("Cura", ["UltiMaker Cura", "Ultimaker Cura"], ["cura", "UltiMaker-Cura"], ["UltiMaker Cura/UltiMaker-Cura.exe"]),
}


def find_slicer(choice):
    """(name, command) for the slicer that plates open in, or None to download them instead.

    The plate's path is added to the end of the command.
    """
    choice = (choice or "auto").strip()
    if choice.lower() in ("none", "off", "download"):
        return None
    if choice.lower() not in SLICERS and choice.lower() != "auto":
        # your own slicer: a command, or a .app on macOS
        cmd = shlex.split(choice)
        if sys.platform == "darwin" and cmd[0].endswith(".app"):
            return (Path(cmd[0]).stem, ["open", "-n", "-a", *cmd, "--args"]) if Path(cmd[0]).exists() else None
        return (Path(cmd[0]).stem, cmd) if shutil.which(cmd[0]) else None
    for key in [choice.lower()] if choice.lower() in SLICERS else SLICERS:
        name, apps, commands, windows = SLICERS[key]
        if sys.platform == "darwin":
            for app in apps:
                for root in (Path("/Applications"), Path.home() / "Applications"):
                    if (root / f"{app}.app").exists():
                        # -n: a separate instance, so a project that's already open is left alone
                        return name, ["open", "-n", "-a", str(root / f"{app}.app"), "--args"]
        if sys.platform == "win32":
            for rel in windows:
                for base in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
                    exe = Path(os.environ.get(base, "")) / rel
                    if os.environ.get(base) and exe.exists():
                        return name, [str(exe)]
        for command in commands:
            if shutil.which(command):
                return name, [shutil.which(command)]
    return None


def open_in_slicer(command, path):
    """Start the slicer on a file. Returns an error message, or None when it started."""
    if any("{file}" in a for a in command):
        cmd = [a.replace("{file}", str(path)) for a in command]
    else:
        cmd = [*command, str(path)]
    try:
        if cmd[0] == "open":   # macOS: `open` returns at once and reports a missing app itself
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            return (r.stderr.strip() or "open failed") if r.returncode else None
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        return str(e)
    return None


def pick_slicer(root):
    """VIEWER_SLICER, then the profile's slicer.open_command, then whatever is installed."""
    if "VIEWER_SLICER" in os.environ:
        return find_slicer(os.environ["VIEWER_SLICER"])
    prof = kit.load(root)["slicer"]
    if prof.get("open_command"):
        return prof.get("name") or "slicer", list(prof["open_command"])
    return find_slicer(None)


SLICER = None   # (name, command), set in main()
LOAD_REQUEST = os.environ.get("VIEWER_LOAD_REQUEST", "").lower() not in ("", "0", "false", "no")


def local_origin(value):
    host = urlparse(value or "").hostname or ""
    return host in ("localhost", "127.0.0.1", "::1") or host.endswith(".localhost")


class Handler(SimpleHTTPRequestHandler):
    def parse_request(self):
        global last_request
        last_request = time.monotonic()
        return super().parse_request()

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        if path == "/api/slicer":
            return self.send_json(200, {"slicer": SLICER[0] if SLICER else None, "loadRequest": LOAD_REQUEST})
        if path == "/api/local-db.js":
            return self.send_body(LOCAL_DB.read_bytes(), "text/javascript; charset=utf-8")
        if path == "/api/store":
            return self.store_get()
        if path.startswith("/vendor/") and (VENDOR / path[8:]).name == path[8:] and (VENDOR / path[8:]).is_file():
            return self.send_body((VENDOR / path[8:]).read_bytes(), "text/javascript; charset=utf-8")
        if path in ("/", "/index.html") and (Path(self.directory) / "data.json").exists():
            return self.send_page()
        return super().do_GET()

    def send_body(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def store_path(self):
        """The ?file= target inside the served folder, or None if it isn't allowed."""
        name = (parse_qs(urlparse(self.path).query).get("file") or [""])[0]
        if not STORE_FILE.fullmatch(name) or name in PROTECTED:
            return None
        root = Path(self.directory).resolve()
        path = (root / name).resolve()
        return path if root in path.parents else None

    def store_get(self):
        if "file=" not in self.path:
            return self.send_json(200, {"store": True})
        path = self.store_path()
        if not path:
            return self.send_json(400, {"error": "file"})
        if not path.exists():
            return self.send_json(200, {"exists": False, "data": None})
        return self.send_json(200, {"exists": True, "data": json.loads(path.read_text(encoding="utf-8"))})

    def store_post(self):
        path = self.store_path()
        if not path:
            return self.send_json(400, {"error": "file"})
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= 10 * 1024 * 1024:
            return self.send_json(413, {"error": "size"})
        try:
            req = json.loads(self.rfile.read(n))
            mode, data = req["mode"], req["data"]
            assert mode in ("set", "update") and isinstance(data, dict)
        except Exception:
            return self.send_json(400, {"error": "body"})
        if mode == "update" and path.exists():
            data = {**json.loads(path.read_text(encoding="utf-8")), **data}
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        self.send_json(200, {"saved": str(path)})

    def send_page(self):
        cfg = Path(self.directory) / "config.json"
        title = json.loads(cfg.read_text(encoding="utf-8")).get("title", "") if cfg.exists() else ""
        body = TEMPLATE.read_text(encoding="utf-8").replace("__TITLE__", title or Path(self.directory).parent.name).encode()
        self.send_body(body, "text/html; charset=utf-8")

    def end_headers(self):
        # always revalidate, so a rebuilt data.json or a template change shows on reload
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_POST(self):
        route = self.path.split("?")[0]
        if route not in ("/api/slicer", "/api/store"):
            return self.send_json(404, {"error": "not found"})
        # a page on another site could POST here too; only our own localhost pages may
        if not local_origin(self.headers.get("Origin")):
            return self.send_json(403, {"error": "origin"})
        if route == "/api/store":
            return self.store_post()
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= MAX_BYTES:
            return self.send_json(413, {"error": "size"})
        data = self.rfile.read(n)
        if data[:2] != b"PK":
            return self.send_json(400, {"error": "not a 3mf"})
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", self.headers.get("X-Filename") or "plate.3mf").strip("-.")
        if not name.endswith(".3mf"):
            name += ".3mf"
        OUT.mkdir(exist_ok=True)
        path = OUT / name
        path.write_bytes(data)
        if not SLICER:
            return self.send_json(404, {"error": "no slicer found"})
        error = open_in_slicer(SLICER[1], path)
        if error:
            return self.send_json(500, {"error": error})
        self.send_json(200, {"opened": str(path), "slicer": SLICER[0]})


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1]).resolve()
    global SLICER
    SLICER = pick_slicer(root)
    port = int(os.environ.get("PORT", "0"))  # 0: any free port
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(root)))
    port = server.server_address[1]
    opens = f"plates open in {SLICER[0]}" if SLICER else "no slicer found, plates download"
    print(f"Serving {root} on http://127.0.0.1:{port}/ ({opens}, saves enabled, exits {IDLE_SECONDS}s after the last tab closes)", flush=True)
    threading.Thread(target=exit_when_idle, args=(server,), daemon=True).start()
    server.serve_forever()
    print("No tab open; exiting", flush=True)


def exit_when_idle(server):
    while time.monotonic() - last_request < IDLE_SECONDS:
        time.sleep(15)
    server.shutdown()


if __name__ == "__main__":
    main()

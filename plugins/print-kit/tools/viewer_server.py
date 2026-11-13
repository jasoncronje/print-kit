#!/usr/bin/env python3
"""Serve a 3D viewer or editor page locally: Open in <slicer>, and saves into the project.

    python3 viewer_server.py <project>/viewer            # port from $PORT, else a free one
    python3 viewer_server.py <project>/trace             # also layout/, measurements/
    portless <name> sh -c 'python3 viewer_server.py <project>/viewer'   # https://<name>.localhost

Serves the folder like `python3 -m http.server` (127.0.0.1 only) and adds:
  GET  / and /index.html -> for a viewer folder (has data.json): the shared template, read
                    fresh on every load with the title from config.json, so a template change
                    shows up on reload everywhere. Other folders serve their own index.html.
  GET  /api/bambu   -> {"bambu": <can open a slicer>, "slicer": name}, so the page knows the
                    helper is there (also its heartbeat). The route name is historical.
  POST /api/bambu   body = the plate's .3mf, header X-Filename; saves it and runs the profile's
                    slicer.open_command with {file} filled in (print-kit.json)
  GET  /api/local-db.js -> tools/local_db.js, the page-side stand-in for the artifact store
  GET  /api/store   -> {"store": true} (helper check and heartbeat)
  GET  /api/store?file=<f>  -> {"exists", "data"} for <f>, a .json file inside the served folder
  POST /api/store?file=<f>  body {"mode": "set" | "update", "data": {...}}; set replaces the
                    file, update merges top-level keys into it. Written atomically.

Only requests from a localhost page are accepted, only .3mf zips are opened, and saves
can't touch config.json or data.json or leave the served folder.

An open viewer tab pings /api/bambu every minute (editor pages ping /api/store).
After IDLE_SECONDS with no request at all (every tab closed), the server exits, so none
are left running.
"""

import json
import os
import re
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
LOCAL_DB = TOOLS / "local_db.js"
STORE_FILE = re.compile(r"[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*\.json")
PROTECTED = {"config.json", "data.json"}
OUT = Path(tempfile.gettempdir()) / "print-kit-plates"
MAX_BYTES = 300 * 1024 * 1024
IDLE_SECONDS = int(os.environ.get("VIEWER_IDLE", "300"))
last_request = time.monotonic()
SLICER = {"name": "", "open_command": []}


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
        if path == "/api/bambu":
            return self.send_json(200, {"bambu": bool(SLICER["open_command"]), "slicer": SLICER["name"]})
        if path == "/api/local-db.js":
            return self.send_body(LOCAL_DB.read_bytes(), "text/javascript; charset=utf-8")
        if path == "/api/store":
            return self.store_get()
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
        if route not in ("/api/bambu", "/api/store"):
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
        if not SLICER["open_command"]:
            return self.send_json(501, {"error": "no slicer.open_command in print-kit.json"})
        cmd = [a.replace("{file}", str(path)) for a in SLICER["open_command"]]
        if not any("{file}" in a for a in SLICER["open_command"]):
            cmd.append(str(path))
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except OSError as e:
            return self.send_json(500, {"error": str(e)})
        if r.returncode:
            return self.send_json(500, {"error": r.stderr.strip() or "open failed"})
        self.send_json(200, {"opened": str(path)})


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1]).resolve()
    SLICER.update(kit.load(root)["slicer"])
    port = int(os.environ.get("PORT", "0"))  # 0: any free port
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(root)))
    port = server.server_address[1]
    print(f"Serving {root} on http://127.0.0.1:{port}/ (Open in {SLICER['name'] or 'slicer'} and saves enabled, exits {IDLE_SECONDS}s after the last tab closes)", flush=True)
    threading.Thread(target=exit_when_idle, args=(server,), daemon=True).start()
    server.serve_forever()
    print("No tab open; exiting", flush=True)


def exit_when_idle(server):
    while time.monotonic() - last_request < IDLE_SECONDS:
        time.sleep(15)
    server.shutdown()


if __name__ == "__main__":
    main()

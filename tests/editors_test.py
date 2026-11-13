#!/usr/bin/env python3
"""Build the sample trace and layout editors, serve them, and save through the server.

    python3 tests/editors_test.py

Checks what a browser can't be asked to in CI: the pages build with their config inline, the
server hands them out with the save helper, and Save lands as a file in the project folder.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "plugins" / "print-kit" / "tools"
BIN = REPO / "tests" / "sample" / "bit-bin"
PORT = 8766
BASE = f"http://127.0.0.1:{PORT}"


def run(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True)


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.read().decode("utf-8")


def post(path, body, origin=BASE):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Origin": origin})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def serve(folder, saved, title, body):
    """Serve one editor folder, load its page and save `body` to `saved` through the server."""
    target = folder / saved
    if target.exists():
        target.unlink()
    server = subprocess.Popen([sys.executable, str(TOOLS / "viewer_server.py"), str(folder)],
                              env={**os.environ, "PORT": str(PORT)})
    try:
        for _ in range(40):
            try:
                page = get("/")
                break
            except OSError:
                time.sleep(0.25)
        else:
            sys.exit(f"{folder.name}: server did not answer")
        assert title in page, f"{folder.name}: page is not the editor"
        assert "__CONFIG__" not in page, f"{folder.name}: config was not filled in"
        assert get("/api/local-db.js").strip(), f"{folder.name}: no save helper"
        assert json.loads(get("/api/store")) == {"store": True}
        assert json.loads(get(f"/api/store?file={saved}")) == {"exists": False, "data": None}
        assert post(f"/api/store?file={saved}", {"mode": "set", "data": body})[0] == 200
        assert json.loads(target.read_text(encoding="utf-8")) == body, f"{saved} was not written"
        assert json.loads(get(f"/api/store?file={saved}"))["data"] == body
        # another site's page must not be able to write here, nor may a save replace the config
        assert post(f"/api/store?file={saved}", {"mode": "set", "data": {}}, "https://example.com")[0] == 403
        assert post("/api/store?file=config.json", {"mode": "set", "data": {}})[0] == 400
        print(f"ok  {folder.name}: page, save helper, {saved} saved and read back")
    finally:
        server.terminate()
        server.wait(timeout=10)
        if target.exists():
            target.unlink()


def main():
    run(TOOLS / "make_trace.py", BIN)
    run(TOOLS / "make_layout.py", BIN)
    serve(BIN / "trace", "points.json", "Bit driver trace",
          {"points_px": [{"x": 60, "y": 100}, {"x": 340, "y": 100}, {"x": 200, "y": 220}]})
    serve(BIN / "layout", "saved.json", "Bit bin layout",
          {"pockets": [{"id": "bit-1", "kind": "bit", "x": -18, "y": 0, "rot": 90}]})
    # a saved trace or layout is what the next build starts from
    (BIN / "trace" / "points.json").write_text(json.dumps(
        {"points_px": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 6}]}), encoding="utf-8")
    try:
        run(TOOLS / "make_trace.py", BIN)
        assert "[[1, 2], [3, 4], [5, 6]]" in (BIN / "trace" / "index.html").read_text(encoding="utf-8")
    finally:
        (BIN / "trace" / "points.json").unlink()
    print("ok  rebuild starts from the saved trace")


if __name__ == "__main__":
    main()

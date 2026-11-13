// Local stand-in for the claude.ai artifact store, for editor pages served by
// tools/viewer_server.py (trace, layout, caliper asks). Same calls as the
// store's db: db.doc(name).get() -> {exists, data()}, .set(obj), .update(obj).
// Each doc is a JSON file in the served folder, so a save lands in the repo
// with no read-back step.
//
//   <script src="/api/local-db.js"></script>
//   db = window.claude ? await window.claude.use("db")
//      : window.localDb ? await window.localDb({ "trace/current": "points.json" }) : null;
//
// Docs not in the map go to saved/<name with / as ->.json. Resolves to null
// when the helper isn't there (page opened from disk or a plain file server).
// While the page is open it pings the helper every minute, so the server
// doesn't exit under an open tab.
(() => {
  const call = async (file, init) => {
    const r = await fetch("/api/store?file=" + encodeURIComponent(file), init);
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(body.error || r.statusText), { code: body.error || "http-" + r.status });
    return body;
  };
  const write = (file, mode, data) => call(file, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, data }),
  }).then(() => undefined);

  window.localDb = async (files = {}) => {
    try { if (!(await fetch("/api/store")).ok) return null; } catch { return null; }
    setInterval(() => fetch("/api/store").catch(() => {}), 60000);
    const fileFor = name => files[name] || "saved/" + name.replace(/[^A-Za-z0-9_-]+/g, "-") + ".json";
    return {
      doc: name => {
        const file = fileFor(name);
        return {
          get: async () => { const b = await call(file); return { exists: b.exists, data: () => b.data }; },
          set: data => write(file, "set", data),
          update: data => write(file, "update", data),
        };
      },
    };
  };
})();

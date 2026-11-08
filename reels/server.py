"""Tiny local web server for the Reels Studio (no extra dependencies)."""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .plan import load_plan, save_plan, timeline
from .render import export_all

STUDIO_HTML = Path(__file__).parent / "studio" / "index.html"


def serve(project_dir: Path, port: int = 8765, open_browser: bool = True) -> None:
    project_dir = project_dir.resolve()
    plan_path = project_dir / "plan.json"
    out_dir = project_dir / "capcut"
    render_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # keep the terminal quiet
            pass

        def _json(self, data, status=200):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: Path):
            if not path.is_file():
                return self._json({"error": "not found"}, 404)
            size = path.stat().st_size
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            start, end = 0, size - 1
            match = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            if match:  # range requests let the browser seek inside videos
                if match.group(1):
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else end
                else:
                    start = size - int(match.group(2))
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            with path.open("rb") as f:
                f.seek(start)
                remaining = end - start + 1
                try:
                    while remaining > 0:
                        chunk = f.read(min(1 << 20, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._file(STUDIO_HTML)
            if self.path == "/api/plan":
                return self._json(load_plan(plan_path))
            m = re.fullmatch(r"/media/clip/(\d+)", self.path.split("?")[0])
            if m:
                clips = load_plan(plan_path)["clips"]
                idx = int(m.group(1))
                return self._file(Path(clips[idx]["path"])) if idx < len(clips) else self._json({}, 404)
            m = re.fullmatch(r"/media/out/([\w.-]+)", self.path.split("?")[0])
            if m:
                return self._file(out_dir / m.group(1))
            self._json({"error": "not found"}, 404)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/plan":
                save_plan(payload, plan_path)
                return self._json({"ok": True})
            if self.path == "/api/render":
                if not render_lock.acquire(blocking=False):
                    return self._json({"error": "A render is already running."}, 409)
                try:
                    plan = load_plan(plan_path)
                    export_all(plan, out_dir, preview=True)
                    length_s = sum(s["end"] - s["start"] for s, _ in timeline(plan))
                    return self._json({"ok": True, "seconds": round(length_s, 1)})
                except Exception as exc:  # report ffmpeg problems in the UI
                    return self._json({"error": str(exc)}, 500)
                finally:
                    render_lock.release()
            self._json({"error": "not found"}, 404)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"Reels Studio running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStudio stopped.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local server — serves files and persists checklist.json."""
import json
import os
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
CHECKLIST_PATH = os.path.join(ROOT, "checklist.json")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/checklist":
            self._send_json(self._read_checklist())
            return
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/checklist":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                if not isinstance(data.get("checked"), list):
                    raise ValueError("checked must be a list")
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                with open(CHECKLIST_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._send_json({"ok": True})
            except Exception as e:
                self.send_response(400)
                self._send_json({"ok": False, "error": str(e)})
            return
        self.send_error(404)

    def _read_checklist(self):
        if os.path.exists(CHECKLIST_PATH):
            with open(CHECKLIST_PATH, encoding="utf-8") as f:
                return json.load(f)
        return {"checked": [], "updated_at": None}

    def _send_json(self, obj, status=200):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    os.chdir(ROOT)
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}/")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()

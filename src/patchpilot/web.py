from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files

from .demo import run_demo


class Handler(BaseHTTPRequestHandler):
    server_version = "PatchPilot/0.1"

    def _headers(self, status: int, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()

    def do_GET(self):
        if self.path == "/healthz":
            body = json.dumps({"status": "ok"}).encode(); self._headers(200, "application/json"); self.wfile.write(body); return
        if self.path == "/":
            body = files("patchpilot.static").joinpath("index.html").read_bytes()
            self._headers(200, "text/html; charset=utf-8"); self.wfile.write(body); return
        self._headers(404, "application/json"); self.wfile.write(b'{"error":"not_found"}')

    def do_POST(self):
        if self.path != "/api/demo":
            self._headers(404, "application/json"); self.wfile.write(b'{"error":"not_found"}'); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096: raise ValueError
            data = json.loads(self.rfile.read(length) or b"{}")
            task = data.get("task", "repair a failing unit test")
            if not isinstance(task, str) or not 1 <= len(task) <= 500: raise ValueError
            body = json.dumps(run_demo(task), ensure_ascii=False).encode("utf-8")
            self._headers(200, "application/json; charset=utf-8"); self.wfile.write(body)
        except (ValueError, json.JSONDecodeError):
            self._headers(400, "application/json"); self.wfile.write(b'{"error":"invalid_request"}')

    def log_message(self, *_args):
        pass


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = 8765):
    server = create_server(host, port)
    print(f"PatchPilot WebUI: http://{host}:{server.server_port}")
    server.serve_forever()


#!/usr/bin/env python3
"""Serve the frontend and proxy /api/v1/* requests to the backend."""

from __future__ import annotations

import http.client
import json
import os
import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
PORT = int(os.getenv("FRONTEND_PORT", "8095"))
BACKEND_BASE = os.getenv("BACKEND_BASE", "http://127.0.0.1:8001")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _pick_free_port(host: str, preferred_port: int, max_tries: int = 40) -> int:
    for offset in range(max_tries):
        candidate = preferred_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
            except OSError:
                continue
            return candidate
    raise OSError(f"No free port found from {preferred_port}")


def _backend_parts() -> tuple[str, int, str]:
    parsed = urlparse(BACKEND_BASE)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
    scheme = parsed.scheme or "http"
    return host, port, scheme


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/backend-health":
            self._backend_health()
            return
        if self.path in ("/", "/index"):
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/v1/"):
            self._proxy_post()
            return
        self.send_error(404, "Not Found")

    def _backend_health(self) -> None:
        host, port, scheme = _backend_parts()
        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        try:
            conn = conn_cls(host, port, timeout=5)
            conn.request("GET", "/")
            resp = conn.getresponse()
            _ = resp.read()
            ok = 200 <= int(resp.status) < 500
            body = json.dumps({"ok": bool(ok)}).encode("utf-8")
            self.send_response(200 if ok else 503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            body = b'{"ok": false}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

    def _proxy_post(self) -> None:
        host, port, scheme = _backend_parts()
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b""

        headers = {
            "Content-Type": self.headers.get("Content-Type", "application/octet-stream"),
            "Accept": self.headers.get("Accept", "application/json"),
        }

        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        try:
            conn = conn_cls(host, port, timeout=180)
            conn.request("POST", self.path, body=raw_body, headers=headers)
            resp = conn.getresponse()
            payload = resp.read()

            self.send_response(resp.status)
            content_type = resp.getheader("Content-Type") or "application/json"
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            body = json.dumps({"success": False, "error": "ProxyError", "detail": str(exc)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass


def main() -> None:
    actual_port = _pick_free_port(HOST, PORT)
    server = ThreadingHTTPServer((HOST, actual_port), Handler)
    print("=" * 68)
    if actual_port == PORT:
        print(f"UI server:  http://{HOST}:{actual_port}")
    else:
        print(f"UI server:  http://{HOST}:{actual_port} (default {PORT} is occupied)")
    print(f"Backend:    {BACKEND_BASE}")
    print("=" * 68)
    server.serve_forever()


if __name__ == "__main__":
    main()

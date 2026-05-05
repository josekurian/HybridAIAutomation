#!/usr/bin/env python3
import base64
import json
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


HOST = os.getenv("PRIVATE_HOST_BIND", "0.0.0.0")
PORT = int(os.getenv("PRIVATE_HOST_PORT", "9100"))
BASIC_USER = os.getenv("BACKEND_BASIC_USER", "af_login")
BASIC_PASSWORD = os.getenv("BACKEND_BASIC_PASSWORD", "change-me")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "AHFFI_SESSION")
AGENT_NAME = os.getenv("AGENT_NAME", "OCI Agent Factory")

ISSUED_SESSIONS: dict[str, float] = {}


def parse_basic_auth(header: str | None) -> tuple[str | None, str | None]:
    if not header or not header.startswith("Basic "):
        return None, None

    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return None, None

    return username, password


def parse_cookies(header: str | None) -> dict[str, str]:
    cookies: dict[str, str] = {}
    if not header:
        return cookies

    for chunk in header.split(";"):
        if "=" not in chunk:
            continue
        name, value = chunk.strip().split("=", 1)
        cookies[name] = value
    return cookies


def issue_session() -> tuple[str, float]:
    issued_at = time.time()
    token = f"sess-{int(issued_at * 1000)}-{secrets.token_hex(4)}"
    ISSUED_SESSIONS[token] = issued_at
    return token, issued_at


class PrivateHostHandler(BaseHTTPRequestHandler):
    server_version = "PrivateHost/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[private-host] {self.address_string()} - {fmt % args}")

    def _send_json(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}

        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Request body must be valid JSON") from None

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "private-host"})
            return

        if path == "/loginValidation":
            username, password = parse_basic_auth(self.headers.get("Authorization"))
            if username != BASIC_USER or password != BASIC_PASSWORD:
                self._send_json(
                    401,
                    {"status": "unauthorized", "message": "Valid Basic Auth credentials are required."},
                    {"WWW-Authenticate": 'Basic realm="OCI Agent Factory"'},
                )
                return

            session_id, issued_at = issue_session()
            cookie = f"{SESSION_COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=Lax"
            self._send_json(
                200,
                {
                    "status": "authenticated",
                    "session_id": session_id,
                    "cookie_name": SESSION_COOKIE_NAME,
                    "issued_at": issued_at,
                    "message": "Fresh session cookie issued by private host.",
                },
                {"Set-Cookie": cookie},
            )
            return

        self._send_json(404, {"status": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/agent/factory":
            self._send_json(404, {"status": "not_found", "path": path})
            return

        cookies = parse_cookies(self.headers.get("Cookie"))
        session_id = cookies.get(SESSION_COOKIE_NAME)
        if not session_id or session_id not in ISSUED_SESSIONS:
            self._send_json(
                401,
                {
                    "status": "unauthorized",
                    "message": f"Missing or invalid {SESSION_COOKIE_NAME} cookie.",
                },
            )
            return

        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json(400, {"status": "bad_request", "message": str(exc)})
            return

        self._send_json(
            200,
            {
                "status": "ok",
                "agent": AGENT_NAME,
                "session_id": session_id,
                "session_created_at": ISSUED_SESSIONS[session_id],
                "request": payload,
                "reply": "Agent request processed with a freshly validated session.",
            },
        )


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PrivateHostHandler)
    print(f"[private-host] listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

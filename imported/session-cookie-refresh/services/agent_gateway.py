#!/usr/bin/env python3
import json
import os
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


HOST = os.getenv("AGENT_GATEWAY_BIND", "0.0.0.0")
PORT = int(os.getenv("AGENT_GATEWAY_PORT", "8100"))
LOGIN_GATEWAY_URL = os.getenv("LOGIN_GATEWAY_URL", "http://127.0.0.1:8000/link/loginValidation")
PRIVATE_AGENT_URL = os.getenv("PRIVATE_AGENT_URL", "http://127.0.0.1:9100/agent/factory")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "AHFFI_SESSION")
SKIP_VERIFY = os.getenv("BACKEND_SSL_SKIP_VERIFY", "true").lower() == "true"
TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))


def build_ssl_context(target_url: str):
    if not target_url.startswith("https://"):
        return None

    if SKIP_VERIFY:
        return ssl._create_unverified_context()

    return ssl.create_default_context()


def execute_request(request: urllib.request.Request) -> tuple[int, dict[str, str], bytes]:
    try:
        with urllib.request.urlopen(
            request,
            context=build_ssl_context(request.full_url),
            timeout=TIMEOUT_SECONDS,
        ) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


def extract_cookie_pair(set_cookie_header: str | None) -> str | None:
    if not set_cookie_header:
        return None
    return set_cookie_header.split(";", 1)[0]


def extract_session_id(cookie_pair: str | None) -> str | None:
    if not cookie_pair or "=" not in cookie_pair:
        return None
    cookie_name, cookie_value = cookie_pair.split("=", 1)
    if cookie_name != SESSION_COOKIE_NAME:
        return None
    return cookie_value


class AgentGatewayHandler(BaseHTTPRequestHandler):
    server_version = "AgentGateway/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[agent-gateway] {self.address_string()} - {fmt % args}")

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

    def _refresh_cookie(self) -> tuple[int, str | None, str | None, bytes]:
        login_request = urllib.request.Request(LOGIN_GATEWAY_URL, method="GET")
        status, headers, body = execute_request(login_request)
        set_cookie = headers.get("Set-Cookie")
        cookie_pair = extract_cookie_pair(set_cookie)
        return status, set_cookie, cookie_pair, body

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "agent-gateway"})
            return

        self._send_json(404, {"status": "not_found", "path": path})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/agent/factory":
            self._send_json(404, {"status": "not_found", "path": path})
            return

        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json(400, {"status": "bad_request", "message": str(exc)})
            return

        login_status, set_cookie, cookie_pair, login_body = self._refresh_cookie()
        if login_status != 200 or not cookie_pair:
            try:
                login_payload = json.loads(login_body.decode("utf-8"))
            except json.JSONDecodeError:
                login_payload = {"raw_body": login_body.decode("utf-8", errors="replace")}

            self._send_json(
                502,
                {
                    "status": "upstream_login_failed",
                    "login_status": login_status,
                    "login_response": login_payload,
                },
            )
            return

        upstream_body = json.dumps(payload).encode("utf-8")
        agent_request = urllib.request.Request(
            PRIVATE_AGENT_URL,
            data=upstream_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(upstream_body)),
                "Cookie": cookie_pair,
            },
            method="POST",
        )

        agent_status, _, agent_response_body = execute_request(agent_request)
        try:
            agent_payload = json.loads(agent_response_body.decode("utf-8"))
        except json.JSONDecodeError:
            agent_payload = {"raw_body": agent_response_body.decode("utf-8", errors="replace")}

        agent_payload["gateway"] = "agent-api-gateway"
        agent_payload["automatic_cookie_refresh"] = True
        agent_payload["refreshed_session_id"] = extract_session_id(cookie_pair)

        headers = {
            "X-Session-Refresh": "automatic",
            "Set-Cookie": set_cookie,
        }
        self._send_json(agent_status, agent_payload, headers)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AgentGatewayHandler)
    print(f"[agent-gateway] listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

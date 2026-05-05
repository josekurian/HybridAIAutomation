#!/usr/bin/env python3
import base64
import json
import os
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


HOST = os.getenv("LOGIN_GATEWAY_BIND", "0.0.0.0")
PORT = int(os.getenv("LOGIN_GATEWAY_PORT", "8000"))
PRIVATE_LOGIN_URL = os.getenv("PRIVATE_LOGIN_URL", "http://127.0.0.1:9100/loginValidation")
BASIC_USER = os.getenv("BACKEND_BASIC_USER", "af_login")
BASIC_PASSWORD = os.getenv("BACKEND_BASIC_PASSWORD", "change-me")
SKIP_VERIFY = os.getenv("BACKEND_SSL_SKIP_VERIFY", "true").lower() == "true"
TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))


def build_ssl_context(target_url: str):
    if not target_url.startswith("https://"):
        return None

    if SKIP_VERIFY:
        return ssl._create_unverified_context()

    return ssl.create_default_context()


def proxy_request(request: urllib.request.Request) -> tuple[int, dict[str, str], bytes]:
    try:
        with urllib.request.urlopen(
            request,
            context=build_ssl_context(request.full_url),
            timeout=TIMEOUT_SECONDS,
        ) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()


class LoginGatewayHandler(BaseHTTPRequestHandler):
    server_version = "LoginGateway/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[login-gateway] {self.address_string()} - {fmt % args}")

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

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "login-gateway"})
            return

        if path != "/link/loginValidation":
            self._send_json(404, {"status": "not_found", "path": path})
            return

        encoded_credentials = base64.b64encode(f"{BASIC_USER}:{BASIC_PASSWORD}".encode("utf-8")).decode("ascii")
        upstream_request = urllib.request.Request(
            PRIVATE_LOGIN_URL,
            headers={"Authorization": f"Basic {encoded_credentials}"},
            method="GET",
        )

        status, upstream_headers, upstream_body = proxy_request(upstream_request)
        set_cookie = upstream_headers.get("Set-Cookie")

        try:
            body_payload = json.loads(upstream_body.decode("utf-8"))
        except json.JSONDecodeError:
            body_payload = {"raw_body": upstream_body.decode("utf-8", errors="replace")}

        body_payload["gateway"] = "login-api-gateway"
        body_payload["proxied_endpoint"] = PRIVATE_LOGIN_URL

        response_headers: dict[str, str] = {}
        if set_cookie:
            response_headers["Set-Cookie"] = set_cookie

        self._send_json(status, body_payload, response_headers)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), LoginGatewayHandler)
    print(f"[login-gateway] listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

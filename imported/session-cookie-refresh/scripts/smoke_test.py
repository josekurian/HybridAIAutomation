#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request


LOGIN_GATEWAY_URL = os.getenv("LOGIN_GATEWAY_URL", "http://127.0.0.1:8000/link/loginValidation")
AGENT_GATEWAY_URL = os.getenv("AGENT_GATEWAY_URL", "http://127.0.0.1:8100/agent/factory")


def call(request: urllib.request.Request):
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, dict(response.headers.items()), response.read()


def call_login():
    request = urllib.request.Request(LOGIN_GATEWAY_URL, method="GET")
    return call(request)


def call_agent(sequence: int):
    payload = json.dumps({"prompt": f"hello-{sequence}", "sequence": sequence}).encode("utf-8")
    request = urllib.request.Request(
        AGENT_GATEWAY_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Content-Length": str(len(payload))},
        method="POST",
    )
    return call(request)


def extract_session(set_cookie_header: str | None) -> str | None:
    if not set_cookie_header:
        return None
    return set_cookie_header.split(";", 1)[0].split("=", 1)[1]


def main() -> int:
    login_status, login_headers, login_body = call_login()
    if login_status != 200:
        print("login gateway failed")
        print(login_body.decode("utf-8", errors="replace"))
        return 1

    initial_session = extract_session(login_headers.get("Set-Cookie"))
    if not initial_session:
        print("login gateway did not return a session cookie")
        return 1

    agent_one_status, agent_one_headers, agent_one_body = call_agent(1)
    time.sleep(0.05)
    agent_two_status, agent_two_headers, agent_two_body = call_agent(2)

    if agent_one_status != 200 or agent_two_status != 200:
        print("agent gateway call failed")
        print(agent_one_body.decode("utf-8", errors="replace"))
        print(agent_two_body.decode("utf-8", errors="replace"))
        return 1

    session_one = extract_session(agent_one_headers.get("Set-Cookie"))
    session_two = extract_session(agent_two_headers.get("Set-Cookie"))

    if not session_one or not session_two:
        print("agent gateway did not return refreshed cookies")
        return 1

    if session_one == session_two:
        print("expected a fresh cookie on each agent call, but the session did not change")
        return 1

    print("initial session:", initial_session)
    print("agent call 1 session:", session_one)
    print("agent call 2 session:", session_two)
    print("agent response 1:", json.loads(agent_one_body.decode("utf-8")))
    print("agent response 2:", json.loads(agent_two_body.decode("utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

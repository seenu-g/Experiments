"""
One-time (well, every ~60 days) LinkedIn OAuth 2.0 3-legged login.

Opens the LinkedIn consent screen in a browser, catches the redirect on
localhost, exchanges the auth code for an access token, and saves it to
token.json. Run this whenever server.py reports the token is missing or
expired.

Requires LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET / LINKEDIN_REDIRECT_URI
in a .env file next to this script (see .env.example). The redirect URI's
host/port/path must exactly match what's registered in the LinkedIn app's
Auth settings.
"""

from dotenv import load_dotenv
load_dotenv()

import json
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

CLIENT_ID = os.environ["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = os.environ["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:3000/callback")
SCOPES = "openid profile email w_member_social"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
TOKEN_FILE = Path(__file__).parent / "token.json"

_redirect = urlparse(REDIRECT_URI)
CALLBACK_HOST = _redirect.hostname or "localhost"
CALLBACK_PORT = _redirect.port or 3000
CALLBACK_PATH = _redirect.path or "/callback"


class _CallbackHandler(BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        _CallbackHandler.result["code"] = params.get("code", [None])[0]
        _CallbackHandler.result["state"] = params.get("state", [None])[0]
        _CallbackHandler.result["error"] = params.get("error_description", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        body = "Login failed, check the terminal." if _CallbackHandler.result["error"] else "Login complete, you can close this tab."
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass  # silence default request logging


def _wait_for_callback(expected_state: str) -> str:
    server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), _CallbackHandler)
    server.handle_request()  # blocks for exactly one request

    result = _CallbackHandler.result
    if result.get("error"):
        raise RuntimeError(f"LinkedIn denied login: {result['error']}")
    if result.get("state") != expected_state:
        raise RuntimeError("state mismatch -- possible CSRF, aborting")
    if not result.get("code"):
        raise RuntimeError("no authorization code in callback")
    return result["code"]


def login() -> dict:
    state = secrets.token_urlsafe(16)
    auth_url = f"{AUTH_URL}?" + urlencode(
        {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
        }
    )

    print(f"Opening browser for LinkedIn login:\n{auth_url}\n")
    webbrowser.open(auth_url)

    code = _wait_for_callback(state)

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    token = response.json()
    token["obtained_at"] = int(time.time())

    TOKEN_FILE.write_text(json.dumps(token, indent=2))
    print(f"Saved token to {TOKEN_FILE} (expires in {token.get('expires_in')}s)")
    return token


if __name__ == "__main__":
    login()

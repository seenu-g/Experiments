"""
MCP server exposing LinkedIn tools:
- get_my_profile: /v2/userinfo (Sign In with LinkedIn using OpenID Connect)
- create_post: /rest/posts text share (Share on LinkedIn product,
  w_member_social scope). Requires a token obtained after auth.py's scope
  included w_member_social -- rerun auth.py if the token predates that.
Run auth.py first to produce token.json.
"""

import json
import time
from pathlib import Path
from urllib.parse import quote

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LinkedIn")

TOKEN_FILE = Path(__file__).parent / "token.json"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_VERSION = "202511"


def _load_token() -> dict:
    if not TOKEN_FILE.exists():
        raise RuntimeError("No token.json found -- run `python auth.py` to log in first.")

    token = json.loads(TOKEN_FILE.read_text())
    obtained_at = token.get("obtained_at", 0)
    expires_in = token.get("expires_in", 0)
    if time.time() >= obtained_at + expires_in:
        raise RuntimeError("LinkedIn access token has expired -- run `python auth.py` to log in again.")
    return token


@mcp.tool()
def get_my_profile() -> str:
    """Get the logged-in LinkedIn member's basic profile (name, email, headline)."""
    token = _load_token()
    response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    if response.status_code == 401:
        return "error: access token rejected by LinkedIn -- run `python auth.py` to log in again."
    response.raise_for_status()
    return json.dumps(response.json())


@mcp.tool()
def create_post(text: str, link_url: str = "", link_title: str = "") -> str:
    """Publish a post to LinkedIn as the logged-in member. If link_url is
    given, it's attached as an article link preview card; LinkedIn requires
    a title for the card, so link_title is used if given, else link_url
    itself is used as a fallback title."""
    token = _load_token()
    auth_header = {"Authorization": f"Bearer {token['access_token']}"}

    userinfo = requests.get(USERINFO_URL, headers=auth_header)
    if userinfo.status_code == 401:
        return "error: access token rejected by LinkedIn -- run `python auth.py` to log in again."
    userinfo.raise_for_status()
    author_urn = f"urn:li:person:{userinfo.json()['sub']}"

    body = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if link_url:
        body["content"] = {"article": {"source": link_url, "title": link_title or link_url}}

    response = requests.post(
        POSTS_URL,
        headers={
            **auth_header,
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_VERSION,
        },
        json=body,
    )
    if response.status_code == 403:
        return (
            "error: 403 Forbidden -- token may be missing the w_member_social scope. "
            "Rerun `python auth.py` (scope was updated to include it)."
        )
    response.raise_for_status()
    post_urn = response.headers.get("x-restli-id", "")
    return f"published: {post_urn}" if post_urn else "published (no post id returned)"


@mcp.tool()
def get_post(post_urn: str) -> str:
    """Fetch a single LinkedIn post by its URN (e.g. 'urn:li:share:12345'),
    such as the URN returned by create_post."""
    token = _load_token()
    response = requests.get(
        f"{POSTS_URL}/{quote(post_urn, safe='')}",
        headers={
            "Authorization": f"Bearer {token['access_token']}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_VERSION,
        },
    )
    if response.status_code == 401:
        return "error: access token rejected by LinkedIn -- run `python auth.py` to log in again."
    if response.status_code == 403:
        return (
            "error: 403 ACCESS_DENIED -- reading posts back (partnerApiPostsExternal) is "
            "gated behind LinkedIn partner API access. w_member_social lets you create "
            "posts but not read them back via this app."
        )
    if response.status_code == 404:
        return f"error: no post found for {post_urn}"
    response.raise_for_status()
    return json.dumps(response.json())


if __name__ == "__main__":
    mcp.run()

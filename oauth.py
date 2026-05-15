from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import os
import sys
import base64
import hashlib
import secrets
import time
from threading import Thread
import http.server
import webbrowser
from urllib.parse import parse_qs, urlparse
from typing import Tuple

import requests
from rfc3986 import builder as uri_builder

logger = logging.getLogger(__name__)


def _load_dotenv_if_available() -> None:
    """Load credentials from a .env file next to the server, if present."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        logger.warning("Could not load .env file: %s", e)


_load_dotenv_if_available()


def _mask_secret(value: str, visible: int = 4) -> str:
    """Show only the last `visible` chars of a secret for safe logging."""
    if not value or len(value) <= visible:
        return "****"
    return "*" * (len(value) - visible) + value[-visible:]


class OAuthConfig:
    def __init__(self, client_id: str, client_secret: str, login_root: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_root = login_root
        self.redirect_uri = redirect_uri

    @classmethod
    def from_env(cls) -> "OAuthConfig":
        client_id = os.getenv("SF_CLIENT_ID")
        client_secret = os.getenv("SF_CLIENT_SECRET")
        login_root = os.getenv("SF_LOGIN_URL", "login.salesforce.com")
        redirect_uri = os.getenv(
            "SF_CALLBACK_URL", "http://localhost:55556/Callback")

        missing = [name for name, val in {
            "SF_CLIENT_ID": client_id,
            "SF_CLIENT_SECRET": client_secret,
        }.items() if not val]
        if missing:
            logger.error(
                "Missing required environment variables: %s. "
                "Set them via env vars or a .env file next to server.py.",
                ", ".join(missing),
            )
            sys.exit(1)

        logger.info(
            "OAuth config loaded (client_id=...%s, login=%s)",
            _mask_secret(client_id), login_root,
        )
        return cls(client_id=client_id, client_secret=client_secret, login_root=login_root, redirect_uri=redirect_uri)


class _RequestHandler(http.server.BaseHTTPRequestHandler):  # pragma: no cover
    def do_GET(self):  # noqa: N802
        parts = urlparse(self.path)
        if parts.path.lower() != "/callback":
            self.send_error(404, "Not Found", "Not Found")
            return

        args = parse_qs(parts.query)
        self.server.oauth_result = args

        has_code = "code" in args
        response_content = f"Final Status: {has_code=}".encode("utf-8")
        response_content += b"\nYou can close this window now"
        self.send_response(200, "OK")
        self.send_header("Content-Type", "text")
        self.send_header("Content-Length", str(len(response_content)))
        self.end_headers()
        self.wfile.write(response_content)


def _generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code verifier and challenge for OAuth flow"""
    code_verifier = (
        base64.urlsafe_b64encode(secrets.token_bytes(
            32)).decode("utf-8").rstrip("=")
    )

    challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = (
        base64.urlsafe_b64encode(challenge).decode("utf-8").rstrip("=")
    )

    return code_verifier, code_challenge


_TOKEN_CACHE_PATH = os.path.expanduser("~/.dc_mcp_token_cache.json")


def _load_token_cache() -> dict:
    try:
        with open(_TOKEN_CACHE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_token_cache(token: str, instance_url: str, exp: datetime, refresh_token: str = None):
    try:
        data = {"token": token, "instance_url": instance_url, "exp": exp.isoformat()}
        if refresh_token:
            data["refresh_token"] = refresh_token
        else:
            existing = _load_token_cache()
            if existing.get("refresh_token"):
                data["refresh_token"] = existing["refresh_token"]
        with open(os.open(_TOKEN_CACHE_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


class OAuthSession:
    def __init__(self, config: OAuthConfig):
        self.config = config
        self.token: str | None = None
        self.exp: datetime | None = None
        self.instance_url: str | None = None
        self.refresh_token: str | None = None
        # Load from disk cache on init
        cache = _load_token_cache()
        if cache.get("refresh_token"):
            self.refresh_token = cache["refresh_token"]
        if cache.get("token") and cache.get("exp"):
            cached_exp = datetime.fromisoformat(cache["exp"])
            if datetime.now() < cached_exp:
                self.token = cache["token"]
                self.exp = cached_exp
                self.instance_url = cache.get("instance_url")

    def _run_oauth_flow(self, scopes: list[str]):
        logger.info(f"Starting OAuth flow with scopes: {scopes}")
        login_url = f"https://{self.config.login_root}/services/oauth2/authorize"
        token_exchange_url = f"https://{self.config.login_root}/services/oauth2/token"
        redirect_uri = self.config.redirect_uri

        code_verifier, code_challenge = _generate_pkce_pair()

        browser_uri: str = (
            uri_builder.URIBuilder(path=login_url)
            .add_query_from(
                {
                    "client_id": self.config.client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": " ".join(scopes),
                    "prompt": "login",
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                }
            )
            .finalize()
            .unsplit()
        )

        parsed_redirect = urlparse(redirect_uri)
        port = parsed_redirect.port

        logger.debug("Starting OAuth callback server on localhost:%s", port)
        server = http.server.HTTPServer(("localhost", port), _RequestHandler)
        server.allow_reuse_address = True
        t = Thread(target=server.handle_request, daemon=True)
        t.start()

        logger.info("Opening browser for OAuth authorization on %s", self.config.login_root)
        webbrowser.open_new_tab(browser_uri)
        while t.is_alive():
            t.join(10)

        oauth_result_args = server.oauth_result

        if "code" not in oauth_result_args:
            error_msg = "OAuth authentication failed - no authorization code received"
            if "error" in oauth_result_args:
                error_msg += f". Error: {oauth_result_args['error'][0]}"
                if "error_description" in oauth_result_args:
                    error_msg += f" - {oauth_result_args['error_description'][0]}"
            raise Exception(error_msg)

        code = oauth_result_args["code"][0]
        logger.info(f"Authorization code received, exchanging for access token")

        response = requests.post(
            token_exchange_url,
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
        )

        logger.info("Token exchange response: status=%s, elapsed=%.2fs", response.status_code, response.elapsed.total_seconds())

        if response.status_code >= 400:
            logger.error("Token exchange failed (HTTP %s). Check Connected App configuration.", response.status_code)

        response.raise_for_status()

        logger.info("Successfully obtained access token")
        return response.json()

    def _refresh_access_token(self) -> bool:
        """Use refresh token to get a new access token without browser interaction."""
        if not self.refresh_token:
            return False
        token_url = f"https://{self.config.login_root}/services/oauth2/token"
        try:
            response = requests.post(
                token_url,
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                },
                headers={"Accept": "application/json"},
            )
            if response.status_code >= 400:
                logger.warning("Refresh token failed (HTTP %s), will re-auth via browser", response.status_code)
                return False
            data = response.json()
            self.token = data["access_token"]
            self.exp = datetime.now() + timedelta(minutes=110)
            self.instance_url = data.get("instance_url", self.instance_url)
            if data.get("refresh_token"):
                self.refresh_token = data["refresh_token"]
            _save_token_cache(self.token, self.instance_url, self.exp, self.refresh_token)
            logger.info("Silently refreshed access token (no browser needed)")
            return True
        except Exception as e:
            logger.warning("Refresh token exchange failed: %s", type(e).__name__)
            return False

    def ensure_access(self) -> str:
        if self.exp is not None and datetime.now() > self.exp:
            self.exp = None
            self.token = None

        if self.token is None:
            if self._refresh_access_token():
                return self.token
            auth_info = self._run_oauth_flow(
                ["api", "cdp_query_api", "cdp_profile_api", "refresh_token", "offline_access"])
            self.token = auth_info["access_token"]
            self.exp = datetime.now() + timedelta(minutes=110)
            self.instance_url = auth_info["instance_url"]
            if auth_info.get("refresh_token"):
                self.refresh_token = auth_info["refresh_token"]
            _save_token_cache(self.token, self.instance_url, self.exp, self.refresh_token)

        return self.token

    def get_token(self) -> str:
        return self.ensure_access()

    def get_instance_url(self) -> str:
        self.ensure_access()
        return self.instance_url

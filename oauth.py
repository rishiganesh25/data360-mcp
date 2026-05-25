from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta

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


class OAuthConfig:
    """Identifies which sf CLI org to use. Kept as a class for API compatibility."""

    def __init__(self, target_org: str | None):
        self.target_org = target_org

    @classmethod
    def from_env(cls) -> "OAuthConfig":
        target_org = os.getenv("SF_TARGET_ORG")
        if target_org:
            logger.info("Using sf CLI org from SF_TARGET_ORG=%s", target_org)
        else:
            logger.info("SF_TARGET_ORG not set; will use sf CLI default target-org")
        return cls(target_org=target_org)


class OAuthSession:
    """
    Auth session backed by the Salesforce CLI (`sf` / `sfdx`).

    Calls `sf org display --target-org <alias> --json` to retrieve the access token
    and instance URL. The CLI handles refresh transparently — when a token has
    expired, `sf org display` re-issues a new one against the cached refresh token.
    """

    # Re-query the CLI at most once every TTL seconds; the CLI itself caches and
    # refreshes the underlying token.
    _CLI_CACHE_TTL = timedelta(minutes=10)

    def __init__(self, config: OAuthConfig):
        self.config = config
        self._cli_path = shutil.which("sf") or shutil.which("sfdx")
        if not self._cli_path:
            raise RuntimeError(
                "Salesforce CLI not found. Install it (https://developer.salesforce.com/tools/salesforce-cli) "
                "and run `sf org login web --alias <alias>`."
            )
        self.token: str | None = None
        self.instance_url: str | None = None
        self._fetched_at: datetime | None = None

    def _run_cli(self) -> dict:
        cmd = [self._cli_path, "org", "display", "--json"]
        if self.config.target_org:
            cmd += ["--target-org", self.config.target_org]
        logger.debug("Running CLI: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or "").strip()
            raise RuntimeError(
                f"`sf org display` failed (exit {e.returncode}). "
                f"Make sure you have authenticated the org "
                f"(`sf org login web --alias {self.config.target_org or '<alias>'}`).\n{stderr}"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError("Salesforce CLI binary disappeared after init.") from e

        payload = json.loads(result.stdout)
        if payload.get("status") != 0 or "result" not in payload:
            raise RuntimeError(f"sf CLI returned unexpected payload: {payload}")
        return payload["result"]

    def _refresh_from_cli(self) -> None:
        info = self._run_cli()
        token = info.get("accessToken")
        instance_url = info.get("instanceUrl")
        if not token or not instance_url:
            raise RuntimeError(
                "sf CLI did not return accessToken/instanceUrl. "
                "The org may not be authenticated; run `sf org login web`."
            )
        self.token = token
        self.instance_url = instance_url
        self._fetched_at = datetime.now()
        logger.info(
            "Loaded sf CLI session: org=%s, instance=%s",
            info.get("alias") or info.get("username"),
            instance_url,
        )

    def ensure_access(self) -> str:
        cache_stale = (
            self._fetched_at is None
            or datetime.now() - self._fetched_at > self._CLI_CACHE_TTL
        )
        if self.token is None or cache_stale:
            self._refresh_from_cli()
        return self.token  # type: ignore[return-value]

    def get_token(self) -> str:
        return self.ensure_access()

    def get_instance_url(self) -> str:
        self.ensure_access()
        assert self.instance_url is not None
        return self.instance_url

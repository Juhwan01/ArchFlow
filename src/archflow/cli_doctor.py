"""archflow doctor — Check connection status and configuration."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import httpx

from archflow import __version__
from archflow.core.config import load_config, resolve_config_path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MCP_CONFIG_FILE = Path.home() / ".claude" / ".mcp.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _skip(msg: str) -> None:
    print(f"  [--] {msg}")


def _warn(msg: str) -> None:
    print(f"  [!!] {msg}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python() -> bool:
    """Check Python version >= 3.11."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        _ok(f"Python: {version_str}")
        return True
    _fail(f"Python: {version_str} (3.11+ required)")
    return False


def check_config() -> tuple[bool, str | None]:
    """Check if config file exists."""
    config_path = resolve_config_path()
    if config_path:
        _ok(f"Config: {config_path}")
        return True, config_path
    _fail("Config: not found (run 'archflow init')")
    return False, None


def check_jira() -> bool:
    """Test Jira API connection using environment variables."""
    url = os.environ.get("JIRA_URL") or os.environ.get("JIRA_INSTANCE_URL", "")
    email = os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_USER_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_API_KEY", "")

    if not all([url, email, token]):
        _fail("Jira: credentials not set (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)")
        return False

    try:
        creds = base64.b64encode(f"{email}:{token}".encode()).decode()
        resp = httpx.get(
            f"{url.rstrip('/')}/rest/api/2/myself",
            headers={
                "Authorization": f"Basic {creds}",
                "Accept": "application/json",
            },
            timeout=10.0,
        )
        if resp.status_code == 200:
            name = resp.json().get("displayName", email)
            _ok(f"Jira: connected ({name})")
            return True
        _fail(f"Jira: HTTP {resp.status_code}")
        return False
    except httpx.ConnectError:
        _fail(f"Jira: cannot connect to {url}")
        return False
    except Exception as e:
        _fail(f"Jira: {e}")
        return False


def check_github() -> bool:
    """Test GitHub API connection."""
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        _skip("GitHub: not configured (optional)")
        return True  # optional

    try:
        resp = httpx.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10.0,
        )
        if resp.status_code == 200:
            login = resp.json().get("login", "unknown")
            _ok(f"GitHub: connected ({login})")
            return True
        _fail(f"GitHub: HTTP {resp.status_code}")
        return False
    except Exception as e:
        _fail(f"GitHub: {e}")
        return False


def check_gdrive() -> bool:
    """Check Google Drive credentials are set."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        _skip("Google Drive: not configured (optional)")
        return True  # optional

    secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    refresh = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
    if not all([secret, refresh]):
        _warn("Google Drive: incomplete credentials (missing secret or refresh token)")
        return False

    _ok("Google Drive: credentials set")
    return True


def check_mcp_registration() -> bool:
    """Check if archflow is registered in ~/.claude/.mcp.json."""
    if not MCP_CONFIG_FILE.exists():
        _fail(f"MCP: {MCP_CONFIG_FILE} not found")
        return False

    try:
        data = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8-sig"))
        servers = data.get("mcpServers", {})
        if "archflow" in servers:
            _ok("MCP: registered in .mcp.json")
            return True
        _fail("MCP: 'archflow' not found in .mcp.json (run 'archflow init')")
        return False
    except (json.JSONDecodeError, OSError) as e:
        _fail(f"MCP: cannot read .mcp.json ({e})")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_doctor() -> None:
    """Run all diagnostic checks."""
    print()
    print(f"  ArchFlow Doctor v{__version__}")
    print("  " + "=" * 34)
    print()

    results = [
        check_python(),
        check_config()[0],
        check_jira(),
        check_github(),
        check_gdrive(),
        check_mcp_registration(),
    ]

    print()
    failures = results.count(False)
    if failures == 0:
        print("  All checks passed! Run 'archflow' to start the server.")
    else:
        print(f"  {failures} issue(s) found. Fix them and run 'archflow doctor' again.")
    print()

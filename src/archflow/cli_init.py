"""archflow init — Interactive setup wizard."""

from __future__ import annotations

import getpass
import json
import os
import shutil
import sys
from pathlib import Path

import httpx
import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOME_CONFIG_DIR = Path.home() / ".archflow"
HOME_CONFIG_FILE = HOME_CONFIG_DIR / "config.yml"
MCP_CONFIG_FILE = Path.home() / ".claude.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    print()
    print("  +==================================+")
    print("  |   ArchFlow — Setup Wizard        |")
    print("  +==================================+")
    print()


def _prompt(label: str, *, default: str = "", secret: bool = False) -> str:
    """Prompt for input with optional default and secret masking."""
    suffix = f" [{default}]" if default else ""
    prompt_text = f"  {label}{suffix}: "
    if secret:
        value = getpass.getpass(prompt_text)
    else:
        value = input(prompt_text)
    return value.strip() or default


def _confirm(label: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {label} ({hint}): ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _skip(msg: str) -> None:
    print(f"  [--] {msg}")


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_jira(url: str, email: str, token: str) -> tuple[bool, str]:
    """Test Jira API connection. Returns (ok, display_name_or_error)."""
    try:
        import base64
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
            data = resp.json()
            return True, data.get("displayName", email)
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except httpx.ConnectError:
        return False, f"Cannot connect to {url}"
    except Exception as e:
        return False, str(e)


def validate_github(token: str) -> tuple[bool, str]:
    """Test GitHub PAT. Returns (ok, username_or_error)."""
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
            data = resp.json()
            return True, data.get("login", "unknown")
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Config writers
# ---------------------------------------------------------------------------

def _write_config(config_data: dict, path: Path) -> None:
    """Write archflow.config.yml."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _install_skills() -> list[str]:
    """Copy bundled slash-command skills to ~/.claude/skills/."""
    skills_src = Path(__file__).parent / "skills"
    skills_dst = Path.home() / ".claude" / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for skill_dir in sorted(skills_src.glob("archflow-*")):
        if skill_dir.is_dir():
            target = skills_dst / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)
            installed.append(skill_dir.name)

    return installed


def _register_mcp(env_vars: dict) -> None:
    """Register archflow MCP server via `claude mcp add-json` (preferred) or direct file edit (fallback)."""
    import subprocess

    server_config = {
        "type": "stdio",
        "command": "uvx",
        "args": ["archflow-hub"],
        "env": {
            "PYTHONUNBUFFERED": "1",
            "ARCHFLOW_CONFIG_PATH": str(HOME_CONFIG_FILE),
            **env_vars,
        },
    }

    # Try the official `claude mcp add-json` CLI first
    try:
        result = subprocess.run(
            [
                "claude", "mcp", "add-json",
                "--scope", "user",
                "archflow",
                json.dumps(server_config),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return
        # CLI failed — fall through to direct file edit
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: write directly to ~/.claude.json
    config: dict = {}
    if MCP_CONFIG_FILE.exists():
        try:
            config = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    config["mcpServers"]["archflow"] = server_config

    MCP_CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run_init() -> None:
    """Run the interactive setup wizard."""
    _print_banner()

    env_vars: dict[str, str] = {}
    config_data: dict = {}

    # ------------------------------------------------------------------
    # Jira (required)
    # ------------------------------------------------------------------
    print("  -- Jira Cloud (required) --")
    print()

    jira_ok = False
    jira_display = ""

    while not jira_ok:
        jira_url = _prompt("Jira URL", default="https://your-domain.atlassian.net")
        jira_email = _prompt("Jira email")
        jira_token = _prompt("Jira API token", secret=True)

        if not all([jira_url, jira_email, jira_token]):
            _fail("All Jira fields are required.")
            if not _confirm("Retry?"):
                print("  Setup cancelled.")
                sys.exit(1)
            continue

        print("  Validating Jira credentials...", end=" ", flush=True)
        jira_ok, jira_display = validate_jira(jira_url, jira_email, jira_token)

        if jira_ok:
            print(f"OK ({jira_display})")
            env_vars["JIRA_URL"] = jira_url.rstrip("/")
            env_vars["JIRA_EMAIL"] = jira_email
            env_vars["JIRA_API_TOKEN"] = jira_token
        else:
            print(f"FAILED")
            _fail(jira_display)
            if not _confirm("Retry?"):
                print("  Setup cancelled.")
                sys.exit(1)

    print()
    jira_projects_raw = _prompt("Jira project keys (comma-separated)", default="KAN")
    jira_projects = [p.strip() for p in jira_projects_raw.split(",") if p.strip()]
    jira_board_id = _prompt("Jira board ID", default="1")

    config_data["jira"] = {
        "url": env_vars["JIRA_URL"],
        "projects": jira_projects,
        "board_id": jira_board_id,
    }

    # ------------------------------------------------------------------
    # GitHub (optional)
    # ------------------------------------------------------------------
    print()
    print("  -- GitHub (optional, Enter to skip) --")
    print()

    github_token = _prompt("GitHub Personal Access Token", secret=True)
    github_repos: list[str] = []

    if github_token:
        print("  Validating GitHub token...", end=" ", flush=True)
        gh_ok, gh_user = validate_github(github_token)

        if gh_ok:
            print(f"OK ({gh_user})")
            env_vars["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
            repos_raw = _prompt("GitHub repos (owner/repo, comma-separated)")
            github_repos = [r.strip() for r in repos_raw.split(",") if r.strip()]
        else:
            print(f"FAILED")
            _fail(gh_user)
            print("  Skipping GitHub.")
    else:
        _skip("GitHub skipped.")

    config_data["github"] = {
        "repos": github_repos,
        "default_branch": "main",
    }

    # ------------------------------------------------------------------
    # Google Drive (optional)
    # ------------------------------------------------------------------
    print()
    print("  -- Google Drive / Draw.io (optional, Enter to skip) --")
    print("  (Requires OAuth credentials — skip if not using Draw.io)")
    print()

    google_client_id = _prompt("Google Client ID")
    gdrive_folder_id = ""

    if google_client_id:
        google_client_secret = _prompt("Google Client Secret", secret=True)
        google_refresh_token = _prompt("Google Refresh Token")
        gdrive_folder_id = _prompt("Google Drive folder ID (containing .drawio files)")

        if google_client_id and google_client_secret and google_refresh_token:
            env_vars["GOOGLE_CLIENT_ID"] = google_client_id
            env_vars["GOOGLE_CLIENT_SECRET"] = google_client_secret
            env_vars["GOOGLE_REFRESH_TOKEN"] = google_refresh_token
            _ok("Google Drive configured.")
        else:
            _skip("Incomplete Google Drive credentials, skipping.")
    else:
        _skip("Google Drive skipped.")

    config_data["gdrive"] = {
        "folder_id": gdrive_folder_id,
        "cache_ttl_minutes": 30,
    }

    # ------------------------------------------------------------------
    # Matching defaults
    # ------------------------------------------------------------------
    config_data["matching"] = {
        "explicit": [],
        "auto_match": {
            "enabled": True,
            "strategy": "fuzzy",
            "min_score": 0.7,
        },
        "issue_patterns": [
            f"(?i){proj}-\\d+" for proj in jira_projects
        ],
    }

    # ------------------------------------------------------------------
    # Write config file
    # ------------------------------------------------------------------
    print()
    print("  -- Save Configuration --")
    print()
    print(f"  Config will be saved to: {HOME_CONFIG_FILE}")

    _write_config(config_data, HOME_CONFIG_FILE)
    _ok(f"Config saved: {HOME_CONFIG_FILE}")

    # ------------------------------------------------------------------
    # Register MCP server
    # ------------------------------------------------------------------
    print()
    if _confirm("Register ArchFlow in Claude Code (~/.claude.json)?"):
        _register_mcp(env_vars)
        _ok("MCP server registered (scope: user)")
    else:
        print()
        print("  Manual registration:")
        print("    claude mcp add archflow --scope user -- uvx archflow-hub")

    # ------------------------------------------------------------------
    # Install slash commands
    # ------------------------------------------------------------------
    print()
    if _confirm("Install slash commands (/archflow-status, /archflow-arch, etc)?"):
        try:
            installed = _install_skills()
            for name in installed:
                _ok(f"Installed: /{name.replace('archflow-', '')}")
        except Exception as e:
            _fail(f"Slash command install failed: {e}")
            print("  Install manually later:")
            if sys.platform == "win32":
                print("    Copy-Item -Recurse skills\\archflow-* $env:USERPROFILE\\.claude\\skills\\")
            else:
                print("    cp -r skills/archflow-* ~/.claude/skills/")
    else:
        _skip("Slash command installation skipped.")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    print()
    print("  +==================================+")
    print("  |        Setup Complete!           |")
    print("  +==================================+")
    print()
    print("  Connected sources:")
    _ok(f"Jira: {env_vars.get('JIRA_URL', 'N/A')} ({jira_display})")
    if "GITHUB_PERSONAL_ACCESS_TOKEN" in env_vars:
        _ok(f"GitHub: {len(github_repos)} repo(s) configured")
    else:
        _skip("GitHub: not configured")
    if "GOOGLE_CLIENT_ID" in env_vars:
        _ok("Google Drive: configured")
    else:
        _skip("Google Drive: not configured")
    print()
    print("  Next steps:")
    print("    1. Restart Claude Code")
    print("    2. Try: /archflow-status or /archflow-onboard")
    print()

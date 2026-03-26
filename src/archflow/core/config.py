"""Load and validate archflow.config.yml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Config schema
# ---------------------------------------------------------------------------


class JiraConfig(BaseModel):
    url: str = ""
    projects: list[str] = []
    board_id: str | None = None


class GitHubConfig(BaseModel):
    repos: list[str] = []
    default_branch: str = "main"


class GDriveConfig(BaseModel):
    folder_id: str = ""
    cache_ttl_minutes: int = 30


class ExplicitMapping(BaseModel):
    diagram_node: str
    jira_component: str | None = None
    jira_labels: list[str] = []
    github_path_prefix: str | None = None


class AutoMatchConfig(BaseModel):
    enabled: bool = True
    strategy: Literal["exact", "fuzzy", "contains"] = "fuzzy"
    min_score: float = 0.7


class MatchingConfig(BaseModel):
    explicit: list[ExplicitMapping] = []
    auto_match: AutoMatchConfig = AutoMatchConfig()
    issue_patterns: list[str] = []


class ArchFlowConfig(BaseModel):
    jira: JiraConfig = JiraConfig()
    github: GitHubConfig = GitHubConfig()
    gdrive: GDriveConfig = GDriveConfig()
    matching: MatchingConfig = MatchingConfig()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def resolve_config_path(path: str | None = None) -> str | None:
    """Find config file path.

    Resolution order:
    1. Explicit path argument
    2. ARCHFLOW_CONFIG_PATH env var
    3. ./archflow.config.yml (cwd)
    4. ~/.archflow/config.yml (home)
    """
    if path and Path(path).exists():
        return path

    env_path = os.environ.get("ARCHFLOW_CONFIG_PATH", "")
    if env_path and Path(env_path).exists():
        return env_path

    cwd_default = Path("archflow.config.yml")
    if cwd_default.exists():
        return str(cwd_default)

    home_default = Path.home() / ".archflow" / "config.yml"
    if home_default.exists():
        return str(home_default)

    return None


def load_config(path: str | None = None) -> ArchFlowConfig:
    """Load config from YAML file.

    Resolution order:
    1. Explicit path argument
    2. ARCHFLOW_CONFIG_PATH env var
    3. ./archflow.config.yml (cwd)
    4. ~/.archflow/config.yml (home)
    5. Empty defaults
    """
    config_path = resolve_config_path(path)

    if config_path:
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return ArchFlowConfig.model_validate(raw)

    return ArchFlowConfig()

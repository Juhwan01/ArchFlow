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


def load_config(path: str | None = None) -> ArchFlowConfig:
    """Load config from YAML file.

    Resolution order:
    1. Explicit path argument
    2. ARCHFLOW_CONFIG_PATH env var
    3. ./archflow.config.yml (cwd)
    4. Empty defaults
    """
    config_path = path or os.environ.get("ARCHFLOW_CONFIG_PATH", "")

    if not config_path:
        default = Path("archflow.config.yml")
        if default.exists():
            config_path = str(default)

    if config_path and Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return ArchFlowConfig.model_validate(raw)

    return ArchFlowConfig()

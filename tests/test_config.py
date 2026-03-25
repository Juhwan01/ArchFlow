"""Tests for config loader."""

import tempfile
from pathlib import Path

from archflow.core.config import ArchFlowConfig, load_config


SAMPLE_YAML = """
jira:
  url: "https://test.atlassian.net"
  projects:
    - "KAN"
    - "FRONT"
  board_id: "1"

github:
  repos:
    - "org/backend"
    - "org/frontend"
  default_branch: "main"

gdrive:
  folder_id: "folder123"
  cache_ttl_minutes: 15

matching:
  explicit:
    - diagram_node: "Auth Service"
      jira_component: "auth"
      jira_labels: ["authentication"]
      github_path_prefix: "src/auth/"
  auto_match:
    enabled: true
    strategy: "fuzzy"
    min_score: 0.8
  issue_patterns:
    - "(?i)KAN-\\\\d+"
"""


class TestConfigLoading:
    def test_loads_from_yaml_file(self, tmp_path: Path):
        config_file = tmp_path / "archflow.config.yml"
        config_file.write_text(SAMPLE_YAML)
        config = load_config(str(config_file))

        assert config.jira.url == "https://test.atlassian.net"
        assert config.jira.projects == ["KAN", "FRONT"]
        assert config.github.repos == ["org/backend", "org/frontend"]
        assert config.gdrive.folder_id == "folder123"
        assert config.gdrive.cache_ttl_minutes == 15

    def test_loads_matching_config(self, tmp_path: Path):
        config_file = tmp_path / "archflow.config.yml"
        config_file.write_text(SAMPLE_YAML)
        config = load_config(str(config_file))

        assert len(config.matching.explicit) == 1
        mapping = config.matching.explicit[0]
        assert mapping.diagram_node == "Auth Service"
        assert mapping.jira_component == "auth"
        assert mapping.github_path_prefix == "src/auth/"
        assert config.matching.auto_match.min_score == 0.8

    def test_returns_defaults_when_no_file(self):
        config = load_config("/nonexistent/path.yml")
        assert isinstance(config, ArchFlowConfig)
        assert config.jira.projects == []
        assert config.github.repos == []

    def test_handles_partial_config(self, tmp_path: Path):
        config_file = tmp_path / "archflow.config.yml"
        config_file.write_text("jira:\n  url: https://test.atlassian.net\n")
        config = load_config(str(config_file))
        assert config.jira.url == "https://test.atlassian.net"
        assert config.github.repos == []
        assert config.matching.auto_match.enabled is True

    def test_env_var_config_path(self, tmp_path: Path, monkeypatch):
        config_file = tmp_path / "custom.yml"
        config_file.write_text(SAMPLE_YAML)
        monkeypatch.setenv("ARCHFLOW_CONFIG_PATH", str(config_file))
        config = load_config()
        assert config.jira.url == "https://test.atlassian.net"

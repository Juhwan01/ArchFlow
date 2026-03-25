"""Tests for cross-source matching engine."""

from archflow.core.config import ArchFlowConfig, AutoMatchConfig, ExplicitMapping, MatchingConfig
from archflow.core.matcher import Matcher


def _make_config(**kwargs) -> ArchFlowConfig:
    return ArchFlowConfig(matching=MatchingConfig(**kwargs))


class TestIssueKeyExtraction:
    def test_finds_standard_keys(self):
        matcher = Matcher(_make_config())
        keys = matcher.find_issue_keys_in_text("Fixed KAN-123 and FRONT-45")
        assert "KAN-123" in keys
        assert "FRONT-45" in keys

    def test_finds_keys_with_custom_pattern(self):
        config = _make_config(issue_patterns=[r"(?i)KAN-\d+"])
        matcher = Matcher(config)
        keys = matcher.find_issue_keys_in_text("branch: feature/kan-99-auth")
        assert "kan-99" in keys

    def test_no_duplicates(self):
        matcher = Matcher(_make_config())
        keys = matcher.find_issue_keys_in_text("KAN-1 KAN-1 KAN-1")
        assert keys == ["KAN-1"]

    def test_no_keys_found(self):
        matcher = Matcher(_make_config())
        keys = matcher.find_issue_keys_in_text("No issue references here")
        assert keys == []


class TestExplicitMapping:
    def test_finds_explicit_mapping(self):
        config = _make_config(
            explicit=[
                ExplicitMapping(
                    diagram_node="Auth Service",
                    jira_component="auth",
                    jira_labels=["authentication"],
                    github_path_prefix="src/auth/",
                )
            ]
        )
        matcher = Matcher(config)
        mapping = matcher.match_node_to_jira("Auth Service")
        assert mapping is not None
        assert mapping.jira_component == "auth"

    def test_case_insensitive(self):
        config = _make_config(
            explicit=[ExplicitMapping(diagram_node="API Gateway", jira_component="api")]
        )
        matcher = Matcher(config)
        assert matcher.match_node_to_jira("api gateway") is not None

    def test_no_mapping(self):
        matcher = Matcher(_make_config())
        assert matcher.match_node_to_jira("Unknown Node") is None


class TestFuzzyMatching:
    def test_fuzzy_match(self):
        config = _make_config(
            auto_match=AutoMatchConfig(enabled=True, strategy="fuzzy", min_score=0.5)
        )
        matcher = Matcher(config)
        result = matcher.fuzzy_match_node_to_component(
            "Auth Service", ["auth-service", "api-gateway", "database"]
        )
        assert result == "auth-service"

    def test_exact_strategy(self):
        config = _make_config(
            auto_match=AutoMatchConfig(enabled=True, strategy="exact", min_score=0.0)
        )
        matcher = Matcher(config)
        result = matcher.fuzzy_match_node_to_component(
            "database", ["Database", "api"]
        )
        assert result == "Database"

    def test_contains_strategy(self):
        config = _make_config(
            auto_match=AutoMatchConfig(enabled=True, strategy="contains", min_score=0.0)
        )
        matcher = Matcher(config)
        result = matcher.fuzzy_match_node_to_component(
            "Auth", ["authentication", "api"]
        )
        assert result == "authentication"

    def test_below_threshold(self):
        config = _make_config(
            auto_match=AutoMatchConfig(enabled=True, strategy="fuzzy", min_score=0.99)
        )
        matcher = Matcher(config)
        result = matcher.fuzzy_match_node_to_component(
            "XYZ Service", ["authentication"]
        )
        assert result is None

    def test_disabled(self):
        config = _make_config(
            auto_match=AutoMatchConfig(enabled=False)
        )
        matcher = Matcher(config)
        result = matcher.fuzzy_match_node_to_component("Auth", ["authentication"])
        assert result is None


class TestGitHubPathMapping:
    def test_finds_github_path(self):
        config = _make_config(
            explicit=[
                ExplicitMapping(
                    diagram_node="Auth Service",
                    github_path_prefix="src/auth/",
                )
            ]
        )
        matcher = Matcher(config)
        assert matcher.match_node_to_github_path("Auth Service") == "src/auth/"

    def test_no_path(self):
        matcher = Matcher(_make_config())
        assert matcher.match_node_to_github_path("Unknown") is None

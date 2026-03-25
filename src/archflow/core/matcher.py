"""Cross-source matching engine: links Jira issues ↔ GitHub PRs ↔ Diagram nodes."""

from __future__ import annotations

import difflib
import re
from typing import Any

from archflow.core.config import ArchFlowConfig, ExplicitMapping


class Matcher:
    """Matches data across Jira, GitHub, and Draw.io sources."""

    def __init__(self, config: ArchFlowConfig) -> None:
        self._config = config
        self._explicit = {m.diagram_node.lower(): m for m in config.matching.explicit}
        self._issue_patterns = [
            re.compile(p) for p in config.matching.issue_patterns
        ] if config.matching.issue_patterns else []

    def find_issue_keys_in_text(self, text: str) -> list[str]:
        """Extract Jira issue keys from text using configured patterns."""
        if not self._issue_patterns:
            fallback = re.compile(r"[A-Z][A-Z0-9]+-\d+")
            return list(set(fallback.findall(text)))

        keys: list[str] = []
        for pattern in self._issue_patterns:
            keys.extend(pattern.findall(text))
        return list(set(keys))

    def match_node_to_jira(self, node_label: str) -> ExplicitMapping | None:
        """Find explicit mapping for a diagram node label."""
        return self._explicit.get(node_label.lower())

    def fuzzy_match_node_to_component(
        self,
        node_label: str,
        components: list[str],
    ) -> str | None:
        """Fuzzy match a diagram node label to a Jira component name."""
        if not self._config.matching.auto_match.enabled:
            return None

        strategy = self._config.matching.auto_match.strategy
        threshold = self._config.matching.auto_match.min_score

        best_match: str | None = None
        best_score = 0.0

        for comp in components:
            if strategy == "exact":
                if node_label.lower() == comp.lower():
                    return comp
            elif strategy == "contains":
                if node_label.lower() in comp.lower() or comp.lower() in node_label.lower():
                    return comp
            else:
                score = difflib.SequenceMatcher(
                    None, node_label.lower(), comp.lower()
                ).ratio()
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = comp

        return best_match

    def match_node_to_github_path(self, node_label: str) -> str | None:
        """Find GitHub path prefix for a diagram node via explicit mapping."""
        mapping = self.match_node_to_jira(node_label)
        if mapping and mapping.github_path_prefix:
            return mapping.github_path_prefix
        return None

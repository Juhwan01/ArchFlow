"""Unified search MCP tool."""

from __future__ import annotations

from typing import Any


def register_search_tools(mcp, get_providers) -> None:  # noqa: ANN001
    """Register unified search tool."""

    @mcp.tool()
    async def archflow_search(
        query: str,
        sources: list[str] | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """Jira + GitHub + 다이어그램 통합 검색. 모든 소스에서 한번에 검색.

        Args:
            query: 검색어 (예: "인증", "Redis", "payment")
            sources: 검색할 소스 목록 (["jira", "github", "drawio"]), 미지정 시 전체
        """
        jira, github, drawio, _, config = get_providers(ctx)
        active_sources = sources or ["jira", "github", "drawio"]
        results: dict[str, Any] = {"query": query}

        if "jira" in active_sources:
            projects = config.jira.projects
            jira_results: list[dict[str, Any]] = []
            for pk in projects:
                search_result = await jira.search(
                    f'project = {pk} AND text ~ "{query}"', max_results=10
                )
                if isinstance(search_result, dict) and "issues" in search_result:
                    jira_results.extend(search_result["issues"])
            results["jira"] = {"total": len(jira_results), "issues": jira_results}

        if "github" in active_sources:
            repos = config.github.repos
            gh_results: list[dict[str, Any]] = []
            for r in repos:
                code = await github.search_code(r, query)
                if isinstance(code, dict) and "files" in code:
                    for f in code["files"]:
                        f["repo"] = r
                    gh_results.extend(code["files"])
            results["github"] = {"total": len(gh_results), "files": gh_results}

        if "drawio" in active_sources:
            nodes = await drawio.search_nodes(query)
            results["drawio"] = {"total": len(nodes), "nodes": nodes}

        return results

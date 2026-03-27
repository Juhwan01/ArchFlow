"""GitHub MCP tools registration."""

from __future__ import annotations

from typing import Any

from fastmcp import Context


def register_github_tools(mcp, get_github) -> None:  # noqa: ANN001
    """Register all GitHub tools on the MCP server."""

    @mcp.tool()
    async def archflow_github_get_pr(
        repo: str,
        pr_number: int,
        ctx: Context,
    ) -> dict[str, Any]:
        """GitHub PR 상세 조회 (diff stats, 리뷰, 연결 이슈).

        Args:
            repo: GitHub 레포 (예: org/repo-name)
            pr_number: PR 번호
        """
        gh = get_github(ctx)
        return await gh.get_pr(repo, pr_number)

    @mcp.tool()
    async def archflow_github_list_prs(
        repo: str,
        ctx: Context,
        state: str = "open",
        author: str | None = None,
        head: str | None = None,
    ) -> dict[str, Any]:
        """GitHub PR 목록 조회 (필터링 가능).

        Args:
            repo: GitHub 레포 (예: org/repo-name)
            state: PR 상태 (open/closed/all, 기본: open)
            author: 작성자로 필터링
            head: 브랜치명으로 필터링
        """
        gh = get_github(ctx)
        return await gh.list_prs(repo, state, author, head)

    @mcp.tool()
    async def archflow_github_pr_for_issue(
        repo: str,
        issue_key: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Jira 이슈 키와 관련된 GitHub PR 찾기 (제목, 브랜치, 본문에서 검색).

        Args:
            repo: GitHub 레포 (예: org/repo-name)
            issue_key: Jira 이슈 키 (예: KAN-123)
        """
        gh = get_github(ctx)
        return await gh.pr_for_issue(repo, issue_key)

    @mcp.tool()
    async def archflow_github_recent_commits(
        repo: str,
        ctx: Context,
        branch: str | None = None,
        since_days: int = 7,
    ) -> dict[str, Any]:
        """최근 커밋 목록 조회.

        Args:
            repo: GitHub 레포 (예: org/repo-name)
            branch: 브랜치명 (미지정 시 기본 브랜치)
            since_days: 조회 기간 (기본 7일)
        """
        gh = get_github(ctx)
        return await gh.recent_commits(repo, branch, since_days)

    @mcp.tool()
    async def archflow_github_search_code(
        repo: str,
        query: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """GitHub 레포에서 코드 검색.

        Args:
            repo: GitHub 레포 (예: org/repo-name)
            query: 검색어
        """
        gh = get_github(ctx)
        return await gh.search_code(repo, query)

    @mcp.tool()
    async def archflow_github_repo_overview(
        repo: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """GitHub 레포 요약 정보 (언어, 최근 활동, 기여자).

        Args:
            repo: GitHub 레포 (예: org/repo-name)
        """
        gh = get_github(ctx)
        return await gh.repo_overview(repo)

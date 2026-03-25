"""Jira MCP tools registration."""

from __future__ import annotations

from typing import Any


def register_jira_tools(mcp, get_jira) -> None:  # noqa: ANN001
    """Register all Jira tools on the MCP server.

    Args:
        mcp: FastMCP instance
        get_jira: Callable that extracts JiraProvider from context
    """

    @mcp.tool()
    async def archflow_jira_get_issue(
        issue_key: str,
        ctx=None,
    ) -> dict[str, Any]:
        """Jira 이슈 상세 조회 (댓글, 링크, 서브태스크 포함).

        Args:
            issue_key: Jira 이슈 키 (예: KAN-123)
        """
        jira = get_jira(ctx)
        return await jira.get_issue(issue_key)

    @mcp.tool()
    async def archflow_jira_sprint_status(
        project_key: str,
        board_id: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """현재 스프린트의 이슈를 상태별(To Do/In Progress/Done)로 그룹핑하여 조회.

        Args:
            project_key: Jira 프로젝트 키 (예: KAN)
            board_id: 보드 ID (미지정 시 프로젝트의 첫 번째 보드 사용)
        """
        jira = get_jira(ctx)
        return await jira.sprint_status(project_key, board_id)

    @mcp.tool()
    async def archflow_jira_search(
        jql: str,
        max_results: int = 50,
        ctx=None,
    ) -> dict[str, Any]:
        """JQL로 Jira 이슈 검색.

        Args:
            jql: JQL 쿼리 문자열 (예: 'project = KAN AND status = "To Do"')
            max_results: 최대 결과 수 (기본 50, 최대 100)
        """
        jira = get_jira(ctx)
        return await jira.search(jql, max_results)

    @mcp.tool()
    async def archflow_jira_user_workload(
        user_name: str,
        project_key: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """특정 사용자에게 할당된 이슈 현황 조회.

        Args:
            user_name: 사용자 이름 또는 계정 ID
            project_key: 특정 프로젝트로 필터링 (선택)
        """
        jira = get_jira(ctx)
        return await jira.user_workload(user_name, project_key)

    @mcp.tool()
    async def archflow_jira_component_status(
        component_name: str,
        project_key: str,
        ctx=None,
    ) -> dict[str, Any]:
        """Jira 컴포넌트별 이슈 진행률 조회.

        Args:
            component_name: 컴포넌트 이름 (예: authentication)
            project_key: 프로젝트 키 (예: KAN)
        """
        jira = get_jira(ctx)
        return await jira.component_status(component_name, project_key)

    @mcp.tool()
    async def archflow_jira_recent_activity(
        project_key: str,
        days: int = 7,
        ctx=None,
    ) -> dict[str, Any]:
        """최근 N일간 업데이트된 이슈 목록.

        Args:
            project_key: 프로젝트 키 (예: KAN)
            days: 조회 기간 (기본 7일)
        """
        jira = get_jira(ctx)
        return await jira.recent_activity(project_key, days)

    @mcp.tool()
    async def archflow_jira_epic_progress(
        epic_key: str,
        ctx=None,
    ) -> dict[str, Any]:
        """에픽의 하위 이슈와 완료율 조회.

        Args:
            epic_key: 에픽 이슈 키 (예: KAN-10)
        """
        jira = get_jira(ctx)
        return await jira.epic_progress(epic_key)

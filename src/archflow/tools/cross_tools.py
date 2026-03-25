"""Cross-source intelligence MCP tools."""

from __future__ import annotations

from typing import Any


def register_cross_tools(mcp, get_providers) -> None:  # noqa: ANN001
    """Register cross-source tools.

    Args:
        mcp: FastMCP instance
        get_providers: Callable returning (jira, github, drawio, matcher, config) tuple
    """

    @mcp.tool()
    async def archflow_trace_issue(
        issue_key: str,
        repo: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """Jira 이슈 → 관련 PR + 코드 위치 + 아키텍처 다이어그램 노드를 추적.

        Args:
            issue_key: Jira 이슈 키 (예: KAN-123)
            repo: 특정 GitHub 레포로 한정 (미지정 시 설정된 모든 레포 검색)
        """
        jira, github, drawio, matcher, config = get_providers(ctx)
        result: dict[str, Any] = {"issue_key": issue_key}

        issue = await jira.get_issue(issue_key)
        result["issue"] = issue

        repos = [repo] if repo else config.github.repos
        all_prs: list[dict[str, Any]] = []
        for r in repos:
            pr_result = await github.pr_for_issue(r, issue_key)
            if isinstance(pr_result, dict) and "matching_prs" in pr_result:
                all_prs.extend(pr_result["matching_prs"])
        result["pull_requests"] = all_prs

        components = issue.get("components", []) if isinstance(issue, dict) else []
        labels = issue.get("labels", []) if isinstance(issue, dict) else []
        search_terms = components + labels

        diagram_matches: list[dict[str, Any]] = []
        for term in search_terms:
            nodes = await drawio.search_nodes(term)
            diagram_matches.extend(nodes)
        result["diagram_nodes"] = diagram_matches

        return result

    @mcp.tool()
    async def archflow_trace_component(
        component_name: str,
        project_key: str | None = None,
        repo: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """아키텍처 컴포넌트 → 관련 Jira 이슈 + PR + 다이어그램 연결 관계 추적.

        Args:
            component_name: 컴포넌트 이름 (예: Auth Service)
            project_key: Jira 프로젝트 키 (미지정 시 설정의 첫 번째 프로젝트)
            repo: GitHub 레포 (미지정 시 설정된 모든 레포)
        """
        jira, github, drawio, matcher, config = get_providers(ctx)

        diagram_result = await drawio.node_connections(component_name)

        pk = project_key or (config.jira.projects[0] if config.jira.projects else "")
        jira_result: dict[str, Any] = {}
        if pk:
            mapping = matcher.match_node_to_jira(component_name)
            if mapping and mapping.jira_component:
                jira_result = await jira.component_status(mapping.jira_component, pk)
            else:
                matched_comp = matcher.fuzzy_match_node_to_component(component_name, [])
                if matched_comp:
                    jira_result = await jira.component_status(matched_comp, pk)
                else:
                    jira_result = await jira.search(
                        f'project = {pk} AND text ~ "{component_name}"', max_results=20
                    )

        repos = [repo] if repo else config.github.repos
        github_path = matcher.match_node_to_github_path(component_name)
        code_results: list[dict[str, Any]] = []
        if github_path:
            for r in repos:
                code = await github.search_code(r, f"path:{github_path}")
                if isinstance(code, dict) and "files" in code:
                    code_results.extend(code["files"])

        return {
            "component": component_name,
            "diagram": diagram_result,
            "jira_issues": jira_result,
            "code_files": code_results,
        }

    @mcp.tool()
    async def archflow_project_overview(
        project_key: str,
        repo: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """프로젝트 종합 현황: 스프린트 상태 + 아키텍처 요약 + GitHub 활동.

        Args:
            project_key: Jira 프로젝트 키 (예: KAN)
            repo: GitHub 레포 (미지정 시 설정된 모든 레포)
        """
        jira, github, drawio, _, config = get_providers(ctx)

        sprint = await jira.sprint_status(project_key)
        diagrams = await drawio.list_diagrams()

        repos = [repo] if repo else config.github.repos
        repo_summaries: list[dict[str, Any]] = []
        for r in repos:
            overview = await github.repo_overview(r)
            if isinstance(overview, dict) and "name" in overview:
                repo_summaries.append(overview)

        return {
            "project_key": project_key,
            "sprint": sprint,
            "diagrams": diagrams,
            "repositories": repo_summaries,
        }

    @mcp.tool()
    async def archflow_team_activity(
        project_key: str,
        repo: str | None = None,
        days: int = 7,
        ctx=None,
    ) -> dict[str, Any]:
        """주간 팀 활동 보고서: 누가 뭘 했는지, PR 현황, 이슈 완료 현황.

        Args:
            project_key: Jira 프로젝트 키
            repo: GitHub 레포 (미지정 시 설정된 모든 레포)
            days: 조회 기간 (기본 7일)
        """
        jira, github, _, _, config = get_providers(ctx)

        activity = await jira.recent_activity(project_key, days)

        repos = [repo] if repo else config.github.repos
        all_commits: list[dict[str, Any]] = []
        all_prs: list[dict[str, Any]] = []
        for r in repos:
            commits = await github.recent_commits(r, since_days=days)
            if isinstance(commits, dict) and "commits" in commits:
                all_commits.extend(commits["commits"])
            prs = await github.list_prs(r, state="all")
            if isinstance(prs, dict) and "pull_requests" in prs:
                all_prs.extend(prs["pull_requests"])

        return {
            "project_key": project_key,
            "period_days": days,
            "jira_activity": activity,
            "github_commits": all_commits,
            "github_prs": all_prs,
        }

    @mcp.tool()
    async def archflow_onboarding_context(
        project_key: str,
        repo: str | None = None,
        ctx=None,
    ) -> dict[str, Any]:
        """신규 팀원용 프로젝트 전체 맥락: 구조, 현재 작업, 핵심 인물.

        Args:
            project_key: Jira 프로젝트 키
            repo: GitHub 레포 (미지정 시 설정된 모든 레포)
        """
        jira, github, drawio, _, config = get_providers(ctx)

        sprint = await jira.sprint_status(project_key)
        diagrams_list = await drawio.list_diagrams()

        diagram_details: list[dict[str, Any]] = []
        for d in diagrams_list[:3]:
            detail = await drawio.get_diagram(d["name"])
            diagram_details.extend(detail)

        repos = [repo] if repo else config.github.repos
        repo_overviews: list[dict[str, Any]] = []
        for r in repos:
            overview = await github.repo_overview(r)
            if isinstance(overview, dict) and "name" in overview:
                repo_overviews.append(overview)

        return {
            "project_key": project_key,
            "sprint_status": sprint,
            "architecture": diagram_details,
            "repositories": repo_overviews,
        }

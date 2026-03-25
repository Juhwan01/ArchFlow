"""Jira business logic: format issues, query sprints, user workload."""

from __future__ import annotations

from typing import Any

from archflow.clients.jira_client import JiraClient
from archflow.core.cache import TTLCache
from archflow.core.models import JiraIssue, SprintSummary


def _format_issue(raw: dict[str, Any]) -> JiraIssue:
    """Convert raw Jira API response to JiraIssue model."""
    fields = raw.get("fields", {})
    return JiraIssue(
        key=raw.get("key", ""),
        summary=fields.get("summary", ""),
        status=(fields.get("status") or {}).get("name", ""),
        issue_type=(fields.get("issuetype") or {}).get("name", ""),
        priority=(fields.get("priority") or {}).get("name", ""),
        assignee=(fields.get("assignee") or {}).get("displayName", ""),
        labels=fields.get("labels", []),
        components=[c.get("name", "") for c in fields.get("components", [])],
    )


class JiraProvider:
    """Higher-level Jira operations with caching."""

    def __init__(self, client: JiraClient, cache: TTLCache) -> None:
        self._client = client
        self._cache = cache

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        """Get issue detail with caching."""
        cache_key = f"jira:issue:{issue_key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.get(f"/rest/api/2/issue/{issue_key}")
        if isinstance(result, dict) and "key" in result:
            formatted = _format_issue(result).model_dump()
            fields = result.get("fields", {})
            formatted["description"] = fields.get("description", "")
            formatted["created"] = fields.get("created", "")
            formatted["updated"] = fields.get("updated", "")

            if fields.get("issuelinks"):
                formatted["links"] = [
                    {
                        "type": (link.get("type") or {}).get("name"),
                        "inward": (link.get("inwardIssue") or {}).get("key"),
                        "outward": (link.get("outwardIssue") or {}).get("key"),
                    }
                    for link in fields["issuelinks"]
                ]

            if fields.get("subtasks"):
                formatted["subtasks"] = [
                    {"key": st.get("key"), "summary": st.get("fields", {}).get("summary")}
                    for st in fields["subtasks"]
                ]

            self._cache.set(cache_key, formatted)
            return formatted
        return result

    async def sprint_status(self, project_key: str, board_id: str | None = None) -> dict[str, Any]:
        """Get current sprint issues grouped by status."""
        cache_key = f"jira:sprint:{project_key}:{board_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if not board_id:
            boards = await self._client.get(
                "/rest/agile/1.0/board",
                params={"projectKeyOrId": project_key},
            )
            if isinstance(boards, dict):
                values = boards.get("values", [])
                if values:
                    board_id = str(values[0].get("id", ""))

        if not board_id:
            return {"error": f"No board found for project {project_key}"}

        sprints = await self._client.get(
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params={"state": "active"},
        )

        if not isinstance(sprints, dict) or not sprints.get("values"):
            return {"error": "No active sprint found"}

        sprint = sprints["values"][0]
        sprint_id = sprint.get("id")

        issues_resp = await self._client.get(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            params={"maxResults": 100},
        )

        if not isinstance(issues_resp, dict):
            return {"error": "Failed to fetch sprint issues"}

        issues = [_format_issue(i) for i in issues_resp.get("issues", [])]

        summary = SprintSummary(
            sprint_name=sprint.get("name", ""),
            sprint_state=sprint.get("state", ""),
            total=len(issues),
            done=sum(1 for i in issues if i.status.lower() == "done"),
            in_progress=sum(1 for i in issues if "progress" in i.status.lower()),
            todo=sum(1 for i in issues if i.status.lower() in ("to do", "todo", "open")),
            issues=issues,
        )

        result = summary.model_dump()
        self._cache.set(cache_key, result, ttl=300)
        return result

    async def search(self, jql: str, max_results: int = 50) -> dict[str, Any]:
        """Search issues via JQL with caching."""
        cache_key = f"jira:search:{jql}:{max_results}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.post(
            "/rest/api/3/search/jql",
            json={
                "jql": jql,
                "fields": ["summary", "status", "assignee", "priority", "issuetype", "labels", "components"],
                "maxResults": min(max_results, 100),
            },
        )

        if isinstance(result, dict) and "issues" in result:
            formatted = {
                "total": result.get("total", 0),
                "issues": [_format_issue(i).model_dump() for i in result["issues"]],
            }
            self._cache.set(cache_key, formatted, ttl=120)
            return formatted
        return result

    async def user_workload(self, user_name: str, project_key: str | None = None) -> dict[str, Any]:
        """Get all issues assigned to a user."""
        jql = f'assignee = "{user_name}"'
        if project_key:
            jql += f" AND project = {project_key}"
        jql += " ORDER BY status ASC"
        return await self.search(jql)

    async def component_status(self, component_name: str, project_key: str) -> dict[str, Any]:
        """Get all issues for a component with progress stats."""
        jql = f'project = {project_key} AND component = "{component_name}"'
        result = await self.search(jql, max_results=100)

        if isinstance(result, dict) and "issues" in result:
            issues = result["issues"]
            total = len(issues)
            done = sum(1 for i in issues if i.get("status", "").lower() == "done")
            result["stats"] = {
                "total": total,
                "done": done,
                "done_percent": round(done / total * 100, 1) if total > 0 else 0,
                "remaining": total - done,
            }
        return result

    async def recent_activity(self, project_key: str, days: int = 7) -> dict[str, Any]:
        """Get recently updated issues."""
        jql = f"project = {project_key} AND updated >= -{days}d ORDER BY updated DESC"
        return await self.search(jql, max_results=50)

    async def epic_progress(self, epic_key: str) -> dict[str, Any]:
        """Get epic with all child issues and completion percentage."""
        cache_key = f"jira:epic:{epic_key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        epic = await self.get_issue(epic_key)
        children_result = await self.search(f'parent = {epic_key}', max_results=100)

        if isinstance(children_result, dict) and "issues" in children_result:
            children = children_result["issues"]
            total = len(children)
            done = sum(1 for c in children if c.get("status", "").lower() == "done")
            result = {
                "epic": epic,
                "children": children,
                "stats": {
                    "total": total,
                    "done": done,
                    "done_percent": round(done / total * 100, 1) if total > 0 else 0,
                },
            }
            self._cache.set(cache_key, result, ttl=300)
            return result
        return {"epic": epic, "children": [], "stats": {"total": 0, "done": 0, "done_percent": 0}}

    async def get_dev_status(self, issue_id: str) -> dict[str, Any]:
        """Get development information (PRs, branches) linked to an issue.

        Uses the Jira dev-status API (requires GitHub for Jira app).
        """
        cache_key = f"jira:devstatus:{issue_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.get(
            "/rest/dev-status/latest/issue/summary",
            params={"issueId": issue_id},
        )

        if isinstance(result, dict):
            self._cache.set(cache_key, result, ttl=600)
        return result

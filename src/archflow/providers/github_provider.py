"""GitHub business logic: PRs, commits, code search."""

from __future__ import annotations

from typing import Any

from archflow.clients.github_client import GitHubClient
from archflow.core.cache import TTLCache
from archflow.core.models import CommitSummary, PRSummary


def _format_pr(raw: dict[str, Any], repo: str) -> dict[str, Any]:
    """Convert raw GitHub PR response to PRSummary dict."""
    return PRSummary(
        number=raw.get("number", 0),
        title=raw.get("title", ""),
        state=raw.get("state", ""),
        author=(raw.get("user") or {}).get("login", ""),
        branch=(raw.get("head") or {}).get("ref", ""),
        repo=repo,
        url=raw.get("html_url", ""),
        merged=raw.get("merged", False) or bool(raw.get("merged_at")),
    ).model_dump()


class GitHubProvider:
    """Higher-level GitHub operations with caching."""

    def __init__(self, client: GitHubClient, cache: TTLCache) -> None:
        self._client = client
        self._cache = cache

    async def get_pr(self, repo: str, pr_number: int) -> dict[str, Any]:
        """Get PR detail."""
        cache_key = f"gh:pr:{repo}:{pr_number}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.get(f"/repos/{repo}/pulls/{pr_number}")
        if isinstance(result, dict) and "number" in result:
            formatted = _format_pr(result, repo)
            formatted["body"] = result.get("body", "")
            formatted["additions"] = result.get("additions", 0)
            formatted["deletions"] = result.get("deletions", 0)
            formatted["changed_files"] = result.get("changed_files", 0)
            self._cache.set(cache_key, formatted)
            return formatted
        return result

    async def list_prs(
        self,
        repo: str,
        state: str = "open",
        author: str | None = None,
        head: str | None = None,
    ) -> dict[str, Any]:
        """List PRs with filtering."""
        cache_key = f"gh:prs:{repo}:{state}:{author}:{head}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        params: dict[str, Any] = {"state": state, "per_page": 30}
        if head:
            params["head"] = head

        result = await self._client.get(f"/repos/{repo}/pulls", params=params)

        if isinstance(result, list):
            prs = [_format_pr(pr, repo) for pr in result]
            if author:
                prs = [pr for pr in prs if pr["author"].lower() == author.lower()]
            formatted = {"total": len(prs), "pull_requests": prs}
            self._cache.set(cache_key, formatted, ttl=120)
            return formatted
        return result

    async def pr_for_issue(self, repo: str, issue_key: str) -> dict[str, Any]:
        """Find PRs that reference a Jira issue key.

        Searches PR titles and branch names. Cached per issue key.
        """
        cache_key = f"gh:pr_issue:{repo}:{issue_key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        key_lower = issue_key.lower()

        all_prs = await self._client.get(
            f"/repos/{repo}/pulls",
            params={"state": "all", "per_page": 100},
        )

        if not isinstance(all_prs, list):
            return {"error": "Failed to fetch PRs", "detail": all_prs}

        matching = []
        for pr in all_prs:
            title = (pr.get("title") or "").lower()
            branch = ((pr.get("head") or {}).get("ref") or "").lower()
            body = (pr.get("body") or "").lower()

            if key_lower in title or key_lower in branch or key_lower in body:
                matching.append(_format_pr(pr, repo))

        result = {"issue_key": issue_key, "matching_prs": matching, "total": len(matching)}
        self._cache.set(cache_key, result, ttl=600)
        return result

    async def recent_commits(
        self,
        repo: str,
        branch: str | None = None,
        since_days: int = 7,
    ) -> dict[str, Any]:
        """Get recent commits."""
        cache_key = f"gh:commits:{repo}:{branch}:{since_days}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        params: dict[str, Any] = {"per_page": 30}
        if branch:
            params["sha"] = branch

        result = await self._client.get(f"/repos/{repo}/commits", params=params)

        if isinstance(result, list):
            commits = [
                CommitSummary(
                    sha=c.get("sha", "")[:7],
                    message=(c.get("commit", {}).get("message") or "").split("\n")[0],
                    author=(c.get("commit", {}).get("author") or {}).get("name", ""),
                    date=(c.get("commit", {}).get("author") or {}).get("date", ""),
                    repo=repo,
                ).model_dump()
                for c in result
            ]
            formatted = {"total": len(commits), "commits": commits}
            self._cache.set(cache_key, formatted, ttl=300)
            return formatted
        return result

    async def search_code(self, repo: str, query: str) -> dict[str, Any]:
        """Search code in a repository."""
        cache_key = f"gh:code:{repo}:{query}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.get(
            "/search/code",
            params={"q": f"{query} repo:{repo}", "per_page": 10},
        )

        if isinstance(result, dict) and "items" in result:
            formatted = {
                "total": result.get("total_count", 0),
                "files": [
                    {
                        "path": item.get("path", ""),
                        "name": item.get("name", ""),
                        "url": item.get("html_url", ""),
                    }
                    for item in result["items"]
                ],
            }
            self._cache.set(cache_key, formatted, ttl=600)
            return formatted
        return result

    async def repo_overview(self, repo: str) -> dict[str, Any]:
        """Get repository summary."""
        cache_key = f"gh:repo:{repo}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = await self._client.get(f"/repos/{repo}")

        if isinstance(result, dict) and "full_name" in result:
            formatted = {
                "name": result.get("full_name"),
                "description": result.get("description", ""),
                "language": result.get("language", ""),
                "stars": result.get("stargazers_count", 0),
                "open_issues": result.get("open_issues_count", 0),
                "default_branch": result.get("default_branch", "main"),
                "updated_at": result.get("updated_at", ""),
                "url": result.get("html_url", ""),
            }
            self._cache.set(cache_key, formatted, ttl=1800)
            return formatted
        return result

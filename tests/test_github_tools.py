"""Tests for GitHub provider."""

from unittest.mock import AsyncMock

import pytest

from archflow.core.cache import TTLCache
from archflow.providers.github_provider import GitHubProvider


MOCK_PR = {
    "number": 42,
    "title": "KAN-123: Add OAuth login",
    "state": "open",
    "user": {"login": "jung"},
    "head": {"ref": "feature/KAN-123-auth"},
    "html_url": "https://github.com/org/repo/pull/42",
    "merged": False,
    "merged_at": None,
    "body": "Implements KAN-123 OAuth flow",
    "additions": 150,
    "deletions": 20,
    "changed_files": 5,
}

MOCK_COMMIT = {
    "sha": "abc1234567890",
    "commit": {
        "message": "feat(KAN-123): add login page\n\nDetailed description",
        "author": {"name": "Jung", "date": "2026-03-25T10:00:00Z"},
    },
}

MOCK_REPO = {
    "full_name": "org/backend",
    "description": "Backend API",
    "language": "Python",
    "stargazers_count": 10,
    "open_issues_count": 5,
    "default_branch": "main",
    "updated_at": "2026-03-25T10:00:00Z",
    "html_url": "https://github.com/org/backend",
}


class TestGitHubProvider:
    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        client.available = True
        return client

    @pytest.fixture
    def provider(self, mock_client):
        return GitHubProvider(mock_client, TTLCache(default_ttl=60))

    @pytest.mark.asyncio
    async def test_get_pr(self, provider, mock_client):
        mock_client.get.return_value = MOCK_PR
        result = await provider.get_pr("org/repo", 42)
        assert result["number"] == 42
        assert result["title"] == "KAN-123: Add OAuth login"
        assert result["author"] == "jung"

    @pytest.mark.asyncio
    async def test_get_pr_caches(self, provider, mock_client):
        mock_client.get.return_value = MOCK_PR
        await provider.get_pr("org/repo", 42)
        await provider.get_pr("org/repo", 42)
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_pr_for_issue_finds_by_title(self, provider, mock_client):
        mock_client.get.return_value = [MOCK_PR]
        result = await provider.pr_for_issue("org/repo", "KAN-123")
        assert result["total"] == 1
        assert result["matching_prs"][0]["number"] == 42

    @pytest.mark.asyncio
    async def test_pr_for_issue_no_match(self, provider, mock_client):
        mock_client.get.return_value = [MOCK_PR]
        result = await provider.pr_for_issue("org/repo", "KAN-999")
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_recent_commits(self, provider, mock_client):
        mock_client.get.return_value = [MOCK_COMMIT]
        result = await provider.recent_commits("org/repo")
        assert result["total"] == 1
        assert result["commits"][0]["message"] == "feat(KAN-123): add login page"
        assert result["commits"][0]["sha"] == "abc1234"

    @pytest.mark.asyncio
    async def test_search_code(self, provider, mock_client):
        mock_client.get.return_value = {
            "total_count": 2,
            "items": [
                {"path": "src/auth/login.py", "name": "login.py", "html_url": "https://..."},
                {"path": "tests/test_auth.py", "name": "test_auth.py", "html_url": "https://..."},
            ],
        }
        result = await provider.search_code("org/repo", "OAuth")
        assert result["total"] == 2
        assert result["files"][0]["path"] == "src/auth/login.py"

    @pytest.mark.asyncio
    async def test_repo_overview(self, provider, mock_client):
        mock_client.get.return_value = MOCK_REPO
        result = await provider.repo_overview("org/backend")
        assert result["name"] == "org/backend"
        assert result["language"] == "Python"

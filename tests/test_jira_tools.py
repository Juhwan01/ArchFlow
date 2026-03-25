"""Tests for Jira provider and tools."""

from unittest.mock import AsyncMock

import pytest

from archflow.core.cache import TTLCache
from archflow.providers.jira_provider import JiraProvider, _format_issue


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_ISSUE_RAW = {
    "key": "KAN-123",
    "fields": {
        "summary": "Add OAuth login",
        "status": {"name": "In Progress"},
        "issuetype": {"name": "Story"},
        "priority": {"name": "High"},
        "assignee": {"displayName": "Jung"},
        "labels": ["auth", "backend"],
        "components": [{"name": "authentication"}],
        "description": "Implement OAuth 2.0 login flow",
        "created": "2026-03-20T10:00:00",
        "updated": "2026-03-25T14:00:00",
        "issuelinks": [],
        "subtasks": [],
    },
}


class TestFormatIssue:
    def test_formats_basic_fields(self):
        issue = _format_issue(MOCK_ISSUE_RAW)
        assert issue.key == "KAN-123"
        assert issue.summary == "Add OAuth login"
        assert issue.status == "In Progress"
        assert issue.issue_type == "Story"
        assert issue.priority == "High"
        assert issue.assignee == "Jung"

    def test_formats_labels_and_components(self):
        issue = _format_issue(MOCK_ISSUE_RAW)
        assert issue.labels == ["auth", "backend"]
        assert issue.components == ["authentication"]

    def test_handles_missing_fields(self):
        raw = {"key": "KAN-1", "fields": {"summary": "Minimal"}}
        issue = _format_issue(raw)
        assert issue.key == "KAN-1"
        assert issue.status == ""
        assert issue.assignee == ""


class TestJiraProvider:
    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        client.available = True
        return client

    @pytest.fixture
    def provider(self, mock_client):
        cache = TTLCache(default_ttl=60)
        return JiraProvider(mock_client, cache)

    @pytest.mark.asyncio
    async def test_get_issue(self, provider, mock_client):
        mock_client.get.return_value = MOCK_ISSUE_RAW
        result = await provider.get_issue("KAN-123")
        assert result["key"] == "KAN-123"
        assert result["summary"] == "Add OAuth login"
        mock_client.get.assert_called_once_with("/rest/api/2/issue/KAN-123")

    @pytest.mark.asyncio
    async def test_get_issue_caches_result(self, provider, mock_client):
        mock_client.get.return_value = MOCK_ISSUE_RAW
        await provider.get_issue("KAN-123")
        await provider.get_issue("KAN-123")
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_search(self, provider, mock_client):
        mock_client.post.return_value = {
            "total": 2,
            "issues": [
                MOCK_ISSUE_RAW,
                {**MOCK_ISSUE_RAW, "key": "KAN-124", "fields": {**MOCK_ISSUE_RAW["fields"], "summary": "Fix bug"}},
            ],
        }
        result = await provider.search("project = KAN")
        assert result["total"] == 2
        assert len(result["issues"]) == 2

    @pytest.mark.asyncio
    async def test_user_workload(self, provider, mock_client):
        mock_client.post.return_value = {
            "total": 1,
            "issues": [MOCK_ISSUE_RAW],
        }
        result = await provider.user_workload("Jung", "KAN")
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_component_status_with_stats(self, provider, mock_client):
        done_issue = {
            **MOCK_ISSUE_RAW,
            "key": "KAN-200",
            "fields": {**MOCK_ISSUE_RAW["fields"], "status": {"name": "Done"}},
        }
        mock_client.post.return_value = {
            "total": 2,
            "issues": [MOCK_ISSUE_RAW, done_issue],
        }
        result = await provider.component_status("authentication", "KAN")
        assert result["stats"]["total"] == 2
        assert result["stats"]["done"] == 1
        assert result["stats"]["done_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_recent_activity(self, provider, mock_client):
        mock_client.post.return_value = {
            "total": 1,
            "issues": [MOCK_ISSUE_RAW],
        }
        result = await provider.recent_activity("KAN", days=3)
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_dev_status(self, provider, mock_client):
        mock_client.get.return_value = {
            "summary": {"pullrequest": {"overall": {"count": 1}}}
        }
        result = await provider.get_dev_status("10001")
        assert "summary" in result

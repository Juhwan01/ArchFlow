"""Shared pydantic models for ArchFlow."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Draw.io / Architecture Diagram
# ---------------------------------------------------------------------------


class DiagramNode(BaseModel):
    """A node in a draw.io diagram."""

    id: str
    label: str
    style: str = ""
    parent_id: str | None = None


class DiagramEdge(BaseModel):
    """An edge (connection) in a draw.io diagram."""

    id: str
    source_id: str
    target_id: str
    label: str = ""


class Diagram(BaseModel):
    """A parsed draw.io diagram with nodes and edges."""

    name: str
    file_id: str = ""
    nodes: list[DiagramNode] = []
    edges: list[DiagramEdge] = []


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------


class JiraIssue(BaseModel):
    """Formatted Jira issue."""

    key: str
    summary: str
    status: str = ""
    issue_type: str = ""
    priority: str = ""
    assignee: str = ""
    labels: list[str] = []
    components: list[str] = []


class SprintSummary(BaseModel):
    """Sprint status summary."""

    sprint_name: str
    sprint_state: str = ""
    total: int = 0
    done: int = 0
    in_progress: int = 0
    todo: int = 0
    issues: list[JiraIssue] = []


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


class PRSummary(BaseModel):
    """GitHub Pull Request summary."""

    number: int
    title: str
    state: str = ""
    author: str = ""
    branch: str = ""
    repo: str = ""
    url: str = ""
    merged: bool = False


class CommitSummary(BaseModel):
    """GitHub commit summary."""

    sha: str
    message: str
    author: str = ""
    date: str = ""
    repo: str = ""


# ---------------------------------------------------------------------------
# Cross-source
# ---------------------------------------------------------------------------


class TraceResult(BaseModel):
    """Result of tracing an issue across all sources."""

    issue: JiraIssue | None = None
    pull_requests: list[PRSummary] = []
    diagram_nodes: list[DiagramNode] = []
    diagram_edges: list[DiagramEdge] = []

"""ArchFlow MCP Server - Context Hub for Jira + GitHub + Draw.io."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastmcp import Context, FastMCP

from archflow.clients.gdrive_client import GDriveClient
from archflow.clients.github_client import GitHubClient
from archflow.clients.jira_client import JiraClient
from archflow.core.cache import TTLCache
from archflow.core.config import ArchFlowConfig, load_config
from archflow.core.matcher import Matcher
from archflow.providers.drawio_provider import DrawioProvider
from archflow.providers.github_provider import GitHubProvider
from archflow.providers.jira_provider import JiraProvider
from archflow.tools.cross_tools import register_cross_tools
from archflow.tools.drawio_tools import register_drawio_tools
from archflow.tools.github_tools import register_github_tools
from archflow.tools.jira_tools import register_jira_tools
from archflow.tools.search_tools import register_search_tools


@dataclass
class AppContext:
    jira: JiraProvider
    github: GitHubProvider
    drawio: DrawioProvider
    matcher: Matcher
    config: ArchFlowConfig
    cache: TTLCache


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    config = load_config()
    cache = TTLCache(default_ttl=config.gdrive.cache_ttl_minutes * 60)

    jira_client = JiraClient()
    github_client = GitHubClient()
    gdrive_client = GDriveClient()

    jira = JiraProvider(jira_client, cache)
    github = GitHubProvider(github_client, cache)
    drawio = DrawioProvider(gdrive_client, cache, folder_id=config.gdrive.folder_id)
    matcher = Matcher(config)

    try:
        yield AppContext(
            jira=jira,
            github=github,
            drawio=drawio,
            matcher=matcher,
            config=config,
            cache=cache,
        )
    finally:
        await jira_client.close()
        await github_client.close()
        await gdrive_client.close()


mcp = FastMCP(
    "ArchFlow",
    instructions=(
        "Context Hub MCP Server - Jira, GitHub, Draw.io 통합 조회 도구. "
        "프로젝트 현황, 이슈-PR-코드 추적, 아키텍처 다이어그램 탐색, "
        "팀 활동 보고서, 신규 팀원 온보딩 등을 지원합니다."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Context extractors
# ---------------------------------------------------------------------------


def _get_app(ctx: Context) -> AppContext:
    return ctx.request_context.lifespan_context


def _get_jira(ctx: Context) -> JiraProvider:
    return _get_app(ctx).jira


def _get_github(ctx: Context) -> GitHubProvider:
    return _get_app(ctx).github


def _get_drawio(ctx: Context) -> DrawioProvider:
    return _get_app(ctx).drawio


def _get_providers(ctx: Context):
    app = _get_app(ctx)
    return app.jira, app.github, app.drawio, app.matcher, app.config


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------

register_jira_tools(mcp, _get_jira)
register_github_tools(mcp, _get_github)
register_drawio_tools(mcp, _get_drawio)
register_cross_tools(mcp, _get_providers)
register_search_tools(mcp, _get_providers)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the ArchFlow MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

"""Draw.io MCP tools registration."""

from __future__ import annotations

from typing import Any

from fastmcp import Context


def register_drawio_tools(mcp, get_drawio) -> None:  # noqa: ANN001
    """Register all Draw.io tools on the MCP server."""

    @mcp.tool()
    async def archflow_drawio_list_diagrams(
        ctx: Context,
    ) -> list[dict[str, Any]]:
        """Google Drive 폴더의 .drawio 파일 목록 조회."""
        drawio = get_drawio(ctx)
        return await drawio.list_diagrams()

    @mcp.tool()
    async def archflow_drawio_get_diagram(
        file_name: str,
        ctx: Context,
    ) -> list[dict[str, Any]]:
        """특정 .drawio 파일의 모든 노드와 연결 관계를 파싱하여 반환.

        Args:
            file_name: .drawio 파일 이름 (예: system-architecture.drawio)
        """
        drawio = get_drawio(ctx)
        return await drawio.get_diagram(file_name)

    @mcp.tool()
    async def archflow_drawio_search_nodes(
        query: str,
        ctx: Context,
    ) -> list[dict[str, Any]]:
        """모든 다이어그램에서 노드 라벨로 검색.

        Args:
            query: 검색어 (예: Auth, Database, API)
        """
        drawio = get_drawio(ctx)
        return await drawio.search_nodes(query)

    @mcp.tool()
    async def archflow_drawio_node_connections(
        node_label: str,
        ctx: Context,
        file_name: str | None = None,
    ) -> dict[str, Any]:
        """특정 노드의 모든 연결 관계 조회 (인바운드/아웃바운드).

        Args:
            node_label: 노드 라벨 (예: Auth Service)
            file_name: 특정 파일로 한정 (선택)
        """
        drawio = get_drawio(ctx)
        return await drawio.node_connections(node_label, file_name)

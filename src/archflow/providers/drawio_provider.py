"""Draw.io provider: fetch from Google Drive, parse, cache, search."""

from __future__ import annotations

from typing import Any

from archflow.clients.gdrive_client import GDriveClient
from archflow.core.cache import TTLCache
from archflow.core.models import Diagram
from archflow.providers.drawio_parser import parse_drawio_xml


class DrawioProvider:
    """Orchestrates Google Drive file fetching and draw.io parsing with caching."""

    def __init__(self, client: GDriveClient, cache: TTLCache, folder_id: str = "") -> None:
        self._client = client
        self._cache = cache
        self._folder_id = folder_id

    async def list_diagrams(self) -> list[dict[str, Any]]:
        """List all .drawio files from Google Drive folder."""
        cache_key = "drawio:files"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        files = await self._client.list_drawio_files(self._folder_id)
        result = [
            {
                "id": f.get("id", ""),
                "name": f.get("name", ""),
                "modified": f.get("modifiedTime", ""),
            }
            for f in files
        ]
        self._cache.set(cache_key, result, ttl=600)
        return result

    async def get_diagram(self, file_name: str) -> list[dict[str, Any]]:
        """Fetch and parse a specific .drawio file by name."""
        cache_key = f"drawio:diagram:{file_name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        files = await self.list_diagrams()
        target = next((f for f in files if f["name"] == file_name), None)

        if not target:
            return [{"error": f"File '{file_name}' not found"}]

        content = await self._client.download_file(target["id"])
        if not content:
            return [{"error": f"Failed to download '{file_name}'"}]

        diagrams = parse_drawio_xml(content, name=file_name)
        result = [d.model_dump() for d in diagrams]
        self._cache.set(cache_key, result, ttl=1800)
        return result

    async def _get_all_diagrams(self) -> list[Diagram]:
        """Fetch and parse all .drawio files (cached)."""
        cache_key = "drawio:all_parsed"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        files = await self.list_diagrams()
        all_diagrams: list[Diagram] = []

        for f in files:
            content = await self._client.download_file(f["id"])
            if content:
                parsed = parse_drawio_xml(content, name=f["name"])
                for d in parsed:
                    d.file_id = f["id"]
                all_diagrams.extend(parsed)

        self._cache.set(cache_key, all_diagrams, ttl=1800)
        return all_diagrams

    async def search_nodes(self, query: str) -> list[dict[str, Any]]:
        """Search for nodes by label across all diagrams."""
        cache_key = f"drawio:search:{query.lower()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        all_diagrams = await self._get_all_diagrams()
        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        for diagram in all_diagrams:
            for node in diagram.nodes:
                if query_lower in node.label.lower():
                    connected_edges = [
                        e.model_dump() for e in diagram.edges
                        if e.source_id == node.id or e.target_id == node.id
                    ]
                    results.append({
                        "node": node.model_dump(),
                        "diagram_name": diagram.name,
                        "connections": connected_edges,
                    })

        self._cache.set(cache_key, results, ttl=1800)
        return results

    async def node_connections(self, node_label: str, file_name: str | None = None) -> dict[str, Any]:
        """Get a specific node and all its direct connections."""
        all_diagrams = await self._get_all_diagrams()

        for diagram in all_diagrams:
            if file_name and diagram.name != file_name:
                continue

            target_node = next(
                (n for n in diagram.nodes if n.label.lower() == node_label.lower()),
                None,
            )
            if not target_node:
                continue

            node_map = {n.id: n.label for n in diagram.nodes}
            inbound = []
            outbound = []

            for edge in diagram.edges:
                if edge.target_id == target_node.id:
                    inbound.append({
                        "from": node_map.get(edge.source_id, edge.source_id),
                        "label": edge.label,
                    })
                elif edge.source_id == target_node.id:
                    outbound.append({
                        "to": node_map.get(edge.target_id, edge.target_id),
                        "label": edge.label,
                    })

            return {
                "node": target_node.model_dump(),
                "diagram_name": diagram.name,
                "inbound": inbound,
                "outbound": outbound,
            }

        return {"error": f"Node '{node_label}' not found"}

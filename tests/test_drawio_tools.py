"""Tests for Draw.io provider (with mocked Google Drive client)."""

from unittest.mock import AsyncMock

import pytest

from archflow.core.cache import TTLCache
from archflow.providers.drawio_provider import DrawioProvider


SAMPLE_DRAWIO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram name="Architecture">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="API Gateway" style="rounded=1;" vertex="1" parent="1"/>
        <mxCell id="3" value="Auth Service" style="rounded=1;" vertex="1" parent="1"/>
        <mxCell id="4" value="Database" style="shape=cylinder;" vertex="1" parent="1"/>
        <mxCell id="5" value="" edge="1" source="2" target="3" parent="1"/>
        <mxCell id="6" value="reads" edge="1" source="3" target="4" parent="1"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


class TestDrawioProvider:
    @pytest.fixture
    def mock_gdrive(self):
        client = AsyncMock()
        client.available = True
        client.list_drawio_files.return_value = [
            {"id": "file1", "name": "architecture.drawio", "modifiedTime": "2026-03-25"},
        ]
        client.download_file.return_value = SAMPLE_DRAWIO_XML
        return client

    @pytest.fixture
    def provider(self, mock_gdrive):
        return DrawioProvider(mock_gdrive, TTLCache(default_ttl=60), folder_id="test_folder")

    @pytest.mark.asyncio
    async def test_list_diagrams(self, provider):
        result = await provider.list_diagrams()
        assert len(result) == 1
        assert result[0]["name"] == "architecture.drawio"

    @pytest.mark.asyncio
    async def test_get_diagram(self, provider):
        result = await provider.get_diagram("architecture.drawio")
        assert len(result) == 1
        diagram = result[0]
        assert diagram["name"] == "Architecture"
        assert len(diagram["nodes"]) == 3
        assert len(diagram["edges"]) == 2

    @pytest.mark.asyncio
    async def test_search_nodes(self, provider):
        results = await provider.search_nodes("Auth")
        assert len(results) == 1
        assert results[0]["node"]["label"] == "Auth Service"
        assert results[0]["diagram_name"] == "Architecture"

    @pytest.mark.asyncio
    async def test_search_nodes_case_insensitive(self, provider):
        results = await provider.search_nodes("database")
        assert len(results) == 1
        assert results[0]["node"]["label"] == "Database"

    @pytest.mark.asyncio
    async def test_node_connections(self, provider):
        result = await provider.node_connections("Auth Service")
        assert result["node"]["label"] == "Auth Service"
        assert len(result["inbound"]) == 1
        assert result["inbound"][0]["from"] == "API Gateway"
        assert len(result["outbound"]) == 1
        assert result["outbound"][0]["to"] == "Database"
        assert result["outbound"][0]["label"] == "reads"

    @pytest.mark.asyncio
    async def test_node_connections_not_found(self, provider):
        result = await provider.node_connections("Nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_caching(self, provider, mock_gdrive):
        await provider.list_diagrams()
        await provider.list_diagrams()
        assert mock_gdrive.list_drawio_files.call_count == 1

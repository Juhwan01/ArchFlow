"""Parse draw.io XML files into structured DiagramNode/DiagramEdge data.

Draw.io files come in two formats:
1. Raw XML: <mxGraphModel> directly in file
2. Compressed: <mxfile> with base64 + deflate encoded <diagram> elements

This parser handles both formats transparently.
"""

from __future__ import annotations

import base64
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from archflow.core.models import Diagram, DiagramEdge, DiagramNode


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags from a string, keeping text content."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _decode_compressed_content(encoded: str) -> str:
    """Decode draw.io compressed content: base64 → inflate → URL-decode."""
    decoded_bytes = base64.b64decode(encoded.strip())
    inflated = zlib.decompress(decoded_bytes, -zlib.MAX_WBITS)
    return urllib.parse.unquote(inflated.decode("utf-8"))


def _parse_mx_graph_model(root: ET.Element) -> tuple[list[DiagramNode], list[DiagramEdge]]:
    """Extract nodes and edges from an mxGraphModel element."""
    nodes: list[DiagramNode] = []
    edges: list[DiagramEdge] = []

    for cell in root.iter("mxCell"):
        cell_id = cell.get("id", "")
        value = cell.get("value", "")
        style = cell.get("style", "")

        if cell_id in ("0", "1"):
            continue

        label = _strip_html_tags(value) if value else ""

        if cell.get("edge") == "1":
            source = cell.get("source", "")
            target = cell.get("target", "")
            if source and target:
                edges.append(DiagramEdge(
                    id=cell_id,
                    source_id=source,
                    target_id=target,
                    label=label,
                ))
        elif cell.get("vertex") == "1":
            parent_id = cell.get("parent")
            if parent_id == "1":
                parent_id = None
            nodes.append(DiagramNode(
                id=cell_id,
                label=label,
                style=style,
                parent_id=parent_id,
            ))

    return nodes, edges


def parse_drawio_xml(xml_content: str, name: str = "") -> list[Diagram]:
    """Parse a .drawio file content and return a list of Diagrams.

    A single .drawio file may contain multiple diagram pages.

    Args:
        xml_content: Raw XML string from a .drawio file
        name: Optional name for the diagram (e.g., filename)

    Returns:
        List of Diagram objects, one per page/tab
    """
    root = ET.fromstring(xml_content)
    diagrams: list[Diagram] = []

    if root.tag == "mxfile":
        for diagram_el in root.findall("diagram"):
            page_name = diagram_el.get("name", name)
            content = (diagram_el.text or "").strip()

            if not content:
                mxgraph = diagram_el.find("mxGraphModel")
                if mxgraph is not None:
                    nodes, edges = _parse_mx_graph_model(mxgraph)
                    diagrams.append(Diagram(name=page_name, nodes=nodes, edges=edges))
                continue

            try:
                decoded_xml = _decode_compressed_content(content)
                inner_root = ET.fromstring(decoded_xml)
                nodes, edges = _parse_mx_graph_model(inner_root)
                diagrams.append(Diagram(name=page_name, nodes=nodes, edges=edges))
            except Exception:
                continue

    elif root.tag == "mxGraphModel":
        nodes, edges = _parse_mx_graph_model(root)
        diagrams.append(Diagram(name=name, nodes=nodes, edges=edges))

    return diagrams

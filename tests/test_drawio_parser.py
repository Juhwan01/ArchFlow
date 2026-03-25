"""Tests for draw.io XML parser."""

from archflow.providers.drawio_parser import parse_drawio_xml


# ---------------------------------------------------------------------------
# Sample draw.io XML (raw, uncompressed format)
# ---------------------------------------------------------------------------

RAW_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="API Gateway" style="rounded=1;" vertex="1" parent="1">
      <mxGeometry x="200" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="Auth Service" style="rounded=1;" vertex="1" parent="1">
      <mxGeometry x="400" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="Database" style="shape=cylinder;" vertex="1" parent="1">
      <mxGeometry x="400" y="250" width="120" height="80" as="geometry"/>
    </mxCell>
    <mxCell id="5" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="2" target="3" parent="1"/>
    <mxCell id="6" value="reads/writes" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="3" target="4" parent="1"/>
  </root>
</mxGraphModel>
"""


# ---------------------------------------------------------------------------
# Sample mxfile format (multi-page, with embedded mxGraphModel)
# ---------------------------------------------------------------------------

MXFILE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram name="System Overview">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="n1" value="Frontend" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="n2" value="Backend API" style="rounded=1;" vertex="1" parent="1">
          <mxGeometry x="300" y="100" width="120" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="e1" value="HTTP" style="" edge="1" source="n1" target="n2" parent="1"/>
      </root>
    </mxGraphModel>
  </diagram>
  <diagram name="Database Layer">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="d1" value="PostgreSQL" style="shape=cylinder;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="120" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="d2" value="Redis Cache" style="shape=cylinder;" vertex="1" parent="1">
          <mxGeometry x="300" y="100" width="120" height="80" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""


# ---------------------------------------------------------------------------
# Sample with HTML labels
# ---------------------------------------------------------------------------

HTML_LABEL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="h1" value="&lt;b&gt;User Service&lt;/b&gt;&lt;br&gt;(microservice)" style="rounded=1;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
"""


class TestRawXmlParsing:
    def test_parses_nodes(self):
        diagrams = parse_drawio_xml(RAW_XML, name="test")
        assert len(diagrams) == 1
        diagram = diagrams[0]
        assert len(diagram.nodes) == 3
        labels = {n.label for n in diagram.nodes}
        assert labels == {"API Gateway", "Auth Service", "Database"}

    def test_parses_edges(self):
        diagrams = parse_drawio_xml(RAW_XML, name="test")
        diagram = diagrams[0]
        assert len(diagram.edges) == 2

        edge_with_label = next(e for e in diagram.edges if e.label)
        assert edge_with_label.label == "reads/writes"
        assert edge_with_label.source_id == "3"
        assert edge_with_label.target_id == "4"

    def test_skips_root_cells(self):
        diagrams = parse_drawio_xml(RAW_XML, name="test")
        diagram = diagrams[0]
        ids = {n.id for n in diagram.nodes}
        assert "0" not in ids
        assert "1" not in ids

    def test_preserves_style(self):
        diagrams = parse_drawio_xml(RAW_XML, name="test")
        diagram = diagrams[0]
        db_node = next(n for n in diagram.nodes if n.label == "Database")
        assert "cylinder" in db_node.style


class TestMxfileParsing:
    def test_parses_multiple_pages(self):
        diagrams = parse_drawio_xml(MXFILE_XML)
        assert len(diagrams) == 2

    def test_page_names(self):
        diagrams = parse_drawio_xml(MXFILE_XML)
        names = {d.name for d in diagrams}
        assert names == {"System Overview", "Database Layer"}

    def test_first_page_content(self):
        diagrams = parse_drawio_xml(MXFILE_XML)
        overview = next(d for d in diagrams if d.name == "System Overview")
        assert len(overview.nodes) == 2
        assert len(overview.edges) == 1
        assert overview.edges[0].label == "HTTP"

    def test_second_page_content(self):
        diagrams = parse_drawio_xml(MXFILE_XML)
        db_layer = next(d for d in diagrams if d.name == "Database Layer")
        assert len(db_layer.nodes) == 2
        labels = {n.label for n in db_layer.nodes}
        assert labels == {"PostgreSQL", "Redis Cache"}


class TestHtmlLabels:
    def test_strips_html_tags(self):
        diagrams = parse_drawio_xml(HTML_LABEL_XML, name="test")
        diagram = diagrams[0]
        assert len(diagram.nodes) == 1
        assert diagram.nodes[0].label == "User Service(microservice)"


class TestEdgeCases:
    def test_empty_diagram(self):
        xml = """<?xml version="1.0"?>
        <mxGraphModel><root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
        </root></mxGraphModel>"""
        diagrams = parse_drawio_xml(xml, name="empty")
        assert len(diagrams) == 1
        assert len(diagrams[0].nodes) == 0
        assert len(diagrams[0].edges) == 0

    def test_edge_without_source_target_skipped(self):
        xml = """<?xml version="1.0"?>
        <mxGraphModel><root>
            <mxCell id="0"/>
            <mxCell id="1" parent="0"/>
            <mxCell id="2" value="Node" vertex="1" parent="1"/>
            <mxCell id="3" value="" edge="1" parent="1"/>
        </root></mxGraphModel>"""
        diagrams = parse_drawio_xml(xml, name="test")
        assert len(diagrams[0].edges) == 0
        assert len(diagrams[0].nodes) == 1

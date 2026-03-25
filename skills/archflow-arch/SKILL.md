---
name: archflow-arch
description: "시스템 아키텍처 다이어그램을 조회하고 설명합니다. 트리거: '시스템 구조', '아키텍처', '뭐랑 연결', '다이어그램', '서비스 관계'"
---

# /arch - 아키텍처 이해

Draw.io 다이어그램에서 시스템 구조를 조회하고 자연어로 설명합니다.

## 판단 기준

| 질문 유형 | 호출할 도구 |
|-----------|------------|
| 전체 구조 ("우리 시스템 구조?") | `mcp__archflow__archflow_drawio_list_diagrams` → `mcp__archflow__archflow_drawio_get_diagram` |
| 특정 서비스 연결 ("Auth Service가 뭐랑 연결?") | `mcp__archflow__archflow_drawio_node_connections` |
| 서비스 검색 ("DB 접근하는 서비스?") | `mcp__archflow__archflow_drawio_search_nodes` |
| 컴포넌트 상세 ("Auth Service 전체 맥락?") | `mcp__archflow__archflow_trace_component` |

## 응답 형식

- 노드와 연결을 자연어로 설명
- "A → B (라벨)" 형태로 연결 관계 표시
- 비개발자도 이해할 수 있게 기술 용어 풀어서 설명

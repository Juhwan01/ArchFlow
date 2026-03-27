---
name: archflow-trace
description: "이슈 ↔ PR ↔ 코드 ↔ 아키텍처 다이어그램 간 연결을 추적합니다. 트리거: '관련 PR', '코드 어디야', '이슈 추적', '관련 코드', '어디서 구현'"
---

# /trace - 이슈/코드/아키텍처 추적

Jira 이슈 키 또는 컴포넌트 이름으로 모든 소스를 크로스 추적합니다.

## 판단 기준

| 질문 유형 | 호출할 도구 |
|-----------|------------|
| 이슈 키 기반 ("KAN-123 관련 PR/코드?") | `mcp__archflow__archflow_trace_issue` |
| 컴포넌트 기반 ("Auth Service 코드 어디?") | `mcp__archflow__archflow_trace_component` |
| PR↔이슈 ("이 PR 어떤 이슈?") | `mcp__archflow__archflow_github_pr_for_issue` |
| 코드 검색 ("인증 관련 코드?") | `mcp__archflow__archflow_github_search_code` |

## 응답 형식

- 이슈 → PR → 코드 파일 순서로 연결 고리를 보여줌
- 다이어그램에서의 위치도 함께 표시
- 링크를 클릭할 수 있도록 URL 포함

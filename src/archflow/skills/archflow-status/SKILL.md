---
name: archflow-status
description: "프로젝트/이슈/기능의 진행 상황을 확인합니다. 트리거: '어디까지 됐어', '스프린트 현황', '누가 뭐 하고 있어', '진행 상황', '상태 확인'"
---

# /status - 작업 현황 확인

사용자의 질문을 분석하여 적절한 ArchFlow MCP 도구를 호출합니다.

## 판단 기준

| 질문 유형 | 호출할 도구 |
|-----------|------------|
| 특정 이슈 상태 ("KAN-123 어떻게 돼?") | `mcp__archflow__archflow_jira_get_issue` |
| 스프린트 현황 ("이번 스프린트 뭐 남았어?") | `mcp__archflow__archflow_jira_sprint_status` |
| 특정 기능/컴포넌트 진행률 ("인증 기능 어디까지?") | `mcp__archflow__archflow_jira_component_status` |
| 에픽 진행률 ("에픽 얼마나 됐어?") | `mcp__archflow__archflow_jira_epic_progress` |
| 특정 사람 작업 ("철수가 뭐 하고 있어?") | `mcp__archflow__archflow_jira_user_workload` |
| 최근 활동 ("요즘 뭐가 바뀌었어?") | `mcp__archflow__archflow_jira_recent_activity` |

## 응답 형식

- 진행률은 퍼센트로 표시
- 상태별 이슈 수를 요약
- 비개발자도 이해할 수 있는 자연어로 답변
- 핵심 수치를 먼저, 상세는 뒤에

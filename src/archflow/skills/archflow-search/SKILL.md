---
name: archflow-search
description: "Jira, GitHub, 다이어그램 전체를 통합 검색합니다. 트리거: '검색', '찾아줘', '어디서 쓰고 있어', '관련된 거 전부'"
---

# /search - 통합 검색

모든 소스(Jira, GitHub, Draw.io)에서 한 번에 검색합니다.

## 사용법

```
/search 인증
/search Redis
/search payment
```

## 워크플로우

1. `mcp__archflow__archflow_search` 호출 (query=검색어)
2. 소스별로 결과 그룹핑하여 표시

## 응답 형식

### Jira 이슈
- 검색어와 관련된 이슈 목록

### GitHub 코드
- 검색어가 포함된 파일 경로 목록

### 아키텍처 다이어그램
- 검색어와 매칭되는 노드와 연결 관계

<p align="center">
  <h1 align="center">ArchFlow</h1>
  <p align="center">
    <strong>Context Hub MCP Server — Jira + GitHub + Draw.io 통합 조회</strong>
  </p>
  <p align="center">
    <a href="#설치">설치</a> ·
    <a href="#사용-가능한-도구">도구</a> ·
    <a href="#슬래시-명령어">명령어</a> ·
    <a href="./README.md">English</a>
  </p>
</p>

---

LLM에게 프로젝트 현황을 물어보세요. ArchFlow가 **Jira**, **GitHub**, **Draw.io** 다이어그램에서 정보를 가져와 답합니다.

**누가 쓰나요?**
| 역할 | 질문 예시 |
|------|----------|
| 대표 / PM | "이번 스프린트 진행률 얼마야?" "이번주 팀 보고서 만들어줘" |
| 신규 팀원 | "우리 시스템 구조 설명해줘" "뭐부터 봐야 해?" |
| 개발자 | "KAN-123 관련 코드 어디야?" "인증 쪽 PR 뭐가 있어?" |

---

## 설치

### 사전 요구사항

1. **Python 3.11+** — 터미널에서 `python --version` 으로 확인
   - 없으면: https://python.org 에서 다운로드
2. **uv** (Python 패키지 매니저) — 터미널에서 `uv --version` 으로 확인
   - 없으면 설치:
     ```bash
     # macOS / Linux
     curl -LsSf https://astral.sh/uv/install.sh | sh

     # Windows (PowerShell)
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
3. **Claude Code** CLI — 이미 사용 중이면 OK

### 빠른 시작 (3분)

```bash
# 1. 클론 (실제 레포 URL로 교체)
git clone https://github.com/your-org/archflow.git
cd archflow

# 2. 대화형 설치 실행
bash scripts/install.sh
```

설치 중에 이렇게 물어봅니다:

```
  ╔══════════════════════════════════╗
  ║   ArchFlow - Context Hub 설치    ║
  ╚══════════════════════════════════╝

[2/4] API 크레덴셜 설정

  ── Jira Cloud ──
  기존 Jira 설정을 발견했습니다: https://your-team.atlassian.net
  기존 설정을 사용하시겠습니까? (Y/n): Y     ← 엔터

  ── GitHub ──
  GitHub Personal Access Token (없으면 Enter로 건너뛰기): ghp_xxx

  ── Google Drive (Draw.io 다이어그램) ──
  Google Client ID (없으면 Enter로 건너뛰기):  ← 나중에 추가 가능
```

```bash
# 3. 프로젝트 설정 편집 (아무 에디터 사용)
code archflow.config.yml     # VS Code
# 또는: notepad archflow.config.yml  (Windows)
# 또는: nano archflow.config.yml     (Mac/Linux)

# 4. Claude Code 재시작 — 끝!
```

> **부분 설정 가능**: GitHub이나 Google Drive 없이도 동작합니다. Jira만 연결해도 Jira 관련 기능은 모두 사용 가능합니다.

---

## 사용 가능한 도구

### Jira (7개)

| 도구 | 설명 |
|------|------|
| `archflow_jira_get_issue` | 이슈 상세 조회 (댓글, 링크, 서브태스크) |
| `archflow_jira_sprint_status` | 현재 스프린트 상태별 이슈 |
| `archflow_jira_search` | JQL 검색 |
| `archflow_jira_user_workload` | 특정 사용자에게 할당된 이슈 |
| `archflow_jira_component_status` | 컴포넌트별 진행률 (%) |
| `archflow_jira_recent_activity` | 최근 N일 업데이트된 이슈 |
| `archflow_jira_epic_progress` | 에픽 하위 이슈 + 완료율 |

### GitHub (6개)

| 도구 | 설명 |
|------|------|
| `archflow_github_get_pr` | PR 상세 (diff 통계) |
| `archflow_github_list_prs` | PR 목록 (상태/작성자/브랜치 필터) |
| `archflow_github_pr_for_issue` | Jira 이슈 키로 관련 PR 찾기 |
| `archflow_github_recent_commits` | 최근 커밋 목록 |
| `archflow_github_search_code` | 레포에서 코드 검색 |
| `archflow_github_repo_overview` | 레포 요약 (언어, 활동) |

### Draw.io / 아키텍처 (4개)

| 도구 | 설명 |
|------|------|
| `archflow_drawio_list_diagrams` | Google Drive의 .drawio 파일 목록 |
| `archflow_drawio_get_diagram` | 다이어그램 → 노드 + 연결 파싱 |
| `archflow_drawio_search_nodes` | 노드 라벨로 검색 |
| `archflow_drawio_node_connections` | 특정 노드의 인바운드/아웃바운드 연결 |

### 크로스소스 인텔리전스 (5개)

| 도구 | 설명 |
|------|------|
| `archflow_trace_issue` | 이슈 → PR + 코드 + 다이어그램 노드 추적 |
| `archflow_trace_component` | 아키텍처 컴포넌트 → 이슈 + PR + 연결 관계 |
| `archflow_project_overview` | 스프린트 + 아키텍처 + GitHub 활동 종합 |
| `archflow_team_activity` | 주간 팀 보고서 (모든 소스 종합) |
| `archflow_onboarding_context` | 신규 팀원용 프로젝트 전체 맥락 |

### 통합 검색 (1개)

| 도구 | 설명 |
|------|------|
| `archflow_search` | Jira + GitHub + 다이어그램 통합 검색 |

---

## 슬래시 명령어

설치 후 Claude Code에서 바로 사용 가능:

| 명령어 | 대상 | 사용 예시 |
|--------|------|----------|
| `/status` | 모두 | "인증 기능 어디까지 됐어?" |
| `/trace` | 개발자 | "KAN-123 관련 코드 어디야?" |
| `/arch` | 모두 | "Auth Service가 뭐랑 연결돼있어?" |
| `/onboard` | 신규 팀원 | "이 프로젝트 전체 요약해줘" |
| `/report` | 대표/PM | "이번주 팀 활동 정리해줘" |
| `/search` | 모두 | "인증 관련 전부 찾아줘" |

---

## 설정

### `archflow.config.yml`

```yaml
# Jira Cloud
jira:
  url: "https://your-domain.atlassian.net"
  projects:                    # 여러 프로젝트 지원
    - "KAN"
    - "FRONT"
  board_id: "1"                # 스프린트 조회용 보드 ID

# GitHub
github:
  repos:                       # 여러 레포 지원
    - "your-org/backend-api"
    - "your-org/frontend-web"
  default_branch: "main"

# Google Drive (Draw.io 파일 저장소)
gdrive:
  folder_id: "1abc123..."     # .drawio 파일이 있는 폴더 ID
  cache_ttl_minutes: 30        # 캐시 유지 시간

# 소스 간 매칭 설정
matching:
  explicit:                    # 수동 매핑: 다이어그램 노드 → Jira/GitHub
    - diagram_node: "Auth Service"
      jira_component: "authentication"
      github_path_prefix: "src/auth/"
  auto_match:
    enabled: true
    strategy: "fuzzy"          # exact | fuzzy | contains
    min_score: 0.7
```

### 환경 변수

| 변수 | 필수 | 발급처 |
|------|------|--------|
| `JIRA_URL` 또는 `JIRA_INSTANCE_URL` | Jira 사용 시 | Atlassian 설정 |
| `JIRA_EMAIL` 또는 `JIRA_USER_EMAIL` | Jira 사용 시 | 본인 이메일 |
| `JIRA_API_TOKEN` 또는 `JIRA_API_KEY` | Jira 사용 시 | 아래 가이드 참고 |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub 사용 시 | 아래 가이드 참고 |
| `GOOGLE_CLIENT_ID` | Draw.io 사용 시 | 아래 가이드 참고 |
| `GOOGLE_CLIENT_SECRET` | Draw.io 사용 시 | Google Cloud Console |
| `GOOGLE_REFRESH_TOKEN` | Draw.io 사용 시 | OAuth 인증 흐름 |

> **참고**: 설치 스크립트(`install.sh`)가 기존 Claude Code의 Jira 설정을 자동 감지합니다. 이미 jira MCP를 사용 중이라면 Jira 크레덴셜 입력이 필요 없습니다.

### 토큰 발급 가이드

<details>
<summary><strong>Jira API 토큰 발급 (2분)</strong></summary>

1. https://id.atlassian.com/manage-profile/security/api-tokens 접속
2. **"API 토큰 만들기"** 클릭
3. 라벨 입력 (예: `archflow`)
4. **"만들기"** 클릭 → 토큰이 표시됨
5. 토큰을 복사해서 설치 스크립트에 붙여넣기

</details>

<details>
<summary><strong>GitHub Personal Access Token 발급 (2분)</strong></summary>

1. https://github.com/settings/tokens?type=beta 접속
2. **"Generate new token"** 클릭
3. 이름 입력 (예: `archflow`)
4. 권한 설정:
   - **Repository access**: 조회할 레포 선택 (또는 All repositories)
   - **Permissions > Repository permissions**:
     - Contents: **Read-only**
     - Pull requests: **Read-only**
     - Metadata: **Read-only**
5. **"Generate token"** → 토큰 복사

</details>

<details>
<summary><strong>Google Drive OAuth 설정 (10분, Draw.io 사용 시만)</strong></summary>

1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
3. **API 및 서비스 > 라이브러리** → "Google Drive API" 검색 → **사용 설정**
4. **API 및 서비스 > 사용자 인증 정보** → **사용자 인증 정보 만들기 > OAuth 클라이언트 ID**
   - 애플리케이션 유형: **데스크톱 앱**
   - 이름: `archflow`
5. **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사
6. Refresh Token 얻기 (OAuth Playground 사용):
   - https://developers.google.com/oauthplayground/ 접속
   - 오른쪽 위 설정(톱니바퀴) → "Use your own OAuth credentials" 체크
   - 위에서 복사한 Client ID, Secret 입력
   - Step 1: `https://www.googleapis.com/auth/drive.readonly` 선택 → Authorize
   - Step 2: **"Exchange authorization code for tokens"** 클릭
   - **Refresh token** 복사

</details>

---

## 아키텍처

```
사용자 질문
     ↓
┌─────────────────────────────────┐
│        ArchFlow MCP Server       │
│                                   │
│  ┌─────────┐  ┌──────────────┐  │
│  │  캐시    │  │   매칭 엔진   │  │
│  │ (TTL)    │  │ (크로스소스)  │  │
│  └─────────┘  └──────────────┘  │
│                                   │
│  ┌─────────┐ ┌────────┐ ┌─────┐ │
│  │  Jira   │ │ GitHub │ │Draw │ │
│  │Provider │ │Provider│ │.io  │ │
│  └────┬────┘ └───┬────┘ └──┬──┘ │
└───────┼──────────┼─────────┼────┘
        ↓          ↓         ↓
   Jira Cloud   GitHub   Google Drive
     REST API   REST API   (.drawio)
```

**토큰 절감**: 모든 API 응답은 TTL 캐시. 같은 질문을 반복하면 API 호출 0.

---

## 문제 해결

| 증상 | 해결 |
|------|------|
| Claude Code에서 서버가 안 보임 | MCP 설정 확인: `python3 -m json.tool ~/.claude/.mcp.json` |
| "Jira not configured" | 환경변수 확인: `JIRA_URL` (또는 `JIRA_INSTANCE_URL`) 설정 필요 |
| "GitHub not configured" | MCP 설정에 `GITHUB_PERSONAL_ACCESS_TOKEN` 추가 |
| Draw.io 파일이 안 보임 | `archflow.config.yml`의 `folder_id` 확인 + Google OAuth 토큰 확인 |
| 데이터가 오래됨 | 기본 캐시 TTL 30분. 서버 재시작하면 캐시 초기화 |
| GitHub rate limit | GitHub Search API: 30회/분 제한. 캐시된 결과 사용 |

### 설정 확인

```bash
# MCP 설정이 유효한 JSON인지 확인
python3 -m json.tool ~/.claude/.mcp.json

# 서버가 에러 없이 시작되는지 확인
cd archflow && uv run archflow
# (Ctrl+C로 종료 — 에러 없으면 정상)

# 테스트 실행
uv run python -m pytest tests/ -v
```

---

## 개발

```bash
# 개발 의존성 설치
uv sync --dev

# 테스트
uv run python -m pytest tests/ -v

# 린트
uv run ruff check src/
```

### 프로젝트 구조

```
src/archflow/
├── server.py          # MCP 서버 엔트리포인트
├── clients/           # HTTP 클라이언트 (Jira, GitHub, Google Drive)
├── providers/         # 소스별 비즈니스 로직
├── core/              # 설정, 캐시, 매칭 엔진, 모델
└── tools/             # MCP 도구 등록 (23개)
```

---

## 라이선스

MIT

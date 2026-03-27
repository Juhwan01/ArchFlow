<p align="center">
  <img src="https://img.shields.io/badge/ArchFlow-Context_Hub-blue?style=for-the-badge" alt="ArchFlow" />
</p>

<h1 align="center">ArchFlow</h1>

<p align="center">
  <strong>Jira + GitHub + Draw.io 정보를 Claude Code 안에서 한번에 조회</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/archflow-hub?style=flat-square&color=blue" alt="PyPI" />
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" />
</p>

<p align="center">
  <a href="#-시작하기">시작하기</a> ·
  <a href="#-이런-걸-할-수-있어요">활용 예시</a> ·
  <a href="#-슬래시-커맨드">커맨드</a> ·
  <a href="#-설정-가이드">설정</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## 이게 뭔가요?

Claude Code에서 Jira 이슈, GitHub PR, 아키텍처 다이어그램을 **탭 전환 없이** 바로 물어볼 수 있게 해주는 도구입니다.

```
You: "KAN-42 관련 코드 어디야?"

ArchFlow:
  Jira   → KAN-42: "OAuth2 로그인 추가" (진행 중, @alice)
  GitHub → PR #87 "feat: oauth2 login flow" (src/auth/oauth.ts)
  Draw.io → Auth Service → API Gateway, User DB와 연결됨
```

---

## 📦 시작하기

### 필요한 것

- **Python 3.11 이상** — [다운로드](https://www.python.org/downloads/)
- **Claude Code** — 이미 사용 중이어야 합니다
- **Jira 계정** — Atlassian Cloud (필수)
- GitHub, Google Drive는 선택사항

### 설치 (5분)

#### Step 1: ArchFlow 설치

```bash
pip install archflow-hub
```

> `pip`이 안 되면 `pip3 install archflow-hub` 또는 `python -m pip install archflow-hub`을 시도하세요.

#### Step 2: 초기 설정

```bash
archflow init
```

터미널에서 대화형으로 진행됩니다. 물어보는 것들:

```
1. Jira URL         → https://your-team.atlassian.net
2. Jira 이메일       → you@company.com
3. Jira API 토큰     → (아래에서 발급 방법 설명)
4. Jira 프로젝트 키   → KAN (또는 PROJ 등 본인 프로젝트)
5. Jira 보드 ID      → 1 (기본값, 아래에서 찾는 법 설명)
6. GitHub 토큰       → (선택, Enter로 스킵 가능)
7. Google Drive      → (선택, Enter로 스킵 가능)
```

완료되면 자동으로:
- API 연결 검증
- 설정 파일 생성
- Claude Code에 MCP 서버 등록
- 슬래시 커맨드 6개 설치 (`/status`, `/trace`, `/arch`, `/onboard`, `/report`, `/search`)

#### Step 3: Claude Code 재시작

Claude Code를 **완전히 종료했다가 다시 실행**하세요. 그리고:

```
/status
```

동작하면 설치 완료!

#### 연결 확인 (문제가 있을 때)

```bash
archflow doctor
```

어디가 문제인지 알려줍니다.

---

### 🔑 API 토큰 발급 방법

<details>
<summary><strong>Jira API 토큰</strong> (2분, 필수)</summary>

1. https://id.atlassian.com/manage-profile/security/api-tokens 접속
2. **"Create API token"** 클릭
3. 라벨 입력 (예: `archflow`) → **Create**
4. 생성된 토큰 복사 → `archflow init`에서 붙여넣기

</details>

<details>
<summary><strong>GitHub Personal Access Token</strong> (2분, 선택)</summary>

1. https://github.com/settings/tokens?type=beta 접속
2. **"Generate new token"** 클릭
3. 이름: `archflow`
4. **Repository permissions** → 아래 3개를 **Read-only**로 설정:
   - Contents
   - Pull requests
   - Metadata
5. 생성된 토큰 복사 → `archflow init`에서 붙여넣기

</details>

<details>
<summary><strong>Google Drive OAuth</strong> (10분, Draw.io 사용 시에만)</summary>

1. [Google Cloud Console](https://console.cloud.google.com/) → 프로젝트 생성 또는 선택
2. **APIs & Services > Library** → **Google Drive API** 활성화
3. **Credentials** → **Create Credentials** → **OAuth client ID** (Desktop app)
4. **Client ID**와 **Client Secret** 복사
5. [OAuth Playground](https://developers.google.com/oauthplayground/)에서 Refresh Token 발급:
   - 오른쪽 상단 설정(톱니바퀴) → "Use your own OAuth credentials" 체크 → Client ID/Secret 입력
   - Step 1: `drive.readonly` 선택 → Authorize
   - Step 2: Exchange → **Refresh token** 복사
6. `archflow init`에서 3개 모두 입력

</details>

<details>
<summary><strong>Jira board_id 찾는 법</strong></summary>

Jira 보드를 브라우저에서 열고 URL을 보세요:
```
https://your-team.atlassian.net/jira/software/projects/KAN/boards/1
                                                                  ^
                                                            이 숫자가 board_id
```

</details>

<details>
<summary><strong>Google Drive folder_id 찾는 법</strong></summary>

`.drawio` 파일이 있는 Google Drive 폴더를 열고 URL을 보세요:
```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                       이 부분이 folder_id
```

</details>

---

## 💡 이런 걸 할 수 있어요

### 누구나

| 이렇게 물어보세요 | ArchFlow가 하는 일 |
|-------------------|-------------------|
| "스프린트 현황 어때?" | Jira에서 현재 스프린트 이슈를 상태별로 정리, 진행률 표시 |
| "Redis 관련된 거 전부 찾아줘" | Jira 이슈 + GitHub 코드 + 다이어그램 노드 통합 검색 |
| "Auth Service랑 연결된 게 뭐야?" | Draw.io 다이어그램에서 연결 관계 파싱 |

### 개발자

| 이렇게 물어보세요 | ArchFlow가 하는 일 |
|-------------------|-------------------|
| "KAN-42 코드 어디야?" | Jira 이슈 → GitHub PR → 코드 파일 → 아키텍처 노드 추적 |
| "auth 관련 PR 보여줘" | GitHub PR을 키워드, 브랜치, Jira 키로 검색 |
| "이번 주 팀이 뭐 했어?" | 커밋 + PR + Jira 상태 변경을 하나로 종합 |

### PM / 신규 팀원

| 이렇게 물어보세요 | ArchFlow가 하는 일 |
|-------------------|-------------------|
| "주간 보고서 만들어줘" | 누가 뭘 했는지, 뭐가 진행 중인지, 뭐가 막혀있는지 정리 |
| "프로젝트 처음인데 설명해줘" | 스프린트 + 아키텍처 + 레포 구조 + 주요 이슈 종합 |
| "인증 에픽 얼마나 됐어?" | 에픽 하위 이슈 진행률, 상태별 분류 |

---

## ⚡ 슬래시 커맨드

Claude Code에서 슬래시(`/`)를 입력하면 바로 사용할 수 있습니다:

| 커맨드 | 설명 | 예시 |
|--------|------|------|
| `/status` | 진행 상황 확인 | "인증 기능 어디까지 됐어?" |
| `/trace` | 이슈 → 코드 추적 | "KAN-123 관련 PR 찾아줘" |
| `/arch` | 아키텍처 조회 | "Auth Service 연결 관계 보여줘" |
| `/onboard` | 프로젝트 개요 | "이 프로젝트 전체 맥락 알려줘" |
| `/report` | 팀 활동 보고서 | "이번 주 팀 리포트" |
| `/search` | 통합 검색 | "Redis 관련된 거 전부" |

> 슬래시 커맨드 없이 자연어로 물어봐도 됩니다. Claude가 알아서 ArchFlow 도구를 사용합니다.

---

## 🔧 설정 가이드

### 설정 파일 위치

`archflow init`이 자동 생성합니다. 나중에 수정하고 싶으면 직접 편집:

```yaml
# ~/.archflow/config.yml

jira:
  url: "https://your-team.atlassian.net"
  projects: ["KAN"]          # 프로젝트 키 (여러 개 가능)
  board_id: "1"              # 스프린트 보드 ID

github:
  repos: ["your-org/repo"]   # owner/repo 형식
  default_branch: "main"

gdrive:
  folder_id: "1AbCdEfG..."   # .drawio 파일이 있는 폴더
  cache_ttl_minutes: 30       # API 캐시 시간 (분)
```

### 설치 방식 비교

| 방식 | 설명 | 언제 쓰나 |
|------|------|----------|
| `pip install archflow-hub` | 컴퓨터에 설치됨 | `archflow init`, `archflow doctor` 명령어를 직접 실행할 때 |
| `uvx archflow-hub` | 설치 없이 임시 실행 (npx와 비슷) | Claude Code가 MCP 서버를 실행할 때 (자동) |

> `archflow init`을 실행하려면 `pip install`이 필요합니다. 설치 후 Claude Code는 내부적으로 `uvx`로 서버를 실행하므로, 한번 init만 하면 됩니다.

---

## 🔥 문제 해결

```bash
archflow doctor    # 모든 연결 상태를 한번에 점검
```

| 문제 | 해결 |
|------|------|
| Claude Code에서 ArchFlow가 안 보임 | `archflow init` 다시 실행 → Claude Code 재시작 |
| "Jira not configured" | `.mcp.json`에 Jira 토큰이 없음 → `archflow init` 재실행 |
| "GitHub not configured" | GitHub 토큰을 스킵했거나 만료됨 → 토큰 재발급 후 init |
| Draw.io 파일이 안 나옴 | `folder_id` 확인 + Google OAuth 3개 값 모두 입력했는지 확인 |
| 데이터가 옛날 것 | 캐시 때문 (기본 30분) → Claude Code 재시작하면 초기화 |
| GitHub 요청 제한 | 검색 API는 분당 30회 제한 → 잠시 기다리면 캐시가 해결 |

---

## Architecture

<p align="center">
  <img src="docs/archflow_architecture.png" alt="ArchFlow Architecture" width="600" />
</p>

```mermaid
graph TB
    User["질문"] --> Server

    subgraph Server["ArchFlow MCP Server"]
        Cache["캐시"]
        Matcher["교차 매칭 엔진"]
        JP["Jira Provider"]
        GP["GitHub Provider"]
        DP["Draw.io Provider"]
    end

    JP --> Jira["Jira Cloud API"]
    GP --> GitHub["GitHub API"]
    DP --> GDrive["Google Drive"]
```

---

## Contributing

### Project Structure

```
src/archflow/
├── server.py              # MCP 서버 + 도구 등록
├── cli.py                 # CLI: init, doctor, serve
├── cli_init.py            # 설치 마법사
├── cli_doctor.py          # 연결 진단
├── clients/               # API 클라이언트 (Jira, GitHub, Google Drive)
├── providers/             # 소스별 비즈니스 로직
├── core/                  # 설정, 캐시, 매칭, 모델
├── tools/                 # MCP 도구 23개
└── skills/                # 슬래시 커맨드 6개
```

### Dev Setup

```bash
git clone https://github.com/Juhwan01/ArchFlow.git
cd ArchFlow
uv sync --dev
uv run python -m pytest tests/ -v
uv run ruff check src/
```

### Commit Convention

```
<type>: <description>
Types: feat | fix | refactor | docs | test | chore | perf | ci
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

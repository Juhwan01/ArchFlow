#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$HOME/.claude/skills"
MCP_CONFIG="$HOME/.claude/.mcp.json"

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║   ArchFlow - Context Hub 설치    ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ==========================================================================
# Step 1: Python 의존성 설치
# ==========================================================================
echo "[1/4] Python 의존성 설치 중..."
cd "$PROJECT_DIR"
if command -v uv &>/dev/null; then
    uv sync 2>/dev/null
else
    echo "  uv가 없습니다. pip으로 설치합니다..."
    pip install -e . 2>/dev/null
fi
echo "  완료."
echo ""

# ==========================================================================
# Step 2: 크레덴셜 수집 (대화형)
# ==========================================================================
echo "[2/4] API 크레덴셜 설정"
echo ""

# --- 기존 값 감지 ---
EXISTING_JIRA_URL=""
EXISTING_JIRA_EMAIL=""
EXISTING_JIRA_TOKEN=""

if [ -f "$MCP_CONFIG" ]; then
    EXISTING_JIRA_URL=$(python3 -c "
import json; d=json.load(open('$MCP_CONFIG'))
e=d.get('mcpServers',{}).get('jira',{}).get('env',{})
print(e.get('JIRA_INSTANCE_URL',''))
" 2>/dev/null || echo "")
    EXISTING_JIRA_EMAIL=$(python3 -c "
import json; d=json.load(open('$MCP_CONFIG'))
e=d.get('mcpServers',{}).get('jira',{}).get('env',{})
print(e.get('JIRA_USER_EMAIL',''))
" 2>/dev/null || echo "")
    EXISTING_JIRA_TOKEN=$(python3 -c "
import json; d=json.load(open('$MCP_CONFIG'))
e=d.get('mcpServers',{}).get('jira',{}).get('env',{})
print(e.get('JIRA_API_KEY',''))
" 2>/dev/null || echo "")
fi

# --- Jira ---
echo "  ── Jira Cloud ──"
if [ -n "$EXISTING_JIRA_URL" ]; then
    echo "  기존 Jira 설정을 발견했습니다: $EXISTING_JIRA_URL"
    read -r -p "  기존 설정을 사용하시겠습니까? (Y/n): " USE_EXISTING
    USE_EXISTING=${USE_EXISTING:-Y}
    if [[ "$USE_EXISTING" =~ ^[Yy]$ ]]; then
        JIRA_URL="$EXISTING_JIRA_URL"
        JIRA_EMAIL="$EXISTING_JIRA_EMAIL"
        JIRA_TOKEN="$EXISTING_JIRA_TOKEN"
    fi
fi

if [ -z "${JIRA_URL:-}" ]; then
    read -r -p "  Jira URL (예: https://your-domain.atlassian.net): " JIRA_URL
    read -r -p "  Jira 이메일: " JIRA_EMAIL
    read -r -s -p "  Jira API 토큰: " JIRA_TOKEN
    echo ""
fi
echo ""

# --- GitHub ---
echo "  ── GitHub ──"
read -r -p "  GitHub Personal Access Token (없으면 Enter로 건너뛰기): " GITHUB_TOKEN
GITHUB_TOKEN=${GITHUB_TOKEN:-""}
echo ""

# --- Google Drive ---
echo "  ── Google Drive (Draw.io 다이어그램) ──"
read -r -p "  Google Client ID (없으면 Enter로 건너뛰기): " GOOGLE_CLIENT_ID
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-""}

if [ -n "$GOOGLE_CLIENT_ID" ]; then
    read -r -s -p "  Google Client Secret: " GOOGLE_CLIENT_SECRET
    echo ""
    read -r -p "  Google Refresh Token: " GOOGLE_REFRESH_TOKEN
else
    GOOGLE_CLIENT_SECRET=""
    GOOGLE_REFRESH_TOKEN=""
fi
echo ""

# ==========================================================================
# Step 3: Skills + MCP 설정 자동 등록
# ==========================================================================
echo "[3/4] Claude Code 설정 중..."

# Skills 복사
for skill_dir in "$PROJECT_DIR/skills/archflow-"*; do
    skill_name="$(basename "$skill_dir")"
    target="$SKILLS_DIR/$skill_name"
    mkdir -p "$target"
    cp "$skill_dir/SKILL.md" "$target/SKILL.md"
    echo "  스킬 설치: /$skill_name"
done

# MCP 서버 설정
python3 -c "
import json
from pathlib import Path

config_path = Path('$MCP_CONFIG')
config = json.loads(config_path.read_text()) if config_path.exists() else {}
if 'mcpServers' not in config:
    config['mcpServers'] = {}

env = {
    'PYTHONUNBUFFERED': '1',
    'ARCHFLOW_CONFIG_PATH': '$PROJECT_DIR/archflow.config.yml',
}

jira_url = '''$JIRA_URL'''
jira_email = '''$JIRA_EMAIL'''
jira_token = '''$JIRA_TOKEN'''
gh_token = '''$GITHUB_TOKEN'''
g_client_id = '''$GOOGLE_CLIENT_ID'''
g_client_secret = '''$GOOGLE_CLIENT_SECRET'''
g_refresh_token = '''$GOOGLE_REFRESH_TOKEN'''

if jira_url:
    env['JIRA_INSTANCE_URL'] = jira_url
    env['JIRA_USER_EMAIL'] = jira_email
    env['JIRA_API_KEY'] = jira_token
if gh_token:
    env['GITHUB_PERSONAL_ACCESS_TOKEN'] = gh_token
if g_client_id:
    env['GOOGLE_CLIENT_ID'] = g_client_id
    env['GOOGLE_CLIENT_SECRET'] = g_client_secret
    env['GOOGLE_REFRESH_TOKEN'] = g_refresh_token

config['mcpServers']['archflow'] = {
    'command': 'uv',
    'args': ['--directory', '$PROJECT_DIR', 'run', 'archflow'],
    'env': env,
}

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(config, indent=2))
print('  MCP 서버 등록 완료')
"

# ==========================================================================
# Step 4: 프로젝트 설정 파일
# ==========================================================================
echo ""
echo "[4/4] 프로젝트 설정..."
if [ ! -f "$PROJECT_DIR/archflow.config.yml" ]; then
    cp "$PROJECT_DIR/archflow.config.example.yml" "$PROJECT_DIR/archflow.config.yml"
    echo "  archflow.config.yml 생성됨 (프로젝트/레포 설정 필요)"
else
    echo "  archflow.config.yml 이미 존재"
fi

# ==========================================================================
# 완료
# ==========================================================================
echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║        설치 완료!                ║"
echo "  ╚══════════════════════════════════╝"
echo ""
echo "  연결된 소스:"
[ -n "${JIRA_URL:-}" ] && echo "    ✓ Jira: $JIRA_URL"
[ -n "${GITHUB_TOKEN:-}" ] && echo "    ✓ GitHub: 연결됨"
[ -n "${GOOGLE_CLIENT_ID:-}" ] && echo "    ✓ Google Drive: 연결됨"
[ -z "${JIRA_URL:-}" ] && echo "    ✗ Jira: 미설정"
[ -z "${GITHUB_TOKEN:-}" ] && echo "    ✗ GitHub: 미설정 (나중에 추가 가능)"
[ -z "${GOOGLE_CLIENT_ID:-}" ] && echo "    ✗ Google Drive: 미설정 (나중에 추가 가능)"
echo ""
echo "  다음 단계:"
echo "    1. archflow.config.yml 에서 프로젝트/레포 설정 편집"
echo "    2. Claude Code 재시작"
echo "    3. 바로 사용!"
echo ""
echo "  사용 가능한 명령어:"
echo "    /status  - 작업 현황 확인"
echo "    /trace   - 이슈↔PR↔코드 추적"
echo "    /arch    - 아키텍처 다이어그램 조회"
echo "    /onboard - 신규 팀원 온보딩"
echo "    /report  - 팀 활동 보고서"
echo "    /search  - 통합 검색"
echo ""

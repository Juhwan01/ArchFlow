<p align="center">
  <h1 align="center">ArchFlow</h1>
  <p align="center">
    <strong>Context Hub MCP Server — Jira + GitHub + Draw.io in one query</strong>
  </p>
  <p align="center">
    <a href="#installation">Install</a> ·
    <a href="#available-tools">Tools</a> ·
    <a href="#slash-commands">Commands</a> ·
    <a href="./README.ko.md">한국어</a>
  </p>
</p>

---

Ask your LLM about project status, trace issues to code, or explain system architecture — ArchFlow pulls data from **Jira**, **GitHub**, and **Draw.io** diagrams in a single MCP server.

**Who is this for?**
| Role | Example Question |
|------|-----------------|
| CEO / PM | "What's the sprint progress?" "Weekly team report" |
| New team member | "Explain our system architecture" "What should I look at first?" |
| Developer | "Where's the code for KAN-123?" "Which PRs are related to auth?" |

---

## Installation

### Prerequisites

1. **Python 3.11+** — Check: `python --version`
   - Install: https://python.org
2. **uv** (Python package manager) — Check: `uv --version`
   - Install:
     ```bash
     # macOS / Linux
     curl -LsSf https://astral.sh/uv/install.sh | sh

     # Windows (PowerShell)
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
3. **Claude Code** CLI — already installed if you're reading this

### Quick Start (3 minutes)

```bash
# 1. Clone
git clone https://github.com/your-org/archflow.git
cd archflow

# 2. Run interactive installer
bash scripts/install.sh
```

The installer will:
1. Install Python dependencies
2. Ask for your API credentials (Jira, GitHub, Google Drive)
3. Auto-detect existing Jira config from Claude Code
4. Register MCP server + 6 slash commands
5. Generate config template

```bash
# 3. Edit project settings (use any editor)
code archflow.config.yml     # VS Code
# or: notepad archflow.config.yml  (Windows)
# or: nano archflow.config.yml     (Mac/Linux)

# 4. Restart Claude Code — done!
```

> **Partial setup OK**: GitHub or Google Drive credentials can be skipped. ArchFlow works with whatever sources are configured — unconfigured sources return "not configured" instead of crashing.

---

## Available Tools

### Jira (7 tools)

| Tool | Description |
|------|-------------|
| `archflow_jira_get_issue` | Full issue detail (comments, links, subtasks) |
| `archflow_jira_sprint_status` | Current sprint grouped by status |
| `archflow_jira_search` | JQL search |
| `archflow_jira_user_workload` | Issues assigned to a specific user |
| `archflow_jira_component_status` | Component progress with % done |
| `archflow_jira_recent_activity` | Recently updated issues (last N days) |
| `archflow_jira_epic_progress` | Epic children + completion rate |

### GitHub (6 tools)

| Tool | Description |
|------|-------------|
| `archflow_github_get_pr` | PR detail with diff stats |
| `archflow_github_list_prs` | List PRs (filter by state/author/branch) |
| `archflow_github_pr_for_issue` | Find PRs referencing a Jira issue key |
| `archflow_github_recent_commits` | Recent commits on a branch |
| `archflow_github_search_code` | Code search in a repo |
| `archflow_github_repo_overview` | Repo summary (language, activity) |

### Draw.io / Architecture (4 tools)

| Tool | Description |
|------|-------------|
| `archflow_drawio_list_diagrams` | List .drawio files from Google Drive |
| `archflow_drawio_get_diagram` | Parse diagram into nodes + edges |
| `archflow_drawio_search_nodes` | Search nodes by label |
| `archflow_drawio_node_connections` | Get a node's inbound/outbound connections |

### Cross-Source Intelligence (5 tools)

| Tool | Description |
|------|-------------|
| `archflow_trace_issue` | Issue → PRs + code + diagram nodes |
| `archflow_trace_component` | Architecture component → issues + PRs + connections |
| `archflow_project_overview` | Sprint + architecture + GitHub activity combined |
| `archflow_team_activity` | Weekly team report across all sources |
| `archflow_onboarding_context` | Everything a new member needs to know |

### Search (1 tool)

| Tool | Description |
|------|-------------|
| `archflow_search` | Unified search across Jira + GitHub + diagrams |

---

## Slash Commands

After installation, these commands are available in Claude Code:

| Command | For | Example |
|---------|-----|---------|
| `/status` | Everyone | "How far is the auth feature?" |
| `/trace` | Developers | "Where's the code for KAN-123?" |
| `/arch` | Everyone | "What connects to Auth Service?" |
| `/onboard` | New members | "Give me a project overview" |
| `/report` | CEO / PM | "Weekly team activity report" |
| `/search` | Everyone | "Find everything related to Redis" |

---

## Configuration

### `archflow.config.yml`

```yaml
jira:
  url: "https://your-domain.atlassian.net"
  projects:
    - "KAN"           # Multiple projects supported
    - "FRONT"
  board_id: "1"

github:
  repos:
    - "your-org/backend-api"    # Multiple repos supported
    - "your-org/frontend-web"
  default_branch: "main"

gdrive:
  folder_id: "1abc123..."      # Google Drive folder with .drawio files
  cache_ttl_minutes: 30

matching:
  explicit:                     # Manual: diagram node → Jira/GitHub mapping
    - diagram_node: "Auth Service"
      jira_component: "authentication"
      github_path_prefix: "src/auth/"
  auto_match:
    enabled: true
    strategy: "fuzzy"           # exact | fuzzy | contains
    min_score: 0.7
```

### Environment Variables

| Variable | Required | Source |
|----------|----------|--------|
| `JIRA_URL` or `JIRA_INSTANCE_URL` | For Jira | Atlassian Settings |
| `JIRA_EMAIL` or `JIRA_USER_EMAIL` | For Jira | Your email |
| `JIRA_API_TOKEN` or `JIRA_API_KEY` | For Jira | See guide below |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | For GitHub | See guide below |
| `GOOGLE_CLIENT_ID` | For Draw.io | See guide below |
| `GOOGLE_CLIENT_SECRET` | For Draw.io | Google Cloud Console |
| `GOOGLE_REFRESH_TOKEN` | For Draw.io | OAuth flow |

### Token Setup Guide

<details>
<summary><strong>Jira API Token (2 min)</strong></summary>

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Enter label (e.g., `archflow`)
4. Click **"Create"** — token appears
5. Copy and paste into installer

</details>

<details>
<summary><strong>GitHub Personal Access Token (2 min)</strong></summary>

1. Go to https://github.com/settings/tokens?type=beta
2. Click **"Generate new token"**
3. Set name (e.g., `archflow`)
4. Set permissions:
   - **Repository access**: Select repos (or All repositories)
   - **Permissions > Repository permissions**:
     - Contents: **Read-only**
     - Pull requests: **Read-only**
     - Metadata: **Read-only**
5. Click **"Generate token"** — copy it

</details>

<details>
<summary><strong>Google Drive OAuth (10 min, only for Draw.io)</strong></summary>

1. Go to https://console.cloud.google.com/
2. Create new project (or select existing)
3. **APIs & Services > Library** — search "Google Drive API" — **Enable**
4. **APIs & Services > Credentials** — **Create Credentials > OAuth client ID**
   - Application type: **Desktop app**
   - Name: `archflow`
5. Copy **Client ID** and **Client Secret**
6. Get Refresh Token (via OAuth Playground):
   - Go to https://developers.google.com/oauthplayground/
   - Settings (gear icon) — check "Use your own OAuth credentials"
   - Enter Client ID and Secret from step 5
   - Step 1: Select `https://www.googleapis.com/auth/drive.readonly` — Authorize
   - Step 2: Click **"Exchange authorization code for tokens"**
   - Copy the **Refresh token**

</details>

---

## Architecture

```
User Question
     ↓
┌─────────────────────────────────┐
│        ArchFlow MCP Server       │
│                                   │
│  ┌─────────┐  ┌──────────────┐  │
│  │  Cache   │  │   Matcher    │  │
│  │ (TTL)    │  │ (cross-src)  │  │
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

**Token efficiency**: All API responses are cached with TTL. Same question = 0 API calls on repeat.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Server not appearing in Claude Code | Check `~/.claude/.mcp.json` syntax: `python3 -m json.tool ~/.claude/.mcp.json` |
| "Jira not configured" | Verify env vars: `JIRA_URL` (or `JIRA_INSTANCE_URL`) must be set |
| "GitHub not configured" | Set `GITHUB_PERSONAL_ACCESS_TOKEN` in MCP config |
| Draw.io files not found | Verify `folder_id` in `archflow.config.yml` and Google OAuth tokens |
| Stale data | Cache TTL is 30min by default. Restart server to clear. |
| Rate limited (GitHub) | GitHub Search API: 30 req/min. Use cached results. |

### Validate Setup

```bash
# Check MCP config is valid JSON
python3 -m json.tool ~/.claude/.mcp.json

# Test server starts without errors
cd archflow && uv run archflow
# (Ctrl+C to stop — if no errors, it works)

# Run tests
uv run python -m pytest tests/ -v
```

---

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run python -m pytest tests/ -v

# Lint
uv run ruff check src/
```

### Project Structure

```
src/archflow/
├── server.py          # MCP server entry point
├── clients/           # HTTP clients (Jira, GitHub, Google Drive)
├── providers/         # Business logic per source
├── core/              # Config, cache, matcher, models
└── tools/             # MCP tool registrations (23 tools)
```

---

## License

MIT

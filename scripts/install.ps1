# ArchFlow - Context Hub MCP Server Installer (Windows)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\install.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$McpConfig = Join-Path $env:USERPROFILE ".claude\.mcp.json"

Write-Host ""
Write-Host "  +==================================+" -ForegroundColor Cyan
Write-Host "  |   ArchFlow - Context Hub Setup   |" -ForegroundColor Cyan
Write-Host "  +==================================+" -ForegroundColor Cyan
Write-Host ""

# ==========================================================================
# Step 0: Python version check
# ==========================================================================
Write-Host "[0/4] Python version check..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "  Python 3.11+ required. Current: $pythonVersion" -ForegroundColor Red
            Write-Host "  Download: https://python.org" -ForegroundColor Red
            exit 1
        }
        Write-Host "  $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  Python not found. Install Python 3.11+ from https://python.org" -ForegroundColor Red
    exit 1
}

# ==========================================================================
# Step 1: Install dependencies
# ==========================================================================
Write-Host ""
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow

Push-Location $ProjectDir
try {
    $uvExists = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvExists) {
        uv sync 2>$null
        Write-Host "  Done (uv sync)." -ForegroundColor Green
    } else {
        Write-Host "  uv not found. Using pip..." -ForegroundColor DarkYellow
        pip install -e . 2>$null
        Write-Host "  Done (pip install)." -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# ==========================================================================
# Step 2: Collect credentials (interactive)
# ==========================================================================
Write-Host ""
Write-Host "[2/4] API Credentials Setup" -ForegroundColor Yellow
Write-Host ""

# --- Detect existing Jira config ---
$ExistingJiraUrl = ""
$ExistingJiraEmail = ""
$ExistingJiraToken = ""

if (Test-Path $McpConfig) {
    try {
        $mcpData = Get-Content $McpConfig -Raw | ConvertFrom-Json
        $jiraEnv = $mcpData.mcpServers.jira.env
        if ($jiraEnv) {
            $ExistingJiraUrl = $jiraEnv.JIRA_INSTANCE_URL
            $ExistingJiraEmail = $jiraEnv.JIRA_USER_EMAIL
            $ExistingJiraToken = $jiraEnv.JIRA_API_KEY
        }
    } catch { }
}

# --- Jira ---
Write-Host "  -- Jira Cloud --" -ForegroundColor White
$JiraUrl = ""
$JiraEmail = ""
$JiraToken = ""

if ($ExistingJiraUrl) {
    Write-Host "  Existing Jira config found: $ExistingJiraUrl"
    $useExisting = Read-Host "  Use existing config? (Y/n)"
    if (-not $useExisting -or $useExisting -match "^[Yy]") {
        $JiraUrl = $ExistingJiraUrl
        $JiraEmail = $ExistingJiraEmail
        $JiraToken = $ExistingJiraToken
    }
}

if (-not $JiraUrl) {
    $JiraUrl = Read-Host "  Jira URL (e.g., https://your-domain.atlassian.net)"
    $JiraEmail = Read-Host "  Jira email"
    $JiraTokenSecure = Read-Host "  Jira API token" -AsSecureString
    $JiraToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($JiraTokenSecure)
    )
}
Write-Host ""

# --- GitHub ---
Write-Host "  -- GitHub --" -ForegroundColor White
$GithubToken = Read-Host "  GitHub Personal Access Token (Enter to skip)"
Write-Host ""

# --- Google Drive ---
Write-Host "  -- Google Drive (Draw.io diagrams) --" -ForegroundColor White
$GoogleClientId = Read-Host "  Google Client ID (Enter to skip)"
$GoogleClientSecret = ""
$GoogleRefreshToken = ""

if ($GoogleClientId) {
    $GoogleClientSecretSecure = Read-Host "  Google Client Secret" -AsSecureString
    $GoogleClientSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($GoogleClientSecretSecure)
    )
    $GoogleRefreshToken = Read-Host "  Google Refresh Token"
}
Write-Host ""

# ==========================================================================
# Step 3: Register Skills + MCP config
# ==========================================================================
Write-Host "[3/4] Registering Claude Code config..." -ForegroundColor Yellow

# Copy skills
$skillDirs = Get-ChildItem "$ProjectDir\skills\archflow-*" -Directory -ErrorAction SilentlyContinue
foreach ($skillDir in $skillDirs) {
    $skillName = $skillDir.Name
    $target = Join-Path $SkillsDir $skillName
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item "$($skillDir.FullName)\SKILL.md" "$target\SKILL.md" -Force
    Write-Host "  Skill installed: /$skillName" -ForegroundColor DarkGray
}

# MCP server config
$mcpDir = Split-Path $McpConfig -Parent
if (-not (Test-Path $mcpDir)) {
    New-Item -ItemType Directory -Path $mcpDir -Force | Out-Null
}

$config = @{}
if (Test-Path $McpConfig) {
    try {
        $config = Get-Content $McpConfig -Raw | ConvertFrom-Json -AsHashtable
    } catch {
        $config = @{}
    }
}

if (-not $config.ContainsKey("mcpServers")) {
    $config["mcpServers"] = @{}
}

$env = @{
    "PYTHONUNBUFFERED" = "1"
    "ARCHFLOW_CONFIG_PATH" = Join-Path $ProjectDir "archflow.config.yml"
}

if ($JiraUrl) {
    $env["JIRA_INSTANCE_URL"] = $JiraUrl
    $env["JIRA_USER_EMAIL"] = $JiraEmail
    $env["JIRA_API_KEY"] = $JiraToken
}
if ($GithubToken) {
    $env["GITHUB_PERSONAL_ACCESS_TOKEN"] = $GithubToken
}
if ($GoogleClientId) {
    $env["GOOGLE_CLIENT_ID"] = $GoogleClientId
    $env["GOOGLE_CLIENT_SECRET"] = $GoogleClientSecret
    $env["GOOGLE_REFRESH_TOKEN"] = $GoogleRefreshToken
}

$config["mcpServers"]["archflow"] = @{
    "command" = "uv"
    "args" = @("--directory", $ProjectDir, "run", "archflow")
    "env" = $env
}

$config | ConvertTo-Json -Depth 10 | Set-Content $McpConfig -Encoding UTF8
Write-Host "  MCP server registered." -ForegroundColor Green

# ==========================================================================
# Step 4: Project config file
# ==========================================================================
Write-Host ""
Write-Host "[4/4] Project config..." -ForegroundColor Yellow

$configFile = Join-Path $ProjectDir "archflow.config.yml"
$exampleFile = Join-Path $ProjectDir "archflow.config.example.yml"

if (-not (Test-Path $configFile)) {
    Copy-Item $exampleFile $configFile
    Write-Host "  archflow.config.yml created (edit your projects/repos)" -ForegroundColor Green
} else {
    Write-Host "  archflow.config.yml already exists" -ForegroundColor DarkGray
}

# ==========================================================================
# Done
# ==========================================================================
Write-Host ""
Write-Host "  +==================================+" -ForegroundColor Green
Write-Host "  |        Setup Complete!           |" -ForegroundColor Green
Write-Host "  +==================================+" -ForegroundColor Green
Write-Host ""
Write-Host "  Connected sources:" -ForegroundColor White
if ($JiraUrl)        { Write-Host "    [OK] Jira: $JiraUrl" -ForegroundColor Green }
else                 { Write-Host "    [--] Jira: not configured" -ForegroundColor DarkGray }
if ($GithubToken)    { Write-Host "    [OK] GitHub: connected" -ForegroundColor Green }
else                 { Write-Host "    [--] GitHub: not configured (add later)" -ForegroundColor DarkGray }
if ($GoogleClientId) { Write-Host "    [OK] Google Drive: connected" -ForegroundColor Green }
else                 { Write-Host "    [--] Google Drive: not configured (add later)" -ForegroundColor DarkGray }

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Edit archflow.config.yml (set your projects/repos)" -ForegroundColor White
Write-Host "    2. Restart Claude Code" -ForegroundColor White
Write-Host "    3. Try: /status or /onboard" -ForegroundColor White
Write-Host ""

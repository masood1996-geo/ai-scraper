# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI Scraper — One-Command Installer (Windows PowerShell)
#  https://github.com/masood1996-geo/ai-scraper
#
#  Usage:
#    irm https://raw.githubusercontent.com/masood1996-geo/ai-scraper/main/install.ps1 | iex
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ErrorActionPreference = "Continue"

# ── Helpers ───────────────────────────────────────────────────────────
function Write-Info    { param($msg) Write-Host "  ℹ  $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  ✓  $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  ⚠  $msg" -ForegroundColor Yellow }
function Write-Fail    { param($msg) Write-Host "  ✗  $msg" -ForegroundColor Red }
function Write-Step    { param($msg) Write-Host "`n── $msg ──" -ForegroundColor White }

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# ── Banner ────────────────────────────────────────────────────────────
function Show-Banner {
    Write-Host ""
    Write-Host "   █████╗ ██╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ " -ForegroundColor Cyan
    Write-Host "  ██╔══██╗██║    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗" -ForegroundColor Cyan
    Write-Host "  ███████║██║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝" -ForegroundColor Cyan
    Write-Host "  ██╔══██║██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗" -ForegroundColor Cyan
    Write-Host "  ██║  ██║██║    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║" -ForegroundColor Cyan
    Write-Host "  ╚═╝  ╚═╝╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Universal AI-Powered Web Data Extraction Engine" -ForegroundColor DarkGray
    Write-Host "  https://github.com/masood1996-geo/ai-scraper" -ForegroundColor DarkGray
    Write-Host ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 1: DETECT PYTHON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$script:PythonCmd = $null

function Find-Python {
    Write-Step "Checking Python"

    foreach ($cmd in @("python", "python3", "py")) {
        if (Test-CommandExists $cmd) {
            try {
                $versionOutput = & $cmd --version 2>&1
                if ($versionOutput -match "(\d+)\.(\d+)\.(\d+)") {
                    $major = [int]$Matches[1]
                    $minor = [int]$Matches[2]
                    if ($major -ge 3 -and $minor -ge 10) {
                        Write-Success "Python $major.$minor.$($Matches[3])"
                        $script:PythonCmd = $cmd
                        return
                    }
                }
            } catch {}
        }
    }

    Write-Fail "Python 3.10+ not found"
    Write-Info "Installing Python automatically..."

    if (Test-CommandExists "winget") {
        cmd /c "winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements 2>&1"
    } elseif (Test-CommandExists "choco") {
        cmd /c "choco install python312 -y 2>&1"
    } else {
        Write-Fail "Cannot auto-install Python. Please install from https://python.org"
        Write-Fail "IMPORTANT: Check 'Add Python to PATH' during installation!"
        exit 1
    }

    # Re-detect
    foreach ($cmd in @("python", "python3", "py")) {
        if (Test-CommandExists $cmd) {
            $script:PythonCmd = $cmd
            Write-Success "Python installed"
            return
        }
    }

    Write-Fail "Python installed but not found in PATH. Restart terminal and re-run."
    exit 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 2: DETECT GIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Find-Git {
    Write-Step "Checking Git"

    if (Test-CommandExists "git") {
        $v = & git --version 2>&1
        Write-Success "Git $($v -replace 'git version ','')"
        return
    }

    Write-Info "Installing Git automatically..."
    if (Test-CommandExists "winget") {
        cmd /c "winget install Git.Git --accept-package-agreements --accept-source-agreements 2>&1"
    } elseif (Test-CommandExists "choco") {
        cmd /c "choco install git -y 2>&1"
    } else {
        Write-Fail "Cannot auto-install Git. Please install from https://git-scm.com"
        exit 1
    }
    Write-Success "Git installed"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 3: ASK FOR API KEY (only user interaction)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Get-ApiKey {
    Write-Step "API Key Configuration"

    # Check if already set
    if ($env:OPENROUTER_API_KEY -or $env:OPENAI_API_KEY -or
        $env:KILO_API_KEY -or $env:AI_SCRAPER_API_KEY) {
        Write-Success "API key already configured"
        return
    }

    Write-Host ""
    Write-Host "  AI Scraper needs an LLM API key to extract data." -ForegroundColor White
    Write-Host ""
    Write-Host "    1) OpenRouter  " -NoNewline; Write-Host "(recommended — free models at https://openrouter.ai/keys)" -ForegroundColor DarkGray
    Write-Host "    2) OpenAI     " -NoNewline; Write-Host "(GPT-4o, paid — https://platform.openai.com/api-keys)" -ForegroundColor DarkGray
    Write-Host "    3) Kilo       " -NoNewline; Write-Host "(free tier — https://kilo.ai)" -ForegroundColor DarkGray
    Write-Host "    4) Ollama     " -NoNewline; Write-Host "(free, local — no key needed)" -ForegroundColor DarkGray
    Write-Host "    5) Skip" -ForegroundColor DarkGray
    Write-Host ""

    $choice = Read-Host "  Choose provider [1-5]"

    $envVar = $null
    switch ($choice) {
        "1" { $envVar = "OPENROUTER_API_KEY" }
        "2" { $envVar = "OPENAI_API_KEY" }
        "3" { $envVar = "KILO_API_KEY" }
        "4" {
            Write-Success "Ollama selected — no key needed"
            Write-Info "Make sure Ollama is running: ollama serve"
            return
        }
        default {
            Write-Warn "Skipping — set API key later via environment variable"
            return
        }
    }

    $apiKey = Read-Host "  Enter your API key"
    if ($apiKey) {
        [Environment]::SetEnvironmentVariable($envVar, $apiKey, "Process")
        [Environment]::SetEnvironmentVariable($envVar, $apiKey, "User")
        Write-Success "API key saved"
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 4: INSTALL AI SCRAPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Install-AIScraper {
    Write-Step "Installing AI Scraper"

    $installDir = Join-Path $HOME "ai-scraper"

    if (Test-Path $installDir) {
        Write-Info "Updating existing installation..."
        Push-Location $installDir
        cmd /c "git pull origin main 2>&1"
        Pop-Location
    } else {
        Write-Info "Downloading AI Scraper..."
        cmd /c "git clone https://github.com/masood1996-geo/ai-scraper.git `"$installDir`" 2>&1"
        if (-not (Test-Path $installDir)) {
            Write-Fail "Download failed"
            return
        }
    }

    Push-Location $installDir
    Write-Info "Installing dependencies..."
    cmd /c "$($script:PythonCmd) -m pip install . --user 2>&1"

    # Verify
    $check = cmd /c "$($script:PythonCmd) -c `"from ai_scraper import AIScraper; print('OK')`" 2>&1"
    Pop-Location

    if ($check -match "OK") {
        Write-Success "AI Scraper installed"
    } else {
        Write-Warn "AI Scraper installed with warnings"
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 5: INSTALL & START OPEN WEBUI VIA DOCKER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$script:OpenWebUIPort = 3000

function Test-OpenWebUIRunning {
    foreach ($port in @(3000, 8080)) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$port" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($r.StatusCode -eq 200) {
                $script:OpenWebUIPort = $port
                return $true
            }
        } catch {}
    }
    return $false
}

function Test-DockerRunning {
    $dockerInfo = cmd /c "docker info 2>&1"
    return ($dockerInfo -match "Server Version" -or $dockerInfo -match "Containers")
}

function Install-And-Start-OpenWebUI {
    Write-Step "Setting up Open WebUI (GUI Interface)"

    # Already running?
    if (Test-OpenWebUIRunning) {
        Write-Success "Open WebUI already running at http://localhost:$($script:OpenWebUIPort)"
        return $true
    }

    # Check if there's an existing stopped container
    $existingContainer = cmd /c "docker ps -a --filter name=open-webui --format `"{{.Names}}`" 2>&1"
    if ($existingContainer -match "open-webui") {
        Write-Info "Found existing Open WebUI container, starting it..."
        cmd /c "docker start open-webui 2>&1"

        # Wait for it
        $waited = 0
        while ($waited -lt 60) {
            Start-Sleep -Seconds 3
            $waited += 3
            if (Test-OpenWebUIRunning) {
                Write-Success "Open WebUI is running!"
                return $true
            }
            Write-Host "." -NoNewline -ForegroundColor DarkGray
        }
    }

    # Check Docker availability
    $hasDocker = Test-CommandExists "docker"

    if (-not $hasDocker) {
        Write-Fail "Docker is required for Open WebUI"
        Write-Info "Install Docker Desktop from: https://docker.com/products/docker-desktop"
        Write-Info "After installing Docker, re-run this installer"
        return $false
    }

    # Start Docker Desktop if not running
    if (-not (Test-DockerRunning)) {
        Write-Info "Starting Docker Desktop..."
        try {
            Start-Process "Docker Desktop" -ErrorAction SilentlyContinue
        } catch {
            # Try alternative paths
            $dockerPaths = @(
                "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
                "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
            )
            foreach ($p in $dockerPaths) {
                if (Test-Path $p) {
                    Start-Process $p
                    break
                }
            }
        }

        Write-Info "Waiting for Docker to start..."
        $waited = 0
        while ($waited -lt 90) {
            Start-Sleep -Seconds 5
            $waited += 5
            if (Test-DockerRunning) {
                Write-Success "Docker is ready"
                break
            }
            Write-Host "." -NoNewline -ForegroundColor DarkGray
        }
        Write-Host ""

        if (-not (Test-DockerRunning)) {
            Write-Fail "Docker didn't start in time. Please start Docker Desktop manually and re-run."
            return $false
        }
    } else {
        Write-Success "Docker is running"
    }

    # Pull and run Open WebUI container
    Write-Info "Pulling Open WebUI image (first time takes 2-5 minutes)..."
    cmd /c "docker pull ghcr.io/open-webui/open-webui:main 2>&1"

    Write-Info "Starting Open WebUI container..."
    cmd /c "docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main 2>&1"

    # Wait for server to be ready
    Write-Info "Waiting for Open WebUI to start..."
    $maxWait = 120
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 3
        $waited += 3
        if (Test-OpenWebUIRunning) {
            Write-Host ""
            Write-Success "Open WebUI is running!"
            return $true
        }
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Warn "Open WebUI is still starting — it may need a moment"
    Write-Info "Check http://localhost:3000 in a minute"
    return $false
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 6: AUTO-CONFIGURE OPEN WEBUI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Configure-OpenWebUI {
    param([bool]$ServerReady)

    Write-Step "Configuring Open WebUI"

    if (-not $ServerReady) {
        Write-Warn "Server not ready yet — skipping auto-configuration"
        Write-Info "Open http://localhost:$($script:OpenWebUIPort) once the server starts"
        return
    }

    $baseUrl = "http://localhost:$($script:OpenWebUIPort)"
    $token = $null

    # Auto-create admin account
    Write-Info "Creating admin account..."
    $signupBody = @{
        name     = "Admin"
        email    = "admin@ai-scraper.local"
        password = "aiscraper2024"
    } | ConvertTo-Json

    try {
        $signup = Invoke-RestMethod -Uri "$baseUrl/api/v1/auths/signup" `
            -Method POST -Body $signupBody -ContentType "application/json" -ErrorAction Stop
        $token = $signup.token
        Write-Success "Admin account created"
    } catch {
        # Account might already exist — try sign in
        try {
            $loginBody = @{
                email    = "admin@ai-scraper.local"
                password = "aiscraper2024"
            } | ConvertTo-Json

            $login = Invoke-RestMethod -Uri "$baseUrl/api/v1/auths/signin" `
                -Method POST -Body $loginBody -ContentType "application/json" -ErrorAction Stop
            $token = $login.token
            Write-Success "Logged into existing account"
        } catch {
            Write-Warn "Could not auto-create account — create one at $baseUrl"
        }
    }

    # Auto-install AI Scraper tool
    if ($token) {
        Write-Info "Installing AI Scraper tool..."
        $toolFile = Join-Path $HOME "ai-scraper" "open_webui_tool.py"

        if (Test-Path $toolFile) {
            $toolContent = Get-Content $toolFile -Raw

            $toolBody = @{
                id      = "ai_scraper_tool"
                name    = "AI Scraper"
                content = $toolContent
                meta    = @{
                    description = "AI-powered web scraping — extract data from any website"
                }
            } | ConvertTo-Json -Depth 5

            $headers = @{ Authorization = "Bearer $token" }

            try {
                Invoke-RestMethod -Uri "$baseUrl/api/v1/tools/create" `
                    -Method POST -Body $toolBody -ContentType "application/json" `
                    -Headers $headers -ErrorAction Stop | Out-Null
                Write-Success "AI Scraper tool installed in Open WebUI!"
            } catch {
                try {
                    Invoke-RestMethod -Uri "$baseUrl/api/v1/tools/id/ai_scraper_tool/update" `
                        -Method POST -Body $toolBody -ContentType "application/json" `
                        -Headers $headers -ErrorAction Stop | Out-Null
                    Write-Success "AI Scraper tool updated in Open WebUI!"
                } catch {
                    Write-Warn "Could not auto-install tool — add it manually from Workspace > Tools"
                    try { Get-Content $toolFile -Raw | Set-Clipboard; Write-Info "Tool code copied to clipboard" } catch {}
                }
            }
        }
    }

    # Final output
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "  ✅ AI Scraper is ready!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""

    if ($token) {
        Write-Host "  Opening Open WebUI in your browser..." -ForegroundColor White
        Write-Host ""
        Write-Host "  Login with:" -ForegroundColor White
        Write-Host "    Email:    " -NoNewline; Write-Host "admin@ai-scraper.local" -ForegroundColor Cyan
        Write-Host "    Password: " -NoNewline; Write-Host "aiscraper2024" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  The AI Scraper tool is already installed." -ForegroundColor Green
        Write-Host "  Just start a new chat and scrape any website!" -ForegroundColor White
    } else {
        Write-Host "  Open WebUI is running at:" -ForegroundColor White
        Write-Host "    http://localhost:$($script:OpenWebUIPort)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1) Create an account" -ForegroundColor White
        Write-Host "  2) Go to Workspace > Tools > + Add Tool" -ForegroundColor White
        Write-Host "  3) Paste the tool code (already in your clipboard)" -ForegroundColor White
    }

    Write-Host ""
    Write-Host "  Documentation: " -NoNewline; Write-Host "https://github.com/masood1996-geo/ai-scraper" -ForegroundColor DarkGray
    Write-Host ""

    # Launch browser
    Start-Process "http://localhost:$($script:OpenWebUIPort)"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Main {
    Show-Banner

    # Step 1: Python
    Find-Python

    # Step 2: Git
    Find-Git

    # Step 3: API Key (only user interaction)
    Get-ApiKey

    # Step 4: Install AI Scraper
    Install-AIScraper

    # Step 5: Install & Start Open WebUI (via Docker)
    $serverReady = Install-And-Start-OpenWebUI

    # Step 6: Auto-configure & launch browser
    Configure-OpenWebUI -ServerReady $serverReady
}

Main


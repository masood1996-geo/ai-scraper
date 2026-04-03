# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI Scraper — One-Command Installer (Windows PowerShell)
#  https://github.com/masood1996-geo/ai-scraper
#
#  Usage:
#    irm https://raw.githubusercontent.com/masood1996-geo/ai-scraper/main/install.ps1 | iex
#
#  Or locally:
#    .\install.ps1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$ErrorActionPreference = "Stop"

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

# ── Helpers ───────────────────────────────────────────────────────────
function Write-Info    { param($msg) Write-Host "  ℹ  $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  ✓  $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "  ⚠  $msg" -ForegroundColor Yellow }
function Write-Fail    { param($msg) Write-Host "  ✗  $msg" -ForegroundColor Red }
function Write-Step    { param($msg) Write-Host "`n── $msg ──" -ForegroundColor White }

function Prompt-YN {
    param([string]$Message, [bool]$Default = $true)
    $suffix = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $response = Read-Host "  $Message $suffix"
    if ([string]::IsNullOrWhiteSpace($response)) {
        return $Default
    }
    return $response -match "^[Yy]"
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEPENDENCY CHECKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$script:PythonCmd = $null
$script:PipCmd = $null
$script:MissingDeps = @()
$script:ChromeMissing = $false

function Check-Python {
    Write-Step "Checking Python"

    $pyCmds = @("python", "python3", "py")
    foreach ($cmd in $pyCmds) {
        if (Test-CommandExists $cmd) {
            try {
                $versionOutput = & $cmd --version 2>&1
                if ($versionOutput -match "(\d+)\.(\d+)\.(\d+)") {
                    $major = [int]$Matches[1]
                    $minor = [int]$Matches[2]
                    $patch = $Matches[3]
                    if ($major -ge 3 -and $minor -ge 10) {
                        Write-Success "Python $major.$minor.$patch (>=3.10 required)"
                        $script:PythonCmd = $cmd
                        return $true
                    }
                }
            } catch {}
        }
    }

    Write-Fail "Python 3.10+ not found"
    $script:MissingDeps += "python"
    return $false
}

function Check-Pip {
    Write-Step "Checking pip"

    if ($script:PythonCmd) {
        try {
            $pipVersion = & $script:PythonCmd -m pip --version 2>&1
            if ($pipVersion -match "pip \d+") {
                Write-Success "pip found: $($pipVersion -split "`n" | Select-Object -First 1)"
                $script:PipCmd = "$($script:PythonCmd) -m pip"
                return $true
            }
        } catch {}
    }

    if (Test-CommandExists "pip") {
        $pipVersion = & pip --version 2>&1
        Write-Success "pip found: $($pipVersion -split "`n" | Select-Object -First 1)"
        $script:PipCmd = "pip"
        return $true
    }

    Write-Fail "pip not found"
    $script:MissingDeps += "pip"
    return $false
}

function Check-Git {
    Write-Step "Checking Git"

    if (Test-CommandExists "git") {
        $gitVersion = & git --version 2>&1
        Write-Success "Git $($gitVersion -replace 'git version ','')"
        return $true
    }

    Write-Fail "Git not found"
    $script:MissingDeps += "git"
    return $false
}

function Check-Chrome {
    Write-Step "Checking Chrome / Chromium"

    $chromePaths = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    )

    foreach ($path in $chromePaths) {
        if (Test-Path $path) {
            try {
                $version = (Get-Item $path).VersionInfo.ProductVersion
                Write-Success "Chrome $version at $path"
                return $true
            } catch {
                Write-Success "Chrome found at $path"
                return $true
            }
        }
    }

    Write-Warn "Chrome/Chromium not detected (required for browser scraping)"
    $script:ChromeMissing = $true
    return $false
}

function Check-PythonPackages {
    Write-Step "Checking Python packages"

    $packages = @(
        @{Import="openai";                  Display="openai"},
        @{Import="bs4";                     Display="beautifulsoup4"},
        @{Import="lxml";                    Display="lxml"},
        @{Import="requests";                Display="requests"},
        @{Import="undetected_chromedriver";  Display="undetected-chromedriver"},
        @{Import="rich";                    Display="rich"},
        @{Import="click";                   Display="click"}
    )

    $installed = @()
    $missing = @()

    foreach ($pkg in $packages) {
        $result = & $script:PythonCmd -c "import $($pkg.Import)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $installed += $pkg.Display
        } else {
            $missing += $pkg.Display
        }
    }

    if ($installed.Count -gt 0) {
        Write-Success "Installed: $($installed -join ', ')"
    }
    if ($missing.Count -gt 0) {
        Write-Warn "Missing: $($missing -join ', ')"
        return $missing
    }

    Write-Success "All Python packages present"
    return @()
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INSTALLATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Install-MissingSystemDeps {
    if ($script:MissingDeps.Count -eq 0) { return }

    Write-Host ""
    Write-Warn "Missing system dependencies: $($script:MissingDeps -join ', ')"

    $hasWinget = Test-CommandExists "winget"
    $hasChoco  = Test-CommandExists "choco"

    foreach ($dep in $script:MissingDeps) {
        switch ($dep) {
            "python" {
                if (Prompt-YN "Install Python 3.12?") {
                    Write-Info "Installing Python..."
                    if ($hasWinget) {
                        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
                    } elseif ($hasChoco) {
                        choco install python312 -y
                    } else {
                        Write-Fail "No package manager found (winget or choco)."
                        Write-Info "Download Python from: https://python.org/downloads"
                        Write-Info "IMPORTANT: Check 'Add Python to PATH' during install!"
                        Read-Host "Press Enter after installing Python..."
                    }
                    Write-Success "Python installed — restart your terminal to use it"
                } else {
                    Write-Fail "Python is required. Install from https://python.org"
                    exit 1
                }
            }
            "pip" {
                Write-Info "Installing pip..."
                & $script:PythonCmd -m ensurepip --default-pip
                Write-Success "pip installed"
            }
            "git" {
                if (Prompt-YN "Install Git?") {
                    if ($hasWinget) {
                        winget install Git.Git --accept-package-agreements --accept-source-agreements
                    } elseif ($hasChoco) {
                        choco install git -y
                    } else {
                        Write-Info "Download Git from: https://git-scm.com/downloads"
                        Read-Host "Press Enter after installing Git..."
                    }
                    Write-Success "Git installed"
                } else {
                    Write-Fail "Git is required for installation."
                    exit 1
                }
            }
        }
    }
}

function Install-Chrome {
    if (-not $script:ChromeMissing) { return }

    Write-Host ""
    Write-Warn "Chrome is required for browser-based web scraping."

    if (Prompt-YN "Install Google Chrome?") {
        Write-Info "Installing Chrome..."
        if (Test-CommandExists "winget") {
            winget install Google.Chrome --accept-package-agreements --accept-source-agreements
        } elseif (Test-CommandExists "choco") {
            choco install googlechrome -y
        } else {
            Start-Process "https://google.com/chrome"
            Write-Info "Opening Chrome download page in your browser..."
            Read-Host "Press Enter after installing Chrome..."
        }
        Write-Success "Chrome installed"
    } else {
        Write-Warn "Skipping Chrome — browser scraping won't work without it."
    }
}

function Install-AIScraper {
    Write-Step "Installing AI Scraper"

    $installDir = Join-Path $HOME "ai-scraper"

    # Clone or update repo
    if (Test-Path $installDir) {
        Write-Info "Found existing installation at $installDir"
        if (Prompt-YN "Update existing installation?") {
            Push-Location $installDir
            & git pull origin main 2>&1 | Out-Host
            Pop-Location
            Write-Success "Updated to latest version"
        }
    } else {
        Write-Info "Cloning from GitHub..."
        & git clone https://github.com/masood1996-geo/ai-scraper.git $installDir 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Git clone failed"
            exit 1
        }
        Write-Success "Cloned to $installDir"
    }

    Push-Location $installDir

    # Strategy 1: Try pip install . (non-editable, most reliable)
    Write-Info "Installing package and dependencies..."

    $installSuccess = $false
    $ErrorActionPreference = "Continue"

    try {
        & $script:PythonCmd -m pip install "." --user 2>&1 | Out-Host
        if ($LASTEXITCODE -eq 0) {
            $installSuccess = $true
        }
    } catch {}

    # Strategy 2: If pyproject install fails, install deps directly
    if (-not $installSuccess) {
        Write-Warn "Package install failed — installing dependencies individually..."

        $deps = @(
            "openai>=1.0",
            "beautifulsoup4>=4.12",
            "lxml>=4.9",
            "requests>=2.31",
            "undetected-chromedriver>=3.5",
            "rich>=13.0",
            "click>=8.1"
        )

        $depString = $deps -join " "
        & $script:PythonCmd -m pip install $deps --user 2>&1 | Out-Host

        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Dependency installation failed"
            Write-Info "Try manually: $script:PythonCmd -m pip install $depString"
            Pop-Location
            return
        }

        # Add the package dir to PYTHONPATH so imports work
        $sitePkgs = & $script:PythonCmd -c "import site; print(site.getusersitepackages())" 2>&1
        Write-Info "Dependencies installed to: $sitePkgs"

        # Try editable install without build isolation (avoids setuptools backend issue)
        & $script:PythonCmd -m pip install -e "." --no-build-isolation --user 2>&1 | Out-Host
        if ($LASTEXITCODE -eq 0) {
            $installSuccess = $true
        } else {
            # Even if editable fails, deps are installed — user can import manually
            Write-Warn "Editable install skipped — dependencies are installed"
            Write-Info "You can import the package by adding $installDir to your PYTHONPATH"
            Write-Info "Or run: set PYTHONPATH=$installDir;%PYTHONPATH%"
        }
    }

    $ErrorActionPreference = "Stop"
    Pop-Location

    if ($installSuccess) {
        Write-Success "AI Scraper installed successfully"
    } else {
        Write-Warn "Package installed with warnings (dependencies are available)"
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API KEY SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Setup-ApiKey {
    Write-Step "API Key Configuration"

    # Check existing
    if ($env:OPENROUTER_API_KEY -or $env:OPENAI_API_KEY -or
        $env:KILO_API_KEY -or $env:AI_SCRAPER_API_KEY) {
        Write-Success "API key already configured via environment variable"
        return
    }

    Write-Host ""
    Write-Host "  AI Scraper needs an LLM API key to extract data." -ForegroundColor White
    Write-Host ""
    Write-Host "  Supported providers:" -ForegroundColor White
    Write-Host "    1) OpenRouter  " -NoNewline; Write-Host "(recommended — free models available)" -ForegroundColor DarkGray
    Write-Host "    2) OpenAI     " -NoNewline; Write-Host "(GPT-4o, paid)" -ForegroundColor DarkGray
    Write-Host "    3) Kilo       " -NoNewline; Write-Host "(free tier available)" -ForegroundColor DarkGray
    Write-Host "    4) Ollama     " -NoNewline; Write-Host "(free, local — no key needed)" -ForegroundColor DarkGray
    Write-Host "    5) Skip for now" -ForegroundColor DarkGray
    Write-Host ""

    $choice = Read-Host "  Choose provider [1-5]"

    $envVar = $null
    $envName = $null

    switch ($choice) {
        "1" {
            $envVar = "OPENROUTER_API_KEY"
            $envName = "OpenRouter"
            Write-Host "`n  Get your free key at: " -NoNewline; Write-Host "https://openrouter.ai/keys" -ForegroundColor Cyan
        }
        "2" {
            $envVar = "OPENAI_API_KEY"
            $envName = "OpenAI"
            Write-Host "`n  Get your key at: " -NoNewline; Write-Host "https://platform.openai.com/api-keys" -ForegroundColor Cyan
        }
        "3" {
            $envVar = "KILO_API_KEY"
            $envName = "Kilo"
            Write-Host "`n  Get your key at: " -NoNewline; Write-Host "https://kilo.ai" -ForegroundColor Cyan
        }
        "4" {
            Write-Success "Ollama selected — no API key needed"
            Write-Info "Make sure Ollama is running: ollama serve"
            return
        }
        default {
            Write-Warn "Skipping API key setup — configure later via environment variable"
            return
        }
    }

    if ($envVar) {
        Write-Host ""
        $apiKey = Read-Host "  Enter your $envName API key"

        if ($apiKey) {
            # Set for current session
            [Environment]::SetEnvironmentVariable($envVar, $apiKey, "Process")

            if (Prompt-YN "Save permanently (user environment variable)?") {
                [Environment]::SetEnvironmentVariable($envVar, $apiKey, "User")
                Write-Success "API key saved permanently"
                Write-Info "Restart your terminal to activate"
            } else {
                Write-Success "API key set for this session only"
            }
        } else {
            Write-Warn "No key entered — configure later"
        }
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VERIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Verify-Installation {
    Write-Step "Verifying Installation"

    # Check CLI
    if (Test-CommandExists "ai-scraper") {
        try {
            $version = & ai-scraper --version 2>&1
            Write-Success "CLI command available: ai-scraper $version"
        } catch {
            Write-Success "CLI command available"
        }
    } else {
        Write-Warn "CLI not in PATH yet — restart your terminal"
        Write-Info "Or run: $script:PythonCmd -m ai_scraper.cli"
    }

    # Check import
    $importCheck = & $script:PythonCmd -c "from ai_scraper import AIScraper; print('OK')" 2>&1
    if ($importCheck -match "OK") {
        Write-Success "Python package importable"
    } else {
        Write-Warn "Package import check failed"
    }

    # Summary
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "  ✅ AI Scraper installed successfully!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Quick Start:" -ForegroundColor White
    Write-Host ""
    Write-Host "    # Scrape a website" -ForegroundColor Cyan
    Write-Host '    ai-scraper scrape https://example.com/listings --schema apartments'
    Write-Host ""
    Write-Host "    # Ask a question about a page" -ForegroundColor Cyan
    Write-Host '    ai-scraper ask https://example.com "What products are listed?"'
    Write-Host ""
    Write-Host "    # Use in Python" -ForegroundColor Cyan
    Write-Host '    python -c "from ai_scraper import AIScraper, Schema; print(''Ready!'')"'
    Write-Host ""
    Write-Host "    # Open WebUI GUI" -ForegroundColor Cyan
    Write-Host "    Paste open_webui_tool.py into Workspace → Tools"
    Write-Host ""
    Write-Host "  Documentation: https://github.com/masood1996-geo/ai-scraper" -ForegroundColor DarkGray
    Write-Host ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Main {
    Show-Banner

    Write-Host "  This installer will check your system and set up AI Scraper." -ForegroundColor White
    Write-Host ""

    if (-not (Prompt-YN "Proceed with installation?")) {
        Write-Host "  Installation cancelled."
        return
    }

    # Phase 1: Check dependencies
    Check-Python | Out-Null
    Check-Pip    | Out-Null
    Check-Git    | Out-Null
    Check-Chrome | Out-Null

    # Phase 2: Install missing system deps
    Install-MissingSystemDeps

    # Re-detect after install if needed
    if (-not $script:PythonCmd) {
        foreach ($cmd in @("python", "python3", "py")) {
            if (Test-CommandExists $cmd) {
                $script:PythonCmd = $cmd
                break
            }
        }
    }
    if (-not $script:PipCmd -and $script:PythonCmd) {
        $script:PipCmd = "$($script:PythonCmd) -m pip"
    }

    # Phase 3: Chrome
    Install-Chrome

    # Phase 4: Clone and install
    Install-AIScraper

    # Phase 5: API key
    Setup-ApiKey

    # Phase 6: Verify
    Verify-Installation
}

Main

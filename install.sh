#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI Scraper — One-Command Installer
#  https://github.com/masood1996-geo/ai-scraper
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/masood1996-geo/ai-scraper/main/install.sh | bash
#
#  Or locally:
#    chmod +x install.sh && ./install.sh
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# ── Banner ────────────────────────────────────────────────────────────
banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "   █████╗ ██╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ "
    echo "  ██╔══██╗██║    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗"
    echo "  ███████║██║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝"
    echo "  ██╔══██║██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗"
    echo "  ██║  ██║██║    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║"
    echo "  ╚═╝  ╚═╝╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "${DIM}  Universal AI-Powered Web Data Extraction Engine${NC}"
    echo -e "${DIM}  https://github.com/masood1996-geo/ai-scraper${NC}"
    echo ""
}

# ── Helper functions ──────────────────────────────────────────────────
info()    { echo -e "  ${CYAN}ℹ${NC}  $1"; }
success() { echo -e "  ${GREEN}✓${NC}  $1"; }
warn()    { echo -e "  ${YELLOW}⚠${NC}  $1"; }
fail()    { echo -e "  ${RED}✗${NC}  $1"; }
step()    { echo -e "\n${BOLD}── $1 ──${NC}"; }

prompt_yn() {
    local msg="$1"
    local default="${2:-y}"
    local yn
    if [ "$default" = "y" ]; then
        read -rp "  $msg [Y/n] " yn
        yn="${yn:-y}"
    else
        read -rp "  $msg [y/N] " yn
        yn="${yn:-n}"
    fi
    case "$yn" in
        [Yy]*) return 0 ;;
        *) return 1 ;;
    esac
}

command_exists() {
    command -v "$1" &>/dev/null
}

# ── Detect OS ─────────────────────────────────────────────────────────
detect_os() {
    case "$(uname -s)" in
        Linux*)   OS="linux" ;;
        Darwin*)  OS="macos" ;;
        MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
        *)        OS="unknown" ;;
    esac
    echo "$OS"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEPENDENCY CHECKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MISSING_DEPS=()
OPTIONAL_MISSING=()

check_python() {
    step "Checking Python"

    local py_cmd=""
    if command_exists python3; then
        py_cmd="python3"
    elif command_exists python; then
        py_cmd="python"
    fi

    if [ -z "$py_cmd" ]; then
        fail "Python not found"
        MISSING_DEPS+=("python")
        return 1
    fi

    local py_version
    py_version=$($py_cmd --version 2>&1 | grep -oP '\d+\.\d+')
    local py_major py_minor
    py_major=$(echo "$py_version" | cut -d. -f1)
    py_minor=$(echo "$py_version" | cut -d. -f2)

    if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 10 ]; then
        success "Python $($py_cmd --version 2>&1 | grep -oP '\d+\.\d+\.\d+') ${DIM}(≥3.10 required)${NC}"
        PYTHON_CMD="$py_cmd"
        return 0
    else
        fail "Python $py_version found, but ≥3.10 is required"
        MISSING_DEPS+=("python>=3.10")
        return 1
    fi
}

check_pip() {
    step "Checking pip"

    local pip_cmd=""
    if command_exists pip3; then
        pip_cmd="pip3"
    elif command_exists pip; then
        pip_cmd="pip"
    elif $PYTHON_CMD -m pip --version &>/dev/null; then
        pip_cmd="$PYTHON_CMD -m pip"
    fi

    if [ -z "$pip_cmd" ]; then
        fail "pip not found"
        MISSING_DEPS+=("pip")
        return 1
    fi

    success "pip found: $($pip_cmd --version 2>&1 | head -1)"
    PIP_CMD="$pip_cmd"
    return 0
}

check_git() {
    step "Checking Git"

    if command_exists git; then
        success "Git $(git --version | grep -oP '\d+\.\d+\.\d+')"
        return 0
    else
        fail "Git not found"
        MISSING_DEPS+=("git")
        return 1
    fi
}

check_chrome() {
    step "Checking Chrome / Chromium"

    local chrome_found=false
    local chrome_path=""

    # Check common Chrome/Chromium locations
    for cmd in google-chrome google-chrome-stable chromium chromium-browser; do
        if command_exists "$cmd"; then
            chrome_found=true
            chrome_path="$cmd"
            break
        fi
    done

    # macOS specific paths
    if [ "$chrome_found" = false ] && [ "$(detect_os)" = "macos" ]; then
        if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
            chrome_found=true
            chrome_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        fi
    fi

    # Windows (WSL/Git Bash)
    if [ "$chrome_found" = false ]; then
        for path in \
            "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
            "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"; do
            if [ -f "$path" ]; then
                chrome_found=true
                chrome_path="$path"
                break
            fi
        done
    fi

    if [ "$chrome_found" = true ]; then
        local chrome_version
        chrome_version=$("$chrome_path" --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1 || echo "detected")
        success "Chrome/Chromium ${chrome_version} at ${DIM}${chrome_path}${NC}"
        return 0
    else
        warn "Chrome/Chromium not detected (required for browser-based scraping)"
        OPTIONAL_MISSING+=("chrome")
        return 1
    fi
}

check_python_packages() {
    step "Checking Python packages"

    local packages=("openai" "bs4" "lxml" "requests" "undetected_chromedriver" "rich" "click")
    local display=("openai" "beautifulsoup4" "lxml" "requests" "undetected-chromedriver" "rich" "click")
    local installed=()
    local missing=()

    for i in "${!packages[@]}"; do
        if $PYTHON_CMD -c "import ${packages[$i]}" 2>/dev/null; then
            installed+=("${display[$i]}")
        else
            missing+=("${display[$i]}")
        fi
    done

    if [ ${#installed[@]} -gt 0 ]; then
        success "Installed: ${installed[*]}"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        warn "Missing: ${missing[*]}"
        PACKAGES_TO_INSTALL=("${missing[@]}")
        return 1
    else
        success "All Python packages present"
        PACKAGES_TO_INSTALL=()
        return 0
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INSTALLATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

install_missing_system_deps() {
    local os
    os=$(detect_os)

    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        return 0
    fi

    echo ""
    warn "Missing system dependencies: ${MISSING_DEPS[*]}"

    if ! prompt_yn "Install missing system dependencies?"; then
        fail "Cannot proceed without: ${MISSING_DEPS[*]}"
        echo ""
        echo "  Install them manually and re-run this script."
        exit 1
    fi

    for dep in "${MISSING_DEPS[@]}"; do
        case "$dep" in
            python|python\>=3.10)
                info "Installing Python..."
                case "$os" in
                    macos)
                        if command_exists brew; then
                            brew install python@3.12
                        else
                            fail "Homebrew not found. Install Python from https://python.org"
                            exit 1
                        fi
                        ;;
                    linux)
                        if command_exists apt-get; then
                            sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
                        elif command_exists dnf; then
                            sudo dnf install -y python3 python3-pip
                        elif command_exists pacman; then
                            sudo pacman -S --noconfirm python python-pip
                        else
                            fail "Unknown package manager. Install Python 3.10+ manually from https://python.org"
                            exit 1
                        fi
                        ;;
                    *)
                        fail "Please install Python 3.10+ from https://python.org"
                        exit 1
                        ;;
                esac
                success "Python installed"
                ;;

            pip)
                info "Installing pip..."
                $PYTHON_CMD -m ensurepip --default-pip 2>/dev/null || \
                    curl -fsSL https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
                success "pip installed"
                ;;

            git)
                info "Installing Git..."
                case "$os" in
                    macos)  brew install git ;;
                    linux)
                        if command_exists apt-get; then
                            sudo apt-get install -y git
                        elif command_exists dnf; then
                            sudo dnf install -y git
                        elif command_exists pacman; then
                            sudo pacman -S --noconfirm git
                        fi
                        ;;
                esac
                success "Git installed"
                ;;
        esac
    done
}

install_chrome() {
    if [[ " ${OPTIONAL_MISSING[*]} " =~ " chrome " ]]; then
        echo ""
        warn "Chrome/Chromium is required for browser-based scraping."

        if prompt_yn "Install Chromium?"; then
            local os
            os=$(detect_os)
            info "Installing Chromium..."
            case "$os" in
                macos)
                    if command_exists brew; then
                        brew install --cask chromium
                    else
                        fail "Install Chrome from https://google.com/chrome"
                    fi
                    ;;
                linux)
                    if command_exists apt-get; then
                        sudo apt-get update && sudo apt-get install -y chromium-browser || \
                            sudo apt-get install -y chromium
                    elif command_exists dnf; then
                        sudo dnf install -y chromium
                    elif command_exists pacman; then
                        sudo pacman -S --noconfirm chromium
                    fi
                    ;;
            esac
            success "Chromium installed"
        else
            warn "Skipping Chrome install — browser scraping won't work without it."
            warn "Install later: https://google.com/chrome"
        fi
    fi
}

install_ai_scraper() {
    step "Installing AI Scraper"

    local install_dir="$HOME/ai-scraper"

    # Clone or update repo
    if [ -d "$install_dir" ]; then
        info "Found existing installation at $install_dir"
        if prompt_yn "Update existing installation?"; then
            cd "$install_dir"
            git pull origin main
            success "Updated to latest version"
        fi
    else
        info "Cloning from GitHub..."
        git clone https://github.com/masood1996-geo/ai-scraper.git "$install_dir"
        success "Cloned to $install_dir"
    fi

    cd "$install_dir"

    # Strategy 1: Try pip install . (non-editable, most reliable)
    info "Installing package and dependencies..."
    local install_ok=false

    set +e  # Don't exit on error during install attempts
    $PYTHON_CMD -m pip install "." --user 2>&1
    if [ $? -eq 0 ]; then
        install_ok=true
    fi

    # Strategy 2: If pyproject install fails, install deps directly
    if [ "$install_ok" = false ]; then
        warn "Package install failed — installing dependencies individually..."

        $PYTHON_CMD -m pip install --user \
            "openai>=1.0" \
            "beautifulsoup4>=4.12" \
            "lxml>=4.9" \
            "requests>=2.31" \
            "undetected-chromedriver>=3.5" \
            "rich>=13.0" \
            "click>=8.1" \
            2>&1

        if [ $? -ne 0 ]; then
            fail "Dependency installation failed"
            info "Try manually: $PYTHON_CMD -m pip install openai beautifulsoup4 lxml requests undetected-chromedriver rich click"
            set -e
            return 1
        fi

        # Try editable install without build isolation
        $PYTHON_CMD -m pip install -e "." --no-build-isolation --user 2>&1
        if [ $? -eq 0 ]; then
            install_ok=true
        else
            warn "Editable install skipped — dependencies are installed"
            info "Add $install_dir to PYTHONPATH to use as a library"
            info "export PYTHONPATH=\"$install_dir:\$PYTHONPATH\""
        fi
    fi

    set -e  # Re-enable exit on error

    if [ "$install_ok" = true ]; then
        success "AI Scraper installed successfully"
    else
        warn "Package installed with warnings (dependencies are available)"
    fi

    return 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API KEY SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

setup_api_key() {
    step "API Key Configuration"

    # Check if any API key is already set
    if [ -n "$OPENROUTER_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || \
       [ -n "$KILO_API_KEY" ] || [ -n "$AI_SCRAPER_API_KEY" ]; then
        success "API key already configured via environment variable"
        return 0
    fi

    echo ""
    echo -e "  ${BOLD}AI Scraper needs an LLM API key to extract data.${NC}"
    echo ""
    echo "  Supported providers:"
    echo -e "    ${CYAN}1)${NC} OpenRouter  ${DIM}(recommended — free models available)${NC}"
    echo -e "    ${CYAN}2)${NC} OpenAI     ${DIM}(GPT-4o, paid)${NC}"
    echo -e "    ${CYAN}3)${NC} Kilo       ${DIM}(free tier available)${NC}"
    echo -e "    ${CYAN}4)${NC} Ollama     ${DIM}(free, local — no API key needed)${NC}"
    echo -e "    ${CYAN}5)${NC} Skip for now"
    echo ""

    read -rp "  Choose provider [1-5]: " choice

    local env_var=""
    local env_name=""

    case "$choice" in
        1)
            env_var="OPENROUTER_API_KEY"
            env_name="OpenRouter"
            echo -e "\n  Get your free key at: ${CYAN}https://openrouter.ai/keys${NC}"
            ;;
        2)
            env_var="OPENAI_API_KEY"
            env_name="OpenAI"
            echo -e "\n  Get your key at: ${CYAN}https://platform.openai.com/api-keys${NC}"
            ;;
        3)
            env_var="KILO_API_KEY"
            env_name="Kilo"
            echo -e "\n  Get your key at: ${CYAN}https://kilo.ai${NC}"
            ;;
        4)
            success "Ollama selected — no API key needed"
            info "Make sure Ollama is running: ollama serve"
            return 0
            ;;
        5|"")
            warn "Skipping API key setup — configure later via environment variable"
            return 0
            ;;
    esac

    if [ -n "$env_var" ]; then
        echo ""
        read -rp "  Enter your $env_name API key: " api_key

        if [ -n "$api_key" ]; then
            # Determine shell config file
            local shell_rc=""
            if [ -f "$HOME/.zshrc" ]; then
                shell_rc="$HOME/.zshrc"
            elif [ -f "$HOME/.bashrc" ]; then
                shell_rc="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                shell_rc="$HOME/.bash_profile"
            fi

            if [ -n "$shell_rc" ]; then
                # Remove any existing entry
                sed -i.bak "/export ${env_var}=/d" "$shell_rc" 2>/dev/null || true
                # Add new entry
                echo "export ${env_var}=\"${api_key}\"" >> "$shell_rc"
                export "${env_var}=${api_key}"
                success "API key saved to $shell_rc"
                info "Run 'source $shell_rc' or open a new terminal to activate"
            else
                export "${env_var}=${api_key}"
                warn "Could not find shell config file. Key set for this session only."
                info "Add to your shell config: export ${env_var}=\"${api_key}\""
            fi
        else
            warn "No key entered — configure later"
        fi
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VERIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

verify_installation() {
    step "Verifying Installation"

    # Check CLI command
    if command_exists ai-scraper; then
        local version
        version=$(ai-scraper --version 2>&1 || echo "installed")
        success "CLI command available: ai-scraper $version"
    else
        warn "CLI command not in PATH — you may need to restart your terminal"
        info "Or run directly: python -m ai_scraper.cli"
    fi

    # Check Python import
    if $PYTHON_CMD -c "from ai_scraper import AIScraper; print('OK')" 2>/dev/null | grep -q "OK"; then
        success "Python package importable"
    else
        warn "Package import check failed — try: pip install ."
    fi

    # Summary
    echo ""
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${BOLD}  ✅ AI Scraper installed successfully!${NC}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

launch_open_webui() {
    step "Open WebUI Setup"

    local install_dir="$HOME/ai-scraper"
    local tool_file="$install_dir/open_webui_tool.py"

    if [ ! -f "$tool_file" ]; then
        warn "open_webui_tool.py not found in $install_dir"
        return
    fi

    # Copy tool content to clipboard
    if command_exists pbcopy; then
        cat "$tool_file" | pbcopy
        success "Tool code copied to clipboard!"
    elif command_exists xclip; then
        cat "$tool_file" | xclip -selection clipboard
        success "Tool code copied to clipboard!"
    elif command_exists xsel; then
        cat "$tool_file" | xsel --clipboard
        success "Tool code copied to clipboard!"
    else
        warn "Could not copy to clipboard — copy manually from: $tool_file"
    fi

    # Detect Open WebUI URL
    local open_webui_url=""
    for port in 3000 8080 8443; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" 2>/dev/null | grep -q "200"; then
            open_webui_url="http://localhost:$port"
            break
        fi
    done

    if [ -n "$open_webui_url" ]; then
        success "Open WebUI detected at $open_webui_url"
        echo ""
        echo -e "  ${BOLD}Opening Open WebUI in your browser...${NC}"
        echo ""
        echo -e "  ${CYAN}📋 The tool code is already in your clipboard!${NC}"
        echo -e "  ${BOLD}Follow these steps:${NC}"
        echo -e "    1) Go to ${CYAN}Workspace → Tools${NC}"
        echo -e "    2) Click ${CYAN}+ Add Tool${NC}"
        echo -e "    3) ${YELLOW}Ctrl+A${NC} to select all, then ${YELLOW}Ctrl+V${NC} to paste"
        echo -e "    4) Click ${CYAN}Save${NC}"
        echo -e "    5) Start a new chat and use the AI Scraper tools!"
        echo ""

        # Open browser
        if command_exists xdg-open; then
            xdg-open "$open_webui_url" 2>/dev/null &
        elif command_exists open; then
            open "$open_webui_url"
        fi
    else
        warn "Open WebUI not detected on localhost"
        echo ""
        echo -e "  ${CYAN}📋 The tool code is in your clipboard (if supported)${NC}"
        echo ""
        echo -e "  ${BOLD}To use AI Scraper with Open WebUI:${NC}"
        echo ""
        echo -e "  ${CYAN}Option 1: Docker (recommended)${NC}"
        echo "    docker run -d -p 3000:8080 --name open-webui ghcr.io/open-webui/open-webui:main"
        echo -e "    Then open: ${CYAN}http://localhost:3000${NC}"
        echo ""
        echo -e "  ${CYAN}Option 2: Pip install${NC}"
        echo "    pip install open-webui"
        echo "    open-webui serve"
        echo -e "    Then open: ${CYAN}http://localhost:8080${NC}"
        echo ""
        echo -e "  ${BOLD}After Open WebUI is running:${NC}"
        echo -e "    1) Go to ${CYAN}Workspace → Tools${NC}"
        echo -e "    2) Click ${CYAN}+ Add Tool${NC}"
        echo -e "    3) ${YELLOW}Ctrl+A${NC} to select all, then ${YELLOW}Ctrl+V${NC} to paste"
        echo -e "    4) Click ${CYAN}Save${NC}"
        echo ""
    fi

    echo ""
    echo -e "  ${BOLD}Quick CLI alternative (no Open WebUI needed):${NC}"
    echo ""
    echo -e "    ${CYAN}# Scrape a website${NC}"
    echo "    ai-scraper scrape https://example.com/listings --schema apartments"
    echo ""
    echo -e "    ${CYAN}# Ask a question about a page${NC}"
    echo "    ai-scraper ask https://example.com \"What products are listed?\""
    echo ""
    echo -e "  ${DIM}Documentation: https://github.com/masood1996-geo/ai-scraper${NC}"
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main() {
    banner

    echo -e "${BOLD}  This installer will check your system and set up AI Scraper.${NC}"
    echo ""

    if ! prompt_yn "Proceed with installation?"; then
        echo "  Installation cancelled."
        exit 0
    fi

    # Phase 1: Check dependencies
    check_python || true
    check_pip    || true
    check_git    || true
    check_chrome || true

    # Phase 2: Install missing system dependencies
    install_missing_system_deps

    # Re-detect after install
    if [ -z "$PYTHON_CMD" ]; then
        if command_exists python3; then PYTHON_CMD="python3"
        elif command_exists python; then PYTHON_CMD="python"
        fi
    fi
    if [ -z "$PIP_CMD" ]; then
        if command_exists pip3; then PIP_CMD="pip3"
        elif command_exists pip; then PIP_CMD="pip"
        else PIP_CMD="$PYTHON_CMD -m pip"
        fi
    fi

    # Phase 3: Install Chrome
    install_chrome

    # Phase 4: Clone and install AI Scraper
    install_ai_scraper

    # Phase 5: API key setup
    setup_api_key

    # Phase 6: Verify
    verify_installation

    # Phase 7: Open WebUI launch
    launch_open_webui
}

main "$@"


#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI Scraper — One-Command Installer (Linux / macOS / WSL)
#  https://github.com/masood1996-geo/ai-scraper
#
#  Usage:
#    curl -fsSL https://raw.githubusercontent.com/masood1996-geo/ai-scraper/main/install.sh | bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

info()    { echo -e "  ${CYAN}ℹ${NC}  $1"; }
success() { echo -e "  ${GREEN}✓${NC}  $1"; }
warn()    { echo -e "  ${YELLOW}⚠${NC}  $1"; }
fail()    { echo -e "  ${RED}✗${NC}  $1"; }
step()    { echo -e "\n${BOLD}── $1 ──${NC}"; }

command_exists() { command -v "$1" &>/dev/null; }

detect_os() {
    case "$(uname -s)" in
        Linux*)   echo "linux" ;;
        Darwin*)  echo "macos" ;;
        *)        echo "unknown" ;;
    esac
}

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 1: DETECT PYTHON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PYTHON_CMD=""

find_python() {
    step "Checking Python"

    for cmd in python3 python; do
        if command_exists "$cmd"; then
            local ver
            ver=$($cmd --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                success "Python $($cmd --version 2>&1 | grep -oP '\d+\.\d+\.\d+')"
                PYTHON_CMD="$cmd"
                return
            fi
        fi
    done

    fail "Python 3.10+ not found"
    info "Installing Python automatically..."
    local os
    os=$(detect_os)

    case "$os" in
        macos)
            if command_exists brew; then brew install python@3.12
            else fail "Install Homebrew first: https://brew.sh" && exit 1; fi ;;
        linux)
            if command_exists apt-get; then sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
            elif command_exists dnf; then sudo dnf install -y python3 python3-pip
            elif command_exists pacman; then sudo pacman -S --noconfirm python python-pip
            else fail "Install Python 3.10+ from https://python.org" && exit 1; fi ;;
        *) fail "Install Python 3.10+ from https://python.org" && exit 1 ;;
    esac

    if command_exists python3; then PYTHON_CMD="python3"
    elif command_exists python; then PYTHON_CMD="python"
    else fail "Python installed but not in PATH" && exit 1; fi
    success "Python installed"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 2: DETECT GIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

find_git() {
    step "Checking Git"

    if command_exists git; then
        success "Git $(git --version | grep -oP '\d+\.\d+\.\d+')"
        return
    fi

    info "Installing Git automatically..."
    local os
    os=$(detect_os)

    case "$os" in
        macos) brew install git ;;
        linux)
            if command_exists apt-get; then sudo apt-get install -y git
            elif command_exists dnf; then sudo dnf install -y git
            elif command_exists pacman; then sudo pacman -S --noconfirm git; fi ;;
    esac
    success "Git installed"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 3: ASK FOR API KEY (only user interaction)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

get_api_key() {
    step "API Key Configuration"

    if [ -n "$OPENROUTER_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || \
       [ -n "$KILO_API_KEY" ] || [ -n "$AI_SCRAPER_API_KEY" ]; then
        success "API key already configured"
        return
    fi

    echo ""
    echo -e "  ${BOLD}AI Scraper needs an LLM API key.${NC}"
    echo ""
    echo -e "    ${CYAN}1)${NC} OpenRouter  ${DIM}(recommended — free at https://openrouter.ai/keys)${NC}"
    echo -e "    ${CYAN}2)${NC} OpenAI     ${DIM}(GPT-4o, paid)${NC}"
    echo -e "    ${CYAN}3)${NC} Kilo       ${DIM}(free tier)${NC}"
    echo -e "    ${CYAN}4)${NC} Ollama     ${DIM}(free, local — no key)${NC}"
    echo -e "    ${CYAN}5)${NC} Skip"
    echo ""

    read -rp "  Choose provider [1-5]: " choice

    local env_var=""
    case "$choice" in
        1) env_var="OPENROUTER_API_KEY" ;;
        2) env_var="OPENAI_API_KEY" ;;
        3) env_var="KILO_API_KEY" ;;
        4) success "Ollama selected — no key needed"; return ;;
        *) warn "Skipping — set API key later"; return ;;
    esac

    read -rp "  Enter your API key: " api_key
    if [ -n "$api_key" ]; then
        local shell_rc=""
        if [ -f "$HOME/.zshrc" ]; then shell_rc="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then shell_rc="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then shell_rc="$HOME/.bash_profile"; fi

        export "${env_var}=${api_key}"
        if [ -n "$shell_rc" ]; then
            sed -i.bak "/export ${env_var}=/d" "$shell_rc" 2>/dev/null || true
            echo "export ${env_var}=\"${api_key}\"" >> "$shell_rc"
        fi
        success "API key saved"
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 4: INSTALL AI SCRAPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

install_ai_scraper() {
    step "Installing AI Scraper"

    local install_dir="$HOME/ai-scraper"

    if [ -d "$install_dir" ]; then
        info "Updating existing installation..."
        cd "$install_dir"
        git pull origin main 2>&1
    else
        info "Downloading AI Scraper..."
        git clone https://github.com/masood1996-geo/ai-scraper.git "$install_dir" 2>&1
    fi

    cd "$install_dir"

    info "Installing dependencies..."
    set +e
    $PYTHON_CMD -m pip install "." --user 2>&1

    local check
    check=$($PYTHON_CMD -c "from ai_scraper import AIScraper; print('OK')" 2>&1)
    set -e

    if echo "$check" | grep -q "OK"; then
        success "AI Scraper installed"
    else
        warn "AI Scraper installed with warnings"
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 5: INSTALL & START OPEN WEBUI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_open_webui_running() {
    curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080" 2>/dev/null | grep -q "200"
}

install_and_start_open_webui() {
    step "Setting up Open WebUI (GUI Interface)"

    if test_open_webui_running; then
        success "Open WebUI already running at http://localhost:8080"
        return 0
    fi

    # Check if installed
    if ! $PYTHON_CMD -c "import open_webui" 2>/dev/null; then
        info "Installing Open WebUI (this takes 2-5 minutes, please wait)..."
        echo ""
        $PYTHON_CMD -m pip install open-webui --user 2>&1
        echo ""

        if $PYTHON_CMD -c "import open_webui" 2>/dev/null; then
            success "Open WebUI installed"
        else
            fail "Open WebUI installation failed"
            info "Try manually: $PYTHON_CMD -m pip install open-webui"
            return 1
        fi
    else
        success "Open WebUI already installed"
    fi

    # Start server in background
    info "Starting Open WebUI server..."
    nohup $PYTHON_CMD -m open_webui.main serve > /dev/null 2>&1 &

    # Wait for ready
    info "Waiting for server to start..."
    local waited=0
    while [ $waited -lt 120 ]; do
        sleep 3
        waited=$((waited + 3))
        if test_open_webui_running; then
            success "Open WebUI is running!"
            return 0
        fi
        printf "." >&2
    done

    warn "Server is still starting — may need more time"
    return 1
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 6: AUTO-CONFIGURE OPEN WEBUI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

configure_open_webui() {
    local server_ready=$1
    step "Configuring Open WebUI"

    if [ "$server_ready" != "0" ]; then
        warn "Server not ready — skipping auto-configuration"
        info "Open http://localhost:8080 once the server starts"
        return
    fi

    local base_url="http://localhost:8080"
    local token=""

    # Auto-create admin account
    info "Creating admin account..."
    local signup_response
    signup_response=$(curl -s -X POST "$base_url/api/v1/auths/signup" \
        -H "Content-Type: application/json" \
        -d '{"name":"Admin","email":"admin@ai-scraper.local","password":"aiscraper2024"}' 2>/dev/null)

    token=$(echo "$signup_response" | $PYTHON_CMD -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

    if [ -z "$token" ]; then
        # Try login
        local login_response
        login_response=$(curl -s -X POST "$base_url/api/v1/auths/signin" \
            -H "Content-Type: application/json" \
            -d '{"email":"admin@ai-scraper.local","password":"aiscraper2024"}' 2>/dev/null)
        token=$(echo "$login_response" | $PYTHON_CMD -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
    fi

    if [ -n "$token" ]; then
        success "Admin account ready"
    else
        warn "Could not auto-create account — create one at $base_url"
    fi

    # Auto-install tool
    if [ -n "$token" ]; then
        info "Installing AI Scraper tool..."
        local tool_file="$HOME/ai-scraper/open_webui_tool.py"

        if [ -f "$tool_file" ]; then
            local tool_content
            tool_content=$(cat "$tool_file")

            # Create tool via API
            local tool_body
            tool_body=$($PYTHON_CMD -c "
import json
content = open('$tool_file').read()
print(json.dumps({
    'id': 'ai_scraper_tool',
    'name': 'AI Scraper',
    'content': content,
    'meta': {'description': 'AI-powered web scraping'}
}))
" 2>/dev/null)

            local create_result
            create_result=$(curl -s -X POST "$base_url/api/v1/tools/create" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$tool_body" 2>/dev/null)

            if echo "$create_result" | grep -q "ai_scraper"; then
                success "AI Scraper tool installed in Open WebUI!"
            else
                # Try update
                curl -s -X POST "$base_url/api/v1/tools/id/ai_scraper_tool/update" \
                    -H "Content-Type: application/json" \
                    -H "Authorization: Bearer $token" \
                    -d "$tool_body" 2>/dev/null
                success "AI Scraper tool updated in Open WebUI!"
            fi
        fi
    fi

    # Final output
    echo ""
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${BOLD}  ✅ AI Scraper is ready!${NC}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if [ -n "$token" ]; then
        echo -e "  ${BOLD}Login:${NC}"
        echo -e "    Email:    ${CYAN}admin@ai-scraper.local${NC}"
        echo -e "    Password: ${CYAN}aiscraper2024${NC}"
        echo ""
        echo -e "  ${GREEN}The AI Scraper tool is already installed.${NC}"
        echo -e "  Just start a new chat and scrape any website!"
    else
        echo -e "  Open WebUI: ${CYAN}http://localhost:8080${NC}"
        echo "  Create an account and add the tool from Workspace > Tools"
    fi

    echo ""
    echo -e "  ${DIM}Documentation: https://github.com/masood1996-geo/ai-scraper${NC}"
    echo ""

    # Open browser
    if command_exists xdg-open; then xdg-open "http://localhost:8080" 2>/dev/null &
    elif command_exists open; then open "http://localhost:8080"; fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main() {
    banner

    # Step 1: Python
    find_python

    # Step 2: Git
    find_git

    # Step 3: API Key (only user interaction)
    get_api_key

    # Step 4: Install AI Scraper
    install_ai_scraper

    # Step 5: Install & Start Open WebUI
    install_and_start_open_webui
    local server_status=$?

    # Step 6: Auto-configure & launch browser
    configure_open_webui "$server_status"
}

main "$@"

#!/usr/bin/env bash
# ==============================================================================
# ProPing - Global Cloud & Datacenter Latency Intelligence Suite
# One-Command Installer & Live Temporary Server Launcher
# Repository: https://github.com/Lagtor-code/ProPing
# ==============================================================================

set -e

# ANSI Color Codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
PURPLE="\033[0;35m"
RESET="\033[0m"

clear 2>/dev/null || true

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  ____             ____  _             
 |  _ \ _ __ ___  |  _ \(_)_ __   __ _ 
 | |_) | '__/ _ \ | |_) | | '_ \ / _` |
 |  __/| | | (_) ||  __/| | | | | (_| |
 |_|   |_|  \___/ |_|   |_|_| |_|\__, |
                                 |___/ 
 Global Cloud & Datacenter Latency Suite
 One-Command Instant Deployer · v1.0.0
EOF
echo -e "${RESET}"

echo -e "${BLUE}▶ Checking system environment...${RESET}"

# Determine installation directory
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/opt/proping"
    BIN_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.proping"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

# Detect package manager & install python3 if missing
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  python3 not found. Attempting automatic installation...${RESET}"
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -y && sudo apt-get install -y python3 python3-minimal
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3
    elif command -v apk >/dev/null 2>&1; then
        apk add --no-cache python3
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python
    else
        echo -e "${RED}❌ python3 is required. Please install python3 and re-run.${RESET}"
        exit 1
    fi
fi

PYTHON_BIN=$(command -v python3)
echo -e "  ${GREEN}✔${RESET} Python detected: ${BOLD}$($PYTHON_BIN --version)${RESET}"

# Download or update repository
REPO_URL="https://github.com/Lagtor-code/ProPing.git"
TAR_URL="https://github.com/Lagtor-code/ProPing/archive/refs/heads/main.tar.gz"

echo -e "${BLUE}▶ Deploying ProPing into ${BOLD}${INSTALL_DIR}${RESET}..."

if command -v git >/dev/null 2>&1; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo -e "  ${CYAN}↻${RESET} Updating existing repository..."
        git -C "$INSTALL_DIR" pull --quiet || true
    else
        mkdir -p "$(dirname "$INSTALL_DIR")"
        rm -rf "$INSTALL_DIR"
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    fi
else
    echo -e "  ${YELLOW}ℹ${RESET} git not found, downloading via tarball..."
    mkdir -p "$INSTALL_DIR"
    TMP_TAR="/tmp/proping_main.tar.gz"
    if command -v curl >/dev/null 2>&1; then
        curl -sSL "$TAR_URL" -o "$TMP_TAR"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$TMP_TAR" "$TAR_URL"
    else
        echo -e "${RED}❌ Neither curl nor wget was found. Please install curl.${RESET}"
        exit 1
    fi
    tar -xzf "$TMP_TAR" -C "$INSTALL_DIR" --strip-components=1
    rm -f "$TMP_TAR"
fi

echo -e "  ${GREEN}✔${RESET} Core repository synchronized."

# Install global 'proping' command wrapper
echo -e "${BLUE}▶ Registering global CLI command...${RESET}"
CLI_WRAPPER="$BIN_DIR/proping"
cat << EOF > "$CLI_WRAPPER"
#!/usr/bin/env bash
exec "$PYTHON_BIN" "$INSTALL_DIR/proping.py" "\$@"
EOF
chmod +x "$CLI_WRAPPER"

# Also symlink to /usr/bin if root for universal PATH access
if [ "$EUID" -eq 0 ] && [ "$BIN_DIR" != "/usr/bin" ]; then
    ln -sf "$CLI_WRAPPER" /usr/bin/proping 2>/dev/null || true
fi

echo -e "  ${GREEN}✔${RESET} Command ${BOLD}proping${RESET} installed to ${CLI_WRAPPER}"

# Ensure catalogs are built
if [ ! -f "$INSTALL_DIR/dist/index.html" ]; then
    echo -e "${BLUE}▶ Compiling cloud catalog templates...${RESET}"
    (cd "$INSTALL_DIR" && "$PYTHON_BIN" proping.py build >/dev/null 2>&1)
    echo -e "  ${GREEN}✔${RESET} Compiled 609 verified cloud providers."
fi

# Detect Public IP
echo -e "${BLUE}▶ Detecting network IP...${RESET}"
PUB_IP=""
for ip_service in "https://api.ipify.org" "https://icanhazip.com" "https://ifconfig.me/ip"; do
    if command -v curl >/dev/null 2>&1; then
        PUB_IP=$(curl -4 -s --connect-timeout 2 "$ip_service" 2>/dev/null | tr -d '[:space:]')
    elif command -v wget >/dev/null 2>&1; then
        PUB_IP=$(wget -4 -qO- --timeout=2 "$ip_service" 2>/dev/null | tr -d '[:space:]')
    fi
    if [[ "$PUB_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        break
    fi
done

if [ -z "$PUB_IP" ]; then
    PUB_IP="127.0.0.1"
fi
echo -e "  ${GREEN}✔${RESET} Server Public IP: ${BOLD}${PUB_IP}${RESET}"

# Parse command line flags for installer
PORT=8080
DAEMON_MODE=false
NO_SERVE=false

for arg in "$@"; do
    case "$arg" in
        --port=*) PORT="${arg#*=}" ;;
        -p=*) PORT="${arg#*=}" ;;
        --daemon) DAEMON_MODE=true ;;
        -d) DAEMON_MODE=true ;;
        --no-serve) NO_SERVE=true ;;
    esac
done

# Check if port is in use, fallback to 8081 or 8000
if command -v ss >/dev/null 2>&1; then
    if ss -tuln | grep -q ":$PORT "; then
        PORT=8081
    fi
fi

# Firewall hint
if command -v ufw >/dev/null 2>&1 && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    FW_HINT="⚠️  UFW is active! If dashboard doesn't open in browser, run: ${YELLOW}sudo ufw allow ${PORT}/tcp${RESET}"
elif command -v firewall-cmd >/dev/null 2>&1 && sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
    FW_HINT="⚠️  Firewalld is active! Run: ${YELLOW}sudo firewall-cmd --add-port=${PORT}/tcp --permanent && sudo firewall-cmd --reload${RESET}"
else
    FW_HINT=""
fi

if [ "$NO_SERVE" = true ]; then
    echo -e "\n${GREEN}${BOLD}🎉 ProPing installed successfully!${RESET}"
    echo -e "Run ${CYAN}proping serve${RESET} to host dashboard, or ${CYAN}proping --help${RESET} for options."
    exit 0
fi

if [ "$DAEMON_MODE" = true ]; then
    echo -e "\n${BLUE}▶ Starting ProPing background daemon on port ${PORT}...${RESET}"
    (cd "$INSTALL_DIR" && "$PYTHON_BIN" proping.py serve --port "$PORT" --daemon)
    if [ -n "$FW_HINT" ]; then echo -e "$FW_HINT"; fi
    exit 0
fi

# Foreground Temporary Server
echo -e "\n${GREEN}========================================================================${RESET}"
echo -e "${BOLD}${CYAN}  ⚡ ProPing Live Temporary Dashboard is RUNNING!${RESET}"
echo -e "${GREEN}========================================================================${RESET}"
echo -e "  🌐 ${BOLD}Main Dashboard (609 Providers):${RESET}"
echo -e "     👉 ${GREEN}${BOLD}http://${PUB_IP}:${PORT}/${RESET}"
echo -e ""
echo -e "  📊 ${BOLD}Hourly Billing Dashboard (62 Providers):${RESET}"
echo -e "     👉 ${CYAN}${BOLD}http://${PUB_IP}:${PORT}/hourly.html${RESET}"
echo -e "${GREEN}========================================================================${RESET}"
if [ -n "$FW_HINT" ]; then
    echo -e "  ${FW_HINT}"
    echo -e "${GREEN}========================================================================${RESET}"
fi
echo -e "  ${YELLOW}💡 Press Ctrl+C at any time to stop this temporary server.${RESET}"
echo -e "  💡 To run in the background instead, execute: ${BOLD}proping serve --daemon${RESET}"
echo -e "  💡 To run live latency tests from this VPS: ${BOLD}proping benchmark${RESET}"
echo -e "${GREEN}========================================================================${RESET}\n"

# Trap Ctrl+C for clean exit
trap 'echo -e "\n\n${YELLOW}🛑 Temporary server stopped cleanly.${RESET}\n${CYAN}💡 You can restart it anytime with:${RESET} ${BOLD}proping serve${RESET}\n"; exit 0' INT TERM

cd "$INSTALL_DIR"
exec "$PYTHON_BIN" proping.py serve --host 0.0.0.0 --port "$PORT" --no-browser

#!/usr/bin/env bash
# ==============================================================================
# ProPing - Global Cloud & Datacenter Latency Intelligence Suite
# One-Command Installer, Live ICMP Prober & Instant Dashboard Deployer
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
 Live Benchmark Prober & Deployer · v1.1.0
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
        sudo apt-get update -y && sudo apt-get install -y python3 python3-minimal iputils-ping
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 iputils
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3 iputils
    elif command -v apk >/dev/null 2>&1; then
        apk add --no-cache python3 iputils
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python iputils
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

if [ "$EUID" -eq 0 ] && [ "$BIN_DIR" != "/usr/bin" ]; then
    ln -sf "$CLI_WRAPPER" /usr/bin/proping 2>/dev/null || true
fi

echo -e "  ${GREEN}✔${RESET} Command ${BOLD}proping${RESET} installed to ${CLI_WRAPPER}"

# Bulletproof Public IP Detection (Never returns HTML error tags)
echo -e "${BLUE}▶ Detecting server network IP...${RESET}"
PUB_IP=""
LOCAL_ROUTE_IP=""

# 1. Check local network interface route directly
if command -v ip >/dev/null 2>&1; then
    LOCAL_ROUTE_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7}')
fi
if [ -z "$LOCAL_ROUTE_IP" ] && command -v hostname >/dev/null 2>&1; then
    LOCAL_ROUTE_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

# Check if local IP is already a public IPv4 (not 10., 192.168., 172.16-31, 127.)
if [[ "$LOCAL_ROUTE_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    if ! [[ "$LOCAL_ROUTE_IP" =~ ^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|127\.|169\.254\.|100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.) ]]; then
        PUB_IP="$LOCAL_ROUTE_IP"
    fi
fi

# 2. If behind NAT, query verified external endpoints with strict IPv4 regex validation
if [ -z "$PUB_IP" ]; then
    for ip_service in "https://api.ipify.org" "https://ip.sb" "https://checkip.amazonaws.com" "https://icanhazip.com" "https://ipecho.net/plain"; do
        CANDIDATE=""
        if command -v curl >/dev/null 2>&1; then
            CANDIDATE=$(curl -4 -s --connect-timeout 2 "$ip_service" 2>/dev/null | tr -d '[:space:]')
        elif command -v wget >/dev/null 2>&1; then
            CANDIDATE=$(wget -4 -qO- --timeout=2 "$ip_service" 2>/dev/null | tr -d '[:space:]')
        fi
        if [[ "$CANDIDATE" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]] && [[ "$CANDIDATE" != *"<"* ]] && [[ "$CANDIDATE" != *"html"* ]]; then
            PUB_IP="$CANDIDATE"
            break
        fi
    done
fi

if [ -z "$PUB_IP" ]; then
    PUB_IP="${LOCAL_ROUTE_IP:-127.0.0.1}"
fi
echo -e "  ${GREEN}✔${RESET} Server Public IP: ${BOLD}${PUB_IP}${RESET}"

# Parse command line flags
CUSTOM_PORT=""
DAEMON_MODE=false
NO_SERVE=false
SKIP_BENCHMARK=false
BENCHMARK_WORKERS=40

for arg in "$@"; do
    case "$arg" in
        --port=*) CUSTOM_PORT="${arg#*=}" ;;
        -p=*) CUSTOM_PORT="${arg#*=}" ;;
        --daemon) DAEMON_MODE=true ;;
        -d) DAEMON_MODE=true ;;
        --no-serve) NO_SERVE=true ;;
        --no-benchmark) SKIP_BENCHMARK=true ;;
        --workers=*) BENCHMARK_WORKERS="${arg#*=}" ;;
    esac
done

# Intelligent Port Selection
check_port() {
    local p=$1
    if command -v ss >/dev/null 2>&1; then
        ss -tuln | grep -q ":${p} " && return 1 || return 0
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":${p} " && return 1 || return 0
    fi
    return 0
}

PORT=8080
if [ -n "$CUSTOM_PORT" ]; then
    PORT="$CUSTOM_PORT"
else
    # Try port 80 first if root (cleanest for web browsers)
    if [ "$EUID" -eq 0 ] && check_port 80; then
        PORT=80
    elif check_port 8080; then
        PORT=8080
    elif check_port 8000; then
        PORT=8000
    elif check_port 8888; then
        PORT=8888
    elif check_port 3000; then
        PORT=3000
    else
        PORT=8081
    fi
fi

# Automatically open firewall port if running as root
if [ "$EUID" -eq 0 ]; then
    iptables -I INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null || true
    if command -v ufw >/dev/null 2>&1; then
        ufw allow "$PORT/tcp" >/dev/null 2>&1 || true
    fi
    if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld 2>/dev/null; then
        firewall-cmd --add-port="${PORT}/tcp" --permanent >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
    fi
fi

# Live Benchmark Probing (Measures latencies from this server right now)
if [ "$SKIP_BENCHMARK" = false ]; then
    echo -e "\n${BLUE}▶ Initiating Live ICMP Latency Probing across 609 Global Datacenters...${RESET}"
    echo -e "  ${YELLOW}⚡ Measuring live round-trip latency from this server (${PUB_IP}) right now...${RESET}"
    (cd "$INSTALL_DIR" && "$PYTHON_BIN" proping.py benchmark --workers "$BENCHMARK_WORKERS" --count 2 --timeout 1)
else
    echo -e "\n${CYAN}ℹ Skipping live benchmark (--no-benchmark specified). Compiling cached catalog...${RESET}"
    (cd "$INSTALL_DIR" && "$PYTHON_BIN" proping.py build >/dev/null 2>&1)
fi

if [ "$NO_SERVE" = true ]; then
    echo -e "\n${GREEN}${BOLD}🎉 ProPing benchmark complete & installed successfully!${RESET}"
    echo -e "Run ${CYAN}proping serve${RESET} to host dashboard, or ${CYAN}proping --help${RESET} for options."
    exit 0
fi

if [ "$DAEMON_MODE" = true ]; then
    echo -e "\n${BLUE}▶ Starting ProPing background daemon on port ${PORT}...${RESET}"
    (cd "$INSTALL_DIR" && "$PYTHON_BIN" proping.py serve --port "$PORT" --daemon)
    exit 0
fi

# Foreground Interactive Server
PORT_SUFFIX=""
if [ "$PORT" != "80" ]; then
    PORT_SUFFIX=":${PORT}"
fi

echo -e "\n${GREEN}========================================================================${RESET}"
echo -e "${BOLD}${CYAN}  ⚡ ProPing Live Telemetry & Latency Dashboard is RUNNING!${RESET}"
echo -e "${GREEN}========================================================================${RESET}"
echo -e "  🌐 ${BOLD}Interactive Web Studio (Bento Grid & Table):${RESET}"
echo -e "     👉 ${GREEN}${BOLD}http://${PUB_IP}${PORT_SUFFIX}/${RESET}"
echo -e ""
echo -e "  📊 ${BOLD}Hourly Pay-As-You-Go Compute Directory:${RESET}"
echo -e "     👉 ${CYAN}${BOLD}http://${PUB_IP}${PORT_SUFFIX}/hourly.html${RESET}"
echo -e ""
echo -e "  📄 ${BOLD}Ranked Text Summary Report:${RESET}"
echo -e "     👉 ${PURPLE}${BOLD}http://${PUB_IP}${PORT_SUFFIX}/top_routes.txt${RESET}"
echo -e "${GREEN}========================================================================${RESET}"
echo -e "  ${YELLOW}💡 Press Ctrl+C at any time to stop this temporary server.${RESET}"
echo -e "  💡 To run in the background instead: ${BOLD}proping serve --daemon${RESET}"
echo -e "  💡 To run a new benchmark anytime:   ${BOLD}proping benchmark${RESET}"
echo -e "${GREEN}========================================================================${RESET}\n"

# Trap Ctrl+C for clean exit
trap 'echo -e "\n\n${YELLOW}🛑 Temporary server stopped cleanly.${RESET}\n${CYAN}💡 You can restart it anytime with:${RESET} ${BOLD}proping serve${RESET}\n"; exit 0' INT TERM

cd "$INSTALL_DIR"
exec "$PYTHON_BIN" proping.py serve --host 0.0.0.0 --port "$PORT" --no-browser

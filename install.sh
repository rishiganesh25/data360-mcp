#!/bin/bash
# =============================================================================
# Data Cloud MCP — Installer for Cursor
# =============================================================================
# Review this script, then run it from a checkout:
#   chmod +x install.sh && ./install.sh
# Do not pipe it from the internet. A remote install must name a full commit SHA:
#   DATA360_MCP_REF=<40-character-commit-sha> ./install.sh
# =============================================================================

set -euo pipefail

INSTALL_DIR="${DATA360_MCP_INSTALL_DIR:-$HOME/.data360-mcp}"
REPO_URL="${DATA360_MCP_REPO:-https://github.com/rishiganesh25/data360-mcp.git}"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Data Cloud MCP Server — Installer                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# --- Step 1: Check prerequisites ---
echo "[1/5] Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed. Install it from https://python.org/downloads"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10+ required, but found $PYTHON_VERSION"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "ERROR: git is not installed. Install it from https://git-scm.com"
    exit 1
fi

if ! command -v sf &> /dev/null && ! command -v sfdx &> /dev/null; then
    echo "ERROR: Salesforce CLI is not installed. Install it with: npm install -g @salesforce/cli"
    exit 1
fi

echo "       python3 ($PYTHON_VERSION) ✓"
echo "       git ✓"
echo "       Salesforce CLI ✓"

# --- Step 2: Install a reviewed snapshot ---
echo ""
echo "[2/5] Installing to $INSTALL_DIR..."

copy_source() {
    mkdir -p "$INSTALL_DIR"
    tar -C "$SOURCE_DIR" \
        --exclude .git \
        --exclude .venv \
        --exclude .env \
        --exclude usage_logs \
        --exclude __pycache__ \
        --exclude .DS_Store \
        -cf - . | tar -C "$INSTALL_DIR" -xf -
}

if [ -f "$SOURCE_DIR/server.py" ]; then
    echo "       Using the reviewed copy in $SOURCE_DIR"
    copy_source
    cd "$INSTALL_DIR"
elif [ -n "${DATA360_MCP_REF:-}" ]; then
    if ! [[ "$DATA360_MCP_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
        echo "ERROR: DATA360_MCP_REF must be a full 40-character commit SHA, not a branch or tag."
        exit 1
    fi
    DATA360_MCP_REF=$(printf '%s' "$DATA360_MCP_REF" | tr '[:upper:]' '[:lower:]')
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "       Checking out $DATA360_MCP_REF"
        git -C "$INSTALL_DIR" fetch --quiet origin "$DATA360_MCP_REF"
        git -C "$INSTALL_DIR" checkout --detach FETCH_HEAD
    else
        git clone --quiet "$REPO_URL" "$INSTALL_DIR"
        git -C "$INSTALL_DIR" checkout --detach "$DATA360_MCP_REF"
    fi
    CHECKED_OUT=$(git -C "$INSTALL_DIR" rev-parse HEAD)
    if [ "$CHECKED_OUT" != "$DATA360_MCP_REF" ]; then
        echo "ERROR: Checkout is $CHECKED_OUT, expected $DATA360_MCP_REF."
        exit 1
    fi
    cd "$INSTALL_DIR"
else
    echo "ERROR: Refusing to clone an unpinned main branch."
    echo "       Run ./install.sh from a reviewed checkout, or set DATA360_MCP_REF to a full commit SHA."
    exit 1
fi

# --- Step 3: Set up virtual environment ---
echo ""
echo "[3/5] Setting up Python virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
python3 -m pip install --quiet --require-hashes -r requirements.lock

echo "       Dependencies installed ✓"

# --- Step 4: Select the authenticated org ---
echo ""
echo "[4/5] Configuring the Salesforce CLI org..."

if [ -f ".env" ]; then
    echo "       .env already exists — skipping."
else
    echo ""
    echo "       Log in first if you have not: sf org login web --alias data360"
    echo ""
    read -p "       Salesforce CLI alias or username [data360]: " SF_TARGET_ORG
    SF_TARGET_ORG=${SF_TARGET_ORG:-data360}

    cat > .env << ENVEOF
SF_TARGET_ORG=$SF_TARGET_ORG
DEFAULT_LIST_TABLE_FILTER=%
MAX_QUERY_ROWS=1000
MAX_QUERY_BYTES=1000000
MCP_RATE_WINDOW_SECONDS=60
MCP_DESTRUCTIVE_RATE_LIMIT=10
MCP_WRITE_RATE_LIMIT=20
MCP_READ_RATE_LIMIT=120
MCP_ENABLE_WRITE_TOOLS=true
MCP_ENABLE_DESTRUCTIVE_TOOLS=true
MCP_ALLOWED_WEBHOOK_HOSTS=
MCP_ENFORCE_TOOL_PINS=true
ENVEOF

    chmod 600 .env
    echo "       .env created ✓"
fi

# --- Step 5: Output Cursor config ---
PYTHON_PATH="$INSTALL_DIR/.venv/bin/python"
ENV_PATH="$INSTALL_DIR/.env"
SERVER_PATH="$INSTALL_DIR/server.py"

echo ""
echo "[5/5] Done! Add this MCP server to Cursor:"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Cursor Settings > MCP > Add new global MCP server          ║"
echo "║  Paste the JSON below:                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
cat << JSONEOF
{
  "mcpServers": {
    "datacloud": {
      "command": "bash",
      "args": [
        "-c",
        "set -a && source $ENV_PATH && set +a && cd $INSTALL_DIR && $PYTHON_PATH server.py"
      ],
      "disabled": false,
      "autoApprove": [
        "list_tables",
        "describe_table",
        "list_data_streams",
        "list_data_model_objects",
        "list_segments",
        "list_calculated_insights",
        "list_data_graphs",
        "list_retrievers",
        "list_search_indexes"
      ]
    }
  }
}
JSONEOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next steps:"
echo "  1. Paste the JSON above into Cursor MCP settings"
echo "  2. Restart Cursor"
echo "  3. Ask: \"List all tables in Data Cloud\""
echo "  4. If tools fail auth, run: sf org login web --alias data360"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

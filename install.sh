#!/bin/bash
# =============================================================================
# Data Cloud MCP — One-click installer for Cursor
# =============================================================================
# Usage: curl -fsSL https://raw.githubusercontent.com/rishiganesh25/data360-mcp/main/install.sh | bash
# Or:    chmod +x install.sh && ./install.sh
# =============================================================================

set -e

INSTALL_DIR="$HOME/.data360-mcp"
REPO_URL="https://github.com/rishiganesh25/data360-mcp.git"

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

echo "       python3 ($PYTHON_VERSION) ✓"
echo "       git ✓"

# --- Step 2: Clone or update ---
echo ""
echo "[2/5] Installing to $INSTALL_DIR..."

if [ -d "$INSTALL_DIR" ]; then
    echo "       Directory exists — pulling latest..."
    cd "$INSTALL_DIR"
    git pull --quiet origin main 2>/dev/null || true
else
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# --- Step 3: Set up virtual environment ---
echo ""
echo "[3/5] Setting up Python virtual environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "       Dependencies installed ✓"

# --- Step 4: Configure credentials ---
echo ""
echo "[4/5] Configuring credentials..."

if [ -f ".env" ]; then
    echo "       .env already exists — skipping."
else
    echo ""
    echo "       You need a Salesforce Connected App with Data Cloud scopes."
    echo "       (See README.md Steps 5-9 for setup instructions)"
    echo ""
    read -p "       Enter your Consumer Key (SF_CLIENT_ID): " SF_CLIENT_ID
    read -p "       Enter your Consumer Secret (SF_CLIENT_SECRET): " SF_CLIENT_SECRET
    echo ""
    read -p "       Login URL [login.salesforce.com]: " SF_LOGIN_URL
    SF_LOGIN_URL=${SF_LOGIN_URL:-login.salesforce.com}

    cat > .env << ENVEOF
SF_CLIENT_ID=$SF_CLIENT_ID
SF_CLIENT_SECRET=$SF_CLIENT_SECRET
SF_LOGIN_URL=$SF_LOGIN_URL
SF_CALLBACK_URL=http://localhost:55556/Callback
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
        "query",
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
echo "  4. A browser will open for Salesforce login (first time only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Data Cloud MCP Server

A Model Context Protocol (MCP) server for **Salesforce Data Cloud** that exposes 30+ tools to AI assistants like Cursor, Claude Code, and Claude Desktop.

Query Data Cloud with SQL, manage data streams, create segments and calculated insights, explore the data model, and more — all from natural language in your AI assistant.

---

## Table of Contents

1. [Quick Start (Cursor — Recommended)](#quick-start-cursor--recommended)
2. [Detailed Setup Guide](#detailed-setup-guide)
   - [Part A: Install Python (one-time)](#part-a-install-python-one-time)
   - [Part B: Create a Connected App in Salesforce](#part-b-create-a-connected-app-in-salesforce)
   - [Part C: Install the MCP Server](#part-c-install-the-mcp-server)
   - [Part D: Add the Server to Cursor](#part-d-add-the-server-to-cursor)
   - [Part E: First Run — Authenticate with Salesforce](#part-e-first-run--authenticate-with-salesforce)
3. [Verify It Works](#verify-it-works)
4. [Tool Catalog](#tool-catalog)
5. [Setup for Other Clients](#setup-for-other-clients)
6. [Configuration Reference](#configuration-reference)
7. [Architecture](#architecture)
8. [Security](#security)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start (Cursor — Recommended)

If you already have **Python 3.10+** installed and a **Salesforce Connected App** ready (with your Consumer Key and Secret), you can set up in under 2 minutes.

Open a terminal in Cursor (`Ctrl+`` ` or `Cmd+`` `) and run:

```bash
curl -fsSL https://raw.githubusercontent.com/rishiganesh25/data360-mcp/main/install.sh | bash
```

The script will:
1. Clone the repo to `~/.data360-mcp`
2. Create a Python virtual environment and install dependencies
3. Ask for your Consumer Key and Consumer Secret
4. Print the JSON config to paste into Cursor

Then paste the JSON into **Cursor Settings > MCP**, restart Cursor, and you're done.

> **Don't have Python or a Connected App yet?** Follow the [Detailed Setup Guide](#detailed-setup-guide) below — it walks through everything from scratch.

---

## Detailed Setup Guide

This guide assumes you are starting from zero. Every step is performed inside **Cursor** and your **browser**. No prior terminal experience needed.

**Total time**: ~15 minutes

---

### Part A: Install Python (one-time)

You only need to do this once. If you already have Python, skip to [Part B](#part-b-create-a-connected-app-in-salesforce).

<details>
<summary><strong>How to check if Python is already installed</strong></summary>

1. Open Cursor
2. Open the terminal: press **Cmd + `** (Mac) or **Ctrl + `** (Windows/Linux) — that's the backtick key, top-left of your keyboard next to the `1` key
3. Type this and press Enter:
   ```bash
   python3 --version
   ```
4. If you see something like `Python 3.12.4`, you're good — skip to Part B
5. If you see `command not found`, follow the install steps below

</details>

#### Installing Python

1. Open your browser and go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Open the downloaded file and follow the installer:
   - **Mac**: Double-click the `.pkg` file. Click Continue through each step, then Install
   - **Windows**: Run the `.exe` file. **CHECK THE BOX** that says **"Add Python to PATH"** (this is critical!). Then click "Install Now"
4. Once installed, go back to Cursor's terminal and verify:
   ```bash
   python3 --version
   ```
   You should now see `Python 3.x.x`. If you're on Windows and this doesn't work, close and reopen Cursor, then try again.

---

### Part B: Create a Connected App in Salesforce

The MCP server needs permission to talk to your Salesforce org. You do this by creating a "Connected App" — think of it as an API key for your org.

> **Who should do this step?** Anyone with Salesforce Admin access. If you don't have admin access, send this section to your Salesforce admin and ask them to do it for you.

#### B1: Enable External Client Apps

1. Log in to your Salesforce org in your browser
2. Click the **gear icon** (top right corner) → **Setup**
3. In the **Quick Find** search box on the left side, type: **External Client Apps**
4. Click **Settings** (under "External Client Apps" in the left sidebar)
5. You'll see two toggles. Turn **both ON**:
   - ✅ "Allow access to External Client App consumer secrets via REST API"
   - ✅ "Allow creation of connected apps"
6. Click **Save**

> **Can't find "External Client Apps"?** Your org edition may not support it. Try searching for **"App Manager"** in Quick Find instead, and create a Connected App from there — the OAuth settings below are the same.

#### B2: Create the Connected App

1. In Setup, look in the left sidebar for **External Client Apps** and click on it
2. Click the **New Connected App** button
3. Fill in these three fields:

   | Field | What to type |
   |---|---|
   | Connected App Name | `Data Cloud MCP` |
   | API Name | Leave as-is (it auto-fills to `Data_Cloud_MCP`) |
   | Contact Email | Your email address |

4. Click **Next**

#### B3: Enable OAuth and Add Scopes

1. Check the box: **"Enable OAuth Settings"** — this expands a new section
2. In the **Callback URL** field, paste this exactly (copy-paste, don't type it):
   ```
   http://localhost:55556/Callback
   ```
   > ⚠️ **Do NOT use port 55555** — it conflicts with macOS AirPlay. Port 55556 is safe.

3. In the **OAuth Scopes** section, you need to add 5 scopes. For each one:
   - Click the dropdown or search box under "Available OAuth Scopes"
   - Find the scope in the list
   - Click **Add** (or the right arrow) to move it to "Selected OAuth Scopes"

   Add these 5 scopes:

   | Scope to find and add | Why it's needed |
   |---|---|
   | `Access the identity URL service (id, profile, email, address, phone)` | Identifies who is logging in |
   | `Manage user data via APIs (api)` | Lets the server call Salesforce APIs |
   | `Manage Data Cloud profile data (cdp_profile_api)` | Access to Data Cloud streams, segments, graphs |
   | `Perform ANSI SQL queries on Data Cloud data (cdp_query_api)` | Run SQL queries against your data |
   | `Perform requests at any time (refresh_token, offline_access)` | Keeps your session alive |

4. Scroll down to **Security Settings** and check all three boxes:
   - ✅ Require Secret for Web Server Flow
   - ✅ Require Secret for Refresh Token Flow
   - ✅ Require Proof Key for Code Exchange (PKCE)

5. Click **Save**

#### B4: Relax IP Restrictions

1. You should now be on your Connected App's detail page. Click the **Manage** button at the top
2. Click **Edit Policies**
3. Find the **IP Relaxation** dropdown (under "OAuth Policies") and change it to:
   ```
   Relax IP restrictions
   ```
4. Click **Save**

> **Why is this needed?** Without this, Salesforce blocks the login from `localhost`. This is safe — the PKCE flow still requires you to log in via your browser.

#### B5: Copy Your Consumer Key and Secret

1. Go back to **Setup** → search **"External Client Apps"** in Quick Find
2. Find **Data Cloud MCP** in the list and click on it
3. Navigate to: **Settings** → **OAuth Settings** → **App Settings**
4. You'll see two values you need to copy:
   - **Consumer Key** — click to select it, then copy (Cmd+C / Ctrl+C). Save it somewhere temporarily (a notes app, a sticky note — you'll need it in Part C)
   - **Consumer Secret** — click **"Click to reveal"**, then copy it. Save it next to the Consumer Key

> ⚠️ **Keep these safe.** They're like a password for your org's API. Never share them in email or chat. Never commit them to git.

> **Note**: Salesforce can take 5-10 minutes to activate a new Connected App. If you get errors later, wait a few minutes and try again.

---

### Part C: Install the MCP Server

Now you'll install the server code. Everything in this section happens inside Cursor.

#### C1: Open a Terminal in Cursor

1. Open Cursor
2. Press **Cmd + `** (Mac) or **Ctrl + `** (Windows/Linux) to open the built-in terminal
3. You should see a terminal panel appear at the bottom of Cursor with a blinking cursor

> **If you don't see a terminal**: Go to the menu bar → **Terminal** → **New Terminal**

#### C2: Run the Installer

Copy-paste this entire command into the terminal and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/rishiganesh25/data360-mcp/main/install.sh | bash
```

**What you'll see**: The script will print progress messages:

```
[1/5] Checking prerequisites...
  python3 (3.12) ✓
  git ✓

[2/5] Installing to /Users/yourname/.data360-mcp...

[3/5] Setting up Python virtual environment...
  Dependencies installed ✓

[4/5] Configuring credentials...
```

#### C3: Enter Your Credentials

The script will ask you for two things. Paste the values you saved from Part B:

```
Enter your Consumer Key (SF_CLIENT_ID): <paste your Consumer Key here>
Enter your Consumer Secret (SF_CLIENT_SECRET): <paste your Consumer Secret here>
Login URL [login.salesforce.com]: <press Enter for production, or type test.salesforce.com for sandbox>
```

> **Which Login URL should I use?**
> - **Production or Developer org**: Just press Enter (the default `login.salesforce.com` is correct)
> - **Sandbox**: Type `test.salesforce.com`
> - **Custom My Domain**: Type your domain, e.g. `mycompany.my.salesforce.com`

#### C4: Copy the JSON Config

After entering credentials, the script prints a JSON block. **Select and copy the entire JSON** — you'll paste it in the next step.

It looks like this (with your actual paths filled in):

```json
{
  "mcpServers": {
    "datacloud": {
      "command": "bash",
      "args": [
        "-c",
        "set -a && source /Users/yourname/.data360-mcp/.env && set +a && cd /Users/yourname/.data360-mcp && .venv/bin/python server.py"
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
```

> **What is `autoApprove`?** These are read-only tools that Cursor will run without asking you "Allow?" every time. This saves clicks. Write operations (like creating segments) will still ask for confirmation.

---

### Part D: Add the Server to Cursor

#### D1: Open Cursor MCP Settings

1. Open Cursor Settings: press **Cmd + ,** (Mac) or **Ctrl + ,** (Windows/Linux)
2. In the left sidebar, scroll down and click **MCP**
3. You should see the "MCP Servers" section

#### D2: Add the Server

1. Click **"+ Add new global MCP server"**
2. This opens a JSON file called `mcp.json`
3. **Delete everything** in this file
4. **Paste the JSON** you copied from Part C
5. **Save the file**: press **Cmd + S** (Mac) or **Ctrl + S** (Windows/Linux)

#### D3: Verify It Appears

1. Go back to **Cursor Settings > MCP**
2. You should see **"datacloud"** in the server list
3. It may show a yellow/orange indicator while starting up — wait a few seconds
4. Once it turns **green**, the server is connected and ready

> **If it stays red or shows an error**: Click on the server name to see the error message, then check the [Troubleshooting](#troubleshooting) section.

---

### Part E: First Run — Authenticate with Salesforce

The first time you use the server, it needs to log you in to Salesforce via your browser.

#### E1: Ask the Agent Something

1. Open the Cursor AI chat (press **Cmd + L** on Mac, or **Ctrl + L** on Windows/Linux)
2. Type a simple question like:
   ```
   List all tables in Data Cloud
   ```
3. Press Enter

#### E2: Authorize in Your Browser

1. **A browser window will open automatically** showing the Salesforce login page
2. Log in with the Salesforce user that has **Data Cloud permissions**
3. When Salesforce asks **"Allow access?"** — click **Allow**
4. You'll see a page that says: **"You can close this window now"**
5. Close the browser tab and **switch back to Cursor**

#### E3: See the Results

Back in Cursor, the AI chat should now show a list of your Data Cloud tables. If it does, everything is working.

> **You won't need to log in again for ~2 hours.** The token is cached at `~/.dc_mcp_token_cache.json`. When it expires, the browser login will open again automatically — just log in and continue.

---

## Verify It Works

Try these prompts in Cursor's AI chat to confirm everything is connected:

| What to type in Cursor chat | What you should see |
|---|---|
| *"List all tables in Data Cloud"* | A list of table names (DMOs, DLOs, CIOs) |
| *"Show me all data streams and their status"* | Streams with Active/Inactive status |
| *"Describe the ssot__Individual__dlm table"* | Column names and types for the Individual DMO |
| *"How many segments do I have?"* | A count and list of segment names |
| *"Run: SELECT COUNT(\*) FROM ssot__Individual__dlm"* | A number showing your record count |

If any of these fail, check the [Troubleshooting](#troubleshooting) section at the bottom.

---

## Tool Catalog

The server exposes 30+ tools organized by function. Cursor's AI agent automatically picks the right tool based on what you ask.

### Query & Schema

| Tool | What it does |
|---|---|
| `query` | Execute SQL (PostgreSQL dialect) against Data Cloud. Handles long-running queries and pagination automatically. |
| `list_tables` | List all queryable tables. Filterable via `DEFAULT_LIST_TABLE_FILTER` env var. |
| `describe_table` | Get column names for a specific table. |

### Data Streams

| Tool | What it does |
|---|---|
| `list_data_streams` | All streams with status, source, category, and last refresh date. |
| `get_data_stream_info` | Detailed configuration for a single stream. |
| `refresh_stream` | Trigger a manual data refresh. |
| `create_new_data_stream` | Create a stream from any connector (CRM, S3, GCS, Azure, SFTP, MuleSoft, IngestApi). |
| `create_ingestion_schema` | Define the schema for an Ingestion API stream. |
| `delete_stream` | Remove a stream (and optionally its Data Lake Object). |
| `list_available_connectors` | Discover configured connectors in your org. |
| `list_connector_objects` | See what source objects a connector offers. |
| `list_connected_source_objects` | See which objects already have streams (avoid duplicates). |

### Data Model

| Tool | What it does |
|---|---|
| `list_data_model_objects` | All DMOs with metadata. |
| `get_dmo_details` | Fields and relationships for a specific DMO. |
| `create_custom_dmo` | Create a new custom Data Model Object with custom fields. |
| `create_custom_dmo_fields` | Add fields to an existing custom DMO. |
| `delete_custom_dmo_fields` | Remove fields from a custom DMO. |
| `create_dlo_dmo_mapping` | Map a Data Lake Object to a DMO with pre-flight validation. |
| `batch_create_dlo_dmo_mappings` | Map multiple DLOs to DMOs in parallel with auto-fix. |
| `update_dlo_dmo_mapping` | Update an existing field mapping. |
| `delete_dlo_dmo_mapping` | Remove a DLO-to-DMO mapping. |
| `list_mappings` | All stream-to-DMO field mappings. |
| `list_identity_rulesets` | Identity resolution ruleset configuration. |

### Segments

| Tool | What it does |
|---|---|
| `list_segments` | All segments in the org. |
| `create_segment` | Create a segment from a JSON definition. |
| `create_segment_dbt` | Create a SQL-based segment (automatically discovers field API names). |

### Calculated Insights

| Tool | What it does |
|---|---|
| `list_calculated_insights` | All calculated insights. |
| `create_calculated_insight` | Create a CI from a SQL SELECT expression with inferred dimensions/measures. |

### Data Graphs

| Tool | What it does |
|---|---|
| `list_data_graphs` | All data graph definitions. |
| `create_data_graph` | Create a graph rooted at a primary DMO with nested relationships. |
| `delete_data_graph` | Delete a data graph by developer name. |

### Retrievers & Search

| Tool | What it does |
|---|---|
| `list_retrievers` | All retrievers (system + custom, for RAG use cases). |
| `list_search_indexes` | All semantic search index definitions. |

### Salesforce REST

| Tool | What it does |
|---|---|
| `sf_rest_api` | Make GET/POST/PATCH/DELETE calls to `/services/data/` and `/services/connect/` paths. |
| `describe_sobject` | Get field metadata for any Salesforce sObject. |
| `create_sobject_record` | Create a record on any sObject. |

---

## Setup for Other Clients

The examples below show how to use the server with other MCP-compatible clients. In all cases, replace `/absolute/path/to/data360-mcp` with the path where the server is installed (the default installer puts it at `~/.data360-mcp`).

### Claude Code (CLI or VS Code Extension)

Create or edit `.mcp.json` in your project root (or `~/.claude/mcp.json` for global access):

```json
{
  "mcpServers": {
    "datacloud": {
      "type": "stdio",
      "command": "bash",
      "args": [
        "-c",
        "set -a && source /absolute/path/to/data360-mcp/.env && set +a && cd /absolute/path/to/data360-mcp && .venv/bin/python server.py"
      ]
    }
  }
}
```

### Claude Desktop

Edit your config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "datacloud": {
      "command": "bash",
      "args": [
        "-c",
        "set -a && source /absolute/path/to/data360-mcp/.env && set +a && cd /absolute/path/to/data360-mcp && .venv/bin/python server.py"
      ]
    }
  }
}
```

---

## Configuration Reference

| Environment Variable | Required | Default | Description |
|---|---|---|---|
| `SF_CLIENT_ID` | Yes | — | Consumer Key from your Connected App |
| `SF_CLIENT_SECRET` | Yes | — | Consumer Secret from your Connected App |
| `SF_LOGIN_URL` | No | `login.salesforce.com` | Login host. Use `test.salesforce.com` for sandboxes or your My Domain. |
| `SF_CALLBACK_URL` | No | `http://localhost:55556/Callback` | Must match the Connected App's Callback URL exactly. |
| `DEFAULT_LIST_TABLE_FILTER` | No | `%` | SQL LIKE filter for `list_tables` (e.g., `ssot__%` for only standard DMOs). |

---

## Architecture

```mermaid
flowchart LR
    Client["MCP Client<br/>(Cursor / Claude Code / Claude Desktop)"] -->|stdio| Server["server.py<br/>FastMCP"]
    Server --> OAuth["oauth.py<br/>OAuth 2.0 + PKCE"]
    Server --> SQL["connect_api_dc_sql.py<br/>SQL query + pagination"]
    Server --> DC["connect_api_datacloud.py<br/>Connect REST API"]
    OAuth -->|browser login| SF["Salesforce Login"]
    OAuth -->|token cache| Disk["~/.dc_mcp_token_cache.json"]
    SQL -->|POST /ssot/query-sql| DCAPI["Data Cloud Query API"]
    DC -->|/ssot/*| ConnectAPI["Data Cloud Connect API"]
    DC -->|/sobjects/*| RestAPI["Salesforce REST API"]
```

---

## Security

- **OAuth 2.0 with PKCE** — no long-lived credentials stored; tokens auto-expire in ~110 minutes
- **Token cache** is written with `0600` permissions (owner-read/write only)
- **Credentials in `.env`** — never committed to git (`.gitignore`'d)
- **`sf_rest_api`** is restricted to `/services/data/` and `/services/connect/` paths only; tooling, composite, and async-query endpoints are blocked
- **SQL input validation** — table names are validated against identifier patterns before use
- **Local transport only** — the server communicates via stdio (no network port exposed)

---

## Troubleshooting

### Server won't start / stays red in Cursor

| What you see | What to do |
|---|---|
| Server shows red dot in Cursor MCP settings | Click on the server name to see the error. Most common cause: Python path is wrong. Open the terminal in Cursor and run `python3 --version` to make sure Python is installed. |
| `ModuleNotFoundError: No module named 'mcp'` | Dependencies aren't installed. Run this in the terminal: `cd ~/.data360-mcp && source .venv/bin/activate && pip install -r requirements.txt` |
| `Connection refused` | The server crashed on startup. Run `cd ~/.data360-mcp && .venv/bin/python server.py` in the terminal to see the error message. |

### Authentication errors

| What you see | What to do |
|---|---|
| `invalid_client_id` after browser login | Your Consumer Key doesn't match. Go to **Setup > External Client Apps > Data Cloud MCP > Settings > OAuth Settings > App Settings** and re-copy the Consumer Key. Also make sure `SF_LOGIN_URL` in your `.env` points to the right org (`login.salesforce.com` vs `test.salesforce.com`). **New Connected Apps can take 5-10 minutes to activate** — wait and try again. |
| `redirect_uri_mismatch` | The Callback URL in the Connected App must be **exactly** `http://localhost:55556/Callback` — case-sensitive, no trailing slash. Go to the Connected App in Setup and fix it. |
| `PKCE challenge failed` | Go to the Connected App in Setup and make sure "Require Proof Key for Code Exchange" is checked. If you just changed it, wait 10 minutes. |
| Browser doesn't open for login | You're running in a headless/remote environment (like a cloud VM with no browser). Run the server on a machine that has a browser. |
| `Address already in use` on port 55556 | Another process is using that port. In the terminal, run `lsof -i :55556` to find it. You can kill it, or change the port in both your `.env` file (`SF_CALLBACK_URL`) and the Connected App in Salesforce. |

### API and permission errors

| What you see | What to do |
|---|---|
| `403 Forbidden` from Data Cloud APIs | The logged-in Salesforce user doesn't have Data Cloud permissions. In Salesforce Setup, go to **Permission Sets** and assign **Customer Data Platform Admin** to your user. |
| `cdp_query_api not enabled` | The Connected App is missing OAuth scopes. Edit it in Setup, add all 5 scopes from [Part B3](#b3-enable-oauth-and-add-scopes), save, and wait ~10 minutes. |
| `401 Unauthorized` mid-session | Token expired and auto-refresh failed. Fix: delete the token cache and re-authenticate. In the terminal, run: `rm ~/.dc_mcp_token_cache.json` — then try any query again and re-login when the browser opens. |

### Tools not showing up

| What you see | What to do |
|---|---|
| No tools appear in Cursor | Click the **refresh icon** next to the server in **Cursor Settings > MCP**. If still nothing, restart Cursor completely (Cmd+Q / Ctrl+Q, then reopen). |
| Tools appear but return errors | Make sure you completed the Salesforce login (Part E). If the browser opened but you didn't click "Allow", try the query again. |

---

## Examples

The [examples/](examples/) folder has standalone scripts using the same OAuth + API helpers:

```bash
# Count active data streams
cd ~/.data360-mcp && source .venv/bin/activate
python examples/count_streams.py

# Dump org DMO metadata
python examples/dump_metadata.py
```

Useful for verifying your Connected App works before wiring up an MCP client.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and PRs welcome.

## License

[Apache License 2.0](LICENSE.txt). See [SECURITY.md](SECURITY.md) for vulnerability disclosure.

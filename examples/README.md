# Examples

Standalone Python scripts that exercise the same OAuth + Data Cloud helpers used by the MCP server. Useful when you want to script a quick check against your org without going through Cursor / Claude Desktop.

All scripts read the same environment variables as the MCP server (`SF_CLIENT_ID`, `SF_CLIENT_SECRET`, optionally `SF_LOGIN_URL`, `SF_CALLBACK_URL`). The first run will pop a browser for the OAuth login; subsequent runs reuse the cached token at `~/.dc_mcp_token_cache.json`.

| Script | What it does |
|---|---|
| `count_active_streams.py` | Prints the count of active data streams and lists each one by name. |
| `list_data_stream_names.py` | Prints all data stream names (any status), sorted alphabetically. |
| `retrieve_all_metadata.py` | Pulls a wide cross-section of org metadata via the REST + Tooling APIs (sObjects, Apex classes, flows, profiles, packages, users, etc.) and writes timestamped JSON files to `metadata_output/`. Takes a few minutes on a populated org. |

## Running

From the repo root:

```bash
pip install -r requirements.txt
export SF_CLIENT_ID=...
export SF_CLIENT_SECRET=...
python examples/count_active_streams.py
```

These scripts are not required to run the MCP server; they are kept here as references and as quick smoke tests for the OAuth + Connect API plumbing.

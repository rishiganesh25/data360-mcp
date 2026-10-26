# Examples

Standalone Python scripts that exercise the same OAuth + Data Cloud helpers used by the MCP server. Useful when you want to script a quick check against your org without going through Cursor / Claude Desktop.

All scripts use the same Salesforce CLI session as the MCP server. Log in with `sf org login web --alias data360` and, if needed, set `SF_TARGET_ORG=data360`.

| Script | What it does |
|---|---|
| `count_active_streams.py` | Prints the count of active data streams and lists each one by name. |
| `list_data_stream_names.py` | Prints all data stream names (any status), sorted alphabetically. |
| `retrieve_all_metadata.py` | Pulls a wide cross-section of org metadata via the REST + Tooling APIs (sObjects, Apex classes, flows, profiles, packages, users, etc.) and writes timestamped JSON files to `metadata_output/`. Takes a few minutes on a populated org. |

## Running

From the repo root:

```bash
pip install -r requirements.txt
sf org login web --alias data360
export SF_TARGET_ORG=data360
python examples/count_active_streams.py
```

These scripts are not required to run the MCP server; they are kept here as references and as quick smoke tests for the OAuth + Connect API plumbing.

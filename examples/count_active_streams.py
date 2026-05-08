#!/usr/bin/env python3
"""Quick script to count active data streams in the connected Salesforce Data Cloud org."""
import os
import sys

# Add current dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oauth import OAuthConfig, OAuthSession
from connect_api_datacloud import get_data_streams


def main():
    config = OAuthConfig.from_env()
    session = OAuthSession(config)
    
    result = get_data_streams(session)
    
    # Handle different response formats from the API
    if isinstance(result, dict):
        streams = result.get("dataStreams", result.get("data", []))
    else:
        streams = result if isinstance(result, list) else []
    
    active = [s for s in streams if isinstance(s, dict) and s.get("status") == "Active"]
    
    print(f"Active data streams: {len(active)}")
    print(f"Total data streams: {len(streams)}")
    if active:
        print("\nActive streams:")
        for s in active:
            print(f"  - {s.get('name', s.get('apiName', 'unknown'))}")


if __name__ == "__main__":
    main()

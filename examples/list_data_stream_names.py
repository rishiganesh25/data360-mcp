#!/usr/bin/env python3
"""List all data stream names from the connected Salesforce Data Cloud org."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oauth import OAuthConfig, OAuthSession
from connect_api_datacloud import get_data_streams


def main():
    config = OAuthConfig.from_env()
    session = OAuthSession(config)
    result = get_data_streams(session)

    if isinstance(result, dict):
        streams = result.get("dataStreams", result.get("data", []))
    else:
        streams = result if isinstance(result, list) else []

    names = []
    for s in streams:
        if isinstance(s, dict):
            name = s.get("name") or s.get("apiName") or s.get("label")
            if name:
                names.append(name)

    print("Data stream names:")
    for n in sorted(names):
        print(f"  - {n}")
    print(f"\nTotal: {len(names)}")


if __name__ == "__main__":
    main()

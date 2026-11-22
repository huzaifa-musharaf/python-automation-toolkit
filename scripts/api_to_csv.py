#!/usr/bin/env python3
"""Fetch JSON from a REST API and save it as a flat CSV file.

Usage:
    python api_to_csv.py https://jsonplaceholder.typicode.com/users -o users.csv
    python api_to_csv.py https://jsonplaceholder.typicode.com/posts --data-key "" --limit 20

The response may be a JSON list of objects, or an object containing a list
under a key (use --data-key to point at it; by default the first list-valued
key is used). Nested objects are flattened with dot notation, e.g.
``address.city``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import requests


def flatten(obj: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten one nested JSON object into a single-level dict."""
    items: dict[str, Any] = {}
    for key, value in obj.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten(value, new_key, sep=sep))
        elif isinstance(value, list):
            items[new_key] = json.dumps(value, ensure_ascii=False)
        else:
            items[new_key] = value
    return items


def extract_records(payload: Any, data_key: str | None) -> list[dict[str, Any]]:
    """Pull the list of record objects out of an API JSON payload."""
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        if data_key:
            if data_key not in payload:
                raise ValueError(f"data key '{data_key}' not found in response")
            records = payload[data_key]
        else:
            list_values = [v for v in payload.values() if isinstance(v, list)]
            if len(list_values) == 1:
                records = list_values[0]
            elif not list_values:
                records = [payload]
            else:
                raise ValueError("response contains several lists; pick one with --data-key")
    else:
        raise ValueError("unsupported JSON payload type")
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError("records are not a list of JSON objects")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch JSON from an API and write it to CSV.")
    parser.add_argument("url", help="API endpoint URL returning JSON")
    parser.add_argument("-o", "--output", type=Path, default=Path("api_output.csv"),
                        help="Output CSV path (default: api_output.csv)")
    parser.add_argument("--data-key", default=None,
                        help="Key holding the record list when the response is an object")
    parser.add_argument("--limit", type=int, default=None, help="Only write the first N records")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    args = parser.parse_args(argv)

    try:
        response = requests.get(args.url, timeout=args.timeout,
                                headers={"User-Agent": "python-automation-toolkit/1.0"})
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        print(f"error: request failed: {exc}", file=sys.stderr)
        return 1
    except ValueError:
        print("error: response was not valid JSON", file=sys.stderr)
        return 1

    try:
        records = extract_records(payload, args.data_key)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.limit is not None:
        records = records[: args.limit]
    if not records:
        print("error: no records found in response", file=sys.stderr)
        return 1

    flat = [flatten(record) for record in records]
    fieldnames: list[str] = []
    for row in flat:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat)

    print(f"Wrote {len(flat)} records with {len(fieldnames)} columns to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

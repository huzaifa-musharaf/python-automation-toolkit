#!/usr/bin/env python3
"""Convert a JSON file holding a list of objects into a CSV file.

Usage:
    python json_to_csv.py products.json -o products.csv
    python json_to_csv.py response.json -o rows.csv --key data

Behaviour:
  * The JSON file must hold a list of objects, or an object with one
    key (use --key) holding that list. API responses often wrap their
    rows this way, for example {"data": [...]}.
  * Nested objects are flattened with dot-separated keys, so
    {"address": {"city": "Lahore"}} becomes an "address.city" column.
  * List values are joined into one cell with "; " between items.
  * Columns are the union of every record's keys, in the order they
    first appear. Records missing a column get an empty cell.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def flatten_record(record: dict, prefix: str = "") -> dict[str, str]:
    """Flatten one JSON object into a flat dict of strings.

    Nested objects become dot-separated keys ("address.city") and
    lists become one string with "; " between items, so every value
    fits in a single CSV cell.
    """
    flat: dict[str, str] = {}
    for key, value in record.items():
        name = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict):
            flat.update(flatten_record(value, prefix=name))
        elif isinstance(value, list):
            flat[name] = "; ".join(str(item) for item in value)
        elif value is None:
            flat[name] = ""
        else:
            flat[name] = str(value)
    return flat


def records_to_table(records: list[dict]) -> tuple[list[str], list[dict[str, str]]]:
    """Turn a list of JSON objects into CSV column names and rows.

    Columns are the union of every record's flattened keys, in the
    order they first appear. A record missing a column gets an empty
    string for that cell, so every row has the same columns.
    """
    if not records:
        raise ValueError("JSON holds no records to convert")

    fieldnames: list[str] = []
    rows: list[dict[str, str]] = []
    for record in records:
        flat = flatten_record(record)
        for key in flat:
            if key not in fieldnames:
                fieldnames.append(key)
        rows.append(flat)

    for row in rows:
        for key in fieldnames:
            if key not in row:
                row[key] = ""
    return fieldnames, rows


def load_records(path: Path, key: str | None = None) -> list[dict]:
    """Read the list of objects out of a JSON file.

    With no --key the file itself must be a list. With --key the file
    must be an object holding the list under that key.
    """
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    if key is not None:
        if not isinstance(data, dict) or key not in data:
            raise ValueError(f"JSON object has no key {key!r}")
        data = data[key]

    if not isinstance(data, list):
        raise ValueError("JSON must hold a list of objects")
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("JSON list must hold objects, not plain values")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert a JSON list of objects into a CSV file.")
    parser.add_argument("input", type=Path, help="JSON file to convert")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output CSV path")
    parser.add_argument("--key", help="Key holding the list, when the JSON is an object wrapping it")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        records = load_records(args.input, args.key)
        fieldnames, rows = records_to_table(records)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Converted {len(rows)} records, wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

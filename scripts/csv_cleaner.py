#!/usr/bin/env python3
"""Clean a CSV file: trim whitespace, normalise headers and remove duplicates.

Usage:
    python csv_cleaner.py input.csv -o output.csv
    python csv_cleaner.py input.csv --dedupe-on email

Behaviour:
  * Header names are normalised to lowercase snake_case.
  * Every cell is stripped of leading/trailing whitespace.
  * Fully empty rows are dropped.
  * Duplicate rows are removed (all columns, or only the columns named
    with --dedupe-on).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


def normalise_header(name: str) -> str:
    """Return a header name in lowercase snake_case."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def clean_rows(rows: list[dict[str, str]], dedupe_on: list[str] | None = None) -> list[dict[str, str]]:
    """Trim cells, drop empty rows and remove duplicates from parsed CSV rows.

    This is a pure function (no I/O) so it can be unit-tested directly.
    """
    cleaned: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        trimmed = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
        if all(value in (None, "") for value in trimmed.values()):
            continue  # fully empty row
        if dedupe_on:
            key = tuple(trimmed.get(col, "") for col in dedupe_on)
        else:
            key = tuple(trimmed[col] for col in sorted(trimmed))
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(trimmed)
    return cleaned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean a CSV: trim, normalise headers, dedupe.")
    parser.add_argument("input", type=Path, help="Path to the input CSV file")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output path (default: <input>_cleaned.csv next to the input)")
    parser.add_argument("--dedupe-on", nargs="*", default=None, metavar="COLUMN",
                        help="Only consider these columns when detecting duplicates "
                             "(use the normalised header names)")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 1

    output = args.output or args.input.with_name(f"{args.input.stem}_cleaned.csv")

    with args.input.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            print("error: input CSV has no header row", file=sys.stderr)
            return 1
        fieldnames = [normalise_header(name) for name in reader.fieldnames]
        raw_rows = [
            {fieldnames[i]: (row.get(orig) or "") for i, orig in enumerate(reader.fieldnames)}
            for row in reader
        ]

    cleaned = clean_rows(raw_rows, dedupe_on=args.dedupe_on)

    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"Read {len(raw_rows)} rows, wrote {len(cleaned)} cleaned rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

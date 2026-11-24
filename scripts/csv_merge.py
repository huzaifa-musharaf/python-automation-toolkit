#!/usr/bin/env python3
"""Merge several CSV files with the same headers into one CSV file.

Usage:
    python csv_merge.py sales_jan.csv sales_feb.csv -o sales_h1.csv
    python csv_merge.py *.csv -o all.csv --add-source

Behaviour:
  * All input files must have the same header row, in the same order.
    If one differs, the merge stops with an error and writes nothing.
  * Rows keep their original order: all rows from the first file, then
    all rows from the second, and so on.
  * With --add-source, a "source_file" column is added holding the name
    of the file each row came from, which is handy when the merged file
    is later split or audited.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read one CSV file and return its header row and its rows."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        rows = [dict(row) for row in reader]
    return reader.fieldnames, rows


def merge_tables(
    tables: list[tuple[list[str], list[dict[str, str]]]],
    source_names: list[str] | None = None,
) -> tuple[list[str], list[dict[str, str]]]:
    """Combine the rows of several CSV tables into one header and row list.

    Every table must share the first table's headers. When source_names
    is given, a "source_file" column is added with the matching name
    for each row, so the origin of every row stays visible.
    """
    if not tables:
        return [], []

    fieldnames = list(tables[0][0])
    for headers, _rows in tables[1:]:
        if headers != fieldnames:
            raise ValueError("CSV files have different headers, cannot merge")

    merged: list[dict[str, str]] = []
    for index, (_headers, rows) in enumerate(tables):
        for row in rows:
            new_row = dict(row)
            if source_names is not None:
                new_row["source_file"] = source_names[index]
            merged.append(new_row)

    if source_names is not None:
        fieldnames = fieldnames + ["source_file"]
    return fieldnames, merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge CSV files with the same headers into one file.")
    parser.add_argument("inputs", type=Path, nargs="+", help="CSV files to merge")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output CSV path")
    parser.add_argument("--add-source", action="store_true",
                        help="Add a source_file column with the name of each row's file")
    args = parser.parse_args(argv)

    for path in args.inputs:
        if not path.is_file():
            print(f"error: input file not found: {path}", file=sys.stderr)
            return 1

    tables = []
    for path in args.inputs:
        try:
            tables.append(read_csv(path))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    source_names = [path.name for path in args.inputs] if args.add_source else None
    try:
        fieldnames, merged = merge_tables(tables, source_names)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    with args.output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    print(f"Merged {len(args.inputs)} files, wrote {len(merged)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

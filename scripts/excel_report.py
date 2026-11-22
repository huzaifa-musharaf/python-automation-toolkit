#!/usr/bin/env python3
"""Build a summary Excel report from a CSV file.

Usage:
    python excel_report.py sales.csv --category region --value amount -o report.xlsx

Reads the CSV, groups rows by the category column, and writes an .xlsx
workbook with two sheets:

  * "Data"    – the original rows, with a bold header row.
  * "Summary" – one row per category with row count, total, average, min
                and max of the value column, plus a grand-total row.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def summarise(rows: list[dict[str, str]], category: str, value: str) -> list[dict[str, float | int | str]]:
    """Aggregate rows by category. Pure function — no I/O."""
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        try:
            number = float(row[value])
        except (KeyError, TypeError, ValueError):
            continue  # skip rows whose value is missing or not numeric
        groups[str(row.get(category, ""))].append(number)

    summary: list[dict[str, float | int | str]] = []
    for name in sorted(groups):
        values = groups[name]
        summary.append({
            "category": name,
            "count": len(values),
            "total": round(sum(values), 2),
            "average": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
        })
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a summary Excel report from a CSV.")
    parser.add_argument("input", type=Path, help="Input CSV file")
    parser.add_argument("--category", required=True, help="Column to group by")
    parser.add_argument("--value", required=True, help="Numeric column to aggregate")
    parser.add_argument("-o", "--output", type=Path, default=Path("report.xlsx"),
                        help="Output .xlsx path (default: report.xlsx)")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 1

    with args.input.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        for column in (args.category, args.value):
            if column not in fieldnames:
                print(f"error: column '{column}' not in CSV (has: {', '.join(fieldnames)})",
                      file=sys.stderr)
                return 1
        rows = list(reader)

    summary = summarise(rows, args.category, args.value)
    if not summary:
        print("error: no numeric values found to summarise", file=sys.stderr)
        return 1

    wb = Workbook()

    data_sheet = wb.active
    data_sheet.title = "Data"
    data_sheet.append(fieldnames)
    for cell in data_sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        data_sheet.append([row.get(name, "") for name in fieldnames])

    summary_sheet = wb.create_sheet("Summary")
    headers = ["Category", "Rows", "Total", "Average", "Min", "Max"]
    summary_sheet.append(headers)
    for cell in summary_sheet[1]:
        cell.font = Font(bold=True)
    for entry in summary:
        summary_sheet.append([entry["category"], entry["count"], entry["total"],
                              entry["average"], entry["min"], entry["max"]])
    total_count = sum(int(e["count"]) for e in summary)
    total_value = round(sum(float(e["total"]) for e in summary), 2)
    total_row = summary_sheet.max_row + 1
    summary_sheet.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
    summary_sheet.cell(row=total_row, column=2, value=total_count).font = Font(bold=True)
    summary_sheet.cell(row=total_row, column=3, value=total_value).font = Font(bold=True)

    for sheet in (data_sheet, summary_sheet):
        for column_cells in sheet.columns:
            width = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(width + 2, 40)

    wb.save(args.output)
    print(f"Wrote {args.output}: {len(rows)} data rows, {len(summary)} categories summarised")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

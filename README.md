# Python Automation Toolkit

Practical Python automation scripts for everyday business data chores:
cleaning CSVs, turning API responses into spreadsheets, tidying folders and
building Excel summary reports. Each script is a small, dependency-light
command-line tool with no hardcoded paths — pass files and options as
arguments.

## Requirements

- Python 3.10+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Script catalogue

| Script | What it does |
| --- | --- |
| `scripts/csv_cleaner.py` | Trims whitespace, normalises headers to snake_case, drops empty rows and removes duplicates from a CSV. |
| `scripts/csv_merge.py` | Merges several CSV files with the same headers into one, with an optional `source_file` column recording where each row came from. |
| `scripts/json_to_csv.py` | Converts a JSON file holding a list of objects into a CSV, flattening nested objects into dot-separated columns. |
| `scripts/api_to_csv.py` | Fetches JSON from a REST API, flattens nested objects and writes a CSV. Handles list responses and object responses with a data key. |
| `scripts/file_organizer.py` | Sorts a folder's files into subfolders by extension (`pdf/`, `jpg/`, …), with a `--dry-run` preview mode and collision-safe renaming. |
| `scripts/excel_report.py` | Builds an `.xlsx` report from a CSV: the raw data plus a Summary sheet with count, total, average, min and max per category. |
| `scripts/duplicate_finder.py` | Finds files with identical contents in a folder (size first, then SHA-256 hash) and can delete the extra copies, keeping one of each. |

## Quick examples

Clean the sample messy CSV (dedupe, trim, normalise headers):

```bash
python scripts/csv_cleaner.py samples/messy_customers.csv -o cleaned.csv
```

Download users from a public test API into a CSV:

```bash
python scripts/api_to_csv.py https://jsonplaceholder.typicode.com/users -o users.csv
```

Combine monthly CSV files with the same headers into one, keeping track of each row's source file:

```bash
python scripts/csv_merge.py sales_jan.csv sales_feb.csv -o sales_h1.csv --add-source
```

Turn a JSON export into a spreadsheet, including one wrapped in a `data` key:

```bash
python scripts/json_to_csv.py products.json -o products.csv
python scripts/json_to_csv.py response.json -o rows.csv --key data
```

Preview how a folder would be organised, then do it for real:

```bash
python scripts/file_organizer.py ~/Downloads --dry-run
python scripts/file_organizer.py ~/Downloads
```

Summarise spending per city from the cleaned sample into an Excel report:

```bash
python scripts/excel_report.py cleaned.csv --category city --value amount_spent -o report.xlsx
```

Find duplicate files in a folder (same size, then same SHA-256 hash), and delete the extra copies after confirming:

```bash
python scripts/duplicate_finder.py ~/Downloads --min-size 1024
python scripts/duplicate_finder.py ~/Downloads --delete
```

Every script supports `--help` for full options.

## Tests

```bash
pip install pytest
pytest
```

The tests cover the CSV cleaning logic (`clean_rows`, `normalise_header`)
in `tests/test_csv_cleaner.py`, the CSV merging logic (`merge_tables`)
in `tests/test_csv_merge.py` — including the `source_file` column and the
error on mismatched headers — the JSON conversion logic
(`flatten_record`, `records_to_table`, `load_records`) in
`tests/test_json_to_csv.py` — including nested objects, the `--key`
wrapper, and the errors on bad input — and the file organising logic
(`organise`, `target_folder_name`, `unique_destination`) in
`tests/test_file_organizer.py` — including the `--dry-run` preview, hidden
files being left alone, and name collisions being renamed instead of
overwritten — and the duplicate finding logic (`find_duplicates`,
`hash_file`, `group_by_size`, `delete_duplicates`) in
`tests/test_duplicate_finder.py` — including same-size files with different
content not being flagged, hidden files being skipped, and deleting keeping
the first copy.

## License

MIT — see [LICENSE](LICENSE).

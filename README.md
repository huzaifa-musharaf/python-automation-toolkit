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
| `scripts/api_to_csv.py` | Fetches JSON from a REST API, flattens nested objects and writes a CSV. Handles list responses and object responses with a data key. |
| `scripts/file_organizer.py` | Sorts a folder's files into subfolders by extension (`pdf/`, `jpg/`, …), with a `--dry-run` preview mode and collision-safe renaming. |
| `scripts/excel_report.py` | Builds an `.xlsx` report from a CSV: the raw data plus a Summary sheet with count, total, average, min and max per category. |

## Quick examples

Clean the sample messy CSV (dedupe, trim, normalise headers):

```bash
python scripts/csv_cleaner.py samples/messy_customers.csv -o cleaned.csv
```

Download users from a public test API into a CSV:

```bash
python scripts/api_to_csv.py https://jsonplaceholder.typicode.com/users -o users.csv
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

Every script supports `--help` for full options.

## Tests

```bash
pip install pytest
pytest
```

The tests cover the CSV cleaning logic (`clean_rows`, `normalise_header`)
in `tests/test_csv_cleaner.py`, and the file organising logic
(`organise`, `target_folder_name`, `unique_destination`) in
`tests/test_file_organizer.py` — including the `--dry-run` preview, hidden
files being left alone, and name collisions being renamed instead of
overwritten.

## License

MIT — see [LICENSE](LICENSE).

"""Tests for the pure cleaning logic in scripts/csv_cleaner.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from csv_cleaner import clean_rows, normalise_header  # noqa: E402


def test_normalise_header_to_snake_case():
    assert normalise_header("First Name") == "first_name"
    assert normalise_header("  Email Address ") == "email_address"
    assert normalise_header("Phone #") == "phone"


def test_trims_whitespace_and_drops_empty_rows():
    rows = [
        {"name": "  Alice ", "city": " Lahore"},
        {"name": "", "city": "   "},
        {"name": "Bob", "city": "Karachi"},
    ]
    result = clean_rows(rows)
    assert result == [
        {"name": "Alice", "city": "Lahore"},
        {"name": "Bob", "city": "Karachi"},
    ]


def test_removes_exact_duplicate_rows():
    rows = [
        {"name": "Alice", "city": "Lahore"},
        {"name": "Alice", "city": "Lahore"},
        {"name": "Alice", "city": "Karachi"},
    ]
    result = clean_rows(rows)
    assert len(result) == 2


def test_dedupe_on_single_column():
    rows = [
        {"email": "a@example.com", "name": "Alice"},
        {"email": "a@example.com", "name": "Alicia"},
        {"email": "b@example.com", "name": "Bob"},
    ]
    result = clean_rows(rows, dedupe_on=["email"])
    assert [r["name"] for r in result] == ["Alice", "Bob"]


def test_keeps_first_occurrence_order():
    rows = [{"n": "3"}, {"n": "1"}, {"n": "3"}, {"n": "2"}]
    result = clean_rows(rows)
    assert [r["n"] for r in result] == ["3", "1", "2"]

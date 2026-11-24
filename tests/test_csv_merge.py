"""Tests for the pure merging logic in scripts/csv_merge.py."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from csv_merge import merge_tables  # noqa: E402


def test_merges_rows_in_file_order():
    first = (["name", "city"], [{"name": "Alice", "city": "Lahore"}])
    second = (["name", "city"], [{"name": "Bob", "city": "Karachi"}])
    _headers, merged = merge_tables([first, second])
    assert [row["name"] for row in merged] == ["Alice", "Bob"]


def test_merging_no_tables_gives_empty_result():
    headers, merged = merge_tables([])
    assert headers == []
    assert merged == []


def test_add_source_column_records_each_rows_file():
    first = (["name"], [{"name": "Alice"}])
    second = (["name"], [{"name": "Bob"}])
    headers, merged = merge_tables([first, second], source_names=["jan.csv", "feb.csv"])
    assert headers == ["name", "source_file"]
    assert [row["source_file"] for row in merged] == ["jan.csv", "feb.csv"]


def test_different_headers_raise_an_error():
    first = (["name", "city"], [{"name": "Alice", "city": "Lahore"}])
    second = (["name", "amount"], [{"name": "Bob", "amount": "10"}])
    with pytest.raises(ValueError, match="different headers"):
        merge_tables([first, second])

"""Tests for the pure conversion logic in scripts/json_to_csv.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from json_to_csv import flatten_record, load_records, records_to_table  # noqa: E402


def test_flatten_record_uses_dot_keys_for_nested_objects():
    flat = flatten_record({"name": "Ali", "address": {"city": "Lahore", "area": "Gulberg"}})
    assert flat == {"name": "Ali", "address.city": "Lahore", "address.area": "Gulberg"}


def test_flatten_record_joins_lists_and_blanks_none():
    flat = flatten_record({"tags": ["new", "sale"], "note": None, "price": 250})
    assert flat == {"tags": "new; sale", "note": "", "price": "250"}


def test_records_to_table_collects_columns_in_first_seen_order():
    records = [{"name": "Ali", "city": "Lahore"}, {"name": "Sara", "amount": "40"}]
    headers, rows = records_to_table(records)
    assert headers == ["name", "city", "amount"]
    assert rows[0] == {"name": "Ali", "city": "Lahore", "amount": ""}
    assert rows[1] == {"name": "Sara", "city": "", "amount": "40"}


def test_records_to_table_rejects_empty_list():
    with pytest.raises(ValueError, match="no records"):
        records_to_table([])


def test_load_records_reads_plain_list(tmp_path):
    path = tmp_path / "items.json"
    path.write_text(json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8")
    assert load_records(path) == [{"id": 1}, {"id": 2}]


def test_load_records_reads_list_under_key(tmp_path):
    path = tmp_path / "wrapped.json"
    path.write_text(json.dumps({"data": [{"id": 1}], "total": 1}), encoding="utf-8")
    assert load_records(path, key="data") == [{"id": 1}]


def test_load_records_rejects_missing_key(tmp_path):
    path = tmp_path / "wrapped.json"
    path.write_text(json.dumps({"rows": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="no key"):
        load_records(path, key="data")


def test_load_records_rejects_list_of_plain_values(tmp_path):
    path = tmp_path / "values.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="must hold objects"):
        load_records(path)

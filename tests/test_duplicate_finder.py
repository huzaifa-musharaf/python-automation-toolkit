"""Tests for the duplicate finder script."""

import hashlib

from scripts.duplicate_finder import (
    delete_duplicates,
    find_duplicates,
    format_size,
    group_by_size,
    hash_file,
    list_files,
    main,
)


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_group_by_size_groups_same_sizes(tmp_path):
    a = write_file(tmp_path / "a.txt", b"hello")
    b = write_file(tmp_path / "b.txt", b"world")
    c = write_file(tmp_path / "c.txt", b"longer content here")
    groups = group_by_size([a, b, c])
    assert len(groups[5]) == 2
    assert len(groups[19]) == 1


def test_hash_file_matches_hashlib(tmp_path):
    path = write_file(tmp_path / "a.txt", b"some content")
    assert hash_file(path) == hashlib.sha256(b"some content").hexdigest()


def test_same_size_different_content_is_not_a_duplicate(tmp_path):
    write_file(tmp_path / "a.txt", b"hello")
    write_file(tmp_path / "b.txt", b"world")
    assert find_duplicates(tmp_path) == []


def test_identical_files_are_grouped(tmp_path):
    a = write_file(tmp_path / "a.txt", b"same content")
    b = write_file(tmp_path / "sub" / "b.txt", b"same content")
    c = write_file(tmp_path / "c.txt", b"same content")
    groups = find_duplicates(tmp_path)
    assert len(groups) == 1
    # Sorted by path, so c.txt comes before sub/b.txt.
    assert groups[0] == [a, c, b]


def test_hidden_files_are_skipped(tmp_path):
    write_file(tmp_path / ".hidden.txt", b"same content")
    write_file(tmp_path / "a.txt", b"same content")
    assert find_duplicates(tmp_path) == []


def test_min_size_filters_small_files(tmp_path):
    write_file(tmp_path / "a.txt", b"small")
    write_file(tmp_path / "b.txt", b"small")
    assert find_duplicates(tmp_path, min_size=10) == []
    assert len(find_duplicates(tmp_path, min_size=5)) == 1


def test_delete_duplicates_keeps_first_copy(tmp_path):
    a = write_file(tmp_path / "a.txt", b"same content")
    b = write_file(tmp_path / "b.txt", b"same content")
    c = write_file(tmp_path / "c.txt", b"same content")
    deleted, freed = delete_duplicates([[a, b, c]])
    assert deleted == 2
    assert freed == 2 * len(b"same content")
    assert a.exists()
    assert not b.exists()
    assert not c.exists()


def test_empty_folder_has_no_duplicates(tmp_path):
    assert find_duplicates(tmp_path) == []


def test_format_size():
    assert format_size(500) == "500 B"
    assert format_size(2048) == "2 KB"
    assert format_size(3 * 1024 * 1024) == "3 MB"


def test_list_files_skips_hidden_folders(tmp_path):
    write_file(tmp_path / ".cache" / "x.txt", b"data")
    write_file(tmp_path / "a.txt", b"data")
    assert list_files(tmp_path) == [tmp_path / "a.txt"]


def test_main_missing_folder_returns_error(tmp_path):
    assert main([str(tmp_path / "no-such-folder")]) == 1


def test_main_reports_no_duplicates(tmp_path, capsys):
    assert main([str(tmp_path)]) == 0
    assert "No duplicate files found" in capsys.readouterr().out

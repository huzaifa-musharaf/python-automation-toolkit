"""Tests for the folder organising logic in scripts/file_organizer.py.

The tests use pytest's tmp_path fixture, which gives each test a fresh
empty folder, so nothing on the real machine is ever moved around.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from file_organizer import organise, target_folder_name, unique_destination  # noqa: E402


def make_file(folder: Path, name: str) -> Path:
    """Create a small file in folder and return its path."""
    path = folder / name
    path.write_text("sample content")
    return path


def test_folder_name_uses_lowercase_extension():
    assert target_folder_name(Path("report.PDF")) == "pdf"
    assert target_folder_name(Path("photo.jpg")) == "jpg"


def test_folder_name_for_files_without_extension():
    assert target_folder_name(Path("README")) == "no_extension"


def test_unique_destination_returns_path_when_free():
    folder = Path("/tmp")  # only used as a path, never touched on disk
    assert unique_destination(folder / "report.pdf") == folder / "report.pdf"


def test_unique_destination_adds_counter_when_taken(tmp_path):
    existing = make_file(tmp_path, "report.pdf")
    assert unique_destination(existing) == tmp_path / "report_1.pdf"


def test_unique_destination_keeps_counting(tmp_path):
    make_file(tmp_path, "report.pdf")
    make_file(tmp_path, "report_1.pdf")
    assert unique_destination(tmp_path / "report.pdf") == tmp_path / "report_2.pdf"


def test_dry_run_moves_nothing(tmp_path):
    make_file(tmp_path, "a.pdf")
    make_file(tmp_path, "b.jpg")

    moves = organise(tmp_path, dry_run=True)

    # Dry run only plans the moves: the files stay where they were and no
    # subfolders are created.
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.pdf", "b.jpg"]
    assert moves == [
        (tmp_path / "a.pdf", tmp_path / "pdf" / "a.pdf"),
        (tmp_path / "b.jpg", tmp_path / "jpg" / "b.jpg"),
    ]


def test_real_run_moves_files_into_extension_folders(tmp_path):
    make_file(tmp_path, "a.pdf")
    make_file(tmp_path, "b.jpg")

    moves = organise(tmp_path, dry_run=False)

    assert len(moves) == 2
    assert (tmp_path / "pdf" / "a.pdf").is_file()
    assert (tmp_path / "jpg" / "b.jpg").is_file()
    assert not (tmp_path / "a.pdf").exists()


def test_real_run_skips_hidden_files_and_subfolders(tmp_path):
    make_file(tmp_path, ".hidden.txt")
    make_file(tmp_path, "visible.txt")
    subfolder = tmp_path / "keep_me"
    subfolder.mkdir()
    make_file(subfolder, "inside.txt")

    moves = organise(tmp_path, dry_run=False)

    assert [source.name for source, _ in moves] == ["visible.txt"]
    assert (tmp_path / ".hidden.txt").exists()
    assert (subfolder / "inside.txt").exists()


def test_real_run_renames_on_collision(tmp_path):
    # A report.pdf already sits in the pdf/ folder, so the loose report.pdf
    # must be moved in as report_1.pdf instead of overwriting it.
    target = tmp_path / "pdf"
    target.mkdir()
    make_file(target, "report.pdf")
    make_file(tmp_path, "report.pdf")

    organise(tmp_path, dry_run=False)

    assert (target / "report.pdf").is_file()
    assert (target / "report_1.pdf").is_file()

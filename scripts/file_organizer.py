#!/usr/bin/env python3
"""Organise a folder by moving files into subfolders named by extension.

Usage:
    python file_organizer.py ~/Downloads --dry-run   # preview only
    python file_organizer.py ~/Downloads             # actually move

Files are grouped like ``pdf/``, ``jpg/``, ``zip/`` … Files without an
extension go into ``no_extension/``. Subfolders and hidden files are left
alone, and name collisions are resolved by appending a counter
(``report_1.pdf``) instead of overwriting.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def target_folder_name(path: Path) -> str:
    """Return the subfolder name a file belongs in, based on its extension."""
    suffix = path.suffix.lower().lstrip(".")
    return suffix if suffix else "no_extension"


def unique_destination(destination: Path) -> Path:
    """Return a non-conflicting path by appending _1, _2, … if needed."""
    if not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        candidate = destination.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organise(folder: Path, dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Plan (and optionally perform) the moves. Returns (source, destination) pairs."""
    moves: list[tuple[Path, Path]] = []
    for entry in sorted(folder.iterdir()):
        if not entry.is_file() or entry.name.startswith("."):
            continue
        destination_dir = folder / target_folder_name(entry)
        destination = unique_destination(destination_dir / entry.name)
        moves.append((entry, destination))
        if dry_run:
            print(f"[dry-run] {entry.name} -> {destination.relative_to(folder)}")
        else:
            destination_dir.mkdir(exist_ok=True)
            shutil.move(str(entry), str(destination))
            print(f"moved {entry.name} -> {destination.relative_to(folder)}")
    return moves


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sort a folder's files into subfolders by extension.")
    parser.add_argument("folder", type=Path, help="Folder to organise")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen without moving anything")
    args = parser.parse_args(argv)

    if not args.folder.is_dir():
        print(f"error: not a folder: {args.folder}", file=sys.stderr)
        return 1

    moves = organise(args.folder, dry_run=args.dry_run)
    verb = "would move" if args.dry_run else "moved"
    print(f"{verb} {len(moves)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

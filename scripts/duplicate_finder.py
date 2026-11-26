#!/usr/bin/env python3
"""Find duplicate files in a folder and, optionally, delete the extra copies.

Usage:
    python duplicate_finder.py ~/Downloads
    python duplicate_finder.py ~/Pictures --min-size 1024
    python duplicate_finder.py ~/Downloads --delete
    python duplicate_finder.py ~/Downloads --delete --yes

Behaviour:
  * Files are first grouped by size, which is cheap. Only files that share
    a size are then hashed (SHA-256), so scanning a big folder stays fast.
  * Two files count as duplicates only when their hashes match, so files
    that happen to be the same size but hold different content are never
    flagged.
  * With --delete, the first file in each duplicate group is kept and the
    rest are deleted. Without --yes, it asks for confirmation first.
  * Hidden files and folders (names starting with a dot) are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Read files in chunks so a very large file is never loaded into memory.
CHUNK_SIZE = 1024 * 1024


def list_files(folder: Path) -> list[Path]:
    """Return every visible file under folder, including in subfolders."""
    found: list[Path] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.is_symlink():
            continue
        if any(part.startswith(".") for part in path.relative_to(folder).parts):
            continue
        found.append(path)
    return found


def group_by_size(files: list[Path]) -> dict[int, list[Path]]:
    """Group files by their size in bytes."""
    groups: dict[int, list[Path]] = {}
    for path in files:
        size = path.stat().st_size
        groups.setdefault(size, []).append(path)
    return groups


def hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(folder: Path, min_size: int = 0) -> list[list[Path]]:
    """Find groups of files under folder with identical contents.

    Only files at least min_size bytes are considered. Each group holds
    two or more paths to files with the same content.
    """
    files = list_files(folder)
    duplicates: list[list[Path]] = []
    for size, same_size in group_by_size(files).items():
        if size < min_size or len(same_size) < 2:
            continue
        by_hash: dict[str, list[Path]] = {}
        for path in same_size:
            by_hash.setdefault(hash_file(path), []).append(path)
        for group in by_hash.values():
            if len(group) > 1:
                duplicates.append(sorted(group))
    duplicates.sort(key=lambda group: str(group[0]))
    return duplicates


def format_size(size: int) -> str:
    """Render a byte count as a short human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size} {unit}"
        size //= 1024
    return f"{size} TB"


def delete_duplicates(groups: list[list[Path]]) -> tuple[int, int]:
    """Delete every file except the first in each duplicate group.

    Returns how many files were deleted and how many bytes that freed.
    """
    deleted = 0
    freed = 0
    for group in groups:
        for path in group[1:]:
            freed += path.stat().st_size
            path.unlink()
            deleted += 1
    return deleted, freed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find duplicate files in a folder.")
    parser.add_argument("folder", type=Path, help="Folder to scan, including subfolders")
    parser.add_argument("--min-size", type=int, default=0,
                        help="Ignore files smaller than this many bytes")
    parser.add_argument("--delete", action="store_true",
                        help="Delete all but the first copy of each duplicate")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the confirmation prompt when deleting")
    args = parser.parse_args(argv)

    if not args.folder.is_dir():
        print(f"error: folder not found: {args.folder}", file=sys.stderr)
        return 1
    if args.min_size < 0:
        print("error: --min-size cannot be negative", file=sys.stderr)
        return 1

    groups = find_duplicates(args.folder, args.min_size)
    if not groups:
        print(f"No duplicate files found in {args.folder}")
        return 0

    total_files = sum(len(group) for group in groups)
    wasted = 0
    for group in groups:
        size = group[0].stat().st_size
        wasted += size * (len(group) - 1)
        print(f"\n{format_size(size)} each, {len(group)} copies:")
        for path in group:
            print(f"  {path}")

    group_word = "group" if len(groups) == 1 else "groups"
    print(f"\n{len(groups)} duplicate {group_word}, {total_files} files, "
          f"{format_size(wasted)} could be freed by keeping one copy of each.")

    if not args.delete:
        return 0

    if not args.yes:
        answer = input(f"Delete {total_files - len(groups)} extra copies? [y/N] ")
        if answer.strip().lower() != "y":
            print("Cancelled, nothing deleted.")
            return 0

    deleted, freed = delete_duplicates(groups)
    print(f"Deleted {deleted} files, freed {format_size(freed)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

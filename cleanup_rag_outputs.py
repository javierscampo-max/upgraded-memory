#!/usr/bin/env python3
"""
Remove artifacts produced by rag_builder.py to reset the local data state.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from config import DATA_DIR, EMBEDDINGS_DIR


def _clear_directory_contents(directory: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Delete all files and folders inside directory while keeping the directory itself."""
    removed: list[Path] = []
    errors: list[tuple[Path, str]] = []

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return removed, errors

    for entry in directory.iterdir():
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed.append(entry)
        except Exception as exc:  # noqa: BLE001 - report the issue and continue
            errors.append((entry, str(exc)))

    directory.mkdir(parents=True, exist_ok=True)
    return removed, errors


def _format_paths(paths: list[Path]) -> str:
    return "\n".join(f"- {path}" for path in paths)


def main() -> int:
    removed_items: list[Path] = []
    error_items: list[tuple[Path, str]] = []

    for target_dir in (DATA_DIR, EMBEDDINGS_DIR):
        removed, errors = _clear_directory_contents(target_dir)
        removed_items.extend(removed)
        error_items.extend(errors)

    if removed_items:
        print("Removed artifacts:")
        print(_format_paths(removed_items))
    else:
        print("No artifacts to remove.")

    if error_items:
        print("\nFailed to remove some items:")
        for path, reason in error_items:
            print(f"- {path}: {reason}")
        return 1

    print("\nCleanup completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

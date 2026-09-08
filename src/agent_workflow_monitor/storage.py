from __future__ import annotations

import os
from pathlib import Path

from .models import SchemaError


def measure_storage(path: str | Path) -> int:
    """Measure one explicitly configured path without following symlinks or writing."""
    root = Path(path).expanduser().resolve()
    home = Path.home().resolve()
    if root in {Path(root.anchor), home}:
        raise SchemaError("broad storage roots are not allowed")
    if not root.exists():
        raise SchemaError("configured storage path is unavailable")
    if root.is_file():
        return root.stat().st_size
    total = 0
    pending = [root]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
    return total


def format_bytes(value: int | None) -> str:
    if value is None:
        return "Not measured"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(value)
    for unit in units:
        if abs(size) < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return "Not measured"

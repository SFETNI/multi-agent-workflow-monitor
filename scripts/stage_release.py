"""Copy only an explicit allowlist; no scanner exemptions for development caches."""
from __future__ import annotations

import shutil
from pathlib import Path


def stage(candidate: Path, files: list[str], target: Path) -> Path:
    if target.exists():
        raise ValueError("staging destination must not exist")
    candidate = candidate.resolve()
    target.mkdir(parents=True)
    for relative in files:
        source = candidate / relative
        if not source.is_file() or source.is_symlink() or any(p.is_symlink() for p in source.parents if p != candidate and candidate in p.parents):
            raise ValueError("allowlisted source is missing or unsafe")
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return target

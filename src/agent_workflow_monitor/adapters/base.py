from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SourceFingerprint:
    size: int
    mtime_ns: int
    sha256: str


def fingerprint(path: Path) -> SourceFingerprint:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return SourceFingerprint(stat.st_size, stat.st_mtime_ns, digest.hexdigest())


class ReadOnlyAdapter(ABC, Generic[T]):
    @abstractmethod
    def read(self) -> T:
        """Read an explicitly configured source without changing it."""

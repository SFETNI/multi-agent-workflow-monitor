from __future__ import annotations

from pathlib import Path

from ..models import PublicSnapshot, SchemaError
from ..schema import load_snapshot
from .base import ReadOnlyAdapter, fingerprint


class SnapshotAdapter(ReadOnlyAdapter[PublicSnapshot]):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self) -> PublicSnapshot:
        before = fingerprint(self.path)
        snapshot = load_snapshot(self.path)
        after = fingerprint(self.path)
        if before != after:
            raise SchemaError("source changed while it was being read")
        return snapshot

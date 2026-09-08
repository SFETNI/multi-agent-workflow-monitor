from __future__ import annotations

import json
from pathlib import Path

from ..models import ActivityEvent, SchemaError
from .base import ReadOnlyAdapter, fingerprint


class JsonlActivityAdapter(ReadOnlyAdapter[tuple[ActivityEvent, ...]]):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self) -> tuple[ActivityEvent, ...]:
        before = fingerprint(self.path)
        events = []
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    events.append(ActivityEvent.from_dict(json.loads(line)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SchemaError("activity source unavailable or malformed") from exc
        after = fingerprint(self.path)
        if before != after:
            raise SchemaError("source changed while it was being read")
        return tuple(sorted(events, key=lambda event: event.relative_order))

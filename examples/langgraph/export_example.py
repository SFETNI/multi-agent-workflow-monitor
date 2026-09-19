"""Optional example: export already-normalized LangGraph callbacks without importing LangGraph."""
from __future__ import annotations
import json
from pathlib import Path


def export(manifest: dict, events: list[dict], target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "workflow_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with (target / "events.jsonl").open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

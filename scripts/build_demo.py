#!/usr/bin/env python3
"""Generate static and embedded demos from one validated snapshot and renderer."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_workflow_monitor.presentation import RENDERER, encode_js, presentation_assets, project_snapshot
from agent_workflow_monitor.schema import load_config, load_snapshot


def build(output: Path | None = None) -> dict:
    target = output or ROOT / "demo" / "static"
    snapshot = load_snapshot(ROOT / "demo" / "public_snapshot.json")
    config = load_config(ROOT / "config" / "example.yaml")
    projection = project_snapshot(snapshot, config)
    (target / "data").mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "app.js", "geometry.js", "presentation.css", "shell.css"):
        shutil.copyfile(RENDERER / name, target / name)
    (target / "presentation.js").write_text("window.PRESENTATION = " + encode_js(presentation_assets(snapshot, config["roles"])) + ";\n", encoding="utf-8")
    (target / "data" / "public_snapshot.json").write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "data" / "public_snapshot.js").write_text("window.PUBLIC_SNAPSHOT = " + encode_js(projection) + ";\n", encoding="utf-8")
    return projection


if __name__ == "__main__":
    build()
    print("Validated v2 demo built from shared renderer")

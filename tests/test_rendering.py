from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from agent_workflow_monitor.presentation import RENDERER, presentation_assets, project_snapshot, render_overview_html
from agent_workflow_monitor.schema import load_config, load_snapshot, parse_snapshot
from build_demo import build

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    return load_snapshot(ROOT / "demo/public_snapshot.json"), load_config(ROOT / "config/example.yaml")


def test_projection_exactly_matches_accepted_public_v2_data():
    snapshot, config = inputs()
    assert project_snapshot(snapshot, config) == json.loads((ROOT / "demo/accepted_snapshot.json").read_text())


def test_mature_visual_sources_are_retained_by_digest():
    receipt = json.loads((ROOT / "docs/renderer-source.json").read_text())
    for name in receipt["unchanged"]:
        assert hashlib.sha256((RENDERER / name).read_bytes()).hexdigest() == receipt["source_files"][name], name


def test_static_and_runtime_use_identical_renderer(tmp_path):
    snapshot, config = inputs()
    build(tmp_path / "static")
    embedded = render_overview_html(snapshot, config)
    for name in ("app.js", "geometry.js", "presentation.css", "shell.css"):
        content = (RENDERER / name).read_text()
        assert (tmp_path / "static" / name).read_text() == content
        assert content in embedded
    assert "connect-src 'none'" in embedded


def test_stale_label_and_animation_are_derived_together():
    snapshot, config = inputs()
    data = project_snapshot(snapshot, config, now=datetime(2027, 1, 1, tzinfo=timezone.utc))
    active = [a for a in data["agents"] if a["id"] in {"A-01", "A-02", "A-04"}]
    assert all(a["status"] == "stale" and not a["working"] for a in active)
    assert not any(e["active"] for e in data["edges"])


def test_freshness_settings_change_visible_states():
    snapshot, config = inputs()
    config["freshness_seconds"] = {"activity": 1, "host": 1}
    data = project_snapshot(snapshot, config)
    assert data["summary"]["active_agents"] == 0
    assert "Host telemetry: Stale" in data["summary"]["freshness"]


def test_disallowed_metrics_are_absent_even_from_hidden_projection():
    snapshot, config = inputs(); config["approved_metrics"] = []
    data = project_snapshot(snapshot, config)
    assert set(data["host"].values()) == {"Not measured"}
    for row in data["sessions"]:
        assert row["value"] == row["storage"] == "Not measured"
        assert row["percent"] is None and row["growth"] is None
    html = render_overview_html(snapshot, config)
    for metric in ("178.8k", "66.8 GB", "995 / 8192 MiB"):
        assert metric not in html


def test_configured_role_labels_and_icons_reach_renderer():
    snapshot, config = inputs()
    config["roles"]["worker"] = {"label": "Quality Analyst", "icon": "evaluator.svg"}
    data = project_snapshot(snapshot, config)
    assert next(a for a in data["agents"] if a["id"] == "A-02")["role"] == "Quality Analyst"
    assert presentation_assets(snapshot, config["roles"])["slot_icons"]["A-02"] == (RENDERER / "roles/evaluator.svg").read_text()


def test_local_observation_uses_current_clock_and_local_label():
    raw = json.loads((ROOT / "demo/public_snapshot.json").read_text())
    raw["snapshot_kind"] = "local_observation"
    for p in raw["participants"]: p["context_usage"].pop("illustrative", None)
    data = project_snapshot(parse_snapshot(raw), inputs()[1], now=datetime(2027, 1, 1, tzinfo=timezone.utc))
    assert data["disclosure"].startswith("Local observation")
    assert data["summary"]["active_agents"] == 0


def test_generated_json_and_js_match_and_no_obsolete_demo():
    data = ROOT / "demo/static/data"
    js = (data / "public_snapshot.js").read_text()
    assert json.loads(js.removeprefix("window.PUBLIC_SNAPSHOT = ").strip().removesuffix(";")) == json.loads((data / "public_snapshot.json").read_text())
    assert not (ROOT / "demo/static/styles.css").exists()

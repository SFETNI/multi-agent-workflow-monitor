from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from agent_workflow_monitor.models import SchemaError
from agent_workflow_monitor.presentation import render_overview_html
from agent_workflow_monitor.schema import load_config, load_snapshot
from agent_workflow_monitor.workflow import derive_run_state, validate_manifest, validate_workflow_event, validate_workflow_snapshot

ROOT = Path(__file__).resolve().parents[1]


def trace():
    return json.loads((ROOT / "demo/workflow/workflow_trace.json").read_text())


def test_manifest_fanout_fanin_and_multiple_conditions_are_valid():
    manifest = validate_manifest(trace()["manifest"])
    assert sum(edge["to"] == "evaluate" for edge in manifest["edges"]) == 3
    copy = deepcopy(manifest)
    copy["edges"].append({"from": "evaluate", "to": "human_gate", "condition": "manual"})
    assert validate_manifest(copy)


def test_duplicate_node_and_invalid_edge_are_rejected():
    manifest = deepcopy(trace()["manifest"]); manifest["nodes"].append(deepcopy(manifest["nodes"][0]))
    with pytest.raises(SchemaError): validate_manifest(manifest)
    manifest = deepcopy(trace()["manifest"]); manifest["edges"][0]["to"] = "missing"
    with pytest.raises(SchemaError): validate_manifest(manifest)


def test_paused_run_separates_state_from_freshness_and_summarizes_retry():
    data = validate_workflow_snapshot(trace())
    state = derive_run_state(data, now=datetime(2026, 9, 19, 12, 15, tzinfo=timezone.utc))
    assert state["state"] == "Paused" and state["freshness"] == "Recent"
    assert state["retries"] == 1 and state["current_node"] == "Human approval"
    assert {"revise", "retry", "accept"} <= set(state["selected_routes"])


def test_stale_incomplete_and_completed_runs():
    data = validate_workflow_snapshot(trace())
    assert derive_run_state(data, now=datetime(2026, 9, 20, tzinfo=timezone.utc))["freshness"] == "Stale"
    done = deepcopy(data)
    done["events"].append({**done["events"][-1], "at_utc": "2026-09-19T12:15:00Z", "node_id": "complete", "event": "graph_completed", "status": "completed", "checkpointed": False})
    assert derive_run_state(done, now=datetime(2026, 9, 19, 12, 15, 1, tzinfo=timezone.utc))["state"] == "Completed"


def test_unvisited_nodes_are_not_failures():
    state = derive_run_state(validate_workflow_snapshot(trace()))
    assert "complete" not in state["visited"] and state["state"] == "Paused"


def test_private_fields_and_control_capabilities_are_rejected():
    event = deepcopy(trace()["events"][0]); event["prompt"] = "not allowed"
    with pytest.raises(SchemaError): validate_workflow_event(event)
    html = render_overview_html(load_snapshot(ROOT / "demo/public_snapshot.json"), load_config(ROOT / "config/example.yaml"))
    lowered = html.lower()
    assert "workflow & trace" in lowered and "observational only" in lowered
    assert ">approve<" not in lowered and ">resume<" not in lowered and ">retry<" not in lowered


def test_optional_langgraph_example_exports_generic_valid_files():
    manifest = json.loads((ROOT / "examples/langgraph/workflow_manifest.json").read_text())
    events = [json.loads(line) for line in (ROOT / "examples/langgraph/events.jsonl").read_text().splitlines()]
    assert validate_manifest(manifest)
    assert all(validate_workflow_event(event) for event in events)

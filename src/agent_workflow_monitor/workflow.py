from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import SchemaError, exact_keys, nonnegative_number, optional_timestamp, public_id, public_text

EVENTS = {"graph_started", "graph_completed", "node_started", "node_completed", "node_failed", "retry_scheduled", "retry_exhausted", "human_interrupt", "human_resumed", "route_selected", "subgraph_started", "subgraph_completed"}


def validate_manifest(raw: Any) -> dict[str, Any]:
    row = exact_keys(raw, {"schema_version", "workflow_id", "label", "nodes", "edges"}, "workflow manifest")
    if row["schema_version"] != 1 or not isinstance(row["nodes"], list) or not isinstance(row["edges"], list):
        raise SchemaError("invalid workflow manifest")
    public_id(row["workflow_id"], "workflow id")
    public_text(row["label"], "workflow label", limit=100)
    ids = []
    for node in row["nodes"]:
        node = exact_keys(node, {"node_id", "label", "kind", "x", "y"}, "workflow node")
        ids.append(public_id(node["node_id"], "workflow node id"))
        public_text(node["label"], "workflow node label", limit=80)
        if node["kind"] not in {"start", "task", "fanout", "fanin", "evaluation", "human_gate", "end", "subgraph"}:
            raise SchemaError("invalid workflow node kind")
        for coordinate in (node["x"], node["y"]):
            if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)) or not 0 <= coordinate <= 100:
                raise SchemaError("invalid workflow node position")
    if len(ids) != len(set(ids)):
        raise SchemaError("duplicate workflow node")
    known = set(ids)
    seen_edges = set()
    for edge in row["edges"]:
        edge = exact_keys(edge, {"from", "to", "condition"}, "workflow edge")
        if edge["from"] not in known or edge["to"] not in known:
            raise SchemaError("invalid workflow edge")
        condition = edge["condition"]
        if condition is not None:
            public_text(condition, "workflow condition", limit=60)
        signature = (edge["from"], edge["to"], condition)
        if signature in seen_edges:
            raise SchemaError("duplicate workflow edge")
        seen_edges.add(signature)
    return row


def validate_workflow_event(raw: Any) -> dict[str, Any]:
    row = exact_keys(raw, {"schema_version", "at_utc", "workflow_id", "run_id", "node_id", "event", "attempt", "status", "duration_ms", "route", "parent_node_id", "checkpointed", "human_action"}, "workflow event")
    if row["schema_version"] != 1 or row["event"] not in EVENTS:
        raise SchemaError("invalid workflow event")
    optional_timestamp(row["at_utc"], "workflow event timestamp")
    for key in ("workflow_id", "run_id"):
        public_id(row[key], key)
    for key in ("node_id", "parent_node_id"):
        if row[key] is not None:
            public_id(row[key], key)
    nonnegative_number(row["attempt"], "workflow attempt", integer=True)
    nonnegative_number(row["duration_ms"], "workflow duration", integer=True)
    if row["status"] is not None and row["status"] not in {"running", "completed", "failed", "paused", "scheduled"}:
        raise SchemaError("invalid workflow status")
    if row["route"] is not None:
        public_text(row["route"], "workflow route", limit=60)
    if type(row["checkpointed"]) is not bool or type(row["human_action"]) is not bool:
        raise SchemaError("invalid workflow flags")
    return dict(row)


def validate_workflow_snapshot(raw: Any) -> dict[str, Any]:
    row = exact_keys(raw, {"schema_version", "manifest", "events"}, "workflow snapshot")
    if row["schema_version"] != 1 or not isinstance(row["events"], list):
        raise SchemaError("invalid workflow snapshot")
    manifest = validate_manifest(row["manifest"])
    events = [validate_workflow_event(item) for item in row["events"]]
    node_ids = {node["node_id"] for node in manifest["nodes"]}
    for event in events:
        if event["workflow_id"] != manifest["workflow_id"] or (event["node_id"] is not None and event["node_id"] not in node_ids):
            raise SchemaError("workflow event reference mismatch")
    return {"schema_version": 1, "manifest": manifest, "events": events}


def derive_run_state(snapshot: dict[str, Any], *, now: datetime | None = None, freshness_seconds: int = 900) -> dict[str, Any]:
    events = sorted(snapshot["events"], key=lambda item: item["at_utc"])
    if not events:
        return {"state": "Not observed", "current_node": "None", "retries": 0, "freshness": "Unknown", "visited": [], "selected_route": None, "selected_routes": [], "timeline": []}
    last = events[-1]
    kinds = [item["event"] for item in events]
    state = "Completed" if "graph_completed" in kinds else "Failed" if "retry_exhausted" in kinds else "Paused" if kinds[-1] == "human_interrupt" else "Running"
    clock = now or datetime.now(timezone.utc)
    age = (clock - datetime.fromisoformat(last["at_utc"].replace("Z", "+00:00"))).total_seconds()
    freshness = "Recent" if 0 <= age <= freshness_seconds else "Stale"
    labels = {node["node_id"]: node["label"] for node in snapshot["manifest"]["nodes"]}
    visited = list(dict.fromkeys(item["node_id"] for item in events if item["node_id"] is not None))
    route = next((item["route"] for item in reversed(events) if item["event"] == "route_selected"), None)
    routes = list(dict.fromkeys(item["route"] for item in events if item["event"] in {"route_selected", "retry_scheduled"} and item["route"] is not None))
    timeline = [{"at": item["at_utc"], "node": labels.get(item["node_id"], "Workflow"), "event": item["event"].replace("_", " "), "attempt": item["attempt"]} for item in events]
    return {"state": state, "current_node": labels.get(last["node_id"], "Workflow"), "retries": kinds.count("retry_scheduled"), "freshness": freshness, "visited": visited, "selected_route": route, "selected_routes": routes, "timeline": timeline}

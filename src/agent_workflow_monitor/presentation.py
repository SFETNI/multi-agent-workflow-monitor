from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import PublicSnapshot, SchemaError
from .schema import role_svg
from .status_semantics import derive_status

RENDERER = Path(__file__).parent / "renderer"
SLOTS = {"H-01": "human", "A-01": "orchestrator", "A-02": "worker", "A-03": "worker", "A-04": "evaluator", "A-05": "lead_evaluator", "X-01": "consultant"}
VISUAL_STATUS = {"observed_active": "observed", "waiting": "waiting", "stale": "stale", "blocked": "blocked", "human_action": "human-action", "idle_unknown": "unknown"}


def encode_js(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def presentation_assets(snapshot: PublicSnapshot, roles: dict) -> dict:
    source = (RENDERER / "presentation.js").read_text(encoding="utf-8")
    assets = json.loads(source.removeprefix("window.PRESENTATION = ").strip().removesuffix(";"))
    assets["slot_icons"] = {p.public_id: role_svg(roles[p.role]["icon"]) for p in snapshot.participants}
    return assets


def project_snapshot(snapshot: PublicSnapshot, config: dict, *, now: datetime | None = None) -> dict:
    people = {p.public_id: p for p in snapshot.participants}
    if set(people) != set(SLOTS) or {w.public_id for w in snapshot.workstreams} != {"Workstream-01", "Workstream-02"}:
        raise SchemaError("v0.1 requires the documented seven public display slots and two workstreams")
    if any(p.role not in config["roles"] for p in people.values()):
        raise SchemaError("participant role is not configured")
    recorded = snapshot.snapshot_kind == "recorded_demo"
    clock = now or (datetime.fromisoformat(snapshot.generated_at.replace("Z", "+00:00")) if recorded else datetime.now(timezone.utc))
    agents = []
    for pid, kind in SLOTS.items():
        p = people[pid]
        status = derive_status(declared_status=p.status, status_basis=p.status_basis, last_observed_at=p.last_observed_at,
                               freshness_seconds=config["freshness_seconds"]["activity"], now=clock,
                               blocker_reported=p.status == "blocked" and p.status_basis == "recorded",
                               human_action_reported=p.status == "human_action" and p.status_basis == "recorded")
        agents.append({"id": pid, "kind": kind, "role": config["roles"][p.role]["label"],
                       "status": "external" if kind == "consultant" and status == "idle_unknown" else VISUAL_STATUS[status],
                       "working": status == "observed_active", "workstream": p.workstream_ids[0] if len(p.workstream_ids) == 1 else None,
                       "responsibilities": ["Plan", "Brainstorm", "Decision", "Review"] if kind == "human" else []})
    by_id = {a["id"]: a for a in agents}
    workstreams = [{"id": wid, "record_id": f"R-{i:02d}", "status": VISUAL_STATUS[next(w.status for w in snapshot.workstreams if w.public_id == wid)]}
                   for i, wid in enumerate(("Workstream-01", "Workstream-02"), 1)]
    events = sorted(snapshot.events, key=lambda e: e.relative_order)
    pairs = [("H-01", "A-01", "standing"), ("H-01", "X-01", "consult"), ("A-01", "A-02", "handoff"), ("A-01", "A-03", "review"), ("A-01", "A-04", "standing"), ("A-01", "A-05", "standing")]
    edges = []
    for i, (src, dst, kind) in enumerate(pairs, 1):
        matching = next((e for e in events if e.source_public_id == src and e.target_public_id == dst), None)
        active = kind in {"handoff", "review"} and matching is not None and by_id[src]["working"] and by_id[dst]["working"]
        edges.append({"id": f"E-{i:02d}", "from": src, "to": dst, "kind": kind, "active": active, "action": matching.action_label if active else None})
    activity = [{"actor_id": e.source_public_id, "workstream": e.workstream_id, "type": "decision" if e.type == "human_action" else e.type,
                 "age": e.time_display, "preview": f"to {e.target_public_id} - " + ("" if e.type == "human_action" else by_id[e.target_public_id]['role'] + " - ") + e.action_label, "detail": e.public_message} for e in events]
    approved = set(config["approved_metrics"])
    sessions = []
    for pid in ("A-01", "A-02", "A-03", "A-04", "A-05"):
        p = people[pid]; c = p.context_usage; storage = p.storage_usage
        value, percent, treatment, unit = "Not measured", None, "Not measured", "tokens"
        if "context_usage" in approved and c.used is not None:
            percent = c.percent
            value = f"{c.percent:.1f}%" if percent is not None else (f"{c.used/1000:.1f}k" if c.used >= 1000 else str(c.used))
            unit = "context" if percent is not None else c.unit
            treatment = c.basis.title() if percent is not None else "Limit ?"
            if recorded and c.illustrative:
                treatment = "Illustrative"
            if by_id[pid]["status"] == "stale":
                treatment = "Stale"
        size = "Not measured" if "storage_usage" not in approved or storage.bytes is None else f"{storage.bytes / 1073741824:.1f} GiB"
        delta = None if "storage_usage" not in approved or storage.delta_bytes is None else format_delta(storage.delta_bytes)
        sessions.append({"agent_id": pid, "value": value, "percent": percent, "treatment": treatment, "unit": unit, "storage": size, "growth": delta})
    h = snapshot.host
    host = {"load_1m": "Not measured", "load_5m": "Not measured", "load_15m": "Not measured", "memory_free": "Not measured", "disk_free": "Not measured", "cpu_count": "Not measured", "uptime": "Not measured", "gpu_memory": "Not measured"}
    host_state = "Not measured"
    if "host" in approved and h.measurement_status != "not_measured":
        age = (clock - datetime.fromisoformat(h.observed_at.replace("Z", "+00:00"))).total_seconds()
        host_state = "Stale" if age > config["freshness_seconds"]["host"] else "Measured" if age >= 0 and h.measurement_status == "measured" else "Unknown"
        if host_state != "Unknown":
            def number(v, fmt): return "Not measured" if v is None else fmt(v)
            host.update({"load_1m": number(h.load_1m, lambda v: f"{v:.2f}"), "load_5m": number(h.load_5m, lambda v: f"{v:.2f}"), "load_15m": number(h.load_15m, lambda v: f"{v:.2f}"),
                         "memory_free": number(h.memory_free_bytes, lambda v: f"{v/1e9:.1f} GB"), "disk_free": number(h.disk_free_bytes, lambda v: f"{v/1e9:.1f} GB"),
                         "cpu_count": number(h.cpu_count, str), "uptime": number(h.uptime_seconds, lambda v: f"{v//86400}d {v%86400//3600}h"),
                         "gpu_memory": "Not measured" if h.gpu_memory_used_bytes is None or h.gpu_memory_total_bytes is None else f"{h.gpu_memory_used_bytes//1048576} / {h.gpu_memory_total_bytes//1048576} MiB"})
    freshness = "Recorded 14 min ago" if recorded else "Local observation"
    if not recorded or host_state != "Measured":
        freshness += f" · Host telemetry: {host_state}"
    return {"schema_version": 1, "title": config["application"]["title"], "subtitle": config["application"]["subtitle"],
            "disclosure": "Recorded workflow - identities generalized - approved operational measurements retained" if recorded else "Local observation - read-only - freshness evaluated at render time",
            "summary": {"active_agents": sum(a["working"] for a in agents if a["id"].startswith("A-")), "monitored_agents": 5,
                        "human_actions": sum(a["status"] == "human-action" for a in agents), "blockers": sum(a["status"] == "blocked" for a in agents), "freshness": freshness},
            "agents": agents, "workstreams": workstreams, "edges": edges, "activity": activity, "sessions": sessions, "host": host}


def format_delta(delta: int | None) -> str:
    return "Not measured" if delta is None else f"{delta / 1073741824:+.1f} GiB / 3d"


def render_overview_html(snapshot: PublicSnapshot, config: dict, *, now: datetime | None = None) -> str:
    data = project_snapshot(snapshot, config, now=now)
    assets = presentation_assets(snapshot, config["roles"])
    markup = (RENDERER / "index.html").read_text(encoding="utf-8")
    scripts = {"data/public_snapshot.js": "window.PUBLIC_SNAPSHOT = " + encode_js(data) + ";", "presentation.js": "window.PRESENTATION = " + encode_js(assets) + ";"}
    for name in ("geometry.js", "app.js"):
        scripts[name] = (RENDERER / name).read_text(encoding="utf-8")
    markup = re.sub(r'<script defer src="([^"]+)"></script>', "", markup)
    markup = re.sub(r'<link rel="stylesheet" href="([^"]+)">', lambda m: '<style>' + (RENDERER / m[1]).read_text(encoding="utf-8") + '</style>', markup)
    markup = markup.replace("script-src 'self'", "script-src 'unsafe-inline'")
    return markup.replace("</body>", "".join('<script>' + value + '</script>' for value in scripts.values()) + "</body>")

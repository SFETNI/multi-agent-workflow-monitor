from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from .models import SchemaError, exact_keys, nonnegative_number, optional_timestamp, public_id

TOKEN_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_tokens",
    "cache_write_5m_tokens", "cache_write_1h_tokens", "output_tokens",
    "reasoning_tokens",
)
BILLING_MODES = {"API_EQUIVALENT", "PROVIDER_REPORTED_USAGE_VALUE", "BILLED", "SUBSCRIPTION_FEE", "UNKNOWN"}
TOTAL_SEMANTICS = {"components_exclusive", "provider_total", "unknown"}


def validate_usage_event(raw: Any) -> dict[str, Any]:
    keys = {
        "schema_version", "event_at_utc", "agent_id", "workstream_id", "provider",
        "model", "model_source", "model_confidence", *TOKEN_FIELDS, "total_tokens",
        "total_semantics", "billing_mode", "provider_reported_value",
        "provider_reported_value_kind", "pricing_context",
    }
    row = exact_keys(raw, keys, "usage event")
    if row["schema_version"] != 1:
        raise SchemaError("unsupported usage event version")
    optional_timestamp(row["event_at_utc"], "usage event timestamp")
    public_id(row["agent_id"], "usage agent id")
    if row["workstream_id"] is not None:
        public_id(row["workstream_id"], "usage workstream id")
    for key in ("provider", "model", "model_source", "model_confidence"):
        if row[key] is not None and (not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 100):
            raise SchemaError("invalid usage identity")
    for key in (*TOKEN_FIELDS, "total_tokens"):
        nonnegative_number(row[key], key, integer=True)
    if row["total_semantics"] not in TOTAL_SEMANTICS or row["billing_mode"] not in BILLING_MODES:
        raise SchemaError("invalid usage semantics")
    context = exact_keys(row["pricing_context"], {"context_tokens", "service_tier", "batch", "fast", "region"}, "pricing context")
    nonnegative_number(context["context_tokens"], "pricing context tokens", integer=True)
    for key in ("service_tier", "region"):
        if context[key] is not None and (not isinstance(context[key], str) or not context[key].strip() or len(context[key]) > 80):
            raise SchemaError("invalid pricing context")
    if type(context["batch"]) is not bool or type(context["fast"]) is not bool:
        raise SchemaError("invalid pricing mode")
    value = row["provider_reported_value"]
    if value is not None:
        nonnegative_number(value, "provider reported value")
    if row["billing_mode"] == "PROVIDER_REPORTED_USAGE_VALUE" and value is None:
        raise SchemaError("provider usage value requires a value")
    if value is None and row["provider_reported_value_kind"] is not None:
        raise SchemaError("provider usage value kind requires a value")
    return {**row, "pricing_context": dict(context)}


def observed_tokens(event: dict[str, Any]) -> int | None:
    if event["total_semantics"] == "provider_total":
        return event["total_tokens"]
    if event["total_semantics"] == "components_exclusive":
        # Reasoning is informational and included in output by this public contract.
        fields = TOKEN_FIELDS[:-1]
        known = [event[key] for key in fields if event[key] is not None]
        return sum(known) if known else None
    return None


def validate_usage_snapshot(raw: Any, known_agents: set[str]) -> dict[str, Any]:
    row = exact_keys(raw, {"schema_version", "windows", "tracked_total", "agents", "coverage", "events"}, "model usage snapshot")
    if row["schema_version"] != 1 or not isinstance(row["windows"], dict) or set(row["windows"]) != {"24h", "7d", "30d"}:
        raise SchemaError("invalid model usage snapshot")
    for key in ("24h", "7d", "30d"):
        _validate_aggregate(row["windows"][key])
    _validate_aggregate(row["tracked_total"])
    if not isinstance(row["agents"], list) or not isinstance(row["events"], list):
        raise SchemaError("invalid model usage collections")
    for item in row["agents"]:
        item = exact_keys(item, {"agent_id", "provider", "model", "tokens_7d", "tracked_tokens", "share_percent", "valuation_quality"}, "usage agent")
        if item["agent_id"] not in known_agents or item["agent_id"] in {"H-01", "X-01"}:
            raise SchemaError("unknown usage agent")
        for key in ("tokens_7d", "tracked_tokens", "share_percent"):
            nonnegative_number(item[key], key)
        if item["valuation_quality"] not in {"exact", "bounded", "estimated", "unknown"}:
            raise SchemaError("invalid valuation quality")
    coverage = exact_keys(row["coverage"], {"included_registered_sources", "excluded_unmapped_sessions", "conflicting_events_excluded", "unknown_model_events"}, "usage coverage")
    for key, value in coverage.items():
        nonnegative_number(value, key, integer=True)
    events = [validate_usage_event(item) for item in row["events"]]
    if any(item["agent_id"] not in known_agents for item in events):
        raise SchemaError("unknown usage event agent")
    return {**row, "events": events}


def _validate_aggregate(raw: Any) -> None:
    row = exact_keys(raw, {"observed_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "event_count", "value_low", "value_high", "valuation_quality"}, "usage aggregate")
    for key in ("observed_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "event_count", "value_low", "value_high"):
        nonnegative_number(row[key], key, integer=key in {"observed_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "event_count"})
    if row["valuation_quality"] not in {"exact", "bounded", "estimated", "unknown"}:
        raise SchemaError("invalid valuation quality")
    if (row["value_low"] is None) != (row["value_high"] is None):
        raise SchemaError("incomplete valuation range")
    if row["value_low"] is not None and row["value_low"] > row["value_high"]:
        raise SchemaError("invalid valuation range")


class UsageLedger:
    """Local append-only token metadata. It never stores prompts or responses."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path)
        db.execute("""CREATE TABLE IF NOT EXISTS usage_events (
            event_hash TEXT PRIMARY KEY, event_at_utc TEXT NOT NULL, agent_id TEXT NOT NULL,
            provider TEXT, model TEXT, observed_tokens INTEGER, event_json TEXT NOT NULL,
            valuation_json TEXT, inserted_at_utc TEXT NOT NULL)""")
        return db

    def ingest(self, events: Iterable[dict[str, Any]], valuations: dict[str, dict[str, Any]] | None = None) -> int:
        added = 0
        with self._connect() as db:
            for source in events:
                event = validate_usage_event(source)
                encoded = json.dumps(event, sort_keys=True, separators=(",", ":"))
                fingerprint = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
                valuation = (valuations or {}).get(fingerprint)
                cursor = db.execute(
                    "INSERT OR IGNORE INTO usage_events VALUES (?,?,?,?,?,?,?,?,?)",
                    (fingerprint, event["event_at_utc"], event["agent_id"], event["provider"], event["model"],
                     observed_tokens(event), encoded, json.dumps(valuation, sort_keys=True) if valuation else None,
                     datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
                )
                added += cursor.rowcount
        return added

    def rows(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            return [{"event": json.loads(event), "valuation": json.loads(value) if value else None}
                    for event, value in db.execute("SELECT event_json, valuation_json FROM usage_events ORDER BY event_at_utc, event_hash")]

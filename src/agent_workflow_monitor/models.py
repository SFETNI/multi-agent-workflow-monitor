from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import re
from typing import Any

STATUSES = frozenset({"observed_active", "waiting", "stale", "blocked", "human_action", "idle_unknown"})
STATUS_BASES = frozenset({"observed", "recorded", "configured", "not_measured"})
MEASUREMENT_BASES = frozenset({"measured", "configured", "unverified", "not_measured"})
EVENT_TYPES = frozenset({"handoff", "activity", "review", "human_action", "blocker"})
PROVENANCE_CLASSES = frozenset({"observed", "recorded", "configured", "demo"})


class SchemaError(ValueError):
    """Public-safe validation error with no source value in its message."""


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise SchemaError(f"invalid {label} schema")
    return value


def public_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise SchemaError(f"invalid {label}")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(char not in allowed for char in value):
        raise SchemaError(f"invalid {label}")
    return value


def public_text(value: Any, label: str, *, limit: int = 240) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SchemaError(f"invalid {label}")
    if any(ord(char) < 32 and char not in "\t\n" for char in value):
        raise SchemaError(f"invalid {label}")
    if re.search(r"(?:/(?:home|Users|private)/|[A-Za-z]:\\|https?://|[\w.-]+\.invalid\b)", value):
        raise SchemaError(f"private-looking {label}")
    return " ".join(value.split())


def optional_timestamp(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SchemaError(f"invalid {label}")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SchemaError(f"invalid {label}") from exc
    return value


def nonnegative_number(value: Any, label: str, *, integer: bool = False) -> int | float | None:
    if value is None:
        return None
    wanted = int if integer else (int, float)
    if isinstance(value, bool) or not isinstance(value, wanted) or not math.isfinite(value) or value < 0:
        raise SchemaError(f"invalid {label}")
    return value


@dataclass(frozen=True)
class ContextUsage:
    used: int | None
    limit: int | None
    unit: str
    percent: float | None
    basis: str
    illustrative: bool = False

    @classmethod
    def from_dict(cls, raw: Any) -> "ContextUsage":
        keys = {"used", "limit", "unit", "percent", "basis"}
        if isinstance(raw, dict) and "illustrative" in raw:
            keys.add("illustrative")
        row = exact_keys(raw, keys, "context usage")
        illustrative = row.get("illustrative", False)
        if type(illustrative) is not bool:
            raise SchemaError("illustrative must be boolean")
        used = nonnegative_number(row["used"], "context used", integer=True)
        limit = nonnegative_number(row["limit"], "context limit", integer=True)
        percent = nonnegative_number(row["percent"], "context percent")
        basis = row["basis"]
        if basis not in MEASUREMENT_BASES:
            raise SchemaError("invalid context basis")
        if row["unit"] not in {"tokens", "context"}:
            raise SchemaError("invalid context unit")
        if limit == 0:
            raise SchemaError("context denominator must be positive")
        if limit is None:
            if percent is not None:
                raise SchemaError("context percent requires a denominator")
        else:
            if used is None or percent is None or basis not in {"measured", "configured"}:
                raise SchemaError("context denominator is inconsistent")
            expected = 100.0 * used / limit
            if abs(float(percent) - expected) > 0.11 or percent > 100:
                raise SchemaError("context percent is inconsistent")
        if basis == "not_measured" and any(value is not None for value in (used, limit, percent)):
            raise SchemaError("unmeasured context carries a value")
        return cls(used, limit, row["unit"], None if percent is None else float(percent), basis, illustrative)


@dataclass(frozen=True)
class StorageUsage:
    bytes: int | None
    delta_bytes: int | None
    basis: str

    @classmethod
    def from_dict(cls, raw: Any) -> "StorageUsage":
        row = exact_keys(raw, {"bytes", "delta_bytes", "basis"}, "storage usage")
        size = nonnegative_number(row["bytes"], "storage bytes", integer=True)
        growth = row["delta_bytes"]
        if growth is not None and type(growth) is not int:
            raise SchemaError("storage delta must be a signed integer")
        basis = row["basis"]
        if basis not in MEASUREMENT_BASES:
            raise SchemaError("invalid storage basis")
        if basis == "not_measured" and (size is not None or growth is not None):
            raise SchemaError("unmeasured storage carries a value")
        return cls(size, growth, basis)


@dataclass(frozen=True)
class Participant:
    public_id: str
    role: str
    label: str
    workstream_ids: tuple[str, ...]
    status: str
    status_basis: str
    last_observed_at: str | None
    context_usage: ContextUsage
    storage_usage: StorageUsage

    @classmethod
    def from_dict(cls, raw: Any) -> "Participant":
        row = exact_keys(raw, {"public_id", "role", "label", "workstream_ids", "status", "status_basis", "last_observed_at", "context_usage", "storage_usage"}, "participant")
        if not isinstance(row["workstream_ids"], list):
            raise SchemaError("invalid participant workstreams")
        status, basis = row["status"], row["status_basis"]
        if status not in STATUSES or basis not in STATUS_BASES:
            raise SchemaError("invalid participant status")
        timestamp = optional_timestamp(row["last_observed_at"], "participant timestamp")
        if status in {"observed_active", "stale"} and (basis != "observed" or timestamp is None):
            raise SchemaError("observed status requires an observation timestamp and basis")
        if status == "observed_active" and basis != "observed":
            raise SchemaError("active status requires observed evidence")
        if status == "blocked" and basis != "recorded":
            raise SchemaError("blocked status requires recorded evidence")
        if status == "human_action" and basis != "recorded":
            raise SchemaError("human action requires recorded evidence")
        return cls(
            public_id(row["public_id"], "participant id"),
            public_id(row["role"], "role key"),
            public_text(row["label"], "participant label", limit=80),
            tuple(public_id(value, "workstream id") for value in row["workstream_ids"]),
            status,
            basis,
            timestamp,
            ContextUsage.from_dict(row["context_usage"]),
            StorageUsage.from_dict(row["storage_usage"]),
        )


@dataclass(frozen=True)
class Workstream:
    public_id: str
    label: str
    status: str
    record_label: str
    participants: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Any) -> "Workstream":
        row = exact_keys(raw, {"public_id", "label", "status", "record_label", "participants"}, "workstream")
        if row["status"] not in STATUSES or not isinstance(row["participants"], list):
            raise SchemaError("invalid workstream state")
        return cls(public_id(row["public_id"], "workstream id"), public_text(row["label"], "workstream label", limit=80), row["status"], public_text(row["record_label"], "record label", limit=80), tuple(public_id(item, "participant id") for item in row["participants"]))


@dataclass(frozen=True)
class ActivityEvent:
    event_id: str
    relative_order: int
    type: str
    source_public_id: str
    target_public_id: str
    workstream_id: str
    action_label: str
    public_message: str
    time_display: str
    provenance_class: str

    @classmethod
    def from_dict(cls, raw: Any) -> "ActivityEvent":
        row = exact_keys(raw, {"event_id", "relative_order", "type", "source_public_id", "target_public_id", "workstream_id", "action_label", "public_message", "time_display", "provenance_class"}, "activity event")
        if isinstance(row["relative_order"], bool) or not isinstance(row["relative_order"], int) or row["relative_order"] < 0:
            raise SchemaError("invalid event order")
        if row["type"] not in EVENT_TYPES or row["provenance_class"] not in PROVENANCE_CLASSES:
            raise SchemaError("invalid event classification")
        return cls(
            public_id(row["event_id"], "event id"), row["relative_order"], row["type"],
            public_id(row["source_public_id"], "source id"), public_id(row["target_public_id"], "target id"),
            public_id(row["workstream_id"], "workstream id"), public_text(row["action_label"], "action label", limit=40),
            public_text(row["public_message"], "public message"), public_text(row["time_display"], "time display", limit=60), row["provenance_class"],
        )


@dataclass(frozen=True)
class HostMetrics:
    load_1m: float | None
    load_5m: float | None
    load_15m: float | None
    memory_free_bytes: int | None
    disk_free_bytes: int | None
    cpu_count: int | None
    uptime_seconds: int | None
    gpu_memory_used_bytes: int | None
    gpu_memory_total_bytes: int | None
    measurement_status: str
    observed_at: str | None

    @classmethod
    def from_dict(cls, raw: Any) -> "HostMetrics":
        keys = {"load_1m", "load_5m", "load_15m", "memory_free_bytes", "disk_free_bytes", "cpu_count", "uptime_seconds", "gpu_memory_used_bytes", "gpu_memory_total_bytes", "measurement_status", "observed_at"}
        row = exact_keys(raw, keys, "host metrics")
        status = row["measurement_status"]
        if status not in {"measured", "stale", "not_measured"}:
            raise SchemaError("invalid host measurement status")
        loads = tuple(nonnegative_number(row[key], key) for key in ("load_1m", "load_5m", "load_15m"))
        integers = tuple(nonnegative_number(row[key], key, integer=True) for key in ("memory_free_bytes", "disk_free_bytes", "cpu_count", "uptime_seconds", "gpu_memory_used_bytes", "gpu_memory_total_bytes"))
        if status == "not_measured" and any(value is not None for value in loads + integers):
            raise SchemaError("unmeasured host carries a value")
        timestamp = optional_timestamp(row["observed_at"], "host timestamp")
        if status in {"measured", "stale"} and timestamp is None:
            raise SchemaError("host measurement requires a timestamp")
        if status == "not_measured" and timestamp is not None:
            raise SchemaError("unmeasured host carries a timestamp")
        if integers[-2] is not None and integers[-1] is not None and integers[-2] > integers[-1]:
            raise SchemaError("host memory usage exceeds total")
        return cls(*loads, *integers, status, timestamp)


@dataclass(frozen=True)
class PublicSnapshot:
    schema_version: int
    snapshot_kind: str
    generated_at: str
    participants: tuple[Participant, ...]
    workstreams: tuple[Workstream, ...]
    events: tuple[ActivityEvent, ...]
    host: HostMetrics

    @classmethod
    def from_dict(cls, raw: Any) -> "PublicSnapshot":
        row = exact_keys(raw, {"schema_version", "snapshot_kind", "generated_at", "participants", "workstreams", "events", "host"}, "snapshot")
        if type(row["schema_version"]) is not int or row["schema_version"] != 1 or row["snapshot_kind"] not in {"recorded_demo", "local_observation"}:
            raise SchemaError("unsupported snapshot version or kind")
        if not all(isinstance(row[key], list) for key in ("participants", "workstreams", "events")):
            raise SchemaError("invalid snapshot collections")
        participants = tuple(Participant.from_dict(item) for item in row["participants"])
        if row["snapshot_kind"] != "recorded_demo" and any(p.context_usage.illustrative for p in participants):
            raise SchemaError("illustrative context is restricted to demo snapshots")
        workstreams = tuple(Workstream.from_dict(item) for item in row["workstreams"])
        events = tuple(ActivityEvent.from_dict(item) for item in row["events"])
        participant_ids = [item.public_id for item in participants]
        workstream_ids = [item.public_id for item in workstreams]
        if len(participant_ids) != len(set(participant_ids)) or len(workstream_ids) != len(set(workstream_ids)):
            raise SchemaError("duplicate public id")
        known_people, known_workstreams = set(participant_ids), set(workstream_ids)
        for participant in participants:
            if not set(participant.workstream_ids) <= known_workstreams:
                raise SchemaError("unknown participant workstream")
        for workstream in workstreams:
            if not set(workstream.participants) <= known_people:
                raise SchemaError("unknown workstream participant")
        for event in events:
            if event.source_public_id not in known_people or event.target_public_id not in known_people or event.workstream_id not in known_workstreams:
                raise SchemaError("unknown event reference")
        timestamp = optional_timestamp(row["generated_at"], "snapshot timestamp")
        if timestamp is None:
            raise SchemaError("snapshot requires a timestamp")
        return cls(1, row["snapshot_kind"], timestamp, participants, workstreams, events, HostMetrics.from_dict(row["host"]))

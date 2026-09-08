from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent_workflow_monitor.adapters.base import fingerprint
from agent_workflow_monitor.adapters.jsonl_activity import JsonlActivityAdapter
from agent_workflow_monitor.adapters.process_metrics import ProcessMetricsAdapter, configured_process_presence
import agent_workflow_monitor.adapters.process_metrics as process_metrics
from agent_workflow_monitor.adapters.snapshot import SnapshotAdapter
from agent_workflow_monitor.models import SchemaError

ROOT = Path(__file__).resolve().parents[1]


def test_snapshot_adapter_is_read_only(tmp_path):
    source = tmp_path / "snapshot.json"
    source.write_bytes((ROOT / "demo" / "public_snapshot.json").read_bytes())
    before = fingerprint(source); result = SnapshotAdapter(source).read(); after = fingerprint(source)
    assert before == after and result.schema_version == 1


def test_jsonl_adapter_is_read_only(tmp_path):
    source = tmp_path / "activity.jsonl"
    source.write_bytes((ROOT / "tests" / "fixtures" / "activity.jsonl").read_bytes())
    before = fingerprint(source); result = JsonlActivityAdapter(source).read(); after = fingerprint(source)
    assert before == after and [item.event_id for item in result] == ["E-101", "E-102"]


def test_jsonl_unknown_field_is_rejected(tmp_path):
    source = tmp_path / "activity.jsonl"
    row = json.loads((ROOT / "tests" / "fixtures" / "activity.jsonl").read_text().splitlines()[0]); row["source_payload"] = {"hidden": True}
    source.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        JsonlActivityAdapter(source).read()


def test_jsonl_malformed_input_is_safe(tmp_path):
    source = tmp_path / "activity.jsonl"; source.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="unavailable or malformed"):
        JsonlActivityAdapter(source).read()


def test_process_presence_reads_only_explicit_pids():
    assert configured_process_presence({"A-01": os.getpid()}) == {"A-01": True}


def test_process_presence_rejects_boolean_pid():
    with pytest.raises(SchemaError):
        configured_process_presence({"A-01": True})


def test_host_adapter_omits_identity_fields(tmp_path):
    host = ProcessMetricsAdapter(tmp_path).read()
    assert not hasattr(host, "hostname") and not hasattr(host, "command") and host.measurement_status == "measured"


def test_host_adapter_uses_psutil_fallback_without_os_getloadavg(tmp_path, monkeypatch):
    hits = {"count": 0}

    def _fake_getloadavg():
        hits["count"] += 1
        return (1.0, 1.5, 2.0)

    monkeypatch.delattr(process_metrics.os, "getloadavg", raising=False)
    monkeypatch.setattr(process_metrics.psutil, "getloadavg", _fake_getloadavg)
    host = ProcessMetricsAdapter(tmp_path).read()

    assert hits["count"] == 1
    assert host.load_1m == 1.0 and host.load_5m == 1.5 and host.load_15m == 2.0
    assert not hasattr(host, "hostname") and not hasattr(host, "command") and host.measurement_status == "measured"

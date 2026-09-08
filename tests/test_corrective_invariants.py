from __future__ import annotations

import json
import tomllib
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

from agent_workflow_monitor.models import ContextUsage, HostMetrics, Participant, SchemaError, StorageUsage
from agent_workflow_monitor.presentation import format_delta, render_overview_html
from agent_workflow_monitor.schema import load_config, parse_snapshot, source_path, validate_config
from agent_workflow_monitor.privacy import display_path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "config/public_snapshot.schema.json").read_text())


def raw(): return json.loads((ROOT / "demo/public_snapshot.json").read_text())


@pytest.mark.parametrize("delta", [-858993459, 0, 1288490189, None])
def test_signed_storage_delta_matches_machine_schema(delta):
    data = raw(); data["participants"][2]["storage_usage"]["delta_bytes"] = delta
    assert parse_snapshot(data).participants[2].storage_usage.delta_bytes == delta
    jsonschema.validate(data, SCHEMA)


@pytest.mark.parametrize("delta", [True, 1.5, "-12"])
def test_storage_rejects_non_integer_delta(delta):
    with pytest.raises(SchemaError): StorageUsage.from_dict({"bytes": 1, "delta_bytes": delta, "basis": "measured"})


@pytest.mark.parametrize("value,expected", [(1288490189, "+1.2 GiB / 3d"), (-858993459, "-0.8 GiB / 3d"), (None, "Not measured")])
def test_signed_delta_display(value, expected):
    assert format_delta(value) == expected


@pytest.mark.parametrize("status,basis,timestamp", [("observed_active", "observed", None), ("observed_active", "recorded", "2026-01-15T12:00:00Z"), ("stale", "recorded", "2026-01-15T12:00:00Z"), ("stale", "observed", None)])
def test_invalid_observation_combinations_rejected_by_both_schemas(status, basis, timestamp):
    data = raw(); p = data["participants"][1]
    p.update(status=status, status_basis=basis, last_observed_at=timestamp)
    with pytest.raises(SchemaError): parse_snapshot(data)
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(data, SCHEMA)


@pytest.mark.parametrize("status", ["measured", "stale"])
def test_host_measurement_requires_timestamp(status):
    data = raw(); data["host"].update(measurement_status=status, observed_at=None)
    with pytest.raises(SchemaError): parse_snapshot(data)
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(data, SCHEMA)


def test_unmeasured_host_rejects_numbers():
    data = raw(); data["host"].update(measurement_status="not_measured", observed_at=None)
    with pytest.raises(SchemaError): parse_snapshot(data)
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(data, SCHEMA)


@pytest.mark.parametrize("basis,limit,percent", [("unverified", 100, 10), ("measured", None, 10), ("configured", 0, None), ("not_measured", None, None)])
def test_context_invalid_basis_or_denominator_rejected(basis, limit, percent):
    data = raw(); data["participants"][1]["context_usage"] = {"used": 10, "limit": limit, "percent": percent, "unit": "tokens", "basis": basis}
    with pytest.raises(SchemaError): parse_snapshot(data)
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(data, SCHEMA)


@pytest.mark.parametrize("adapter", ["jsonl_activity", "process_metrics"])
def test_fragment_adapters_not_selectable_app_sources(adapter):
    config = load_config(ROOT / "config/example.yaml"); config["source"]["adapter"] = adapter
    with pytest.raises(SchemaError): validate_config(config)
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(config, json.loads((ROOT / "config/schema.json").read_text()))


@pytest.mark.parametrize("icon", ["missing.svg", "unsafe.js", "folder/icon.svg"])
def test_invalid_or_missing_icons_rejected(icon):
    config = load_config(ROOT / "config/example.yaml"); config["roles"]["worker"]["icon"] = icon
    with pytest.raises(SchemaError): validate_config(config)


def test_config_and_snapshot_validate_against_machine_schemas():
    jsonschema.validate(raw(), SCHEMA, format_checker=jsonschema.FormatChecker())
    jsonschema.validate(load_config(ROOT / "config/example.yaml"), json.loads((ROOT / "config/schema.json").read_text()))


def test_relative_sources_resolve_beside_config_not_cwd(tmp_path, monkeypatch):
    config = load_config(ROOT / "config/example.yaml"); monkeypatch.chdir(tmp_path)
    assert source_path(config, ROOT / "config/example.yaml") == ROOT / "config/public_snapshot.json"


def test_streamlit_exact_privacy_settings():
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
    assert config["client"]["showErrorDetails"] == "none"
    assert config["client"]["showErrorLinks"] is False
    assert config["client"]["toolbarMode"] == "viewer"
    assert config["server"]["address"] == "127.0.0.1"
    assert config["server"]["enableCORS"] and config["server"]["enableXsrfProtection"]
    assert config["browser"]["gatherUsageStats"] is False


def test_text_sentinel_paths_rejected_in_allowed_fields():
    data = raw(); data["events"][0]["public_message"] = "/" + "home/private-user/secret-project/"
    with pytest.raises(SchemaError): parse_snapshot(data)


def test_html_script_breakout_is_escaped():
    data = raw(); data["events"][0]["public_message"] = '</script><script>window.injected=true</script>'
    html = render_overview_html(parse_snapshot(data), load_config(ROOT / "config/example.yaml"))
    assert data["events"][0]["public_message"] not in html
    assert "\\u003c/script\\u003e" in html

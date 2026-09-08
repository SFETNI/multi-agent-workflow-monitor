from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from agent_workflow_monitor.models import ContextUsage, SchemaError
from agent_workflow_monitor.schema import load_config, load_snapshot, parse_snapshot, validate_config

ROOT = Path(__file__).resolve().parents[1]


def raw_snapshot():
    return json.loads((ROOT / "demo" / "public_snapshot.json").read_text(encoding="utf-8"))


def test_valid_public_snapshot_is_accepted():
    snapshot = load_snapshot(ROOT / "demo" / "public_snapshot.json")
    assert snapshot.schema_version == 1 and len(snapshot.participants) == 7


@pytest.mark.parametrize("section", ["root", "participant", "workstream", "event", "host"])
def test_unknown_normalized_fields_are_rejected(section):
    raw = raw_snapshot()
    target = {"root": raw, "participant": raw["participants"][0], "workstream": raw["workstreams"][0], "event": raw["events"][0], "host": raw["host"]}[section]
    target["unexpected"] = "discard me"
    with pytest.raises(SchemaError):
        parse_snapshot(raw)


def test_malformed_collection_is_a_safe_schema_error():
    raw = raw_snapshot(); raw["participants"] = "not-a-list"
    with pytest.raises(SchemaError, match="invalid snapshot collections"):
        parse_snapshot(raw)


def test_context_percent_requires_denominator():
    raw = {"used": 100, "limit": None, "unit": "tokens", "percent": 10.0, "basis": "measured"}
    with pytest.raises(SchemaError, match="requires a denominator"):
        ContextUsage.from_dict(raw)


def test_context_percent_must_match_values():
    raw = {"used": 50, "limit": 100, "unit": "tokens", "percent": 90.0, "basis": "configured"}
    with pytest.raises(SchemaError, match="inconsistent"):
        ContextUsage.from_dict(raw)


def test_missing_measurements_remain_missing():
    snapshot = parse_snapshot(raw_snapshot())
    owner = snapshot.participants[0]
    assert owner.context_usage.used is None and owner.context_usage.percent is None
    assert owner.storage_usage.bytes is None


def test_cross_record_reference_must_resolve():
    raw = raw_snapshot(); raw["events"][0]["target_public_id"] = "A-99"
    with pytest.raises(SchemaError, match="unknown event reference"):
        parse_snapshot(raw)


def test_config_is_valid_and_role_registry_is_extensible():
    config = load_config(ROOT / "config" / "example.yaml")
    custom = deepcopy(config)
    custom["roles"]["domain_specialist"] = {"label": "Domain Specialist", "icon": "worker.svg"}
    assert "domain_specialist" in validate_config(custom)["roles"]


def test_config_unknown_field_is_rejected():
    config = yaml.safe_load((ROOT / "config" / "example.yaml").read_text(encoding="utf-8")); config["raw"] = {}
    with pytest.raises(SchemaError):
        validate_config(config)


def test_config_requires_loopback():
    config = yaml.safe_load((ROOT / "config" / "example.yaml").read_text(encoding="utf-8")); config["application"]["bind_address"] = "0" + ".0.0.0"
    with pytest.raises(SchemaError, match="loopback"):
        validate_config(config)

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_workflow_monitor.models import SchemaError
from agent_workflow_monitor.schema import parse_snapshot
from agent_workflow_monitor.status_semantics import derive_status, should_animate
from agent_workflow_monitor.usage import context_display

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 1, 15, 12, 15, tzinfo=timezone.utc)


def participants():
    raw = json.loads((ROOT / "demo" / "public_snapshot.json").read_text(encoding="utf-8"))
    return {item.public_id: item for item in parse_snapshot(raw).participants}


def test_responsibility_does_not_imply_execution():
    assert derive_status(declared_status="waiting", status_basis="recorded", last_observed_at=None, freshness_seconds=60, responsibility=True, now=NOW) == "waiting"


def test_fresh_observed_signal_is_active():
    assert derive_status(declared_status="observed_active", status_basis="observed", last_observed_at="2026-01-15T12:14:30Z", freshness_seconds=60, now=NOW) == "observed_active"


def test_old_observed_signal_is_stale():
    assert derive_status(declared_status="observed_active", status_basis="observed", last_observed_at="2026-01-15T12:10:00Z", freshness_seconds=60, now=NOW) == "stale"


def test_active_without_observed_basis_becomes_unknown():
    assert derive_status(declared_status="observed_active", status_basis="recorded", last_observed_at="2026-01-15T12:14:30Z", freshness_seconds=60, now=NOW) == "idle_unknown"


def test_declared_blocked_without_evidence_becomes_unknown():
    assert derive_status(declared_status="blocked", status_basis="recorded", last_observed_at=None, freshness_seconds=60, now=NOW) == "idle_unknown"


def test_explicit_blocker_wins():
    assert derive_status(declared_status="waiting", status_basis="recorded", last_observed_at=None, freshness_seconds=60, blocker_reported=True, now=NOW) == "blocked"


def test_human_action_requires_explicit_evidence():
    assert derive_status(declared_status="human_action", status_basis="recorded", last_observed_at=None, freshness_seconds=60, now=NOW) == "idle_unknown"
    assert derive_status(declared_status="waiting", status_basis="recorded", last_observed_at=None, freshness_seconds=60, human_action_reported=True, now=NOW) == "human_action"


def test_evidence_flags_reject_truthy_strings():
    with pytest.raises(SchemaError):
        derive_status(declared_status="waiting", status_basis="recorded", last_observed_at=None, freshness_seconds=60, blocker_reported="false", now=NOW)


def test_animation_only_for_fresh_observed_activity():
    people = participants()
    assert should_animate(people["A-01"], freshness_seconds=60, now=NOW)
    assert not should_animate(people["A-03"], freshness_seconds=60, now=NOW)
    assert not should_animate(people["H-01"], freshness_seconds=60, now=NOW)


def test_context_basis_display_is_explicit():
    people = participants()
    assert context_display(people["A-02"].context_usage)["basis"] == "Measured"
    assert context_display(people["A-04"].context_usage)["basis"] == "Configured"
    assert context_display(people["A-03"].context_usage)["percent"] is None

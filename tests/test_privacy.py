from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflow_monitor.models import SchemaError
from agent_workflow_monitor.presentation import render_overview_html
from agent_workflow_monitor.privacy import display_path, reject_forbidden_fields, safe_error_message
from agent_workflow_monitor.schema import load_config, parse_snapshot
from audit_public_candidate import audit

ROOT = Path(__file__).resolve().parents[1]


def private_path_sentinel() -> str:
    return "/" + "home" + "/private-user/secret-project/"


def session_sentinel() -> str:
    return "SESSION" + "-SECRET-SENTINEL"


@pytest.mark.parametrize("mode,expected", [("hidden", "Hidden"), ("basename", "source.json"), ("configured-label", "Approved source")])
def test_path_display_never_returns_absolute_path(mode, expected):
    assert display_path(private_path_sentinel() + "source.json", mode, "Approved source") == expected


def test_invalid_path_mode_rejected():
    with pytest.raises(SchemaError):
        display_path("source.json", "absolute")


@pytest.mark.parametrize("field", ["raw", "metadata", "source_payload", "original_event"])
def test_raw_catch_all_fields_are_rejected(field):
    with pytest.raises(SchemaError):
        reject_forbidden_fields({"safe": [{field: session_sentinel()}]})


def test_fictional_private_path_cannot_enter_normalized_record():
    raw = json.loads((ROOT / "demo" / "public_snapshot.json").read_text(encoding="utf-8"))
    raw["participants"][0]["source_payload"] = {"path": private_path_sentinel()}
    with pytest.raises(SchemaError):
        parse_snapshot(raw)


def test_safe_error_never_contains_filename_or_value():
    message = safe_error_message(RuntimeError(private_path_sentinel() + session_sentinel()))
    assert private_path_sentinel() not in message and session_sentinel() not in message


def test_rendered_html_contains_no_source_path_or_sentinel():
    snapshot = parse_snapshot(json.loads((ROOT / "demo" / "public_snapshot.json").read_text(encoding="utf-8")))
    html = render_overview_html(snapshot, load_config(ROOT / "config" / "example.yaml"))
    assert private_path_sentinel() not in html and session_sentinel() not in html
    assert "data-node" in html and "source_payload" not in html


def test_external_denylist_catches_contaminated_candidate(tmp_path):
    candidate = tmp_path / "candidate"; candidate.mkdir()
    (candidate / "README.md").write_text("PRIVATE_PROJECT_SENTINEL", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"; allowlist.write_text("README.md\n", encoding="utf-8")
    denylist = tmp_path / "denylist.txt"; denylist.write_text("PRIVATE_PROJECT_SENTINEL\n", encoding="utf-8")
    result = audit(candidate, allowlist, denylist_path=denylist)
    assert result["status"] == "FAIL" and result["categories"] == {"external_denylist": 1}

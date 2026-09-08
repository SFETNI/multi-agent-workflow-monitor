from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

import streamlit.testing.v1 as streamlit_testing
AppTest = streamlit_testing.AppTest
ROOT = Path(__file__).resolve().parents[1]


def test_local_app_renders_without_exception(monkeypatch):
    monkeypatch.setenv("AWM_CONFIG", str(ROOT / "config" / "example.yaml"))
    app = AppTest.from_file(str(ROOT / "src" / "agent_workflow_monitor" / "app.py")).run(timeout=15)
    assert not app.exception
    assert "Hidden" in app.info[0].value
    assert not app.error
    assert "av-beam-rotor" in app.get("iframe")[0].proto.srcdoc


def test_local_app_failure_is_generic_and_hides_source(monkeypatch, tmp_path):
    config = yaml.safe_load((ROOT / "config" / "example.yaml").read_text(encoding="utf-8"))
    marker = "/" + "home" + "/private-user/secret-project/missing.json"
    config["source"]["path"] = marker
    path = tmp_path / "config.yaml"; path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setenv("AWM_CONFIG", str(path))
    app = AppTest.from_file(str(ROOT / "src" / "agent_workflow_monitor" / "app.py")).run(timeout=15)
    assert not app.exception
    assert app.error and marker not in app.error[0].value
    assert app.error[0].value == "Data unavailable. The configured source did not match the approved schema."

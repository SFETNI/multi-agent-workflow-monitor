from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from agent_workflow_monitor.privacy import display_path, safe_error_message
from agent_workflow_monitor.presentation import render_overview_html
from agent_workflow_monitor.schema import load_config, source_path
from agent_workflow_monitor.adapters.snapshot import SnapshotAdapter


def _configured_path() -> Path:
    value = os.environ.get("AWM_CONFIG", "config/example.yaml")
    return Path(value)


@st.fragment(run_every=5)
def monitor(config_path: Path | None = None) -> None:
    try:
        path = config_path or _configured_path()
        config = load_config(path)
        source = source_path(config, path)
        snapshot = SnapshotAdapter(source).read()
        source_label = display_path(source, config["application"]["path_display"], config["source"].get("label"))
        st.info(f"Configured source: {source_label} · {snapshot.snapshot_kind.replace('_', ' ')}")
        st.iframe(render_overview_html(snapshot, config), height=1600)
    except Exception as exc:  # The normal UI never exposes a traceback or source value.
        st.error(safe_error_message(exc))


def main() -> None:
    render()


def render(config_path: Path | None = None) -> None:
    st.set_page_config(page_title="Agent Workflow Monitor", layout="wide")
    monitor(config_path)


if __name__ == "__main__":
    main()

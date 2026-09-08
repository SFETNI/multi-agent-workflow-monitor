#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_workflow_monitor.schema import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local read-only dashboard.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "example.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    env = os.environ.copy()
    env["AWM_CONFIG"] = str(args.config.resolve())
    command = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "src" / "agent_workflow_monitor" / "app.py"),
        "--server.address", config["application"]["bind_address"], "--server.headless", "true", "--browser.gatherUsageStats", "false",
        "--client.showErrorDetails", "none", "--client.showErrorLinks", "false",
        "--server.enableCORS", "true", "--server.enableXsrfProtection", "true",
    ]
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

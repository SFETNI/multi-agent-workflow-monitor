#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_workflow_monitor.models import SchemaError  # noqa: E402
from agent_workflow_monitor.schema import load_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agent Workflow Monitor configuration.")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        load_config(args.config)
    except SchemaError as exc:
        print(f"INVALID: {exc}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

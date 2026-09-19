#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_workflow_monitor.workflow import derive_run_state, validate_workflow_snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=ROOT / "demo/workflow/workflow_trace.json")
    args = parser.parse_args()
    trace = validate_workflow_snapshot(json.loads(args.path.read_text(encoding="utf-8")))
    state = derive_run_state(trace)
    print(f"PASS nodes={len(trace['manifest']['nodes'])} events={len(trace['events'])} state={state['state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

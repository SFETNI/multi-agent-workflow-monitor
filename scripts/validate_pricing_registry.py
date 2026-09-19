#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_workflow_monitor.pricing import load_registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, nargs="?", default=ROOT / "config/pricing/model_pricing_registry.json")
    args = parser.parse_args()
    registry = load_registry(args.path)
    print(f"PASS providers={len(registry['providers'])} reviewed_entries={len(registry['entries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
from pathlib import Path


def digest(path: Path) -> tuple[int, int, str]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("module")
    parser.add_argument("class_name")
    args = parser.parse_args()
    before = digest(args.source)
    adapter_type = getattr(importlib.import_module(args.module), args.class_name)
    adapter_type(args.source).read()
    after = digest(args.source)
    if before != after:
        print("FAIL: source changed")
        return 1
    print("PASS: source unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

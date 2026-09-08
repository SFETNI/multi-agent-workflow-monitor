#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from audit_public_candidate import audit, load_allowlist, sha256
from stage_release import stage

FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def build(candidate: Path, allowlist_path: Path, output: Path, manifest_path: Path) -> dict:
    candidate = candidate.resolve()
    files = load_allowlist(allowlist_path)
    if output.resolve().is_relative_to(candidate) or manifest_path.resolve().is_relative_to(candidate):
        raise ValueError("release outputs must be outside the candidate")
    with tempfile.TemporaryDirectory(prefix="awm-release-") as directory:
        fresh = Path(directory) / "agent-workflow-monitor"
        stage(candidate, files, fresh)
        result = audit(fresh, allowlist_path)
        if result["status"] != "PASS":
            raise ValueError("strict staged release audit failed: " + json.dumps(result["categories"]))
        members = []
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in files:
                source = fresh / relative
                member = f"agent-workflow-monitor/{relative}"
                info = zipfile.ZipInfo(member, FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if relative.startswith("scripts/") or "/scripts/" in relative else 0o100644) << 16
                payload = source.read_bytes()
                archive.writestr(info, payload)
                members.append({"path": member, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    result = {
        "schema_version": 1,
        "archive": output.name,
        "archive_sha256": sha256(output),
        "member_count": len(members),
        "members": members,
    }
    manifest_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic candidate ZIP from an explicit allowlist.")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.candidate, args.allowlist, args.output, args.manifest)
    print(f"{result['archive_sha256']}  {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

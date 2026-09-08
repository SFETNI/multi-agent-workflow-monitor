#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_public_candidate.py"), str(ROOT), "--allowlist", str(ROOT / "release_allowlist.txt"), "--staged", *sys.argv[1:]], cwd=ROOT, check=False).returncode)

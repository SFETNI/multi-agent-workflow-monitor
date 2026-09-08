#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_config.py"), *sys.argv[1:]], cwd=ROOT, check=False).returncode)

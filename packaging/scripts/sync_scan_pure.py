#!/usr/bin/env python3
"""
Sync packaging/aos_health_mcp/_scan_pure.py from canonical core/ahr_scan_pure.py.

Usage:
  python3 packaging/scripts/sync_scan_pure.py        # copy + verify
  python3 packaging/scripts/sync_scan_pure.py --check-only  # verify only, exit 1 on drift
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL = _TOOL_ROOT / "core" / "ahr_scan_pure.py"
_DIST_COPY = _TOOL_ROOT / "packaging" / "aos_health_mcp" / "_scan_pure.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_body_hash(path: Path) -> str:
    """Module docstring を除いた本体のハッシュ（正本と配布コピーの docstring 差を許容）。"""
    text = path.read_text(encoding="utf-8")
    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end != -1:
            text = text[end + 3 :].lstrip("\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync _scan_pure.py from canonical core module")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Verify hash match without copying; exit 1 on drift",
    )
    args = parser.parse_args()

    if not _CANONICAL.is_file():
        print(f"FATAL: canonical missing: {_CANONICAL}", file=sys.stderr)
        return 2
    if not _DIST_COPY.parent.is_dir():
        print(f"FATAL: packaging dir missing: {_DIST_COPY.parent}", file=sys.stderr)
        return 2

    if not args.check_only:
        shutil.copy2(_CANONICAL, _DIST_COPY)
        print(f"OK: copied {_CANONICAL.name} -> {_DIST_COPY}")

    if not _DIST_COPY.is_file():
        print(f"FATAL: distribution copy missing: {_DIST_COPY}", file=sys.stderr)
        return 2

    c_hash = _code_body_hash(_CANONICAL)
    d_hash = _code_body_hash(_DIST_COPY)
    if c_hash != d_hash:
        print(
            f"FAIL: code-body hash mismatch canonical={c_hash[:12]}… dist={d_hash[:12]}…",
            file=sys.stderr,
        )
        return 1

    print(f"OK: code-body hash match ({c_hash[:16]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

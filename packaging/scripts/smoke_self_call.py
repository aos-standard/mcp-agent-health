#!/usr/bin/env python3
"""
G1 self-connectivity smoke — simulates tools/call and writes JSONL evidence.

Usage:
  python3 packaging/scripts/smoke_self_call.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PACKAGING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PACKAGING))

from aos_health_mcp.call_logger import log_tool_call  # noqa: E402
from aos_health_mcp.scanner import scan_agent  # noqa: E402


def main() -> int:
    target = Path.cwd()
    report = scan_agent("1066", target_dir=target, mock=True)
    payload = {
        "status": "success",
        "aos_score": report.aos_score,
        "tool_id": report.tool_id,
        "certified": report.aos_score >= 80,
        "sections": report.sections,
    }
    log_path = log_tool_call(
        "aos_agent_health_scan",
        {"tool_id": "1066", "target_dir": str(target), "mock": True},
        payload,
        caller="smoke_self_call",
    )
    print(f"OK: JSONL appended -> {log_path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

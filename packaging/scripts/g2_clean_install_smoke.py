#!/usr/bin/env python3
"""
G2 clean-install smoke — mock なし実スキャン + JSONL 物理ログ。

クリーン venv 前提（帝國 shared / 02_Production を PYTHONPATH に含めない）。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_TOOL_ROOT = Path(__file__).resolve().parents[2]
_PACKAGING = _TOOL_ROOT / "packaging"
sys.path.insert(0, str(_PACKAGING))

from aos_health_mcp.call_logger import log_tool_call  # noqa: E402
from aos_health_mcp.scanner import scan_agent  # noqa: E402


def main() -> int:
    target_dir = Path(
        os.environ.get("AOS_G2_TARGET_DIR", str(_TOOL_ROOT))
    ).resolve()

    report = scan_agent("1066", target_dir=target_dir, mock=False)
    payload = {
        "status": "success",
        "aos_score": report.aos_score,
        "certified": report.aos_score >= 80,
        "tool_id": report.tool_id,
        "target_path": report.target_path,
        "sections": report.sections,
        "mock": False,
    }

    if report.target_path is None:
        print("FAIL: target_path is None — agent not found under target_dir", file=sys.stderr)
        return 1
    if report.aos_score <= 0:
        print("FAIL: aos_score is 0 — no meaningful output", file=sys.stderr)
        return 1

    log_path = log_tool_call(
        "aos_agent_health_scan",
        {"tool_id": "1066", "target_dir": str(target_dir), "mock": False},
        payload,
        caller="g2_clean_install",
    )
    print(f"OK: G2 mock=false scan -> {log_path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

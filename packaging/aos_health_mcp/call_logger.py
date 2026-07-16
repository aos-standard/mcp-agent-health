"""
JSONL call logger for G1 self-connectivity evidence.

Each tools/call appends one line. Path: AOS_HEALTH_MCP_LOG or ~/.aos_health_mcp/calls.jsonl
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _log_path() -> Path:
    env = os.environ.get("AOS_HEALTH_MCP_LOG", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".aos_health_mcp" / "calls.jsonl"


def log_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    *,
    caller: str = "self",
) -> Path:
    """Append one JSONL line and return the log file path."""
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "caller": caller,
        "arguments": arguments,
        "status": result.get("status", "unknown"),
        "aos_score": result.get("aos_score"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path

#!/usr/bin/env python3
"""
AOS Agent Health Reporter — FastMCP stdio server (external distribution).

Detect agents that silently fail in production: validate AOS-compliant agent
health and report pass/fail readiness scores for any target directory.

No shared.Core / 02_Production dependency. Use target_dir to scan local agents.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from aos_health_mcp.call_logger import log_tool_call
from aos_health_mcp.scanner import audit_agents, format_json_payload, scan_agent

mcp = FastMCP(
    "aos_agent_health_reporter",
    instructions=(
        "Validate AOS-compliant agent health before deployment. "
        "Agents that look fine locally often silently fail in production — "
        "this tool scores manifest, runtime, immune loop, and physical evidence."
    ),
    json_response=True,
)


def _resolve_target_dir(target_dir: str | None) -> Path:
    raw = (target_dir or os.environ.get("AOS_HEALTH_TARGET_DIR") or ".").strip()
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"target_dir is not a directory: {path}")
    return path


@mcp.tool()
def aos_agent_health_scan(
    tool_id: str,
    target_dir: str | None = None,
    mock: bool = False,
) -> dict[str, Any]:
    """
    Scan a single AOS agent by tool_id under target_dir and return health score.

    Args:
        tool_id: Four-digit agent id (e.g. "1066").
        target_dir: Root directory to search (default: cwd or AOS_HEALTH_TARGET_DIR).
        mock: Deterministic mock output for CI (no filesystem reads).
    """
    root = _resolve_target_dir(target_dir)
    report = scan_agent(tool_id, target_dir=root, mock=mock)
    payload: dict[str, Any] = {
        "status": "success",
        "aos_score": report.aos_score,
        "certified": report.aos_score >= 80,
        "tool_id": report.tool_id,
        "target_dir": str(root),
        "target_path": report.target_path,
        "sections": report.sections,
        "precedent_meta": report.precedent_meta,
        "scanned_at": report.scanned_at,
    }
    log_tool_call(
        "aos_agent_health_scan",
        {"tool_id": tool_id, "target_dir": str(root), "mock": mock},
        payload,
    )
    return payload


@mcp.tool()
def aos_agent_health_audit(
    target_dir: str | None = None,
    mock: bool = False,
) -> dict[str, Any]:
    """
    Audit all agents under target_dir and return aggregate health report.

    Args:
        target_dir: Root directory to search (default: cwd or AOS_HEALTH_TARGET_DIR).
        mock: Deterministic mock output for CI.
    """
    root = _resolve_target_dir(target_dir)
    reports = audit_agents(target_dir=root, mock=mock)
    avg = round(sum(r.aos_score for r in reports) / len(reports), 1) if reports else 0.0
    payload: dict[str, Any] = {
        "status": "success",
        "total_tools": len(reports),
        "avg_score": avg,
        "target_dir": str(root),
        "reports": [r.to_dict() for r in reports],
    }
    log_tool_call(
        "aos_agent_health_audit",
        {"target_dir": str(root), "mock": mock},
        {"status": "success", "aos_score": avg, **payload},
    )
    return payload


@mcp.tool()
def aos_agent_health_self_test(mock: bool = True) -> dict[str, Any]:
    """
    Self-connectivity check — returns sample scan JSON for MCP wiring verification.
    """
    root = _resolve_target_dir(None)
    report = scan_agent("1066", target_dir=root, mock=mock)
    raw = format_json_payload(report)
    payload: dict[str, Any] = {
        "status": "success",
        "message": "self_test_ok",
        "aos_score": report.aos_score,
        "sample_json": raw,
    }
    log_tool_call("aos_agent_health_self_test", {"mock": mock}, payload)
    return payload


def main() -> None:
    transport = os.environ.get("AOS_HEALTH_MCP_TRANSPORT", "stdio").strip().lower()
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()

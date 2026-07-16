"""
External self-contained scanner.

Monorepo dev: imports core/ahr_scan_pure via sys.path.
Pip distribution: uses bundled aos_health_mcp/_scan_pure.py.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _load_pure_module():
    here = Path(__file__).resolve()
    monorepo_core = here.parents[2]
    if (monorepo_core / "core" / "ahr_scan_pure.py").is_file():
        core_parent = str(monorepo_core)
        if core_parent not in sys.path:
            sys.path.insert(0, core_parent)
        from core.ahr_scan_pure import (  # noqa: WPS433
            AHRReport,
            audit_agents,
            discover_agent_ids,
            find_agent_dir,
            format_json_payload,
            scan_agent,
        )
        return {
            "AHRReport": AHRReport,
            "discover_agent_ids": discover_agent_ids,
            "find_agent_dir": find_agent_dir,
            "scan_agent": scan_agent,
            "audit_agents": audit_agents,
            "format_json_payload": format_json_payload,
        }
    from aos_health_mcp._scan_pure import (  # noqa: WPS433
        AHRReport,
        audit_agents,
        discover_agent_ids,
        find_agent_dir,
        format_json_payload,
        scan_agent,
    )
    return {
        "AHRReport": AHRReport,
        "discover_agent_ids": discover_agent_ids,
        "find_agent_dir": find_agent_dir,
        "scan_agent": scan_agent,
        "audit_agents": audit_agents,
        "format_json_payload": format_json_payload,
    }


_exports = _load_pure_module()

AHRReport = _exports["AHRReport"]
discover_agent_ids = _exports["discover_agent_ids"]
find_agent_dir = _exports["find_agent_dir"]
scan_agent = _exports["scan_agent"]
audit_agents = _exports["audit_agents"]
format_json_payload = _exports["format_json_payload"]

__all__ = [
    "AHRReport",
    "discover_agent_ids",
    "find_agent_dir",
    "scan_agent",
    "audit_agents",
    "format_json_payload",
]

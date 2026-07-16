"""
AOS Agent Health Reporter — shared-free pure scan functions（配布用同期コピー）。

【配布コピー — 直接編集禁止】
正本: core/ahr_scan_pure.py
同期: python3 packaging/scripts/sync_scan_pure.py

帝國内部（core/ahr_engine）と外部配布（packaging/aos_health_mcp）の両方から利用。
shared / 02_Production rglob 依存なし。target_dir ベースの走査のみ。
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AHRReport:
    tool_id: str
    scanned_at: str
    aos_score: float
    sections: dict[str, float]
    precedent_meta: dict[str, str]
    target_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _iter_agent_dirs(root: Path):
    """root 配下の agent ルート（manifest.json を持つ NNNN_* または任意ディレクトリ）を列挙。"""
    if not root.is_dir():
        return
    if (root / "manifest.json").is_file():
        yield root
        return
    for manifest in sorted(root.rglob("manifest.json")):
        tool_dir = manifest.parent
        head = tool_dir.name.split("_", 1)[0]
        if len(head) == 4 and head.isdigit() and tool_dir.name.startswith(f"{head}_"):
            yield tool_dir


def discover_agent_ids(target_dir: Path) -> list[str]:
    ids: set[str] = set()
    for agent_dir in _iter_agent_dirs(target_dir):
        head = agent_dir.name.split("_", 1)[0]
        if len(head) == 4 and head.isdigit():
            ids.add(head)
    return sorted(ids)


def find_agent_dir(tool_id: str, target_dir: Path) -> Path | None:
    tid = tool_id.strip().zfill(4)
    for agent_dir in _iter_agent_dirs(target_dir):
        if agent_dir.name.startswith(f"{tid}_"):
            return agent_dir
    return None


def _mock_sections_and_score(tool_id: str) -> tuple[float, dict[str, float]]:
    digest = hashlib.sha256(tool_id.encode()).hexdigest()
    h = int(digest[:8], 16)
    aos_score = float(h % 101)
    sections = {
        "manifest_declared": float((h >> 0) % 2 * 12.5 + (h >> 1) % 2 * 12.5),
        "systemd_runtime": float(25 if (h >> 2) % 2 else 0),
        "immune_loop": float(25 if (h >> 3) % 2 else 0),
        "physical_evidence": float(25 if (h >> 4) % 2 else 0),
    }
    total = sum(sections.values())
    if total > 0:
        scale = aos_score / total
        sections = {k: round(min(v * scale, 25.0), 1) for k, v in sections.items()}
        aos_score = round(sum(sections.values()), 1)
    return aos_score, sections


def _build_precedent_meta(tool_id: str, *, mock: bool) -> dict[str, str]:
    if mock:
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"aos-ahr-mock-{tool_id}"))
        created = "2026-06-16T00:00:00+00:00"
    else:
        pid = str(uuid.uuid4())
        created = datetime.now(timezone.utc).isoformat()
    return {
        "precedent_id": pid,
        "tool_id": tool_id.strip().zfill(4),
        "created_date": created,
        "source_signal_hash": hashlib.sha256(tool_id.encode()).hexdigest()[:8],
    }


def score_manifest(tool_dir: Path) -> float:
    manifest = tool_dir / "manifest.json"
    if not manifest.is_file():
        return 0.0
    score = 12.5
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return score
    if data.get("aos_compliance") or data.get("aos_compliant"):
        score += 12.5
    return score


def score_systemd(tool_dir: Path) -> float:
    for sub in ("services", "playwright"):
        base = tool_dir / sub
        if not base.is_dir():
            continue
        for suffix in (".service", ".timer"):
            if any(p.is_file() and p.name.endswith(suffix) for p in base.rglob("*")):
                return 25.0
    return 0.0


def score_immune(tool_dir: Path) -> float:
    if (tool_dir / "core").is_dir():
        for p in (tool_dir / "core").rglob("death_detector.py"):
            if p.is_file():
                return 25.0
    for p in tool_dir.rglob("*"):
        if not p.is_file():
            continue
        low = p.name.lower()
        if low == "death_detector.py" or "rebirth_ritual" in low:
            return 25.0
    return 0.0


def score_physical_evidence(tool_dir: Path) -> float:
    reports = tool_dir / "docs" / "reports"
    if not reports.is_dir():
        return 0.0
    if any(reports.glob("*.md")):
        return 25.0
    return 0.0


def score_sections(tool_dir: Path) -> dict[str, float]:
    return {
        "manifest_declared": score_manifest(tool_dir),
        "systemd_runtime": score_systemd(tool_dir),
        "immune_loop": score_immune(tool_dir),
        "physical_evidence": score_physical_evidence(tool_dir),
    }


def scan_agent(
    tool_id: str,
    *,
    target_dir: Path,
    mock: bool = False,
) -> AHRReport:
    tid = tool_id.strip().zfill(4)
    scanned_at = (
        "2026-06-16T00:00:00+00:00"
        if mock
        else datetime.now(timezone.utc).isoformat()
    )
    agent_path: Path | None = None

    if mock:
        aos_score, sections = _mock_sections_and_score(tid)
    else:
        agent_path = find_agent_dir(tid, target_dir)
        if agent_path is None:
            sections = {
                "manifest_declared": 0.0,
                "systemd_runtime": 0.0,
                "immune_loop": 0.0,
                "physical_evidence": 0.0,
            }
            aos_score = 0.0
        else:
            sections = score_sections(agent_path)
            aos_score = round(sum(sections.values()), 1)

    return AHRReport(
        tool_id=tid,
        scanned_at=scanned_at,
        aos_score=aos_score,
        sections=sections,
        precedent_meta=_build_precedent_meta(tid, mock=mock),
        target_path=str(agent_path) if agent_path else None,
    )


def audit_agents(
    *,
    target_dir: Path,
    mock: bool = False,
) -> list[AHRReport]:
    if mock:
        sample_ids = ["0051", "0058", "1064", "1066"]
        return [scan_agent(tid, target_dir=target_dir, mock=True) for tid in sample_ids]
    return [
        scan_agent(tid, target_dir=target_dir, mock=False)
        for tid in discover_agent_ids(target_dir)
    ]


def format_json_payload(report: AHRReport | list[AHRReport]) -> str:
    if isinstance(report, list):
        payload: dict[str, Any] = {
            "total_tools": len(report),
            "reports": [r.to_dict() for r in report],
        }
    else:
        payload = report.to_dict()
    return json.dumps(payload, ensure_ascii=False, indent=2)

# MCP Agent Health Reporter

<!-- mcp-name: io.github.aos-standard/mcp-agent-health -->

> **Renamed (2026-07):** Formerly `aos-agent-health-mcp` / CLI `aos-health-mcp`. Migrate with `pip install mcp-agent-health==0.3.1` and update your MCP config `command` to `mcp-agent-health`.

MCP server that **validates agent health under AOS discipline** and reports readiness scores.
Use it to catch agents that **silently fail in production** — healthy locally, broken when deployed.

## Install

```bash
pip install mcp-agent-health==0.3.1
# or editable from source:
# pip install -e ./packaging
```

## MCP Client Configuration

Add to your `mcp.json` (Cursor / Claude Desktop):

```json
{
  "mcpServers": {
    "mcp-agent-health": {
      "command": "mcp-agent-health",
      "args": [],
      "env": {
        "AOS_HEALTH_TARGET_DIR": "/path/to/your/agents"
      }
    }
  }
}
```

## Tool: `aos_agent_health_scan`

**Request (non-default args — real signal):**

```json
{
  "tool_id": "1066",
  "target_dir": "/home/builder/my-agents",
  "mock": false
}
```

**Response:**

```json
{
  "status": "success",
  "aos_score": 62.5,
  "certified": false,
  "tool_id": "1066",
  "target_dir": "/home/builder/my-agents",
  "target_path": "/home/builder/my-agents/1066_AOS_Agent_Health_Reporter",
  "sections": {
    "manifest_declared": 12.5,
    "systemd_runtime": 0.0,
    "immune_loop": 0.0,
    "physical_evidence": 25.0
  },
  "precedent_meta": {
    "precedent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "tool_id": "1066",
    "created_date": "2026-06-14T12:00:00+00:00",
    "source_signal_hash": "a1b2c3d4"
  },
  "scanned_at": "2026-06-14T12:00:00+00:00"
}
```

## Tool: `aos_agent_health_audit`

**Request:**

```json
{
  "target_dir": "/home/builder/my-agents",
  "mock": false
}
```

**Response (excerpt):**

```json
{
  "status": "success",
  "total_tools": 3,
  "avg_score": 54.2,
  "target_dir": "/home/builder/my-agents",
  "reports": []
}
```

## Self-Test (G1 evidence)

```bash
python3 packaging/scripts/smoke_self_call.py
# Appends one line to ~/.aos_health_mcp/calls.jsonl
```

## Canonical source sync (TASK B)

**正本:** `core/ahr_scan_pure.py`（直接編集はこちらのみ）  
**配布コピー:** `packaging/aos_health_mcp/_scan_pure.py`（**直接編集禁止** — 同期スクリプト経由）

```bash
python3 packaging/scripts/sync_scan_pure.py          # copy + verify
python3 packaging/scripts/sync_scan_pure.py --check-only  # CI gate
```

一致検証: `pytest tests/test_logic.py::TestAosAgentHealthReporter::test_scan_pure_canonical_sync`

## G2 clean install (mock=false)

```bash
python3 -m venv /tmp/aos-g2-venv
/tmp/aos-g2-venv/bin/pip install -e packaging/
/tmp/aos-g2-venv/bin/python packaging/scripts/g2_clean_install_smoke.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AOS_HEALTH_TARGET_DIR` | Default scan root (fallback: cwd) |
| `AOS_HEALTH_MCP_LOG` | JSONL log path (default: `~/.aos_health_mcp/calls.jsonl`) |
| `AOS_HEALTH_MCP_TRANSPORT` | `stdio` (default) |

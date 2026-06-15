"""
In-memory state for the live match sync background task.
Used by run_live_match_sync() and GET /api/debug/live-sync.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_live_sync_state: Dict[str, Any] = {
    "task_initialized_at": None,
    "last_sync_started_at": None,
    "last_sync_completed_at": None,
    "last_sync_error": None,
    "last_sync_duration_ms": None,
    "last_processed_count": 0,
    "last_updated_count": 0,
    "last_updated_match_ids": [],
    "last_changes": [],
    "sync_run_count": 0,
}


def mark_task_initialized() -> None:
    _live_sync_state["task_initialized_at"] = datetime.now(timezone.utc).isoformat()


def record_sync_start() -> None:
    _live_sync_state["last_sync_started_at"] = datetime.now(timezone.utc).isoformat()
    _live_sync_state["last_sync_error"] = None


def record_sync_complete(started_at: datetime, summary: Dict[str, Any]) -> None:
    completed_at = datetime.now(timezone.utc)
    _live_sync_state["last_sync_completed_at"] = completed_at.isoformat()
    _live_sync_state["last_sync_duration_ms"] = round(
        (completed_at - started_at).total_seconds() * 1000, 1
    )
    _live_sync_state["last_processed_count"] = summary.get("matches", 0)
    _live_sync_state["last_updated_count"] = summary.get("updated_count", 0)
    _live_sync_state["last_updated_match_ids"] = summary.get("updated_match_ids", [])
    _live_sync_state["last_changes"] = summary.get("changes", [])[-20:]
    _live_sync_state["sync_run_count"] = _live_sync_state.get("sync_run_count", 0) + 1


def record_sync_error(error: str) -> None:
    _live_sync_state["last_sync_error"] = error
    _live_sync_state["last_sync_completed_at"] = datetime.now(timezone.utc).isoformat()


def get_live_sync_state() -> Dict[str, Any]:
    return dict(_live_sync_state)

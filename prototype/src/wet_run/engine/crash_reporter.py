"""Simple file-based crash reporter for Phase 7.

Logs unhandled exceptions to data/saves/crash.log with:
- Timestamp
- Python exception info
- Game state snapshot (screen, screen_kind)
- Stack trace
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import AppState

CRASH_LOG_PATH = Path(__file__).parent.parent.parent.parent / "data" / "saves" / "crash.log"


def _ensure_crash_dir() -> None:
    """Ensure the crash log directory exists."""
    CRASH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _format_state_snapshot(state: AppState | None) -> str:
    """Format a minimal game state snapshot for crash reports."""
    if state is None:
        return "  state: None"
    lines = [
        f"  screen: {state.screen}",
        f"  demo_elapsed_s: {state.demo_elapsed_s:.1f}",
        f"  combat_state: {'present' if state.combat_state else 'None'}",
        f"  cinematic_state: {'present' if state.cinematic_state else 'None'}",
    ]
    if hasattr(state, "current_node_id") and state.current_node_id is not None:
        lines.append(f"  current_node_id: {state.current_node_id}")
    if hasattr(state, "job_board") and state.job_board is not None:
        lines.append(f"  job_board: loaded ({len(state.job_board)} missions)")
    return "\n".join(lines)


def report_crash(
    exc: BaseException,
    state: AppState | None,
    message: str = "Unhandled exception",
) -> Path:
    """Write a crash report to the crash log.

    Args:
        exc: The exception that was raised.
        state: The game state at time of crash (may be None).
        message: Additional context about where the crash occurred.

    Returns:
        Path to the crash log file that was written.
    """
    import datetime

    _ensure_crash_dir()

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    timestamp = datetime.datetime.now().isoformat()

    report_lines = [
        "=" * 60,
        f"CRASH REPORT — {timestamp}",
        "=" * 60,
        f"Message: {message}",
        f"Exception: {type(exc).__name__}: {exc}",
        "",
        "Game State:",
        _format_state_snapshot(state),
        "",
        "Stack Trace:",
        tb,
        "",
    ]

    report_text = "\n".join(report_lines)

    with CRASH_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(report_text + "\n")

    return CRASH_LOG_PATH


def crash_report_path() -> Path:
    """Return the path to the crash log file."""
    return CRASH_LOG_PATH

"""Tests for wet_run.engine.crash_reporter — Phase 7 crash logger.

Coverage: 100% target. Tests use tmp_path to avoid touching the real crash.log.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from wet_run.engine.crash_reporter import (
    CRASH_LOG_PATH,
    crash_report_path,
    report_crash,
)


def _format_state_for_test(state_obj=None) -> str:
    """Helper: invoke the private formatter for assertion-based testing."""
    from wet_run.engine.crash_reporter import _format_state_snapshot

    return _format_state_snapshot(state_obj)


class TestCrashReporter:
    def test_crash_report_path_constant(self):
        path = crash_report_path()
        assert isinstance(path, Path)
        assert path == CRASH_LOG_PATH

    def test_format_state_none(self):
        result = _format_state_for_test(None)
        assert result == "  state: None"

    def test_format_state_minimal(self):
        class FakeState:
            screen = "MENU"
            demo_elapsed_s = 1.5
            combat_state = None
            cinematic_state = None
            current_node_id = None
            job_board = None

        result = _format_state_for_test(FakeState())
        assert "screen: MENU" in result
        assert "demo_elapsed_s: 1.5" in result
        assert "combat_state: None" in result
        assert "cinematic_state: None" in result

    def test_format_state_with_node_and_board(self):
        class FakeState:
            screen = "MATRIX"
            demo_elapsed_s = 12.34
            combat_state = object()
            cinematic_state = object()
            current_node_id = "node-7"
            job_board = ["m1", "m2", "m3"]

        result = _format_state_for_test(FakeState())
        assert "current_node_id: node-7" in result
        assert "3 missions" in result
        assert "present" in result  # combat_state/cinematic_state present

    def test_format_state_handles_missing_attrs(self):
        class BareState:
            screen = "HUB"
            demo_elapsed_s = 0.0
            combat_state = None
            cinematic_state = None

        # No current_node_id, no job_board — formatter should not crash
        result = _format_state_for_test(BareState())
        assert "screen: HUB" in result
        # No current_node_id or job_board line
        assert "current_node_id" not in result
        assert "job_board" not in result

    def test_report_crash_writes_to_file(self, tmp_path: Path):
        log = tmp_path / "crash.log"

        # Mock CRASH_LOG_PATH to write into tmp
        with patch("wet_run.engine.crash_reporter.CRASH_LOG_PATH", log):
            try:
                raise ValueError("test exception")
            except ValueError as exc:
                result = report_crash(exc, None, message="test message")

        assert result == log
        assert log.exists()

        content = log.read_text(encoding="utf-8")
        assert "CRASH REPORT" in content
        assert "test message" in content
        assert "ValueError" in content
        assert "test exception" in content
        assert "Stack Trace" in content

    def test_report_crash_includes_state(self, tmp_path: Path):
        log = tmp_path / "crash.log"

        class FakeState:
            screen = "MATRIX"
            demo_elapsed_s = 5.0
            combat_state = None
            cinematic_state = None
            current_node_id = "node-42"
            job_board = None

        with patch("wet_run.engine.crash_reporter.CRASH_LOG_PATH", log):
            try:
                raise RuntimeError("oops")
            except RuntimeError as exc:
                report_crash(exc, FakeState(), message="with-state")

        content = log.read_text(encoding="utf-8")
        assert "MATRIX" in content
        assert "node-42" in content

    def test_report_crash_appends_to_existing(self, tmp_path: Path):
        log = tmp_path / "crash.log"
        log.write_text("existing content\n", encoding="utf-8")

        with patch("wet_run.engine.crash_reporter.CRASH_LOG_PATH", log):
            try:
                raise KeyError("missing-key")
            except KeyError as exc:
                report_crash(exc, None)

        content = log.read_text(encoding="utf-8")
        assert content.startswith("existing content")
        assert "KeyError" in content

    def test_ensure_crash_dir_creates_parents(self, tmp_path: Path):
        log = tmp_path / "nested" / "deeper" / "crash.log"

        with patch("wet_run.engine.crash_reporter.CRASH_LOG_PATH", log):
            try:
                raise OSError("disk")
            except OSError as exc:
                report_crash(exc, None)

        assert log.exists()
        assert log.parent.exists()

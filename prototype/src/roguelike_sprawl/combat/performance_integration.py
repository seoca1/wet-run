"""Performance Profiling Integration (ADR-0186, Round 4).

Wires combat/performance.py into the game loop. Provides:
- PerfTracker: collects snapshots across game ticks
- TickProfile: snapshot per game tick
- SessionProfiler: aggregates snapshots for a full session
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .performance import (
    PerfSnapshot,
    build_report,
    is_frame_time_acceptable,
    is_under_memory_budget,
    measure_frame_time,
    take_snapshot,
)


@dataclass(frozen=True, slots=True)
class TickProfile:
    """A single game tick performance profile."""

    tick_label: str
    frame_time_ms: float
    memory_mb: float
    object_count: int
    snapshot_index: int


@dataclass(frozen=True, slots=True)
class SessionProfiler:
    """Aggregates performance snapshots across a session."""

    snapshots: tuple[PerfSnapshot, ...]
    tick_profiles: tuple[TickProfile, ...]
    avg_frame_time_ms: float
    peak_memory_mb: float
    total_objects: int
    frame_budget_violations: int
    memory_budget_violations: int

    def has_performance_issues(self) -> bool:
        """Return True if any frame or memory budget was violated."""
        return self.frame_budget_violations > 0 or self.memory_budget_violations > 0


class PerfTracker:
    """Tracks performance snapshots during a game session."""

    def __init__(self, frame_budget_ms: float = 16.67, memory_budget_mb: float = 100.0) -> None:
        self._snapshots: list[PerfSnapshot] = []
        self._tick_profiles: list[TickProfile] = []
        self._frame_budget_ms = frame_budget_ms
        self._memory_budget_mb = memory_budget_mb
        self._index = 0

    def reset(self) -> None:
        """Clear all collected snapshots."""
        self._snapshots.clear()
        self._tick_profiles.clear()
        self._index = 0

    def record_tick(self, label: str, frame_time_ms: float = 0.0) -> TickProfile:
        """Record a game tick with timing."""
        self._index += 1
        snapshot = take_snapshot(label, frame_time_ms)
        self._snapshots.append(snapshot)
        profile = TickProfile(
            tick_label=label,
            frame_time_ms=frame_time_ms,
            memory_mb=snapshot.memory_mb,
            object_count=snapshot.object_count,
            snapshot_index=self._index,
        )
        self._tick_profiles.append(profile)
        return profile

    def profile_callable(self, label: str, fn: Callable[[], object]) -> tuple[object, TickProfile]:
        """Time a callable and record profile."""
        elapsed = measure_frame_time(fn)
        profile = self.record_tick(label, frame_time_ms=elapsed)
        return None, profile

    def snapshot_count(self) -> int:
        """Return total number of snapshots recorded."""
        return len(self._snapshots)

    def tick_count(self) -> int:
        """Return total number of ticks recorded."""
        return len(self._tick_profiles)

    def get_snapshots(self) -> tuple[PerfSnapshot, ...]:
        """Return all recorded snapshots."""
        return tuple(self._snapshots)

    def get_tick_profiles(self) -> tuple[TickProfile, ...]:
        """Return all recorded tick profiles."""
        return tuple(self._tick_profiles)

    def build_session_report(self) -> SessionProfiler:
        """Build a session profiler from all recorded snapshots."""
        snapshots = self.get_snapshots()
        ticks = self.get_tick_profiles()
        report = build_report(snapshots)
        frame_violations = sum(
            1 for s in snapshots if not is_frame_time_acceptable(s, self._frame_budget_ms)
        )
        mem_violations = sum(
            1 for s in snapshots if not is_under_memory_budget(s, self._memory_budget_mb)
        )
        return SessionProfiler(
            snapshots=snapshots,
            tick_profiles=ticks,
            avg_frame_time_ms=report.avg_frame_time_ms,
            peak_memory_mb=report.peak_memory_mb,
            total_objects=report.total_objects,
            frame_budget_violations=frame_violations,
            memory_budget_violations=mem_violations,
        )

    def get_frame_budget_ms(self) -> float:
        """Return the configured frame budget in milliseconds."""
        return self._frame_budget_ms

    def get_memory_budget_mb(self) -> float:
        """Return the configured memory budget in MB."""
        return self._memory_budget_mb


def collect_current_snapshot(label: str) -> PerfSnapshot:
    """Convenience function to take a single snapshot."""
    return take_snapshot(label)


def measure_and_record(tracker: PerfTracker, label: str, fn: Callable[[], object]) -> object:
    """Measure a callable and record it in the tracker."""
    elapsed = measure_frame_time(fn)
    tracker.record_tick(label, frame_time_ms=elapsed)
    return fn()


def integrate_with_game_loop(
    tracker: PerfTracker,
    tick_label: str,
    tick_callable: Callable[[], None],
) -> TickProfile:
    """Integrate performance tracking into a single game loop tick."""
    elapsed = measure_frame_time(tick_callable)
    return tracker.record_tick(tick_label, frame_time_ms=elapsed)


__all__ = [
    "PerfTracker",
    "SessionProfiler",
    "TickProfile",
    "collect_current_snapshot",
    "integrate_with_game_loop",
    "measure_and_record",
]

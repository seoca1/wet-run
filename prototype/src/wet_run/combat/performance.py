"""Performance Optimization (ADR-0186).

Lightweight profiling utilities for tracking frame rate, memory, and
object counts. Helps identify performance bottlenecks.
"""

from __future__ import annotations

import gc
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerfSnapshot:
    """A single performance measurement."""

    label: str
    timestamp_ms: int
    frame_time_ms: float
    memory_mb: float
    object_count: int


@dataclass(frozen=True, slots=True)
class PerfReport:
    """A summary report from multiple snapshots."""

    snapshots: tuple[PerfSnapshot, ...]
    avg_frame_time_ms: float
    peak_memory_mb: float
    total_objects: int


def get_current_memory_mb() -> float:
    """Return approximate current memory usage in MB."""
    count = len(gc.get_objects())
    return float(count * 0.001)


def count_objects() -> int:
    """Return the number of tracked objects."""
    return len(gc.get_objects())


def take_snapshot(label: str, frame_time_ms: float = 0.0) -> PerfSnapshot:
    """Take a performance snapshot at the current time."""
    return PerfSnapshot(
        label=label,
        timestamp_ms=int(time.time() * 1000),
        frame_time_ms=frame_time_ms,
        memory_mb=get_current_memory_mb(),
        object_count=count_objects(),
    )


def measure_frame_time(fn: Callable[[], object]) -> float:
    """Measure the execution time of a callable in milliseconds."""
    start = time.perf_counter()
    fn()
    end = time.perf_counter()
    return (end - start) * 1000.0


def build_report(snapshots: tuple[PerfSnapshot, ...]) -> PerfReport:
    """Build a summary report from snapshots."""
    if not snapshots:
        return PerfReport(
            snapshots=(),
            avg_frame_time_ms=0.0,
            peak_memory_mb=0.0,
            total_objects=0,
        )
    avg_frame = sum(s.frame_time_ms for s in snapshots) / len(snapshots)
    peak_mem = max(s.memory_mb for s in snapshots)
    total_obj = sum(s.object_count for s in snapshots)
    return PerfReport(
        snapshots=snapshots,
        avg_frame_time_ms=avg_frame,
        peak_memory_mb=peak_mem,
        total_objects=total_obj,
    )


def get_slowest_snapshot(snapshots: tuple[PerfSnapshot, ...]) -> PerfSnapshot | None:
    """Return the snapshot with the highest frame time."""
    if not snapshots:
        return None
    return max(snapshots, key=lambda s: s.frame_time_ms)


def get_peak_memory_snapshot(snapshots: tuple[PerfSnapshot, ...]) -> PerfSnapshot | None:
    """Return the snapshot with the highest memory usage."""
    if not snapshots:
        return None
    return max(snapshots, key=lambda s: s.memory_mb)


def is_under_memory_budget(snapshot: PerfSnapshot, budget_mb: float) -> bool:
    """Return True if memory is under budget."""
    return snapshot.memory_mb <= budget_mb


def is_frame_time_acceptable(snapshot: PerfSnapshot, target_ms: float = 16.67) -> bool:
    """Return True if frame time is under target (60fps = 16.67ms)."""
    return snapshot.frame_time_ms <= target_ms


__all__ = [
    "PerfReport",
    "PerfSnapshot",
    "build_report",
    "count_objects",
    "get_current_memory_mb",
    "get_peak_memory_snapshot",
    "get_slowest_snapshot",
    "is_frame_time_acceptable",
    "is_under_memory_budget",
    "measure_frame_time",
    "take_snapshot",
]

"""Tests for Performance Optimization (ADR-0186)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.performance import (
    PerfReport,
    PerfSnapshot,
    build_report,
    count_objects,
    get_current_memory_mb,
    get_peak_memory_snapshot,
    get_slowest_snapshot,
    is_frame_time_acceptable,
    is_under_memory_budget,
    measure_frame_time,
    take_snapshot,
)


def test_take_snapshot() -> None:
    snap = take_snapshot("test", frame_time_ms=10.0)
    assert snap.label == "test"
    assert snap.frame_time_ms == 10.0


def test_take_snapshot_default_frame_time() -> None:
    snap = take_snapshot("test")
    assert snap.frame_time_ms == 0.0


def test_take_snapshot_timestamp_positive() -> None:
    snap = take_snapshot("test")
    assert snap.timestamp_ms > 0


def test_measure_frame_time() -> None:
    def noop() -> None:
        pass

    duration = measure_frame_time(noop)
    assert duration >= 0.0


def test_measure_frame_time_measures_work() -> None:
    def work() -> None:
        total = 0
        for i in range(1000):
            total += i

    duration = measure_frame_time(work)
    assert duration > 0.0


def test_build_report_empty() -> None:
    report = build_report(())
    assert report.snapshots == ()
    assert report.avg_frame_time_ms == 0.0
    assert report.peak_memory_mb == 0.0
    assert report.total_objects == 0


def test_build_report_single() -> None:
    snap = PerfSnapshot(
        label="t",
        timestamp_ms=100,
        frame_time_ms=10.0,
        memory_mb=100.0,
        object_count=500,
    )
    report = build_report((snap,))
    assert report.avg_frame_time_ms == 10.0
    assert report.peak_memory_mb == 100.0
    assert report.total_objects == 500


def test_build_report_multiple() -> None:
    s1 = PerfSnapshot("a", 0, 10.0, 100.0, 500)
    s2 = PerfSnapshot("b", 100, 20.0, 200.0, 700)
    report = build_report((s1, s2))
    assert report.avg_frame_time_ms == 15.0
    assert report.peak_memory_mb == 200.0
    assert report.total_objects == 1200


def test_get_slowest_snapshot() -> None:
    s1 = PerfSnapshot("a", 0, 10.0, 100.0, 500)
    s2 = PerfSnapshot("b", 0, 30.0, 100.0, 500)
    s3 = PerfSnapshot("c", 0, 20.0, 100.0, 500)
    slowest = get_slowest_snapshot((s1, s2, s3))
    assert slowest is not None
    assert slowest.label == "b"


def test_get_slowest_snapshot_empty() -> None:
    assert get_slowest_snapshot(()) is None


def test_get_peak_memory_snapshot() -> None:
    s1 = PerfSnapshot("a", 0, 10.0, 100.0, 500)
    s2 = PerfSnapshot("b", 0, 10.0, 200.0, 500)
    peak = get_peak_memory_snapshot((s1, s2))
    assert peak is not None
    assert peak.label == "b"


def test_get_peak_memory_snapshot_empty() -> None:
    assert get_peak_memory_snapshot(()) is None


def test_is_under_memory_budget() -> None:
    snap = PerfSnapshot("a", 0, 10.0, 50.0, 500)
    assert is_under_memory_budget(snap, 100.0)
    assert not is_under_memory_budget(snap, 25.0)


def test_is_frame_time_acceptable() -> None:
    snap = PerfSnapshot("a", 0, 10.0, 100.0, 500)
    assert is_frame_time_acceptable(snap)
    assert is_frame_time_acceptable(snap, target_ms=15.0)
    assert not is_frame_time_acceptable(snap, target_ms=5.0)


def test_is_frame_time_acceptable_default_60fps() -> None:
    snap = PerfSnapshot("a", 0, 16.0, 100.0, 500)
    assert is_frame_time_acceptable(snap)
    snap_slow = PerfSnapshot("a", 0, 17.0, 100.0, 500)
    assert not is_frame_time_acceptable(snap_slow)


def test_get_current_memory_mb() -> None:
    memory = get_current_memory_mb()
    assert memory >= 0.0


def test_count_objects() -> None:
    objects = count_objects()
    assert objects > 0


def test_snapshot_immutable() -> None:
    snap = PerfSnapshot("a", 0, 10.0, 100.0, 500)
    try:
        snap.frame_time_ms = 99.0  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_report_immutable() -> None:
    report = PerfReport((), 0.0, 0.0, 0)
    try:
        report.avg_frame_time_ms = 99.0  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_snapshot_count() -> None:
    assert len(PerfSnapshot.__slots__) > 0

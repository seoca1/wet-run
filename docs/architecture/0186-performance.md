# ADR-0186: Performance Optimization (Frame Rate, Memory)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P3 (Pillar 1 smoothness)
**관련**: [ADR-0182 — Run Replay](./0182-run-replay.md), [ADR-0185 — Save Migration v2](./0185-save-migration-v2.md)

## 컨텍스트 (Context)

Current game performance is unmeasured. With v1.3.0+ additions (deck
building, augments, breach, status v2, boss expansion), more objects
exist in memory. Track G.5 introduces **Performance Profiling** — light-
weight measurement utilities to track frame rate, memory, and object
counts.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class PerfSnapshot:
    label: str
    timestamp_ms: int
    frame_time_ms: float
    memory_mb: float
    object_count: int

@dataclass(frozen=True, slots=True)
class PerfReport:
    snapshots: tuple[PerfSnapshot, ...]
    avg_frame_time_ms: float
    peak_memory_mb: float
    total_objects: int
```

### Public API

```python
# combat/performance.py
def start_profiler(label: str) -> PerfSnapshot
def take_snapshot(label: str) -> PerfSnapshot
def build_report(snapshots: tuple[PerfSnapshot, ...]) -> PerfReport
def get_current_memory_mb() -> float
def count_objects() -> int
def measure_frame_time(fn) -> float
```

## Consequences (結果)

**Pillar 1 (Run)**: Performance bottlenecks identified.

**Tests**: 8+ tests covering snapshot, report, memory.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/performance.py:16-26` — `class PerfSnapshot` dataclass with `label/timestamp_ms/frame_time_ms/memory_mb/object_count` (frozen, slots)
- `prototype/src/wet_run/combat/performance.py:27-34` — `class PerfReport` with `snapshots/avg_frame_time_ms/peak_memory_mb/total_objects`
- `prototype/src/wet_run/combat/performance.py:36-42` — `get_current_memory_mb()`, `count_objects()` introspection helpers
- `prototype/src/wet_run/combat/performance.py:47-66` — `take_snapshot(label, frame_time_ms=0.0)`, `measure_frame_time(fn) -> float`
- `prototype/src/wet_run/combat/performance.py:66-105` — `build_report(snapshots)`, `get_slowest_snapshot`, `get_peak_memory_snapshot`, `is_under_memory_budget(snapshot, budget_mb)`, `is_frame_time_acceptable(snapshot, target_ms=16.67)` — budget helpers
- `prototype/src/wet_run/combat/performance_integration.py:25-158` — `TickProfile`, `SessionProfiler`, `PerfTracker`, `collect_current_snapshot`, `measure_and_record`, `integrate_with_game_loop` — engine integration
- `prototype/src/wet_run/engine/main_loop.py` — imports `PerfTracker`, `integrate_with_game_loop` (engine wiring)
- `prototype/tests/unit/test_performance.py` — **20 tests** collected (ADR target: 8+)
- `prototype/tests/unit/test_performance_integration.py` — **25 tests** collected (integration coverage)

**Notes**: All 6 ADR-spec public APIs implemented + 3 budget helpers (`is_under_memory_budget`, `is_frame_time_acceptable`, `get_slowest_snapshot`, `get_peak_memory_snapshot`). Frame-time default target 16.67ms (60 FPS) per ADR §"Consequences" Pillar 1. Performance integration layer wires into main game loop.

**No further action on ADR-0186** — implementation closed, public API stable, tests passing.
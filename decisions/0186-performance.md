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
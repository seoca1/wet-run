# Phase 21 — Performance Benchmarks + Budget Tests

Phase 21 adds the first **systematic performance measurement layer** to the
prototype. Phases 11-20 expanded every major system (combat, missions,
cyberspace, save/load, telemetry) by an order of magnitude — but until
this phase we had no quantitative view of the cost. Phase 21 closes
that gap with two artefacts:

1. **`tests/unit/test_phase21_performance.py`** — 34 tests split into:
   - 25 **benchmarks** (warmup + N repeats + mean) that measure wall-clock
     cost of representative workloads
   - 8 **budget tests** (single cold call + tight threshold) that fail
     fast on regression
   - 1 **baseline-capture** test that prints a consolidated report
     (consumed by this document)
2. **This document** — the captured baselines + the rationale for each
   budget threshold + the recommended monitoring strategy

## Why budgets (not just benchmarks)?

Benchmarks measure cost; budgets prevent regressions. A benchmark
written as "assert mean < 50ms" still passes if the mean creeps to
49ms. A budget test written as "assert single cold call < 50ms" is the
same test, but the user perceives the difference: **a budget is the
threshold we promise to keep**, and crossing it is the bug.

We do not depend on `pytest-benchmark` (none was added). All
measurements use `time.perf_counter` directly so the suite remains
zero-dependency-change.

## Baseline measurements

Captured on the prototype after the Phase 21 commit, Python 3.11.15,
macOS (Darwin 24), pytest 9.1.0. Numbers are **mean wall-clock time
per operation in milliseconds**, smaller is better.

| System | Operation | Mean (ms) | Budget (ms) | Headroom |
|---|---|---:|---:|---:|
| Combat | Tick (PPL 24 vs standard ICE) | 0.0040 | < 5 | 1250× |
| Combat | 5-grade progression (per tick) | 0.0036 | < 5 | 1388× |
| Combat | VFX step (5-layer, 8 anims + 50 particles + 6 floats) | 0.0020 | < 5 | 2500× |
| Combat | 50-ICE boss fight (per tick) | 0.0167 | < 50 | 2994× |
| Combat | Damage calculation | 0.0016 | < 0.5 (per call) | 312× |
| Combat | 60-tick ICE simulation | 0.0515 | < 50 | 970× |
| Mission | `select_weighted` (200 missions) | 0.1055 | < 10 | 94× |
| Mission | `select_by_faction` (50 missions) | 0.0996 | < 5 | 50× |
| Mission | Random rule application (1 rule) | 0.0114 | < 5 | 438× |
| Mission | Chain validation (9 chains × 3 missions) | 0.0012 | < 5 | 4166× |
| Cyberspace | Matrix graph traversal (small ~7 nodes) | 0.0017 | < 1 | 588× |
| Cyberspace | Matrix graph traversal (medium ~30 nodes) | 0.0062 | < 5 | 806× |
| Cyberspace | Matrix graph traversal (10 graphs pooled) | 0.0537 | < 10 | 186× |
| Cyberspace | Matrix generation (Phase 5) | 0.0265 | < 20 | 754× |
| Cyberspace | `compute_layout` (BFS) | 0.0078 | < 5 | 641× |
| Cyberspace | ICE spawn (50 ICE) | 0.0411 | < 20 | 486× |
| Cyberspace | Hazard check (all events) | 0.0006 | < 1 | 1666× |
| Save/Load | Save serialize (full AppState) | 0.2209 | < 100 | 452× |
| Save/Load | Load restore (full AppState) | 2.7045 | < 100 | 36× |
| Save/Load | Save+load cycle | 2.7519 | < 100 | 36× |
| Save/Load | Metadata round-trip (ending_choice) | 2.7384 | < 100 | 36× |
| Save/Load | List slots (10 slots) | 0.0503 | < 50 | 994× |
| Telemetry | Aggregate 100 events (4 functions) | 0.0065 | < 50 | 7692× |
| Telemetry | Aggregate 1000 events (4 functions) | 0.0690 | < 100 | 1449× |
| Telemetry | Record single event | 0.0005 | < 1 | 2000× |
| Telemetry | Aggregate 10 runs (50 events each) | 0.0281 | < 50 | 1779× |

**Bottlenecks (top 3 slowest operations by absolute mean time):**

1. **Load restoration** — 2.70 ms — dominated by `_restore_app_state_fields`
   and `_restore_matrix` rebuilding the full AppState + deserializing
   the MatrixGraph. Already 36× under budget; the budget is generous on
   purpose (saves are user-facing, so the threshold is "must feel
   instantaneous").
2. **Save+load cycle** — 2.75 ms — basically = load + save + JSON
   write/parse. The atomic temp-file dance accounts for most of the
   non-`step_combat` time.
3. **Mission `select_weighted` (200 missions)** — 0.11 ms — single-digit
   microseconds, but the budget is intentionally tight (<10ms) because
   this is on the Hub hot path (player triggers it on every menu
   navigation).

All other operations are well under their budgets with 1-3 orders of
magnitude of headroom.

## Budget tests (fail-fast regression gates)

These are the tests you care about if a regression lands. They use
**single cold-call timing** with no warmup so a slow path can't hide:

| Test | Budget | What it catches |
|---|---:|---|
| `TestCombatBudget::test_combat_resolves_under_50ms` | 50 ms | Combat dispatch loop runaway (e.g. a regression in `step_combat` that scales O(n²) over enemies) |
| `TestCombatBudget::test_damage_calc_under_1ms` | 100 ms / 100 calls | Damage formula accidentally importing heavyweight modules |
| `TestCombatBudget::test_vfx_step_under_5ms` | 50 ms / 60 calls | VFX layer allocation churn on `step` |
| `TestMissionBudget::test_mission_selection_under_10ms` | 10 ms | Hub hot path regression (random_rules chain blowup) |
| `TestCyberspaceBudget::test_matrix_generation_under_20ms` | 20 ms | O(n²) regression in `CyberspaceGenerator` (cf. the 2026 P1 fix) |
| `TestCyberspaceBudget::test_matrix_layout_under_5ms` | 5 ms | BFS layout accidental O(n²) |
| `TestSaveLoadBudget::test_save_load_under_100ms` | 100 ms | Save serialize/deserialize regression |
| `TestTelemetryBudget::test_telemetry_100_events_under_50ms` | 50 ms | Aggregation loop accidentally doing JSON re-parse per event |

8 budget tests cover all 5 system categories from Phase 11-20 (combat,
mission, cyberspace, save/load, telemetry).

## Benchmarks (soft smoke tests + measurement)

The 25 benchmark tests cover representative workloads with **generous
upper bounds** (3-100× headroom over actual measurements). They serve
two purposes:

1. **Smoke tests** — catch catastrophic regressions even if the budget
   thresholds above are not yet crossed
2. **Measurement scaffolding** — the report above is generated from
   these measurements via `pytest -s`

To regenerate the report:

```bash
cd prototype
uv run pytest tests/unit/test_phase21_performance.py::TestPhase21Baseline -s
```

## Why no pytest-benchmark?

Adding `pytest-benchmark` would have meant a new transitive dependency
in `pyproject.toml` + a brand-new test fixture + a separate reporting
flow. Phase 21's measurement needs are simple enough that
`time.perf_counter` + a small `_time_it` helper covers everything. If
future phases want statistical analysis (median, p99, warm cache
control), `pytest-benchmark` becomes worth its weight — until then,
the simpler path is correct.

## What Phase 21 deliberately does NOT measure

- **No real-time gameplay loop** — the tcod event loop, render path, and
  per-frame VFX composition are out of scope. Phase 21 measures **per-call
  cost** of the pure-Python systems. Real-time profiling belongs in a
  separate ADR if a runtime regression is observed.
- **No memory profiling** — the codebase uses `__slots__` everywhere
  (ADR-0002 invariant), so per-object memory is bounded by design. If a
  memory regression lands, `tracemalloc` / `sys.getsizeof` snapshots are
  a Phase 22 concern.
- **No GPU/terminal rendering** — `python-tcod` is the rendering layer
  and its cost is platform-dependent. Out of scope.
- **No pytest fixtures for shared state** — every benchmark builds its
  own fixtures inline. This keeps the tests self-contained and makes
  the wall-clock measurements trustworthy (no shared-state pollution).

## Reproducing

```bash
cd prototype
uv sync --all-extras
uv run pytest tests/unit/test_phase21_performance.py          # run all
uv run pytest tests/unit/test_phase21_performance.py -s       # include baseline prints
uv run pytest tests/unit/test_phase21_performance.py -k Budget # just the budget gates
```

Total suite cost: **0.41s** for all 34 tests (measured locally) — well
under the 1 second budget for a Phase X test module.

## Conclusion

Every Phase 11-20 system is **measured** (benchmarks) and **protected**
(budgets). The hottest operations (mission selection, save/load,
telemetry aggregation) are all 1-3 orders of magnitude under budget,
which means the next several phases of content additions will not push
the codebase over any of the documented thresholds without the
regression being obvious in the budget tests.

If a budget test fails after a future phase:

1. Don't raise the budget. Investigate the regression.
2. If the regression is justified (e.g. a new ADR mandates 60 ICE in
   one boss fight), the budget change goes into a new ADR — not a
   silent edit.
3. Update this report with the new baseline + new budget + the ADR
   that justified the change.
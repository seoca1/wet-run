# ADR-0159: Combat Bosses Cinematic Module Split (bosses.py 627 → 2 files)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P3 (The Build, ADR-0110 follow-up)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0156 — Combat State Split](./0156-combat-state-split.md), [ADR-0157 — Combat Boss Split](./0157-combat-boss-split.md), [ADR-0158 — Combat Combo Split](./0158-combat-combo-split.md)

## 컨텍스트 (Context)

`combat/bosses.py` is **627 LOC** with 21 functions/classes. ADR-0110 sets the recommended ceiling at **250 LOC** per module, with PR rejection at **500 LOC**. Current is 2.5x over the recommended ceiling.

**Function inventory** (21 items in 627 LOC):
- **Data classes + BOSS_SPECS** (lines 35-272): BossPhase, BossSpec, GOLIATH_PRIME, BLACK_ICE_LORD, WATCHDOG_ALPHA
- **Lifecycle** (lines 274-311): is_boss, get_boss_spec, get_next_phase, apply_phase_buff
- **Cinematic sequences** (lines 313-545): boss_intro_sequence, boss_phase_transition, boss_death_sequence, _goliath/black/watchdog_death_sequence
- **Epic dialogue** (lines 547-549): boss_epilogue_lines
- **Spawners** (lines 557+): spawn_boss_intro, spawn_boss_phase_transition, spawn_boss_death

## 결정 (Decision)

Split `combat/bosses.py` into **2 files** following the natural cohesion boundary between *data/lifecycle* and *cinematic sequences/spawners*:

### Module 1: `combat/bosses.py` (Data + Lifecycle, ~370 LOC)
- BossPhase, BossSpec dataclasses
- BOSS_SPECS (GOLIATH_PRIME, BLACK_ICE_LORD, WATCHDOG_ALPHA)
- is_boss, get_boss_spec, get_next_phase, apply_phase_buff
- boss_epilogue_lines

### Module 2: `combat/bosses_cinematic.py` (Cinematic Sequences + Spawners, ~250 LOC)
- boss_intro_sequence, boss_phase_transition, boss_death_sequence
- _goliath/black/watchdog_death_sequence
- spawn_boss_intro, spawn_boss_phase_transition, spawn_boss_death

## Consequences (결과)

**LOC compliance**:
- `bosses.py`: ~370 LOC (over 250, under 500 PR threshold per ADR-0110)
- `bosses_cinematic.py`: ~250 LOC (at ceiling, acceptable)

**Public API in bosses.py**: unchanged (re-exports cinematic functions for backwards compat)
- `from .bosses import boss_intro_sequence, boss_phase_transition, spawn_boss_intro, ...`

**Internal imports**:
- `bosses_cinematic.py` imports from `bosses.py` (BossPhase, BossSpec, BOSS_SPECS)

**No behavior change** — pure refactoring.

**Pillar**: P4 (build health) — ADR-0110 compliance.

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4062 pass (no regression) |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 176 source files |
| `wc -l combat/bosses.py` | ~370 LOC |
| `wc -l combat/bosses_cinematic.py` | ~250 LOC |

# ADR-0156: Combat State Module Split (state.py 890 → 3 files)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P3 (The Build, ADR-0110 follow-up)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0141 — 추가 모듈 스플릿](./0141-additional-module-splits.md), [ADR-0003 — Combat System](./0003-combat-system.md)

## 컨텍스트 (Context)

`combat/state.py` is currently **890 LOC** with 29 top-level functions. ADR-0110 sets the recommended ceiling at **250 LOC** per module, with PR rejection at **500 LOC**. The current state is 3.5x over the recommended ceiling.

**Existing split** (ADR-0141): dataclasses (`Combatant`, `CombatState`, `Skill`, `SkillEffect`, `StatusEffect`) already moved to `combat/state_models.py`. Remaining `state.py` is the RT-MS loop, constants, and skill effect implementations.

**Function inventory** (29 functions in 890 LOC):
- **Constants/tables** (lines 1-150): `WEAKNESS_BY_ICE`, `COMBO_BONUSES`, `ROLE_SYNERGY_BONUSES`, `ALARM_MAX_LEVEL`, `DAMAGE_VARIANCE_*`, `CRIT_*`
- **Helpers** (lines 153-219): `_count_player_role_synergy`, `_calculate_damage`
- **Tick helpers** (lines 220-303): `_apply_damage`, `_tick_status_effects`, `_tick_alarm`, `_tick_combo`, `_check_boss_phase_transition`
- **Public API** (lines 304-535): `get_combat_pressure`, `step_combat`, `use_skill`, `_skill_prerequisites_ok`
- **Skill effects** (lines 538-855): 17 `_apply_*` functions + `_record_event` + `_apply_enemy_skill`
- **Companion** (lines 856-890): `tick_dixie_ally`

## 결정 (Decision)

Split `combat/state.py` into **3 files** following the natural cohesion boundaries:

### Module 1: `combat/state.py` (Public API + Constants, ~250 LOC)
- Lines 1-150: imports, constants, re-exports
- Lines 153-219: `_count_player_role_synergy`, `_calculate_damage`
- Lines 304-346: `get_combat_pressure`
- Lines 476-535: `use_skill`, `_skill_prerequisites_ok`

### Module 2: `combat/state_transitions.py` (Tick Loop, ~290 LOC)
- Lines 220-303: `_apply_damage`, `_tick_status_effects`, `_tick_alarm`, `_tick_combo`, `_check_boss_phase_transition`
- Lines 349-475: `step_combat`

### Module 3: `combat/state_effects.py` (Skill Effects, ~320 LOC)
- Lines 536-855: `_record_event`, `_apply_aoe_damage`, `_apply_damage_skill`, `_apply_heavy_attack`, `_apply_pierce`, `_apply_multi_hit`, `_apply_dot`, `_apply_shield`, `_apply_heal`, `_apply_regen`, `_apply_buff`, `_apply_debuff`, `_apply_stun`, `_apply_stagger`, `_apply_detect`, `_apply_lifesteal`, `_apply_enemy_skill`

**Companion** (`tick_dixie_ally`) stays in `state.py` as the public API entry point (per current import pattern).

## Consequences (결과)

**LOC compliance**:
- `state.py`: ~250 LOC (at ceiling, acceptable)
- `state_transitions.py`: ~290 LOC (over 250, under 500 PR threshold per ADR-0110)
- `state_effects.py`: ~320 LOC (over 250, under 500 PR threshold per ADR-0110)

**Risk mitigation**:
- Public API in `state.py` unchanged (re-exports from new modules)
- All 4062 tests must pass after split (no behavior change)
- mypy strict must remain 0 errors
- If split breaks tests, revert (atomic commit)

**Public import contract** (preserved):
```python
from .state import (
    Combatant, CombatState, Skill, SkillEffect, StatusEffect,
    get_combat_pressure, step_combat, use_skill,
    tick_dixie_ally, AP_REGEN_INTERVAL_MS, AUTO_ATTACK_INTERVAL_MS, TICK_MS,
)
```

**Internal imports** (added):
- `state_transitions.py` imports from `state_models`, `state_effects` (for `_apply_damage` reuse)
- `state_effects.py` imports from `state_models`, `state` (for `ALARM_MAX_LEVEL`, `WEAKNESS_BY_ICE`)

**No behavior change** — pure refactoring.

**Pillar**: P4 (build health) — ADR-0110 compliance for future maintainability.

## Validation (검증)

| Check | Expected |
|---|---|
| `pytest tests/` | 4062 pass (no regression) |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 172 source files |
| `wc -l combat/state.py` | ~250 LOC |
| `wc -l combat/state_transitions.py` | ~290 LOC |
| `wc -l combat/state_effects.py` | ~320 LOC |

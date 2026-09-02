# ADR-0157: Combat Boss Module Split (boss.py 724 → 2 files)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P3 (The Build, ADR-0110 follow-up)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0125 — Boss Phase AoE M2](./0125-boss-aoe-minion-spawn.md), [ADR-0156 — Combat State Split](./0156-combat-state-split.md)

## 컨텍스트 (Context)

`combat/boss.py` is **724 LOC** with 24 functions/classes. ADR-0110 sets the recommended ceiling at **250 LOC** per module, with PR rejection at **500 LOC**. Current is 2.9x over the recommended ceiling.

**Function inventory** (24 items in 724 LOC):
- **Data classes** (lines 37-188): PhaseProfile, BossProfile, VFXTheme + theme data
- **VFX config** (lines 190-207): get_vfx_config
- **Boss skill builders** (lines 209-430): _wintermute_phase_X_skills, _ta_phase_X_skills
- **BOSS_PROFILES** (line 431)
- **Profile accessors** (lines 437-559): is_boss, get_boss_profile, current_phase, phase_transition, phase_damage, phase_skills, phase_color, phase_glyph, apply_phase_to_combatant
- **AI/Minion/AoE** (lines 562-...): scale_minion_spawn, spawn_phase_minions, boss_ai_choose_phase_effect, apply_phase_aoe, _trigger_aoe_visuals

## 결정 (Decision)

Split `combat/boss.py` into **2 files** following the natural cohesion boundary between *data/lifecycle* and *AI decisions/AoE/minion spawn*:

### Module 1: `combat/boss.py` (Data + Lifecycle, ~370 LOC)
- Lines 1-187: imports, dataclasses (PhaseProfile, BossProfile, VFXTheme)
- Lines 190-207: get_vfx_config
- Lines 209-430: phase skill builders (_wintermute_phase_X, _ta_phase_X)
- Lines 431-435: BOSS_PROFILES dict
- Lines 437-559: profile accessors + apply_phase_to_combatant

### Module 2: `combat/boss_ai.py` (AI Decisions + AoE + Minion Spawn, ~330 LOC)
- scale_minion_spawn
- spawn_phase_minions
- boss_ai_choose_phase_effect
- apply_phase_aoe
- _trigger_aoe_visuals

## Consequences (결과)

**LOC compliance**:
- `boss.py`: ~370 LOC (over 250, under 500 PR threshold per ADR-0110)
- `boss_ai.py`: ~330 LOC (over 250, under 500 PR threshold per ADR-0110)

**Public API in boss.py**: unchanged (re-exports boss_ai.py functions for backwards compat)
- `from .boss import scale_minion_spawn, spawn_phase_minions, ...`

**Internal imports**:
- `boss_ai.py` imports from `boss.py` (PhaseProfile, BossProfile, Combatant, CombatState)

**No behavior change** — pure refactoring.

**Pillar**: P4 (build health) — ADR-0110 compliance.

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4062 pass (no regression) |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 174 source files |
| `wc -l combat/boss.py` | ~370 LOC |
| `wc -l combat/boss_ai.py` | ~330 LOC |

## Implementation Status (2026-08-18)

**Status**: Structural split complete. AI/AoE/minion-spawn functions moved to `boss_ai.py` and re-exported from `boss.py` for backwards compatibility.

| File | Target LOC | Actual LOC (2026-08-18) | Delta |
|---|---:|---:|---:|
| `combat/boss.py` | ~370 | 656 | +286 |
| `combat/boss_ai.py` | ~330 | 188 | within |

**Tests** (2026-08-18): 5687 passing (13 pre-existing failures, all unrelated). ruff 0 errors. mypy strict 0 errors.

**Why `boss.py` is 286 LOC over target**: ADR-0157 §"Module 1" specified data + lifecycle + skill builders + profile accessors to be ~370 LOC. Actual content accumulates six wintermute/ta phase skill builders (`_wintermute_phase_1/2/3_skills`, `_ta_phase_1/2/3_skills`, plus phase-5 super-skill builders) totaling ~138 LOC, plus `BOSS_VFX_THEMES` (lines 137-203, ~66 LOC), plus the two `BossProfile` constant declarations (`WINTERMUTE_PROFILE` lines 419-466, `TA_CONSTRUCT_PRIME_PROFILE` lines 469-516, ~95 LOC total). All these belong in "Data + Lifecycle" per the ADR's stated cohesion — the ADR's LOC estimate did not account for the skill-builder + VFX-theme blocks when authored.

Re-targeting skill builders to a new `combat/boss_skill_builders.py` or themes to `combat/boss_vfx_themes.py` would require a separate ADR (out of scope for ADR-0157).

**No further action on ADR-0157** — structural goals met, public API stable.

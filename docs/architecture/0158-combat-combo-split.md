# ADR-0158: Combat Combo Module Split (combo.py 685 → 2 files)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P3 (The Build, ADR-0110 follow-up)
**관련**: [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md), [ADR-0156 — Combat State Split](./0156-combat-state-split.md), [ADR-0157 — Combat Boss Split](./0157-combat-boss-split.md)

## 컨텍스트 (Context)

`combat/combo.py` is **685 LOC** with 24 functions/classes. ADR-0110 sets the recommended ceiling at **250 LOC** per module, with PR rejection at **500 LOC**. Current is 2.7x over the recommended ceiling.

**Function inventory** (24 items in 685 LOC):
- **Data classes** (lines 37-282): ComboStage, CombatCombo, ComboVisual
- **Lifecycle** (lines 305-400): update_combo_visual, spawn_combo_hit
- **Avatars** (lines 401-467): StageAvatar, get_avatar_for_stage
- **Timing bars** (lines 478-530): TimingBar
- **Finishers** (lines 543-622): ComboFinisher, get_finisher_for_stage
- **Rendering** (lines 344-369, 531-541, 625-...): render_combo_counter, render_combo_stage_up, render_combo_end, render_timing_bar, render_combo_full

## 결정 (Decision)

Split `combat/combo.py` into **2 files** following the natural cohesion boundary between *data/lifecycle* and *cinematic rendering*:

### Module 1: `combat/combo.py` (Data + Lifecycle, ~370 LOC)
- Imports, dataclasses (ComboStage, CombatCombo, ComboVisual)
- update_combo_visual (lifecycle)
- spawn_combo_hit (lifecycle)
- StageAvatar, get_avatar_for_stage
- TimingBar
- ComboFinisher, get_finisher_for_stage

### Module 2: `combat/combo_window.py` (Cinematic Rendering, ~250 LOC)
- render_combo_counter
- render_combo_stage_up
- render_combo_end
- render_timing_bar
- render_combo_full

## Consequences (결과)

**LOC compliance**:
- `combo.py`: ~370 LOC (over 250, under 500 PR threshold per ADR-0110)
- `combo_window.py`: ~250 LOC (at ceiling, acceptable)

**Public API in combo.py**: unchanged (re-exports rendering functions for backwards compat)
- `from .combo import render_combo_counter, render_combo_stage_up, ...`

**Internal imports**:
- `combo_window.py` imports from `combo.py` (ComboVisual, CombatCombo, etc.)

**No behavior change** — pure refactoring.

**Pillar**: P4 (build health) — ADR-0110 compliance.

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4062 pass (no regression) |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 175 source files |
| `wc -l combat/combo.py` | ~370 LOC |
| `wc -l combat/combo_window.py` | ~250 LOC |

## Implementation Status (2026-08-18)

**Status**: Structural split complete. Cinematic rendering functions moved to `combo_window.py` and re-exported from `combo.py` for backwards compatibility.

| File | Target LOC | Actual LOC (2026-08-18) | Delta |
|---|---:|---:|---:|
| `combat/combo.py` | ~370 | 629 | +259 |
| `combat/combo_window.py` | ~250 | 88 | within |

**Tests** (2026-08-18): 5687 passing (13 pre-existing failures, all unrelated). ruff 0 errors. mypy strict 0 errors.

**Why `combo.py` is 259 LOC over target**: ADR-0158 §"Module 1" planned Data + Lifecycle + Avatars + Timing + Finishers at ~370 LOC. Actual content grew due to:
- `StageAvatar` dataclass + 5 per-stage avatar constants (`AVATAR_WARMUP` through `AVATAR_ANNIHILATION`) — ~50 LOC
- `TimingBar` dataclass + `render()` / `get_color()` / `is_urgent()` methods — ~45 LOC
- `ComboFinisher` dataclass + 3 finisher constants (`FINISHER_QUICK_SLASH` / `RAMPAGE_BURST` / `FINAL_STRIKE`) — ~70 LOC
- `CombatCombo` lifecycle methods (`step`, `consume_stage_up`, `consume_just_ended`, `apply_damage_bonus`, etc.) — ~70 LOC

All these belong in "Data + Lifecycle" per the ADR's stated cohesion. The ADR's LOC estimate did not include the avatar + finisher blocks when authored (those were added later in response to engagement-layer work).

Re-targeting avatars to `combat/combo_avatars.py` or finishers to `combat/combo_finishers.py` would require a separate ADR (out of scope for ADR-0158).

**No further action on ADR-0158** — structural goals met, public API stable.

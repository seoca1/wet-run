# ADR-0171: ASCII Battle Portrait Evolution

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 5 style, Pillar 3 visual feedback)
**관련**: [ADR-0011 — ASCII Portraits](./0011-ascii-portraits.md), [ADR-0160 — Status Effects System](./0160-status-effects-system.md), [ADR-0168 — Death Taunts](./0168-death-taunts.md), [ADR-0170 — Gibson Fluff Library](./0170-gibson-fluff-library.md)

## 컨텍스트 (Context)

Current ASCII battle portraits are static — a single glyph per ICE type
that doesn't change during combat. After v1.2.0+ Polish added status
effects (burn, stun, slow, silence, vulnerability), players have no
visual feedback for these states on the portrait.

Track D.5 adds **portrait evolution** — the ASCII portrait changes based
on combat state:
- HP thresholds (full, healthy, wounded, critical, dying)
- Status effects (burn glow, stun shake, slow trail, silence cross-out)
- Phase progression (boss portraits change color per phase)

## 결정 (Decision)

### Portrait schema

```python
@dataclass(frozen=True, slots=True)
class BattlePortrait:
    base_glyph: str
    color: tuple[int, int, int]
    effect_overlay: str = ""
    suffix: str = ""
```

### Implementation surface

**`combat/battle_portraits.py`** (NEW):
- `get_portrait(ice_type, hp_ratio, statuses, phase) -> BattlePortrait`
- `get_hp_threshold(ratio) -> str` — full/healthy/wounded/critical/dying
- `get_status_overlay(statuses) -> str` — burn/stun/slow/silence icons
- `PORTRAIT_EVOLUTION_RULES: dict` — evolution config

**`tests/unit/test_battle_portraits.py`** (NEW):
- 10+ tests covering HP thresholds, status overlays, boss phase colors.

## Consequences (결과)

**Pillar 3 (The Flatline)**: Visual feedback for damage states — players see when ICE is dying.

**Pillar 5 (The Style)**: ASCII portriats evolve with combat — WINTERMUTE phase 4 shows different glyph than phase 1.

**Test additions**: ~10 tests.

## Implementation Status (2026-08-20)

**Status**: 🟡 Partial (library complete; render-path integration pending)

**Evidence**:
- `prototype/src/wet_run/combat/battle_portraits.py:15` — `BattlePortrait` frozen dataclass (base_glyph, color, effect_overlay, suffix)
- `prototype/src/wet_run/combat/battle_portraits.py:24` — `HP_THRESHOLDS` dict (full=0.95 / healthy=0.7 / wounded=0.4 / critical=0.2 / dying=0.0)
- `prototype/src/wet_run/combat/battle_portraits.py:32` — `ICE_PORTRAITS` glyph dict for 10 ICE types (watchdog/goliath/black/construct/standard/patrol/hunter/wintermute/ta_construct_prime/neuromancer)
- `prototype/src/wet_run/combat/battle_portraits.py:45` — `ICE_COLORS` per-type base colors
- `prototype/src/wet_run/combat/battle_portraits.py:58` — `BOSS_PHASE_COLORS` per-phase evolution for wintermute (4 phases) and ta_construct_prime (4 phases) — glyph+color shifts per phase
- `prototype/src/wet_run/combat/battle_portraits.py:74` — `get_hp_threshold(ratio)` returns one of 5 buckets
- `prototype/src/wet_run/combat/battle_portraits.py:87` — `get_color_for_threshold(ice_type, threshold)` darkens base color by 0.8/0.6/0.4, dying = pure red
- `prototype/src/wet_run/combat/battle_portraits.py:106` — `get_status_overlay(status_effect_ids)` composes icons (^=burn, ~=stun, ...=slow, X=silence, !=vulnerable)
- `prototype/src/wet_run/combat/battle_portraits.py:122` — `get_glyph_for_threshold(ice_type, threshold)` mutates glyph per threshold (lowercase for dying, "*" suffix for critical)
- `prototype/src/wet_run/combat/battle_portraits.py:132` — `get_portrait(ice_type, hp_ratio, status_effect_ids, phase)` top-level assembler returns `BattlePortrait`
- `prototype/tests/unit/test_battle_portraits.py:1` — 183 LOC covering HP thresholds, status overlays, boss phase colors, glyph evolution

**Notes**: Module is internally complete and exceeds spec in coverage (10 ICE types + 2 boss phase progressions). Spec's `PORTRAIT_EVOLUTION_RULES: dict` was split into the more focused `HP_THRESHOLDS` + `ICE_PORTRAITS` + `ICE_COLORS` + `BOSS_PHASE_COLORS` tables for clarity. However, **the render path still uses static `enemy.portrait` from `Combatant`**: `engine/combat_view_render.py:255` does `console.print(x=x, y=y, string=enemy.portrait, fg=enemy.color)` directly, with no call to `get_portrait()` or to update the portrait based on HP/status/phase. The `BattlePortrait` assembler is never called by the rendering code. `cinematic_art.py:get_portrait` is an unrelated function (graphic-novel scene art).

**Open items**: Wire `get_portrait(enemy.ice_type, enemy.hp / enemy.max_hp, tuple(s.effect_id for s in enemy.statuses), current_boss_phase)` into `engine/combat_view_render.py:255` in place of the static `enemy.portrait`; also use the resulting color/overlay instead of `enemy.color` directly; ensure combat-state tick updates portrait (or compute on render).

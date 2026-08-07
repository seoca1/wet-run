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

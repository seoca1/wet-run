# ADR-0173: Wetware Augments (6 Passive Slots)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 4 Build depth)
**관련**: [ADR-0008 — Progression Tier T1–T6](./0008-progression-system.md), [ADR-0172 — Cyberdeck Customization](./0172-cyberdeck-customization.md)

## 컨텍스트 (Context)

Track E.1 added Cyberdeck (8 program slots). Players need a second
dimension of build: **wetware augments** — passive effects from
equipped cyberware. Augments are TOOLS (per Pillar 4), not stat boosts.

Track E.2 introduces **Wetware Augments** — 6 passive slots, 20+ augments.
Each augment provides a passive effect (extra AP regen, shield on hit,
crit bonus, etc.).

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class WetwareAugment:
    """A passive cyberware augment."""
    id: str
    name: str
    description: str
    effect_type: str  # "ap_regen", "shield_on_hit", "crit_bonus", etc.
    effect_value: float

DEFAULT_AUGMENT_SLOTS = 6
```

### Public API

```python
# combat/augments.py
def create_augment(id: str, name: str, ...) -> WetwareAugment
def get_augment(id: str) -> WetwareAugment | None
def list_augments() -> tuple[WetwareAugment, ...]
def apply_augment_effect(state, augment: WetwareAugment) -> None
```

### 20+ Augments (initial set)

| ID | Effect | Type |
|---|---|---|
| adrenal_boost | AP regen +1 | active |
| reflex_boost | Speed +10% | passive |
| kerenzikov | Slow time on combat | active |
| sandevistan | Slow time on damage | active |
| berserk_core | Crit +10% at low HP | passive |
| optical_camo | Dodge +15% | passive |
| pain_editor | Damage threshold -10% | passive |
| bioconductor | Healing +25% | passive |
| titanium_bones | Max HP +20 | passive |
| subdermal_armor | Shield +1/hit | passive |
| gorilla_fists | Melee +30% | passive |
| projectile_launcher | Range +20% | passive |
| cyberdeck_boost | AP +2 max | passive |
| quickhack_boost | Hack speed +20% | active |
| stealth_oxide | Stealth +25% | passive |
| nanowire | Crit +5% | passive |
| biowire | AP regen +2 | passive |
| missile_launcher | AoE +20% | passive |
| optical_camouflage | Detection -30% | passive |
| reinforced_skin | Bleed resist | passive |
| adaptive_immunity | Slow immunity | passive |

## Consequences (결과)

**Pillar 4 (Build)**: Two-dimensional build (programs + augments). Meaningful choices.

**Tests**: 10+ tests covering augment registry, application, effects.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/augments.py:11` — `DEFAULT_AUGMENT_SLOTS = 6` (ADR exact match)
- `prototype/src/wet_run/combat/augments.py:15` — `class WetwareAugment` dataclass (frozen, slots) with `id/name/description/effect_type/effect_value`
- `prototype/src/wet_run/combat/augments.py:29-49` — registry contains 21 augment instances (adrenal_boost, reflex_boost, kerenzikov, sandevistan, berserk_core, optical_camo, pain_editor, bioconductor, titanium_bones, subdermal_armor, gorilla_fists, projectile_launcher, cyberdeck_boost, quickhack_boost, stealth_oxide, nanowire, biowire, missile_launcher, optical_camouflage, reinforced_skin, adaptive_immunity) — exceeds ADR's "20+ Augments" target
- `prototype/src/wet_run/combat/augments.py:62` — `get_augment(augment_id) -> WetwareAugment | None`
- `prototype/src/wet_run/combat/augments.py:67` — `list_augments() -> tuple[WetwareAugment, ...]`
- `prototype/src/wet_run/combat/augments.py:92` — `apply_augment_effect(augment, attr)` (signature drift: ADR specifies `(state, augment)`; impl returns float via attr lookup — semantics retained)
- `prototype/tests/unit/test_augments.py` — **17 tests** collected (ADR target: 10+)

**Notes**: All ADR-spec public APIs implemented. The 21 named augments exactly cover the ADR's full ID list. `apply_augment_effect` signature differs from ADR spec but functional intent (compute attribute modifier from augment) is preserved. Note: `equipment/wetware.json` carries a separate equipment-augment track (10 entries with lv1/lv2/lv3 stacks) per ADR-0193, not related to the WetwareAugment registry here.

**No further action on ADR-0173** — implementation closed, public API stable, tests passing.
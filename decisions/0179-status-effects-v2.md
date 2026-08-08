# ADR-0179: Status Effects v2 (Bleed, Fatigue, Confused, Terrified)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 3 depth)
**관련**: [ADR-0160 — Status Effects System](./0160-status-effects-system.md), [ADR-0148 — Combat Depth Expansion](./0148-combat-depth-expansion.md), [ADR-0161 — ICE Personality Archetypes](./0161-ice-personality-archetypes.md)

## 컨텍스트 (Context)

Current status effects (ADR-0160) are 5 (DoT, Stun, Slow, Silence, Vulnerability).
Track F.3 adds **4 more effects** for deeper combat:

- **Bleed**: HP loss over time, ignores shield
- **Fatigue**: AP regen -50%
- **Confused**: 25% chance skill hits wrong target
- **Terrified**: damage taken +25%, ICE becomes aggressive vs player

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class StatusEffectV2:
    id: str
    name: str
    effect_type: str  # "bleed", "fatigue", "confused", "terrified"
    duration_ms: int
    value: float
```

### Effects

| Effect | Effect Type | Value | Duration |
|---|---|---|---|
| Bleed | `bleed` | 5 HP/tick | 5000 ms |
| Fatigue | `fatigue` | -0.5 AP regen | 8000 ms |
| Confused | `confused` | 0.25 miss-chance | 6000 ms |
| Terrified | `terrified` | +0.25 damage taken | 4000 ms |

### Public API

```python
# combat/status_effects_v2.py
def get_status_v2(effect_id: str) -> StatusEffectV2 | None
def list_status_v2() -> tuple[StatusEffectV2, ...]
def get_status_v2_by_type(effect_type: str) -> tuple[StatusEffectV2, ...]
def apply_bleed(target: Combatant, duration_ms: int) -> StatusEffectV2
def apply_fatigue(target: Combatant, duration_ms: int) -> StatusEffectV2
def apply_confused(target: Combatant, duration_ms: int) -> StatusEffectV2
def apply_terrified(target: Combatant, duration_ms: int) -> StatusEffectV2
```

## Consequences (결과)

**Pillar 3 (Flatline)**: More debuff states — death weight amplifies.

**Pillar 4 (Build)**: Antivirus / cleanse augments become valuable.

**Tests**: 10+ tests covering each effect type, registry, helpers.
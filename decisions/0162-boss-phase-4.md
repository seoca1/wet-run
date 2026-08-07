# ADR-0162: Boss Phase 5 Last Stand

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 climax, Pillar 5 finale)
**관련**: [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0157 — Combat Boss Split](./0157-combat-boss-split.md), [ADR-0159 — Combat Bosses Cinematic Split](./0159-combat-bosses-split.md)

## 컨텍스트 (Context)

BOSS fights currently cap at Phase 3 (Wintermute/T-A Construct Prime). The "finale" moment is when you deal the killing blow — no scripted climax sequence, no last words, no final super-skill.

Track B.4 adds **Phase 4 — "Last Stand"** as a scripted post-Phase-3 finale:
- Triggered when boss HP drops below 10% after Phase 3
- Boss delivers a final dialogue line (Gibson "I am the interface" / "the family votes")
- Boss fires one super-skill before dying
- Cinematic sequence with screen flash + slow-motion

## 결정 (Decision)

### Phase 4 trigger

```python
def should_trigger_phase_4(boss: Combatant, current_phase: BossPhase) -> bool:
    """Phase 4 triggers when in phase 3, HP < 10%, and phase4_super_skill configured."""
    if current_phase.index != 3:
        return False
    if boss.max_hp <= 0:
        return False
    if current_phase.phase4_super_skill is None:
        return False
    return boss.hp / boss.max_hp < 0.10
```

### Phase 4 schema

```python
@dataclass(frozen=True, slots=True)
class PhaseProfile:
    # ... existing fields ...
    phase4_super_skill: Skill | None = None
    phase4_dialogue: str = ""
    phase4_damage_multiplier: float = 3.0
```

### Implementation surface

- `combat/boss.py`: PhaseProfile adds 3 new fields. WINTERMUTE_PROFILE and TA_CONSTRUCT_PRIME_PROFILE get Phase 4 data populated.
- `combat/bosses.py`: `should_trigger_phase_4` function added.
- `combat/bosses_cinematic.py`: `boss_phase_4_sequence` + `spawn_boss_phase4` added.
- `tests/unit/test_boss_phase_4.py`: 12 new tests covering trigger, cinematic, super-skill.

## Consequences (결과)

**Pillar 1 (The Run)**: Climax gets a final beat — Phase 4 is "this is it" moment. Boss drops one final speech, fires a super-skill, then dies.

**Pillar 3 (The Flatline)**: Phase 4 is asymmetric — boss is dying but gets one free super-skill shot. Weight preserved.

**Pillar 5 (The Style)**: Phase 4 dialogue uses Gibson "I am the interface" / "we are the message" tone.

**Test additions**: 12 new tests covering trigger conditions, cinematic content, super-skill application, profile data.

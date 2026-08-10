# ADR-0187: Boss Phase 5 Expansion (Last Stand)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 climax, Pillar 5 finale)
**관련**: [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0157 — Combat Boss Split](./0157-combat-boss-split.md), [ADR-0159 — Combat Bosses Cinematic Split](./0159-combat-bosses-split.md)

## 컨텍스트 (Context)

BOSS fights currently cap at Phase 4 (per ADR-0149: Wintermute phase 3
spawns minions, T-A phase 3 lifesteals). Phase 4 was the "finale"
climax. After 4 phases, the boss is dead. Players reach the scripted
climax via HP thresholds.

Track B.4 adds **Phase 5 — "Last Stand"** as a *post-Phase-4-finale mode*:
- Triggered when boss HP drops below 10% after Phase 4
- Boss enters a single, dramatic, scripted sequence before death
- Uses 1 super-skill + 1 final dialogue line
- Game-over vs. victory weight preserved (Pillar 3)

This is *in addition to* Phase 4 — Phase 4 may have retired sub-mechanics;
Phase 5 is the FINAL death rattle.

## 결정 (Decision)

### Phase 5 trigger

```python
def trigger_phase_5(boss: Combatant, profile: BossProfile) -> bool:
    """Phase 5 = Last Stand (HP < 10%, after Phase 4)."""
    return (
        boss.current_phase == 4
        and boss.hp / max(1, boss.max_hp) < 0.10
    )
```

### Phase 5 schema

```python
@dataclass(frozen=True, slots=True)
class PhaseProfile:
    # ... existing fields ...
    phase5_super_skill: Skill | None = None  # NEW: scripted final skill
    phase5_dialogue: str = ""  # NEW: last words before death
    phase5_damage_multiplier: float = 3.0  # NEW: 200%+ damage spike
```

### Implementation surface

**`combat/boss.py`** (modify):
- `PhaseProfile` adds 3 new fields (phase5_super_skill, phase5_dialogue, phase5_damage_multiplier).
- `WINTERMUTE_PROFILE` and `TA_CONSTRUCT_PRIME_PROFILE` get phase 5 data populated.

**`combat/bosses.py`** (modify):
- `get_next_phase` recognizes Phase 5 trigger.
- `apply_phase_to_combatant` declares Phase 5 entry.

**`combat/bosses_cinematic.py`** (modify):
- New `boss_phase_5_sequence` builder for the Last Stand cinematic.
- `spawn_boss_phase5` spawner.

**`combat/__init__.py`** (re-export):
- `boss_phase_5_sequence`, `spawn_boss_phase5`.

## Consequences (결과)

**Pillar 1 (The Run)**: Climax gets a *final beat* — Phase 5 is the
"this is it" moment. Boss gives one last speech, fires one last
super-skill, then dies.

**Pillar 3 (The Flatline)**: Phase 5 is asymmetric — boss is dying
but gets one free super-skill shot. Weight preserved.

**Pillar 5 (The Style)**: Phase 5 dialogue uses Gibson "I am the
interface" / "we are the message" tone.

**Test additions**: ~12 new tests covering:
- Phase 5 trigger conditions
- Super-skill application
- Phase 5 cinematic text
- SP-only behavior (no defense skills)

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4101 + ~12 = ~4113 pass |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 180+ source files |

# ADR-0162: Boss Phase 4 Last Stand

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

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented (with superset coverage)

**Evidence**:
- `prototype/src/wet_run/combat/boss_phase4/__init__.py:1` — public package re-exporting `should_trigger_phase4`, `trigger_phase4`, `apply_personality_drift`, `apply_family_vote`, `apply_construct_merge`, `apply_ground_slam`, `apply_glitch_burst`, `apply_phase4_mechanic`, `boss_intro_text`, `taunt_for`
- `prototype/src/wet_run/combat/boss_phase4/trigger.py:22` — `PHASE4_HP_THRESHOLD = 0.15` (15% per ADR-0149 cycle 5, tightened from spec's 10%)
- `prototype/src/wet_run/combat/boss_phase4/trigger.py:35` — `should_trigger_phase4(boss, max_boss_hp)` (HP-fraction check)
- `prototype/src/wet_run/combat/boss_phase4/trigger.py:44` — `trigger_phase4(state, app_state, boss_id)` (one-shot flag guard)
- `prototype/src/wet_run/combat/boss_phase4/mechanics.py:45` — `apply_personality_drift` (Wintermute)
- `prototype/src/wet_run/combat/boss_phase4/mechanics.py:66` — `apply_family_vote` (T-A Prime)
- `prototype/src/wet_run/combat/boss_phase4/mechanics.py` — also `apply_construct_merge` (Neuromancer), `apply_ground_slam` (Goliath), `apply_glitch_burst` (Black ICE Lord) — 5 bosses vs spec's 2
- `prototype/src/wet_run/combat/boss_phase4/intro.py:35` — `BOSS_INTRO` dict with 3-stage intro per boss
- `prototype/src/wet_run/combat/boss_phase4/taunts.py` — `taunt_for(boss_id)` returns Gibson death taunt
- `prototype/tests/unit/test_boss_phase4.py:1` — 495 LOC covering trigger, mechanics, intro, taunts
- `prototype/tests/unit/test_boss_phase_5.py:1` — 158 LOC (v1.2.0+ super-skills follow-up)
- `prototype/tests/unit/test_f4_boss_phase_combat.py:1` — 504 LOC end-to-end combat integration

**Notes**: Implementation went above spec: 5 bosses (Wintermute/TA/Neuromancer/Goliath/Black ICE) with distinct mechanics, plus 3-stage intro overlay (ADR-0149 cycle 5 deliverables). HP threshold is 15% (ADR-0149) rather than spec's 10%, both per ADR-0149 §Consequences.7. Profile dataclass kept in dedicated `boss_phase4/mechanics.py` constants rather than mutating `combat/boss.py::PhaseProfile` — cleaner separation per ADR-0150 split principle.

**No further action on ADR-0162** — implementation closed.

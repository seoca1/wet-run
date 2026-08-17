# ADR-0161: ICE Personality Archetypes (4 behaviors beyond aggression)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 5 variety, Pillar 3 weight via different pressure)
**관련**: [ADR-0148 — Combat Depth Expansion](./0148-combat-depth-expansion.md), [ADR-0150 — Module Split depth.py + boss_phase4.py](./0150-module-split-depth-boss-phase4.md), [ADR-0152 — Multi-Enemy Encounters](./0152-multi-enemy-encounters.md), [ADR-0160 — Status Effects System](./0160-status-effects-system.md)

## 컨텍스트 (Context)

`combat/depth/aggression.py` already provides 4 aggression tiers (PASSIVE /
STANDARD / AGGRESSIVE / BOSS) that determine *skill use probability*
per tick. The system has no behavioral differentiation beyond that —
every ICE uses its highest-damage skill first regardless of situation.

Track B.3 adds depth via **4 personality archetypes** that influence:
1. **Skill selection** (which skill to use, not just probability)
2. **Target selection** (which enemy to heal/buff, self vs others)
3. **State reactions** (panic when low HP, defensive recovery)
4. **Pressure dynamics** (alarm generation, status-effect application)

The existing aggression tier is *orthogonal* to personality — an ICE
can be BOSS-tier aggression **and** DEFENSIVE personality (defensive
raid boss). The personality layer adds strategic depth.

## 결정 (Decision)

### Personality archetypes (4 distinct behaviors)

| Personality | Behavior | Skill preference | Special |
|---|---|---|---|
| **AGGRESSIVE** | Constant offense, high skill use | damage/heavy_attack/pierce | +5% crit chance |
| **DEFENSIVE** | Self-preservation, prefer shields when HP < 50% | shield/buff/heal | Triggers shield when HP < 50% |
| **STEALTH** | Low alarm, prefer evade/silence | silence/slow | Alarm generation × 0.5 |
| **SUPPORT** | Buff allies, prefer heal/buff | heal/buff/shield | Targets other ICE first (in multi-enemy) |

### Schema addition

```python
# In combat/state_models.py
class Combatant:
    # ... existing fields ...
    personality: str = "aggressive"  # one of: aggressive, defensive, stealth, support
```

### Implementation surface

**`combat/depth/personality.py`** (NEW):
- `PersonalityLevel(StrEnum)`: AGGRESSIVE / DEFENSIVE / STEALTH / SUPPORT
- `PERSONALITY_BEHAVIORS: dict[str, dict[str, any]]` — config table
- `select_skill_by_personality(combatant, available_skills, state) -> Skill | None`
- `should_defensive_act(combatant) -> bool` — True if HP < 50% and is DEFENSIVE
- `get_alarm_multiplier(combatant) -> float` — 0.5 for STEALTH, 1.0 otherwise
- `should_target_ally(combatant, state) -> bool` — True if SUPPORT and allies wounded

**`combat/state_transitions.py`** (modify):
- `_tick_alarm` applies `get_alarm_multiplier(state.target)` — STEALTH alarm × 0.5
- `step_combat` skill selection uses `select_skill_by_personality`

**`combat/state.py`** (modify):
- `_calculate_damage` applies `+5% crit chance` for AGGRESSIVE defender

### Public API additions

```python
from wet_run.combat.depth.personality import (
    PersonalityLevel,
    select_skill_by_personality,
    should_defensive_act,
    get_alarm_multiplier,
    should_target_ally,
)
```

## Consequences (결과)

**Pillar 1 (The Run)**: Behavioral variety within tiers — same
aggression, different feel (aggressive Wintermute vs defensive Wintermute).

**Pillar 3 (The Flatline)**: STEALTH reduces alarm weight (Pillar 3
preserved — alarm still ticks, just slower); DEFENSIVE gives ICE
survivability → harder kills.

**Pillar 4 (The Build)**: Defensive ICE is more survivable but
less aggressive — natural skill selection over time.

**Pillar 5 (The Style)**: Per-ICE behavior creates "personality" —
each ICE archetype feels distinct.

**Test additions**: ~20 new tests covering:
- Each personality's skill selection
- DEFENSIVE shield trigger at HP threshold
- STEALTH alarm reduction
- SUPPORT target selection
- AGGRESSIVE crit bonus

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4081 + ~20 new = ~4101 pass |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 179+ source files |
| `wc -l combat/depth/personality.py` | ~150 LOC (new module) |

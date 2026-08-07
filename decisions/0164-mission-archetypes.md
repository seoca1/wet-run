# ADR-0164: Mission Archetypes (4 mission types)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (Pillar 1 run variety)
**관련**: [ADR-0051 — Mission Story Metadata](./0051-mission-story-metadata.md), [ADR-0061 — Novel Integration Architecture](./0061-novel-integration-architecture.md), [ADR-0163 — Run Mutators](./0163-run-mutators.md)

## 컨텍스트 (Context)

Current missions are all "extract data" or "defeat ICE" — there's
no mission variety. Players encounter the same flow regardless of
job type. After v1.2.0+ Polish added salvage trade-offs, info items,
and multi-enemy, the game can support **mission archetypes** that change
the rules per-mission.

Track C.2 adds 4 mission archetypes:

| Archetype | Rules | Pillar Impact |
|---|---|---|
| **STEALTH** | No-kill detection bonus; kills increase alarm | P1 (avoidance), P5 (nyromancer) |
| **RACE** | Time limit (45s); bonus for fast clear | P1 (pressure), P4 (build) |
| **EXTRACTION** | Multi-objective; partial success pays | P1 (flexibility), P4 (build) |
| **DEFENSE** | Protect friendly node; survive waves | P1 (tactical), P5 (sentiment) |

## 결정 (Decision)

### Archetype schema

```python
class MissionArchetype(StrEnum):
    STEALTH = "stealth"
    RACE = "race"
    EXTRACTION = "extraction"
    DEFENSE = "defense"


@dataclass(frozen=True, slots=True)
class MissionArchetypeConfig:
    id: MissionArchetype
    name: str
    description: str
    icon: str
    rules: dict[str, str]
```

### Application point

Archetypes are applied at **mission start** (after job select, before
matrix entry). The AppState / CombatState carries the active archetype:

```python
@dataclass
class AppState:
    # ... existing fields ...
    active_archetype: MissionArchetype | None = None
```

### Implementation surface

**`combat/mission_archetypes.py`** (NEW):
- `MissionArchetype` enum + `MissionArchetypeConfig`
- `MISSION_ARCHETYPES: dict[MissionArchetype, MissionArchetypeConfig]`
- `apply_archetype(app_state, archetype)` — sets active
- `clear_archetype(app_state)` — clears
- `is_archetype_active(app_state, archetype) -> bool`
- `get_archetype_rules(app_state) -> dict[str, str]`

**`tests/unit/test_mission_archetypes.py`** (NEW):
- 12+ tests covering apply, clear, rules, integration.

## Consequences (결과)

**Pillar 1 (The Run)**: Each mission has distinct rules — players
adapt their build to the archetype.

**Pillar 4 (The Build)**: Archetypes force creative use of skills
(STEALTH rewards avoidance, RACE rewards burst, DEFENSE rewards shields).

**Pillar 5 (The Style)**: Archetype names use Gibson tone ("STEALTH — move like wintermute").

**Test additions**: ~12 tests covering application, clearing, rules.

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4130 + ~12 = ~4142 pass |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 180+ source files |

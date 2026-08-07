# ADR-0167: Mission Expansion (15 → 25 missions)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 content variety, Pillar 5 progression)
**관련**: [ADR-0051 — Mission Story Metadata](./0051-mission-story-metadata.md), [ADR-0061 — Novel Integration Architecture](./0061-novel-integration-architecture.md), [ADR-0166 — Phase 6 Arc](./0166-phase-6-arc.md)

## 컨텍스트 (Context)

The current game has 15 missions. Per the CONTENT_EXPANSION_PLAN.md, the
target is 30+ missions for 10+ hours of playtime. After Phase 6 Arc
(4 missions in Aftermath zone), we have 15 + 4 = 19 missions. Track C.5
adds 6 more mid-tier missions to reach 25 total.

New missions fill the Novice/Veteran/Heretic gap:

| # | ID | Difficulty | Zone | Theme |
|---|---|---|---|---|
| 16 | hosaka_after_hours | novice | mid | Corporate espionage |
| 17 | sense_net_infiltration | veteran | mid | ICE-heavy data heist |
| 18 | yakuza_meeting | veteran | mid | Social/intimidation |
| 19 | t_a_construction_site | heretic | core | T-A adjacent |
| 20 | zion_lab_breach | heretic | core | Zion adjacent |
| 21 | construct_market | novice | surface | Pawn shop |

## 결정 (Decision)

### Mission schema

```python
@dataclass(frozen=True, slots=True)
class ExpansionMission:
    id: str
    name: str
    difficulty: str
    zone: str
    description: str
    story_intro: str
    primary_ice: tuple[str, ...]
```

### Implementation surface

**`combat/mission_expansion.py`** (NEW):
- `EXPANSION_MISSIONS: tuple[ExpansionMission, ...]` — 6 missions
- `get_expansion_mission(mission_id) -> ExpansionMission | None`
- `is_expansion_mission(mission_id) -> bool`
- `expansion_mission_count() -> int`
- `expansion_missions_by_difficulty(difficulty) -> tuple[ExpansionMission, ...]`

**`tests/unit/test_mission_expansion.py`** (NEW):
- 10+ tests covering registry, accessors, difficulty filter.

## Consequences (결과)

**Pillar 1 (The Run)**: 25 missions = ~9h playtime (target: 10h).

**Pillar 5 (The Style)**: Mission names use Gibson tone ("Hosaka After Hours — the suits are gone").

**Test additions**: ~10 tests.

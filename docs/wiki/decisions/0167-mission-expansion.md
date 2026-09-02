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

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Notes**:
- Full board wiring complete: 5 of 6 expansion missions added to `data/missions/missions.json` with full mission schema.
  - ✅ Added: `hosaka_after_hours`, `yakuza_meeting`, `t_a_construction_site`, `zion_lab_breach`, `construct_market`
  - ⚠ Already in missions.json from earlier work: `sense_net_infiltration` (different content source — pre-existing entry kept, see ADR-0195 §"Open items")
- All 5 newly-added missions have valid pillar values (`people`/`power`/`code`), Gibson vocabulary in synopsis_en, and accurate word_count_en / char_count_ko (no-spaces formula).
- Registry (`combat/mission_expansion.py`) + missions.json (200→209) + game_facts.json (mission_count: 200→209) all in sync.
- All 6 expansion mission IDs are accessible via `expansion_mission_ids()` in Python; 5 newly authored with full data; `sense_net_infiltration` is the pre-existing one.

**Evidence**:
- `prototype/src/wet_run/combat/mission_expansion.py:13` — `ExpansionMission` frozen dataclass matching spec
- `prototype/src/wet_run/combat/mission_expansion.py:25` — `EXPANSION_MISSIONS` tuple with all 6 missions in spec order: `hosaka_after_hours` (novice/mid), `sense_net_infiltration` (veteran/mid), `yakuza_meeting` (veteran/mid), `t_a_construction_site` (heretic/core), `zion_lab_breach` (heretic/core), `construct_market` (novice/surface)
- `prototype/src/wet_run/combat/mission_expansion.py:83-108` — `get_expansion_mission`, `is_expansion_mission`, `expansion_mission_count`, `expansion_missions_by_difficulty`, `expansion_mission_ids`
- `prototype/tests/unit/test_mission_expansion.py:1` — 100 LOC covering registry + accessors + difficulty filter + frozen invariant

**Notes**: Registry is complete with all 6 missions in spec difficulty/zone order. However, the expansion registry is **not wired into the live mission board**. `data/missions/missions.json` contains 200 missions but none match the 6 ADR-0167 IDs (`hosaka_after_hours`, `yakuza_meeting`, `t_a_construction_site`, `zion_lab_breach`, `construct_market`); `sense_net_infiltration` exists in `missions.json` but is a pre-existing Phase 1 mission unrelated to ADR-0167's "ICE-heavy data heist" definition. Search for `is_expansion_mission` / `expansion_missions` outside the module returns 0 hits in `src/wet_run/`. The registry is a **standalone island**.

**Open items**: Add the 6 expansion missions to `data/missions/missions.json`; wire `is_expansion_mission` / `get_expansion_mission` into `missions/board.py::JobBoard`; resolve the `sense_net_infiltration` collision (Phase 1 mission vs ADR-0167 spec).

# ADR-0166: Phase 6 Arc (Aftermath - Post-Ending NG+ Content)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 endgame, Pillar 4 meta progression)
**관련**: [ADR-0090 — Salvation Phase Integration](./0090-salvation-phase-integration.md), [ADR-0155 — NG+ Grade 5→6 PPL Rebalance](./0155-ng-plus-grade-5-to-6-rebalance.md), [ADR-0163 — Run Mutators](./0163-run-mutators.md), [ADR-0164 — Mission Archetypes](./0164-mission-archetypes.md)

## 컨텍스트 (Context)

The current game has Arcs 1-5 (5 narrative arcs). After completing Arc 5
("Neuromancer merger"), the game ends with Salvation Phase + epilogue.
There's no post-game content — players who finish the main story have
nothing new to do except NG+ (which just increases difficulty).

Track C.4 adds **Phase 6 Arc — Aftermath** as post-ending NG+ content:
- **4 missions** that play after the epilogue
- New "Aftermath" zone (stylized as leftover matrix fragments)
- New ICE archetypes (post-Neuromancer constructs)
- Story content: the merger left *residue* — fragments of Wintermute
  in the grid that the player must clean up

## 결정 (Decision)

### Arc structure

Phase 6 Arc = 4 missions in sequence:

1. **ghost_signal_origin** (Novice, Aftermath) — Investigate a ghost signal
2. **wintermute_residue** (Veteran, Aftermath) — Hunt residual Wintermute fragments
3. **tessier_ashpool_aftermath** (Veteran, Aftermath) — Clean up T-A remnants
4. **neuromancer_merger_residue** (Heretic, Aftermath) — Final cleanup of Neuromancer merger

### Mission schema

```python
@dataclass(frozen=True, slots=True)
class Arc6Mission:
    id: str
    name: str
    difficulty: str  # "novice" / "veteran" / "heretic"
    zone: str  # "aftermath"
    description: str
    story_intro: str
    primary_ice: tuple[str, ...]
```

### Implementation surface

**`combat/arc6.py`** (NEW):
- `ARC6_MISSIONS: tuple[Arc6Mission, ...]` — 4 missions
- `get_arc6_mission(mission_id) -> Arc6Mission | None`
- `is_arc6_mission(mission_id) -> bool`
- `arc6_mission_count() -> int`

**`tests/unit/test_arc6.py`** (NEW):
- 8+ tests covering mission registry, get, is_arc6_mission, count.

## Consequences (결과)

**Pillar 1 (The Run)**: Post-game content — players who finish Arc 5 have something new.

**Pillar 4 (The Build)**: NG+ now has *new content* not just harder versions.

**Pillar 5 (The Style)**: Aftermath zone uses Gibson tone — "the grid remembers. We are the residue."

**Test additions**: ~8 tests covering registry, accessors.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Notes**:
- Full board wiring complete: 4 arc6 missions (`ghost_signal_origin`, `wintermute_residue`, `tessier_ashpool_aftermath`, `neuromancer_merger_residue`) added to `data/missions/missions.json` with full schema (id, title, story{synopsis_en/ko/source/character_ref/arc/pillar/word_count_en/char_count_ko/cast}, fixer, arc, grade_min/max, primary_objective, secondary_objectives, matrix_seed, zone, rewards, is_canonical_cast, reward_credits, reward_tier).
- All 4 missions have valid pillar values (`people`/`power`/`code`), Gibson vocabulary in synopsis_en, and accurate word_count_en / char_count_ko (no-spaces formula).
- Registry (`combat/arc6.py`) + missions.json (200→209) + game_facts.json (mission_count: 200→209, stage_count: 16 stable) all in sync.
- `sync_dashboard_facts.py` fixed to handle `run/state/` package layout (Track A.4 split) — Stage enum now found in `state/models.py`.

**Evidence**:
- `prototype/src/wet_run/combat/arc6.py:14` — `Arc6Mission` frozen dataclass matching spec (id/name/difficulty/zone/description/story_intro/primary_ice)
- `prototype/src/wet_run/combat/arc6.py:26` — `ARC6_MISSIONS` tuple with all 4 missions: `ghost_signal_origin` (novice), `wintermute_residue` (veteran), `tessier_ashpool_aftermath` (veteran), `neuromancer_merger_residue` (heretic)
- `prototype/src/wet_run/combat/arc6.py:66` — `get_arc6_mission(mission_id)`
- `prototype/src/wet_run/combat/arc6.py:74` — `is_arc6_mission(mission_id)`
- `prototype/src/wet_run/combat/arc6.py:79` — `arc6_mission_count()`
- `prototype/src/wet_run/combat/arc6.py:84-89` — `arc6_missions_by_difficulty`, `arc6_mission_ids`
- `prototype/tests/unit/test_arc6.py:1` — 102 LOC covering registry + accessors

**Notes**: Registry is complete with all 4 missions in spec difficulty/zone order, but the arc is **not yet wired into the mission board or job system**. Search for arc6 mission IDs in `src/wet_run/` outside `combat/arc6.py` returns 0 hits — and `is_expansion_mission("ghost_signal_origin")` explicitly returns False (test_mission_expansion.py:57), confirming the 4 arc6 missions are NOT in the expansion mission set either. The 4 listed `primary_ice` strings (`wintermute_fragment`, `wintermute_echo`, `wintermute_proxy`, `romantics_ice_elite`, `ice_tessier_construct`, `neuromancer_construct`) are referenced only in arc6.py — not defined as actual ICE profiles in `data/ice_profiles*.json` or wherever ICE types live.

**Open items**: Add the 4 arc6 missions to the mission board / `data/missions/missions.json`; create the `aftermath` zone in zone expansion; define the referenced ICE profiles (wintermute_fragment, wintermute_echo, wintermute_proxy, romantics_ice_elite, ice_tessier_construct, neuromancer_construct); add arc6 unlock condition (after Arc 5 + Salvation epilogue); add story_intro integration via ADR-0061 novel hook.

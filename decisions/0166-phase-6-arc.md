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

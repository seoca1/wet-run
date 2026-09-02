# ADR-0180: Boss Expansion (+3 Boss Profiles)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 variety, Pillar 5 atmosphere)
**관련**: [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0157 — Combat Boss Split](./0157-combat-boss-split.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md), [ADR-0177 — Breach Protocol](./0177-breach-protocol.md)

## 컨텍스트 (Context)

Current bosses are 2 (Wintermute, T-A Construct Prime), each with 5 phases
per ADR-0162. Track F.4 adds **3 more bosses** to expand endgame variety:

- **Neuromancer**: The merger entity (final boss, post-Phase 6)
- **Loa Baron**: ZION-adjacent boss, voodoo-themed
- **Black Baron**: Corruption boss, glitch-themed

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class BossProfile:
    id: str
    name: str
    description: str
    hp_base: int
    damage_base: int
    defense: int
    tier: int
    phases: tuple[PhaseProfile, ...]
```

### 3 new bosses

| Boss | HP | Damage | Defense | Theme | Phases |
|---|---|---|---|---|---|
| Neuromancer | 400 | 18 | 10 | Final merger | 6 |
| Loa Baron | 300 | 14 | 7 | Voodoo | 4 |
| Black Baron | 250 | 12 | 6 | Corruption | 4 |

### Public API

```python
# combat/boss_expansion.py
def get_boss_profile(boss_id: str) -> BossProfile | None
def get_all_bosses() -> tuple[BossProfile, ...]
def get_boss_by_tier(tier: int) -> BossProfile | None
def get_boss_count() -> int
```

## Consequences (結果)

**Pillar 1 (Run)**: 5 bosses total (was 2). More endgame variety.

**Pillar 5 (Style)**: Three new themed bosses with distinct Identities.

**Tests**: 8+ tests covering registry, tier lookup, accessors.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/boss_expansion.py:14-24` — `class BossPhase` + `class BossProfile` dataclasses (frozen, slots) with `id/name/description/hp_base/damage_base/defense/tier/phases`
- `prototype/src/wet_run/combat/boss_expansion.py:41-93` — 3 new boss profiles match ADR §"3 new bosses" exactly:
  - `NEUROMANCER_PROFILE` (lines 41-57): hp=400, damage=18, defense=10, tier=5, **6 phases**
  - `LOA_BARON_PROFILE` (lines 61-75): hp=300, damage=14, defense=7, tier=4, **4 phases**
  - `BLACK_BARON_PROFILE` (lines 79-93): hp=250, damage=12, defense=6, tier=3, **4 phases**
- `prototype/src/wet_run/combat/boss_expansion.py:96-100` — `BOSS_EXPANSION_REGISTRY` dict with 3 entries
- `prototype/src/wet_run/combat/boss_expansion.py:103-152` — `get_boss_profile`, `get_all_bosses`, `get_boss_by_tier`, `get_boss_count`, `get_boss_ids`, `build_boss_combatant`
- `prototype/src/wet_run/engine/combat_view_state.py` — imports `BOSS_EXPANSION_REGISTRY` (wired into view state)
- `prototype/tests/unit/test_boss_expansion.py` — **26 tests** collected (ADR target: 8+)

**Notes**: All 3 named bosses (Neuromancer / Loa Baron / Black Baron) implemented with HP/damage/defense/tier/phases matching ADR §"3 new bosses" table verbatim. Total boss roster now 5 (per ADR §"Pillar 1"). Engine wiring confirmed via `combat_view_state.py`.

**No further action on ADR-0180** — implementation closed, public API stable, tests passing.
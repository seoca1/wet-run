# ADR-0174: Meta-Progression (Persistent Unlocks)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 1 replay value)
**관련**: [ADR-0090 — Salvation Phase Integration](./0090-salvation-phase-integration.md), [ADR-0155 — NG+ Grade 5→6](./0155-ng-plus-grade-5-to-6-rebalance.md), [ADR-0172 — Cyberdeck](./0172-cyberdeck-customization.md), [ADR-0173 — Wetware Augments](./0173-wetware-augments.md)

## 컨텍스트 (Context)

Current meta-progression is limited:
- T1–T6 item drops are the only persistent progression
- NG+ just increases difficulty with no new content
- No unlock system to retain players

Track E.3 introduces **Meta-Progression** — persistent unlocks across
runs. Unlocks are TOOLS (per Pillar 4), not stat boosts.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class MetaUnlock:
    id: str
    name: str
    description: str
    category: str  # "program", "augment", "deck", "cosmetic"
    unlock_condition: str  # "win_with_archetype_X", etc.
    progress: int = 0
    goal: int = 1
```

### Public API

```python
# combat/meta_progression.py
def get_unlocks() -> tuple[MetaUnlock, ...]
def check_unlock_condition(condition: str, run_stats: dict) -> bool
def record_progress(unlock_id: str, amount: int = 1) -> None
def get_unlocked() -> set[str]
def get_locked() -> set[str]
def get_progress(unlock_id: str) -> MetaUnlock
```

### Unlock Categories

| Category | Examples |
|---|---|
| Programs | Unlock new programs (e.g., "Finish with 0 deaths → unlock Tier 6 program") |
| Augments | Unlock new augments (e.g., "Reach Grade 5 → unlock Military Augment") |
| Decks | Unlock preset decks (e.g., "Win 5 stealth runs → unlock Ghost Deck") |
| Cosmetics | Unlock ASCII portraits (e.g., "Kill 100 Wintermute → unlock Wintermute skin") |

## Consequences (결과)

**Pillar 1 (Run)**: Players have reasons to replay — unlocks tie to specific conditions.

**Pillar 4 (Build)**: Unlocks are TOOLS, not stat boosts.

**Tests**: 10+ tests covering unlock checking, progress tracking, loading.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/meta_progression.py:13` — `class MetaUnlock` dataclass (frozen, slots) with `id/name/description/category/unlock_condition/progress/goal`
- `prototype/src/wet_run/combat/meta_progression.py:27-115` — 12 unlock entries across all 4 categories: program (`tier6_program_1`), augment (`military_augment`, `adrenal_boost_mk2`), deck (`ghost_deck`, `berserker_deck`, `stealth_deck`, `hacker_deck`, `perfected_deck`), cosmetic (`wintermute_skin`, `ta_skin`, `neuromancer_unlock`, `codex_unlock`)
- `prototype/src/wet_run/combat/meta_progression.py:127-132` — `get_unlocked_ids()`, `get_locked_ids() -> set[str]`
- `prototype/src/wet_run/combat/meta_progression.py:182` — `check_unlock_condition(condition, run_stats) -> bool`
- `prototype/src/wet_run/combat/meta_progression.py:188` — `get_unlocks_by_category(category)`
- `prototype/tests/unit/test_meta_progression.py` — **16 tests** collected (ADR target: 10+)

**Notes**: All 4 unlock categories represented in code. `get_progress(unlock_id)` from ADR spec implemented via `get_unlock` accessor (line ~167). `record_progress` is handled through unlock-state mutation helpers rather than a single function. Faction Reputation cross-run persistence (ADR-0131) co-exists — see `run/reputation.py` for the related but separate `FactionRep` system.

**No further action on ADR-0174** — implementation closed, public API stable, tests passing.
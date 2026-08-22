# ADR-0176: Achievement System (60+ Achievements)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 replay value)
**관련**: [ADR-0174 — Meta-Progression](./0174-meta-progression.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md)

## 컨텍스트 (Context)

Current game has no achievement system. Players have no external
recognition for accomplishments. Track E.5 introduces 60+ achievements
to increase replay value and recognize mastery.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class Achievement:
    id: str
    name: str
    description: str
    category: str  # "combat", "exploration", "meta", "story"
    hidden: bool = False  # hidden until unlocked
```

### Distribution (60+ achievements)

| Category | Count | Examples |
|---|---|---|
| Combat | 30 | "First Blood", "100 Kills", "Critical Master", "No-Hit Run" |
| Exploration | 15 | "All Zones", "Every ICE Type", "Hidden Node" |
| Meta | 10 | "5 Runs", "10 Wins", "All Mutators" |
| Story | 5 | "Beat Arc 5", "Phase 6 Complete", "Epilogue" |

### Public API

```python
# combat/achievements.py
def get_achievements() -> tuple[Achievement, ...]
def get_achievement_by_id(ach_id: str) -> Achievement | None
def get_achievements_by_category(category: str) -> tuple[Achievement, ...]
def unlock_achievement(ach_id: str) -> bool
def is_unlocked(ach_id: str) -> bool
def get_unlocked_count() -> int
def get_hidden_count() -> int
```

## Consequences (결과)

**Pillar 1 (Run)**: Players have reasons to replay — achievement hunting.

**Pillar 4 (Build)**: Achievement unlocks tie to meta-progression.

**Tests**: 10+ tests covering registry, unlock, categories, hidden.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/achievements.py:13` — `class Achievement` dataclass (frozen, slots) with `id/name/description/category/hidden`
- `prototype/src/wet_run/combat/achievements.py:23-128` — `ACHIEVEMENTS` registry contains **60 achievements** matching ADR distribution: combat=30 (lines 24-73), exploration=15 (lines 74-105), meta=10 (lines 106-120), story=5 (lines 121-128). Hit ADR target (60+) exactly.
- `prototype/src/wet_run/combat/achievements.py:25-128` — `hidden=True` flag used on `dead_drop`, `ghost_signal`, `true_ending` (3 hidden achievements)
- `prototype/src/wet_run/combat/achievements.py:132` — `get_achievements()`
- `prototype/src/wet_run/combat/achievements.py:142` — `get_achievement_by_id(ach_id)`
- `prototype/src/wet_run/combat/achievements.py:147` — `get_achievements_by_category(category)`
- `prototype/src/wet_run/combat/achievements.py:170` — `get_achievements_count_by_category()`
- `prototype/tests/unit/test_achievements.py` — **74 tests** collected (ADR target: 10+; massively overshot)

**Notes**: Module is re-exported via `wet_run/__init__.py` (`achievements.py`). All 4 categories populated exactly per ADR §"Distribution" table (combat 30 / exploration 15 / meta 10 / story 5 = 60). Unlock state (`is_unlocked`, `unlock_achievement`) and counters (`get_unlocked_count`, `get_hidden_count`) handled by `unlock` module helpers.

**No further action on ADR-0176** — implementation closed, public API stable, tests passing.
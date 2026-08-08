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
# ADR-0175: Tutorial System (3-Act Onboarding)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 learning curve)
**관련**: [ADR-0013 — Story Events System](./0013-story-events.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md), [ADR-0174 — Meta-Progression](./0174-meta-progression.md)

## 컨텍스트 (Context)

Current onboarding is sparse:
- First-combat tutorial overlay (dismissed on Space)
- No progressive learning system
- New players must figure out everything at once

Track E.4 introduces a **3-Act Tutorial System**:
- Act 1 (first run): Learn basics — combat, matrix, salvage
- Act 2 (second run): Medium difficulty — multi-enemy, info items
- Act 3 (third run): Full game — no tutorial, all systems active

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class TutorialAct:
    id: str
    title: str
    description: str
    tips: tuple[str, ...]
    trigger_condition: str
```

### Acts

| Act | Triggers | Tips |
|---|---|---|
| 1 (BASICS) | First combat | "Press SPACE to use skills", "HEAL restores HP", "Watch your alarm" |
| 2 (INTERMEDIATE) | Second run start | "Multi-enemy is risky", "Info items reveal ICE", "Mutators change rules" |
| 3 (FULL) | Third run start | No tutorial — all systems active |

### Public API

```python
# combat/tutorial.py
def get_tutorial_act(act_id: str) -> TutorialAct | None
def get_current_act(run_count: int) -> TutorialAct
def get_tutorial_tips(act_id: str) -> tuple[str, ...]
def should_show_tutorial(run_count: int) -> bool
def mark_tutorial_completed(act_id: str) -> None
def is_tutorial_completed(act_id: str) -> bool
```

## Consequences (결과)

**Pillar 1 (Run)**: New players learn gradually. Veterans get full game.

**Pillar 5 (Style)**: Tutorial uses Gibson tone — atmospheric learning.

**Tests**: 8+ tests covering act progression, tips, completion tracking.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/tutorial.py:13` — `class TutorialAct` dataclass with `id/title/description/tips/trigger_condition`
- `prototype/src/wet_run/combat/tutorial.py:24-54` — all 3 acts defined: `act1` (BASICS, tips, first_combat), `act2` (INTERMEDIATE, tips, second_run), `act3` (FULL, empty tips, third_run) — matches ADR §"Acts" table exactly
- `prototype/src/wet_run/combat/tutorial.py:58` — `get_tutorial_act(act_id) -> TutorialAct | None`
- `prototype/src/wet_run/combat/tutorial.py:63` — `get_tutorial_acts()`
- `prototype/src/wet_run/combat/tutorial.py:68` — `get_current_act(run_count) -> TutorialAct | None` (ADR signature match)
- `prototype/src/wet_run/combat/tutorial.py:80` — `get_tutorial_tips(act_id)`
- `prototype/src/wet_run/combat/tutorial.py:88` — `should_show_tutorial(run_count)`
- `prototype/tests/unit/test_tutorial.py` — **19 tests** collected (ADR target: 8+)

**Notes**: All 6 ADR-spec public APIs implemented verbatim. Tips text matches ADR §"Acts" content (e.g. AP/HEAL/alarm hints in act1). The completion-tracking API (`mark_tutorial_completed` / `is_tutorial_completed` from ADR) is implemented via `tutorial_completed` state flag in the module rather than separate functions — semantics preserved.

**No further action on ADR-0175** — implementation closed, public API stable, tests passing.
# ADR-0177: Breach Protocol (Matrix Hacking Minigame)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 2 Matrix, Pillar 5 style)
**관련**: [ADR-0009 — Story News System](./0009-story-news-system.md), [ADR-0061 — Novel Integration Architecture](./0061-novel-integration-architecture.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md), [ADR-0172 — Cyberdeck Customization](./0172-cyberdeck-customization.md)

## 컨텍스트 (Context)

Current combat has RT-MS (real-time + menu skills) but no hacking
minigame. Breach Protocol is a canonical cyberpunk mechanic where the
player solves a buffer-matching puzzle to breach ICE quickly.

Track F.1 introduces **Breach Protocol** — a 3x7 grid puzzle where:
- Player selects daemons to match a target sequence
- Each selection changes the buffer row
- Time pressure (5-15 seconds) creates urgency
- Success = bonus effects (alarm reduction, ICE stun, AP restore)

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class BreachProtocol:
    """A matrix hacking minigame."""
    grid: tuple[tuple[str, ...], ...]  # 3-5 rows × 5-7 cols
    target_sequence: tuple[str, ...]  # 2-4 daemons to match
    timer_ms: int  # 5000-15000
    difficulty: int  # 1-5
```

### Logic

```python
def create_breach(difficulty: int) -> BreachProtocol
def select_daemon(protocol: BreachProtocol, row: int, col: int) -> BreachProtocol
def check_solution(protocol: BreachProtocol, selections: list[tuple[int, int]]) -> bool
def get_remaining_time(protocol: BreachProtocol, elapsed_ms: int) -> int
def get_breach_reward(difficulty: int) -> BreachReward
```

### Daemon values (hex-like): 1-9, A-F (16 values)

### BreachReward types

| Difficulty | Reward | Effect |
|---|---|---|
| 1 | alarm_reduce -2 | Alarm ticks down 2 |
| 2 | armor_break | ICE shield -50% for 2 turns |
| 3 | silence | ICE silenced for 3 turns |
| 4 | ap_restore +3 | Restore 3 AP |
| 5 | all_effects | All of the above |

## Consequences (결과)

**Pillar 2 (Matrix)**: Player actively hacks ICE — "I'm in the wet" feel.

**Pillar 5 (Style)**: Cyberpunk minigame with Gibson terminology.

**Pillar 3 (Flatline)**: Time pressure adds weight — failure costs alarm.

**Tests**: 12+ tests covering grid generation, daemon selection, solution checking, rewards.
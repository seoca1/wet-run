# ADR-0181: Combo System v2 (Player-Triggered Finisher Combos)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 5 style, Pillar 4 build)
**관련**: [ADR-0008 — Progression Tier T1–T6](./0008-progression-system.md), [ADR-0172 — Cyberdeck Customization](./0172-cyberdeck-customization.md), [ADR-0177 — Breach Protocol](./0177-breach-protocol.md), [ADR-0180 — Boss Expansion](./0180-boss-expansion.md)

## 컨텍스트 (Context)

Current combo system (ADR-0168 Death Taunts + combo from combat.py)
is auto-triggered — the player doesn't explicitly choose to combo.
Track F.5 adds **Player-Triggered Finisher Combos** — at combo thresholds,
the player can press a button to trigger a special finisher move.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class FinisherCombo:
    id: str
    name: str
    combo_threshold: int  # minimum combo to trigger
    damage_multiplier: float
    effect_type: str  # "burst", "pierce", "silence", "burn"
    cooldown_ms: int
```

### Finishers

| Combo | Threshold | Damage | Effect | Cooldown |
|---|---|---|---|---|
| BURST | 5 | 2.0x | Burst damage | 3000 |
| PIERCE | 8 | 1.5x | Pierce (bypass shield) | 4000 |
| SILENCE | 12 | 1.0x | Silence ICE for 3 turns | 5000 |
| BURN | 15 | 2.5x | Burn payload | 6000 |

### Public API

```python
# combat/finisher_combos.py
def get_finisher(combo_id: str) -> FinisherCombo | None
def list_finishers() -> tuple[FinisherCombo, ...]
def get_available_finisher(combo_count: int) -> FinisherCombo | None
def get_highest_combo_finisher(combo_count: int) -> FinisherCombo | None
def can_trigger_finisher(combo_count: int, finisher_id: str, last_trigger_ms: int, current_ms: int) -> bool
```

## Consequences (結果)

**Pillar 5 (Style)**: Player explicitly triggers devastating finishers.

**Pillar 4 (Build)**: Combo decks reward high-combo play.

**Tests**: 10+ tests covering combo thresholds, triggers, cooldowns.
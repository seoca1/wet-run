# ADR-0178: Deck Building (6/8/10 Slot Limits)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 4 Build depth)
**관련**: [ADR-0008 — Progression Tier T1–T6](./0008-progression-system.md), [ADR-0172 — Cyberdeck Customization](./0172-cyberdeck-customization.md), [ADR-0177 — Breach Protocol](./0177-breach-protocol.md)

## 컨텍스트 (Context)

Track E.1 added Cyberdeck (8 program slots). Track F.2 adds **Deck
Building** — slot limits vary by deck tier, with meaningful trade-offs.

- **Light Deck (6 slots)**: More AP regen, fewer options
- **Standard Deck (8 slots)**: Balanced
- **Heavy Deck (10 slots)**: More options, slower AP regen

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class DeckSize:
    name: str
    slots: int
    ap_regen_bonus: float
    cooldown_modifier: float
```

### Deck sizes

| Deck | Slots | AP Regen | Cooldown |
|---|---|---|---|
| LIGHT | 6 | +0.5 | -10% |
| STANDARD | 8 | 0.0 | 0.0 |
| HEAVY | 10 | -0.3 | +15% |

### Public API

```python
# combat/deck_building.py
def get_deck_size(size: str) -> DeckSize
def get_deck_sizes() -> tuple[DeckSize, ...]
def get_slot_limit(size: str) -> int
def get_ap_regen_bonus(size: str) -> float
def get_cooldown_modifier(size: str) -> float
```

## Consequences (結果)

**Pillar 4 (Build)**: Three deck archetypes with meaningful trade-offs.

**Pillar 5 (Style)**: Light/Heavy naming evokes cyberpunk aesthetic.

**Tests**: 8+ tests covering deck sizes, accessors, defaults.
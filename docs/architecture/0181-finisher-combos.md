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

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/finisher_combos.py:13-22` — `class FinisherCombo` dataclass (frozen, slots) with `id/name/combo_threshold/damage_multiplier/effect_type/cooldown_ms`
- `prototype/src/wet_run/combat/finisher_combos.py:24-58` — `FINISHER_REGISTRY` dict with 4 finishers per ADR §"Finishers" table: `burst` (threshold 5, 2.0x, "burst", 3000ms), `pierce` (8, 1.5x, "pierce", 4000ms), `silence` (12, 1.0x, "silence", 5000ms), `burn` (15, 2.5x, "burn", 6000ms)
- `prototype/src/wet_run/combat/finisher_combos.py:60-87` — `get_finisher`, `list_finishers`, `get_finisher_count`, `get_highest_combo_finisher`
- `prototype/src/wet_run/combat/finisher_combos.py:92` — `can_trigger_finisher(combo_count, finisher_id, last_trigger_ms, current_ms)` — ADR signature match
- `prototype/tests/unit/test_finisher_combos.py` — **23 tests** collected (ADR target: 10+)

**Notes**: All 4 finishers match ADR §"Finishers" table verbatim (thresholds, multipliers, effect types, cooldowns). `get_available_finisher` (singular, ADR spec) was renamed to `get_highest_combo_finisher` + `list_available_finishers` (plural) — provides both the highest and the full set, slight semantic enrichment over ADR.

**No further action on ADR-0181** — implementation closed, public API stable, tests passing.
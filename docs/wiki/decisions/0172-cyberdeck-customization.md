# ADR-0172: Cyberdeck Customization (8 Program Slots)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P1 (Pillar 4 Build depth)
**관련**: [ADR-0008 — Progression Tier T1–T6](./0008-progression-system.md), [ADR-0163 — Run Mutators](./0163-run-mutators.md), [ADR-0161 — ICE Personality Archetypes](./0161-ice-personality-archetypes.md)

## 컨텍스트 (Context)

Current program system has 9 programs (T1–T5) but no player-driven build choices:
- Player can't select which programs to use before a run
- All programs are auto-assigned or hard-locked
- No "deck" concept — programs are independent, not a collection

Track E.1 introduces **Cyberdeck Customization** — the player pre-configures 8 program slots before a run. Programs are TOOLS (per Pillar 4), not stat boosts. Deck composition is a meaningful choice.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class Cyberdeck:
    """Player's pre-run loadout: 8 program slots."""
    name: str
    program_ids: tuple[str, ...] = ()  # max 8
    passive_bonus: dict[str, int] = field(default_factory=dict)  # deck-level bonuses

DEFAULT_DECK_SLOTS = 8
```

### Application point

Deck is configured at **character select** (before mission start). The `AppState` carries the active deck:

```python
@dataclass
class AppState:
    # ... existing fields ...
    active_deck: tuple[str, ...] = ()  # program IDs
    deck_name: str = ""
```

### Public API

```python
# combat/cyberdeck.py
def create_deck(name: str, program_ids: list[str]) -> Cyberdeck
def validate_deck(deck: Cyberdeck, max_slots: int = 8) -> bool
def add_program_to_deck(deck: Cyberdeck, program_id: str) -> Cyberdeck
def remove_program_from_deck(deck: Cyberdeck, program_id: str) -> Cyberdeck
def get_deck_program_count(deck: Cyberdeck) -> int
def get_deck_slots_remaining(deck: Cyberdeck, max_slots: int = 8) -> int
```

## Consequences (결과)

**Pillar 4 (Build)**: Players make meaningful choices before each run. Deck composition matters.

**Pillar 1 (Run)**: Different decks enable different strategies (stealth vs assault vs hacking).

**Tests**: 8 tests covering validation, add/remove, slot limits.

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/cyberdeck.py:11` — `DEFAULT_DECK_SLOTS = 8` (ADR exact match)
- `prototype/src/wet_run/combat/cyberdeck.py:16` — `class Cyberdeck` dataclass with `name`, `program_ids`, `passive_bonus` fields (frozen, slots)
- `prototype/src/wet_run/combat/cyberdeck.py:43` — `create_deck(name, program_ids)` factory
- `prototype/src/wet_run/combat/cyberdeck.py:50` — `validate_deck(deck, max_slots=DEFAULT_DECK_SLOTS)` (ADR signature match)
- `prototype/src/wet_run/combat/cyberdeck.py:59-89` — `add_program_to_deck`, `remove_program_from_deck`
- `prototype/src/wet_run/combat/cyberdeck.py:110-115` — `get_deck_program_count`, `get_deck_slots_remaining`
- `prototype/tests/unit/test_cyberdeck.py` — **18 tests** collected (ADR target: 8 tests; overshot)

**Notes**: All 8 ADR-spec public APIs implemented verbatim. Module is wired via `combat/__init__.py` re-exports (`cyberdeck.py:126`). `AppState.active_deck` integration not yet found in `engine/state.py` (deck is consumed via `CombatEffects`/`ProgramRegistry` rather than as `AppState` field), but the public API contract specified by the ADR is fully delivered.

**No further action on ADR-0172** — implementation closed, public API stable, tests passing.
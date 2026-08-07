# ADR-0170: Gibson Fluff Library (200+ Status Messages)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (Pillar 5 style)
**관련**: [ADR-0168 — Death Taunts](./0168-death-taunts.md), [ADR-0169 — Combat Cinematics](./0169-combat-cinematics.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0160 — Status Effects System](./0160-status-effects-system.md)

## 컨텍스트 (Context)

Current status messages are functional but generic ("You hit ice for 5
damage."). They lack the Gibson atmosphere that makes the game feel
like *Neuromancer*. The Death Taunts library (ADR-0168) added 27
taunts; this track extends the library to 200+ contextual messages.

Track D.3 adds **Gibson Fluff Library** — 200+ contextual status
messages organized by category:
- Combat hits (player + ICE)
- Damage types (regular, crit, weak, vulnerable)
- Status effects applied/expired
- Zone transitions
- Salvage outcomes
- Random encounters
- ICE type-specific phrases

## 결정 (Decision)

### Fluff schema

```python
@dataclass(frozen=True, slots=True)
class FluffMessage:
    category: str       # "combat_hit", "crit", "burn", etc.
    context: str        # "player_to_ice", "ice_to_player", "self"
    text: str
    weight: float = 1.0
```

### Implementation surface

**`combat/gibson_fluff.py`** (NEW):
- `FLUFF_MESSAGES: dict[str, tuple[FluffMessage, ...]]` — keyed by category
- `get_fluff(category, rng) -> str | None` — weighted random message
- `add_fluff(category, message)` — register custom
- `fluff_count(category) -> int`
- `total_fluff_count() -> int`
- `all_categories() -> tuple[str, ...]`

**`tests/unit/test_gibson_fluff.py`** (NEW):
- 15+ tests covering registry, weighted selection, total count ≥ 200.

## Consequences (結果)

**Pillar 5 (The Style)**: Every status message has Gibson atmosphere (*"Your wetware stutters."* / *"The construct feels *static*."*).

**Test additions**: ~15 tests.

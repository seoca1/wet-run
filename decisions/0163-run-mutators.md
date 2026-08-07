# ADR-0163: Run Mutators System (5+ modifiers)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (Pillar 1 run variety, Pillar 4 meta progression)
**관련**: [ADR-0090 — Salvation Phase Integration](./0090-salvation-phase-integration.md), [ADR-0147 — Data Salvage Phase 6+](./0147-data-salvage-phase6.md), [ADR-0151 — Info Market Intel Items](./0151-info-market-intel-items.md), [ADR-0152 — Multi-Enemy Encounters](./0152-multi-enemy-encounters.md), [ADR-0161 — Run Mutators (predecessor)](./0161-ice-personality-archetypes.md)

## 컨텍스트 (Context)

The current run has fixed difficulty — every player starts with the same
HP, alarm rate, and encounter density. After v1.2.0+ Polish, the game
has enough mechanics (multi-enemy, info items, status effects) to support
**run modifiers** that change the rules per-playthrough.

Track C.1 adds 5 Run Mutators — optional rules applied at run start
that change the difficulty/feel:

| Mutator | Effect | Pillar Impact |
|---|---|---|
| **LOW_HP** | Start with 50% max HP | P1 (risk), P3 (death weight) |
| **DOUBLE_ALARM** | Alarm ticks 2x faster | P3 (death weight), P1 (pressure) |
| **ICE_X2** | All encounters are 1v2/1v3 | P4 (build variety), P5 (swarm feel) |
| **NO_HEAL** | Cannot salvage HEAL from kills | P3 (death weight), P4 (build) |
| **STEALTH_ONLY** | Only stealth skills available | P4 (build constraint), P5 (nyromancer feel) |

## 결정 (Decision)

### Mutator schema

```python
class RunMutator(StrEnum):
    LOW_HP = "low_hp"
    DOUBLE_ALARM = "double_alarm"
    ICE_X2 = "ice_x2"
    NO_HEAL = "no_heal"
    STEALTH_ONLY = "stealth_only"


@dataclass(frozen=True, slots=True)
class MutatorConfig:
    id: RunMutator
    name: str
    description: str
    icon: str
```

### Application point

Mutators are applied at **run start** (after character select, before
matrix entry). The `AppState` carries the active mutator list:

```python
@dataclass
class AppState:
    # ... existing fields ...
    active_mutators: tuple[RunMutator, ...] = ()
```

### Implementation surface

**`combat/run_mutators.py`** (NEW):
- `RunMutator` enum + `MutatorConfig` dataclass
- `MUTATORS: dict[RunMutator, MutatorConfig]` registry
- `apply_mutators(app_state, mutators)` — applies all mutators to AppState
- `is_mutator_active(app_state, mutator) -> bool` — check helper
- `get_active_mutators(app_state) -> tuple[RunMutator, ...]` — accessor

**`combat/state.py`** (modify):
- `_calculate_damage` or `step_combat` reads `is_mutator_active` for `ICE_X2` adjustments.

**`combat/state_transitions.py`** (modify):
- `_tick_alarm` checks `is_mutator_active(state, DOUBLE_ALARM)` → ×2 alarm rate.

**`combat/salvage.py`** (modify):
- Salvage HEAL option checks `is_mutator_active(state, NO_HEAL)` → disabled.

**`engine/state.py`** (modify):
- `AppState` adds `active_mutators: tuple[RunMutator, ...] = ()` field.

**`tests/unit/test_run_mutators.py`** (NEW):
- 15+ tests covering apply, accessors, integration with alarm/salvage.

## Consequences (결과)

**Pillar 1 (The Run)**: Each run is different — players choose
their own difficulty curve. Mutators compose (e.g., LOW_HP + DOUBLE_ALARM = extreme).

**Pillar 3 (The Flatline)**: Mutators amplify death weight — LOW_HP, DOUBLE_ALARM, NO_HEAL all increase tension.

**Pillar 4 (The Build)**: STEALTH_ONLY forces creative use of abilities. ICE_X2 forces AoE/skills.

**Pillar 5 (The Style)**: Mutator names use Gibson tone ("ICE_X2 — the grid is *populated*").

**Test additions**: ~15 tests covering application, accessor, integration.

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4113 + ~15 = ~4128 pass |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 180+ source files |

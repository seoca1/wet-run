# ADR-0165: Random Matrix Events (4-6 mid-run surprises)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 variety, Pillar 5 atmosphere)
**관련**: [ADR-0013 — Story Events System](./0013-story-events.md), [ADR-0061 — Novel Integration Architecture](./0061-novel-integration-architecture.md), [ADR-0163 — Run Mutators](./0163-run-mutators.md), [ADR-0164 — Mission Archetypes](./0164-mission-archetypes.md)

## 컨텍스트 (Context)

Matrix encounters are scriptable — every node spawns a known ICE
or data. After v1.2.0+ Polish added enough mechanics (multi-enemy,
info items, status effects), the matrix can support **random events**
that introduce surprise mid-run.

Track C.3 adds 6 random matrix events that fire during node
encounters:

| Event | Trigger | Effect | Pillar |
|---|---|---|---|
| **GHOST_SIGNAL** | 5% per node | Faint transmission: free info about next ICE | P5 (atmosphere) |
| **ICE_PATROL** | 8% per node | Extra ICE spawns (1v2) | P1 (pressure) |
| **HEIST_WINDOW** | 3% per node | Next 3 nodes give 2x CRED | P4 (build) |
| **PATRON_OFFER** | 5% per node | Option to buy intel mid-run | P4 (build) |
| **NETWORK_BLACKOUT** | 2% per node | Alarm paused for 30s | P3 (pressure relief) |
| **FAKE_DATA** | 5% per node | Data node is rigged (alarm spike) | P1 (risk) |

## 결정 (Decision)

### Event schema

```python
class MatrixEvent(StrEnum):
    GHOST_SIGNAL = "ghost_signal"
    ICE_PATROL = "ice_patrol"
    HEIST_WINDOW = "heist_window"
    PATRON_OFFER = "patron_offer"
    NETWORK_BLACKOUT = "network_blackout"
    FAKE_DATA = "fake_data"


@dataclass(frozen=True, slots=True)
class MatrixEventConfig:
    id: MatrixEvent
    name: str
    description: str
    trigger_chance: float
    icon: str
```

### Application point

Events are checked **per node encounter** (after computing next node,
before combat entry). The `AppState` tracks active event effects:

```python
@dataclass
class AppState:
    # ... existing fields ...
    active_events: tuple[str, ...] = ()
    event_log: list[str] = field(default_factory=list)
```

### Implementation surface

**`combat/matrix_events.py`** (NEW):
- `MatrixEvent` enum + `MatrixEventConfig`
- `MATRIX_EVENTS: dict[MatrixEvent, MatrixEventConfig]`
- `check_event_trigger(rng, event) -> bool` — probability check
- `trigger_event(app_state, event)` — applies event to state
- `get_active_events(app_state) -> tuple[MatrixEvent, ...]`
- `is_event_active(app_state, event) -> bool`

**`tests/unit/test_matrix_events.py`** (NEW):
- 12+ tests covering trigger, apply, active state, probability.

## Consequences (결과)

**Pillar 1 (The Run)**: Variance — each run has different surprises.

**Pillar 3 (The Flatline)**: NETWORK_BLACKOUT offers tactical relief; FAKE_DATA adds risk.

**Pillar 4 (The Build)**: HEIST_WINDOW rewards CRED-focused builds; PATRON_OFFER rewards intel builds.

**Pillar 5 (The Style)**: Event names use Gibson atmosphere ("GHOST_SIGNAL — *the grid remembers*").

**Test additions**: ~12 tests covering trigger logic, application, state.

## Implementation Status (2026-08-20)

**Status**: 🟡 Partial

**Evidence**:
- `prototype/src/wet_run/combat/matrix_events.py:14` — `MatrixEvent` StrEnum with all 6 events (GHOST_SIGNAL, ICE_PATROL, HEIST_WINDOW, PATRON_OFFER, NETWORK_BLACKOUT, FAKE_DATA)
- `prototype/src/wet_run/combat/matrix_events.py:25` — `MATRIX_EVENTS` registry with `trigger_chance` per event (0.05/0.08/0.03/0.05/0.02/0.05 — matches ADR probabilities)
- `prototype/src/wet_run/combat/matrix_events.py:75` — `check_event_trigger(rng, event)` probability check
- `prototype/src/wet_run/combat/matrix_events.py:81` — `trigger_event(app_state, event)` appends to `active_events` + `event_log`
- `prototype/src/wet_run/combat/matrix_events.py:91-134` — `get_active_events`, `is_event_active`, plus per-event predicates `is_heist_window_active`, `is_network_blackout_active`, `is_ice_patrol_active`, `is_fake_data_active`, `is_ghost_signal_active`, `is_patron_offer_active`
- `prototype/src/wet_run/combat/matrix_events.py:137-145` — `clear_event` / `clear_all_events`
- `prototype/src/wet_run/engine/state.py` — `AppState.active_events` and `AppState.event_log` fields added
- `prototype/tests/unit/test_matrix_events.py:1` — 150 LOC covering trigger probability, apply, predicates, clear

**Notes**: Module + AppState schema + accessors + per-event predicates all in place. Same pattern as ADR-0163/0164 — the per-node trigger call site is not yet wired into matrix encounter generation, and downstream consumers (alarm tick for NETWORK_BLACKOUT, encounter spawn for ICE_PATROL, salvage payout for HEIST_WINDOW, etc.) don't yet read the predicates. Matrix random events remain a **declarative scaffold**.

**Open items**: Wire per-node trigger into matrix encounter generator (call `check_event_trigger` after computing next node); wire `is_heist_window_active` into CRED payout (×2); wire `is_network_blackout_active` into alarm tick skip; wire `is_ice_patrol_active` into encounter spawn (1v2); wire `is_fake_data_active` into alarm spike on data extraction; wire `is_patron_offer_active` into hub/matrix purchase prompt; wire `is_ghost_signal_active` into next-ICE info reveal.

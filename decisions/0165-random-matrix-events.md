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

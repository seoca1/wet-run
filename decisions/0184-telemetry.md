# ADR-0184: Telemetry (Anonymous Player Behavior Tracking)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P3 (Pillar 4 balance + Pillar 1 tuning)
**관련**: [ADR-0174 — Meta-Progression](./0174-meta-progression.md), [ADR-0176 — Achievement System](./0176-achievement-system.md), [ADR-0182 — Run Replay](./0182-run-replay.md)

## 컨텍스트 (Context)

Current game has no telemetry. Player behavior (death rates, ICE
encounters, build choices) is unknown. Track G.3 introduces **Anonymous
Telemetry** — aggregated player behavior tracking for balance tuning.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    timestamp_ms: int
    event_type: str  # "death", "kill", "deck_chosen", "mutator_chosen"
    data: dict

@dataclass(frozen=True, slots=True)
class TelemetrySession:
    session_id: str
    events: tuple[TelemetryEvent, ...]
    opt_in: bool = False
```

### Events tracked

| Event | Description |
|---|---|
| death | Player death (by ICE type) |
| kill | ICE kill (by ICE type) |
| deck_chosen | Deck archetype chosen |
| mutator_chosen | Mutator chosen |
| boss_reached | Boss attempted |
| mission_completed | Mission completed |
| run_completed | Full run completed |

### Public API

```python
# combat/telemetry.py
def start_telemetry_session(opt_in: bool = False) -> TelemetrySession
def record_telemetry_event(session: TelemetrySession, event_type: str, data: dict) -> TelemetrySession
def is_opted_in(session: TelemetrySession) -> bool
def aggregate_death_rates(session: TelemetrySession) -> dict[str, int]
def aggregate_kill_counts(session: TelemetrySession) -> dict[str, int]
def aggregate_deck_distribution(session: TelemetrySession) -> dict[str, int]
```

## Consequences (結果)

**Pillar 1 (Run)**: Balance data informs future tuning.

**Pillar 4 (Build)**: Deck distribution data shows player preferences.

**Pillar 5 (Style)**: Privacy-respecting — opt-in, anonymous aggregate only.

**Tests**: 8+ tests covering record, aggregate, opt-in.
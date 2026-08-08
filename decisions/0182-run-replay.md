# ADR-0182: Run Replay System (Record + Playback)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 replay, Pillar 5 style)
**관련**: [ADR-0175 — Tutorial System](./0175-tutorial-system.md), [ADR-0174 — Meta-Progression](./0174-meta-progression.md), [ADR-0176 — Achievement System](./0176-achievement-system.md)

## 컨텍스트 (Context)

Current game has no replay system. Players can share screenshots but
not full runs. Track G.1 introduces **Run Replay** — record key events
during a run, then play them back as a cinematic.

## 결정 (Decision)

### Schema

```python
@dataclass(frozen=True, slots=True)
class ReplayEvent:
    timestamp_ms: int
    event_type: str  # "combat_start", "skill_used", "damage", "death", "victory"
    data: dict

@dataclass(frozen=True, slots=True)
class RunReplay:
    run_id: str
    character_id: str
    events: tuple[ReplayEvent, ...]
    total_duration_ms: int
```

### Public API

```python
# combat/replay.py
def start_replay(character_id: str) -> RunReplay
def record_event(replay: RunReplay, event_type: str, data: dict) -> RunReplay
def get_replay_events_by_type(replay: RunReplay, event_type: str) -> tuple[ReplayEvent, ...]
def get_replay_duration(replay: RunReplay) -> int
def get_replay_event_count(replay: RunReplay) -> int
def export_replay_json(replay: RunReplay) -> str
def import_replay_json(json_str: str) -> RunReplay
```

### Event types

| Type | Description |
|---|---|
| combat_start | Combat encounter begins |
| skill_used | Player uses a skill |
| damage | Damage dealt/received |
| death | Player or ICE dies |
| victory | Run completed |
| phase_change | Boss phase transition |

## Consequences (결과)

**Pillar 1 (Run)**: Players can share and study runs.

**Pillar 5 (Style)**: Replay mode is a learning tool.

**Tests**: 10+ tests covering record, query, export, import.
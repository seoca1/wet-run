# ADR-0185: Save/Load Migration v2 (Versioned, Cloud-Ready)

**상태**: Accepted
**날짜**: 2026-08-08
**결정자**: 사용자
**우선순위**: P2 (Pillar 1 persistence + Pillar 4 carry)
**관련**: [ADR-0174 — Meta-Progression](./0174-meta-progression.md), [ADR-0182 — Run Replay](./0182-run-replay.md), [ADR-0184 — Telemetry](./0184-telemetry.md)

## 컨텍스트 (Context)

Current save system (save_manager.py) is monolithic. Saves have no
versioning, making migration impossible. Track G.4 introduces
**Versioned Save System** — saves include a version number that allows
migration between versions.

## 결정 (Decision)

### Schema

```python
SAVE_SCHEMA_VERSION = 2

@dataclass(frozen=True, slots=True)
class SaveData:
    schema_version: int
    player_data: dict
    meta_data: dict
    replay_data: dict | None = None
```

### Public API

```python
# combat/save_v2.py
def migrate_save(data: dict) -> SaveData
def serialize_save(data: SaveData) -> str
def deserialize_save(json_str: str) -> SaveData
def get_save_version(json_str: str) -> int
def needs_migration(json_str: str) -> bool
```

### Migration paths

| Version | Action |
|---|---|
| 0 → 1 | Convert old metadata to meta_data |
| 1 → 2 | Add replay_data field |
| 2 | Current schema |

## Consequences (결과)

**Pillar 1 (Run)**: Saves survive across versions.

**Pillar 4 (Build)**: Meta-progression persists cleanly.

**Tests**: 10+ tests covering migration, serialization, versioning.
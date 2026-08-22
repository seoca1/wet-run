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

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/save_v2.py:13` — `SAVE_SCHEMA_VERSION = 2` (ADR exact match)
- `prototype/src/wet_run/combat/save_v2.py:17-24` — `class SaveData` dataclass with `schema_version/player_data/meta_data/replay_data` (frozen, slots)
- `prototype/src/wet_run/combat/save_v2.py:26-33` — `create_save_data(player_data, meta_data, replay_data=None)` — factory
- `prototype/src/wet_run/combat/save_v2.py:40-67` — `migrate_save(data) -> SaveData` — handles v0→v1 and v1→v2 transitions per ADR §"Migration paths"
- `prototype/src/wet_run/combat/save_v2.py:72-85` — `serialize_save(data) -> str`, `deserialize_save(json_str) -> SaveData` (with auto-migration)
- `prototype/src/wet_run/combat/save_v2.py:89-98` — `get_save_version(json_str)`, `needs_migration(json_str)`, `get_current_version()` helpers
- `prototype/tests/unit/test_save_v2.py` — **17 tests** collected (ADR target: 10+)

**Notes**: All 5 ADR-spec public APIs implemented verbatim. Migration logic covers v0→v1 (metadata conversion) and v1→v2 (replay_data field addition) per ADR §"Migration paths". `replay_data` field defaults to `None` and is omitted from serialization when absent — cloud-ready JSON shape.

**No further action on ADR-0185** — implementation closed, public API stable, tests passing.
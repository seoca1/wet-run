"""Save/Load Migration v3 (ADR-0185, ADR-0196).

Versioned save system. Saves include a schema version number that
allows migration between versions.

v2 → v3 (ADR-0196): ``player_data["colorblind_mode"]`` migrates from a
plain ``bool`` to a 4-value ``str`` (one of ``COLORBLIND_MODES``).
``bool=True`` maps to ``"deuteranopia"`` (most common form per ADR-0196
recommendation) and ``bool=False`` maps to ``"none"``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from .accessibility import COLORBLIND_MODES

SAVE_SCHEMA_VERSION = 3


@dataclass(frozen=True, slots=True)
class SaveData:
    """A versioned save data record."""

    schema_version: int
    player_data: dict[str, object]
    meta_data: dict[str, object]
    replay_data: dict[str, object] | None = None


def create_save_data(
    player_data: dict[str, object],
    meta_data: dict[str, object],
    replay_data: dict[str, object] | None = None,
) -> SaveData:
    """Create a new save data with current schema version."""
    return SaveData(
        schema_version=SAVE_SCHEMA_VERSION,
        player_data=player_data,
        meta_data=meta_data,
        replay_data=replay_data,
    )


def migrate_save(data: dict[str, object]) -> SaveData:
    """Migrate a save dict from any version to current."""
    version: int = cast(int, data.get("schema_version", 0))
    if version >= SAVE_SCHEMA_VERSION:
        player: dict[str, object] = cast(dict[str, object], data.get("player_data", {}))
        meta: dict[str, object] = cast(dict[str, object], data.get("meta_data", {}))
        replay: dict[str, object] | None = cast(dict[str, object] | None, data.get("replay_data"))
        return SaveData(
            schema_version=cast(int, data.get("schema_version", SAVE_SCHEMA_VERSION)),
            player_data=player,
            meta_data=meta,
            replay_data=replay,
        )
    if version == 0:
        if "metadata" in data and "meta_data" not in data:
            data["meta_data"] = data.pop("metadata")
        data["schema_version"] = 1
    if version <= 1:
        if "replay_data" not in data:
            data["replay_data"] = None
        data["schema_version"] = 2
    if version <= 2:
        _migrate_colorblind_field(data)
        data["schema_version"] = 3
    player2: dict[str, object] = cast(dict[str, object], data.get("player_data", {}))
    meta2: dict[str, object] = cast(dict[str, object], data.get("meta_data", {}))
    replay2: dict[str, object] | None = cast(dict[str, object] | None, data.get("replay_data"))
    return SaveData(
        schema_version=SAVE_SCHEMA_VERSION,
        player_data=player2,
        meta_data=meta2,
        replay_data=replay2,
    )


def _migrate_colorblind_field(data: dict[str, object]) -> None:
    """Convert ``player_data['colorblind_mode']`` from bool → str per ADR-0196.

    In-place mutation. ``True``→``"deuteranopia"``, ``False``/missing→``"none"``,
    any other unrecognized value falls back to ``"none"``.
    """
    player_data_raw = data.get("player_data")
    player_data = (
        cast(dict[str, object], player_data_raw) if isinstance(player_data_raw, dict) else {}
    )
    raw_value = player_data.get("colorblind_mode", False)
    if isinstance(raw_value, bool):
        migrated = "deuteranopia" if raw_value else "none"
    elif isinstance(raw_value, str) and raw_value in COLORBLIND_MODES:
        migrated = raw_value
    else:
        migrated = "none"
    player_data["colorblind_mode"] = migrated
    data["player_data"] = player_data


def serialize_save(data: SaveData) -> str:
    """Serialize save data as JSON string."""
    payload = {
        "schema_version": data.schema_version,
        "player_data": data.player_data,
        "meta_data": data.meta_data,
        "replay_data": data.replay_data,
    }
    return json.dumps(payload)


def deserialize_save(json_str: str) -> SaveData:
    """Deserialize save from JSON and migrate to current version."""
    data = json.loads(json_str)
    return migrate_save(data)


def get_save_version(json_str: str) -> int:
    """Return the schema version of a save JSON string."""
    data = json.loads(json_str)
    version: int = data.get("schema_version", 0)
    return version


def needs_migration(json_str: str) -> bool:
    """Return True if the save needs migration."""
    return get_save_version(json_str) < SAVE_SCHEMA_VERSION


def is_current_version(version: int) -> bool:
    """Return True if the version is current."""
    return version >= SAVE_SCHEMA_VERSION


def get_schema_version() -> int:
    """Return the current schema version."""
    return SAVE_SCHEMA_VERSION


__all__ = [
    "SAVE_SCHEMA_VERSION",
    "SaveData",
    "create_save_data",
    "deserialize_save",
    "get_save_version",
    "get_schema_version",
    "is_current_version",
    "migrate_save",
    "needs_migration",
    "serialize_save",
]

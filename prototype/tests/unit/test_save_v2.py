"""Tests for Save/Load Migration v2 (ADR-0185)."""

from __future__ import annotations

import dataclasses

import pytest

from wet_run.combat.save_v2 import (
    SAVE_SCHEMA_VERSION,
    create_save_data,
    deserialize_save,
    get_save_version,
    get_schema_version,
    is_current_version,
    migrate_save,
    needs_migration,
    serialize_save,
)


def test_schema_version_constant() -> None:
    assert SAVE_SCHEMA_VERSION == 2
    assert get_schema_version() == 2


def test_create_save_data() -> None:
    data = create_save_data({"hp": 100}, {"unlocked": ["deck1"]})
    assert data.schema_version == SAVE_SCHEMA_VERSION
    assert data.player_data["hp"] == 100


def test_serialize_save() -> None:
    data = create_save_data({"hp": 100}, {"x": 1})
    json_str = serialize_save(data)
    assert "schema_version" in json_str


def test_deserialize_save() -> None:
    data = create_save_data({"hp": 100}, {"x": 1})
    json_str = serialize_save(data)
    data2 = deserialize_save(json_str)
    assert data2.player_data["hp"] == 100


def test_get_save_version() -> None:
    data = create_save_data({}, {})
    json_str = serialize_save(data)
    assert get_save_version(json_str) == SAVE_SCHEMA_VERSION


def test_needs_migration_current() -> None:
    data = create_save_data({}, {})
    json_str = serialize_save(data)
    assert not needs_migration(json_str)


def test_needs_migration_old() -> None:
    old_json = '{"schema_version": 1, "player_data": {}, "meta_data": {}}'
    assert needs_migration(old_json)


def test_migrate_v0_to_v2() -> None:
    old_data = {"player_data": {"hp": 100}, "metadata": {"x": 1}}
    migrated = migrate_save(old_data)
    assert migrated.schema_version == SAVE_SCHEMA_VERSION
    assert "meta_data" in migrated.meta_data or migrated.meta_data != {}


def test_migrate_v1_to_v2() -> None:
    v1_data = {
        "schema_version": 1,
        "player_data": {"hp": 50},
        "meta_data": {"unlocked": ["deck1"]},
    }
    migrated = migrate_save(v1_data)
    assert migrated.schema_version == SAVE_SCHEMA_VERSION
    assert migrated.replay_data is None


def test_migrate_v2_to_v2() -> None:
    data = create_save_data({"hp": 100}, {"x": 1})
    payload = {
        "schema_version": data.schema_version,
        "player_data": data.player_data,
        "meta_data": data.meta_data,
        "replay_data": data.replay_data,
    }
    migrated = migrate_save(payload)
    assert migrated.schema_version == SAVE_SCHEMA_VERSION


def test_roundtrip_with_replay() -> None:
    data = create_save_data(
        {"hp": 100},
        {"x": 1},
        replay_data={"events": []},
    )
    json_str = serialize_save(data)
    data2 = deserialize_save(json_str)
    assert data2.replay_data == {"events": []}


def test_is_current_version() -> None:
    assert is_current_version(SAVE_SCHEMA_VERSION)
    assert is_current_version(3)
    assert not is_current_version(1)
    assert not is_current_version(0)


def test_save_data_immutable() -> None:
    data = create_save_data({}, {})
    try:
        data.schema_version = 99  # type: ignore[misc]
        pytest.fail("Should be frozen")
    except (AttributeError, dataclasses.FrozenInstanceError):
        pass


def test_migrate_without_schema_version() -> None:
    data = {"player_data": {}, "meta_data": {}}
    migrated = migrate_save(data)
    assert migrated.schema_version == SAVE_SCHEMA_VERSION


def test_migrate_preserves_player_data() -> None:
    data = {"player_data": {"hp": 100, "max_hp": 200}, "meta_data": {}}
    migrated = migrate_save(data)
    assert migrated.player_data["hp"] == 100
    assert migrated.player_data["max_hp"] == 200


def test_migrate_preserves_replay_data() -> None:
    data = {
        "schema_version": 2,
        "player_data": {},
        "meta_data": {},
        "replay_data": {"events": [{"type": "kill"}]},
    }
    migrated = migrate_save(data)
    assert migrated.replay_data is not None
    assert migrated.replay_data["events"][0]["type"] == "kill"


def test_serialize_deserialize_roundtrip() -> None:
    data = create_save_data({"hp": 100}, {"x": 1})
    json_str = serialize_save(data)
    data2 = deserialize_save(json_str)
    assert data2.player_data == data.player_data
    assert data2.meta_data == data.meta_data
    assert data2.schema_version == data.schema_version

"""Tests for engine.meta_state_manager — disk persistence with atomic writes.

Coverage target for src/wet_run/engine/meta_state_manager.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from wet_run.engine.meta_state_manager import (
    DEFAULT_META_STATE_FILENAME,
    default_meta_state_path,
    load_meta_state,
    reset_meta_state,
    save_meta_state,
)
from wet_run.run.meta_state import META_STATE_VERSION, MetaState
from wet_run.run.reputation import ReputationState

# ----------------------------------------------------------------------------
# default_meta_state_path
# ----------------------------------------------------------------------------


class TestDefaultMetaStatePath:
    def test_returns_path_under_data_dir(self, tmp_path: Path):
        result = default_meta_state_path(tmp_path)
        assert result == tmp_path / "saves" / DEFAULT_META_STATE_FILENAME

    def test_filename_constant(self):
        assert DEFAULT_META_STATE_FILENAME == "meta_state.json"


# ----------------------------------------------------------------------------
# load_meta_state
# ----------------------------------------------------------------------------


class TestLoadMetaState:
    def test_missing_file_returns_empty(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        state = load_meta_state(path)
        assert isinstance(state, MetaState)
        assert state.version == META_STATE_VERSION

    def test_loads_valid_file(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        original = MetaState()
        save_meta_state(original, path)

        loaded = load_meta_state(path)
        assert loaded.version == original.version

    def test_corrupt_json_returns_empty(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        path.write_text("{not valid json", encoding="utf-8")
        state = load_meta_state(path)
        assert isinstance(state, MetaState)

    def test_non_dict_json_returns_empty(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        state = load_meta_state(path)
        assert isinstance(state, MetaState)

    def test_newer_version_returns_empty(self, tmp_path: Path):
        """File with version > current META_STATE_VERSION should be rejected."""
        path = tmp_path / "meta_state.json"
        path.write_text(
            json.dumps({"version": META_STATE_VERSION + 10, "reputation": {}}),
            encoding="utf-8",
        )
        state = load_meta_state(path)
        # Should return empty default due to version mismatch
        assert state.version == META_STATE_VERSION

    def test_older_version_accepted(self, tmp_path: Path):
        """File with version <= current META_STATE_VERSION is loaded."""
        path = tmp_path / "meta_state.json"
        path.write_text(
            json.dumps(
                {
                    "version": META_STATE_VERSION - 1 if META_STATE_VERSION > 0 else 0,
                    "reputation": {},
                }
            ),
            encoding="utf-8",
        )
        state = load_meta_state(path)
        # Older or same version is accepted
        assert isinstance(state, MetaState)


# ----------------------------------------------------------------------------
# save_meta_state
# ----------------------------------------------------------------------------


class TestSaveMetaState:
    def test_creates_file(self, tmp_path: Path):
        path = tmp_path / "saves" / "meta_state.json"
        state = MetaState()
        save_meta_state(state, path)
        assert path.exists()

    def test_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "deep" / "nested" / "saves" / "meta_state.json"
        state = MetaState()
        save_meta_state(state, path)
        assert path.exists()
        assert path.parent.exists()

    def test_roundtrip_data(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        original = MetaState()
        original.reputation = ReputationState()
        save_meta_state(original, path)

        loaded = load_meta_state(path)
        assert loaded.version == original.version

    def test_uses_atomic_write(self, tmp_path: Path):
        """Verify atomic write — temp file should not remain after write."""
        path = tmp_path / "meta_state.json"
        state = MetaState()
        save_meta_state(state, path)

        # Temp file should be cleaned up after os.replace
        tmp_file = path.with_suffix(path.suffix + ".tmp")
        assert not tmp_file.exists()

    def test_writes_valid_json(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        save_meta_state(MetaState(), path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "version" in data
        assert "reputation" in data

    def test_overwrites_existing(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        path.write_text('{"old": "data"}', encoding="utf-8")
        save_meta_state(MetaState(), path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert "version" in loaded
        assert "old" not in loaded


# ----------------------------------------------------------------------------
# reset_meta_state
# ----------------------------------------------------------------------------


class TestResetMetaState:
    def test_deletes_existing_file(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        path.write_text('{"version": 1}', encoding="utf-8")
        assert path.exists()

        reset_meta_state(path)
        assert not path.exists()

    def test_no_error_on_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        # Should not raise
        reset_meta_state(path)

    def test_idempotent(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        path.write_text("{}", encoding="utf-8")
        reset_meta_state(path)
        reset_meta_state(path)  # Second call on already-deleted
        # No error
        assert not path.exists()


# ----------------------------------------------------------------------------
# Integration: save → load → reset cycle
# ----------------------------------------------------------------------------


class TestSaveLoadResetCycle:
    def test_full_cycle(self, tmp_path: Path):
        path = tmp_path / "saves" / "meta_state.json"

        # Save new state
        save_meta_state(MetaState(), path)
        assert path.exists()

        # Load verifies data integrity
        loaded = load_meta_state(path)
        assert loaded.version == META_STATE_VERSION

        # Reset removes file
        reset_meta_state(path)
        assert not path.exists()

        # Load after reset returns empty default
        fresh = load_meta_state(path)
        assert fresh.version == META_STATE_VERSION

    def test_persists_reputation_changes(self, tmp_path: Path):
        path = tmp_path / "meta_state.json"
        state = MetaState()
        # Future: reputation changes can be persisted
        save_meta_state(state, path)

        loaded = load_meta_state(path)
        assert loaded.reputation is not None

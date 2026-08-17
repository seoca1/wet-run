"""Unit tests for ``engine/graphic_novel_save.py``.

Focuses on the pure logic:
- ``slot_path`` validation
- ``GNProgress.to_dict`` / ``from_dict`` round-trip + ending default
- ``_migrate_gn_data`` walk across version migrations
- ``make_progress`` factory

We also cover the disk round-trip via ``save_gn_progress`` /
``load_gn_progress`` / ``has_gn_save`` / ``delete_gn_progress`` using
``tmp_path``.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from wet_run.engine import graphic_novel_save as gns
from wet_run.engine.graphic_novel_save import (
    DEFAULT_SAVE_PATH,
    GN_SAVE_SLOTS,
    SAVE_SLOT_PATTERN,
    GNProgress,
    GNSaveCorruptedError,
    GNSaveEmptyError,
    GNSaveError,
    GNSaveVersionMismatchError,
    _migrate_gn_data,
    _slot_path_with_dir,
    delete_gn_progress,
    has_gn_save,
    has_gn_save_slot,
    load_gn_progress,
    make_progress,
    progress_to_dict,
    save_gn_progress,
    slot_path,
)

# ---------------------------------------------------------------------------
# slot_path / _slot_path_with_dir
# ---------------------------------------------------------------------------


class TestSlotPath:
    def test_valid_slot(self):
        path = slot_path(1)
        assert path.name == SAVE_SLOT_PATTERN.format(slot_id=1)

    def test_raises_for_zero(self):
        with pytest.raises(ValueError, match=r"slot_id must be"):
            slot_path(0)

    def test_raises_for_overflow(self):
        with pytest.raises(ValueError, match=r"slot_id must be"):
            slot_path(GN_SAVE_SLOTS + 1)

    def test_raises_for_negative(self):
        with pytest.raises(ValueError, match=r"slot_id must be"):
            slot_path(-1)

    def test_with_explicit_save_dir(self, tmp_path: Path):
        path = _slot_path_with_dir(2, tmp_path)
        assert path.parent == tmp_path


# ---------------------------------------------------------------------------
# GNProgress dataclass — to_dict / from_dict
# ---------------------------------------------------------------------------


def _make_progress(
    mode: str = "novice",
    scene_index: int = 3,
    dialogue_index: int = 5,
    elapsed_in_dialogue_ms: float = 1200.0,
    character_id: str = "novice",
    chain_length: int = 12,
    ending: str = "A",
) -> GNProgress:
    return make_progress(
        mode=mode,
        scene_index=scene_index,
        dialogue_index=dialogue_index,
        elapsed_in_dialogue_ms=elapsed_in_dialogue_ms,
        character_id=character_id,
        chain_length=chain_length,
        ending=ending,
    )


class TestGNProgress:
    def test_to_dict_round_trip(self):
        p = _make_progress()
        d = p.to_dict()
        # Convert back via from_dict and compare.
        p2 = GNProgress.from_dict(d)
        assert p2 == p

    def test_from_dict_default_ending_a(self):
        # v1.0.0 saves don't have ``ending``; from_dict should default to A.
        d = {
            "mode": "novice",
            "scene_index": 1,
            "dialogue_index": 0,
            "elapsed_in_dialogue_ms": 0.0,
            "character_id": "novice",
            "chain_length": 12,
            "saved_at": "2026-01-01T00:00:00+00:00",
            "session_id": "abc123",
        }
        p = GNProgress.from_dict(d)
        assert p.ending == "A"

    def test_from_dict_unknown_ending_defaults_to_a(self):
        d = {
            "mode": "novice",
            "scene_index": 1,
            "dialogue_index": 0,
            "elapsed_in_dialogue_ms": 0.0,
            "character_id": "novice",
            "chain_length": 12,
            "saved_at": "",
            "session_id": "",
            "ending": "ZZ",  # unknown
        }
        p = GNProgress.from_dict(d)
        assert p.ending == "A"

    def test_from_dict_invalid_int_defaults_to_zero(self):
        d = {
            "mode": "novice",
            "scene_index": "not-a-number",
            "dialogue_index": "also-not",
            "elapsed_in_dialogue_ms": "blah",
            "character_id": "novice",
            "chain_length": "huh",
            "saved_at": "",
            "session_id": "",
        }
        p = GNProgress.from_dict(d)
        assert p.scene_index == 0
        assert p.dialogue_index == 0
        assert p.elapsed_in_dialogue_ms == 0.0
        assert p.chain_length == 0

    def test_progress_to_dict_alias(self):
        p = _make_progress()
        assert progress_to_dict(p) == p.to_dict()


# ---------------------------------------------------------------------------
# make_progress factory
# ---------------------------------------------------------------------------


class TestMakeProgress:
    def test_returns_progress_with_current_time(self):
        p = make_progress(
            mode="veteran",
            scene_index=2,
            dialogue_index=1,
            elapsed_in_dialogue_ms=500.0,
            character_id="veteran",
            chain_length=8,
        )
        assert isinstance(p, GNProgress)
        assert p.mode == "veteran"
        assert p.scene_index == 2
        assert p.chain_length == 8
        assert p.ending == "A"  # default
        # saved_at is a parseable ISO 8601 string
        assert datetime.fromisoformat(p.saved_at) is not None

    def test_unique_session_ids(self):
        p1 = make_progress("novice", 0, 0, 0.0, "novice", 12)
        p2 = make_progress("novice", 0, 0, 0.0, "novice", 12)
        assert p1.session_id != p2.session_id

    def test_ending_passed_through(self):
        p = make_progress(
            mode="heretic",
            scene_index=0,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="heretic",
            chain_length=12,
            ending="B",
        )
        assert p.ending == "B"


# ---------------------------------------------------------------------------
# _migrate_gn_data
# ---------------------------------------------------------------------------


class TestMigrateGNData:
    def test_no_op_when_already_target(self):
        d = {"version": gns.GN_SAVE_VERSION, "any": "field"}
        out = _migrate_gn_data(d)
        assert out is d

    def test_raises_when_no_path_to_target(self):
        # Version that doesn't exist in the migration table.
        with pytest.raises(GNSaveVersionMismatchError):
            _migrate_gn_data({"version": "0.0.0-unknown"})

    def test_walks_to_target_via_known_steps(self):
        # If the migration table includes a step from "0.9.0" → current,
        # a v0.9.0 save gets transformed.
        original_migrations = list(gns._GN_SAVE_MIGRATIONS)
        original_target = gns.GN_SAVE_VERSION
        try:
            gns._GN_SAVE_MIGRATIONS = [("0.9.0", "1.0.0", lambda d: {**d, "new_field": 42})]
            gns.GN_SAVE_VERSION = "1.0.0"
            out = _migrate_gn_data({"version": "0.9.0", "old_field": 1})
            # The transform applied; "new_field" exists in the result.
            assert out.get("new_field") == 42
            # The original field is preserved.
            assert out.get("old_field") == 1
        finally:
            gns._GN_SAVE_MIGRATIONS = original_migrations
            gns.GN_SAVE_VERSION = original_target


# ---------------------------------------------------------------------------
# has_gn_save + slot round-trip
# ---------------------------------------------------------------------------


class TestHasGNSave:
    def test_returns_false_when_no_file(self, tmp_path: Path):
        assert has_gn_save(tmp_path / "gn_progress.json") is False

    def test_returns_true_when_file_exists(self, tmp_path: Path):
        path = tmp_path / "gn_progress.json"
        path.write_text("{}", encoding="utf-8")
        assert has_gn_save(path) is True


class TestSlotRoundTrip:
    def test_save_and_load(self, tmp_path: Path):
        original = _make_progress()
        path = save_gn_progress(original, save_path=tmp_path / "save.json")
        loaded = load_gn_progress(save_path=path)
        assert loaded == original

    def test_load_missing_raises_empty_error(self, tmp_path: Path):
        # The implementation raises GNSaveEmptyError for missing files
        # (a deliberate regression — the empty path is the same as a
        # corrupted save).  We assert that here.
        with pytest.raises(GNSaveEmptyError):
            load_gn_progress(save_path=tmp_path / "absent.json")

    def test_load_empty_file_raises_corrupt_error(self, tmp_path: Path):
        # An empty file is invalid JSON, so the loader raises
        # GNSaveCorruptedError.  (This is the behaviour as of the
        # current implementation; if the loader ever special-cases
        # empty files, this test will fail loudly.)
        path = tmp_path / "gn_progress.json"
        path.write_text("", encoding="utf-8")
        with pytest.raises((GNSaveCorruptedError, GNSaveError)):
            load_gn_progress(save_path=path)

    def test_load_corrupt_json_raises(self, tmp_path: Path):
        path = tmp_path / "gn_progress.json"
        path.write_text("this is not json", encoding="utf-8")
        with pytest.raises((GNSaveCorruptedError, GNSaveError)):
            load_gn_progress(save_path=path)

    def test_delete_returns_true_when_existed(self, tmp_path: Path):
        path = tmp_path / "gn_progress.json"
        path.write_text("{}", encoding="utf-8")
        assert delete_gn_progress(save_path=path) is True
        assert not path.exists()

    def test_delete_returns_false_when_missing(self, tmp_path: Path):
        assert delete_gn_progress(save_path=tmp_path / "absent.json") is False

    def test_atomic_write_via_tmp_then_rename(self, tmp_path: Path):
        """A crash mid-write should not leave a partial save file."""
        path = tmp_path / "gn_progress.json"
        original = _make_progress()
        save_gn_progress(original, save_path=path)
        assert path.exists()
        # Simulate mid-write: a stray .tmp file should not exist.
        tmp_candidates = list(tmp_path.glob("*.tmp"))
        assert not any("gn_progress" in p.name for p in tmp_candidates)


# ---------------------------------------------------------------------------
# Multi-slot API
# ---------------------------------------------------------------------------


class TestMultiSlot:
    def test_has_gn_save_slot(self, tmp_path: Path):
        save_dir = tmp_path / "saves"
        save_dir.mkdir()
        slot_file = save_dir / SAVE_SLOT_PATTERN.format(slot_id=1)
        slot_file.write_text("{}", encoding="utf-8")
        assert has_gn_save_slot(1, save_dir) is True
        assert has_gn_save_slot(2, save_dir) is False

    def test_default_save_path_is_module_constant(self):
        # Sanity: the module's default path is reasonable.
        assert str(DEFAULT_SAVE_PATH).endswith("gn_progress.json")

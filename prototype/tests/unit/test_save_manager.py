"""Tests for the save/load system.

Verifies:
- SaveManager save/load roundtrip preserves all relevant state
- Save metadata extraction
- Slot management (list, has, delete)
- Atomic write (no partial files on crash)
- Version mismatch handling
- Corrupted file detection
- Restore integrates with AppState
- Auto-save triggers (JACK_OUT, DEATH)
- Default save directory (platform-appropriate)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from wet_run.engine import (
    AppState,
    SaveCorruptedError,
    SaveError,
    SaveManager,
    SaveMetadata,
    SaveSlotEmptyError,
    SaveVersionMismatchError,
    ScreenKind,
)
from wet_run.engine.save_manager import SAVE_FORMAT_VERSION
from wet_run.matrix.node import ZoneDepth
from wet_run.missions.mission import Mission, Rewards
from wet_run.run import Stage, start_run


def _make_state(
    inventory: dict[str, int] | None = None,
    credits: int = 0,
    stage: Stage = Stage.MEET_NPC,
) -> AppState:
    """Create a test AppState with a run in progress."""
    state = AppState()
    state.inventory = inventory or {}
    state.credits = credits
    state.run_state = start_run("first_jack")
    state.run_state.current_stage = stage
    state.current_mission = Mission(
        id="first_jack",
        title="Test Mission",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        rewards=Rewards(credits=500, materials={"data_fragment": 2}),
    )
    state.player_grade = 1
    state.current_node_id = "data1"
    state.defeated_nodes = {"ice1"}
    state.extracted_nodes = {"data1"}
    state.mission_progress = {"defeat": 1, "extract_data": 1}
    return state


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    """Provide an isolated save directory for each test."""
    save_path = tmp_path / "saves"
    save_path.mkdir()
    return save_path


class TestSaveManagerBasics:
    """Basic SaveManager operations."""

    def test_creates_dir_on_init(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "fresh_saves"
        SaveManager(save_dir=new_dir)
        assert new_dir.exists()

    def test_slot_path_validates(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        with pytest.raises(ValueError, match="slot must be"):
            manager._slot_path(-1)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="slot must be"):
            manager._slot_path(11)  # type: ignore[arg-type]  # Phase 7.3: MAX_SLOTS=10

    def test_has_save_false_for_empty(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        assert not manager.has_save(1)
        assert not manager.has_save(5)

    def test_has_save_true_after_save(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        manager.save(1, state)
        assert manager.has_save(1)
        assert not manager.has_save(2)


class TestSave:
    """save() creates a valid file with correct content."""

    def test_save_creates_file(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=300, inventory={"ice_shard": 1})
        manager.save(1, state)
        assert manager.has_save(1)
        file = save_dir / "slot_1.json"
        assert file.exists()
        assert file.stat().st_size > 0

    def test_save_returns_metadata(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=300)
        meta = manager.save(1, state)
        assert isinstance(meta, SaveMetadata)
        assert meta.slot == 1
        assert meta.exists is True
        assert meta.is_compatible is True
        assert meta.credits == 300
        assert meta.mission_id == "first_jack"

    def test_save_persists_credits(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=1234)
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.app_state["credits"] == 1234

    def test_save_persists_inventory(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(inventory={"ice_shard": 5, "data_fragment": 2})
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.app_state["inventory"] == {"ice_shard": 5, "data_fragment": 2}

    def test_save_persists_stage(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(stage=Stage.JACK_OUT)
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.run_state["current_stage"] == "jack_out"

    def test_save_persists_completed_stages(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        state.run_state.completed_stages = (Stage.MEET_NPC, Stage.EXTRACT_DATA)
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.run_state["completed_stages"] == ["meet_npc", "extract_data"]

    def test_save_persists_mission(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.mission is not None
        assert loaded.mission["id"] == "first_jack"
        assert loaded.mission["title"] == "Test Mission"

    def test_save_persists_mission_progress(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        state.mission_progress = {"defeat": 3, "extract_data": 1}
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.app_state["mission_progress"] == {"defeat": 3, "extract_data": 1}

    def test_save_overwrites_previous(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=100)
        manager.save(1, state)
        state.credits = 200
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.app_state["credits"] == 200

    def test_save_validates_state_type(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        with pytest.raises(TypeError):
            manager.save(1, "not a state")  # type: ignore[arg-type]

    def test_save_requires_run_state(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = AppState()
        state.run_state = None
        with pytest.raises(SaveError):
            manager.save(1, state)


class TestLoad:
    """load() retrieves saved data correctly."""

    def test_load_empty_slot_raises(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        with pytest.raises(SaveSlotEmptyError):
            manager.load(1)

    def test_load_returns_saved_run(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=500)
        manager.save(1, state)
        loaded = manager.load(1)
        assert loaded.version == SAVE_FORMAT_VERSION
        assert loaded.saved_at != ""
        assert loaded.run_state is not None
        assert loaded.app_state is not None

    def test_load_corrupted_file(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        (save_dir / "slot_1.json").write_text("{ this is not valid json }", encoding="utf-8")
        with pytest.raises(SaveCorruptedError):
            manager.load(1)

    def test_load_version_mismatch(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        # Create a save with wrong version
        wrong = {
            "version": "99.0.0",
            "saved_at": "2026-06-18T20:00:00Z",
            "run_state": {"current_stage": "pending"},
            "mission": None,
            "app_state": {},
            "metadata": {},
        }
        (save_dir / "slot_1.json").write_text(json.dumps(wrong), encoding="utf-8")
        with pytest.raises(SaveVersionMismatchError):
            manager.load(1)


class TestRestoreState:
    """restore_state() modifies AppState in-place."""

    def test_restores_reputation(self, save_dir: Path) -> None:
        """Faction reputation persists across save/restore."""
        from wet_run.matrix.node import Faction

        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=500)
        # Build a reputation profile (within clamp range ±25)
        state.reputation.adjust(Faction.HOSAKA, 20, source="mission:ta_heist")
        state.reputation.adjust(Faction.MAAS, -25, source="combat:black_ice")
        manager.save(1, state)

        # Restore into fresh state — reputation must come back
        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.reputation.get(Faction.HOSAKA).score == 20
        assert new_state.reputation.get(Faction.MAAS).score == -25
        assert new_state.reputation.get(Faction.HOSAKA).tier() == "TRUSTED"
        assert new_state.reputation.get(Faction.MAAS).tier() == "HOSTILE"

    def test_restores_reputation_missing_field(self, save_dir: Path) -> None:
        """Legacy save without reputation field → empty state, no crash."""
        from wet_run.run.reputation import ReputationState

        manager = SaveManager(save_dir=save_dir)
        # Manually save with no reputation field (simulating old save)
        path = save_dir / "slot_1.json"
        legacy = {
            "version": "0.1.0",
            "saved_at": "2026-01-01T00:00:00Z",
            "elapsed_seconds": 0,
            "run_state": {"current_stage": "pending", "mission_id": "first_jack"},
            "app_state": {
                "inventory": {},
                "credits": 0,
                "defeated_nodes": [],
                "extracted_nodes": [],
                "mission_progress": {},
            },
            "metadata": {},
        }
        path.write_text(json.dumps(legacy), encoding="utf-8")

        new_state = AppState()
        manager.restore_state(1, new_state)
        # Default empty reputation — no crash, no factions touched.
        assert isinstance(new_state.reputation, ReputationState)
        assert new_state.reputation.all_factions() == []

    def test_restores_run_state(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(stage=Stage.DEFEAT_ICE)
        state.run_state.completed_stages = (Stage.MEET_NPC, Stage.EXTRACT_DATA)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.run_state is not None
        assert new_state.run_state.current_stage is Stage.DEFEAT_ICE
        assert Stage.MEET_NPC in new_state.run_state.completed_stages
        assert Stage.EXTRACT_DATA in new_state.run_state.completed_stages

    def test_restores_inventory_and_credits(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=500, inventory={"ice_shard": 3})
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.credits == 500
        assert new_state.inventory == {"ice_shard": 3}

    def test_restores_mission_progress(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        state.mission_progress = {"defeat": 2, "extract_data": 1}
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.mission_progress == {"defeat": 2, "extract_data": 1}

    def test_restores_node_states(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        state.current_node_id = "data1"
        state.defeated_nodes = {"ice1", "ice2"}
        state.extracted_nodes = {"data1"}
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.current_node_id == "data1"
        assert new_state.defeated_nodes == {"ice1", "ice2"}
        assert new_state.extracted_nodes == {"data1"}

    def test_restores_screen_for_cyberspace_stage(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(stage=Stage.MEET_NPC)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        # No matrix, so should go to HUB
        assert new_state.screen is ScreenKind.HUB

    def test_restores_screen_for_jack_out(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(stage=Stage.JACK_OUT)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        # Post-combat stages go to HUB
        assert new_state.screen is ScreenKind.HUB

    def test_restores_screen_for_death(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(stage=Stage.FAILED)
        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.screen is ScreenKind.DEATH

    def test_clears_matrix_on_restore(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        state.matrix = "fake matrix"  # type: ignore[assignment]
        state.cyberspace_layouts = {"x": 1}
        state.combat_state = "fake combat"  # type: ignore[assignment]
        manager.save(1, state)

        new_state = AppState()
        new_state.matrix = "stale"  # type: ignore[assignment]
        new_state.cyberspace_layouts = {"stale": 1}
        manager.restore_state(1, new_state)
        # Matrix-related state should be cleared (re-jack-in required)
        assert new_state.matrix is None
        assert new_state.cyberspace_layouts is None
        assert new_state.combat_state is None

    def test_appends_status_message(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        manager.save(1, state)
        new_state = AppState()
        manager.restore_state(1, new_state)
        assert any("loaded from slot 1" in m for m in new_state.status_messages)

    def test_round_trips_scalar_gameplay_fields(self, save_dir: Path) -> None:
        """Regression (GA-004): scalar gameplay fields must round-trip
        through save/restore. Prior to the fix, fields like is_dead,
        death_reason, mutator multipliers, and salvage counters were
        silently dropped on save (saved_at had wrong values), causing
        progression loss on reload.
        """
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=100)
        state.is_dead = True
        state.death_reason = "Test death"
        state.death_cause = "Black ICE"
        state.heal_disabled = True
        state.alarm_speed_multiplier = 2.5
        state.encounter_multiplier = 3
        state.tempo_mode = "fast"
        state.salvage_fragments = 42
        state.pending_salvage = True
        state.phase4_triggered = True
        state.faction_tension_probability_boost = 0.75
        state.near_miss_triggered = True

        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.is_dead is True
        assert new_state.death_reason == "Test death"
        assert new_state.death_cause == "Black ICE"
        assert new_state.heal_disabled is True
        assert new_state.alarm_speed_multiplier == 2.5
        assert new_state.encounter_multiplier == 3
        assert new_state.tempo_mode == "fast"
        assert new_state.salvage_fragments == 42
        assert new_state.pending_salvage is True
        assert new_state.phase4_triggered is True
        assert new_state.faction_tension_probability_boost == 0.75
        assert new_state.near_miss_triggered is True

    def test_round_trips_run_state_chapter_progression(self, save_dir: Path) -> None:
        """Regression (GA-005): chapter_state and current_phase_index
        must round-trip through save/restore. Prior to the fix, both
        were silently reset to defaults on load, forcing the player
        to replay chapters from scratch after every save.
        """
        from wet_run.run.state import ChapterState

        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=100)
        state.run_state.chapter_state = ChapterState.IN_CHAPTER_3
        state.run_state.current_phase_index = 5

        manager.save(1, state)

        new_state = AppState()
        manager.restore_state(1, new_state)
        assert new_state.run_state.chapter_state is ChapterState.IN_CHAPTER_3
        assert new_state.run_state.current_phase_index == 5


class TestSlotManagement:
    """list_slots, get_metadata, delete."""

    def test_list_slots_includes_empty(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        slots = manager.list_slots()
        assert len(slots) == 10  # MAX_SLOTS (Phase 7.3: 5 → 10)
        for meta in slots:
            assert meta.exists is False

    def test_list_slots_shows_existing(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        manager.save(2, _make_state())
        manager.save(4, _make_state())
        slots = manager.list_slots()
        assert slots[0].exists is False  # slot 1
        assert slots[1].exists is True  # slot 2
        assert slots[2].exists is False  # slot 3
        assert slots[3].exists is True  # slot 4
        assert slots[4].exists is False  # slot 5

    def test_get_metadata_for_empty_slot(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        meta = manager.get_metadata(1)
        assert meta.exists is False
        assert meta.slot == 1
        assert meta.is_compatible is False

    def test_get_metadata_for_existing_slot(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=500, stage=Stage.JACK_OUT)
        manager.save(1, state)
        meta = manager.get_metadata(1)
        assert meta.exists is True
        assert meta.is_compatible is True
        assert meta.credits == 500
        assert meta.current_stage == "jack_out"
        assert meta.mission_id == "first_jack"
        assert meta.size_bytes > 0

    def test_delete_existing(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        manager.save(1, _make_state())
        assert manager.has_save(1)
        assert manager.delete(1) is True
        assert not manager.has_save(1)

    def test_delete_empty_returns_false(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        assert manager.delete(1) is False


class TestQuickSaveLoad:
    """quick_save / quick_load use slot 1."""

    def test_quick_save_to_slot_1(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state()
        manager.quick_save(state)
        assert manager.has_save(1)

    def test_quick_load_from_slot_1(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        state = _make_state(credits=999)
        manager.save(1, state)
        new_state = AppState()
        manager.quick_load(new_state)
        assert new_state.credits == 999

    def test_quick_load_empty_raises(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        new_state = AppState()
        with pytest.raises(SaveSlotEmptyError):
            manager.quick_load(new_state)


class TestAtomicWrite:
    """save() uses atomic write (no partial files on crash)."""

    def test_no_temp_file_left_on_success(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        manager.save(1, _make_state())
        # Should not have any .tmp files
        tmps = list(save_dir.glob("*.tmp"))
        assert tmps == []

    def test_atomic_write_overwrites_safely(self, save_dir: Path) -> None:
        manager = SaveManager(save_dir=save_dir)
        manager.save(1, _make_state(credits=100))
        manager.save(1, _make_state(credits=200))
        manager.save(1, _make_state(credits=300))
        loaded = manager.load(1)
        assert loaded.app_state["credits"] == 300


class TestDefaultSaveDir:
    """_default_save_dir returns platform-appropriate path."""

    def test_linux_uses_xdg(self) -> None:
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}, clear=False):
            from wet_run.engine.save_manager import _default_save_dir

            path = _default_save_dir()
            assert "wet_run" in str(path)
            assert "saves" in str(path)

    def test_linux_falls_back_to_local_share(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "XDG_DATA_HOME"}
        with patch.dict(os.environ, env, clear=True):
            from wet_run.engine.save_manager import _default_save_dir

            path = _default_save_dir()
            assert ".local" in str(path) or "share" in str(path)


class TestSaveMigration:
    """Save format migrations auto-upgrade older versions on load."""

    def test_legacy_save_without_version_loads(self, save_dir: Path) -> None:
        """Pre-0.1.0 saves had no version key; auto-upgrade."""
        manager = SaveManager(save_dir=save_dir)
        # Write a "legacy" save (no version field, missing common fields)
        legacy_data = {
            "saved_at": "2026-05-01T10:00:00Z",
            "elapsed_seconds": 100,
            "run_state": {"current_stage": "meet_npc", "mission_id": "first_jack"},
            "app_state": {"inventory": {"data_fragment": 1}, "credits": 250},
            "metadata": {},
        }
        (save_dir / "slot_1.json").write_text(json.dumps(legacy_data), encoding="utf-8")

        loaded = manager.load(1)
        assert loaded.version == SAVE_FORMAT_VERSION
        assert loaded.app_state["credits"] == 250
        assert loaded.app_state["inventory"]["data_fragment"] == 1

    def test_legacy_via_restore_state(self, save_dir: Path) -> None:
        """restore_state() works on legacy saves too."""
        manager = SaveManager(save_dir=save_dir)
        legacy_data = {
            "saved_at": "2026-05-01T10:00:00Z",
            "elapsed_seconds": 50,
            "run_state": {"current_stage": "meet_npc", "mission_id": "first_jack"},
            "app_state": {"inventory": {}, "credits": 100},
            "metadata": {"player_grade": 2},
        }
        (save_dir / "slot_1.json").write_text(json.dumps(legacy_data), encoding="utf-8")

        state = AppState()
        manager.restore_state(1, state)
        assert state.credits == 100
        assert state.player_grade == 2

    def test_unknown_version_still_raises(self, save_dir: Path) -> None:
        """Version with no migration path → SaveVersionMismatchError."""
        from wet_run.engine.save_manager import (
            _migrate_save_data,
        )

        # Synthesise a future version that's not in the migration chain.
        future = {"version": "99.0.0", "app_state": {}}
        with pytest.raises(SaveVersionMismatchError, match="No migration path"):
            _migrate_save_data(future)

    def test_current_version_passes_through_unchanged(self, save_dir: Path) -> None:
        """Current version bypasses migration (no-op roundtrip)."""
        from wet_run.engine.save_manager import _migrate_save_data

        data = {"version": SAVE_FORMAT_VERSION, "saved_at": "x"}
        out = _migrate_save_data(data)
        assert out is data or out == data

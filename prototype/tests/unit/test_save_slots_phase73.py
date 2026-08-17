"""Tests for 10-slot + auto-save expansion (Phase 7.3).

Phase 7.3 changes:
  - MAX_SLOTS: 5 → 10 (manual save slots)
  - AUTO_SAVE_SLOT = 0 (separate autosave.json)
  - autosave() method
  - list_all() method (auto + 10 manual)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wet_run.engine.save_manager import (
    AUTO_SAVE_FILENAME,
    AUTO_SAVE_SLOT,
    MAX_SLOTS,
    SaveManager,
)


class TestTenSlots:
    def test_max_slots_is_ten(self):
        assert MAX_SLOTS == 10, "Phase 7.3 expanded MAX_SLOTS from 5 to 10"

    def test_auto_save_slot_is_separate(self):
        assert AUTO_SAVE_SLOT == 0

    def test_slot_paths(self, save_dir: Path):
        manager = SaveManager(save_dir=save_dir)
        # Manual slots use slot_N.json
        for n in range(1, MAX_SLOTS + 1):
            assert manager._slot_path(n).name == f"slot_{n}.json"
        # Auto-save uses autosave.json
        assert manager._slot_path(AUTO_SAVE_SLOT).name == AUTO_SAVE_FILENAME

    def test_slot_validation(self, save_dir: Path):
        manager = SaveManager(save_dir=save_dir)
        # Outside range
        with pytest.raises(ValueError, match="slot must be"):
            manager._slot_path(-1)
        with pytest.raises(ValueError, match="slot must be"):
            manager._slot_path(MAX_SLOTS + 1)


class TestAutoSave:
    def test_autosave_creates_file(self, save_dir: Path, app_state):
        manager = SaveManager(save_dir=save_dir)
        assert not manager.has_autosave()
        manager.autosave(app_state)
        assert manager.has_autosave()
        # Auto-save file should exist
        assert (save_dir / AUTO_SAVE_FILENAME).exists()

    def test_autosave_overwrites_previous(self, save_dir: Path, app_state):
        manager = SaveManager(save_dir=save_dir)
        manager.autosave(app_state)
        path = save_dir / AUTO_SAVE_FILENAME
        first_mtime = path.stat().st_mtime
        # Wait briefly
        import time

        time.sleep(0.01)
        manager.autosave(app_state)
        second_mtime = path.stat().st_mtime
        assert second_mtime >= first_mtime

    def test_autosave_separate_from_manual(self, save_dir: Path, app_state):
        manager = SaveManager(save_dir=save_dir)
        manager.autosave(app_state)
        # Manual slot 1 should be empty
        assert not manager.has_save(1)
        assert manager.has_autosave()

    def test_list_all_includes_autosave_first(self, save_dir: Path, app_state):
        manager = SaveManager(save_dir=save_dir)
        manager.autosave(app_state)
        manager.save(3, app_state)
        all_saves = manager.list_all()
        # 1 auto + 10 manual = 11
        assert len(all_saves) == 1 + MAX_SLOTS
        # First entry is auto-save (slot 0)
        assert all_saves[0].slot == AUTO_SAVE_SLOT


@pytest.fixture
def app_state():
    """AppState with a run in progress for save/load tests."""
    from wet_run.engine.state import AppState
    from wet_run.matrix.node import ZoneDepth
    from wet_run.missions.mission import Mission, Rewards
    from wet_run.run.helpers import start_run

    state = AppState()
    state.inventory = {}
    state.credits = 100
    state.run_state = start_run("first_jack")
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
    return state


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    """Temporary save directory."""
    save = tmp_path / "saves"
    save.mkdir(parents=True, exist_ok=True)
    return save

"""Tests for Phase 16 endings persistence (ADR-0192).

Verifies that ``AppState.ending_choice`` survives a save/restore
round-trip via SaveManager. The choice is stored in the save's
``metadata`` dict alongside ``player_grade`` and ``screen``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.state import AppState  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    """Empty save directory for each test."""
    save_dir = tmp_path / "saves"
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir


def _make_state(ending_choice: str = "") -> AppState:
    state = AppState()
    state.ending_choice = ending_choice
    return state


# ---------------------------------------------------------------------------
# Round-trip: save → load → assert ending_choice matches
# ---------------------------------------------------------------------------


class TestEndingChoiceRoundTrip:
    """Save ending_choice, restore on a fresh AppState, assert equality."""

    def test_empty_ending_choice_round_trips(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        loaded = _make_state(ending_choice="NOT_PERSISTED")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == ""

    def test_ending_a_round_trips(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="A")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "A"

    def test_ending_b_round_trips(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="B")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "B"

    def test_ending_c_round_trips(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="C")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "C"


# ---------------------------------------------------------------------------
# Metadata shape: ending_choice is written to the metadata dict
# ---------------------------------------------------------------------------


class TestEndingChoiceMetadata:
    """The save's metadata dict must contain ``ending_choice``."""

    def test_metadata_contains_ending_choice(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="B")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        # The on-disk payload includes ending_choice.
        saved = sm.load(1)
        assert saved.metadata.get("ending_choice") == "B"

    def test_metadata_default_empty_string(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        saved = sm.load(1)
        assert saved.metadata.get("ending_choice") == ""


# ---------------------------------------------------------------------------
# Legacy save without ending_choice: defaults to empty string
# ---------------------------------------------------------------------------


class TestLegacySaveBackwardCompat:
    """Saves from before Phase 16 have no ``ending_choice`` key.

    Loading such a save must leave ``state.ending_choice`` at its
    default empty string (no exception).
    """

    def test_legacy_save_loads_without_error(self, save_dir: Path) -> None:
        """Loading a legacy save (no ``ending_choice`` key) must not crash.

        When the key is absent, ``state.ending_choice`` keeps whatever
        default the caller provided (typically the empty string for a
        fresh AppState). The crucial requirement is that the load
        succeeds without raising.
        """
        import json

        from wet_run.engine.save_manager import SaveManager

        # Hand-roll a legacy save file: no ``ending_choice`` metadata.
        legacy = {
            "version": "0.1.0",
            "saved_at": "2026-06-01T00:00:00Z",
            "elapsed_seconds": 0,
            "run_state": {
                "current_stage": "pending",
                "completed_stages": [],
                "pending_advance": False,
                "current_target_node": None,
                "last_visited_node": None,
                "mission_id": "first_jack",
                "started_at_ms": 0,
            },
            "mission": None,
            "app_state": {
                "inventory": {},
                "credits": 0,
                "current_node_id": None,
                "defeated_nodes": [],
                "extracted_nodes": [],
                "mission_progress": {},
                "in_server_browser": True,
                "selected_server_index": 0,
            },
            "metadata": {
                "player_grade": 3,
                "screen": "hub",
            },
        }
        (save_dir / "slot_1.json").write_text(json.dumps(legacy))

        sm = SaveManager(save_dir)
        loaded = _make_state(ending_choice="")  # default empty
        sm.restore_state(1, loaded)
        # The fresh AppState's default ``""`` is preserved — the
        # legacy save didn't have an ending_choice to restore.
        assert loaded.ending_choice == ""


# ---------------------------------------------------------------------------
# End-to-end: process_ending → save → load → assert preserved
# ---------------------------------------------------------------------------


class TestEndingChoiceEndToEnd:
    """Full flow: state.ending_choice set → save → load → verified."""

    def test_full_round_trip_with_process_ending(self, save_dir: Path) -> None:
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run
        from wet_run.story.endings import process_ending

        # 1. Process an ending (this is how state.ending_choice gets set
        #    in the real game).
        state = _make_state()
        state.run_state = start_run(mission_id="first_jack")
        result = process_ending("ending_case_redemption", state)
        assert result.achieved is True
        assert state.ending_choice == "ending_case_redemption"

        # 2. Save.
        sm = SaveManager(save_dir)
        sm.save(slot=1, state=state, elapsed_seconds=180)

        # 3. Simulate game restart: create a fresh state with a stale
        #    default ending_choice.
        fresh_state = _make_state(ending_choice="")
        fresh_state.run_state = start_run(mission_id="first_jack")
        sm.restore_state(1, fresh_state)

        # 4. The ending choice is preserved.
        assert fresh_state.ending_choice == "ending_case_redemption"


# ---------------------------------------------------------------------------
# Phase 20 edge cases: corrupted save, missing metadata, non-ASCII, concurrent
# ---------------------------------------------------------------------------


class TestEndingChoiceCorruptedSave:
    """Phase 20 edge case: a corrupted JSON save file fails gracefully."""

    def test_corrupted_save_raises_clean_error(self, save_dir: Path) -> None:
        """A JSON-corrupted save file must raise SaveCorruptedError, not crash."""
        from wet_run.engine.save_manager import (
            SaveCorruptedError,
            SaveManager,
        )

        (save_dir / "slot_1.json").write_text("{this is not valid json")
        sm = SaveManager(save_dir)
        loaded = _make_state(ending_choice="")
        with pytest.raises(SaveCorruptedError):
            sm.restore_state(1, loaded)

    def test_empty_save_file_raises_corrupted_error(self, save_dir: Path) -> None:
        """An empty save file produces a JSON decode error → SaveCorruptedError."""
        from wet_run.engine.save_manager import (
            SaveCorruptedError,
            SaveManager,
        )

        (save_dir / "slot_1.json").write_text("")
        sm = SaveManager(save_dir)
        loaded = _make_state(ending_choice="")
        with pytest.raises(SaveCorruptedError):
            sm.restore_state(1, loaded)


class TestEndingChoiceLegacyMetadata:
    """Phase 20 edge case: legacy saves missing arbitrary keys load with defaults."""

    def test_missing_player_grade_metadata(self, save_dir: Path) -> None:
        """Legacy save without player_grade metadata must still load."""
        import json

        from wet_run.engine.save_manager import SaveManager

        legacy = {
            "version": "0.1.0",
            "saved_at": "2026-06-01T00:00:00Z",
            "elapsed_seconds": 0,
            "run_state": {
                "current_stage": "pending",
                "completed_stages": [],
                "pending_advance": False,
                "current_target_node": None,
                "last_visited_node": None,
                "mission_id": "first_jack",
                "started_at_ms": 0,
            },
            "mission": None,
            "app_state": {
                "inventory": {},
                "credits": 0,
                "current_node_id": None,
                "defeated_nodes": [],
                "extracted_nodes": [],
                "mission_progress": {},
                "in_server_browser": True,
                "selected_server_index": 0,
            },
            "metadata": {
                "screen": "hub",
                "ending_choice": "A",
                # Intentionally no player_grade.
            },
        }
        (save_dir / "slot_1.json").write_text(json.dumps(legacy))
        sm = SaveManager(save_dir)
        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "A"


class TestEndingChoiceNonAsciiRoundTrip:
    """Phase 20 edge case: non-ASCII data in ending_choice survives round-trip."""

    def test_non_ascii_save_load_round_trip(self, save_dir: Path) -> None:
        """A save containing a non-ASCII ending string survives JSON round-trip."""
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        original = _make_state(ending_choice="ending_케이스")
        original.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=original, elapsed_seconds=42)

        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "ending_케이스"


class TestEndingChoiceConcurrentSaves:
    """Phase 20 edge case: rapid back-to-back saves don't corrupt state."""

    def test_consecutive_saves_overwrite_cleanly(self, save_dir: Path) -> None:
        """Two saves in quick succession: the second overwrites the first."""
        from wet_run.engine.save_manager import SaveManager
        from wet_run.run import start_run

        sm = SaveManager(save_dir)
        state_a = _make_state(ending_choice="A")
        state_a.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=state_a, elapsed_seconds=10)

        state_b = _make_state(ending_choice="B")
        state_b.run_state = start_run(mission_id="first_jack")
        sm.save(slot=1, state=state_b, elapsed_seconds=20)

        loaded = _make_state(ending_choice="")
        sm.restore_state(1, loaded)
        assert loaded.ending_choice == "B"


class TestEndingChoiceVersionMismatch:
    """Phase 20 edge case: future-version save files raise a version error."""

    def test_unknown_future_save_version_raises(self, save_dir: Path) -> None:
        """A save file with an unknown version string must raise VersionMismatchError."""
        import json

        from wet_run.engine.save_manager import (
            SaveManager,
            SaveVersionMismatchError,
        )

        future = {
            "version": "9.9.9-future",
            "saved_at": "2099-01-01T00:00:00Z",
            "elapsed_seconds": 0,
            "run_state": {
                "current_stage": "pending",
                "completed_stages": [],
                "pending_advance": False,
                "current_target_node": None,
                "last_visited_node": None,
                "mission_id": "first_jack",
                "started_at_ms": 0,
            },
            "mission": None,
            "app_state": {},
            "metadata": {"player_grade": 1, "screen": "hub", "ending_choice": "C"},
        }
        (save_dir / "slot_1.json").write_text(json.dumps(future))
        sm = SaveManager(save_dir)
        loaded = _make_state(ending_choice="")
        with pytest.raises(SaveVersionMismatchError):
            sm.restore_state(1, loaded)

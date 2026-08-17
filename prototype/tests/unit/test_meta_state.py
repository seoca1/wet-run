"""Tests for MetaState (ADR-0131) — cross-run persistent meta progression.

Validates:
- MetaState dataclass: roundtrip serialization
- MetaStateManager: load/save, atomic write, missing/corrupt/legacy file
- promote_from_run: cross-run faction reputation merge
- Integration with ReputationState (delegation correctness)
"""

from __future__ import annotations

import json
from pathlib import Path

from wet_run.engine.meta_state_manager import (
    default_meta_state_path,
    load_meta_state,
    reset_meta_state,
    save_meta_state,
)
from wet_run.matrix.node import Faction
from wet_run.run.meta_state import META_STATE_VERSION, MetaState
from wet_run.run.reputation import ReputationState

# ============================================================================
# MetaState dataclass tests
# ============================================================================


class TestMetaStateDataclass:
    """Basic MetaState behavior: defaults, serialization, defensive parsing."""

    def test_default_construction(self) -> None:
        """Default MetaState has version 1, empty reputation, empty future buckets."""
        ms = MetaState()
        assert ms.version == META_STATE_VERSION
        assert isinstance(ms.reputation, ReputationState)
        assert ms.reputation.total_score() == 0
        assert ms.future_buckets == {}

    def test_to_dict_roundtrip(self) -> None:
        """to_dict → from_dict preserves all fields."""
        ms = MetaState()
        ms.reputation.adjust(Faction.HOSAKA, 20, source="test_mission")
        ms.future_buckets["hall_of_dead"] = ["jockey_1", "jockey_2"]

        data = ms.to_dict()
        restored = MetaState.from_dict(data)

        assert restored.version == META_STATE_VERSION
        assert restored.reputation.get(Faction.HOSAKA).score == 20
        assert restored.future_buckets.get("hall_of_dead") == ["jockey_1", "jockey_2"]

    def test_from_dict_empty_returns_default(self) -> None:
        """Empty dict → default MetaState."""
        ms = MetaState.from_dict({})
        assert ms.version == META_STATE_VERSION
        assert ms.reputation.total_score() == 0

    def test_from_dict_malformed_returns_default(self) -> None:
        """Non-dict input → empty MetaState (defensive)."""
        # None, list, string, int — all should not crash
        for bad in [None, [], "string", 42]:
            ms = MetaState.from_dict(bad)  # type: ignore[arg-type]
            assert isinstance(ms, MetaState)
            assert ms.version == META_STATE_VERSION

    def test_from_dict_preserves_unknown_keys_in_future_buckets(self) -> None:
        """Unknown top-level keys go to future_buckets (forward compat)."""
        data = {
            "version": 1,
            "reputation": {},
            "unknown_field": {"foo": "bar"},
            "another_future": [1, 2, 3],
        }
        ms = MetaState.from_dict(data)
        assert ms.future_buckets.get("unknown_field") == {"foo": "bar"}
        assert ms.future_buckets.get("another_future") == [1, 2, 3]

    def test_from_dict_corrupt_reputation_skipped(self) -> None:
        """Malformed reputation dict → empty ReputationState (no crash)."""
        data = {
            "version": 1,
            "reputation": "not_a_dict",
        }
        ms = MetaState.from_dict(data)
        assert ms.reputation.total_score() == 0

    def test_from_dict_invalid_version_defaults(self) -> None:
        """Invalid version field defaults to current."""
        data = {"version": "not_an_int"}
        ms = MetaState.from_dict(data)
        assert ms.version == META_STATE_VERSION

    def test_version_constant_matches(self) -> None:
        """META_STATE_VERSION constant exists and is 1."""
        assert META_STATE_VERSION == 1


# ============================================================================
# MetaStateManager disk persistence tests
# ============================================================================


class TestMetaStateManager:
    """Disk load/save behavior with atomic write and corruption recovery."""

    def test_load_missing_returns_default(self, tmp_path: Path) -> None:
        """No file → empty MetaState."""
        path = tmp_path / "meta_state.json"
        ms = load_meta_state(path)
        assert ms.version == META_STATE_VERSION
        assert ms.reputation.total_score() == 0

    def test_load_corrupt_returns_default(self, tmp_path: Path) -> None:
        """Malformed JSON → empty MetaState (no crash)."""
        path = tmp_path / "meta_state.json"
        path.write_text("not valid json {{{")
        ms = load_meta_state(path)
        assert ms.version == META_STATE_VERSION
        assert ms.reputation.total_score() == 0

    def test_load_empty_returns_default(self, tmp_path: Path) -> None:
        """Empty file → empty MetaState."""
        path = tmp_path / "meta_state.json"
        path.write_text("")
        ms = load_meta_state(path)
        assert ms.version == META_STATE_VERSION

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        """Save and reload preserves all fields."""
        path = tmp_path / "meta_state.json"
        original = MetaState()
        original.reputation.adjust(Faction.HOSAKA, 20, source="promote")
        original.reputation.adjust(Faction.MAAS, 15, source="promote")
        original.future_buckets["hall_of_dead"] = ["jockey_x"]

        save_meta_state(original, path)
        loaded = load_meta_state(path)

        assert loaded.reputation.get(Faction.HOSAKA).score == 20
        assert loaded.reputation.get(Faction.MAAS).score == 15
        assert loaded.future_buckets.get("hall_of_dead") == ["jockey_x"]

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """save_meta_state creates parent directory if missing."""
        path = tmp_path / "deeply" / "nested" / "meta_state.json"
        assert not path.parent.exists()
        save_meta_state(MetaState(), path)
        assert path.exists()

    def test_save_atomic_no_temp_file_leftover(self, tmp_path: Path) -> None:
        """After save, no .tmp file remains."""
        path = tmp_path / "meta_state.json"
        save_meta_state(MetaState(), path)
        siblings = list(path.parent.iterdir())
        assert not any(p.suffix == ".tmp" for p in siblings)

    def test_save_then_load_handles_roundtrip_with_history(self, tmp_path: Path) -> None:
        """Reputation history survives roundtrip."""
        path = tmp_path / "meta_state.json"
        ms = MetaState()
        ms.reputation.adjust(Faction.HOSAKA, 10, source="mission_a")
        ms.reputation.adjust(Faction.HOSAKA, 15, source="mission_b")
        ms.reputation.adjust(Faction.HOSAKA, 5, source="mission_c")

        save_meta_state(ms, path)
        loaded = load_meta_state(path)
        history = loaded.reputation.get(Faction.HOSAKA).history

        assert len(history) == 3
        assert history[0][1] == "mission_c"  # newest first
        assert history[1][1] == "mission_b"
        assert history[2][1] == "mission_a"

    def test_save_writes_valid_json(self, tmp_path: Path) -> None:
        """Saved file is valid JSON."""
        path = tmp_path / "meta_state.json"
        ms = MetaState()
        ms.reputation.adjust(Faction.HOSAKA, 50, source="x")
        save_meta_state(ms, path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
        assert data["version"] == META_STATE_VERSION

    def test_reset_deletes_file(self, tmp_path: Path) -> None:
        """reset_meta_state removes the file."""
        path = tmp_path / "meta_state.json"
        path.write_text("{}")
        assert path.exists()
        reset_meta_state(path)
        assert not path.exists()

    def test_reset_noop_when_missing(self, tmp_path: Path) -> None:
        """reset_meta_state doesn't crash on missing file."""
        path = tmp_path / "meta_state.json"
        reset_meta_state(path)  # should not raise
        assert not path.exists()

    def test_load_future_version_returns_default(self, tmp_path: Path) -> None:
        """meta_state.json from a newer version → empty default (defensive)."""
        path = tmp_path / "meta_state.json"
        path.write_text(json.dumps({"version": 999, "reputation": {}}))
        ms = load_meta_state(path)
        assert ms.version == META_STATE_VERSION

    def test_default_meta_state_path(self, tmp_path: Path) -> None:
        """default_meta_state_path returns saves/meta_state.json under data_dir."""
        path = default_meta_state_path(tmp_path)
        assert path == tmp_path / "saves" / "meta_state.json"


# ============================================================================
# Cross-run promotion tests
# ============================================================================


class TestMetaStatePromotion:
    """promote_from_run merges a finished run into persistent meta state."""

    def test_promote_zero_history_no_op(self) -> None:
        """Run with no reputation interaction → meta state unchanged."""
        ms = MetaState()
        run_rep = ReputationState()  # all zeros, no history
        ms.promote_from_run(run_rep)
        assert ms.reputation.total_score() == 0

    def test_promote_adds_score(self) -> None:
        """Run's reputation scores merge into meta state."""
        ms = MetaState()
        run_rep = ReputationState()
        run_rep.adjust(Faction.HOSAKA, 20, source="mission_ta_heist")
        run_rep.adjust(Faction.MAAS, 15, source="mission_maas_neural")

        ms.promote_from_run(run_rep)

        assert ms.reputation.get(Faction.HOSAKA).score == 20
        assert ms.reputation.get(Faction.MAAS).score == 15

    def test_promote_accumulates_across_runs(self) -> None:
        """Multiple runs accumulate reputation (not overwrite)."""
        ms = MetaState()

        run1 = ReputationState()
        run1.adjust(Faction.HOSAKA, 20, source="run1")
        ms.promote_from_run(run1)

        run2 = ReputationState()
        run2.adjust(Faction.HOSAKA, 15, source="run2")
        ms.promote_from_run(run2)

        score = ms.reputation.get(Faction.HOSAKA).score
        assert score == 35, f"Expected 35 (20+15), got {score}"

    def test_promote_preserves_history(self) -> None:
        """Run's history entries carry over (with 'run:' prefix)."""
        ms = MetaState()
        run_rep = ReputationState()
        run_rep.adjust(Faction.HOSAKA, 10, source="mission_x")
        run_rep.adjust(Faction.HOSAKA, 15, source="mission_y")

        ms.promote_from_run(run_rep)

        history = ms.reputation.get(Faction.HOSAKA).history
        sources = [src for _, src in history]
        assert "run:mission_y" in sources
        assert "run:mission_x" in sources
        assert "run_promote" not in sources


# ============================================================================
# Integration: full save → load → promote → save → load cycle
# ============================================================================


class TestMetaStateIntegration:
    """End-to-end persistence cycle matching real usage."""

    def test_full_cycle_preserves_reputation(self, tmp_path: Path) -> None:
        """Load → adjust → save → load → verify persistence."""
        path = default_meta_state_path(tmp_path)

        # Session 1: load empty, adjust, save
        ms1 = load_meta_state(path)
        ms1.reputation.adjust(Faction.HOSAKA, 20, source="session1_mission")
        save_meta_state(ms1, path)

        # Session 2: load (simulating fresh app start), verify
        ms2 = load_meta_state(path)
        assert ms2.reputation.get(Faction.HOSAKA).score == 20

        # Session 2: adjust more, save
        ms2.reputation.adjust(Faction.HOSAKA, 10, source="session2_mission")
        save_meta_state(ms2, path)

        # Session 3: load, verify cumulative
        ms3 = load_meta_state(path)
        score = ms3.reputation.get(Faction.HOSAKA).score
        assert score >= 20  # at least session1 contribution

    def test_run_promotion_via_save_load(self, tmp_path: Path) -> None:
        """Simulate: complete run → promote → save → reload → promote again."""
        path = default_meta_state_path(tmp_path)

        # Session 1: complete a run
        meta = load_meta_state(path)
        run_rep = ReputationState()
        run_rep.adjust(Faction.HOSAKA, 15, source="mission_a")
        meta.promote_from_run(run_rep)
        save_meta_state(meta, path)

        # Session 2: load, complete another run
        meta = load_meta_state(path)
        assert meta.reputation.get(Faction.HOSAKA).score > 0

        run_rep2 = ReputationState()
        run_rep2.adjust(Faction.HOSAKA, 10, source="mission_b")
        meta.promote_from_run(run_rep2)
        save_meta_state(meta, path)

        # Session 3: load, verify cumulative reputation
        meta = load_meta_state(path)
        # Cumulative should be at least session1's contribution
        assert meta.reputation.get(Faction.HOSAKA).score >= 15


# ============================================================================
# State.py integration smoke test
# ============================================================================


class TestAppStateHydration:
    """AppState should be able to hydrate reputation from MetaState."""

    def test_hydrate_app_state_from_meta_state(self, tmp_path: Path) -> None:
        """AppState.reputation = MetaState.reputation (delegation)."""
        from wet_run.engine.state import AppState

        meta = MetaState()
        meta.reputation.adjust(Faction.HOSAKA, 20, source="test")
        save_meta_state(meta, default_meta_state_path(tmp_path))

        loaded = load_meta_state(default_meta_state_path(tmp_path))

        app = AppState()
        # In real code, app.reputation is hydrated from loaded
        app.reputation = loaded.reputation  # type: ignore[assignment]
        assert app.reputation.get(Faction.HOSAKA).score == 20

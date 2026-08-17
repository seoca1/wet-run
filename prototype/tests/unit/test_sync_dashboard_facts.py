"""Unit tests for ``scripts/sync_dashboard_facts.py``.

These tests focus on the diff/check logic.  We don't exercise the
real data sources (we patch the collectors) so the tests run
without touching missions.json or the source tree.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# Load the script as a module (it lives under scripts/, not in a
# package).  We do this once and cache the module.
SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "sync_dashboard_facts.py"
_spec = importlib.util.spec_from_file_location("sync_dashboard_facts", SCRIPT_PATH)
sync_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_mod)


# ---------------------------------------------------------------------------
# Diff logic
# ---------------------------------------------------------------------------


class TestDiffFacts:
    def test_no_old_returns_create_message(self) -> None:
        diffs = sync_mod._diff_facts(None, {"a": 1})
        assert diffs == ["facts.json did not exist — would be created"]

    def test_equal_returns_empty(self) -> None:
        diffs = sync_mod._diff_facts({"a": 1}, {"a": 1})
        assert diffs == []

    def test_value_change_is_listed(self) -> None:
        diffs = sync_mod._diff_facts({"a": 1}, {"a": 2})
        # The diff line should mention the key and both old/new values.
        joined = "\n".join(diffs)
        assert "a:" in joined
        assert "1" in joined
        assert "2" in joined

    def test_key_added_is_listed(self) -> None:
        diffs = sync_mod._diff_facts({}, {"a": 1})
        assert len(diffs) == 1
        joined = "\n".join(diffs)
        assert "a:" in joined
        assert "1" in joined

    def test_key_removed_is_listed(self) -> None:
        diffs = sync_mod._diff_facts({"a": 1}, {})
        assert len(diffs) == 1
        joined = "\n".join(diffs)
        assert "a:" in joined


# ---------------------------------------------------------------------------
# Individual fact collectors — verify they don't crash on edge cases
# ---------------------------------------------------------------------------


class TestCountIce:
    def test_count_ice_returns_positive(self, tmp_path: Path, monkeypatch) -> None:
        fake = tmp_path / "ice.json"
        fake.write_text(json.dumps({"a": {}, "b": {}, "c": {}}))
        # Patch the path the collector uses.
        monkeypatch.setattr(sync_mod, "PROTOTYPE", tmp_path)
        # The collector references PROTOTYPE / "data" / "combat" /
        # "ice_types.json" — build that tree.
        (tmp_path / "data" / "combat").mkdir(parents=True)
        import shutil

        shutil.copy(fake, tmp_path / "data" / "combat" / "ice_types.json")
        # Reimport so the module picks up the new PROTOTYPE.
        # (Simpler: just call the helper directly with the file
        # explicitly.)
        assert sync_mod._count_ice() == 3


class TestCountSounds:
    def test_returns_zero_when_sounds_dir_empty(self, tmp_path, monkeypatch) -> None:
        # The collector reads from ``SOUNDS_DIR`` (a module-level
        # constant), not from PROTOTYPE at call time.  Point it at an
        # empty directory to verify the zero-count branch.
        empty = tmp_path / "empty_sounds"
        empty.mkdir()
        monkeypatch.setattr(sync_mod, "SOUNDS_DIR", empty)
        assert sync_mod._count_sounds() == 0


class TestCountPrograms:
    def test_returns_count_of_programs(self, tmp_path, monkeypatch) -> None:
        # Patch PROGRAMS_JSON to a fake file in tmp_path.
        fake = tmp_path / "programs.json"
        fake.write_text(json.dumps({"a": 1, "b": 2, "c": 3, "d": 4}))
        monkeypatch.setattr(sync_mod, "PROGRAMS_JSON", fake)
        assert sync_mod._count_programs() == 4


# ---------------------------------------------------------------------------
# _collect_facts integration: end-to-end without touching real data
# ---------------------------------------------------------------------------


class TestCollectFactsShape:
    def test_keys_match_expected(self, monkeypatch) -> None:
        """All expected keys are present in the collected facts dict."""
        # Patch every collector to return a sentinel value.
        monkeypatch.setattr(sync_mod, "_count_missions", lambda: 38)
        monkeypatch.setattr(sync_mod, "_character_stats", lambda: (4, ["x"]))
        monkeypatch.setattr(sync_mod, "_arc_stats", lambda: ([1, 2], {"1": 1}))
        monkeypatch.setattr(sync_mod, "_count_stages", lambda: 13)
        monkeypatch.setattr(sync_mod, "_count_ice", lambda: 5)
        monkeypatch.setattr(sync_mod, "_count_sounds", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_gn_scenes", lambda: ({"case": 1}, 1))
        monkeypatch.setattr(sync_mod, "_count_programs", lambda: 0)
        monkeypatch.setattr(sync_mod, "_cyberspace_stats", lambda: (2, 4, 8))
        monkeypatch.setattr(sync_mod, "_count_skill_effects", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_tests", lambda: 0)
        facts = sync_mod._collect_facts()
        expected_keys = {
            "mission_count",
            "character_count",
            "character_ids",
            "arcs",
            "arc_distribution",
            "ice_unique_count",
            "stage_count",
            "sound_wav_count",
            "gn_scenes_by_char",
            "gn_scenes_total",
            "program_count",
            "ending_combinations",
            "cyberspace_worlds",
            "cyberspace_sectors_per_world",
            "cyberspace_sectors_total",
            "cyberspace_servers_total",
            "skill_effect_count",
            "test_count_collected",
            "_generated_at",
        }
        assert expected_keys.issubset(facts.keys())

    def test_sectors_per_world_divisor_safe(self, monkeypatch) -> None:
        """Zero worlds should not crash the divisor in
        ``cyberspace_sectors_per_world``."""
        monkeypatch.setattr(sync_mod, "_count_missions", lambda: 0)
        monkeypatch.setattr(sync_mod, "_character_stats", lambda: (0, []))
        monkeypatch.setattr(sync_mod, "_arc_stats", lambda: ([], {}))
        monkeypatch.setattr(sync_mod, "_count_stages", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_ice", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_sounds", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_gn_scenes", lambda: ({}, 0))
        monkeypatch.setattr(sync_mod, "_count_programs", lambda: 0)
        monkeypatch.setattr(sync_mod, "_cyberspace_stats", lambda: (0, 0, 0))
        monkeypatch.setattr(sync_mod, "_count_skill_effects", lambda: 0)
        monkeypatch.setattr(sync_mod, "_count_tests", lambda: 0)
        facts = sync_mod._collect_facts()
        # No ZeroDivisionError; default is 0.
        assert facts["cyberspace_sectors_per_world"] == 0


# ---------------------------------------------------------------------------
# Regression: skill_effect_count must scan state_models.py (ADR-0141 Phase 4)
# ---------------------------------------------------------------------------


class TestSkillEffectRegression:
    """Lock the scan target after the Phase 4 combat/state.py split.

    Background: prior to v1.1.0a1, ``SkillEffect`` lived in ``combat/state.py``.
    The Phase 4 split moved it to ``combat/state_models.py``. The sync script
    was originally hard-coded to scan ``state.py``, returning ``0`` — a silent
    regression in the dashboard's ``skill_effect_count``. This regression
    block exercises ``_count_skill_effects`` against the real source so a
    similar future move would be caught immediately.
    """

    def test_returns_positive_from_real_source(self) -> None:
        """``_count_skill_effects`` must read the source containing SkillEffect."""
        count: int = sync_mod._count_skill_effects()
        assert count > 0, (
            "skill_effect_count regressed to 0 — _count_skill_effects is "
            "scanning the wrong file (state.py vs state_models.py)."
        )

    def test_matches_actual_skill_effect_enum(self) -> None:
        """Reported count must equal the SkillEffect enum size."""
        from wet_run.combat.state_models import SkillEffect  # type: ignore[import-untyped]

        count: int = sync_mod._count_skill_effects()
        assert count == len(list(SkillEffect))

    def test_scan_target_points_to_state_models(self) -> None:
        """The configured scan path must reference state_models.py."""
        configured: str = str(sync_mod.COMBAT_STATE_MODELS_PY)
        assert configured.endswith("state_models.py"), (
            f"COMBAT_STATE_MODELS_PY = {configured!r} — expected to point at combat/state_models.py"
        )

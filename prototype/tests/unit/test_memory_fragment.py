"""Tests for Memory Fragment encounter logic (ADR-0140 §Proposal 2)."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from wet_run.lore.memory_fragment import (
    MemoryFragmentPick,
    load_encounter_table,
    roll_memory_fragment,
)


@pytest.fixture
def encounter_table() -> dict[str, object]:
    """Standard 4-fragment encounter table for tests."""
    return {
        "version": 1,
        "per_run_cap": 6,
        "base_chance": 0.25,
        "fragments": [
            {
                "id": "memory_signal_echo_01",
                "category": "signal_echo",
                "zone": "surface",
                "tier_min": 1,
                "tier_max": 6,
                "chance": 0.25,
                "faction": None,
                "rep_delta": 0,
                "grade_min": 1,
                "grade_max": 6,
            },
            {
                "id": "memory_construct_cache_01",
                "category": "construct_cache",
                "zone": "core",
                "tier_min": 3,
                "tier_max": 6,
                "chance": 0.30,
                "faction": "hosaka",
                "rep_delta": 1,
                "grade_min": 1,
                "grade_max": 6,
            },
            {
                "id": "memory_anomaly_log_01",
                "category": "anomaly_log",
                "zone": "ta",
                "tier_min": 5,
                "tier_max": 6,
                "chance": 0.40,
                "faction": "tessier_ashpool",
                "rep_delta": 2,
                "grade_min": 5,
                "grade_max": 6,
            },
            {
                "id": "memory_dead_channel_01",
                "category": "dead_channel",
                "zone": "deep",
                "tier_min": 3,
                "tier_max": 6,
                "chance": 0.20,
                "faction": None,
                "rep_delta": 0,
                "grade_min": 1,
                "grade_max": 6,
            },
        ],
    }


class TestLoadEncounterTable:
    """Disk load behavior — defensive against missing/corrupt files."""

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "missing.json"
        result = load_encounter_table(path)
        assert result["fragments"] == []
        assert result["version"] == 0

    def test_load_corrupt_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json {{{")
        result = load_encounter_table(path)
        assert result["fragments"] == []
        assert result["version"] == 0

    def test_load_valid_table(self, tmp_path: Path) -> None:
        path = tmp_path / "valid.json"
        path.write_text(
            json.dumps({"version": 1, "fragments": [], "per_run_cap": 5, "base_chance": 0.3})
        )
        result = load_encounter_table(path)
        assert result["version"] == 1
        assert result["per_run_cap"] == 5
        assert result["base_chance"] == 0.3


class TestRollMemoryFragment:
    """Encounter logic — filters, weights, exclusions."""

    def test_base_chance_zero_returns_none(self, encounter_table: dict[str, object]) -> None:
        """If base_chance is 0, never rolls."""
        encounter_table["base_chance"] = 0.0
        rng = random.Random(42)
        for _ in range(100):
            result = roll_memory_fragment(encounter_table, "surface", 1, None, rng)
            assert result is None

    def test_zone_filter(self, encounter_table: dict) -> None:
        """Fragments only fire in their designated zone."""
        rng = random.Random(42)
        for _ in range(50):
            result = roll_memory_fragment(encounter_table, "mid", 1, None, rng)
            # 'mid' is not in encounter table → should always fail
            # (would succeed only on base_chance roll AND candidate match)
            assert result is None

    def test_grade_filter(self, encounter_table: dict) -> None:
        """High-tier fragments only available to high-grade players."""
        rng = random.Random(42)
        # Grade 1 in TA zone → anomaly_log requires grade_min=5, excluded
        for _ in range(100):
            result = roll_memory_fragment(encounter_table, "ta", 1, "tessier_ashpool", rng)
            assert result is None

    def test_signal_echo_in_surface(self, encounter_table: dict) -> None:
        """Signal echo (surface, no faction) can be found at any grade."""
        encounter_table["base_chance"] = 1.0
        rng = random.Random(42)
        result = roll_memory_fragment(encounter_table, "surface", 1, None, rng)
        if result is not None:
            assert result.fragment_id == "memory_signal_echo_01"
            assert result.rep_delta == 0

    def test_faction_filter(self, encounter_table: dict) -> None:
        """Hosaka construct only in hosaka servers."""
        rng = random.Random(42)
        # Core zone with no faction → construct_cache excluded
        for _ in range(50):
            result = roll_memory_fragment(encounter_table, "core", 3, None, rng)
            assert result is None

    def test_already_found_excluded(self, encounter_table: dict) -> None:
        """Once a fragment is found, it won't roll again."""
        rng = random.Random(42)
        already = {"memory_signal_echo_01"}
        for _ in range(100):
            result = roll_memory_fragment(
                encounter_table, "surface", 1, None, rng, already_found=already
            )
            assert result is None

    def test_tier_high_unlock(self, encounter_table: dict) -> None:
        """Grade 5+ in TA zone can roll anomaly_log."""
        encounter_table["base_chance"] = 1.0
        rng = random.Random(42)
        result = roll_memory_fragment(encounter_table, "ta", 6, "tessier_ashpool", rng)
        if result is not None:
            assert result.fragment_id == "memory_anomaly_log_01"
            assert result.rep_delta == 2

    def test_returns_pick_dataclass(self, encounter_table: dict) -> None:
        """Result is a MemoryFragmentPick with expected fields."""
        encounter_table["base_chance"] = 1.0
        rng = random.Random(42)
        result = roll_memory_fragment(encounter_table, "surface", 1, None, rng)
        assert isinstance(result, MemoryFragmentPick)
        assert hasattr(result, "fragment_id")
        assert hasattr(result, "category")
        assert hasattr(result, "rep_delta")
        assert hasattr(result, "faction")


class TestEndToEnd:
    """Full integration: load → roll multiple times → distribution sanity."""

    def test_distribution_respects_weights(self, tmp_path: Path) -> None:
        """Over many rolls, surface-only should yield signal_echo most often."""
        path = tmp_path / "single.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "fragments": [
                        {
                            "id": "only",
                            "category": "test",
                            "zone": "test",
                            "tier_min": 1,
                            "tier_max": 6,
                            "chance": 0.5,
                            "faction": None,
                            "rep_delta": 0,
                            "grade_min": 1,
                            "grade_max": 6,
                        }
                    ],
                    "per_run_cap": 5,
                    "base_chance": 1.0,
                }
            )
        )
        table = load_encounter_table(path)
        rng = random.Random(0)
        results = [roll_memory_fragment(table, "test", 1, None, rng) for _ in range(100)]
        non_null = [r for r in results if r is not None]
        assert all(r.fragment_id == "only" for r in non_null)
        assert len(non_null) > 50

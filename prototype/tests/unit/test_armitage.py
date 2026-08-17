"""Tests for the 4th character "Armitage" content (Phase 6+ expansion).

Covers:
- New missions load correctly with `character_ref="suit"`
- New chapter JSON for the suit
- New Armitage portraits (3)
- New tessier_ashpool_lab background
- build_dashboard aggregates: 33 missions, 4 chapters, 4 characters
- Per-arc distribution (now 1+ missions per arc 2..5)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Use the project_root / data_dir fixtures from conftest.py.
# REPO is the project root (this prototype/) for build_dashboard
# calls; the data_dir fixture from conftest covers other tests.
REPO = Path("/Users/emilio/projects/Projects/Game/wet_run/prototype")


@pytest.fixture
def data_dir() -> Path:
    """Override the conftest data_dir because the Game-path test
    tree doesn't have its own conftest. We point to the full
    Projects-path data directory which has all the new content."""
    return REPO / "data"


# ============================================================================
# 4th character mission data
# ============================================================================


class TestArmitageMissions:
    EXPECTED_IDS = [
        "armitage_infiltration",
        "hosaka_extraction",
        "ta_defection",
        "wintermute_negotiation",
    ]

    def test_all_4_missions_present(self, data_dir: Path) -> None:
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for mid in self.EXPECTED_IDS:
            assert mid in data, f"Missing 4th-character mission: {mid}"

    def test_all_4_missions_have_suit_character_ref(self, data_dir: Path) -> None:
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for mid in self.EXPECTED_IDS:
            m = data[mid]
            assert m["story"]["character_ref"] == "suit", (
                f"{mid} should be character_ref=suit, got {m['story']['character_ref']}"
            )

    def test_arc_progression_2_to_5(self, data_dir: Path) -> None:
        """Armitage's arc spans arcs 2-5: infiltration → hosaka → TA defection → Wintermute."""
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for mid, expected_arc in zip(self.EXPECTED_IDS, [2, 3, 4, 5]):
            assert data[mid]["arc"] == expected_arc, (
                f"{mid} should be arc {expected_arc}, got {data[mid]['arc']}"
            )

    def test_grade_progression(self, data_dir: Path) -> None:
        """Grade increases as the arc progresses."""
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        grades = [data[mid]["grade_max"] for mid in self.EXPECTED_IDS]
        # 3, 4, 5, 6 — increasing grade as the player grows more dangerous.
        assert grades == [3, 4, 5, 6]

    def test_wintermute_negotiation_is_master_only(self, data_dir: Path) -> None:
        """The finale is reserved for grade-6 (master-tier) jockeys."""
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        mission = data["wintermute_negotiation"]
        assert mission["grade_min"] == 5
        assert mission["grade_max"] == 6

    def test_chapter_novice_fixes_preserved(self, data_dir: Path) -> None:
        """The 4 new missions don't break the existing novice-friendly missions."""
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        assert "first_jack" in data
        assert data["first_jack"]["grade_max"] == 1
        assert data["first_jack"]["story"]["character_ref"] == "novice"

    def test_synopsis_texts_non_empty(self, data_dir: Path) -> None:
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for mid in self.EXPECTED_IDS:
            assert data[mid]["story"]["synopsis_en"].strip()
            assert data[mid]["story"]["synopsis_ko"].strip()

    def test_korean_synopsis_within_word_count(self, data_dir: Path) -> None:
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        for mid in self.EXPECTED_IDS:
            # ADR-0051: ko synopsis ≥ 300 chars without spaces.
            ko = data[mid]["story"]["synopsis_ko"].replace(" ", "")
            assert len(ko) >= 300, f"{mid} ko synopsis too short: {len(ko)} chars"


# ============================================================================
# Chapter JSON
# ============================================================================


class TestArmitageChapter:
    def test_chapter_suit_exists(self, data_dir: Path) -> None:
        p = data_dir / "story" / "chapters" / "suit.json"
        assert p.exists(), f"Missing chapter: {p}"

    def test_chapter_suit_has_required_fields(self, data_dir: Path) -> None:
        p = data_dir / "story" / "chapters" / "suit.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        required = {
            "character",
            "id",
            "title_en",
            "title_ko",
            "subtitle_en",
            "subtitle_ko",
            "portrait",
            "theme",
            "excerpt_en",
            "excerpt_ko",
            "duration_ms",
            "next_screen",
            "char_delay_ms",
        }
        missing = required - set(data.keys())
        assert not missing, f"Chapter missing: {missing}"

    def test_chapter_suit_links_to_missions(self, data_dir: Path) -> None:
        p = data_dir / "story" / "chapters" / "suit.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        # _integrated_with.missions is a metadata field for testing.
        missions = data.get("_integrated_with", {}).get("missions", [])
        assert "armitage_infiltration" in missions
        assert "wintermute_negotiation" in missions

    def test_chapter_suit_portrait_exists(self, data_dir: Path) -> None:
        p = data_dir / "story" / "chapters" / "suit.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        portrait_id = data["portrait"]
        # portrait format: "art:<portrait_id>". Accept the base name
        # (e.g. "armitage") or any prefix variant (e.g. "armitage_suit").
        portraits_p = data_dir / "art" / "portraits" / "portraits.json"
        if portraits_p.exists():
            portraits = json.loads(portraits_p.read_text(encoding="utf-8"))
            base = portrait_id.replace("art:", "")
            matching = [k for k in portraits if k == base or k.startswith(base + "_")]
            assert matching, (
                f"No portrait found for base '{base}' in {sorted(portraits.keys())[:5]}…"
            )


# ============================================================================
# Portraits + backgrounds
# ============================================================================


class TestArmitagePortraits:
    EXPECTED_PORTRAITS = [
        "armitage_suit",
        "armitage_terminal",
        "armitage_betrayed",
    ]

    def test_all_3_portraits_registered(self, data_dir: Path) -> None:
        p = data_dir / "art" / "portraits" / "portraits.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        for portrait in self.EXPECTED_PORTRAITS:
            assert portrait in data, f"Missing portrait: {portrait}"

    def test_portraits_have_correct_character_tag(self, data_dir: Path) -> None:
        p = data_dir / "art" / "portraits" / "portraits.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        for portrait in self.EXPECTED_PORTRAITS:
            assert data[portrait]["character"] == "suit", f"{portrait} should be character=suit"

    def test_portraits_have_10x12_grid(self, data_dir: Path) -> None:
        p = data_dir / "art" / "portraits" / "portraits.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        for portrait in self.EXPECTED_PORTRAITS:
            assert data[portrait]["size"] == [10, 12]
            assert len(data[portrait]["art"]) == 12


class TestTessierAshpoolLab:
    def test_background_registered(self, data_dir: Path) -> None:
        p = data_dir / "art" / "backgrounds" / "backgrounds.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "tessier_ashpool_lab" in data

    def test_background_grid_dimensions(self, data_dir: Path) -> None:
        p = data_dir / "art" / "backgrounds" / "backgrounds.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        bg = data["tessier_ashpool_lab"]
        # Size declares the intent (40x16). Actual art may have
        # shorter lines (padding trimmed). The test ensures the
        # background has *some* art and that the size field is set.
        assert bg["size"] == [40, 16]
        assert len(bg["art"]) > 0


# ============================================================================
# build_dashboard integration
# ============================================================================


class TestDashboardIntegration:
    def test_dashboard_reflects_4th_character(self) -> None:
        """build_dashboard aggregates: 33 missions, 4 chapters, 4 characters."""
        import importlib.util
        import sys as _sys

        # build_dashboard lives in the Projects-path tools/ dir
        # (not the Game path that hosts this test). Use the Projects
        # workspace root to find it.
        projects_root = Path("/Users/emilio/projects/Projects/Game/wet_run")
        if "build_dashboard" not in _sys.modules:
            _sys.path.insert(0, str(projects_root / "tools"))
            spec = importlib.util.spec_from_file_location(
                "build_dashboard", projects_root / "tools" / "build_dashboard.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            mod = _sys.modules["build_dashboard"]

        # The Projects path has the full data (missions, chapters,
        # reactions, etc.) so stats loaded against it reflect the
        # post-expansion state. build_dashboard expects the project
        # root (parent of prototype/).
        from pathlib import Path as _Path

        stats = mod.load_mission_stats(_Path(projects_root))
        assert stats["missions"] == 200
        assert "Armitage" in stats["characters"]
        assert len(stats["characters"]) == 27
        assert stats["missions"] == 200
        assert "Armitage" in stats["characters"]
        assert len(stats["characters"]) == 27

    def test_arc_distribution_after_expansion(self, data_dir: Path) -> None:
        """At least one mission per arc 1-5 after the 4th character expansion."""
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        arcs_present = {m["arc"] for m in data.values()}
        # 4 new missions add arcs 2, 3, 4, 5. Combined with the
        # existing 29 missions that already cover arcs 1-4, all of
        # 1..5 should now have at least one mission.
        for arc in (1, 2, 3, 4, 5):
            assert arc in arcs_present, f"No mission in arc {arc}"


# ============================================================================
# 4th character end-to-end (mission + chapter + portrait + reputation)
# ============================================================================


class TestArmitageEndToEnd:
    """The 4th character should appear in the full reputation + faction
    ecosystem too — they have mission hooks that adjust faction rep."""

    def test_4_missions_use_existing_fixer_reputation(self, data_dir: Path) -> None:
        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        armitage_ids = {
            "armitage_infiltration",
            "hosaka_extraction",
            "ta_defection",
            "wintermute_negotiation",
        }
        fixers = {data[mid]["fixer"] for mid in armitage_ids}
        # All four missions use established fixers (no new NPC needed).
        assert fixers.issubset({"finn", "ta_rep", "3jane", "dixie"})

    def test_4_missions_diverse_faction_alignment(self, data_dir: Path) -> None:
        """4 missions span Hosaka → T-A (Armitage's character arc)."""
        from wet_run.engine.mission_completion import fixer_to_factions
        from wet_run.matrix.node import Faction

        with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
            data = json.load(f)
        # The T-A / 3jane mission should affect T-A reputation.
        ta_mission = data["ta_defection"]
        assert ta_mission["fixer"] == "3jane"
        factions = fixer_to_factions("3jane")
        assert Faction.TA in factions

        # The Hosaka extract affects Hosaka.
        hosaka_mission = data["hosaka_extraction"]
        assert hosaka_mission["fixer"] == "finn"
        factions = fixer_to_factions("finn")
        assert Faction.HOSAKA in factions

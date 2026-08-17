"""Tests for the build_dashboard metadata pipeline.

Covers the metadata → novel → story events → stages wiring:
- load_mission_stats: mission / chapters / aftermath / reactions /
  event_triggers / total_rewards fields
- load_event_dialogues_stats: npcs / dialogues / lines / characters
- load_stages_stats: stages / stage_enum / chapter_states / objectives
- _collect_event_trigger_names: parses EventTrigger enum from
  source (regex-based, robust to comments)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="dashboard restructured 2026-07-10")


# Load tools/build_dashboard.py directly (it's a script, not a package).
_TOOLS_DIR = Path(__file__).parent.parent.parent.parent / "tools"
_BUILD_DASH_PATH = _TOOLS_DIR / "build_dashboard.py"
_spec = importlib.util.spec_from_file_location("build_dashboard", _BUILD_DASH_PATH)
build_dashboard = importlib.util.module_from_spec(_spec)
sys.modules["build_dashboard"] = build_dashboard
_spec.loader.exec_module(build_dashboard)

_collect_event_trigger_names = build_dashboard._collect_event_trigger_names
load_event_dialogues_stats = build_dashboard.load_event_dialogues_stats
load_stages_stats = build_dashboard.load_stages_stats
load_mission_stats = build_dashboard.load_mission_stats


# Resolve REPO at runtime: try the test file's own tree first, then
# the parent. This handles the dual-tree layout (Game/ + Projects/)
# where the .venv lives in one and the source in the other.
def _find_repo() -> Path:
    p = Path(__file__).resolve().parent
    for _ in range(6):  # climb up to 6 levels
        if (p / "prototype" / "data" / "story" / "aftermath.json").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find REPO root with prototype/data/story")


REPO = _find_repo()
_PROJECTS_ROOT = Path("/Users/emilio/projects/Projects/Game/wet_run")


@pytest.fixture
def data_dir() -> Path:
    return REPO / "prototype" / "data"


# ============================================================================
# load_mission_stats
# ============================================================================


class TestLoadStoryStats:
    def test_basic_fields_present(self, data_dir: Path) -> None:
        stats = load_mission_stats(REPO)
        # Legacy fields
        assert stats["missions"] >= 25  # real game has 29+
        assert stats["arcs"] == 4  # case/sil/kas/suit
        assert stats["chapters"] == 4

    def test_aftermath_events_count(self, data_dir: Path) -> None:
        """Phase 6+ content expansion: 12 aftermath events in data."""
        stats = load_mission_stats(REPO)
        # Should be ≥12 (Phase 6+ expansion added 7 new events).
        assert stats["aftermath_events"] >= 12

    def test_reactions_count(self, data_dir: Path) -> None:
        """Phase 6+ content expansion: 25 reactions."""
        stats = load_mission_stats(REPO)
        assert stats["reactions"] >= 18  # 10 original + 15 new

    def test_reaction_characters_populated(self, data_dir: Path) -> None:
        stats = load_mission_stats(REPO)
        chars = stats["reaction_characters"]
        # New characters (3jane, sally) should appear after expansion.
        assert "3jane" in chars
        assert "sally" in chars
        assert "case" in chars
        assert "finn" in chars
        assert "dixie" in chars
        assert "maelcum" in chars

    def test_event_triggers_from_source(self, data_dir: Path) -> None:
        """Event trigger names parsed from event_story.py source."""
        stats = load_mission_stats(REPO)
        triggers = stats["event_triggers"]
        # Phase 6+ added 4 new triggers.
        assert "chapter_complete" in triggers
        assert "vendor_unlocked" in triggers
        assert "hub_visited" in triggers
        assert "dialogue_completed" in triggers
        # Original triggers still present.
        assert "npc_choice" in triggers
        assert "combat_end" in triggers

    def test_total_rewards(self, data_dir: Path) -> None:
        """Sum of all StoryReward items across all aftermath events."""
        stats = load_mission_stats(REPO)
        # At least 1 reward per event (12 events × 1+ = ≥12).
        assert stats["total_rewards"] >= 12

    def test_hub_visit_events_count(self, data_dir: Path) -> None:
        """atmosphere_hub_first_visit uses hub_visited trigger."""
        stats = load_mission_stats(REPO)
        # at least 1 hub_visited event (the one added in Phase 6+).
        assert stats["hub_visit_events"] >= 1


# ============================================================================
# load_event_dialogues_stats
# ============================================================================


class TestLoadEventDialoguesStats:
    def test_basic_fields(self, data_dir: Path) -> None:
        stats = load_event_dialogues_stats(_PROJECTS_ROOT)
        assert stats["npcs"] >= 5  # finn, dixie, maelcum, bartender, ta_rep
        assert stats["dialogues"] >= 10
        assert stats["lines"] >= 30

    def test_characters_list_populated(self, data_dir: Path) -> None:
        stats = load_event_dialogues_stats(_PROJECTS_ROOT)
        chars = stats["characters"]
        assert "finn" in chars
        assert "dixie" in chars
        assert "maelcum" in chars
        assert "bartender" in chars
        assert "ta_rep" in chars

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        stats = load_event_dialogues_stats(tmp_path)
        assert stats["npcs"] == 0
        assert stats["dialogues"] == 0
        assert stats["lines"] == 0


# ============================================================================
# load_stages_stats
# ============================================================================


class TestLoadStagesStats:
    def test_stages_from_source(self, data_dir: Path) -> None:
        """Stage enum count parsed from run/state.py source."""
        stats = load_stages_stats(_PROJECTS_ROOT)
        # CONTENT_EXPANSION Phase B added BRIEFING / TRAVEL /
        # BYPASS_SECURITY → 10 → 13 stages.
        # Phase 9 added SALVATION_EPILOGUE → 13 → 14 stages.
        assert stats["stages"] == 14
        assert stats["stage_enum"] == 14

    def test_chapter_states_from_source(self, data_dir: Path) -> None:
        """ChapterState enum: PROLOGUE + 3 ENDING_ + 5 IN_CHAPTER_ + 5 CHAPTER_*_COMPLETE + 3 SALVATION + 1 FINAL = 18."""
        stats = load_stages_stats(_PROJECTS_ROOT)
        assert stats["chapter_states"] == 18

    def test_objectives_from_source(self, data_dir: Path) -> None:
        """ObjectiveKind: NPC / DATA / ICE / NONE = 4."""
        stats = load_stages_stats(_PROJECTS_ROOT)
        assert stats["objectives"] == 4

    def test_missions_mirrors_story(self, data_dir: Path) -> None:
        stats = load_stages_stats(_PROJECTS_ROOT)
        story = load_mission_stats(_PROJECTS_ROOT)
        assert stats["missions"] == story["missions"]


# ============================================================================
# _collect_event_trigger_names (regex-based parser)
# ============================================================================


class TestCollectEventTriggerNames:
    def test_parses_event_story_source(self, data_dir: Path) -> None:
        """The regex parser correctly extracts all EventTrigger enum
        values from event_story.py source code."""
        triggers = _collect_event_trigger_names(REPO)
        # All 9 expected triggers should be in the result.
        assert len(triggers) == 9
        assert "npc_choice" in triggers
        assert "npc_greeting" in triggers
        assert "combat_end" in triggers
        assert "node_enter" in triggers
        assert "story_milestone" in triggers
        assert "chapter_complete" in triggers
        assert "vendor_unlocked" in triggers
        assert "hub_visited" in triggers
        assert "dialogue_completed" in triggers

    def test_fallback_when_source_missing(self, tmp_path: Path) -> None:
        """When event_story.py doesn't exist, fall back to the
        hard-coded list (with all 9 expected triggers)."""
        triggers = _collect_event_trigger_names(tmp_path)
        assert "npc_choice" in triggers
        assert "chapter_complete" in triggers
        assert "hub_visited" in triggers

    def test_handles_unparseable_source(self, tmp_path: Path) -> None:
        """If source exists but has no EventTrigger class, fall back."""
        bogus = tmp_path / "src" / "wet_run" / "engine"
        bogus.mkdir(parents=True)
        (bogus / "event_story.py").write_text("# no enum here\n", encoding="utf-8")
        triggers = _collect_event_trigger_names(tmp_path)
        # Falls back to default 9-trigger list.
        assert len(triggers) == 9


# ============================================================================
# data_index.json registry
# ============================================================================


class TestDataIndexRegistry:
    """The data_index.json must register the 2 new stats files."""

    def test_data_index_lists_new_stats(self) -> None:
        idx_path = REPO / "dashboard" / "data" / "data_index.json"
        if not idx_path.exists():
            pytest.skip("data_index.json not generated yet")
        data = json.loads(idx_path.read_text(encoding="utf-8"))
        outputs = data.get("outputs", {})
        assert "mission_stats.json" in outputs
        assert "event_dialogues_stats.json" in outputs
        assert "stages_stats.json" in outputs

    def test_all_stats_files_present(self) -> None:
        """Every stats JSON referenced in data_index must exist on disk."""
        idx_path = REPO / "dashboard" / "data" / "data_index.json"
        if not idx_path.exists():
            pytest.skip("data_index.json not generated yet")
        data = json.loads(idx_path.read_text(encoding="utf-8"))
        for filename in data.get("outputs", {}).keys():
            f = REPO / "dashboard" / "data" / filename
            assert f.exists(), f"data_index references missing file: {filename}"


# ============================================================================
# End-to-end metadata → stats → dashboard pipeline
# ============================================================================


class TestMetadataPipeline:
    """Verify the full metadata flow: source data → stats JSON → HTML."""

    def test_aftermath_event_count_matches_data(self, data_dir: Path) -> None:
        """Aftermath events in stats should match what's in the JSON."""
        aftermath_p = data_dir / "story" / "aftermath.json"
        if not aftermath_p.exists():
            pytest.skip("aftermath.json not available")
        data = json.loads(aftermath_p.read_text(encoding="utf-8"))
        stats = load_mission_stats(REPO)
        assert stats["aftermath_events"] == len(data)

    def test_reaction_count_matches_data(self, data_dir: Path) -> None:
        reactions_p = data_dir / "story" / "reactions.json"
        if not reactions_p.exists():
            pytest.skip("reactions.json not available")
        data = json.loads(reactions_p.read_text(encoding="utf-8"))
        stats = load_mission_stats(REPO)
        assert stats["reactions"] == len(data)

    def test_event_dialogue_count_matches_data(self, data_dir: Path) -> None:
        evt_p = REPO / "design" / "story" / "event_dialogues.json"
        if not evt_p.exists():
            pytest.skip("event_dialogues.json not available")
        data = json.loads(evt_p.read_text(encoding="utf-8"))
        stats = load_event_dialogues_stats(_PROJECTS_ROOT)
        npc_count = len(data.get("npcs", {}))
        dlg_count = len(data.get("dialogues", {}))
        assert stats["npcs"] == npc_count
        assert stats["dialogues"] == dlg_count

    def test_stages_html_loads_stages_stats_json(self) -> None:
        stages = REPO / "dashboard" / "stages.html"
        if not stages.exists():
            pytest.skip("stages.html not available")
        html = stages.read_text(encoding="utf-8")
        assert "stages_stats.json" in html

    def test_story_html_loads_event_dialogues_stats(self) -> None:
        story = REPO / "dashboard" / "missions.html"
        if not story.exists():
            pytest.skip("story.html not available")
        html = story.read_text(encoding="utf-8")
        assert "event_dialogues_stats.json" in html

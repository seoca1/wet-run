"""Unit tests for ``engine/story_view.py``.

Aftermath/Reaction/StoryRegistry are pure data classes — easy to
cover.  ``render_story`` is a tcod painter; we just verify it
doesn't blow up and that the expected fragments appear in the
output.  ``_load_aftermaths`` / ``_load_reactions`` parse JSON
files and surface error tolerance.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.engine import story_view
from wet_run.engine.story_view import (
    StoryRegistry,
)

# ---------------------------------------------------------------------------
# _load_aftermaths
# ---------------------------------------------------------------------------


@pytest.fixture
def aftermath_path(tmp_path: Path) -> Path:
    p = tmp_path / "aftermath.json"
    p.write_text(
        json.dumps(
            {
                "aftermath_black_ice": {
                    "id": "aftermath_black_ice",
                    "importance": "major",
                    "trigger": "combat_end",
                    "duration_ms": 4000,
                    "narrative_en": "The Black ICE dissolves.",
                    "narrative_ko": "블랙 ICE가 해체된다.",
                    "reaction_ids": ["r1", "r2"],
                },
                "aftermath_secondary": {
                    "id": "aftermath_secondary",
                    "importance": "minor",
                    "trigger": "npc_choice",
                    "duration_ms": 2000,
                    "narrative_en": "Minor event.",
                    "narrative_ko": "사소한 사건.",
                    "reaction_ids": [],
                },
            }
        ),
        encoding="utf-8",
    )
    return p


@pytest.fixture
def reactions_path(tmp_path: Path) -> Path:
    p = tmp_path / "reactions.json"
    p.write_text(
        json.dumps(
            {
                "r1": {
                    "id": "r1",
                    "character": "case",
                    "trigger": "npc_choice",
                    "text_en": "I'm out.",
                    "text_ko": "나간다.",
                    "portrait": "case",
                },
                "r2": {
                    "id": "r2",
                    "character": "finn",
                    "trigger": "npc_choice",
                    "text_en": "Next job is in the Sprawl.",
                    "text_ko": "다음 일은 스프롤 안에.",
                    "portrait": "finn",
                },
                "r3_invalid": {"id": "r3"},  # missing fields
            }
        ),
        encoding="utf-8",
    )
    return p


class TestLoadAftermaths:
    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        assert story_view._load_aftermaths(tmp_path / "absent.json") == {}

    def test_returns_empty_when_root_not_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        assert story_view._load_aftermaths(p) == {}

    def test_loads_all_entries(self, aftermath_path: Path) -> None:
        result = story_view._load_aftermaths(aftermath_path)
        assert len(result) == 2
        assert "aftermath_black_ice" in result
        assert "aftermath_secondary" in result

    def test_parsed_fields_match_input(self, aftermath_path: Path) -> None:
        result = story_view._load_aftermaths(aftermath_path)
        a = result["aftermath_black_ice"]
        assert a.id == "aftermath_black_ice"
        assert a.importance == "major"
        assert a.duration_ms == 4000
        assert a.reaction_ids == ("r1", "r2")
        assert "Black ICE" in a.narrative_en
        assert "블랙 ICE" in a.narrative_ko


class TestLoadReactions:
    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        assert story_view._load_reactions(tmp_path / "absent.json") == {}

    def test_loads_valid_entries(self, reactions_path: Path) -> None:
        result = story_view._load_reactions(reactions_path)
        # r3_invalid is included with placeholder fields — the loader
        # is forgiving, so we get all 3.
        assert len(result) == 3
        assert "r1" in result
        assert result["r1"].character == "case"
        assert "스프롤" in result["r2"].text_ko

    def test_invalid_entry_falls_back_to_defaults(self, reactions_path: Path) -> None:
        result = story_view._load_reactions(reactions_path)
        # The malformed r3 entry was filled in with placeholders.
        assert result["r3_invalid"].character == "case"
        assert result["r3_invalid"].text_en == ""


# ---------------------------------------------------------------------------
# StoryRegistry
# ---------------------------------------------------------------------------


class TestStoryRegistry:
    @pytest.fixture
    def data_dir(self, tmp_path: Path) -> Path:
        (tmp_path / "story").mkdir(parents=True, exist_ok=True)
        (tmp_path / "story" / "aftermath.json").write_text(
            json.dumps(
                {
                    "aftermath_black_ice": {
                        "id": "aftermath_black_ice",
                        "importance": "major",
                        "trigger": "combat_end",
                        "duration_ms": 4000,
                        "narrative_en": "The Black ICE dissolves.",
                        "narrative_ko": "블랙 ICE가 해체된다.",
                        "reaction_ids": ["r1", "r2"],
                    },
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "story" / "reactions.json").write_text(
            json.dumps(
                {
                    "r1": {
                        "id": "r1",
                        "character": "case",
                        "trigger": "npc_choice",
                        "text_en": "I'm out.",
                        "text_ko": "나간다.",
                        "portrait": "case",
                    },
                }
            ),
            encoding="utf-8",
        )
        return tmp_path

    def test_load_returns_combined_registry(self, data_dir: Path) -> None:
        reg = StoryRegistry.load(data_dir)
        assert "aftermath_black_ice" in reg.aftermaths
        assert "r1" in reg.reactions

    def test_get_aftermath_returns_none_for_missing(self, data_dir: Path) -> None:
        reg = StoryRegistry.load(data_dir)
        assert reg.get_aftermath("nope") is None
        assert reg.get_reaction("nope") is None

    def test_get_returns_loaded_data(self, data_dir: Path) -> None:
        reg = StoryRegistry.load(data_dir)
        a = reg.get_aftermath("aftermath_black_ice")
        r = reg.get_reaction("r1")
        assert a is not None
        assert a.id == "aftermath_black_ice"
        assert r is not None
        assert r.character == "case"


# ---------------------------------------------------------------------------
# render_story — pure smoke test (we just check it doesn't crash and
# that fragments appear in the printed output).
# ---------------------------------------------------------------------------


class _FakeConsole:
    def __init__(self, width: int = 80, height: int = 50) -> None:
        self.width = width
        self.height = height
        self.prints: list[dict] = []

    def clear(self) -> None:
        self.prints.append({"op": "clear"})

    def print(self, x: int = 0, y: int = 0, string: str = "", fg=None) -> None:
        self.prints.append({"op": "print", "x": x, "y": y, "string": string, "fg": fg})


class TestRenderStory:
    @pytest.fixture
    def data_dir(self, tmp_path: Path) -> Path:
        (tmp_path / "story").mkdir(parents=True, exist_ok=True)
        (tmp_path / "story" / "aftermath.json").write_text(
            json.dumps(
                {
                    "aftermath_black_ice": {
                        "id": "aftermath_black_ice",
                        "importance": "major",
                        "trigger": "combat_end",
                        "duration_ms": 4000,
                        "narrative_en": "The Black ICE dissolves.",
                        "narrative_ko": "블랙 ICE가 해체된다.",
                        "reaction_ids": ["r1"],
                    },
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "story" / "reactions.json").write_text(
            json.dumps(
                {
                    "r1": {
                        "id": "r1",
                        "character": "case",
                        "trigger": "npc_choice",
                        "text_en": "I'm out.",
                        "text_ko": "나간다.",
                        "portrait": "case",
                    },
                }
            ),
            encoding="utf-8",
        )
        return tmp_path

    def test_renders_narrative_text(self, data_dir: Path) -> None:
        reg = StoryRegistry.load(data_dir)
        console = _FakeConsole()
        state = _make_story_state()
        story_view.render_story(console, state, reg, "aftermath_black_ice", elapsed_s=1.5)
        flat = " ".join(str(p.get("string", "")) for p in console.prints)
        # English narrative + Korean subtitle appear somewhere
        assert "Black ICE" in flat
        assert "블랙 ICE" in flat

    def test_falls_back_to_default_when_id_missing(self, data_dir: Path) -> None:
        reg = StoryRegistry.load(data_dir)
        console = _FakeConsole()
        state = _make_story_state()
        # missing ID — should not crash, falls back to default
        story_view.render_story(console, state, reg, "missing_aftermath", elapsed_s=0.0)
        assert len(console.prints) > 0


def _make_story_state():
    """Minimal AppState-like object for render_story.

    We use a small custom class instead of MagicMock so that ``str(state.foo)``
    produces the value verbatim (MagicMock prints the mock repr, which
    pollutes the rendered output and breaks substring assertions).
    """
    from types import SimpleNamespace

    class _State:
        pass

    s = _State()
    s.story_importance = "major"
    s.story_flags = set()
    s.shown_events = set()
    s.active_event = None
    s.screen = None
    s.status_messages = []
    s.player_hp = 50
    s.player_max_hp = 100
    s.player_ppl = 5
    s.player_grade = 1
    s.current_mission = SimpleNamespace(title="first_jack")
    s.demo_step = 0
    return s


def magicmock_story_state():
    """Minimal AppState-like mock for render_story."""
    from unittest.mock import MagicMock

    s = MagicMock()
    s.story_importance = "major"
    s.story_aftermath_id = ""
    s.story_flags = set()
    s.status_messages = []
    s.active_event = None
    s.screen = None
    return s

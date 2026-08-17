"""Edge case tests for engine/graphic_novel_loaders.py (ADR-0060 Edge case 분석).

Covers defensive branches in _parse_scene + load_portrait/load_background prefix handling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.engine.graphic_novel_loaders import (
    _parse_scene,
    load_background,
    load_portrait,
)


class TestLoadPortrait:
    """load_portrait(art_dir, portrait_id) — JSON file loader with 'art:' prefix handling."""

    def test_loads_valid_portrait(self, tmp_path: Path) -> None:
        """Valid portrait JSON → Portrait dataclass returned."""
        art_dir = tmp_path / "art"
        portraits_dir = art_dir / "portraits"
        portraits_dir.mkdir(parents=True)
        (portraits_dir / "portraits.json").write_text(
            json.dumps(
                {
                    "case_think": {
                        "id": "art:case_think",
                        "title_en": "Thinking",
                        "title_ko": "생각 중",
                        "character": "novice",
                        "size": [10, 14],
                        "art": ["row1", "row2"],
                        "palette": {"@": [255, 255, 255]},
                        "char_colors": {"@": "white"},
                    }
                }
            ),
            encoding="utf-8",
        )
        portrait = load_portrait(art_dir, "art:case_think")
        assert portrait.id == "art:case_think"
        assert portrait.title_en == "Thinking"

    def test_strips_art_prefix(self, tmp_path: Path) -> None:
        """'art:case_think' and 'case_think' both resolve to the same portrait."""
        art_dir = tmp_path / "art"
        portraits_dir = art_dir / "portraits"
        portraits_dir.mkdir(parents=True)
        (portraits_dir / "portraits.json").write_text(
            json.dumps(
                {
                    "hero": {
                        "id": "art:hero",
                        "title_en": "Hero",
                        "title_ko": "영웅",
                        "character": "novice",
                        "size": [10, 14],
                        "art": ["row1"],
                        "palette": {},
                        "char_colors": {},
                    }
                }
            ),
            encoding="utf-8",
        )
        p1 = load_portrait(art_dir, "art:hero")
        p2 = load_portrait(art_dir, "hero")
        assert p1.id == p2.id

    def test_raises_when_portrait_id_missing(self, tmp_path: Path) -> None:
        """Unknown portrait_id → KeyError (no silent fallback)."""
        art_dir = tmp_path / "art"
        (art_dir / "portraits").mkdir(parents=True)
        (art_dir / "portraits" / "portraits.json").write_text("{}", encoding="utf-8")
        with pytest.raises(KeyError):
            load_portrait(art_dir, "nonexistent_portrait")


class TestLoadBackground:
    """load_background(art_dir, bg_id) — JSON file loader."""

    def test_loads_valid_background(self, tmp_path: Path) -> None:
        """Valid background JSON → Background dataclass returned."""
        art_dir = tmp_path / "art"
        bg_dir = art_dir / "backgrounds"
        bg_dir.mkdir(parents=True)
        (bg_dir / "backgrounds.json").write_text(
            json.dumps(
                {
                    "chiba_rain": {
                        "id": "chiba_rain",
                        "title_en": "Chiba Rain",
                        "title_ko": "지바 비",
                        "size": [80, 50],
                        "art": ["row1"],
                        "palette": {":": [50, 50, 50]},
                        "char_colors": {},
                    }
                }
            ),
            encoding="utf-8",
        )
        bg = load_background(art_dir, "chiba_rain")
        assert bg.id == "chiba_rain"
        assert bg.width == 80
        assert bg.height == 50


class TestParseSceneDefensiveBranches:
    """_parse_scene(raw) — defensive parsing for missing optional fields."""

    def test_missing_dialogue_field_uses_empty_list(self) -> None:
        """raw without 'dialogue' key → empty dialogue tuple (no crash)."""
        raw = {
            "id": "scene_test",
            "character": "novice",
            "title_en": "Test",
            "title_ko": "테스트",
        }
        scene = _parse_scene(raw)
        assert scene.dialogue == ()
        assert scene.id == "scene_test"

    def test_non_list_dialogue_field_uses_empty_list(self) -> None:
        """raw with 'dialogue' as non-list value → empty dialogue tuple (defensive)."""
        raw = {
            "id": "scene_test",
            "character": "novice",
            "title_en": "Test",
            "title_ko": "테스트",
            "dialogue": "not a list",
        }
        scene = _parse_scene(raw)
        assert scene.dialogue == ()

    def test_dialogue_with_missing_optional_fields_uses_defaults(self) -> None:
        """Dialogue entry with only speaker → other fields use defaults."""
        raw = {
            "id": "scene_test",
            "character": "novice",
            "title_en": "Test",
            "title_ko": "테스트",
            "dialogue": [{"speaker": "narrator"}],
        }
        scene = _parse_scene(raw)
        assert len(scene.dialogue) == 1
        assert scene.dialogue[0].speaker == "narrator"
        assert scene.dialogue[0].text_en == ""
        assert scene.dialogue[0].duration_ms == 5000

    def test_default_values_for_missing_top_level_fields(self) -> None:
        """Missing 'order', 'ending', 'background_id' → use defaults (0, 'A', '')."""
        raw = {
            "id": "scene_test",
            "character": "novice",
            "title_en": "Test",
            "title_ko": "테스트",
        }
        scene = _parse_scene(raw)
        assert scene.order == 0
        assert scene.ending == "A"
        assert scene.background_id == ""
        assert scene.portrait_left is None
        assert scene.portrait_right is None
        assert scene.next_scene is None

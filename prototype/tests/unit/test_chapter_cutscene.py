"""Unit tests for ``engine/chapter_cutscene.py``.

The module is mostly tcod console painters + JSON loaders.  The
loaders are pure data transformations and easy to cover end-to-end;
the painters we verify via the FakeConsole pattern.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wet_run.engine import chapter_cutscene
from wet_run.engine.chapter_cutscene import (
    ArcData,
    CombatData,
    CutsceneRef,
    get_arc_for_character,
    get_chapter,
    load_arc,
)

# ---------------------------------------------------------------------------
# Sample arc JSON
# ---------------------------------------------------------------------------


ARC_JSON = {
    "character": "case",
    "arc_id": "arc_case",
    "title_en": "Case's Arc",
    "title_ko": "케이의 아크",
    "description_en": "First arc",
    "description_ko": "첫 아크",
    "chapters": [
        {
            "chapter_number": 1,
            "chapter_id": "ch_1",
            "title_en": "First Jack",
            "title_ko": "첫 잭인",
            "description_en": "d1",
            "description_ko": "d1k",
            "cutscene_start": {"scene_id": "s1", "title_en": "Start", "title_ko": "시작"},
            "cutscene_mid": {"scene_id": "m1", "title_en": "Mid", "title_ko": "중간"},
            "cutscene_end": {"scene_id": "e1", "title_en": "End", "title_ko": "끝"},
            "phases": [
                {
                    "phase_id": "p1",
                    "phase_index": 0,
                    "title_en": "Phase 1",
                    "title_ko": "1단계",
                    "description_en": "p1d",
                    "description_ko": "p1dk",
                    "story_beats": ["b1", "b2"],
                    "beats": [
                        {"beat_id": "b1", "type": "action", "text_en": "Go", "text_ko": "가라"},
                        {"beat_id": "b2", "type": "dialogue", "text_en": "Hi", "text_ko": "안녕"},
                    ],
                    "game_action": "wait",
                    "combat": {
                        "encounter_id": "enc1",
                        "enemy_type": "wisp",
                        "difficulty": 2,
                        "outcome": "victory",
                        "damage_amount": 10,
                    },
                    "gain": "credits:100",
                    "loss": None,
                }
            ],
            "ending_type": "A",
            "next_chapter_id": "ch_2",
            "is_playable": True,
        },
        {
            "chapter_number": 2,
            "chapter_id": "ch_2",
            "title_en": "Second",
            "title_ko": "둘째",
            "description_en": "d2",
            "description_ko": "d2k",
            "phases": [],
            "ending_type": "B",
            "next_chapter_id": None,
            "is_playable": False,
        },
    ],
}


@pytest.fixture
def arc_path(tmp_path: Path) -> Path:
    p = tmp_path / "case_arc.json"
    p.write_text(json.dumps(ARC_JSON), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_arc
# ---------------------------------------------------------------------------


class TestLoadArc:
    def test_returns_arc_data(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        assert isinstance(arc, ArcData)
        assert arc.character == "case"
        assert arc.title_en == "Case's Arc"
        assert arc.title_ko == "케이의 아크"

    def test_parses_chapters_in_order(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        assert len(arc.chapters) == 2
        assert arc.chapters[0].chapter_id == "ch_1"
        assert arc.chapters[1].chapter_id == "ch_2"

    def test_parses_phases_and_beats(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        phase = arc.chapters[0].phases[0]
        assert phase.phase_id == "p1"
        assert phase.phase_index == 0
        assert len(phase.beats) == 2
        assert phase.beats[0].beat_id == "b1"
        assert phase.beats[0].type == "action"
        assert phase.beats[1].text_ko == "안녕"

    def test_parses_combat_data(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        phase = arc.chapters[0].phases[0]
        assert isinstance(phase.combat, CombatData)
        assert phase.combat.encounter_id == "enc1"
        assert phase.combat.enemy_type == "wisp"
        assert phase.combat.difficulty == 2
        assert phase.combat.outcome == "victory"
        assert phase.combat.damage_amount == 10

    def test_parses_cutscene_refs(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        ch = arc.chapters[0]
        assert isinstance(ch.cutscene_start, CutsceneRef)
        assert ch.cutscene_start.scene_id == "s1"
        assert ch.cutscene_mid.scene_id == "m1"
        assert ch.cutscene_end.scene_id == "e1"

    def test_next_chapter_id_can_be_none(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        assert arc.chapters[1].next_chapter_id is None
        assert arc.chapters[1].is_playable is False

    def test_handles_missing_optional_fields(self, tmp_path: Path) -> None:
        minimal = {
            "character": "x",
            "arc_id": "a",
            "title_en": "T",
            "title_ko": "Tk",
            "chapters": [
                {
                    "chapter_number": 1,
                    "chapter_id": "c1",
                    "title_en": "C1",
                    "title_ko": "C1k",
                    "phases": [],
                    "ending_type": "A",
                }
            ],
        }
        p = tmp_path / "x_arc.json"
        p.write_text(json.dumps(minimal), encoding="utf-8")
        arc = load_arc(p)
        assert arc.description_en == ""
        assert arc.description_ko == ""
        ch = arc.chapters[0]
        assert ch.cutscene_start is None
        assert ch.cutscene_mid is None
        assert ch.cutscene_end is None
        assert ch.is_playable is False
        assert ch.next_chapter_id is None


# ---------------------------------------------------------------------------
# get_arc_for_character
# ---------------------------------------------------------------------------


class TestGetArcForCharacter:
    def test_known_characters(self, tmp_path: Path) -> None:
        (tmp_path / "story" / "arcs").mkdir(parents=True)
        for char_id in ("case", "sil", "kas"):
            (tmp_path / "story" / "arcs" / f"{char_id}_arc.json").write_text(
                json.dumps(
                    {
                        "character": char_id,
                        "arc_id": f"arc_{char_id}",
                        "title_en": f"{char_id} arc",
                        "title_ko": "k",
                        "chapters": [
                            {
                                "chapter_number": 1,
                                "chapter_id": "c1",
                                "title_en": "c1",
                                "title_ko": "c1k",
                                "phases": [],
                                "ending_type": "A",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
        for nick, expected in (("novice", "case"), ("veteran", "sil"), ("heretic", "kas")):
            arc = get_arc_for_character(tmp_path, nick)
            assert arc.character == expected

    def test_unknown_character_falls_through(self, tmp_path: Path) -> None:
        # Unknown character id should still attempt to load <id>_arc.json.
        # Since the file doesn't exist, this raises FileNotFoundError.
        with pytest.raises(FileNotFoundError):
            get_arc_for_character(tmp_path, "unknown_hero")


# ---------------------------------------------------------------------------
# get_chapter
# ---------------------------------------------------------------------------


class TestGetChapter:
    def test_returns_chapter_by_number(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        ch = get_chapter(arc, 1)
        assert ch is not None
        assert ch.chapter_id == "ch_1"

    def test_returns_chapter_2(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        ch = get_chapter(arc, 2)
        assert ch is not None
        assert ch.chapter_id == "ch_2"

    def test_returns_none_for_missing(self, arc_path: Path) -> None:
        arc = load_arc(arc_path)
        assert get_chapter(arc, 99) is None


# ---------------------------------------------------------------------------
# get_cutscene — uses load_scene from another module
# ---------------------------------------------------------------------------


class _FakeScene:
    def __init__(self, scene_id: str):
        self.scene_id = scene_id


class TestGetCutscene:
    def test_resolves_via_load_scene(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sentinel = _FakeScene(scene_id="s1")
        monkeypatch.setattr(
            chapter_cutscene,
            "load_scene",
            lambda scenes_dir, scene_id: sentinel,
        )
        ref = CutsceneRef(scene_id="s1", title_en="t", title_ko="tk")
        out = chapter_cutscene.get_cutscene(Path("/scenes"), ref)
        assert out is sentinel


# ---------------------------------------------------------------------------
# render_chapter_cutscene — smoke test
# ---------------------------------------------------------------------------


class _FakeConsole:
    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self.prints: list[str] = []

    def clear(self) -> None:
        self.prints.append("__clear__")

    def print(self, x: int = 0, y: int = 0, string: str = "") -> None:
        self.prints.append(string)


class TestRenderCutsceneFrame:
    def test_renders_english_title_and_typed_text(self) -> None:
        from wet_run.engine.graphic_novel_view import (
            DialogueLine,
            SceneData,
        )

        line = DialogueLine(
            speaker="narrator",
            speaker_ko="narrator_ko",
            portrait="p",
            text_en="Hello world",
            text_ko="안녕 세계",
            duration_ms=5000,
        )
        scene = SceneData(
            id="s1",
            character="novice",
            order=0,
            title_en="Start",
            title_ko="시작",
            background_id="bg_chat",
            portrait_left=None,
            portrait_right=None,
            dialogue=(line,),
            next_scene=None,
        )

        class _State:
            typed_chars = 5  # half of "Hello"
            dialogue_index = 0

        state = _State()
        state.scene = scene
        state.current_line = line

        translator = MagicMock()
        translator.lang = "en"

        console = _FakeConsole()
        chapter_cutscene.render_cutscene_frame(
            console,
            state,
            background=None,
            portrait_l=None,
            portrait_r=None,
            translator=translator,
            scene_index=0,
            scene_total=3,
        )
        # Title should appear in the top bar
        assert any("Start" in s for s in console.prints)
        # "1/3" scene counter
        assert any("1/3" in s for s in console.prints)

    def test_uses_korean_text_when_lang_ko(self) -> None:
        from wet_run.engine.graphic_novel_view import (
            DialogueLine,
            SceneData,
        )

        line = DialogueLine(
            speaker="narrator",
            speaker_ko="narrator_ko",
            portrait="p",
            text_en="Hello",
            text_ko="안녕",
            duration_ms=5000,
        )
        scene = SceneData(
            id="s1",
            character="novice",
            order=0,
            title_en="Start",
            title_ko="시작",
            background_id="bg_chat",
            portrait_left=None,
            portrait_right=None,
            dialogue=(line,),
            next_scene=None,
        )

        class _State:
            typed_chars = 5
            dialogue_index = 0

        state = _State()
        state.scene = scene
        state.current_line = line

        translator = MagicMock()
        translator.lang = "ko"

        console = _FakeConsole()
        chapter_cutscene.render_cutscene_frame(
            console,
            state,
            background=None,
            portrait_l=None,
            portrait_r=None,
            translator=translator,
            scene_index=0,
            scene_total=1,
        )
        # Korean title appears
        assert any("시작" in s for s in console.prints)

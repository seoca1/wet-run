"""Tests for the graphic_novel_view module (ADR-0032).

Covers:
    - Portrait / Background / DialogueLine / SceneData dataclasses
    - load_portrait(), load_background()
    - load_scene(), load_scene_chain(), load_prologue_chain()
    - dialogue_typed_chars(), scene_progress()
    - render_scene() output stability
    - render_graphic_novel_menu() output
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import tcod.console  # noqa: E402

from wet_run.engine import graphic_novel_view  # noqa: E402
from wet_run.engine.graphic_novel_view import (  # noqa: E402
    Background,
    DialogueLine,
    Portrait,
    SceneData,
    dialogue_typed_chars,
    list_scenes_for_character,
    load_background,
    load_portrait,
    load_prologue_chain,
    load_scene,
    load_scene_chain,
    render_graphic_novel_menu,
    render_scene,
    scene_progress,
)
from wet_run.i18n import Translator  # noqa: E402

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SCENES_DIR = DATA_DIR / "scenes"
ART_DIR = DATA_DIR / "art"


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def en_translator() -> Translator:
    return Translator("en", data_dir=DATA_DIR / "i18n")


@pytest.fixture
def ko_translator() -> Translator:
    return Translator("ko", data_dir=DATA_DIR / "i18n")


@pytest.fixture
def scene_case_intro() -> SceneData:
    return load_scene(SCENES_DIR, "01_chattos")


# ----------------------------------------------------------------------------
# Portrait / Background / DialogueLine / SceneData
# ----------------------------------------------------------------------------


def test_portrait_frozen() -> None:
    p = Portrait(
        id="test",
        title_en="T",
        title_ko="T",
        character="case",
        width=10,
        height=12,
        art=("a", "b"),
        palette={"default": (200, 200, 220)},
        char_colors={},
    )
    with pytest.raises((AttributeError, Exception)):
        p.id = "hacked"  # type: ignore[misc]


def test_background_frozen() -> None:
    b = Background(
        id="test",
        title_en="T",
        title_ko="T",
        width=40,
        height=16,
        art=("a", "b"),
        palette={"default": (160, 160, 180)},
        char_colors={},
    )
    with pytest.raises((AttributeError, Exception)):
        b.id = "hacked"  # type: ignore[misc]


def test_dialogue_line_minimal() -> None:
    d = DialogueLine(
        speaker="case",
        speaker_ko="케이",
        portrait="art:case_think",
        text_en="hi",
        text_ko="안녕",
        duration_ms=5000,
    )
    assert d.sound is None  # default


# ----------------------------------------------------------------------------
# load_portrait / load_background
# ----------------------------------------------------------------------------


def test_load_portrait_case_think() -> None:
    p = load_portrait(ART_DIR, "art:case_think")
    assert p.id == "case_think"
    assert p.character == "case"
    assert p.width == 10
    assert len(p.art) == 12


def test_load_portrait_marly_mask() -> None:
    p = load_portrait(ART_DIR, "art:marly_mask")
    assert p.character == "marly"


def test_load_portrait_kumiko_wheel() -> None:
    p = load_portrait(ART_DIR, "art:kumiko_wheel")
    assert p.character == "kumiko"


def test_load_portrait_strips_prefix() -> None:
    """Both 'art:foo' and 'foo' should work."""
    p1 = load_portrait(ART_DIR, "art:case_think")
    p2 = load_portrait(ART_DIR, "case_think")
    assert p1.id == p2.id


def test_load_background_chat_room() -> None:
    b = load_background(ART_DIR, "art:bg_chat_room")
    assert b.id == "bg_chat_room"
    assert b.width == 40
    assert len(b.art) >= 14


def test_load_background_industrial() -> None:
    b = load_background(ART_DIR, "art:bg_industrial")
    assert b.id == "bg_industrial"


# ----------------------------------------------------------------------------
# load_scene
# ----------------------------------------------------------------------------


def test_load_scene_case_intro(scene_case_intro: SceneData) -> None:
    s = scene_case_intro
    assert s.id == "scene_case_intro"
    assert s.character == "novice"
    assert s.order == 1
    assert s.title_en == "CHATTO'S 24/7"
    assert s.next_scene == "scene_case_jackin"


def test_load_scene_has_dialogue(scene_case_intro: SceneData) -> None:
    assert len(scene_case_intro.dialogue) >= 1
    d = scene_case_intro.dialogue[0]
    assert d.speaker
    assert d.text_ko
    assert d.duration_ms > 0


def test_load_scene_has_background_id(scene_case_intro: SceneData) -> None:
    assert scene_case_intro.background_id == "bg_chat_room"


def test_load_scene_last_has_no_next() -> None:
    """Last scene in chain should have next_scene=None."""
    s = load_scene(SCENES_DIR, "04_finn")
    assert s.next_scene is None


# ----------------------------------------------------------------------------
# list_scenes_for_character
# ----------------------------------------------------------------------------


def test_list_scenes_novice() -> None:
    scenes = list_scenes_for_character(SCENES_DIR, "novice")
    assert len(scenes) == 9  # 4 ending A + 2 ending B + 2 ending C + 1 epilogue (ADR-0090)
    assert scenes == sorted(scenes)  # sorted by stem


def test_list_scenes_veteran() -> None:
    scenes = list_scenes_for_character(SCENES_DIR, "veteran")
    assert len(scenes) == 9  # 4 ending A + 2 ending B + 2 ending C + 1 epilogue (ADR-0090)


def test_list_scenes_heretic() -> None:
    scenes = list_scenes_for_character(SCENES_DIR, "heretic")
    assert len(scenes) == 9  # 4 ending A + 2 ending B + 2 ending C + 1 epilogue (ADR-0090)


def test_list_scenes_unknown_character() -> None:
    scenes = list_scenes_for_character(SCENES_DIR, "unknown")
    assert scenes == []


# ----------------------------------------------------------------------------
# load_scene_chain
# ----------------------------------------------------------------------------


def test_load_scene_chain_novice() -> None:
    chain = load_scene_chain(SCENES_DIR, "novice", max_order=8)
    assert len(chain) == 4  # ending A only by default (excludes epilogue)
    assert all(s.character == "novice" for s in chain)


def test_load_scene_chain_preserves_order() -> None:
    """Within a character, scenes should be in order."""
    chain = load_scene_chain(SCENES_DIR, "novice", max_order=8)
    orders = [s.order for s in chain]
    assert orders == sorted(orders)
    assert orders == [1, 2, 3, 4]


def test_load_scene_chain_shuffle() -> None:
    """shuffle=True should produce a permutation."""
    chain = load_scene_chain(SCENES_DIR, "novice", shuffle=True, seed=42, max_order=8)
    assert len(chain) == 4  # ending A only by default
    # Same set, different order
    orders = sorted(s.order for s in chain)
    assert orders == [1, 2, 3, 4]


# ----------------------------------------------------------------------------
# load_prologue_chain
# ----------------------------------------------------------------------------


def test_load_prologue_chain_length() -> None:
    chain = load_prologue_chain(SCENES_DIR, seed=42)
    # 9 chars × 4 scenes = 36
    assert len(chain) == 36


def test_load_prologue_chain_groups_characters() -> None:
    """Within a character group, scenes are in order."""
    chain = load_prologue_chain(SCENES_DIR, seed=42)
    # Find character boundaries
    char_groups: list[list[str]] = []
    current: list[str] = []
    current_char = chain[0].character
    for s in chain:
        if s.character != current_char:
            char_groups.append(current)
            current = []
            current_char = s.character
        current.append(s.id)
    char_groups.append(current)
    # Each group should have 4 scenes (ending A only — prologue uses default)
    for group in char_groups:
        assert len(group) == 4


def test_load_prologue_chain_seed_deterministic() -> None:
    """Same seed → same order."""
    chain1 = load_prologue_chain(SCENES_DIR, seed=42)
    chain2 = load_prologue_chain(SCENES_DIR, seed=42)
    assert [s.id for s in chain1] == [s.id for s in chain2]


def test_load_prologue_chain_different_seeds() -> None:
    """Different seeds → different orders (usually)."""
    chain1 = load_prologue_chain(SCENES_DIR, seed=42)
    chain2 = load_prologue_chain(SCENES_DIR, seed=99)
    # Different seeds should produce different orders at least sometimes
    # (3! = 6 possible orders, so collision is unlikely)
    if len({s.id for s in chain1[:4]}) > 1:  # not all from one character
        # Very likely different
        assert [s.id for s in chain1] != [s.id for s in chain2] or len(chain1) < 8


# ----------------------------------------------------------------------------
# dialogue_typed_chars
# ----------------------------------------------------------------------------


def test_dialogue_typed_chars_zero() -> None:
    assert dialogue_typed_chars(5000, 0, 100) == 0


def test_dialogue_typed_chars_partial() -> None:
    # 1000ms / 30ms = 33 chars
    assert dialogue_typed_chars(5000, 1000, 100) == 33


def test_dialogue_typed_chars_full() -> None:
    assert dialogue_typed_chars(5000, 99999, 100) == 100


def test_dialogue_typed_chars_zero_duration() -> None:
    assert dialogue_typed_chars(0, 99999, 100) == 100


# ----------------------------------------------------------------------------
# scene_progress
# ----------------------------------------------------------------------------


def test_scene_progress_zero() -> None:
    assert scene_progress(0, 12) == 0.0


def test_scene_progress_half() -> None:
    assert scene_progress(6, 12) == 0.5


def test_scene_progress_full() -> None:
    assert scene_progress(12, 12) == 1.0


def test_scene_progress_empty() -> None:
    assert scene_progress(0, 0) == 0.0


# ----------------------------------------------------------------------------
# render_scene
# ----------------------------------------------------------------------------


def test_render_scene_en(scene_case_intro: SceneData, en_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    bg = load_background(ART_DIR, scene_case_intro.background_id)
    p_l = (
        load_portrait(ART_DIR, scene_case_intro.portrait_left)
        if scene_case_intro.portrait_left
        else None
    )
    d = scene_case_intro.dialogue[0]
    render_scene(console, scene_case_intro, d, bg, p_l, None, en_translator, 50, 0, 4)
    text = graphic_novel_view._console_to_text(console)
    assert "CHATTO" in text or "case" in text


def test_render_scene_ko(scene_case_intro: SceneData, ko_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    bg = load_background(ART_DIR, scene_case_intro.background_id)
    p_l = (
        load_portrait(ART_DIR, scene_case_intro.portrait_left)
        if scene_case_intro.portrait_left
        else None
    )
    d = scene_case_intro.dialogue[0]
    render_scene(console, scene_case_intro, d, bg, p_l, None, ko_translator, 50, 0, 4)
    text = graphic_novel_view._console_to_text(console)
    # Korean text should appear
    assert "케이" in text or "챠토" in text


def test_render_scene_progress_bar(scene_case_intro: SceneData, en_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    bg = load_background(ART_DIR, scene_case_intro.background_id)
    p_l = (
        load_portrait(ART_DIR, scene_case_intro.portrait_left)
        if scene_case_intro.portrait_left
        else None
    )
    d = scene_case_intro.dialogue[0]
    render_scene(console, scene_case_intro, d, bg, p_l, None, en_translator, 100, 1, 4)
    text = graphic_novel_view._console_to_text(console)
    # 1/4 = 25% — should have some empty (░) blocks
    assert "░" in text


# ----------------------------------------------------------------------------
# render_graphic_novel_menu
# ----------------------------------------------------------------------------


def test_render_gn_menu_en(en_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    render_graphic_novel_menu(console, en_translator, selected_index=0)
    text = graphic_novel_view._console_to_text(console)
    assert "GRAPHIC" in text or "NOVEL" in text


def test_render_gn_menu_ko(ko_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    render_graphic_novel_menu(console, ko_translator, selected_index=0)
    text = graphic_novel_view._console_to_text(console)
    assert "그래픽" in text or "노블" in text


def test_render_gn_menu_selection_marker(en_translator: Translator) -> None:
    console = tcod.console.Console(80, 30, order="F")
    render_graphic_novel_menu(console, en_translator, selected_index=2)
    text = graphic_novel_view._console_to_text(console)
    # Selection marker should be present
    assert ">" in text


# ----------------------------------------------------------------------------
# Module API
# ----------------------------------------------------------------------------


def test_module_exports() -> None:
    """Public API surface."""
    assert callable(load_portrait)
    assert callable(load_background)
    assert callable(load_scene)
    assert callable(load_scene_chain)
    assert callable(load_prologue_chain)
    assert callable(render_scene)
    assert callable(render_graphic_novel_menu)


def test_all_24_scenes_loadable() -> None:
    """All scene JSON files must load (9 chars × 4 ending A + 9 chars × 2 ending B = 54)."""
    for char in (
        "novice",
        "veteran",
        "heretic",
        "suit",
        "wigan",
        "angie",
        "sally",
        "3jane",
        "neuromancer",
    ):
        chain_a = load_scene_chain(SCENES_DIR, char, ending="A", max_order=8)
        chain_b = load_scene_chain(SCENES_DIR, char, ending="B")
        assert len(chain_a) == 4, f"Expected 4 ending A scenes for {char}"
        assert len(chain_b) == 3 if char == "suit" else 2, f"Expected 2 ending B scenes for {char}"
        for chain in (chain_a, chain_b):
            for s in chain:
                assert s.dialogue
                assert s.title_en
                assert s.title_ko
                assert s.background_id


def test_all_scenes_have_valid_backgrounds() -> None:
    """Each scene's background_id must exist in backgrounds.json."""
    chain = load_prologue_chain(SCENES_DIR, seed=42)
    for s in chain:
        try:
            load_background(ART_DIR, s.background_id)
        except (KeyError, FileNotFoundError) as e:
            pytest.fail(f"Scene {s.id} has invalid background {s.background_id}: {e}")


def test_all_scenes_with_portrait_have_valid_portrait() -> None:
    """Each scene's portrait must exist in portraits.json."""
    chain = load_prologue_chain(SCENES_DIR, seed=42)
    for s in chain:
        for p_id in (s.portrait_left, s.portrait_right):
            if p_id:
                try:
                    load_portrait(ART_DIR, p_id)
                except (KeyError, FileNotFoundError) as e:
                    pytest.fail(f"Scene {s.id} has invalid portrait {p_id}: {e}")

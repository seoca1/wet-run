"""Graphic novel view — top-level screen coordinator (ADR-0032).

Thin coordinator module after the ADR-0133 v2 split (2026-08-05):
    - graphic_novel_data: SceneData, DialogueLine, Portrait, Background
    - graphic_novel_loaders: load_*, _parse_*, list_scenes_for_character
    - gn_render: render_scene + render_chapter_card + render_blank_transition + utilities
    - gn_menu: GRAPHIC_NOVEL_MENU + GRAPHIC_NOVEL_ENDING_MENU
    - graphic_novel_view (this file): render_graphic_novel_screen + _console_to_text + re-exports

The render_graphic_novel_screen function dispatches to gn_render for actual
scene rendering. This module exists for backward compatibility (ADR-0111):
existing imports of ``from .graphic_novel_view import SceneData,
load_prologue_chain, render_scene, render_graphic_novel_menu`` continue to
work via the re-exports below.

Module structure (post ADR-0133 v2 split) — view is now ~120 LOC coordinator
(down from 1266 LOC monolithic).

Auto-play loop:
    - Within a dialogue: type out text at 30ms/char
    - After dialogue duration: advance to next dialogue
    - After last dialogue: advance to next scene
    - After last scene: exit graphic novel
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

from ..combat.palette import DYING_COLOR, GRAY_BLACK
from .gn_menu import (  # noqa: F401 - re-exports for backward compat (ADR-0111)
    _ENDING_DESCRIPTIONS,
    GN_ENDING_A,
    GN_ENDING_B,
    GN_ENDING_BACK,
    GN_MENU_3JANE,
    GN_MENU_ANGIE,
    GN_MENU_BACK,
    GN_MENU_CONTINUE,
    GN_MENU_HERETIC,
    GN_MENU_NEUROMANCER,
    GN_MENU_NOVICE,
    GN_MENU_PROLOGUE,
    GN_MENU_SALLY,
    GN_MENU_SUIT,
    GN_MENU_VETERAN,
    GN_MENU_WIGAN,
    available_endings,
    get_gn_ending_menu_options,
    get_gn_menu_key,
    get_gn_menu_options,
    render_graphic_novel_ending_menu,
    render_graphic_novel_menu,
)
from .gn_render import (  # noqa: F401 - re-exports for backward compat (ADR-0111)
    NOVEL_LEFT_MARGIN,
    NOVEL_RIGHT_MARGIN,
    _character_label,
    _to_roman,
    compute_typed_page_index,
    dialogue_typed_chars,
    paginate_lines,
    render_blank_transition,
    render_chapter_card,
    render_scene,
    scene_progress,
    wrap_text_for_novel,
)
from .graphic_novel_data import (  # noqa: F401 - re-exports for backward compat (ADR-0111)
    Background,
    DialogueLine,
    Portrait,
    SceneData,
)
from .graphic_novel_loaders import (  # noqa: F401 - re-exports for backward compat (ADR-0111)
    _parse_char_colors,
    _parse_palette,
    _parse_scene,
    list_scenes_for_character,
    load_background,
    load_portrait,
    load_prologue_chain,
    load_scene,
    load_scene_chain,
)

if TYPE_CHECKING:
    from .state import AppState

if TYPE_CHECKING:
    from ..i18n import Translator


# ============================================================================
# Top-level screen coordinator
# ============================================================================


def render_graphic_novel_screen(
    console: tcod.console.Console,
    state: AppState,
    translator: Translator,
) -> None:
    """Phase D-2: extracted GRAPHIC_NOVEL screen render logic.

    Renders current scene + dialogue with background/portrait loading
    and typing animation. Replaces 50 LOC of inline code in app.py.

    Coordinator: dispatches to ``gn_render.render_scene`` for the actual
    scene rendering (ADR-0133 v2 split).
    """
    scenes = state.gn_scenes
    if scenes and 0 <= state.gn_scene_index < len(scenes):
        scene = scenes[state.gn_scene_index]
        if scene.dialogue and 0 <= state.gn_dialogue_index < len(scene.dialogue):
            dialogue = scene.dialogue[state.gn_dialogue_index]
            bg = None
            if scene.background_id:
                try:
                    from . import config as _gn_config

                    bg = load_background(_gn_config.DATA_DIR / "art", scene.background_id)
                except Exception:
                    pass
            p_l = None
            p_r = None
            if scene.portrait_left:
                try:
                    from . import config as _gn_config

                    p_l = load_portrait(_gn_config.DATA_DIR / "art", scene.portrait_left)
                except Exception:
                    pass
            if scene.portrait_right:
                try:
                    from . import config as _gn_config

                    p_r = load_portrait(_gn_config.DATA_DIR / "art", scene.portrait_right)
                except Exception:
                    pass
            typed = dialogue_typed_chars(
                dialogue.duration_ms, state.gn_elapsed_ms, len(dialogue.text_en)
            )
            render_scene(
                console,
                scene,
                dialogue,
                bg,
                p_l,
                p_r,
                translator,
                typed,
                state.gn_scene_index,
                len(scenes),
                paused=state.gn_paused,
            )
        else:
            console.clear(bg=GRAY_BLACK)
            console.print(x=2, y=2, string="=== NO DIALOGUE ===", fg=DYING_COLOR)
    else:
        console.clear(bg=GRAY_BLACK)
        console.print(x=2, y=2, string="=== NO SCENES LOADED ===", fg=DYING_COLOR)


def _console_to_text(console: tcod.console.Console) -> str:
    """Convert a tcod console buffer to plain text (one char per cell).

    Used by tests and headless demos.
    """
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


__all__ = [
    "Background",
    "DialogueLine",
    "GN_ENDING_A",
    "GN_ENDING_B",
    "GN_ENDING_BACK",
    "GN_MENU_3JANE",
    "GN_MENU_ANGIE",
    "GN_MENU_BACK",
    "GN_MENU_CONTINUE",
    "GN_MENU_HERETIC",
    "GN_MENU_NEUROMANCER",
    "GN_MENU_NOVICE",
    "GN_MENU_PROLOGUE",
    "GN_MENU_SALLY",
    "GN_MENU_SUIT",
    "GN_MENU_VETERAN",
    "GN_MENU_WIGAN",
    "NOVEL_LEFT_MARGIN",
    "NOVEL_RIGHT_MARGIN",
    "Portrait",
    "SceneData",
    "_character_label",
    "_console_to_text",
    "_ENDING_DESCRIPTIONS",
    "_parse_char_colors",
    "_parse_palette",
    "_parse_scene",
    "_to_roman",
    "available_endings",
    "compute_typed_page_index",
    "dialogue_typed_chars",
    "get_gn_ending_menu_options",
    "get_gn_menu_key",
    "get_gn_menu_options",
    "list_scenes_for_character",
    "load_background",
    "load_portrait",
    "load_prologue_chain",
    "load_scene",
    "load_scene_chain",
    "paginate_lines",
    "render_blank_transition",
    "render_chapter_card",
    "render_graphic_novel_ending_menu",
    "render_graphic_novel_menu",
    "render_graphic_novel_screen",
    "render_scene",
    "scene_progress",
    "wrap_text_for_novel",
]

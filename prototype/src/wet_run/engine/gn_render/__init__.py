"""Graphic novel render functions — sub-package re-export shim (ADR-0032 + ADR-0042).

Split from the monolithic gn_render.py (ADR-0142 v2 pattern, ADR-0110 size policy).
The original 761 LOC file is now a 3-way sub-package:

    - gn_render.text  : constants, _to_roman, wrap_text_for_novel, paginate_lines,
                        compute_typed_page_index (text utilities, no rendering)
    - gn_render.scene : dialogue_typed_chars, scene_progress, render_scene + helpers
                        (book-page scene rendering with portrait/bg/prose)
    - gn_render.card  : _character_label, render_chapter_card + helpers,
                        render_blank_transition (inter-scene transitions + fade)

This ``__init__`` re-exports the public API so existing imports of
``from wet_run.engine.gn_render import ...`` continue to work without
modification (ADR-0111 backward compatibility).
"""

from __future__ import annotations

from ..graphic_novel_data import Background, DialogueLine, Portrait, SceneData
from .card import _character_label, render_blank_transition, render_chapter_card
from .scene import dialogue_typed_chars, render_scene, scene_progress
from .text import (
    NOVEL_LEFT_MARGIN,
    NOVEL_RIGHT_MARGIN,
    _to_roman,
    compute_typed_page_index,
    paginate_lines,
    wrap_text_for_novel,
)

__all__ = [
    "Background",
    "DialogueLine",
    "NOVEL_LEFT_MARGIN",
    "NOVEL_RIGHT_MARGIN",
    "Portrait",
    "SceneData",
    "_character_label",
    "_to_roman",
    "compute_typed_page_index",
    "dialogue_typed_chars",
    "paginate_lines",
    "render_blank_transition",
    "render_chapter_card",
    "render_scene",
    "scene_progress",
    "wrap_text_for_novel",
]

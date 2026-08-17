"""Graphic novel data classes — Portrait, Background, DialogueLine, SceneData.

Extracted from graphic_novel_view.py (ADR-0111 split, 2026-07-27).
These dataclasses are the canonical data shapes for graphic novel content.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Portrait:
    """A character portrait (10x12 Unicode block art) with per-cell color.

    Attributes:
        id: Portrait identifier (e.g. "case_think")
        title_en: English title
        title_ko: Korean title
        character: Character id (case, marly, kumiko, etc.)
        width: Portrait width in cells
        height: Portrait height in cells
        art: Tuple of art lines
        palette: Mapping from color key to RGB tuple, e.g. {"default": (200,200,220), "eyes": (80,160,255)}
        char_colors: Mapping from character to palette key, e.g. {"◉": "eyes", "─": "default"}
    """

    id: str
    title_en: str
    title_ko: str
    character: str
    width: int
    height: int
    art: tuple[str, ...]
    palette: dict[str, tuple[int, int, int]]
    char_colors: dict[str, str]


@dataclass(frozen=True, slots=True)
class Background:
    """A background scene (40x16 Unicode block art) with per-cell color.

    Attributes:
        id: Background identifier (e.g. "bg_chat_room")
        title_en: English title
        title_ko: Korean title
        width: Width in cells
        height: Height in cells
        art: Tuple of art lines
        palette: Mapping from color key to RGB tuple
        char_colors: Mapping from character to palette key
    """

    id: str
    title_en: str
    title_ko: str
    width: int
    height: int
    art: tuple[str, ...]
    palette: dict[str, tuple[int, int, int]]
    char_colors: dict[str, str]


@dataclass(frozen=True, slots=True)
class DialogueLine:
    """A single line of dialogue in a scene.

    Attributes:
        speaker: English speaker name (or "narrator")
        speaker_ko: Korean speaker name
        portrait: Portrait id (or None for narrator)
        text_en: English text
        text_ko: Korean text
        duration_ms: How long to display this line
        sound: Optional sound cue id
    """

    speaker: str
    speaker_ko: str
    portrait: str | None
    text_en: str
    text_ko: str
    duration_ms: int
    sound: str | None = None


@dataclass(frozen=True, slots=True)
class SceneData:
    """A complete scene with art + dialogue.

    Attributes:
        id: Unique scene id (e.g. "scene_case_intro")
        character: "novice" | "veteran" | "heretic"
        order: Sequence number within character
        ending: "A" (default) or "B" — which ending variant this scene is part of
        title_en: English title
        title_ko: Korean title
        background_id: Background id
        portrait_left: Portrait id (or None)
        portrait_right: Portrait id (or None)
        dialogue: Tuple of DialogueLine
        next_scene: Next scene id (or None for last)
    """

    id: str
    character: str
    order: int
    title_en: str
    title_ko: str
    background_id: str
    portrait_left: str | None
    portrait_right: str | None
    dialogue: tuple[DialogueLine, ...]
    next_scene: str | None
    ending: str = "A"


__all__ = [
    "Background",
    "DialogueLine",
    "Portrait",
    "SceneData",
]

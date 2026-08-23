"""Graphic novel loaders — JSON parsing + scene/art chain loading.

Extracted from graphic_novel_view.py (ADR-0111 split, 2026-07-27).
Owns all disk I/O for graphic novel assets: portraits, backgrounds, scenes,
and per-character scene chains (load_scene_chain, load_prologue_chain).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..combat.palette import GRAY_BRIGHT
from .graphic_novel_data import (
    Background,
    DialogueLine,
    Portrait,
    SceneData,
)


def _parse_palette(raw_palette: object) -> dict[str, tuple[int, int, int]]:
    """Parse a palette dict from JSON: values can be RGB lists or palette-key strings."""
    if not raw_palette:
        return {"default": GRAY_BRIGHT}
    result: dict[str, tuple[int, int, int]] = {}
    if isinstance(raw_palette, dict):
        for k, v in raw_palette.items():
            if isinstance(v, list) and len(v) == 3:
                result[k] = (v[0], v[1], v[2])
            elif isinstance(v, str) and v in result:
                result[k] = result[v]
    return result if result else {"default": GRAY_BRIGHT}


def _parse_char_colors(raw: object) -> dict[str, str]:
    """Parse char_colors dict from JSON: maps single characters to palette keys."""
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def load_portrait(art_dir: Path, portrait_id: str) -> Portrait:
    """Load a portrait by id from data/art/portraits/portraits.json.

    The id is in the format "art:case_think" or just "case_think".
    """
    short_id = portrait_id.removeprefix("art:")
    path = art_dir / "portraits" / "portraits.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data[short_id]
    palette = _parse_palette(raw.get("palette"))
    char_colors = _parse_char_colors(raw.get("char_colors"))
    height = raw.get("size", [10, 12])[1]
    return Portrait(
        id=raw["id"],
        title_en=raw["title_en"],
        title_ko=raw["title_ko"],
        character=raw["character"],
        width=raw["size"][0],
        height=height,
        art=tuple(raw["art"]),
        palette=palette,
        char_colors=char_colors,
    )


def load_background(art_dir: Path, bg_id: str) -> Background:
    """Load a background by id from data/art/backgrounds/backgrounds.json."""
    short_id = bg_id.removeprefix("art:")
    path = art_dir / "backgrounds" / "backgrounds.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data[short_id]
    palette = _parse_palette(raw.get("palette"))
    char_colors = _parse_char_colors(raw.get("char_colors"))
    return Background(
        id=raw["id"],
        title_en=raw["title_en"],
        title_ko=raw["title_ko"],
        width=raw["size"][0],
        height=raw["size"][1],
        art=tuple(raw["art"]),
        palette=palette,
        char_colors=char_colors,
    )


def _parse_scene(raw: dict[str, object]) -> SceneData:
    """Parse a scene JSON dict into a SceneData."""
    raw_dialogue = raw.get("dialogue", [])
    if not isinstance(raw_dialogue, list):
        raw_dialogue = []
    dialogue = tuple(
        DialogueLine(
            speaker=str(d.get("speaker", "")),
            speaker_ko=str(d.get("speaker_ko", d.get("speaker", ""))),
            portrait=str(d["portrait"]) if d.get("portrait") is not None else None,
            text_en=str(d.get("text_en", "")),
            text_ko=str(d.get("text_ko", d.get("text_en", ""))),
            duration_ms=int(str(d.get("duration_ms", 5000))),
            sound=str(d["sound"]) if d.get("sound") is not None else None,
        )
        for d in raw_dialogue
    )
    return SceneData(
        id=str(raw["id"]),
        character=str(raw["character"]),
        order=int(str(raw.get("order", 0))),
        ending=str(raw.get("ending", "A")),
        title_en=str(raw["title_en"]),
        title_ko=str(raw["title_ko"]),
        background_id=str(raw.get("background_id", "")),
        portrait_left=str(raw["portrait_left"]) if raw.get("portrait_left") is not None else None,
        portrait_right=str(raw["portrait_right"])
        if raw.get("portrait_right") is not None
        else None,
        dialogue=dialogue,
        next_scene=str(raw["next_scene"]) if raw.get("next_scene") is not None else None,
    )


def load_scene(scenes_dir: Path, scene_id: str) -> SceneData:
    """Load a scene by id from data/scenes/{character}/{scene_id}.json.

    Search through all character subdirectories.
    """
    for char_dir in scenes_dir.iterdir():
        if not char_dir.is_dir():
            continue
        for path in char_dir.glob("*.json"):
            if path.stem in scene_id or scene_id in path.stem:
                raw = json.loads(path.read_text(encoding="utf-8"))
                return _parse_scene(raw)
    for char_dir in scenes_dir.iterdir():
        if not char_dir.is_dir():
            continue
        for path in char_dir.glob("*.json"):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if str(raw.get("id", "")) == scene_id:
                return _parse_scene(raw)
    raise FileNotFoundError(f"Scene {scene_id!r} not found in {scenes_dir}")


# Per-character directory mapping (graphic_novel ↔ data/scenes subdir name).
_CHAR_TO_DIR: dict[str, str] = {
    "novice": "case",
    "veteran": "sil",
    "heretic": "kas",
    "suit": "suit",
    "wigan": "wigan",
    "angie": "angie",
    "sally": "sally",
    "3jane": "3jane",
    "neuromancer": "neuromancer",
}


def list_scenes_for_character(scenes_dir: Path, character: str) -> list[str]:
    """Return sorted list of scene file stems for a character.

    Args:
        scenes_dir: Path to data/scenes/
        character: "novice" | "veteran" | "heretic" | "suit" | "wigan" | "angie" | "sally"

    Returns:
        List of scene file stems (e.g. ["01_chattos", "02_jackin", ...])
    """
    char_dir_name = _CHAR_TO_DIR.get(character)
    if char_dir_name is None:
        return []
    char_dir = scenes_dir / char_dir_name
    if not char_dir.exists():
        return []
    return sorted(p.stem for p in char_dir.glob("*.json"))


def load_scene_chain(
    scenes_dir: Path,
    character: str,
    *,
    shuffle: bool = False,
    seed: int | None = None,
    ending: str = "A",
    max_order: int = 999,
) -> list[SceneData]:
    """Load a chain of scenes for a character.

    Args:
        scenes_dir: Path to data/scenes/
        character: "novice" | "veteran" | "heretic"
        shuffle: If True, shuffle scene order (per-character shuffle).
        seed: Optional random seed for reproducibility.
        ending: "A" (default) or "B" — which ending set to load.
            Scenes with matching ``"ending"`` field are included. Scenes
            without an ``"ending"`` field default to "A".
        max_order: Include scenes with order <= this value.

    Returns:
        List of SceneData in order.
    """
    stems = list_scenes_for_character(scenes_dir, character)
    char_dir = scenes_dir / _CHAR_TO_DIR[character]

    filtered_stems: list[str] = []
    for stem in stems:
        try:
            raw = json.loads((char_dir / f"{stem}.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        scene_ending = raw.get("ending", "A")
        if scene_ending == ending:
            order = raw.get("order", 999)
            if order <= max_order:
                filtered_stems.append(stem)

    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(filtered_stems)

    return [
        _parse_scene(json.loads((char_dir / f"{stem}.json").read_text())) for stem in filtered_stems
    ]


def load_prologue_chain(
    scenes_dir: Path,
    *,
    seed: int | None = None,
    ending: str = "A",
    max_order: int = 8,
) -> list[SceneData]:
    """Load the prologue chain: characters × scenes, characters in random order.

    Args:
        scenes_dir: Path to data/scenes/
        seed: Optional random seed for reproducibility.
        ending: "A" (default) or "B" — which ending set to load.
        max_order: Include scenes with order <= this value (8 excludes epilogue).
    """
    chars = list(_CHAR_TO_DIR.keys())
    rng = random.Random(seed)
    rng.shuffle(chars)
    chain: list[SceneData] = []
    for char in chars:
        chain.extend(
            load_scene_chain(scenes_dir, char, shuffle=False, ending=ending, max_order=max_order)
        )
    return chain


__all__ = [
    "_CHAR_TO_DIR",
    "_parse_char_colors",
    "_parse_palette",
    "_parse_scene",
    "list_scenes_for_character",
    "load_background",
    "load_portrait",
    "load_prologue_chain",
    "load_scene",
    "load_scene_chain",
]

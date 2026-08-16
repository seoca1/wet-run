"""Chapter cutscene support — reuses GN scenes as chapter cutscenes.

Provides:
    - ArcData: dataclass wrapping an arc JSON (5 chapters per character)
    - load_arc: load arc JSON from data/story/arcs/
    - get_cutscene: resolve a cutscene scene_id to SceneData (reuses GN scene)
    - render_cutscene_frame: render a cutscene frame to console
    - ChapterCutsceneState: per-chapter-cutscene playback state

Chapter flow:
    CHARACTER_SELECT → PROLOGUE (cutscene) → HUB → CHAPTER_PHASE_N → ... → CHAPTER_END
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import tcod.console

from .graphic_novel_view import (
    Background,
    DialogueLine,
    Portrait,
    SceneData,
    load_scene,
)

if TYPE_CHECKING:
    from ..i18n import Translator


@dataclass(frozen=True, slots=True)
class CombatData:
    """Combat encounter data within a phase."""

    encounter_id: str
    enemy_type: str
    difficulty: int
    outcome: str
    damage_amount: int | None = None


@dataclass(frozen=True, slots=True)
class BeatData:
    """A single beat (text unit) within a phase."""

    beat_id: str
    type: str
    text_en: str
    text_ko: str


@dataclass(frozen=True, slots=True)
class PhaseData:
    """A single Phase within a chapter."""

    phase_id: str
    phase_index: int
    title_en: str
    title_ko: str
    description_en: str
    description_ko: str
    episode_ref: str | None = None
    story_beats: tuple[str, ...] = ()
    beats: tuple[BeatData, ...] = ()
    game_action: str | None = None
    combat: CombatData | None = None
    gain: str | None = None
    loss: str | None = None


@dataclass(frozen=True, slots=True)
class CutsceneRef:
    """Reference to a GN scene used as a chapter cutscene."""

    scene_id: str
    title_en: str
    title_ko: str


@dataclass(frozen=True, slots=True)
class ChapterData:
    """A single Chapter within an Arc."""

    chapter_number: int
    chapter_id: str
    title_en: str
    title_ko: str
    description_en: str
    description_ko: str
    cutscene_start: CutsceneRef | None
    cutscene_mid: CutsceneRef | None
    cutscene_end: CutsceneRef | None
    phases: tuple[PhaseData, ...]
    ending_type: str
    next_chapter_id: str | None
    is_playable: bool


@dataclass(frozen=True, slots=True)
class ArcData:
    """Complete Arc for one character (5 Chapters)."""

    character: str
    arc_id: str
    title_en: str
    title_ko: str
    description_en: str
    description_ko: str
    chapters: tuple[ChapterData, ...]


def load_arc(arc_path: Path) -> ArcData:
    """Load an arc JSON file."""
    raw = json.loads(arc_path.read_text(encoding="utf-8"))

    chapters = []
    for ch in raw.get("chapters", []):
        phases = []
        for ph in ch.get("phases", []):
            combat_data = None
            if ph.get("combat"):
                c = ph["combat"]
                combat_data = CombatData(
                    encounter_id=str(c.get("encounter_id", "")),
                    enemy_type=str(c.get("enemy_type", "")),
                    difficulty=int(c.get("difficulty", 0)),
                    outcome=str(c.get("outcome", "")),
                    damage_amount=c.get("damage_amount"),
                )

            beats = tuple(
                BeatData(
                    beat_id=str(b.get("beat_id", "")),
                    type=str(b.get("type", "")),
                    text_en=str(b.get("text_en", "")),
                    text_ko=str(b.get("text_ko", "")),
                )
                for b in ph.get("beats", [])
            )

            phases.append(
                PhaseData(
                    phase_id=str(ph["phase_id"]),
                    phase_index=int(ph["phase_index"]),
                    title_en=str(ph["title_en"]),
                    title_ko=str(ph["title_ko"]),
                    description_en=str(ph["description_en"]),
                    description_ko=str(ph["description_ko"]),
                    episode_ref=ph.get("episode_ref"),
                    story_beats=tuple(ph.get("story_beats", [])),
                    beats=beats,
                    game_action=ph.get("game_action"),
                    combat=combat_data,
                    gain=ph.get("gain"),
                    loss=ph.get("loss"),
                )
            )

        cs_start = None
        if ch.get("cutscene_start"):
            cs = ch["cutscene_start"]
            cs_start = CutsceneRef(
                scene_id=str(cs["scene_id"]),
                title_en=str(cs["title_en"]),
                title_ko=str(cs["title_ko"]),
            )

        cs_mid = None
        if ch.get("cutscene_mid"):
            cs = ch["cutscene_mid"]
            cs_mid = CutsceneRef(
                scene_id=str(cs["scene_id"]),
                title_en=str(cs["title_en"]),
                title_ko=str(cs["title_ko"]),
            )

        cs_end = None
        if ch.get("cutscene_end"):
            cs = ch["cutscene_end"]
            cs_end = CutsceneRef(
                scene_id=str(cs["scene_id"]),
                title_en=str(cs["title_en"]),
                title_ko=str(cs["title_ko"]),
            )

        chapters.append(
            ChapterData(
                chapter_number=int(ch["chapter_number"]),
                chapter_id=str(ch["chapter_id"]),
                title_en=str(ch["title_en"]),
                title_ko=str(ch["title_ko"]),
                description_en=str(ch.get("description_en", "")),
                description_ko=str(ch.get("description_ko", "")),
                cutscene_start=cs_start,
                cutscene_mid=cs_mid,
                cutscene_end=cs_end,
                phases=tuple(phases),
                ending_type=str(ch.get("ending_type", "A")),
                next_chapter_id=str(ch["next_chapter_id"]) if ch.get("next_chapter_id") else None,
                is_playable=bool(ch.get("is_playable", False)),
            )
        )

    return ArcData(
        character=str(raw["character"]),
        arc_id=str(raw["arc_id"]),
        title_en=str(raw["title_en"]),
        title_ko=str(raw["title_ko"]),
        description_en=str(raw.get("description_en", "")),
        description_ko=str(raw.get("description_ko", "")),
        chapters=tuple(chapters),
    )


def get_arc_for_character(data_dir: Path, character: str) -> ArcData:
    """Load the Arc JSON for a given character."""
    char_to_arc = {"novice": "case", "veteran": "sil", "heretic": "kas"}
    arc_id = char_to_arc.get(character, character)
    arc_file = f"{arc_id}_arc.json"
    return load_arc(data_dir / "story" / "arcs" / arc_file)


def get_chapter(arc: ArcData, chapter_number: int) -> ChapterData | None:
    """Return a specific chapter by number (1-indexed)."""
    for ch in arc.chapters:
        if ch.chapter_number == chapter_number:
            return ch
    return None


def get_cutscene(scenes_dir: Path, cutscene_ref: CutsceneRef) -> SceneData:
    """Resolve a cutscene scene_id to actual SceneData (reuses GN scene)."""
    return load_scene(scenes_dir, cutscene_ref.scene_id)


@dataclass
class ChapterCutsceneState:
    """Playback state for a single cutscene within a chapter."""

    scene: SceneData
    dialogue_index: int = 0
    typed_chars: int = 0
    elapsed_ms: int = 0
    done: bool = False
    char_delay_ms: int = 30

    def tick(self, dt_ms: int) -> None:
        """Advance the cutscene timer and typing effect."""
        self.elapsed_ms += dt_ms
        # Typing effect: advance character display
        chars_to_add = self.elapsed_ms // self.char_delay_ms
        full_text = self.current_line.text_en
        self.typed_chars = min(chars_to_add, len(full_text))
        if self.elapsed_ms >= self.current_line.duration_ms:
            self.typed_chars = len(full_text)
            self.advance()

    @property
    def current_line(self) -> DialogueLine:
        """Return the dialogue line the player is currently seeing.

        Index is 0-based and bounded by ``len(self.scene.dialogue)``.
        Callers advance it via :meth:`advance` (auto on
        :meth:`tick` expiry); reading the property does not mutate
        ``dialogue_index``, so it is safe to call from render code
        without affecting playback.
        """
        return self.scene.dialogue[self.dialogue_index]

    def advance(self) -> None:
        """Move to the next dialogue line or mark done."""
        if self.dialogue_index + 1 < len(self.scene.dialogue):
            self.dialogue_index += 1
            self.typed_chars = 0
            self.elapsed_ms = 0
        else:
            self.done = True

    def skip_to_end(self) -> None:
        """Skip to the end of the cutscene."""
        self.done = True


def render_cutscene_frame(
    console: tcod.console.Console,
    state: ChapterCutsceneState,
    background: Background | None,
    portrait_l: Portrait | None,
    portrait_r: Portrait | None,
    translator: Translator,
    scene_index: int,
    scene_total: int,
) -> None:
    """Render one frame of a chapter cutscene (simplified GN style).

    Args:
        console: tcod console.
        state: Cutscene playback state.
        background: Optional background art.
        portrait_l: Optional left portrait.
        portrait_r: Optional right portrait.
        translator: i18n translator.
        scene_index: Index of this cutscene within the chapter (0-based).
        scene_total: Total number of cutscenes in this chapter.
    """
    width: int = console.width
    height: int = console.height
    console.clear()

    is_ko = translator.lang == "ko"
    scene = state.scene
    line = state.current_line

    title = scene.title_ko if is_ko else scene.title_en
    speaker = line.speaker_ko if is_ko else line.speaker
    full_text = line.text_ko if is_ko else line.text_en
    typed_text = full_text[: state.typed_chars]

    # Top bar
    top = f" [{scene_index + 1}/{scene_total}]  {title}"
    console.print(0, 0, top[:width])
    console.print(0, 1, "=" * width)

    # Background
    if background is not None:
        for i, bg_line in enumerate(background.art):
            y = 2 + i
            if y >= height - 6:
                break
            console.print(0, y, bg_line[:width])

    # Portrait area
    portrait = portrait_l or portrait_r
    if portrait is not None:
        px = 2 if portrait_l else width - portrait.width - 2
        py = 2
        for dy in range(min(portrait.height, height - 6 - py)):
            y = py + dy
            if y >= height - 6:
                break
            line_art = portrait.art[dy] if dy < len(portrait.art) else ""
            console.print(px, y, line_art)

    # Speaker name
    speaker_y = 3
    speaker_text = f"◆ {speaker}"
    console.print(2, speaker_y, speaker_text)

    # Dialogue text (typing effect)
    text_y = 5
    max_text_width = width - 4
    wrapped = _wrap_text(typed_text, max_text_width)
    for i, text_line in enumerate(wrapped):
        y = text_y + i
        if y >= height - 4:
            break
        console.print(2, y, text_line)

    # Progress
    progress_y = height - 2
    progress = f" [{state.dialogue_index + 1}/{len(scene.dialogue)}]"
    console.print(0, progress_y, progress)


def _wrap_text(text: str, width: int) -> list[str]:
    """Simple word-wrap."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines

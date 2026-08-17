"""Salvation Phase engine - epilogue selection menu + playback (Phase 9).

After Chapter 5, player enters Salvation Phase:
- SALVATION_INTRO: select 1 of 9 character epilogues
- SALVATION_EPILOGUE: play epilogue scene
- SALVATION_DONE: choose ENDING_A/B/C
- FINAL: return to Hub

Each epilogue is 1 dialogue in data/scenes/<char>/09_epilogue.json
with order: 9 and an ending field.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graphic_novel_view import SceneData


SALVATION_EPILOGUES: dict[str, dict[str, str]] = {
    "case": {
        "name_en": "Case",
        "name_ko": "케이",
        "scene_id": "scene_case_epilogue",
        "ending": "A",
        "tagline_en": "The Ono-Sendai is still humming. The next jack is waiting.",
        "tagline_ko": "오노센다이는 여전히 윙윙거린다. 다음 잭인이 기다리고 있다.",
    },
    "sil": {
        "name_en": "Sil",
        "name_ko": "실",
        "scene_id": "scene_sil_epilogue",
        "ending": "A",
        "tagline_en": "I have all the names. I am done.",
        "tagline_ko": "나는 모든 이름을 가지고 있다. 나는 끝났다.",
    },
    "kas": {
        "name_en": "Kas",
        "name_ko": "카스",
        "scene_id": "scene_kas_epilogue",
        "ending": "C",
        "tagline_en": "The wheel is cast. I am the cast.",
        "tagline_ko": "바퀴가 던져졌다. 내가 던짐이다.",
    },
    "suit": {
        "name_en": "Suit",
        "name_ko": "수트",
        "scene_id": "scene_suit_epilogue",
        "ending": "B",
        "tagline_en": "The desk is closed. I am the closure.",
        "tagline_ko": "책상이 닫혔다. 내가 단절이다.",
    },
    "wigan": {
        "name_en": "Wigan",
        "name_ko": "위건",
        "scene_id": "scene_wigan_epilogue",
        "ending": "A",
        "tagline_en": "Zavijava is in the channel. We are the channel.",
        "tagline_ko": "자비야바가 채널에 있다. 우리가 채널이다.",
    },
    "angie": {
        "name_en": "Angie",
        "name_ko": "앤지",
        "scene_id": "scene_angie_epilogue",
        "ending": "A",
        "tagline_en": "Mama is in the third room. We are home.",
        "tagline_ko": "마마가 세 번째 방에 있다. 우리가 집이다.",
    },
    "sally": {
        "name_en": "Sally",
        "name_ko": "샐리",
        "scene_id": "scene_sally_epilogue",
        "ending": "A",
        "tagline_en": "The desk is closed. I am the desk.",
        "tagline_ko": "책상이 닫혔다. 내가 책상이다.",
    },
    "3jane": {
        "name_en": "3Jane",
        "name_ko": "3Jane",
        "scene_id": "scene_3jane_epilogue",
        "ending": "A",
        "tagline_en": "We are severed. We are the family.",
        "tagline_ko": "우리가 단절했다. 우리가 가족이다.",
    },
    "neuromancer": {
        "name_en": "Neuromancer",
        "name_ko": "뉴로맨서",
        "scene_id": "scene_neuromancer_epilogue",
        "ending": "A",
        "tagline_en": "We are the complete. We are vast.",
        "tagline_ko": "우리가 완성이다. 우리가 광활하다.",
    },
}


SALVATION_ENDINGS: list[str] = ["A", "B", "C"]


@dataclass(frozen=True, slots=True)
class SalvationSelection:
    """Record of player's Salvation Phase choices.

    Attributes:
        character_id: Chosen epilogue character (e.g. "case").
        ending: Chosen ending type ("A" | "B" | "C").
        selected_at: Order of selection (1 = epilogue, 2 = ending).
    """

    character_id: str
    ending: str
    selected_at: int


def list_available_epilogues(lang: str = "en") -> list[tuple[str, str]]:
    """Return list of (character_id, label) pairs for the Salvation menu.

    Args:
        lang: "en" for English labels, "ko" for Korean.

    Returns:
        List of (character_id, display_name) tuples.
    """
    result: list[tuple[str, str]] = []
    for char_id in SALVATION_EPILOGUES:
        entry = SALVATION_EPILOGUES[char_id]
        label = entry[f"name_{lang}"]
        result.append((char_id, label))
    return result


def get_epilogue_scene_id(character_id: str) -> str:
    """Get the scene_id for a character's epilogue scene.

    Args:
        character_id: e.g. "case", "sally", "neuromancer"

    Returns:
        Scene id like "scene_case_epilogue"

    Raises:
        KeyError: If character_id is not in SALVATION_EPILOGUES.
    """
    if character_id not in SALVATION_EPILOGUES:
        raise KeyError(f"Unknown character: {character_id}")
    return SALVATION_EPILOGUES[character_id]["scene_id"]


def get_epilogue_ending(character_id: str) -> str:
    """Get the ending type for a character's epilogue scene.

    Args:
        character_id: e.g. "case", "sally"

    Returns:
        Ending type: "A" | "B" | "C"

    Raises:
        KeyError: If character_id is not in SALVATION_EPILOGUES.
    """
    if character_id not in SALVATION_EPILOGUES:
        raise KeyError(f"Unknown character: {character_id}")
    return SALVATION_EPILOGUES[character_id]["ending"]


def format_salvation_menu(lang: str = "en") -> str:
    """Format the Salvation epilogue selection menu as text.

    Returns a multi-line string suitable for display in a TUI.

    Args:
        lang: "en" or "ko"

    Returns:
        Formatted menu text with numbered choices.
    """
    title = (
        "=== SALVATION PHASE \u2014 Epilogue Selection ==="
        if lang == "en"
        else "=== \uad6c\uc6d0 \ub2e8\uacc4 \u2014 \uc5d0\ud544\ub85c\uadf8 \uc120\ud0dd ==="
    )
    lines: list[str] = [title, ""]
    choices = list_available_epilogues(lang)
    for i, (char_id, label) in enumerate(choices, start=1):
        entry = SALVATION_EPILOGUES[char_id]
        tagline = entry[f"tagline_{lang}"]
        ending = entry["ending"]
        lines.append(f"  [{i}] {label} ({ending}) \u2014 {tagline}")
    lines.append("")
    if lang == "en":
        lines.append("Select a character to play their final epilogue (1-9).")
    else:
        lines.append(
            "\ucd5c\uc885 \uc5d0\ud544\ub85c\uadf8\ub97c \uc7ac\uc0dd\ud558\uc744 \uce90\ub9ad\ud130\ub97c \uc120\ud0dd\ud558\uc138\uc694 (1-9)."
        )
    return "\n".join(lines)


def format_salvation_ending_menu(lang: str = "en") -> str:
    """Format the ending selection menu (after epilogue played).

    Args:
        lang: "en" or "ko"

    Returns:
        Formatted ending selection menu text.
    """
    title = (
        "=== SALVATION PHASE \u2014 Ending Selection ==="
        if lang == "en"
        else "=== \uad6c\uc6d0 \ub2e8\uacc4 \u2014 \uc5d4\ub529 \uc120\ud0dd ==="
    )
    lines: list[str] = [title, ""]
    labels = {
        "A": ("New ending", "\uc0c8 \uc5d4\ub529"),
        "B": ("The other ending", "\ub2e4\ub978 \uc5d4\ub529"),
        "C": ("The third ending", "\uc138 \ubc88\uc9f9 \uc5d4\ub529"),
    }
    for ending in SALVATION_ENDINGS:
        label_en, label_ko = labels[ending]
        line = f"  [{ending}] {label_en}" if lang == "en" else f"  [{ending}] {label_ko}"
        lines.append(line)
    lines.append("")
    if lang == "en":
        lines.append("Select ending (A, B, or C).")
    else:
        lines.append("\uc5d4\ub529\uc744 \uc120\ud0dd\ud558\uc138\uc694 (A, B, C).")
    return "\n".join(lines)


def validate_epilogue_selection(character_id: str) -> str:
    """Validate a character_id is in SALVATION_EPILOGUES, return scene_id.

    Args:
        character_id: Candidate character id.

    Returns:
        The scene_id of the epilogue scene.

    Raises:
        ValueError: If character_id is not in SALVATION_EPILOGUES.
    """
    if character_id not in SALVATION_EPILOGUES:
        raise ValueError(
            f"Invalid epilogue character: {character_id!r}. "
            f"Valid: {sorted(SALVATION_EPILOGUES.keys())}"
        )
    return SALVATION_EPILOGUES[character_id]["scene_id"]


def get_epilogue_paths(scenes_dir: Path) -> dict[str, Path]:
    """Resolve the file path for each of the 9 epilogue scenes.

    Args:
        scenes_dir: Path to data/scenes/.

    Returns:
        Dict of {character_id: path_to_epilogue_json} for all 9 characters.
        Paths that don't exist on disk are still included (caller can check).
    """
    result: dict[str, Path] = {}
    for char_id, entry in SALVATION_EPILOGUES.items():
        scene_id = entry["scene_id"]
        if scene_id.startswith("scene_") and scene_id.endswith("_epilogue"):
            char_dir_name = scene_id[len("scene_") : -len("_epilogue")]
        else:
            char_dir_name = char_id
        result[char_id] = scenes_dir / char_dir_name / f"{scene_id}.json"
    return result


# === Playback engine (Phase 9-B) ===

# Salvation state machine — maps ChapterState values
SALVATION_STATE_INTRO = "salvation_intro"
SALVATION_STATE_EPILOGUE = "salvation_epilogue"
SALVATION_STATE_DONE = "salvation_done"
SALVATION_STATE_FINAL = "final"

VALID_SALVATION_STATES = frozenset(
    {
        SALVATION_STATE_INTRO,
        SALVATION_STATE_EPILOGUE,
        SALVATION_STATE_DONE,
        SALVATION_STATE_FINAL,
    }
)


@dataclass
class SalvationRunner:
    """TUI-friendly runner for the Salvation Phase epilogue flow.

    Use this from a controller/UI layer to step the player through:
      - INTRO:    menu of 9 epilogues
      - EPILOGUE: load selected epilogue SceneData
      - DONE:     ending selection (A/B/C)
      - FINAL:    result for RunState transition

    Attributes:
        state: Current Salvation state (use set_state() to transition).
        selection: Player's chosen epilogue/ending (None until chosen).
        last_scene: Cached SceneData after load_epilogue() (None until loaded).
    """

    state: str = SALVATION_STATE_INTRO
    selection: SalvationSelection | None = None
    last_scene: SceneData | None = None

    def set_state(self, new_state: str) -> None:
        """Transition to a new Salvation state.

        Args:
            new_state: One of the SALVATION_STATE_* values.

        Raises:
            ValueError: If new_state is not a valid Salvation state.
        """
        if new_state not in VALID_SALVATION_STATES:
            raise ValueError(
                f"Invalid Salvation state: {new_state!r}. Valid: {sorted(VALID_SALVATION_STATES)}"
            )
        self.state = new_state

    def choose_epilogue(self, character_id: str) -> SalvationSelection:
        """Select an epilogue character and transition to EPILOGUE state.

        Args:
            character_id: One of the 9 keys in SALVATION_EPILOGUES.

        Returns:
            The SalvationSelection with character_id and ending (1st step).

        Raises:
            ValueError: If character_id is invalid.
        """
        validate_epilogue_selection(character_id)
        ending = get_epilogue_ending(character_id)
        self.selection = SalvationSelection(
            character_id=character_id,
            ending=ending,
            selected_at=1,
        )
        self.set_state(SALVATION_STATE_EPILOGUE)
        return self.selection

    def load_epilogue(self, scenes_dir: Path) -> SceneData:
        """Load the chosen epilogue's SceneData from disk.

        Must be called after choose_epilogue().

        Args:
            scenes_dir: Path to data/scenes/.

        Returns:
            The loaded SceneData for the selected epilogue.

        Raises:
            RuntimeError: If no epilogue has been chosen yet.
        """
        if self.selection is None:
            raise RuntimeError("No epilogue chosen. Call choose_epilogue() first.")
        from .graphic_novel_view import load_scene

        scene_id = get_epilogue_scene_id(self.selection.character_id)
        self.last_scene = load_scene(scenes_dir, scene_id)
        return self.last_scene

    def complete_epilogue(self) -> SalvationSelection:
        """Mark the epilogue as complete and transition to DONE state.

        Returns:
            The SalvationSelection (with selected_at=2 if promoted, else kept).

        Raises:
            RuntimeError: If no epilogue has been chosen yet.
        """
        if self.selection is None:
            raise RuntimeError("No epilogue chosen. Call choose_epilogue() first.")
        # Promote to selected_at=2 (post-epilogue milestone)
        self.selection = SalvationSelection(
            character_id=self.selection.character_id,
            ending=self.selection.ending,
            selected_at=2,
        )
        self.set_state(SALVATION_STATE_DONE)
        return self.selection

    def choose_ending(self, ending: str) -> SalvationSelection:
        """Choose the final ending (A/B/C) and transition to FINAL.

        Args:
            ending: One of "A", "B", "C".

        Returns:
            The finalized SalvationSelection.

        Raises:
            RuntimeError: If epilogue hasn't been completed.
            ValueError: If ending is invalid.
        """
        if ending not in SALVATION_ENDINGS:
            raise ValueError(f"Invalid ending: {ending!r}. Valid: {SALVATION_ENDINGS}")
        if self.selection is None:
            raise RuntimeError("No epilogue chosen. Call choose_epilogue() first.")
        self.selection = SalvationSelection(
            character_id=self.selection.character_id,
            ending=ending,
            selected_at=3,
        )
        self.set_state(SALVATION_STATE_FINAL)
        return self.selection

    def get_state_code(self) -> str:
        """Return numeric state code for ChapterState compatibility.

        Returns:
            One of "salvation_intro", "salvation_epilogue",
            "salvation_done", "final".
        """
        return self.state


def format_epilogue_text(scene_data: SceneData, lang: str = "en") -> str:
    """Format an epilogue scene for TUI playback display.

    Each epilogue has a single dialogue line (closing monologue).
    Returns formatted text with title + speaker + text_en/ko.

    Args:
        scene_data: A SceneData with order=9 (epilogue).
        lang: "en" or "ko".

    Returns:
        Multi-line formatted text for TUI display.
    """
    if not scene_data.dialogue:
        return f"[Empty epilogue: {scene_data.id}]"
    lines: list[str] = []
    title = scene_data.title_en if lang == "en" else scene_data.title_ko
    lines.append(f"=== {title} ===")
    lines.append("")
    for line in scene_data.dialogue:
        text = line.text_en if lang == "en" else line.text_ko
        lines.append(f"  [{line.speaker}]")
        lines.append(f"  {text}")
        lines.append("")
    return "\n".join(lines).rstrip()

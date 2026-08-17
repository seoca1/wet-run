#!/usr/bin/env uv run python
"""Arc Chapter Demo — plays through arc.json phases with beats.

Demonstrates the Story → Stage → Event pipeline:
    expanded.json (story beats)
        ↓
    chapter_flow.json (phases)
        ↓
    arc.json (playable events with beats)
        ↓
    Demo playback

Usage:
    uv run python scripts/play_arc_chapter.py
    uv run python scripts/play_arc_chapter.py --character case --chapter 1 --lang en
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.chapter_cutscene import ArcData, BeatData, PhaseData, load_arc

BEAT_TYPE_COLORS = {
    "interior_monologue": "\033[33m",  # Yellow
    "action": "\033[32m",  # Green
    "dialogue": "\033[36m",  # Cyan
    "combat": "\033[31m",  # Red
    "default": "\033[0m",  # Reset
}
COLOR_RESET = "\033[0m"


def render_beat_console(
    beat: BeatData,
    typed_chars: int,
    is_ko: bool,
    phase_num: int,
    total_phases: int,
    beat_num: int,
    total_beats: int,
) -> None:
    """Render a single beat with typing effect (console output)."""
    text = beat.text_ko if is_ko else beat.text_en
    beat_type = beat.type

    # Clear screen
    print("\033[2J\033[H", end="")

    # Header
    color = BEAT_TYPE_COLORS.get(beat_type, BEAT_TYPE_COLORS["default"])
    print(f"{color}═" * 70)
    print(
        f"║ CHAPTER {phase_num}/{total_phases} — PHASE: {beat.phase_id if hasattr(beat, 'phase_id') else 'N/A'}"
    )
    print(f"║ Beat {beat_num}/{total_beats} [{beat_type}]")
    print(f"{COLOR_RESET}{color}═" * 70 + COLOR_RESET)

    # Typed text
    display_text = text[:typed_chars]
    print(f"\n{display_text}")

    # Progress indicator
    progress = typed_chars / max(len(text), 1)
    bar_len = 50
    filled = int(bar_len * progress)
    bar = "█" * filled + "░" * (bar_len - filled)

    print(f"\n{color}[{bar}] {progress * 100:.1f}%{COLOR_RESET}")


def tick_beat(
    text: str,
    elapsed_ms: float,
    typed_chars: int,
    char_delay_ms: float = 30,
) -> int:
    """Advance typing animation."""
    if char_delay_ms <= 0:
        return len(text)
    new_count = int(elapsed_ms / char_delay_ms)
    return min(new_count, len(text))


def play_phase(
    phase: PhaseData,
    phase_num: int,
    total_phases: int,
    is_ko: bool,
    char_delay_ms: float = 25,
) -> None:
    """Play through a single phase's beats."""
    print(f"\n\033[1;36m>>> PHASE {phase_num}: {phase.title_en} ({phase.title_ko})\033[0m")
    print(f"\033[90m    {phase.description_en[:80]}...\033[0m")

    if not phase.beats:
        print("\033[90m    [No beats in this phase]\033[0m")
        time.sleep(1)
        return

    for i, beat in enumerate(phase.beats, 1):
        print(f"\n\033[90m    --- Beat {i}/{len(phase.beats)} ---\033[0m")

        text = beat.text_ko if is_ko else beat.text_en
        typed_chars = 0
        start_time = time.time()

        # Typing effect loop
        while typed_chars < len(text):
            elapsed = (time.time() - start_time) * 1000
            typed_chars = tick_beat(text, elapsed, typed_chars, char_delay_ms)
            render_beat_console(
                beat, typed_chars, is_ko, phase_num, total_phases, i, len(phase.beats)
            )
            time.sleep(0.05)

        # Final display (full text)
        print("\n\033[90m    Press Enter to continue...\033[0m", end="", flush=True)
        input()


def play_chapter(
    arc: ArcData,
    chapter_num: int,
    is_ko: bool,
    char_delay_ms: float = 25,
) -> None:
    """Play through a single chapter's phases."""
    if chapter_num < 1 or chapter_num > len(arc.chapters):
        print(f"Error: Chapter {chapter_num} not found (1-{len(arc.chapters)})")
        return

    chapter = arc.chapters[chapter_num - 1]
    print(f"\n\033[1;35m{'=' * 70}\033[0m")
    print(f"\033[1;35mCHAPTER {chapter_num}: {chapter.title_en}\033[0m")
    print(f"\033[1;35m{chapter.title_ko}\033[0m")
    print(f"\033[1;35m{'=' * 70}\033[0m")
    print(f"\n\033[90m{chapter.description_en[:150]}...\033[0m")
    print("\n\033[90mPress Enter to start...\033[0m", end="", flush=True)
    input()

    for i, phase in enumerate(chapter.phases, 1):
        play_phase(phase, i, len(chapter.phases), is_ko, char_delay_ms)

        # Check for combat
        if phase.combat:
            print("\n\033[1;31m*** COMBAT ENCOUNTER ***\033[0m")
            print(f"    Enemy: {phase.combat.enemy_type}")
            print(f"    Difficulty: {phase.combat.difficulty}")
            print(f"    Outcome: {phase.combat.outcome}")
            print("\033[90mPress Enter to continue...\033[0m", end="", flush=True)
            input()

        # Check for gain/loss
        if phase.gain:
            print(f"\n\033[1;32m+ {phase.gain}\033[0m")
        if phase.loss:
            print(f"\n\033[1;31m- {phase.loss}\033[0m")


def play_arc(
    arc: ArcData,
    is_ko: bool,
    char_delay_ms: float = 25,
) -> None:
    """Play through all chapters in an arc."""
    print(f"\n\033[1;33m{'=' * 70}\033[0m")
    print(f"\033[1;33mARC: {arc.title_en}\033[0m")
    print(f"\033[1;33m{arc.title_ko}\033[0m")
    print(f"\033[1;33m{'=' * 70}\033[0m")
    print(f"\n\033[90m{arc.description_en[:150]}...\033[0m")
    print(f"\n\033[90mTotal Chapters: {len(arc.chapters)}\033[0m")
    print("\n\033[90mPress Enter to start Chapter 1...\033[0m", end="", flush=True)
    input()

    for i in range(1, len(arc.chapters) + 1):
        play_chapter(arc, i, is_ko, char_delay_ms)


def main() -> None:
    parser = argparse.ArgumentParser(description="Play through arc chapter with phases and beats")
    parser.add_argument(
        "--character",
        "-c",
        choices=["case", "sil", "kas"],
        default="case",
        help="Character arc to play",
    )
    parser.add_argument(
        "--chapter",
        "-ch",
        type=int,
        default=0,
        help="Specific chapter to play (1-5, 0=all)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=["en", "ko"],
        default="en",
        help="Language",
    )
    parser.add_argument(
        "--char-delay",
        "-d",
        type=float,
        default=25,
        help="Typing delay in ms (default 25)",
    )
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    arc_path = data_dir / "story" / "arcs" / f"{args.character}_arc.json"

    print(f"\033[1;36mLoading arc from: {arc_path}\033[0m")
    arc = load_arc(arc_path)

    is_ko = args.lang == "ko"

    if args.chapter == 0:
        play_arc(arc, is_ko, args.char_delay)
    else:
        play_chapter(arc, args.chapter, is_ko, args.char_delay)

    print("\n\033[1;32m=== DEMO COMPLETE ===\033[0m")


if __name__ == "__main__":
    main()

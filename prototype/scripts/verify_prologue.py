"""Headless validation demo of the prologue and briefing scenes.

Runs through PROLOGUE_SCENE and BRIEFING_FINN_SCENE in text mode,
showing:
- Each story line with typing effect simulation
- Which ASCII portrait is shown for each line/scene
- Bilingual EN + KO text
- Speaker labels and effects
- Scene transitions

Use this to validate the prologue and briefing look correct before
running the GUI version. No tcod window required.

Usage:
  uv run python scripts/verify_prologue.py
  uv run python scripts/verify_prologue.py --scene prologue
  uv run python scripts/verify_prologue.py --scene briefing
  uv run python scripts/verify_prologue.py --speed fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.cinematic_art import (
    ArtStyle,
    get_scene_art,
    resolve_line_art,
)
from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    StoryLine,
    StoryScene,
    TextSpeed,
)

# ANSI styling
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_YELLOW = "\033[93m"
ANSI_MAGENTA = "\033[95m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_GRAY = "\033[90m"
ANSI_WHITE = "\033[97m"


STYLE_COLOR = {
    ArtStyle.NEON: ANSI_MAGENTA,
    ArtStyle.GHOST: ANSI_CYAN,
    ArtStyle.GLITCH: ANSI_RED,
    ArtStyle.MATRIX: ANSI_GREEN,
    ArtStyle.SHADOW: ANSI_GRAY,
    ArtStyle.STATIC: ANSI_WHITE,
    ArtStyle.FIRE: ANSI_RED,
}


def _print_header(title: str) -> None:
    """Print a section header."""
    print()
    print(f"{ANSI_BOLD}{'=' * 70}{ANSI_RESET}")
    print(f"{ANSI_BOLD}  {title}{ANSI_RESET}")
    print(f"{ANSI_BOLD}{'=' * 70}{ANSI_RESET}")
    print()


def _print_art_preview(art, key: str) -> None:
    """Print ASCII art preview with style indicator."""
    if art is None:
        print(f"{ANSI_DIM}(no art){ANSI_RESET}")
        return
    color = STYLE_COLOR.get(art.style, ANSI_WHITE)
    print(f"{ANSI_DIM}── {key} ({art.style.value}, fg={art.fg}) ──{ANSI_RESET}")
    for line in art.lines:
        print(f"{color}{line}{ANSI_RESET}")
    print(f"{ANSI_DIM}{'─' * 50}{ANSI_RESET}")


def _typing_simulate(text: str, speed: TextSpeed, line: StoryLine) -> None:
    """Simulate typing effect by printing char-by-char with delays."""
    # Speed → chars per second
    if speed is TextSpeed.INSTANT:
        chars_per_sec = 1000
    elif speed is TextSpeed.FAST:
        chars_per_sec = 60
    elif speed is TextSpeed.SLOW:
        chars_per_sec = 15
    else:
        chars_per_sec = 30

    interval = 1.0 / chars_per_sec
    if speed is TextSpeed.INSTANT:
        # Don't actually wait for instant
        print(f"{ANSI_WHITE}{text}{ANSI_RESET}")
        return

    # Print chars with optional glitch effect
    for i, ch in enumerate(text):
        # Apply glitch occasionally
        if line.effect.value == "glitch" and i > 0 and i % 5 == 0:
            glitch_chars = "█▓▒░▄▀■"
            sys.stdout.write(f"{ANSI_RED}{glitch_chars[i % len(glitch_chars)]}{ANSI_RESET}")
            sys.stdout.flush()
            time.sleep(interval * 2)
            # Backspace + correct char
            sys.stdout.write("\b")
            sys.stdout.write(f"{ANSI_WHITE}{ch}{ANSI_RESET}")
        else:
            sys.stdout.write(f"{ANSI_WHITE}{ch}{ANSI_RESET}")
        sys.stdout.flush()
        time.sleep(interval)
    print()


def _verify_line(
    line: StoryLine,
    line_index: int,
    total_lines: int,
    scene: StoryScene,
    speed: TextSpeed,
    delay: float,
) -> None:
    """Verify and display a single story line."""
    # Header for this line
    effect_str = f" [{line.effect.value}]" if line.effect.value != "none" else ""
    speed_str = f" ({speed.value})"
    print(f"{ANSI_DIM}[line {line_index + 1}/{total_lines}{speed_str}{effect_str}]{ANSI_RESET}")

    # Speaker + portrait
    if line.speaker:
        art = resolve_line_art(line.portrait, scene.id)
        if art is not None:
            # Line art override (art:key) or scene art
            print(
                f"{ANSI_CYAN}>> {line.speaker.upper()}:{ANSI_RESET} "
                f"{ANSI_DIM}[art: {art.style.value}, "
                f"{len(art.lines)} lines, "
                f"{art.width} chars wide]{ANSI_RESET}"
            )
        else:
            # Legacy single-glyph portrait
            print(f"{ANSI_CYAN}{line.portrait} {line.speaker.upper()}:{ANSI_RESET}")
    elif line.portrait:
        art = resolve_line_art(line.portrait, scene.id)
        if art is not None:
            print(f"{ANSI_DIM}[narrator art: {art.style.value}]{ANSI_RESET}")

    # English text with typing effect
    _typing_simulate(line.text_en, speed, line)

    # Korean subtitle
    if line.text_ko:
        time.sleep(0.1)
        print(f"{ANSI_YELLOW}  {line.text_ko}{ANSI_RESET}")

    print()
    time.sleep(delay)


def _verify_scene(scene: StoryScene, speed: TextSpeed, delay: float) -> None:
    """Verify a story scene end-to-end."""
    _print_header(f"SCENE: {scene.id}")
    print(f"{ANSI_DIM}Title (EN):{ANSI_RESET} {scene.title_en}")
    print(f"{ANSI_DIM}Title (KO):{ANSI_RESET} {scene.title_ko}")
    print(f"{ANSI_DIM}Lines:    {ANSI_RESET} {len(scene.lines)}")
    print(f"{ANSI_DIM}Next:     {ANSI_RESET} {scene.next_scene or '(end)'}")

    # Show scene art preview
    print()
    print(f"{ANSI_BOLD}Scene Art (shown when no line override):{ANSI_RESET}")
    scene_art = get_scene_art(scene.id)
    _print_art_preview(scene_art, scene.id)

    # Verify each line
    print(f"{ANSI_BOLD}Lines:{ANSI_RESET}")
    for i, line in enumerate(scene.lines):
        _verify_line(line, i, len(scene.lines), scene, speed, delay)

    # Pause between scenes
    print(f"{ANSI_DIM}[scene end]{ANSI_RESET}")
    time.sleep(0.5)


def _verify_transitions() -> None:
    """Verify scene transitions are set up correctly."""
    _print_header("SCENE TRANSITIONS")

    scenes = [PROLOGUE_SCENE, BRIEFING_FINN_SCENE]

    for scene in scenes:
        next_label = scene.next_scene or "(none - end of cinematic)"
        print(f"  {ANSI_CYAN}{scene.id:35s}{ANSI_RESET} → {next_label}")

    print()
    print(f"{ANSI_DIM}Flow: PROLOGUE → BRIEFING → (exit to Hub){ANSI_RESET}")


def _verify_bilingual() -> None:
    """Verify all lines have Korean translations."""
    _print_header("BILINGUAL COVERAGE")

    for scene in [PROLOGUE_SCENE, BRIEFING_FINN_SCENE]:
        total = len(scene.lines)
        with_ko = sum(1 for line in scene.lines if line.text_ko)
        with_speaker = sum(1 for line in scene.lines if line.speaker)
        with_portrait = sum(1 for line in scene.lines if line.portrait)

        print(f"  {ANSI_CYAN}{scene.id}{ANSI_RESET}")
        print(f"    Total lines:        {total}")
        print(f"    With KO:            {with_ko}/{total} ({with_ko * 100 // total}%)")
        print(f"    With speaker:       {with_speaker}/{total}")
        print(f"    With portrait hint: {with_portrait}/{total}")
        print()


def _verify_art_coverage() -> None:
    """Verify which art is used for each scene."""
    _print_header("ART COVERAGE")

    for scene in [PROLOGUE_SCENE, BRIEFING_FINN_SCENE]:
        scene_art = get_scene_art(scene.id)
        print(f"  {ANSI_CYAN}{scene.id}{ANSI_RESET}")
        print(f"    Default art: {scene_art.style.value} ({len(scene_art.lines)} lines)")
        print("    Sample line arts:")
        for i, line in enumerate(scene.lines):
            if line.portrait:
                art = resolve_line_art(line.portrait, scene.id)
                if art is not None:
                    label = f"line {i + 1}: {art.style.value}"
                    if line.speaker:
                        label += f" ({line.speaker})"
                    print(f"      {label}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless prologue verification")
    parser.add_argument(
        "--scene",
        choices=["prologue", "briefing", "transitions", "coverage", "all"],
        default="all",
        help="What to verify (default: all)",
    )
    parser.add_argument(
        "--speed",
        choices=["instant", "fast", "normal", "slow"],
        default="fast",
        help="Typing speed for demo (default: fast)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Delay between lines in seconds (default: 0.3)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors",
    )
    args = parser.parse_args()

    if args.no_color:
        # Disable all ANSI
        for attr in dir():
            if attr.startswith("ANSI_") and attr != "ANSI_RESET":
                globals()[attr] = ""

    speed_map = {
        "instant": TextSpeed.INSTANT,
        "fast": TextSpeed.FAST,
        "normal": TextSpeed.NORMAL,
        "slow": TextSpeed.SLOW,
    }
    speed = speed_map[args.speed]

    _print_header("PROLOGUE VERIFICATION DEMO")
    print(f"{ANSI_DIM}This demo runs through the prologue and briefing scenes{ANSI_RESET}")
    print(f"{ANSI_DIM}to verify text, art mapping, and bilingual coverage.{ANSI_RESET}")
    print(
        f"{ANSI_DIM}Speed: {args.speed}  |  Delay: {args.delay}s  |  "
        f"Color: {'off' if args.no_color else 'on'}{ANSI_RESET}"
    )

    if args.scene in ("prologue", "all"):
        _verify_scene(PROLOGUE_SCENE, speed, args.delay)
    if args.scene in ("briefing", "all"):
        _verify_scene(BRIEFING_FINN_SCENE, speed, args.delay)
    if args.scene in ("transitions", "all"):
        _verify_transitions()
    if args.scene in ("coverage", "all"):
        _verify_bilingual()
        _verify_art_coverage()

    _print_header("VERIFICATION COMPLETE")
    print(f"{ANSI_GREEN}All scenes rendered successfully.{ANSI_RESET}")
    print(f"{ANSI_DIM}Run the GUI demo to see the actual rendered output:{ANSI_RESET}")
    print(f"{ANSI_DIM}  make run  (or)  make prologue{ANSI_RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

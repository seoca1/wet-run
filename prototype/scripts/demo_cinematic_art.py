"""Headless demo of the cinematic ASCII art system.

Prints each portrait with its color/style and shows what the prologue
would look like. Use this to verify the art looks good before running
the GUI demo.

Usage:
  uv run python scripts/demo_cinematic_art.py
  uv run python scripts/demo_cinematic_art.py --character finn
  uv run python scripts/demo_cinematic_art.py --list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.cinematic_art import (
    ARMITAGE,
    CASE,
    CHIBA_CITY,
    CYBERSPACE,
    DIXIE_FLATLINE,
    GLITCH_BURST,
    MATRIX_RAIN,
    MOLLY_MILLIONS,
    PORTRAITS,
    SCENE_ART,
    SENSE_NET,
    THE_FINN,
    get_scene_art,
)

# ANSI color codes for terminal display
ANSI_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",
    "reset": "\033[0m",
}


def color_for_rgb(rgb: tuple[int, int, int]) -> str:
    """Map RGB to closest ANSI color."""
    r, g, b = rgb
    # Simple nearest-color heuristic
    if r > 200 and g > 200 and b > 200:
        return ANSI_COLORS["white"]
    if r > 200 and g < 100 and b > 150:
        return ANSI_COLORS["magenta"]
    if r > 200 and g < 100 and b < 100:
        return ANSI_COLORS["red"]
    if r < 100 and g > 200 and b < 100:
        return ANSI_COLORS["green"]
    if r < 100 and g > 200 and b > 200:
        return ANSI_COLORS["cyan"]
    if r < 100 and g < 100 and b > 200:
        return ANSI_COLORS["blue"]
    if r > 200 and g > 200 and b < 100:
        return ANSI_COLORS["yellow"]
    return ANSI_COLORS["gray"]


def render_ansi(art) -> None:
    """Render ASCII art to terminal with ANSI colors."""
    color = color_for_rgb(art.fg)
    print(f"{color}Style: {art.style.value}  FG: {art.fg}{ANSI_COLORS['reset']}")
    for line in art.lines:
        print(f"{color}{line}{ANSI_COLORS['reset']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Cinematic ASCII art demo")
    parser.add_argument(
        "--character",
        choices=[
            "finn",
            "dixie",
            "molly",
            "armitage",
            "case",
            "chiba",
            "cyberspace",
            "matrix_rain",
            "sense_net",
            "glitch",
        ],
        help="Show one specific character/location",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available art",
    )
    parser.add_argument(
        "--scene",
        help="Show art for a specific scene (e.g. prologue_sprawl, briefing_finn_first_jack)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  CINEMATIC ASCII ART DEMO")
    print("  Gibson-style cyberpunk portraits for the prologue and story scenes")
    print("=" * 70)
    print()

    if args.list:
        print(f"Available art ({len(PORTRAITS)}):")
        for key in sorted(PORTRAITS.keys()):
            print(f"  - {key}")
        print()
        print(f"Scene art mapping ({len(SCENE_ART)}):")
        for scene_id, art_key in sorted(SCENE_ART.items()):
            print(f"  - {scene_id} → {art_key}")
        return 0

    if args.scene:
        art = get_scene_art(args.scene)
        print(f"Scene: {args.scene}")
        render_ansi(art)
        return 0

    if args.character:
        key_map = {
            "finn": "finn",
            "dixie": "dixie",
            "molly": "molly",
            "armitage": "armitage",
            "case": "case",
            "chiba": "chiba",
            "cyberspace": "cyberspace",
            "matrix_rain": "matrix_rain",
            "sense_net": "sense_net",
            "glitch": "glitch",
        }
        art = PORTRAITS.get(key_map[args.character])
        if art is None:
            print(f"ERROR: Art '{args.character}' not found")
            return 1
        print(f"Character: {args.character}")
        render_ansi(art)
        return 0

    # Default: show all major characters
    print("--- Major Characters ---\n")
    render_ansi(THE_FINN)
    render_ansi(DIXIE_FLATLINE)
    render_ansi(ARMITAGE)
    render_ansi(MOLLY_MILLIONS)
    render_ansi(CASE)

    print("--- Locations ---\n")
    render_ansi(CHIBA_CITY)
    render_ansi(CYBERSPACE)
    render_ansi(SENSE_NET)
    render_ansi(MATRIX_RAIN)
    render_ansi(GLITCH_BURST)

    print("=" * 70)
    print("  Demo complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

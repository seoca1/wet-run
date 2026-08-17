#!/usr/bin/env python3
"""Text-only demo for verification (no tcod, pure terminal output).

Usage:
  uv run python scripts/text_demo.py
  uv run python scripts/text_demo.py --fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    TextSpeed,
)


def main() -> int:
    """Run text-only demo."""
    parser = argparse.ArgumentParser(description="Text-only demo")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast typing (no delays)",
    )
    parser.add_argument(
        "--scene",
        choices=["prologue", "briefing"],
        default="prologue",
        help="Scene to play",
    )
    args = parser.parse_args()

    # Select scene
    if args.scene == "prologue":
        scene = PROLOGUE_SCENE
    elif args.scene == "briefing":
        scene = BRIEFING_FINN_SCENE
    else:
        print(f"Unknown scene: {args.scene}")
        return 1

    print("=" * 80)
    print(f"TEXT DEMO: {scene.title_en}")
    print(f"          {scene.title_ko}")
    print("=" * 80)
    print()

    for i, line in enumerate(scene.lines, 1):
        print(f"[Line {i}/{len(scene.lines)}]")
        print("-" * 80)

        # Speaker
        if line.speaker and line.portrait:
            print(f"{line.portrait} {line.speaker.upper()}:")
            print()

        # English text
        if args.fast:
            print(f"  {line.text_en}")
        else:
            _type_text(line.text_en, line.speed)

        print()

        # Korean subtitle (as comment)
        print(f"  # {line.text_ko}")

        print()
        print("-" * 80)
        print()

        # Pause between lines
        if not args.fast:
            time.sleep(line.pause_ms / 1000.0)

    print("=" * 80)
    print("DEMO FINISHED")
    print("=" * 80)
    return 0


def _type_text(text: str, speed: TextSpeed) -> None:
    """Type text character by character."""
    delay_map = {
        TextSpeed.INSTANT: 0.0,
        TextSpeed.FAST: 0.016,  # 60 chars/sec
        TextSpeed.NORMAL: 0.033,  # 30 chars/sec
        TextSpeed.SLOW: 0.066,  # 15 chars/sec
    }
    delay = delay_map.get(speed, 0.033)

    print("  ", end="", flush=True)
    for char in text:
        print(char, end="", flush=True)
        if delay > 0:
            time.sleep(delay)
    print()


if __name__ == "__main__":
    sys.exit(main())

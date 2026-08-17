#!/usr/bin/env python3
"""Prologue simulator: Play the game's opening cinematic story.

Usage:
  uv run python scripts/prologue.py
  uv run python scripts/prologue.py --scene briefing
  uv run python scripts/prologue.py --speed fast
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tcod.console
import tcod.context
import tcod.tileset

from wet_run.engine import config, story_cinematic
from wet_run.engine.state import AppState, ScreenKind
from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    CinematicState,
)
from wet_run.i18n import Translator


def main() -> int:
    """Run the prologue simulator."""
    parser = argparse.ArgumentParser(description="Prologue simulator")
    parser.add_argument(
        "--scene",
        choices=["prologue", "briefing"],
        default="prologue",
        help="Scene to play (default: prologue)",
    )
    parser.add_argument(
        "--speed",
        choices=["instant", "fast", "normal", "slow"],
        default="normal",
        help="Typing speed override (default: normal)",
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

    # Override typing speed if requested
    if args.speed != "normal":
        from wet_run.engine.story_cinematic import StoryLine, TextSpeed

        speed_map = {
            "instant": TextSpeed.INSTANT,
            "fast": TextSpeed.FAST,
            "slow": TextSpeed.SLOW,
        }
        new_speed = speed_map[args.speed]
        # Rebuild scene with new speed
        new_lines = tuple(
            StoryLine(
                text_en=line.text_en,
                text_ko=line.text_ko,
                speaker=line.speaker,
                portrait=line.portrait,
                effect=line.effect,
                speed=new_speed,
                pause_ms=line.pause_ms,
            )
            for line in scene.lines
        )
        scene = story_cinematic.StoryScene(
            id=scene.id,
            title_en=scene.title_en,
            title_ko=scene.title_ko,
            lines=new_lines,
            next_scene=scene.next_scene,
        )

    # Setup tcod
    if not config.FONT_PATH.exists():
        sys.stderr.write(
            f"ERROR: Font not found at {config.FONT_PATH}\n"
            f"Run: make download-font (in prototype/ directory)\n"
        )
        return 1

    tileset = tcod.tileset.load_tilesheet(
        str(config.FONT_PATH),
        config.FONT_COLUMNS,
        config.FONT_ROWS,
        tcod.tileset.CHARMAP_TCOD,
    )

    t = Translator(config.DEFAULT_LANGUAGE, data_dir=config.DATA_DIR / "i18n")
    state = AppState()
    state.screen = ScreenKind.CINEMATIC
    state.cinematic_state = CinematicState(scene=scene)

    start_time = time.time()

    with tcod.context.new(
        columns=config.SCREEN_WIDTH,
        rows=config.SCREEN_HEIGHT,
        tileset=tileset,
        title=f"{config.SCREEN_TITLE} — Prologue",
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, order="F")

        running = True
        while running:
            elapsed_s = time.time() - start_time
            elapsed_ms = int(elapsed_s * 1000)
            state.demo_elapsed_s = elapsed_s

            # Step cinematic (typing progression)
            if state.cinematic_state is not None:
                story_cinematic.step_cinematic(state.cinematic_state, elapsed_ms)

            # Render
            story_cinematic.render_cinematic(
                root_console, t, state, state.cinematic_state, elapsed_ms
            )
            context.present(root_console)

            # Handle input
            for event in tcod.event.wait(timeout=0.016):  # ~60 FPS
                if not story_cinematic.handle_cinematic_input(event, state, state.cinematic_state):
                    running = False
                    break

                # Check if screen changed (ESC pressed)
                if state.screen is not ScreenKind.CINEMATIC:
                    running = False
                    break

    print(f"\n=== Prologue finished: {scene.id} ===")
    print(f"Total time: {elapsed_s:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

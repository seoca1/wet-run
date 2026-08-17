#!/usr/bin/env python3
"""Test tcod rendering to diagnose font issues.

Usage:
  uv run python scripts/test_tcod.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tcod.console
import tcod.context
import tcod.tileset

from wet_run.engine import config


def main() -> int:
    """Test basic tcod rendering."""
    print(f"Font path: {config.FONT_PATH}")
    print(f"Font exists: {config.FONT_PATH.exists()}")
    print(f"Screen size: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
    print()

    if not config.FONT_PATH.exists():
        print("ERROR: Font file not found!")
        print("Run: make download-font")
        return 1

    # Try to load tileset
    print("Loading tileset...")
    try:
        tileset = tcod.tileset.load_tilesheet(
            str(config.FONT_PATH),
            config.FONT_COLUMNS,
            config.FONT_ROWS,
            tcod.tileset.CHARMAP_TCOD,
        )
        print("✓ Tileset loaded successfully")
        print(f"  Tile size: {tileset.tile_width}x{tileset.tile_height}")
    except Exception as e:
        print(f"✗ Failed to load tileset: {e}")
        return 1

    print()
    print("Opening window... (press ESC or Q to close)")
    print()

    with tcod.context.new(
        columns=config.SCREEN_WIDTH,
        rows=config.SCREEN_HEIGHT,
        tileset=tileset,
        title="TCOD Test - Press ESC to exit",
        vsync=True,
    ) as context:
        console = tcod.console.Console(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, order="F")

        running = True
        while running:
            # Clear
            console.clear(bg=(0, 0, 0))

            # Test: Draw simple ASCII characters
            y = 2
            console.print(x=2, y=y, string="=== TCOD FONT TEST ===", fg=(255, 255, 255))
            y += 2

            # ASCII printable characters
            console.print(x=2, y=y, string="ASCII: ABCDEFGHIJKLMNOPQRSTUVWXYZ", fg=(200, 200, 200))
            y += 1
            console.print(x=2, y=y, string="       abcdefghijklmnopqrstuvwxyz", fg=(200, 200, 200))
            y += 1
            console.print(x=2, y=y, string="       0123456789", fg=(200, 200, 200))
            y += 1
            console.print(
                x=2, y=y, string="       !@#$%^&*()_+-=[]{}|;':\",./<>?", fg=(200, 200, 200)
            )
            y += 2

            # Box drawing characters
            console.print(x=2, y=y, string="Box drawing:", fg=(180, 180, 180))
            y += 1
            console.print(x=2, y=y, string="+-----------+", fg=(0, 255, 255))
            y += 1
            console.print(x=2, y=y, string="| Text box  |", fg=(0, 255, 255))
            y += 1
            console.print(x=2, y=y, string="+-----------+", fg=(0, 255, 255))
            y += 2

            # Unicode box drawing
            console.print(x=2, y=y, string="Unicode box:", fg=(180, 180, 180))
            y += 1
            try:
                console.print(x=2, y=y, string="╔═══════════╗", fg=(0, 255, 0))
                y += 1
                console.print(x=2, y=y, string="║ Unicode   ║", fg=(0, 255, 0))
                y += 1
                console.print(x=2, y=y, string="╚═══════════╝", fg=(0, 255, 0))
            except Exception as e:
                console.print(x=2, y=y, string=f"Error: {str(e)[:40]}", fg=(255, 0, 0))
            y += 2

            # Special characters
            console.print(x=2, y=y, string="Special: ▓▒░▄▀■□▪▫", fg=(255, 255, 0))
            y += 2

            # Test string from game
            console.print(x=2, y=y, string="Game text:", fg=(180, 180, 180))
            y += 1
            console.print(
                x=2, y=y, string="The sky above the port was the color", fg=(255, 255, 255)
            )
            y += 1
            console.print(
                x=2, y=y, string="of television, tuned to a dead channel.", fg=(255, 255, 255)
            )
            y += 2

            # Instructions
            console.print(
                x=2,
                y=config.SCREEN_HEIGHT - 4,
                string="If you can read this text, the font is working.",
                fg=(128, 128, 128),
            )
            console.print(
                x=2,
                y=config.SCREEN_HEIGHT - 2,
                string="Press ESC or Q to exit",
                fg=(128, 128, 128),
            )

            context.present(console)

            # Handle input
            for event in tcod.event.wait():
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
                        running = False
                        break

    print("Test finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

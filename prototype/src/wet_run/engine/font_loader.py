"""Font loader with TTF (Korean-capable) support.

Supports two font modes:
1. Bitmap font (terminal10x10_gs_tc.png) - ASCII only, fast
2. TTF font (AppleGothic, Nanum, etc.) - Unicode + Korean

TTF font is preferred for Korean support.
"""

from __future__ import annotations

import sys

import tcod.tileset

from . import config


def load_font() -> tuple[object, bool]:
    """Load the best available font.

    Returns:
        (tileset, is_ttf) - tileset object and whether it's TTF
    """
    ttf_path = config.find_ttf_font()

    if ttf_path is not None:
        try:
            tileset = tcod.tileset.load_truetype_font(
                str(ttf_path),
                config.TTF_TILE_SIZE,
                config.TTF_TILE_SIZE,
            )
            print(f"[Font] Loaded TTF: {ttf_path}", file=sys.stderr)
            return tileset, True
        except Exception as e:
            print(f"[Font] TTF load failed: {e}, falling back to bitmap", file=sys.stderr)

    # Fallback to bitmap font
    if not config.FONT_PATH.exists():
        raise FileNotFoundError(
            f"No font available. TTF not found, bitmap missing at {config.FONT_PATH}"
        )

    tileset = tcod.tileset.load_tilesheet(
        str(config.FONT_PATH),
        config.FONT_COLUMNS,
        config.FONT_ROWS,
        tcod.tileset.CHARMAP_TCOD,
    )
    print(f"[Font] Loaded bitmap: {config.FONT_PATH}", file=sys.stderr)
    return tileset, False


def is_korean_capable() -> bool:
    """Check if the current font supports Korean characters."""
    ttf_path = config.find_ttf_font()
    return ttf_path is not None

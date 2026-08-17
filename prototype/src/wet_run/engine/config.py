"""Game configuration constants."""

from __future__ import annotations

import os
import platform
from pathlib import Path

# Screen
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
SCREEN_TITLE = "Roguelike Sprawl"

# FPS target
TARGET_FPS = 60

# Font
FONT_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "fonts" / "terminal10x10_gs_tc.png"
)
FONT_COLUMNS = 32
FONT_ROWS = 8

# TTF font (for Korean + Unicode support)
TTF_FONT_PATHS = {
    "darwin": [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleSDGothicNeo.ttc",
        "/Library/Fonts/NanumGothic.ttf",
    ],
    "linux": [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ],
    "win32": [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
    ],
}
TTF_TILE_SIZE = 16

# i18n
DEFAULT_LANGUAGE = "en"
# Options: "en" (English only), "ko" (Korean only), "both" (English + Korean subtitles)
LANGUAGE_MODE = "both"

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def find_ttf_font() -> Path | None:
    """Find an available TTF font for the current platform."""
    system = platform.system().lower()
    paths = TTF_FONT_PATHS.get(system, TTF_FONT_PATHS["linux"])
    for path_str in paths:
        path = Path(path_str)
        if path.exists():
            return path
    # Try environment variable fallback
    if "FONT_PATH" in os.environ:
        env_path = Path(os.environ["FONT_PATH"])
        if env_path.exists():
            return env_path
    return None

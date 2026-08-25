"""Game configuration constants."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ResolutionPreset:
    """A named logical grid resolution (ADR-0198).

    The preset defines columns/rows for the in-game logical coordinate
    system. tcod handles display-fit scaling to the actual window.

    Tier 1 = production (8 named presets). Tier 2 = experimental.
    """

    name: str
    cols: int
    rows: int
    ratio: str
    target_device: str
    tier: int  # 1 = production, 2 = experimental


# Default screen (Classic 80x50 — Steam Deck native). Override via
# AppState.resolution + ResolutionPreset in app.py:_main_inner (ADR-0198).
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
SCREEN_TITLE = "Wet Run"

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
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
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

# Resolution presets (ADR-0198). Default = "classic" (80x50 = Steam Deck native).
# Phone Portrait 40x70 marked Tier 2 experimental.
RESOLUTION_PRESETS: dict[str, ResolutionPreset] = {
    "classic": ResolutionPreset(
        name="classic",
        cols=80,
        rows=50,
        ratio="8:5",
        target_device="Steam Deck 1280x800; legacy desktop",
        tier=1,
    ),
    "compact": ResolutionPreset(
        name="compact",
        cols=60,
        rows=35,
        ratio="12:7",
        target_device="small laptops; iPad mini legacy",
        tier=1,
    ),
    "wide": ResolutionPreset(
        name="wide",
        cols=100,
        rows=55,
        ratio="20:11",
        target_device="1080p desktop; 1600x900",
        tier=1,
    ),
    "ultrawide": ResolutionPreset(
        name="ultrawide",
        cols=120,
        rows=50,
        ratio="12:5",
        target_device="ultrawide monitors",
        tier=1,
    ),
    "tablet_portrait": ResolutionPreset(
        name="tablet_portrait",
        cols=60,
        rows=80,
        ratio="3:4",
        target_device="iPad portrait",
        tier=1,
    ),
    "tablet_landscape": ResolutionPreset(
        name="tablet_landscape",
        cols=90,
        rows=60,
        ratio="3:2",
        target_device="iPad Pro landscape",
        tier=1,
    ),
    "phone_landscape": ResolutionPreset(
        name="phone_landscape",
        cols=80,
        rows=40,
        ratio="2:1",
        target_device="phone landscape",
        tier=1,
    ),
    "auto": ResolutionPreset(
        name="auto",
        cols=0,
        rows=0,
        ratio="varies",
        target_device="device detection — Tier 2",
        tier=2,
    ),
}

# Default resolution name (must key into RESOLUTION_PRESETS).
DEFAULT_RESOLUTION = "classic"


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

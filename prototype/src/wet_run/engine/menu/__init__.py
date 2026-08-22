"""Main menu package (ADR-0110 split).

This sub-package replaces the monolithic ``engine/menu.py`` (891 LOC).
Public symbols are re-exported unchanged so any ``from wet_run.engine.menu import X``
call site continues to work without modification.

Cohesion split:
    main_menu.py — top-level menu (render_menu, handle_menu_input, OPTION_*)
    pre_run.py   — character/deck/ending selection (pre-game flow)
    gn_menu.py   — graphic novel + endings browser + telemetry stats
"""

from .gn_menu import (
    GN_MENU_OPTION_COUNT,
    handle_endings_browser_input,
    handle_graphic_novel_ending_menu_input,
    handle_graphic_novel_input,
    handle_graphic_novel_menu_input,
    handle_save_slot_select_input,
    handle_saved_progress_input,
    handle_telemetry_stats_input,
    render_endings_browser,
    render_telemetry_summary,
)
from .main_menu import (
    MENU_OPTION_COUNT,
    OPTION_CONTINUE,
    OPTION_CREDITS,
    OPTION_ENDINGS,
    OPTION_GRAPHIC_NOVEL,
    OPTION_HALL_OF_DEAD,
    OPTION_HELP,
    OPTION_NEW_RUN,
    OPTION_SETTINGS,
    OPTION_STATS,
    handle_menu_input,
    render_menu,
)
from .pre_run import (
    CHARACTER_OPTIONS,
    handle_character_select_input,
    handle_deck_select_input,
    handle_ending_input,
    render_character_select,
    render_deck_select,
    render_ending,
)

__all__ = [
    # main_menu
    "MENU_OPTION_COUNT",
    "OPTION_CONTINUE",
    "OPTION_CREDITS",
    "OPTION_ENDINGS",
    "OPTION_GRAPHIC_NOVEL",
    "OPTION_HALL_OF_DEAD",
    "OPTION_HELP",
    "OPTION_NEW_RUN",
    "OPTION_SETTINGS",
    "OPTION_STATS",
    "handle_menu_input",
    "render_menu",
    # pre_run
    "CHARACTER_OPTIONS",
    "handle_character_select_input",
    "handle_deck_select_input",
    "handle_ending_input",
    "render_character_select",
    "render_deck_select",
    "render_ending",
    # gn_menu
    "GN_MENU_OPTION_COUNT",
    "handle_endings_browser_input",
    "handle_graphic_novel_ending_menu_input",
    "handle_graphic_novel_input",
    "handle_graphic_novel_menu_input",
    "handle_save_slot_select_input",
    "handle_saved_progress_input",
    "handle_telemetry_stats_input",
    "render_endings_browser",
    "render_telemetry_summary",
]

"""Main menu screen (ADR-0009, ADR-0032).

Text-based top-level menu with 9 options (ADR-0032 + ADR-0040 + Phase 7
+ Phase 15 + Phase 17). The Hub is described as a cyberspace construct,
but the main menu itself is a thin real-world UI.

Phase 5+: Uses unified screen shell (engine.layout).
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ...combat.palette import DEFAULT_COLOR, GRAY_MID, ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR
from ...i18n import Translator
from ..layout import (
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from ..state import AppState, ScreenKind

# Main menu options (1-indexed) — ADR-0032, ADR-0040, Phase 7/15/17
OPTION_NEW_RUN = 1
OPTION_GRAPHIC_NOVEL = 2
OPTION_CONTINUE = 3
OPTION_SETTINGS = 4
OPTION_CREDITS = 5
OPTION_HALL_OF_DEAD = 6  # Hall of Dead Jockeys (ADR-0040)
OPTION_HELP = 7  # Help screen (Phase 7: tutorial/onboarding)
OPTION_ENDINGS = 8  # Endings browser (Phase 15)
OPTION_STATS = 9  # Telemetry stats (Phase 17, requires telemetry_opt_in)

MENU_OPTION_COUNT = 9


def render_menu(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the main menu screen with unified layout (9 options)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    # Title
    draw_title(console, title_r, title=t("app.title"), subtitle=t("app.subtitle"))

    # Main area: 9 menu options (ADR-0032 + ADR-0040 + Phase 7 + Phase 15 + Phase 17)
    has_save = getattr(state, "has_save", False)
    stats_enabled = getattr(state, "telemetry_opt_in", False)
    options = [
        (OPTION_NEW_RUN, t("menu.new_run")),
        (OPTION_GRAPHIC_NOVEL, t("menu.graphic_novel")),
        (OPTION_CONTINUE, t("menu.continue") + ("" if has_save else " (없음)")),
        (OPTION_SETTINGS, t("menu.settings")),
        (OPTION_CREDITS, t("menu.credits")),
        (OPTION_HALL_OF_DEAD, t("menu.hall_of_dead")),
        (OPTION_HELP, t("menu.help")),
        (OPTION_ENDINGS, t("menu.endings")),
        (OPTION_STATS, t("stats.menu_label")),
    ]
    y = main_r.y + 1
    selected = getattr(state, "menu_selected_index", 0)
    for i, (key, label) in enumerate(options):
        # Dim disabled options (Continue when no save; Stats when opt-out).
        dim = (key == OPTION_CONTINUE and not has_save) or (
            key == OPTION_STATS and not stats_enabled
        )
        if dim:
            label = f"{label} (opt-in)"
        is_selected = i == selected
        marker = "▸ " if is_selected else "  "
        fg = (
            GRAY_MID
            if dim
            else (ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if is_selected else DEFAULT_COLOR)
        )
        console.print(
            x=main_r.x + 4,
            y=y + i * 2,
            string=f"{marker}{label}",
            fg=fg,
        )

    # Message (if any)
    if state.message:
        console.print(
            x=main_r.x + 4,
            y=main_r.y + main_r.h - 4,
            string=f"> {state.message}",
            fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
        )

    # Controls
    draw_controls(
        console,
        ctrl_r,
        lines=[t("menu.controls")],
    )

    # Footer
    draw_footer(
        console, foot_r, text=f"Main Menu  |  Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s"
    )


def _select_menu_option(state: AppState, index: int) -> None:
    """Execute the menu action for the given 0-based option index."""
    has_save = getattr(state, "has_save", False)
    if index == 0:
        state.screen = ScreenKind.HUB
    elif index == 1:
        state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
        state.gn_scene_chain = []
        state.gn_scene_index = 0
        state.gn_dialogue_index = 0
        state.gn_elapsed_ms = 0.0
        state.gn_paused = False
    elif index == 2:
        if has_save:
            state.screen = ScreenKind.HUB
            state.message = "Loading save..."
        else:
            state.message = "No save file. Use NEW RUN."
    elif index == 3:
        state.screen = ScreenKind.SETTINGS
        state.settings_selected = 0
    elif index == 4:
        state.message = "Credits: (Phase 7+)"
    elif index == 5:
        state.screen = ScreenKind.HALL_OF_DEAD
        state.hall_of_dead_selected = 0
    elif index == 6:
        state.screen = ScreenKind.HELP
        state.help_page = 0
    elif index == 7:
        state.screen = ScreenKind.ENDINGS_BROWSER
        state.endings_selected = 0
    elif index == 8:
        # Phase 17: gated by telemetry_opt_in. The disabled label in
        # render_menu already warns ("opt-in"), but the action itself
        # is a no-op when the player hasn't opted in.
        if getattr(state, "telemetry_opt_in", False):
            state.screen = ScreenKind.TELEMETRY_STATS
        else:
            state.message = "Stats require telemetry opt-in (Settings)"


def handle_menu_input(event: tcod.event.Event, state: AppState) -> bool:
    """Handle input on the menu screen. Returns False to quit.

    Arrow keys (↑↓) navigate, Enter/Space confirms.
    Number keys (1-9) also work.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            return False
        if event.sym in (KeySym.UP, KeySym.W):
            state.menu_selected_index = (state.menu_selected_index - 1) % MENU_OPTION_COUNT
            return True
        if event.sym in (KeySym.DOWN, KeySym.S):
            state.menu_selected_index = (state.menu_selected_index + 1) % MENU_OPTION_COUNT
            return True
        if event.sym in (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE):
            _select_menu_option(state, state.menu_selected_index)
            return True
        if event.sym is KeySym.N1:
            state.menu_selected_index = 0
            _select_menu_option(state, 0)
        elif event.sym is KeySym.N2:
            state.menu_selected_index = 1
            _select_menu_option(state, 1)
        elif event.sym is KeySym.N3:
            state.menu_selected_index = 2
            _select_menu_option(state, 2)
        elif event.sym is KeySym.N4:
            state.menu_selected_index = 3
            _select_menu_option(state, 3)
        elif event.sym is KeySym.N5:
            state.menu_selected_index = 4
            _select_menu_option(state, 4)
        elif event.sym is KeySym.N6:
            state.menu_selected_index = 5
            _select_menu_option(state, 5)
        elif event.sym is KeySym.N7:
            state.menu_selected_index = 6
            _select_menu_option(state, 6)
        elif event.sym is KeySym.N8:
            state.menu_selected_index = 7
            _select_menu_option(state, 7)
        elif event.sym is KeySym.N9:
            state.menu_selected_index = 8
            _select_menu_option(state, 8)
    return True

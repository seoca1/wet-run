"""Graphic Novel menu + post-game screens (ADR-0032, ADR-0048, ADR-0049, Phase 15/17).

Covers:
    - GRAPHIC_NOVEL_MENU input + scene-chain application
    - GRAPHIC_NOVEL_ENDING_MENU input (ADR-0048, ADR-0049)
    - GRAPHIC_NOVEL playback input (next/skip/pause/menu)
    - SAVED_PROGRESS input
    - SAVE_SLOT_SELECT input (ADR-0051)
    - ENDINGS_BROWSER render + input (Phase 15)
    - TELEMETRY_STATS render + input (Phase 17, ADR-0184)

Split from engine.menu.py per ADR-0110 (module size policy).
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ...i18n import Translator
from ...story.ending_renderer import EndingRenderer
from ...combat.palette import (
    DEFAULT_COLOR,
    GRAY_120,
    GRAY_DARK,
    GRAY_LIGHT,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    OLIVE,
    TA_CONSTRUCT_P2_COLOR,
)
from ..state import AppState, ScreenKind

GN_MENU_OPTION_COUNT = 11


def handle_graphic_novel_menu_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the GRAPHIC_NOVEL_MENU screen.

    Arrow keys (↑↓) or WASD navigate; Enter/Space confirms.
    Number keys (1-9, 0, A) also work for direct jumps.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            state.screen = ScreenKind.MENU
            return True
        if event.sym in (KeySym.UP, KeySym.W):
            state.gn_menu_selected = (state.gn_menu_selected - 1) % GN_MENU_OPTION_COUNT
            return True
        if event.sym in (KeySym.DOWN, KeySym.S):
            state.gn_menu_selected = (state.gn_menu_selected + 1) % GN_MENU_OPTION_COUNT
            return True
        if event.sym in (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE):
            _apply_gn_menu_selection(state)
            return True
        key_map = {
            KeySym.N1: 0,
            KeySym.N2: 1,
            KeySym.N3: 2,
            KeySym.N4: 3,
            KeySym.N5: 10,
            KeySym.N6: 5,
            KeySym.N7: 6,
            KeySym.N8: 7,
            KeySym.N9: 8,
            KeySym.N0: 9,
            KeySym.A: 9,
        }
        if event.sym in key_map:
            state.gn_menu_selected = key_map[event.sym]
            _apply_gn_menu_selection(state)
            return True
    return True


def _apply_gn_menu_selection(state: AppState) -> None:
    """Apply the GRAPHIC_NOVEL_MENU selection based on gn_menu_selected."""
    from ..graphic_novel_view import (
        GN_MENU_3JANE,
        GN_MENU_ANGIE,
        GN_MENU_BACK,
        GN_MENU_CONTINUE,
        GN_MENU_HERETIC,
        GN_MENU_NEUROMANCER,
        GN_MENU_NOVICE,
        GN_MENU_PROLOGUE,
        GN_MENU_SALLY,
        GN_MENU_SUIT,
        GN_MENU_VETERAN,
        GN_MENU_WIGAN,
    )

    has_save = getattr(state, "has_save", False)
    idx = state.gn_menu_selected
    if has_save:
        mapping = [
            GN_MENU_CONTINUE,
            GN_MENU_PROLOGUE,
            GN_MENU_NOVICE,
            GN_MENU_VETERAN,
            GN_MENU_HERETIC,
            GN_MENU_SUIT,
            GN_MENU_WIGAN,
            GN_MENU_ANGIE,
            GN_MENU_SALLY,
            GN_MENU_3JANE,
            GN_MENU_NEUROMANCER,
        ]
    else:
        mapping = [
            GN_MENU_PROLOGUE,
            GN_MENU_NOVICE,
            GN_MENU_VETERAN,
            GN_MENU_HERETIC,
            GN_MENU_SUIT,
            GN_MENU_WIGAN,
            GN_MENU_ANGIE,
            GN_MENU_SALLY,
            GN_MENU_3JANE,
            GN_MENU_NEUROMANCER,
        ]
    if idx == len(mapping):
        state.screen = ScreenKind.MENU
        return
    mode = mapping[idx]
    if mode == GN_MENU_BACK:
        state.screen = ScreenKind.MENU
        return
    if mode == GN_MENU_CONTINUE:
        state.screen = ScreenKind.SAVED_PROGRESS
        return
    state.gn_mode = mode
    state.screen = ScreenKind.GRAPHIC_NOVEL
    state.gn_scene_index = 0
    state.gn_dialogue_index = 0
    state.gn_elapsed_ms = 0.0
    state.gn_scene_chain = []
    from .. import config
    from ..graphic_novel_view import load_prologue_chain, load_scene_chain

    scenes_dir = config.DATA_DIR / "scenes"
    if mode == "prologue":
        state.gn_scenes = load_prologue_chain(scenes_dir, seed=42, ending="A")
    else:
        state.gn_scenes = load_scene_chain(scenes_dir, mode, ending="A")


def handle_graphic_novel_ending_menu_input(
    event: tcod.event.Event,
    state: AppState,
) -> str:
    """Handle input on the GRAPHIC_NOVEL_ENDING_MENU screen (ADR-0048, ADR-0049).

    Returns the selected ending:
        - "A" : default ending (Finn's offer accepted, etc.)
        - "B" : alternative ending (mysterious refusal, etc.)
        - "C" : third ending — vanishing / erase / unmaking (ADR-0049)
        - "back" : return to GRAPHIC_NOVEL_MENU
        - "" if no action

    The number of options depends on how many endings exist for the current
    character (probed from :func:`available_endings`). N1..N{count} map to
    endings A..{chr(ord('A')+count-1)}. ESC/Q are always "back".
    """
    from ..graphic_novel_view import available_endings

    if not isinstance(event, KeyDown):
        return ""
    if event.sym in (KeySym.ESCAPE, KeySym.Q):
        return "back"
    # Determine current character's available endings from the screen context
    # (state.gn_mode is set to novice/veteran/heretic when entering the screen).
    endings = available_endings(state.gn_mode)
    n_count = len(endings)
    back_keys = [getattr(KeySym, f"N{i}") for i in range(1, n_count + 1)]
    # Find the back key (first N-key not used by an ending option)
    back_sym: KeySym | None = None
    for i in range(1, n_count + 2):
        sym = getattr(KeySym, f"N{i}")
        if sym not in back_keys:
            back_sym = sym
            break
    if back_sym is not None and event.sym is back_sym:
        return "back"
    for i, ending in enumerate(endings, start=1):
        if event.sym is getattr(KeySym, f"N{i}"):
            return ending
    return ""


def handle_graphic_novel_input(
    event: tcod.event.Event,
    state: AppState,
) -> str:
    """Handle input during graphic novel playback.

    Returns the action:
        - "next" : advance to next dialogue
        - "skip" : skip current scene
        - "pause" : toggle pause
        - "menu" : exit graphic novel → saved_progress
        - "" : no action
    """
    if not isinstance(event, KeyDown):
        return ""
    if event.sym in (KeySym.ESCAPE, KeySym.Q):
        return "menu"
    if event.sym in (KeySym.SPACE, KeySym.RIGHT):
        return "next"
    if event.sym is KeySym.S:
        return "skip"
    if event.sym is KeySym.P:
        return "pause"
    return ""


def handle_saved_progress_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the SAVED_PROGRESS screen.

    Arrow keys (↑↓) or WASD navigate; Enter/Space confirms.
    """
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q, KeySym.N3):
            state.screen = ScreenKind.MENU
            return True
        if event.sym in (KeySym.UP, KeySym.W):
            return True
        if event.sym in (KeySym.DOWN, KeySym.S):
            return True
        if event.sym in (KeySym.RETURN, KeySym.KP_ENTER, KeySym.SPACE, KeySym.N1):
            state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
            return True
        if event.sym is KeySym.N2:
            state.screen = ScreenKind.HUB
            return True
    return True


def handle_save_slot_select_input(
    event: tcod.event.Event,
    state: AppState,
) -> str:
    """Handle input on the SAVE_SLOT_SELECT screen (ADR-0051).

    Returns the action:
        - "select_1" / "select_2" / "select_3" : choose slot
        - "delete_1" / "delete_2" / "delete_3" : delete slot (D key)
        - "back" : return to previous menu (ESC)
        - "" : no action
    """
    if not isinstance(event, KeyDown):
        return ""
    if event.sym in (KeySym.ESCAPE, KeySym.Q):
        return "back"
    if event.sym in (KeySym.N1, KeySym.N2, KeySym.N3):
        slot = int(event.sym.name[1:])  # "N1" → 1
        state.gn_save_slot_selected = slot
        return f"select_{slot}"
    # D + N for delete (Shift+D or just D1/D2/D3)
    if event.sym == getattr(KeySym, "D", None):
        # Plain D — delete currently selected (or last selected)
        if state.gn_save_slot_selected:
            return f"delete_{state.gn_save_slot_selected}"
    return ""


def render_endings_browser(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the ENDINGS_BROWSER screen — browse unlocked endings (Phase 15)."""
    console.clear()
    width = console.width

    title = "엔딩 브라우저" if t.lang == "ko" else "Endings Browser"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    renderer = EndingRenderer()
    all_endings = renderer.get_all()

    if not all_endings:
        console.print(4, 4, "No endings found.", fg=GRAY_LIGHT)
    else:
        selected = getattr(state, "endings_selected", 0)
        # Simple list with scrolling if needed
        y_start = 3
        max_visible = console.height - 10
        offset = max(0, selected - max_visible + 1)

        for i, ending in enumerate(all_endings[offset : offset + max_visible]):
            idx = i + offset
            is_selected = idx == selected
            marker = "▶ " if is_selected else "  "
            fg = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if is_selected else DEFAULT_COLOR
            console.print(x=2, y=y_start + i, string=f"{marker}{ending.title}", fg=fg)

        # Details for selected ending
        if selected < len(all_endings):
            e = all_endings[selected]
            detail_y = y_start + max_visible + 1
            console.print(x=2, y=detail_y, string="─" * (width - 4), fg=GRAY_DARK)
            console.print(
                x=2, y=detail_y + 1, string=f"Type: {e.ending_type.upper()}", fg=GRAY_LIGHT
            )
            console.print(
                x=2, y=detail_y + 2, string=f"Character: {e.character_ref}", fg=GRAY_LIGHT
            )

            # Wrap description
            desc_lines = []
            words = e.description.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 < width - 6:
                    current_line += word + " "
                else:
                    desc_lines.append(current_line.strip())
                    current_line = word + " "
            desc_lines.append(current_line.strip())

            for i, line in enumerate(desc_lines[:3]):
                console.print(x=2, y=detail_y + 3 + i, string=line, fg=DEFAULT_COLOR)

    footer_hint = "[↑↓] Navigate  [ESC] Back"
    if t.lang == "ko":
        footer_hint = "[↑↓] 이동  [ESC] 뒤로"
    console.print(0, console.height - 1, "═" * width)
    console.print((width - len(footer_hint)) // 2, console.height - 1, f" {footer_hint} ")


def handle_endings_browser_input(event: object, state: AppState) -> bool:
    """Handle input on ENDINGS_BROWSER screen."""
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.MENU
            return True

        renderer = EndingRenderer()
        total = renderer.get_total()
        if total > 0:
            selected = getattr(state, "endings_selected", 0)
            if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.W):
                state.endings_selected = (selected - 1) % total
                return True
            if event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.S):
                state.endings_selected = (selected + 1) % total
                return True
    return True


def render_telemetry_summary(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the TELEMETRY_STATS screen (Phase 17, ADR-0184).

    Read-only display of aggregated run statistics. Opt-in guard:
    the screen is only reachable when ``state.telemetry_opt_in`` is
    True (enforced in ``_select_menu_option``). We double-check here
    so a state-internal bug cannot leak aggregate data to an
    opt-out player.
    """
    from ...combat.telemetry_integration import TelemetryIntegrator

    console.clear()
    width = console.width
    title = t("stats.title")
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)
    subtitle = t("stats.subtitle")
    console.print((width - len(subtitle)) // 2, 3, subtitle, fg=OLIVE)

    if not getattr(state, "telemetry_opt_in", False):
        console.print(
            x=4,
            y=6,
            string="(Telemetry is OFF — opt in via Settings to see stats.)",
            fg=TA_CONSTRUCT_P2_COLOR,
        )
        _stats_footer(console, t, width)
        return

    integrator = getattr(state, "telemetry", None)
    if not isinstance(integrator, TelemetryIntegrator):
        console.print(x=4, y=6, string=t("stats.empty"), fg=GRAY_LIGHT)
        _stats_footer(console, t, width)
        return

    y = 5
    console.print(x=2, y=y, string=t("stats.section_meta"), fg=OLIVE)
    y += 1
    total = integrator.get_event_count()
    console.print(
        x=4,
        y=y,
        string=t("stats.total_events", n=total),
        fg=DEFAULT_COLOR,
    )
    y += 2

    deaths = integrator.aggregate_death_rates()
    kills = integrator.aggregate_kill_counts()
    decks = integrator.aggregate_deck_distribution()
    mutators = integrator.aggregate_mutator_choices()

    for section_label, data in (
        (t("stats.section_deaths"), deaths),
        (t("stats.section_kills"), kills),
        (t("stats.section_deck"), decks),
        (t("stats.section_mutator"), mutators),
    ):
        console.print(x=2, y=y, string=section_label, fg=OLIVE)
        y += 1
        if not data:
            console.print(x=4, y=y, string="(none)", fg=GRAY_120)
            y += 1
        else:
            for key, count in sorted(data.items()):
                console.print(
                    x=4,
                    y=y,
                    string=f"  {key}: {count}",
                    fg=DEFAULT_COLOR,
                )
                y += 1
        y += 1

    _stats_footer(console, t, width)


def _stats_footer(console: tcod.console.Console, t: Translator, width: int) -> None:
    """Draw the standard footer for the telemetry stats screen."""
    console.print(0, console.height - 1, "═" * width)
    controls = t("stats.controls")
    console.print((width - len(controls)) // 2, console.height - 1, f" {controls} ")


def handle_telemetry_stats_input(event: object, state: AppState) -> bool:
    """Handle input on TELEMETRY_STATS screen.

    The screen is read-only — ESC / Q returns to the main menu. No
    navigation arrows needed (each section is short, fits on screen).
    """
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.MENU
            return True
    return True

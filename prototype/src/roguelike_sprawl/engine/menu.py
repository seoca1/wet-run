"""Main menu screen (ADR-0009, ADR-0032).

Text-based menu. The Hub is described as a cyberspace construct, but
the main menu itself is a thin real-world UI.

Phase 5+: Uses unified screen shell (engine.layout).
ADR-0032: Extended to 5 options (NEW RUN, GRAPHIC NOVEL, CONTINUE,
          SETTINGS, CREDITS).
"""

from __future__ import annotations

import tcod.console
import tcod.context
import tcod.event
from tcod.event import KeyDown, KeySym

from ..i18n import Translator
from .layout import (
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .state import AppState, ScreenKind

# Main menu options (1-indexed) — ADR-0032, ADR-0040, Phase 7
OPTION_NEW_RUN = 1
OPTION_GRAPHIC_NOVEL = 2
OPTION_CONTINUE = 3
OPTION_SETTINGS = 4
OPTION_CREDITS = 5
OPTION_HALL_OF_DEAD = 6  # Hall of Dead Jockeys (ADR-0040)
OPTION_HELP = 7  # Help screen (Phase 7: tutorial/onboarding)

MENU_OPTION_COUNT = 7


def render_menu(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the main menu screen with unified layout (5 options)."""
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

    # Main area: 7 menu options (ADR-0032 + ADR-0040 + Phase 7)
    has_save = getattr(state, "has_save", False)
    options = [
        (OPTION_NEW_RUN, t("menu.new_run")),
        (OPTION_GRAPHIC_NOVEL, t("menu.graphic_novel")),
        (OPTION_CONTINUE, t("menu.continue") + ("" if has_save else " (없음)")),
        (OPTION_SETTINGS, t("menu.settings")),
        (OPTION_CREDITS, t("menu.credits")),
        (OPTION_HALL_OF_DEAD, t("menu.hall_of_dead")),
        (OPTION_HELP, t("menu.help")),
    ]
    y = main_r.y + 1
    selected = getattr(state, "menu_selected_index", 0)
    for i, (_key, label) in enumerate(options):
        # Dim disabled options (e.g. Continue when no save)
        dim = i + 1 == OPTION_CONTINUE and not has_save
        is_selected = i == selected
        marker = "▸ " if is_selected else "  "
        fg = (100, 100, 100) if dim else ((255, 255, 0) if is_selected else (200, 200, 200))
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
            fg=(255, 255, 0),
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


def handle_menu_input(event: tcod.event.Event, state: AppState) -> bool:
    """Handle input on the menu screen. Returns False to quit.

    Arrow keys (↑↓) navigate, Enter/Space confirms.
    Number keys (1-7) also work.
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
    return True


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
    from .graphic_novel_view import (
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
    from . import config
    from .graphic_novel_view import load_prologue_chain, load_scene_chain

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
    from .graphic_novel_view import available_endings

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


CHARACTER_OPTIONS = [
    ("케이 (K)", "novice", "Case — Neuromancer trilogy protagonist"),
    ("실 (Sil)", "veteran", "Molly's crew — Count Zero"),
    ("카스 (Kas)", "heretic", "Wintermute's ally — Mona Lisa Overdrive"),
]

_CHARACTER_TO_CHAPTER_FILE = {
    "novice": "case.json",
    "veteran": "sil.json",
    "heretic": "kas.json",
}


def _load_chapter(state: AppState, char_id: str) -> None:
    """Load chapter and arc JSON for the given character ID into state."""
    from . import config as config_mod
    from .chapter_cutscene import get_arc_for_character
    from .chapter_view import load_chapter

    filename = _CHARACTER_TO_CHAPTER_FILE.get(char_id)
    if filename is None:
        return
    chapter_path = config_mod.DATA_DIR / "story" / "chapters" / filename
    try:
        state.chapter_data = load_chapter(chapter_path)
    except FileNotFoundError:
        state.chapter_data = None

    try:
        state.current_arc = get_arc_for_character(config_mod.DATA_DIR, char_id)
    except Exception:
        state.current_arc = None

    state.chapter_elapsed_ms = 0.0
    state.chapter_typed_chars = 0
    state.current_chapter_index = 0
    state.current_phase_index = 0
    state.current_beat_index = 0
    state.phase_elapsed_ms = 0.0
    state.phase_typed_chars = 0


def render_character_select(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the CHARACTER_SELECT screen — choose jockey (ADR-0031)."""
    console.clear()
    width = console.width

    title = "자키 선택" if t.lang == "ko" else "Choose Your Jockey"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    hint = "The Finn's offer: simple data extraction run. ICE is light."
    if t.lang == "ko":
        hint = "더 핀의 제안:简单的 데이터 추출 미션. ICE는 가벼울 거야."
    console.print((width - len(hint)) // 2, 3, hint, fg=(180, 180, 100))

    selected = getattr(state, "character_select_index", 0)
    y = 6
    for i, (name, _char_id, desc) in enumerate(CHARACTER_OPTIONS):
        marker = "▶ " if i == selected else "  "
        fg = (255, 255, 0) if i == selected else (200, 200, 200)
        console.print(x=4, y=y + i * 4, string=f"{marker}[{i + 1}] {name}", fg=fg)
        console.print(x=6, y=y + i * 4 + 1, string=desc, fg=(128, 128, 128))
        console.print(x=6, y=y + i * 4 + 2, string="─" * 50, fg=(60, 60, 60))

    if state.ng_plus_unlocked:
        ng_status = "NG+ MODE: ON" if state.ng_plus_active else "NG+ MODE: OFF"
        ng_color = (255, 200, 80) if state.ng_plus_active else (120, 120, 120)
        console.print(
            x=(width - len(ng_status)) // 2,
            y=console.height - 3,
            string=ng_status,
            fg=ng_color,
        )

    footer_hint = "[↑↓] Navigate  [Enter] Confirm  [ESC] Back"
    if state.ng_plus_unlocked:
        footer_hint = "[↑↓] Navigate  [N] NG+  [Enter] Confirm  [ESC] Back"
    if t.lang == "ko":
        footer_hint = "[↑↓] 이동  [Enter] 확인  [ESC] 뒤로"
        if state.ng_plus_unlocked:
            footer_hint = "[↑↓] 이동  [N] NG+  [Enter] 확인  [ESC] 뒤로"
    console.print(0, console.height - 1, "═" * width)
    console.print((width - len(footer_hint)) // 2, console.height - 1, f" {footer_hint} ")


def handle_character_select_input(event: object, state: AppState) -> bool:
    """Handle input on CHARACTER_SELECT screen. Arrow keys navigate, Enter confirms.

    Cycle 4 Pillar 4: NG+ unlock hook — press N to toggle ng_plus_active when
    ng_plus_unlocked is True. Confirming a character applies the toggle to
    the new run (state.ng_plus_active reflects whether this is an NG+ run).
    """
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.MENU
            return True
        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.W):
            state.character_select_index = (state.character_select_index - 1) % 3
            return True
        if event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.S):
            state.character_select_index = (state.character_select_index + 1) % 3
            return True
        if event.sym is tcod.event.KeySym.N and state.ng_plus_unlocked:
            state.ng_plus_active = not state.ng_plus_active
            return True
        if event.sym in (
            tcod.event.KeySym.RETURN,
            tcod.event.KeySym.KP_ENTER,
            tcod.event.KeySym.SPACE,
        ):
            idx = state.character_select_index
            char_id = CHARACTER_OPTIONS[idx][1]
            state.character_id = char_id
            state.chapter_id = f"chapter_{char_id}"
            if not state.ng_plus_unlocked:
                state.ng_plus_active = False
            _load_chapter(state, char_id)
            state.screen = ScreenKind.CHAPTER
            return True
        if event.sym in (tcod.event.KeySym.N1, tcod.event.KeySym.N2, tcod.event.KeySym.N3):
            idx = int(event.sym.name[1]) - 1
            state.character_select_index = idx
            char_id = CHARACTER_OPTIONS[idx][1]
            state.character_id = char_id
            state.chapter_id = f"chapter_{char_id}"
            if not state.ng_plus_unlocked:
                state.ng_plus_active = False
            _load_chapter(state, char_id)
            state.screen = ScreenKind.CHAPTER
            return True
    return True


def render_ending(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the ENDING screen (ADR-0031)."""
    console.clear()
    width = console.width
    height = console.height

    title = "ENDING" if state.ending_choice else "PENDING"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    if state.ending_choice == "A":
        msg_ko = "엔딩 A — 더 핀의 제안을 받아들였다"
        msg_en = "Ending A — You accepted The Finn's offer"
    elif state.ending_choice == "B":
        msg_ko = "엔딩 B — 더 핀의 제안을 거절했다"
        msg_en = "Ending B — You declined The Finn's offer"
    elif state.ending_choice == "C":
        msg_ko = "엔딩 C — 모든 것을 지웠다"
        msg_en = "Ending C — You erased everything"
    else:
        msg_ko = "엔딩이 아직 결정되지 않았다"
        msg_en = "Ending not yet determined"

    msg = msg_ko if t.lang == "ko" else msg_en
    console.print((width - len(msg)) // 2, height // 2 - 2, msg, fg=(255, 255, 0))
    hint = "[ESC] Return to menu"
    console.print(0, height - 1, "═" * width)
    console.print((width - len(hint)) // 2, height - 1, f" {hint} ")


def handle_ending_input(event: object, state: AppState) -> bool:
    """Handle input on ENDING screen."""
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.MENU
            return True
    return True

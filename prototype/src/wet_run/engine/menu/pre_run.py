"""Pre-run selection flow: CHARACTER_SELECT → DECK_SELECT → CHAPTER, plus ENDING.

Per ADR-0031 (jockey selection) + ADR-0178 (deck size selection). These
screens sit between the main menu and the first gameplay screen, so we
keep them grouped even though they are not the "main" menu.

Split from engine.menu.py per ADR-0110 (module size policy).
"""

from __future__ import annotations

import tcod.console

from ...i18n import Translator
from ...combat.palette import (
    COMBO_BAR_YELLOW,
    DEFAULT_COLOR,
    GRAY_120,
    GRAY_DARK,
    GRAY_MID_LIGHT,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    OLIVE,
)
from ..state import AppState, ScreenKind

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
    from .. import config as config_mod
    from ..chapter_cutscene import get_arc_for_character
    from ..chapter_view import load_chapter

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
    console.print((width - len(hint)) // 2, 3, hint, fg=OLIVE)

    selected = getattr(state, "character_select_index", 0)
    y = 6
    for i, (name, _char_id, desc) in enumerate(CHARACTER_OPTIONS):
        marker = "▶ " if i == selected else "  "
        fg = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if i == selected else DEFAULT_COLOR
        console.print(x=4, y=y + i * 4, string=f"{marker}[{i + 1}] {name}", fg=fg)
        console.print(x=6, y=y + i * 4 + 1, string=desc, fg=GRAY_MID_LIGHT)
        console.print(x=6, y=y + i * 4 + 2, string="─" * 50, fg=GRAY_DARK)

    if state.ng_plus_unlocked:
        ng_status = "NG+ MODE: ON" if state.ng_plus_active else "NG+ MODE: OFF"
        ng_color = COMBO_BAR_YELLOW if state.ng_plus_active else GRAY_120
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
            state.screen = ScreenKind.DECK_SELECT
            state.deck_select_index = 1  # Default to STANDARD
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
            state.screen = ScreenKind.DECK_SELECT
            state.deck_select_index = 1  # Default to STANDARD
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
    console.print(
        (width - len(msg)) // 2, height // 2 - 2, msg, fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR
    )
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


def render_deck_select(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the DECK_SELECT screen — choose deck size (ADR-0178)."""
    console.clear()
    width = console.width

    title = "데크 사이즈 선택" if t.lang == "ko" else "Choose Deck Size"
    console.print(0, 0, "═" * width)
    console.print((width - len(title)) // 2, 0, f" {title} ")
    console.print(0, 1, "─" * width)

    hint = "Deck size affects program slots, AP regen, and cooldowns."
    if t.lang == "ko":
        hint = "데크 사이즈는 프로그램 슬롯, AP 재생, 쿨다운에 영향을 줍니다."
    console.print((width - len(hint)) // 2, 3, hint, fg=OLIVE)

    options = [
        ("LIGHT", "light", "6 slots, +50% AP regen, -10% cooldowns"),
        ("STANDARD", "standard", "8 slots, balanced"),
        ("HEAVY", "heavy", "10 slots, -30% AP regen, +15% cooldowns"),
    ]

    selected = getattr(state, "deck_select_index", 1)
    y = 6
    for i, (name, _size_id, desc) in enumerate(options):
        marker = "▶ " if i == selected else "  "
        fg = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if i == selected else DEFAULT_COLOR
        console.print(x=4, y=y + i * 4, string=f"{marker}[{i + 1}] {name}", fg=fg)
        console.print(x=6, y=y + i * 4 + 1, string=desc, fg=GRAY_MID_LIGHT)
        console.print(x=6, y=y + i * 4 + 2, string="─" * 50, fg=GRAY_DARK)

    footer_hint = "[↑↓] Navigate  [Enter] Confirm  [ESC] Back"
    if t.lang == "ko":
        footer_hint = "[↑↓] 이동  [Enter] 확인  [ESC] 뒤로"
    console.print(0, console.height - 1, "═" * width)
    console.print((width - len(footer_hint)) // 2, console.height - 1, f" {footer_hint} ")


def handle_deck_select_input(event: object, state: AppState) -> bool:
    """Handle input on DECK_SELECT screen."""
    import tcod.event

    if isinstance(event, tcod.event.KeyDown):
        if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
            state.screen = ScreenKind.CHARACTER_SELECT
            return True
        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.W):
            state.deck_select_index = (state.deck_select_index - 1) % 3
            return True
        if event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.S):
            state.deck_select_index = (state.deck_select_index + 1) % 3
            return True
        if event.sym in (
            tcod.event.KeySym.RETURN,
            tcod.event.KeySym.KP_ENTER,
            tcod.event.KeySym.SPACE,
        ):
            idx = state.deck_select_index
            sizes = ["light", "standard", "heavy"]
            _confirm_deck_choice(state, sizes[idx])
            state.screen = ScreenKind.CHAPTER
            return True
        if event.sym in (tcod.event.KeySym.N1, tcod.event.KeySym.N2, tcod.event.KeySym.N3):
            idx = int(event.sym.name[1]) - 1
            state.deck_select_index = idx
            sizes = ["light", "standard", "heavy"]
            _confirm_deck_choice(state, sizes[idx])
            state.screen = ScreenKind.CHAPTER
            return True
    return True


def _confirm_deck_choice(state: AppState, deck_size: str) -> None:
    """Persist the chosen deck size and emit telemetry (Phase 16)."""
    state.deck_size = deck_size
    if getattr(state, "telemetry_opt_in", False):
        integrator = getattr(state, "telemetry", None)
        if integrator is not None:
            try:
                integrator.record_deck_chosen(deck_size)
            except Exception as exc:  # pragma: no cover - defensive
                state.status_messages.append(f">>> Telemetry deck_chosen failed: {exc}")

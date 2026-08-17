"""Help screen — controls reference and game concepts (Phase 7).

Displays:
- Universal controls (navigation, confirm, cancel)
- Matrix exploration controls
- Combat controls
- Key concepts (ICE, deck, matrix, etc.)

Accessible from main menu as option 7 (HELP).
"""

from __future__ import annotations

import tcod.console
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

HELP_PAGES = [
    {
        "title": "UNIVERSAL CONTROLS",
        "lines": [
            "  /\\ /\\   Navigate menus (up/down/left/right)",
            " <   >   ENTER or SPACE  —  Confirm / Use",
            "  \\/ \\/   ESC  —  Cancel / Back / Close",
            "   []    Q  —  Quit game",
            "",
            "  Both ENTER and SPACE work the same way!",
        ],
    },
    {
        "title": "MATRIX EXPLORATION",
        "lines": [
            "  Arrow keys  —  Move between nodes",
            "  D  —  Toggle Dungeon Mode (2D grid view)",
            "  ENTER/SPACE  —  Open action menu",
            "  S  —  Quick SCAN shortcut",
            "  E  —  Quick EXTRACT/ENGAGE shortcut",
            "  J  —  Quick JACK OUT shortcut",
        ],
    },
    {
        "title": "COMBAT (RT-MS)",
        "lines": [
            "  Arrow keys  —  Select skill",
            "  ENTER/SPACE  —  Use selected skill",
            "  1-4  —  Quick skill shortcut (no navigation)",
            "  ESC  —  Disengage / Flee",
            "",
            "  Status colors:",
            "  Cyan = Selected   White = Available   Gray = Unavailable",
        ],
    },
    {
        "title": "KEY CONCEPTS",
        "lines": [
            "  MATRIX  —  Cyberspace network you jack into",
            "  ICE  —  Intrusion Countermeasures Electronics (security)",
            "  DECK  —  Your hardware for jacking in",
            "  PROGRAM  —  Software tools (attack, defense, scan)",
            "  ZDR  —  Zone Difficulty Rating (higher = harder)",
            "  PPL  —  Player Power Level (your combat strength)",
        ],
    },
    {
        "title": "MISSION FLOW",
        "lines": [
            "  1. Hub  —  Accept a job from a fixer",
            "  2. Matrix  —  Jack in, navigate, bypass ICE",
            "  3. Combat  —  Fight ICE to get data",
            "  4. Jack Out  —  Disconnect safely",
            "  5. Reward  —  Collect payment and items",
            "",
            "  If you die: Hall of Dead → choose new jockey",
        ],
    },
]


def render_help(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    page: int = 0,
) -> None:
    """Render the help screen (current page)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    total = len(HELP_PAGES)
    current = page % total
    info = HELP_PAGES[current]

    draw_title(
        console,
        title_r,
        title=t("help.title"),
        subtitle=f"[{current + 1}/{total}] {info['title']}",
    )

    y = main_r.y + 1
    for line in info["lines"]:
        if y > main_r.y + main_r.h - 2:
            break
        console.print(x=main_r.x + 2, y=y, string=line)
        y += 1

    draw_controls(console, ctrl_r, [t("help.controls")])
    draw_footer(
        console,
        foot_r,
        text=f"[{current + 1}/{total}] {info['title']} | {t('help.footer')}",
    )


def handle_help_input(
    event: tcod.event.Event,
    state: AppState,
) -> AppState | None:
    """Handle input on the help screen. Returns new state or None to stay."""
    page = getattr(state, "help_page", 0)
    total = len(HELP_PAGES)

    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE, KeySym.Q):
            state.screen = ScreenKind.MENU
            if hasattr(state, "help_page"):
                delattr(state, "help_page")
            return state
        elif event.sym in (KeySym.LEFT, KeySym.PAGEUP):
            state.help_page = (page - 1) % total
            return state
        elif event.sym in (KeySym.RIGHT, KeySym.PAGEDOWN, KeySym.SPACE, KeySym.RETURN):
            state.help_page = (page + 1) % total
            return state

    return state

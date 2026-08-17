"""Debrief screen — optional narrative between REWARD and Hub.

When enabled, this screen shows a short narrative message after
the reward screen — world-building, intel unlocked, or a teaser for
the next mission. Player presses any key to dismiss.

References:
    run.state.Stage.DEBRIEF
    design/systems/stage_structure.json
"""

from __future__ import annotations

import tcod.console
import tcod.event

from ..run import Stage
from . import config as _engine_config
from .state import AppState, ScreenKind

# Static debrief messages (per-character flavor)
DEBRIEF_MESSAGES: dict[str, tuple[str, ...]] = {
    "novice": (
        "Dixie's voice, faint: 'You did good, cowboy.'",
        "The data burns. The Sprawl forgets.",
        "Wim slides you a beer. 'On the house.'",
    ),
    "veteran": (
        "Mara's ghost, maybe: 'You got them, Sil.'",
        "Tessier-Ashpool will know. Soon.",
        "Freeside's relays pick up the signal.",
    ),
    "heretic": (
        "Maelcum's voice, calm: 'The wheel turns.'",
        "The Loa network carries the truth.",
        "Zion remembers. Babylon forgets.",
    ),
}


def enter_debrief(state: AppState, character: str = "novice") -> None:
    """Transition into the Debrief screen.

    Args:
        state: App state.
        character: Which protagonist (for flavor text).
    """
    state.screen = ScreenKind.DEBRIEF
    state.debrief_character = character
    state.debrief_index = 0
    state.status_messages.append(">>> Debrief: mission complete.")


def advance_from_debrief(state: AppState) -> None:
    """Move from DEBRIEF to COMPLETE stage.

    Called when the player dismisses the debrief message.
    """
    if state.run_state is None:
        return
    if state.run_state.current_stage is not Stage.DEBRIEF:
        return

    # Advance to next stage (which is COMPLETE for debrief)
    state.run_state.mark_advance()

    # Now in COMPLETE. Return to hub.
    # We need to reset matrix state and switch to hub
    # Reward view has the cleanup, but we don't want to award rewards again
    # Just do the reset directly
    state.matrix = None
    state.current_node_id = None
    state.cyberspace_layouts = None
    state.server_subgraph = None
    state.in_server_browser = True
    state.selected_server_index = 0
    state.current_mission = None
    state.mission_progress = {}
    state.screen = ScreenKind.HUB
    state.status_messages.append(">>> Debrief complete. Returned to hub.")


def render_debrief(console: tcod.console.Console, state: AppState) -> None:
    """Render the Debrief screen."""
    SCREEN_WIDTH = _engine_config.SCREEN_WIDTH  # noqa: N806
    SCREEN_HEIGHT = _engine_config.SCREEN_HEIGHT  # noqa: N806

    console.clear(bg=(0, 0, 0))

    # Title
    title = "DEBRIEF"
    console.print(
        x=(SCREEN_WIDTH - len(title)) // 2,
        y=3,
        string=title,
        fg=(200, 200, 100),
    )

    # Box
    box_x = (SCREEN_WIDTH - 60) // 2
    box_y = 6
    box_w = 60
    box_h = 8

    console.print(x=box_x, y=box_y, string="┌" + "─" * (box_w - 2) + "┐", fg=(200, 200, 100))
    for y in range(box_y + 1, box_y + box_h - 1):
        console.print(x=box_x, y=y, string="│" + " " * (box_w - 2) + "│", fg=(200, 200, 100))
    console.print(
        x=box_x,
        y=box_y + box_h - 1,
        string="└" + "─" * (box_w - 2) + "┘",
        fg=(200, 200, 100),
    )

    # Get message for current character
    char = getattr(state, "debrief_character", "novice")
    messages = DEBRIEF_MESSAGES.get(char, DEBRIEF_MESSAGES["novice"])
    idx = getattr(state, "debrief_index", 0) % len(messages)
    message = messages[idx]

    # Render message centered
    msg_y = box_y + 3
    words = message.split()
    line = ""
    line_y = msg_y
    for word in words:
        test = line + " " + word if line else word
        if len(test) > box_w - 6:
            console.print(
                x=box_x + 3,
                y=line_y,
                string=line,
                fg=(180, 180, 200),
            )
            line = word
            line_y += 1
        else:
            line = test
    if line:
        console.print(
            x=box_x + 3,
            y=line_y,
            string=line,
            fg=(180, 180, 200),
        )

    # Prompt
    prompt = "[ANY KEY] Continue"
    console.print(
        x=(SCREEN_WIDTH - len(prompt)) // 2,
        y=box_y + box_h + 2,
        string=prompt,
        fg=(200, 200, 200),
    )

    # Status
    if state.status_messages:
        for i, msg in enumerate(state.status_messages[-3:]):
            console.print(
                x=2,
                y=SCREEN_HEIGHT - 5 + i,
                string=msg,
                fg=(120, 120, 120),
            )


def handle_debrief_input(event: tcod.event.Event, state: AppState) -> bool:
    """Handle input on the Debrief screen."""
    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym is tcod.event.KeySym.Q:
        return False
    if event.sym is tcod.event.KeySym.ESCAPE:
        return False

    # Any other key advances
    advance_from_debrief(state)
    return True

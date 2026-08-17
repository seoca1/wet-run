"""Jack Out screen — matrix disconnect animation.

When a Run enters Stage.JACK_OUT, this screen shows a brief
disconnect animation and waits for player input to advance to
Stage.REWARD (rewards screen).

ASCII animation uses gradient blocks (░▒▓█) fading out to simulate
the neural connection breaking.

References:
    run.state.Stage.JACK_OUT
    design/systems/stage_structure.json
"""

from __future__ import annotations

import time

import tcod.console
import tcod.event

from ..audio import sound_manager as _sm_module
from ..run import Stage
from . import config as _engine_config
from .state import AppState, ScreenKind

# --- Animation ---

# Frames for the disconnect animation.
# Each frame is a list of strings (lines). Lines get progressively shorter.
_ANIMATION_FRAMES: tuple[tuple[str, ...], ...] = (
    (  # Frame 0: full connection
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        "  ░  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░",
        "  ░  ── DISCONNECTING ──   ░",
        "  ░  ░▒▓█             ▓▒░  ░",
        "  ░  ░▒▓█  CONNECTED  ▓▒░  ░",
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ),
    (  # Frame 1: glitch
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        "  ░  ░▒▓█▓▒░░▒▓▓▒░░▒▓▓▒░  ░",
        "  ░  ── DISCONNECTING ──   ░",
        "  ░  ░▒▓█  ░ GLITCH  ▓▒░  ░",
        "  ░  ░▒▓█▓▒░░▒▓▓▒░░▒▓▓▒░  ░",
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ),
    (  # Frame 2: fading
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        "  ░                       ░",
        "  ░   ── DISCONNECTING ── ░",
        "  ░      ░▒▓ FADE ▓▒░       ░",
        "  ░                       ░",
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ),
    (  # Frame 3: gone
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        "  ░                       ░",
        "  ░                       ░",
        "  ░      J A C K E D  O U T ░",
        "  ░                       ░",
        "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ),
)

_FRAME_DURATION_S = 0.5  # seconds per frame


# --- Stage transition helpers ---


def enter_jack_out(state: AppState) -> None:
    """Transition into the Jack Out screen.

    Called from cyberspace when DEFEAT_ICE advances to JACK_OUT.
    Sets up animation state and switches screen.
    """
    state.screen = ScreenKind.JACK_OUT
    state.jack_out_frame_index = 0
    state.jack_out_started_at = time.monotonic()
    state.status_messages.append(">>> Jacking out of the matrix...")

    # Play jack-out sound
    try:
        _sm_module.play("movement/jack_out")
    except Exception:
        pass

    # Auto-save on JACK_OUT (critical point — player has earned rewards)
    _try_auto_save(state, slot=2)  # Use slot 2 for autosave


def _try_auto_save(state: AppState, slot: int = 2) -> None:
    """Try to auto-save the current run, silently ignoring errors."""
    try:
        from .save_manager import SaveManager

        manager = SaveManager()
        manager.save(slot, state, elapsed_seconds=int(state.demo_elapsed_s))
        state.status_messages.append(f">>> Auto-saved to slot {slot}")
    except Exception:
        # Silent failure — auto-save is best-effort
        pass


def advance_to_reward(state: AppState) -> None:
    """Move from JACK_OUT to REWARD stage.

    Called when the player dismisses the jack out animation.
    Advances the run state and transitions to the reward screen.
    """
    if state.run_state is None:
        return
    if state.run_state.current_stage is not Stage.JACK_OUT:
        return

    # Advance run state
    state.run_state.mark_advance()
    # Now in REWARD stage
    state.status_messages.append(">>> Mission rewards calculated.")

    # Switch to reward screen
    from . import reward_view

    reward_view.enter_reward(state)


# --- Rendering ---


def render_jack_out(console: tcod.console.Console, state: AppState) -> None:
    """Render the Jack Out screen.

    Animates through frames over time, then shows a "press any key" prompt.
    """
    SCREEN_WIDTH = _engine_config.SCREEN_WIDTH  # noqa: N806
    SCREEN_HEIGHT = _engine_config.SCREEN_HEIGHT  # noqa: N806

    console.clear(bg=(0, 0, 0))

    # Determine current frame based on time
    started = getattr(state, "jack_out_started_at", None)
    if started is None:
        state.jack_out_started_at = time.monotonic()
        started = state.jack_out_started_at
    elapsed = time.monotonic() - started
    frame_idx = min(int(elapsed / _FRAME_DURATION_S), len(_ANIMATION_FRAMES) - 1)

    # Get frame
    frame = _ANIMATION_FRAMES[frame_idx]
    state.jack_out_frame_index = frame_idx

    # Render frame
    start_y = SCREEN_HEIGHT // 2 - len(frame) // 2 - 2
    for i, line in enumerate(frame):
        console.print(
            x=(SCREEN_WIDTH - len(line)) // 2,
            y=start_y + i,
            string=line,
            fg=(100, 200, 255) if frame_idx < len(_ANIMATION_FRAMES) - 1 else (0, 255, 100),
        )

    # Stage title
    title = "JACKING OUT"
    console.print(
        x=(SCREEN_WIDTH - len(title)) // 2,
        y=2,
        string=title,
        fg=(0, 200, 200),
    )

    # Status message
    if frame_idx < len(_ANIMATION_FRAMES) - 1:
        msg = f"Disconnecting... ({frame_idx + 1}/{len(_ANIMATION_FRAMES)})"
        console.print(
            x=(SCREEN_WIDTH - len(msg)) // 2,
            y=SCREEN_HEIGHT - 6,
            string=msg,
            fg=(150, 150, 150),
        )
    else:
        # Final frame: show "press any key" prompt
        prompt1 = "▼ Neural connection severed"
        prompt2 = "[ANY KEY] Continue to rewards"
        console.print(
            x=(SCREEN_WIDTH - len(prompt1)) // 2,
            y=SCREEN_HEIGHT - 8,
            string=prompt1,
            fg=(0, 255, 150),
        )
        console.print(
            x=(SCREEN_WIDTH - len(prompt2)) // 2,
            y=SCREEN_HEIGHT - 6,
            string=prompt2,
            fg=(200, 200, 200),
        )

    # Status panel
    if state.status_messages:
        for i, msg in enumerate(state.status_messages[-3:]):
            console.print(
                x=2,
                y=SCREEN_HEIGHT - 3 + i,
                string=msg,
                fg=(120, 120, 120),
            )


# --- Input ---


def handle_jack_out_input(
    event: tcod.event.Event,
    state: AppState,
) -> bool:
    """Handle input on the Jack Out screen.

    Any key advances to REWARD stage. Returns False to quit.
    """
    if not isinstance(event, tcod.event.KeyDown):
        return True

    # Q quits
    if event.sym is tcod.event.KeySym.Q:
        return False

    # ESC also quits
    if event.sym is tcod.event.KeySym.ESCAPE:
        return False

    # Any other key advances
    # But wait until animation completes (final frame)
    started = getattr(state, "jack_out_started_at", None)
    if started is not None:
        elapsed = time.monotonic() - started
        if elapsed < (len(_ANIMATION_FRAMES) - 1) * _FRAME_DURATION_S:
            # Still animating — don't advance yet
            return True

    # Animation complete (or no timer) — advance
    advance_to_reward(state)
    return True

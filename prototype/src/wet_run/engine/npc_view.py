"""NPC event screen: render and handle NPC dialogues.

A dedicated screen for NPC encounters with dialogue trees and player choices.
"""

from __future__ import annotations

from typing import Any

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..i18n import Translator
from .input_utils import is_confirm_key
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_title,
    make_shell,
)
from .npc_event import ChoiceEffect, DialogueChoice, NPCState
from .state import AppState, ScreenKind
from .status_panel import render_status_panel


def render_npc(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    npc_state: NPCState,
) -> None:
    """Render the NPC event screen."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    # Title
    draw_title(
        console,
        title_r,
        title=f"NPC ENCOUNTER — {npc_state.event.npc_name}",
        subtitle=npc_state.event.description,
    )

    # Persistent status panel
    render_status_panel(console, state, panel_r)

    # Main area: dialogue
    _draw_dialogue(console, main_r, npc_state, state)

    # Controls
    draw_controls(
        console,
        ctrl_r,
        lines=[
            "↑↓ Select Choice  ENTER Confirm  ESC Leave",
            "1-9 Quick Select",
        ],
    )

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s",
        status_messages=state.status_messages,
    )


def _draw_dialogue(
    console: tcod.console.Console,
    main: Region,
    npc_state: NPCState,
    state: AppState,
) -> None:
    """Draw the current dialogue line and choices."""
    line = npc_state.event.get_line(npc_state.current_line_index)
    if line is None:
        return

    x = main.x + 2
    y = main.y + 1
    y = _draw_dialogue_header(console, main, line, x, y)
    y = _draw_dialogue_text(console, main, line.text, x, y, (200, 200, 200))
    y = _draw_dialogue_korean(console, main, line, x, y)
    _draw_dialogue_choices_or_prompt(console, main, line, state, x, y)


# ------------------------------------------------------------------
# _draw_dialogue helpers
# ------------------------------------------------------------------


def _draw_dialogue_header(
    console: tcod.console.Console, main: Region, line: Any, x: int, y: int
) -> int:
    """Render the NPC portrait + speaker name + separator.

    Returns the y-row just past the separator.
    """
    if not line.portrait:
        return y
    console.print(x=x, y=y, string=line.portrait, fg=(0, 255, 255))
    # Use Korean speaker name if available
    from . import config
    from .font_loader import is_korean_capable

    speaker_name = line.speaker
    if (
        config.LANGUAGE_MODE in ("ko", "both")
        and is_korean_capable()
        and hasattr(line, "speaker_ko")
        and line.speaker_ko
    ):
        speaker_name = f"{line.speaker} ({line.speaker_ko})"
    console.print(x=x + 5, y=y, string=speaker_name, fg=(255, 255, 0))
    y += 1
    console.print(x=x, y=y, string="=" * (main.w - 4), fg=(80, 80, 80))
    y += 2
    return y


def _draw_dialogue_text(
    console: tcod.console.Console, main: Any, text: str, x: int, y: int, color: tuple[int, int, int]
) -> int:
    """Word-wrap and print a single dialogue paragraph.  Returns new y."""
    max_width = main.w - 6
    for line_text in _wrap_text(text, max_width):
        console.print(x=x, y=y, string=line_text, fg=color)
        y += 1
    return y + 1


def _draw_dialogue_korean(
    console: tcod.console.Console, main: Any, line: Any, x: int, y: int
) -> int:
    """Render the Korean subtitle (if enabled, font supports it, and
    the line has a translation).  Returns the new y-row."""
    from . import config
    from .font_loader import is_korean_capable

    if not (config.LANGUAGE_MODE in ("ko", "both") and is_korean_capable() and line.text_ko):
        return y
    return (
        _draw_dialogue_text(
            console,
            main,
            line.text_ko,
            x,
            y,
            (255, 220, 100),
        )
        + 1
    )


def _draw_dialogue_choices_or_prompt(
    console: tcod.console.Console, main: Any, line: Any, state: AppState, x: int, y: int
) -> None:
    """Draw the player-choice list (with faction-gate filtering) or
    a generic continue prompt if the line has no choices.
    """
    if not line.choices:
        y += 1
        console.print(
            x=x,
            y=y,
            string=">> Press any key to continue...",
            fg=(128, 128, 128),
        )
        return

    from . import config
    from .font_loader import is_korean_capable

    # Phase 6+: filter choices by faction rep gate. Choices whose
    # `faction_gate` is set and doesn't match the current player
    # reputation are hidden from the menu.
    reputation = getattr(state, "reputation", None)
    visible_choices: list[DialogueChoice] = [c for c in line.choices if c.is_available(reputation)]

    if not visible_choices:
        # All choices were filtered out — show a locked message.
        console.print(
            x=x,
            y=y,
            string="[dialogue locked — faction standing required]",
            fg=(140, 100, 100),
        )
        return

    console.print(x=x, y=y, string="What do you say?", fg=(180, 180, 180))
    y += 2

    # Initialize selection index
    if not hasattr(state, "npc_choice_index"):
        state.npc_choice_index = 0

    for i, choice in enumerate(visible_choices):
        is_selected = i == state.npc_choice_index
        cursor = ">" if is_selected else " "
        fg = (0, 255, 255) if is_selected else (200, 200, 200)
        # Use Korean if available
        choice_text = choice.text
        if config.LANGUAGE_MODE == "ko" and choice.text_ko and is_korean_capable():
            choice_text = choice.text_ko
        # Show a small tag for faction-gated choices.
        gate_tag = ""
        if choice.faction_gate is not None:
            gate_tag = f" [{choice.faction_gate.value}/{choice.min_tier or '?'}]"
        console.print(
            x=x,
            y=y + i,
            string=f"  {cursor} [{choice.key}] {choice_text}{gate_tag}",
            fg=fg,
        )


def _wrap_text(text: str, max_width: int) -> list[str]:
    """Word-wrap helper shared by the EN/KO dialogue renderers."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_width:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word) if current else word
    if current:
        lines.append(current)
    return lines


def handle_npc_input(
    event: tcod.event.Event,
    state: AppState,
    npc_state: NPCState,
) -> bool:
    """Handle input on NPC screen. Returns False to quit."""
    if not isinstance(event, KeyDown):
        return True

    if event.sym is KeySym.Q:
        return False

    if event.sym is KeySym.ESCAPE:
        # Leave NPC encounter
        npc_state.finished = True
        state.status_messages.append(">>> Left NPC encounter")
        state.screen = ScreenKind.MATRIX
        return True

    line = npc_state.event.get_line(npc_state.current_line_index)
    if line is None:
        return True

    # Phase 6+: filter choices by faction rep gate so the index space
    # matches the visible list drawn by `_draw_dialogue`.

    reputation = getattr(state, "reputation", None)
    visible_choices: list[DialogueChoice] = [c for c in line.choices if c.is_available(reputation)]

    # Initialize choice index
    if not hasattr(state, "npc_choice_index"):
        state.npc_choice_index = 0

    # Navigation
    if event.sym is KeySym.UP:
        if visible_choices:
            state.npc_choice_index = max(0, state.npc_choice_index - 1)
            safe_play("ui/menu_select")
        return True

    if event.sym is KeySym.DOWN:
        if visible_choices:
            state.npc_choice_index = min(len(visible_choices) - 1, state.npc_choice_index + 1)
        return True

    # Confirm with ENTER or SPACE
    if is_confirm_key(event.sym):
        if visible_choices and 0 <= state.npc_choice_index < len(visible_choices):
            safe_play("ui/menu_confirm")
            _execute_choice(state, npc_state, visible_choices[state.npc_choice_index])
        else:
            safe_play("story/dialogue_advance")
            _advance_dialogue(state, npc_state)
        return True

    # Quick select with number key
    if visible_choices and event.sym.name.startswith("N"):
        try:
            num = int(event.sym.name[1:])
            if 1 <= num <= len(visible_choices):
                _execute_choice(state, npc_state, visible_choices[num - 1])
        except (ValueError, IndexError):
            pass
        return True

    return True


def _execute_choice(state: AppState, npc_state: NPCState, choice: DialogueChoice) -> None:
    """Execute a player choice."""
    state.status_messages.append(f">>> {choice.text}")

    if choice.log_message:
        state.status_messages.append(f">>> {choice.log_message}")

    # Handle effect
    if choice.effect is ChoiceEffect.GOODBYE:
        npc_state.finished = True
        state.screen = ScreenKind.MATRIX
        state.npc_state = None
    elif choice.effect is ChoiceEffect.GAIN_INFO and "info" in choice.effect_data:
        info = choice.effect_data["info"]
        state.status_messages.append(f">>> Learned: {info}")
        _advance_dialogue(state, npc_state)
    elif choice.effect is ChoiceEffect.CONTINUE:
        if choice.response:
            state.status_messages.append(f">>> {npc_state.event.npc_name}: {choice.response}")
        _advance_dialogue(state, npc_state)
    else:
        _advance_dialogue(state, npc_state)

    # If dialogue ended naturally, clear npc_state
    if npc_state.finished and state.screen is ScreenKind.MATRIX:
        state.npc_state = None
        # Check for event story trigger after NPC dialogue
        _check_post_npc_event(state, npc_state)


def _check_post_npc_event(state: AppState, npc_state: NPCState) -> None:
    """Check if an event story should trigger after NPC dialogue."""
    from .event_story import EventRegistry, EventState, EventTrigger, check_event_trigger

    if not hasattr(state, "_event_registry") or state._event_registry is None:
        state._event_registry = EventRegistry()

    event = check_event_trigger(
        state,
        registry=state._event_registry,
        trigger=EventTrigger.NPC_GREETING,
        trigger_id=npc_state.event.id,
    )
    if event is not None:
        state.active_event = EventState(event=event)
        state.screen = ScreenKind.EVENT


def _advance_dialogue(state: AppState, npc_state: NPCState) -> None:
    """Advance to next dialogue line."""
    line = npc_state.event.get_line(npc_state.current_line_index)
    if line is None:
        return

    if line.next_line_index is not None:
        npc_state.current_line_index = line.next_line_index
    elif npc_state.current_line_index + 1 < len(npc_state.event.lines):
        npc_state.current_line_index += 1
    else:
        # End of dialogue
        npc_state.finished = True
        state.screen = ScreenKind.MATRIX

        # Advance RunState: if we're on MEET_NPC stage, talking to
        # the NPC satisfies the objective.
        from ..run import check_npc_talk_complete, ensure_run_state

        run_state = ensure_run_state(state)
        if check_npc_talk_complete(run_state):
            run_state.mark_advance()
            state.status_messages.append(f">>> Stage complete: {run_state.current_info().title}")

    # Reset choice index
    state.npc_choice_index = 0

"""Event Story view: cinematic scene with character art.

Renders large ASCII character art alongside multi-line dialogue.
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..i18n import Translator
from .event_story import CharacterArt, EventChoice, EventLine, EventState
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
from .state import AppState, ScreenKind


def render_event_story(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    event_state: EventState,
) -> None:
    """Render the event story screen with character art."""
    event = event_state.event
    current_line = event.get_line(event_state.current_line_index)
    if current_line is None:
        return

    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    # Clear
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    # Title
    draw_title(
        console,
        title_r,
        title=f"━━ {event.title} ━━",
        subtitle=event.description,
    )

    # Main area: split into art (left) and dialogue (right)
    _render_event_main(console, main_r, event_state)

    # Controls
    if current_line.choices:
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "↑↓ Select Choice  ENTER/SPACE Confirm",
                "1-9 Quick select  ESC Skip",
            ],
        )
    else:
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "ENTER/SPACE Continue  ESC Skip",
                "Q Quit",
            ],
        )

    # Footer
    draw_footer(
        console,
        foot_r,
        text=f"Event {event_state.current_line_index + 1}/{len(event.lines)}",
        status_messages=state.status_messages,
    )


def _render_event_main(
    console: tcod.console.Console,
    main: Region,
    event_state: EventState,
) -> None:
    """Render the main area with art + dialogue."""
    event = event_state.event
    line = event.get_line(event_state.current_line_index)
    if line is None:
        return

    # Layout: art on left, text on right
    art_width = 22
    text_x = main.x + 2 + art_width + 2
    text_width = main.w - art_width - 6

    # Draw art (if any)
    if line.art is not None:
        _draw_character_art(
            console,
            x=main.x + 2,
            y=main.y + 1,
            art=line.art,
            max_height=min(15, main.h - 4),
        )

    # Draw dialogue
    _draw_dialogue(
        console,
        x=text_x,
        y=main.y + 1,
        max_width=text_width,
        line=line,
    )

    # Draw choices if any
    if line.choices:
        _draw_choices(
            console,
            x=text_x,
            y=main.y + main.h - len(line.choices) - 3,
            max_width=text_width,
            line=line,
            event_state=event_state,
        )


def _draw_character_art(
    console: tcod.console.Console,
    x: int,
    y: int,
    art: CharacterArt,
    max_height: int,
) -> None:
    """Draw the large character art."""
    color = art.color_hint
    # Draw each line of art
    for i, line in enumerate(art.art_lines):
        if i >= max_height:
            break
        # Center the art
        art_x = x + (20 - len(line)) // 2
        if art_x < 0:
            art_x = x
        console.print(
            x=art_x,
            y=y + i,
            string=line,
            fg=color,
        )

    # Character name
    name_y = y + len(art.art_lines) + 1
    if name_y < y + max_height:
        console.print(
            x=x + 2,
            y=name_y,
            string=f"── {art.character_id.upper()} ──",
            fg=color,
        )


def _draw_dialogue(
    console: tcod.console.Console,
    x: int,
    y: int,
    max_width: int,
    line: EventLine,
) -> None:
    """Draw the dialogue text with effects."""
    # Speaker
    if line.speaker and line.portrait:
        console.print(
            x=x,
            y=y,
            string=f"{line.portrait} {line.speaker}:",
            fg=(255, 255, 0),
        )
    elif line.speaker:
        console.print(
            x=x,
            y=y,
            string=f"{line.speaker}:",
            fg=(255, 255, 0),
        )

    # Korean speaker (if available)
    if line.speaker_ko and line.speaker_ko != line.speaker:
        console.print(
            x=x,
            y=y + 1,
            string=f"   {line.speaker_ko}",
            fg=(200, 200, 100),
        )

    text_y = y + 3

    # Text (English)
    if line.text:
        _draw_text_wrapped(
            console,
            x=x,
            y=text_y,
            text=line.text,
            max_width=max_width,
            color=_get_text_color(line.effect),
        )
        text_y += _count_wrapped_lines(line.text, max_width) + 1

    # Korean text
    if line.text_ko and line.text_ko != line.text:
        text_y += 1
        _draw_text_wrapped(
            console,
            x=x,
            y=text_y,
            text=line.text_ko,
            max_width=max_width,
            color=(255, 220, 100),
        )

    # Effect indicator
    if line.effect and line.effect != "none":
        effect_y = text_y + _count_wrapped_lines(line.text_ko or line.text, max_width) + 2
        if effect_y < main_height(console):
            console.print(
                x=x,
                y=effect_y,
                string=f"[{line.effect.upper()}]",
                fg=(200, 200, 200),
            )


def main_height(console: tcod.console.Console) -> int:
    """Get console height."""
    return console.height


def _get_text_color(effect: str) -> tuple[int, int, int]:
    """Get text color based on effect."""
    if effect == "glitch":
        return (200, 200, 255)
    elif effect == "type":
        return (200, 200, 200)
    return (255, 255, 255)


def _draw_text_wrapped(
    console: tcod.console.Console,
    x: int,
    y: int,
    text: str,
    max_width: int,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Draw text with word wrapping."""
    if not text:
        return
    words = text.split()
    current_line = ""
    current_y = y

    for word in words:
        if len(current_line) + len(word) + 1 > max_width:
            if current_line:
                console.print(
                    x=x,
                    y=current_y,
                    string=current_line,
                    fg=color,
                )
                current_y += 1
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word

    if current_line:
        console.print(
            x=x,
            y=current_y,
            string=current_line,
            fg=color,
        )


def _count_wrapped_lines(text: str, max_width: int) -> int:
    """Count how many lines text will wrap to."""
    if not text:
        return 0
    words = text.split()
    lines = 1
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_width:
            lines += 1
            current_len = len(word)
        else:
            current_len += len(word) + 1
    return lines


def _draw_choices(
    console: tcod.console.Console,
    x: int,
    y: int,
    max_width: int,
    line: EventLine,
    event_state: EventState,
) -> None:
    """Draw the dialogue choices."""
    console.print(x=x, y=y - 1, string="─" * max_width, fg=(80, 80, 80))

    for i, choice in enumerate(line.choices):
        is_selected = i == event_state.choice_index
        cursor = "▶" if is_selected else " "
        fg = (0, 255, 255) if is_selected else (200, 200, 200)

        # Choice text
        console.print(
            x=x,
            y=y + i,
            string=f"{cursor} [{choice.key}] {choice.text}",
            fg=fg,
        )

        # Korean
        if choice.text_ko and choice.text_ko != choice.text:
            console.print(
                x=x + 4,
                y=y + i + 1 if i < len(line.choices) - 1 else y + i,
                string=f"     {choice.text_ko}",
                fg=(180, 180, 100),
            )


def handle_event_input(
    event: tcod.event.Event,
    state: AppState,
    event_state: EventState,
) -> bool:
    """Handle input on event story screen. Returns False to quit."""
    if not isinstance(event, KeyDown):
        return True

    if event.sym is KeySym.Q:
        return False
    if event.sym is KeySym.ESCAPE:
        # Skip event
        _complete_event(state, event_state)
        return True

    current_line = event_state.event.get_line(event_state.current_line_index)
    if current_line is None:
        return True

    if current_line.choices:
        # Navigate choices
        if event.sym is KeySym.UP:
            event_state.choice_index = max(0, event_state.choice_index - 1)
            return True
        if event.sym is KeySym.DOWN:
            event_state.choice_index = min(
                len(current_line.choices) - 1,
                event_state.choice_index + 1,
            )
            return True
        # Confirm
        if is_confirm_key(event.sym):
            if 0 <= event_state.choice_index < len(current_line.choices):
                _execute_choice(state, event_state, current_line.choices[event_state.choice_index])
            return True
        # Quick select
        if event.sym.name.startswith("N"):
            try:
                num = int(event.sym.name[1:])
                if 1 <= num <= len(current_line.choices):
                    _execute_choice(state, event_state, current_line.choices[num - 1])
            except (ValueError, IndexError):
                pass
            return True
    else:
        # Just continue
        if is_confirm_key(event.sym):
            _advance_event(state, event_state)
            return True

    return True


def _execute_choice(
    state: AppState,
    event_state: EventState,
    choice: EventChoice,
) -> None:
    """Execute a player choice in event story."""
    if hasattr(state, "status_messages"):
        state.status_messages.append(f">>> Event: {choice.text}")

    # Apply rewards
    if choice.grants_credits > 0:
        if not hasattr(state, "inventory") or state.inventory is None:
            state.inventory = {}
        # No direct credits field; could add later
        state.status_messages.append(f">>> +{choice.grants_credits} credits")

    if choice.grants_item:
        if not hasattr(state, "inventory") or state.inventory is None:
            state.inventory = {}
        state.inventory[choice.grants_item] = state.inventory.get(choice.grants_item, 0) + 1
        state.status_messages.append(f">>> +1 {choice.grants_item}")

    # Advance
    if choice.next_line_index is not None:
        event_state.current_line_index = choice.next_line_index
        event_state.choice_index = 0
    else:
        _advance_event(state, event_state)


def _advance_event(state: AppState, event_state: EventState) -> None:
    """Advance to next line or end event."""
    event_state.current_line_index += 1
    if event_state.current_line_index >= len(event_state.event.lines):
        _complete_event(state, event_state)
    else:
        event_state.choice_index = 0


def _complete_event(state: AppState, event_state: EventState) -> None:
    """Complete the event story."""
    event = event_state.event
    event_state.finished = True

    # Mark as shown
    if not hasattr(state, "shown_events"):
        state.shown_events = set()
    state.shown_events.add(event.id)

    # Set flag
    if event.set_flag is not None:
        if not hasattr(state, "story_flags"):
            state.story_flags = set()
        state.story_flags.add(event.set_flag)

    # Return to previous screen
    if hasattr(state, "active_event"):
        state.active_event = None
    state.screen = ScreenKind.MATRIX
    if hasattr(state, "status_messages"):
        state.status_messages.append(f">>> Event '{event.title}' completed")

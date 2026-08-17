"""Combat view input handling (ADR-0113 module split).

Extracted from combat_view.py to reduce the rendering module below
the 1000+ LOC threshold. Handles keyboard input for the Combat
screen — skill navigation, skill activation, disengage, and
number-key shortcuts.

Public API (preserved from combat_view.py):
- handle_combat_input: Main entry point for tcod KeyDown events

Internal helpers (private):
- _handle_combat_disengage: ESC — flee the encounter
- _handle_combat_skill_navigation: UP/DOWN — move skill highlight
- _handle_combat_skill_activation: ENTER/SPACE — use highlighted skill
- _handle_combat_number_key: 1..9 — direct skill shortcut
- _COMBAT_NUMBER_KEYS: frozenset of numeric KeySym shortcuts
"""

from __future__ import annotations

import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..combat.state import CombatState
from . import combat_view
from .input_utils import is_confirm_key
from .state import AppState

# Direct numeric-key shortcuts (1..9) in a frozenset for fast lookup.
_COMBAT_NUMBER_KEYS = frozenset(
    {
        KeySym.N1,
        KeySym.N2,
        KeySym.N3,
        KeySym.N4,
        KeySym.N5,
        KeySym.N6,
        KeySym.N7,
        KeySym.N8,
        KeySym.N9,
    }
)


def _handle_combat_disengage(state: AppState, combat_state: CombatState) -> bool:
    """Handle ESC — flee the encounter."""
    safe_play("ui/menu_cancel")
    if not combat_state.finished:
        combat_state.finished = True
        combat_state.outcome = "defeat"
        combat_state.push(">> You disengage. The ICE holds.")
    combat_view._end_combat(state, combat_state)
    return True


def _handle_combat_skill_navigation(
    state: AppState,
    combat_state: CombatState,
    delta: int,
) -> bool:
    """Move the highlighted skill slot up (delta<0) or down (delta>0)."""
    safe_play("ui/menu_select")
    old_idx = state.combat_skill_index
    if delta < 0:
        state.combat_skill_index = max(0, state.combat_skill_index - 1)
    else:
        max_idx = len(combat_state.player.skills) - 1
        state.combat_skill_index = min(max_idx, state.combat_skill_index + 1)
    if old_idx != state.combat_skill_index:
        skill = combat_state.player.skills[state.combat_skill_index]
        state.status_messages.append(f">>> Selected: {skill.name}")
    return True


def _handle_combat_skill_activation(
    state: AppState,
    combat_state: CombatState,
) -> bool:
    """Try to use the highlighted skill (with AP / cooldown checks)."""
    idx = state.combat_skill_index
    if not (0 <= idx < len(combat_state.player.skills)):
        return True
    skill = combat_state.player.skills[idx]
    if combat_view._can_use_skill(combat_state, skill):
        combat_view._execute_skill(state, combat_state, skill)
    else:
        combat_view._report_skill_unavailable(state, combat_state, skill)
    return True


def _handle_combat_number_key(
    state: AppState,
    combat_state: CombatState,
    sym: KeySym,
) -> None:
    """Legacy direct-number shortcut — pick the Nth skill (1-indexed)."""
    if combat_state.finished:
        return
    idx = int(sym.name[1:]) - 1
    if not (0 <= idx < len(combat_state.player.skills)):
        return
    skill = combat_state.player.skills[idx]
    combat_view._execute_skill(state, combat_state, skill)


def handle_combat_input(
    event: tcod.event.Event,
    state: AppState,
    combat_state: CombatState,
) -> bool:
    """Handle input on the Combat screen. Returns False to quit."""
    if not isinstance(event, KeyDown):
        return True

    # Phase E-2: first-combat tutorial dismissed on Space/Enter
    if getattr(state, "show_first_combat_tutorial", False) and event.sym in (
        KeySym.SPACE,
        KeySym.RETURN,
    ):
        state.show_first_combat_tutorial = False
        state.status_messages.append(">>> Tutorial dismissed. Good luck, cowboy.")
        return True

    # System keys (quit / escape / continue) have priority.
    if event.sym is KeySym.Q:
        return False
    if event.sym is KeySym.ESCAPE:
        return _handle_combat_disengage(state, combat_state)
    if is_confirm_key(event.sym) and combat_state.finished:
        safe_play("ui/menu_confirm")
        combat_view._end_combat(state, combat_state)
        return True

    if not combat_state.finished:
        if event.sym is KeySym.UP:
            return _handle_combat_skill_navigation(state, combat_state, -1)
        if event.sym is KeySym.DOWN:
            return _handle_combat_skill_navigation(state, combat_state, +1)
        if is_confirm_key(event.sym):
            return _handle_combat_skill_activation(state, combat_state)
        if event.sym in _COMBAT_NUMBER_KEYS:
            _handle_combat_number_key(state, combat_state, event.sym)
            return True

    return True


__all__ = ["handle_combat_input"]

"""Action Menu: node interaction popup (Phase 5+).

When the player presses ENTER on a node in the Matrix, this menu appears
showing available actions based on the node kind.

Actions by node kind (hacking.md):
  - DATA: SCAN → EXTRACT (mission objective)
  - ICE: SCAN → ENGAGE (combat)
  - EXIT: SCAN → JACK OUT (leave matrix)
  - ROUTER: SCAN → MOVE (pass-through)
  - SYSTEM: SCAN → HACK (Phase 6+)
  - CONSTRUCT: SCAN → COMMUNICATE (Phase 6+)
  - CORE: SCAN → ACCESS (Phase 6+)

Navigation: Arrow keys (↑/↓) to select, ENTER to confirm, ESC to cancel.
"""

from __future__ import annotations

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..audio import safe_play
from ..combat.registry import IceRegistry, ProgramRegistry
from ..i18n import Translator
from ..matrix.node import Node, NodeKind
from . import combat_view, hacking_view
from .input_utils import is_confirm_key
from .layout import Region, clear_region
from .npc_event import DIXIE_FLATLINE_EVENT, NPCState
from .state import AppState, ScreenKind


def render_action_menu(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    node: Node,
    menu_region: Region,
) -> None:
    """Render the action menu popup for the given node.

    The menu_region should be a centered box in the main area (e.g., 40x10).
    """
    clear_region(console, menu_region)

    # Draw box border
    _draw_box_border(console, menu_region)

    # Title
    x = menu_region.x + 2
    y = menu_region.y + 1
    console.print(x=x, y=y, string=f"=== {node.label} ===", fg=(255, 255, 255))
    y += 1
    console.print(x=x, y=y, string=f"Kind: {node.kind.value}", fg=(180, 180, 180))
    y += 2

    # Actions (based on node kind)
    actions = _get_actions(node)
    selected_index = getattr(state, "action_menu_index", 0)

    for i, (key, label, action_id) in enumerate(actions):
        is_selected = i == selected_index
        is_disabled = _is_action_disabled(action_id, node, state)

        # Visual indicators
        cursor = ">" if is_selected else " "

        # Color coding
        if is_disabled:
            fg = (80, 80, 80)  # Dark gray for disabled
            label_with_status = f"{label} [LOCKED]"
        elif is_selected:
            fg = (0, 255, 255)  # Cyan for selected
            label_with_status = label
        else:
            fg = (200, 200, 200)  # Light gray for normal
            label_with_status = label

        console.print(x=x, y=y + i, string=f"{cursor} [{key}] {label_with_status}", fg=fg)

    # Footer
    y = menu_region.y + menu_region.h - 2
    console.print(x=x, y=y, string="↑↓ Select  ENTER Confirm  ESC Cancel", fg=(128, 128, 128))


def _draw_box_border(console: tcod.console.Console, region: Region) -> None:
    """Draw a simple ASCII box border around the region."""
    fg = (100, 100, 100)
    # Corners
    console.print(x=region.x, y=region.y, string="+", fg=fg)
    console.print(x=region.x2, y=region.y, string="+", fg=fg)
    console.print(x=region.x, y=region.y2, string="+", fg=fg)
    console.print(x=region.x2, y=region.y2, string="+", fg=fg)
    # Top and bottom
    for x in range(region.x + 1, region.x2):
        console.print(x=x, y=region.y, string="-", fg=fg)
        console.print(x=x, y=region.y2, string="-", fg=fg)
    # Left and right
    for y in range(region.y + 1, region.y2):
        console.print(x=region.x, y=y, string="|", fg=fg)
        console.print(x=region.x2, y=y, string="|", fg=fg)


def _get_actions(node: Node) -> list[tuple[str, str, str]]:
    """Return available actions for the node as (key, label, action_id)."""
    if node.kind is NodeKind.DATA:
        return [
            ("S", "SCAN — analyze node", "scan"),
            ("E", "EXTRACT — retrieve data", "extract"),
        ]
    if node.kind is NodeKind.ICE:
        return [
            ("S", "SCAN — analyze defenses", "scan"),
            ("E", "ENGAGE — combat", "engage"),
        ]
    if node.kind is NodeKind.EXIT:
        return [
            ("S", "SCAN — confirm exit", "scan"),
            ("J", "JACK OUT — leave matrix", "jack_out"),
        ]
    if node.kind is NodeKind.ROUTER:
        return [
            ("S", "SCAN — trace routes", "scan"),
            ("M", "MOVE — pass through", "move"),
        ]
    if node.kind is NodeKind.SYSTEM:
        return [
            ("S", "SCAN — probe system", "scan"),
            ("H", "HACK — intrude", "hack"),
        ]
    if node.kind is NodeKind.CONSTRUCT:
        return [
            ("S", "SCAN — identify construct", "scan"),
            ("C", "COMMUNICATE — interact", "communicate"),
        ]
    if node.kind is NodeKind.CORE:
        return [
            ("S", "SCAN — deep scan", "scan"),
            ("A", "ACCESS — core breach", "access"),
        ]
    # Entry or unknown
    return [
        ("S", "SCAN — scan node", "scan"),
    ]


def _is_action_disabled(action_id: str, node: Node, state: AppState) -> bool:
    """Check if an action is currently disabled (locked/unavailable)."""
    # Phase 6+ actions now have lightweight stubs that emit a status
    # message and (for hack/access) grant small rewards. They are no
    # longer locked — see _execute_action for the implementation.

    # EXTRACT requires node not already extracted
    if action_id == "extract":
        return getattr(node, "extracted", False)

    return False


def handle_action_menu_input(
    event: tcod.event.Event,
    state: AppState,
    node: Node,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> tuple[bool, bool]:
    """Handle input on the action menu.

    Returns (continue_running, close_menu).
    - continue_running: False = quit game
    - close_menu: True = close action menu and return to matrix
    """
    if not isinstance(event, KeyDown):
        return True, False

    if event.sym is KeySym.ESCAPE:
        safe_play("ui/menu_cancel")
        return True, True

    actions = _get_actions(node)

    # Initialize menu index if not set
    if not hasattr(state, "action_menu_index"):
        state.action_menu_index = 0

    # Arrow key navigation
    if event.sym is KeySym.UP:
        state.action_menu_index = max(0, state.action_menu_index - 1)
        safe_play("ui/menu_select")
        return True, False

    if event.sym is KeySym.DOWN:
        state.action_menu_index = min(len(actions) - 1, state.action_menu_index + 1)
        return True, False

    # ENTER or SPACE to confirm selected action
    if is_confirm_key(event.sym):
        if 0 <= state.action_menu_index < len(actions):
            _key, _label, action_id = actions[state.action_menu_index]
            # Check if disabled
            if not _is_action_disabled(action_id, node, state):
                _execute_action(state, node, action_id, prog_registry, ice_registry)
                state.action_menu_index = 0  # Reset for next time
                return True, True
        return True, False

    # Legacy: Direct key shortcuts still work
    action_map = {
        "S": KeySym.S,
        "E": KeySym.E,
        "J": KeySym.J,
        "M": KeySym.M,
        "H": KeySym.H,
        "C": KeySym.C,
        "A": KeySym.A,
    }
    for key, _label, action_id in actions:
        if event.sym == action_map.get(key):
            if not _is_action_disabled(action_id, node, state):
                _execute_action(state, node, action_id, prog_registry, ice_registry)
                state.action_menu_index = 0
                return True, True
            return True, False

    return True, False


def _execute_action(
    state: AppState,
    node: Node,
    action_id: str,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    """Execute the selected action."""
    if action_id == "scan":
        state.message = f"Scanned {node.label}: {node.kind.value}"
        state.status_messages.append(f">>> SCAN: {node.label} ({node.kind.value})")
    elif action_id == "extract":
        # Data extraction (mission objective)
        state.message = f"Extracted data from {node.label}!"
        state.status_messages.append(f">>> EXTRACT: Data retrieved from {node.label}")
        state.status_messages.append(">>> Gained: 1x Data Fragment")

        # Add to inventory
        if not hasattr(state, "inventory") or state.inventory is None:
            state.inventory = {}
        state.inventory["data_fragment"] = state.inventory.get("data_fragment", 0) + 1

        # Mark as extracted
        state.extracted_nodes.add(node.id)
        # Remove the data node from matrix
        from .combat_view import _remove_node_from_graph

        if state.matrix is not None:
            state.matrix = _remove_node_from_graph(state.matrix, node.id)
            state.status_messages.append(f">>> Data node [{node.id}] removed")
            # Move to a remaining neighbor
            if state.matrix is not None and len(state.matrix.nodes) > 0:
                state.current_node_id = state.matrix.entry_id

        # Progress mission objective (extract_data) and possibly complete mission
        from .mission_completion import update_mission_progress

        update_mission_progress(state, "extract_data", 1)

        # Advance RunState: if we're on EXTRACT_DATA stage, this
        # extraction satisfies the objective and we move forward.
        from ..run import check_extract_complete, ensure_run_state

        run_state = ensure_run_state(state)
        if check_extract_complete(run_state):
            run_state.mark_advance()
            state.status_messages.append(f">>> Stage complete: {run_state.current_info().title}")
    elif action_id == "engage":
        # Start combat (Phase 5: implemented)
        state.status_messages.append(f">>> ENGAGE: Initiating combat with {node.label}")
        _start_combat_transition(state, node, prog_registry, ice_registry)
    elif action_id == "jack_out":
        # Leave matrix - return to server browser if we have one
        state.status_messages.append(">>> JACK OUT: Disconnecting from server...")
        if hasattr(state, "world_map") and state.world_map is not None:
            state.screen = ScreenKind.CYBERSPACE_BROWSER
            state.status_messages.append(">>> Returned to server browser")
        else:
            state.screen = ScreenKind.HUB
        state.message = "Jacked out."
    elif action_id == "move":
        # Router pass-through (no-op)
        state.message = f"Passed through {node.label}."
        state.status_messages.append(f">>> MOVE: Passed through {node.label}")
    elif action_id == "hack":
        hacking_view.start_hack(state, node.label)
    elif action_id == "communicate":
        state.npc_state = NPCState(event=DIXIE_FLATLINE_EVENT)
        state.screen = ScreenKind.NPC
        state.action_menu_open = False
        state.status_messages.append(f">>> COMMUNICATE: {node.label} — opening dialog...")
    elif action_id == "access":
        # Phase 6 stub: CORE node — peek at the next objective.
        state.message = f"Core '{node.label}' exposes a route forward."
        state.status_messages.append(f">>> ACCESS: {node.label} — core reveals a route")
        # Reveal one unvisited node hint to the player.
        if state.matrix is not None:
            unvisited = [n for n in state.matrix.nodes if n.id not in state.extracted_nodes]
            if unvisited:
                hint = unvisited[0]
                state.context_hint = f"Next target: {hint.label} ({hint.id})"
    else:
        state.message = f"Unknown action: {action_id}"
        state.status_messages.append(f">>> ERROR: Unknown action {action_id}")


def _start_combat_transition(
    state: AppState,
    ice_node: Node,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    """Transition from Matrix to Combat screen."""
    combat_state = combat_view.start_combat(state, ice_node, prog_registry, ice_registry)
    state.combat_state = combat_state
    state.screen = ScreenKind.COMBAT
    state.message = ""

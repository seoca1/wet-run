"""Helpers for integrating RunState with AppState.

These functions handle the boilerplate of:
- Lazy-initializing ``state.run_state`` if it's None
- Starting a new run for a given mission
- Finding the next target node in the matrix for the active stage
- Detecting when a player's action satisfies the current stage's objective
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..matrix.node import NodeKind
from .state import (
    DEFAULT_FLOW,
    ObjectiveKind,
    RunState,
    Stage,
    get_mission_flow,
    get_next_stage_in_flow,
    get_stage_info,
    start_run,
    validate_stage_transition,
)

if TYPE_CHECKING:
    from ..engine.state import AppState
    from ..matrix.graph import MatrixGraph


# --- Re-exports ---

__all__ = [
    "DEFAULT_FLOW",
    "ensure_run_state",
    "start_new_run",
    "resolve_target_for_stage",
    "check_objective_at_node",
    "check_combat_victory",
    "check_extract_complete",
    "check_npc_talk_complete",
    "advance_stage",
    "get_mission_flow",
    "get_next_stage_in_flow",
    "get_stage_info",
    "validate_stage_transition",
]


# --- Run lifecycle ---


def ensure_run_state(state: AppState) -> RunState:
    """Get state.run_state, creating it if missing."""
    if state.run_state is None:
        state.run_state = start_run()
    return state.run_state


def start_new_run(state: AppState, mission_id: str = "first_jack") -> RunState:
    """Reset run state to start a new run for the given mission.

    Args:
        state: The app state.
        mission_id: The mission to start. Each mission has its own
            stage flow (see MISSION_FLOWS in state.py).

    Returns:
        The new RunState.
    """
    state.run_state = start_run(mission_id)
    return state.run_state


# --- Stage advancement ---


def advance_stage(run_state: RunState) -> Stage:
    """Advance to the next stage in the mission flow.

    Wraps RunState.mark_advance() and returns the NEW current stage
    (so callers can react to the transition).

    Returns the stage AFTER the advance. If the run was already at
    a terminal stage, returns the same stage.
    """
    run_state.mark_advance()
    return run_state.current_stage


# --- Target resolution ---


def resolve_target_for_stage(
    run_state: RunState,
    matrix: MatrixGraph | None,
) -> str | None:
    """Find the matrix node id that satisfies the current stage.

    For each objective kind, scans the matrix for the first matching node:
      - NPC → CONSTRUCT node
      - DATA → DATA node
      - ICE → ICE node
      - NONE → None (no target)

    Returns None if no matching node exists.
    """
    if matrix is None or not matrix.nodes:
        return None

    kind = run_state.objective_kind()
    target_kind: NodeKind | None = None
    if kind is ObjectiveKind.NPC:
        target_kind = NodeKind.CONSTRUCT
    elif kind is ObjectiveKind.DATA:
        target_kind = NodeKind.DATA
    elif kind is ObjectiveKind.ICE:
        target_kind = NodeKind.ICE
    else:
        return None

    for node in matrix.nodes:
        if node.kind is target_kind:
            return node.id
    return None


# --- Objective detection ---


def check_objective_at_node(
    run_state: RunState,
    node_id: str,
    matrix: MatrixGraph | None,
) -> bool:
    """Check if the player being at a given node satisfies the current stage.

    Returns True if the stage is now complete (call mark_advance next).
    """
    if matrix is None or not run_state.is_in_cyberspace():
        return False

    node = matrix.get(node_id)
    if node is None:
        return False

    kind = run_state.objective_kind()
    if kind is ObjectiveKind.NPC and node.kind is NodeKind.CONSTRUCT:
        return True
    if kind is ObjectiveKind.DATA and node.kind is NodeKind.DATA:
        return True
    if kind is ObjectiveKind.ICE and node.kind is NodeKind.ICE:
        return True
    return False


def check_combat_victory(run_state: RunState) -> bool:
    """Check if a combat victory satisfied the current stage.

    Used by the combat_view after a victory: if the stage was DEFEAT_ICE
    and the player won, the stage is complete.
    """
    return run_state.is_in_cyberspace() and run_state.objective_kind() is ObjectiveKind.ICE


def check_extract_complete(run_state: RunState) -> bool:
    """Check if a data extraction satisfied the current stage."""
    return run_state.is_in_cyberspace() and run_state.objective_kind() is ObjectiveKind.DATA


def check_npc_talk_complete(run_state: RunState) -> bool:
    """Check if talking to the NPC satisfied the current stage."""
    return run_state.is_in_cyberspace() and run_state.objective_kind() is ObjectiveKind.NPC


# --- Progress display ---


def get_progress_text(run_state: RunState) -> str:
    """Return a human-readable progress string for status panel.

    Example: "Stage 2/5 — Extract the Data"
    """
    total = run_state.stages_total()
    current = run_state.stages_completed() + (1 if run_state.is_in_progress() else 0)
    title = run_state.title()
    return f"Stage {current}/{total} — {title}"

"""Run state system — manages stage progression in a single playthrough.

Public API:
    Stage: Enum of stage values.
    ObjectiveKind: Enum of objective types.
    StageInfo: Static metadata for a stage.
    RunState: The state object tracking current stage.
    StageEvent: Lifecycle event (enter/exit/complete/failed).
    StageEventBus: Pub/sub for stage events.

    get_stage_info(stage): Get StageInfo for a stage.
    get_mission_flow(mission_id): Get the stage sequence for a mission.
    validate_stage_transition(from, to, mission): Check if valid.
    get_next_stage_in_flow(current, mission_id): Next stage in flow.

    start_run(mission_id, initial_stage): Create fresh RunState.
    start_new_run(state, mission_id): Reset app state's run.
    ensure_run_state(state): Get or create run_state.
    advance_stage(run_state): Advance to next stage.
    resolve_target_for_stage(run_state, matrix): Find target node.
    check_objective_at_node(run_state, node_id, matrix): Test stage completion.
    check_combat_victory(run_state): Test combat victory.
    check_extract_complete(run_state): Test extract complete.
    check_npc_talk_complete(run_state): Test NPC talk complete.
    get_progress_text(run_state): Formatted progress string.

    get_event_bus(): Get default StageEventBus.
    reset_event_bus(): Reset for testing.
"""

from .events import (
    StageEvent,
    StageEventBus,
    StageEventHandler,
    StageEventKind,
    get_event_bus,
    reset_event_bus,
)
from .helpers import (
    DEFAULT_FLOW,
    advance_stage,
    check_combat_victory,
    check_extract_complete,
    check_npc_talk_complete,
    check_objective_at_node,
    ensure_run_state,
    get_mission_flow,
    get_next_stage_in_flow,
    get_progress_text,
    get_stage_info,
    resolve_target_for_stage,
    start_new_run,
    validate_stage_transition,
)
from .state import (
    MISSION_FLOWS,
    ChapterState,
    ObjectiveKind,
    Phase,
    RunState,
    Stage,
    StageInfo,
    StageSequence,
    get_mission_stage_count,
    start_run,
)

__all__ = [
    # Enums
    "Stage",
    "Phase",
    "ChapterState",
    "ObjectiveKind",
    "StageEventKind",
    # Data classes
    "StageInfo",
    "RunState",
    "StageEvent",
    "StageEventBus",
    "StageEventHandler",
    "StageSequence",
    # Flow data
    "DEFAULT_FLOW",
    "MISSION_FLOWS",
    # State accessors
    "get_stage_info",
    "get_mission_flow",
    "get_mission_stage_count",
    "get_next_stage_in_flow",
    "validate_stage_transition",
    # Run lifecycle
    "start_run",
    "start_new_run",
    "ensure_run_state",
    "advance_stage",
    # Stage helpers
    "resolve_target_for_stage",
    "check_objective_at_node",
    "check_combat_victory",
    "check_extract_complete",
    "check_npc_talk_complete",
    "get_progress_text",
    # Event bus
    "get_event_bus",
    "reset_event_bus",
]

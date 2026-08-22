"""Run-state model definitions, stage metadata, and flow queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Stage(StrEnum):
    """Ordered stages of a single Run (aliased as Phase).

    Default first_jack mission flow (CONTENT_EXPANSION Phase B):
      PENDING → BRIEFING → TRAVEL → MEET_NPC →
      EXTRACT_DATA → BYPASS_SECURITY (optional) → DEFEAT_ICE →
      JACK_OUT → REWARD → DEBRIEF → COMPLETE

    Phase is the new canonical name; Stage is kept for backward compatibility.
    """

    PENDING = "pending"  # Run not started (Hub: waiting for mission accept)
    BRIEFING = "briefing"  # NPC (Finn, Dixie, ...) explains the job details
    TRAVEL = "travel"  # Jack-in animation / pre-matrix prep
    MEET_NPC = "meet_npc"  # Find and talk to a construct NPC
    EXTRACT_DATA = "extract_data"  # Find data node, extract payload
    BYPASS_SECURITY = "bypass_security"  # Optional: bypass a security layer
    DEFEAT_ICE = "defeat_ice"  # Find ICE node, win combat
    JACK_OUT = "jack_out"  # Disconnect from matrix (animation)
    REWARD = "reward"  # Show mission rewards
    DEBRIEF = "debrief"  # Optional narrative between COMPLETE and Hub
    COMPLETE = "complete"  # Run finished, return to hub
    DEATH_RESTART = "death_restart"  # After death, show restart option
    FAILED = "failed"  # Player flatlined
    # Phase 9: Salvation epilogue (ADR-0090)
    SALVATION_EPILOGUE = "salvation_epilogue"  # Epilogue scene playing
    # v0.5 expansion
    BLACKMARKET = "black_market"  # Hub: vendor for programs/deck upgrades
    GHOST_ENCOUNTER = "ghost_encounter"  # Matrix: Loa event in deep architecture


Phase = Stage


class ChapterState(StrEnum):
    """High-level story progression across a character Arc.

    Each Chapter may contain multiple Phases. The Arc starts at PROLOGUE,
    then cycles through IN_CHAPTER_N states. After the final chapter,
    the player reaches an ENDING. Phase 9 (Salvation) adds epilogue
    states for 9-character resolution.
    """

    PROLOGUE = "prologue"  # Character intro (cinematic text, no gameplay)
    IN_CHAPTER_1 = "in_chapter_1"
    CHAPTER_1_COMPLETE = "chapter_1_complete"
    IN_CHAPTER_2 = "in_chapter_2"
    CHAPTER_2_COMPLETE = "chapter_2_complete"
    IN_CHAPTER_3 = "in_chapter_3"
    CHAPTER_3_COMPLETE = "chapter_3_complete"
    IN_CHAPTER_4 = "in_chapter_4"
    CHAPTER_4_COMPLETE = "chapter_4_complete"
    IN_CHAPTER_5 = "in_chapter_5"
    CHAPTER_5_COMPLETE = "chapter_5_complete"
    # Phase 9: Salvation Phase epilogue states (ADR-0090)
    SALVATION_INTRO = "salvation_intro"  # Epilogue selection menu
    SALVATION_EPILOGUE = "salvation_epilogue"  # Epilogue scene playing
    SALVATION_DONE = "salvation_done"  # Epilogue complete, ready for ENDING
    ENDING_A = "ending_a"
    ENDING_B = "ending_b"
    ENDING_C = "ending_c"
    FINAL = "final"  # All epilogue/ending complete, return to Hub


class ObjectiveKind(StrEnum):
    """What kind of in-game action satisfies a Phase.

    Used to find the right node in the matrix and detect completion.
    """

    NPC = "npc"  # Node with kind=CONSTRUCT (talk to)
    DATA = "data"  # Node with kind=DATA (extract from)
    ICE = "ice"  # Node with kind=ICE (combat)
    NONE = "none"  # No specific target (e.g. PENDING, JACK_OUT, REWARD)


# --- Stage metadata ---


@dataclass(frozen=True, slots=True)
class StageInfo:
    """Static description of a stage.

    Attributes:
        stage: The Stage enum value.
        title: Short, human-readable title.
        objective_kind: What kind of action satisfies this stage.
        hint: Player-facing hint for the current stage.
        next_stage: The stage that follows this one in the mission flow.
        on_enter: Optional callback when entering this stage.
        on_exit: Optional callback when leaving this stage.
        ascii_art: Optional ASCII art displayed in the stage view.
    """

    stage: Stage
    title: str
    objective_kind: ObjectiveKind
    hint: str
    next_stage: Stage | None = None
    on_enter: str | None = None
    on_exit: str | None = None
    ascii_art: tuple[str, ...] = field(default_factory=tuple)


# --- Default mission flow (First Jack) ---


DEFAULT_FLOW: dict[Stage, StageInfo] = {
    Stage.PENDING: StageInfo(
        stage=Stage.PENDING,
        title="Awaiting Jack-In",
        objective_kind=ObjectiveKind.NONE,
        hint="Accept a mission at the Hub to begin.",
        next_stage=Stage.BRIEFING,
    ),
    Stage.BRIEFING: StageInfo(
        stage=Stage.BRIEFING,
        title="Mission Briefing",
        objective_kind=ObjectiveKind.NONE,
        hint="Listen to the fixer's briefing.",
        next_stage=Stage.TRAVEL,
        on_enter="The Finn leans back. 'Listen close, cowboy.'",
        ascii_art=(
            "  ┌──────────────────────────┐",
            "  │  ♠F♠ THE FINN'S OFFICE   │",
            "  │  ────────────────────    │",
            "  │  'Pay's in the credstick │",
            "  │   when the data's in     │",
            "  │   my hand. Don't die.'   │",
            "  └──────────────────────────┘",
        ),
    ),
    Stage.TRAVEL: StageInfo(
        stage=Stage.TRAVEL,
        title="Travel to Jack-In Point",
        objective_kind=ObjectiveKind.NONE,
        hint="Head to the jack-in spot.",
        next_stage=Stage.MEET_NPC,
        on_enter="Rain on the Chiba window. The deck hums warm.",
        ascii_art=(
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░  ◢◣  HEADING TO ▒░░░  ░",
            "  ░  ──  JACK-IN POINT ──  ░",
            "  ░  ░▒▓  CHIBA, 11LV  ▓▒░ ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        ),
    ),
    Stage.MEET_NPC: StageInfo(
        stage=Stage.MEET_NPC,
        title="Meet the Construct",
        objective_kind=ObjectiveKind.NPC,
        hint="Find and talk to the construct (Dixie Flatline).",
        next_stage=Stage.EXTRACT_DATA,
        on_enter="Dixie's voice crackles: 'Hey cowboy. Ready?'",
    ),
    Stage.EXTRACT_DATA: StageInfo(
        stage=Stage.EXTRACT_DATA,
        title="Extract the Data",
        objective_kind=ObjectiveKind.DATA,
        hint="Locate the data node and extract the payload.",
        next_stage=Stage.DEFEAT_ICE,
        on_enter="Data fragment detected. Locking on...",
    ),
    Stage.BYPASS_SECURITY: StageInfo(
        stage=Stage.BYPASS_SECURITY,
        title="Bypass Security",
        objective_kind=ObjectiveKind.NONE,
        hint="Slip past the corporate security layer.",
        next_stage=Stage.DEFEAT_ICE,
        on_enter="You ghost the Watchdog's patrol route. The blind spot lasts three seconds.",
    ),
    Stage.DEFEAT_ICE: StageInfo(
        stage=Stage.DEFEAT_ICE,
        title="Defeat the ICE",
        objective_kind=ObjectiveKind.ICE,
        hint="Engage and defeat the ICE protecting the data.",
        next_stage=Stage.JACK_OUT,
        on_enter="⚠ ICE detected. Combat initiated.",
    ),
    Stage.JACK_OUT: StageInfo(
        stage=Stage.JACK_OUT,
        title="Jack Out",
        objective_kind=ObjectiveKind.NONE,
        hint="Disconnecting from the matrix...",
        next_stage=Stage.REWARD,
        ascii_art=(
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░",
            "  ░  ── JACKING OUT ──     ░",
            "  ░  ░▒▓█             ▓▒░  ░",
            "  ░  ░▒▓█             ▓▒░  ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░",
        ),
    ),
    Stage.REWARD: StageInfo(
        stage=Stage.REWARD,
        title="Mission Rewards",
        objective_kind=ObjectiveKind.NONE,
        hint="Collect your rewards.",
        next_stage=Stage.COMPLETE,
        ascii_art=(
            "  ┌──────────────────────┐",
            "  │  ✓ MISSION COMPLETE  │",
            "  │  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣◢◣  │",
            "  │  ░▒▓ Credits  +500  ▓▒░  │",
            "  │  ░▒▓ Materials +2   ▓▒░  │",
            "  │  ░▒▓ Press ENTER    ▓▒░  │",
            "  └──────────────────────┘",
        ),
    ),
    Stage.DEBRIEF: StageInfo(
        stage=Stage.DEBRIEF,
        title="Debrief",
        objective_kind=ObjectiveKind.NONE,
        hint="Mission summary and intel unlocked.",
        next_stage=Stage.COMPLETE,
    ),
    Stage.COMPLETE: StageInfo(
        stage=Stage.COMPLETE,
        title="Run Complete",
        objective_kind=ObjectiveKind.NONE,
        hint="Mission complete. Return to hub for next job.",
        next_stage=None,
    ),
    Stage.DEATH_RESTART: StageInfo(
        stage=Stage.DEATH_RESTART,
        title="Restart",
        objective_kind=ObjectiveKind.NONE,
        hint="Press ENTER to restart, ESC to quit to menu.",
        next_stage=Stage.PENDING,
    ),
    Stage.FAILED: StageInfo(
        stage=Stage.FAILED,
        title="Flatline",
        objective_kind=ObjectiveKind.NONE,
        hint="Your run ended in cyberspace.",
        next_stage=Stage.DEATH_RESTART,
    ),
    # Phase 9: Salvation epilogue (ADR-0090)
    Stage.SALVATION_EPILOGUE: StageInfo(
        stage=Stage.SALVATION_EPILOGUE,
        title="Salvation Epilogue",
        objective_kind=ObjectiveKind.NONE,
        hint="Choose an epilogue character to play the final scene.",
        next_stage=Stage.SALVATION_EPILOGUE,
    ),
    Stage.BLACKMARKET: StageInfo(
        stage=Stage.BLACKMARKET,
        title="Black Market",
        objective_kind=ObjectiveKind.NONE,
        hint="Trade credits and materials for programs, deck upgrades, and intel.",
        next_stage=Stage.PENDING,
        on_enter="The back-alley vendor counts your creds twice. 'Cash only, cowboy.'",
        ascii_art=(
            "  ┌──────────────────────────┐",
            "  │  ░▒▓█  BLACK MARKET  █▓▒░  │",
            "  │  ────────────────────     │",
            "  │  'Cash, credits, code'    │",
            "  │   — the silent menu       │",
            "  │   of the Sprawl.         │",
            "  └──────────────────────────┘",
        ),
    ),
    Stage.GHOST_ENCOUNTER: StageInfo(
        stage=Stage.GHOST_ENCOUNTER,
        title="Loa Encounter",
        objective_kind=ObjectiveKind.NPC,
        hint="A ghost-god in the deep architecture. Talk, fight, or leave with empty hands.",
        next_stage=Stage.DEFEAT_ICE,
        on_enter="Something old. Something that has been waiting in the dark.",
        ascii_art=(
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░   ◢◣  GHOST  IN  ▒░░  ░",
            "  ░  ──  THE  MACHINE  ──  ░",
            "  ░  ░▒▓  IT  WATCHES  ▓▒░  ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
        ),
    ),
}


def get_stage_info(stage: Stage) -> StageInfo:
    """Return the StageInfo for a given Stage."""
    return DEFAULT_FLOW.get(
        stage,
        StageInfo(
            stage=stage, title=stage.value.title(), objective_kind=ObjectiveKind.NONE, hint=""
        ),
    )


# --- Per-mission stage flows ---


# Type alias for stage flow sequence
StageSequence = tuple[StageInfo, ...]


# Each mission has its own stage sequence.
# Watchdog Patrol skips EXTRACT_DATA (no data to extract).
# Ice Run has same flow as First Jack but different ICE count.
# Phase C-1: 3 canonical entries below; per-mission flows now live in
# missions.json `stage_flow` field (data-driven). The dict below is the
# fallback for missions that don't declare their own flow.
MISSION_FLOWS: dict[str, StageSequence] = {
    "first_jack": (
        DEFAULT_FLOW[Stage.BRIEFING],
        DEFAULT_FLOW[Stage.TRAVEL],
        DEFAULT_FLOW[Stage.MEET_NPC],
        DEFAULT_FLOW[Stage.EXTRACT_DATA],
        DEFAULT_FLOW[Stage.DEFEAT_ICE],
        DEFAULT_FLOW[Stage.JACK_OUT],
        DEFAULT_FLOW[Stage.REWARD],
        DEFAULT_FLOW[Stage.COMPLETE],
    ),
    "watchdog_patrol": (
        DEFAULT_FLOW[Stage.BRIEFING],
        DEFAULT_FLOW[Stage.TRAVEL],
        DEFAULT_FLOW[Stage.MEET_NPC],
        # No EXTRACT_DATA — pure combat mission; BYPASS_SECURITY flavor.
        DEFAULT_FLOW[Stage.BYPASS_SECURITY],
        DEFAULT_FLOW[Stage.DEFEAT_ICE],
        DEFAULT_FLOW[Stage.JACK_OUT],
        DEFAULT_FLOW[Stage.REWARD],
        DEFAULT_FLOW[Stage.COMPLETE],
    ),
    "ice_run": (
        DEFAULT_FLOW[Stage.BRIEFING],
        DEFAULT_FLOW[Stage.TRAVEL],
        DEFAULT_FLOW[Stage.MEET_NPC],
        DEFAULT_FLOW[Stage.EXTRACT_DATA],
        DEFAULT_FLOW[Stage.DEFEAT_ICE],
        DEFAULT_FLOW[Stage.JACK_OUT],
        DEFAULT_FLOW[Stage.REWARD],
        DEFAULT_FLOW[Stage.COMPLETE],
    ),
}


def _resolve_stage_flow_from_mission_data(
    mission_entry: dict[str, object] | None,
) -> StageSequence | None:
    """Phase C-1: read stage_flow from mission JSON if declared.

    Format: list[str] of Stage names (e.g. ["BRIEFING", "TRAVEL", ...]).
    Returns None if not declared or invalid.
    """
    if not isinstance(mission_entry, dict):
        return None
    raw = mission_entry.get("stage_flow")
    if not isinstance(raw, list):
        return None
    sequence: list[StageInfo] = []
    for name in raw:
        if not isinstance(name, str):
            return None
        try:
            stage = Stage(name.lower())
        except ValueError:
            return None
        info = DEFAULT_FLOW.get(stage)
        if info is None:
            return None
        sequence.append(info)
    return tuple(sequence) if sequence else None


def get_mission_flow(
    mission_id: str,
    missions_data: dict[str, dict[str, object]] | None = None,
) -> StageSequence:
    """Return the stage sequence for a given mission.

    Falls back to first_jack's flow if mission_id is unknown.
    Phase C-1: if missions_data is provided, check mission's
    `stage_flow` field before the MISSION_FLOWS dict.
    """
    if missions_data is not None:
        from_mission = _resolve_stage_flow_from_mission_data(missions_data.get(mission_id))
        if from_mission is not None:
            return from_mission
    return MISSION_FLOWS.get(mission_id, MISSION_FLOWS["first_jack"])


def get_mission_stage_count(mission_id: str) -> int:
    """Return the number of stages in a mission's flow."""
    return len(get_mission_flow(mission_id))


# --- Stage validation ---


def validate_stage_transition(
    from_stage: Stage,
    to_stage: Stage,
    mission_id: str,
) -> bool:
    """Check if a stage transition is valid for the given mission.

    A transition is valid if `to_stage` follows `from_stage` in the
    mission's flow, OR if `to_stage` is FAILED (which can happen from
    any non-terminal stage).

    Args:
        from_stage: Current stage.
        to_stage: Proposed next stage.
        mission_id: The mission context.

    Returns:
        True if the transition is valid.
    """
    # FAILED is reachable from any in-progress stage
    if to_stage is Stage.FAILED:
        return from_stage not in (Stage.COMPLETE, Stage.FAILED, Stage.PENDING)

    flow = get_mission_flow(mission_id)
    stage_order = [info.stage for info in flow]

    if from_stage not in stage_order:
        return False

    from_idx = stage_order.index(from_stage)
    # Next stage in flow
    if from_idx + 1 < len(stage_order) and stage_order[from_idx + 1] is to_stage:
        return True
    # Allow staying in same stage (re-entry)
    if from_stage is to_stage:
        return True
    return False


def get_next_stage_in_flow(current: Stage, mission_id: str) -> Stage | None:
    """Get the next stage in the mission flow after `current`.

    Returns None if current is the last stage in the flow.
    """
    flow = get_mission_flow(mission_id)
    stage_order = [info.stage for info in flow]
    if current not in stage_order:
        return None
    idx = stage_order.index(current)
    if idx + 1 < len(stage_order):
        return stage_order[idx + 1]
    return None

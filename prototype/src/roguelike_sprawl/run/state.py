"""Run State system — manages a single playthrough's stage progression.

A "Run" is one complete playthrough: from accepting a mission at the
Hub to completing it (or flatlining). Each Run is divided into Stages,
which are concrete objectives the player must satisfy in order.

This module is the source of truth for "what should the player be doing
right now?" — the matrix screen, demo loop, and status panel all read
from it instead of tracking ad-hoc flags.

Stage Flow (Pillar 6: Stage Flow):

    ┌─────────┐
    │ PENDING │  (Hub: Accept mission)
    └────┬────┘
         ↓
    ┌──────────┐
    │ MEET_NPC │  (Matrix: Talk to construct)
    └────┬─────┘
         ↓
    ┌─────────────┐
    │ EXTRACT_DATA│  (Matrix: Extract data — optional per mission)
    └────┬────────┘
         ↓
    ┌──────────┐
    │ DEFEAT_ICE│  (Matrix: Win combat)
    └────┬──────┘
         ↓
    ┌─────────┐
    │ JACK_OUT│  (Animation: Disconnect from matrix)
    └────┬────┘
         ↓
    ┌─────────┐
    │ REWARD  │  (Hub: Show rewards)
    └────┬────┘
         ↓
    ┌──────────┐
    │ COMPLETE │  (Run done)
    └──────────┘

On any failure (combat defeat, etc.):
         ↓
    ┌──────────────┐
    │ FAILED      │  (Death screen)
    └────┬─────────┘
         ↓
    ┌────────────────┐
    │ DEATH_RESTART  │  (Hub: Restart option)
    └────┬───────────┘
         ↓
    (back to PENDING for new run)
"""

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
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
            "  ░  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░",
            "  ░  ── JACKING OUT ──     ░",
            "  ░  ░▒▓█             ▓▒░  ░",
            "  ░  ░▒▓█             ▓▒░  ░",
            "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
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
            "  ░  ░▒▓  IT  WATCHES  ▓▒░ ░",
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


# --- RunState ---


@dataclass
class RunState:
    """The player's current progress through a single Run.

    Replaces the old `visited_npc_dixie` / `visited_data` / `visited_ice`
    flags in the demo. The matrix screen, demo loop, and status panel all
    read from this to decide what to show and where to navigate.

    Attributes:
        current_stage: The stage the player is currently in.
        completed_stages: Tuple of stages the player has completed.
        pending_advance: Set when a stage transition just happened but
            the UI hasn't acknowledged it yet.
        current_target_node: Matrix node id where the current stage's
            objective should be done. None = not yet determined.
        last_visited_node: Last matrix node visited (for path context).
        mission_id: The mission this run belongs to.
        started_at: Timestamp (ms) when the run started.
    """

    current_stage: Stage = Stage.PENDING
    completed_stages: tuple[Stage, ...] = ()
    pending_advance: bool = False
    current_target_node: str | None = None
    last_visited_node: str | None = None
    mission_id: str = "first_jack"
    started_at_ms: int = 0
    chapter_state: ChapterState = ChapterState.PROLOGUE
    current_phase_index: int = 0

    # --- Lifecycle ---

    def reset(self, mission_id: str = "first_jack") -> None:
        """Reset to initial state for a new Run."""
        # CONTENT_EXPANSION Phase B: missions now start at BRIEFING
        # (was MEET_NPC). The first mark_advance() progresses through
        # TRAVEL → MEET_NPC → ...
        self.current_stage = Stage.BRIEFING
        self.completed_stages = ()
        self.pending_advance = False
        self.current_target_node = None
        self.last_visited_node = None
        self.mission_id = mission_id
        self.started_at_ms = 0
        self.chapter_state = ChapterState.PROLOGUE
        self.current_phase_index = 0

    def is_complete(self) -> bool:
        """Run is finished (success or failure)."""
        return self.current_stage in (Stage.COMPLETE, Stage.FAILED, Stage.DEATH_RESTART)

    def is_in_progress(self) -> bool:
        """Run is currently happening (player in cyberspace)."""
        return self.current_stage not in (
            Stage.PENDING,
            Stage.COMPLETE,
            Stage.FAILED,
            Stage.DEATH_RESTART,
        )

    def is_in_cyberspace(self) -> bool:
        """Player is currently jacked into the matrix."""
        return self.current_stage in (Stage.MEET_NPC, Stage.EXTRACT_DATA, Stage.DEFEAT_ICE)

    def current_info(self) -> StageInfo:
        """Return info for the current stage."""
        return get_stage_info(self.current_stage)

    def objective_kind(self) -> ObjectiveKind:
        """Return the objective kind for the current stage."""
        return self.current_info().objective_kind

    def hint(self) -> str:
        """Return a player-facing hint for the current stage."""
        return self.current_info().hint

    def title(self) -> str:
        """Return the title for the current stage."""
        return self.current_info().title

    # --- Progress ---

    def progress_fraction(self) -> float:
        """Return current progress as a fraction (0.0-1.0)."""
        total = get_mission_stage_count(self.mission_id)
        if total == 0:
            return 0.0
        completed = len(self.completed_stages)
        return min(1.0, completed / total)

    def stages_total(self) -> int:
        """Return total stages in the current mission."""
        return get_mission_stage_count(self.mission_id)

    def stages_completed(self) -> int:
        """Return number of stages completed in the current run."""
        return len(self.completed_stages)

    # --- Stage transitions ---

    def mark_advance(self) -> None:
        """Mark the current stage as completed and advance to the next.

        Not idempotent: calling twice will advance twice (so the same
        stage is recorded as completed twice in completed_stages). This
        is intentional — the call site is responsible for ensuring it
        is only called once per stage transition (use the various
        check_* helpers to gate the call).

        Does not change state if already at COMPLETE or FAILED.
        """
        if self.current_stage in (
            Stage.COMPLETE,
            Stage.FAILED,
            Stage.PENDING,
            Stage.DEATH_RESTART,
        ):
            return

        info = self.current_info()
        # Add to completed
        self.completed_stages = self.completed_stages + (self.current_stage,)
        # Advance via mission flow (preferred) or info.next_stage (fallback)
        next_in_flow = get_next_stage_in_flow(self.current_stage, self.mission_id)
        if next_in_flow is not None:
            self.current_stage = next_in_flow
        elif info.next_stage is not None:
            self.current_stage = info.next_stage
        else:
            self.current_stage = Stage.COMPLETE
        # Reset target (will be re-resolved by matrix screen)
        self.current_target_node = None
        # Mark that a transition just happened (used by UI to show
        # "Stage complete" message until the player dismisses it).
        self.pending_advance = True

    def confirm_advance(self) -> None:
        """Acknowledge that the stage transition has been observed."""
        self.pending_advance = False

    def mark_failed(self) -> None:
        """Mark the run as failed (e.g. player flatlined).

        No-op if the run is already at a terminal stage
        (COMPLETE, FAILED, DEATH_RESTART).
        """
        if self.current_stage in (Stage.COMPLETE, Stage.FAILED, Stage.DEATH_RESTART):
            return
        self.completed_stages = self.completed_stages + (self.current_stage,)
        self.current_stage = Stage.FAILED
        self.current_target_node = None
        self.pending_advance = True

    def mark_death_restart(self) -> None:
        """Transition from FAILED to DEATH_RESTART (after death screen)."""
        if self.current_stage is Stage.FAILED:
            self.current_stage = Stage.DEATH_RESTART
            self.pending_advance = True

    def set_target(self, node_id: str | None) -> None:
        """Set the current target node for the active stage."""
        self.current_target_node = node_id

    def mark_visited(self, node_id: str) -> None:
        """Record that the player visited a node (for path context)."""
        self.last_visited_node = node_id

    # --- Chapter transitions ---

    def start_chapter(self, chapter_num: int) -> None:
        """Phase C-2: Transition to IN_CHAPTER_N (table-driven).

        Validates chapter_num (1-5). Sets chapter_state, current_stage
        to PENDING, and resets phase index. Replaces the 5 separate
        start_chapter_N() methods.
        """
        if not 1 <= chapter_num <= 5:
            raise ValueError(
                f"start_chapter: chapter_num must be 1..5, got {chapter_num} (valid: 1, 2, 3, 4, 5)"
            )
        new_state = ChapterState(f"in_chapter_{chapter_num}")
        self.chapter_state = new_state
        self.current_stage = Stage.PENDING
        self.reset_phase()

    def complete_chapter(self, chapter_num: int) -> None:
        """Phase C-2: Mark chapter N complete (table-driven).

        Validates chapter_num (1-5). Sets chapter_state to
        CHAPTER_N_COMPLETE. Replaces the 5 separate complete_chapter_N()
        methods.
        """
        if not 1 <= chapter_num <= 5:
            raise ValueError(
                f"complete_chapter: chapter_num must be 1..5, got {chapter_num} "
                f"(valid: 1, 2, 3, 4, 5)"
            )
        complete_state = ChapterState(f"chapter_{chapter_num}_complete")
        self.chapter_state = complete_state

    def is_chapter_complete(self) -> bool:
        """Check if current chapter is complete (chapter end phase)."""
        return self.current_stage is Stage.COMPLETE

    def is_in_chapter_1(self) -> bool:
        """Player is currently in Chapter 1."""
        return self.chapter_state is ChapterState.IN_CHAPTER_1

    def is_in_chapter_2(self) -> bool:
        """Player is currently in Chapter 2."""
        return self.chapter_state is ChapterState.IN_CHAPTER_2

    def is_in_chapter_3(self) -> bool:
        """Player is currently in Chapter 3."""
        return self.chapter_state is ChapterState.IN_CHAPTER_3

    def is_in_chapter_4(self) -> bool:
        """Player is currently in Chapter 4."""
        return self.chapter_state is ChapterState.IN_CHAPTER_4

    def is_in_chapter_5(self) -> bool:
        """Player is currently in Chapter 5."""
        return self.chapter_state is ChapterState.IN_CHAPTER_5

    def is_at_prologue(self) -> bool:
        """Player is currently in the Prologue."""
        return self.chapter_state is ChapterState.PROLOGUE

    def is_at_ending(self) -> bool:
        """Player has reached an ending."""
        return self.chapter_state in (
            ChapterState.ENDING_A,
            ChapterState.ENDING_B,
            ChapterState.ENDING_C,
        )

    # --- Phase 9: Salvation Phase helpers (ADR-0090) ---

    def enter_salvation_intro(self) -> None:
        """Transition to SALVATION_INTRO (epilogue selection menu)."""
        self.chapter_state = ChapterState.SALVATION_INTRO

    def start_salvation_epilogue(self) -> None:
        """Begin epilogue playback (SALVATION_EPILOGUE)."""
        self.chapter_state = ChapterState.SALVATION_EPILOGUE

    def complete_salvation_epilogue(self) -> None:
        """Epilogue complete (SALVATION_DONE), ready to select ending."""
        self.chapter_state = ChapterState.SALVATION_DONE

    def is_at_salvation(self) -> bool:
        """Player is in any Salvation state (intro/epilogue/done)."""
        return self.chapter_state in (
            ChapterState.SALVATION_INTRO,
            ChapterState.SALVATION_EPILOGUE,
            ChapterState.SALVATION_DONE,
        )

    def is_salvation_complete(self) -> bool:
        """Epilogue played; player must now choose ENDING_A/B/C."""
        return self.chapter_state is ChapterState.SALVATION_DONE

    def reach_final(self) -> None:
        """After ENDING selected, transition to FINAL (Hub return)."""
        self.chapter_state = ChapterState.FINAL

    def advance_phase(self) -> int:
        """Advance to the next phase. Returns the new phase index."""
        self.current_phase_index += 1
        return self.current_phase_index

    def reset_phase(self) -> None:
        """Reset phase index to 0 (for new chapter)."""
        self.current_phase_index = 0

    def get_phase_index(self) -> int:
        """Get the current phase index (0-based)."""
        return self.current_phase_index

    def set_phase_index(self, index: int) -> None:
        """Set the phase index (used when loading saves)."""
        self.current_phase_index = index


# --- Factory ---


def start_run(mission_id: str = "first_jack", initial_stage: Stage | None = None) -> RunState:
    """Create a fresh RunState for a given mission.

    Args:
        mission_id: The mission to start. Defaults to "first_jack".
        initial_stage: Override the initial stage (default: BRIEFING for
            active missions, PENDING for unstarted).  CONTENT_EXPANSION
            Phase B moved the first in-mission stage from MEET_NPC to
            BRIEFING so the player sees the fixer's briefing before
            traveling to the jack-in point.

    Returns:
        A new RunState.
    """
    if initial_stage is None:
        initial_stage = Stage.BRIEFING
    return RunState(
        current_stage=initial_stage,
        mission_id=mission_id,
    )

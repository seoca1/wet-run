"""RunState lifecycle and stage-transition behavior."""

from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ChapterState,
    ObjectiveKind,
    Stage,
    StageInfo,
    get_mission_stage_count,
    get_next_stage_in_flow,
    get_stage_info,
)


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

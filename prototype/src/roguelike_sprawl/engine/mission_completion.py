"""Mission completion system (ADR-0017).

When a player satisfies a mission's primary objective (e.g. extracted
data, defeated ICE), the mission is marked complete:
1. Reward credits and materials are added to state.
2. Mission is added to ``completed_missions`` set.
3. Current mission is cleared.
4. The next mission (if any) for the player's grade becomes available.
5. (Phase 6+) Faction reputation is adjusted based on the fixer.

This is the game's primary progression loop: do mission → get reward →
unlock next mission → repeat.
"""

from __future__ import annotations

from ..matrix.node import Faction
from ..run.reputation import MAX_DELTA_PER_EVENT
from .state import AppState

# Faction rep deltas for mission completion, keyed by fixer.
# Positive values = mission went well for the faction; negative values
# = mission went against their interests (e.g. you destroyed Sense/Net
# servers while working for Hosaka).
FIXER_REPUTATION: dict[str, dict[str, int]] = {
    "finn": {"hosaka": +5, "sense_net": +5},  # Jack-it-up fixer (neutral)
    "dixie": {"ta": -3, "hosaka": +3},  # Construct - works against T-A
    "kumiko": {"maas": +8},  # Maas-affiliated Count Zero character
    "maas": {"maas": +10, "hosaka": -3},  # Direct Maas work, against Hosaka
    "sally": {"sense_net": +10, "maas": -3},  # Sense/Net ally
    "ta_rep": {"ta": +10, "sense_net": -3},  # Tessier-Ashpool work
    "3jane": {"ta": +5, "sense_net": +3},  # Romantic (Phase 6+) — T-A insider
    "yakuza": {},  # No faction in enum — neutral for rep
}


def fixer_to_factions(fixer: str) -> list[Faction]:
    """Map a fixer ID to the factions whose reputation they affect.

    Returns the list of Faction enum values for the given fixer, or
    an empty list for unknown fixers (e.g. yakuza).
    """
    deltas = FIXER_REPUTATION.get(fixer, {})
    factions: list[Faction] = []
    for name in deltas:
        try:
            factions.append(Faction(name))
        except ValueError:
            continue
    return factions


def _apply_fixer_reputation(state: AppState, fixer: str, source: str) -> None:
    """Apply reputation deltas for a fixer's mission completion.

    Writes to ``state.status_messages`` so the player sees the effect.
    """
    deltas = FIXER_REPUTATION.get(fixer)
    if not deltas:
        return
    for faction_name, delta in deltas.items():
        # Clamp to MAX_DELTA_PER_EVENT (defensive — already clamped by adjust)
        clamped = max(-MAX_DELTA_PER_EVENT, min(MAX_DELTA_PER_EVENT, delta))
        try:
            faction = Faction(faction_name)
        except ValueError:
            continue
        state.reputation.adjust(faction, clamped, source=source)
        tier = state.reputation.get(faction).tier()
        state.status_messages.append(f">>> Rep {faction.value}: {clamped:+d} ({tier})")


def check_mission_completion(state: AppState) -> bool:
    """Check if the current mission is complete based on player progress.

    Returns:
        True if mission was completed (and rewards were awarded).
    """
    if state.current_mission is None:
        return False

    if not state.current_mission.check_completion(state.mission_progress):
        return False

    # Already completed (shouldn't happen, but safety)
    if state.current_mission.id in state.completed_missions:
        return False

    complete_mission(state, state.current_mission)
    return True


def complete_mission(state: AppState, mission: object) -> None:
    """Award rewards and mark mission as complete.

    Args:
        state: App state.
        mission: The Mission to complete.
    """
    # Import here to avoid circular import
    from ..missions.mission import Mission

    if not isinstance(mission, Mission):
        return

    # Award credits
    credits_amount = mission.reward_credits
    if credits_amount > 0:
        state.credits += credits_amount
        state.status_messages.append(f">>> +{credits_amount} credits")
        state.status_messages.append(f"   Total: {state.credits} credits")

    # Award materials
    rewards = mission.rewards
    if rewards is not None:
        for mat_id, count in rewards.materials.items():
            if not hasattr(state, "inventory") or state.inventory is None:
                state.inventory = {}
            state.inventory[mat_id] = state.inventory.get(mat_id, 0) + count
            state.status_messages.append(f">>> +{count}x {mat_id}")

    # Mark complete
    state.completed_missions.add(mission.id)

    # Phase 6+: adjust faction reputation based on the fixer who
    # gave us the job. Finn work → balance; Maas work → Maas+ /
    # Hosaka-; Sense/Net work → Sense/Net+ / Maas-; etc.
    if hasattr(state, "reputation") and mission.fixer:
        _apply_fixer_reputation(state, mission.fixer, source=f"mission:{mission.id}")

    state.current_mission = None

    # Reset progress for next mission
    state.mission_progress = {}

    # Show completion message
    state.status_messages.append(f">>> MISSION COMPLETE: {mission.title}")
    state.status_messages.append(">>> Return to hub for next job")

    # Phase 16: Telemetry (opt-in only).
    if getattr(state, "telemetry_opt_in", False):
        integrator = getattr(state, "telemetry", None)
        if integrator is not None:
            try:
                integrator.record_mission_completed(mission.id, state.player_grade)
                # Fires once per mission completion. The run-level
                # event is emitted on death (failed) or when state
                # transitions to Stage.COMPLETE in handle_event handlers.
            except Exception as exc:  # pragma: no cover - defensive
                state.status_messages.append(f">>> Telemetry mission_completed failed: {exc}")


def update_mission_progress(
    state: AppState,
    objective_type: str,
    count: int = 1,
) -> bool:
    """Increment progress toward current mission's primary objective.

    Args:
        state: App state.
        objective_type: The objective type to progress (e.g. "extract_data", "defeat").
        count: How much to increment by.

    Returns:
        True if mission was completed as a result.
    """
    if state.current_mission is None:
        return False

    if state.current_mission.primary_objective is None:
        return False

    if state.current_mission.primary_objective.type != objective_type:
        # Not the primary objective; ignore
        return False

    state.mission_progress[objective_type] = state.mission_progress.get(objective_type, 0) + count

    state.status_messages.append(
        f">>> Progress: {objective_type} {state.mission_progress[objective_type]}"
        f"/{state.current_mission.primary_objective.count}"
    )

    # Check if this completes the mission
    return check_mission_completion(state)


def get_next_available_mission(state: AppState) -> object | None:
    """Get the next available mission for the player's grade.

    Skips completed missions. Returns None if all available missions
    are done.
    """
    if not hasattr(state, "job_board") or state.job_board is None:
        return None

    available = state.job_board.available_for(state.player_grade)
    for mission in available:
        if mission.id not in state.completed_missions:
            return mission
    return None


def get_mission_summary(state: AppState) -> str:
    """Get a one-line summary of current mission status.

    Returns:
        String like "First Jack — extract_data 1/1 (75%)" or "No mission".
    """
    if state.current_mission is None:
        return "No active mission"

    m = state.current_mission
    pct = int(m.progress_pct(state.mission_progress) * 100)
    if m.primary_objective is not None:
        current = state.mission_progress.get(m.primary_objective.type, 0)
        required = m.primary_objective.count
        return f"{m.title} — {m.primary_objective.type} {current}/{required} ({pct}%)"
    return f"{m.title} — (no objective)"

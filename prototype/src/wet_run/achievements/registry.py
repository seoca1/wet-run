"""Achievement event handlers and display helpers.

Provides the behavior layer over the catalog defined in
:mod:`wet_run.achievements.models`:
- :func:`check_combat_event` — combat event → achievement unlocks.
- :func:`check_exploration_event` — exploration event → achievement unlocks.
- :func:`check_story_event` — story event → achievement unlocks.
- :func:`check_mastery_event` — mastery event → achievement unlocks.
- :func:`check_true_hacker` — manual meta-achievement check.
- :func:`check_matrix_master` — manual matrix_master check.
- :func:`render_achievement` — single achievement as a card string.
- :func:`get_achievements_summary` — aggregate stats for HUD/UI.

Kept separate from :mod:`wet_run.achievements.models` (data) per ADR-0110
(≤ 500 LOC per module).
"""

from __future__ import annotations

from wet_run.achievements.catalog import ALL_ACHIEVEMENTS
from wet_run.achievements.models import (
    Achievement,
    AchievementState,
)

# ----------------------------------------------------------------------------
# Event-based check helpers
# ----------------------------------------------------------------------------


def check_combat_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a combat event.

    Events:
      - "ice_killed": value=number of ICE killed this fight
      - "crit_hit": value=number of crits in this fight
      - "boss_killed": value=boss kind ("goliath_prime", "black_ice_lord", ...)
      - "max_combo": value=highest combo this fight
      - "won_fight": value=1
      - "won_flawless": value=1
    """
    unlocked: list[Achievement] = []

    if event == "ice_killed":
        if value >= 1:
            ach = state.unlock("first_blood", current_ms)
            if ach:
                unlocked.append(ach)
        # Track total kills (cumulative)
        prev = state.get_progress("centurion_progress")
        state.set_progress("centurion_progress", prev + value)
        if state.get_progress("centurion_progress") >= 100:
            ach = state.unlock("centurion", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "crit_hit" and value >= 10:
        ach = state.unlock("sharpshooter", current_ms)
        if ach:
            unlocked.append(ach)

    elif event == "boss_killed":
        ach = state.unlock("boss_slayer", current_ms)
        if ach:
            unlocked.append(ach)
        boss_kind = str(value)
        if boss_kind == "goliath_prime":
            ach = state.unlock("goliath_slayer", current_ms)
            if ach:
                unlocked.append(ach)
        elif boss_kind == "black_ice_lord":
            ach = state.unlock("void_walker", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "max_combo" and value >= 6:
        ach = state.unlock("combo_master", current_ms)
        if ach:
            unlocked.append(ach)
        if value >= 50:
            ach = state.unlock("combo_quant", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "won_flawless":
        prev = state.get_progress("flawless_progress")
        state.set_progress("flawless_progress", prev + 1)
        if state.get_progress("flawless_progress") >= 50:
            ach = state.unlock("flawless", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "won_fight":
        # Undefeated tracking
        prev = state.get_progress("undefeated_progress")
        state.set_progress("undefeated_progress", prev + 1)
        if state.get_progress("undefeated_progress") >= 10:
            ach = state.unlock("undefeated", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_exploration_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after an exploration event.

    Events:
      - "jack_in": value=1
      - "visited_world": value=world_id
      - "visited_server": value=server_id (cumulative tracking)
      - "data_extracted": value=count
      - "jack_out": value=1
      - "node_visited": value=count
    """
    unlocked: list[Achievement] = []

    if event == "jack_in":
        ach = state.unlock("first_jackin", current_ms)
        if ach:
            unlocked.append(ach)

    elif event == "visited_world":
        # Track unique worlds (use set semantics via progress)
        prev = state.get_progress("worlds_visited")
        if value not in (1, 2):  # unknown world
            return unlocked
        bit = 1 << (value - 1)  # bit 0 for world 1, bit 1 for world 2
        new_progress = prev | bit
        state.set_progress("worlds_visited", new_progress)
        if (new_progress & 0b11) == 0b11:  # both worlds visited
            ach = state.unlock("world_walker", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "visited_server":
        prev = state.get_progress("servers_visited")
        state.set_progress("servers_visited", prev | (1 << value))
        # Check all 6 visited
        if (prev | (1 << value)) & 0b111111 == 0b111111:
            ach = state.unlock("server_domination", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "data_extracted":
        prev = state.get_progress("data_extracted_progress")
        state.set_progress("data_extracted_progress", prev + value)
        if state.get_progress("data_extracted_progress") >= 10:
            ach = state.unlock("data_extractor", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "jack_out":
        prev = state.get_progress("jackouts")
        state.set_progress("jackouts", prev + 1)
        if state.get_progress("jackouts") >= 10:
            ach = state.unlock("jackout_survivor", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "node_visited":
        prev = state.get_progress("nodes_visited")
        state.set_progress("nodes_visited", prev + 1)
        if state.get_progress("nodes_visited") >= 50:
            ach = state.unlock("matrix_explorer", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_story_event(
    state: AchievementState,
    event: str,
    value: str = "",
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a story event.

    Events:
      - "prologue_complete": value=character name
      - "story_read": value=story id
      - "ending_unlocked": value=ending name
    """
    unlocked: list[Achievement] = []

    if event == "prologue_complete":
        ach_id = {
            "novice": "case_journey",
            "case": "case_journey",
            "veteran": "sil_awakening",
            "sil": "sil_awakening",
            "heretic": "kas_rise",
            "kas": "kas_rise",
        }.get(value.lower())
        if ach_id:
            ach = state.unlock(ach_id, current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "story_read":
        # Use a simple counter incremented per story_read event
        # (caller responsible for unique stories)
        prev = state.get_progress("stories_read")
        state.set_progress("stories_read", prev + 1)
        if state.get_progress("stories_read") >= 5:
            ach = state.unlock("five_tales", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "ending_unlocked":
        prev = state.get_progress("endings_unlocked")
        if not value:
            return unlocked
        # Track via progress number (incremented per unique ending)
        state.set_progress("endings_unlocked", prev + 1)
        if state.get_progress("endings_unlocked") >= 3:
            ach = state.unlock("the_truth", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_mastery_event(
    state: AchievementState,
    event: str,
    value: int = 0,
    current_ms: int = 0,
) -> list[Achievement]:
    """Check achievements after a mastery event.

    Events:
      - "ppl_reached": value=current PPL
      - "zdr_cleared": value=highest ZDR the player has cleared
      - "ppl_zdr_combined": value = max(PPL + ZDR) achieved in one fight
    """
    unlocked: list[Achievement] = []

    if event == "ppl_reached":
        if value >= 10:
            ach = state.unlock("ppl_10", current_ms)
            if ach:
                unlocked.append(ach)
        if value >= 20:
            ach = state.unlock("ppl_20", current_ms)
            if ach:
                unlocked.append(ach)
        if value >= 30:
            ach = state.unlock("ppl_30", current_ms)
            if ach:
                unlocked.append(ach)

    elif event == "zdr_cleared":
        # MATRIX_MASTER: PPL 30 + ZDR 30 in the same fight.
        # The caller is expected to fire BOTH ppl_reached AND zdr_cleared
        # with the same values; we record the highest ZDR cleared and
        # check it together with the highest PPL reached in check_meta.
        prev = state.get_progress("max_zdr_cleared")
        if value > prev:
            state.set_progress("max_zdr_cleared", value)

    elif event == "ppl_zdr_combined":
        # Single combined check: PPL + ZDR ≥ 60 (i.e. 30 + 30).
        if value >= 60:
            ach = state.unlock("matrix_master", current_ms)
            if ach:
                unlocked.append(ach)
        # Check true_hacker: player has unlocked every non-self achievement.
        if state.get_total_unlocked() >= len(ALL_ACHIEVEMENTS) - 1:
            ach = state.unlock("true_hacker", current_ms)
            if ach:
                unlocked.append(ach)

    return unlocked


def check_true_hacker(state: AchievementState, current_ms: int = 0) -> Achievement | None:
    """Manual check for the ``true_hacker`` meta-achievement.

    Returns the unlocked achievement if the player has every other
    achievement, else None. Useful to call after batch unlocks (e.g.
    end-of-run reward screens).
    """
    if state.get_total_unlocked() >= len(ALL_ACHIEVEMENTS) - 1:
        return state.unlock("true_hacker", current_ms)
    return None


def check_matrix_master(
    state: AchievementState, ppl: int, zdr: int, current_ms: int = 0
) -> Achievement | None:
    """Manual check for ``matrix_master``: PPL + ZDR ≥ 60 (one fight).

    Returns the unlocked achievement if conditions met, else None.
    """
    if ppl + zdr >= 60:
        return state.unlock("matrix_master", current_ms)
    return None


# ----------------------------------------------------------------------------
# Display helpers
# ----------------------------------------------------------------------------


def render_achievement(ach: Achievement, unlocked: bool) -> str:
    """Render an achievement as a card string."""
    status = "\u2705" if unlocked else "\U0001f512"
    lines = [
        f"{status} [{ach.tier.value.upper()}] {ach.icon} {ach.name_ko} ({ach.name})",
        f"   {ach.description}",
    ]
    if ach.reward_credits > 0:
        lines.append(f"   보상: {ach.reward_credits} 크레딧")
    return "\n".join(lines)


def get_achievements_summary(state: AchievementState) -> dict[str, object]:
    """Get a summary dict of achievement progress for display."""
    return {
        "total_unlocked": state.get_total_unlocked(),
        "total_available": state.get_total_available(),
        "completion_pct": round(state.get_completion_pct(), 1),
        "credits_earned": state.total_credits_earned,
        "by_category": state.get_completion_stats(),
    }


__all__ = [
    "check_combat_event",
    "check_exploration_event",
    "check_mastery_event",
    "check_story_event",
    "check_matrix_master",
    "check_true_hacker",
    "render_achievement",
    "get_achievements_summary",
]

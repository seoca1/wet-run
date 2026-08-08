"""Tutorial System (ADR-0175).

3-Act onboarding: Act 1 (basics), Act 2 (intermediate), Act 3 (full).
Tutorial uses Gibson tone — atmospheric learning.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TutorialAct:
    """A tutorial act for onboarding."""

    id: str
    title: str
    description: str
    tips: tuple[str, ...]
    trigger_condition: str


TUTORIAL_ACTS: dict[str, TutorialAct] = {
    "act1": TutorialAct(
        id="act1",
        title="FIRST JACK",
        description="The basics. Learn to survive.",
        tips=(
            "Press SPACE to use skills.",
            "HEAL restores HP after combat.",
            "Watch your alarm — full alarm means flatline.",
            "Programs have AP cost — manage resources.",
        ),
        trigger_condition="first_combat",
    ),
    "act2": TutorialAct(
        id="act2",
        title="DEEPER IN",
        description="Medium difficulty. The real game begins.",
        tips=(
            "Multi-enemy encounters are risky — use AoE wisely.",
            "Info items reveal ICE weaknesses before combat.",
            "Mutators change run rules — read carefully.",
            "ICE personalities determine behavior — adapt.",
        ),
        trigger_condition="second_run",
    ),
    "act3": TutorialAct(
        id="act3",
        title="THE MATRIX",
        description="No more hand-holding. You're jacked in.",
        tips=(),
        trigger_condition="third_run",
    ),
}


def get_tutorial_act(act_id: str) -> TutorialAct | None:
    """Return tutorial act by id."""
    return TUTORIAL_ACTS.get(act_id)


def get_tutorial_acts() -> tuple[TutorialAct, ...]:
    """Return all tutorial acts in order."""
    return (TUTORIAL_ACTS["act1"], TUTORIAL_ACTS["act2"], TUTORIAL_ACTS["act3"])


def get_current_act(run_count: int) -> TutorialAct | None:
    """Return the current tutorial act based on run count.

    Run 1 -> Act 1, Run 2 -> Act 2, Run 3+ -> Act 3 (no tutorial).
    """
    if run_count <= 1:
        return TUTORIAL_ACTS["act1"]
    if run_count == 2:
        return TUTORIAL_ACTS["act2"]
    return TUTORIAL_ACTS["act3"]


def get_tutorial_tips(act_id: str) -> tuple[str, ...]:
    """Return the tips for a tutorial act."""
    act = TUTORIAL_ACTS.get(act_id)
    if act is None:
        return ()
    return act.tips


def should_show_tutorial(run_count: int) -> bool:
    """Return True if tutorial should be shown (runs 1-2)."""
    return run_count <= 2


def tutorial_has_tips(act_id: str) -> bool:
    """Return True if the act has tips (Act 3 has none)."""
    return len(get_tutorial_tips(act_id)) > 0


def get_act_index(act_id: str) -> int:
    """Return the 1-based index of the act."""
    acts = get_tutorial_acts()
    for i, a in enumerate(acts, start=1):
        if a.id == act_id:
            return i
    return 0


def is_first_run(run_count: int) -> bool:
    """Return True if this is the player's first run."""
    return run_count <= 1


def is_learning_phase(run_count: int) -> bool:
    """Return True if player is in the learning phase (runs 1-2)."""
    return run_count <= 2


__all__ = [
    "TUTORIAL_ACTS",
    "TutorialAct",
    "get_act_index",
    "get_current_act",
    "get_tutorial_act",
    "get_tutorial_acts",
    "get_tutorial_tips",
    "is_first_run",
    "is_learning_phase",
    "should_show_tutorial",
    "tutorial_has_tips",
]

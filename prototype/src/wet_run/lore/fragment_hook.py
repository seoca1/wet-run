"""Memory Fragment integration hook (ADR-0140 §Proposal 2).

High-level helper called on matrix node entry to roll for fragments,
update tracker, and emit status messages.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fragment_tracker import MemoryFragmentTracker
from .memory_fragment import (
    MemoryFragmentPick,
    roll_memory_fragment,
)


@dataclass(frozen=True, slots=True)
class FragmentTriggerResult:
    """Outcome of a fragment-trigger check on node entry."""

    pick: MemoryFragmentPick | None
    status_message: str
    cap_reached: bool


def check_memory_fragment_on_node_entry(
    state: Any,
    encounter_table: dict[str, object],
    tracker: MemoryFragmentTracker,
    rng: random.Random,
    *,
    current_zone: str,
    current_grade: int,
    faction: str | None,
) -> FragmentTriggerResult:
    """Roll for Memory Fragment on node entry and apply state changes.

    Args:
        state: AppState-like object with status_messages list.
        encounter_table: Loaded encounter table.
        tracker: Per-run tracker (modified in-place).
        rng: Random instance.
        current_zone: Current zone name.
        current_grade: Current player grade.
        faction: Server faction (may be None).

    Returns:
        FragmentTriggerResult with pick (if any) and status message.
        Also appends the message to state.status_messages.
    """
    if not tracker.can_discover():
        return FragmentTriggerResult(
            pick=None,
            status_message=">>> Memory fragment signal too faint — cap reached",
            cap_reached=True,
        )

    pick = roll_memory_fragment(
        encounter_table,
        current_zone,
        current_grade,
        faction,
        rng,
        already_found=tracker.already_found,
    )

    if pick is None:
        return FragmentTriggerResult(
            pick=None,
            status_message="",
            cap_reached=False,
        )

    added = tracker.mark_found(pick.fragment_id)
    if not added:
        return FragmentTriggerResult(
            pick=pick,
            status_message="",
            cap_reached=False,
        )

    msg = f">>> Memory fragment recovered: {pick.fragment_id} ({pick.category})"
    if pick.rep_delta != 0 and pick.faction:
        msg += f" — faction rep {pick.faction} {pick.rep_delta:+d}"

    status_list = getattr(state, "status_messages", None)
    if isinstance(status_list, list):
        status_list.append(msg)

    return FragmentTriggerResult(
        pick=pick,
        status_message=msg,
        cap_reached=False,
    )


def get_default_encounter_table_path(project_root: Path) -> Path:
    """Resolve default encounter table path under data/lore/."""
    return project_root / "data" / "lore" / "encounter_table.json"


__all__ = [
    "FragmentTriggerResult",
    "check_memory_fragment_on_node_entry",
    "get_default_encounter_table_path",
]

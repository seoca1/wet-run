"""Lore subsystem (ADR-0140 §Proposal 1+2 — Construct Whisper + Memory Fragments)."""

from __future__ import annotations

from .construct_whisper import (
    HINTS_BY_FACTION,
    WHISPER_UNLOCK_TIER,
    ConstructWhisper,
    get_hint_for_faction,
)
from .construct_whisper_hook import check_construct_whisper_on_combat_start
from .fragment_hook import (
    FragmentTriggerResult,
    check_memory_fragment_on_node_entry,
    get_default_encounter_table_path,
)
from .fragment_tracker import MemoryFragmentTracker
from .memory_fragment import (
    MemoryFragmentPick,
    load_encounter_table,
    roll_memory_fragment,
)

__all__ = [
    "ConstructWhisper",
    "FragmentTriggerResult",
    "HINTS_BY_FACTION",
    "MemoryFragmentPick",
    "MemoryFragmentTracker",
    "WHISPER_UNLOCK_TIER",
    "check_construct_whisper_on_combat_start",
    "check_memory_fragment_on_node_entry",
    "get_default_encounter_table_path",
    "get_hint_for_faction",
    "load_encounter_table",
    "roll_memory_fragment",
]

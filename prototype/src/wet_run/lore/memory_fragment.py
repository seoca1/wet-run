"""Memory Fragment encounter logic (ADR-0140 §Proposal 2).

Picks a fragment to discover based on current zone/tier/grade/faction.
Per-run cap prevents excessive grinding.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True, slots=True)
class MemoryFragmentPick:
    """Result of a Memory Fragment encounter roll."""

    fragment_id: str
    category: str
    rep_delta: int = 0
    faction: str | None = None


def load_encounter_table(path: Path) -> dict[str, object]:
    """Load the encounter table JSON.

    Args:
        path: Path to encounter_table.json.

    Returns:
        Parsed table dict. Empty dict if file missing or corrupt.
    """
    if not path.exists():
        return {"version": 0, "fragments": [], "per_run_cap": 0, "base_chance": 0.0}
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"version": 0, "fragments": [], "per_run_cap": 0, "base_chance": 0.0}
    if not isinstance(data, dict):
        return {"version": 0, "fragments": [], "per_run_cap": 0, "base_chance": 0.0}
    return data


def _zone_matches(fragment: dict[str, object], current_zone: str) -> bool:
    """Check if fragment's zone matches current zone.

    Args:
        fragment: Fragment metadata dict.
        current_zone: Current matrix zone name (lowercase).

    Returns:
        True if zone matches.
    """
    zone = str(cast(Any, fragment.get("zone", ""))).lower()
    return zone == current_zone.lower()


def _grade_matches(fragment: dict[str, object], current_grade: int) -> bool:
    """Check if fragment's grade range includes current grade.

    Args:
        fragment: Fragment metadata dict.
        current_grade: Current player grade (1-6).

    Returns:
        True if current_grade is within [grade_min, grade_max].
    """
    grade_min = _safe_int(fragment.get("grade_min", 1))
    grade_max = _safe_int(fragment.get("grade_max", 6))
    return grade_min <= current_grade <= grade_max


def _faction_matches(fragment: dict[str, object], faction: str | None) -> bool:
    """Check if fragment's faction matches the current server faction.

    Args:
        fragment: Fragment metadata dict.
        faction: Server faction name (e.g. 'hosaka', 'tessier_ashpool') or None.

    Returns:
        True if fragment has no faction requirement, or faction matches.
    """
    frag_faction = fragment.get("faction")
    if frag_faction is None or str(frag_faction).lower() == "none":
        return True
    if faction is None:
        return False
    return str(frag_faction).lower() == faction.lower()


def _safe_int(value: Any) -> int:
    """Best-effort int coercion; default 0 on failure."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    """Best-effort float coercion; default 0.0 on failure."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def roll_memory_fragment(
    encounter_table: dict[str, object],
    current_zone: str,
    current_grade: int,
    faction: str | None,
    rng: random.Random,
    *,
    already_found: set[str] | None = None,
) -> MemoryFragmentPick | None:
    """Roll for a Memory Fragment encounter.

    Filters fragments by zone/grade/faction, then weights remaining
    fragments by their individual chance. Excludes already-found
    fragments in the same run.

    Args:
        encounter_table: Loaded encounter table dict.
        current_zone: Current matrix zone.
        current_grade: Current player grade.
        faction: Server faction for current zone (may be None).
        rng: Random instance for reproducibility.
        already_found: Set of fragment IDs already found this run.
            Excluded from candidate pool.

    Returns:
        MemoryFragmentPick if a fragment is found, else None.
    """
    if already_found is None:
        already_found = set()

    fragments_raw = encounter_table.get("fragments", [])
    if not isinstance(fragments_raw, list) or not fragments_raw:
        return None

    base_chance = _safe_float(encounter_table.get("base_chance", 0.0))
    if rng.random() >= base_chance:
        return None

    candidates: list[tuple[float, dict[str, object]]] = []
    for frag in fragments_raw:
        if not isinstance(frag, dict):
            continue
        fid = frag.get("id")
        if not fid or fid in already_found:
            continue
        if not _zone_matches(frag, current_zone):
            continue
        if not _grade_matches(frag, current_grade):
            continue
        if not _faction_matches(frag, faction):
            continue
        chance = _safe_float(frag.get("chance", 0.0))
        if chance > 0:
            candidates.append((chance, frag))

    if not candidates:
        return None

    weights = [w for w, _ in candidates]
    chosen = rng.choices(candidates, weights=weights, k=1)[0][1]

    raw_rep_delta = chosen.get("rep_delta", 0)
    raw_faction = chosen.get("faction")
    rep_delta = _safe_int(raw_rep_delta)
    resolved_faction: str | None
    if raw_faction is None or str(raw_faction).lower() == "none":
        resolved_faction = None
    else:
        resolved_faction = str(raw_faction)
    return MemoryFragmentPick(
        fragment_id=str(chosen["id"]),
        category=str(cast(Any, chosen.get("category", ""))),
        rep_delta=rep_delta,
        faction=resolved_faction,
    )


__all__ = [
    "MemoryFragmentPick",
    "load_encounter_table",
    "roll_memory_fragment",
]

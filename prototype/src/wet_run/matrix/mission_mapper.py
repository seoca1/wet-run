"""Mission-to-room mapping (ADR-0060 Phase 3).

Maps a ``Mission`` plus a character reference to a list of ``RoomType``
suitable for the procedural dungeon generator.  This is the bridge
between the high-level mission definition (Arc 1-5, character arc)
and the low-level room graph (Entry → ... → Exit).

Algorithm:
    1.  Add ENTRY and EXIT (always first and last).
    2.  Scan the mission objective text for keywords that map to
        RoomType (data / ice / npc / extractor / router).
    3.  Add 1-2 rooms per keyword match.
    4.  Pad with Router rooms based on a target room count derived
        from ``mission.arc`` (Arc 1 → 4 rooms, Arc 5 → 9 rooms).
    5.  Apply character bias:
            - ``novice``:  no NPC rooms, minimal ICE
            - ``veteran``: 1 NPC, 1 ICE
            - ``heretic``: 2 NPC, 2 ICE, optional LOA flair (Router)

The result is a deterministic, keyword-driven room list that the
procedural generator can place inside BSP leaves.
"""

from __future__ import annotations

from ..matrix.dungeon_generator import ProceduralDungeonGenerator, RoomType
from .graph import MatrixGraph

# Type hint only — Missions/Mission live in ``wet_run.missions.mission``.
# We intentionally accept the minimum interface (id, title, objective, arc,
# primary_objective) via duck typing so this module has no hard import on
# the missions package.  At call time we expect a Mission instance.
MissionLike = object


# Keyword → (RoomType, weight).  Longer keywords appear first so that
# "black ICE" matches before "ICE" alone.
_KEYWORD_RULES: tuple[tuple[str, RoomType, int], ...] = (
    # Loa / voodoo (heretic only — fall back to Router for others)
    ("mona lisa overdrive", RoomType.ROUTER, 1),
    ("voodoo", RoomType.ROUTER, 1),
    ("loa", RoomType.ROUTER, 1),
    # Constructs / NPCs
    ("dixie flatline", RoomType.NPC, 1),
    ("construct", RoomType.NPC, 1),
    ("dixie", RoomType.NPC, 1),
    ("molly", RoomType.NPC, 1),
    ("armitage", RoomType.NPC, 1),
    ("case", RoomType.NPC, 1),
    # ICE / combat
    ("black ice", RoomType.ICE, 1),
    ("wolfgang", RoomType.ICE, 1),
    ("tessier", RoomType.ICE, 1),
    ("ice", RoomType.ICE, 1),
    # Data / extraction
    ("rom construct", RoomType.DATA, 1),
    ("extract", RoomType.DATA, 1),
    ("download", RoomType.DATA, 1),
    ("data", RoomType.DATA, 1),
    ("rom", RoomType.DATA, 1),
    # Cores / systems
    ("core", RoomType.CORE, 1),
    ("system", RoomType.ROUTER, 1),
)


# Target room counts per Arc (excluding ENTRY/EXIT).
_TARGET_BY_ARC: dict[int, tuple[int, int]] = {
    1: (3, 4),  # short intros
    2: (4, 5),
    3: (5, 6),
    4: (6, 7),
    5: (7, 8),  # climactic
}


# Character-based biases (additional rooms beyond keyword-driven ones).
# Each tuple = (extra_npc, extra_ice, extra_router_loa).
_CHAR_BIAS: dict[str, tuple[int, int, int]] = {
    "novice": (0, 0, 0),
    "veteran": (1, 1, 0),
    "heretic": (2, 2, 1),  # extra router stand-in for Loa flair
}


def _mission_text(mission: MissionLike) -> str:
    """Extract textual content used for keyword scanning."""
    parts: list[str] = []
    for attr in ("title", "objective"):
        val = getattr(mission, attr, "") or ""
        if isinstance(val, str):
            parts.append(val.lower())
    primary = getattr(mission, "primary_objective", None)
    if primary is not None:
        obj_type = getattr(primary, "type", "") or ""
        if isinstance(obj_type, str):
            parts.append(obj_type.lower())
        target = getattr(primary, "data_id", "") or ""
        if isinstance(target, str):
            parts.append(target.lower())
        mat = getattr(primary, "material", "") or ""
        if isinstance(mat, str):
            parts.append(mat.lower())
    return " ".join(parts)


def _keyword_rooms(text: str) -> list[RoomType]:
    """Match keywords in ``text`` and return their mapped RoomType list.

    Each keyword match contributes one room.  Order is preserved so the
    returned list mirrors the order of the keyword rules, but duplicate
    consecutive matches are collapsed.
    """
    rooms: list[RoomType] = []
    last: RoomType | None = None
    for needle, room_type, weight in _KEYWORD_RULES:
        if needle in text:
            for _ in range(weight):
                # Avoid two identical consecutive rooms for readability.
                if last is room_type and rooms:
                    continue
                rooms.append(room_type)
                last = room_type
    return rooms


def _arc_target(arc: int) -> tuple[int, int]:
    """Return ``(min_middle, max_middle)`` for the given Arc 1-5."""
    if arc < 1:
        return _TARGET_BY_ARC[1]
    if arc > 5:
        return _TARGET_BY_ARC[5]
    return _TARGET_BY_ARC[arc]


def missions_to_rooms(
    mission: MissionLike,
    character_ref: str = "veteran",
) -> list[RoomType]:
    """Map a mission to a dungeon room sequence.

    The result always starts with ``RoomType.ENTRY`` and ends with
    ``RoomType.EXIT``.  Middle rooms are keyword-driven (objective text)
    plus character-driven extras, padded with ``RoomType.ROUTER``
    to meet the arc target count.

    Args:
        mission: A ``Mission`` (duck-typed — must expose ``title``,
            ``objective``, ``arc``, and ``primary_objective`` if present).
        character_ref: ``"novice"`` | ``"veteran"`` | ``"heretic"`` —
            controls how many NPC and ICE rooms appear.

    Returns:
        A list of ``RoomType`` of length 5..9 representing the dungeon.
    """
    arc = getattr(mission, "arc", 1) or 1
    char = character_ref if character_ref in _CHAR_BIAS else "veteran"
    target_min, target_max = _arc_target(arc)

    text = _mission_text(mission)
    keyword_rooms = _keyword_rooms(text)

    # Apply character bias.
    extra_npc, extra_ice, extra_router = _CHAR_BIAS[char]
    extra_rooms: list[RoomType] = []
    extra_rooms.extend([RoomType.NPC] * extra_npc)
    extra_rooms.extend([RoomType.ICE] * extra_ice)
    extra_rooms.extend([RoomType.ROUTER] * extra_router)

    middle = keyword_rooms + extra_rooms
    target = min(target_max, max(target_min, len(middle)))

    # Pad or trim to reach ``target`` middle rooms.
    if len(middle) < target:
        middle = middle + [RoomType.ROUTER] * (target - len(middle))
    elif len(middle) > target:
        # Keep first ``target`` rooms to preserve keyword order.
        middle = middle[:target]

    # Ensure exactly one EXIT (in case a keyword matched)
    middle = [r for r in middle if r is not RoomType.EXIT]

    return [RoomType.ENTRY, *middle, RoomType.EXIT]


def mission_to_graph(
    mission: MissionLike,
    character_ref: str = "veteran",
    seed: int | None = None,
    proc_generator: ProceduralDungeonGenerator | None = None,
) -> MatrixGraph:
    """Bridge function: combine ``missions_to_rooms`` with a BSP generator.

    This is the high-level entry point used by the dungeon-mode
    render path.  Steps:

        1.  Build the RoomType outline from the mission + character.
        2.  Generate a base BSP graph big enough to host the outline.
        3.  Re-tag the BSP nodes so the first ``len(outline)`` nodes
            carry the mission's RoomType semantics (kind, zone, ice).
        4.  Return the decorated graph.

    Args:
        mission: A ``Mission``-like object.
        character_ref: ``"novice"`` | ``"veteran"`` | ``"heretic"``.
        seed: Optional RNG seed (defaults to ``mission.matrix_seed``
            if the mission exposes it, else 0).
        proc_generator: Optional ``ProceduralDungeonGenerator`` (caller
            may inject for caching / custom configurations).

    Returns:
        A ``MatrixGraph`` whose nodes reflect the mission outline.
    """
    if proc_generator is None:
        proc_generator = ProceduralDungeonGenerator()
    outline = missions_to_rooms(mission, character_ref=character_ref)
    arc = getattr(mission, "arc", 3) or 3
    if seed is None:
        seed = getattr(mission, "matrix_seed", 0) or 0
    graph = proc_generator.generate(
        seed=seed,
        mission_grade=arc,
        character_ref=character_ref,
        mission_id=getattr(mission, "id", None),
    )
    return proc_generator.decorate_with_outline(graph, outline, character_ref=character_ref)


__all__ = [
    "MissionLike",
    "_arc_target",
    "_keyword_rooms",
    "_mission_text",
    "mission_to_graph",
    "missions_to_rooms",
]

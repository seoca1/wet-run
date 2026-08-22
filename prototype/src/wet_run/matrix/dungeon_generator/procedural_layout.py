"""Layout helpers for the procedural dungeon generator.

Pure functions that turn BSP leaves into a fully decorated
:class:`MatrixGraph`:

    connect_adjacent        — Kruskal spanning tree over leaves (L-corridors).
    add_dead_ends           — extra branches proportional to character_ref.
    assign_room_types       — promote ENTRY/EXIT and decorate DATA/ICE/NPC.
    pick_room_type          — weighted random for non-special leaves.
    label_for               — short label for a non-special room type.
    rooms_to_nodes          — convert placed rooms into MatrixGraph Nodes.
    faction_for             — map character_ref to default dungeon faction.
    node_attributes         — map RoomType -> (NodeKind, IceKind, ZoneDepth).
    build_bidirectional_edges — deduplicate + emit bidirectional Edges.
    build_graph             — wrap nodes/edges into MatrixGraph (fallback).
    decorate_with_outline   — re-tag nodes to match mission RoomType outline.

These were originally methods of
:class:`wet_run.matrix.dungeon_generator.procedural.ProceduralDungeonGenerator`;
factored into this sub-module per ADR-0110 (≤ 500 LOC per module).

Originally part of ``matrix/dungeon_generator.py`` (862 LOC).
"""

from __future__ import annotations

import random

from ..graph import Edge, MatrixGraph
from ..node import Faction, IceKind, Node, NodeKind, ZoneDepth
from .models import Room, RoomType, _BspNode

# Dead-end fraction per character reference.  Higher = more back-tracking.
# Used by :func:`add_dead_ends` to decide how many extra branch edges to add.
DEADEND_BY_CHAR: dict[str, float] = {
    "novice": 0.10,
    "veteran": 0.25,
    "heretic": 0.40,
}

# Fraction of rooms that contain ICE encounters.  Tighter for novice.
ICE_FRACTION_BY_CHAR: dict[str, float] = {
    "novice": 0.15,
    "veteran": 0.20,
    "heretic": 0.30,
}

# Target number of NPC rooms per character reference.
NPC_BIAS_BY_CHAR: dict[str, int] = {
    "novice": 0,
    "veteran": 1,
    "heretic": 2,
}


def connect_adjacent(
    rng: random.Random,  # noqa: ARG001 — RNG reserved for future variations
    leaves: list[_BspNode],
) -> list[tuple[str, str]]:
    """Build a spanning tree over ``leaves`` using Kruskal MST.

    For small dungeon graphs (~30 leaves), the O(n^2) candidate-edge
    build + sort-by-distance + Union-Find join is well within budget
    and yields more interesting layouts than a trivial chain.

    Args:
        rng: RNG; unused but kept in signature for parity with future variants.
        leaves: BSP leaves whose ``room.room_id`` will form edges.

    Returns:
        List of ``(room_id_a, room_id_b)`` tuples forming a spanning tree.
    """
    if len(leaves) < 2:
        return []
    edges: list[tuple[str, str]] = []
    parent = list(range(len(leaves)))

    def find(i: int) -> int:
        """Find the root of ``i`` in the Union-Find forest with path compression."""
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> bool:
        """Union two sets; returns True if a merge happened, False if already same set."""
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[rb] = ra
        return True

    # Build candidate edges with Manhattan distance between centers.
    candidates: list[tuple[int, int, int]] = []  # (distance, i, j)
    for i, a in enumerate(leaves):
        ax, ay = a.center()
        for j in range(i + 1, len(leaves)):
            b = leaves[j]
            bx, by = b.center()
            distance = abs(bx - ax) + abs(by - ay)
            candidates.append((distance, i, j))
    candidates.sort()

    for _, i, j in candidates:
        if union(i, j):
            a_id = leaves[i].room.room_id  # type: ignore[union-attr]
            b_id = leaves[j].room.room_id  # type: ignore[union-attr]
            if a_id is not None and b_id is not None:
                edges.append((a_id, b_id))
            if len(edges) >= len(leaves) - 1:
                break
    return edges


def add_dead_ends(
    rng: random.Random,
    leaves: list[_BspNode],
    existing_edges: list[tuple[str, str]],
    character_ref: str,
) -> list[tuple[str, str]]:
    """Add extra branch edges proportional to ``character_ref``'s dead-end fraction."""
    fraction = DEADEND_BY_CHAR.get(character_ref, 0.0)
    if fraction <= 0 or len(leaves) < 3:
        return existing_edges

    # How many extra edges?  Fraction of total leaf count minus the
    # spanning tree size (``len(leaves) - 1``).
    target_extras = int(round(fraction * (len(leaves) - 1)))
    if target_extras <= 0:
        return existing_edges

    existing_set = {tuple(sorted(e)) for e in existing_edges}
    added = 0
    max_tries = max(1, target_extras * 8)

    for _ in range(max_tries):
        if added >= target_extras:
            break
        pair = rng.sample(leaves, 2)
        a, b = pair[0], pair[1]
        a_id = a.room.room_id if a.room else None
        b_id = b.room.room_id if b.room else None
        if a_id is None or b_id is None:
            continue
        key = tuple(sorted([a_id, b_id]))
        if key in existing_set:
            continue
        existing_edges.append((a_id, b_id))
        existing_set.add(key)
        added += 1
    return existing_edges


def assign_room_types(
    rng: random.Random,
    leaves: list[_BspNode],
    character_ref: str,
) -> list[Room]:
    """Promote ENTRY/EXIT and decorate DATA / ICE / NPC rooms.

    - First leaf (top-left): always ENTRY.
    - Leaf farthest from ENTRY along the spanning tree: EXIT.
    - Remaining non-special leaves: random DATA / ICE / NPC / ROUTER.
    """
    if not leaves:
        return []

    # Choose ENTRY/EXIT using simple distance heuristic: ENTRY = first
    # leaf; EXIT = leaf whose center is farthest (Manhattan) from
    # entry center.
    entry_leaf = leaves[0]
    entry_center = entry_leaf.center()
    exit_leaf = max(
        leaves,
        key=lambda n: abs(n.center()[0] - entry_center[0]) + abs(n.center()[1] - entry_center[1]),
    )

    rooms: list[Room] = []
    for i, leaf in enumerate(leaves):
        room = leaf.room
        if room is None:
            continue
        if leaf is entry_leaf:
            room_type = RoomType.ENTRY
            label = "Jack-in Point"
        elif leaf is exit_leaf:
            room_type = RoomType.EXIT
            label = "Extraction Gate"
        else:
            room_type = pick_room_type(rng, character_ref, i, len(leaves))
            label = label_for(room_type, i)
        rooms.append(
            Room(
                id=room.room_id,
                x=room.x,
                y=room.y,
                room_type=room_type,
                label=label,
            )
        )
    return rooms


def pick_room_type(
    rng: random.Random,
    character_ref: str,
    index: int,
    total: int,
) -> RoomType:
    """Pick a non-special room type weighted by character reference."""
    ice_fraction = ICE_FRACTION_BY_CHAR.get(character_ref, 0.20)
    npc_bias = NPC_BIAS_BY_CHAR.get(character_ref, 1)

    roll = rng.random()
    # Encourage at least one DATA room regardless of character.
    data_threshold = 1.0 - (1.0 / max(3, total))
    if roll < data_threshold - ice_fraction - (0.05 * npc_bias):
        return RoomType.DATA
    if roll < data_threshold - (0.05 * npc_bias):
        return RoomType.ICE
    if roll < data_threshold:
        return RoomType.ROUTER
    # NPC bias adds up to 2 extra NPC slots
    if npc_bias > 0 and rng.random() < (0.10 + 0.10 * npc_bias):
        return RoomType.NPC
    if rng.random() < 0.08:
        return RoomType.DEAD_END
    return RoomType.ROUTER


def label_for(room_type: RoomType, index: int) -> str:
    """A short label for the room by type (kept readable)."""
    labels = {
        RoomType.DATA: "Data Vault",
        RoomType.ICE: "ICE Barrier",
        RoomType.NPC: "Construct",
        RoomType.ROUTER: "Router",
        RoomType.CORE: "Core",
        RoomType.EMPTY: "Empty",
        RoomType.DEAD_END: "Dead End",
    }
    base = labels.get(room_type, "Room")
    return f"{base} {index}"


def rooms_to_nodes(rooms: list[Room], character_ref: str) -> list[Node]:
    """Convert placed rooms into MatrixGraph Node instances."""
    faction = faction_for(character_ref)
    nodes: list[Node] = []
    for room in rooms:
        node_kind, ice_kind, zone = node_attributes(room.room_type, character_ref)
        nodes.append(
            Node(
                id=room.id,
                kind=node_kind,
                label=room.label,
                zone=zone,
                ice=ice_kind,
                faction=faction,
                room_type=room.room_type,
            )
        )
    return nodes


def faction_for(character_ref: str) -> Faction:
    """Map a character_ref to its default dungeon faction."""
    return {
        "novice": Faction.NONE,
        "veteran": Faction.SENSE_NET,
        "heretic": Faction.TA,
    }.get(character_ref, Faction.NONE)


def node_attributes(
    room_type: RoomType,
    character_ref: str,
) -> tuple[NodeKind, IceKind, ZoneDepth]:
    """Map room_type to NodeKind, IceKind, ZoneDepth."""
    if room_type is RoomType.ENTRY:
        return (NodeKind.ENTRY, IceKind.NONE, ZoneDepth.SURFACE)
    if room_type is RoomType.EXIT:
        return (NodeKind.EXIT, IceKind.NONE, ZoneDepth.CORE)
    if room_type is RoomType.DATA:
        return (NodeKind.DATA, IceKind.NONE, ZoneDepth.SURFACE)
    if room_type is RoomType.ICE:
        # heretic gets tougher ICE than veteran/novice
        ice = IceKind.BLACK if character_ref == "heretic" else IceKind.STANDARD
        return (NodeKind.ICE, ice, ZoneDepth.MID)
    if room_type is RoomType.NPC:
        return (NodeKind.CONSTRUCT, IceKind.NONE, ZoneDepth.MID)
    if room_type is RoomType.DEAD_END:
        return (NodeKind.ROUTER, IceKind.NONE, ZoneDepth.MID)
    return (NodeKind.ROUTER, IceKind.NONE, ZoneDepth.SURFACE)


def build_bidirectional_edges(
    pairs: list[tuple[str, str]],
    rooms: list[Room],
) -> list[Edge]:
    """Deduplicate and emit bidirectional edges."""
    room_ids = {room.id for room in rooms}
    edge_set: set[tuple[str, str]] = set()
    for a, b in pairs:
        if a not in room_ids or b not in room_ids or a == b:
            continue
        edge_set.add((a, b))
    return [Edge(a, b) for a, b in sorted(edge_set)]


def build_graph(
    nodes: list[Node],
    edges: list[Edge],
    entry_id: str,
) -> MatrixGraph:
    """Wrap a (possibly empty) layout into a MatrixGraph.

    When ``nodes`` is empty, return a minimal ENTRY/EXIT pair so the
    screen renders something rather than crashing.
    """
    if not nodes:
        nodes = [
            Node(
                id="entry",
                kind=NodeKind.ENTRY,
                label="Jack-in Point",
                zone=ZoneDepth.SURFACE,
            ),
            Node(
                id="exit",
                kind=NodeKind.EXIT,
                label="Extraction Gate",
                zone=ZoneDepth.CORE,
            ),
        ]
        edges = [Edge("entry", "exit")]
        entry_id = "entry"
    return MatrixGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
        entry_id=entry_id,
    )


def decorate_with_outline(
    graph: MatrixGraph,
    outline: list[RoomType],
    character_ref: str = "veteran",
) -> MatrixGraph:
    """Re-tag nodes in ``graph`` to match the RoomType sequence in ``outline``.

    Used after procedural BSP generation to apply mission-driven
    decoration.  The first ``len(outline)`` nodes (in storage order)
    take their kind/zone/ice from the corresponding ``RoomType``;
    any surplus nodes are downgraded to plain Router rooms.

    The graph topology (edges, entry_id) is preserved.

    Args:
        graph: A ``MatrixGraph`` produced by the BSP generator.
        outline: A list of ``RoomType`` whose length should match the
            number of middle rooms produced by ``missions_to_rooms``.
        character_ref: Same character reference as passed to ``generate()``.

    Returns:
        A new ``MatrixGraph`` with decorated Node attributes.
    """
    nodes = list(graph.nodes)
    if not nodes:
        return graph
    decorated: list[Node] = []
    for i, node in enumerate(nodes):
        if i < len(outline):
            room_type = outline[i]
            kind, ice, zone = node_attributes(room_type, character_ref)
            decorated.append(
                Node(
                    id=node.id,
                    kind=kind,
                    label=node.label,
                    zone=zone,
                    ice=ice,
                    faction=node.faction,
                )
            )
        else:
            # Surplus nodes become plain routers.
            decorated.append(
                Node(
                    id=node.id,
                    kind=NodeKind.ROUTER,
                    label=node.label,
                    zone=ZoneDepth.SURFACE,
                    ice=IceKind.NONE,
                    faction=node.faction,
                )
            )
    return MatrixGraph(
        nodes=tuple(decorated),
        edges=graph.edges,
        entry_id=graph.entry_id,
    )


__all__ = [
    "DEADEND_BY_CHAR",
    "ICE_FRACTION_BY_CHAR",
    "NPC_BIAS_BY_CHAR",
    "add_dead_ends",
    "assign_room_types",
    "build_bidirectional_edges",
    "build_graph",
    "connect_adjacent",
    "decorate_with_outline",
    "faction_for",
    "label_for",
    "node_attributes",
    "pick_room_type",
    "rooms_to_nodes",
]

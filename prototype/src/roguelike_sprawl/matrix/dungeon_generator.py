"""Dungeon-style matrix generator.

Generates a 2D grid-based dungeon with rooms connected by corridors.
Uses a BFS-based layout algorithm for clean cardinal direction movement.

Phase 2 (ADR-0060): adds ``ProceduralDungeonGenerator`` which uses a
Binary Space Partitioning (BSP) algorithm to produce seed-determined
non-linear dungeon layouts.  Mission grade (1-5) and character reference
(novice/veteran/heretic) configure layout parameters.  Layouts are
reproducible: the same seed, grade, and character_ref always yield the
same matrix.

The original ``DungeonGenerator`` (hand-crafted 7x5 layout) is kept for
backwards compatibility with existing tests.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum

from typing_extensions import override

from .graph import Edge, MatrixGraph
from .node import Faction, IceKind, Node, NodeKind, ZoneDepth


class RoomType(StrEnum):
    """Visual type of room for rendering."""

    EMPTY = "empty"
    ENTRY = "entry"
    EXIT = "exit"
    DATA = "data"
    ICE = "ice"
    NPC = "npc"
    ROUTER = "router"
    CORE = "core"
    DEAD_END = "dead_end"


@dataclass
class Room:
    """A room in the dungeon grid."""

    id: str
    x: int
    y: int
    room_type: RoomType
    label: str
    description: str = ""


# ============================================================================
# Layout parameters per mission grade and character reference
# ============================================================================

# Grid size (cols x rows) for each mission grade (1-5).
# Smaller for novice, larger for higher grades.
_GRID_BY_GRADE: dict[int, tuple[int, int]] = {
    1: (7, 5),  # 10-12 rooms
    2: (9, 6),  # 14-18 rooms
    3: (11, 7),  # 19-24 rooms
    4: (13, 8),  # 25-30 rooms
    5: (15, 10),  # 35-42 rooms
}

# Target number of NPC rooms per character reference.  Higher = more
# narrative encounters during exploration.
_NPC_BIAS_BY_CHAR: dict[str, int] = {
    "novice": 0,
    "veteran": 1,
    "heretic": 2,
}

# Fraction of extra branch edges (dead-ends relative to main path).
# Higher = more back-tracking required to find objectives.
_DEADEND_BY_CHAR: dict[str, float] = {
    "novice": 0.10,
    "veteran": 0.25,
    "heretic": 0.40,
}

# Fraction of rooms that contain ICE encounters.  Tighter for novice.
_ICE_FRACTION_BY_CHAR: dict[str, float] = {
    "novice": 0.15,
    "veteran": 0.20,
    "heretic": 0.30,
}


# ============================================================================
# Manual generator (Phase 1, kept for backwards compatibility)
# ============================================================================


class DungeonGenerator:
    """Generates a 2D grid-based dungeon with rooms.

    Phase 1 hand-crafted 7x5 layout.  Kept for backwards compatibility
    with tests that assert on the exact nodes/edges of this layout.
    Phase 2 (``ProceduralDungeonGenerator``) is the recommended path.
    """

    __slots__ = ()

    def generate(self, seed: int, mission_grade: int = 1) -> MatrixGraph:
        """Generate a dungeon-style MatrixGraph.

        Grid: 5x4 (cols x rows) — 4-directional layout
        Every room (except EXT) has exits in all 4 cardinal directions.
        Path: Entry(R2,C0) → Dixie(R1,C2) → Data(R1,C3) →绕ICE→ Exit(R2,C4)
        """
        # Layout is deterministic; seed reserved for future random variations
        del seed

        # 5 columns x 4 rows grid (col=x, row=y)
        # Row 0 (top):    (0,0)R (1,0)R (2,0)ICE (3,0)R (4,0)R
        # Row 1 (mid):    (0,1)R (1,1)R (2,1)NPC (3,1)DATA (4,1)R
        # Row 2 (bot):    (0,2)ENT(1,2)R (2,2)R (3,2)R (4,2)EXT
        # Row 3 (btm2):   (0,3)R (1,3)R (2,3)R (3,3)R (4,3)R
        layout: list[tuple[str, int, int, RoomType, str]] = [
            # Row 0
            ("r00", 0, 0, RoomType.ROUTER, "Comms Relay"),
            ("r10", 1, 0, RoomType.ROUTER, "Router"),
            ("ice", 2, 0, RoomType.ICE, "ICE Barrier"),
            ("r30", 3, 0, RoomType.ROUTER, "Junction"),
            ("r40", 4, 0, RoomType.ROUTER, "Gateway"),
            # Row 1
            ("r01", 0, 1, RoomType.ROUTER, "Buffer"),
            ("r11", 1, 1, RoomType.ROUTER, "Hub"),
            ("npc_dixie", 2, 1, RoomType.NPC, "Dixie Flatline"),
            ("data", 3, 1, RoomType.DATA, "Data Vault"),
            ("r41", 4, 1, RoomType.ROUTER, "Node"),
            # Row 2
            ("entry", 0, 2, RoomType.ENTRY, "Entry"),
            ("r12", 1, 2, RoomType.ROUTER, "Corridor"),
            ("r22", 2, 2, RoomType.ROUTER, "Intersect"),
            ("r32", 3, 2, RoomType.ROUTER, "Access Point"),
            ("exit", 4, 2, RoomType.EXIT, "Exit"),
            # Row 3
            ("r03", 0, 3, RoomType.ROUTER, "Sublevel"),
            ("r13", 1, 3, RoomType.ROUTER, "Underpass"),
            ("r23", 2, 3, RoomType.ROUTER, "Deep Core"),
            ("r33", 3, 3, RoomType.ROUTER, "Archive"),
            ("r43", 4, 3, RoomType.ROUTER, "Terminal"),
        ]

        rooms: list[Room] = [
            Room(id=room_id, x=x, y=y, room_type=room_type, label=label)
            for room_id, x, y, room_type, label in layout
        ]

        # Define connections — every room connects to its 4 cardinal neighbors
        # (x,y) connects to (x±1,y) and (x,y±1) where those rooms exist
        def edge_pairs() -> list[Edge]:
            pairs: list[tuple[str, str]] = []
            ids_at: dict[tuple[int, int], str] = {(r.x, r.y): r.id for r in rooms}
            for r in rooms:
                for dx, dy in [(1, 0), (0, 1)]:  # only forward pairs (reverse added below)
                    neighbor = ids_at.get((r.x + dx, r.y + dy))
                    if neighbor:
                        pairs.append((r.id, neighbor))
            # Add reverse edges (graph is undirected)
            result: list[Edge] = []
            for a, b in pairs:
                result.append(Edge(a, b))
                result.append(Edge(b, a))
            return result

        edges: list[Edge] = edge_pairs()

        # Convert rooms to Nodes
        faction = Faction.SENSE_NET
        nodes: list[Node] = []

        for room in rooms:
            if room.room_type is RoomType.ENTRY:
                node_kind = NodeKind.ENTRY
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.EXIT:
                node_kind = NodeKind.EXIT
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.DATA:
                node_kind = NodeKind.DATA
                ice_kind = IceKind.NONE
            elif room.room_type is RoomType.ICE:
                node_kind = NodeKind.ICE
                ice_kind = IceKind.STANDARD
            elif room.room_type is RoomType.NPC:
                node_kind = NodeKind.CONSTRUCT
                ice_kind = IceKind.NONE
            else:
                node_kind = NodeKind.ROUTER
                ice_kind = IceKind.NONE

            node = Node(
                id=room.id,
                kind=node_kind,
                label=room.label,
                zone=ZoneDepth.SURFACE,
                ice=ice_kind,
                faction=faction,
                x=room.x,
                y=room.y,
            )
            nodes.append(node)

        return MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id="entry",
        )


# ============================================================================
# Procedural generator (Phase 2 — BSP)
# ============================================================================


@dataclass(slots=True)
class _BspRoom:
    """Internal room placement for BSP partitioning."""

    x: int  # top-left x of room (inclusive)
    y: int  # top-left y of room (inclusive)
    w: int  # room width (cells)
    h: int  # room height (cells)
    room_id: str  # assigned when converted to Node


@dataclass(slots=True)
class _BspNode:
    """Recursive BSP partition."""

    x: int  # region x0
    y: int  # region y0
    w: int  # region width
    h: int  # region height
    left: _BspNode | None = None
    right: _BspNode | None = None
    room: _BspRoom | None = None  # leaf only

    # Identity-based hash/equality so instances are deduplicated by id()
    # when used as dict keys or sorted.  Required because @dataclass(slots=True)
    # disables synthesized __eq__/__hash__ on slotted classes.
    @override
    def __hash__(self) -> int:
        return id(self)

    @override
    def __eq__(self, other: object) -> bool:
        return self is other

    def __lt__(self, other: object) -> bool:
        return id(self) < id(other) if isinstance(other, _BspNode) else NotImplemented

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def center(self) -> tuple[int, int]:
        """Center coordinate of the leaf's room (or region if no room)."""
        if self.room is not None:
            return (self.room.x + self.room.w // 2, self.room.y + self.room.h // 2)
        return (self.x + self.w // 2, self.y + self.h // 2)


class ProceduralDungeonGenerator:
    """Procedural BSP dungeon generator (Phase 2).

    Produces a non-linear dungeon from a seed, mission grade, and
    character reference.  The same (seed, grade, character_ref) tuple
    always yields the same MatrixGraph, enabling deterministic runs and
    easy regression testing.

    Algorithm:
        1.  Choose grid size based on ``mission_grade`` (1-5).
        2.  Recursively partition the grid using BSP — each split is
            chosen randomly (horizontal/vertical) and the cut position
            is jittered within the region's interior.
        3.  Each leaf places one room, sized relative to the region.
        4.  Connect adjacent rooms with L-shaped corridors to form a
            spanning tree, then add extra branches (dead-ends) based
            on character reference.
        5.  Promote one endpoint leaf to ENTRY and the leaf farthest
            from entry (within the spanning tree) to EXIT.  Mark a few
            rooms as DATA / ICE / NPC based on character_ref.
        6.  Return a MatrixGraph with all nodes and bidirectional edges.
    """

    __slots__ = ("min_leaf_size", "room_padding")

    def __init__(
        self,
        min_leaf_size: int = 2,
        room_padding: int = 1,
    ) -> None:
        """Configure BSP leaf size and the room padding inside each region.

        ``min_leaf_size`` controls recursion depth: the smaller this
        value, the more (smaller) rooms.  ``room_padding`` reserves a
        border around each room for corridors to pass through.
        """
        self.min_leaf_size = min_leaf_size
        self.room_padding = room_padding

    # --------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------

    def generate(
        self,
        seed: int,
        mission_grade: int = 1,
        character_ref: str = "veteran",
        mission_id: str | None = None,
    ) -> MatrixGraph:
        """Generate a procedural BSP dungeon.

        Args:
            seed: RNG seed; same value + grade + character_ref => same layout.
            mission_grade: 1-5, controls grid size (and thus room count).
            character_ref: ``"novice"`` | ``"veteran"`` | ``"heretic"`` —
                controls dead-end fraction and ICE / NPC density.
            mission_id: optional identifier used to vary the seed slightly
                so different missions with identical (seed, grade) aren't
                identical rooms.

        Returns:
            A ``MatrixGraph`` with ENTRY → ... → EXIT and bidirectional
            corridor edges between rooms.
        """
        # Per-mission RNG (so identical seed + grade yields reproducible
        # results, but mission_id introduces a stable offset).
        effective_seed = seed
        if mission_id is not None:
            effective_seed += hash(mission_id) % 7919
        rng = random.Random(effective_seed)

        grade = max(1, min(5, mission_grade))
        char = character_ref if character_ref in _DEADEND_BY_CHAR else "veteran"
        cols, rows = _GRID_BY_GRADE[grade]

        # 1. BSP partition
        root = self._bsp_partition(rng, 0, 0, cols, rows)

        # 2. Place rooms inside leaf nodes
        self._place_rooms(rng, root)

        # 3. Collect all rooms with their BSP centers for spanning tree
        leaves = self._collect_leaves(root)
        if len(leaves) < 2:
            # Degenerate (very small grade) — return empty adjacent pair
            return self._build_graph([], [], entry_id="entry")

        # 4. Build spanning tree by joining adjacent leaves (L-corridors)
        edges_with_dirs = self._connect_adjacent(rng, leaves)

        # 5. Add dead-end branches for character variation
        edges_with_dirs = self._add_dead_ends(rng, leaves, edges_with_dirs, char)

        # 6. Assign room types (ENTRY/EXIT/DATA/ICE/NPC) and ids
        rooms = self._assign_room_types(rng, leaves, char)

        # 7. Convert to nodes
        nodes = self._rooms_to_nodes(rooms, char)

        # 8. Build bidirectional edges
        edges = self._build_bidirectional_edges(edges_with_dirs, rooms)

        # 9. Find entry id (always the first room placed, top-left)
        # Leaves are visited in BSP pre-order so the first leaf is the
        # top-left region — perfect for the jack-in point.
        entry_id = leaves[0].room.room_id  # type: ignore[union-attr]

        return MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id=entry_id,
        )

    # --------------------------------------------------------------------
    # BSP partitioning
    # --------------------------------------------------------------------

    def _bsp_partition(
        self,
        rng: random.Random,
        x: int,
        y: int,
        w: int,
        h: int,
    ) -> _BspNode:
        """Recursively split a region until leaves are small enough."""
        node = _BspNode(x=x, y=y, w=w, h=h)

        # Stop splitting when region is too small to split further.
        # We need a minimum leaf size that, minus room padding, still
        # leaves room for a 1x1 actual room and a corridor on each side.
        min_size = self.min_leaf_size
        if w < min_size * 2 and h < min_size * 2:
            # Cannot split — leaf
            return node

        # Pick a split orientation that is feasible.  A split is feasible
        # when the chosen dimension is at least 2*min_size so both halves
        # satisfy the leaf threshold.
        can_vertical = w >= 2 * min_size
        can_horizontal = h >= 2 * min_size
        if not can_vertical and not can_horizontal:
            return node  # leaf — neither dim allows a split

        # Prefer vertical when clearly wider, horizontal when clearly taller,
        # otherwise choose at random among feasible options.
        if can_vertical and (not can_horizontal or w >= h * 1.25):
            split_vertical = True
        elif can_horizontal and (not can_vertical or h > w * 1.25):
            split_vertical = False
        else:
            split_vertical = rng.random() < 0.5

        if split_vertical:
            # Vertical split: choose cut between min_size and w-min_size.
            cut_min = min_size
            cut_max = w - min_size
            cut = rng.randint(cut_min, cut_max)
            left_w = cut
            right_w = w - cut
            node.left = self._bsp_partition(rng, x, y, left_w, h)
            node.right = self._bsp_partition(rng, x + cut, y, right_w, h)
        else:
            cut_min = min_size
            cut_max = h - min_size
            cut = rng.randint(cut_min, cut_max)
            top_h = cut
            bottom_h = h - cut
            node.left = self._bsp_partition(rng, x, y, w, top_h)
            node.right = self._bsp_partition(rng, x, y + cut, w, bottom_h)
        return node

    # --------------------------------------------------------------------
    # Room placement
    # --------------------------------------------------------------------

    def _place_rooms(
        self, rng: random.Random, node: _BspNode, counter: list[int] | None = None
    ) -> int:
        """Place one room inside each leaf.  Returns next room counter."""
        if counter is None:
            counter = [0]
        if node.is_leaf:
            padding = self.room_padding
            # Room must fit inside the region with padding for corridors.
            max_w = max(1, node.w - 2 * padding)
            max_h = max(1, node.h - 2 * padding)
            # Bias toward slightly larger rooms for visual readability.
            room_w = max(1, min(max_w, rng.randint(2, max(2, max_w))))
            room_h = max(1, min(max_h, rng.randint(2, max(2, max_h))))
            # Position room inside the region, leaving padding on sides.
            rx_min = node.x + padding
            rx_max = node.x + node.w - padding - room_w
            ry_min = node.y + padding
            ry_max = node.y + node.h - padding - room_h
            rx = rx_min if rx_max <= rx_min else rng.randint(rx_min, rx_max)
            ry = ry_min if ry_max <= ry_min else rng.randint(ry_min, ry_max)
            node.room = _BspRoom(
                x=rx,
                y=ry,
                w=room_w,
                h=room_h,
                room_id=f"r{counter[0]}",
            )
            counter[0] += 1
            return counter[0]
        # Internal node — recurse
        if node.left is not None:
            counter[0] = self._place_rooms(rng, node.left, counter)
        if node.right is not None:
            counter[0] = self._place_rooms(rng, node.right, counter)
        return counter[0]

    def _collect_leaves(self, node: _BspNode, out: list[_BspNode] | None = None) -> list[_BspNode]:
        """Walk BSP and collect every leaf node (depth-first, pre-order)."""
        if out is None:
            out = []
        if node.is_leaf:
            out.append(node)
        else:
            if node.left is not None:
                self._collect_leaves(node.left, out)
            if node.right is not None:
                self._collect_leaves(node.right, out)
        return out

    # --------------------------------------------------------------------
    # Spanning tree (L-corridors)
    # --------------------------------------------------------------------

    def _connect_adjacent(
        self,
        rng: random.Random,  # noqa: ARG002 — RNG reserved for future variations
        leaves: list[_BspNode],
    ) -> list[tuple[str, str]]:
        """Build a spanning tree over ``leaves`` using Kruskal MST.

        For small dungeon graphs (~30 leaves), the O(n^2) candidate-edge
        build + sort-by-distance + Union-Find join is well within budget
        and yields more interesting layouts than a trivial chain.
        """
        if len(leaves) < 2:
            return []
        edges: list[tuple[str, str]] = []
        parent = list(range(len(leaves)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(a: int, b: int) -> bool:
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

    # Dead-end branches (character variation)
    # --------------------------------------------------------------------

    def _add_dead_ends(
        self,
        rng: random.Random,
        leaves: list[_BspNode],
        existing_edges: list[tuple[str, str]],
        character_ref: str,
    ) -> list[tuple[str, str]]:
        """Add extra branch edges proportional to ``character_ref``'s dead-end fraction."""
        fraction = _DEADEND_BY_CHAR.get(character_ref, 0.0)
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

    # --------------------------------------------------------------------
    # Room type assignment
    # --------------------------------------------------------------------

    def _assign_room_types(
        self,
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
            key=lambda n: (
                abs(n.center()[0] - entry_center[0]) + abs(n.center()[1] - entry_center[1])
            ),
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
                room_type = self._pick_room_type(rng, character_ref, i, len(leaves))
                label = self._label_for(room_type, i)
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

    def _pick_room_type(
        self,
        rng: random.Random,
        character_ref: str,
        index: int,
        total: int,
    ) -> RoomType:
        """Pick a non-special room type weighted by character reference."""
        ice_fraction = _ICE_FRACTION_BY_CHAR.get(character_ref, 0.20)
        npc_bias = _NPC_BIAS_BY_CHAR.get(character_ref, 1)

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

    def _label_for(self, room_type: RoomType, index: int) -> str:
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

    # --------------------------------------------------------------------
    # Node and edge construction
    # --------------------------------------------------------------------

    def _rooms_to_nodes(self, rooms: list[Room], character_ref: str) -> list[Node]:
        """Convert placed rooms into MatrixGraph Node instances."""
        faction = self._faction_for(character_ref)
        nodes: list[Node] = []
        for room in rooms:
            node_kind, ice_kind, zone = self._node_attributes(room.room_type, character_ref)
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

    def _faction_for(self, character_ref: str) -> Faction:
        return {
            "novice": Faction.NONE,
            "veteran": Faction.SENSE_NET,
            "heretic": Faction.TA,
        }.get(character_ref, Faction.NONE)

    def _node_attributes(
        self,
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

    def _build_bidirectional_edges(
        self,
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

    # --------------------------------------------------------------------
    # Degenerate fallback (used when very small grade yields no rooms)
    # --------------------------------------------------------------------

    def _build_graph(
        self,
        nodes: list[Node],
        edges: list[Edge],
        entry_id: str,
    ) -> MatrixGraph:
        """Wrap a (possibly empty) layout into a MatrixGraph."""
        if not nodes:
            # Avoid an empty graph — provide a minimal entry/exit pair so
            # the screen renders something.
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

    # --------------------------------------------------------------------
    # Outline application (used by mission_mapper)
    # --------------------------------------------------------------------

    def decorate_with_outline(
        self,
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
            graph: A ``MatrixGraph`` produced by ``generate()``.
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
                kind, ice, zone = self._node_attributes(room_type, character_ref)
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

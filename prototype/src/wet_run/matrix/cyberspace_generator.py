"""Cyberspace graph generator: large branching tree.

Generates a graph-based exploration with:
- Branching paths (binary/ternary tree)
- Multiple depth levels
- Wider than screen (requires scrolling)
- Various node types at different depths
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum

from .graph import Edge, MatrixGraph
from .node import Faction, IceKind, Node, NodeKind, ZoneDepth


def _index_nodes_by_id(nodes: list[Node]) -> dict[str, int]:
    """Build a node-id → index map. O(n) once, then O(1) lookups.

    Replaces the previous ``for i, n in enumerate(nodes): if n.id == c``
    pattern which was O(n) per lookup, making nested loops O(n²).
    """
    return {n.id: i for i, n in enumerate(nodes)}


class DepthLevel(StrEnum):
    """Depth levels in cyberspace (cyberspace hierarchy)."""

    SURFACE = "surface"  # Entry level
    SHALLOW = "shallow"  # First branching
    MID = "mid"  # Middle layers
    DEEP = "deep"  # Deep system
    CORE = "core"  # Core systems


@dataclass
class CyberspaceLayout:
    """Layout information for cyberspace nodes.

    Stores absolute positions for each node (not constrained to a grid).
    """

    node_id: str
    x: float  # Continuous x coordinate
    y: float  # Continuous y coordinate (0 = surface, positive = deeper)
    depth: DepthLevel


class CyberspaceGenerator:
    """Generates a large branching cyberspace graph.

    Layout strategy:
    - Entry at (0, 0)
    - Each level adds y depth
    - Branching factor 2-3 per node
    - Width grows with depth (exponential)
    - Total ~30-50 nodes
    """

    __slots__ = ()

    def generate(
        self, seed: int, mission_grade: int = 1
    ) -> tuple[MatrixGraph, dict[str, CyberspaceLayout]]:
        """Generate cyberspace graph with layout info.

        Returns:
            (graph, layouts) where layouts is a dict of node_id -> CyberspaceLayout
        """
        rng = random.Random(seed)
        layouts: dict[str, CyberspaceLayout] = {}
        nodes: list[Node] = []
        edges: list[Edge] = []

        faction = Faction.SENSE_NET

        # Layout configuration
        y_spacing = 8  # Vertical distance between depth levels
        x_branching = 12  # Horizontal distance between branches

        # Level 0: Entry.
        entry_id = "entry"
        nodes.append(self._make_node(entry_id, NodeKind.ENTRY, "Entry", faction, ZoneDepth.SURFACE))
        layouts[entry_id] = CyberspaceLayout(entry_id, 0, 0, DepthLevel.SURFACE)

        # Levels 1-3: branching tree.
        l1_nodes = self._build_level(
            rng,
            entry_id,
            rng.randint(2, 3),
            x_branching,
            y_spacing,
            DepthLevel.SHALLOW,
            ZoneDepth.SURFACE,
            faction,
            [NodeKind.ROUTER, NodeKind.DATA, NodeKind.CONSTRUCT],
            nodes,
            edges,
            layouts,
        )
        l2_nodes = self._branch_from(
            rng,
            l1_nodes,
            1,
            2,
            x_branching,
            y_spacing,
            DepthLevel.MID,
            ZoneDepth.SURFACE,
            faction,
            [NodeKind.ROUTER, NodeKind.ICE, NodeKind.SYSTEM],
            nodes,
            edges,
            layouts,
        )
        l3_parents = [n for n in l2_nodes if rng.random() < 0.6]
        self._branch_from(
            rng,
            l3_parents,
            1,
            2,
            x_branching * 1.5,
            y_spacing,
            DepthLevel.DEEP,
            ZoneDepth.MID,
            faction,
            [NodeKind.ICE, NodeKind.DATA, NodeKind.CONSTRUCT],
            nodes,
            edges,
            layouts,
        )

        # Mandatory infrastructure: at least one ICE, one NPC, one exit.
        self._ensure_main_ice(nodes, edges, layouts, entry_id, l2_nodes, y_spacing, faction)
        self._ensure_exit(nodes, edges, layouts, y_spacing, faction)
        self._ensure_npc(nodes, edges, layouts, entry_id, x_branching, y_spacing, faction)
        # Add a couple of DATA vaults near routers for loot.
        self._add_data_vaults(nodes, edges, layouts, x_branching, y_spacing, faction)

        graph = MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id=entry_id,
        )
        return graph, layouts

    # ------------------------------------------------------------------
    # Level builders
    # ------------------------------------------------------------------

    def _build_level(
        self,
        rng: random.Random,
        parent_id: str,
        n_children: int,
        x_spacing: float,
        y_spacing: float,
        depth: DepthLevel,
        zone: ZoneDepth,
        faction: Faction,
        node_kinds: list[NodeKind],
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
    ) -> list[str]:
        """Build a single level of children under a parent node."""
        return self._generate_level(
            rng,
            parent_id,
            n_children,
            x_spacing,
            y_spacing,
            depth,
            zone,
            faction,
            node_kinds,
            nodes,
            edges,
            layouts,
        )

    def _branch_from(
        self,
        rng: random.Random,
        parents: list[str],
        min_children: int,
        max_children: int,
        x_spacing: float,
        y_spacing: float,
        depth: DepthLevel,
        zone: ZoneDepth,
        faction: Faction,
        node_kinds: list[NodeKind],
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
    ) -> list[str]:
        """For each parent in ``parents``, spawn a small number of children.
        Returns a flat list of all newly created child node ids.
        """
        all_children: list[str] = []
        for parent in parents:
            n_children = rng.randint(min_children, max_children)
            ids = self._generate_level(
                rng,
                parent,
                n_children,
                x_spacing,
                y_spacing,
                depth,
                zone,
                faction,
                node_kinds,
                nodes,
                edges,
                layouts,
            )
            all_children.extend(ids)
        return all_children

    # ------------------------------------------------------------------
    # Required-infrastructure helpers
    # ------------------------------------------------------------------

    def _ensure_main_ice(
        self,
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
        entry_id: str,
        l2_nodes: list[str],
        y_spacing: float,
        faction: Faction,
    ) -> None:
        """Make sure the graph has at least one ICE node for the mission."""
        if any(n.kind is NodeKind.ICE for n in nodes):
            return
        # Place the main ICE below the first L2 node, falling back to entry.
        parent = l2_nodes[0] if l2_nodes else entry_id
        parent_layout = layouts[parent]
        ice_id = "ice_main"
        nodes.append(
            Node(
                id=ice_id,
                kind=NodeKind.ICE,
                label="ICE Sentinel",
                zone=ZoneDepth.MID,
                ice=IceKind.STANDARD,
                faction=faction,
            )
        )
        layouts[ice_id] = CyberspaceLayout(
            ice_id,
            parent_layout.x,
            parent_layout.y + y_spacing,
            DepthLevel.DEEP,
        )
        edges.append(Edge(parent, ice_id))

    def _ensure_exit(
        self,
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
        y_spacing: float,
        faction: Faction,
    ) -> None:
        """Attach an exit node below the deepest deep node, if any."""
        deepest = [n for n in nodes if layouts[n.id].depth is DepthLevel.DEEP]
        if not deepest:
            return
        parent = deepest[0]
        parent_layout = layouts[parent.id]
        nodes.append(
            Node(
                id="exit",
                kind=NodeKind.EXIT,
                label="Exit",
                zone=ZoneDepth.CORE,
                faction=faction,
            )
        )
        layouts["exit"] = CyberspaceLayout(
            "exit",
            parent_layout.x,
            parent_layout.y + y_spacing,
            DepthLevel.CORE,
        )
        edges.append(Edge(parent.id, "exit"))

    def _ensure_npc(
        self,
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
        entry_id: str,
        x_branching: float,
        y_spacing: float,
        faction: Faction,
    ) -> None:
        """Make sure the graph has an NPC (Dixie Flatline) near the entry."""
        if any(n.kind is NodeKind.CONSTRUCT for n in nodes):
            return
        npc_id = "npc_dixie"
        entry_layout = layouts[entry_id]
        nodes.append(
            Node(
                id=npc_id,
                kind=NodeKind.CONSTRUCT,
                label="Dixie Flatline",
                zone=ZoneDepth.SURFACE,
                faction=faction,
            )
        )
        layouts[npc_id] = CyberspaceLayout(
            npc_id,
            entry_layout.x - x_branching,
            entry_layout.y + y_spacing,
            DepthLevel.SHALLOW,
        )
        edges.append(Edge(entry_id, npc_id))

    def _add_data_vaults(
        self,
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
        x_branching: float,
        y_spacing: float,
        faction: Faction,
    ) -> None:
        """Attach a couple of DATA vaults to routers for loot."""
        router_nodes = [
            n
            for n in nodes
            if n.kind is NodeKind.ROUTER
            and layouts[n.id].depth in (DepthLevel.SHALLOW, DepthLevel.MID)
        ]
        for i, router in enumerate(router_nodes[:2]):
            data_id = f"data_{i}"
            parent_layout = layouts[router.id]
            nodes.append(
                Node(
                    id=data_id,
                    kind=NodeKind.DATA,
                    label="Data Vault",
                    zone=ZoneDepth.SURFACE,
                    faction=faction,
                )
            )
            layouts[data_id] = CyberspaceLayout(
                data_id,
                int(parent_layout.x + (2 if i % 2 == 0 else -2)),
                int(parent_layout.y + y_spacing * 0.5),
                DepthLevel.SHALLOW,
            )
            edges.append(Edge(router.id, data_id))

    def _generate_level(
        self,
        rng: random.Random,
        parent_id: str,
        n_children: int,
        x_spacing: float,
        y_spacing: float,
        depth: DepthLevel,
        zone: ZoneDepth,
        faction: Faction,
        node_kinds: list[NodeKind],
        nodes: list[Node],
        edges: list[Edge],
        layouts: dict[str, CyberspaceLayout],
    ) -> list[str]:
        """Generate child nodes from a parent."""
        parent_layout = layouts[parent_id]
        children: list[str] = []

        # Calculate x positions for children
        if n_children == 1:
            x_offsets: list[float] = [0]
        elif n_children == 2:
            x_offsets = [-x_spacing / 2, x_spacing / 2]
        elif n_children == 3:
            x_offsets = [-x_spacing, 0, x_spacing]
        else:
            x_offsets = [(i - (n_children - 1) / 2) * x_spacing for i in range(n_children)]

        for i in range(n_children):
            child_id = f"{parent_id}_{depth.value}_{i}"
            kind = rng.choice(node_kinds)

            # Random label
            labels = {
                NodeKind.ROUTER: "Router",
                NodeKind.DATA: "Data Vault",
                NodeKind.ICE: "ICE",
                NodeKind.SYSTEM: "System",
                NodeKind.CONSTRUCT: "Construct",
            }
            label = labels.get(kind, "Node")

            nodes.append(self._make_node(child_id, kind, label, faction, zone))
            layouts[child_id] = CyberspaceLayout(
                child_id,
                int(parent_layout.x + x_offsets[i]),
                int(parent_layout.y + y_spacing),
                depth,
            )
            edges.append(Edge(parent_id, child_id))
            children.append(child_id)

        return children

    def _make_node(
        self,
        node_id: str,
        kind: NodeKind,
        label: str,
        faction: Faction,
        zone: ZoneDepth,
    ) -> Node:
        """Create a node with default settings."""
        ice_kind = IceKind.STANDARD if kind is NodeKind.ICE else IceKind.NONE
        return Node(
            id=node_id,
            kind=kind,
            label=label,
            zone=zone,
            ice=ice_kind,
            faction=faction,
        )

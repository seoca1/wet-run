"""Procedural matrix generator (ADR-0005, design/systems/hacking.md).

Phase 5 generator: deterministic, Surface-only, small (5-7 nodes).
Uses Python's stdlib ``random.Random`` for seeded determinism.
"""

from __future__ import annotations

import random

from .graph import Edge, MatrixGraph
from .node import Faction, IceKind, Node, NodeKind, ZoneDepth

# ADR-0140 §Proposal 6 — Variable Reward Nodes. 30% of DATA nodes are
# flagged as anomaly variants (visually distinct, bonus reward on entry).
ANOMALY_PROBABILITY: float = 0.30


class MatrixGenerator:
    """Deterministic procedural matrix generator.

    Usage:
        gen = MatrixGenerator()
        graph = gen.generate(seed=42, mission_grade=1)
    """

    __slots__ = ()

    def generate(self, seed: int, mission_grade: int = 1) -> MatrixGraph:
        """Generate a MatrixGraph for the given seed and mission grade.

        Phase 5 algorithm (mission_grade=1):
            - Surface zone only
            - 1 entry, 2-3 routers, 1-2 data, 1 ice, 1 exit
            - Total: 5-7 nodes
            - Linear-ish tree layout
            - 30% of DATA nodes flagged is_anomaly (ADR-0140)

        Higher grades (Phase 6+) will scale up.
        """
        rng = random.Random(seed)

        if mission_grade <= 1:
            return self._generate_surface_mission_1(rng)
        # Phase 6+ grades
        return self._generate_surface_mission_1(rng, scale=mission_grade)

    def _generate_surface_mission_1(self, rng: random.Random, scale: int = 1) -> MatrixGraph:
        """Surface mission for grade 1-2. 5-7 nodes."""
        # 2-3 routers between entry and the rest
        n_routers = rng.randint(2, 3)
        # 1-2 data nodes
        n_data = rng.randint(1, 2)
        # 1 ICE node (standard)
        # 1 exit
        # entry + routers + data + ice + exit
        # Pick Sense/Net as the single faction modifier (typical Arc 1 vibe).
        faction = Faction.SENSE_NET

        nodes: list[Node] = []
        edges: list[Edge] = []

        # Entry
        entry_id = "E_0"
        nodes.append(
            Node(
                id=entry_id,
                kind=NodeKind.ENTRY,
                label="Entry",
                zone=ZoneDepth.SURFACE,
                faction=faction,
            )
        )

        # Routers (linear chain to keep layout predictable)
        router_ids: list[str] = []
        for i in range(n_routers):
            rid = f"R_{i}"
            router_ids.append(rid)
            nodes.append(
                Node(
                    id=rid,
                    kind=NodeKind.ROUTER,
                    label="Router",
                    zone=ZoneDepth.SURFACE,
                    faction=faction,
                )
            )

        # Data nodes — 30% flagged as anomaly (ADR-0140).
        data_ids: list[str] = []
        for i in range(n_data):
            did = f"D_{i}"
            data_ids.append(did)
            is_anomaly = rng.random() < ANOMALY_PROBABILITY
            nodes.append(
                Node(
                    id=did,
                    kind=NodeKind.DATA,
                    label="Anomaly" if is_anomaly else "Data",
                    zone=ZoneDepth.SURFACE,
                    faction=faction,
                    is_anomaly=is_anomaly,
                )
            )

        # ICE node
        ice_id = "I_0"
        nodes.append(
            Node(
                id=ice_id,
                kind=NodeKind.ICE,
                label="ICE",
                zone=ZoneDepth.SURFACE,
                ice=IceKind.STANDARD,
                faction=faction,
            )
        )

        # Exit
        exit_id = "X_0"
        nodes.append(
            Node(
                id=exit_id,
                kind=NodeKind.EXIT,
                label="Exit",
                zone=ZoneDepth.SURFACE,
                faction=faction,
            )
        )

        # Edges: entry -> all routers (star, no chain — keeps the BFS depth small
        # so the layout fits on the 80x50 screen).
        for rid in router_ids:
            edges.append(Edge(entry_id, rid))

        last_router = router_ids[-1]

        for did in data_ids:
            edges.append(Edge(last_router, did))

        edges.append(Edge(last_router, ice_id))

        for did in data_ids:
            edges.append(Edge(did, exit_id))
        edges.append(Edge(ice_id, exit_id))

        # Suppress unused-arg warning for `scale` (used by future grades)
        del scale
        return MatrixGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
            entry_id=entry_id,
        )

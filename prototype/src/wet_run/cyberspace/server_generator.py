"""Per-server subgraph generator.

Each server in a sector has its own internal graph.
A server is a small, mission-targeted cyberspace (5-10 nodes).
"""

from __future__ import annotations

from ..matrix.cyberspace_generator import CyberspaceGenerator, CyberspaceLayout
from ..matrix.graph import MatrixGraph


class ServerSubgraphGenerator:
    """Generates a subgraph for a specific server (mission target)."""

    __slots__ = ()

    def generate(
        self,
        seed: int,
        difficulty: int,
    ) -> tuple[MatrixGraph, dict[str, CyberspaceLayout]]:
        """Generate a subgraph for a server."""
        gen = CyberspaceGenerator()
        graph, layouts = gen.generate(seed=seed, mission_grade=1)
        return graph, layouts

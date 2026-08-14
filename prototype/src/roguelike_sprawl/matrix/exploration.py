"""Exploration state for the matrix (ADR-0020).

Tracks which nodes have been visited / scanned and what the player
can currently see. Used by the matrix view to render fog of war.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .graph import MatrixGraph
from .node import NodeKind


class Visibility(StrEnum):
    """How visible a node is to the player (ADR-0020)."""

    CURRENT = "current"
    ADJACENT = "adjacent"
    DISCOVERED = "discovered"
    UNKNOWN = "unknown"


@dataclass
class ExplorationState:
    """Tracks the player's progress through the matrix (ADR-0020)."""

    current: str
    discovered: set[str] = field(default_factory=set)
    scanned: set[str] = field(default_factory=set)
    path: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.current:
            self.discovered.add(self.current)
        if self.current and (not self.path or self.path[-1] != self.current):
            self.path.append(self.current)

    def visit(self, node_id: str) -> None:
        """Move to a new node. Adds to discovered + path."""
        self.current = node_id
        self.discovered.add(node_id)
        if not self.path or self.path[-1] != node_id:
            self.path.append(node_id)

    def probe(self, node_id: str) -> None:
        """Use a Probe program on a node — reveals full info (ZDR)."""
        self.scanned.add(node_id)

    def adjacent_to_current(self, graph: MatrixGraph) -> list[str]:
        """Return IDs of all nodes adjacent to the current node."""
        return [n.id for n in graph.neighbors(self.current)]

    def is_visible(self, graph: MatrixGraph, node_id: str) -> bool:
        """Return True if the player can see the node at all."""
        v = self.visibility(graph, node_id)
        return v is not Visibility.UNKNOWN

    def visibility(self, graph: MatrixGraph, node_id: str) -> Visibility:
        """Return the visibility class for a given node."""
        if self.current and node_id == self.current:
            return Visibility.CURRENT
        if node_id in self.discovered:
            return Visibility.DISCOVERED
        if graph.is_connected(self.current, node_id) or graph.is_connected(node_id, self.current):
            return Visibility.ADJACENT
        return Visibility.UNKNOWN

    def is_scanned(self, node_id: str) -> bool:
        """Return True if the player has probed/scanned this node."""
        return node_id in self.scanned

    def discoverable_now(self, graph: MatrixGraph) -> list[str]:
        """Return IDs of nodes the player could move to from here."""
        return [nid for nid in self.adjacent_to_current(graph) if nid != self.current]


def is_always_visible_kind(kind: NodeKind) -> bool:
    """Whether the entry/exit node should be visible from the start."""
    return kind in (NodeKind.ENTRY, NodeKind.EXIT)

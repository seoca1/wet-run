"""Matrix (cyberspace) subsystem (ADR-0005, design/systems/hacking.md).

Pure-data classes for the node graph that represents a cyberspace mission.
No rendering or input here; this module is UI-agnostic.
"""

from .exploration import ExplorationState, Visibility, is_always_visible_kind
from .generator import MatrixGenerator
from .graph import Edge, MatrixGraph, compute_layout
from .labels import zone_label
from .node import (
    AlarmLevel,
    Faction,
    IceKind,
    Node,
    NodeKind,
    ZoneDepth,
)
from .ppl import Loadout, Program, calculate_ppl
from .zdr import (
    Status,
    calculate_status,
    calculate_zdr,
    node_status,
    node_zdr,
    status_color,
)

__all__ = [
    "AlarmLevel",
    "Edge",
    "ExplorationState",
    "Faction",
    "IceKind",
    "Loadout",
    "MatrixGenerator",
    "MatrixGraph",
    "Node",
    "NodeKind",
    "Program",
    "Status",
    "Visibility",
    "ZoneDepth",
    "calculate_ppl",
    "calculate_status",
    "calculate_zdr",
    "compute_layout",
    "is_always_visible_kind",
    "node_status",
    "node_zdr",
    "status_color",
    "zone_label",
]

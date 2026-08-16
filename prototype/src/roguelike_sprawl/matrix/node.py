"""Matrix node data model (ADR-0005, design/systems/hacking.md).

A `Node` is a single point in the cyberspace graph. It carries the
attributes needed to compute ZDR and to render a portrait/label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from roguelike_sprawl.matrix.dungeon_generator import RoomType


class NodeKind(StrEnum):
    """Kinds of matrix nodes (ADR-0005)."""

    ENTRY = "entry"
    DATA = "data"
    SYSTEM = "system"
    ICE = "ice"
    CONSTRUCT = "construct"
    ROUTER = "router"
    CORE = "core"
    EXIT = "exit"


class ZoneDepth(StrEnum):
    """Matrix depth zones (ADR-0012). Base ZDR ranges.

    Original 4 tiers (SURFACE/MID/CORE/TA) cover the Sprawl. The DEEP
    and FREESIDE tiers were added when missions expanded into Loa/
    construct zones and orbital colonies (Freeside) — see ADR-0017,
    missions ``voodoo_loa_encounter`` (DEEP) and ``final_choice``
    (FREESIDE).
    """

    SURFACE = "surface"  # 1-3
    MID = "mid"  # 4-8
    DEEP = "deep"  # 6-10 (Loa / construct zones between MID and CORE)
    CORE = "core"  # 9-15
    TA = "ta"  # 20-30
    FREESIDE = "freeside"  # 25-35 (orbital colonies, hardest)
    SOHO = "soho"  # 3-5 (London-style black market district, v0.5)
    TOKYO = "tokyo"  # 5-8 (Yakuza-adjacent underworld district, v0.5)


class IceKind(StrEnum):
    """ICE categories. Affects ZDR and combat behavior (ADR-0012, ADR-0003)."""

    NONE = "none"
    STANDARD = "standard"
    WATCHDOG = "watchdog"
    BLACK = "black"


class AlarmLevel(StrEnum):
    """Alarm state of a node. Affects ZDR."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Faction(StrEnum):
    """Faction modifier source (ADR-0012)."""

    NONE = "none"
    HOSAKA = "hosaka"
    MAAS = "maas"
    SENSE_NET = "sense_net"
    TA = "ta"


@dataclass(frozen=True, slots=True)
class Node:
    """A single node in the cyberspace graph.

    Attributes:
        id: Unique node id (e.g. ``"E_first_jack"``).
        kind: Node kind (entry / data / ice / ...).
        label: Short human-readable label (e.g. ``"Entry"``).
        zone: Depth zone.
        ice: ICE present at this node (usually ``NONE`` for non-ice nodes).
        alarm: Alarm level.
        faction: Faction modifier.
        is_anomaly: ``True`` if this DATA node is an anomaly variant (ADR-0140 P2.6
            — Variable Reward Nodes). Visually distinct (glyph ``◆``, magenta
            color) and grants bonus reward on entry. Only DATA nodes can be
            anomaly (validated in __post_init__).
        x: Grid x coordinate (0 = leftmost column).
        y: Grid y coordinate (0 = topmost row).
    """

    id: str
    kind: NodeKind
    label: str
    zone: ZoneDepth
    ice: IceKind = IceKind.NONE
    alarm: AlarmLevel = AlarmLevel.LOW
    faction: Faction = Faction.NONE
    room_type: RoomType | None = None
    is_anomaly: bool = False
    x: int = 0
    y: int = 0

    def __post_init__(self) -> None:
        """Validate Node invariants: non-empty id/label, ICE nodes need IceKind!=NONE,
        anomaly flag only valid for DATA nodes (ADR-0140 P2.6).

        Raises:
            ValueError: If the id or label is empty, if an ICE node has no
                ``IceKind``, or if the anomaly flag is set on a non-DATA
                node. The message includes the offending node id, the
                offending field value, and (for ICE-node errors) the
                expected set of ``IceKind`` values so JSON-data authors
                can locate the bad row quickly.
        """
        if not self.id:
            raise ValueError("Node id must be non-empty")
        if not self.label:
            raise ValueError(f"Node {self.id!r}: label must be non-empty")
        # ice nodes should have an IceKind != NONE
        if self.kind is NodeKind.ICE and self.ice is IceKind.NONE:
            raise ValueError(
                f"ICE node {self.id!r} (kind={self.kind.value}) must have "
                f"an IceKind != NONE (expected one of: "
                f"{[k.value for k in IceKind if k is not IceKind.NONE]})"
            )
        # anomaly flag is only valid for DATA nodes (ADR-0140)
        if self.is_anomaly and self.kind is not NodeKind.DATA:
            raise ValueError(
                f"Non-DATA node {self.id!r} (kind={self.kind.value}) cannot be anomaly "
                f"(anomaly flag is only valid for NodeKind.DATA per ADR-0140 P2.6; "
                f"expected kind={NodeKind.DATA.value})"
            )

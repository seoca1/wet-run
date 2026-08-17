"""Tests for matrix nodes and ZDR (ADR-0005, ADR-0012)."""

from __future__ import annotations

import pytest

from wet_run.matrix.node import (
    AlarmLevel,
    Faction,
    IceKind,
    Node,
    NodeKind,
    ZoneDepth,
)
from wet_run.matrix.zdr import (
    Status,
    base_zdr,
    calculate_status,
    calculate_zdr,
    node_status,
    node_zdr,
    status_color,
)


def test_node_creation() -> None:
    n = Node(
        id="E_1",
        kind=NodeKind.ENTRY,
        label="Entry",
        zone=ZoneDepth.SURFACE,
    )
    assert n.id == "E_1"
    assert n.kind is NodeKind.ENTRY
    assert n.ice is IceKind.NONE
    assert n.alarm is AlarmLevel.LOW
    assert n.faction is Faction.NONE


def test_node_empty_id_rejected() -> None:
    with pytest.raises(ValueError, match="id must be non-empty"):
        Node(id="", kind=NodeKind.ENTRY, label="Entry", zone=ZoneDepth.SURFACE)


def test_node_empty_label_rejected() -> None:
    with pytest.raises(ValueError, match="label must be non-empty"):
        Node(id="E_1", kind=NodeKind.ENTRY, label="", zone=ZoneDepth.SURFACE)


def test_ice_node_requires_ice_kind() -> None:
    with pytest.raises(ValueError, match="must have an IceKind"):
        Node(
            id="I_1",
            kind=NodeKind.ICE,
            label="ICE",
            zone=ZoneDepth.SURFACE,
            ice=IceKind.NONE,
        )


# --- ZDR ---


def test_base_zdr() -> None:
    assert base_zdr(ZoneDepth.SURFACE) == 1
    assert base_zdr(ZoneDepth.MID) == 5
    assert base_zdr(ZoneDepth.CORE) == 12
    assert base_zdr(ZoneDepth.TA) == 25


def test_calculate_zdr_surface_plain() -> None:
    assert calculate_zdr(ZoneDepth.SURFACE) == 1


def test_calculate_zdr_with_ice() -> None:
    # Surface (1) + standard ICE (+2) = 3
    assert calculate_zdr(ZoneDepth.SURFACE, ice=IceKind.STANDARD) == 3
    # Surface (1) + black ICE (+10) = 11
    assert calculate_zdr(ZoneDepth.SURFACE, ice=IceKind.BLACK) == 11
    # Surface (1) + watchdog (+1) = 2
    assert calculate_zdr(ZoneDepth.SURFACE, ice=IceKind.WATCHDOG) == 2


def test_calculate_zdr_with_alarm() -> None:
    assert calculate_zdr(ZoneDepth.SURFACE, alarm=AlarmLevel.MEDIUM) == 4
    assert calculate_zdr(ZoneDepth.SURFACE, alarm=AlarmLevel.HIGH) == 6
    assert calculate_zdr(ZoneDepth.SURFACE, alarm=AlarmLevel.CRITICAL) == 11


def test_calculate_zdr_with_faction() -> None:
    # Surface (1) + Sense/Net (+4) = 5
    assert calculate_zdr(ZoneDepth.SURFACE, faction=Faction.SENSE_NET) == 5
    # Mid (5) + T-A (+5) = 10
    assert calculate_zdr(ZoneDepth.MID, faction=Faction.TA) == 10


def test_calculate_zdr_combined() -> None:
    # Core (12) + black ICE (+10) + high alarm (+5) = 27
    zdr = calculate_zdr(
        ZoneDepth.CORE,
        ice=IceKind.BLACK,
        alarm=AlarmLevel.HIGH,
    )
    assert zdr == 27


# --- Status ---


def test_status_zdr_zero_is_safe() -> None:
    assert calculate_status(ppl=10, zdr=0) is Status.SAFE


def test_status_safe() -> None:
    assert calculate_status(ppl=20, zdr=10) is Status.SAFE  # ratio 2.0
    assert calculate_status(ppl=16, zdr=10) is Status.SAFE  # ratio 1.6


def test_status_match() -> None:
    assert calculate_status(ppl=15, zdr=10) is Status.MATCH  # ratio 1.5
    assert calculate_status(ppl=10, zdr=10) is Status.MATCH  # ratio 1.0


def test_status_tough() -> None:
    assert calculate_status(ppl=9, zdr=10) is Status.TOUGH  # ratio 0.9
    assert calculate_status(ppl=8, zdr=10) is Status.TOUGH  # ratio 0.8


def test_status_deadly() -> None:
    assert calculate_status(ppl=7, zdr=10) is Status.DEADLY  # ratio 0.7
    assert calculate_status(ppl=5, zdr=10) is Status.DEADLY  # ratio 0.5


def test_status_futile() -> None:
    assert calculate_status(ppl=4, zdr=10) is Status.FUTILE  # ratio 0.4
    assert calculate_status(ppl=1, zdr=10) is Status.FUTILE


def test_status_colors() -> None:
    assert status_color(Status.SAFE) == (0, 255, 0)
    assert status_color(Status.MATCH) == (0, 255, 255)
    assert status_color(Status.DEADLY) == (255, 0, 64)
    assert status_color(Status.FUTILE) == (128, 0, 32)


# --- Node helpers ---


def test_node_zdr_helper() -> None:
    n = Node(
        id="I_1",
        kind=NodeKind.ICE,
        label="ICE",
        zone=ZoneDepth.SURFACE,
        ice=IceKind.STANDARD,
        faction=Faction.SENSE_NET,
    )
    # 1 (surface) + 2 (standard) + 4 (sense_net) = 7
    assert node_zdr(n) == 7


def test_node_status_helper() -> None:
    n = Node(
        id="I_1",
        kind=NodeKind.ICE,
        label="ICE",
        zone=ZoneDepth.SURFACE,
        ice=IceKind.STANDARD,
    )
    # ZDR = 1 + 2 = 3. PPL 6 / 3 = 2.0 -> SAFE
    assert node_status(n, ppl=6) is Status.SAFE
    # PPL 3 / 3 = 1.0 -> MATCH
    assert node_status(n, ppl=3) is Status.MATCH

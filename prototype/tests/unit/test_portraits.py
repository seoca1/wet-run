"""Tests for the PortraitManager (ADR-0011)."""

from __future__ import annotations

from pathlib import Path

from wet_run.portraits import PortraitManager
from wet_run.portraits.manager import parse_color


def test_parse_color_named() -> None:
    assert parse_color("red") == (255, 0, 64)
    assert parse_color("green") == (0, 255, 0)
    assert parse_color("cyan") == (0, 255, 255)
    assert parse_color("white") == (255, 255, 255)


def test_parse_color_tuple() -> None:
    assert parse_color((100, 150, 200)) == (100, 150, 200)
    assert parse_color([10, 20, 30]) == (10, 20, 30)


def test_parse_color_unknown_falls_back_to_white() -> None:
    assert parse_color("nonexistent") == (255, 255, 255)
    assert parse_color("") == (255, 255, 255)


def test_portrait_manager_loads(data_dir: Path) -> None:
    pm = PortraitManager(data_dir=data_dir / "portraits")
    player = pm.get("player")
    assert player["ascii"] == "◉P◉"
    assert player["color"] == (0, 255, 0)  # green
    assert player["name"] == "you"


def test_portrait_manager_ice(data_dir: Path) -> None:
    pm = PortraitManager(data_dir=data_dir / "portraits")
    ice = pm.get("ice.standard")
    assert "ICE" in ice["ascii"]
    assert ice["color"] == (255, 0, 255)  # magenta


def test_portrait_manager_missing_returns_default() -> None:
    pm = PortraitManager(data_dir=Path("/nonexistent"))
    portrait = pm.get("unknown")
    assert portrait["ascii"] == "????"
    assert portrait["color"] == (255, 255, 255)


def test_portrait_manager_has() -> None:
    pm = PortraitManager(data_dir=Path("/nonexistent"))
    assert not pm.has("player")
    assert not pm.has("anything")


def test_portrait_manager_empty_dir(tmp_path: Path) -> None:
    pm = PortraitManager(data_dir=tmp_path)
    assert len(pm) == 0
    portrait = pm.get("player")
    assert portrait["ascii"] == "????"

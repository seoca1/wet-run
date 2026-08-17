"""Tests for v0.5 movement stats (mobility improvement).

Covers:
- AppState default values (movement_step_count=0, nodes_visited=set())
- Field type safety
- _draw_mobility_stats rendering
"""

from __future__ import annotations

from unittest.mock import MagicMock

from wet_run.engine.matrix_view import _draw_mobility_stats
from wet_run.engine.state import AppState


class TestMobilityStatsDefaults:
    def test_default_step_count_zero(self) -> None:
        state = AppState()
        assert state.movement_step_count == 0

    def test_default_visited_empty(self) -> None:
        state = AppState()
        assert state.nodes_visited == set()

    def test_visited_tracks_unique_nodes(self) -> None:
        state = AppState()
        state.nodes_visited.add("node_a")
        state.nodes_visited.add("node_a")  # duplicate
        state.nodes_visited.add("node_b")
        assert len(state.nodes_visited) == 2


class TestMobilityStatsTracking:
    def test_increment_step(self) -> None:
        state = AppState()
        state.movement_step_count += 1
        state.movement_step_count += 1
        state.movement_step_count += 1
        assert state.movement_step_count == 3

    def test_movement_loop(self) -> None:
        """Simulate a player moving through 5 nodes."""
        state = AppState()
        for nid in ["a", "b", "c", "d", "e"]:
            state.movement_step_count += 1
            state.nodes_visited.add(nid)
        assert state.movement_step_count == 5
        assert len(state.nodes_visited) == 5


class TestMobilityStatsRender:
    def test_draw_writes_step_and_visited(self) -> None:
        state = AppState()
        state.movement_step_count = 7
        state.nodes_visited.add("n1")
        state.nodes_visited.add("n2")
        state.nodes_visited.add("n3")
        console = MagicMock()
        side = MagicMock()
        side.x = 40
        side.y2 = 28
        side.w = 38
        _draw_mobility_stats(console, state, side)
        console.print.assert_called_once()
        call_kwargs = console.print.call_args
        assert "Steps: 7" in call_kwargs.kwargs["string"]
        assert "Visited: 3" in call_kwargs.kwargs["string"]

    def test_draw_with_zero(self) -> None:
        state = AppState()
        console = MagicMock()
        side = MagicMock()
        side.x = 0
        side.y2 = 0
        side.w = 40
        _draw_mobility_stats(console, state, side)
        assert "Steps: 0" in console.print.call_args.kwargs["string"]
        assert "Visited: 0" in console.print.call_args.kwargs["string"]

    def test_draw_uses_light_blue_fg(self) -> None:
        """Light blue (128, 200, 255) is the mobility stats color."""
        state = AppState()
        console = MagicMock()
        side = MagicMock()
        side.x = 0
        side.y2 = 0
        side.w = 40
        _draw_mobility_stats(console, state, side)
        assert console.print.call_args.kwargs["fg"] == (128, 200, 255)

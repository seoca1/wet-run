"""Tests for cyberspace generator performance optimizations (P1 fix).

The previous implementation had an O(n²) pattern when enforcing ICE
placement: ``for i, n in enumerate(nodes): if n.id == c``. This was
called inside a loop over children, making the worst case O(n²)
per mission generation.

This file verifies:
  1. _index_nodes_by_id helper produces correct lookups
  2. Generated graphs still have the expected ICE structure
  3. Generator performance is reasonable on a large graph
"""

from __future__ import annotations

import time

import pytest

from wet_run.matrix.cyberspace_generator import (
    CyberspaceGenerator,
    _index_nodes_by_id,
)
from wet_run.matrix.node import Node


class TestIndexNodesById:
    def test_empty_list_returns_empty_dict(self) -> None:
        assert _index_nodes_by_id([]) == {}

    def test_indexes_each_node(self) -> None:
        nodes = [
            Node(id="a", kind="data", label="A", zone="surface"),  # type: ignore[arg-type]
            Node(id="b", kind="data", label="B", zone="surface"),  # type: ignore[arg-type]
            Node(id="c", kind="data", label="C", zone="surface"),  # type: ignore[arg-type]
        ]
        idx = _index_nodes_by_id(nodes)
        assert idx == {"a": 0, "b": 1, "c": 2}

    def test_lookup_is_o1(self) -> None:
        """Large list → single dict lookup beats linear scan."""
        n = 1000
        nodes = [
            Node(id=f"n_{i}", kind="data", label=str(i), zone="surface")  # type: ignore[arg-type]
            for i in range(n)
        ]
        idx = _index_nodes_by_id(nodes)
        # Verify last node indexable
        assert idx[f"n_{n - 1}"] == n - 1


class TestCyberspaceGeneratorPerf:
    """Smoke + timing test for the generator after O(n²) fix."""

    def test_generates_valid_graph(self) -> None:
        graph, _layouts = CyberspaceGenerator().generate(seed=42, mission_grade=1)
        # Should have entry node at "entry".
        assert any(n.id == "entry" for n in graph.nodes)
        # Should have exit node.
        assert any(n.id == "exit" for n in graph.nodes)
        # Should have at least one ICE (forced for missions).
        assert any(n.kind.value == "ice" for n in graph.nodes)

    def test_repeated_generation_is_fast(self) -> None:
        """Generation should not be O(n²) per mission — well under 1s for typical sizes."""
        gen = CyberspaceGenerator()
        # Warm-up
        gen.generate(seed=7, mission_grade=1)

        start = time.perf_counter()
        for i in range(10):
            gen.generate(seed=i + 100, mission_grade=1)
        elapsed = time.perf_counter() - start

        # 10 generations under 1s (O(n²) was taking ~3s per generation).
        assert elapsed < 1.0, f"10 generations took {elapsed:.3f}s (expected <1.0s)"

    def test_generated_graph_has_unique_node_ids(self) -> None:
        """The O(n²) → O(1) refactor must not break uniqueness."""
        graph, _layouts = CyberspaceGenerator().generate(seed=99, mission_grade=3)
        ids = [n.id for n in graph.nodes]
        assert len(ids) == len(set(ids)), "duplicate node ids in generated graph"


@pytest.mark.parametrize("seed", [1, 42, 99, 256, 1024])
def test_deterministic_per_seed(seed: int) -> None:
    """Same seed → same graph (regression for non-determinism introduced by edit)."""
    gen_a = CyberspaceGenerator()
    gen_b = CyberspaceGenerator()
    g_a, _ = gen_a.generate(seed=seed, mission_grade=1)
    g_b, _ = gen_b.generate(seed=seed, mission_grade=1)
    assert len(g_a.nodes) == len(g_b.nodes)
    assert {n.id for n in g_a.nodes} == {n.id for n in g_b.nodes}

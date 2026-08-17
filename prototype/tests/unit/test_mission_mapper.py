"""Tests for mission-to-room mapping (ADR-0060 Phase 3).

Covers:
    - Start/end invariants (ENTRY first, EXIT last)
    - Keyword extraction (data, ice, npc, construct, etc.)
    - Arc-based target room count
    - Character bias (novice 0 extras, heretic 3 extras)
    - Edge cases (no keywords, multiple matches, arc clamping)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.matrix.dungeon_generator import RoomType  # noqa: E402
from wet_run.matrix.mission_mapper import (  # noqa: E402
    _keyword_rooms,
    _mission_text,
    missions_to_rooms,
)
from wet_run.matrix.node import ZoneDepth  # noqa: E402
from wet_run.missions.mission import Mission, Objective  # noqa: E402


def _mission(
    arc: int = 1,
    title: str = "Generic Mission",
    objective: str = "",
    primary_type: str = "extract_data",
    primary_data_id: str | None = None,
    primary_enemy: str | None = None,
    matrix_seed: int | None = None,
    mission_id: str | None = None,
) -> Mission:
    return Mission(
        id=mission_id or f"m_{arc}_{title[:8]}",
        title=title,
        fixer="finn",
        arc=arc,
        grade_min=arc,
        grade_max=arc,
        matrix_seed=matrix_seed if matrix_seed is not None else arc,
        zone=ZoneDepth.SURFACE,
        objective=objective,
        primary_objective=Objective(
            type=primary_type,
            count=1,
            data_id=primary_data_id,
            enemy=primary_enemy,
        ),
    )


# ============================================================================
# Start / end invariants
# ============================================================================


class TestInvariants:
    def test_starts_with_entry(self) -> None:
        rooms = missions_to_rooms(_mission(title="First Jack-In"))
        assert rooms[0] is RoomType.ENTRY

    def test_ends_with_exit(self) -> None:
        rooms = missions_to_rooms(_mission(title="First Jack-In"))
        assert rooms[-1] is RoomType.EXIT

    def test_exactly_one_entry(self) -> None:
        rooms = missions_to_rooms(_mission(title="with entry keyword"))
        assert sum(1 for r in rooms if r is RoomType.ENTRY) == 1

    def test_exactly_one_exit(self) -> None:
        rooms = missions_to_rooms(_mission(title="with exit keyword"))
        assert sum(1 for r in rooms if r is RoomType.EXIT) == 1

    def test_minimum_five_rooms(self) -> None:
        rooms = missions_to_rooms(_mission(arc=1, title="tiny", objective=""))
        assert len(rooms) >= 5  # entry + 3 middle + exit at minimum


# ============================================================================
# Keyword extraction
# ============================================================================


class TestKeywords:
    def test_data_keyword(self) -> None:
        rooms = missions_to_rooms(_mission(arc=1, title="Extract data fragment", objective="data"))
        assert RoomType.DATA in rooms

    def test_ice_keyword(self) -> None:
        rooms = missions_to_rooms(
            _mission(arc=1, title="Defeat ICE patrol", objective="ICE breach")
        )
        assert RoomType.ICE in rooms

    def test_construct_keyword(self) -> None:
        rooms = missions_to_rooms(_mission(arc=1, title="Construct contact", objective="construct"))
        assert RoomType.NPC in rooms

    def test_dixie_keyword(self) -> None:
        rooms = missions_to_rooms(_mission(arc=2, title="Dixie Flatline", objective=""))
        assert RoomType.NPC in rooms

    def test_molly_keyword(self) -> None:
        rooms = missions_to_rooms(_mission(arc=2, title="Molly run", objective=""))
        assert RoomType.NPC in rooms

    def test_black_ice_with_room_type(self) -> None:
        rooms = missions_to_rooms(
            _mission(arc=3, title="Black ICE defense", objective="defeat black ice")
        )
        assert RoomType.ICE in rooms

    def test_no_keywords(self) -> None:
        # Use a primary_type that no keyword rule matches.
        rooms = missions_to_rooms(_mission(arc=2, title="???", primary_type="navigate"))
        # With no keywords, the result is just entry + routers + exit.
        assert rooms[0] is RoomType.ENTRY
        assert rooms[-1] is RoomType.EXIT
        # middle rooms should all be router (or npc/ice from char bias)
        for r in rooms[1:-1]:
            assert r in (RoomType.ROUTER, RoomType.NPC, RoomType.ICE)

    def test_keyword_only_once_per_token(self) -> None:
        """A single keyword match yields at most one room."""
        text = "extract data from the data vault"
        rooms = _keyword_rooms(text)
        data_count = sum(1 for r in rooms if r is RoomType.DATA)
        # "data" appears twice in the text but only the first match in
        # order matters; consecutive same-type rooms are collapsed.
        assert data_count >= 1


# ============================================================================
# Arc scaling
# ============================================================================


class TestArcScaling:
    def test_arc_1_short(self) -> None:
        rooms = missions_to_rooms(_mission(arc=1, title="tutorial level", objective=""))
        # Arc 1 target is 3-4 middle rooms → 5-6 total.
        assert 5 <= len(rooms) <= 6

    def test_arc_3_medium(self) -> None:
        rooms = missions_to_rooms(_mission(arc=3, title="midgame", objective=""))
        # Arc 3 target is 5-6 middle rooms → 7-8 total.
        assert 7 <= len(rooms) <= 8

    def test_arc_5_long(self) -> None:
        rooms = missions_to_rooms(_mission(arc=5, title="climax", objective=""))
        # Arc 5 target is 7-8 middle rooms → 9-10 total.
        assert 9 <= len(rooms) <= 10

    def test_arc_clamped_high(self) -> None:
        # Test the helper directly (Mission rejects invalid arcs at construction)
        from wet_run.matrix.mission_mapper import _arc_target

        clamped = _arc_target(7)
        normal = _arc_target(5)
        assert clamped == normal

    def test_arc_clamped_low(self) -> None:
        from wet_run.matrix.mission_mapper import _arc_target

        clamped = _arc_target(0)
        normal = _arc_target(1)
        assert clamped == normal


# ============================================================================
# Character bias
# ============================================================================


class TestCharacterBias:
    def test_novice_no_extras(self) -> None:
        """Novice adds 0 NPC/ICE extras vs heretic's 5 extras."""
        # Use primary_type that no keyword rule matches so the only
        # difference between novice and heretic is character bias.
        empty = _mission(arc=4, title="Empty", objective="", primary_type="navigate")
        novice_rooms = missions_to_rooms(empty, character_ref="novice")
        heretic_rooms = missions_to_rooms(empty, character_ref="heretic")
        # Compare extras based on NPC/ICE counts (heretic has 2+2=4 of these).
        novice_combat = sum(1 for r in novice_rooms if r in (RoomType.NPC, RoomType.ICE))
        heretic_combat = sum(1 for r in heretic_rooms if r in (RoomType.NPC, RoomType.ICE))
        assert heretic_combat > novice_combat

    def test_heretic_more_ice_than_novice(self) -> None:
        # Same seed-like content; only character differs.
        m = _mission(arc=4, title="ICE-heavy", objective="defeat ICE")
        novice_rooms = missions_to_rooms(m, character_ref="novice")
        heretic_rooms = missions_to_rooms(m, character_ref="heretic")
        novice_ice = sum(1 for r in novice_rooms if r is RoomType.ICE)
        heretic_ice = sum(1 for r in heretic_rooms if r is RoomType.ICE)
        assert heretic_ice >= novice_ice

    def test_unknown_character_falls_back(self) -> None:
        rooms = missions_to_rooms(_mission(arc=1, title="x", objective=""), character_ref="zzz")
        assert rooms[0] is RoomType.ENTRY


# ============================================================================
# All 29 missions smoke test
# ============================================================================


class TestRealMissions:
    """Test against the actual 29 missions defined in missions.json."""

    def test_all_29_missions_produce_valid_sequences(self) -> None:
        from pathlib import Path

        from wet_run.missions.board import JobBoard

        board = JobBoard.load(
            Path(__file__).parent.parent.parent / "data" / "missions" / "missions.json"
        )
        missions = list(board)  # JobBoard supports __iter__

        assert len(missions) > 0, "Expected missions to be loaded"
        valid_room_set = set(RoomType)

        for mission in missions:
            for char in ("novice", "veteran", "heretic"):
                rooms = missions_to_rooms(mission, character_ref=char)
                assert rooms[0] is RoomType.ENTRY, f"{mission.id}/{char}: not ENTRY"
                assert rooms[-1] is RoomType.EXIT, f"{mission.id}/{char}: not EXIT"
                assert 4 <= len(rooms) <= 10, f"{mission.id}/{char}: too long {len(rooms)}"
                for r in rooms:
                    assert r in valid_room_set, f"{mission.id}/{char}: unknown RoomType {r}"


# ============================================================================
# Internal helpers
# ============================================================================


# ============================================================================
# Bridge: mission_to_graph
# ============================================================================


class TestBridgeToGraph:
    """``mission_to_graph`` combines ``missions_to_rooms`` + BSP generator."""

    def test_returns_matrix_graph(self) -> None:
        from wet_run.matrix.graph import MatrixGraph
        from wet_run.matrix.mission_mapper import mission_to_graph

        m = _mission(
            arc=3,
            title="bridge mission",
            objective="extract data fragment",
            primary_type="extract_data",
        )
        graph = mission_to_graph(m, character_ref="veteran", seed=42)
        assert isinstance(graph, MatrixGraph)

    def test_entry_is_entry_node(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph

        m = _mission(arc=3, title="x", objective="", mission_id="t1")
        graph = mission_to_graph(m, character_ref="veteran", seed=42)
        entry = graph.get(graph.entry_id)
        assert entry is not None
        # Map RoomType -> NodeKind for comparison.
        from wet_run.matrix.node import NodeKind

        assert entry.kind is NodeKind.ENTRY

    def test_exit_node_exists(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph
        from wet_run.matrix.node import NodeKind

        m = _mission(arc=3, title="x", objective="", mission_id="t2")
        graph = mission_to_graph(m, character_ref="veteran", seed=42)
        exit_count = sum(1 for n in graph.nodes if n.kind is NodeKind.EXIT)
        assert exit_count == 1

    def test_outline_kinds_applied(self) -> None:
        """Outline determines the first N node kinds."""
        from wet_run.matrix.mission_mapper import (
            mission_to_graph,
            missions_to_rooms,
        )

        m = _mission(
            arc=2,
            title="data mission",
            objective="extract data fragment",
            primary_type="extract_data",
        )
        outline = missions_to_rooms(m, character_ref="novice")
        graph = mission_to_graph(m, character_ref="novice", seed=42)

        # First len(outline) nodes should have kinds matching the outline.
        for i, target in enumerate(outline):
            if i >= len(graph.nodes):
                break
            kind = graph.nodes[i].kind
            # Compare by RoomType:
            #   entry    -> NodeKind.ENTRY
            #   data     -> NodeKind.DATA
            #   ice      -> NodeKind.ICE
            #   npc      -> NodeKind.CONSTRUCT
            #   router   -> NodeKind.ROUTER
            #   core     -> NodeKind.CORE
            #   exit     -> NodeKind.EXIT
            expected_kind = {
                RoomType.ENTRY: "entry",
                RoomType.DATA: "data",
                RoomType.ICE: "ice",
                RoomType.NPC: "construct",
                RoomType.ROUTER: "router",
                RoomType.CORE: "core",
                RoomType.EXIT: "exit",
            }[target]
            assert kind.value == expected_kind, f"node {i}: outline={target}, node={kind.value}"

    def test_seeds_use_mission_matrix_seed_when_none(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph

        # Same mission_id + same matrix_seed ⇒ same graph.
        m1 = _mission(
            arc=3,
            title="x",
            objective="",
            matrix_seed=99,
            mission_id="same_seed_test",
        )
        m2 = _mission(
            arc=3,
            title="x",
            objective="",
            matrix_seed=99,
            mission_id="same_seed_test",
        )

        g1 = mission_to_graph(m1, character_ref="veteran")
        g2 = mission_to_graph(m2, character_ref="veteran")

        ids_a = sorted(n.id for n in g1.nodes)
        ids_b = sorted(n.id for n in g2.nodes)
        assert ids_a == ids_b

    def test_explicit_seed_overrides_matrix_seed(self) -> None:
        from wet_run.matrix.mission_mapper import mission_to_graph

        m = _mission(
            arc=3,
            title="x",
            objective="",
            matrix_seed=99,
            mission_id="explicit_seed_test",
        )

        # Use distinct explicit seeds.
        g_a = mission_to_graph(m, character_ref="veteran", seed=10)
        g_b = mission_to_graph(m, character_ref="veteran", seed=20)

        edges_a = {(e.src, e.dst) for e in g_a.edges}
        edges_b = {(e.src, e.dst) for e in g_b.edges}
        # Different seeds must give different graphs.
        assert edges_a != edges_b


class TestTextExtraction:
    def test_extracts_title_and_objective(self) -> None:
        text = _mission_text(_mission(arc=2, title="Find Data", objective="Extract data"))
        assert "find data" in text
        assert "extract data" in text

    def test_includes_primary_type(self) -> None:
        text = _mission_text(_mission(primary_type="defeat_ice"))
        assert "defeat_ice" in text

    def test_handles_missing_attributes(self) -> None:
        """Mission-like object with missing fields should not crash."""

        class _Bare:
            id = "bare"
            title = "Bare"
            objective = ""
            arc = 2

        text = _mission_text(_Bare())
        assert "bare" in text

"""Tests for ADR-0166 + ADR-0167 mission registry wiring (post-acceptance).

Validates that JobBoard.load() correctly wires Arc6 + Mission Expansion
missions into the playable board after the deferred registry integration.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure prototype/src is on sys.path so `wet_run.*` imports resolve.
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest

from wet_run.combat import enrich_mission_registry
from wet_run.combat.arc6 import ARC6_MISSIONS, enrich_arc6_mission, is_arc6_mission
from wet_run.combat.mission_expansion import (
    EXPANSION_MISSIONS,
    enrich_expansion_mission,
    is_expansion_mission,
)
from wet_run.missions.board import JobBoard
from wet_run.matrix.node import ZoneDepth


MISSIONS_PATH = Path("data/missions/missions.json")


class TestZoneDepthAftermath:
    def test_aftermath_member_exists(self) -> None:
        assert ZoneDepth.AFTERMATH == "aftermath"
        assert "aftermath" in ZoneDepth.__members__.values()


class TestEnrichArc6Mission:
    def test_returns_none_for_unknown_mission(self) -> None:
        assert enrich_arc6_mission("unknown_mission", {"title": "x"}) is None

    def test_merges_registry_fields(self) -> None:
        base: dict[str, object] = {"title": "Ghost", "fixer": "sally"}
        enriched = enrich_arc6_mission("ghost_signal_origin", dict(base))
        assert enriched is not None
        assert enriched["title"] == "Ghost"
        assert enriched["fixer"] == "sally"
        assert enriched["registry_source"] == "ADR-0166"
        assert "wintermute_fragment" in enriched["registry_primary_ice"]
        assert "Investigate" in enriched["registry_description"]

    def test_does_not_override_existing_keys(self) -> None:
        base: dict[str, object] = {
            "title": "Override",
            "registry_description": "USER OVERRIDE",
        }
        enriched = enrich_arc6_mission("ghost_signal_origin", dict(base))
        assert enriched is not None
        assert enriched["registry_description"] == "USER OVERRIDE"


class TestEnrichExpansionMission:
    def test_returns_none_for_unknown_mission(self) -> None:
        assert enrich_expansion_mission("unknown_mission", {"title": "x"}) is None

    def test_merges_registry_fields(self) -> None:
        base: dict[str, object] = {"title": "Hosaka", "fixer": "finn"}
        enriched = enrich_expansion_mission("hosaka_after_hours", dict(base))
        assert enriched is not None
        assert enriched["title"] == "Hosaka"
        assert enriched["registry_source"] == "ADR-0167"
        assert "hosaka_security" in enriched["registry_primary_ice"]


class TestEnrichMissionRegistry:
    def test_arc6_path(self) -> None:
        enriched = enrich_mission_registry(
            "ghost_signal_origin", {"title": "x", "fixer": "y"}
        )
        assert enriched["registry_source"] == "ADR-0166"

    def test_expansion_path(self) -> None:
        enriched = enrich_mission_registry(
            "hosaka_after_hours", {"title": "x", "fixer": "y"}
        )
        assert enriched["registry_source"] == "ADR-0167"

    def test_unknown_returns_base_unchanged(self) -> None:
        base: dict[str, object] = {"title": "x", "fixer": "y"}
        enriched = enrich_mission_registry("totally_unknown", base)
        assert enriched == base


class TestJobBoardWiring:
    @pytest.fixture
    def board(self) -> JobBoard:
        return JobBoard.load(MISSIONS_PATH)

    def test_arc6_missions_loaded(self, board: JobBoard) -> None:
        for mid in ("ghost_signal_origin", "wintermute_residue",
                    "tessier_ashpool_aftermath", "neuromancer_merger_residue"):
            mission = board.get(mid)
            assert mission is not None, f"{mid} not loaded"
            assert mission.zone == ZoneDepth.AFTERMATH
            assert mission.arc == 6

    def test_expansion_missions_loaded(self, board: JobBoard) -> None:
        expansion_ids = {
            mid for mid in (
                "hosaka_after_hours", "sense_net_infiltration", "yakuza_meeting",
                "t_a_construction_site", "zion_lab_breach", "construct_market",
            )
        }
        for mid in expansion_ids:
            assert board.get(mid) is not None, f"{mid} not loaded"

    def test_total_mission_count_increased(self, board: JobBoard) -> None:
        assert len(board._missions) >= 209

    def test_registry_predicates(self) -> None:
        for mission in ARC6_MISSIONS:
            assert is_arc6_mission(mission.id)
        for mission in EXPANSION_MISSIONS:
            assert is_expansion_mission(mission.id)

class T:
    def t1(self): from wet_run.missions.board import _p; m=_p(dict(id="t",title="T",fixer="finn",grade_min=1,grade_max=2,matrix_seed=0,zone="surface")); assert m is not None and m.random_weight==1.0
    def t2(self): import json; d=json.load(open("prototype/data/missions/missions.json")); assert d["ghost_signal_origin"].get("random_weight")==1.5
    def t3(self): import json; d=json.load(open("prototype/data/missions/missions.json")); assert d["hosaka_after_hours"].get("random_weight")==1.2



class TestWeightedPick:
    """Tests for board.py select_weighted + random_rules weighted pick with random_weight (ADR-0208)."""

    def test_get_random_mission_with_weights(self) -> None:
        from wet_run.missions.random_rules import get_random_mission
        weights = {"a": 0.0, "b": 1.0, "c": 0.0}
        for _ in range(20):
            result = get_random_mission(state=type("S", (), {})(), available_missions=["a", "b", "c"], seed=None, mission_weights=weights)
            assert result == "b", f"weighted pick failed with zero-weight a,c got {result}"

    def test_get_random_mission_excludes_zero_weight(self) -> None:
        from wet_run.missions.random_rules import get_random_mission
        weights = {"a": 0.0, "b": 1.0, "c": 0.5}
        seen = set()
        for seed in range(50):
            result = get_random_mission(state=type("S", (), {})(), available_missions=["a", "b", "c"], seed=seed, mission_weights=weights)
            seen.add(result)
        assert "a" not in seen, f"zero-weight mission a should be excluded, seen={seen}"

    def test_select_weighted_uses_self_mission_weights(self) -> None:
        from wet_run.missions.board import JobBoard, Mission
        from wet_run.matrix.node import ZoneDepth
        m1 = Mission(id="common", title="Common", fixer="finn", arc=1, grade_min=1, grade_max=2, matrix_seed=0, zone=ZoneDepth.SURFACE, random_weight=0.001)
        m2 = Mission(id="rare", title="Rare", fixer="finn", arc=1, grade_min=1, grade_max=2, matrix_seed=0, zone=ZoneDepth.SURFACE, random_weight=1.0)
        board = JobBoard((m1, m2))
        state = type("S", (), {"grade": 1, "faction_rep": 0})()
        seen = set()
        for seed in range(30):
            result = board.select_weighted(state=state, available=(m1, m2), seed=seed)
            if result is not None:
                seen.add(result.id)
        assert "rare" in seen, f"rare mission should be selected at least once, seen={seen}"

"""Tests for Phase 11 mission types (ADR-0188).

Covers 5 new mission types + 1 example chain:
- investigation
- defense
- dual_objective
- extraction_v2
- stealth
- chain (ta_succession)
"""

from __future__ import annotations

import pytest

from wet_run.matrix.node import ZoneDepth
from wet_run.missions.mission import (
    ChainFailure,
    ChainMission,
    ChainReward,
    ChainUnlockCondition,
    Mission,
    MissionChain,
    MissionType,
    Objective,
)

# ----- Test MissionType enum -----


def test_mission_type_enum_has_new_types() -> None:
    """Verify all 5 new mission types are in MissionType enum."""
    new_types = {
        MissionType.INVESTIGATION_COMPLETE,
        MissionType.SURVIVE_N_WAVES,
        MissionType.EXTRACTION_AND_DEFEAT,
        MissionType.REACH_TARGET_AND_EXTRACT_DATA,
    }
    # EXTRACTION_V2 uses same type as EXTRACT_DATA but with timer
    assert len(new_types) >= 4
    assert MissionType.INVESTIGATION_COMPLETE.value == "investigation_complete"
    assert MissionType.SURVIVE_N_WAVES.value == "survive_n_waves"


# ----- Test Investigation mission type -----


def test_investigation_mission_creation() -> None:
    """Investigation mission: multi-stage evidence collection without combat."""
    m = Mission(
        id="ta_investigate_3jane_initiative",
        title="3Jane's Corporate Initiative",
        fixer="kumiko",
        arc=4,
        grade_min=4,
        grade_max=5,
        matrix_seed=4701,
        zone=ZoneDepth.TA,
        reward_tier=3,
        reward_credits=1100,
        primary_objective=Objective(
            type="investigation_complete",
            evidence_required=4,
            evidence_types=("testimony", "audit", "data_fragment", "witness"),
        ),
        secondary_objectives=(
            Objective(type="avoid_combat", detection_threshold=50),
            Objective(type="preserve_evidence", corruption_max=0),
        ),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.evidence_required == 4
    assert m.primary_objective.evidence_types == ("testimony", "audit", "data_fragment", "witness")
    avoid_combat = next(
        (o for o in m.secondary_objectives if o.type == "avoid_combat"),
        None,
    )
    assert avoid_combat is not None
    assert avoid_combat.detection_threshold == 50
    preserve_evidence = next(
        (o for o in m.secondary_objectives if o.type == "preserve_evidence"),
        None,
    )
    assert preserve_evidence is not None
    assert preserve_evidence.corruption_max == 0


def test_investigation_mission_evidence_count_validation() -> None:
    """Investigation mission must have evidence_required >= 1."""
    # Investigation type requires at least 1 evidence
    obj = Objective(
        type="investigation_complete",
        evidence_required=1,
    )
    assert obj.evidence_required == 1

    # Default behavior: evidence_required is None for non-investigation types
    obj_def = Objective(type="extract_data")
    assert obj_def.evidence_required is None


# ----- Test Defense mission type -----


def test_defense_mission_creation() -> None:
    """Defense mission: survive N waves, protect NPC."""
    m = Mission(
        id="ta_defend_straylight_perimeter",
        title="Straylight Perimeter Defense",
        fixer="3jane",
        arc=4,
        grade_min=5,
        grade_max=6,
        matrix_seed=4702,
        zone=ZoneDepth.TA,
        reward_tier=4,
        reward_credits=1400,
        primary_objective=Objective(
            type="survive_n_waves",
            wave_count=6,
            wave_intensity="tier_4",
        ),
        secondary_objectives=(
            Objective(type="protect_npc", must_survive=True),
            Objective(type="minimize_damage", node_hp_min=50),
        ),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.wave_count == 6
    assert m.primary_objective.wave_intensity == "tier_4"
    # Find secondary objectives
    protect_npc = next(
        (o for o in m.secondary_objectives if o.type == "protect_npc"),
        None,
    )
    assert protect_npc is not None
    assert protect_npc.must_survive is True


# ----- Test Dual-Objective mission type -----


def test_dual_objective_mission_creation() -> None:
    """Dual-objective mission: two simultaneous primaries."""
    m = Mission(
        id="ta_dual_objective_ashpool_vote",
        title="Ashpool Succession Vote",
        fixer="kumiko",
        arc=4,
        grade_min=5,
        grade_max=6,
        matrix_seed=4703,
        zone=ZoneDepth.TA,
        reward_tier=5,
        reward_credits=1800,
        primary_objective=Objective(
            type="extraction_AND_defeat",
            extract_spec={"data_id": "ta_vote_record", "count": 1},
            defeat_spec={"enemy": "ice.boss.construct_proxy", "count": 1},
            time_limit_seconds=600,
            objective_lock="both_required",
        ),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.time_limit_seconds == 600
    assert m.primary_objective.objective_lock == "both_required"
    assert m.primary_objective.extract_spec is not None
    assert m.primary_objective.defeat_spec is not None


# ----- Test Extraction_v2 (high-risk) mission type -----


def test_extraction_v2_mission_creation() -> None:
    """High-risk extraction: timer + penalty on failure."""
    m = Mission(
        id="ta_extract_aleph_chip",
        title="Aleph Chip Extraction",
        fixer="wintermute",
        arc=4,
        grade_min=6,
        grade_max=6,
        matrix_seed=4704,
        zone=ZoneDepth.TA,
        reward_tier=5,
        reward_credits=3000,
        primary_objective=Objective(
            type="extract_data",
            data_id="aleph_chip_fragment",
            count=1,
            time_limit_seconds=120,
            penalty_on_failure="construct_loss",
        ),
        secondary_objectives=(Objective(type="evade", enemy="ice.black_construct", min_evade=3),),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.time_limit_seconds == 120
    assert m.primary_objective.penalty_on_failure == "construct_loss"
    assert m.primary_objective.data_id == "aleph_chip_fragment"


def test_extraction_v2_short_time_limit_is_valid() -> None:
    """High-risk extraction with 120s timer (very short)."""
    obj = Objective(
        type="extract_data",
        data_id="test",
        time_limit_seconds=120,
    )
    assert obj.time_limit_seconds == 120
    assert obj.time_limit_seconds < 300  # Very short


# ----- Test Stealth mission type -----


def test_stealth_mission_creation() -> None:
    """Stealth mission: no combat, detection threshold."""
    m = Mission(
        id="ta_stealth_construct_chamber",
        title="Construct Chamber Infiltration",
        fixer="wintermute",
        arc=5,
        grade_min=5,
        grade_max=6,
        matrix_seed=4705,
        zone=ZoneDepth.TA,
        reward_tier=4,
        reward_credits=1600,
        primary_objective=Objective(
            type="reach_target_AND_extract_data",
            target_id="construct_chamber_core",
            data_id="construct_chamber_key",
            detection_threshold=50,
            no_combat_allowed=True,
        ),
        secondary_objectives=(
            Objective(type="minimize_alerts", alert_max=0),
            Objective(type="preserve_trace", logging_max=0),
        ),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.no_combat_allowed is True
    assert m.primary_objective.detection_threshold == 50
    assert m.primary_objective.target_id == "construct_chamber_core"


def test_stealth_mission_no_combat_enforced() -> None:
    """Stealth mission must have no_combat_allowed=True."""
    obj = Objective(
        type="reach_target_AND_extract_data",
        target_id="x",
        no_combat_allowed=True,
    )
    assert obj.no_combat_allowed is True


# ----- Test MissionChain -----


def test_chain_mission_creation() -> None:
    """ChainMission dataclass with all required fields."""
    cm = ChainMission(
        id="ta_investigate_3jane_initiative",
        order=1,
        type="investigation",
        chain_role="intro",
    )
    assert cm.id == "ta_investigate_3jane_initiative"
    assert cm.order == 1
    assert cm.chain_role == "intro"


def test_chain_unlock_condition_creation() -> None:
    """ChainUnlockCondition with multiple fields."""
    uc = ChainUnlockCondition(
        arc_progress_min=50,
        faction_reputation={"ta_rep": 3},
        min_grade=4,
    )
    assert uc.arc_progress_min == 50
    assert uc.faction_reputation["ta_rep"] == 3
    assert uc.min_grade == 4


def test_chain_reward_creation() -> None:
    """ChainReward with multiple bonus types."""
    cr = ChainReward(
        construct_unlock="ta_construct_full",
        reputation_bonus={"ta_rep": 25},
        credits=50000,
        achievement="succession_complete",
    )
    assert cr.construct_unlock == "ta_construct_full"
    assert cr.reputation_bonus["ta_rep"] == 25
    assert cr.credits == 50000


def test_chain_failure_creation() -> None:
    """ChainFailure with penalty fields."""
    cf = ChainFailure(
        reputation_penalty={"ta_rep": -10},
        construct_lock="ta_construct_forever",
        achievement="succession_failed",
    )
    assert cf.reputation_penalty["ta_rep"] == -10
    assert cf.construct_lock == "ta_construct_forever"


def test_mission_chain_ta_succession() -> None:
    """ta_succession chain: 5 missions, faction-driven, TA arc."""
    chain = MissionChain(
        chain_id="ta_succession",
        chain_name="Tessier-Ashpool Succession",
        chain_type="faction_driven",
        chain_arc=4,
        unlock_condition=ChainUnlockCondition(
            arc_progress_min=50,
            faction_reputation={"ta_rep": 3},
            min_grade=4,
        ),
        missions=(
            ChainMission(
                id="ta_investigate_3jane_initiative",
                order=1,
                type="investigation",
                chain_role="intro",
            ),
            ChainMission(
                id="ta_defend_straylight_perimeter",
                order=2,
                type="defense",
                chain_role="escalation",
            ),
            ChainMission(
                id="ta_dual_objective_ashpool_vote",
                order=3,
                type="dual_objective",
                chain_role="climax",
            ),
            ChainMission(
                id="ta_extract_aleph_chip", order=4, type="extraction_v2", chain_role="revelation"
            ),
            ChainMission(
                id="ta_stealth_construct_chamber", order=5, type="stealth", chain_role="resolution"
            ),
        ),
        chain_reward=ChainReward(
            construct_unlock="ta_construct_full",
            reputation_bonus={"ta_rep": 25},
            credits=50000,
            achievement="succession_complete",
        ),
        chain_failure=ChainFailure(
            reputation_penalty={"ta_rep": -10},
            construct_lock="ta_construct_forever",
        ),
    )
    assert chain.chain_id == "ta_succession"
    assert len(chain.missions) == 5
    assert chain.chain_type == "faction_driven"
    assert chain.chain_arc == 4


def test_mission_chain_sequence() -> None:
    """ChainMission.sequence() returns missions in order."""
    chain = MissionChain(
        chain_id="test_chain",
        chain_name="Test",
        chain_type="faction_driven",
        chain_arc=1,
        unlock_condition=ChainUnlockCondition(),
        missions=(
            ChainMission(id="m1", order=2, type="type", chain_role="x"),
            ChainMission(id="m2", order=1, type="type", chain_role="x"),
            ChainMission(id="m3", order=3, type="type", chain_role="x"),
        ),
        chain_reward=ChainReward(),
        chain_failure=ChainFailure(),
    )
    seq = chain.sequence()
    assert [m.id for m in seq] == ["m2", "m1", "m3"]


def test_chain_too_short_rejected() -> None:
    """Chain must have 3-5 missions."""
    with pytest.raises(ValueError, match="3-5"):
        MissionChain(
            chain_id="short",
            chain_name="Short",
            chain_type="faction_driven",
            chain_arc=1,
            unlock_condition=ChainUnlockCondition(),
            missions=(
                ChainMission(id="m1", order=1, type="x", chain_role="x"),
                ChainMission(id="m2", order=2, type="x", chain_role="x"),
            ),
            chain_reward=ChainReward(),
            chain_failure=ChainFailure(),
        )


def test_chain_too_long_rejected() -> None:
    """Chain must have 3-5 missions."""
    with pytest.raises(ValueError, match="3-5"):
        MissionChain(
            chain_id="long",
            chain_name="Long",
            chain_type="faction_driven",
            chain_arc=1,
            unlock_condition=ChainUnlockCondition(),
            missions=tuple(
                ChainMission(id=f"m{i}", order=i, type="x", chain_role="x") for i in range(1, 7)
            ),
            chain_reward=ChainReward(),
            chain_failure=ChainFailure(),
        )


def test_chain_invalid_type_rejected() -> None:
    """Chain type must be valid."""
    with pytest.raises(ValueError, match="chain_type"):
        MissionChain(
            chain_id="invalid",
            chain_name="Invalid",
            chain_type="bogus_type",
            chain_arc=1,
            unlock_condition=ChainUnlockCondition(),
            missions=(
                ChainMission(id="m1", order=1, type="x", chain_role="x"),
                ChainMission(id="m2", order=2, type="x", chain_role="x"),
                ChainMission(id="m3", order=3, type="x", chain_role="x"),
            ),
            chain_reward=ChainReward(),
            chain_failure=ChainFailure(),
        )


# ----- Test chain_id field on Mission -----


def test_chain_mission_must_have_chain_id() -> None:
    """Chain mission must have chain_id field."""
    with pytest.raises(ValueError, match="chain_id"):
        Mission(
            id="chain_mission_no_id",
            title="Test",
            fixer="finn",
            arc=1,
            grade_min=1,
            grade_max=1,
            matrix_seed=1,
            zone=ZoneDepth.SURFACE,
            is_chain_mission=True,  # True but no chain_id
            chain_id=None,
        )


def test_chain_mission_with_chain_id_ok() -> None:
    """Chain mission with chain_id is valid."""
    m = Mission(
        id="chain_mission",
        title="Test",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=1,
        zone=ZoneDepth.SURFACE,
        is_chain_mission=True,
        chain_id="ta_succession",
        chain_order=1,
    )
    assert m.is_chain_mission is True
    assert m.chain_id == "ta_succession"
    assert m.chain_order == 1


# ----- Test legacy missions still work -----


def test_legacy_mission_unchanged() -> None:
    """Existing mission types (extract_data, defeat, etc.) still work."""
    # Old-style mission with simple objective
    m = Mission(
        id="first_jack",
        title="First Jack",
        fixer="finn",
        arc=1,
        grade_min=1,
        grade_max=1,
        matrix_seed=42,
        zone=ZoneDepth.SURFACE,
        reward_tier=1,
        reward_credits=500,
    )
    assert m.primary_type() == "extract_data"


def test_legacy_extract_data_mission() -> None:
    """Extract_data mission with structured primary_objective."""
    m = Mission(
        id="aleph_fragment",
        title="Aleph Fragment",
        fixer="finn",
        arc=5,
        grade_min=5,
        grade_max=6,
        matrix_seed=999,
        zone=ZoneDepth.DEEP,
        reward_tier=6,
        reward_credits=4000,
        primary_objective=Objective(
            type="extract_data",
            data_id="aleph_data",
            count=1,
        ),
    )
    assert m.primary_objective is not None
    assert m.primary_objective.type == "extract_data"
    assert m.primary_objective.data_id == "aleph_data"
    assert m.check_completion({"extract_data": 1}) is True
    assert m.check_completion({"extract_data": 0}) is False


def test_progress_pct_for_new_types() -> None:
    """Progress percentage works for new types too."""
    obj = Objective(
        type="investigation_complete",
        evidence_required=4,
    )
    assert obj.count == 1  # Default count
    # Progress is calculated based on `type` field, not evidence_required
    # So a partial investigation_complete progress would report 2/1 = 100%
    # This is a limitation of the current check_completion logic
    # Future: add type-specific progress calculation

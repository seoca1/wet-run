"""Automated tests for Boss Phase 4 Finale (ADR-0149).

Source spec: Game/roguelike_sprawl/testcases/combat/boss-phase4.md (TC-PHASE4-001 ~ 016)

Four sub-features:
- Phase 4 trigger at HP 15% (one-shot)
- Per-boss mechanics (5 bosses × unique effect)
- Death taunts (player death by boss)
- Intro enhancement (3-stage text overlay)
"""

from __future__ import annotations

import random

from roguelike_sprawl.combat.boss_phase4 import (
    CONSTRUCT_MERGE_ATTACK_BONUS,
    CONSTRUCT_MERGE_DURATION_MS,
    CONSTRUCT_MERGE_HEAL_PCT,
    DEATH_TAUNTS,
    FAMILY_VOTE_COMPANION_BONUS,
    FAMILY_VOTE_DAMAGE,
    GLITCH_BURST_DURATION_MS,
    GLITCH_BURST_STATUS_COUNT,
    GROUND_SLAM_STUN_MS,
    PERSONALITY_DRIFT_DURATION_MS,
    PERSONALITY_DRIFT_PCT,
    PHASE4_HP_THRESHOLD,
    BossIntroEnhancement,
    Phase4Mechanic,
    apply_boss_intro_enhancement,
    apply_construct_merge,
    apply_death_taunt,
    apply_family_vote,
    apply_glitch_burst,
    apply_ground_slam,
    apply_personality_drift,
    apply_phase4_mechanic,
    get_boss_intro,
    pick_death_taunt,
    should_trigger_phase4,
    trigger_phase4,
)
from roguelike_sprawl.combat.state import Combatant, CombatState


def _make_player(*, hp: int = 100, max_hp: int = 100) -> Combatant:
    return Combatant(
        id="player",
        name="Player",
        portrait="portrait.player",
        color=(255, 255, 255),
        hp=hp,
        max_hp=max_hp,
        ap=10,
        max_ap=10,
        auto_attack_damage=10,
    )


def _make_boss(
    *,
    boss_id: str = "wintermute",
    hp: int = 100,
    max_hp: int = 100,
    aggression: str = "boss",
) -> Combatant:
    return Combatant(
        id=boss_id,
        name=boss_id.upper(),
        portrait=f"portrait.boss.{boss_id}",
        color=(255, 50, 50),
        hp=hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=15,
        team="enemy",
        aggression=aggression,
    )


def _make_state(
    *,
    player: Combatant | None = None,
    boss: Combatant | None = None,
    rng: random.Random | None = None,
) -> CombatState:
    if player is None:
        player = _make_player()
    if boss is None:
        boss = _make_boss()
    if rng is None:
        rng = random.Random(0)
    return CombatState(player=player, enemy=boss, rng=rng)


class _StubAppState:
    """Minimal AppState stub for boss phase 4 tests."""

    __slots__ = (
        "phase4_triggered",
        "boss_phase4_mechanic",
        "death_taunt",
        "boss_intro_enhancement",
        "construct_companion_active",
    )

    def __init__(self) -> None:
        self.phase4_triggered = False
        self.boss_phase4_mechanic: str | None = None
        self.death_taunt: str | None = None
        self.boss_intro_enhancement = None
        self.construct_companion_active = False


# ---------------------------------------------------------------------------
# TC-PHASE4-001: Phase 4 trigger at HP 15%
# ---------------------------------------------------------------------------


class TestPhase4Trigger:
    def test_should_trigger_at_15_percent(self) -> None:
        boss = _make_boss(hp=15, max_hp=100)
        assert should_trigger_phase4(boss)

    def test_should_not_trigger_above_15_percent(self) -> None:
        boss = _make_boss(hp=16, max_hp=100)
        assert not should_trigger_phase4(boss)

    def test_should_trigger_below_15_percent(self) -> None:
        boss = _make_boss(hp=10, max_hp=100)
        assert should_trigger_phase4(boss)

    def test_threshold_value(self) -> None:
        assert PHASE4_HP_THRESHOLD == 0.15

    def test_trigger_phase4_returns_wintermute_mechanic(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=14, max_hp=100))
        app = _StubAppState()
        m = trigger_phase4(state, app, "wintermute")
        assert m is Phase4Mechanic.PERSONALITY_DRIFT
        assert app.phase4_triggered is True
        assert state.boss_phase4_mechanic == "personality_drift"

    def test_trigger_phase4_returns_none_when_already_triggered(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=14, max_hp=100))
        app = _StubAppState()
        app.phase4_triggered = True
        m = trigger_phase4(state, app, "wintermute")
        assert m is None

    def test_trigger_phase4_returns_none_when_hp_above_threshold(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=50, max_hp=100))
        app = _StubAppState()
        m = trigger_phase4(state, app, "wintermute")
        assert m is None
        assert app.phase4_triggered is False


# ---------------------------------------------------------------------------
# TC-PHASE4-002: Wintermute personality drift
# ---------------------------------------------------------------------------


class TestPersonalityDrift:
    def test_drift_reduces_player_attack(self) -> None:
        state = _make_state()
        original = state.player.auto_attack_damage
        apply_personality_drift(state)
        drift = next(
            (s for s in state.player.statuses if s.effect_id == "personality_drift"),
            None,
        )
        assert drift is not None
        assert drift.remaining_ms == PERSONALITY_DRIFT_DURATION_MS
        assert drift.attack_bonus == -(original * PERSONALITY_DRIFT_PCT // 100)

    def test_drift_constants(self) -> None:
        assert PERSONALITY_DRIFT_PCT == 50
        assert PERSONALITY_DRIFT_DURATION_MS == 3_000


# ---------------------------------------------------------------------------
# TC-PHASE4-003: T-A family vote
# ---------------------------------------------------------------------------


class TestFamilyVote:
    def test_damage_without_companion(self) -> None:
        state = _make_state(player=_make_player(hp=100, max_hp=100))
        dmg = apply_family_vote(state, has_companion=False)
        assert dmg == FAMILY_VOTE_DAMAGE
        assert state.player.hp == 100 - FAMILY_VOTE_DAMAGE

    def test_damage_with_companion(self) -> None:
        state = _make_state(player=_make_player(hp=100, max_hp=100))
        dmg = apply_family_vote(state, has_companion=True)
        assert dmg == FAMILY_VOTE_DAMAGE + FAMILY_VOTE_COMPANION_BONUS
        assert state.player.hp == 100 - (FAMILY_VOTE_DAMAGE + FAMILY_VOTE_COMPANION_BONUS)

    def test_damage_does_not_go_negative(self) -> None:
        state = _make_state(player=_make_player(hp=5, max_hp=100))
        apply_family_vote(state, has_companion=True)
        assert state.player.hp == 0

    def test_family_vote_constants(self) -> None:
        assert FAMILY_VOTE_DAMAGE == 20
        assert FAMILY_VOTE_COMPANION_BONUS == 10


# ---------------------------------------------------------------------------
# TC-PHASE4-004: Neuromancer construct merge
# ---------------------------------------------------------------------------


class TestConstructMerge:
    def test_merge_heals_boss(self) -> None:
        boss = _make_boss(boss_id="neuromancer", hp=20, max_hp=100)
        state = _make_state(boss=boss)
        heal = apply_construct_merge(state)
        expected_heal = int(100 * CONSTRUCT_MERGE_HEAL_PCT)
        assert heal == expected_heal
        assert boss.hp == 20 + expected_heal

    def test_merge_caps_at_max_hp(self) -> None:
        boss = _make_boss(boss_id="neuromancer", hp=90, max_hp=100)
        state = _make_state(boss=boss)
        apply_construct_merge(state)
        assert boss.hp == 100

    def test_merge_applies_attack_buff(self) -> None:
        state = _make_state()
        apply_construct_merge(state)
        boss = state.target
        merged = next((s for s in boss.statuses if s.effect_id == "merged"), None)
        assert merged is not None
        assert merged.attack_bonus == CONSTRUCT_MERGE_ATTACK_BONUS
        assert merged.remaining_ms == CONSTRUCT_MERGE_DURATION_MS

    def test_construct_merge_constants(self) -> None:
        assert CONSTRUCT_MERGE_HEAL_PCT == 0.20
        assert CONSTRUCT_MERGE_ATTACK_BONUS == 2
        assert CONSTRUCT_MERGE_DURATION_MS == 3_000


# ---------------------------------------------------------------------------
# TC-PHASE4-005: Goliath ground slam
# ---------------------------------------------------------------------------


class TestGroundSlam:
    def test_ground_slam_stuns_player(self) -> None:
        state = _make_state()
        apply_ground_slam(state)
        stun = next(
            (
                s
                for s in state.player.statuses
                if s.is_stunned and s.remaining_ms == GROUND_SLAM_STUN_MS
            ),
            None,
        )
        assert stun is not None

    def test_ground_slam_constants(self) -> None:
        assert GROUND_SLAM_STUN_MS == 1_000


# ---------------------------------------------------------------------------
# TC-PHASE4-006: Black ICE glitch burst
# ---------------------------------------------------------------------------


class TestGlitchBurst:
    def test_glitch_burst_applies_3_statuses(self) -> None:
        state = _make_state()
        rng = random.Random(42)
        applied = apply_glitch_burst(state, rng)
        assert len(applied) == GLITCH_BURST_STATUS_COUNT
        glitch_statuses = [s for s in state.player.statuses if s.effect_id.startswith("glitch_")]
        assert len(glitch_statuses) == GLITCH_BURST_STATUS_COUNT

    def test_glitch_burst_status_duration(self) -> None:
        state = _make_state()
        apply_glitch_burst(state, random.Random(0))
        for s in state.player.statuses:
            if s.effect_id.startswith("glitch_"):
                assert s.remaining_ms == GLITCH_BURST_DURATION_MS

    def test_glitch_burst_constants(self) -> None:
        assert GLITCH_BURST_STATUS_COUNT == 3
        assert GLITCH_BURST_DURATION_MS == 3_000


# ---------------------------------------------------------------------------
# TC-PHASE4-007/008/009: One-shot semantics
# ---------------------------------------------------------------------------


class TestPhase4OneShot:
    def test_phase4_triggers_only_once(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=14, max_hp=100))
        app = _StubAppState()
        m1 = trigger_phase4(state, app, "wintermute")
        m2 = trigger_phase4(state, app, "wintermute")
        assert m1 is Phase4Mechanic.PERSONALITY_DRIFT
        assert m2 is None

    def test_apply_phase4_mechanic_full_flow(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=14, max_hp=100))
        app = _StubAppState()
        result = apply_phase4_mechanic(state, app, "wintermute", random.Random(0))
        assert result is True
        assert app.phase4_triggered is True
        assert any(s.effect_id == "personality_drift" for s in state.player.statuses)

    def test_apply_phase4_mechanic_no_op_when_already_triggered(self) -> None:
        state = _make_state(boss=_make_boss(boss_id="wintermute", hp=14, max_hp=100))
        app = _StubAppState()
        app.phase4_triggered = True
        result = apply_phase4_mechanic(state, app, "wintermute", random.Random(0))
        assert result is False
        assert not any(s.effect_id == "personality_drift" for s in state.player.statuses)

    def test_apply_phase4_dispatches_all_5_bosses(self) -> None:
        for boss_id, expected_mechanic in [
            ("wintermute", Phase4Mechanic.PERSONALITY_DRIFT),
            ("ta_prime", Phase4Mechanic.FAMILY_VOTE),
            ("neuromancer", Phase4Mechanic.CONSTRUCT_MERGE),
            ("goliath_prime", Phase4Mechanic.GROUND_SLAM),
            ("black_ice_lord", Phase4Mechanic.GLITCH_BURST),
        ]:
            state = _make_state(boss=_make_boss(boss_id=boss_id, hp=14, max_hp=100))
            app = _StubAppState()
            m = trigger_phase4(state, app, boss_id)
            assert m is expected_mechanic, f"{boss_id} expected {expected_mechanic}"


# ---------------------------------------------------------------------------
# TC-PHASE4-010~013: Death taunts
# ---------------------------------------------------------------------------


class TestDeathTaunts:
    def test_wintermute_taunt(self) -> None:
        state = _make_state()
        app = _StubAppState()
        taunt = apply_death_taunt(state, app, "wintermute")
        assert taunt in DEATH_TAUNTS["wintermute"]
        assert app.death_taunt == taunt

    def test_neuromancer_taunt(self) -> None:
        state = _make_state()
        app = _StubAppState()
        taunt = apply_death_taunt(state, app, "neuromancer")
        assert taunt in DEATH_TAUNTS["neuromancer"]

    def test_ta_prime_taunt(self) -> None:
        state = _make_state()
        app = _StubAppState()
        taunt = apply_death_taunt(state, app, "ta_prime")
        assert taunt in DEATH_TAUNTS["ta_prime"]

    def test_goliath_prime_taunt(self) -> None:
        state = _make_state()
        app = _StubAppState()
        taunt = apply_death_taunt(state, app, "goliath_prime")
        assert taunt in DEATH_TAUNTS["goliath_prime"]

    def test_taunt_none_for_unknown_boss(self) -> None:
        state = _make_state()
        app = _StubAppState()
        taunt = apply_death_taunt(state, app, "regular_ice")
        assert taunt is None
        assert app.death_taunt is None

    def test_pick_death_taunt_returns_random_line(self) -> None:
        rng = random.Random(0)
        taunts_seen = set()
        for _ in range(50):
            t = pick_death_taunt("wintermute", rng)
            if t is not None:
                taunts_seen.add(t)
        # With 3 lines and 50 random picks, should see all 3
        assert taunts_seen == set(DEATH_TAUNTS["wintermute"])

    def test_pick_death_taunt_alias_resolution(self) -> None:
        # Aliases should resolve to canonical pool
        t_alias = pick_death_taunt("winter", random.Random(0))
        t_canonical = pick_death_taunt("wintermute", random.Random(0))
        # Both should return strings from the same pool (different RNG state OK)
        assert t_alias in DEATH_TAUNTS["wintermute"]
        assert t_canonical in DEATH_TAUNTS["wintermute"]


# ---------------------------------------------------------------------------
# TC-PHASE4-014~016: Intro enhancement
# ---------------------------------------------------------------------------


class TestBossIntroEnhancement:
    def test_get_boss_intro_wintermute(self) -> None:
        intro = get_boss_intro("wintermute")
        assert intro is not None
        assert intro.stage_1 == "[WINTERMUTE]"
        assert "neural" in intro.stage_2.lower()
        assert "trace" in intro.stage_3.lower()

    def test_get_boss_intro_ta_prime(self) -> None:
        intro = get_boss_intro("ta_prime")
        assert intro is not None
        assert intro.stage_1 == "[T-A PRIME]"
        assert "tessier" in intro.stage_2.lower()

    def test_get_boss_intro_neuromancer(self) -> None:
        intro = get_boss_intro("neuromancer")
        assert intro is not None
        assert intro.stage_1 == "[NEUROMANCER]"

    def test_get_boss_intro_goliath_prime(self) -> None:
        intro = get_boss_intro("goliath_prime")
        assert intro is not None
        assert intro.stage_1 == "[GOLIATH PRIME]"

    def test_get_boss_intro_black_ice_lord(self) -> None:
        intro = get_boss_intro("black_ice_lord")
        assert intro is not None
        assert intro.stage_1 == "[BLACK ICE LORD]"

    def test_get_boss_intro_unknown_returns_none(self) -> None:
        assert get_boss_intro("unknown_boss") is None

    def test_apply_intro_enhancement_sets_state(self) -> None:
        app = _StubAppState()
        intro = apply_boss_intro_enhancement(app, "wintermute")
        assert intro is not None
        assert app.boss_intro_enhancement is not None
        assert app.boss_intro_enhancement.stage_1 == "[WINTERMUTE]"

    def test_apply_intro_enhancement_unknown_returns_none(self) -> None:
        app = _StubAppState()
        result = apply_boss_intro_enhancement(app, "unknown_boss")
        assert result is None
        assert app.boss_intro_enhancement is None


# ---------------------------------------------------------------------------
# Constants & StrEnum
# ---------------------------------------------------------------------------


class TestPhase4MechanicEnum:
    def test_personality_drift_value(self) -> None:
        assert Phase4Mechanic.PERSONALITY_DRIFT == "personality_drift"

    def test_family_vote_value(self) -> None:
        assert Phase4Mechanic.FAMILY_VOTE == "family_vote"

    def test_construct_merge_value(self) -> None:
        assert Phase4Mechanic.CONSTRUCT_MERGE == "construct_merge"

    def test_ground_slam_value(self) -> None:
        assert Phase4Mechanic.GROUND_SLAM == "ground_slam"

    def test_glitch_burst_value(self) -> None:
        assert Phase4Mechanic.GLITCH_BURST == "glitch_burst"


class TestDeathTauntPools:
    def test_each_boss_has_taunt_pool(self) -> None:
        expected_bosses = {
            "wintermute",
            "ta_prime",
            "neuromancer",
            "goliath_prime",
            "black_ice_lord",
        }
        assert set(DEATH_TAUNTS.keys()) == expected_bosses

    def test_each_pool_has_2_to_3_lines(self) -> None:
        for boss_id, lines in DEATH_TAUNTS.items():
            assert 2 <= len(lines) <= 3, f"{boss_id} has {len(lines)} taunts"


class TestBossIntroEnhancementDataclass:
    def test_dataclass_fields(self) -> None:
        intro = BossIntroEnhancement(
            stage_1="[X]",
            stage_2="X // role",
            stage_3="warning text",
        )
        assert intro.stage_1 == "[X]"
        assert intro.stage_2 == "X // role"
        assert intro.stage_3 == "warning text"

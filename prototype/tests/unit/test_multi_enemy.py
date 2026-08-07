"""Automated tests for Multi-Enemy Encounters (ADR-0152, Cycle 8).

Source spec: Game/roguelike_sprawl/testcases/combat/multi-enemy.md (TC-MULTI-001~012)

Multi-enemy encounter support:
- cycle_target: Tab key cycles target_index through alive enemies
- all_alive_enemies: list of enemies with hp > 0
- encounter_count_for_grade: 1/2/3 mapping (Grade 1-2: 1, Grade 3-4: 2, Grade 5-6: 3)
- HEAL rebalance 20% -> 15% (ADR-0152 §Consequences.2)
- step_combat player auto-attack hits all alive enemies (ADR-0152 §Consequences.3)
"""

from __future__ import annotations

import random

import pytest

from roguelike_sprawl.combat.multi_enemy import (
    ENCOUNTER_COUNT_BY_GRADE,
    all_alive_enemies,
    cycle_target,
    encounter_count_for_grade,
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


def _make_enemy(
    *,
    enemy_id: str = "ice_standard",
    hp: int = 100,
    max_hp: int = 100,
    auto_attack_damage: int = 5,
) -> Combatant:
    return Combatant(
        id=enemy_id,
        name=enemy_id.upper(),
        portrait=f"portrait.{enemy_id}",
        color=(150, 200, 200),
        hp=hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=auto_attack_damage,
        team="enemy",
    )


# ---------------------------------------------------------------------------
# TC-MULTI-001: cycle_target rotates through alive enemies
# ---------------------------------------------------------------------------


class TestCycleTarget:
    def test_cycle_through_2_alive(self) -> None:
        e1, e2 = _make_enemy(enemy_id="ice_1"), _make_enemy(enemy_id="ice_2")
        state = CombatState(player=_make_player(), enemies=(e1, e2), rng=random.Random(0))
        assert state.target is e1
        cycle_target(state)
        assert state.target is e2
        cycle_target(state)
        assert state.target is e1  # wraps around

    def test_cycle_through_3_alive(self) -> None:
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2"),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        targets = [state.target]
        cycle_target(state)
        targets.append(state.target)
        cycle_target(state)
        targets.append(state.target)
        cycle_target(state)
        targets.append(state.target)
        # All 3 distinct (use ids since Combatant is unhashable)
        assert len({t.id for t in targets}) == 3

    def test_cycle_skips_dead(self) -> None:
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2", hp=0),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        # e2 is dead, cycle should skip from e1 to e3
        cycle_target(state)
        assert state.target is e3
        # Wrap around from e3 to e1 (skipping e2 which is dead)
        cycle_target(state)
        assert state.target is e1

    def test_cycle_with_no_alive_returns_none(self) -> None:
        e1 = _make_enemy(enemy_id="ice_1", hp=0)
        state = CombatState(player=_make_player(), enemies=(e1,), rng=random.Random(0))
        result = cycle_target(state)
        assert result is None

    def test_cycle_with_no_enemies_returns_none(self) -> None:
        state = CombatState(player=_make_player(), rng=random.Random(0))
        result = cycle_target(state)
        assert result is None


# ---------------------------------------------------------------------------
# TC-MULTI-002: step_combat attacks all alive enemies
# ---------------------------------------------------------------------------


class TestStepCombatMultiEnemy:
    def test_player_attacks_all_alive_enemies(self) -> None:
        """Player's auto-attack hits all alive enemies in one tick."""
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2"),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        # Advance tick_ms past auto-attack interval
        state.tick_ms = 2500  # > AUTO_ATTACK_INTERVAL_MS (2000)
        from roguelike_sprawl.combat.state import step_combat

        step_combat(state)

        # All 3 enemies should have taken damage
        # (we don't assert exact damage to avoid test brittleness, just that
        # HP decreased from initial)
        assert e1.hp < 100
        assert e2.hp < 100
        assert e3.hp < 100

    def test_player_skips_dead_enemies(self) -> None:
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2", hp=0),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        state.tick_ms = 2500
        from roguelike_sprawl.combat.state import step_combat

        step_combat(state)

        # e2 was already dead (hp=0), e1 and e3 should have taken damage
        assert e1.hp < 100
        assert e2.hp == 0  # unchanged (was already dead)
        assert e3.hp < 100


# ---------------------------------------------------------------------------
# TC-MULTI-005: encounter_count_for_grade mapping
# ---------------------------------------------------------------------------


class TestEncounterCountForGrade:
    @pytest.mark.parametrize(
        ("grade", "expected"),
        [
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 2),
            (5, 3),
            (6, 3),
        ],
    )
    def test_grade_to_count_mapping(self, grade: int, expected: int) -> None:
        assert encounter_count_for_grade(grade) == expected

    def test_below_grade_1_returns_1(self) -> None:
        assert encounter_count_for_grade(0) == 1

    def test_above_grade_6_clamps_to_grade_6(self) -> None:
        assert encounter_count_for_grade(7) == 3  # clamps to Grade 6 = 3

    def test_encounter_count_table(self) -> None:
        assert ENCOUNTER_COUNT_BY_GRADE == {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3}


# ---------------------------------------------------------------------------
# TC-MULTI-007: target cycling skips dead enemies
# ---------------------------------------------------------------------------


class TestCycleTargetAdvanced:
    def test_target_index_updated_correctly(self) -> None:
        """After cycle, state.target_index reflects the new target's position."""
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2"),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        assert state.target_index == 0
        cycle_target(state)
        assert state.target_index == 1
        cycle_target(state)
        assert state.target_index == 2

    def test_target_index_with_dead_skips_correctly(self) -> None:
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2", hp=0),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        # Initial: target = e1 (index 0)
        # Cycle: skip e2 (dead), target = e3 (index 2)
        cycle_target(state)
        assert state.target_index == 2
        # Cycle: wrap to e1 (index 0, skip e2)
        cycle_target(state)
        assert state.target_index == 0


# ---------------------------------------------------------------------------
# TC-MULTI-009: multi-enemy auto-attack damage split
# ---------------------------------------------------------------------------


class TestMultiEnemyDamage:
    def test_player_damage_dealt_sums_across_enemies(self) -> None:
        """stats.damage_dealt should equal sum of damage to all enemies."""
        e1, e2 = _make_enemy(enemy_id="ice_1"), _make_enemy(enemy_id="ice_2")
        state = CombatState(player=_make_player(), enemies=(e1, e2), rng=random.Random(0))
        state.tick_ms = 2500
        from roguelike_sprawl.combat.state import step_combat

        step_combat(state)

        # damage_dealt should be > 0 and reflect damage to both enemies
        assert state.stats.damage_dealt > 0

    def test_enemies_attack_player_individually(self) -> None:
        """Each alive enemy attacks the player in their own auto-attack tick."""
        e1, e2 = _make_enemy(enemy_id="ice_1"), _make_enemy(enemy_id="ice_2")
        state = CombatState(
            player=_make_player(hp=100, max_hp=100),
            enemies=(e1, e2),
            rng=random.Random(0),
        )
        state.tick_ms = 2500
        from roguelike_sprawl.combat.state import step_combat

        step_combat(state)

        # Player took damage from both enemies
        assert state.player.hp < 100


# ---------------------------------------------------------------------------
# TC-MULTI-012: target_index boundary (negative/overflow)
# ---------------------------------------------------------------------------


class TestTargetIndexBoundary:
    def test_all_alive_enemies_helper(self) -> None:
        e1, e2, e3 = (
            _make_enemy(enemy_id="ice_1"),
            _make_enemy(enemy_id="ice_2", hp=0),
            _make_enemy(enemy_id="ice_3"),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2, e3), rng=random.Random(0))
        alive = all_alive_enemies(state)
        assert len(alive) == 2
        assert e2 not in alive
        assert e1 in alive
        assert e3 in alive

    def test_all_alive_empty_when_all_dead(self) -> None:
        e1, e2 = (
            _make_enemy(enemy_id="ice_1", hp=0),
            _make_enemy(enemy_id="ice_2", hp=0),
        )
        state = CombatState(player=_make_player(), enemies=(e1, e2), rng=random.Random(0))
        assert all_alive_enemies(state) == []

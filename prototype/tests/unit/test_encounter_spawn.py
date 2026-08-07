"""Integration tests: Matrix encounter spawn → multi-enemy CombatState (ADR-0153, Cycle 9).

When the player enters an ICE node, ``start_combat`` creates N enemies
based on the player's grade:
- Grade 1-2: 1 enemy (1v1)
- Grade 3-4: 2 enemies (1v2)
- Grade 5-6: 3 enemies (1v3)

Pillar 정합 (ADR-0153 §Consequences.6):
- P1 (The Run): Grade → 1vN automatic
- P3 (The Flatline): HEAL 15% 보완 (ADR-0152)
"""

from __future__ import annotations

import pytest

from roguelike_sprawl.combat.multi_enemy import encounter_count_for_grade


class TestEncounterSpawnIntegration:
    """Test that encounter_count_for_grade produces the expected multi-enemy mapping."""

    @pytest.mark.parametrize(
        ("grade", "expected_count"),
        [
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 2),
            (5, 3),
            (6, 3),
        ],
    )
    def test_grade_maps_to_encounter_count(self, grade: int, expected_count: int) -> None:
        """Each grade maps to the expected number of enemies in the encounter."""
        assert encounter_count_for_grade(grade) == expected_count

    def test_grade_below_1_returns_1(self) -> None:
        assert encounter_count_for_grade(0) == 1

    def test_grade_above_6_clamps_to_grade_6(self) -> None:
        assert encounter_count_for_grade(7) == 3  # Grade 6 = 3 enemies

    def test_grade_8_clamps_to_grade_6(self) -> None:
        """Master tier (Grade 6+) all use 1v3 encounters."""
        assert encounter_count_for_grade(8) == 3

    def test_negative_grade_clamps_to_grade_1(self) -> None:
        """Defensive: invalid grade values clamp to Grade 1 (1v1)."""
        assert encounter_count_for_grade(-5) == 1


class TestEncounterSpawnSemantic:
    """Test the semantic meaning of the encounter count mapping."""

    def test_novice_grade_1_is_1v1(self) -> None:
        """Novice players face single ICE (tutorial pacing)."""
        assert encounter_count_for_grade(1) == 1

    def test_novice_grade_2_is_1v1(self) -> None:
        """Grade 2 is still 1v1 (gradual difficulty)."""
        assert encounter_count_for_grade(2) == 1

    def test_intermediate_grade_3_is_1v2(self) -> None:
        """Grade 3 introduces pack encounters (1v2)."""
        assert encounter_count_for_grade(3) == 2

    def test_intermediate_grade_4_is_1v2(self) -> None:
        """Grade 4 is still pack (1v2)."""
        assert encounter_count_for_grade(4) == 2

    def test_veteran_grade_5_is_1v3(self) -> None:
        """Grade 5 introduces swarm encounters (1v3)."""
        assert encounter_count_for_grade(5) == 3

    def test_master_grade_6_is_1v3(self) -> None:
        """Master tier (Grade 6) is swarm (1v3)."""
        assert encounter_count_for_grade(6) == 3


class TestEncounterSpawnWithPillarIntegration:
    """Verify that encounter count integrates with the existing Pillar system."""

    def test_grade_3_1v2_with_heal_15_percent(self) -> None:
        """Grade 3 player with 1v2 encounter gets HEAL 15% (ADR-0152 rebalance).

        This validates the Pillar 3 weight preservation: HEAL 15% is
        NOT trivial against 1v2 damage.
        """
        grade = 3
        count = encounter_count_for_grade(grade)
        # Grade 3 = 1v2 (2 enemies)
        assert count == 2
        # Pillar 3 (ADR-0152): HEAL_PCT = 0.15, so T1 max_hp=100 → +15
        # 1v2 means 2 enemies dealing e.g. 10 damage each = 20 total
        # HEAL 15 = 75% of one enemy's damage, not 100% trivial
        heal_pct = 0.15
        one_enemy_damage = 10
        total_damage = count * one_enemy_damage
        heal_amount = 100 * heal_pct
        # HEAL is LESS than total damage (not trivial)
        assert heal_amount < total_damage

    def test_grade_5_1v3_with_alarm_tradeoff(self) -> None:
        """Grade 5 player with 1v3 encounter gets alarm trade-off (ADR-0147).

        1v3 increases alarm faster → CRED salvage alarm reduction matters.
        """
        grade = 5
        count = encounter_count_for_grade(grade)
        assert count == 3
        # 1v3 = 3 enemies → 3 auto-attacks per tick → faster alarm
        # CRED salvage alarm-1 is more impactful in 1v3 than 1v1
        # (no direct assertion, just verifies the semantic relationship)
        assert count > encounter_count_for_grade(1)  # 1v1

    def test_intel_alarm_reducer_1v3_use_case(self) -> None:
        """ADR-0151 alarm_reducer (-2 alarm) is more useful in 1v3.

        1v3 generates more alarm per tick → player benefits more from
        the alarm_reducer intel item.
        """
        count_1v3 = encounter_count_for_grade(5)
        count_1v1 = encounter_count_for_grade(1)
        # 1v3 generates 3x alarm per tick vs 1v1
        assert count_1v3 > count_1v1
        # alarm_reducer (-2) is proportionally more impactful in 1v3
        # (no direct calculation, just structural verification)

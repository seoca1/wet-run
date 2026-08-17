"""Difficulty verification demo scenarios.

Verifies PPL vs Enemy scaling balance across different grades.

Usage:
    python scripts/combat_grades_demo.py              # Run all scenarios
    python scripts/combat_grades_demo.py --scenario A # Run only scenario A
    python scripts/combat_grades_demo.py --verbose    # Show detailed stats
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.combat import (
    CombatState,
    IceRegistry,
    build_default_player,
    build_ice_enemy,
    step_combat,
)
from wet_run.matrix.ppl import Loadout, Program, calculate_ppl

DEMO_SCENARIOS = {
    "A": {
        "name": "Grade 1 - Beginner",
        "grade": 1,
        "ppl": 5,
        "loadout": Loadout(
            deck_tier=1,
            programs=(Program(id="wisp", name="Wisp", tier=1),),
            wetware_tier=1,
        ),
        "enemies": [
            ("wisp", 1),
        ],
        "expected_difficulty": "normal",
    },
    "B": {
        "name": "Grade 3 - Intermediate",
        "grade": 3,
        "ppl": 22,
        "loadout": Loadout(
            deck_tier=2,
            programs=(
                Program(id="wisp", name="Wisp", tier=2),
                Program(id="goliath", name="Goliath", tier=2),
            ),
            wetware_tier=2,
        ),
        "enemies": [
            ("watchdog", 3),
            ("spider", 3),
        ],
        "expected_difficulty": "hard",
    },
    "C": {
        "name": "Grade 5 - Advanced",
        "grade": 5,
        "ppl": 45,
        "loadout": Loadout(
            deck_tier=4,
            programs=(
                Program(id="wisp", name="Wisp", tier=3),
                Program(id="goliath", name="Goliath", tier=3),
                Program(id="wardrone", name="Wardrone", tier=3),
            ),
            wetware_tier=4,
            construct_tier=2,
        ),
        "enemies": [
            ("black", 5),
            ("goliath", 5),
        ],
        "expected_difficulty": "hard",
    },
}


def calculate_enemy_power(ice_reg: IceRegistry, enemies: list[tuple[str, int]]) -> float:
    """Calculate total enemy power (weighted by HP * DMG)."""
    total = 0.0
    for ice_id, player_grade in enemies:
        data = ice_reg.get(ice_id)
        if data:
            hp, dmg = _get_scaled_stats_raw(data, player_grade)
            total += hp * dmg
    return total


def _get_scaled_stats_raw(data: dict, player_grade: int) -> tuple[int, int]:
    """Get scaled stats without the registry helper (for demo purposes)."""
    hp_base = int(data.get("hp_base", 80))
    hp_per_grade = int(data.get("hp_per_grade", 0))
    dmg_base = int(data.get("dmg_base", 3))
    dmg_per_grade = int(data.get("dmg_per_grade", 0))
    ice_tier = int(data.get("tier", 1))

    grade_diff = player_grade - ice_tier

    if grade_diff >= 0:
        hp = hp_base + (hp_per_grade * grade_diff)
        dmg = dmg_base + (dmg_per_grade * grade_diff)
    else:
        scale = 1.0 + (grade_diff * 0.15)
        scale = max(0.7, scale)
        hp = int(hp_base * scale)
        dmg = int(dmg_base * scale)

    return hp, dmg


def calculate_power_ratio(player_ppl: float, enemy_power: float) -> float:
    """Calculate PPL vs Enemy Power ratio."""
    if enemy_power == 0:
        return float("inf")
    return player_ppl / (enemy_power**0.5)


def get_difficulty_label(ratio: float) -> str:
    """Get difficulty label from power ratio."""
    if ratio >= 1.5:
        return "very_easy"
    elif ratio >= 1.2:
        return "easy"
    elif ratio >= 0.8:
        return "normal"
    elif ratio >= 0.5:
        return "hard"
    else:
        return "very_hard"


def simulate_combat(
    ice_reg: IceRegistry,
    scenario: dict,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """Simulate combat for a scenario and return results."""
    grade = scenario["grade"]
    loadout = scenario["loadout"]
    enemies_data = scenario["enemies"]

    player = build_default_player(
        loadout=loadout,
        max_hp=80 + (grade * 20),
        max_ap=6,
        base_damage=5 + (grade * 2),
    )

    enemies = []
    for ice_id, _ in enemies_data:
        enemy = build_ice_enemy(ice_id, ice_reg, player_grade=grade)
        enemies.append(enemy)

    main_enemy = enemies[0]

    if verbose:
        print(f"  Player HP: {player.max_hp}, PPL: {calculate_ppl(loadout)}")
        print(f"  Enemy HP: {main_enemy.max_hp}, DMG: {main_enemy.auto_attack_damage}")

    state = CombatState(player=player, enemy=main_enemy, rng=random.Random(seed))

    steps = 0
    max_steps = 500
    while not state.finished and steps < max_steps:
        step_combat(state)
        steps += 1

    outcome = state.outcome
    player_hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0

    return {
        "outcome": outcome,
        "steps": steps,
        "player_hp_remaining": player.hp,
        "player_hp_ratio": player_hp_ratio,
        "player_died": outcome == "defeat",
        "timeout": steps >= max_steps,
    }


def run_scenario(
    scenario_id: str, scenario: dict, ice_reg: IceRegistry, verbose: bool = False
) -> None:
    """Run a single scenario and display results."""
    print(f"\n{'=' * 60}")
    print(f"Scenario {scenario_id}: {scenario['name']}")
    print(f"{'=' * 60}")

    grade = scenario["grade"]
    loadout = scenario["loadout"]
    ppl = calculate_ppl(loadout)

    print(f"  Grade: {grade}")
    print(f"  PPL: {ppl}")
    print(f"  Loadout: Deck T{loadout.deck_tier}, Programs {[p.tier for p in loadout.programs]}")

    enemy_power = calculate_enemy_power(ice_reg, scenario["enemies"])
    ratio = calculate_power_ratio(ppl, enemy_power)
    difficulty = get_difficulty_label(ratio)

    print("\n  Enemies:")
    for ice_id, _ in scenario["enemies"]:
        data = ice_reg.get(ice_id)
        if data:
            hp, dmg = _get_scaled_stats_raw(data, grade)
            print(f"    - {data['name']}: HP={hp}, DMG={dmg}, Tier={data['tier']}")

    print(f"\n  Enemy Power: {enemy_power:.1f}")
    print(f"  Power Ratio: {ratio:.2f}")
    print(f"  Calculated Difficulty: {difficulty}")
    print(f"  Expected Difficulty: {scenario['expected_difficulty']}")

    if difficulty == scenario["expected_difficulty"]:
        print("  ✓ Difficulty matches expected!")
    else:
        print(
            f"  ⚠ Difficulty mismatch (expected {scenario['expected_difficulty']}, got {difficulty})"
        )

    if verbose:
        print("\n  Running combat simulation...")
        result = simulate_combat(ice_reg, scenario, seed=42, verbose=True)
        print("  Combat Result:")
        print(f"    Steps: {result['steps']}")
        print(f"    Outcome: {result['outcome']}")
        print(f"    Player HP: {result['player_hp_remaining']}/{scenario['grade'] * 20 + 80}")
        if result["player_died"]:
            print("    ⚠ Player died!")
        elif result["timeout"]:
            print("    ⚠ Combat timed out!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Combat difficulty verification demo")
    parser.add_argument("--scenario", choices=["A", "B", "C"], help="Run specific scenario")
    parser.add_argument("--verbose", action="store_true", help="Show detailed combat simulation")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"
    ice_reg = IceRegistry.load(data_dir / "combat" / "ice_types.json")

    scenarios_to_run = [args.scenario] if args.scenario else ["A", "B", "C"]

    print("=" * 60)
    print("Wet Run - Difficulty Verification Demo")
    print("=" * 60)

    for sid in scenarios_to_run:
        if sid in DEMO_SCENARIOS:
            run_scenario(sid, DEMO_SCENARIOS[sid], ice_reg, args.verbose)
        else:
            print(f"Unknown scenario: {sid}")

    print(f"\n{'=' * 60}")
    print("Summary")
    print("=" * 60)
    print("\nGrade/PPL vs Enemy Power Recommendations:")
    print("  Grade 1: PPL 3-12, fight T1 enemies (Wisp, Standard, Watchdog)")
    print("  Grade 2: PPL 10-20, fight T1-T2 enemies (add Raven)")
    print("  Grade 3: PPL 18-30, fight T2-T3 enemies (add Black, Goliath)")
    print("  Grade 4: PPL 28-42, fight T3-T4 enemies")
    print("  Grade 5: PPL 40-60, fight T4-T5 enemies (Dixie)")


if __name__ == "__main__":
    main()

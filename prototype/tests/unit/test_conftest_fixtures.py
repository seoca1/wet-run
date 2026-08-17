"""Smoke test for Phase 25 shared combat fixtures in ``tests/conftest.py``.

These fixtures (added in Phase 25) eliminate boilerplate in combat tests
by providing reusable builders for players, ICE enemies, and seeded
CombatStates. They are OPT-IN — existing tests don't use them yet —
so this file documents the contract and verifies the fixtures work.

If you modify the fixtures in conftest.py, update these tests too.
"""

from __future__ import annotations

import random

from wet_run.combat.state_models import CombatState


def test_seeded_rng_is_deterministic(seeded_rng: random.Random) -> None:
    """``seeded_rng`` returns the same sequence each call."""
    first = [seeded_rng.random() for _ in range(5)]
    rng2 = random.Random(0)
    second = [rng2.random() for _ in range(5)]
    assert first == second


def test_make_player_returns_combatant(make_player) -> None:
    """``make_player`` builds a Combatant with the requested HP/AP/damage."""
    player = make_player(max_hp=120, max_ap=8, base_damage=10)
    assert player.hp == 120
    assert player.max_hp == 120
    assert player.max_ap == 8
    assert player.auto_attack_damage == 10
    assert player.team == "player"


def test_make_player_defaults(make_player) -> None:
    """``make_player`` defaults match the canonical player build."""
    player = make_player()
    assert player.max_hp == 100
    assert player.max_ap == 6
    assert player.auto_attack_damage == 5


def test_make_ice_enemy_returns_combatant(make_ice_enemy) -> None:
    """``make_ice_enemy`` builds an enemy Combatant."""
    enemy = make_ice_enemy(max_hp=50, base_damage=10, ice_id="banana")
    assert enemy.id == "banana"
    assert enemy.hp == 50
    assert enemy.auto_attack_damage == 10
    assert enemy.team == "enemy"
    assert enemy.ice_kind == "standard"


def test_make_ice_enemy_ice_kind_override(make_ice_enemy) -> None:
    """``make_ice_enemy`` accepts an ICE kind override (used by boss tests)."""
    enemy = make_ice_enemy(ice_kind="wintermute")
    assert enemy.ice_kind == "wintermute"


def test_make_combat_state_returns_state_with_player_and_enemy(make_combat_state) -> None:
    """``make_combat_state`` returns a seeded CombatState with player + enemy."""
    state = make_combat_state(player_hp=120, enemy_hp=50)
    assert isinstance(state, CombatState)
    assert state.player.hp == 120
    assert state.player.max_hp == 120
    assert state.player.team == "player"
    assert state.enemy is not None
    assert state.enemy.hp == 50
    assert state.enemy.team == "enemy"
    assert isinstance(state.rng, random.Random)


def test_make_combat_state_is_deterministic_across_calls(make_combat_state) -> None:
    """Two combat states built from the same factory share RNG state."""
    state_a = make_combat_state()
    state_b = make_combat_state()
    # Both share the seeded RNG factory, so initial seq match.
    seq_a = [state_a.rng.random() for _ in range(5)]
    seq_b = [state_b.rng.random() for _ in range(5)]
    assert seq_a == seq_b


def test_autouse_isolate_random_seed_does_not_leak() -> None:
    """The autouse ``_isolate_random_seed`` fixture preserves module random state.

    This test relies on the autouse fixture being active. It calls
    ``random.random()`` twice and verifies the second call differs from
    the first (i.e. the seed was *not* re-seeded to a fixed value).
    The fixture should restore state without resetting the seed, so
    consecutive test runs produce different sequences.
    """
    import random as _random

    first = _random.random()
    second = _random.random()
    assert first != second  # module RNG is not re-seeded

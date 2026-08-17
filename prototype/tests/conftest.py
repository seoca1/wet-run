"""Pytest configuration and shared fixtures (Phase 25).

Provides project-wide fixtures:

* Path helpers — :func:`project_root`, :func:`data_dir`, :func:`saves_dir`
* RNG seeding — :func:`seeded_rng` for deterministic tests
* Combat builders — :func:`make_player`, :func:`make_ice_enemy`,
  :func:`make_combat_state` to eliminate boilerplate in combat tests

Per-Phase 23 + 24 flake fixes (combat RNG must be explicitly seeded in
each test that calls ``_calculate_damage`` / ``step_combat`` to avoid
variance flakes). Use ``seeded_rng`` for full determinism or accept a
seeded ``CombatState.rng`` from :func:`make_combat_state`.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from pathlib import Path

import pytest

# -----------------------------------------------------------------------------
# Path helpers
# -----------------------------------------------------------------------------


@pytest.fixture
def project_root() -> Path:
    """Return the prototype project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    """Return the data directory."""
    return project_root / "data"


@pytest.fixture
def saves_dir(data_dir: Path) -> Path:
    """Return the GN save directory (``data/saves``)."""
    return data_dir / "saves"


# -----------------------------------------------------------------------------
# RNG seeding (Phase 25: deterministic test infra)
# -----------------------------------------------------------------------------


@pytest.fixture
def seeded_rng() -> random.Random:
    """Provide a deterministic ``random.Random(0)`` instance.

    Used by combat tests that read from ``state.rng`` (damage variance,
    crit chance, enemy skill selection). Phase 23 + 24 flake fixes rely
    on every such test being reproducible — opt-in by requesting this
    fixture rather than building a fresh ``random.Random()`` ad-hoc.
    """
    return random.Random(0)


@pytest.fixture(autouse=True)
def _isolate_random_seed() -> Iterator[None]:
    """Auto-applied: snapshot and restore ``random`` module state per test.

    Prevents accidental cross-test pollution from module-level ``random``
    usage (e.g. ``random.choice``, ``random.randint``). Tests that need
    their own seed should request :func:`seeded_rng` instead.
    """
    state = random.getstate()
    yield
    random.setstate(state)


# -----------------------------------------------------------------------------
# Combat builders (Phase 25: shared test infrastructure)
# -----------------------------------------------------------------------------


@pytest.fixture
def make_player():
    """Factory fixture: build a 1-up player Combatant for combat tests.

    Usage::

        def test_x(make_player):
            player = make_player(max_hp=120, base_damage=8)
    """

    def _factory(
        *,
        max_hp: int = 100,
        max_ap: int = 6,
        base_damage: int = 5,
        team: str = "player",
    ) -> object:
        from wet_run.combat.registry import build_default_player

        return build_default_player(
            max_hp=max_hp,
            max_ap=max_ap,
            base_damage=base_damage,
            programs=None,
        )

    return _factory


@pytest.fixture
def make_ice_enemy():
    """Factory fixture: build an ICE Combatant with default portrait/colour.

    Usage::

        def test_x(make_ice_enemy):
            enemy = make_ice_enemy(max_hp=50, base_damage=10)
    """

    def _factory(
        *,
        max_hp: int = 80,
        base_damage: int = 3,
        ice_id: str = "test_ice",
        ice_kind: str = "standard",
    ) -> object:
        from wet_run.combat.state_models import Combatant

        return Combatant(
            id=ice_id,
            name=ice_id,
            portrait="▲ICE▲",
            color=(255, 0, 255),
            hp=max_hp,
            max_hp=max_hp,
            ap=0,
            max_ap=0,
            auto_attack_damage=base_damage,
            team="enemy",
            ice_kind=ice_kind,
        )

    return _factory


@pytest.fixture
def make_combat_state():
    """Factory fixture: build a seeded CombatState for deterministic combat tests.

    Combines :func:`make_player` + :func:`make_ice_enemy` + a
    deterministic RNG. Eliminates the ~15-line ``_make_player`` /
    ``_make_boss`` / ``CombatState(player=…, enemy=…, rng=…)`` boilerplate
    repeated across ~20 combat test files.

    Each call returns a fresh state with a ``random.Random(0)`` RNG
    (independent of other state objects), so two states built in the
    same test produce the *same* variance sequence — i.e. reproducible
    across test runs.

    Usage::

        def test_x(make_combat_state):
            state = make_combat_state(player_hp=120, enemy_hp=50)
    """

    def _factory(
        *,
        player_hp: int = 100,
        player_dmg: int = 5,
        enemy_hp: int = 80,
        enemy_dmg: int = 3,
        ice_kind: str = "standard",
        rng: random.Random | None = None,
    ) -> object:
        from wet_run.combat.registry import build_default_player
        from wet_run.combat.state_models import CombatState

        player = build_default_player(
            max_hp=player_hp,
            max_ap=6,
            base_damage=player_dmg,
            programs=None,
        )
        enemy = build_default_player(
            max_hp=enemy_hp,
            max_ap=0,
            base_damage=enemy_dmg,
            programs=None,
        )
        # build_default_player returns a "player"-team Combatant — re-flag
        # the second one as enemy so CombatState accepts it.
        enemy.team = "enemy"
        enemy.ice_kind = ice_kind
        return CombatState(
            player=player,
            enemy=enemy,
            rng=rng if rng is not None else random.Random(0),
        )

    return _factory

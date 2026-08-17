"""Unit tests for Construct companion (Cycle 4: Pillar 5 actual combat ally).

Covers:
- AppState.construct_companion_active default + boolean toggle
- Pillar 5 compliance: Dixie as combat ally (not dialog-only)
- Death/rebirth: combat ally is ephemeral (Pillar 4 unlock-only meta-progression)
- Combat integration: tick_dixie_ally behavior (combat/state.py)
"""

from __future__ import annotations

from wet_run.combat.state import Combatant, CombatState, tick_dixie_ally
from wet_run.engine.state import AppState


def _make_enemy() -> Combatant:
    return Combatant(
        id="test_enemy",
        name="Test Enemy",
        portrait="X",
        color=(255, 255, 255),
        hp=100,
        max_hp=100,
        ap=0,
        max_ap=0,
        auto_attack_damage=5,
        skills=(),
        team="enemy",
        ice_kind="standard",
    )


def _make_player() -> Combatant:
    return Combatant(
        id="test_player",
        name="Test Player",
        portrait="@",
        color=(255, 255, 255),
        hp=100,
        max_hp=100,
        ap=0,
        max_ap=0,
        auto_attack_damage=10,
        skills=(),
        team="player",
        ice_kind="standard",
    )


def _make_combat_state() -> CombatState:
    return CombatState(player=_make_player(), enemy=_make_enemy())


class TestConstructCompanionField:
    """AppState.construct_companion_active default + boolean toggle."""

    def test_construct_companion_active_default_false(self) -> None:
        state = AppState()
        assert state.construct_companion_active is False

    def test_construct_companion_active_can_be_enabled(self) -> None:
        state = AppState()
        state.construct_companion_active = True
        assert state.construct_companion_active is True

    def test_construct_companion_active_can_be_disabled(self) -> None:
        state = AppState()
        state.construct_companion_active = True
        state.construct_companion_active = False
        assert state.construct_companion_active is False

    def test_is_boolean_type(self) -> None:
        state = AppState()
        assert isinstance(state.construct_companion_active, bool)


class TestPillar5Compliance:
    """Construct companion: Dixie as actual combat ally (Pillar 5 The Style)."""

    def test_no_meta_state_write(self) -> None:
        state = AppState()
        state.construct_companion_active = True
        assert not hasattr(state, "meta_state") or state.meta_state is None

    def test_does_not_persist_across_resets(self) -> None:
        """AppState() constructor resets all defaults — ephemeral."""
        a = AppState()
        a.construct_companion_active = True
        b = AppState()
        assert b.construct_companion_active is False

    def test_does_not_modify_player_stats(self) -> None:
        """Construct companion is a combat ally flag, no stat boosts."""
        state = AppState()
        original_hp = state.player_hp
        original_max_hp = state.player_max_hp
        state.construct_companion_active = True
        assert state.player_hp == original_hp
        assert state.player_max_hp == original_max_hp


class TestConstructCompanionBehavior:
    """Behavior contract (combat ally flag, dialog-only by default)."""

    def test_default_is_dialog_only(self) -> None:
        """Default: construct_companion_active = False (dialog-only mode)."""
        state = AppState()
        assert state.construct_companion_active is False

    def test_can_be_toggled_to_combat_ally(self) -> None:
        """Enabling switches Dixie from dialog-only to actual combat ally."""
        state = AppState()
        state.construct_companion_active = True
        assert state.construct_companion_active is True


class TestTickDixieAlly:
    """tick_dixie_ally: Dixie attacks alongside player when construct_companion_active."""

    def test_no_op_when_construct_companion_inactive(self) -> None:
        """Default: Dixie is dialog-only, no attacks."""
        app = AppState()
        cs = _make_combat_state()
        original_hp = cs.enemy.hp
        tick_dixie_ally(cs, app)
        assert cs.enemy.hp == original_hp

    def test_attacks_when_construct_companion_active(self) -> None:
        """When enabled, Dixie strikes the target.

        ADR-0148: Dixie may use a companion skill (icebreaker_overdrive 50 dmg
        when target HP >= 80) OR plain auto-attack (5 dmg). Accept either.
        """
        from wet_run.combat.state import DIXIE_ALLY_DAMAGE

        app = AppState()
        app.construct_companion_active = True
        cs = _make_combat_state()
        original_hp = cs.enemy.hp
        cs.tick_ms = DIXIE_ALLY_DAMAGE + 5000
        tick_dixie_ally(cs, app)
        # Either 5 (auto-attack) or 50 (icebreaker_overdrive).
        damage_dealt = original_hp - cs.enemy.hp
        assert damage_dealt in (DIXIE_ALLY_DAMAGE, 50)

    def test_no_op_when_combat_finished(self) -> None:
        """If combat ended, Dixie doesn't attack."""
        from wet_run.combat.state import DIXIE_ALLY_DAMAGE

        app = AppState()
        app.construct_companion_active = True
        cs = _make_combat_state()
        cs.finished = True
        original_hp = cs.enemy.hp
        cs.tick_ms = DIXIE_ALLY_DAMAGE + 5000
        tick_dixie_ally(cs, app)
        assert cs.enemy.hp == original_hp

    def test_no_op_when_target_is_dead(self) -> None:
        """If target hp <= 0, Dixie doesn't attack."""
        from wet_run.combat.state import DIXIE_ALLY_DAMAGE

        app = AppState()
        app.construct_companion_active = True
        cs = _make_combat_state()
        cs.enemy.hp = 0
        original_hp = cs.enemy.hp
        cs.tick_ms = DIXIE_ALLY_DAMAGE + 5000
        tick_dixie_ally(cs, app)
        assert cs.enemy.hp == original_hp

    def test_respects_attack_interval(self) -> None:
        """Dixie does not attack on every tick (interval respected)."""
        from wet_run.combat.state import DIXIE_ALLY_DAMAGE

        app = AppState()
        app.construct_companion_active = True
        cs = _make_combat_state()
        cs.tick_ms = DIXIE_ALLY_DAMAGE + 5000
        original_hp = cs.enemy.hp
        tick_dixie_ally(cs, app)
        hp_after_first = cs.enemy.hp
        tick_dixie_ally(cs, app)
        assert cs.enemy.hp == hp_after_first
        # First call deals either 5 (auto-attack) or 50 (icebreaker).
        assert original_hp - hp_after_first in (DIXIE_ALLY_DAMAGE, 50)


__all__ = [
    "TestConstructCompanionField",
    "TestPillar5Compliance",
    "TestConstructCompanionBehavior",
    "TestTickDixieAlly",
]

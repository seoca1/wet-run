"""Combat state model (ADR-0003, RT-MS).

Pure-data combat primitives: ``Combatant``, ``Skill``, ``CombatState``.
A deterministic ``step_combat`` advances the simulation by one tick and
returns the events that occurred (damage, skill use, etc.).

ADR-0156 split: ``step_combat`` and tick helpers live in
:mod:`state_transitions`; skill effect handlers live in
:mod:`state_effects`. Both are imported lazily to avoid circular
dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .state_models import (  # ADR-0141 split — dataclasses live in state_models
    AUTO_ATTACK_INTERVAL_MS,
    TICK_MS,
    Combatant,
    CombatState,
    Skill,
    SkillEffect,
    StatusEffect,
)

if TYPE_CHECKING:
    from ..engine.state import AppState

from .telemetry_integration import record_kill

__all__ = [
    "ALARM_MAX_LEVEL",
    "ALARM_SPEED_BY_ICE",
    "ALARM_TICK_INTERVAL_MS",
    "AP_REGEN_INTERVAL_MS",
    "AUTO_ATTACK_INTERVAL_MS",
    "COMBO_BONUSES",
    "COMBO_WINDOW_MS",
    "CRIT_CHANCE",
    "CRIT_MULTIPLIER",
    "CRIT_MULTIPLIER_MAX",
    "CRIT_MULTIPLIER_MIN",
    "Combatant",
    "CombatState",
    "DAMAGE_VARIANCE_MAX",
    "DAMAGE_VARIANCE_MIN",
    "DEFAULT_ALARM_SPEED",
    "DEFAULT_WEAKNESS_MULTIPLIER",
    "ROLE_CRIT_BONUSES",
    "ROLE_SYNERGY_BONUSES",
    "Skill",
    "SkillEffect",
    "STAGGER_DURATION_MS",
    "StatusEffect",
    "TICK_MS",
    "WEAKNESS_BY_ICE",
    "_record_event",
    "get_combat_pressure",
    "step_combat",
    "tick_dixie_ally",
    "use_skill",
]

AP_REGEN_INTERVAL_MS = 2000  # 1 AP / 2s

# Damage variance: ±20% randomization
DAMAGE_VARIANCE_MIN = 0.8
DAMAGE_VARIANCE_MAX = 1.2

# Critical hit: 15% chance, 2x damage (variance 1.8-2.2)
CRIT_CHANCE = 0.15
CRIT_MULTIPLIER = 2.0
CRIT_MULTIPLIER_MIN = 1.8
CRIT_MULTIPLIER_MAX = 2.2

WEAKNESS_BY_ICE: dict[str, dict[str, float]] = {
    "standard": {
        "strike": 1.5,
        "burst": 1.2,
        "guard": 1.0,
        "utility": 1.0,
        "sustain": 0.8,
    },
    "watchdog": {
        "burst": 1.5,
        "strike": 1.2,
        "guard": 1.0,
        "utility": 0.8,
        "sustain": 0.6,
    },
    "goliath": {
        "sustain": 1.5,
        "utility": 1.0,
        "strike": 1.0,
        "guard": 0.9,
        "burst": 0.7,
    },
    "black": {
        "burst": 1.5,
        "strike": 1.0,
        "utility": 0.8,
        "guard": 0.7,
        "sustain": 0.6,
    },
    "construct": {
        "utility": 1.5,
        "strike": 1.0,
        "burst": 1.0,
        "guard": 1.0,
        "sustain": 0.8,
    },
    "wintermute": {
        "strike": 1.5,
        "guard": 1.0,
        "utility": 1.0,
        "sustain": 1.0,
        "burst": 0.6,
    },
    "ta_construct_prime": {
        "burst": 1.5,
        "strike": 0.8,
        "guard": 0.8,
        "utility": 0.8,
        "sustain": 0.8,
    },
}

DEFAULT_WEAKNESS_MULTIPLIER = 1.0

ALARM_TICK_INTERVAL_MS = 10000  # 10s per alarm level during combat
ALARM_MAX_LEVEL = 5  # alarm_level == 5 → trace complete → flatline

ROLE_SYNERGY_BONUSES: dict[int, float] = {
    1: 1.0,
    2: 1.15,
    3: 1.30,
    4: 1.50,
    5: 1.75,
}

ALARM_SPEED_BY_ICE: dict[str, float] = {
    "standard": 1.0,
    "watchdog": 1.3,
    "goliath": 0.7,
    "black": 2.0,
    "construct": 0.5,
    "wintermute": 2.5,
    "ta_construct_prime": 3.0,
}

DEFAULT_ALARM_SPEED = 1.0

COMBO_BONUSES: dict[int, float] = {
    1: 1.0,
    2: 1.0,
    3: 1.2,
    4: 1.5,
    5: 2.0,
    6: 3.0,
}

COMBO_WINDOW_MS = 3500

ROLE_CRIT_BONUSES: dict[str, float] = {
    "strike": 0.05,
    "burst": 0.10,
    "guard": 0.0,
    "utility": 0.05,
    "sustain": 0.0,
}

STAGGER_DURATION_MS = 1500  # stagger skips one auto-attack window


def _count_player_role_synergy(state: CombatState) -> int:
    """Return how many player skills share the same role as the last used skill."""
    skill = state.last_skill_used
    if skill is None or skill.role is None:
        return 0
    return sum(1 for s in state.player.skills if s.role == skill.role)


def _calculate_damage(
    state: CombatState,
    base_damage: int,
    attacker: Combatant,
    defender: Combatant,
    can_crit: bool = True,
) -> tuple[int, bool]:
    """Calculate final damage with variance, resistance, weakness, defense, and crit."""
    variance = state.rng.uniform(DAMAGE_VARIANCE_MIN, DAMAGE_VARIANCE_MAX)
    dmg = base_damage * variance

    if defender.ice_resistance > 0.0:
        dmg *= 1.0 - defender.ice_resistance

    if (
        attacker.team == "player"
        and state.last_skill_used is not None
        and state.last_skill_used.role is not None
        and defender.ice_kind is not None
    ):
        role = state.last_skill_used.role
        weakness = WEAKNESS_BY_ICE.get(defender.ice_kind, {}).get(role, DEFAULT_WEAKNESS_MULTIPLIER)
        dmg *= weakness

    if attacker.team == "player" and state.last_skill_used is not None:
        synergy = _count_player_role_synergy(state)
        dmg *= ROLE_SYNERGY_BONUSES.get(synergy, 1.0)

    if attacker.team == "player":
        combo_mult = COMBO_BONUSES.get(state.player_combo, 1.0)
        dmg *= combo_mult

    if attacker.team == "enemy" and state.boss_profile is not None:
        for phase_def in state.boss_profile.phases:
            if phase_def.phase == attacker.current_phase:
                dmg *= phase_def.damage_multiplier
                break

    # Phase 17: F.4 boss phase damage multiplier (ADR-0180, 0190).
    # F.4 bosses use boss_phase_tracker instead of boss_profile.
    if attacker.team == "enemy" and state.boss_phase_tracker is not None:
        from typing import cast

        from .boss_phase_tracker import BossPhaseTracker

        f4_tracker = cast(BossPhaseTracker, state.boss_phase_tracker)
        dmg *= f4_tracker.get_damage_multiplier()

    dmg = int(dmg)

    from .status_effects import get_vulnerability_multiplier

    dmg = int(dmg * get_vulnerability_multiplier(defender))

    dmg += attacker.get_attack_bonus()

    dmg = max(0, dmg - defender.get_defense_bonus())

    is_crit = False
    if can_crit:
        crit_chance = CRIT_CHANCE
        from .depth.personality import get_crit_bonus

        crit_chance += get_crit_bonus(attacker)
        if state.last_skill_used and state.last_skill_used.crit_bonus > 0:
            crit_chance += state.last_skill_used.crit_bonus
        if state.last_skill_used is not None and state.last_skill_used.role is not None:
            crit_chance += ROLE_CRIT_BONUSES.get(state.last_skill_used.role, 0.0)
        if state.rng.random() < crit_chance:
            crit_mult = state.rng.uniform(CRIT_MULTIPLIER_MIN, CRIT_MULTIPLIER_MAX)
            dmg = int(dmg * crit_mult)
            is_crit = True

    return max(1, dmg), is_crit


def _apply_damage(
    state: CombatState,
    target: Combatant,
    amount: int,
    bypass_shield: bool = False,
) -> int:
    """Apply damage to target, handling shield. Returns damage actually applied."""
    if bypass_shield:
        target.hp = max(0, target.hp - amount)
        return amount

    absorbed = min(state.shield, amount)
    applied = amount - absorbed
    state.shield = max(0, state.shield - amount)
    target.hp = max(0, target.hp - applied)
    if target.hp <= 0:
        record_kill(target.ice_kind)  # type: ignore[arg-type]
        # Mission Archetype (ADR-0164): STEALTH kills spike alarm.
        from .mission_archetypes import alarm_per_kill

        archetype_str = getattr(state, "mission_archetype", None)
        archetype_obj = None
        if archetype_str is not None:
            from .mission_archetypes import MissionArchetype

            try:
                archetype_obj = MissionArchetype(archetype_str)
            except ValueError:
                archetype_obj = None
        alarm_bump = alarm_per_kill(archetype_obj) if archetype_obj is not None else 1
        if alarm_bump <= 0:
            alarm_bump = 1
        state.alarm_level = min(ALARM_MAX_LEVEL, state.alarm_level + alarm_bump)
        if state.telemetry is not None:
            from typing import cast

            from .telemetry_integration import TelemetryIntegrator

            ice_kind = target.ice_kind or "unknown"
            cast(TelemetryIntegrator, state.telemetry).record_kill(ice_kind)
        if state.boss_phase_tracker is not None and target.ice_kind:
            if target.ice_kind.startswith("boss_"):
                from typing import cast

                from .boss_phase_tracker import BossPhaseTracker

                tracker = cast(BossPhaseTracker, state.boss_phase_tracker)
                if tracker.should_transition(target.hp, target.max_hp):
                    tracker.transition()
    return applied


def get_combat_pressure(state: CombatState) -> dict[str, int | float | str | None]:
    """Summarize current combat intensity for HUD / analytics."""
    target = state.target
    alarm_fraction = state.alarm_level / ALARM_MAX_LEVEL if ALARM_MAX_LEVEL else 0.0
    combo_mult = COMBO_BONUSES.get(state.player_combo, 1.0)
    role_count = _count_player_role_synergy(state)
    synergy_mult = ROLE_SYNERGY_BONUSES.get(role_count, 1.0)

    weakness_mult = DEFAULT_WEAKNESS_MULTIPLIER
    if (
        target is not None
        and state.last_skill_used is not None
        and state.last_skill_used.role is not None
        and target.ice_kind is not None
    ):
        weakness_mult = WEAKNESS_BY_ICE.get(target.ice_kind, {}).get(
            state.last_skill_used.role, DEFAULT_WEAKNESS_MULTIPLIER
        )

    boss_phase = (
        target.current_phase if state.boss_profile is not None and target is not None else 0
    )

    return {
        "alarm_level": state.alarm_level,
        "alarm_max": ALARM_MAX_LEVEL,
        "alarm_fraction": alarm_fraction,
        "alarm_speed": target.alarm_speed if target is not None else 1.0,
        "player_combo": state.player_combo,
        "combo_multiplier": combo_mult,
        "role_synergy_count": role_count,
        "synergy_multiplier": synergy_mult,
        "weakness_multiplier": weakness_mult,
        "boss_phase": boss_phase,
        "ice_resistance": target.ice_resistance if target is not None else 0.0,
    }


def use_skill(state: CombatState, skill: Skill) -> bool:
    """Apply a player skill. Returns True if the skill was used.

    Dispatches to per-SkillEffect handlers via ``dispatch_skill_effect``
    in :mod:`state_effects`. This top-level function enforces pre-flight
    checks (AP, cooldown, finished-flag) and applies the post-hit
    end-of-fight check.
    """
    from .state_effects import dispatch_skill_effect

    if not _skill_prerequisites_ok(state, skill):
        return False

    state.player.ap -= skill.ap_cost
    state.last_skill_used = skill
    state.stats.skills_used += 1
    if skill.cooldown_ms > 0:
        state.skill_cooldowns[skill.id] = skill.cooldown_ms

    dispatch_skill_effect(state, skill)

    # Re-check end of fight.
    if state.enemies and all(e.hp <= 0 for e in state.enemies):
        state.finished = True
        state.outcome = "victory"
    return True


def _skill_prerequisites_ok(state: CombatState, skill: Skill) -> bool:
    """Return True iff the skill can fire (not finished, enough AP,
    not on cooldown, not silenced)."""
    if state.finished:
        return False
    if skill.ap_cost > state.player.ap:
        return False
    if state.skill_cooldowns.get(skill.id, 0) > 0:
        return False
    from .status_effects import is_silenced

    if is_silenced(state.player):
        return False
    return True


DIXIE_ALLY_DAMAGE = 5
ALLY_AUTO_ATTACK_INTERVAL_MS = 2000


def tick_dixie_ally(combat_state: CombatState, app_state: AppState) -> None:
    """Cycle 4 Pillar 5: Dixie attacks alongside player when construct_companion_active."""
    from .depth import dixie_choose_skill, dixie_use_skill

    if not getattr(app_state, "construct_companion_active", False):
        return
    if combat_state.finished:
        return
    target = combat_state.target
    if target is None or target.hp <= 0:
        return
    last = combat_state.dixie_last_attack_ms
    if combat_state.tick_ms - last < ALLY_AUTO_ATTACK_INTERVAL_MS:
        return
    skill_id = dixie_choose_skill(combat_state, app_state, combat_state.rng)
    if skill_id is not None and dixie_use_skill(
        combat_state, app_state, skill_id, combat_state.rng
    ):
        combat_state.dixie_last_attack_ms = combat_state.tick_ms
        return
    _apply_damage(combat_state, target, DIXIE_ALLY_DAMAGE)
    combat_state.push(f">>> Dixie strikes {target.id} for {DIXIE_ALLY_DAMAGE}")
    combat_state.dixie_last_attack_ms = combat_state.tick_ms


from .state_effects import _record_event  # noqa: E402,F401
from .state_effects import apply_enemy_skill as _apply_enemy_skill  # noqa: E402,F401
from .state_transitions import (  # noqa: E402,F401
    _check_boss_phase_transition,
    _tick_alarm,
    _tick_combo,
    _tick_status_effects,
    step_combat,  # noqa: E402
)

"""Combat state model (ADR-0003, RT-MS).

Pure-data combat primitives: ``Combatant``, ``Skill``, ``CombatState``.
A deterministic ``step_combat`` advances the simulation by one tick and
returns the events that occurred (damage, skill use, etc.).
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

__all__ = [
    "AP_REGEN_INTERVAL_MS",
    "AUTO_ATTACK_INTERVAL_MS",
    "Combatant",
    "CombatState",
    "Skill",
    "SkillEffect",
    "StatusEffect",
    "TICK_MS",
    "get_combat_pressure",
    "step_combat",
    "use_skill",
]

if TYPE_CHECKING:
    pass

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

    dmg = int(dmg)

    dmg += attacker.get_attack_bonus()

    dmg = max(0, dmg - defender.get_defense_bonus())

    is_crit = False
    if can_crit:
        crit_chance = CRIT_CHANCE
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
    return applied


def _tick_status_effects(state: CombatState, target: Combatant) -> list[str]:
    """Process status effects for one tick. Returns list of log messages."""
    messages: list[str] = []
    for status in list(target.statuses):
        status.remaining_ms = max(0, status.remaining_ms - TICK_MS)
        # Apply per-tick effects
        if status.dot_damage > 0 and status.remaining_ms > 0:
            target.hp = max(0, target.hp - status.dot_damage)
            messages.append(f"{status.effect_id} burns {target.name} for {status.dot_damage}")
        if status.heal_per_tick > 0 and status.remaining_ms > 0:
            target.hp = min(target.max_hp, target.hp + status.heal_per_tick)
        if status.remaining_ms <= 0:
            target.statuses.remove(status)
    return messages


def _tick_alarm(state: CombatState) -> None:
    """Increment alarm_level when ALARM_TICK_INTERVAL_MS has elapsed.

    Tick interval is shortened by the target enemy's alarm_speed multiplier
    (e.g. Wintermute at 2.5× ticks every 4s instead of 10s). alarm_level 5
    ends combat as a flatline (Pillar 3 alignment).
    """
    target = state.target
    if target is None:
        return
    tick_interval = ALARM_TICK_INTERVAL_MS / max(0.01, target.alarm_speed)
    if state.tick_ms - state.last_alarm_tick_ms >= tick_interval:
        state.alarm_level += 1
        state.last_alarm_tick_ms = state.tick_ms
        state.stats.peak_alarm_level = max(state.stats.peak_alarm_level, state.alarm_level)
        state.push(f"TRACE WARNING: alarm level {state.alarm_level}/{ALARM_MAX_LEVEL}")


def _tick_combo(state: CombatState) -> None:
    """Reset player_combo if no hit landed within COMBO_WINDOW_MS."""
    if state.player_combo > 0 and state.tick_ms - state.combo_last_hit_ms > COMBO_WINDOW_MS:
        state.player_combo = 0


def _check_boss_phase_transition(state: CombatState) -> None:
    """Advance target.current_phase when HP crosses the next phase's hp_threshold.

    Looks up the highest phase in state.boss_profile whose hp_threshold
    is at or above the current HP fraction. If that phase is higher than
    target.current_phase, advance and log the transition.
    """
    profile = state.boss_profile
    target = state.target
    if profile is None or target is None or target.max_hp <= 0:
        return

    hp_fraction = target.hp / target.max_hp

    target_phase = target.current_phase
    for phase_def in profile.phases:
        if hp_fraction <= phase_def.hp_threshold:
            if phase_def.phase > target_phase:
                target_phase = phase_def.phase

    if target_phase > target.current_phase:
        old_phase = target.current_phase
        target.current_phase = target_phase
        state.push(f"{target.name} PHASE {old_phase} → {target_phase}")


def get_combat_pressure(state: CombatState) -> dict[str, int | float | str | None]:
    """Summarize current combat intensity for HUD / analytics.

    Returns a dict with the live values of all 7 multipliers introduced
    this session: alarm level, combo count, role synergy, weakness
    multiplier (against current enemy), boss phase, alarm speed, and
    ICE resistance. Designed for HUD pickup, debugging, and balance
    telemetry.
    """
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


def step_combat(state: CombatState) -> None:
    """Advance ``state`` by one tick (TICK_MS).

    Mutates ``state`` in place: applies auto-attacks, regenerates AP,
    resolves end conditions. Events are appended to ``state.log``.
    """
    if state.finished:
        return
    state.tick_ms += TICK_MS
    state.stats.turns_elapsed += 1

    # Tick down status effects (DoT, HoT, etc)
    player_msgs = _tick_status_effects(state, state.player)
    enemy_msgs: list[str] = []
    for enemy in state.enemies:
        enemy_msgs.extend(_tick_status_effects(state, enemy))
    for msg in player_msgs + enemy_msgs:
        state.push(msg)

    # Reduce skill cooldowns
    for skill_id in list(state.skill_cooldowns.keys()):
        state.skill_cooldowns[skill_id] = max(0, state.skill_cooldowns[skill_id] - TICK_MS)
        if state.skill_cooldowns[skill_id] <= 0:
            del state.skill_cooldowns[skill_id]

    # AP regen
    if state.tick_ms - state.last_ap_regen_ms >= AP_REGEN_INTERVAL_MS:
        if state.player.ap < state.player.max_ap:
            state.player.ap = min(state.player.max_ap, state.player.ap + 1)
            state.last_ap_regen_ms = state.tick_ms

    # Alarm / trace tick
    _tick_alarm(state)

    _tick_combo(state)

    _check_boss_phase_transition(state)

    # Auto-attack: player (hits all alive enemies, ADR-0152 multi-enemy)
    if state.tick_ms - state.last_player_attack_ms >= AUTO_ATTACK_INTERVAL_MS:
        if not state.player.is_stunned():
            from .multi_enemy import all_alive_enemies

            alive = all_alive_enemies(state)
            if alive:
                base_dmg = state.player.auto_attack_damage
                for target in alive:
                    dmg, is_crit = _calculate_damage(state, base_dmg, state.player, target)
                    applied = _apply_damage(state, target, dmg)

                    crit_text = " CRITICAL HIT!" if is_crit else ""
                    state.push(f"You strike {target.name} for {applied} damage.{crit_text}")
                    state.player_combo += 1
                    state.combo_last_hit_ms = state.tick_ms
                    state.stats.damage_dealt += applied
                    if is_crit:
                        state.stats.crits_landed += 1
                state.stats.max_combo_reached = max(
                    state.stats.max_combo_reached, state.player_combo
                )
                state.last_player_attack_ms = state.tick_ms
                state.last_event = "player_attack"
                state.last_event_color = (200, 200, 200)
                state.last_event_tick = state.tick_ms
        else:
            state.push("You are stunned and cannot attack!")
            state.last_player_attack_ms = state.tick_ms

    # Auto-attack: each enemy (with shield absorption, skip if stunned)
    if state.tick_ms - state.last_enemy_attack_ms >= AUTO_ATTACK_INTERVAL_MS:
        for enemy in state.enemies:
            if enemy.hp <= 0:
                continue
            if enemy.is_staggered():
                enemy.consume_stagger()
                state.push(f"{enemy.name} staggered — attack skipped!")
                state.last_enemy_attack_ms = state.tick_ms
                continue
            if not enemy.is_stunned():
                base_dmg = enemy.auto_attack_damage
                dmg, is_crit = _calculate_damage(state, base_dmg, enemy, state.player)
                absorbed = min(state.shield, dmg)
                applied = dmg - absorbed
                state.shield = max(0, state.shield - dmg)
                state.player.hp = max(0, state.player.hp - applied)
                state.last_enemy_attack_ms = state.tick_ms
                state.last_event = "enemy_attack"
                state.last_event_color = (255, 100, 100)
                state.last_event_tick = state.tick_ms

                crit_text = " CRITICAL HIT!" if is_crit else ""
                if absorbed > 0:
                    state.push(
                        f"{enemy.name} hits you for {applied} dmg (shield absorbed {absorbed}).{crit_text}"
                    )
                else:
                    state.push(f"{enemy.name} hits you for {applied} damage.{crit_text}")
                state.enemy_combo += 1
                state.stats.damage_received += applied
                if is_crit:
                    state.stats.crits_received += 1

                # ICE-side skill use: aggression-tier-aware probability (ADR-0148).
                if enemy.skills and enemy.hp > 0:
                    from .depth import enemy_should_use_skill

                    if enemy.alive_skills_available() and enemy_should_use_skill(enemy, state.rng):
                        skill = enemy.choose_skill(state.rng)
                        if skill is not None:
                            _apply_enemy_skill(state, enemy, skill)
            else:
                state.push(f"{enemy.name} is stunned and cannot attack!")
                state.last_enemy_attack_ms = state.tick_ms

    # End conditions
    if state.enemies and all(e.hp <= 0 for e in state.enemies):
        state.finished = True
        state.outcome = "victory"
    elif state.alarm_level >= ALARM_MAX_LEVEL:
        state.finished = True
        state.outcome = "defeat"
        state.push("TRACE COMPLETE: flatline. Connection severed.")
    elif state.player.hp <= 0:
        state.finished = True
        state.outcome = "defeat"


def use_skill(state: CombatState, skill: Skill) -> bool:
    """Apply a player skill. Returns True if the skill was used.

    The dispatch into effect-specific code paths is delegated to
    small per-category helpers below — this top-level function
    exists to enforce the pre-flight checks (AP, cooldown,
    finished-flag) and to apply the post-hit end-of-fight check.
    """
    if not _skill_prerequisites_ok(state, skill):
        return False

    state.player.ap -= skill.ap_cost
    state.last_skill_used = skill
    state.stats.skills_used += 1
    if skill.cooldown_ms > 0:
        state.skill_cooldowns[skill.id] = skill.cooldown_ms

    # Dispatch to per-category effect.
    dispatch = {
        SkillEffect.ATTACK: _apply_damage_skill,
        SkillEffect.HEAVY_ATTACK: _apply_heavy_attack,
        SkillEffect.PIERCE: _apply_pierce,
        SkillEffect.MULTI_HIT: _apply_multi_hit,
        SkillEffect.DOT: _apply_dot,
        SkillEffect.POISON: _apply_dot,
        SkillEffect.SHIELD: _apply_shield,
        SkillEffect.HEAL: _apply_heal,
        SkillEffect.REGEN: _apply_regen,
        SkillEffect.BUFF: _apply_buff,
        SkillEffect.DEBUFF: _apply_debuff,
        SkillEffect.STUN: _apply_stun,
        SkillEffect.STAGGER: _apply_stagger,
        SkillEffect.DETECT: _apply_detect,
        SkillEffect.LIFESTEAL: _apply_lifesteal,
    }
    handler = dispatch.get(skill.effect)
    if handler is None:
        state.push(f">> {skill.name}: used.")
    else:
        handler(state, skill)

    # Re-check end of fight.
    if state.enemies and all(e.hp <= 0 for e in state.enemies):
        state.finished = True
        state.outcome = "victory"
    return True


def _skill_prerequisites_ok(state: CombatState, skill: Skill) -> bool:
    """Return True iff the skill can fire (not finished, enough AP,
    not on cooldown)."""
    if state.finished:
        return False
    if skill.ap_cost > state.player.ap:
        return False
    if state.skill_cooldowns.get(skill.id, 0) > 0:
        return False
    return True


# ---------------------------------------------------------------------------
# Effect handlers — one per category. Each modifies ``state`` in place.
# ---------------------------------------------------------------------------


def _record_event(
    state: CombatState,
    event: str,
    color: tuple[int, int, int],
) -> None:
    """Stamp the last-event fields used by the renderer."""
    state.last_event = event
    state.last_event_color = color
    state.last_event_tick = state.tick_ms


def _apply_aoe_damage(
    state: CombatState,
    skill: Skill,
    effect_label: str,
    crit_label: str = " [CRITICAL!]",
    bypass_shield: bool = False,
    apply_dot: bool = False,
) -> None:
    """Apply damage-type skill to every living enemy (multi-ICE AOE)."""
    total_dmg = 0
    crit_seen = False
    for enemy in state.enemies:
        if enemy.hp <= 0:
            continue
        dmg, is_crit = _calculate_damage(state, skill.damage, state.player, enemy)
        applied = _apply_damage(state, enemy, dmg, bypass_shield=bypass_shield)
        total_dmg += applied
        crit_seen = crit_seen or is_crit
        state.stats.damage_dealt += applied
        if is_crit:
            state.stats.crits_landed += 1
        if apply_dot:
            enemy.statuses.append(
                StatusEffect(
                    effect_id="burn",
                    remaining_ms=skill.dot_duration_ms,
                    dot_damage=skill.dot_damage,
                )
            )
    crit_text = crit_label if crit_seen else ""
    _record_event(state, effect_label, skill.effect_color)
    state.push(f">> {skill.name} AOE! {total_dmg} total damage across all targets.{crit_text}")


def _apply_damage_skill(state: CombatState, skill: Skill) -> None:
    if skill.aoe:
        _apply_aoe_damage(state, skill, "skill_attack")
        return
    target = state.target
    if target is None:
        return
    dmg, is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg)
    crit = " [CRITICAL!]" if is_crit else ""
    _record_event(state, "skill_attack", skill.effect_color)
    state.push(f">> {skill.name}! {applied} damage to {target.name}.{crit}")


def _apply_heavy_attack(state: CombatState, skill: Skill) -> None:
    if skill.aoe:
        _apply_aoe_damage(state, skill, "heavy_attack", " [DEVASTATING!]")
        return
    target = state.target
    if target is None:
        return
    dmg, is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg)
    crit = " [DEVASTATING!]" if is_crit else ""
    _record_event(state, "heavy_attack", skill.effect_color)
    state.push(f">> {skill.name} SMASH! {applied} damage!{crit}")


def _apply_pierce(state: CombatState, skill: Skill) -> None:
    if skill.aoe:
        _apply_aoe_damage(state, skill, "pierce", " [PIERCING!]", bypass_shield=True)
        return
    target = state.target
    if target is None:
        return
    dmg, is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg, bypass_shield=True)
    crit = " [PIERCING!]" if is_crit else ""
    _record_event(state, "pierce", skill.effect_color)
    state.push(f">> {skill.name} pierces through! {applied} damage.{crit}")


def _apply_multi_hit(state: CombatState, skill: Skill) -> None:
    target = state.target
    if target is None:
        return
    total = 0
    crit_hit = False
    for _ in range(skill.hit_count):
        dmg, is_crit = _calculate_damage(state, skill.damage, state.player, target, can_crit=False)
        total += _apply_damage(state, target, dmg)
        crit_hit = crit_hit or is_crit
    crit = " [ALL CRITS!]" if crit_hit else ""
    _record_event(state, "multi_hit", skill.effect_color)
    state.push(f">> {skill.name} strikes {skill.hit_count} times! Total: {total} damage.{crit}")


def _apply_dot(state: CombatState, skill: Skill) -> None:
    if skill.aoe:
        _apply_aoe_damage(state, skill, "dot", " [BURN ALL!]", apply_dot=True)
        return
    target = state.target
    if target is None:
        return
    dmg, _is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg)
    target.statuses.append(
        StatusEffect(
            effect_id="burn",
            remaining_ms=skill.dot_duration_ms,
            dot_damage=skill.dot_damage,
        )
    )
    _record_event(state, "dot", skill.effect_color)
    state.push(
        f">> {skill.name}: {applied} damage + burn ({skill.dot_damage}/s for {skill.dot_duration_ms // 1000}s)!"
    )


def _apply_shield(state: CombatState, skill: Skill) -> None:
    state.shield += skill.shield
    _record_event(state, "shield", skill.effect_color)
    state.push(f">> {skill.name}: +{skill.shield} shield! (Total: {state.shield})")


def _apply_heal(state: CombatState, skill: Skill) -> None:
    healed = min(skill.heal, state.player.max_hp - state.player.hp)
    state.player.hp = min(state.player.max_hp, state.player.hp + skill.heal)
    _record_event(state, "heal", skill.effect_color)
    state.push(f">> {skill.name}: +{healed} HP restored!")


def _apply_regen(state: CombatState, skill: Skill) -> None:
    state.player.statuses.append(
        StatusEffect(
            effect_id="regen",
            remaining_ms=skill.buff_duration_ms,
            heal_per_tick=max(1, skill.heal // 10),
        )
    )
    _record_event(state, "regen", skill.effect_color)
    state.push(f">> {skill.name}: regen active ({skill.heal // 10}/s)")


def _apply_buff(state: CombatState, skill: Skill) -> None:
    state.player.statuses.append(
        StatusEffect(
            effect_id="powered",
            remaining_ms=skill.buff_duration_ms,
            attack_bonus=skill.buff_amount,
        )
    )
    _record_event(state, "buff", skill.effect_color)
    state.push(f">> {skill.name}: +{skill.buff_amount} attack power!")


def _apply_debuff(state: CombatState, skill: Skill) -> None:
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="weakened",
            remaining_ms=skill.buff_duration_ms,
            attack_bonus=-skill.buff_amount,
        )
    )
    _record_event(state, "debuff", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} weakened (-{skill.buff_amount} attack)!")


def _apply_stun(state: CombatState, skill: Skill) -> None:
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="stun",
            remaining_ms=skill.stun_duration_ms,
            is_stunned=True,
        )
    )
    _record_event(state, "stun", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} stunned for {skill.stun_duration_ms // 1000}s!")


def _apply_stagger(state: CombatState, skill: Skill) -> None:
    """Apply stagger to current target — skips their next auto-attack."""
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="stagger",
            remaining_ms=STAGGER_DURATION_MS,
            is_staggered=True,
        )
    )
    _record_event(state, "stagger", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} staggered (next attack skipped)!")


def _apply_detect(state: CombatState, skill: Skill) -> None:
    target = state.target
    if target is None:
        return
    ice_kind = target.ice_kind
    if ice_kind is not None and ice_kind in WEAKNESS_BY_ICE:
        weakness = WEAKNESS_BY_ICE[ice_kind]
        best_role = max(weakness, key=lambda r: weakness[r])
        best_mult = weakness[best_role]
        pct = int(round((best_mult - 1.0) * 100))
        if best_mult > 1.0:
            state.push(
                f">> {skill.name}: {target.name} WEAK to {best_role.upper()} (+{pct}% damage)!"
            )
        elif best_mult < 1.0:
            state.push(
                f">> {skill.name}: {target.name} RESISTS {best_role.upper()} ({pct}% reduction)"
            )
        else:
            state.push(f">> {skill.name}: {target.name} — no significant weakness")
    else:
        state.push(
            f">> {skill.name}: {target.name} HP {target.hp}/{target.max_hp}"
            f" | AP {target.ap}/{target.max_ap}"
        )


def _apply_lifesteal(state: CombatState, skill: Skill) -> None:
    target = state.target
    if target is None:
        return
    dmg, _is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg)
    healed = applied // 2
    state.player.hp = min(state.player.max_hp, state.player.hp + healed)
    _record_event(state, "lifesteal", skill.effect_color)
    state.push(f">> {skill.name}: {applied} damage, drained {healed} HP!")


def _apply_enemy_skill(state: CombatState, enemy: Combatant, skill: Skill) -> None:
    """Phase B-1: ICE uses a skill against the player.

    Wraps the existing player skill handlers by temporarily using the
    enemy as the "player" (attacker) and the actual player as the
    "target". Reuses damage calculations via _calculate_damage.

    ADR-0148: opens a 200ms counter window after enemy skill use.
    """
    from .depth import open_counter_window

    state.last_skill_used = skill
    state.stats.skills_used += 1
    state.push(f"!! {enemy.name} uses {skill.name}!")
    # Open counter window (ADR-0148). Player can use a COUNTER skill
    # in the next 200ms (2 ticks at TICK_MS=100) for 2x damage + stun.
    open_counter_window(state)
    # Damage skills: calculate with enemy as attacker
    if skill.effect in (
        SkillEffect.ATTACK,
        SkillEffect.HEAVY_ATTACK,
        SkillEffect.PIERCE,
        SkillEffect.MULTI_HIT,
        SkillEffect.DOT,
        SkillEffect.POISON,
    ):
        dmg, is_crit = _calculate_damage(state, skill.damage, enemy, state.player)
        if skill.effect == SkillEffect.PIERCE:
            applied = _apply_damage(state, state.player, dmg, bypass_shield=True)
        else:
            applied = _apply_damage(state, state.player, dmg)
        state.stats.damage_received += applied
        if is_crit:
            state.stats.crits_received += 1
        _record_event(state, "enemy_skill", skill.effect_color)
        state.push(f"!! {skill.name} hits you for {applied} damage!")
    elif skill.effect in (SkillEffect.STUN, SkillEffect.STAGGER):
        # Apply CC to player
        state.player.statuses.append(
            StatusEffect(
                effect_id="stun" if skill.effect == SkillEffect.STUN else "stagger",
                remaining_ms=skill.stun_duration_ms
                if skill.effect == SkillEffect.STUN
                else STAGGER_DURATION_MS,
                is_stunned=(skill.effect == SkillEffect.STUN),
                is_staggered=(skill.effect == SkillEffect.STAGGER),
            )
        )
        state.push(
            f"!! {skill.name}: you are "
            f"{'stunned' if skill.effect == SkillEffect.STUN else 'staggered'}!"
        )
    elif skill.effect == SkillEffect.DEBUFF:
        state.player.statuses.append(
            StatusEffect(
                effect_id="weakened",
                remaining_ms=skill.buff_duration_ms,
                attack_bonus=-skill.buff_amount,
            )
        )
        state.push(f"!! {skill.name}: your attack power -{skill.buff_amount}!")
    # Buff/heal/detect skills have no effect when used by enemies on
    # themselves (no AI decision-making); skip silently.


DIXIE_ALLY_DAMAGE = 5
ALLY_AUTO_ATTACK_INTERVAL_MS = 2000


def tick_dixie_ally(combat_state: CombatState, app_state: AppState) -> None:
    """Cycle 4 Pillar 5: Dixie attacks alongside player when construct_companion_active.

    Only active when the player toggled Dixie from dialog-only to combat ally.
    Ephemeral: relies on ``app_state.construct_companion_active`` (Pillar 4 compliant,
    no meta-progression; resets on AppState() construction).

    ADR-0148: Dixie can also use [[decompile]] / [[icebreaker_overdrive]] skills,
    chosen via dixie_choose_skill (probabilistic AI). Each skill use is gated
    by ALLY_AUTO_ATTACK_INTERVAL_MS cooldown.
    """
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
    # ADR-0148: companion skill auto-pick (decompile / icebreaker_overdrive).
    # If no skill picked, fall back to plain auto-attack.
    skill_id = dixie_choose_skill(combat_state, app_state, combat_state.rng)
    if skill_id is not None and dixie_use_skill(
        combat_state, app_state, skill_id, combat_state.rng
    ):
        combat_state.dixie_last_attack_ms = combat_state.tick_ms
        return
    _apply_damage(combat_state, target, DIXIE_ALLY_DAMAGE)
    combat_state.push(f">>> Dixie strikes {target.id} for {DIXIE_ALLY_DAMAGE}")
    combat_state.dixie_last_attack_ms = combat_state.tick_ms
    combat_state._dixie_last_attack_ms = combat_state.tick_ms  # type: ignore[attr-defined]

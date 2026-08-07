"""Combat state transitions (ADR-0156 split).

Tick-loop primitives: status effects, alarm, combo, boss phase transitions,
and the main ``step_combat`` tick loop. These functions mutate
``CombatState`` in place and rely on ``state.py`` for low-level helpers
(``_apply_damage``, ``_calculate_damage``) and ``state_effects.py`` for
skill effect handlers. Imports from state.py are lazy to avoid circular
dependency at module load.
"""

from __future__ import annotations

from .state_models import AUTO_ATTACK_INTERVAL_MS, TICK_MS, Combatant, CombatState

__all__ = [
    "_check_boss_phase_transition",
    "_tick_alarm",
    "_tick_combo",
    "_tick_status_effects",
    "step_combat",
]


def _tick_status_effects(state: CombatState, target: Combatant) -> list[str]:
    """Process status effects for one tick. Returns list of log messages."""
    messages: list[str] = []
    for status in list(target.statuses):
        status.remaining_ms = max(0, status.remaining_ms - TICK_MS)
        if status.dot_damage > 0 and status.remaining_ms > 0:
            target.hp = max(0, target.hp - status.dot_damage)
            messages.append(f"{status.effect_id} burns {target.name} for {status.dot_damage}")
        if status.heal_per_tick > 0 and status.remaining_ms > 0:
            target.hp = min(target.max_hp, target.hp + status.heal_per_tick)
        if status.remaining_ms <= 0:
            target.statuses.remove(status)
    return messages


def _tick_alarm(state: CombatState) -> None:
    """Increment alarm_level when ALARM_TICK_INTERVAL_MS has elapsed."""
    from .state import ALARM_MAX_LEVEL, ALARM_TICK_INTERVAL_MS

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
    from .state import COMBO_WINDOW_MS

    if state.player_combo > 0 and state.tick_ms - state.combo_last_hit_ms > COMBO_WINDOW_MS:
        state.player_combo = 0


def _check_boss_phase_transition(state: CombatState) -> None:
    """Advance target.current_phase when HP crosses the next phase's hp_threshold."""
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


def step_combat(state: CombatState) -> None:
    """Advance ``state`` by one tick (TICK_MS).

    Mutates ``state`` in place: applies auto-attacks, regenerates AP,
    resolves end conditions. Events are appended to ``state.log``.
    """
    from .state import (
        ALARM_MAX_LEVEL,
        AP_REGEN_INTERVAL_MS,
        _apply_damage,
        _calculate_damage,
    )
    from .state_effects import apply_enemy_skill

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
                            apply_enemy_skill(state, enemy, skill)
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

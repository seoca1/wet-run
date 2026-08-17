"""Combat view skill management — execute + VFX + cooldown logic (ADR-0110 split).

Split from combat_view.py (ADR-0143). Owns skill resolution: sound map,
execute_skill, skill availability check, VFX spawning, "skill unavailable"
reporting. combat_view.py is reduced to a thin coordinator that re-exports
these.

Module structure (post ADR-0143):
    - combat_view (thin coordinator + re-exports)
    - combat_view_input (existing — input handling)
    - combat_view_render: screen + _draw_* helpers
    - combat_view_skills (this file): skill management
    - combat_view_state: combat state mutations + lifecycle
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..combat.effects import spawn_hit_effects
from ..combat.state import (
    CombatState,
    Skill,
    SkillEffect,
    use_skill,
)
from .state import AppState

if TYPE_CHECKING:
    pass


# Skill effect → sound mapping (moved from combat_view for cohesion with skills module).
_SKILL_SOUND_MAP: dict[SkillEffect, str] = {
    SkillEffect.ATTACK: "combat/skill_physical",
    SkillEffect.HEAVY_ATTACK: "combat/skill_physical",
    SkillEffect.PIERCE: "combat/skill_physical",
    SkillEffect.MULTI_HIT: "combat/skill_physical",
    SkillEffect.DOT: "combat/skill_magic",
    SkillEffect.POISON: "combat/skill_magic",
    SkillEffect.SHIELD: "combat/block",
    SkillEffect.HEAL: "combat/skill_heal",
    SkillEffect.REGEN: "combat/skill_heal",
    SkillEffect.BUFF: "combat/skill_buff",
    SkillEffect.DEBUFF: "combat/skill_debuff",
    SkillEffect.STUN: "combat/stun",
    SkillEffect.LIFESTEAL: "combat/skill_physical",
    SkillEffect.DETECT: "ui/notification",
}


def _can_use_skill(combat_state: CombatState, skill: Skill) -> bool:
    """Check if a skill can be used (enough AP, no cooldown)."""
    player = combat_state.player
    cooldown_remaining = combat_state.skill_cooldowns.get(skill.id, 0)
    return player.ap >= skill.ap_cost and cooldown_remaining <= 0 and not combat_state.finished


def _execute_skill(
    state: AppState,
    combat_state: CombatState,
    skill: Skill,
) -> None:
    """Use ``skill`` (sound + VFX + ``use_skill``)."""
    state.status_messages.append(f">>> Used skill: {skill.name}")
    from ..audio import sound_manager as _sm

    sound_name = _SKILL_SOUND_MAP.get(skill.effect, "combat/skill_physical")
    _sm.get_sound_manager().play(sound_name)

    enemy = combat_state.enemy
    if enemy is None:
        return
    _player_hp_before = combat_state.player.hp
    _enemy_hp_before = enemy.hp
    use_skill(combat_state, skill)
    _spawn_skill_vfx(
        state,
        skill,
        combat_state,
        enemy_delta=_enemy_hp_before - enemy.hp,
        player_delta=_player_hp_before - combat_state.player.hp,
    )


def _report_skill_unavailable(
    state: AppState,
    combat_state: CombatState,
    skill: Skill,
) -> None:
    """Explain why the selected skill can't be used right now."""
    cooldown = combat_state.skill_cooldowns.get(skill.id, 0)
    if cooldown > 0:
        state.status_messages.append(f">>> {skill.name} on cooldown ({cooldown / 1000:.1f}s)")
    elif combat_state.player.ap < skill.ap_cost:
        state.status_messages.append(
            f">>> Not enough AP ({combat_state.player.ap}/{skill.ap_cost})"
        )


def _spawn_skill_vfx(
    state: AppState,
    skill: Skill,
    combat_state: CombatState,
    *,
    enemy_delta: int,
    player_delta: int,
) -> None:
    """Spawn VFX for a skill resolution. Called from handle_combat_input."""
    fx = state.combat_effects
    effect_name = skill.effect.value
    # Determine target based on skill effect
    if effect_name in ("heal", "regen", "buff", "shield"):
        # Self-targeted (player)
        target_x, target_y = 4.0, 8.0  # Left side (player)
        damage = -player_delta  # Show as positive heal
        spawn_hit_effects(
            fx,
            target_x,
            target_y,
            damage,
            effect_type=effect_name,
            is_crit=False,
        )
    elif effect_name in ("dot", "poison", "debuff", "stun", "detect"):
        # Enemy-targeted debuff
        target_x, target_y = 12.0, 8.0  # Right side (enemy)
        damage = max(0, enemy_delta)
        spawn_hit_effects(
            fx,
            target_x,
            target_y,
            damage,
            effect_type=effect_name,
            is_crit=False,
        )
    else:
        # Damaging skill (attack/heavy/pierce/multi/counter/lifesteal)
        target_x, target_y = 12.0, 8.0
        damage = max(0, enemy_delta)
        is_crit = damage > skill.damage * 1.4  # heuristic
        spawn_hit_effects(
            fx,
            target_x,
            target_y,
            damage,
            effect_type=effect_name,
            is_crit=is_crit,
        )
        # Lifesteal: also show heal on player
        if effect_name == "lifesteal" and player_delta < 0:
            spawn_hit_effects(
                fx,
                4.0,
                8.0,
                -player_delta,
                effect_type="heal",
                is_crit=False,
            )
        # Counter: also show small hit on player if reflected
        if effect_name == "counter" and player_delta < 0:
            spawn_hit_effects(
                fx,
                4.0,
                8.0,
                -player_delta,
                effect_type="attack",
                is_crit=False,
            )


def _get_skill_effect_description(skill: Skill) -> str:
    """Get a short description of what a skill does."""
    from ..combat.state import SkillEffect

    descriptions = {
        SkillEffect.ATTACK: f"Deal {skill.damage} damage",
        SkillEffect.HEAVY_ATTACK: f"SMASH for {skill.damage} damage",
        SkillEffect.PIERCE: f"{skill.damage} dmg (ignores shield)",
        SkillEffect.MULTI_HIT: f"Hit {skill.hit_count}x for {skill.damage} each",
        SkillEffect.DOT: f"{skill.damage} dmg + burn ({skill.dot_damage}/s)",
        SkillEffect.POISON: f"{skill.damage} dmg + poison ({skill.dot_damage}/s)",
        SkillEffect.SHIELD: f"+{skill.shield} shield",
        SkillEffect.HEAL: f"+{skill.heal} HP",
        SkillEffect.REGEN: f"+{skill.heal} HP over time",
        SkillEffect.BUFF: f"+{skill.buff_amount} attack power",
        SkillEffect.DEBUFF: f"Reduce enemy atk by {skill.buff_amount}",
        SkillEffect.STUN: f"Stun enemy for {skill.stun_duration_ms // 1000}s",
        SkillEffect.DETECT: "Reveal enemy stats",
        SkillEffect.LIFESTEAL: f"{skill.damage} dmg + heal half",
    }
    return descriptions.get(skill.effect, "Special effect")


# Re-exported by combat_view for backward compat (ADR-0110).
__all__ = [
    "_SKILL_SOUND_MAP",
    "_can_use_skill",
    "_execute_skill",
    "_get_skill_effect_description",
    "_report_skill_unavailable",
    "_spawn_skill_vfx",
]

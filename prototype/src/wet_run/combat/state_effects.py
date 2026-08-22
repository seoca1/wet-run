"""Combat skill effects (ADR-0156 split).

Per-SkillEffect handlers: damage skills (attack/heavy/pierce/multi/dot),
defense skills (shield/heal/regen/buff/debuff), crowd control (stun/stagger),
utility (detect/lifesteal), and enemy skill use. Used by ``use_skill`` in
``state.py`` and by ``step_combat`` for ICE auto-skills. Imports from
state.py are lazy to avoid circular dependency at module load.
"""

from __future__ import annotations

from .state_models import Combatant, CombatState, Skill, SkillEffect, StatusEffect

__all__ = [
    "ALLY_AUTO_ATTACK_INTERVAL_MS",
    "DIXIE_ALLY_DAMAGE",
    "apply_enemy_skill",
    "dispatch_skill_effect",
]

DIXIE_ALLY_DAMAGE = 5
ALLY_AUTO_ATTACK_INTERVAL_MS = 2000


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
    from .state import _apply_damage, _calculate_damage

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
    """Standard attack skill: damage the current target (or AOE if flagged)."""
    from .state import _apply_damage, _calculate_damage

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
    """Heavy attack skill: high-damage single-target or AOE, crit flavor 'DEVASTATING!'."""
    from .state import _apply_damage, _calculate_damage

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
    """Pierce skill: damage that bypasses target's shield (or AOE pierce)."""
    from .state import _apply_damage, _calculate_damage

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
    """Multi-hit skill: deal skill.damage ``skill.hit_count`` times to one target.

    Crits are disabled per hit to keep variance stable across rapid-fire attacks.
    """
    from .state import _apply_damage, _calculate_damage

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
    """Damage-over-time skill: immediate damage plus a burn status ticking for ``dot_duration_ms``."""
    from .state import _apply_damage, _calculate_damage

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
    from .gibson_fluff import push_fluff
    push_fluff(state, "burn")


def _apply_shield(state: CombatState, skill: Skill) -> None:
    """Shield skill: add ``skill.shield`` to player shield pool (no cap)."""
    state.shield += skill.shield
    _record_event(state, "shield", skill.effect_color)
    state.push(f">> {skill.name}: +{skill.shield} shield! (Total: {state.shield})")


def _apply_heal(state: CombatState, skill: Skill) -> None:
    """Heal skill: restore ``skill.heal`` HP to player, capped at max_hp."""
    healed = min(skill.heal, state.player.max_hp - state.player.hp)
    state.player.hp = min(state.player.max_hp, state.player.hp + skill.heal)
    _record_event(state, "heal", skill.effect_color)
    state.push(f">> {skill.name}: +{healed} HP restored!")


def _apply_regen(state: CombatState, skill: Skill) -> None:
    """Regen skill: apply a regen status that heals ``skill.heal // 10`` HP per tick."""
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
    """Buff skill: apply 'powered' status with +attack_bonus for buff_duration_ms."""
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
    """Debuff skill: apply 'weakened' status (negative attack_bonus) to current target."""
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
    """Stun skill: apply 'stun' status to current target for stun_duration_ms."""
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
    from .gibson_fluff import push_fluff
    push_fluff(state, "stun")


def _apply_slow(state: CombatState, skill: Skill) -> None:
    """Slow skill: apply 'slow' status to current target (slow_pct tick rate)."""
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="slow",
            remaining_ms=skill.buff_duration_ms,
            slow_pct=getattr(skill, "slow_pct", 50),
        )
    )
    _record_event(state, "slow", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} slowed!")
    from .gibson_fluff import push_fluff
    push_fluff(state, "slow")


def _apply_silence(state: CombatState, skill: Skill) -> None:
    """Silence skill: apply 'silence' status (prevents skill use) to current target."""
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="silence",
            remaining_ms=skill.buff_duration_ms,
            is_silenced=True,
        )
    )
    _record_event(state, "silence", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} silenced — no skill use!")
    from .gibson_fluff import push_fluff
    push_fluff(state, "silence")


def _apply_vulnerability(state: CombatState, skill: Skill) -> None:
    """Vulnerability skill: apply 'vulnerable' status (extra damage taken) to current target."""
    target = state.target
    if target is None:
        return
    target.statuses.append(
        StatusEffect(
            effect_id="vulnerable",
            remaining_ms=skill.buff_duration_ms,
            vulnerability_pct=getattr(skill, "vulnerability_pct", 25),
        )
    )
    _record_event(state, "debuff", skill.effect_color)
    state.push(f">> {skill.name}: {target.name} vulnerable (+damage taken)!")
    from .gibson_fluff import push_fluff
    push_fluff(state, "vulnerable")


def _apply_stagger(state: CombatState, skill: Skill) -> None:
    """Apply stagger to current target — skips their next auto-attack."""
    from .state import STAGGER_DURATION_MS

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
    """Detect skill: reveal current target's role-based weakness or HP/AP if unknown.

    Looks up WEAKNESS_BY_ICE for target.ice_kind; if found, reports the role with
    the largest damage multiplier (positive = weakness, negative = resistance).
    Otherwise reports raw HP/AP. Always pushes a player-facing message.
    """
    from .state import WEAKNESS_BY_ICE

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
    """Lifesteal skill: damage target then heal player for half the damage dealt (capped at max_hp)."""
    from .state import _apply_damage, _calculate_damage

    target = state.target
    if target is None:
        return
    dmg, _is_crit = _calculate_damage(state, skill.damage, state.player, target)
    applied = _apply_damage(state, target, dmg)
    healed = applied // 2
    state.player.hp = min(state.player.max_hp, state.player.hp + healed)
    _record_event(state, "lifesteal", skill.effect_color)
    state.push(f">> {skill.name}: {applied} damage, drained {healed} HP!")


def dispatch_skill_effect(state: CombatState, skill: Skill) -> None:
    """Dispatch a player skill to its effect-specific handler."""
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
        SkillEffect.SLOW: _apply_slow,
        SkillEffect.SILENCE: _apply_silence,
        SkillEffect.VULNERABLE: _apply_vulnerability,
        SkillEffect.STAGGER: _apply_stagger,
        SkillEffect.DETECT: _apply_detect,
        SkillEffect.LIFESTEAL: _apply_lifesteal,
    }
    handler = dispatch.get(skill.effect)
    if handler is None:
        state.push(f">> {skill.name}: used.")
    else:
        handler(state, skill)


def apply_enemy_skill(state: CombatState, enemy: Combatant, skill: Skill) -> None:
    """ICE uses a skill against the player.

    Wraps the existing player skill handlers by temporarily using the
    enemy as the "player" (attacker) and the actual player as the
    "target". Reuses damage calculations via _calculate_damage.

    ADR-0148: opens a 200ms counter window after enemy skill use.
    """
    from .state import STAGGER_DURATION_MS, _apply_damage, _calculate_damage

    state.last_skill_used = skill
    state.stats.skills_used += 1
    state.push(f"!! {enemy.name} uses {skill.name}!")
    from .depth import open_counter_window

    open_counter_window(state)
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

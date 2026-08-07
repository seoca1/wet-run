"""Boss AI decisions + AoE + minion spawn (ADR-0157 split).

Per-boss heuristic AI: ``boss_ai_choose_phase_effect`` picks between AoE
burst and minion spawn based on player HP. The minion spawn pipeline
(``scale_minion_spawn`` + ``spawn_phase_minions``) builds ICE enemies
via the registry. The AoE pipeline (``apply_phase_aoe`` +
``_trigger_aoe_visuals``) deals damage and triggers boss-specific VFX
shake/flash from the VFXTheme palette.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .boss import PhaseProfile, get_vfx_config
from .effects import IceType
from .registry import IceRegistry, ProgramRegistry
from .state import Combatant, CombatState

if TYPE_CHECKING:
    from ..portraits import PortraitManager

__all__ = [
    "apply_phase_aoe",
    "boss_ai_choose_phase_effect",
    "scale_minion_spawn",
    "spawn_phase_minions",
]


def scale_minion_spawn(
    phase: PhaseProfile,
    boss: Combatant,
    state: CombatState,
) -> tuple[str, ...]:
    """ADR-0125 M3: dynamic minion spawn intensity scaling.

    Scales the spawn_minions tuple based on:
      - Phase index (later phases spawn more minions)
      - Player grade (boss adapts to player power)
      - Player HP (desperate players get fewer adds)
    Returns the (possibly scaled) spawn list to use.
    """
    base_count = len(phase.spawn_minions)
    if base_count == 0:
        return ()

    phase_num = getattr(phase, "phase", None) or getattr(phase, "index", None) or 1
    phase_mult = 1.0 + (phase_num - 1) * 0.5
    grade_mult = 1.0 + max(0, (boss.equip_attack_bonus or 0) - 1) * 0.1

    player_hp_pct = 1.0
    for c in state.enemies:
        if c.team == "player":
            player_hp_pct = c.hp / max(1, c.max_hp)
            break
    hp_mult = 1.5 if player_hp_pct < 0.3 else (1.2 if player_hp_pct < 0.6 else 1.0)

    total_mult = phase_mult * grade_mult * hp_mult
    target_count = max(1, min(int(base_count * total_mult + 0.5), base_count * 3))
    if target_count >= base_count:
        return phase.spawn_minions
    return phase.spawn_minions[:target_count]


def spawn_phase_minions(
    boss: Combatant,
    phase: PhaseProfile,
    state: CombatState,
    ice_registry: IceRegistry,
    program_registry: ProgramRegistry,
    portraits: PortraitManager | None = None,
) -> list[Combatant]:
    """Phase B-3: spawn minion ICE at phase transition.

    ADR-0125 M3: applies scale_minion_spawn to adjust spawn count
    based on phase index, player grade, and player HP.
    """
    from .registry import build_ice_enemy

    spawn_list = scale_minion_spawn(phase, boss, state)
    spawned: list[Combatant] = []
    for ice_id in spawn_list:
        try:
            minion = build_ice_enemy(
                ice_id,
                ice_registry,
                portraits=portraits,
                program_registry=program_registry,
                player_grade=boss.equip_attack_bonus or 1,
            )
        except KeyError:
            continue
        spawned.append(minion)
    if spawned:
        state.enemies = state.enemies + tuple(spawned)
    return spawned


def boss_ai_choose_phase_effect(
    phase: PhaseProfile,
    state: CombatState,
) -> str:
    """ADR-0125 M4: boss AI decision logic for phase-effect selection.

    Heuristic: if player HP is low, prioritize AoE burst (finish them).
    Otherwise if boss is wounded, spawn adds (defend). Otherwise
    default to the phase's primary declared action.
    """
    has_aoe = phase.aoe_damage > 0
    has_spawn = bool(phase.spawn_minions)

    if not (has_aoe or has_spawn):
        return "none"

    player = getattr(state, "player", None)
    if player is not None and player.max_hp > 0:
        player_hp_pct = player.hp / player.max_hp
    else:
        player_hp_pct = 1.0

    if has_aoe and player_hp_pct < 0.4:
        return "aoe"
    if has_spawn and player_hp_pct > 0.7:
        return "spawn"
    if has_aoe:
        return "aoe"
    if has_spawn:
        return "spawn"
    return "none"


def apply_phase_aoe(
    phase: PhaseProfile,
    state: CombatState,
    ice_type: IceType | None = None,
) -> int:
    """Phase B-3: apply AoE damage from boss phase transition.

    Phase B-3.5 (ADR-0125 M2): also triggers visual effects:
      - Screen shake (intensity scales with aoe_damage)
      - Hit flash (red overlay)
    """
    if phase.aoe_damage <= 0:
        return 0
    state.player.hp = max(0, state.player.hp - phase.aoe_damage)
    phase_num = getattr(phase, "phase", None)
    if phase_num is None:
        phase_num = phase.index  # type: ignore[attr-defined]
    state.push(f"!! {phase.aoe_damage} AoE damage from phase {phase_num}!")
    _trigger_aoe_visuals(phase, state, ice_type)
    return phase.aoe_damage


def _trigger_aoe_visuals(
    phase: PhaseProfile, state: CombatState, ice_type: IceType | None = None
) -> None:
    """Phase B-3.5: trigger screen shake + hit flash for AoE burst.

    Intensity scales with aoe_damage (capped at 8.0 to avoid extreme
    shaking). Hit flash uses the phase's color, customized per boss type
    via VFXTheme config.
    """
    fx = getattr(state, "combat_effects", None)
    if fx is None:
        return

    vfx_config: dict[str, object] = {}
    if ice_type is not None:
        vfx_config = get_vfx_config(ice_type)

    base_intensity = min(8.0, 1.5 * phase.aoe_damage)
    shake_mult = vfx_config.get("shake_intensity_mult", 1.0)
    if not isinstance(shake_mult, (int, float)):
        shake_mult = 1.0
    intensity = min(8.0, base_intensity * shake_mult)
    duration = vfx_config.get("shake_duration_ms", 250 + int(phase.aoe_damage * 10))
    if not isinstance(duration, int):
        duration = 250 + int(phase.aoe_damage * 10)
    fx.shake.trigger(intensity, duration)

    hit_flash_color = vfx_config.get("hit_flash_color", phase.color)
    if not isinstance(hit_flash_color, tuple):
        hit_flash_color = phase.color
    hit_flash_duration = vfx_config.get("hit_flash_duration_ms", duration)
    if not isinstance(hit_flash_duration, int):
        hit_flash_duration = duration
    fx.hit_flash.trigger(hit_flash_color, hit_flash_duration)

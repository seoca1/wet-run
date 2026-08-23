"""Combat view render functions — screen + _draw_* helpers (ADR-0003, ADR-0110 split).

Split from combat_view.py (ADR-0143). Owns all rendering logic for the
combat screen: top-level coordinator + 6 _draw_* helpers + HP bar utility.
combat_view.py is reduced to a thin coordinator that re-exports these.

Module structure (post ADR-0143):
    - combat_view (thin coordinator + re-exports)
    - combat_view_input (existing — input handling)
    - combat_view_render (this file): render_combat + _draw_* helpers
    - combat_view_skills: skill management (_SKILL_SOUND_MAP, _execute_skill, etc.)
    - combat_view_state: combat state mutations + lifecycle (start_combat, _end_combat, etc.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tcod.console

from ..combat.battle_portraits import get_portrait
from ..combat.palette import (
    CYAN_PURE,
    DEFAULT_COLOR,
    GOLIATH_PARTICLE_COLOR,
    GRAY_160,
    GRAY_BLACK,
    GRAY_MID_DARK,
    GRAY_MID_LIGHT,
    GREEN_BRIGHT,
    GREEN_PURE,
    HIT_FLASH_COLOR,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    ICE_WARN_GOLD,
    PROBE_COLOR,
    SHIELD_COLOR,
    STUN_COLOR,
    WARM,
    YELLOW_ORANGE,
)
from ..combat.state import Skill
from .layout import (
    Region,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_side,
    draw_title,
    make_shell,
)
from .state import AppState

if TYPE_CHECKING:
    from ..combat.effects import CombatEffects
    from ..combat.state import CombatState
    from ..i18n import Translator
    from ..matrix.node import Node
    from ..matrix.ppl import calculate_ppl
    from ..matrix.zdr import node_status, node_zdr
    from .layout import RegionId
    from .status_panel import render_status_panel


def render_combat(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    combat_state: CombatState,
) -> None:
    """Render the combat screen (RT-MS, ADR-0003)."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    side_r = shell[RegionId.SIDE]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]
    panel_r = shell[RegionId.STATUS_PANEL]

    # Step combat VFX (animations, particles, shake, etc.)
    state.combat_effects.step(50)  # ~20 fps tick

    # Apply screen shake to draw origin
    shake_dx, shake_dy = state.combat_effects.shake.offset()

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console, shell)

    # Render persistent status panel
    render_status_panel(console, state, panel_r)

    # T2.3: achievement toast overlay — top of status panel, 3s auto-dismiss.
    from ..combat.achievement_toast_render import draw_achievement_toast

    draw_achievement_toast(console, panel_r, t, state)

    # Title
    ppl = calculate_ppl(state.player_loadout)
    # Assume current_node_id points to the ICE node
    ice_node: Node | None = None
    if state.matrix is not None and state.current_node_id is not None:
        ice_node = state.matrix.get(state.current_node_id)
    if ice_node is not None:
        zdr = node_zdr(ice_node)
        status = node_status(ice_node, ppl)
        ratio = ppl / zdr if zdr > 0 else float("inf")
        subtitle = f"PPL: {ppl}  vs  ZDR: {zdr}  |  Status: {status.value.upper()} ({ratio:.2f}x)"
    else:
        subtitle = "Combat"
    draw_title(console, title_r, title="COMBAT — RT-MS", subtitle=subtitle)

    # Main area: combatants + effects
    _draw_combatants(console, main_r, combat_state)
    _draw_combat_effects(console, main_r, combat_state)
    # VFX overlay (animations, particles, floating numbers, hit flash, cinematic)
    _draw_vfx_overlay(console, main_r, state.combat_effects, shake_dx, shake_dy)

    # Action log (in main area, below combatants)
    _draw_action_log(console, main_r, combat_state)

    # Side panel: skill menu (if paused) or stats
    if combat_state.finished:
        draw_side(
            console,
            side_r,
            label="Combat Over",
            lines=[
                f"Outcome: {combat_state.outcome.upper()}",
                f"Duration: {combat_state.tick_ms / 1000:.1f}s",
                f"Player HP: {combat_state.player.hp}/{combat_state.player.max_hp}",
            ],
        )
    else:
        _draw_skills_menu(console, side_r, combat_state, state)

    # Controls
    if combat_state.finished:
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "[Space] Continue  [ESC] Back to Hub",
                "[Q] Quit",
            ],
        )
    else:
        draw_controls(
            console,
            ctrl_r,
            lines=[
                "↑↓ Select Skill  ENTER Use  [1-9] Quick Use",
                "[ESC] Disengage  [Q] Quit",
            ],
        )

    # Footer with status messages
    elapsed_s = combat_state.tick_ms / 1000.0
    draw_footer(
        console,
        foot_r,
        text=f"Combat  |  T+{elapsed_s:.1f}s  |  Step {state.demo_step}",
        status_messages=state.status_messages,
    )

    # Phase E-2: first-combat tutorial overlay
    if getattr(state, "show_first_combat_tutorial", False):
        _draw_first_combat_tutorial(console, main_r)


def _draw_vfx_overlay(
    console: tcod.console.Console,
    region: Region,
    fx: CombatEffects,
    shake_dx: int,
    shake_dy: int,
) -> None:
    """Render VFX overlay on top of combat (Layer 1-5 effects)."""
    rx, ry, rw, rh = region.x, region.y, region.w, region.h

    # Clear the overlay area first to prevent afterimages (hit flash etc.)
    for y in range(ry, min(ry + rh, console.height)):
        for x in range(rx, min(rx + rw, console.width)):
            console.print(x=x, y=y, string=" ", fg=GRAY_BLACK, bg=GRAY_BLACK)

    # Hit flash: white overlay with alpha fade
    if fx.hit_flash.is_active:
        flash_char = "█"
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                if (x + y) % 3 == 0:  # sparse flash pattern
                    console.print(
                        x=x,
                        y=y,
                        string=flash_char,
                        fg=fx.hit_flash.color,
                    )

    # Animations: render current frame
    for anim in fx.animations:
        frame = anim.current_frame
        if frame is None:
            continue
        # Place in center of region
        cx = rx + rw // 2 + frame.offset[0] + shake_dx
        cy = ry + rh // 2 + frame.offset[1] + shake_dy
        if rx <= cx < rx + rw and ry <= cy < ry + rh:
            console.print(x=cx, y=cy, string=frame.text, fg=frame.color)

    # Particles
    for p in fx.particles.particles:
        px, py = int(p.x) + rx + shake_dx, int(p.y) + ry + shake_dy
        if rx <= px < rx + rw and ry <= py < ry + rh:
            # Fade color by mixing toward black
            alpha = p.alpha
            r, g, b = p.color
            faded: tuple[int, int, int] = (int(r * alpha), int(g * alpha), int(b * alpha))
            console.print(x=px, y=py, string=p.char, fg=faded)

    # Floating damage/heal numbers
    for n in fx.floating_numbers:
        nx, ny = int(n.x) + rx + shake_dx, int(n.y) + ry + shake_dy
        if rx <= nx < rx + rw and ry <= ny < ry + rh:
            # Brighten color for crits
            color = n.color
            if n.is_crit:
                color = (min(255, color[0] + 50), color[1], color[2])
            console.print(x=nx, y=ny, string=n.text, fg=color)

    # Cinematic (intro/death/critical) — large centered text
    if fx.cinematic is not None:
        phase = fx.cinematic.current_phase
        if phase is not None:
            text, color, _duration = phase
            cx = rx + (rw - len(text)) // 2
            cy = ry + rh // 2
            if rx <= cx < rx + rw and ry <= cy < ry + rh:
                console.print(x=cx, y=cy, string=text, fg=color)


def _draw_combatants(
    console: tcod.console.Console,
    main: Region,
    combat_state: CombatState,
) -> None:
    """Draw player and enemy portraits + HP bars."""
    player = combat_state.player
    enemy = combat_state.enemy
    if enemy is None:
        return

    # Player (left side)
    x = main.x + 4
    y = main.y + 2
    console.print(x=x, y=y, string=player.portrait, fg=player.color)
    y += 1
    console.print(x=x, y=y, string=f"{player.name}", fg=DEFAULT_COLOR)
    y += 1
    console.print(x=x, y=y, string=f"HP: {player.hp}/{player.max_hp}", fg=GREEN_PURE)
    y += 1
    hp_bar = _hp_bar(player.hp, player.max_hp, width=20)
    console.print(x=x, y=y, string=hp_bar, fg=GREEN_PURE)
    y += 1
    console.print(x=x, y=y, string=f"AP: {player.ap}/{player.max_ap}", fg=PROBE_COLOR)
    y += 1
    console.print(x=x, y=y, string=f"ATK: {player.auto_attack_damage}", fg=(180, 180, 180))
    if combat_state.shield > 0:
        y += 1
        console.print(
            x=x,
            y=y,
            string=f"Shield: {combat_state.shield}",
            fg=CYAN_PURE,
        )

    # Enemy (right side)
    x = main.x + main.w - 25
    y = main.y + 2
    enemy_portrait = get_portrait(
        ice_type=enemy.ice_kind or "standard",
        hp_ratio=enemy.hp / max(enemy.max_hp, 1),
        status_effect_ids=tuple(s.effect_id for s in enemy.statuses),
        phase=enemy.current_phase,
    )
    console.print(
        x=x,
        y=y,
        string=enemy_portrait.base_glyph + enemy_portrait.suffix,
        fg=enemy_portrait.color,
    )
    y += 1
    console.print(x=x, y=y, string=f"{enemy.name}", fg=DEFAULT_COLOR)
    y += 1
    console.print(x=x, y=y, string=f"HP: {enemy.hp}/{enemy.max_hp}", fg=GOLIATH_PARTICLE_COLOR)
    y += 1
    hp_bar = _hp_bar(enemy.hp, enemy.max_hp, width=20)
    console.print(x=x, y=y, string=hp_bar, fg=GOLIATH_PARTICLE_COLOR)

    # Boss Phase Info (Phase 15 + Phase 17 transition flash)
    if combat_state.boss_phase_tracker is not None:
        from typing import cast

        from ..combat.boss_phase_tracker import BossPhaseTracker

        tracker = cast(BossPhaseTracker, combat_state.boss_phase_tracker)
        progress = tracker.get_progress(enemy.hp, enemy.max_hp)
        y += 1
        phase_str = f"PHASE {progress.phase_index + 1}/{tracker.total_phases}"
        # Phase 17: flash the phase color for ~1.5s after a transition so
        # the player notices the change before the badge settles.
        flash_age_ms = combat_state.tick_ms - combat_state.phase_change_ms
        phase_color = combat_state.phase_change_color
        if flash_age_ms < 1500 and combat_state.phase_change_ms > 0:
            intensity = max(0.0, 1.0 - flash_age_ms / 1500.0)
            base = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR
            phase_color = (
                int(base[0] * (1 - intensity) + phase_color[0] * intensity),
                int(base[1] * (1 - intensity) + phase_color[1] * intensity),
                int(base[2] * (1 - intensity) + phase_color[2] * intensity),
            )
        console.print(x=x, y=y, string=phase_str, fg=phase_color)
        if not progress.is_last_phase:
            y += 1
            next_str = f"NEXT: {int(progress.hp_threshold * 100)}% HP"
            console.print(x=x, y=y, string=next_str, fg=ICE_WARN_GOLD)

    y += 1
    console.print(x=x, y=y, string=f"ATK: {enemy.auto_attack_damage}", fg=(180, 180, 180))


def _hp_bar(hp: int, max_hp: int, width: int = 20) -> str:
    """Generate an HP bar: [▓▓▓▓░░░░░]."""
    if max_hp <= 0:
        return "[" + "░" * width + "]"
    ratio = hp / max_hp
    filled = min(int(ratio * width), width)
    empty = width - filled
    return "[" + "▓" * filled + "░" * empty + "]"


def _draw_combat_effects(
    console: tcod.console.Console,
    main: Region,
    combat_state: CombatState,
) -> None:
    """Draw visual effects overlay (center of screen)."""
    # Only show recent effects (last 1 second)
    elapsed = combat_state.tick_ms - combat_state.last_event_tick
    if elapsed > 1500 or combat_state.last_event == "":
        return

    # Calculate effect intensity (fade over time)
    intensity = max(0, 1.0 - elapsed / 1500.0)

    # Get effect color and glyph
    color = combat_state.last_event_color
    glyph_map = {
        "player_attack": "─→",
        "enemy_attack": "←─",
        "skill_attack": "✦✦✦",
        "heavy_attack": "💥",  # Will render as multiple chars
        "pierce": "»»",
        "multi_hit": "≡≡≡",
        "dot": "♣",
        "shield": "◇",
        "heal": "+HP",
        "regen": "+♥",
        "buff": "↑ATK",
        "debuff": "↓ATK",
        "stun": "★",
        "lifesteal": "♥+",
    }
    text = glyph_map.get(combat_state.last_event, "*")

    # Apply intensity to color
    faded_color = (
        int(color[0] * intensity + 50 * (1 - intensity)),
        int(color[1] * intensity + 50 * (1 - intensity)),
        int(color[2] * intensity + 50 * (1 - intensity)),
    )

    # Draw effect text in center of screen
    center_y = main.y + 4
    center_x = main.x + (main.w - len(text)) // 2

    if 0 <= center_x and center_x + len(text) < main.x2:
        console.print(
            x=center_x,
            y=center_y,
            string=text,
            fg=faded_color,
        )


def _draw_action_log(
    console: tcod.console.Console,
    main: Region,
    combat_state: CombatState,
) -> None:
    """Draw the action log in the lower part of the main area."""
    x = main.x + 2
    y = main.y + 15
    console.print(x=x, y=y, string="═══ COMBAT LOG ═══", fg=(100, 100, 200))
    y += 1

    for i, line in enumerate(combat_state.log[-7:]):
        # Color code log entries
        line_lower = line.lower()
        if "critical" in line_lower or "devastating" in line_lower or "pierces" in line_lower:
            fg = ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR  # Yellow for crit
        elif "stun" in line_lower or "weakened" in line_lower:
            fg = YELLOW_ORANGE  # Orange for CC
        elif "burn" in line_lower or "poison" in line_lower:
            fg = GREEN_BRIGHT  # Green for DoT
        elif (
            "heal" in line_lower
            or "regen" in line_lower
            or "shield" in line_lower
            or "powered" in line_lower
        ):
            fg = SHIELD_COLOR  # Cyan for buffs
        elif "smash" in line_lower or "strikes" in line_lower:
            fg = GOLIATH_PARTICLE_COLOR  # Red for big attacks
        elif "hit" in line_lower or "damage" in line_lower:
            fg = DEFAULT_COLOR  # Gray for normal hits
        else:
            fg = (180, 180, 180)

        console.print(
            x=x,
            y=y + i,
            string=line[: main.w - 4],
            fg=fg,
        )


def _draw_skills_menu(
    console: tcod.console.Console,
    side_r: Region,
    combat_state: CombatState,
    state: AppState,
) -> None:
    """Draw skills menu with arrow key navigation support."""

    x = side_r.x + 2
    y = side_r.y + 1

    console.print(x=x, y=y, string="=== SKILLS ===", fg=HIT_FLASH_COLOR)
    y += 2

    selected_index = state.combat_skill_index
    player = combat_state.player

    for i, skill in enumerate(player.skills):
        is_selected = i == selected_index
        cooldown_remaining = combat_state.skill_cooldowns.get(skill.id, 0)
        is_disabled = not _can_use_skill(combat_state, skill)

        # Visual indicators
        cursor = ">" if is_selected else " "
        glyph = skill.effect_glyph

        # Tier badge: T1 grey → T6 gold (ADR-0008)
        tier_badge = f"T{skill.tier}"

        # Color and status based on state
        if cooldown_remaining > 0:
            fg = GRAY_MID_DARK  # Dark gray for cooldown
            status = f"[{cooldown_remaining / 1000:.1f}s]"
        elif is_disabled:
            fg = GRAY_MID_DARK  # Dark gray for disabled (not enough AP)
            status = f"[{skill.ap_cost} AP]"
        elif is_selected:
            fg = skill.effect_color  # Use skill's color
            status = f"[{skill.ap_cost} AP]"
        else:
            fg = DEFAULT_COLOR  # Light gray for normal
            status = f"[{skill.ap_cost} AP]"

        # Build line: cursor + key + glyph + tier + name + status
        line = f"{cursor} [{i + 1}] {glyph} {tier_badge} {skill.name} {status}"
        console.print(x=x, y=y + i, string=line, fg=fg)

        # Show effect type as small subtitle (if selected)
        if is_selected:
            effect_desc = _get_skill_effect_description(skill)
            console.print(
                x=x + 2,
                y=y + i + 1,
                string=effect_desc[: side_r.w - 4],
                fg=skill.effect_color,
            )

    # Show active status effects on player
    y = side_r.y + side_r.h - 12
    # Access statuses via getattr to avoid forward reference issues
    statuses = getattr(player, "statuses", []) or []
    if statuses:
        console.print(x=x, y=y, string="STATUS:", fg=(180, 180, 180))
        y += 1
        for status in statuses[:3]:
            secs_left = max(0, status.remaining_ms / 1000)
            line = f"  {status.effect_id}: {secs_left:.1f}s"
            color = WARM if "burn" in status.effect_id else GREEN_BRIGHT
            console.print(x=x, y=y, string=line, fg=color)
            y += 1

    # Instructions
    y = side_r.y + side_r.h - 6
    console.print(x=x, y=y, string="↑↓ Select  ENTER/SPACE Use", fg=GRAY_MID_LIGHT)
    y += 1
    console.print(x=x, y=y, string="1-9 Quick use", fg=GRAY_MID_LIGHT)
    y += 1
    console.print(x=x, y=y, string="ESC Disengage", fg=GRAY_MID_LIGHT)


def _draw_first_combat_tutorial(console: tcod.console.Console, region: Region) -> None:
    """Phase E-2: brief tutorial overlay for first combat encounter.

    Renders 4 lines of keyboard hints centered in the main region, surrounded
    by an ASCII box border and a skill-hotkey hint line. Persistent throughout
    first combat (every frame the ``show_first_combat_tutorial`` flag is True)
    and dismissed by Space/Enter (handled in input layer).
    """
    lines = [
        "== FIRST COMBAT ==",
        "[SPACE] open skill menu",
        "[1-9] quick-use skill",
        "[ESC] disengage",
    ]
    hint = "> Press 1-9 for skills"
    border_color = GRAY_160
    box_w = max(len(line) for line in lines) + 2  # pad 1 on each side
    box_w = max(box_w, len(hint) + 2)
    cx = region.x + (region.w - box_w) // 2
    cy = region.y + region.h // 2 - 1  # -1 to keep the hint line inside the box
    # Top border
    console.print(
        x=cx,
        y=cy,
        string=f"+{'-' * (box_w - 2)}+",
        fg=border_color,
    )
    # Body: pipe-wrapped lines
    for i, line in enumerate(lines):
        fg = STUN_COLOR if i == 0 else DEFAULT_COLOR
        body = f"|{line.center(box_w - 2)}|"
        console.print(x=cx, y=cy + 1 + i, string=body, fg=fg)
    # Hint row (last interior row)
    hint_row = cy + 1 + len(lines)
    console.print(
        x=cx,
        y=hint_row,
        string=f"|{hint.center(box_w - 2)}|",
        fg=(140, 200, 255),
    )
    # Bottom border
    console.print(
        x=cx,
        y=hint_row + 1,
        string=f"+{'-' * (box_w - 2)}+",
        fg=border_color,
    )


# Skill helpers (used by _draw_skills_menu — kept here for cohesion).
def _can_use_skill(combat_state: CombatState, skill: Skill) -> bool:
    """Check if a skill can be used (enough AP, no cooldown)."""
    player = combat_state.player
    cooldown_remaining = combat_state.skill_cooldowns.get(skill.id, 0)
    return player.ap >= skill.ap_cost and cooldown_remaining <= 0 and not combat_state.finished


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
    "_can_use_skill",
    "_draw_action_log",
    "_draw_combat_effects",
    "_draw_combatants",
    "_draw_first_combat_tutorial",
    "_draw_skills_menu",
    "_draw_vfx_overlay",
    "_get_skill_effect_description",
    "_hp_bar",
    "render_combat",
]

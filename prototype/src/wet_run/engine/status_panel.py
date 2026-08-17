"""Status panel: persistent right-side display of game state.

Shows player stats, inventory, mission, and recent activities.
Always visible across all screens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tcod.console

from ..matrix.ppl import calculate_ppl
from ..missions import Mission
from .layout import Region, clear_region
from .settings_ui import get_volume, is_muted
from .state import AppState

if TYPE_CHECKING:
    pass  # MaterialRegistry not yet implemented


def render_status_panel(
    console: tcod.console.Console,
    state: AppState,
    panel_region: Region,
    material_registry: Any | None = None,
) -> None:
    """Render the persistent status panel on the right side.

    panel_region should be the right column of the screen (e.g., 25 cols x 40 rows).
    """
    clear_region(console, panel_region)

    # Draw border
    _draw_panel_border(console, panel_region)

    x = panel_region.x + 1
    y = panel_region.y + 1
    max_width = panel_region.w - 2

    # Section 1: Player Stats
    y = _draw_player_stats(console, x, y, state, max_width)
    y += 1

    # Section 1.5: Equipment Summary
    y = _draw_equipment_summary(console, x, y, state, max_width)
    y += 1

    # Section 2: Current Screen
    y = _draw_current_screen(console, x, y, state, max_width)
    y += 1

    # Section 3: Mission
    y = _draw_mission_info(console, x, y, state, max_width)
    y += 1

    # Section 4: Inventory
    y = _draw_inventory(console, x, y, state, max_width, panel_region, material_registry)
    y += 1

    # Section 5: Recent Activity Log
    _draw_recent_activity(console, x, y, state, max_width, panel_region)


def _draw_panel_border(
    console: tcod.console.Console,
    region: Region,
) -> None:
    """Draw border around the panel."""
    fg = (80, 80, 80)
    # Corners
    console.print(x=region.x, y=region.y, string="+", fg=fg)
    console.print(x=region.x2, y=region.y, string="+", fg=fg)
    console.print(x=region.x, y=region.y2, string="+", fg=fg)
    console.print(x=region.x2, y=region.y2, string="+", fg=fg)
    # Edges
    for xi in range(region.x + 1, region.x2):
        console.print(x=xi, y=region.y, string="-", fg=fg)
        console.print(x=xi, y=region.y2, string="-", fg=fg)
    for yi in range(region.y + 1, region.y2):
        console.print(x=region.x, y=yi, string="|", fg=fg)
        console.print(x=region.x2, y=yi, string="|", fg=fg)


def _draw_equipment_summary(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
) -> int:
    """Draw a compact equipment summary with ASCII character.

    Returns the y-row just past the last drawn line.
    """
    y = _draw_equipment_header(console, x, y, max_width)
    loadout = getattr(state, "equipment_loadout", None)
    if loadout is None:
        console.print(x=x, y=y, string="(no equipment)", fg=(100, 100, 100))
        return y + 1
    y = _draw_equipment_slot_rows(console, x, y, loadout)
    return _draw_equipment_total(console, x, y, loadout)


# ------------------------------------------------------------------
# _draw_equipment_summary helpers
# ------------------------------------------------------------------


def _draw_equipment_header(
    console: tcod.console.Console,
    x: int,
    y: int,
    max_width: int,
) -> int:
    """Top + bottom section dividers plus the RIG label."""
    bar = "=" * (max_width - 1)
    console.print(x=x, y=y, string=bar, fg=(100, 200, 255))
    y += 1
    console.print(x=x, y=y, string=" RIG", fg=(100, 200, 255))
    y += 1
    console.print(x=x, y=y, string=bar, fg=(100, 200, 255))
    y += 1
    return y


def _draw_equipment_slot_rows(console: tcod.console.Console, x: int, y: int, loadout: Any) -> int:
    """Draw the 8 body-slot rows (head, eyes, body, gloves, boots, deck,
    implant, trodes).  Each row either shows the equipment glyph/tier
    or a dimmed ``[  ]`` placeholder.
    """
    from ..equipment.equipment import EquipSlot

    slot_labels: list[tuple[EquipSlot, str]] = [
        (EquipSlot.HEADWARE, "HEAD"),
        (EquipSlot.EYEWARE, "EYES"),
        (EquipSlot.BODYSUIT, "BODY"),
        (EquipSlot.GLOVES, "GRIP"),
        (EquipSlot.BOOTS, "BOOT"),
        (EquipSlot.DECK, "DECK"),
        (EquipSlot.IMPLANT, "IMPL"),
        (EquipSlot.TRODES, "TROD"),
    ]
    placeholder = "[  ]"
    for slot, label in slot_labels:
        item = loadout.get(slot)
        if item is None:
            console.print(x=x, y=y, string=f"{label}: {placeholder}", fg=(80, 80, 80))
        else:
            console.print(
                x=x,
                y=y,
                string=f"{label}: {item.ascii_glyph} {item.tier.value}",
                fg=item.ascii_color,
            )
        y += 1
    return y


def _draw_equipment_total(console: tcod.console.Console, x: int, y: int, loadout: Any) -> int:
    """Bottom line: total bonus summary across all slots."""
    stats = loadout.total_stats()
    total_bonuses = (
        stats.attack_bonus
        + stats.crit_bonus_pct
        + stats.defense
        + stats.hp_bonus
        + stats.shield_bonus
        + stats.ap_bonus
        + stats.program_power
        + stats.ice_resistance
    )
    if total_bonuses > 0:
        console.print(x=x, y=y, string=f"Total: +{total_bonuses} bonus", fg=(0, 255, 0))
    else:
        console.print(x=x, y=y, string="Total: (no bonuses)", fg=(100, 100, 100))
    y += 1
    return y


def _draw_player_stats(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
) -> int:
    """Draw player stats section. Returns new y position."""
    # Section title
    console.print(x=x, y=y, string="=" * max_width, fg=(0, 200, 200))
    y += 1
    console.print(x=x, y=y, string=" PLAYER ", fg=(0, 255, 255))
    y += 1
    console.print(x=x, y=y, string="=" * max_width, fg=(0, 200, 200))
    y += 1

    # PPL (Player Power Level)
    ppl = calculate_ppl(state.player_loadout)
    console.print(x=x, y=y, string=f"Grade: {state.player_grade}", fg=(200, 200, 200))
    y += 1
    console.print(x=x, y=y, string=f"PPL:   {ppl}", fg=(180, 180, 180))
    y += 1

    # HP/AP (in combat)
    if state.combat_state is not None:
        player = state.combat_state.player
        hp_pct = (player.hp / player.max_hp * 100) if player.max_hp > 0 else 0
        hp_color = _get_hp_color(hp_pct)

        console.print(
            x=x,
            y=y,
            string=f"HP:    {player.hp}/{player.max_hp}",
            fg=hp_color,
        )
        y += 1
        console.print(
            x=x,
            y=y,
            string=f"AP:    {player.ap}/{player.max_ap}",
            fg=(0, 200, 200),
        )
        y += 1

        # HP bar
        bar_width = max_width - 4
        filled = int((player.hp / player.max_hp) * bar_width) if player.max_hp > 0 else 0
        bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
        console.print(x=x, y=y, string=bar, fg=hp_color)
        y += 1
    else:
        # HP outside combat (from AppState)
        hp = state.player_hp if state.player_hp > 0 else 100  # Default to 100 if not set
        max_hp = state.player_max_hp if state.player_max_hp > 0 else 100
        hp_pct = (hp / max_hp * 100) if max_hp > 0 else 100
        hp_color = _get_hp_color(hp_pct)

        console.print(
            x=x,
            y=y,
            string=f"HP:    {hp}/{max_hp}",
            fg=hp_color,
        )
        y += 1

        # HP bar (outside combat)
        bar_width = max_width - 4
        filled = int((hp / max_hp) * bar_width) if max_hp > 0 else 0
        bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
        console.print(x=x, y=y, string=bar, fg=hp_color)
        y += 1

    return y


def _draw_current_screen(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
) -> int:
    """Draw current screen info. Returns new y position."""
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1
    console.print(x=x, y=y, string=" WHERE ", fg=(0, 255, 255))
    y += 1
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1

    screen_name = str(state.screen.value).upper()
    console.print(x=x, y=y, string=f"Screen: {screen_name}", fg=(200, 200, 200))
    y += 1

    # Screen-specific info
    if state.screen.value == "matrix" and state.matrix is not None:
        if state.current_node_id:
            current = state.matrix.get(state.current_node_id)
            if current:
                console.print(
                    x=x,
                    y=y,
                    string=f"At: {current.label[: max_width - 4]}",
                    fg=(255, 255, 0),
                )
                y += 1
                console.print(
                    x=x,
                    y=y,
                    string=f"Type: {current.kind.value}",
                    fg=(180, 180, 180),
                )
                y += 1
        if state.exploration is not None:
            visited = len(state.exploration.discovered)
            total = len(state.matrix.nodes)
            console.print(
                x=x,
                y=y,
                string=f"Visited: {visited}/{total}",
                fg=(180, 180, 180),
            )
            y += 1

    elif state.screen.value == "combat" and state.combat_state is not None:
        enemy = state.combat_state.enemy
        if enemy is not None:
            console.print(
                x=x, y=y, string=f"Enemy: {enemy.name[: max_width - 7]}", fg=(255, 100, 100)
            )
            y += 1
            hp_pct = (enemy.hp / enemy.max_hp * 100) if enemy.max_hp > 0 else 0
            console.print(
                x=x,
                y=y,
                string=f"EHp:   {enemy.hp}/{enemy.max_hp}",
                fg=_get_hp_color(hp_pct),
            )
            y += 1

    elif state.screen.value == "hub":
        console.print(x=x, y=y, string="At: The Sprawl Hub", fg=(180, 180, 180))
        y += 1

    elif state.screen.value == "cinematic":
        if state.cinematic_state is not None:
            scene = state.cinematic_state.scene
            console.print(x=x, y=y, string="Scene:", fg=(180, 180, 180))
            y += 1
            scene_title = scene.title_en[: max_width - 1]
            console.print(x=x, y=y, string=scene_title, fg=(255, 255, 0))
            y += 1

    return y


def _draw_mission_info(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
) -> int:
    """Draw current mission. Returns new y position."""
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1
    console.print(x=x, y=y, string=" MISSION ", fg=(0, 255, 255))
    y += 1
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1

    if state.current_mission is None:
        console.print(x=x, y=y, string="(none active)", fg=(128, 128, 128))
        y += 1
        return y

    mission: Mission = state.current_mission
    title = mission.title[: max_width - 1]
    console.print(x=x, y=y, string=title, fg=(255, 255, 0))
    y += 1

    if hasattr(mission, "client") and mission.client:
        client = mission.client[: max_width - 1]
        console.print(x=x, y=y, string=f"Client: {client}", fg=(180, 180, 180))
        y += 1

    if hasattr(mission, "reward"):
        console.print(
            x=x,
            y=y,
            string=f"Reward: {mission.reward} cr",
            fg=(255, 215, 0),
        )
        y += 1

    # Objective
    if hasattr(mission, "objective") and mission.objective:
        obj = mission.objective[: max_width - 1]
        console.print(x=x, y=y, string="Obj:", fg=(180, 180, 180))
        y += 1
        console.print(x=x, y=y, string=obj, fg=(200, 200, 200))
        y += 1

    return y


def _draw_inventory(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
    panel_region: Region,
    material_registry: Any | None,
) -> int:
    """Draw inventory section. Returns new y position."""
    # Check if we have space
    if y + 5 >= panel_region.y2:
        return y

    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1
    console.print(x=x, y=y, string=" INVENTORY ", fg=(0, 255, 255))
    y += 1
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1

    # Get inventory from state (if exists)
    inventory = getattr(state, "inventory", None)
    if not inventory:
        console.print(x=x, y=y, string="(empty)", fg=(128, 128, 128))
        y += 1
        return y

    # Count items
    if isinstance(inventory, dict):
        items = list(inventory.items())[:3]  # Top 3
        if not items:
            console.print(x=x, y=y, string="(empty)", fg=(128, 128, 128))
            y += 1
            return y

        for item_id, count in items:
            # Get name
            name = item_id
            if material_registry is not None:
                mat = material_registry.get(item_id)
                if mat is not None:
                    name = mat.name

            line = f"{name[: max_width - 6]} x{count}"
            console.print(x=x, y=y, string=line, fg=(200, 200, 200))
            y += 1
    else:
        console.print(x=x, y=y, string=f"Items: {len(inventory)}", fg=(200, 200, 200))
        y += 1

    return y


def _draw_recent_activity(
    console: tcod.console.Console,
    x: int,
    y: int,
    state: AppState,
    max_width: int,
    panel_region: Region,
) -> None:
    """Draw recent activity log."""
    # Check if we have space
    if y + 4 >= panel_region.y2:
        return

    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1
    console.print(x=x, y=y, string=" ACTIVITY ", fg=(0, 255, 255))
    y += 1
    console.print(x=x, y=y, string="-" * max_width, fg=(80, 80, 80))
    y += 1

    # Get recent status messages
    messages = state.status_messages[-3:]  # Last 3

    if not messages:
        console.print(x=x, y=y, string="(no activity)", fg=(128, 128, 128))
        return

    for msg in messages:
        if y >= panel_region.y2:
            break
        # Truncate message
        if len(msg) > max_width:
            msg = msg[: max_width - 3] + "..."
        console.print(x=x, y=y, string=msg, fg=(160, 160, 160))
        y += 1

    # Audio status (bottom of panel)
    y += 1
    if y < panel_region.y2 - 2:
        mute_label = "MUTED" if is_muted() else "ON"
        vol_pct = int(get_volume() * 100)
        console.print(x=x, y=y, string=" AUDIO ", fg=(0, 255, 255))
        y += 1
        if y < panel_region.y2:
            console.print(x=x, y=y, string=f"  {mute_label}  Vol:{vol_pct}%", fg=(160, 160, 160))
            y += 1
        if y < panel_region.y2:
            console.print(x=x, y=y, string="  [M] mute  [+/-] vol", fg=(100, 100, 100))


def _get_hp_color(hp_pct: float) -> tuple[int, int, int]:
    """Get color based on HP percentage."""
    if hp_pct >= 70:
        return (0, 255, 0)  # Green
    elif hp_pct >= 30:
        return (255, 255, 0)  # Yellow
    else:
        return (255, 50, 50)  # Red

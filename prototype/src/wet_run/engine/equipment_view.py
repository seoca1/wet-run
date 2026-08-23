"""Equipment visualizer: shows player's character with equipped gear.

Renders an ASCII character with equipment overlay.
"""

from __future__ import annotations

import tcod.console

from ..combat.palette import (
    CYAN_PURE,
    DEBUFF_COLOR,
    DEFAULT_COLOR,
    GOLIATH_PARTICLE_COLOR,
    GRAY_120,
    GRAY_LIGHT,
    GRAY_MID,
    GREEN_BRIGHT,
    ICE_GREEN_GLOW,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    MAGENTA_PINK,
    SHIELD_COLOR,
    WARM,
    YELLOW_ORANGE,
)
from ..equipment.equipment import (
    EquipmentLoadout,
    EquipSlot,
)
from ..equipment.wetware_stacking import stack_wetware
from .layout import Region, clear_region


def render_equipment_visualizer(
    console: tcod.console.Console,
    region: Region,
    loadout: EquipmentLoadout,
    inventory: dict[str, int] | None = None,
) -> None:
    """Render the player character with equipped gear.

    Shows:
    - ASCII character with equipment at each body slot
    - Total stats summary (including wetware stacking)
    - Equipment list
    """
    clear_region(console, region)
    _draw_border(console, region)

    x = region.x + 2
    y = region.y + 1
    max_w = region.w - 4

    # Title
    console.print(x=x, y=y, string="═══ RIG ═══", fg=SHIELD_COLOR)
    y += 1

    # Draw character with equipment
    _draw_character_with_gear(console, x, y, loadout)
    y += 11  # Character takes ~10 rows

    # Stats summary
    y += 1
    _draw_total_stats(console, x, y, loadout, inventory, max_w)
    y += 8

    # Equipment list
    if y < region.y2 - 1:
        _draw_equipment_list(console, x, y, loadout, region, max_w)


def _draw_border(console: tcod.console.Console, region: Region) -> None:
    """Draw border around the visualizer."""
    fg = (60, 60, 80)
    console.print(x=region.x, y=region.y, string="+", fg=fg)
    console.print(x=region.x2, y=region.y, string="+", fg=fg)
    console.print(x=region.x, y=region.y2, string="+", fg=fg)
    console.print(x=region.x2, y=region.y2, string="+", fg=fg)
    for xi in range(region.x + 1, region.x2):
        console.print(x=xi, y=region.y, string="-", fg=fg)
        console.print(x=xi, y=region.y2, string="-", fg=fg)
    for yi in range(region.y + 1, region.y2):
        console.print(x=region.x, y=yi, string="|", fg=fg)
        console.print(x=region.x2, y=yi, string="|", fg=fg)


def _draw_character_with_gear(
    console: tcod.console.Console,
    x: int,
    y: int,
    loadout: EquipmentLoadout,
) -> None:
    """Draw a character silhouette with equipment at body slots.

    Layout:
            [H]      <- headware
             |
           [E][E]    <- eyeware
         [B]     [B] <- bodysuit
          \\   /
           [|]     <- hands (gloves)
           / \
          [B] [B]  <- boots
           |
        (core)    <- deck (back-mounted)
    """
    # Get equipment
    head = loadout.get(EquipSlot.HEADWARE)
    eyes = loadout.get(EquipSlot.EYEWARE)
    body = loadout.get(EquipSlot.BODYSUIT)
    gloves = loadout.get(EquipSlot.GLOVES)
    boots = loadout.get(EquipSlot.BOOTS)
    deck = loadout.get(EquipSlot.DECK)
    implant = loadout.get(EquipSlot.IMPLANT)
    trodes = loadout.get(EquipSlot.TRODES)

    # Row 0: Title
    # Row 1: Empty
    # Row 2: Headware
    head_glyph = head.ascii_glyph if head else " o "
    head_fg = head.ascii_color if head else GRAY_LIGHT
    console.print(x=x + 5, y=y + 2, string=head_glyph, fg=head_fg)
    if head:
        console.print(x=x + 9, y=y + 2, string=f"  ← {head.tier.value}", fg=GRAY_120)

    # Row 3: Eyeware
    if eyes:
        eye_str = eyes.ascii_glyph
        eye_fg = eyes.ascii_color
        console.print(x=x + 4, y=y + 3, string=eye_str, fg=eye_fg)
        console.print(x=x + 4, y=y + 3, string="  ", fg=eye_fg)
    else:
        console.print(x=x + 5, y=y + 3, string=" o ", fg=GRAY_LIGHT)

    # Row 4: Torso (Bodysuit + Deck)
    body_glyph = body.ascii_glyph if body else "[|]"
    body_fg = body.ascii_color if body else GRAY_LIGHT
    console.print(x=x + 4, y=y + 4, string="─", fg=body_fg)
    console.print(x=x + 5, y=y + 4, string=body_glyph, fg=body_fg)
    console.print(x=x + 9, y=y + 4, string="─", fg=body_fg)

    # Row 5: Belt/loincloth area
    belt_str = "═══════════"
    console.print(x=x + 3, y=y + 5, string=belt_str, fg=body_fg)

    # Row 6: Arms (Gloves)
    arm_left = "/"
    arm_right = "\\"
    console.print(x=x + 1, y=y + 6, string=arm_left, fg=GRAY_LIGHT)
    console.print(x=x + 12, y=y + 6, string=arm_right, fg=GRAY_LIGHT)

    # Row 7: Gloves
    if gloves:
        glove_glyph = gloves.ascii_glyph
        glove_fg = gloves.ascii_color
        console.print(x=x, y=y + 7, string=glove_glyph, fg=glove_fg)
        console.print(x=x + 12, y=y + 7, string=glove_glyph, fg=glove_fg)
    else:
        console.print(x=x, y=y + 7, string=" |", fg=GRAY_MID)
        console.print(x=x + 12, y=y + 7, string="| ", fg=GRAY_MID)

    # Row 8: Hips / Legs start
    leg_left = "/"
    leg_right = "\\"
    console.print(x=x + 5, y=y + 8, string=leg_left, fg=GRAY_LIGHT)
    console.print(x=x + 8, y=y + 8, string=leg_right, fg=GRAY_LIGHT)

    # Row 9: Legs
    console.print(x=x + 4, y=y + 9, string="|", fg=GRAY_LIGHT)
    console.print(x=x + 9, y=y + 9, string="|", fg=GRAY_LIGHT)

    # Row 10: Boots
    if boots:
        boot_glyph = boots.ascii_glyph
        boot_fg = boots.ascii_color
        console.print(x=x + 3, y=y + 10, string=boot_glyph, fg=boot_fg)
        console.print(x=x + 8, y=y + 10, string=boot_glyph, fg=boot_fg)
    else:
        console.print(x=x + 3, y=y + 10, string="[ ]", fg=GRAY_MID)
        console.print(x=x + 8, y=y + 10, string="[ ]", fg=GRAY_MID)

    # Right side indicators (deck, implant, trodes)
    if deck:
        console.print(x=x + 17, y=y + 3, string="[DECK]", fg=deck.ascii_color)
        console.print(x=x + 17, y=y + 4, string=deck.tier.value, fg=GRAY_LIGHT)
    if implant:
        console.print(x=x + 17, y=y + 6, string="[IMPL]", fg=implant.ascii_color)
    if trodes:
        console.print(x=x + 17, y=y + 8, string="[TROD]", fg=trodes.ascii_color)


def _draw_total_stats(
    console: tcod.console.Console,
    x: int,
    y: int,
    loadout: EquipmentLoadout,
    inventory: dict[str, int] | None,
    max_w: int,
) -> None:
    """Draw total stats from all equipped items + wetware stacking."""
    stats = loadout.total_stats()

    # Wetware stacking (Phase 15)
    wetware_ids = []
    if inventory:
        # Assume wetware IDs are in inventory with count > 0
        # In a real run, we'd filter for actual wetware IDs
        from ..equipment.wetware_stacking import get_all_augments

        all_aug_ids = {a["id"] for a in get_all_augments()}
        wetware_ids = [k for k in inventory.keys() if k in all_aug_ids]

    stacked = stack_wetware(wetware_ids)

    console.print(x=x, y=y, string="─── STATS ───", fg=SHIELD_COLOR)
    y += 1

    # Combine equipment stats with wetware bonuses
    total_atk = stats.attack_bonus
    total_crit = stats.crit_bonus_pct + int(stacked.crit_chance * 100)
    total_hp = stats.hp_bonus + stacked.hp_bonus
    total_ap_regen = stats.ap_regen_bonus_pct + int(stacked.ap_regen * 100)
    total_shield = stats.shield_bonus + int(stacked.shield * 100)

    if total_atk > 0:
        console.print(x=x, y=y, string=f"ATK +{total_atk}", fg=GOLIATH_PARTICLE_COLOR)
        y += 1
    if total_crit > 0:
        console.print(x=x, y=y, string=f"CRIT +{total_crit}%", fg=ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR)
        y += 1
    if stats.damage_bonus_pct > 0:
        console.print(x=x, y=y, string=f"DMG +{stats.damage_bonus_pct}%", fg=(255, 150, 100))
        y += 1
    if stats.defense > 0:
        console.print(x=x, y=y, string=f"DEF +{stats.defense}", fg=SHIELD_COLOR)
        y += 1
    if total_hp > 0:
        console.print(x=x, y=y, string=f"HP +{total_hp}", fg=GOLIATH_PARTICLE_COLOR)
        y += 1
    if total_shield > 0:
        console.print(x=x, y=y, string=f"SHIELD +{total_shield}", fg=SHIELD_COLOR)
        y += 1
    if stats.ap_bonus > 0:
        console.print(x=x, y=y, string=f"AP +{stats.ap_bonus}", fg=CYAN_PURE)
        y += 1
    if total_ap_regen > 0:
        console.print(x=x, y=y, string=f"AP REGEN +{total_ap_regen}%", fg=CYAN_PURE)
        y += 1

    # New wetware stats (Phase 15)
    if stacked.armor > 0:
        console.print(x=x, y=y, string=f"ARMOR +{int(stacked.armor * 100)}%", fg=GRAY_LIGHT)
        y += 1
    if stacked.focus > 0:
        console.print(x=x, y=y, string=f"FOCUS +{int(stacked.focus * 100)}%", fg=WARM)
        y += 1

    if stats.program_power > 0:
        console.print(x=x, y=y, string=f"PROG PWR +{stats.program_power}", fg=DEBUFF_COLOR)
        y += 1
    if stats.ice_resistance > 0:
        console.print(x=x, y=y, string=f"ICE RES +{stats.ice_resistance}%", fg=GREEN_BRIGHT)
        y += 1

    if not any(
        [
            total_atk,
            total_crit,
            stats.damage_bonus_pct,
            stats.defense,
            total_hp,
            total_shield,
            stats.ap_bonus,
            total_ap_regen,
            stats.program_power,
            stats.ice_resistance,
            stacked.armor,
            stacked.focus,
        ]
    ):
        console.print(x=x, y=y, string="(no equipment)", fg=GRAY_MID)


def _draw_equipment_list(
    console: tcod.console.Console,
    x: int,
    y: int,
    loadout: EquipmentLoadout,
    region: Region,
    max_w: int,
) -> None:
    """Draw the list of equipped items."""
    console.print(x=x, y=y, string="─── EQUIPPED ───", fg=SHIELD_COLOR)
    y += 1

    for slot, equipment in loadout.equipment.items():
        if y >= region.y2 - 1:
            break
        # Slot label
        slot_label = _slot_short_label(slot)
        # Equipment info
        line = f"  {slot_label}: {equipment.name}"
        # Color by tier
        tier_color = _tier_color(equipment.tier)
        console.print(x=x, y=y, string=line[:max_w], fg=tier_color)
        y += 1


def _slot_short_label(slot: EquipSlot) -> str:
    """Short label for a slot."""
    labels = {
        EquipSlot.DECK.value: "DECK",
        EquipSlot.HEADWARE.value: "HEAD",
        EquipSlot.EYEWARE.value: "EYES",
        EquipSlot.BODYSUIT.value: "BODY",
        EquipSlot.GLOVES.value: "HAND",
        EquipSlot.BOOTS.value: "FEET",
        EquipSlot.IMPLANT.value: "IMPL",
        EquipSlot.TRODES.value: "TROD",
    }
    slot_key = getattr(slot, "value", slot)
    return labels.get(slot_key, str(slot_key).upper())


def _tier_color(tier: object) -> tuple[int, int, int]:
    """Color by tier."""
    colors = {
        "T0": GRAY_LIGHT,
        "T1": ICE_GREEN_GLOW,
        "T2": (100, 150, 255),
        "T3": DEBUFF_COLOR,
        "T4": YELLOW_ORANGE,
        "T5": MAGENTA_PINK,
    }
    return colors.get(str(getattr(tier, "value", tier)), DEFAULT_COLOR)

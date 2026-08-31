"""Hub screen: the cyberspace construct job board (ADR-0009, ADR-0017).

Meatspace is *not* shown (Pillar 2). The Hub is a text-based construct
interface. Fixer dialogue is also text-only — no portraits of meatspace
people.

Phase 5+: 4-panel layout (Avatar / Materials / Recipes / Job Board).
Uses unified screen shell (engine.layout).
"""

from __future__ import annotations

import json

import tcod.console
import tcod.event
from tcod.event import KeyDown, KeySym

from ..combat.palette import (
    DAMAGE_FLASH_COLOR,
    DEFAULT_COLOR,
    GLITCH_COLOR,
    GRAY_64,
    GRAY_160,
    GRAY_MID,
    GRAY_MID_LIGHT,
    GREEN_PURE,
    ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR,
    ORANGE_BRIGHT,
    PURPLE_LIGHT,
    RED_LIGHT,
    YELLOW_GOLD,
)
from ..i18n import Translator
from ..matrix.node import Faction
from ..matrix.ppl import calculate_ppl
from ..matrix.zdr import calculate_status, calculate_zdr, status_color
from ..missions import Mission
from . import config as _engine_config
from .layout import (
    Region,
    RegionId,
    clear_region,
    draw_controls,
    draw_dividers,
    draw_footer,
    draw_side,
    draw_title,
    make_shell,
)
from .state import AppState, ScreenKind


def render_hub(console: tcod.console.Console, t: Translator, state: AppState) -> None:
    """Render the Hub (job board) screen with unified layout."""
    shell = make_shell()
    title_r = shell[RegionId.TITLE]
    main_r = shell[RegionId.MAIN]
    side_r = shell[RegionId.SIDE]
    ctrl_r = shell[RegionId.CONTROLS]
    foot_r = shell[RegionId.FOOTER]

    # Clear and draw dividers
    for r in shell.values():
        clear_region(console, r)
    draw_dividers(console)

    # Title
    ppl = calculate_ppl(state.player_loadout)
    # Phase 6+: subtitle reflects Finn's reputation-based greeting
    # (so the player sees the effect of their faction standing at a
    # glance). Falls back to the default greeting if reputation is
    # neutral or the helper returns nothing.
    from .npc_greeting import get_greeting_text

    greeting = get_greeting_text("finn", state, korean=False)
    subtitle_base = greeting if greeting else t("hub.fixer_intro")
    subtitle = subtitle_base + f"  |  Grade: {state.player_grade}-up  |  PPL: {ppl}"
    draw_title(console, title_r, title=t("hub.title"), subtitle=subtitle)

    # Main area: 4-panel layout
    _draw_4panel(console, main_r, t, state, ppl)

    # Side panel: Mission details (if selected)
    available = state.job_board.available_for(state.player_grade)
    if available and 0 <= state.hub_selected_index < len(available):
        selected = available[state.hub_selected_index]
        zdr = _preview_zdr(selected)
        status = calculate_status(ppl, zdr)
        detail_lines = [
            f"Title: {selected.title}",
            f"Objective: {selected.objective}",
            f"ZDR: {zdr}  Status: {status.value.upper()}",
            f"Reward: T{selected.reward_tier} + {selected.reward_credits} cr",
        ]
        # Phase 17: annotate the selected mission with the random rule
        # that drove the recommendation (set by select_weighted).
        selected_rule_id = getattr(state, "last_rule_id", None)
        if selected_rule_id is not None:
            detail_lines.append("")
            detail_lines.append(f"Rule: {selected_rule_id}")
            if getattr(state, "show_active_rules", False):
                _append_active_rules(detail_lines, state)
        # Phase β-1: Fiction cross-reference link (if available)
        from pathlib import Path as _Path

        from ..data.story_resolver import (  # noqa: E402
            get_fiction_story_for_mission,
        )

        repo_root = _Path(__file__).resolve().parents[4]
        fiction = get_fiction_story_for_mission(selected.id, repo_root)
        if fiction is not None:
            detail_lines.append("")
            detail_lines.append(f"Fiction: {fiction['title_en']}")
            detail_lines.append(f"  ({fiction['word_count']}w, {fiction['character_ref']} POV)")
            detail_lines.append(f"  → {fiction['file']}")
        draw_side(
            console,
            side_r,
            label="Mission Details",
            lines=detail_lines,
        )
    else:
        draw_side(console, side_r, label="Mission Details", lines=["No mission selected"])

    # Controls
    from .save_manager import SaveManager

    has_saves = any(meta.exists for meta in SaveManager().list_slots())
    save_hint = "[F5] Save  [L] Load  " if has_saves else "[F5] Save  "
    draw_controls(
        console,
        ctrl_r,
        lines=[
            f"{save_hint}[1-9] Select Mission  [ESC] Back to Menu",
            "[Q] Quit",
        ],
    )

    # Footer with phase progress (Phase C-3)
    if state.run_state is not None:
        progress = state.run_state.progress_fraction()
        completed = state.run_state.stages_completed()
        total = state.run_state.stages_total()
        progress_text = (
            f"Hub  |  Phase {completed}/{total} "
            f"({int(progress * 100):3d}%)  T+{state.demo_elapsed_s:.1f}s"
        )
    else:
        progress_text = f"Hub  |  Step {state.demo_step}  T+{state.demo_elapsed_s:.1f}s"
    draw_footer(console, foot_r, text=progress_text)


def _draw_4panel(
    console: tcod.console.Console,
    main: Region,
    t: Translator,
    state: AppState,
    ppl: int,
) -> None:
    """Draw the 4-panel Hub layout in the MAIN region (ADR-0017).

    Layout (35 rows in main):
      Row 0-7:   Panel 1 - Avatar (left half)
      Row 0-7:   Panel 2 - Materials (right half)
      Row 8:     divider
      Row 9-16:  Panel 3 - Recipes (left half)
      Row 9-16:  Panel 4 - Job Board (right half)
      Row 17+:   overflow (job list continuation)
    """
    half_w = main.w // 2

    # Panel 1: Avatar (top-left)
    _draw_avatar_panel(console, main, x_offset=0, y_offset=0, width=half_w, state=state, ppl=ppl)

    # Panel 2: Materials (top-right)
    _draw_materials_panel(console, main, x_offset=half_w, y_offset=0, width=half_w, state=state)

    from .equipment_view import render_equipment_visualizer

    side_r = Region(id=RegionId.SIDE, x=main.x + half_w, y=main.y, w=half_w, h=main.h)
    render_equipment_visualizer(console, side_r, state.equipment_loadout, state.inventory)

    # Mid divider
    console.print(
        x=main.x,
        y=main.y + 8,
        string="─" * main.w,
        fg=GRAY_64,
    )

    # Panel 3: Recipes (bottom-left)
    _draw_recipes_panel(console, main, x_offset=0, y_offset=9, width=half_w, state=state)

    # Panel 4: Job Board (bottom-right)
    _draw_job_board_panel(
        console, main, x_offset=half_w, y_offset=9, width=half_w, state=state, ppl=ppl
    )


# Phase 6+: faction reputation dot colours keyed by tier. Each
# faction gets a coloured glyph reflecting their standing with the
# player (bright = friendly, dim = neutral, red = hostile).
_REPUTATION_GLYPHS: dict[str, str] = {
    "ALLIED": "★",
    "FRIENDLY": "●",
    "TRUSTED": "○",
    "NEUTRAL": "·",
    "HOSTILE": "✗",
    "ENEMY": "✗",
    "OUTCAST": "✗",
}

# Faction order shown in the rep strip (Sprawl's big 5 — plus the
# "ghost" NONE for unaligned fixers).
_REP_DISPLAY_ORDER: list[tuple[str, tuple[int, int, int]]] = [
    ("hosaka", (180, 50, 50)),  # red — corp
    ("maas", ORANGE_BRIGHT),  # amber — biz
    ("sense_net", (50, 200, 150)),  # teal — research
    ("ta", PURPLE_LIGHT),  # magenta — T-A
    ("none", GRAY_MID),  # grey — neutral
]


def _render_reputation_dots(state: AppState) -> str:
    """Render a compact faction-rep strip for the Hub.

    Each faction shown as a coloured glyph:
      ● green  = FRIENDLY+
      ○ cyan   = TRUSTED
      · grey   = NEUTRAL
      ✗ red    = HOSTILE+

    Returns a short string like "●○·✗·" for embedding in a single
    row of the avatar panel.
    """
    if not hasattr(state, "reputation"):
        return ""
    parts: list[str] = []
    for faction_name, _color in _REP_DISPLAY_ORDER:
        try:
            faction = Faction(faction_name)
        except ValueError:
            continue
        rep = state.reputation.get(faction)
        tier = rep.tier()
        glyph = _REPUTATION_GLYPHS.get(tier, "?")
        parts.append(glyph)
    return "".join(parts)


def _render_market_summary(state: AppState) -> str:
    """Render a one-line Info Market summary for the Hub.

    Shows the discounted T1 program price so the player sees their
    faction-discount in action. Example outputs:
      - "T1 100cr (neutral)"
      - "T1 50cr (Hosaka -50%)"
      - "T1 130cr (Maas +30%)"
      - "" if market unavailable
    """
    try:
        from ..crafting.info_market import InfoMarket
    except ImportError:
        return ""
    try:
        market = InfoMarket.load_default()
    except (OSError, ValueError):
        return ""
    t1 = market.get("t1_program")
    if t1 is None or t1.base_price is None:
        return ""
    # Cached (load_default has its own cache)
    if not hasattr(state, "reputation") or state.reputation is None:
        return f"T1 {t1.base_price}cr (neutral)"
    base = t1.base_price
    if t1.faction is None:
        return f"T1 {base}cr (neutral)"
    score = state.reputation.get(t1.faction).score
    final = t1.discounted_price(score)
    if final is None:
        return ""
    if final < base:
        pct = round((1 - final / base) * 100)
        return f"T1 {final}cr ({t1.faction.value} -{pct}%)"
    if final > base:
        pct = round((final / base - 1) * 100)
        return f"T1 {final}cr ({t1.faction.value} +{pct}%)"
    return f"T1 {final}cr (neutral)"


def _draw_avatar_panel(
    console: tcod.console.Console,
    main: Region,
    x_offset: int,
    y_offset: int,
    width: int,
    state: AppState,
    ppl: int,
) -> None:
    """Draw the Avatar panel (ADR-0016)."""
    x = main.x + x_offset + 2
    y = main.y + y_offset
    console.print(x=x, y=y, string="[Avatar]", fg=(180, 180, 180))
    y += 1
    # Simplified avatar (Phase 5: placeholder)
    console.print(x=x, y=y, string="  ◉P◉", fg=GREEN_PURE)
    y += 1
    console.print(x=x, y=y, string="  /|\\", fg=(180, 180, 180))
    y += 1
    console.print(x=x, y=y, string=" ★W★", fg=GLITCH_COLOR)
    y += 1
    console.print(
        x=x, y=y, string="║DK" + str(state.player_loadout.deck_tier) + "║", fg=DEFAULT_COLOR
    )
    y += 1
    console.print(x=x, y=y + 1, string=f"PPL: {ppl}", fg=GREEN_PURE)
    console.print(x=x, y=y + 2, string=f"Grade: {state.player_grade}-up", fg=DEFAULT_COLOR)

    # Phase 6+: faction reputation dots (compact display)
    # 5 factions: Hosaka, Maas, Sense/Net, TA, none — each shown
    # as a coloured dot whose intensity reflects reputation tier.
    rep_line = _render_reputation_dots(state)
    console.print(x=x, y=y + 4, string=f"Rep: {rep_line}", fg=(180, 180, 180))

    # Phase 6+: show the discounted Info Market price for T1 so the
    # player sees the effect of their faction standing at a glance.
    # GA-008 fix: removed duplicate render block that printed the same
    # market_line at the same coordinates a second time.
    market_line = _render_market_summary(state)
    if market_line:
        console.print(x=x, y=y + 5, string=f"Market: {market_line}", fg=(180, 180, 180))

    # HP bar
    hp = state.player_hp if state.player_hp > 0 else 100
    max_hp = state.player_max_hp if state.player_max_hp > 0 else 100
    hp_pct = (hp / max_hp * 100) if max_hp > 0 else 100
    if hp_pct > 60:
        hp_color = GREEN_PURE
    elif hp_pct > 30:
        hp_color = YELLOW_GOLD
    else:
        hp_color = DAMAGE_FLASH_COLOR
    bar_width = 8
    filled = int((hp / max_hp) * bar_width) if max_hp > 0 else 0
    bar = "[" + "=" * filled + " " * (bar_width - filled) + "]"
    console.print(x=x, y=y + 3, string=f"HP: {bar}", fg=hp_color)
    console.print(x=x + 9, y=y + 3, string=f"{hp}/{max_hp}", fg=hp_color)


_MATERIALS_CACHE: list[tuple[str, int, int]] | None = None
_RECIPES_CACHE: list[tuple[str, str, bool]] | None = None


def _load_materials_data(*, force_reload: bool = False) -> list[tuple[str, int, int]]:
    """Load material display data from JSON, falling back to placeholder.

    Returns list of (name, have, need) tuples. The ``have`` value is
    always 0 (placeholder) since the real inventory is in
    ``state.inventory``; only the ``need`` target is data-driven.

    The result is cached after first load to avoid re-parsing the
    JSON on every render frame (this function used to be called per
    frame and was a noticeable performance hot spot).
    """
    global _MATERIALS_CACHE
    if _MATERIALS_CACHE is not None and not force_reload:
        return _MATERIALS_CACHE
    path = _engine_config.DATA_DIR / "crafting" / "materials.json"
    result = _PLACEHOLDER_MATERIALS
    if path.exists():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = None
        if data is not None:
            items = data.get("materials", []) if isinstance(data, dict) else []
            parsed: list[tuple[str, int, int]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                need = int(item.get("need", 1))
                if name:
                    parsed.append((name, 0, need))
            if parsed:
                result = parsed
    _MATERIALS_CACHE = result
    return result


# Fallback when data/crafting/materials.json is missing or malformed.
_PLACEHOLDER_MATERIALS: list[tuple[str, int, int]] = [
    ("ICE Shard", 0, 5),
    ("Data Fragment", 0, 4),
    ("ROM Echo", 0, 3),
    ("Wetware Chip", 0, 2),
    ("Biosoft Agent", 0, 1),
]


def _draw_materials_panel(
    console: tcod.console.Console,
    main: Region,
    x_offset: int,
    y_offset: int,
    width: int,
    state: AppState,
) -> None:
    """Draw the Materials panel (ADR-0015, ADR-0017).

    Material targets load from ``data/crafting/materials.json`` (with
    a hardcoded fallback). Real ``have`` counts come from
    ``state.inventory`` so the player sees their actual stock.
    """
    x = main.x + x_offset + 2
    y = main.y + y_offset
    console.print(x=x, y=y, string="[Materials]", fg=(180, 180, 180))
    y += 1
    inventory = getattr(state, "inventory", None) or {}
    for name, _placeholder_have, need in _load_materials_data():
        if y >= main.y + y_offset + 7:
            break
        # Best-effort lookup by display name → inventory key map.
        inv_key = _MATERIAL_NAME_TO_INV.get(name, name.lower().replace(" ", "_"))
        have = int(inventory.get(inv_key, 0)) if isinstance(inventory, dict) else 0
        gauge = _material_gauge(have, need, width=5)
        console.print(
            x=x,
            y=y,
            string=f"{name[:14]:<14} {gauge} {have}/{need}",
            fg=GRAY_160,
        )
        y += 1


# Display name → inventory key map (data files use friendly names but
# inventory may use snake_case ids). Extend as needed.
_MATERIAL_NAME_TO_INV: dict[str, str] = {
    "ICE Shard": "ice_shard",
    "Data Fragment": "data_fragment",
    "ROM Echo": "rom_echo",
    "Wetware Chip": "wetware_chip",
    "Biosoft Agent": "biosoft_agent",
}


def _material_gauge(have: int, need: int, width: int = 5) -> str:
    """Generate a proportional gauge that preserves ratio information.

    Renders as ``▓▓▓░░`` blocks filling the full ``width`` based on
    the ``have/need`` ratio. The fill always reflects the actual
    fraction (e.g. 7/3 → 5/0 with a ``+`` overflow marker) instead
    of the older implementation that silently dropped overflow.

    Args:
        have: Current stock.
        need: Target stock.
        width: Bar width in characters (default 5).

    Returns:
        A string of length ``width`` (plus optional suffix) showing
        the fill ratio. Examples::

            _material_gauge(0, 4) == "░░░░░"
            _material_gauge(2, 4) == "██░░░"   # 50% of width
            _material_gauge(4, 4) == "█████"   # 100% (ready)
            _material_gauge(7, 3) == "█████+"  # overflow marker
            _material_gauge(3, 7) == "██░░░"   # 3/7 ≈ 43%
    """
    if need <= 0:
        # Degenerate: zero need target → show as ready.
        return "▓" * width
    if have >= need:
        # Ready (or over-stocked).
        bar = "▓" * width
        return bar + "+" if have > need else bar
    # Proportional fill: width chars showing have/need ratio.
    filled = round(width * have / need)
    filled = max(0, min(width, filled))
    empty = width - filled
    return "▓" * filled + "░" * empty


def _load_recipes_data(*, force_reload: bool = False) -> list[tuple[str, str, bool]]:
    """Load recipe display data from JSON, falling back to placeholder.

    Cached after first load to avoid re-parsing on every render frame.
    """
    global _RECIPES_CACHE
    if _RECIPES_CACHE is not None and not force_reload:
        return _RECIPES_CACHE
    path = _engine_config.DATA_DIR / "crafting" / "recipes.json"
    result = _PLACEHOLDER_RECIPES
    if path.exists():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = None
        if data is not None:
            items = data.get("recipes", []) if isinstance(data, dict) else []
            parsed: list[tuple[str, str, bool]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", ""))
                glyph = str(item.get("glyph", "···"))
                ready = bool(item.get("ready", False))
                if name:
                    parsed.append((name, glyph, ready))
            if parsed:
                result = parsed
    _RECIPES_CACHE = result
    return result


# Fallback when data/crafting/recipes.json is missing or malformed.
_PLACEHOLDER_RECIPES: list[tuple[str, str, bool]] = [
    ("T1 Program", "·W·", True),
    ("T2 Program", ":H:", False),
    ("T3 Program", "|G|", False),
    ("T4 Program", "▓W▓", False),
    ("T5 Kraken", "★K★", False),
]


def _draw_recipes_panel(
    console: tcod.console.Console,
    main: Region,
    x_offset: int,
    y_offset: int,
    width: int,
    state: AppState,
) -> None:
    """Draw the Recipes panel (ADR-0015, ADR-0017)."""
    x = main.x + x_offset + 2
    y = main.y + y_offset
    console.print(x=x, y=y, string="[Recipes]", fg=(180, 180, 180))
    y += 1
    for name, glyph, ready in _load_recipes_data():
        if y >= main.y + y_offset + 7:
            break
        status_str = "READY ✓" if ready else "need materials"
        fg = GREEN_PURE if ready else GRAY_MID_LIGHT
        console.print(
            x=x,
            y=y,
            string=f"{glyph}  {name:<12} {status_str}",
            fg=fg,
        )
        y += 1


def _draw_job_board_panel(
    console: tcod.console.Console,
    main: Region,
    x_offset: int,
    y_offset: int,
    width: int,
    state: AppState,
    ppl: int,
) -> None:
    """Draw the Job Board panel."""
    x = main.x + x_offset + 2
    y = main.y + y_offset
    console.print(x=x, y=y, string="[Job Board]", fg=(180, 180, 180))
    y += 1

    # Phase 6+: pass reputation so locked missions are excluded.
    rep = getattr(state, "reputation", None)
    available = state.job_board.available_for(state.player_grade, reputation=rep)
    locked_count = 0
    if rep is not None:
        locked_count = len(state.job_board.locked_for(rep))

    if not available:
        if locked_count > 0:
            console.print(
                x=x,
                y=y,
                string=f"All {locked_count} jobs LOCKED (faction rep)",
                fg=RED_LIGHT,
            )
        else:
            console.print(x=x, y=y, string="No jobs available", fg=GRAY_MID_LIGHT)
        return

    for i, mission in enumerate(available):
        if y >= main.y + main.h - 2:
            break
        zdr = _preview_zdr(mission)
        status = calculate_status(ppl, zdr)
        color = status_color(status)
        prefix = ">" if i == state.hub_selected_index else " "
        fg_title = (
            ICE_TYPE_TA_CONSTRUCT_PRIME_COLOR if i == state.hub_selected_index else DEFAULT_COLOR
        )

        console.print(
            x=x,
            y=y,
            string=f"{prefix}[{i + 1}] {mission.title[: width - 6]}",
            fg=fg_title,
        )
        y += 1
        console.print(
            x=x + 2,
            y=y,
            string=f"ZDR: {zdr} ({status.value})",
            fg=color,
        )
        y += 1
        console.print(
            x=x + 2,
            y=y,
            string=f"Reward: {mission.reward_credits} cr",
            fg=(200, 200, 0),
        )
        y += 2  # spacing

    # Phase 6+: show locked count footer.
    if locked_count > 0 and y < main.y + main.h - 1:
        console.print(
            x=x,
            y=y,
            string=f"[+{locked_count} jobs locked by rep]",
            fg=(140, 100, 100),
        )


def _preview_zdr(mission: Mission) -> int:
    """Return the ZDR of the mission's entry node (used as a quick preview)."""
    # We use the zone's base ZDR plus a sense_net faction modifier (typical Arc 1).
    from ..matrix.node import Faction

    faction = Faction.SENSE_NET  # Arc 1 default
    return calculate_zdr(mission.zone, faction=faction)


def _append_active_rules(detail_lines: list[str], state: AppState) -> None:
    """Append a short active-rules annotation to the hub side panel.

    Phase 17: When ``state.show_active_rules`` is True, list all rules
    whose trigger is currently satisfied for the player. The annotation
    is short (max 5 lines) so the side panel never overflows.
    """
    from ..missions.random_rules import get_all_active_rules

    active = get_all_active_rules(state)
    if not active:
        detail_lines.append("(no active rules)")
        return
    detail_lines.append("Active rules:")
    for rule in active[:5]:
        rule_id = str(rule.get("rule_id", "unknown"))
        detail_lines.append(f"  - {rule_id}")


def handle_hub_input(event: tcod.event.Event, state: AppState) -> bool:
    """Handle input on the Hub screen. Returns False to quit."""
    if isinstance(event, KeyDown):
        if event.sym in (KeySym.ESCAPE,):
            state.screen = ScreenKind.MENU
            state.message = ""
            return True
        if event.sym is KeySym.Q:
            return False
        # L: open save/load browser
        if event.sym is KeySym.L:
            from .save_load_view import enter_save_load

            enter_save_load(state)
            return True
        # M: open cyberspace map
        if event.sym is KeySym.M:
            _ensure_world_map(state)
            state.screen = ScreenKind.CYBERSPACE_MAP
            return True
        if event.sym in (KeySym.N1, KeySym.N2, KeySym.N3, KeySym.N4, KeySym.N5):
            available = state.job_board.available_for(state.player_grade)
            idx = int(event.sym.name[1:]) - 1
            if 0 <= idx < len(available):
                _start_mission(state, available[idx])
            elif available:
                # Phase 16 (ADR-0188): weighted fallback when no slice match.
                picked = state.job_board.select_weighted(state, available=available)
                if picked is not None:
                    _start_mission(state, picked)
        # Phase 16: ENTER at the hub (no mission in flight) biases the
        # selection cursor via random_rules so the recommended job
        # reflects the player's reputation / NG+ / chain unlocks.
        if event.sym is KeySym.RETURN and state.current_mission is None:
            available = state.job_board.available_for(state.player_grade)
            if available:
                picked = state.job_board.select_weighted(state, available=available)
                if picked is not None:
                    for i, m in enumerate(available):
                        if m.id == picked.id:
                            state.hub_selected_index = i
                            break
    return True


def _ensure_world_map(state: AppState) -> None:
    """Load world map if not already loaded."""
    if not hasattr(state, "world_map") or state.world_map is None:
        from ..cyberspace.registry import WorldRegistry
        from . import config as config_mod

        registry = WorldRegistry.load(config_mod.DATA_DIR / "cyberspace" / "worlds.json")
        state.world_map = registry.world_map


def _start_mission(state: AppState, mission: Mission) -> None:
    """Transition from Hub to Cyberspace Browser."""
    from ..cyberspace.registry import WorldRegistry

    state.current_mission = mission

    # Load world map if not loaded
    _ensure_world_map(state)
    assert state.world_map is not None

    # Find the server for this mission
    registry = WorldRegistry(state.world_map)
    location = registry.get_server_by_mission(mission.id)
    if location is not None:
        world_id, sector_id, server = location
        state.world_map.set_location(world_id, sector_id, server.id)
        # Find the server index

        world = state.world_map.get_current_world()
        if world is not None:
            sector = world.get_sector(sector_id)
            if sector is not None:
                for i, s in enumerate(sector.servers):
                    if s.id == server.id:
                        state.selected_server_index = i
                        break
    else:
        # Default to first sector's first server
        world = state.world_map.get_current_world()
        if world is not None and world.sectors:
            first_sector = list(world.sectors.values())[0]
            if first_sector.servers:
                state.world_map.set_location(
                    world.id,
                    first_sector.id,
                    first_sector.servers[0].id,
                )

    state.in_server_browser = True
    state.screen = ScreenKind.CYBERSPACE_BROWSER
    state.message = ""

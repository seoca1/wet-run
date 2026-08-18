#!/usr/bin/env python3
"""Full game flow demo WITH SOUND: Prologue → Briefing → Matrix → Combat.

This is the sound-enabled version of full_demo.py. Plays audio cues at every
major game event:
- Cinematic typing sound (per chunk of text)
- Dialogue advance sound (per line)
- Menu navigation sounds (UP/DOWN/ENTER/ESC)
- Movement sounds in cyberspace (per step)
- Jack-in sound (entering a server)
- Skill use sounds (physical/magic/heal/buff/debuff)
- Combat victory/defeat sounds
- Item pickup sound (after data extraction)

Usage:
  uv run python scripts/full_demo_sound.py
  uv run python scripts/full_demo_sound.py --skip-prologue
  uv run python scripts/full_demo_sound.py --fast
  uv run python scripts/full_demo_sound.py --no-sound  (silent mode)
  uv run python scripts/full_demo_sound.py --no-korean

Press Q to quit, ESC to skip current cinematic, ENTER to confirm.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from wet_run.combat.registry import IceRegistry, ProgramRegistry
from wet_run.combat.state import step_combat
from wet_run.engine import (
    combat_view,
    config,
    hub,
    story_cinematic,
)
from wet_run.engine.state import AppState, ScreenKind
from wet_run.engine.story_cinematic import (
    BRIEFING_FINN_SCENE,
    PROLOGUE_SCENE,
    CinematicState,
)
from wet_run.i18n import Translator
from wet_run.matrix.node import NodeKind
from wet_run.missions import JobBoard


def _safe_play(name: str) -> None:
    """Play a sound, swallowing all errors."""
    if not args.no_sound:
        try:
            from wet_run.audio import sound_manager

            sound_manager.play(name)
        except Exception:
            pass


# Module-level global for args (used by _safe_play closure)
args: argparse.Namespace


def main() -> int:
    global args
    parser = argparse.ArgumentParser(description="Full game flow demo WITH SOUND")
    parser.add_argument("--skip-prologue", action="store_true", help="Skip prologue")
    parser.add_argument("--fast", action="store_true", help="Fast typing speed")
    parser.add_argument("--auto-combat", action="store_true", help="Auto-play combat")
    parser.add_argument("--no-korean", action="store_true", help="Disable Korean subtitles")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--manual-combat", action="store_true", help="Manual combat")
    parser.add_argument("--no-sound", action="store_true", help="Disable sound (silent mode)")
    parser.add_argument(
        "--volume", type=float, default=0.2, help="Master volume 0.0-1.0 (default 0.2)"
    )
    args = parser.parse_args()

    if not args.interactive and not args.manual_combat:
        args.auto_combat = True

    # Set up sound volume
    if not args.no_sound:
        from wet_run.audio import sound_manager

        sm = sound_manager.get_sound_manager()
        sm.set_volume(args.volume)
        print(
            f"[SOUND] Backend: {sm._tool} | Volume: {int(args.volume * 100)}% | "
            f"Available: {sm.is_available()} | Sounds: {len(sm.list_sounds())}"
        )

    # Font check
    if not config.FONT_PATH.exists() and config.find_ttf_font() is None:
        sys.stderr.write("ERROR: No font found (bitmap or TTF)\nRun: make download-font\n")
        return 1

    from wet_run.engine.font_loader import load_font

    tileset, _ = load_font()

    t = Translator(config.DEFAULT_LANGUAGE, data_dir=config.DATA_DIR / "i18n")
    prog_registry = ProgramRegistry.load(config.DATA_DIR / "programs" / "programs.json")
    ice_registry = IceRegistry.load(config.DATA_DIR / "combat" / "ice_types.json")

    state = AppState()
    state.job_board = JobBoard.load(config.DATA_DIR / "missions" / "missions.json")

    # Starting equipment
    from wet_run.equipment.equipment import (
        STARTER_DECK,
        STARTER_HEADWARE,
        EquipmentLoadout,
        EquipmentRegistry,
    )

    equip_reg = EquipmentRegistry.load_default()
    state.equipment_loadout = EquipmentLoadout()
    state.equipment_loadout.equip(equip_reg.get("deck_basic") or STARTER_DECK)
    state.equipment_loadout.equip(equip_reg.get("head_basic") or STARTER_HEADWARE)

    if args.skip_prologue:
        _start_briefing(state, args.fast, args.no_korean)
    else:
        _start_prologue(state, args.fast, args.no_korean)
        # Opening sound
        _safe_play("story/event_trigger")

    start_time = time.time()

    with tcod.context.new(
        columns=config.SCREEN_WIDTH,
        rows=config.SCREEN_HEIGHT,
        tileset=tileset,
        title=f"{config.SCREEN_TITLE} — Sound Demo",
        vsync=True,
    ) as context:
        root_console = tcod.console.Console(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, order="F")

        running = True
        last_combat_step = 0
        last_npc_step = 0
        last_auto_step = 0
        visited_npc_dixie = False
        visited_data = False
        visited_ice = False
        npc_triggered = False
        combat_started = False
        last_node_id: str | None = None

        while running:
            elapsed_s = time.time() - start_time
            elapsed_ms = int(elapsed_s * 1000)
            state.demo_elapsed_s = elapsed_s
            state.demo_step += 1

            if state.screen is ScreenKind.CINEMATIC and state.cinematic_state is not None:
                story_cinematic.step_cinematic(state.cinematic_state, elapsed_ms)
                if state.cinematic_state.finished:
                    _safe_play("story/event_trigger")
                    _advance_demo_stage(state, prog_registry, ice_registry)

            if state.screen is ScreenKind.COMBAT and state.combat_state is not None:
                if state.demo_step - last_combat_step > 6:
                    # Detect hit/crit/miss sounds via combat log
                    old_log_len = len(state.combat_state.log)
                    step_combat(state.combat_state)
                    last_combat_step = state.demo_step
                    new_entries = state.combat_state.log[old_log_len:]
                    for entry in new_entries:
                        if "CRIT" in entry or "critical" in entry.lower():
                            _safe_play("combat/hit_crit")
                        elif "miss" in entry.lower() or "dodge" in entry.lower():
                            _safe_play("combat/hit_miss")
                        elif "hit" in entry.lower() or "damage" in entry.lower():
                            _safe_play("combat/hit_normal")

                    if state.combat_state.finished:
                        outcome = state.combat_state.outcome
                        print(f"\n=== Combat finished: {outcome} ===")
                        if outcome == "victory":
                            _safe_play("combat/victory")
                            print(">>> Rewards: 1x ICE Shard, 50 credits")
                        else:
                            _safe_play("combat/defeat")
                        time.sleep(2.5)
                        from wet_run.engine.combat_view import _end_combat

                        _end_combat(state, state.combat_state)
                        state.combat_state = None
                        state.message = "Combat ended."
                        print(f"=== Returned to: {state.screen} ===")

            if (
                not args.interactive
                and state.screen is ScreenKind.NPC
                and state.npc_state is not None
            ):
                if state.demo_step - last_npc_step > 180:
                    from wet_run.engine import npc_view

                    _safe_play("story/dialogue_advance")
                    line = state.npc_state.event.get_line(state.npc_state.current_line_index)
                    if line and line.choices:
                        npc_view._execute_choice(state, state.npc_state, line.choices[0])
                    else:
                        npc_view._advance_dialogue(state, state.npc_state)
                    last_npc_step = state.demo_step

            # Auto-jack in from cyberspace browser (demo mode)
            if (
                not args.interactive
                and state.screen is ScreenKind.CYBERSPACE_BROWSER
                and hasattr(state, "_browser_auto_step")
                and state.demo_step - state._browser_auto_step > 90
            ):
                # ~1.5s at 60 FPS — auto-jack in
                from tcod.event import KeySym, Modifier, Scancode

                from wet_run.engine import cyberspace_browser as _cs_browser

                ev = tcod.event.KeyDown(
                    sym=KeySym.RETURN, scancode=Scancode.RETURN, mod=Modifier.NONE
                )
                _cs_browser.handle_browser_input(ev, state)
                state._browser_auto_step = state.demo_step
            elif not args.interactive and state.screen is ScreenKind.CYBERSPACE_BROWSER:
                # First time entering browser — start the auto timer
                state._browser_auto_step = state.demo_step

            if (
                not args.interactive
                and state.screen is ScreenKind.MATRIX
                and not state.action_menu_open
            ):
                if state.matrix is not None and state.current_node_id is not None:
                    current_node = state.matrix.get(state.current_node_id)
                    if current_node is not None:
                        # Play arrival sound when entering a new node
                        if state.current_node_id != last_node_id:
                            if last_node_id is not None:
                                _safe_play("movement/nav_step")
                            last_node_id = state.current_node_id

                        if state.demo_step - last_auto_step > 30:
                            from tcod.event import KeySym

                            from wet_run.engine import cyberspace_view

                            npc_target = None
                            data_target = None
                            ice_target = None
                            for n in state.matrix.nodes:
                                if n.kind is NodeKind.CONSTRUCT and npc_target is None:
                                    npc_target = n.id
                                elif n.kind is NodeKind.DATA and data_target is None:
                                    data_target = n.id
                                elif n.kind is NodeKind.ICE and ice_target is None:
                                    ice_target = n.id

                            target_id: str | None = None
                            if (
                                not visited_npc_dixie
                                and npc_target
                                and state.current_node_id != npc_target
                            ):
                                target_id = npc_target
                            elif (
                                not visited_data
                                and data_target
                                and state.current_node_id != data_target
                            ):
                                target_id = data_target
                            elif (
                                not visited_ice
                                and ice_target
                                and state.current_node_id != ice_target
                            ):
                                target_id = ice_target

                            if (
                                npc_target
                                and state.current_node_id == npc_target
                                and not visited_npc_dixie
                            ):
                                if not npc_triggered:
                                    from wet_run.engine.npc_event import (
                                        DIXIE_FLATLINE_EVENT,
                                        NPCState,
                                    )

                                    _safe_play("story/event_trigger")
                                    state.npc_state = NPCState(event=DIXIE_FLATLINE_EVENT)
                                    state.screen = ScreenKind.NPC
                                    npc_triggered = True
                                    print(f"\n=== NPC ENCOUNTER: {current_node.label} ===")
                            elif (
                                data_target
                                and state.current_node_id == data_target
                                and not visited_data
                            ):
                                visited_data = True
                                from wet_run.engine import action_menu

                                _safe_play("items/pickup")
                                action_menu._execute_action(
                                    state, current_node, "extract", prog_registry, ice_registry
                                )
                                print("\n=== Data extracted ===")
                            elif (
                                ice_target
                                and state.current_node_id == ice_target
                                and not visited_ice
                            ):
                                visited_ice = True
                                if not combat_started:
                                    state.action_menu_open = True
                                    combat_started = True
                                    _safe_play("combat/hit_normal")
                                    print(f"\n=== ICE detected: {current_node.label} ===")

                            at_stop = (
                                npc_target
                                and state.current_node_id == npc_target
                                and not visited_npc_dixie
                            ) or (
                                ice_target
                                and state.current_node_id == ice_target
                                and not visited_ice
                            )
                            if target_id and state.current_node_id != target_id and not at_stop:
                                if state.cyberspace_layouts is None:
                                    # Layouts not initialized — skip movement
                                    continue
                                current_layout = state.cyberspace_layouts.get(state.current_node_id)
                                target_layout = state.cyberspace_layouts.get(target_id)
                                if current_layout and target_layout:
                                    cx, cy = current_layout.x, current_layout.y
                                    tx, ty = target_layout.x, target_layout.y
                                    if tx > cx:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.RIGHT
                                        )
                                    elif tx < cx:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.LEFT
                                        )
                                    elif ty > cy:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.DOWN
                                        )
                                    elif ty < cy:
                                        cyberspace_view._handle_cyberspace_movement(
                                            state, KeySym.UP
                                        )

                            last_auto_step = state.demo_step

            if (
                state.screen is ScreenKind.MATRIX
                and state.npc_state is None
                and not visited_npc_dixie
            ):
                visited_npc_dixie = True

            _render_demo(root_console, t, state, prog_registry, ice_registry)
            context.present(root_console)

            for event in tcod.event.wait(timeout=0.016):
                if not _handle_demo_input(event, state, prog_registry, ice_registry):
                    running = False
                    break

    print("\n=== Demo finished ===")
    print(f"Total time: {elapsed_s:.1f}s")
    print(f"Final screen: {state.screen}")
    return 0


def _start_prologue(state: AppState, fast: bool, no_korean: bool = False) -> None:
    scene = PROLOGUE_SCENE
    if fast:
        scene = _make_fast_scene(scene)
    state.screen = ScreenKind.CINEMATIC
    state.cinematic_state = CinematicState(scene=scene, show_korean=not no_korean)


def _start_briefing(state: AppState, fast: bool, no_korean: bool = False) -> None:
    scene = BRIEFING_FINN_SCENE
    if fast:
        scene = _make_fast_scene(scene)
    state.screen = ScreenKind.CINEMATIC
    state.cinematic_state = CinematicState(scene=scene, show_korean=not no_korean)


def _make_fast_scene(scene: story_cinematic.StoryScene) -> story_cinematic.StoryScene:
    from wet_run.engine.story_cinematic import StoryLine, TextSpeed

    new_lines = tuple(
        StoryLine(
            text_en=line.text_en,
            text_ko=line.text_ko,
            speaker=line.speaker,
            portrait=line.portrait,
            effect=line.effect,
            speed=TextSpeed.FAST,
            pause_ms=200,
        )
        for line in scene.lines
    )
    return story_cinematic.StoryScene(
        id=scene.id,
        title_en=scene.title_en,
        title_ko=scene.title_ko,
        lines=new_lines,
        next_scene=scene.next_scene,
    )


def _advance_demo_stage(
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    if state.cinematic_state is None:
        return
    scene_id = state.cinematic_state.scene.id

    if scene_id == "prologue_sprawl":
        print("\n=== Prologue finished → Starting briefing ===")
        time.sleep(1)
        show_korean = state.cinematic_state.show_korean
        _start_briefing(state, fast=False, no_korean=not show_korean)
    elif scene_id == "briefing_finn_first_jack":
        print("\n=== Briefing finished → Jacking into matrix ===")
        time.sleep(1)
        _start_matrix(state)
    else:
        state.screen = ScreenKind.HUB
        state.cinematic_state = None


def _start_matrix(state: AppState) -> None:
    from wet_run.cyberspace.registry import WorldRegistry

    available = state.job_board.available_for(state.player_grade)
    if not available:
        print("ERROR: No missions available")
        state.screen = ScreenKind.HUB
        return

    first_mission = available[0]
    state.current_mission = first_mission
    _safe_play("movement/jack_in")

    if not hasattr(state, "world_map") or state.world_map is None:
        registry = WorldRegistry.load(config.DATA_DIR / "cyberspace" / "worlds.json")
        state.world_map = registry.world_map

    registry = WorldRegistry(state.world_map)
    location = registry.get_server_by_mission(first_mission.id)
    if location is not None:
        world_id, sector_id, server = location
        state.world_map.set_location(world_id, sector_id, server.id)
        world = state.world_map.get_current_world()
        if world:
            sector = world.get_sector(sector_id)
            if sector:
                for i, s in enumerate(sector.servers):
                    if s.id == server.id:
                        state.selected_server_index = i
                        break

    state.in_server_browser = True
    state.screen = ScreenKind.CYBERSPACE_BROWSER
    state.message = "Select a server to jack into."

    print(f"\n=== Cyberspace browser: {len(state.world_map.worlds)} worlds available ===")


def _render_demo(
    console: tcod.console.Console,
    t: Translator,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> None:
    if state.screen is ScreenKind.CINEMATIC:
        if state.cinematic_state is not None:
            elapsed_ms = int(state.demo_elapsed_s * 1000)
            story_cinematic.render_cinematic(console, t, state, state.cinematic_state, elapsed_ms)
    elif state.screen is ScreenKind.MENU:
        console.clear(bg=(0, 0, 0))
        console.print(x=35, y=20, string="Wet Run", fg=(0, 255, 255))
        console.print(x=30, y=22, string="Demo transitioning...", fg=(200, 200, 200))
        console.print(x=28, y=24, string="Press any key to continue", fg=(128, 128, 128))
    elif state.screen is ScreenKind.HUB:
        hub.render_hub(console, t, state)
    elif state.screen is ScreenKind.CYBERSPACE_BROWSER:
        from wet_run.engine import cyberspace_browser

        cyberspace_browser.render_cyberspace_browser(console, t, state)
    elif state.screen is ScreenKind.MATRIX:
        from wet_run.engine import cyberspace_view

        cyberspace_view.render_cyberspace(console, t, state, prog_registry, ice_registry)
    elif state.screen is ScreenKind.NPC:
        from wet_run.engine import npc_view

        if state.npc_state is not None:
            npc_view.render_npc(console, t, state, state.npc_state)
    elif state.screen is ScreenKind.EVENT:
        from wet_run.engine import event_view

        if state.active_event is not None:
            event_view.render_event_story(console, t, state, state.active_event)
    elif state.screen is ScreenKind.COMBAT:
        if state.combat_state is not None:
            combat_view.render_combat(console, t, state, state.combat_state)
    else:
        console.clear(bg=(0, 0, 0))
        console.print(x=2, y=2, string=f"Unknown screen: {state.screen}", fg=(255, 0, 0))


def _handle_demo_input(
    event: object,
    state: AppState,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> bool:
    import tcod.event

    if not isinstance(event, tcod.event.KeyDown):
        return True

    if event.sym is tcod.event.KeySym.Q:
        return False

    # Global mute toggle
    if event.sym is tcod.event.KeySym.M:
        from wet_run.audio import sound_manager

        muted = sound_manager.toggle_mute()
        print(f"\n[SOUND] {'MUTED' if muted else 'UNMUTED'}")
        return True

    if state.screen is ScreenKind.CINEMATIC:
        if state.cinematic_state is not None:
            _safe_play("story/dialogue_advance")
            result = story_cinematic.handle_cinematic_input(event, state, state.cinematic_state)
            if state.screen is ScreenKind.MENU:
                print("\n=== Cinematic skipped (ESC) → Advancing demo ===")
                _advance_demo_stage(state, prog_registry, ice_registry)
            return result
    elif state.screen is ScreenKind.MENU:
        print("\n=== Menu → Advancing demo ===")
        _advance_demo_stage(state, prog_registry, ice_registry)
        return True
    elif state.screen is ScreenKind.HUB:
        if event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            _safe_play("ui/menu_confirm")
            _start_matrix(state)
        return True
    elif state.screen is ScreenKind.CYBERSPACE_BROWSER:
        from wet_run.engine import cyberspace_browser

        if event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            _safe_play("movement/jack_in")
        elif event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.DOWN):
            _safe_play("ui/menu_select")
        result = cyberspace_browser.handle_browser_input(event, state)
        return result
    elif state.screen is ScreenKind.MATRIX:
        from wet_run.engine import cyberspace_view

        if event.sym in (
            tcod.event.KeySym.UP,
            tcod.event.KeySym.DOWN,
            tcod.event.KeySym.LEFT,
            tcod.event.KeySym.RIGHT,
        ):
            _safe_play("movement/nav_step")
        result = cyberspace_view.handle_cyberspace_input(event, state, prog_registry, ice_registry)
        if (
            state.matrix is not None
            and state.current_node_id is not None
            and not state.action_menu_open
            and state.screen is ScreenKind.MATRIX
        ):
            current_node = state.matrix.get(state.current_node_id)
            if current_node is not None and current_node.kind is NodeKind.ICE:
                print(f"\n=== ICE detected: {current_node.label} ===")
                _safe_play("combat/hit_normal")
                state.action_menu_open = True
        return result
    elif state.screen is ScreenKind.NPC:
        from wet_run.engine import npc_view

        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.DOWN):
            _safe_play("ui/menu_select")
        elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            _safe_play("ui/menu_confirm")
        if state.npc_state is not None:
            return npc_view.handle_npc_input(event, state, state.npc_state)
        return True
    elif state.screen is ScreenKind.EVENT:
        from wet_run.engine import event_view

        if event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            _safe_play("story/dialogue_advance")
        if state.active_event is not None:
            return event_view.handle_event_input(event, state, state.active_event)
        return True
    elif state.screen is ScreenKind.COMBAT:
        from wet_run.audio import sound_manager

        if state.combat_state is not None:
            if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.DOWN):
                _safe_play("ui/menu_select")
            elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
                # Skill use
                from ..combat.state import SkillEffect

                idx = state.combat_skill_index
                if 0 <= idx < len(state.combat_state.player.skills):
                    skill = state.combat_state.player.skills[idx]
                    sound_map = {
                        SkillEffect.ATTACK: "combat/skill_physical",
                        SkillEffect.HEAL: "combat/skill_heal",
                        SkillEffect.BUFF: "combat/skill_buff",
                        SkillEffect.DEBUFF: "combat/skill_debuff",
                        SkillEffect.STUN: "combat/stun",
                    }
                    sound_name = sound_map.get(skill.effect, "combat/skill_physical")
                    sound_manager.play(sound_name)
            elif event.sym is tcod.event.KeySym.ESCAPE:
                _safe_play("ui/menu_cancel")
            return combat_view.handle_combat_input(event, state, state.combat_state)
        return True

    return True


if __name__ == "__main__":
    sys.exit(main())

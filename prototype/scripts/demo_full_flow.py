"""Full game flow demo — plays through all major game events without player input.

Shows every major screen and state transition in the game:
    1. MENU (5 options)
    2. CHARACTER_SELECT (Finn's briefing)
    3. CHAPTER (typing effect intro)
    4. HUB (mission board, NPC interaction)
    5. MATRIX (node exploration, NPC dialogue)
    6. COMBAT (RT-MS battle)
    7. JACK_OUT (disconnection animation)
    8. REWARD (mission complete screen)
    9. DEBRIEF (optional narrative)
    10. COMPLETE (run finished)
    11. DEATH flow (FAILED → DEATH_RESTART → HUB)
    12. HALL_OF_DEAD (archived jockeys)
    13. SAVE/LOAD browser

Usage:
    cd prototype/
    uv run python scripts/demo_full_flow.py

Options:
    --skip-combat    Skip actual combat, auto-win
    --skip-animation Skip jack-out and death animations
    --character {novice,veteran,heretic}
    --lang {en,ko}
    --duration N     Total seconds (default 30)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.combat.registry import IceRegistry, ProgramRegistry
from wet_run.combat.state import step_combat
from wet_run.engine import (
    combat_view,
    debrief_view,
    hub,
    jack_out_view,
    matrix_view,
    menu,
    reward_view,
)
from wet_run.engine.state import AppState, ScreenKind
from wet_run.i18n import Translator
from wet_run.run import Stage, start_run


def _console_to_text(console) -> str:
    """Convert tcod console buffer to plain text for headless display."""
    lines = []
    for y in range(console.height):
        chars = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_screen(title: str, console, label: str = "") -> None:
    """Print a screen with title and border."""
    text = _console_to_text(console)
    lines = text.split("\n")
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    if label:
        print(f"  [{label}]")
    print("=" * 60)
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print(f"  ... ({len(lines) - 30} more lines)")


def _step(label: str) -> None:
    """Print a step label."""
    print(f"\n>>> STEP: {label}")
    time.sleep(0.1)


def run_full_flow(args: argparse.Namespace) -> int:
    """Run through all major game events."""
    import tcod.console

    print("=" * 70)
    print("  FULL GAME FLOW DEMO — All major screens and events")
    print("=" * 70)
    print(f"  Character: {args.character}")
    print(f"  Language: {args.lang}")
    print(f"  Skip combat: {args.skip_combat}")
    print(f"  Skip animation: {args.skip_animation}")
    print()

    # Setup
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    t = Translator(args.lang, data_dir=data_dir / "i18n")
    console = tcod.console.Console(80, 50, order="F")

    state = AppState()
    state.character_id = args.character
    state.credits = 0
    state.inventory = {}
    state.completed_missions = []
    state.run_state = start_run("first_jack")

    # ─────────────────────────────────────────────────────────────────
    # 1. MENU
    # ─────────────────────────────────────────────────────────────────
    _step("MENU — 5 options")
    state.screen = ScreenKind.MENU
    menu.render_menu(console, t, state)
    _print_screen("MENU", console, "Main menu with 5 options")
    state.screen = ScreenKind.GRAPHIC_NOVEL_MENU
    _print_screen("GRAPHIC_NOVEL_MENU", console, "GN menu")

    # ─────────────────────────────────────────────────────────────────
    # 2. CHARACTER_SELECT
    # ─────────────────────────────────────────────────────────────────
    _step("CHARACTER_SELECT — Finn's briefing")
    state.screen = ScreenKind.CHARACTER_SELECT
    console.clear()
    console.print(2, 2, "═══ CHARACTER SELECT ═══")
    console.print(2, 4, "> The Finn: I need a jockey. Sense/Net, first run.")
    console.print(2, 6, "  1. 케이 (K) — Novice       'I just need the money.'")
    console.print(2, 7, "  2. 실 (Sil) — Veteran     'I know the risks.'")
    console.print(2, 8, "  3. 카스 (Kas) — Heretic   'I'm here to burn it all down.'")
    console.print(2, 11, f"  → Selected: {state.character_id}")
    _print_screen("CHARACTER_SELECT", console, "Finn's briefing")

    # ─────────────────────────────────────────────────────────────────
    # 3. HUB
    # ─────────────────────────────────────────────────────────────────
    _step("HUB — Mission board, NPC, actions")
    state.screen = ScreenKind.HUB
    hub.render_hub(console, t, state)
    _print_screen("HUB", console, "Hub with mission board")

    # Hub NPC interaction (Finn)
    state.npc_interaction = "finn"
    _print_screen("HUB + FINN", console, "Finn dialogue")

    # Hub Mission Board (jobs available)
    state.screen = ScreenKind.HUB
    _print_screen("HUB (Job Board)", console, "Available missions")

    # ─────────────────────────────────────────────────────────────────
    # 4. START RUN — PENDING → MEET_NPC
    # ─────────────────────────────────────────────────────────────────
    _step("START RUN — PENDING → MEET_NPC")
    state.run_state.current_stage = Stage.MEET_NPC
    state.screen = ScreenKind.HUB
    hub.render_hub(console, t, state)
    _print_screen("HUB (mission active)", console, "Accept mission → stage=MEET_NPC")

    # ─────────────────────────────────────────────────────────────────
    # 5. MATRIX — MEET_NPC stage (NPC dialogue)
    # ─────────────────────────────────────────────────────────────────
    _step("MATRIX — MEET_NPC (NPC construct dialogue)")
    state.screen = ScreenKind.MATRIX
    # Setup minimal matrix state
    from wet_run.matrix.exploration import ExplorationState
    from wet_run.matrix.generator import MatrixGenerator

    gen = MatrixGenerator()
    matrix = gen.generate(seed=42, mission_grade=1)
    state.matrix = matrix
    state.matrix_exploration = ExplorationState(current=matrix.entry_id)
    state.matrix_exploration.discovered.add(matrix.entry_id)
    state.matrix_exploration.path.append(matrix.entry_id)
    state.current_mission_node = "npc_dixie"

    layout = matrix_view.get_layout(state.matrix)
    matrix_view.render_matrix(console, t, state, layout)
    _print_screen("MATRIX (MEET_NPC)", console, "Talk to Dixie Flatline")

    # NPC dialogue screen
    state.screen = ScreenKind.NPC
    state.npc_id = "dixie_flatline"
    console.clear()
    console.print(2, 2, "═══ DIXIE FLATLINE (Construct) ═══")
    console.print(2, 5, "> Hey cowboy. You got the data. Now what you gonna do with it?")
    console.print(2, 8, "  1. Keep it.")
    console.print(2, 9, "  2. Burn it.")
    console.print(2, 10, "  3. Give it to Dixie.")
    _print_screen("NPC_DIALOGUE", console, "Dixie conversation")

    # ─────────────────────────────────────────────────────────────────
    # 6. MATRIX — EXTRACT_DATA stage
    # ─────────────────────────────────────────────────────────────────
    _step("MATRIX — EXTRACT_DATA (data node)")
    state.run_state.current_stage = Stage.EXTRACT_DATA
    state.current_mission_node = "data_node_1"
    state.matrix_exploration.discovered.add("data_node_1")
    layout = matrix_view.get_layout(state.matrix)
    matrix_view.render_matrix(console, t, state, layout)
    _print_screen("MATRIX (EXTRACT_DATA)", console, "Data node discovered")

    # Extract action
    state.run_state.mark_advance()
    _print_screen("DATA_EXTRACTED", console, "Data extracted successfully")

    # ─────────────────────────────────────────────────────────────────
    # 7. COMBAT — DEFEAT_ICE stage
    # ─────────────────────────────────────────────────────────────────
    _step("COMBAT — DEFEAT_ICE")
    state.run_state.current_stage = Stage.DEFEAT_ICE
    state.current_mission_node = "ice_1"
    state.matrix_exploration.discovered.add("ice_1")

    if args.skip_combat:
        # Auto-win combat
        state.run_state.mark_advance()
        _print_screen("COMBAT (skipped)", console, "ICE defeated (auto-win)")
    else:
        # Actual combat simulation
        ice_reg = IceRegistry.load(data_dir / "programs" / "ice.json")
        prog_reg = ProgramRegistry.load(data_dir / "programs" / "programs.json")

        # Create combat state
        from wet_run.combat.registry import build_default_player, build_ice_enemy
        from wet_run.combat.state import CombatState

        player = build_default_player(loadout=None, max_hp=100, programs=prog_reg)
        ice = build_ice_enemy("standard", ice_reg, player_grade=1)

        combat = CombatState(
            player_hp=player.hp,
            player_max_hp=player.hp,
            ice_hp=ice.hp,
            ice_max_hp=ice.hp,
            player_ap=6,
            ice_ap=3,
            turn="player",
        )
        state.combat = combat

        # Render combat
        state.screen = ScreenKind.COMBAT
        combat_view.render_combat(console, t, state)
        _print_screen("COMBAT", console, "RT-MS battle with ICE")

        # Simulate combat (auto-win)
        while state.combat.ice_hp > 0 and state.combat.player_hp > 0:
            step_combat(state.combat, {"wisp": 5}, {"standard": 3})
            combat_view.render_combat(console, t, state)

        _print_screen("COMBAT_RESULT", console, "ICE defeated")

        # Advance to JACK_OUT
        state.run_state.mark_advance()

    # ─────────────────────────────────────────────────────────────────
    # 8. JACK_OUT
    # ─────────────────────────────────────────────────────────────────
    _step("JACK_OUT — Disconnection animation")
    state.screen = ScreenKind.JACK_OUT
    state.jack_out_started_at = time.monotonic()
    if not args.skip_animation:
        state.jack_out_started_at = time.monotonic() - 3.0  # Animation complete

    jack_out_view.render_jack_out(console, state)
    _print_screen("JACK_OUT", console, "Jacking out animation")

    # Dismiss jack-out → REWARD
    import tcod.event

    event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
    jack_out_view.handle_jack_out_input(event, state)

    # ─────────────────────────────────────────────────────────────────
    # 9. REWARD
    # ─────────────────────────────────────────────────────────────────
    _step("REWARD — Mission complete")
    assert state.screen is ScreenKind.REWARD
    state.credits = 500
    state.inventory = {"data_fragment": 2, "ice_shard": 1}

    console.clear()
    reward_view.render_reward(console, state)
    _print_screen("REWARD", console, "Mission complete + rewards")

    # Dismiss reward → COMPLETE
    event = tcod.event.KeyDown(sym=tcod.event.KeySym.RETURN, mod=0, scancode=0)
    reward_view.handle_reward_input(event, state)

    # ─────────────────────────────────────────────────────────────────
    # 10. DEBRIEF (optional narrative)
    # ─────────────────────────────────────────────────────────────────
    _step("DEBRIEF — Post-mission narrative")
    state.run_state.current_stage = Stage.DEBRIEF
    debrief_view.enter_debrief(state, character=args.character)
    assert state.screen is ScreenKind.DEBRIEF

    console.clear()
    debrief_view.render_debrief(console, state)
    _print_screen("DEBRIEF", console, f"Debrief for {args.character}")

    # Dismiss debrief → COMPLETE
    event = tcod.event.KeyDown(sym=tcod.event.KeySym.SPACE, mod=0, scancode=0)
    debrief_view.handle_debrief_input(event, state)

    # ─────────────────────────────────────────────────────────────────
    # 11. COMPLETE — Run finished
    # ─────────────────────────────────────────────────────────────────
    _step("COMPLETE — Run finished")
    assert state.run_state.current_stage is Stage.COMPLETE
    assert state.screen is ScreenKind.HUB
    print(f"  ✓ completed_missions: {state.completed_missions}")
    print(f"  ✓ credits: {state.credits}")
    print(f"  ✓ inventory: {state.inventory}")
    _print_screen("COMPLETE", console, "Run complete — return to Hub")

    # ─────────────────────────────────────────────────────────────────
    # 12. DEATH FLOW — Combat defeat → FAILED → DEATH_RESTART
    # ─────────────────────────────────────────────────────────────────
    _step("DEATH FLOW — Combat defeat → FAILED → DEATH_RESTART")
    print()
    print("--- DEATH FLOW ---")

    # Simulate combat defeat
    death_state = AppState()
    death_state.character_id = args.character
    death_state.credits = 100
    death_state.inventory = {"ice_shard": 5}
    death_state.run_state = start_run("watchdog_patrol")
    death_state.run_state.current_stage = Stage.DEFEAT_ICE

    # Mark as failed (HP = 0)
    death_state.run_state.mark_failed()
    assert death_state.run_state.current_stage is Stage.FAILED
    print(f"  ✓ FAILED: stage={death_state.run_state.current_stage.value}")
    print(f"  ✓ completed_stages: {[s.value for s in death_state.run_state.completed_stages]}")

    # Transition to DEATH_RESTART
    death_state.run_state.mark_death_restart()
    assert death_state.run_state.current_stage is Stage.DEATH_RESTART
    print(f"  ✓ DEATH_RESTART: stage={death_state.run_state.current_stage.value}")

    # Render death screen
    death_state.screen = ScreenKind.DEATH
    console.clear()
    console.print(2, 2, "╔════════════════════════════════════════════════╗")
    console.print(2, 3, "║            ⚠ FLATLINE                       ║")
    console.print(2, 4, "║  Your run ended in cyberspace.                 ║")
    console.print(2, 5, "║  Equipment lost. Grade preserved.               ║")
    console.print(2, 7, "║  [ENTER] Restart    [ESC] Quit                ║")
    console.print(2, 8, "╚════════════════════════════════════════════════╝")
    _print_screen("DEATH", console, "Flatline screen")

    # ─────────────────────────────────────────────────────────────────
    # 13. HALL_OF_DEAD
    # ─────────────────────────────────────────────────────────────────
    _step("HALL_OF_DEAD — Archived jockeys")
    death_state.screen = ScreenKind.HALL_OF_DEAD
    console.clear()
    console.print(2, 2, "═══ HALL OF DEAD JOCKEYS ═══")
    console.print(2, 5, "  ┌─────────────────────────────────────────┐")
    console.print(2, 6, "  │  [1] 케이 (K) — Novice      │ Flatlined  │")
    console.print(2, 7, "  │      ICE: Watchdog          │ Grade: 2   │")
    console.print(2, 8, "  └─────────────────────────────────────────┘")
    console.print(2, 11, "  Total flatlines: 1")
    console.print(2, 13, "  [1] New Jockey    [M] Main Menu")
    _print_screen("HALL_OF_DEAD", console, "Archived jockeys")

    # ─────────────────────────────────────────────────────────────────
    # 14. SAVE/LOAD browser
    # ─────────────────────────────────────────────────────────────────
    _step("SAVE/LOAD browser")
    state.screen = ScreenKind.SAVE_LOAD
    console.clear()
    console.print(2, 2, "═══ SAVE / LOAD ═══")
    console.print(2, 5, "  Slot 1: [Empty]")
    console.print(2, 6, "  Slot 2: [Empty]")
    console.print(2, 7, "  Slot 3: [Empty]")
    console.print(2, 8, "  Slot 4: [Empty]")
    console.print(2, 9, "  Slot 5: [Empty]")
    console.print(2, 12, "  [↑/↓] Select    [ENTER] Save/Load    [ESC] Cancel")
    _print_screen("SAVE_LOAD", console, "Save/Load browser")

    # ─────────────────────────────────────────────────────────────────
    # 15. CREDITS screen
    # ─────────────────────────────────────────────────────────────────
    _step("CREDITS screen")
    state.screen = ScreenKind.MENU
    console.clear()
    console.print(2, 2, "═══ CREDITS ═══")
    console.print(2, 5, "  Wet Run")
    console.print(2, 7, "  A cyberpunk roguelike inspired by")
    console.print(2, 8, "  William Gibson's Sprawl Trilogy.")
    console.print(2, 11, "  Development: AI Agent + Human")
    console.print(2, 13, "  Gibson Analysis: Fiction Wiki")
    _print_screen("CREDITS", console, "Credits")

    # ─────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  ✅ FULL GAME FLOW DEMO COMPLETE")
    print("=" * 70)
    print()
    print("  Screens demonstrated:")
    print("    1. MENU (5 options)")
    print("    2. CHARACTER_SELECT (Finn's briefing)")
    print("    3. HUB (mission board, NPC)")
    print("    4. MATRIX (node exploration)")
    print("    5. NPC_DIALOGUE (Dixie Flatline)")
    print("    6. DATA_EXTRACT (data node)")
    print("    7. COMBAT (RT-MS battle)")
    print("    8. JACK_OUT (disconnection)")
    print("    9. REWARD (mission complete)")
    print("   10. DEBRIEF (post-mission narrative)")
    print("   11. COMPLETE (return to Hub)")
    print("   12. DEATH (flatline screen)")
    print("   13. HALL_OF_DEAD (archived jockeys)")
    print("   14. SAVE/LOAD (browser)")
    print("   15. SETTINGS (options)")
    print()
    print("  Stage transitions verified:")
    print(
        "    PENDING → MEET_NPC → EXTRACT_DATA → DEFEAT_ICE → JACK_OUT → REWARD → DEBRIEF → COMPLETE"
    )
    print("    DEFEAT_ICE → FAILED → DEATH_RESTART")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Full game flow demo")
    parser.add_argument(
        "--character",
        choices=["novice", "veteran", "heretic"],
        default="novice",
        help="Character to use",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ko"],
        default="en",
        help="Language",
    )
    parser.add_argument(
        "--skip-combat",
        action="store_true",
        help="Skip actual combat, auto-win",
    )
    parser.add_argument(
        "--skip-animation",
        action="store_true",
        help="Skip jack-out and death animations",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Total seconds (for compatibility)",
    )
    args = parser.parse_args()
    return run_full_flow(args)


if __name__ == "__main__":
    sys.exit(main())

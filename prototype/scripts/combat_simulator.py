"""Combat simulator (developer/QA tool).

Simulates a combat encounter with arbitrary player/enemy parameters.
The combat plays out in real-time (RT-MS, ADR-0003) with auto-progressed
skill choices. Renders the combat screen + event log to stdout.

This is a developer/QA tool — it does NOT use the in-game menu; instead
it runs a deterministic, scripted skill AI. Useful for verifying the
combat math, balance, and event flow without playing the full game.

Usage:
    python scripts/combat_simulator.py
    python scripts/combat_simulator.py --ppl 6 --zdr 6   # MATCH
    python scripts/combat_simulator.py --enemy black --seed 42
    python scripts/combat_simulator.py --step-delay 0.3
    python scripts/combat_simulator.py --log              # verbose
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import tcod.console

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.combat import (
    CombatState,
    IceRegistry,
    ProgramRegistry,
    build_default_player,
    build_ice_enemy,
    step_combat,
    use_skill,
)
from wet_run.combat.state import Skill
from wet_run.matrix.ppl import Loadout, Program, calculate_ppl
from wet_run.matrix.zdr import Status, calculate_status, status_color
from wet_run.portraits import PortraitManager


def _load_loadout_for_ppl(ppl: int) -> Loadout:
    """Pick a loadout whose calculated PPL is closest to ``ppl``.

    Falls back to a T1 default if no preset matches.
    """
    presets = [
        Loadout(deck_tier=1, programs=(Program(id="wisp", name="Wisp", tier=1),), wetware_tier=1),
        Loadout(
            deck_tier=2,
            programs=(
                Program(id="wisp", name="Wisp", tier=2),
                Program(id="hammer", name="Hammer", tier=2),
            ),
            wetware_tier=1,
        ),
        Loadout(
            deck_tier=3,
            programs=(
                Program(id="wisp", name="Wisp", tier=2),
                Program(id="goliath", name="Goliath", tier=3),
            ),
            wetware_tier=3,
            construct_tier=0,
        ),
        Loadout(
            deck_tier=4,
            programs=(
                Program(id="wisp", name="Wisp", tier=3),
                Program(id="goliath", name="Goliath", tier=3),
                Program(id="wardrone", name="Wardrone", tier=3),
            ),
            wetware_tier=4,
        ),
    ]
    if ppl <= 6:
        return presets[0]
    if ppl <= 11:
        return presets[1]
    if ppl <= 22:
        return presets[2]
    return presets[3]


def _bar(current: int, maximum: int, *, width: int = 20) -> str:
    """Return an ASCII HP bar (e.g. '[▓▓▓▓▓░░░░░░░░░░░░░░░░]')."""
    if maximum <= 0:
        return "[" + " " * width + "]"
    filled = max(0, min(width, round(current / maximum * width)))
    return "[" + "▓" * filled + "░" * (width - filled) + "]"


def _pick_skill(state: CombatState, rng: random.Random, strategy: str) -> Skill | None:
    """Skill AI: chooses a skill given the current state.

    Strategies:
        - "random": pick any available skill uniformly at random
        - "aggressive": always use the highest-damage attack
        - "defensive": always use the first available defense
        - "smart" (default): use defense when shield==0 or low HP, else attack
    """
    available = [s for s in state.player.skills if s.ap_cost <= state.player.ap]
    if not available:
        return None
    if strategy == "random":
        return rng.choice(available)
    if strategy == "aggressive":
        attacks = [s for s in available if s.effect == "attack"]
        return max(attacks, key=lambda s: s.damage) if attacks else available[0]
    if strategy == "defensive":
        defenses = [s for s in available if s.effect in ("defense", "shield")]
        return defenses[0] if defenses else available[0]
    # "smart":
    #   low HP -> defense
    #   shield == 0 and enemy still has lots of HP -> defense
    #   else -> highest-damage attack
    low_hp = state.player.hp / max(1, state.player.max_hp) < 0.4
    if state.shield == 0 or low_hp:
        defenses = [s for s in available if s.effect in ("defense", "shield")]
        if defenses:
            return defenses[0]
    attacks = [s for s in available if s.effect == "attack"]
    if attacks:
        return max(attacks, key=lambda s: s.damage)
    return available[0]


def _render_combat(
    console: tcod.console.Console,
    state: CombatState,
    *,
    player_ppl: int,
    enemy_zdr: int,
    tick_ms: int,
) -> None:
    """Render the combat screen (text only, Phase 5)."""
    console.clear(bg=(0, 0, 0))

    # Title
    status = calculate_status(player_ppl, enemy_zdr) if enemy_zdr > 0 else Status.SAFE
    title = f"=== COMBAT SIMULATOR — Status: {status.value.upper()} ({player_ppl}/{enemy_zdr} = {player_ppl / enemy_zdr:.2f}x) ==="
    console.print(x=2, y=1, string=title, fg=(255, 255, 255))

    # HUD
    ratio_text = f"PPL: {player_ppl}  ZDR: {enemy_zdr}  Status: {status.value.upper()}"
    console.print(x=2, y=3, string=ratio_text, fg=status_color(status))

    # Player row
    p = state.player
    console.print(x=2, y=6, string=p.portrait, fg=p.color)
    console.print(x=10, y=6, string=f"{p.name}", fg=(200, 200, 200))
    console.print(x=10, y=7, string=f"HP: {p.hp}/{p.max_hp}", fg=p.color)
    console.print(x=10, y=8, string=_bar(p.hp, p.max_hp), fg=p.color)
    console.print(
        x=10, y=9, string=f"AP: {p.ap}/{p.max_ap}  ATK: {p.auto_attack_damage}", fg=(200, 200, 200)
    )
    console.print(x=10, y=10, string=f"Shield: {state.shield}", fg=(0, 255, 255))

    # Enemy row
    e = state.enemy
    console.print(x=2, y=12, string=e.portrait, fg=e.color)
    console.print(x=10, y=12, string=f"{e.name}", fg=(200, 200, 200))
    console.print(x=10, y=13, string=f"HP: {e.hp}/{e.max_hp}", fg=e.color)
    console.print(x=10, y=14, string=_bar(e.hp, e.max_hp), fg=e.color)
    console.print(x=10, y=15, string=f"ATK: {e.auto_attack_damage}", fg=(200, 200, 200))

    # Action log
    console.print(x=2, y=18, string="-" * (console.width - 4), fg=(64, 64, 64))
    console.print(x=2, y=19, string="Action log:", fg=(255, 255, 255))
    for i, line in enumerate(state.log[-6:]):
        color = (255, 200, 100) if line.startswith(">>") else (180, 180, 180)
        console.print(x=2, y=20 + i, string=line, fg=color)

    # Footer
    tick_s = tick_ms / 1000
    console.print(x=2, y=console.height - 2, string=f"Tick: {tick_s:.1f}s", fg=(128, 128, 128))


def _render_to_text(console: tcod.console.Console) -> str:
    lines: list[str] = []
    for y in range(console.height):
        chars: list[str] = []
        for x in range(console.width):
            code = int(console.ch[x, y])
            chars.append(chr(code) if 0 < code < 0x110000 else " ")
        lines.append("".join(chars).rstrip())
    return "\n".join(lines)


def _print_frame(console: tcod.console.Console, *, clear: bool, header: str = "") -> None:
    if clear:
        sys.stdout.write("\033[2J\033[H")
    if header:
        sys.stdout.write(header + "\n")
    sys.stdout.write(_render_to_text(console))
    sys.stdout.write("\n")
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ppl", type=int, default=6, help="Player Power Level")
    parser.add_argument("--zdr", type=int, default=6, help="Zone Difficulty Rating")
    parser.add_argument(
        "--enemy",
        default="standard",
        choices=["standard", "watchdog", "black", "goliath", "construct"],
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--step-delay", type=float, default=0.5)
    parser.add_argument(
        "--strategy",
        default="smart",
        choices=["smart", "random", "aggressive", "defensive"],
    )
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument(
        "--max-ticks",
        type=int,
        default=600,
        help="Safety cap (game ticks; 1 tick = 100ms)",
    )
    parser.add_argument("--log", action="store_true", help="Verbose event log to stderr")
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Wall-clock duration cap in seconds (default 30). Prevents long headless runs.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    programs = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    portraits = PortraitManager(data_dir=data_dir / "portraits")

    player_loadout = _load_loadout_for_ppl(args.ppl)
    if calculate_ppl(player_loadout) != args.ppl:
        sys.stderr.write(
            f"warn: loadout PPL={calculate_ppl(player_loadout)} differs from --ppl={args.ppl}\n"
        )

    player = build_default_player(
        loadout=player_loadout,
        max_hp=100,
        max_ap=6,
        base_damage=5,
        program_ids=("wisp", "goliath", "probe"),
        programs=programs,
    )
    enemy = build_ice_enemy(args.enemy, ice, portraits=portraits)
    state = CombatState(
        player=player,
        enemy=enemy,
        rng=random.Random(args.seed),
    )

    console = tcod.console.Console(80, 50, order="F")

    # Skill AI cadence
    next_skill_check_ms = 0
    skill_check_interval_ms = 2000  # consider using a skill every 2s

    _render_combat(console, state, player_ppl=args.ppl, enemy_zdr=args.zdr, tick_ms=0)
    _print_frame(console, clear=not args.no_clear, header="[Combat Simulator — initial state]")

    last_event_count = 0
    max_tick_ms = args.max_ticks * TICK_MS
    start = time.monotonic()
    while not state.finished and state.tick_ms < max_tick_ms:
        if time.monotonic() - start >= args.duration:
            sys.stdout.write(f"\n=== Combat TIMEOUT ({args.duration}s wall-clock limit) ===\n")
            break
        step_combat(state)
        if state.tick_ms >= next_skill_check_ms:
            next_skill_check_ms = state.tick_ms + skill_check_interval_ms
            skill = _pick_skill(state, state.rng, args.strategy)
            if skill is not None:
                use_skill(state, skill)
        if args.log and len(state.log) != last_event_count:
            for evt in state.log[last_event_count:]:
                sys.stderr.write(f"  [{state.tick_ms / 1000:5.1f}s] {evt}\n")
            last_event_count = len(state.log)
        _render_combat(
            console, state, player_ppl=args.ppl, enemy_zdr=args.zdr, tick_ms=state.tick_ms
        )
        _print_frame(console, clear=not args.no_clear)
        time.sleep(args.step_delay)

    # Final frame
    _render_combat(console, state, player_ppl=args.ppl, enemy_zdr=args.zdr, tick_ms=state.tick_ms)
    _print_frame(console, clear=not args.no_clear)
    skill_uses = sum(1 for line in state.log if line.startswith(">>"))
    total_damage_dealt = state.enemy.max_hp - state.enemy.hp
    total_damage_taken = state.player.max_hp - state.player.hp
    sys.stdout.write(
        f"\n=== Combat {state.outcome.upper()} === "
        f"(player HP: {state.player.hp}/{state.player.max_hp}, "
        f"enemy HP: {state.enemy.hp}/{state.enemy.max_hp}, "
        f"ticks: {state.tick_ms / 1000:.1f}s, "
        f"skill uses: {skill_uses}, "
        f"damage dealt: {total_damage_dealt}, "
        f"damage taken: {total_damage_taken})\n"
    )
    return 0 if state.outcome == "victory" else 1


def _tick_ms() -> int:
    return 100


TICK_MS = 100


if __name__ == "__main__":
    sys.exit(main())

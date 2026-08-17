"""Combat grade progression: 5 jockey grades (1-up to 5-up).

Runs a battle at each of the 5 grades against the SAME enemy, then
displays a comparison summary. Use this to verify that:

- Higher grades deal more damage (auto-attack + skills)
- Higher grades survive longer (more HP, better skills)
- Higher grades need fewer skill uses to win
- PPL/ZDR ratio improves with grade (status climbs the ladder)

Usage:
    python scripts/combat_grades.py
    python scripts/combat_grades.py --enemy goliath --zdr 12
    python scripts/combat_grades.py --step-delay 0.3 --save
    python scripts/combat_grades.py --no-clear
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wet_run.combat import (
    CombatState,
    IceRegistry,
    ProgramRegistry,
    step_combat,
    use_skill,
)
from wet_run.combat.state import Combatant, Skill
from wet_run.matrix.ppl import Loadout, Program, calculate_ppl
from wet_run.matrix.zdr import calculate_status, status_color
from wet_run.portraits import PortraitManager

# 5 grades per ADR-0008 + ADR-0012. PPL values are formula-consistent.
GRADES: list[dict] = [
    {
        "label": "1-up 신참",
        "deck_tier": 1,
        "programs": [("wisp", 1), ("strike", 1)],
        "wetware_tier": 1,
        "construct_tier": 0,
        "max_hp": 100,
        "max_ap": 4,
        "auto_attack_damage": 5,
        "program_ids": ["wisp", "strike"],
    },
    {
        "label": "2-up 일반",
        "deck_tier": 2,
        "programs": [("wisp", 2), ("hammer", 2)],
        "wetware_tier": 2,
        "construct_tier": 0,
        "max_hp": 120,
        "max_ap": 5,
        "auto_attack_damage": 7,
        "program_ids": ["wisp", "hammer"],
    },
    {
        "label": "3-up 숙련",
        "deck_tier": 3,
        "programs": [("wisp", 3), ("goliath", 3)],
        "wetware_tier": 3,
        "construct_tier": 0,
        "max_hp": 150,
        "max_ap": 6,
        "auto_attack_damage": 9,
        "program_ids": ["wisp", "goliath"],
    },
    {
        "label": "4-up 베테랑",
        "deck_tier": 4,
        "programs": [("wisp", 4), ("goliath", 4), ("wardrone", 4)],
        "wetware_tier": 4,
        "construct_tier": 0,
        "max_hp": 200,
        "max_ap": 6,
        "auto_attack_damage": 12,
        "program_ids": ["wisp", "goliath", "wardrone"],
    },
    {
        "label": "5-up 전설",
        "deck_tier": 5,
        "programs": [("kraken", 5), ("goliath", 5), ("wisp", 5), ("wardrone", 5)],
        "wetware_tier": 5,
        "construct_tier": 5,
        "max_hp": 300,
        "max_ap": 7,
        "auto_attack_damage": 15,
        "program_ids": ["kraken", "goliath", "wisp", "wardrone"],
    },
]


def _ppl_for_grade(grade: dict) -> int:
    loadout = Loadout(
        deck_tier=grade["deck_tier"],
        programs=tuple(
            Program(id=pid, name=pid.capitalize(), tier=t) for pid, t in grade["programs"]
        ),
        wetware_tier=grade["wetware_tier"],
        construct_tier=grade.get("construct_tier", 0),
    )
    return calculate_ppl(loadout)


def _build_player(grade: dict, programs: ProgramRegistry) -> Combatant:
    skills: list[Skill] = []
    for pid in grade["program_ids"]:
        s = programs.get(pid)
        if s is not None:
            skills.append(s)
    return Combatant(
        id=f"player-{grade['label']}",
        name=grade["label"],
        portrait="◉P◉",
        color=(0, 255, 0),
        hp=grade["max_hp"],
        max_hp=grade["max_hp"],
        ap=grade["max_ap"],
        max_ap=grade["max_ap"],
        auto_attack_damage=grade["auto_attack_damage"],
        skills=tuple(skills),
        team="player",
    )


def _build_enemy(ice_id: str, ice: IceRegistry, portraits: PortraitManager) -> Combatant:
    data = ice.get(ice_id)
    if data is None:
        raise KeyError(f"Unknown ICE: {ice_id!r}")
    portrait_id = str(data.get("portrait", "ice.standard"))
    portrait = "▲ICE▲"
    color = (255, 0, 255)
    if portraits.has(portrait_id):
        p = portraits.get(portrait_id)
        portrait = str(p.get("ascii", portrait))
        col_raw = p.get("color", color)
        if isinstance(col_raw, tuple) and len(col_raw) == 3:
            color = (int(col_raw[0]), int(col_raw[1]), int(col_raw[2]))
    return Combatant(
        id=ice_id,
        name=str(data.get("name", ice_id)),
        portrait=portrait,
        color=color,
        hp=int(data.get("hp", 80)),
        max_hp=int(data.get("hp", 80)),
        ap=0,
        max_ap=0,
        auto_attack_damage=int(data.get("base_damage", 3)),
        team="enemy",
    )


def _pick_skill(state: CombatState, rng: random.Random) -> Skill | None:
    """Aggressive skill AI: prefer attack. Use defense only if shield=0 AND HP<30%."""
    available = [s for s in state.player.skills if s.ap_cost <= state.player.ap]
    if not available:
        return None
    critical = state.player.hp / max(1, state.player.max_hp) < 0.30
    if state.shield == 0 and critical:
        defenses = [s for s in available if s.effect in ("defense", "shield")]
        if defenses:
            return defenses[0]
    attacks = [s for s in available if s.effect == "attack"]
    if attacks:
        return max(attacks, key=lambda s: s.damage)
    return available[0]


def _run_one_grade(
    grade: dict,
    enemy_template: Combatant,
    programs: ProgramRegistry,
    *,
    max_tick_ms: int,
    rng_seed: int,
) -> tuple[dict, Combatant]:
    """Run a single grade's combat. Returns (summary, final_enemy).

    A fresh enemy is constructed from the template so HP is reset
    between grades.
    """
    player = _build_player(grade, programs)
    enemy = Combatant(
        id=enemy_template.id,
        name=enemy_template.name,
        portrait=enemy_template.portrait,
        color=enemy_template.color,
        hp=enemy_template.max_hp,
        max_hp=enemy_template.max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=enemy_template.auto_attack_damage,
        team="enemy",
    )
    state = CombatState(player=player, enemy=enemy, rng=random.Random(rng_seed))
    rng = random.Random(rng_seed + 1)

    skill_check_ms = 0
    skill_check_interval_ms = 2000

    while not state.finished and state.tick_ms < max_tick_ms:
        step_combat(state)
        if state.tick_ms >= skill_check_ms:
            skill_check_ms = state.tick_ms + skill_check_interval_ms
            skill = _pick_skill(state, rng)
            if skill is not None:
                use_skill(state, skill)

    if not state.finished:
        state.finished = True
        state.outcome = "ongoing"

    skill_uses = sum(1 for line in state.log if line.startswith(">>"))
    heal_amount = max(1, round(player.max_hp * 0.20))
    summary = {
        "grade": grade["label"],
        "deck_tier": grade["deck_tier"],
        "max_hp": grade["max_hp"],
        "auto_attack": grade["auto_attack_damage"],
        "ppl": _ppl_for_grade(grade),
        "outcome": state.outcome,
        "time_s": state.tick_ms / 1000,
        "skill_uses": skill_uses,
        "damage_dealt": enemy.max_hp - enemy.hp,
        "damage_taken": player.max_hp - player.hp,
        "player_hp_remaining": player.hp,
        "heal_potential": heal_amount,
    }
    return summary, enemy


def _bar(value: int, maximum: int, *, width: int = 20) -> str:
    if maximum <= 0:
        return "[" + " " * width + "]"
    filled = max(0, min(width, round(value / maximum * width)))
    return "[" + "▓" * filled + "░" * (width - filled) + "]"


AFTERMATHS: dict[str, dict] = {
    "1-up": {
        "narrative": "You jack out, hands shaking. The deck's warm. You did it — barely. The construct is gone, but something else is watching now.",
        "ko": "잭아웃한다, 손이 떨린다. 데크가 따뜻하다. 해냈다 — 간신히. 구성체는 사라졌지만, 이제 다른 무언가가 지켜보고 있다.",
        "character": "case",
        "reaction": "Your hands are shaking. The deck's warm. You jack out, and the shaking doesn't stop.",
        "reaction_ko": "네 손이 떨린다. 데크가 따뜻하다. 잭아웃해도, 떨림은 멈추지 않는다.",
    },
    "2-up": {
        "narrative": "A clean kill. The system was small, but the construct inside was real — fragments of code, frozen mid-thought.",
        "ko": "깔끔한 격파. 시스템은 작았지만, 안의 구성체는 진짜였다 — 생각하던 도중에 굳은 코드 조각들.",
        "character": "finn",
        "reaction": "Standard. Don't make a habit of dying. The Finn pays for results, not for funerals.",
        "reaction_ko": "평범해. 죽는 데 익숙해지지 마. The Finn은 결과를 사고, 장례식이 아니라.",
    },
    "3-up": {
        "narrative": "You carved through the matrix like it owed you something. The construct didn't stand a chance.",
        "ko": "매트릭스를 뭔가 빚진 것처럼 헤집고 다녔다. 구성체는 어쩔 수 없었다.",
        "character": "dixie",
        "reaction": "야, 잘 했어. 근데 조심해 — 그건 그냥 sentry였어. T-A가 더 큰 거 가지고 있어.",
        "reaction_ko": "야, 잘 했어. 근데 조심해 — 그건 그냥 sentry였어. T-A가 더 큰 거 가지고 있어.",
    },
    "4-up": {
        "narrative": "You moved like a veteran. The matrix bent around you. In Sprawl, they're starting to notice.",
        "ko": "베테랑처럼 움직였다. 매트릭스가 네 주위에서 휘었다. 스프롤에서, 이제 알아채기 시작한다.",
        "character": "3jane",
        "reaction": "I see you. The construct I sent was a test. The next will not be.",
        "reaction_ko": "당신을 본다. 보낸 구성체는 시험이었다. 다음은 그렇지 않을 거다.",
    },
    "5-up": {
        "narrative": "You are the construct's nightmare. The matrix parts for you — not because it fears you, but because it remembers you.",
        "ko": "당신은 구성체의 악몽이다. 매트릭스가 당신을 위해 갈라진다 — 두려워서가 아니라, 기억하기 때문이다.",
        "character": "dixie",
        "reaction": "I was a cowboy once. Killed a few. Doesn't make it easier. Don't let it make you cold.",
        "reaction_ko": "나도 한때 카우보이였다. 몇 개 죽였다. 그게 쉬워지진 않는다. 너를 차갑게 만들지도 마라.",
    },
}


def _print_aftermath(grade_key: str) -> None:
    """Print the grade-specific aftermath narrative + character reaction."""
    after = AFTERMATHS.get(grade_key)
    if after is None:
        return
    print("  [Aftermath]")
    print(f"  > {after['narrative']}")
    print(f"  > {after['ko']}")
    print()
    print(f"  [Reaction — {after['character'].title()}]")
    print(f'  > "{after["reaction"]}"')
    print(f'  > "{after["reaction_ko"]}"')
    print()


def _print_grade_summary(result: dict, enemy: Combatant, zdr: int, grade_key: str) -> None:
    ppl = result["ppl"]
    status = calculate_status(ppl, zdr)
    ratio = ppl / zdr if zdr > 0 else float("inf")
    print(
        f"=== {result['grade']} (PPL {ppl} vs ZDR {zdr} = {ratio:.2f}x, {status.value.upper()}) ==="
    )
    print(f"  Deck T{result['deck_tier']}  HP {result['max_hp']}  ATK {result['auto_attack']}")
    print(f"  Status: {status.value.upper()}  Color: {status_color(status)}")
    print()
    if result["outcome"] == "victory":
        print(f"  VICTORY in {result['time_s']:.1f}s")
        print(
            f"  Damage dealt: {result['damage_dealt']}  Taken: {result['damage_taken']}  "
            f"Skill uses: {result['skill_uses']}  HP left: {result['player_hp_remaining']}"
        )
        print(f"  HEAL potential: +{result['heal_potential']} HP (max 20% of {result['max_hp']})")
        _print_aftermath(grade_key)
    elif result["outcome"] == "defeat":
        print(f"  DEFEAT in {result['time_s']:.1f}s")
        print(
            f"  Damage dealt: {result['damage_dealt']}  Taken: {result['damage_taken']}  "
            f"Skill uses: {result['skill_uses']}"
        )
        print(f"  Player HP at flatline: {result['player_hp_remaining']}")
    else:
        print(f"  TIMEOUT in {result['time_s']:.1f}s (combat still ongoing)")
        print(
            f"  Damage dealt: {result['damage_dealt']}  Taken: {result['damage_taken']}  "
            f"Skill uses: {result['skill_uses']}  HP left: {result['player_hp_remaining']}"
        )
    print()


def _print_comparison(results: list[dict], enemy_name: str, zdr: int) -> None:
    print("=" * 78)
    print(f"  COMPARISON: vs {enemy_name} (ZDR {zdr})")
    print("=" * 78)
    header = (
        f"{'Grade':<14} {'PPL':>4} {'Ratio':>6} {'Status':<8} "
        f"{'Outcome':<9} {'Time':>6} {'Dmg Out':>8} {'Dmg In':>7} {'Skills':>7}"
    )
    print(header)
    print("-" * 78)
    for r in results:
        ppl = r["ppl"]
        ratio = ppl / zdr if zdr > 0 else float("inf")
        status = calculate_status(ppl, zdr).value
        outcome = r["outcome"].upper()
        print(
            f"{r['grade']:<14} {ppl:>4} {ratio:>6.2f} {status:<8} "
            f"{outcome:<9} {r['time_s']:>5.1f}s "
            f"{r['damage_dealt']:>8} {r['damage_taken']:>7} {r['skill_uses']:>7}"
        )
    print("-" * 78)


def _print_avatar_for_grade(grade: dict) -> str:
    """Render a stick-figure avatar for the given grade (ADR-0016)."""
    head = "◉P◉" if grade["max_hp"] > 0 else "X"
    arms = " ".join(_tier_glyph(pid, t) for pid, t in grade["programs"])
    deck_glyph = f"║DK{grade['deck_tier']}║"
    wetware = "▓" * grade["wetware_tier"] + "░" * (5 - grade["wetware_tier"])
    construct = "◆D◆" if grade.get("construct_tier", 0) >= 5 else ""
    lines = [
        head,
        "  /|\\",
        f" {arms}",
        "  \\|/",
        f" {deck_glyph}",
        f"  {wetware}",
    ]
    if construct:
        lines.append(f"  {construct}")
    return "\n".join("    " + line for line in lines)


def _tier_glyph(skill_id: str, tier: int) -> str:
    initial = skill_id[0].upper()
    return {
        1: f"·{initial}·",
        2: f":{initial}:",
        3: f"|{initial}|",
        4: f"▓{initial}▓",
        5: f"★{initial}★",
    }.get(tier, "?")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--enemy",
        default="standard",
        choices=["standard", "watchdog", "black", "goliath", "construct"],
        help="Enemy ICE type (default: standard for full progression).",
    )
    parser.add_argument("--zdr", type=int, default=6, help="ZDR for the fight")
    parser.add_argument("--max-ticks", type=int, default=30000)
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    parser.add_argument("--no-clear", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    programs = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    portraits = PortraitManager(data_dir=data_dir / "portraits")

    enemy = _build_enemy(args.enemy, ice, portraits)

    print("=" * 78)
    print(f"  COMBAT GRADE PROGRESSION — vs {enemy.name} (ZDR {args.zdr})")
    print("=" * 78)
    print()
    print(f"Enemy: {enemy.portrait} {enemy.name}  HP {enemy.hp}  ATK {enemy.auto_attack_damage}")
    print()

    results: list[dict] = []
    for grade in GRADES:
        if not args.no_clear:
            pass
        print("=" * 78)
        print(f"  {grade['label']}")
        print("=" * 78)
        print()
        print("Avatar:")
        print(_print_avatar_for_grade(grade))
        print()
        result, _ = _run_one_grade(
            grade,
            enemy,
            programs,
            max_tick_ms=args.max_ticks,
            rng_seed=42,
        )
        results.append(result)
        grade_key = grade["label"].split()[0]
        _print_grade_summary(result, enemy, args.zdr, grade_key)
        if not args.no_clear:
            print()

    _print_comparison(results, enemy.name, args.zdr)
    print()
    print("=" * 78)
    print("  PROGRESSION INSIGHTS")
    print("=" * 78)
    print("- Higher grades deal more damage per second (auto-attack scales with deck tier).")
    print("- Higher grades have larger HP pools, surviving more hits before flatline.")
    print("- Higher grades unlock more powerful skills (Wisp T1 → Kraken T5).")
    print("- Higher grades need fewer skill uses because auto-attack is sufficient.")
    print("- HEAL via Data Salvage (ADR-0014) restores more HP at higher grades (20% of max_hp).")
    print("- PPL climbs 8 → 65 (~8x), so even matched enemies (1.0x) become trivial at high grade.")
    print()

    if args.save:
        out_path = project_root / "data" / "combat" / "grade_progression.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "enemy": enemy.name,
                    "zdr": args.zdr,
                    "results": results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
            print(f"Results saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

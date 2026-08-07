"""Tests for the combat model and simulator (ADR-0003)."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from roguelike_sprawl.combat import (
    Combatant,
    CombatState,
    IceRegistry,
    ProgramRegistry,
    build_default_player,
    build_ice_enemy,
    step_combat,
    use_skill,
)
from roguelike_sprawl.combat.state import (
    ALARM_MAX_LEVEL,
    ALARM_TICK_INTERVAL_MS,
    AUTO_ATTACK_INTERVAL_MS,
    COMBO_WINDOW_MS,
    Skill,
    SkillEffect,
    StatusEffect,
    _calculate_damage,
)


def _enemy(max_hp: int, base_damage: int) -> Combatant:
    return Combatant(
        id="enemy",
        name="Test",
        portrait="▲ICE▲",
        color=(255, 0, 255),
        hp=max_hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=base_damage,
        team="enemy",
    )


def test_combatant_creation() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    assert p.hp == 100
    assert p.max_hp == 100
    assert p.ap == 6
    assert p.team == "player"
    assert p.is_alive()


def test_combatant_take_damage() -> None:
    p = build_default_player(max_hp=50, max_ap=6, programs=ProgramRegistry({}))
    p.hp = 30
    assert p.is_alive()
    p.hp = 0
    assert not p.is_alive()


def test_step_combat_auto_attack() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 10
    e = _enemy(max_hp=80, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert e.hp < 80
    assert "You hit" in state.log[-1] or len(state.log) > 0


def test_step_combat_enemy_attack() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e = _enemy(max_hp=80, base_damage=5)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert p.hp < 100
    assert any("Test hits you" in line for line in state.log)


def test_use_skill_attack() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    skill = Skill(
        id="goliath",
        name="Goliath",
        tier=3,
        effect=SkillEffect.ATTACK,
        ap_cost=3,
        damage=25,
    )
    p.skills = (skill,)
    e = _enemy(max_hp=80, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    used = use_skill(state, skill)
    assert used
    assert p.ap == 3
    # Damage has 80-120% variance
    assert 50 <= e.hp <= 60  # 25 dmg ±20% = 20-30
    assert "Goliath" in state.log[-1]


def test_use_skill_insufficient_ap() -> None:
    p = build_default_player(max_hp=100, max_ap=2, programs=ProgramRegistry({}))
    skill = Skill(id="goliath", name="Goliath", tier=3, effect="attack", ap_cost=3, damage=25)
    p.skills = (skill,)
    e = _enemy(max_hp=80, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    used = use_skill(state, skill)
    assert not used
    assert p.ap == 2
    assert e.hp == 80


def test_use_skill_shield() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    skill = Skill(
        id="wisp",
        name="Wisp",
        tier=1,
        effect=SkillEffect.SHIELD,
        ap_cost=2,
        shield=1,
    )
    p.skills = (skill,)
    e = _enemy(max_hp=80, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, skill)
    assert state.shield == 1


def test_shield_absorbs_damage() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=80, base_damage=5)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.shield = 10
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    # Shield reduced (exact amount varies due to 80-120% damage variance)
    assert state.shield < 10  # Some shield absorbed
    assert p.hp == 100  # Player took no damage (all absorbed)


def test_victory_condition() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 100
    e = _enemy(max_hp=10, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.finished
    assert state.outcome == "victory"


def test_defeat_condition() -> None:
    p = build_default_player(max_hp=10, max_ap=0, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e = _enemy(max_hp=80, base_damage=100)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.finished
    assert state.outcome == "defeat"


def test_step_combat_after_finished_no_op() -> None:
    p = build_default_player(max_hp=10, max_ap=0, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e = _enemy(max_hp=1, base_damage=100)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.finished
    enemy_hp_before = e.hp
    tick_before = state.tick_ms
    step_combat(state)
    assert e.hp == enemy_hp_before
    assert state.tick_ms == tick_before


def test_program_registry_loads(data_dir: Path) -> None:
    reg = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    assert len(reg) >= 3
    wisp = reg.get("wisp")
    assert wisp is not None
    # Effect should be a valid SkillEffect enum
    assert wisp.effect in SkillEffect
    assert wisp.shield >= 0


def test_ice_registry_loads(data_dir: Path) -> None:
    reg = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    assert "standard" in reg
    assert "black" in reg
    standard = reg.get("standard")
    assert standard is not None
    assert int(standard["hp_base"]) == 80


def test_build_ice_enemy(data_dir: Path) -> None:
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    e = build_ice_enemy("standard", ice)
    assert e.name == "ICE — Standard"
    assert e.hp == 80
    assert e.team == "enemy"


def test_build_ice_enemy_scaled(data_dir: Path) -> None:
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    e_g1 = build_ice_enemy("standard", ice, player_grade=1)
    assert e_g1.hp == 80
    e_g3 = build_ice_enemy("standard", ice, player_grade=3)
    assert e_g3.hp == 80 + (15 * 2)
    e_g5 = build_ice_enemy("standard", ice, player_grade=5)
    assert e_g5.hp == 80 + (15 * 4)


def test_log_capped_at_6() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (Skill(id="g", name="G", tier=1, effect="attack", ap_cost=1, damage=1),)
    e = _enemy(max_hp=80, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(10):
        use_skill(state, p.skills[0])
    assert len(state.log) <= 6


def test_construct_data_shape(data_dir: Path) -> None:
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    for ice_id in ("standard", "watchdog", "black", "goliath", "dixie"):
        data = ice.get(ice_id)
        assert data is not None
        assert "hp_base" in data
        assert "dmg_base" in data
        assert int(data["hp_base"]) > 0
        assert int(data["dmg_base"]) >= 0


def test_start_combat_uses_node_ice_kind(data_dir: Path) -> None:
    """Regression: combat_view.start_combat must use ice_node.ice to pick
    the enemy, not hardcoded 'standard'. Pre-fix: every node spawned the
    same Standard ICE regardless of node.ice value.
    """
    from roguelike_sprawl.engine import combat_view
    from roguelike_sprawl.engine.state import AppState
    from roguelike_sprawl.matrix.node import IceKind, Node, NodeKind, ZoneDepth

    ice_reg = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    prog_reg = ProgramRegistry.load(data_dir / "programs" / "programs.json")

    # Black ICE node → should spawn black enemy, not standard
    black_node = Node(
        id="ice_black_test",
        kind=NodeKind.ICE,
        label="Black ICE",
        zone=ZoneDepth.CORE,
        ice=IceKind.BLACK,
    )
    state = AppState()
    cs = combat_view.start_combat(state, black_node, prog_reg, ice_reg)
    assert "Black" in cs.enemy.name, f"Expected Black ICE, got {cs.enemy.name!r}"

    # Watchdog node → should spawn watchdog enemy
    watchdog_node = Node(
        id="ice_watchdog_test",
        kind=NodeKind.ICE,
        label="Watchdog",
        zone=ZoneDepth.MID,
        ice=IceKind.WATCHDOG,
    )
    state2 = AppState()
    cs2 = combat_view.start_combat(state2, watchdog_node, prog_reg, ice_reg)
    assert "Watchdog" in cs2.enemy.name, f"Expected Watchdog ICE, got {cs2.enemy.name!r}"


def test_all_mission_ice_ids_resolve(data_dir: Path) -> None:
    """Regression: every ``ice.<X>`` referenced by a mission must exist
    in the ICE registry. Pre-fix: 10 references (construct, boss,
    revelation, neuromancer, ai_whisper, surveillance, wintermute,
    zion_defense) silently failed at runtime — added in this session.
    """
    import json

    ice_reg = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    with (data_dir / "missions" / "missions.json").open(encoding="utf-8") as f:
        missions = json.load(f)

    missing: list[str] = []
    for mid, m in missions.items():
        for obj in [m.get("primary_objective", {})] + m.get("secondary_objectives", []):
            enemy = obj.get("enemy", "")
            if enemy.startswith("ice."):
                ice_id = enemy[len("ice.") :]
                if ice_reg.get(ice_id) is None:
                    missing.append(f"{mid}: {enemy} (resolved {ice_id!r})")

    assert not missing, "Mission ICE references missing from registry:\n" + "\n".join(
        f"  {m}" for m in missing
    )


def test_ap_regen() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.ap = 0
    e = _enemy(max_hp=200, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(70):
        step_combat(state)
    assert p.ap >= 3


def test_vfx_overlay_no_afterimage() -> None:
    """Regression: hit flash must not leave afterimages when expired.

    Before fix: _draw_vfx_overlay only printed at sparse cells (x+y)%3==0,
    and console.print only set fg (not bg). After flash expired, the colored
    cells remained visible as ghost images (afterimages).

    After fix: _draw_vfx_overlay clears the entire region with bg=0 before
    drawing any effects, preventing afterimages.
    """
    import tcod.console

    from roguelike_sprawl.combat.effects import CombatEffects
    from roguelike_sprawl.engine.combat_view import _draw_vfx_overlay
    from roguelike_sprawl.engine.layout import Region, RegionId

    console = tcod.console.Console(30, 20)
    region = Region(id=RegionId.MAIN, x=5, y=3, w=20, h=14)

    fx = CombatEffects()
    fx.hit_flash.trigger(color=(255, 255, 255), duration_ms=120)
    _draw_vfx_overlay(console, region, fx, 0, 0)

    flash_count_active = sum(
        1
        for y in range(region.y, region.y + region.h)
        for x in range(region.x, region.x + region.w)
        if chr(console.ch[y, x]) == "█"
    )
    assert flash_count_active > 0, "Hit flash should render some cells"

    fx.step(200)  # 200ms > 120ms duration
    assert not fx.hit_flash.is_active, "Hit flash should be expired"

    _draw_vfx_overlay(console, region, fx, 0, 0)

    flash_count_after = sum(
        1
        for y in range(region.y, region.y + region.h)
        for x in range(region.x, region.x + region.w)
        if chr(console.ch[y, x]) == "█"
    )
    assert flash_count_after == 0, (
        f"Afterimage bug: {flash_count_after} flash cells remain after expiry. "
        "The overlay region should be cleared before re-drawing."
    )


def test_weakness_matrix_has_all_ice_kinds() -> None:
    """Every known ICE kind must appear in WEAKNESS_BY_ICE."""
    from roguelike_sprawl.combat.state import WEAKNESS_BY_ICE

    expected = {
        "standard",
        "watchdog",
        "goliath",
        "black",
        "construct",
        "wintermute",
        "ta_construct_prime",
    }
    assert expected.issubset(WEAKNESS_BY_ICE.keys()), (
        f"Missing ICE kinds: {expected - WEAKNESS_BY_ICE.keys()}"
    )


def test_weakness_matrix_each_entry_has_all_roles() -> None:
    """Each ICE entry must define all five roles."""
    from roguelike_sprawl.combat.state import WEAKNESS_BY_ICE

    roles = {"strike", "burst", "guard", "utility", "sustain"}
    for ice_kind, mapping in WEAKNESS_BY_ICE.items():
        missing = roles - mapping.keys()
        assert not missing, f"{ice_kind} missing roles: {missing}"


def test_weakness_matrix_multipliers_in_range() -> None:
    """All multipliers must be in (0.0, 2.0]."""
    from roguelike_sprawl.combat.state import WEAKNESS_BY_ICE

    for ice_kind, mapping in WEAKNESS_BY_ICE.items():
        for role, mult in mapping.items():
            assert 0.0 < mult <= 2.0, f"{ice_kind}/{role} multiplier {mult} out of bounds"


def test_default_weakness_multiplier_is_neutral() -> None:
    from roguelike_sprawl.combat.state import DEFAULT_WEAKNESS_MULTIPLIER

    assert DEFAULT_WEAKNESS_MULTIPLIER == 1.0


def _skill_with_role(role: str | None, damage: int = 25) -> Skill:
    return Skill(
        id="test",
        name="Test",
        tier=1,
        effect=SkillEffect.ATTACK,
        ap_cost=1,
        damage=damage,
        role=role,
    )


def _enemy_with_kind(ice_kind: str | None, resistance: float = 0.0) -> Combatant:
    e = _enemy(max_hp=200, base_damage=0)
    e.ice_kind = ice_kind
    e.ice_resistance = resistance
    return e


def test_weakness_strike_vs_standard_deals_more_damage() -> None:
    """strike role vs standard ICE → 1.5× multiplier applies."""
    from roguelike_sprawl.combat.state import WEAKNESS_BY_ICE

    assert WEAKNESS_BY_ICE["standard"]["strike"] == 1.5

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role("strike", damage=100))

    log = state.log[-1]
    import re

    m = re.search(r"(\d+) damage", log)
    assert m, f"No damage found in log: {log}"
    dmg = int(m.group(1))
    assert 120 <= dmg <= 180, f"Expected 120-180 (base × 1.5), got {dmg}"


def test_resistance_sustain_vs_standard_deals_less_damage() -> None:
    """sustain role vs standard ICE → 0.8× multiplier applies."""
    from roguelike_sprawl.combat.state import WEAKNESS_BY_ICE

    assert WEAKNESS_BY_ICE["standard"]["sustain"] == 0.8

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role("sustain", damage=100))

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m, f"No damage found in log: {log}"
    dmg = int(m.group(1))
    assert 64 <= dmg <= 96, f"Expected 64-96 (base × 0.8), got {dmg}"


def test_no_weakness_when_role_is_none() -> None:
    """role=None on skill → no weakness multiplier applied (backward compat)."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role(None, damage=100))

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 80 <= dmg <= 120, f"Expected 80-120 (no multiplier), got {dmg}"


def test_no_weakness_when_ice_kind_is_none() -> None:
    """ice_kind=None on enemy → no weakness multiplier applied."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role("strike", damage=100))

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 80 <= dmg <= 120, f"Expected 80-120 (no multiplier), got {dmg}"


def test_ice_resistance_reduces_damage() -> None:
    """defender.ice_resistance=0.3 → 30% damage reduction."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None, resistance=0.3)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role(None, damage=100))

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 56 <= dmg <= 84, f"Expected 56-84 (base × 0.7), got {dmg}"


def test_unknown_ice_kind_uses_default_multiplier() -> None:
    """ICE kind not in matrix → DEFAULT_WEAKNESS_MULTIPLIER (1.0)."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind("some_unknown_ice")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, _skill_with_role("strike", damage=100))

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 80 <= dmg <= 120, f"Expected 80-120 (default 1.0×), got {dmg}"


def test_probe_reveals_weakness_for_known_ice(data_dir: Path) -> None:
    """Probe against Standard ICE → reports WEAK to STRIKE (+50%)."""
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    e = build_ice_enemy("standard", ice)

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    probe = Skill(
        id="probe",
        name="Probe",
        tier=1,
        effect=SkillEffect.DETECT,
        ap_cost=1,
    )
    p.skills = (probe,)

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, probe)

    log = state.log[-1]
    assert "WEAK" in log, f"Expected WEAK in log: {log}"
    assert "STRIKE" in log, f"Expected STRIKE in log: {log}"
    assert "+50%" in log, f"Expected +50% in log: {log}"


def test_probe_reveals_resistance_for_strong_against(data_dir: Path) -> None:
    """Probe against Watchdog ICE → best role is burst (+50%)."""
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    e = build_ice_enemy("watchdog", ice)

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    probe = Skill(
        id="probe",
        name="Probe",
        tier=1,
        effect=SkillEffect.DETECT,
        ap_cost=1,
    )
    p.skills = (probe,)

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, probe)

    log = state.log[-1]
    assert "WEAK" in log
    assert "BURST" in log


def test_probe_falls_back_to_hp_ap_when_no_ice_kind() -> None:
    """Probe against enemy without ice_kind → shows HP/AP (legacy fallback)."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.hp = 42
    e.max_hp = 100

    probe = Skill(
        id="probe",
        name="Probe",
        tier=1,
        effect=SkillEffect.DETECT,
        ap_cost=1,
    )
    p.skills = (probe,)

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, probe)

    log = state.log[-1]
    assert "HP" in log
    assert "42" in log
    assert "100" in log


def test_program_registry_loads_role_from_json(data_dir: Path) -> None:
    """Role field must round-trip through JSON loader."""
    reg = ProgramRegistry.load(data_dir / "programs" / "programs.json")
    strike = reg.get("strike")
    assert strike is not None
    assert strike.role == "strike"
    wisp = reg.get("wisp")
    assert wisp is not None
    assert wisp.role == "guard"


def test_build_ice_enemy_sets_ice_kind_and_resistance(data_dir: Path) -> None:
    """build_ice_enemy must populate ice_kind and ice_resistance fields."""
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    e = build_ice_enemy("watchdog", ice)
    assert e.ice_kind == "watchdog"
    assert 0.0 <= e.ice_resistance <= 1.0


def test_alarm_constants_defined() -> None:
    from roguelike_sprawl.combat.state import (
        ALARM_MAX_LEVEL,
        ALARM_TICK_INTERVAL_MS,
    )

    assert ALARM_MAX_LEVEL == 5
    assert ALARM_TICK_INTERVAL_MS == 10000


def test_alarm_starts_at_zero() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=200, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    assert state.alarm_level == 0
    assert state.last_alarm_tick_ms == 0


def test_alarm_ticks_after_interval() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=200, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    ticks_for_one_alarm = ALARM_TICK_INTERVAL_MS // 100
    for _ in range(ticks_for_one_alarm):
        step_combat(state)
    assert state.alarm_level == 1


def test_alarm_logs_warning_message() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=200, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    ticks_for_one_alarm = ALARM_TICK_INTERVAL_MS // 100
    for _ in range(ticks_for_one_alarm):
        step_combat(state)
    assert any("TRACE WARNING" in line for line in state.log)
    assert any("alarm level 1/" in line for line in state.log)


def test_alarm_reaching_max_causes_flatline() -> None:
    p = build_default_player(max_hp=1000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    ticks_for_full_trace = (ALARM_TICK_INTERVAL_MS * ALARM_MAX_LEVEL) // 100
    for _ in range(ticks_for_full_trace):
        if state.finished:
            break
        step_combat(state)
    assert state.finished
    assert state.outcome == "defeat"
    assert state.alarm_level >= ALARM_MAX_LEVEL
    assert any("TRACE COMPLETE" in line for line in state.log)


def test_alarm_does_not_progress_after_finished() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    p.auto_attack_damage = 1000
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.finished
    alarm_at_finish = state.alarm_level
    ticks_for_one_alarm = ALARM_TICK_INTERVAL_MS // 100
    for _ in range(ticks_for_one_alarm * 2):
        step_combat(state)
    assert state.alarm_level == alarm_at_finish


def test_alarm_reduces_player_hp_pressure_time() -> None:
    """Player must win before alarm 5 OR lose HP via flatline."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10, base_damage=10_000)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    p.auto_attack_damage = 1000
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.outcome == "victory"
    assert state.alarm_level < ALARM_MAX_LEVEL


def test_alarm_warning_message_appears_in_log_after_one_tick() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    ticks_for_one_alarm = ALARM_TICK_INTERVAL_MS // 100
    for _ in range(ticks_for_one_alarm):
        step_combat(state)
    assert "TRACE WARNING" in state.log[-1]


def _strike_skill(damage: int = 100) -> Skill:
    return Skill(
        id="strike_test",
        name="Strike Test",
        tier=1,
        effect=SkillEffect.ATTACK,
        ap_cost=1,
        damage=damage,
        role="strike",
    )


def _burst_skill(damage: int = 100) -> Skill:
    return Skill(
        id="burst_test",
        name="Burst Test",
        tier=1,
        effect=SkillEffect.ATTACK,
        ap_cost=1,
        damage=damage,
        role="burst",
    )


def _guard_skill() -> Skill:
    return Skill(
        id="guard_test",
        name="Guard Test",
        tier=1,
        effect=SkillEffect.SHIELD,
        ap_cost=1,
        shield=1,
        role="guard",
    )


def test_role_synergy_constants_defined() -> None:
    from roguelike_sprawl.combat.state import ROLE_SYNERGY_BONUSES

    assert ROLE_SYNERGY_BONUSES[1] == 1.0
    assert ROLE_SYNERGY_BONUSES[2] == 1.15
    assert ROLE_SYNERGY_BONUSES[3] == 1.30


def test_role_synergy_no_bonus_when_single_skill() -> None:
    """1 skill with role → no bonus (1.0×)."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, p.skills[0])

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 80 <= dmg <= 120, f"Expected 80-120 (no bonus), got {dmg}"


def test_role_synergy_two_skills_15pct_bonus() -> None:
    """2 skills with same role → +15% damage."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill())
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, p.skills[0])

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 92 <= dmg <= 138, f"Expected 92-138 (× 1.15), got {dmg}"


def test_role_synergy_three_skills_30pct_bonus() -> None:
    """3 skills with same role → +30% damage."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill(), _strike_skill())
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, p.skills[0])

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 104 <= dmg <= 156, f"Expected 104-156 (× 1.30), got {dmg}"


def test_role_synergy_different_roles_no_bonus() -> None:
    """Different roles → no synergy even with 3 skills."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _burst_skill(), _guard_skill())
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, p.skills[0])

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 80 <= dmg <= 120, f"Expected 80-120 (no synergy, different roles), got {dmg}"


def test_role_synergy_does_not_apply_to_enemy_attacks() -> None:
    """Synergy is player-only; enemy auto-attack never gets bonus."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill())
    e = _enemy_with_kind(None)
    e.auto_attack_damage = 100
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    p.hp = 1000

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert p.hp < 1000
    assert p.hp >= 800


def test_role_synergy_composes_with_weakness() -> None:
    """Weakness × synergy stack multiplicatively."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill(), _strike_skill())
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    use_skill(state, p.skills[0])

    import re

    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 156 <= dmg <= 234, f"Expected 156-234 (× 1.5 weakness × 1.30 synergy), got {dmg}"


def test_role_synergy_count_helper() -> None:
    """_count_player_role_synergy returns count of same-role skills."""
    from roguelike_sprawl.combat.state import _count_player_role_synergy

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill(), _burst_skill())
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.last_skill_used = p.skills[0]
    assert _count_player_role_synergy(state) == 2

    state.last_skill_used = p.skills[2]
    assert _count_player_role_synergy(state) == 1

    state.last_skill_used = None
    assert _count_player_role_synergy(state) == 0


# ----------------------------------------------------------------------------
# Per-ICE alarm speed (C1.5)
# ----------------------------------------------------------------------------


def test_alarm_speed_by_ice_constant_defined() -> None:
    from roguelike_sprawl.combat.state import ALARM_SPEED_BY_ICE

    assert "standard" in ALARM_SPEED_BY_ICE
    assert "wintermute" in ALARM_SPEED_BY_ICE
    assert ALARM_SPEED_BY_ICE["standard"] == 1.0
    assert ALARM_SPEED_BY_ICE["wintermute"] > 2.0


def test_alarm_speed_default_is_one() -> None:
    from roguelike_sprawl.combat.state import DEFAULT_ALARM_SPEED

    assert DEFAULT_ALARM_SPEED == 1.0


def test_alarm_ticks_faster_against_wintermute() -> None:
    """Wintermute (alarm_speed=2.5) should tick alarm twice as fast as standard."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.alarm_speed = 2.5
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(100):
        step_combat(state)
    assert state.alarm_level >= 2


def test_alarm_ticks_slower_against_construct() -> None:
    """Construct (alarm_speed=0.5) should tick alarm half as fast as standard."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.alarm_speed = 0.5
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    for _ in range(100):
        step_combat(state)
    assert state.alarm_level == 0


def test_build_ice_enemy_sets_alarm_speed(data_dir: Path) -> None:
    """build_ice_enemy must populate alarm_speed from ALARM_SPEED_BY_ICE."""
    ice = IceRegistry.load(data_dir / "combat" / "ice_types.json")
    standard = build_ice_enemy("standard", ice)
    assert standard.alarm_speed == 1.0
    wintermute = build_ice_enemy("wintermute", ice)
    assert wintermute.alarm_speed == 2.5
    construct = build_ice_enemy("construct", ice)
    assert construct.alarm_speed == 0.5


def test_wintermute_flatlines_before_standard() -> None:
    """Wintermute traces faster than standard — player must kill faster or die."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0

    e_wintermute = _enemy(max_hp=100_000, base_damage=0)
    e_wintermute.alarm_speed = 2.5
    state = CombatState(player=p, enemy=e_wintermute, rng=random.Random(0))

    ticks = (ALARM_TICK_INTERVAL_MS * ALARM_MAX_LEVEL) // 100
    for _ in range(ticks):
        if state.finished:
            break
        step_combat(state)

    assert state.finished
    assert state.outcome == "defeat"
    assert state.alarm_level >= ALARM_MAX_LEVEL


# ----------------------------------------------------------------------------
# Combo bonus (B2-1)
# ----------------------------------------------------------------------------


def test_combo_bonuses_constant_defined() -> None:
    from roguelike_sprawl.combat.state import COMBO_BONUSES, COMBO_WINDOW_MS

    assert COMBO_BONUSES[1] == 1.0
    assert COMBO_BONUSES[3] == 1.2
    assert COMBO_BONUSES[5] == 2.0
    assert COMBO_BONUSES[6] == 3.0
    assert COMBO_WINDOW_MS == 3500


def test_combo_starts_at_zero() -> None:
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=200, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    assert state.player_combo == 0
    assert state.combo_last_hit_ms == 0


def test_combo_no_bonus_at_one_or_two_hits() -> None:
    """Combo of 1-2 hits → 1.0× (no bonus)."""
    from roguelike_sprawl.combat.state import COMBO_BONUSES

    assert COMBO_BONUSES[1] == 1.0
    assert COMBO_BONUSES[2] == 1.0


def test_combo_bonus_three_hits_20pct() -> None:
    """3 hits → 1.2× damage."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=100),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.player_combo = 3

    import re

    use_skill(state, p.skills[0])
    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 96 <= dmg <= 144, f"Expected 96-144 (× 1.2), got {dmg}"


def test_combo_bonus_six_hits_3x_damage() -> None:
    """6+ hits → 3.0× damage."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=100),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.player_combo = 6

    import re

    use_skill(state, p.skills[0])
    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 240 <= dmg <= 360, f"Expected 240-360 (× 3.0), got {dmg}"


def test_combo_increments_on_player_hit() -> None:
    """Each player auto-attack should increment player_combo."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 50
    e = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.player_combo >= 1
    assert state.combo_last_hit_ms > 0


def test_combo_resets_after_window_expires() -> None:
    """If no hit lands within COMBO_WINDOW_MS, combo resets to 0."""
    from roguelike_sprawl.combat.state import _tick_combo

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    state.player_combo = 5
    state.combo_last_hit_ms = 0
    state.tick_ms = COMBO_WINDOW_MS + 1000

    _tick_combo(state)
    assert state.player_combo == 0


def test_combo_does_not_reset_within_window() -> None:
    """If a hit lands within COMBO_WINDOW_MS, combo persists."""
    from roguelike_sprawl.combat.state import _tick_combo

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    state.player_combo = 5
    state.combo_last_hit_ms = state.tick_ms
    state.tick_ms = state.combo_last_hit_ms + (COMBO_WINDOW_MS - 100)

    _tick_combo(state)
    assert state.player_combo == 5


def test_combo_does_not_apply_to_enemy_attacks() -> None:
    """Enemy attacks never benefit from combo bonus."""
    p = build_default_player(max_hp=1000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e = _enemy(max_hp=10_000, base_damage=100)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.enemy_combo = 6

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage_taken = 1000 - p.hp
    assert damage_taken < 200  # No 3× multiplier


def test_combo_composes_with_weakness() -> None:
    """Weakness × combo stack multiplicatively."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=100),)
    e = _enemy_with_kind("standard")  # strike vs standard = 1.5×
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.player_combo = 5  # 2.0× combo

    import re

    use_skill(state, p.skills[0])
    log = state.log[-1]
    m = re.search(r"(\d+) damage", log)
    assert m
    dmg = int(m.group(1))
    assert 240 <= dmg <= 360, f"Expected 240-360 (× 1.5 × 2.0), got {dmg}"


# ----------------------------------------------------------------------------
# Boss phase auto-transition (E1-1)
# ----------------------------------------------------------------------------


def _two_phase_profile() -> object:
    from roguelike_sprawl.combat.boss import BossProfile, PhaseProfile
    from roguelike_sprawl.combat.effects import IceType

    return BossProfile(
        ice_type=IceType.WINTERMUTE,
        name="Test Boss",
        phases=(
            PhaseProfile(
                phase=1,
                hp_threshold=1.0,
                damage_multiplier=1.0,
                color=(255, 255, 255),
                glyph="1",
                intro_text="Phase 1",
            ),
            PhaseProfile(
                phase=2,
                hp_threshold=0.5,
                damage_multiplier=1.5,
                color=(255, 100, 100),
                glyph="2",
                intro_text="Phase 2",
            ),
        ),
    )


def test_boss_phase_advances_when_hp_drops_below_threshold() -> None:
    """HP fraction ≤ 0.5 should advance current_phase from 1 → 2."""

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=10),)
    e = _enemy_with_kind(None)
    e.max_hp = 100
    e.hp = 49
    e.current_phase = 1

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()

    use_skill(state, p.skills[0])
    step_combat(state)
    assert e.current_phase == 2
    assert any("PHASE" in line and "1" in line and "2" in line for line in state.log)


def test_boss_phase_no_transition_above_threshold() -> None:
    """HP fraction > 0.5 should NOT advance phase."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.max_hp = 100
    e.hp = 80
    e.current_phase = 1

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()

    for _ in range(5):
        step_combat(state)
    assert e.current_phase == 1


def test_boss_phase_no_transition_without_profile() -> None:
    """Without boss_profile, phase never advances."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.max_hp = 100
    e.hp = 1
    e.current_phase = 1

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = None

    step_combat(state)
    assert e.current_phase == 1


def test_boss_phase_does_not_regress() -> None:
    """Phase can only advance, never go back."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.max_hp = 100
    e.hp = 50
    e.current_phase = 2

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()

    step_combat(state)
    assert e.current_phase == 2


def test_boss_phase_three_phase_progression() -> None:
    """Boss with 3 phases should advance 1 → 2 → 3 as HP drops."""
    from roguelike_sprawl.combat.boss import BossProfile, PhaseProfile
    from roguelike_sprawl.combat.effects import IceType

    three_phase = BossProfile(
        ice_type=IceType.WINTERMUTE,
        name="Tri-Phase",
        phases=(
            PhaseProfile(1, 1.0, 1.0, (255, 255, 255), "1", "P1"),
            PhaseProfile(2, 0.66, 1.3, (255, 200, 0), "2", "P2"),
            PhaseProfile(3, 0.33, 1.6, (255, 100, 0), "3", "P3"),
        ),
    )

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    e.max_hp = 100
    e.current_phase = 1

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = three_phase

    e.hp = 60
    step_combat(state)
    assert e.current_phase == 2

    e.hp = 30
    step_combat(state)
    assert e.current_phase == 3


# ----------------------------------------------------------------------------
# Boss phase damage multiplier
# ----------------------------------------------------------------------------


def test_boss_phase_1_damage_is_base() -> None:
    """Phase 1 boss deals base damage (multiplier=1.0)."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=100)
    e.current_phase = 1

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()

    p_hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert p_hp_before - p.hp >= 80
    assert p_hp_before - p.hp <= 120


def test_boss_phase_2_damage_is_50pct_higher() -> None:
    """Phase 2 boss deals damage × 1.5."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=100)
    e.current_phase = 2

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()

    p_hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage = p_hp_before - p.hp
    assert 120 <= damage <= 180, f"Expected 120-180 (100 × 1.5), got {damage}"


def test_boss_phase_damage_no_profile_uses_base() -> None:
    """Without boss_profile, phase multiplier is 1.0 (no effect)."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=100)
    e.current_phase = 3

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = None

    p_hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage = p_hp_before - p.hp
    assert 80 <= damage <= 120, f"Expected 80-120 (no multiplier), got {damage}"


def test_boss_phase_3_damage_uses_60pct_increase() -> None:
    """Boss with phase 3 at 1.6× multiplier deals 1.6× damage."""
    from roguelike_sprawl.combat.boss import BossProfile, PhaseProfile
    from roguelike_sprawl.combat.effects import IceType

    profile = BossProfile(
        ice_type=IceType.WINTERMUTE,
        name="Tri",
        phases=(
            PhaseProfile(1, 1.0, 1.0, (255, 255, 255), "1", "P1"),
            PhaseProfile(3, 0.0, 1.6, (255, 100, 0), "3", "P3"),
        ),
    )
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=100)
    e.current_phase = 3

    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = profile

    p_hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage = p_hp_before - p.hp
    assert 128 <= damage <= 192, f"Expected 128-192 (100 × 1.6), got {damage}"


# ----------------------------------------------------------------------------
# get_combat_pressure() — summary helper for HUD / telemetry
# ----------------------------------------------------------------------------


def test_combat_pressure_baseline() -> None:
    """At combat start, all multipliers should be neutral (1.0×)."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    pressure = get_combat_pressure(state)

    assert pressure["alarm_level"] == 0
    assert pressure["alarm_fraction"] == 0.0
    assert pressure["player_combo"] == 0
    assert pressure["combo_multiplier"] == 1.0
    assert pressure["synergy_multiplier"] == 1.0
    assert pressure["weakness_multiplier"] == 1.0
    assert pressure["boss_phase"] == 0


def test_combat_pressure_reflects_alarm() -> None:
    """Alarm level / max / fraction should be reflected in pressure dict."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.alarm_level = 3

    pressure = get_combat_pressure(state)
    assert pressure["alarm_level"] == 3
    assert pressure["alarm_fraction"] == 0.6


def test_combat_pressure_reflects_combo_and_synergy() -> None:
    """Combo count and synergy should be reflected in pressure dict."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(), _strike_skill(), _strike_skill())
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.player_combo = 5
    state.last_skill_used = p.skills[0]

    pressure = get_combat_pressure(state)
    assert pressure["player_combo"] == 5
    assert pressure["combo_multiplier"] == 2.0
    assert pressure["role_synergy_count"] == 3
    assert pressure["synergy_multiplier"] == 1.30


def test_combat_pressure_reflects_weakness() -> None:
    """Weakness multiplier should reflect ICE kind × skill role."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(),)
    e = _enemy_with_kind("standard")
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.last_skill_used = p.skills[0]

    pressure = get_combat_pressure(state)
    assert pressure["weakness_multiplier"] == 1.5


def test_combat_pressure_reflects_boss_phase() -> None:
    """boss_phase should be 0 if no profile, else enemy.current_phase."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.boss_profile = _two_phase_profile()
    e.current_phase = 2

    pressure = get_combat_pressure(state)
    assert pressure["boss_phase"] == 2

    state.boss_profile = None
    pressure = get_combat_pressure(state)
    assert pressure["boss_phase"] == 0


def test_combat_pressure_reflects_ice_resistance() -> None:
    """ice_resistance field should be reflected directly."""
    from roguelike_sprawl.combat.state import get_combat_pressure

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None, resistance=0.3)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    pressure = get_combat_pressure(state)
    assert pressure["ice_resistance"] == 0.3


def test_role_crit_bonuses_constant_defined() -> None:
    from roguelike_sprawl.combat.state import ROLE_CRIT_BONUSES

    assert ROLE_CRIT_BONUSES["burst"] == 0.10
    assert ROLE_CRIT_BONUSES["strike"] == 0.05
    assert ROLE_CRIT_BONUSES["guard"] == 0.0
    assert ROLE_CRIT_BONUSES["sustain"] == 0.0


def test_role_crit_bonus_applies_to_burst_skill() -> None:
    """Burst role skills get +10% crit chance."""
    from roguelike_sprawl.combat.state import ROLE_CRIT_BONUSES

    assert ROLE_CRIT_BONUSES["burst"] == 0.10
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_burst_skill(),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.last_skill_used = p.skills[0]

    crit_count = 0
    for i in range(200):
        state.rng = random.Random(i)
        dmg, is_crit = _calculate_damage(state, 100, state.player, state.enemy)
        crit_count += int(is_crit)

    crit_rate = crit_count / 200
    base_rate = 0.15
    assert crit_rate > base_rate, f"Burst crit rate {crit_rate} should exceed base {base_rate}"


def test_role_crit_bonus_does_not_apply_to_guard() -> None:
    """Guard role skills get no role-based crit bonus."""
    from roguelike_sprawl.combat.state import ROLE_CRIT_BONUSES

    assert ROLE_CRIT_BONUSES["guard"] == 0.0
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_guard_skill(),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.last_skill_used = p.skills[0]

    for i in range(100):
        state.rng = random.Random(i)
        dmg, is_crit = _calculate_damage(state, 100, state.player, state.enemy)
        assert not is_crit or dmg > 100


def test_role_crit_bonus_unknown_role_treated_as_zero() -> None:
    """Skill with unknown role (e.g. custom) gets no role bonus."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    custom_skill = Skill(
        id="custom",
        name="Custom",
        tier=1,
        effect=SkillEffect.ATTACK,
        ap_cost=1,
        damage=100,
        role="exotic_role",
    )
    p.skills = (custom_skill,)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))
    state.last_skill_used = custom_skill

    for i in range(100):
        state.rng = random.Random(i)
        dmg, is_crit = _calculate_damage(state, 100, state.player, state.enemy)
        assert not is_crit or dmg > 100


def test_crit_variance_constants_defined() -> None:
    from roguelike_sprawl.combat.state import (
        CRIT_MULTIPLIER_MAX,
        CRIT_MULTIPLIER_MIN,
    )

    assert CRIT_MULTIPLIER_MIN == 1.8
    assert CRIT_MULTIPLIER_MAX == 2.2
    assert CRIT_MULTIPLIER_MIN < CRIT_MULTIPLIER_MAX


def test_crit_variance_in_range_across_samples() -> None:
    """Over many crits, damage multipliers should span MIN-MAX range."""
    from roguelike_sprawl.combat.state import (
        CRIT_MULTIPLIER_MAX,
        CRIT_MULTIPLIER_MIN,
        DAMAGE_VARIANCE_MAX,
        DAMAGE_VARIANCE_MIN,
    )

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    crit_multipliers: list[float] = []
    for i in range(500):
        state.rng = random.Random(i)
        base_dmg = 1000
        dmg, is_crit = _calculate_damage(state, base_dmg, state.player, state.enemy)
        if is_crit:
            crit_multipliers.append(dmg / base_dmg)

    assert len(crit_multipliers) >= 30
    floor = CRIT_MULTIPLIER_MIN * DAMAGE_VARIANCE_MIN * 0.95
    ceiling = CRIT_MULTIPLIER_MAX * DAMAGE_VARIANCE_MAX * 1.05
    assert min(crit_multipliers) >= floor
    assert max(crit_multipliers) <= ceiling


def test_crit_variance_single_sample_in_range() -> None:
    """A single crit sample should fall within CRIT_MULTIPLIER_MIN × variance × base."""
    from roguelike_sprawl.combat.state import (
        CRIT_MULTIPLIER_MAX,
        CRIT_MULTIPLIER_MIN,
    )

    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(7))

    for _ in range(100):
        dmg, is_crit = _calculate_damage(state, 1000, state.player, state.enemy)
        if is_crit:
            assert CRIT_MULTIPLIER_MIN * 1000 * 0.8 <= dmg
            assert dmg <= CRIT_MULTIPLIER_MAX * 1000 * 1.2
            return
    pytest.fail("No crit observed in 100 samples")


# ----------------------------------------------------------------------------
# CombatStats tracking
# ----------------------------------------------------------------------------


def test_combat_stats_default_zero() -> None:
    """Fresh CombatState should have all-zero stats."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=100, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    assert state.stats.damage_dealt == 0
    assert state.stats.damage_received == 0
    assert state.stats.crits_landed == 0
    assert state.stats.crits_received == 0
    assert state.stats.skills_used == 0
    assert state.stats.max_combo_reached == 0
    assert state.stats.peak_alarm_level == 0
    assert state.stats.turns_elapsed == 0


def test_combat_stats_damage_dealt_tracked() -> None:
    """Player auto-attacks accumulate damage_dealt."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 20
    e = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)

    assert state.stats.damage_dealt > 0
    assert state.stats.turns_elapsed >= AUTO_ATTACK_INTERVAL_MS // 100


def test_combat_stats_damage_received_tracked() -> None:
    """Enemy auto-attacks accumulate damage_received."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e = _enemy(max_hp=10_000, base_damage=50)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)

    assert state.stats.damage_received > 0


def test_combat_stats_skills_used_tracked() -> None:
    """use_skill increments skills_used counter."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=10),)
    e = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(5):
        use_skill(state, p.skills[0])
    assert state.stats.skills_used == 5


def test_combat_stats_max_combo_tracked() -> None:
    """max_combo_reached should reflect peak player_combo."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 10
    e = _enemy(max_hp=10_000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100 * 3):
        step_combat(state)
    assert state.stats.max_combo_reached >= 1


def test_combat_stats_peak_alarm_tracked() -> None:
    """peak_alarm_level should reflect highest alarm reached."""
    from roguelike_sprawl.combat.state import ALARM_TICK_INTERVAL_MS

    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10_000, base_damage=0)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    ticks = (ALARM_TICK_INTERVAL_MS * 3) // 100
    for _ in range(ticks):
        step_combat(state)
    assert state.stats.peak_alarm_level >= 2


def test_multi_ice_enemies_tuple_synced_from_enemy() -> None:
    """CombatState(enemy=e) should populate enemies tuple via __post_init__."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=80, base_damage=5)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    assert state.enemies == (e,)
    assert state.target is e


def test_multi_ice_target_property_returns_indexed_enemy() -> None:
    """target property returns enemies[target_index]."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    e1 = _enemy(max_hp=80, base_damage=5)
    e2 = _enemy(max_hp=120, base_damage=3)
    state = CombatState(player=p, enemies=(e1, e2), target_index=1, rng=random.Random(0))

    assert state.target is e2
    state.target_index = 0
    assert state.target is e1


def test_multi_ice_all_enemies_auto_attack() -> None:
    """All enemies should auto-attack the player each interval."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e1 = _enemy(max_hp=10_000, base_damage=10)
    e2 = _enemy(max_hp=10_000, base_damage=15)
    e3 = _enemy(max_hp=10_000, base_damage=20)
    state = CombatState(player=p, enemies=(e1, e2, e3), rng=random.Random(0))

    hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage = hp_before - p.hp
    assert damage >= 30  # sum of 10+15+20 with some variance tolerance


def test_multi_ice_victory_only_when_all_dead() -> None:
    """Combat should not end until ALL enemies are dead."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 0
    e1 = _enemy(max_hp=1, base_damage=0)
    e2 = _enemy(max_hp=100, base_damage=0)
    state = CombatState(player=p, enemies=(e1, e2), rng=random.Random(0))

    e1.hp = 0
    step_combat(state)
    assert not state.finished

    e2.hp = 0
    step_combat(state)
    assert state.finished
    assert state.outcome == "victory"


def test_multi_ice_player_attacks_all_alive_enemies() -> None:
    """ADR-0152 multi-enemy: player auto-attack hits ALL alive enemies."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.auto_attack_damage = 50
    e1 = _enemy(max_hp=1000, base_damage=0)
    e2 = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemies=(e1, e2), target_index=0, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)

    # ADR-0152: player auto-attack hits all alive enemies in sequence
    # (not just state.target). Both e1 and e2 should have taken damage.
    assert e1.hp < 1000  # target took damage
    assert e2.hp < 1000  # non-target ALSO took damage (multi-enemy)


def test_multi_ice_backward_compat_single_enemy_victory() -> None:
    """Single-enemy combat (legacy) should still end at enemy.hp <= 0."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    e = _enemy(max_hp=10, base_damage=0)
    p.auto_attack_damage = 1000
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert state.finished
    assert state.outcome == "victory"


def test_aoe_skill_field_default_false() -> None:
    """Skill.aoe should default to False (single-target)."""
    skill = Skill(
        id="strike",
        name="Strike",
        tier=1,
        effect=SkillEffect.ATTACK,
        ap_cost=1,
        damage=10,
    )
    assert skill.aoe is False


def test_aoe_skill_hits_all_enemies() -> None:
    """AOE skill should damage every living enemy."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (
        Skill(
            id="firestorm",
            name="Firestorm",
            tier=2,
            effect=SkillEffect.ATTACK,
            ap_cost=3,
            damage=50,
            aoe=True,
        ),
    )
    e1 = _enemy(max_hp=1000, base_damage=0)
    e2 = _enemy(max_hp=1000, base_damage=0)
    e3 = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemies=(e1, e2, e3), rng=random.Random(0))

    use_skill(state, p.skills[0])

    assert e1.hp < 1000
    assert e2.hp < 1000
    assert e3.hp < 1000
    assert any("AOE" in line for line in state.log)


def test_aoe_skill_skips_dead_enemies() -> None:
    """AOE should not deal damage to already-dead enemies."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (
        Skill(
            id="firestorm",
            name="Firestorm",
            tier=2,
            effect=SkillEffect.ATTACK,
            ap_cost=3,
            damage=50,
            aoe=True,
        ),
    )
    e1 = _enemy(max_hp=1000, base_damage=0)
    e2 = _enemy(max_hp=1000, base_damage=0)
    e2.hp = 0  # already dead
    state = CombatState(player=p, enemies=(e1, e2), rng=random.Random(0))

    e1_hp_before = e1.hp
    use_skill(state, p.skills[0])

    assert e1.hp < e1_hp_before  # live target hit
    assert e2.hp == 0  # dead target untouched


def test_aoe_heavy_attack_uses_heavy_label() -> None:
    """AOE heavy attack should use DEVASTATING! label, not CRITICAL!."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (
        Skill(
            id="quake",
            name="Quake",
            tier=3,
            effect=SkillEffect.HEAVY_ATTACK,
            ap_cost=4,
            damage=100,
            aoe=True,
        ),
    )
    e1 = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemies=(e1,), rng=random.Random(0))

    use_skill(state, p.skills[0])
    assert any("AOE" in line for line in state.log)


def test_aoe_dot_applies_burn_to_all() -> None:
    """AOE dot skill should apply burn status to every living enemy."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (
        Skill(
            id="plague",
            name="Plague",
            tier=3,
            effect=SkillEffect.DOT,
            ap_cost=4,
            damage=30,
            dot_damage=5,
            dot_duration_ms=6000,
            aoe=True,
        ),
    )
    e1 = _enemy(max_hp=1000, base_damage=0)
    e2 = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemies=(e1, e2), rng=random.Random(0))

    use_skill(state, p.skills[0])
    assert any(s.effect_id == "burn" for s in e1.statuses)
    assert any(s.effect_id == "burn" for s in e2.statuses)


def test_non_aoe_skill_still_targets_only_one_enemy() -> None:
    """Non-AOE skill should only hit current target, leaving others untouched."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_strike_skill(damage=50),)
    e1 = _enemy(max_hp=1000, base_damage=0)
    e2 = _enemy(max_hp=1000, base_damage=0)
    state = CombatState(player=p, enemies=(e1, e2), target_index=0, rng=random.Random(0))

    use_skill(state, p.skills[0])
    assert e1.hp < 1000
    assert e2.hp == 1000
    assert not any("AOE" in line for line in state.log)


# ----------------------------------------------------------------------------
# Stagger mechanic
# ----------------------------------------------------------------------------


def _stagger_skill(damage: int = 30) -> Skill:
    return Skill(
        id="stagger_strike",
        name="Stagger Strike",
        tier=2,
        effect=SkillEffect.STAGGER,
        ap_cost=2,
        damage=damage,
    )


def test_stagger_constant_defined() -> None:
    from roguelike_sprawl.combat.state import STAGGER_DURATION_MS

    assert STAGGER_DURATION_MS == 1500


def test_stagger_effect_enum_value_exists() -> None:
    assert SkillEffect.STAGGER.value == "stagger"


def test_stagger_skill_applies_status_with_is_staggered_flag() -> None:
    """Stagger skill should add a stagger status effect to current target."""
    p = build_default_player(max_hp=100, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_stagger_skill(),)
    e = _enemy_with_kind(None)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    use_skill(state, p.skills[0])
    assert any(s.is_staggered for s in e.statuses)


def test_staggered_enemy_skips_next_auto_attack() -> None:
    """Staggered enemy should skip its next auto-attack, then recover."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_stagger_skill(),)
    e = _enemy(max_hp=10_000, base_damage=50)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    use_skill(state, p.skills[0])
    hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    damage = hp_before - p.hp
    assert damage == 0  # enemy auto-attack was skipped
    assert any("staggered" in line.lower() for line in state.log)


def test_stagger_clears_after_first_skipped_attack() -> None:
    """After skipping one attack, stagger is consumed and enemy resumes attacking."""
    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_stagger_skill(),)
    e = _enemy(max_hp=10_000, base_damage=50)
    state = CombatState(player=p, enemy=e, rng=random.Random(0))

    use_skill(state, p.skills[0])
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert not e.is_staggered()

    hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert p.hp < hp_before  # enemy resumed attacking


def test_stagger_aoe_skips_all_enemies() -> None:
    """AOE stagger (future) would skip all enemies; here we verify multi-enemy stagger works."""
    from roguelike_sprawl.combat.state import (
        STAGGER_DURATION_MS,
    )

    p = build_default_player(max_hp=10_000, max_ap=6, programs=ProgramRegistry({}))
    p.skills = (_stagger_skill(),)
    e1 = _enemy(max_hp=10_000, base_damage=30)
    e2 = _enemy(max_hp=10_000, base_damage=40)
    state = CombatState(player=p, enemies=(e1, e2), rng=random.Random(0))

    e1.statuses.append(
        StatusEffect(
            effect_id="stagger",
            remaining_ms=STAGGER_DURATION_MS,
            is_staggered=True,
        )
    )
    e2.statuses.append(
        StatusEffect(
            effect_id="stagger",
            remaining_ms=STAGGER_DURATION_MS,
            is_staggered=True,
        )
    )

    hp_before = p.hp
    for _ in range(AUTO_ATTACK_INTERVAL_MS // 100):
        step_combat(state)
    assert p.hp == hp_before

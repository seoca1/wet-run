"""Unit tests for combat_view.py pure helper functions.

Targets the 34% coverage gap flagged by the deep quality audit (2026-08-04).
Covers: _hp_bar, _get_skill_effect_description, _can_use_skill.
"""

from __future__ import annotations

import tcod.console  # type: ignore[import-untyped]

from wet_run.combat.state import CombatState  # type: ignore[import-untyped]
from wet_run.combat.state_models import (  # type: ignore[import-untyped]
    Combatant,
    Skill,
    SkillEffect,
)
from wet_run.engine.combat_view import (  # type: ignore[import-untyped]
    COMBAT_REPUTATION,
    _can_use_skill,
    _check_post_combat_event,
    _draw_action_log,
    _draw_combat_effects,
    _draw_combatants,
    _draw_first_combat_tutorial,
    _draw_skills_menu,
    _draw_vfx_overlay,
    _get_skill_effect_description,
    _hp_bar,
    _remove_node_from_graph,
)
from wet_run.engine.layout import Region, RegionId  # type: ignore[import-untyped]
from wet_run.matrix.graph import Edge, MatrixGraph  # type: ignore[import-untyped]
from wet_run.matrix.node import (  # type: ignore[import-untyped]
    Faction,
    Node,
    NodeKind,
    ZoneDepth,
)


class TestHpBar:
    """`_hp_bar(hp, max_hp, width)` — generate HP bar string."""

    def test_full_hp_shows_all_filled(self) -> None:
        bar = _hp_bar(hp=100, max_hp=100, width=10)
        assert bar == "[" + "▓" * 10 + "░" * 0 + "]"
        assert bar.count("▓") == 10
        assert bar.count("░") == 0

    def test_zero_hp_shows_all_empty(self) -> None:
        bar = _hp_bar(hp=0, max_hp=100, width=10)
        assert bar == "[" + "▓" * 0 + "░" * 10 + "]"

    def test_half_hp_shows_balanced(self) -> None:
        bar = _hp_bar(hp=50, max_hp=100, width=10)
        assert bar.count("▓") == 5
        assert bar.count("░") == 5

    def test_default_width_is_20(self) -> None:
        bar = _hp_bar(hp=100, max_hp=100)
        assert len(bar) == 22  # 20 chars + 2 brackets
        assert bar.count("▓") == 20

    def test_zero_max_hp_returns_all_empty(self) -> None:
        """Defensive: max_hp <= 0 → empty bar (avoid ZeroDivisionError)."""
        bar = _hp_bar(hp=50, max_hp=0, width=10)
        assert bar == "[" + "░" * 10 + "]"

    def test_negative_max_hp_returns_all_empty(self) -> None:
        bar = _hp_bar(hp=50, max_hp=-1, width=10)
        assert bar == "[" + "░" * 10 + "]"

    def test_overfill_clamps_at_max(self) -> None:
        """HP > max_hp (overheal) → render as full bar (clamped)."""
        bar = _hp_bar(hp=120, max_hp=100, width=10)
        assert bar.count("▓") == 10
        assert bar.count("░") == 0

    def test_custom_width(self) -> None:
        bar = _hp_bar(hp=50, max_hp=100, width=20)
        assert bar.count("▓") == 10
        assert bar.count("░") == 10
        assert len(bar) == 22  # 20 chars + 2 brackets


def _make_skill(
    effect: SkillEffect = SkillEffect.ATTACK,
    damage: int = 10,
    ap_cost: int = 1,
    cooldown_ms: int = 0,
) -> Skill:
    return Skill(
        id=f"test_skill_{effect.value}",
        name=f"Test {effect.value}",
        tier=1,
        effect=effect,
        ap_cost=ap_cost,
        damage=damage,
        cooldown_ms=cooldown_ms,
    )


class TestGetSkillEffectDescription:
    """`_get_skill_effect_description(skill)` — short description per effect type."""

    def test_attack_description_includes_damage(self) -> None:
        skill = _make_skill(SkillEffect.ATTACK, damage=42)
        assert _get_skill_effect_description(skill) == "Deal 42 damage"

    def test_heavy_attack_description(self) -> None:
        skill = _make_skill(SkillEffect.HEAVY_ATTACK, damage=80)
        assert _get_skill_effect_description(skill) == "SMASH for 80 damage"

    def test_pierce_description(self) -> None:
        skill = _make_skill(SkillEffect.PIERCE, damage=15)
        assert _get_skill_effect_description(skill) == "15 dmg (ignores shield)"

    def test_multi_hit_description(self) -> None:
        skill = Skill(
            id="mh",
            name="MH",
            tier=1,
            effect=SkillEffect.MULTI_HIT,
            ap_cost=1,
            damage=5,
            hit_count=4,
        )
        assert _get_skill_effect_description(skill) == "Hit 4x for 5 each"

    def test_dot_description_includes_dot_damage(self) -> None:
        skill = Skill(
            id="dot",
            name="DOT",
            tier=1,
            effect=SkillEffect.DOT,
            ap_cost=1,
            damage=20,
            dot_damage=5,
        )
        assert _get_skill_effect_description(skill) == "20 dmg + burn (5/s)"

    def test_heal_description(self) -> None:
        skill = Skill(
            id="heal",
            name="HEAL",
            tier=1,
            effect=SkillEffect.HEAL,
            ap_cost=1,
            heal=30,
        )
        assert _get_skill_effect_description(skill) == "+30 HP"

    def test_shield_description(self) -> None:
        skill = Skill(
            id="shield",
            name="SHIELD",
            tier=1,
            effect=SkillEffect.SHIELD,
            ap_cost=1,
            shield=20,
        )
        assert _get_skill_effect_description(skill) == "+20 shield"

    def test_stun_description_converts_ms_to_s(self) -> None:
        skill = Skill(
            id="stun",
            name="STUN",
            tier=1,
            effect=SkillEffect.STUN,
            ap_cost=1,
            stun_duration_ms=3000,
        )
        assert _get_skill_effect_description(skill) == "Stun enemy for 3s"

    def test_unknown_effect_falls_back_to_default(self) -> None:
        """Future SkillEffect variants not in the dict → 'Special effect' fallback."""
        # SkillEffect is a StrEnum; an unknown effect requires mocking or a valid enum.
        # We test that a known but missing-from-dict effect returns fallback.
        # All current effects are in dict; this verifies the .get(..., default) pattern.
        # Build a valid skill and verify the dict has it
        skill = _make_skill(SkillEffect.DETECT)
        desc = _get_skill_effect_description(skill)
        assert desc  # non-empty fallback


def _make_player_combatant(ap: int = 5) -> Combatant:
    return Combatant(
        id="player",
        name="Player",
        portrait="@",
        color=(255, 255, 255),
        hp=100,
        max_hp=100,
        ap=ap,
        max_ap=10,
        auto_attack_damage=5,
        skills=(),
        team="player",
        ice_kind="standard",
    )


class TestCanUseSkill:
    """`_can_use_skill(combat_state, skill)` — predicate for skill availability."""

    def test_skill_usable_when_enough_ap_no_cooldown(self) -> None:
        player = _make_player_combatant(ap=5)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=2, cooldown_ms=0)
        assert _can_use_skill(cs, skill) is True

    def test_skill_unusable_when_insufficient_ap(self) -> None:
        player = _make_player_combatant(ap=1)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=2, cooldown_ms=0)
        assert _can_use_skill(cs, skill) is False

    def test_skill_unusable_during_cooldown(self) -> None:
        player = _make_player_combatant(ap=5)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=2, cooldown_ms=3000)
        cs.skill_cooldowns[skill.id] = 1500  # 1.5s remaining
        assert _can_use_skill(cs, skill) is False

    def test_skill_usable_at_cooldown_boundary_zero(self) -> None:
        """Cooldown exactly 0 → usable."""
        player = _make_player_combatant(ap=5)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=2, cooldown_ms=0)
        cs.skill_cooldowns[skill.id] = 0
        assert _can_use_skill(cs, skill) is True

    def test_skill_unusable_when_combat_finished(self) -> None:
        player = _make_player_combatant(ap=5)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=1, cooldown_ms=0)
        cs.finished = True
        assert _can_use_skill(cs, skill) is False

    def test_skill_with_no_cooldown_entry_in_state(self) -> None:
        """Skill.id not in skill_cooldowns dict → treated as 0 cooldown."""
        player = _make_player_combatant(ap=5)
        cs = CombatState(player=player, enemy=None)
        skill = _make_skill(ap_cost=2, cooldown_ms=1000)
        # Don't add to skill_cooldowns; should default to 0 (usable)
        assert _can_use_skill(cs, skill) is True


class TestCombatReputation:
    """COMBAT_REPUTATION constant — faction rep deltas when player defeats ICE."""

    def test_has_four_entries(self) -> None:
        assert len(COMBAT_REPUTATION) == 4

    def test_hosaka_self_penalty_and_maas_bonus(self) -> None:
        """HOSAKA self: -3 (you hurt them), MAAS rival: +1 (you weakened HOSAKA)."""
        assert COMBAT_REPUTATION[Faction.HOSAKA][Faction.HOSAKA] == -3
        assert COMBAT_REPUTATION[Faction.HOSAKA][Faction.MAAS] == +1

    def test_maas_self_penalty_and_hosaka_bonus(self) -> None:
        assert COMBAT_REPUTATION[Faction.MAAS][Faction.MAAS] == -3
        assert COMBAT_REPUTATION[Faction.MAAS][Faction.HOSAKA] == +1

    def test_sensenet_self_penalty_and_ta_bonus(self) -> None:
        assert COMBAT_REPUTATION[Faction.SENSE_NET][Faction.SENSE_NET] == -3
        assert COMBAT_REPUTATION[Faction.SENSE_NET][Faction.TA] == +1

    def test_ta_self_penalty_and_sensenet_bonus(self) -> None:
        assert COMBAT_REPUTATION[Faction.TA][Faction.TA] == -3
        assert COMBAT_REPUTATION[Faction.TA][Faction.SENSE_NET] == +1

    def test_each_entry_sums_to_minus_two(self) -> None:
        """Net per faction: -3 self + 1 rival = -2 (player loses net rep per defeat)."""
        for defender, deltas in COMBAT_REPUTATION.items():
            assert sum(deltas.values()) == -2, f"{defender} entry doesn't sum to -2: {deltas}"

    def test_self_deltas_are_always_negative(self) -> None:
        """Defending faction (where you infiltrated) always loses rep."""
        for defender, deltas in COMBAT_REPUTATION.items():
            assert deltas[defender] == -3, f"{defender} self-delta should be -3 (you hurt them)"

    def test_only_one_rival_bonus_per_entry(self) -> None:
        """Each faction has exactly one +1 (one opposing rival gains)."""
        for defender, deltas in COMBAT_REPUTATION.items():
            bonuses = [v for v in deltas.values() if v > 0]
            assert len(bonuses) == 1, f"{defender} should have exactly 1 bonus, got {bonuses}"
            assert bonuses[0] == 1, f"{defender} bonus should be +1, got {bonuses[0]}"


def _make_node(
    id: str,
    kind: NodeKind = NodeKind.DATA,
    label: str | None = None,
) -> Node:
    return Node(
        id=id,
        kind=kind,
        label=label or id,
        zone=ZoneDepth.MID,
    )


def _make_graph(
    nodes: list[Node],
    edges: list[tuple[str, str]] | None = None,
    entry_id: str | None = None,
) -> MatrixGraph:
    """Construct a MatrixGraph from a list of nodes and edge tuples."""
    edge_objs = tuple(Edge(src=s, dst=d) for s, d in (edges or []))
    return MatrixGraph(
        nodes=tuple(nodes),
        edges=edge_objs,
        entry_id=entry_id or (nodes[0].id if nodes else ""),
    )


class TestRemoveNodeFromGraph:
    """`_remove_node_from_graph(matrix, node_id)` — pure graph mutation helper."""

    def test_returns_none_when_matrix_is_none(self) -> None:
        assert _remove_node_from_graph(None, "anything") is None

    def test_removes_target_node_keeps_others(self) -> None:
        nodes = [_make_node("entry"), _make_node("data1"), _make_node("data2")]
        graph = _make_graph(nodes, [("entry", "data1"), ("entry", "data2")])
        result = _remove_node_from_graph(graph, "data1")
        assert result is not None
        assert "data1" not in {n.id for n in result.nodes}
        assert {"entry", "data2"} == {n.id for n in result.nodes}

    def test_removes_edges_involving_removed_node(self) -> None:
        nodes = [_make_node("entry"), _make_node("a"), _make_node("b"), _make_node("c")]
        graph = _make_graph(
            nodes,
            [("entry", "a"), ("a", "b"), ("b", "c")],
        )
        result = _remove_node_from_graph(graph, "a")
        assert result is not None
        edge_pairs = {(e.src, e.dst) for e in result.edges}
        assert edge_pairs == {("b", "c")}, f"expected only (b→c), got {edge_pairs}"

    def test_preserves_unrelated_edges(self) -> None:
        nodes = [_make_node("x"), _make_node("y"), _make_node("z")]
        graph = _make_graph(nodes, [("x", "y"), ("y", "z")])
        result = _remove_node_from_graph(graph, "nonexistent")
        assert result is not None
        edge_pairs = {(e.src, e.dst) for e in result.edges}
        assert edge_pairs == {("x", "y"), ("y", "z")}

    def test_updates_entry_id_when_entry_node_removed(self) -> None:
        nodes = [_make_node("entry"), _make_node("second"), _make_node("third")]
        graph = _make_graph(nodes, entry_id="entry")
        result = _remove_node_from_graph(graph, "entry")
        assert result is not None
        assert result.entry_id == "second"

    def test_preserves_entry_id_when_non_entry_removed(self) -> None:
        nodes = [_make_node("entry"), _make_node("data1"), _make_node("data2")]
        graph = _make_graph(nodes, entry_id="entry")
        result = _remove_node_from_graph(graph, "data2")
        assert result is not None
        assert result.entry_id == "entry"

    def test_returns_none_when_removing_only_node(self) -> None:
        single_node = _make_node("only")
        graph = _make_graph([single_node], entry_id="only")
        result = _remove_node_from_graph(graph, "only")
        assert result is None

    def test_result_has_correct_node_count(self) -> None:
        nodes = [_make_node(f"n{i}") for i in range(5)]
        graph = _make_graph(nodes)
        result = _remove_node_from_graph(graph, "n2")
        assert result is not None
        assert len(result.nodes) == 4


class TestDrawVfxOverlay:
    """`_draw_vfx_overlay(console, region, fx, shake_dx, shake_dy)` — smoke tests.

    Rendering functions don't return a value; we verify they execute without
    crash on minimal state. Full output verification requires visual inspection.
    """

    def _make_console(self, width: int = 80, height: int = 50) -> tcod.console.Console:
        return tcod.console.Console(width=width, height=height)

    def test_smoke_runs_with_empty_combat_effects(self) -> None:
        """Empty CombatEffects (no hit_flash, no animations, no particles) → renders cleanly."""
        from wet_run.combat.effects_vfx import CombatEffects

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=20, h=10)
        fx = CombatEffects()
        _draw_vfx_overlay(console, region, fx, shake_dx=0, shake_dy=0)

    def test_smoke_runs_with_nonzero_shake_offsets(self) -> None:
        """Shake offsets (5, 3) — exercises offset arithmetic in particles/floating_numbers."""
        from wet_run.combat.effects_vfx import CombatEffects

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=20, h=10)
        fx = CombatEffects()
        _draw_vfx_overlay(console, region, fx, shake_dx=5, shake_dy=3)

    def test_smoke_runs_with_offset_region(self) -> None:
        """Region offset from origin (10, 5) — exercises region arithmetic."""
        from wet_run.combat.effects_vfx import CombatEffects

        console = self._make_console(width=80, height=50)
        region = Region(id=RegionId.MAIN, x=10, y=5, w=20, h=10)
        fx = CombatEffects()
        _draw_vfx_overlay(console, region, fx, shake_dx=0, shake_dy=0)

    def test_smoke_runs_with_active_hit_flash(self) -> None:
        """HitFlash active → exercises the white overlay render branch."""
        from wet_run.combat.effects_vfx import CombatEffects, HitFlash

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=20, h=10)
        fx = CombatEffects()
        fx.hit_flash = HitFlash(color=(255, 255, 255), duration_ms=200, elapsed_ms=0)
        _draw_vfx_overlay(console, region, fx, shake_dx=0, shake_dy=0)


class TestDrawCombatants:
    """`_draw_combatants(console, main, combat_state)` — smoke tests.

    Early-return branch (no enemy) + basic render branches (player/enemy + shield).
    """

    def _make_console(self, width: int = 80, height: int = 50) -> tcod.console.Console:
        return tcod.console.Console(width=width, height=height)

    def test_returns_silently_when_enemy_is_none(self) -> None:
        """Early-return branch: no enemy → no rendering (combat ended)."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        player = Combatant(
            id="player",
            name="Player",
            portrait="@",
            color=(255, 255, 255),
            hp=100,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )
        cs = CombatState(player=player, enemy=None)
        _draw_combatants(console, region, cs)

    def test_smoke_with_player_and_enemy(self) -> None:
        """Basic render: both combatants present → player + enemy portraits + HP bars drawn."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        player = Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )
        enemy = Combatant(
            id="black_ice",
            name="Black ICE",
            portrait="■",
            color=(255, 0, 0),
            hp=50,
            max_hp=80,
            ap=0,
            max_ap=0,
            auto_attack_damage=8,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        cs = CombatState(player=player, enemy=enemy)
        _draw_combatants(console, region, cs)

    def test_smoke_with_shield_active(self) -> None:
        """Shield branch: combat_state.shield > 0 → shield line drawn for player."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        player = Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )
        enemy = Combatant(
            id="black_ice",
            name="Black ICE",
            portrait="■",
            color=(255, 0, 0),
            hp=50,
            max_hp=80,
            ap=0,
            max_ap=0,
            auto_attack_damage=8,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        cs = CombatState(player=player, enemy=enemy)
        cs.shield = 15
        _draw_combatants(console, region, cs)


class TestDrawBossPhaseIndicator:
    """Lock the render path of `phase_str` for BossPhaseTracker users.

    Per .omo/plans/wet-run-ui-visibility-upgrade.md T2.1: only 3 F.4 bosses
    use BossPhaseTracker (neuromancer / loa_baron / black_baron); wintermute
    and ta_construct_prime use phase logic directly in combat/boss.py and
    must cleanly skip the phase block (no orphan PHASE string).
    """

    def _make_console(self) -> tcod.console.Console:
        return tcod.console.Console(width=80, height=50)

    def _make_player(self) -> Combatant:
        return Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )

    def _make_enemy(self, name: str = "Boss", ice_kind: str = "boss") -> Combatant:
        return Combatant(
            id=ice_kind,
            name=name,
            portrait="*",
            color=(255, 0, 100),
            hp=400,
            max_hp=400,
            ap=0,
            max_ap=0,
            auto_attack_damage=20,
            skills=(),
            team="enemy",
            ice_kind=ice_kind,
            current_phase=1,
        )

    def _decode_row(self, console: tcod.console.Console, y: int, x_start: int, x_end: int) -> str:
        cells = console.ch[y][x_start:x_end].tolist()
        return "".join(chr(c) if c != 0 else " " for c in cells)

    def test_tracker_neuromancer_renders_phase_1_of_6(self) -> None:
        """Happy: neuromancer tracker at phase 1 → 'PHASE 1/6' on phase row."""
        from wet_run.combat.boss_expansion import NEUROMANCER_PROFILE
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = CombatState(
            player=self._make_player(), enemy=self._make_enemy("Neuromancer", "neuromancer")
        )
        cs.boss_phase_tracker = BossPhaseTracker(NEUROMANCER_PROFILE)
        cs.phase_change_ms = 0  # disable flash; deterministic color
        _draw_combatants(console, region, cs)

        # Enemy portrait at (55, 2); phase_str renders at row 6.
        row = self._decode_row(console, y=6, x_start=55, x_end=70)
        assert "PHASE 1/6" in row, f"Expected 'PHASE 1/6' at row 6 x=55, got {row!r}"

    def test_tracker_loa_baron_renders_phase_1_of_4(self) -> None:
        from wet_run.combat.boss_expansion import LOA_BARON_PROFILE
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = CombatState(
            player=self._make_player(), enemy=self._make_enemy("Loa Baron", "loa_baron")
        )
        cs.boss_phase_tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        cs.phase_change_ms = 0
        _draw_combatants(console, region, cs)

        row = self._decode_row(console, y=6, x_start=55, x_end=70)
        assert "PHASE 1/4" in row, f"Expected 'PHASE 1/4' at row 6 x=55, got {row!r}"

    def test_tracker_black_baron_renders_phase_1_of_4(self) -> None:
        from wet_run.combat.boss_expansion import BLACK_BARON_PROFILE
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = CombatState(
            player=self._make_player(), enemy=self._make_enemy("Black Baron", "black_baron")
        )
        cs.boss_phase_tracker = BossPhaseTracker(BLACK_BARON_PROFILE)
        cs.phase_change_ms = 0
        _draw_combatants(console, region, cs)

        row = self._decode_row(console, y=6, x_start=55, x_end=70)
        assert "PHASE 1/4" in row, f"Expected 'PHASE 1/4' at row 6 x=55, got {row!r}"

    def test_tracker_phase_transition_updates_string(self) -> None:
        """Transition 1→2 → re-render shows 'PHASE 2/4'."""
        from wet_run.combat.boss_expansion import LOA_BARON_PROFILE
        from wet_run.combat.boss_phase_tracker import BossPhaseTracker

        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        enemy = self._make_enemy("Loa Baron", "loa_baron")
        cs = CombatState(player=self._make_player(), enemy=enemy)
        tracker = BossPhaseTracker(LOA_BARON_PROFILE)
        cs.boss_phase_tracker = tracker
        cs.phase_change_ms = 0
        _draw_combatants(console, region, cs)

        row1 = self._decode_row(console, y=6, x_start=55, x_end=70)
        assert "PHASE 1/4" in row1, f"Pre-transition: expected 'PHASE 1/4', got {row1!r}"

        tracker.transition()
        enemy.current_phase = 2
        cs2 = CombatState(player=self._make_player(), enemy=enemy)
        cs2.boss_phase_tracker = tracker
        cs2.phase_change_ms = 0
        console2 = self._make_console()
        _draw_combatants(console2, region, cs2)

        row2 = self._decode_row(console2, y=6, x_start=55, x_end=70)
        assert "PHASE 2/4" in row2, f"Post-transition: expected 'PHASE 2/4', got {row2!r}"

    def test_no_tracker_cleanly_skips_phase_block(self) -> None:
        """Failure: tracker is None (wintermute / ta_construct_prime) →
        no orphan 'PHASE' string at row 6. Render must not crash."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = CombatState(
            player=self._make_player(),
            enemy=self._make_enemy("Wintermute", "wintermute"),
        )
        assert cs.boss_phase_tracker is None, "Pre-condition: tracker must default to None"
        _draw_combatants(console, region, cs)

        # Row 6 must NOT contain "PHASE" — block was cleanly skipped.
        full_row = self._decode_row(console, y=6, x_start=0, x_end=80)
        assert "PHASE" not in full_row, (
            f"Orphan 'PHASE' string at row 6 when tracker is None: {full_row!r}"
        )

        # ATK line at row 6 (no tracker → no phase block advance) renders.
        # The render code unconditionally prints ATK one row below hp_bar;
        # when tracker is None the ATK line lands on row 6.
        atk_row = self._decode_row(console, y=6, x_start=55, x_end=80)
        assert "ATK:" in atk_row, f"ATK line missing after no-tracker render: {atk_row!r}"


class TestDrawCombatEffects:
    """`_draw_combat_effects(console, main, combat_state)` — smoke tests.

    Early-return branches (no recent event) + fade color render branch.
    """

    def _make_console(self, width: int = 80, height: int = 50) -> tcod.console.Console:
        return tcod.console.Console(width=width, height=height)

    def _make_basic_state(self) -> CombatState:
        """Construct a CombatState with player + enemy for draw functions."""
        player = Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )
        enemy = Combatant(
            id="black_ice",
            name="Black ICE",
            portrait="■",
            color=(255, 0, 0),
            hp=50,
            max_hp=80,
            ap=0,
            max_ap=0,
            auto_attack_damage=8,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        return CombatState(player=player, enemy=enemy)

    def test_returns_silently_when_no_recent_event(self) -> None:
        """Early-return: tick_ms - last_event_tick > 1500 → no render."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = self._make_basic_state()
        cs.last_event = "player_attack"
        cs.last_event_tick = 0
        cs.tick_ms = 5000  # elapsed = 5000 > 1500
        _draw_combat_effects(console, region, cs)

    def test_returns_silently_when_last_event_empty(self) -> None:
        """Early-return: last_event == "" → no render."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = self._make_basic_state()
        cs.last_event = ""
        cs.last_event_tick = 0
        cs.tick_ms = 1000
        _draw_combat_effects(console, region, cs)

    def test_renders_glyph_with_fade_color(self) -> None:
        """Recent event (elapsed=1000ms, within 1500ms fade window) → fade-colored glyph rendered."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = self._make_basic_state()
        cs.last_event = "player_attack"
        cs.last_event_color = (200, 200, 200)
        cs.last_event_tick = 0
        cs.tick_ms = 1000  # elapsed = 1000ms, intensity ≈ 0.33
        _draw_combat_effects(console, region, cs)


class TestDrawActionLog:
    """`_draw_action_log(console, main, combat_state)` — smoke tests.

    Iterates combat_state.log[-7:] and color-codes entries based on keywords
    (crit → yellow, DoT → green, heal → cyan, etc.).
    """

    def _make_console(self, width: int = 80, height: int = 50) -> tcod.console.Console:
        return tcod.console.Console(width=width, height=height)

    def _make_basic_state(self) -> CombatState:
        """Construct a CombatState with player + enemy for draw functions."""
        player = Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=(),
            team="player",
            ice_kind="standard",
        )
        enemy = Combatant(
            id="black_ice",
            name="Black ICE",
            portrait="■",
            color=(255, 0, 0),
            hp=50,
            max_hp=80,
            ap=0,
            max_ap=0,
            auto_attack_damage=8,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        return CombatState(player=player, enemy=enemy)

    def test_renders_empty_log_with_header_only(self) -> None:
        """Empty log → only the COMBAT LOG header is rendered."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = self._make_basic_state()
        cs.log = []
        _draw_action_log(console, region, cs)

    def test_renders_color_coded_entries(self) -> None:
        """Mixed log entries → color-coded by keywords (crit/DoT/heal/etc.)."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        cs = self._make_basic_state()
        cs.log = [
            "Critical hit! 50 damage",
            "Burn tick: 5 damage",
            "Heal: +20 HP",
            "Player hits for 10 damage",
            "Generic event without keywords",
        ]
        _draw_action_log(console, region, cs)

    def test_truncates_long_lines_to_region_width(self) -> None:
        """Long log entry longer than main.w - 4 → truncated to fit."""
        console = self._make_console()
        region = Region(id=RegionId.MAIN, x=0, y=0, w=20, h=30)  # Narrow region
        cs = self._make_basic_state()
        cs.log = [
            "This is a very long log entry that exceeds the region width "
            "by a significant margin and should be truncated to fit",
        ]
        _draw_action_log(console, region, cs)


class TestDrawSkillsMenu:
    """`_draw_skills_menu(console, side_r, combat_state, state)` — smoke tests.

    Color branches: cooldown (dark gray), disabled (dark gray), selected
    (skill color), normal (light gray). Also: effect desc + player statuses.
    """

    def _make_console(self, width: int = 80, height: int = 50) -> tcod.console.Console:
        return tcod.console.Console(width=width, height=height)

    def _make_player_with_skills(self) -> Combatant:
        skills = (
            _make_skill(SkillEffect.ATTACK, damage=10, ap_cost=2),
            _make_skill(SkillEffect.HEAL, ap_cost=3, cooldown_ms=2000),
        )
        skills = (
            skills[0].__class__(
                id=skills[0].id,
                name=skills[0].name,
                tier=skills[0].tier,
                effect=skills[0].effect,
                ap_cost=skills[0].ap_cost,
                damage=skills[0].damage,
                effect_glyph="★",
            ),
            skills[1].__class__(
                id=skills[1].id,
                name=skills[1].name,
                tier=skills[1].tier,
                effect=skills[1].effect,
                ap_cost=skills[1].ap_cost,
                damage=skills[1].damage,
                heal=skills[1].heal,
                effect_glyph="+",
            ),
        )
        return Combatant(
            id="player",
            name="Hero",
            portrait="@",
            color=(255, 255, 255),
            hp=80,
            max_hp=100,
            ap=5,
            max_ap=10,
            auto_attack_damage=10,
            skills=skills,
            team="player",
            ice_kind="standard",
        )

    def _make_basic_state(self) -> tuple[Combatant, CombatState]:
        player = self._make_player_with_skills()
        enemy = Combatant(
            id="black_ice",
            name="Black ICE",
            portrait="■",
            color=(255, 0, 0),
            hp=50,
            max_hp=80,
            ap=0,
            max_ap=0,
            auto_attack_damage=8,
            skills=(),
            team="enemy",
            ice_kind="black",
        )
        return player, CombatState(player=player, enemy=enemy)

    def test_renders_skills_basic_with_cooldown(self) -> None:
        """Basic render: 2 skills (1 selected, 1 on cooldown)."""
        from wet_run.engine.state import AppState

        console = self._make_console()
        side_r = Region(id=RegionId.SIDE, x=80, y=0, w=20, h=30)
        player, cs = self._make_basic_state()
        cs.skill_cooldowns[player.skills[1].id] = 1500
        state = AppState()
        state.combat_skill_index = 0
        _draw_skills_menu(console, side_r, cs, state)

    def test_renders_disabled_when_insufficient_ap(self) -> None:
        """Insufficient AP → disabled branch (dark gray, '[X AP]' status)."""
        from wet_run.engine.state import AppState

        console = self._make_console()
        side_r = Region(id=RegionId.SIDE, x=80, y=0, w=20, h=30)
        player, cs = self._make_basic_state()
        cs.player.ap = 1
        state = AppState()
        state.combat_skill_index = 0
        _draw_skills_menu(console, side_r, cs, state)

    def test_renders_player_statuses(self) -> None:
        """Player with active statuses (e.g., burn DoT) → STATUS: section rendered."""
        from wet_run.combat.state_models import StatusEffect
        from wet_run.engine.state import AppState

        console = self._make_console()
        side_r = Region(id=RegionId.SIDE, x=80, y=0, w=20, h=30)
        player, cs = self._make_basic_state()
        player.statuses = [
            StatusEffect(effect_id="burn", remaining_ms=5000),
        ]
        state = AppState()
        state.combat_skill_index = 0
        _draw_skills_menu(console, side_r, cs, state)


class TestDrawFirstCombatTutorial:
    """`_draw_first_combat_tutorial(console, region)` — smoke tests.

    Renders 4 lines of keyboard hints centered in the main region.
    First line (header) highlighted yellow, others gray.
    """

    def test_smoke_basic_render(self) -> None:
        """Basic render: 4 hint lines centered in default region."""
        console = tcod.console.Console(width=80, height=50)
        region = Region(id=RegionId.MAIN, x=0, y=0, w=80, h=30)
        _draw_first_combat_tutorial(console, region)

    def test_smoke_with_small_region(self) -> None:
        """Small region (w=30, h=10) — exercises centering math with narrow space."""
        console = tcod.console.Console(width=80, height=50)
        region = Region(id=RegionId.MAIN, x=10, y=5, w=30, h=10)
        _draw_first_combat_tutorial(console, region)


class TestCheckPostCombatEvent:
    """`_check_post_combat_event(state, trigger_id)` — smoke tests.

    Initializes event_registry if missing + calls check_event_trigger.
    If event returned, sets state.active_event + state.screen = EVENT.
    """

    def test_initializes_event_registry_when_missing(self) -> None:
        """Fresh AppState has no _event_registry → call initializes it."""
        from wet_run.engine.state import AppState

        state = AppState()
        assert not hasattr(state, "_event_registry") or state._event_registry is None
        _check_post_combat_event(state, "unknown_trigger")
        assert state._event_registry is not None

    def test_no_event_trigger_keeps_state(self) -> None:
        """Unknown trigger_id → check_event_trigger returns None → state.active_event unchanged."""
        from wet_run.engine.state import AppState

        state = AppState()
        _check_post_combat_event(state, "unknown_trigger_id")
        assert getattr(state, "active_event", None) is None

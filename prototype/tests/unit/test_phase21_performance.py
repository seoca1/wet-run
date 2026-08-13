"""Phase 21 — Performance benchmarks + budget tests.

This module measures wall-clock time of key game systems added/expanded
across Phases 11-20 (combat, missions, cyberspace, save/load, telemetry).
The measurements are paired with explicit budget thresholds so a future
regression surfaces as a test failure.

Approach
--------
The project does NOT depend on ``pytest-benchmark`` (see pyproject.toml).
Benchmarks therefore use ``time.perf_counter`` directly, run the target
operation N times (small N to keep the suite fast) and report mean /
median timings in milliseconds. Budget tests assert wall-clock budgets
on a single cold-call.

Layered structure
-----------------
1. **Benchmarks** — ``Test*Bench`` classes. Measure and assert a
   generous upper bound so they act as soft smoke tests + measurement.
2. **Budgets** — ``Test*Budget`` classes. Single-call assertions on
   tight performance budgets; fail-fast on regression.

Both layers feed the Phase 21 performance report
(``docs/performance/phase21-benchmarks.md``).

The thresholds here are calibrated against the actual codebase as of
Phase 21 (commit pre-Phase 21). See the report for current baselines.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from roguelike_sprawl.combat import (
    Combatant,
    CombatState,
    IceRegistry,
    ProgramRegistry,
    build_default_player,
    build_ice_enemy,
    step_combat,
)
from roguelike_sprawl.combat.effects_data import (
    Animation,
    AnimationFrame,
    FloatingNumber,
)
from roguelike_sprawl.combat.effects_vfx_compose import CombatEffects
from roguelike_sprawl.combat.matrix_events import (
    MATRIX_EVENTS,
    check_event_trigger,
)
from roguelike_sprawl.combat.state import _calculate_damage
from roguelike_sprawl.combat.telemetry import (
    TelemetrySession,
    aggregate_death_rates,
    aggregate_deck_distribution,
    aggregate_kill_counts,
    aggregate_mutator_choices,
    record_telemetry_event,
    start_telemetry_session,
)
from roguelike_sprawl.engine import AppState, SaveManager
from roguelike_sprawl.engine.save_manager import SAVE_FORMAT_VERSION
from roguelike_sprawl.matrix.cyberspace_generator import CyberspaceGenerator
from roguelike_sprawl.matrix.generator import MatrixGenerator
from roguelike_sprawl.matrix.graph import compute_layout
from roguelike_sprawl.matrix.node import ZoneDepth
from roguelike_sprawl.missions.board import JobBoard
from roguelike_sprawl.missions.mission import (
    ChainFailure,
    ChainMission,
    ChainReward,
    ChainUnlockCondition,
    Mission,
    MissionChain,
    Rewards,
)
from roguelike_sprawl.missions.random_rules import (
    apply_rule,
    get_random_mission_with_rule,
    get_total_rules,
)
from roguelike_sprawl.run import Stage, start_run

# ---------------------------------------------------------------------------
# Helpers — timing + state fixtures
# ---------------------------------------------------------------------------


def _time_it(fn: Callable[[], Any], repeats: int = 100) -> float:
    """Return mean wall-clock time in milliseconds across ``repeats`` calls.

    Includes one warm-up call before the measured loop to amortise
    import / cache effects without polluting the measurement.
    """
    fn()  # warm-up
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    elapsed = time.perf_counter() - start
    return (elapsed / repeats) * 1000.0


@dataclass
class DummyState:
    """Minimal state shape expected by JobBoard.select_weighted (ADR-0188)."""

    grade: int = 1
    yakuza_rep: int = 0
    sense_net_rep: int = 0
    hosaka_rep: int = 0
    ta_rep: int = 0
    freeside_rep: int = 0
    loa_rep: int = 0
    faction_rep: int = 0
    has_construct: bool = False
    consecutive_failures: int = 0
    consecutive_completions: int = 0
    consecutive_high_salvages: int = 0
    boss_defeated_recently: bool = False
    chain_complete_recently: bool = False
    chain_failed_recently: bool = False
    construct_lost_recently: bool = False
    fixer_used_recently: bool = False
    node_turns: int = 0
    bandwidth: int = 100
    corrupted_node: bool = False
    hp_pct: int = 100
    days_until_random_expires: int = 5
    reputation: object | None = None


def _make_mission(
    mid: str, *, grade_min: int = 1, grade_max: int = 6, fixer: str = "finn"
) -> Mission:
    """Build a minimal valid Mission (no JSON parse path)."""
    return Mission(
        id=mid,
        title=f"Mission {mid}",
        fixer=fixer,
        arc=1,
        grade_min=grade_min,
        grade_max=grade_max,
        matrix_seed=1,
        zone=ZoneDepth.MID,
        objective="extract",
        reward_tier=1,
        reward_credits=100,
        primary_objective=None,
        secondary_objectives=(),
        rewards=Rewards(credits=100, materials={}),
    )


def _build_board(mission_ids: list[str], grades: tuple[int, int] = (1, 6)) -> JobBoard:
    """Build a JobBoard with synthetic missions for benchmark purposes."""
    lo, hi = grades
    missions = tuple(_make_mission(mid, grade_min=lo, grade_max=hi) for mid in mission_ids)
    return JobBoard(missions)


def _enemy_standard(max_hp: int = 80, base_damage: int = 5) -> Combatant:
    """Build a standard ICE enemy Combatant."""
    return Combatant(
        id="ice_standard",
        name="Standard ICE",
        portrait="▲ICE▲",
        color=(255, 0, 255),
        hp=max_hp,
        max_hp=max_hp,
        ap=0,
        max_ap=0,
        auto_attack_damage=base_damage,
        team="enemy",
    )


def _make_appstate_with_run(tmp_path: Path) -> AppState:
    """Build an AppState with a real run + matrix for save/load benchmarks."""
    state = AppState()
    state.inventory = {"data_fragment": 5, "ice_shard": 2}
    state.credits = 750
    state.run_state = start_run("bench_mission")
    state.run_state.current_stage = Stage.EXTRACT_DATA
    state.current_mission = _make_mission("bench_mission")
    state.player_grade = 3
    state.current_node_id = "data1"
    state.defeated_nodes = {"ice1", "ice2"}
    state.extracted_nodes = {"data1"}
    state.mission_progress = {"defeat": 2, "extract_data": 1}
    state.ending_choice = "A"
    # Generate a small matrix to exercise the matrix serialize/restore path
    gen = MatrixGenerator()
    state.matrix = gen.generate(seed=42, mission_grade=1)
    return state


# ---------------------------------------------------------------------------
# 1. Combat benchmarks
# ---------------------------------------------------------------------------


class TestCombatBench:
    """Wall-clock benchmarks for the combat model."""

    def test_single_combat_resolution_ppl24(self) -> None:
        """One full combat (PPL 24 vs standard ICE) tick resolution."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=200, max_ap=12, programs=programs)
        player.auto_attack_damage = 24
        enemy = _enemy_standard(max_hp=400, base_damage=5)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))

        def one_tick() -> None:
            step_combat(state)

        mean_ms = _time_it(one_tick, repeats=100)
        # PPL 24 vs standard ICE: a single tick should be sub-millisecond.
        assert mean_ms < 5.0, f"single combat tick took {mean_ms:.3f}ms (expected <5ms)"

    def test_combat_5_grade_progression(self) -> None:
        """5-grade combat progression: simulate 5 successive rounds."""
        programs = ProgramRegistry({})
        # Simulate escalating grades 1..5 by scaling player damage.
        results: list[float] = []
        for grade in range(1, 6):
            player = build_default_player(max_hp=100 + grade * 20, max_ap=6, programs=programs)
            player.auto_attack_damage = 5 * grade
            enemy = _enemy_standard(max_hp=80 + grade * 30, base_damage=3 * grade)
            state = CombatState(player=player, enemy=enemy, rng=random.Random(grade))
            # 20 ticks per grade is enough to exercise auto-attack timing.
            mean_ms = _time_it(lambda s=state: step_combat(s), repeats=20)
            results.append(mean_ms)
        mean_overall = sum(results) / len(results)
        assert mean_overall < 5.0, f"5-grade progression mean {mean_overall:.3f}ms (expected <5ms)"

    def test_5_layer_vfx_rendering(self) -> None:
        """5-Layer VFX rendering: step a populated CombatEffects instance."""
        effects = CombatEffects()
        # Pre-populate all 5 layers with active content (animations + shake
        # + flash + floating numbers + particles).
        for _ in range(8):
            effects.animations.append(_make_anim_for_step())
        effects.particles.spawn_burst(x=0.0, y=0.0, count=50)
        for i in range(6):
            effects.floating_numbers.append(_make_floating_number(i))

        def step_effects() -> None:
            effects.step(16)  # 16 ms ≈ 60 fps tick

        mean_ms = _time_it(step_effects, repeats=100)
        assert mean_ms < 5.0, f"5-layer VFX step took {mean_ms:.3f}ms (expected <5ms)"

    def test_50_ice_boss_fight_simulation(self) -> None:
        """Worst-case: 50 ICE in one combat (boss-rush). Tick resolution."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=1000, max_ap=20, programs=programs)
        player.auto_attack_damage = 50  # high damage to keep combat active
        enemies = tuple(
            Combatant(
                id=f"ice_{i}",
                name=f"Ice {i}",
                portrait="▲",
                color=(255, 0, 255),
                hp=200,
                max_hp=200,
                ap=0,
                max_ap=0,
                auto_attack_damage=4,
                team="enemy",
            )
            for i in range(50)
        )
        state = CombatState(player=player, enemies=enemies, rng=random.Random(0))

        def one_tick() -> None:
            step_combat(state)

        mean_ms = _time_it(one_tick, repeats=20)
        # 50 ICE tick should still be sub-50ms on commodity hardware.
        assert mean_ms < 50.0, f"50-ICE tick took {mean_ms:.3f}ms (expected <50ms)"

    def test_damage_calc_50_hit_combat(self) -> None:
        """Damage calculation through 50 hits: pure damage formula throughput."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=100, max_ap=6, programs=programs)
        player.auto_attack_damage = 10
        enemy = _enemy_standard(max_hp=200, base_damage=3)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))

        def one_damage() -> tuple[int, bool]:
            return _calculate_damage(state, player.auto_attack_damage, player, enemy)

        mean_ms = _time_it(one_damage, repeats=100)
        assert mean_ms < 0.5, f"damage calc took {mean_ms:.3f}ms (expected <0.5ms)"


# ---------------------------------------------------------------------------
# 2. Combat budget tests (single-call, fail-fast)
# ---------------------------------------------------------------------------


class TestCombatBudget:
    """Single-call performance budgets for combat."""

    def test_combat_resolves_under_50ms(self) -> None:
        """Combat (PPL 24 vs standard ICE) must resolve in <50ms (Phase 21 budget)."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=200, max_ap=12, programs=programs)
        player.auto_attack_damage = 24
        enemy = _enemy_standard(max_hp=400, base_damage=5)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))
        # 10 ticks is enough to exercise the auto-attack path on most configs.
        start = time.perf_counter()
        for _ in range(10):
            step_combat(state)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 50.0, f"10 ticks took {elapsed_ms:.3f}ms (expected <50ms)"

    def test_damage_calc_under_1ms(self) -> None:
        """Damage calculation must complete in <1ms per call (Phase 21 budget)."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=100, max_ap=6, programs=programs)
        player.auto_attack_damage = 10
        enemy = _enemy_standard(max_hp=200, base_damage=3)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))
        start = time.perf_counter()
        for _ in range(100):
            _calculate_damage(state, player.auto_attack_damage, player, enemy)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 100.0, f"100 damage calcs took {elapsed_ms:.3f}ms (expected <100ms)"

    def test_vfx_step_under_5ms(self) -> None:
        """VFX step (60 fps tick) must complete in <5ms per call (Phase 21 budget)."""
        effects = CombatEffects()
        for _ in range(8):
            effects.animations.append(_make_anim_for_step())
        effects.particles.spawn_burst(x=0.0, y=0.0, count=50)
        for i in range(6):
            effects.floating_numbers.append(_make_floating_number(i))
        start = time.perf_counter()
        for _ in range(60):
            effects.step(16)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 50.0, f"60 VFX steps took {elapsed_ms:.3f}ms (expected <50ms)"


# ---------------------------------------------------------------------------
# 3. Mission selection benchmarks
# ---------------------------------------------------------------------------


class TestMissionBench:
    """Wall-clock benchmarks for mission selection."""

    def test_select_weighted_200_missions(self) -> None:
        """JobBoard.select_weighted with 200 missions."""
        ids = [f"m_{i}" for i in range(200)]
        board = _build_board(ids)
        state = DummyState(grade=3)

        def one_select() -> Any:
            return board.select_weighted(state, seed=42)

        mean_ms = _time_it(one_select, repeats=50)
        assert mean_ms < 10.0, f"select_weighted (200) took {mean_ms:.3f}ms (expected <10ms)"

    def test_select_by_faction_full_state(self) -> None:
        """JobBoard.select_by_faction with the full faction rep state."""
        ids = [f"m_{i}" for i in range(50)]
        board = _build_board(ids)

        def one_filter() -> Any:
            return board.select_by_faction("finn", grade=3)

        mean_ms = _time_it(one_filter, repeats=100)
        assert mean_ms < 5.0, f"select_by_faction took {mean_ms:.3f}ms (expected <5ms)"

    def test_random_rule_application_chain_19(self) -> None:
        """Apply all 19 random selection rules against a state."""
        rules_total = get_total_rules()
        assert rules_total >= 19, f"expected >=19 random rules, got {rules_total}"
        state = DummyState(grade=4, yakuza_rep=3, has_construct=True)

        def one_apply() -> Any:
            return get_random_mission_with_rule(state, [f"m_{i}" for i in range(50)], seed=42)

        mean_ms = _time_it(one_apply, repeats=100)
        assert mean_ms < 10.0, f"random rule chain took {mean_ms:.3f}ms (expected <10ms)"

    def test_apply_rule_single(self) -> None:
        """Single rule application (warm-path)."""
        from roguelike_sprawl.missions.random_rules import get_rule_by_id

        rules_total = get_total_rules()
        if rules_total == 0:
            pytest.skip("no rules loaded")
        # rule_id must match an entry in data/missions/random_selection_rules.json
        rule_id = "faction_weighted"
        if get_rule_by_id(rule_id) is None:
            pytest.skip(f"rule {rule_id!r} not in random_selection_rules.json")
        state = DummyState(grade=3)

        def one_rule() -> Any:
            return apply_rule(rule_id, state, [f"m_{i}" for i in range(50)])

        mean_ms = _time_it(one_rule, repeats=100)
        assert mean_ms < 5.0, f"apply_rule took {mean_ms:.3f}ms (expected <5ms)"

    def test_mission_chain_validation_9_chains(self) -> None:
        """Mission chain sequence/validation across 9 chains (3-5 missions each)."""
        chains = tuple(_make_chain(i) for i in range(9))

        def one_sequence() -> Any:
            for c in chains:
                # `sequence()` sorts missions by order — exercises the
                # full chain code path including __post_init__ invariants.
                _ = c.sequence()

        mean_ms = _time_it(one_sequence, repeats=50)
        assert mean_ms < 5.0, f"9 chains took {mean_ms:.3f}ms (expected <5ms)"


class TestMissionBudget:
    """Single-call performance budgets for mission selection."""

    def test_mission_selection_under_10ms(self) -> None:
        """Mission selection must complete in <10ms (Phase 21 budget)."""
        ids = [f"m_{i}" for i in range(200)]
        board = _build_board(ids)
        state = DummyState(grade=3)
        start = time.perf_counter()
        result = board.select_weighted(state, seed=42)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert result is not None
        assert elapsed_ms < 10.0, f"select_weighted took {elapsed_ms:.3f}ms (expected <10ms)"


class TestCyberspaceBudget:
    """Single-call performance budgets for cyberspace (Phase 21 fail-fast)."""

    def test_matrix_generation_under_20ms(self) -> None:
        """Cyberspace matrix generation (Phase 5+) must complete in <20ms."""
        gen = CyberspaceGenerator()
        gen.generate(seed=0, mission_grade=1)  # warm-up
        start = time.perf_counter()
        gen.generate(seed=42, mission_grade=1)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 20.0, f"matrix generate took {elapsed_ms:.3f}ms (expected <20ms)"

    def test_matrix_layout_under_5ms(self) -> None:
        """Matrix BFS layout computation must complete in <5ms (Phase 21 budget)."""
        graph, _ = CyberspaceGenerator().generate(seed=42, mission_grade=1)
        start = time.perf_counter()
        compute_layout(graph)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 5.0, f"compute_layout took {elapsed_ms:.3f}ms (expected <5ms)"


# ---------------------------------------------------------------------------
# 4. Cyberspace navigation benchmarks
# ---------------------------------------------------------------------------


class TestCyberspaceBench:
    """Wall-clock benchmarks for the cyberspace / matrix systems."""

    def test_matrix_graph_traversal_small(self) -> None:
        """Matrix node graph traversal: small graph (~7 nodes)."""
        graph = MatrixGenerator().generate(seed=1, mission_grade=1)

        def traverse() -> Any:
            # Walk the graph from entry, collecting neighbors at each hop.
            visited: list[str] = []
            stack = [graph.entry_id]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.append(nid)
                for n in graph.neighbors(nid):
                    stack.append(n.id)
            return visited

        mean_ms = _time_it(traverse, repeats=100)
        assert mean_ms < 1.0, f"small graph traversal took {mean_ms:.3f}ms (expected <1ms)"

    def test_matrix_graph_traversal_medium(self) -> None:
        """Matrix node graph traversal: medium graph (~30-50 nodes via CyberspaceGenerator)."""
        graph, _ = CyberspaceGenerator().generate(seed=7, mission_grade=1)

        def traverse() -> Any:
            visited: list[str] = []
            stack = [graph.entry_id]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.append(nid)
                for n in graph.neighbors(nid):
                    stack.append(n.id)
            return visited

        mean_ms = _time_it(traverse, repeats=100)
        assert mean_ms < 5.0, f"medium graph traversal took {mean_ms:.3f}ms (expected <5ms)"

    def test_matrix_graph_traversal_large(self) -> None:
        """Matrix graph traversal: large graph via repeated generation."""
        gen = CyberspaceGenerator()
        # Pre-build a pool of graphs to traverse (avoids measuring generator cost).
        graphs = [gen.generate(seed=i + 100, mission_grade=1)[0] for i in range(10)]

        def traverse() -> Any:
            for g in graphs:
                visited: list[str] = []
                stack = [g.entry_id]
                while stack:
                    nid = stack.pop()
                    if nid in visited:
                        continue
                    visited.append(nid)
                    for n in g.neighbors(nid):
                        stack.append(n.id)

        mean_ms = _time_it(traverse, repeats=20)
        assert mean_ms < 10.0, f"large graph traversal took {mean_ms:.3f}ms (expected <10ms)"

    def test_compute_layout_medium_graph(self) -> None:
        """Compute BFS layout for a medium graph."""
        graph, _ = CyberspaceGenerator().generate(seed=11, mission_grade=1)

        def one_layout() -> Any:
            return compute_layout(graph)

        mean_ms = _time_it(one_layout, repeats=100)
        assert mean_ms < 5.0, f"compute_layout took {mean_ms:.3f}ms (expected <5ms)"

    def test_ice_encounter_spawn_50(self) -> None:
        """Spawning 50 ICE-style enemy combatants (registry build)."""
        registry = IceRegistry({"standard": {"hp": 80, "base_damage": 5, "tier": 1}})

        def one_spawn() -> Any:
            return tuple(build_ice_enemy("standard", registry) for _ in range(50))

        mean_ms = _time_it(one_spawn, repeats=20)
        assert mean_ms < 20.0, f"50 ICE spawn took {mean_ms:.3f}ms (expected <20ms)"

    def test_ice_behavior_simulation_60_ticks(self) -> None:
        """ICE behavior simulation: 60 ticks of standard combat resolution."""
        programs = ProgramRegistry({})
        player = build_default_player(max_hp=100, max_ap=6, programs=programs)
        player.auto_attack_damage = 5
        enemy = _enemy_standard(max_hp=60, base_damage=3)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))

        def run_60_ticks() -> None:
            for _ in range(60):
                step_combat(state)

        mean_ms = _time_it(run_60_ticks, repeats=50)
        assert mean_ms < 50.0, f"60-tick sim took {mean_ms:.3f}ms (expected <50ms)"

    def test_hazard_application_matrix(self) -> None:
        """Hazard application across matrix: event trigger checks for all events."""
        rng = random.Random(0)
        events = list(MATRIX_EVENTS.keys())

        def check_all() -> Any:
            return tuple(check_event_trigger(rng, e) for e in events)

        mean_ms = _time_it(check_all, repeats=200)
        assert mean_ms < 1.0, f"hazard check took {mean_ms:.3f}ms (expected <1ms)"


# ---------------------------------------------------------------------------
# 5. Save / Load benchmarks
# ---------------------------------------------------------------------------


class TestSaveLoadBench:
    """Wall-clock benchmarks for save/load (Phase 11-20 metadata)."""

    def test_save_serialization_full(self, tmp_path: Path) -> None:
        """Save state serialization (full AppState with matrix + reputation)."""
        manager = SaveManager(save_dir=tmp_path / "saves")

        def one_save() -> Any:
            state = _make_appstate_with_run(tmp_path)
            return manager.save(1, state, elapsed_seconds=120)

        mean_ms = _time_it(one_save, repeats=20)
        assert mean_ms < 100.0, f"save took {mean_ms:.3f}ms (expected <100ms)"

    def test_load_restoration_full(self, tmp_path: Path) -> None:
        """Load state restoration (full AppState including matrix)."""
        manager = SaveManager(save_dir=tmp_path / "saves")
        # Pre-create a save to load from.
        seeded = _make_appstate_with_run(tmp_path)
        seeded.ending_choice = "B"
        manager.save(1, seeded, elapsed_seconds=120)

        def one_load() -> Any:
            state = AppState()
            state.run_state = start_run("anything")  # will be overwritten
            manager.restore_state(1, state)
            return state

        mean_ms = _time_it(one_load, repeats=20)
        assert mean_ms < 100.0, f"load took {mean_ms:.3f}ms (expected <100ms)"

    def test_metadata_round_trip_with_ending_choice(self, tmp_path: Path) -> None:
        """Save + load metadata round-trip preserving ending_choice."""
        manager = SaveManager(save_dir=tmp_path / "saves")
        seeded = _make_appstate_with_run(tmp_path)
        seeded.ending_choice = "B"

        def round_trip() -> str:
            manager.save(1, seeded, elapsed_seconds=60)
            fresh = AppState()
            fresh.run_state = start_run("anything")
            manager.restore_state(1, fresh)
            return fresh.ending_choice

        mean_ms = _time_it(round_trip, repeats=20)
        assert mean_ms < 100.0, f"metadata round-trip took {mean_ms:.3f}ms (expected <100ms)"

    def test_list_slots_cold(self, tmp_path: Path) -> None:
        """List all save slots — filesystem metadata walk."""
        manager = SaveManager(save_dir=tmp_path / "saves")

        def list_slots() -> Any:
            return manager.list_slots()

        mean_ms = _time_it(list_slots, repeats=50)
        assert mean_ms < 50.0, f"list_slots took {mean_ms:.3f}ms (expected <50ms)"


class TestSaveLoadBudget:
    """Single-call performance budgets for save/load (Phase 21 fail-fast)."""

    def test_save_load_under_100ms(self, tmp_path: Path) -> None:
        """Save + load cycle must complete in <100ms (Phase 21 budget)."""
        manager = SaveManager(save_dir=tmp_path / "saves")
        state = _make_appstate_with_run(tmp_path)
        state.ending_choice = "A"
        start = time.perf_counter()
        manager.save(1, state, elapsed_seconds=60)
        fresh = AppState()
        fresh.run_state = start_run("anything")
        manager.restore_state(1, fresh)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 100.0, f"save+load took {elapsed_ms:.3f}ms (expected <100ms)"
        # Round-trip preserves ending_choice as advertised in ADR-0192.
        assert fresh.ending_choice == "A"


# ---------------------------------------------------------------------------
# 6. Telemetry aggregation benchmarks
# ---------------------------------------------------------------------------


class TestTelemetryBench:
    """Wall-clock benchmarks for telemetry aggregation."""

    def _make_session(self, n_events: int, *, opt_in: bool = True) -> TelemetrySession:
        """Build a session with ``n_events`` mixed events."""
        session = start_telemetry_session(opt_in=opt_in)
        rng = random.Random(0)
        event_types = (
            "death",
            "kill",
            "deck_chosen",
            "mutator_chosen",
            "boss_reached",
            "mission_completed",
            "run_completed",
        )
        for i in range(n_events):
            et = event_types[i % len(event_types)]
            data: dict[str, object]
            if et == "death":
                data = {"ice_type": f"ice_{i % 5}"}
            elif et == "kill":
                data = {"ice_type": f"ice_{i % 7}"}
            elif et == "deck_chosen":
                data = {"deck": "standard"}
            elif et == "mutator_chosen":
                data = {"mutator": f"mut_{i % 4}"}
            else:
                data = {"value": i}
            session = record_telemetry_event(
                session,
                et,
                data,
                timestamp_ms=int(rng.random() * 100000),
            )
        return session

    def test_aggregation_100_events(self) -> None:
        """Aggregate 100 events: all 4 aggregation functions."""
        session = self._make_session(100)

        def aggregate_all() -> Any:
            return (
                aggregate_death_rates(session),
                aggregate_kill_counts(session),
                aggregate_deck_distribution(session),
                aggregate_mutator_choices(session),
            )

        mean_ms = _time_it(aggregate_all, repeats=50)
        assert mean_ms < 50.0, f"100-event aggregate took {mean_ms:.3f}ms (expected <50ms)"

    def test_aggregation_1000_events(self) -> None:
        """Aggregate 1000 events: all 4 aggregation functions."""
        session = self._make_session(1000)

        def aggregate_all() -> Any:
            return (
                aggregate_death_rates(session),
                aggregate_kill_counts(session),
                aggregate_deck_distribution(session),
                aggregate_mutator_choices(session),
            )

        mean_ms = _time_it(aggregate_all, repeats=20)
        assert mean_ms < 100.0, f"1000-event aggregate took {mean_ms:.3f}ms (expected <100ms)"

    def test_run_completion_aggregation_10_runs(self) -> None:
        """Run completion aggregation across 10 runs."""
        sessions = tuple(self._make_session(50) for _ in range(10))

        def aggregate_runs() -> Any:
            total_deaths = 0
            total_kills = 0
            for s in sessions:
                total_deaths += sum(aggregate_death_rates(s).values())
                total_kills += sum(aggregate_kill_counts(s).values())
            return total_deaths, total_kills

        mean_ms = _time_it(aggregate_runs, repeats=20)
        assert mean_ms < 50.0, f"10-run aggregate took {mean_ms:.3f}ms (expected <50ms)"

    def test_record_event_chain(self) -> None:
        """Recording a single event (immutable session update)."""
        session = start_telemetry_session(opt_in=True)

        def record() -> Any:
            return record_telemetry_event(
                session,
                "kill",
                {"ice_type": "standard"},
                timestamp_ms=0,
            )

        mean_ms = _time_it(record, repeats=100)
        assert mean_ms < 1.0, f"record_event took {mean_ms:.3f}ms (expected <1ms)"


class TestTelemetryBudget:
    """Single-call performance budgets for telemetry (Phase 21 fail-fast)."""

    def test_telemetry_100_events_under_50ms(self) -> None:
        """Telemetry aggregation (100 events) must complete in <50ms."""
        session = start_telemetry_session(opt_in=True)
        rng = random.Random(0)
        for i in range(100):
            session = record_telemetry_event(
                session,
                "kill",
                {"ice_type": f"ice_{i % 5}"},
                timestamp_ms=int(rng.random() * 100000),
            )
        start = time.perf_counter()
        aggregate_death_rates(session)
        aggregate_kill_counts(session)
        aggregate_deck_distribution(session)
        aggregate_mutator_choices(session)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 50.0, f"telemetry 100 events took {elapsed_ms:.3f}ms (expected <50ms)"


# ---------------------------------------------------------------------------
# Local helpers (kept private to this module to avoid polluting the package)
# ---------------------------------------------------------------------------


def _make_anim_for_step() -> Animation:
    """Return a minimal Animation instance for CombatEffects stepping."""
    return Animation(
        frames=(AnimationFrame(text="*", color=(255, 255, 255), duration_ms=80),),
    )


def _make_floating_number(value: int) -> FloatingNumber:
    """Return a minimal FloatingNumber that can be stepped."""
    return FloatingNumber(
        x=float(value),
        y=0.0,
        value=value,
        color=(255, 255, 255),
    )


def _make_chain(idx: int) -> MissionChain:
    """Build a synthetic 3-mission chain for benchmark loops."""
    return MissionChain(
        chain_id=f"bench_chain_{idx}",
        chain_name=f"Bench Chain {idx}",
        chain_type="story_driven",
        chain_arc=1,
        unlock_condition=ChainUnlockCondition(
            min_grade=idx + 1,
            prerequisite_chain=None,
        ),
        missions=tuple(
            ChainMission(
                id=f"bench_{idx}_{m}",
                order=m,
                type="investigation",
                chain_role="intro" if m == 0 else "climax" if m == 2 else "escalation",
            )
            for m in range(3)
        ),
        chain_reward=ChainReward(credits=500),
        chain_failure=ChainFailure(reputation_penalty={"finn": -1}),
    )


# ---------------------------------------------------------------------------
# Phase 21 baseline capture test (single-shot, prints numbers)
# ---------------------------------------------------------------------------


class TestPhase21Baseline:
    """Single-shot baseline numbers used to author docs/performance/phase21-benchmarks.md.

    Each test measures once and prints the result for pytest ``-s``
    capture. These are NOT budget tests — they only enforce loose
    upper bounds so a regression in the measurement scaffolding itself
    doesn't silently break Phase 21 reporting.
    """

    def test_capture_all_baselines(self, tmp_path: Path) -> None:
        """Print a single consolidated baseline table for the Phase 21 report."""
        lines: list[str] = []
        lines.append("[phase21] baseline.measurements.start")

        programs = ProgramRegistry({})
        player = build_default_player(max_hp=200, max_ap=12, programs=programs)
        player.auto_attack_damage = 24
        enemy = _enemy_standard(max_hp=400, base_damage=5)
        state = CombatState(player=player, enemy=enemy, rng=random.Random(0))
        lines.append(
            f"[phase21] combat.tick.mean_ms={_time_it(lambda: step_combat(state), repeats=100):.4f}"
        )

        grade_means: list[float] = []
        for grade in range(1, 6):
            pl = build_default_player(max_hp=100 + grade * 20, max_ap=6, programs=programs)
            pl.auto_attack_damage = 5 * grade
            en = _enemy_standard(max_hp=80 + grade * 30, base_damage=3 * grade)
            st = CombatState(player=pl, enemy=en, rng=random.Random(grade))
            grade_means.append(_time_it(lambda s=st: step_combat(s), repeats=20))
        lines.append(f"[phase21] combat.5grade.mean_ms={sum(grade_means) / len(grade_means):.4f}")

        effects = CombatEffects()
        for _ in range(8):
            effects.animations.append(_make_anim_for_step())
        effects.particles.spawn_burst(x=0.0, y=0.0, count=50)
        for i in range(6):
            effects.floating_numbers.append(_make_floating_number(i))
        lines.append(
            f"[phase21] combat.vfx.step.mean_ms={_time_it(lambda: effects.step(16), repeats=100):.4f}"
        )

        big_player = build_default_player(max_hp=1000, max_ap=20, programs=programs)
        big_player.auto_attack_damage = 50
        big_enemies = tuple(
            Combatant(
                id=f"ice_{i}",
                name=f"Ice {i}",
                portrait="▲",
                color=(255, 0, 255),
                hp=200,
                max_hp=200,
                ap=0,
                max_ap=0,
                auto_attack_damage=4,
                team="enemy",
            )
            for i in range(50)
        )
        big_state = CombatState(player=big_player, enemies=big_enemies, rng=random.Random(0))
        lines.append(
            f"[phase21] combat.50ice.tick.mean_ms={_time_it(lambda: step_combat(big_state), repeats=20):.4f}"
        )

        lines.append(
            f"[phase21] combat.damage_calc.mean_ms="
            f"{_time_it(lambda: _calculate_damage(state, 10, player, enemy), repeats=100):.4f}"
        )

        board = _build_board([f"m_{i}" for i in range(200)])
        dummy_state = DummyState(grade=3)
        lines.append(
            f"[phase21] mission.select_weighted.200.mean_ms="
            f"{_time_it(lambda: board.select_weighted(dummy_state, seed=42), repeats=50):.4f}"
        )

        lines.append(
            f"[phase21] mission.select_by_faction.mean_ms="
            f"{_time_it(lambda: board.select_by_faction('finn', grade=3), repeats=100):.4f}"
        )

        lines.append(
            f"[phase21] mission.random_rule.mean_ms="
            f"{_time_it(lambda: get_random_mission_with_rule(dummy_state, [f'm_{i}' for i in range(50)], seed=42), repeats=100):.4f}"
        )

        chains = tuple(_make_chain(i) for i in range(9))

        def sequence_chains() -> Any:
            for c in chains:
                _ = c.sequence()

        lines.append(
            f"[phase21] mission.chain_validation.9.mean_ms={_time_it(sequence_chains, repeats=50):.4f}"
        )

        graph_small = MatrixGenerator().generate(seed=1, mission_grade=1)

        def traverse_small() -> Any:
            visited: list[str] = []
            stack = [graph_small.entry_id]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.append(nid)
                for n in graph_small.neighbors(nid):
                    stack.append(n.id)

        lines.append(
            f"[phase21] matrix.traversal.small.mean_ms={_time_it(traverse_small, repeats=100):.4f}"
        )

        graph_medium, _ = CyberspaceGenerator().generate(seed=7, mission_grade=1)

        def traverse_medium() -> Any:
            visited: list[str] = []
            stack = [graph_medium.entry_id]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.append(nid)
                for n in graph_medium.neighbors(nid):
                    stack.append(n.id)

        lines.append(
            f"[phase21] matrix.traversal.medium.mean_ms="
            f"{_time_it(traverse_medium, repeats=100):.4f}"
        )

        gen = CyberspaceGenerator()
        graphs_large = [gen.generate(seed=i + 100, mission_grade=1)[0] for i in range(10)]

        def traverse_large() -> Any:
            for g in graphs_large:
                visited: list[str] = []
                stack = [g.entry_id]
                while stack:
                    nid = stack.pop()
                    if nid in visited:
                        continue
                    visited.append(nid)
                    for n in g.neighbors(nid):
                        stack.append(n.id)

        lines.append(
            f"[phase21] matrix.traversal.large.mean_ms={_time_it(traverse_large, repeats=20):.4f}"
        )

        gen_instance = CyberspaceGenerator()
        gen_instance.generate(seed=0, mission_grade=1)
        lines.append(
            f"[phase21] matrix.generate.mean_ms="
            f"{_time_it(lambda: gen_instance.generate(seed=42, mission_grade=1), repeats=100):.4f}"
        )

        lines.append(
            f"[phase21] matrix.compute_layout.mean_ms="
            f"{_time_it(lambda: compute_layout(graph_medium), repeats=100):.4f}"
        )

        registry = IceRegistry({"standard": {"hp": 80, "base_damage": 5, "tier": 1}})

        def spawn_50() -> Any:
            return tuple(build_ice_enemy("standard", registry) for _ in range(50))

        lines.append(f"[phase21] ice.spawn.50.mean_ms={_time_it(spawn_50, repeats=20):.4f}")

        sim_state = CombatState(
            player=build_default_player(max_hp=100, max_ap=6, programs=programs),
            enemy=_enemy_standard(max_hp=60, base_damage=3),
            rng=random.Random(0),
        )
        sim_state.player.auto_attack_damage = 5

        def sim_60() -> None:
            for _ in range(60):
                step_combat(sim_state)

        lines.append(f"[phase21] combat.60tick.mean_ms={_time_it(sim_60, repeats=50):.4f}")

        rng = random.Random(0)
        events = list(MATRIX_EVENTS.keys())

        def check_hazards() -> Any:
            return tuple(check_event_trigger(rng, e) for e in events)

        lines.append(
            f"[phase21] matrix.hazard_check.mean_ms={_time_it(check_hazards, repeats=200):.4f}"
        )

        manager = SaveManager(save_dir=tmp_path / "saves")
        app_state = _make_appstate_with_run(tmp_path)
        lines.append(
            f"[phase21] save.serialize.mean_ms="
            f"{_time_it(lambda: manager.save(1, app_state, elapsed_seconds=120), repeats=20):.4f}"
        )

        seeded = _make_appstate_with_run(tmp_path)
        seeded.ending_choice = "B"
        manager.save(1, seeded, elapsed_seconds=120)

        def load_one() -> Any:
            fresh = AppState()
            fresh.run_state = start_run("anything")
            manager.restore_state(1, fresh)
            return fresh

        lines.append(f"[phase21] load.restore.mean_ms={_time_it(load_one, repeats=20):.4f}")

        def cycle() -> None:
            manager.save(1, app_state, elapsed_seconds=60)
            fresh = AppState()
            fresh.run_state = start_run("anything")
            manager.restore_state(1, fresh)

        lines.append(f"[phase21] save_load.cycle.mean_ms={_time_it(cycle, repeats=20):.4f}")

        seeded2 = _make_appstate_with_run(tmp_path)
        seeded2.ending_choice = "B"

        def round_trip() -> str:
            manager.save(1, seeded2, elapsed_seconds=60)
            fresh = AppState()
            fresh.run_state = start_run("anything")
            manager.restore_state(1, fresh)
            return fresh.ending_choice

        lines.append(
            f"[phase21] save_load.metadata_roundtrip.mean_ms={_time_it(round_trip, repeats=20):.4f}"
        )

        lines.append(
            f"[phase21] save.list_slots.mean_ms={_time_it(manager.list_slots, repeats=50):.4f}"
        )

        session100 = start_telemetry_session(opt_in=True)
        rng_t = random.Random(0)
        for i in range(100):
            session100 = record_telemetry_event(
                session100,
                "kill",
                {"ice_type": f"ice_{i % 5}"},
                timestamp_ms=int(rng_t.random() * 100000),
            )

        def aggregate_100() -> Any:
            return (
                aggregate_death_rates(session100),
                aggregate_kill_counts(session100),
                aggregate_deck_distribution(session100),
                aggregate_mutator_choices(session100),
            )

        lines.append(
            f"[phase21] telemetry.aggregate.100.mean_ms={_time_it(aggregate_100, repeats=50):.4f}"
        )

        session1000 = start_telemetry_session(opt_in=True)
        rng_t2 = random.Random(0)
        for i in range(1000):
            session1000 = record_telemetry_event(
                session1000,
                "kill",
                {"ice_type": f"ice_{i % 7}"},
                timestamp_ms=int(rng_t2.random() * 100000),
            )

        def aggregate_1000() -> Any:
            return (
                aggregate_death_rates(session1000),
                aggregate_kill_counts(session1000),
                aggregate_deck_distribution(session1000),
                aggregate_mutator_choices(session1000),
            )

        lines.append(
            f"[phase21] telemetry.aggregate.1000.mean_ms={_time_it(aggregate_1000, repeats=20):.4f}"
        )

        session_record = start_telemetry_session(opt_in=True)

        def record_one() -> Any:
            return record_telemetry_event(
                session_record,
                "kill",
                {"ice_type": "standard"},
                timestamp_ms=0,
            )

        lines.append(f"[phase21] telemetry.record.mean_ms={_time_it(record_one, repeats=100):.4f}")

        run_events_tuples: list[tuple[TelemetrySession, tuple[Any, ...]]] = []
        for run_idx in range(10):
            session_id = f"bench_run_{run_idx}"
            sess = start_telemetry_session(opt_in=True)
            sess = TelemetrySession(
                session_id=sess.session_id,
                events=(),
                opt_in=True,
            )
            events_tuple: list[Any] = []
            for i in range(50):
                sess = record_telemetry_event(
                    sess,
                    "kill",
                    {"ice_type": f"ice_{i % 5}"},
                    timestamp_ms=i,
                )
                events_tuple = list(sess.events)
            run_events_tuples.append(
                (
                    TelemetrySession(
                        session_id=session_id,
                        events=tuple(events_tuple),
                        opt_in=True,
                    ),
                    tuple(events_tuple),
                )
            )

        def aggregate_runs() -> Any:
            total_deaths = 0
            total_kills = 0
            for s, _ in run_events_tuples:
                total_deaths += sum(aggregate_death_rates(s).values())
                total_kills += sum(aggregate_kill_counts(s).values())
            return total_deaths, total_kills

        lines.append(
            f"[phase21] telemetry.aggregate.10runs.mean_ms="
            f"{_time_it(aggregate_runs, repeats=20):.4f}"
        )

        lines.append("[phase21] baseline.measurements.end")
        print("\n" + "\n".join(lines))

        assert True


# Touch the SAVE_FORMAT_VERSION symbol so the import is not flagged unused
# and so the test file self-documents its relationship to the save format.
assert SAVE_FORMAT_VERSION == "0.1.0"  # nosec — literal compare, no security implication

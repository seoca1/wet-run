"""Combat view state mutations — start/end + reputation + ICE node removal (ADR-0110 split).

Split from combat_view.py (ADR-0143). Owns combat lifecycle: start_combat,
_end_combat, _check_post_combat_event, _apply_combat_reputation,
_defeat_current_ice_node, _remove_node_from_graph, spawn_phase_transition,
COMBAT_REPUTATION constant.

combat_view.py is reduced to a thin coordinator that re-exports these.

Module structure (post ADR-0143):
    - combat_view (thin coordinator + re-exports)
    - combat_view_input (existing — input handling)
    - combat_view_render: screen + _draw_* helpers
    - combat_view_skills: skill management
    - combat_view_state (this file): combat state mutations + lifecycle
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..audio import safe_play
from ..combat.boss import PhaseProfile, apply_phase_to_combatant, get_boss_profile, is_boss
from ..combat.effects import (
    CombatEffects,
    IceType,
    boss_phase_transition_sequence,
    spawn_ice_death,
    spawn_ice_intro,
)
from ..combat.registry import IceRegistry, ProgramRegistry, build_ice_enemy
from ..combat.state import Combatant, CombatState, Skill
from ..matrix.graph import MatrixGraph
from ..matrix.node import Faction, Node
from ..matrix.ppl import calculate_ppl
from .state import AppState, ScreenKind

if TYPE_CHECKING:
    pass


def start_combat(
    state: AppState,
    ice_node: Node,
    prog_registry: ProgramRegistry,
    ice_registry: IceRegistry,
) -> CombatState:
    """Initialize a CombatState from the current player loadout and ICE node."""
    # Build player combatant
    _ = calculate_ppl(state.player_loadout)  # Reserved for future use (scaling damage)
    player_skills: list[Skill] = []
    for prog in state.player_loadout.programs:
        skill = prog_registry.get(prog.id)
        if skill is not None:
            player_skills.append(skill)

    # Get base player stats
    base_hp = 100
    base_attack = 5
    base_max_ap = 6
    equip_attack_bonus = 0
    equip_defense_bonus = 0
    equip_hp_bonus = 0
    equip_shield_bonus = 0
    equip_ap_bonus = 0
    equip_program_power = 0
    equip_ice_resistance = 0
    equip_damage_bonus_pct = 0
    equip_crit_bonus_pct = 0
    equip_grants_skill_id = None

    # Apply equipment stats
    from ..equipment.equipment import EquipmentLoadout, EquipStats

    loadout = state.equipment_loadout
    stats: EquipStats | None = None
    if isinstance(loadout, EquipmentLoadout):
        raw_stats = loadout.total_stats
        stats = raw_stats if isinstance(raw_stats, EquipStats) else None
        if stats is not None:
            equip_attack_bonus = stats.attack_bonus
            equip_defense_bonus = stats.defense
            equip_hp_bonus = stats.hp_bonus
            equip_shield_bonus = stats.shield_bonus
            equip_ap_bonus = stats.ap_bonus
            equip_program_power = stats.program_power
            equip_ice_resistance = stats.ice_resistance
            equip_damage_bonus_pct = stats.damage_bonus_pct
            equip_crit_bonus_pct = stats.crit_bonus_pct
            equip_grants_skill_id = stats.grants_skill_id

        # Apply bonuses to base stats
        base_hp = 100 + equip_hp_bonus
        base_max_ap = 6 + equip_ap_bonus

        # Add equipment-granted skill if any
        if equip_grants_skill_id is not None:
            granted = prog_registry.get(equip_grants_skill_id)
            if granted is not None and granted not in player_skills:
                player_skills.append(granted)

    player = Combatant(
        id="player",
        name="You",
        portrait="◉P◉",
        color=(0, 255, 0),
        hp=base_hp,
        max_hp=base_hp,
        ap=3 + equip_ap_bonus,  # Start with bonus AP
        max_ap=base_max_ap,
        auto_attack_damage=base_attack + equip_attack_bonus,
        skills=tuple(player_skills),
        team="player",
        # Apply equipment stats
        equip_attack_bonus=equip_attack_bonus,
        equip_defense_bonus=equip_defense_bonus,
        equip_hp_bonus=equip_hp_bonus,
        equip_shield_bonus=equip_shield_bonus,
        equip_ap_bonus=equip_ap_bonus,
        equip_program_power=equip_program_power,
        equip_ice_resistance=equip_ice_resistance,
        equip_damage_bonus_pct=equip_damage_bonus_pct,
        equip_crit_bonus_pct=equip_crit_bonus_pct,
        equip_grants_skill_id=equip_grants_skill_id,
    )

    # Build enemy combatant from the actual ICE on this node.
    # IceKind.NONE → defensive fallback to "standard".
    from ..combat.multi_enemy import encounter_count_for_grade
    from ..matrix.node import IceKind

    ice_kind_value = ice_node.ice.value if ice_node.ice is not IceKind.NONE else "standard"
    ice_kind_id = ice_kind_value  # ice_types.json keys match IceKind values
    try:
        enemy = build_ice_enemy(ice_kind_id, ice_registry)
    except KeyError:
        # Unknown ICE id (data gap) — fall back to standard rather than crash.
        enemy = build_ice_enemy("standard", ice_registry)
        ice_kind_id = "standard"
    # ADR-0153: multi-encounter — create N-1 additional enemies based on player grade
    encounter_n = encounter_count_for_grade(state.player_grade)
    enemies_list = [enemy]
    for _ in range(encounter_n - 1):
        try:
            additional = build_ice_enemy(ice_kind_id, ice_registry)
        except KeyError:
            additional = build_ice_enemy("standard", ice_registry)
        enemies_list.append(additional)
    if encounter_n > 1:
        state.status_messages.append(f">>> ENCOUNTER: 1v{encounter_n} ({encounter_n} enemies)")
    state.combat_effects.clear()
    # Map ice_kind string to IceType enum
    try:
        ice_type = IceType(ice_kind_id)
    except ValueError:
        ice_type = IceType.STANDARD
    spawn_ice_intro(state.combat_effects, ice_type, enemy.name)
    cs = CombatState(player=player, enemies=tuple(enemies_list))

    if is_boss(ice_type) and cs.enemy is not None:
        profile = get_boss_profile(ice_type)
        if profile is not None:
            apply_phase_to_combatant(cs.enemy, profile)
            cs.boss_profile = profile

    return cs


def spawn_phase_transition(
    effects: CombatEffects,
    phase: PhaseProfile,
    ice_type: IceType,
) -> None:
    """Spawn boss phase transition cinematic (ADR-0050)."""
    total_phases = len(phase) if hasattr(phase, "__len__") else 3
    effects.cinematic = boss_phase_transition_sequence(
        ice_type,
        phase.phase,
        total_phases,
    )
    effects.slow_motion_ms = effects.cinematic.total_duration_ms
    effects.shake.trigger(intensity=3.0, duration_ms=400)


def _end_combat(state: AppState, combat_state: CombatState) -> None:
    """Transition from Combat to next state with rewards."""
    enemy = combat_state.enemy
    if combat_state.outcome == "victory" and enemy is not None:
        # VFX: ICE death cinematic (per ICE type)
        try:
            ice_type = IceType(enemy.id)
        except ValueError:
            ice_type = IceType.STANDARD
        spawn_ice_death(state.combat_effects, ice_type)
        # Play victory sound
        safe_play("combat/victory")
        # Award rewards: ICE Shard material + credits
        if not hasattr(state, "inventory") or state.inventory is None:
            state.inventory = {}
        state.inventory["ice_shard"] = state.inventory.get("ice_shard", 0) + 1
        state.status_messages.append(">>> VICTORY! Gained: 1x ICE Shard")
        state.status_messages.append(">>> Gained: 50 credits")

        # Salvage menu (ADR-0014 + ADR-0147): queue a 3-way choice
        # (HEAL/FRAG/CRED/SKIP) for the next interaction cycle. The
        # menu UI itself is rendered in a follow-up cycle; for now we
        # set the flag so downstream code (and tests) know a choice is
        # pending and the defaults can be applied if the user dismisses
        # without picking.
        state.pending_salvage = True

        # Phase 6+: defeating ICE in a faction's server boosts that
        # faction's rep (you successfully infiltrated their space).
        # Reverse-direction targets (opposing factions) lose rep.
        _apply_combat_reputation(state, ice_type)

        # Progress mission objective (defeat)
        from .mission_completion import update_mission_progress

        update_mission_progress(state, "defeat", 1)

        # Advance RunState: if we're on the DEFEAT_ICE stage, this
        # victory satisfies the objective and we should move forward.
        from ..run import Stage, check_combat_victory, ensure_run_state

        run_state = ensure_run_state(state)
        if check_combat_victory(run_state):
            run_state.mark_advance()
            state.status_messages.append(f">>> Stage complete: {run_state.current_info().title}")

            # If we advanced to JACK_OUT, switch to the jack out screen
            if run_state.current_stage is Stage.JACK_OUT:
                from .jack_out_view import enter_jack_out

                enter_jack_out(state)
                # Mark current ICE node as defeated before returning
                _defeat_current_ice_node(state)
                # Trigger victory event (ICE destruction)
                _check_post_combat_event(state, "standard_ice_victory")
                return  # Don't return to matrix; we're entering JACK_OUT

        # Mark current ICE node as defeated - removed from dungeon
        if state.matrix is not None and state.current_node_id is not None:
            _defeat_current_ice_node(state)

        # Return to matrix (player can continue exploring)
        state.screen = ScreenKind.MATRIX
        state.message = "ICE defeated! Path is now clear."

        # Trigger victory event (ICE destruction)
        _check_post_combat_event(state, "standard_ice_victory")
    elif combat_state.outcome == "defeat":
        # Player died — Pillar 3: The Flatline
        from ..combat.boss_phase4 import apply_death_taunt
        from ..run import ensure_run_state
        from .death import trigger_death

        run_state = ensure_run_state(state)
        run_state.mark_failed()
        trigger_death(state, reason="ICE breach")
        # ADR-0149: Boss death taunt. Applied after trigger_death so the
        # DEATH screen shows the taunt line as the boss's last words.
        boss_id = ""
        if combat_state.enemy is not None:
            boss_id = combat_state.enemy.id
        if boss_id:
            apply_death_taunt(combat_state, state, boss_id)
    else:
        # Disengage (player fled)
        state.screen = ScreenKind.MATRIX
        state.message = "Disengaged from combat."


def _check_post_combat_event(state: AppState, trigger_id: str) -> None:
    """Check if an event story should trigger after combat."""
    from .event_story import EventRegistry, EventState, EventTrigger, check_event_trigger

    if not hasattr(state, "_event_registry") or state._event_registry is None:
        state._event_registry = EventRegistry()

    event = check_event_trigger(
        state,
        registry=state._event_registry,
        trigger=EventTrigger.COMBAT_END,
        trigger_id=trigger_id,
    )
    if event is not None:
        state.active_event = EventState(event=event)
        state.screen = ScreenKind.EVENT


# Reputation deltas when player defeats ICE on a faction's server.
# The defending faction (whose ICE was killed) loses rep (you hurt them);
# opposing factions gain rep (you're weakening their rivals).
COMBAT_REPUTATION: dict[Faction, dict[Faction, int]] = {
    Faction.HOSAKA: {Faction.HOSAKA: -3, Faction.MAAS: +1},
    Faction.MAAS: {Faction.MAAS: -3, Faction.HOSAKA: +1},
    Faction.SENSE_NET: {Faction.SENSE_NET: -3, Faction.TA: +1},
    Faction.TA: {Faction.TA: -3, Faction.SENSE_NET: +1},
}


def _apply_combat_reputation(state: AppState, ice_type: object) -> None:
    """Adjust faction reputation after defeating an ICE.

    Looks up the defeated node's faction (where you successfully
    infiltrated) and applies:
      - defending faction: -3 (you hurt them)
      - opposing faction: +1 (you weakened their rivals)

    Pure black-ICE / non-corp ICE → no rep change.
    """
    if not hasattr(state, "reputation"):
        return
    # Find the current node to determine its faction.
    node_faction = Faction.NONE
    if state.matrix is not None and state.current_node_id is not None:
        node = next(
            (n for n in state.matrix.nodes if n.id == state.current_node_id),
            None,
        )
        if node is not None:
            node_faction = node.faction

    if node_faction is Faction.NONE or node_faction not in COMBAT_REPUTATION:
        return

    # ice_type is the IceType enum (or fallback IceType.STANDARD).
    type_name = getattr(ice_type, "name", str(ice_type))
    deltas = COMBAT_REPUTATION[node_faction]
    for faction, delta in deltas.items():
        state.reputation.adjust(faction, delta, source=f"combat:{type_name}")
    affected = ", ".join(f"{f.value} {d:+d}" for f, d in deltas.items())
    state.status_messages.append(f">>> Rep shifted: {affected}")


def _defeat_current_ice_node(state: AppState) -> None:
    """Mark the current ICE node as defeated and remove from graph.

    Helper for _end_combat() — used in both the JACK_OUT path and
    the standard matrix-return path.
    """
    if state.matrix is None or state.current_node_id is None:
        return
    defeated_id = state.current_node_id
    state.defeated_nodes.add(defeated_id)
    state.status_messages.append(f">>> ICE [{defeated_id}] destroyed")
    state.matrix = _remove_node_from_graph(state.matrix, defeated_id)
    if state.matrix is not None and len(state.matrix.nodes) > 0:
        neighbors = (
            state.matrix.neighbors(defeated_id)
            if defeated_id in [n.id for n in state.matrix.nodes]
            else []
        )
        if neighbors:
            state.current_node_id = neighbors[0].id
        else:
            state.current_node_id = state.matrix.entry_id


def _remove_node_from_graph(matrix: MatrixGraph | None, node_id: str) -> MatrixGraph | None:
    """Remove a node from the matrix graph (returns new graph or None)."""
    if matrix is None:
        return None

    # Filter out the node
    new_nodes = tuple(n for n in matrix.nodes if n.id != node_id)

    # Filter out edges involving the node
    new_edges = tuple(e for e in matrix.edges if e.src != node_id and e.dst != node_id)

    # Need to import here to avoid circular imports
    from ..matrix.graph import MatrixGraph

    if not new_nodes:
        return None

    # Update entry_id if the removed node was the entry
    new_entry_id = matrix.entry_id
    if matrix.entry_id == node_id and new_nodes:
        new_entry_id = new_nodes[0].id

    return MatrixGraph(
        nodes=new_nodes,
        edges=new_edges,
        entry_id=new_entry_id,
    )


# Re-exported by combat_view for backward compat (ADR-0110).
__all__ = [
    "COMBAT_REPUTATION",
    "_apply_combat_reputation",
    "_check_post_combat_event",
    "_defeat_current_ice_node",
    "_end_combat",
    "_remove_node_from_graph",
    "spawn_phase_transition",
    "start_combat",
]

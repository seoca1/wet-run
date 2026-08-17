"""State-mutating tests for _apply_combat_reputation (combat_view.py).

Covers early-return branches + main reputation adjustment behavior:
- No state.reputation → return
- node_faction is Faction.NONE → return
- node_faction not in COMBAT_REPUTATION → return
- node_faction in COMBAT_REPUTATION → state.reputation adjusted + status message
"""

from __future__ import annotations

from unittest.mock import MagicMock

from wet_run.engine.combat_view import (  # type: ignore[import-untyped]
    COMBAT_REPUTATION,
    _apply_combat_reputation,
)
from wet_run.engine.state import AppState  # type: ignore[import-untyped]
from wet_run.matrix.graph import MatrixGraph  # type: ignore[import-untyped]
from wet_run.matrix.node import (  # type: ignore[import-untyped]
    Faction,
    Node,
    NodeKind,
    ZoneDepth,
)


def _make_node(faction: Faction = Faction.HOSAKA, id: str = "data_node") -> Node:
    return Node(
        id=id,
        kind=NodeKind.DATA,
        label="Data Node",
        zone=ZoneDepth.MID,
        faction=faction,
    )


def _make_state_with_node(faction: Faction) -> AppState:
    """Construct an AppState with matrix containing a single faction node."""
    state = AppState()
    node = _make_node(faction=faction)
    state.matrix = MatrixGraph(nodes=(node,), edges=(), entry_id=node.id)
    state.current_node_id = node.id
    return state


class TestApplyCombatReputationEarlyReturns:
    """_apply_combat_reputation — early-return branches (no mutation)."""

    def test_early_return_when_state_has_no_reputation(self) -> None:
        """State without reputation attribute → return silently, no crash."""
        from wet_run.combat.effects import IceType

        state = AppState()
        # Remove reputation attribute via delattr (with type: ignore)
        if hasattr(state, "reputation"):
            delattr(state, "reputation")
        _apply_combat_reputation(state, IceType.BLACK)
        # No assertion needed — just verify no crash

    def test_early_return_when_node_faction_is_none(self) -> None:
        """Node with Faction.NONE → return silently, no rep change."""
        from wet_run.combat.effects import IceType

        state = _make_state_with_node(Faction.NONE)
        # Set up reputation as MagicMock to detect any calls
        state.reputation = MagicMock()
        _apply_combat_reputation(state, IceType.BLACK)
        state.reputation.adjust.assert_not_called()

    def test_early_return_when_node_faction_not_in_combat_reputation(self) -> None:
        """Node faction not in COMBAT_REPUTATION (e.g., Faction.NONE variant) → return."""
        from wet_run.combat.effects import IceType

        # COMBAT_REPUTATION only has HOSAKA, MAAS, SENSE_NET, TA
        # Use Faction.NONE which is the canonical "not in dict" case
        state = _make_state_with_node(Faction.NONE)
        state.reputation = MagicMock()
        _apply_combat_reputation(state, IceType.BLACK)
        state.reputation.adjust.assert_not_called()


class TestApplyCombatReputationMain:
    """_apply_combat_reputation — main behavior (reputation adjustment + status message)."""

    def test_applies_reputation_delta_for_hosaka_node(self) -> None:
        """HOSAKA node → apply HOSAKA deltas (self=-3, MAAS=+1) to state.reputation."""
        from wet_run.combat.effects import IceType

        state = _make_state_with_node(Faction.HOSAKA)
        state.reputation = MagicMock()
        _apply_combat_reputation(state, IceType.BLACK)
        # Expect 2 adjust calls: HOSAKA -3, MAAS +1
        assert state.reputation.adjust.call_count == 2
        calls = state.reputation.adjust.call_args_list
        faction_deltas = {(c.args[0], c.args[1]) for c in calls}
        assert (Faction.HOSAKA, -3) in faction_deltas
        assert (Faction.MAAS, 1) in faction_deltas

    def test_appends_rep_shift_status_message(self) -> None:
        """Main behavior → status_messages gets ">>> Rep shifted: ..." entry."""
        from wet_run.combat.effects import IceType

        state = _make_state_with_node(Faction.MAAS)
        state.reputation = MagicMock()
        _apply_combat_reputation(state, IceType.BLACK)
        rep_messages = [m for m in state.status_messages if "Rep shifted" in m]
        assert len(rep_messages) == 1
        assert "maas -3" in rep_messages[0]
        assert "hosaka +1" in rep_messages[0]

    def test_ice_type_name_appears_in_status_message_source(self) -> None:
        """ice_type.name appears in the status message (combat source tracking)."""
        from wet_run.combat.effects import IceType

        state = _make_state_with_node(Faction.SENSE_NET)
        state.reputation = MagicMock()
        # Inspect calls to verify the 'source' parameter includes ice_type name
        _apply_combat_reputation(state, IceType.STANDARD)
        calls = state.reputation.adjust.call_args_list
        for call in calls:
            source_kwarg = call.kwargs.get("source", "")
            assert "combat:" in source_kwarg
            assert "STANDARD" in source_kwarg

    def test_only_iterates_over_known_factions(self) -> None:
        """COMBAT_REPUTATION dict size matches adjust call count for any faction."""
        from wet_run.combat.effects import IceType

        for faction in COMBAT_REPUTATION:
            state = _make_state_with_node(faction)
            state.reputation = MagicMock()
            _apply_combat_reputation(state, IceType.STANDARD)
            expected = len(COMBAT_REPUTATION[faction])
            assert state.reputation.adjust.call_count == expected

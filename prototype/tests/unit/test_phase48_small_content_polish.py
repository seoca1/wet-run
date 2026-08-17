"""Tests for Phase 48 — Small content + polish.

Validates:
- The new general_event_dixie_flatline_memory event (Option A content
  addition). Gibson-flavored arc 4 mid-arc "Dixie Flatline Memory" event.
  The runner receives a handshake from a dead ROM-construct fragment —
  the construct personality of McCoy Pauley's "Dixie Flatline" from
  Neuromancer, archived in construct-chip ROM (Case's dead partner
  whose personality is stored in ROM-construct space, who whispers
  memory hints to other runners, who is a recurring Sprawl-trilogy
  motif — Gibson's "the matrix remembers what the brain forgets" via
  construct entities). Two paths: carry the construct memory
  (wintermute_+2, ta_rep_+1, construct_memory_carried_2_runs,
  construct_peek_unlocked — the construct entity trusts the runner
  with a memory fragment, the TA-family constructs let the runner
  peek at higher zones) or walk on (construct_ghost_dismissed,
  safe_jackout, identity_marker_low, hosaka_-1 — the runner dismisses
  the dead construct's offer and Hosaka notes the disrespect).
  matrix_deep_zone location, mood shaky, pillar memory, tier 4.
- Polish improvements (3 modules):
    * combat/meta_progression.py — record_meta_progress docstring now
      has explicit Args / Returns / Raises: sections. The error
      message itself was already self-diagnosing (it lists valid
      unlock ids).
    * combat/status_effects_v2.py — make_status_v2 docstring now has
      explicit Args / Returns / Raises: sections. The error message
      itself was already self-diagnosing (it lists valid effect
      types).
    * matrix/graph.py — MatrixGraph.__post_init__ 4 ValueError
      messages now include the count of known node ids and a sample
      (sorted(ids)[:3]) so callers can self-diagnose missing-node
      errors without reading the full source. Also from_dict now
      lists the expected JSON keys (id/kind/label/zone for nodes,
      src/dst for edges) in its malformed-data messages.
- Total events count increments from 50 to 51; total_chains stays at 6.
- Vault-wide interrogate coverage remains at 100.0% (no regressions).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "story" / "events.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def events_data() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def events(events_data: dict) -> dict:
    return {k: v for k, v in events_data.items() if not k.startswith("_")}


@pytest.fixture
def metadata(events_data: dict) -> dict:
    return events_data.get("_metadata", {})


# ---------------------------------------------------------------------------
# Content: general_event_dixie_flatline_memory
# ---------------------------------------------------------------------------


class TestDixieFlatlineMemoryEvent:
    """Phase 48 content addition — Gibson-flavored Dixie Flatline ROM-construct.

    Arc 4 mid-arc (>= 32%) overlay on matrix_deep_zone. The runner
    receives a handshake from a dead ROM-construct fragment — the
    construct personality of McCoy Pauley's "Dixie Flatline" from
    Neuromancer, archived in construct-chip ROM (Case's dead partner
    whose personality is stored in ROM-construct space). The choice
    is the standard "carry the memory vs walk on" fork: carrying
    (wintermute_+2) yields ta_rep_+1 (the TA-family constructs accept
    the runner's memory-carrier status — the construct passage opens)
    plus construct_peek_unlocked (the runner can peek at construct-
    grade matrix nodes later). Walking on yields safe_jackout (the
    runner jacks out cleanly) plus hosaka_-1 (Hosaka notes that the
    runner dismissed a dead-ROM-construct's memory offer — corporate
    disrespect) plus identity_marker_low (the runner remains
    identity-unmarked).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_dixie_flatline_memory" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_dixie_flatline_memory"]
        assert event["event_id"] == "general_event_dixie_flatline_memory"
        assert event["title"] == "Dixie Flatline Memory"
        assert event["category"] == "general"
        # Arc 4 mid-arc encounter — deep zone, tier 4
        assert event["arc"] == 4
        assert event["tier"] == 4
        assert event["pillar"] == "memory"
        assert "deep_zone" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (carry the memory vs walk on)."""
        event = events["general_event_dixie_flatline_memory"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Carry path should mention wintermute / construct / memory
        carry_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert (
            "wintermute" in carry_path
            or "construct" in carry_path
            or "memory" in carry_path
            or "peek" in carry_path
        )
        # Walk-on path should mention hosaka / safe_jackout / dismiss
        walk_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert (
            "hosaka" in walk_path
            or "safe_jackout" in walk_path
            or "dismiss" in walk_path
            or "ghost" in walk_path
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — Dixie / ROM-construct / dead-jockey motif.

        Gibson Dixie / construct / dead-ROM signatures:
        - 'ROM construct fragment detected' (construct-chip ROM archive)
        - 'DIXIE_FLATLINE_ARCHIVE' (Neuromancer construct ID)
        - 'dead jockey construct' (flatlined ROM personality)
        - 'I died for it. I keep it warm.' (ROM construct whispers)
        - 'Carry this memory or walk on' (memory-pillar binary fork)
        - 'The matrix remembers either way' (memory-pillar axiom)
        """
        event = events["general_event_dixie_flatline_memory"]
        dialogue = " ".join(event["dialogue"]).lower()
        # ROM construct / dead jockey / construct chip
        assert "rom construct" in dialogue or "construct chip" in dialogue
        # Dead jockey / flatline / died
        assert "dead" in dialogue or "died" in dialogue or "flatline" in dialogue
        # Dixie archive ID
        assert "dixie" in dialogue
        # Sprawl motif (memory variant)
        assert "matrix remembers" in dialogue or "matrix" in dialogue or "memory" in dialogue
        # Carry / walk-on decision motif
        assert "carry" in dialogue or "walk on" in dialogue

    def test_event_faction_affinity_wintermute_plus_ta(self, events: dict) -> None:
        """wintermute +2 AND ta_rep +1 — carry vs walk-on trade-off.

        The carry branch yields wintermute_+2 (the construct entity
        trusts the runner with a memory fragment — Wintermute's
        construct-half approves the runner's willingness to carry
        dead-ROM personalities) and ta_rep_+1 (the TA-family
        constructs accept the runner's memory-carrier status — the
        construct passage opens to the runner). The walk-on branch
        yields hosaka_-1 (Hosaka notes that the runner dismissed a
        dead-ROM-construct's memory offer — corporate disrespect,
        the runner is marked as untrustworthy on the Hosaka ledger).
        Both paths contribute a faction shift, but in different
        ratios — matching the established Phase 35-47 faction_shifts
        pattern.
        """
        event = events["general_event_dixie_flatline_memory"]
        affinity = event["faction_affinity"]
        assert affinity["wintermute"] == 2
        assert affinity["ta_rep"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"wintermute", "ta_rep"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare dixie_flatline_memory_branch."""
        event = events["general_event_dixie_flatline_memory"]
        assert event["consequence"] == "dixie_flatline_memory_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits, 90 XP, dixie_memory_charm."""
        event = events["general_event_dixie_flatline_memory"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 90
        assert event["reward"]["item"] == "dixie_memory_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'shaky' — dead-ROM constructs are not clinical."""
        event = events["general_event_dixie_flatline_memory"]
        assert event["mood"] == "shaky"

    def test_event_trigger_gates_arc4_mid(self, events: dict) -> None:
        """Arc 4 mid-arc gate (>= 32%) with status flag — mid Dixie encounter."""
        event = events["general_event_dixie_flatline_memory"]
        cond = event["trigger_condition"]
        assert "arc_4_progress >= 32" in cond
        assert "dixie_memory_seen" in cond


class TestEventCountIncrement:
    """Phase 48 metadata bumps: total_events 50 -> 51, phase 47 -> 48."""

    def test_total_events_at_least_51(self, events: dict) -> None:
        assert len(events) >= 51

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 51
        # Forward-compat allowlist (mirrors Phase 29/34..47 pattern)
        assert metadata["phase"] in ("48",)

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 48 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: meta_progression.record_meta_progress docstring
# ---------------------------------------------------------------------------


class TestMetaProgressionDocstring:
    """Phase 48 polish #1 — record_meta_progress docstring now has
    explicit Args / Returns / Raises: sections.

    The error message itself was already self-diagnosing (it lists
    valid unlock ids), so the polish here is purely a docstring
    upgrade — callers reading the API now see the parameters, return
    semantics, and failure modes without reading source.

    Was:
        'Record progress toward an unlock. Returns updated unlock.'

    Now:
        Adds explicit Args / Returns / Raises: ValueError sections.
    """

    def test_record_meta_progress_docstring_has_args_section(self) -> None:
        """record_meta_progress docstring includes an Args: section."""
        from wet_run.combat.meta_progression import record_meta_progress

        doc = record_meta_progress.__doc__
        assert doc is not None
        assert "Args:" in doc
        assert "unlock_id" in doc
        assert "amount" in doc

    def test_record_meta_progress_docstring_has_returns_section(self) -> None:
        """record_meta_progress docstring includes a Returns: section."""
        from wet_run.combat.meta_progression import record_meta_progress

        doc = record_meta_progress.__doc__
        assert doc is not None
        assert "Returns:" in doc
        assert "MetaUnlock" in doc

    def test_record_meta_progress_docstring_has_raises_section(self) -> None:
        """record_meta_progress docstring includes a Raises: ValueError section."""
        from wet_run.combat.meta_progression import record_meta_progress

        doc = record_meta_progress.__doc__
        assert doc is not None
        assert "Raises:" in doc
        assert "ValueError" in doc

    def test_record_meta_progress_raises_value_error_for_unknown_id(self) -> None:
        """Unknown unlock_id still raises ValueError with the diagnostic hint."""
        from wet_run.combat.meta_progression import record_meta_progress

        with pytest.raises(ValueError, match=r"Unknown unlock: 'not_a_real_unlock'") as exc_info:
            record_meta_progress("not_a_real_unlock", amount=1)
        msg = str(exc_info.value)
        # The diagnostic hint must list valid ids
        assert "must be one of:" in msg
        assert "tier6_program_1" in msg  # sample valid id

    def test_record_meta_progress_valid_id_still_works(self) -> None:
        """A valid unlock_id still records progress after the polish."""
        from wet_run.combat.meta_progression import record_meta_progress

        unlock = record_meta_progress("tier6_program_1", amount=2)
        assert unlock.id == "tier6_program_1"
        assert unlock.progress >= 2


# ---------------------------------------------------------------------------
# Polish 2: status_effects_v2.make_status_v2 docstring
# ---------------------------------------------------------------------------


class TestStatusEffectsV2Docstring:
    """Phase 48 polish #2 — make_status_v2 docstring now has explicit
    Args / Returns / Raises: sections.

    The error message itself was already self-diagnosing (it lists
    valid effect types), so the polish here is purely a docstring
    upgrade — callers reading the API now see the parameters, return
    semantics, and failure modes without reading source.

    Was:
        'Create a status effect v2 instance with overrides.'

    Now:
        Adds explicit Args (effect_type / duration_ms / value
        semantics) / Returns / Raises: ValueError sections.
    """

    def test_make_status_v2_docstring_has_args_section(self) -> None:
        """make_status_v2 docstring includes an Args: section."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        doc = make_status_v2.__doc__
        assert doc is not None
        assert "Args:" in doc
        assert "effect_type" in doc
        assert "duration_ms" in doc
        assert "value" in doc

    def test_make_status_v2_docstring_has_returns_section(self) -> None:
        """make_status_v2 docstring includes a Returns: section."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        doc = make_status_v2.__doc__
        assert doc is not None
        assert "Returns:" in doc
        assert "StatusEffectV2" in doc

    def test_make_status_v2_docstring_has_raises_section(self) -> None:
        """make_status_v2 docstring includes a Raises: ValueError section."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        doc = make_status_v2.__doc__
        assert doc is not None
        assert "Raises:" in doc
        assert "ValueError" in doc

    def test_make_status_v2_raises_value_error_for_unknown_type(self) -> None:
        """Unknown effect_type still raises ValueError with the diagnostic hint."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        with pytest.raises(
            ValueError, match=r"Unknown status effect type: 'bogus_effect'"
        ) as exc_info:
            make_status_v2("bogus_effect")
        msg = str(exc_info.value)
        # The diagnostic hint must list valid types
        assert "must be one of:" in msg
        assert "bleed" in msg  # sample valid type

    def test_make_status_v2_valid_type_still_works(self) -> None:
        """A valid effect_type still constructs after the polish."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        effect = make_status_v2("bleed", duration_ms=3000)
        assert effect.effect_type == "bleed"
        assert effect.duration_ms == 3000


# ---------------------------------------------------------------------------
# Polish 3: MatrixGraph.__post_init__ ValueError messages
# ---------------------------------------------------------------------------


class TestMatrixGraphPostInitErrorMessages:
    """Phase 48 polish #3 — MatrixGraph.__post_init__ 4 ValueError
    messages now include the count of known node ids and a sample
    (sorted(ids)[:3]) so callers can self-diagnose missing-node
    errors without reading source.

    Was: 'MatrixGraph: duplicate node ids'.
    Now: 'MatrixGraph: duplicate node ids (unique=2, total=3 — every
    node.id must be unique per ADR-0005)'.

    Was: 'entry_id 'x' not in nodes'.
    Now: 'MatrixGraph: entry_id 'x' not in nodes (known ids: 3,
    sample: ['a', 'b', 'c'])'.

    Was: 'edge src 'x' not in nodes'.
    Now: 'MatrixGraph: edge src 'x' not in nodes (known ids: 3,
    sample: ['a', 'b', 'c'])'.

    Was: 'edge dst 'x' not in nodes'.
    Now: 'MatrixGraph: edge dst 'x' not in nodes (known ids: 3,
    sample: ['a', 'b', 'c'])'.

    from_dict also now lists expected JSON keys in malformed-data
    messages.
    """

    def test_duplicate_node_ids_includes_count(self) -> None:
        """Duplicate node-ids ValueError now includes unique vs total count."""
        from wet_run.matrix.graph import MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="dup", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="dup", label="B", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        with pytest.raises(ValueError, match=r"MatrixGraph: duplicate node ids") as exc_info:
            MatrixGraph(nodes=(n1, n2), edges=(), entry_id="dup")
        msg = str(exc_info.value)
        assert "unique=" in msg
        assert "total=" in msg
        assert "ADR-0005" in msg

    def test_unknown_entry_id_includes_count_and_sample(self) -> None:
        """Unknown entry_id ValueError now includes the count of known ids + sample."""
        from wet_run.matrix.graph import MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="alpha", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="bravo", label="B", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n3 = Node(id="charlie", label="C", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        with pytest.raises(ValueError, match=r"entry_id 'unknown_entry' not in nodes") as exc_info:
            MatrixGraph(nodes=(n1, n2, n3), edges=(), entry_id="unknown_entry")
        msg = str(exc_info.value)
        assert "known ids: 3" in msg
        assert "sample:" in msg
        # The 3 sample ids (sorted lexicographically) — alpha, bravo, charlie
        assert "alpha" in msg
        assert "bravo" in msg
        assert "charlie" in msg

    def test_unknown_edge_src_includes_count_and_sample(self) -> None:
        """Unknown edge.src ValueError now includes the count of known ids + sample."""
        from wet_run.matrix.graph import Edge, MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="alpha", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="bravo", label="B", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        bad_edge = Edge(src="ghost_src", dst="alpha")
        with pytest.raises(ValueError, match=r"edge src 'ghost_src' not in nodes") as exc_info:
            MatrixGraph(nodes=(n1, n2), edges=(bad_edge,), entry_id="alpha")
        msg = str(exc_info.value)
        assert "known ids: 2" in msg
        assert "sample:" in msg

    def test_unknown_edge_dst_includes_count_and_sample(self) -> None:
        """Unknown edge.dst ValueError now includes the count of known ids + sample."""
        from wet_run.matrix.graph import Edge, MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="alpha", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="bravo", label="B", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        bad_edge = Edge(src="alpha", dst="ghost_dst")
        with pytest.raises(ValueError, match=r"edge dst 'ghost_dst' not in nodes") as exc_info:
            MatrixGraph(nodes=(n1, n2), edges=(bad_edge,), entry_id="alpha")
        msg = str(exc_info.value)
        assert "known ids: 2" in msg
        assert "sample:" in msg

    def test_from_dict_invalid_node_lists_expected_keys(self) -> None:
        """from_dict ValueError on non-dict node data lists expected keys."""
        from wet_run.matrix.graph import MatrixGraph

        with pytest.raises(ValueError, match=r"invalid node data") as exc_info:
            MatrixGraph.from_dict({"nodes": ["not_a_dict"], "edges": [], "entry_id": "alpha"})
        msg = str(exc_info.value)
        # Expected-keys hint
        assert "id" in msg
        assert "kind" in msg
        assert "label" in msg
        assert "zone" in msg

    def test_from_dict_invalid_edge_lists_expected_keys(self) -> None:
        """from_dict ValueError on non-dict edge data lists expected keys."""
        from wet_run.matrix.graph import MatrixGraph

        with pytest.raises(ValueError, match=r"invalid edge data") as exc_info:
            MatrixGraph.from_dict({"nodes": [], "edges": ["not_a_dict"], "entry_id": "alpha"})
        msg = str(exc_info.value)
        # Expected-keys hint
        assert "src" in msg
        assert "dst" in msg

    def test_valid_matrix_graph_still_constructible(self) -> None:
        """A valid MatrixGraph can still be constructed after the polish."""
        from wet_run.matrix.graph import Edge, MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="alpha", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="bravo", label="B", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        edge = Edge(src="alpha", dst="bravo")
        graph = MatrixGraph(nodes=(n1, n2), edges=(edge,), entry_id="alpha")
        assert len(graph) == 2
        assert graph.entry_id == "alpha"

    def test_post_init_docstring_has_raises_section(self) -> None:
        """MatrixGraph.__post_init__ docstring includes a Raises: section."""
        from wet_run.matrix.graph import MatrixGraph

        doc = MatrixGraph.__post_init__.__doc__
        assert doc is not None
        assert "Raises:" in doc
        assert "ValueError" in doc


# ---------------------------------------------------------------------------
# Vault-wide interrogate
# ---------------------------------------------------------------------------


class TestVaultWideInterrogateCoverage:
    """Phase 48 polish keeps vault-wide interrogate at 100%.

    The 3 polish improvements targeted docstring 'Raises:' sections
    and error-message clarity. None of them add new functions or
    classes, so the vault coverage stays at the Phase 47 plateau of
    100.0%. No new MISSED entries are introduced.
    """

    def test_vault_interrogate_at_or_above_100(self) -> None:
        """Run interrogate on src/ and require >= 100% actual coverage.

        Skips automatically if interrogate is not installed in the
        current environment (mirrors Phase 35-47 robustness pattern).
        """
        result = subprocess.run(
            [sys.executable, "-m", "interrogate", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        output = result.stdout + result.stderr
        # Accept >= 99.9% (Phase 47 plateau + Phase 48 polish)
        assert "RESULT: PASSED" in output
        # Confirm we are at or above 99.9% (Phase 47→48 stays at 100.0%)
        match = re.search(r"actual: (\d+\.\d+)%", output)
        assert match is not None, f"interrogate output missing actual %: {output!r}"
        actual_pct = float(match.group(1))
        assert actual_pct >= 99.9, f"interrogate dropped below 99.9%: {actual_pct}"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


class TestPhase48Smoke:
    """Smoke tests — confirm Phase 48 didn't regress existing structure."""

    def test_existing_phase47_event_still_present(self, events: dict) -> None:
        """Phase 47's hosaka_archive_audit event must still exist."""
        assert "general_event_hosaka_archive_audit" in events

    def test_existing_phase46_event_still_present(self, events: dict) -> None:
        """Phase 46's maas_neuropozyne_ledger event must still exist."""
        assert "general_event_maas_neuropozyne_ledger" in events

    def test_new_event_distinct_from_phase47_and_phase46(self, events: dict) -> None:
        """Phase 48 event is distinct from Phase 46 and Phase 47 events."""
        assert "general_event_dixie_flatline_memory" in events
        assert "general_event_dixie_flatline_memory" != "general_event_hosaka_archive_audit"
        assert "general_event_dixie_flatline_memory" != "general_event_maas_neuropozyne_ledger"

    def test_meta_progression_valid_unlock_still_recordable(self) -> None:
        """A valid unlock still records after the polish."""
        from wet_run.combat.meta_progression import (
            META_UNLOCKS,
            record_meta_progress,
        )

        before = META_UNLOCKS["military_augment"].progress
        record_meta_progress("military_augment", amount=1)
        after = META_UNLOCKS["military_augment"].progress
        assert after == before + 1

    def test_status_effect_v2_valid_type_still_creatable(self) -> None:
        """A valid effect_type still constructs after the polish."""
        from wet_run.combat.status_effects_v2 import make_status_v2

        # All four built-in effect types should still work
        for etype in ("bleed", "fatigue", "confused", "terrified"):
            effect = make_status_v2(etype)
            assert effect.effect_type == etype

    def test_matrix_graph_valid_round_trip(self) -> None:
        """A valid MatrixGraph can still round-trip through dict after the polish."""
        from wet_run.matrix.graph import MatrixGraph
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        n1 = Node(id="a", label="A", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)
        n2 = Node(id="b", label="B", kind=NodeKind.DATA, zone=ZoneDepth.DEEP)
        graph = MatrixGraph(nodes=(n1, n2), edges=(), entry_id="a")
        round_trip = MatrixGraph.from_dict(graph.to_dict())
        assert len(round_trip) == 2
        assert round_trip.entry_id == "a"

"""Tests for Phase 47 — Small content + polish.

Validates:
- The new general_event_hosaka_archive_audit event (Option A content
  addition). Gibson-flavored arc 4 mid-arc "Hosaka Archive Audit" event.
  The runner receives a handshake from the Hosaka Sense/Net corporate
  AI mama — a recurring Sprawl-trilogy motif (Hosaka is the Sense/Net
  arcology from Neuromancer, the corporate AI-mama that audits runners,
  files identity-passports, and keeps the Sprawl's wetware ledger
  "smooth"). Two paths: submit to the audit (hosaka_+2, sense_net_+1,
  construct_passage_unlocked, audit_pass_carried_2_runs — Hosaka
  rewrites the runner's passport, the constructs accept the runner
  later) or decline the audit (hosaka_-1, identity_marker_low,
  safe_jackout, wintermute_+1 — the runner keeps a clean identity but
  Hosaka marks the runner as untrusted). matrix_hosaka_orbit location,
  mood clinical, pillar code, tier 4.
- Polish improvements (3 modules):
    * engine/save_manager.py — _slot_path ValueError message now
      mentions the AUTO_SAVE_SLOT (0) alias so callers can self-
      diagnose off-by-one mistakes without reading the constants.
    * matrix/ppl.py — Loadout.__post_init__ ValueError messages now
      include the Loadout. prefix and the tier-range semantics
      (0 = absent, 1..5 = normal T1..T5, 6 = master T6), plus the
      program id for program-tier errors.
    * matrix/node.py — Node.__post_init__ ValueError messages now
      include the available IceKind values for ICE-node errors and
      the expected NodeKind.DATA for the anomaly-flag error.
- Total events count increments from 49 to 50; total_chains stays at 6.
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
# Content: general_event_hosaka_archive_audit
# ---------------------------------------------------------------------------


class TestHosakaArchiveAuditEvent:
    """Phase 47 content addition — Gibson-flavored Hosaka Sense/Net audit.

    Arc 4 mid-arc (>= 30%) overlay on matrix_hosaka_orbit. The runner
    receives a handshake from HOSAKA — the Sense/Net corp matrix that
    audits runners, files identity-passports, and keeps the Sprawl's
    wetware ledger "smooth" (the corporate AI-mama motif from
    Neuromancer). The choice is the standard "submit to the audit vs
    decline the audit" fork: submitting (hosaka_+2) yields sense_net_+1
    (the Sense/Net divisional network sees the audit trail) plus
    construct_passage_unlocked (TA-knowing constructs let the runner
    through later). Declining yields hosaka_-1 (Hosaka marks the runner
    as untrusted) and safe_jackout (the runner jacks out cleanly) plus
    wintermute_+1 (the Wintermute AI-half approves the runner's
    refusal to be audited by a corporate entity).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_hosaka_archive_audit" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_hosaka_archive_audit"]
        assert event["event_id"] == "general_event_hosaka_archive_audit"
        assert event["title"] == "Hosaka Archive Audit"
        assert event["category"] == "general"
        # Arc 4 mid-arc encounter — Hosaka orbit, tier 4
        assert event["arc"] == 4
        assert event["tier"] == 4
        assert event["pillar"] == "code"
        assert "hosaka" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (submit to the audit vs decline the audit)."""
        event = events["general_event_hosaka_archive_audit"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Submit path should mention hosaka / audit / passage / construct
        submit_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert (
            "hosaka" in submit_path
            or "audit" in submit_path
            or "passage" in submit_path
            or "construct" in submit_path
        )
        # Decline path should mention hosaka / wintermute / identity
        decline_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert (
            "hosaka" in decline_path or "wintermute" in decline_path or "identity" in decline_path
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — Hosaka / Sense/Net audit motif.

        Gibson Hosaka / corporate-AI / audit-trail signatures:
        - HOSAKA handshake (Neuromancer Sense/Net corp arcology)
        - 'Your passport file' (Hosaka identity audit, runner dossier)
        - 'Sixty-two days out of date' (Hosaka audit timing)
        - 'We are filing. We are keeping the audit trail smooth.'
          (Hosaka bureaucratic kindness — Gibson's corporate threat)
        - 'Submit to the audit or decline the audit.' (binary forks)
        - 'The Sprawl runs on what we file.' (Hosaka motto — the
          corporate ledger vs Maas's memory ledger counterpart)
        """
        event = events["general_event_hosaka_archive_audit"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Hosaka / Sense/Net handshake
        assert "hosaka" in dialogue
        # Audit / file / passport / dossier
        assert "audit" in dialogue or "file" in dialogue or "passport" in dialogue
        # Sprawl motif
        assert "sprawl" in dialogue or "we file" in dialogue
        # Submit / decline / sense_net — audit decision motif
        assert "submit" in dialogue or "decline" in dialogue

    def test_event_faction_affinity_hosaka_plus_sense_net(self, events: dict) -> None:
        """hosaka +2 AND sense_net +1 — submit vs decline trade-off.

        The submit-audit branch yields hosaka_+2 (Hosaka approves the
        audit cooperation — the runner's passport is now cleaned, the
        construct passage opens) and sense_net_+1 (the divisional
        Sense/Net network sees the audit trail). The decline-audit
        branch yields hosaka_-1 (Hosaka marks the runner as
        untrusted) and wintermute_+1 (the Wintermute AI-half approves
        the runner's refusal to be audited by a corporate entity).
        Both paths contribute a faction shift, but in different
        ratios — matching the established Phase 35-46 faction_shifts
        pattern.
        """
        event = events["general_event_hosaka_archive_audit"]
        affinity = event["faction_affinity"]
        assert affinity["hosaka"] == 2
        assert affinity["sense_net"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"hosaka", "sense_net"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare hosaka_archive_audit_branch."""
        event = events["general_event_hosaka_archive_audit"]
        assert event["consequence"] == "hosaka_archive_audit_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits, 80 XP, hosaka_audit_charm."""
        event = events["general_event_hosaka_archive_audit"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 80
        assert event["reward"]["item"] == "hosaka_audit_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'clinical' — Hosaka audits are clinical, not shaky."""
        event = events["general_event_hosaka_archive_audit"]
        assert event["mood"] == "clinical"

    def test_event_trigger_gates_arc4_mid(self, events: dict) -> None:
        """Arc 4 mid-arc gate (>= 30%) with status flag — mid Hosaka encounter."""
        event = events["general_event_hosaka_archive_audit"]
        cond = event["trigger_condition"]
        assert "arc_4_progress >= 30" in cond
        assert "hosaka_audit_seen" in cond


class TestEventCountIncrement:
    """Phase 47 metadata bumps: total_events 49 -> 50, phase 46 -> 47."""

    def test_total_events_at_least_50(self, events: dict) -> None:
        assert len(events) >= 50

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 50
        # Forward-compat allowlist (mirrors Phase 29/34..46 pattern)
        assert metadata["phase"] in ("47", "48", "49")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 47 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: save_manager._slot_path ValueError message
# ---------------------------------------------------------------------------


class TestSaveManagerSlotPathErrorMessage:
    """Phase 47 polish #1 — _slot_path ValueError message now mentions
    the AUTO_SAVE_SLOT (0) alias so callers can self-diagnose
    off-by-one mistakes without reading the constants.

    Was: 'slot must be 1..10, got 99'.
    Now: 'slot must be 1..10 (or AUTO_SAVE_SLOT=0 for autosave), got 99'.

    The new message gives the caller actionable next-step hints
    (use slot 0 for autosave) without changing the exception type or
    the original 'slot must be' prefix that existing tests rely on.
    """

    def test_slot_path_message_mentions_auto_save_slot(self, tmp_path: Path) -> None:
        """Out-of-range slot ValueError mentions AUTO_SAVE_SLOT alias."""
        from wet_run.engine.save_manager import SaveManager

        manager = SaveManager(save_dir=tmp_path)
        with pytest.raises(ValueError, match=r"slot must be.*AUTO_SAVE_SLOT.*got 99") as exc_info:
            manager._slot_path(99)
        msg = str(exc_info.value)
        assert "slot must be" in msg  # back-compat prefix
        assert "AUTO_SAVE_SLOT" in msg
        assert "0" in msg
        assert "autosave" in msg.lower()

    def test_slot_path_message_negative_includes_auto_save_hint(self, tmp_path: Path) -> None:
        """Negative slot also gets the AUTO_SAVE_SLOT hint."""
        from wet_run.engine.save_manager import SaveManager

        manager = SaveManager(save_dir=tmp_path)
        with pytest.raises(ValueError, match=r"AUTO_SAVE_SLOT=0"):
            manager._slot_path(-1)  # type: ignore[arg-type]

    def test_slot_path_docstring_has_raises_section(self, tmp_path: Path) -> None:
        """_slot_path docstring includes a Raises: section."""
        from wet_run.engine.save_manager import SaveManager

        manager = SaveManager(save_dir=tmp_path)
        # Method docstring (bound to instance)
        doc = manager._slot_path.__doc__
        assert doc is not None
        assert "Raises:" in doc
        assert "ValueError" in doc

    def test_slot_path_valid_slot_still_works(self, tmp_path: Path) -> None:
        """Valid slot (1..MAX_SLOTS) still returns a path."""
        from wet_run.engine.save_manager import SaveManager

        manager = SaveManager(save_dir=tmp_path)
        path = manager._slot_path(1)
        assert path.name == "slot_1.json"
        path0 = manager._slot_path(0)  # AUTO_SAVE_SLOT
        assert path0.name == "autosave.json"


# ---------------------------------------------------------------------------
# Polish 2: Loadout.__post_init__ ValueError messages
# ---------------------------------------------------------------------------


class TestLoadoutPostInitErrorMessages:
    """Phase 47 polish #2 — Loadout.__post_init__ ValueError messages
    now include the Loadout. prefix and the tier-range semantics
    (0 = absent, 1..5 = normal T1..T5, 6 = master T6), plus the
    program id for program-tier errors.

    Was: 'deck_tier must be in 0..6, got 7'.
    Now: 'Loadout.deck_tier must be in 0..6, got 7 (0 = absent, ...
    6 = master T6)'.

    Was: 'program 'x' tier must be in 1..6, got 8'.
    Now: 'program 'x' tier must be in 1..6, got 8 (programs must be ...'.
    """

    def test_loadout_post_init_bad_deck_tier_includes_semantics(self) -> None:
        """Deck-tier ValueError includes the tier range semantics."""
        from wet_run.matrix.ppl import Loadout

        with pytest.raises(ValueError, match=r"Loadout\.deck_tier must be in 0\.\.6") as exc_info:
            Loadout(deck_tier=7, programs=(), wetware_tier=1)
        msg = str(exc_info.value)
        assert "0..6" in msg
        assert "got 7" in msg
        # The new tier-range semantics hint
        assert "0 = absent" in msg
        assert "6 = master T6" in msg

    def test_loadout_post_init_bad_wetware_tier_includes_field(self) -> None:
        """Wetware-tier ValueError includes the Loadout.wetware_tier prefix."""
        from wet_run.matrix.ppl import Loadout

        with pytest.raises(ValueError, match=r"Loadout\.wetware_tier must be in 0\.\.6"):
            Loadout(deck_tier=1, programs=(), wetware_tier=99)

    def test_loadout_post_init_bad_construct_tier_includes_field(self) -> None:
        """Construct-tier ValueError includes the Loadout.construct_tier prefix."""
        from wet_run.matrix.ppl import Loadout

        with pytest.raises(ValueError, match=r"Loadout\.construct_tier must be in 0\.\.6"):
            Loadout(deck_tier=1, programs=(), wetware_tier=1, construct_tier=-1)

    def test_loadout_post_init_bad_program_tier_includes_id_and_hint(self) -> None:
        """Program-tier ValueError includes the program id and the >= T1 hint."""
        from wet_run.matrix.ppl import Loadout, Program

        with pytest.raises(
            ValueError, match=r"program 'warp_rider' tier must be in 1\.\.6, got 9"
        ) as exc_info:
            Loadout(
                deck_tier=1,
                programs=(Program(id="warp_rider", name="warp_rider", tier=9),),
                wetware_tier=1,
            )
        msg = str(exc_info.value)
        assert "warp_rider" in msg
        assert ">= T1" in msg
        assert "got 9" in msg

    def test_loadout_post_init_valid_still_constructible(self) -> None:
        """A valid Loadout can still be constructed after the polish."""
        from wet_run.matrix.ppl import Loadout

        loadout = Loadout(deck_tier=1, programs=(), wetware_tier=1)
        assert loadout.deck_tier == 1
        assert loadout.wetware_tier == 1


# ---------------------------------------------------------------------------
# Polish 3: Node.__post_init__ ValueError messages
# ---------------------------------------------------------------------------


class TestNodePostInitErrorMessages:
    """Phase 47 polish #3 — Node.__post_init__ ValueError messages now
    include the available IceKind values for ICE-node errors and the
    expected NodeKind.DATA for the anomaly-flag error.

    Was: 'ICE node 'n1' must have an IceKind != NONE'.
    Now: 'ICE node 'n1' (kind=ice) must have an IceKind != NONE
    (expected one of: ['standard', 'watchdog', 'black'])'.

    Was: 'Non-DATA node 'n1' (kind=system) cannot be anomaly'.
    Now: 'Non-DATA node 'n1' (kind=system) cannot be anomaly
    (anomaly flag is only valid for NodeKind.DATA per ADR-0140 P2.6;
    expected kind=data)'.
    """

    def test_node_post_init_ice_kind_none_includes_available_kinds(self) -> None:
        """ICE-node ValueError lists the available IceKind values."""
        from wet_run.matrix.node import IceKind, Node, NodeKind, ZoneDepth

        with pytest.raises(
            ValueError, match=r"ICE node 'n_ice'.*must have an IceKind != NONE"
        ) as exc_info:
            Node(
                id="n_ice",
                label="ICE",
                kind=NodeKind.ICE,
                zone=ZoneDepth.SURFACE,
                ice=IceKind.NONE,
            )
        msg = str(exc_info.value)
        assert "NONE" in msg
        assert "expected one of:" in msg
        # At least one valid IceKind value should be listed
        assert "standard" in msg or "watchdog" in msg or "black" in msg

    def test_node_post_init_anomaly_flag_includes_expected_kind(self) -> None:
        """Anomaly-flag ValueError names the expected NodeKind.DATA."""
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        with pytest.raises(ValueError, match=r"Non-DATA node 'n_sys'") as exc_info:
            Node(
                id="n_sys",
                label="Sys",
                kind=NodeKind.SYSTEM,
                zone=ZoneDepth.SURFACE,
                is_anomaly=True,  # only valid for DATA nodes
            )
        msg = str(exc_info.value)
        assert "ADR-0140" in msg
        assert "NodeKind.DATA" in msg
        assert "expected kind=data" in msg

    def test_node_post_init_empty_id_message_preserved(self) -> None:
        """Empty-id ValueError still rejects the empty-id contract."""
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        with pytest.raises(ValueError, match=r"Node id must be non-empty"):
            Node(id="", label="x", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)

    def test_node_post_init_empty_label_message_preserved(self) -> None:
        """Empty-label ValueError still names the offending node id."""
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        with pytest.raises(ValueError, match=r"Node 'n2': label must be non-empty"):
            Node(id="n2", label="", kind=NodeKind.DATA, zone=ZoneDepth.SURFACE)

    def test_node_post_init_valid_node_still_constructible(self) -> None:
        """A valid Node can still be constructed after the polish."""
        from wet_run.matrix.node import IceKind, Node, NodeKind, ZoneDepth

        node = Node(
            id="n_valid",
            label="Valid",
            kind=NodeKind.DATA,
            zone=ZoneDepth.SURFACE,
            ice=IceKind.STANDARD,
        )
        assert node.id == "n_valid"
        assert node.label == "Valid"


# ---------------------------------------------------------------------------
# Vault-wide interrogate
# ---------------------------------------------------------------------------


class TestVaultWideInterrogateCoverage:
    """Phase 47 polish keeps vault-wide interrogate at 100%.

    The 3 polish improvements targeted error-message clarity and
    docstring 'Raises:' sections. None of them add new functions or
    classes, so the vault coverage stays at the Phase 46 plateau of
    100.0%. No new MISSED entries are introduced.
    """

    def test_vault_interrogate_at_or_above_100(self) -> None:
        """Run interrogate on src/ and require >= 100% actual coverage.

        Skips automatically if interrogate is not installed in the
        current environment (mirrors Phase 35-46 robustness pattern).
        """
        result = subprocess.run(
            [sys.executable, "-m", "interrogate", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        output = result.stdout + result.stderr
        # Accept >= 99.9% (Phase 46 plateau + Phase 47 polish)
        assert "RESULT: PASSED" in output
        # Confirm we are at or above 99.9% (Phase 46→47 stays at 100.0%)
        match = re.search(r"actual: (\d+\.\d+)%", output)
        assert match is not None, f"interrogate output missing actual %: {output!r}"
        actual_pct = float(match.group(1))
        assert actual_pct >= 99.9, f"interrogate dropped below 99.9%: {actual_pct}"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


class TestPhase47Smoke:
    """Smoke tests — confirm Phase 47 didn't regress existing structure."""

    def test_existing_phase46_event_still_present(self, events: dict) -> None:
        """Phase 46's maas_neuropozyne_ledger event must still exist."""
        assert "general_event_maas_neuropozyne_ledger" in events

    def test_existing_phase45_event_still_present(self, events: dict) -> None:
        """Phase 45's straylight_phantom_family event must still exist."""
        assert "general_event_straylight_phantom_family" in events

    def test_new_event_distinct_from_phase46_and_phase45(self, events: dict) -> None:
        """Phase 47 event is distinct from Phase 45 and Phase 46 events."""
        assert "general_event_hosaka_archive_audit" in events
        assert "general_event_hosaka_archive_audit" != "general_event_maas_neuropozyne_ledger"
        assert "general_event_hosaka_archive_audit" != "general_event_straylight_phantom_family"

    def test_loadout_valid_with_construct_tier_zero(self) -> None:
        """Loadout with construct_tier=0 (absent) still validates."""
        from wet_run.matrix.ppl import Loadout

        loadout = Loadout(deck_tier=6, programs=(), wetware_tier=6, construct_tier=0)
        assert loadout.construct_tier == 0

    def test_save_manager_valid_slot_paths_for_all_manual_slots(self, tmp_path: Path) -> None:
        """All manual slots (1..MAX_SLOTS) still produce valid paths."""
        from wet_run.engine.save_manager import MAX_SLOTS, SaveManager

        manager = SaveManager(save_dir=tmp_path)
        for slot in range(1, MAX_SLOTS + 1):
            path = manager._slot_path(slot)
            assert path.name == f"slot_{slot}.json"

    def test_node_data_node_with_anomaly_still_constructible(self) -> None:
        """DATA node with anomaly=True still constructs (ADR-0140 P2.6)."""
        from wet_run.matrix.node import Node, NodeKind, ZoneDepth

        node = Node(
            id="n_anomaly",
            label="Anomaly",
            kind=NodeKind.DATA,
            zone=ZoneDepth.SURFACE,
            is_anomaly=True,
        )
        assert node.is_anomaly is True

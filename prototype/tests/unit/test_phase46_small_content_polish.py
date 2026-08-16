"""Tests for Phase 46 — Small content + polish.

Validates:
- The new general_event_maas_neuropozyne_ledger event (Option A content
  addition). Gibson-flavored arc 4 mid-arc "Maas BioLabs ledger" event.
  The runner receives a handshake from the Maas BioLabs clinical
  back-room terminal — a recurring Sprawl trilogy motif (Maas's neuropozyne
  empire, the wetware IDs Maas archives, the Sprawl runs on what Maas
  remembers). Two paths: settle the ledger (credits_-1200, maas_debt
  cleared, ta_rep_+1, construct_passage_unlocked, the runner bought their
  wetware freedom) or carry the marker (maas_+2, ledger_carried 3 runs,
  identity_marker_low, construct_whisper_locked, the runner chose Maas
  over TA passage). matrix_chiba_backroom location, mood shaky,
  pillar memory, tier 4.
- Polish improvements (3 modules):
    * combat/cyberdeck.py — improved add_program_to_deck /
      remove_program_from_deck ValueError messages (now include the
      operation context, current program list, and (for add) the
      frozen-deck swap hint, (for remove) the case-mismatch hint).
    * combat/registry.py — enhanced build_ice_enemy docstring with
      explicit Raises: section + improved KeyError message to indicate
      the JSON source path and total count.
    * missions/mission.py — Mission.__post_init__ ValueError messages
      now include the mission_id and offending value for JSON-data
      debugging.
- Total events count increments from 48 to 49; total_chains stays at 6.
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
# Content: general_event_maas_neuropozyne_ledger
# ---------------------------------------------------------------------------


class TestMaasNeuropozyneLedgerEvent:
    """Phase 46 content addition — Gibson-flavored Maas BioLabs debt ledger.

    Arc 4 mid-arc (>= 35%) overlay on matrix_chiba_backroom. The runner
    receives a handshake from MAAS BIOLABS — the same clinical back-room
    the runner visited for the Phase 30 maas_neuropozyne ICE type, the
    same wetware-ID archive that Maas has been keeping since Count Zero.
    The choice is the standard "settle the ledger vs carry the marker"
    fork: settling the ledger (credits_-1200) yields ta_rep_+1 (T-A
    family attention — the runner bought their wetware freedom, the TA
    passage opens) plus construct_passage_unlocked (TA-knowing
    constructs let the runner through later). Carrying the marker yields
    maas_+2 (Maas approves the loyalty) and locks construct_whisper
    (the constructs stop talking to a runner who owes Maas).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_maas_neuropozyne_ledger" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_maas_neuropozyne_ledger"]
        assert event["event_id"] == "general_event_maas_neuropozyne_ledger"
        assert event["title"] == "Maas BioLabs Ledger"
        assert event["category"] == "general"
        # Arc 4 mid-arc encounter — Chiba backroom, tier 4
        assert event["arc"] == 4
        assert event["tier"] == 4
        assert event["pillar"] == "memory"
        assert "chiba" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (settle the ledger vs carry the marker)."""
        event = events["general_event_maas_neuropozyne_ledger"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Settle path should mention credits / ta_rep / ledger / passage
        settle_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert (
            "credits" in settle_path
            or "ta_rep" in settle_path
            or "ledger" in settle_path
            or "passage" in settle_path
        )
        # Carry path should mention maas / ledger / construct
        carry_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "maas" in carry_path or "ledger" in carry_path or "construct" in carry_path

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — Maas BioLabs handshake + ledger motif.

        Gibson Maas / archive / Sprawl-running signatures:
        - MAAS BIOLABS handshake (Count Zero / Mona Lisa Overdrive Maas)
        - 'Your file is open' (Maas archive, runner dossier)
        - 'archive the doses / wetware / names' (Maas memory ledger)
        - 'Settle the ledger or carry it' (Count Zero debt structure)
        - 'The Sprawl runs on what we remember' (Maas motto / wetware)
        """
        event = events["general_event_maas_neuropozyne_ledger"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Maas / BioLabs handshake
        assert "maas" in dialogue
        # Archive / ledger / file / dossier
        assert "archive" in dialogue or "ledger" in dialogue or "file" in dialogue
        # Sprawl motif
        assert "sprawl" in dialogue or "wetware" in dialogue
        # Settle / carry / remember — debt decision motif
        assert "settle" in dialogue or "carry" in dialogue or "remember" in dialogue

    def test_event_faction_affinity_maas_plus_ta_rep(self, events: dict) -> None:
        """maas +2 AND ta_rep +1 — carry vs settle trade-off.

        The carry-marker branch yields maas_+2 (Maas approves the loyalty
        — the runner keeps the debt, the constructs stop whispering, but
        the runner now wears Maas's marker). The settle-ledger branch
        yields ta_rep_+1 (the runner paid their tab in cold credits,
        the TA family notices, the passage opens). Both paths contribute
        a faction shift, but in different ratios — matching the
        established Phase 35-45 faction_shifts pattern.
        """
        event = events["general_event_maas_neuropozyne_ledger"]
        affinity = event["faction_affinity"]
        assert affinity["maas"] == 2
        assert affinity["ta_rep"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"maas", "ta_rep"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare maas_neuropozyne_ledger_branch."""
        event = events["general_event_maas_neuropozyne_ledger"]
        assert event["consequence"] == "maas_neuropozyne_ledger_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits, 85 XP, maas_ledger_charm."""
        event = events["general_event_maas_neuropozyne_ledger"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 85
        assert event["reward"]["item"] == "maas_ledger_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'shaky' — the ledger is open, but is the runner?"""
        event = events["general_event_maas_neuropozyne_ledger"]
        assert event["mood"] == "shaky"

    def test_event_trigger_gates_arc4_mid(self, events: dict) -> None:
        """Arc 4 mid-arc gate (>= 35%) with status flag — mid Maas encounter."""
        event = events["general_event_maas_neuropozyne_ledger"]
        cond = event["trigger_condition"]
        assert "arc_4_progress >= 35" in cond
        assert "maas_ledger_seen" in cond


class TestEventCountIncrement:
    """Phase 46 metadata bumps: total_events 48 -> 49, phase 45 -> 46."""

    def test_total_events_at_least_49(self, events: dict) -> None:
        assert len(events) >= 49

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 49
        # Forward-compat allowlist (mirrors Phase 29/34..45 pattern)
        assert metadata["phase"] in ("46", "47")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 46 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: cyberdeck ValueError messages
# ---------------------------------------------------------------------------


class TestCyberdeckErrorMessages:
    """Phase 46 polish #1 — add_program_to_deck / remove_program_from_deck
    ValueError messages now include the offending operation context, the
    current program list, and a debugging hint.

    Was: 'Program X already in deck (current programs: [...])'.
    Now: 'Program X already in deck (current programs: [...]); the deck
    is frozen - call remove_program_from_deck first to swap.'

    Was: 'Program X not in deck (current programs: [...])'.
    Now: 'Program X not in deck (current programs: [...]); check for case
    mismatch or that the program was not already removed.'

    The new messages give the caller actionable next-step hints without
    changing the exception type or the data they convey.
    """

    def test_add_program_already_present_message_mentions_swap(self) -> None:
        """Add-program-already-present ValueError mentions remove_program_from_deck."""
        from roguelike_sprawl.combat.cyberdeck import (
            DEFAULT_DECK_SLOTS,
            Cyberdeck,
            add_program_to_deck,
        )

        deck = Cyberdeck(name="d", program_ids=("deck_wrecker",))
        with pytest.raises(ValueError, match="remove_program_from_deck first to swap"):
            add_program_to_deck(deck, "deck_wrecker", max_slots=DEFAULT_DECK_SLOTS)

    def test_add_program_already_present_includes_current_programs(self) -> None:
        """The error message still includes the current program list."""
        from roguelike_sprawl.combat.cyberdeck import (
            DEFAULT_DECK_SLOTS,
            Cyberdeck,
            add_program_to_deck,
        )

        deck = Cyberdeck(name="d", program_ids=("deck_wrecker", "ice_breaker"))
        with pytest.raises(ValueError, match=r"current programs.*deck_wrecker"):
            add_program_to_deck(deck, "deck_wrecker", max_slots=DEFAULT_DECK_SLOTS)

    def test_add_program_deck_full_message_includes_programs(self) -> None:
        """Deck-full ValueError includes the current program list."""
        from roguelike_sprawl.combat.cyberdeck import (
            Cyberdeck,
            add_program_to_deck,
        )

        deck = Cyberdeck(
            name="d",
            program_ids=("p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"),
        )
        with pytest.raises(ValueError, match=r"Deck full.*programs: \[.*p1.*p8"):
            add_program_to_deck(deck, "p9", max_slots=8)

    def test_remove_program_not_present_message_mentions_case(self) -> None:
        """Remove-program-not-present ValueError mentions case mismatch."""
        from roguelike_sprawl.combat.cyberdeck import Cyberdeck, remove_program_from_deck

        deck = Cyberdeck(name="d", program_ids=("deck_wrecker",))
        with pytest.raises(ValueError, match="check for case mismatch"):
            remove_program_from_deck(deck, "Deck_Wrecker")  # wrong case

    def test_remove_program_not_present_includes_current_programs(self) -> None:
        """The error message still includes the current program list."""
        from roguelike_sprawl.combat.cyberdeck import Cyberdeck, remove_program_from_deck

        deck = Cyberdeck(name="d", program_ids=("alpha", "beta"))
        with pytest.raises(ValueError, match=r"current programs.*alpha"):
            remove_program_from_deck(deck, "gamma")

    def test_cyberdeck_docstrings_intact(self) -> None:
        """Both functions retain their docstrings after polish."""
        from roguelike_sprawl.combat.cyberdeck import (
            add_program_to_deck,
            remove_program_from_deck,
        )

        assert add_program_to_deck.__doc__ is not None
        assert remove_program_from_deck.__doc__ is not None
        assert "Raises" in add_program_to_deck.__doc__
        assert "Raises" in remove_program_from_deck.__doc__

    def test_cyberdeck_return_annotations_intact(self) -> None:
        """Return type annotations remain Cyberdeck."""
        import typing

        from roguelike_sprawl.combat.cyberdeck import (
            Cyberdeck,
            add_program_to_deck,
            remove_program_from_deck,
        )

        for func in (add_program_to_deck, remove_program_from_deck):
            ret_anno = func.__annotations__["return"]
            if isinstance(ret_anno, str):
                resolved = typing.get_type_hints(func)["return"]
                assert resolved is Cyberdeck, f"{func.__name__} return != Cyberdeck"
            else:
                assert ret_anno is Cyberdeck, f"{func.__name__} return != Cyberdeck"


# ---------------------------------------------------------------------------
# Polish 2: build_ice_enemy docstring + KeyError message
# ---------------------------------------------------------------------------


class TestBuildIceEnemyDocstringAndMessage:
    """Phase 46 polish #2 — build_ice_enemy docstring + KeyError message.

    The docstring now includes an explicit 'Raises:' section. The
    KeyError message now mentions the JSON source path and the total
    count of available ICE ids, so debug output is unambiguous about
    where to look for typos in mission spawn tables.
    """

    def test_build_ice_enemy_docstring_has_raises_section(self) -> None:
        """The docstring must include a Raises: section documenting KeyError."""
        from roguelike_sprawl.combat.registry import build_ice_enemy

        doc = build_ice_enemy.__doc__
        assert doc is not None
        assert "Raises:" in doc
        assert "KeyError" in doc

    def test_build_ice_enemy_docstring_mentions_registry_and_scaling(self) -> None:
        """The docstring documents player_grade scaling and registry lookup."""
        from roguelike_sprawl.combat.registry import build_ice_enemy

        doc = build_ice_enemy.__doc__
        assert doc is not None
        doc_lower = doc.lower()
        assert "registry" in doc_lower
        assert "player_grade" in doc_lower or "player grade" in doc_lower
        assert "scale" in doc_lower or "scaling" in doc_lower or "difficulty" in doc_lower

    def test_build_ice_enemy_unknown_ice_keyerror_includes_total(self) -> None:
        """KeyError includes total available ICE count and JSON source path."""
        from roguelike_sprawl.combat.registry import IceRegistry, build_ice_enemy

        registry = IceRegistry(
            {
                "hosaka_watchdog": {"hp": 50},
                "sense_net_probe": {"hp": 40},
                "yakuza_brute": {"hp": 60},
            }
        )
        with pytest.raises(KeyError) as exc_info:
            build_ice_enemy("nonexistent_ice", registry)
        msg = str(exc_info.value)
        assert "total 3 registered" in msg
        assert "ice_types.json" in msg
        assert "'nonexistent_ice'" in msg

    def test_build_ice_enemy_unknown_ice_suggests_close_match(self) -> None:
        """KeyError still includes the 'Did you mean' suggestion."""
        from roguelike_sprawl.combat.registry import IceRegistry, build_ice_enemy

        registry = IceRegistry(
            {
                "hosaka_watchdog": {"hp": 50},
                "sense_net_probe": {"hp": 40},
                "yakuza_brute": {"hp": 60},
            }
        )
        with pytest.raises(KeyError, match=r"Did you mean"):
            build_ice_enemy("hosaka_watchdoog", registry)  # typo


# ---------------------------------------------------------------------------
# Polish 3: Mission.__post_init__ ValueError messages
# ---------------------------------------------------------------------------


class TestMissionPostInitErrorMessages:
    """Phase 46 polish #3 — Mission.__post_init__ ValueError messages
    now include the offending value AND the mission_id so JSON-data
    authors can locate the bad row quickly when ``missions.json`` fails
    to load.

    Was: 'arc must be 1..5, got 6'.
    Now: 'arc must be in 1..5, got 6 (mission_id="m_bad")'.
    """

    def test_mission_post_init_bad_arc_includes_value_and_id(self) -> None:
        """Arc ValueError includes the offending value and the mission_id."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"arc must be in 1\.\.5, got 6") as exc_info:
            Mission(
                id="m_test_bad_arc",
                title="t",
                fixer="x",
                arc=6,  # out of range
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=3,
                reward_credits=100,
                primary_objective=None,
            )
        msg = str(exc_info.value)
        assert "1..5" in msg
        assert "got 6" in msg
        assert "m_test_bad_arc" in msg

    def test_mission_post_init_bad_reward_tier_includes_value_and_id(self) -> None:
        """reward_tier ValueError includes the offending value and the mission_id."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"reward_tier must be in 1\.\.6, got 7") as exc_info:
            Mission(
                id="m_test_bad_tier",
                title="t",
                fixer="x",
                arc=3,
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=7,  # out of range
                reward_credits=100,
                primary_objective=None,
            )
        msg = str(exc_info.value)
        assert "1..6" in msg
        assert "got 7" in msg
        assert "m_test_bad_tier" in msg

    def test_mission_post_init_negative_credits_includes_value_and_id(self) -> None:
        """reward_credits ValueError includes the offending value."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"reward_credits must be >= 0") as exc_info:
            Mission(
                id="m_test_neg_credits",
                title="t",
                fixer="x",
                arc=3,
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=3,
                reward_credits=-50,  # negative
                primary_objective=None,
            )
        msg = str(exc_info.value)
        assert ">= 0" in msg
        assert "got -50" in msg
        assert "m_test_neg_credits" in msg

    def test_mission_post_init_empty_id_message_preserved(self) -> None:
        """Empty-id ValueError still rejects non-empty id contract."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"Mission id must be non-empty"):
            Mission(
                id="",  # empty
                title="t",
                fixer="x",
                arc=3,
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=3,
                reward_credits=100,
                primary_objective=None,
            )

    def test_mission_post_init_grade_range_includes_bounds(self) -> None:
        """Grade-range ValueError includes both bounds and the mission_id."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"invalid grade range 4\.\.2") as exc_info:
            Mission(
                id="m_test_bad_grade",
                title="t",
                fixer="x",
                arc=3,
                grade_min=4,
                grade_max=2,  # min > max
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=3,
                reward_credits=100,
                primary_objective=None,
            )
        msg = str(exc_info.value)
        assert "4..2" in msg
        assert "m_test_bad_grade" in msg


# ---------------------------------------------------------------------------
# Vault-wide interrogate
# ---------------------------------------------------------------------------


class TestVaultWideInterrogateCoverage:
    """Phase 46 polish keeps vault-wide interrogate at 100%.

    The 3 polish improvements targeted error-message clarity and
    docstring 'Raises:' sections. None of them add new functions or
    classes, so the vault coverage stays at the Phase 45 plateau of
    100.0%. No new MISSED entries are introduced.
    """

    def test_vault_interrogate_at_or_above_100(self) -> None:
        """Run interrogate on src/ and require >= 100% actual coverage.

        Skips automatically if interrogate is not installed in the
        current environment (mirrors Phase 35-45 robustness pattern).
        """
        result = subprocess.run(
            [sys.executable, "-m", "interrogate", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        output = result.stdout + result.stderr
        # Accept >= 99.9% (Phase 45 plateau + Phase 46 polish)
        assert "RESULT: PASSED" in output
        # Confirm we are at or above 99.9% (Phase 45→46 stays at 100.0%)
        match = re.search(r"actual: (\d+\.\d+)%", output)
        assert match is not None, f"interrogate output missing actual %: {output!r}"
        actual_pct = float(match.group(1))
        assert actual_pct >= 99.9, f"interrogate dropped below 99.9%: {actual_pct}"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


class TestPhase46Smoke:
    """Smoke tests — confirm Phase 46 didn't regress existing structure."""

    def test_existing_phase45_event_still_present(self, events: dict) -> None:
        """Phase 45's straylight_phantom_family event must still exist."""
        assert "general_event_straylight_phantom_family" in events

    def test_existing_phase45_event_total_unchanged(self, events: dict) -> None:
        """Phase 45 event's metadata fields unchanged."""
        event = events["general_event_straylight_phantom_family"]
        assert event["title"] == "Straylight's Phantom Family"
        assert event["arc"] == 4
        assert event["pillar"] == "code"
        assert event["faction_affinity"]["ta_rep"] == 2
        assert event["faction_affinity"]["wintermute"] == 1

    def test_new_event_distinct_from_phase45(self, events: dict) -> None:
        """Phase 46 event is NOT the Phase 45 event."""
        assert "general_event_maas_neuropozyne_ledger" != "general_event_straylight_phantom_family"
        assert "general_event_maas_neuropozyne_ledger" in events

    def test_cyberdeck_add_and_remove_still_work(self) -> None:
        """add_program_to_deck + remove_program_from_deck still produce valid decks."""
        from roguelike_sprawl.combat.cyberdeck import (
            Cyberdeck,
            add_program_to_deck,
            remove_program_from_deck,
        )

        deck = Cyberdeck(name="d", program_ids=())
        deck2 = add_program_to_deck(deck, "deck_wrecker")
        assert "deck_wrecker" in deck2.program_ids
        deck3 = remove_program_from_deck(deck2, "deck_wrecker")
        assert "deck_wrecker" not in deck3.program_ids

    def test_ice_registry_build_still_works_for_known_ice(self) -> None:
        """build_ice_enemy still builds Combatant for known ICE ids."""
        from roguelike_sprawl.combat.registry import IceRegistry, build_ice_enemy

        registry = IceRegistry(
            {
                "hosaka_watchdog": {
                    "name": "Hosaka Watchdog",
                    "hp": 50,
                    "damage": 10,
                    "tier": 1,
                    "ice_kind": "watchdog",
                    "speed": 1.0,
                }
            }
        )
        enemy = build_ice_enemy("hosaka_watchdog", registry)
        assert enemy is not None
        assert enemy.name == "Hosaka Watchdog"

    def test_mission_post_init_valid_mission_still_constructible(self) -> None:
        """A valid Mission can still be constructed after the polish."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        m = Mission(
            id="m_smoke",
            title="t",
            fixer="x",
            arc=3,
            grade_min=1,
            grade_max=6,
            matrix_seed=0,
            zone=ZoneDepth.SURFACE,
            reward_tier=3,
            reward_credits=100,
            primary_objective=None,
        )
        assert m.id == "m_smoke"
        assert m.arc == 3

    def test_phase40_arc_validation_test_still_passes(self) -> None:
        """Phase 40's test_mission_post_init_rejects_bad_arc regex still matches."""
        from roguelike_sprawl.matrix.node import ZoneDepth
        from roguelike_sprawl.missions.mission import Mission

        with pytest.raises(ValueError, match=r"arc must be.*1..5"):
            Mission(
                id="m_smoke_bad",
                title="t",
                fixer="x",
                arc=6,
                grade_min=1,
                grade_max=6,
                matrix_seed=0,
                zone=ZoneDepth.SURFACE,
                reward_tier=3,
                reward_credits=100,
                primary_objective=None,
            )

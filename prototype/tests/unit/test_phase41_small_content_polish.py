"""Tests for Phase 41 — Small content + polish.

Validates:
- The new general_event_deck_static event (Option A content addition).
  Gibson-flavored Count Zero / Neuromancer precursor "ghost in the
  deck" event for arc 1 (the matrix is full of echoes). The runner's
  cyberdeck catches a residual construct fragment — a phantom process
  riding home in the wetware. Purging the deck keeps the runner clean
  (no faction shift, slot penalty for 3 runs); keeping the static
  yields loa +1 (construct residue) but at the cost of future
  construct_whisper lock and a recurring identity marker.
- Docstring coverage on 3 modules:
    * combat/cyberdeck.py — Cyberdeck.__post_init__ (90% -> 100%)
    * combat/gibson_fluff.py — _m factory (90% -> 100%)
    * i18n/translator.py — Translator.__repr__ (90% -> 100%)
- Total events count increments from 43 to 44; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 99.1% to 99.2%+.
"""

from __future__ import annotations

import json
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
# Content: general_event_deck_static
# ---------------------------------------------------------------------------


class TestDeckStaticEvent:
    """Phase 41 content addition — Gibson-flavored ghost-in-the-deck event.

    Arc 1 early-encounter overlay. The matrix has ghosts — small
    fragments of older constructs that ride home in the wetware.
    The runner's deck starts cycling phantom commands. The choice is
    the standard "clean code path vs keep the scar" fork: purge the
    residual (no faction shift, slot penalty) or keep the static
    (loa +1 recurrence, construct_whisper_locked later).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_deck_static" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_deck_static"]
        assert event["event_id"] == "general_event_deck_static"
        assert event["title"] == "Ghost in the Deck"
        assert event["category"] == "general"
        # Arc 1 early-arc encounter — surface_grid, low tier
        assert event["arc"] == 1
        assert event["tier"] == 1
        assert event["pillar"] == "code"
        # Location should be a surface-tier grid
        assert "surface" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_1_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (purge vs keep the static)."""
        event = events["general_event_deck_static"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Purge path should mention deck purge / program slot penalty
        accept = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "purge" in accept or "slot" in accept or "clean" in accept
        # Keep path should mention loa or the residual
        refuse = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "loa" in refuse or "static" in refuse or "residual" in refuse

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — process echo, weight is never zero."""
        event = events["general_event_deck_static"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson deck-static signatures
        assert "console" in dialogue or "unscheduled" in dialogue or "residual" in dialogue
        # Gibson "weight is never zero" echo (Count Zero / Neuromancer)
        assert "weight" in dialogue or "matrix" in dialogue
        # Runner voice — "I didn't" / "that's not mine"
        assert "not mine" in dialogue or "self" in dialogue or "purge" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """loa +1 only — keeping the static is a loa (construct residue) choice.

        The purge path yields no faction shift (clean code path). The
        event's ``faction_affinity`` represents the *leaning* of the
        keep-static branch, which is the only branch with a faction
        cost/benefit.
        """
        event = events["general_event_deck_static"]
        assert event["faction_affinity"]["loa"] == 1
        # No other faction shifts
        assert len(event["faction_affinity"]) == 1

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare deck_static_branch."""
        event = events["general_event_deck_static"]
        assert event["consequence"] == "deck_static_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits (the static isn't worth money), 40 XP, static_fragment_charm."""
        event = events["general_event_deck_static"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 40
        assert event["reward"]["item"] == "static_fragment_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'paranoid' — the deck is doing something it shouldn't."""
        event = events["general_event_deck_static"]
        assert event["mood"] == "paranoid"

    def test_event_trigger_gates_arc1_low(self, events: dict) -> None:
        """Arc 1 early-arc gate (>= 10%) — overlay surface, not late-arc."""
        event = events["general_event_deck_static"]
        cond = event["trigger_condition"]
        assert "arc_1_progress >= 10" in cond
        assert "deck_static_seen" in cond


class TestEventCountIncrement:
    """Phase 41 metadata bumps: total_events 43 -> 44, phase 40 -> 41."""

    def test_total_events_at_least_44(self, events: dict) -> None:
        assert len(events) >= 44

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 44
        # Forward-compat allowlist (mirrors Phase 29/32..40 pattern)
        assert metadata["phase"] in ("41", "42", "43", "44")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 41 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: combat/cyberdeck.py docstring coverage
# ---------------------------------------------------------------------------


class TestCyberdeckDocstringCoverage:
    """Phase 41 polish — Cyberdeck.__post_init__ docstring (90% -> 100%)."""

    def test_cyberdeck_post_init_has_docstring(self) -> None:
        from roguelike_sprawl.combat.cyberdeck import Cyberdeck

        doc = Cyberdeck.__post_init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions validation
        assert "valid" in doc_lower or "invariant" in doc_lower
        # Mentions MAX_DECK_NAME_LENGTH
        assert "max_deck_name_length" in doc_lower or "32" in doc
        # Mentions program_ids / program validation deferred
        assert "program" in doc_lower or "slot" in doc_lower

    def test_interrogate_cyberdeck_at_100(self) -> None:
        """Verify interrogate reports combat/cyberdeck.py at 100% coverage (was 90%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/combat/cyberdeck.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 2: combat/gibson_fluff.py docstring coverage
# ---------------------------------------------------------------------------


class TestGibsonFluffDocstringCoverage:
    """Phase 41 polish — _m factory docstring (90% -> 100%)."""

    def test_m_factory_has_docstring(self) -> None:
        from roguelike_sprawl.combat.gibson_fluff import _m

        doc = _m.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions factory / shortcut
        assert "factory" in doc_lower or "shorthand" in doc_lower or "build" in doc_lower
        # Mentions FluffMessage
        assert "fluffmessage" in doc_lower

    def test_interrogate_gibson_fluff_at_100(self) -> None:
        """Verify interrogate reports combat/gibson_fluff.py at 100% (was 90%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/combat/gibson_fluff.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 3: i18n/translator.py docstring coverage
# ---------------------------------------------------------------------------


class TestTranslatorDocstringCoverage:
    """Phase 41 polish — Translator.__repr__ docstring (90% -> 100%)."""

    def test_repr_has_docstring(self) -> None:
        from roguelike_sprawl.i18n.translator import Translator

        doc = Translator.__repr__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions debug / repr
        assert "debug" in doc_lower or "repr" in doc_lower
        # Mentions key count
        assert "key" in doc_lower or "load" in doc_lower or "dictionary" in doc_lower

    def test_interrogate_translator_at_100(self) -> None:
        """Verify interrogate reports i18n/translator.py at 100% (was 90%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/i18n/translator.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Smoke tests — ensure polished code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase41Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_cyberdeck_post_init_validates_long_name(self) -> None:
        """Cyberdeck.__post_init__ rejects >32-char names (validation preserved)."""
        from roguelike_sprawl.combat.cyberdeck import MAX_DECK_NAME_LENGTH, Cyberdeck

        with pytest.raises(ValueError, match="Deck name too long"):
            Cyberdeck(name="X" * (MAX_DECK_NAME_LENGTH + 1))

    def test_cyberdeck_short_name_accepted(self) -> None:
        """Cyberdeck.__post_init__ accepts <=32-char names (validation preserved)."""
        from roguelike_sprawl.combat.cyberdeck import Cyberdeck

        deck = Cyberdeck(name="Cortex-7")
        assert deck.name == "Cortex-7"
        assert deck.program_ids == ()

    def test_m_factory_returns_fluff_message(self) -> None:
        """_m factory still produces a FluffMessage with given kwargs."""
        from roguelike_sprawl.combat.gibson_fluff import FluffMessage, _m

        msg = _m("combat_hit", "player_to_ice", "Test message", weight=2.0)
        assert isinstance(msg, FluffMessage)
        assert msg.category == "combat_hit"
        assert msg.context == "player_to_ice"
        assert msg.text == "Test message"
        assert msg.weight == 2.0

    def test_m_factory_default_weight(self) -> None:
        """_m factory defaults weight to 1.0."""
        from roguelike_sprawl.combat.gibson_fluff import FluffMessage, _m

        msg = _m("combat_hit", "player_to_ice", "Default weight")
        assert isinstance(msg, FluffMessage)
        assert msg.weight == 1.0

    def test_translator_repr_includes_lang_and_keys(self) -> None:
        """Translator.__repr__ returns lang + key count (validation preserved)."""
        from roguelike_sprawl.i18n.translator import Translator

        t = Translator(lang="en")
        rep = repr(t)
        assert "en" in rep
        assert "keys" in rep
        assert "0" in rep  # empty data dict => 0 keys

    def test_translator_repr_with_loaded_data(self) -> None:
        """Translator.__repr__ reflects loaded data size after _load()."""
        from roguelike_sprawl.i18n.translator import Translator

        t = Translator(lang="en")
        t._data = {"a": 1, "b": 2, "c": 3}  # simulate loaded state
        rep = repr(t)
        assert "en" in rep
        assert "3" in rep  # 3 keys

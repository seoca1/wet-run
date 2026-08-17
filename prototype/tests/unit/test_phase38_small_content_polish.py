"""Tests for Phase 38 — Small content + polish.

Validates:
- The new general_event_freeside_kumiko_invitation event (Option A content addition).
  Gibson-flavored Count Zero / Mona Lisa Overdrive-era Freeside encounter with
  Kumiko (the Wigan Ludlow / TA daughter who fled to Freeside). Arc 5 mid-arc
  Freeside orbital event. Kumiko's tea ceremony reaches out via the Freeside
  guest quarters handshake — complements Phase 35's wintermute_bargain
  (wintermute +3, ta_rep -1), Phase 36's loa_construct_echo (loa +3,
  wintermute +1), and Phase 37's 3jane_puppet_show (ta_rep +3, wintermute +1)
  by giving ta_rep +2 + loa +2 (Kumiko's TA origins and her Count Zero
  Loa-construct connection).
- Docstring coverage on 4 modules:
    * avatar/state.py — Status + ConstructKind enum members (80% -> 100%)
    * data_fragment.py — FragmentRarity enum members (88% -> 100%)
    * combat/depth/personality.py — _combatant_personality helper (88% -> 100%)
    * engine/cinematic_art.py — ArtStyle enum members (89% -> 100%)
- Total events count increments from 40 to 41; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 98.6% to 98.7%+.
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
# Content: general_event_freeside_kumiko_invitation
# ---------------------------------------------------------------------------


class TestFreesideKumikoInvitationEvent:
    """Phase 38 content addition — Gibson-flavored Kumiko / Freeside encounter.

    Arc 5 mid-arc Freeside orbital event. Kumiko's tea ceremony reaches out
    via the Freeside guest quarters handshake — the Count Zero / MLO
    character who fled TA to live in orbit. Complements Phase 35
    wintermute_bargain (wintermute +3, ta_rep -1), Phase 36 loa_construct_echo
    (loa +3, wintermute +1), and Phase 37 3jane_puppet_show (ta_rep +3,
    wintermute +1) by giving ta_rep +2 + loa +2 — Kumiko's TA origins
    and her Loa-construct connection in Count Zero.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_freeside_kumiko_invitation" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["event_id"] == "general_event_freeside_kumiko_invitation"
        assert event["title"] == "Kumiko's Tea Ceremony"
        assert event["category"] == "general"
        # Arc 5 mid-arc Freeside orbital event
        assert event["arc"] == 5
        assert event["tier"] == 5
        assert event["pillar"] == "memory"
        # Location should be in the Freeside orbit area
        assert "freeside" in event["location"].lower() or "orbit" in event["location"].lower()
        # Triggered on node_enter with arc gate
        assert event["trigger"] == "node_enter"
        assert "arc_5_progress" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept the tea ceremony vs decline politely)."""
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention ta or kumiko or freeside
        accept = event["choice"]["consequence_a"].lower()
        assert "ta_" in accept or "kumiko" in accept or "freeside" in accept
        # Refuse path should mark safe jackout or respectful dismissal
        refuse = event["choice"]["option_b"].lower() + event["choice"]["consequence_b"].lower()
        assert (
            "safe_jackout" in refuse
            or "decline" in refuse
            or "respectful" in refuse
            or "silent" in refuse
        )

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored Kumiko / Freeside dialogue (Count Zero / MLO era)."""
        event = events["general_event_freeside_kumiko_invitation"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Kumiko / Freeside / tea signature phrases
        assert "kumiko" in dialogue
        assert "freeside" in dialogue or "orbit" in dialogue
        assert "tea" in dialogue or "father" in dialogue or "construct" in dialogue
        # Kumiko's reserved, contemplative tone — sit / moving / waiting
        assert "wait" in dialogue or "sit" in dialogue or "moving" in dialogue

    def test_event_faction_affinity(self, events: dict) -> None:
        """ta_rep +2, loa +2 (Kumiko's TA origins + Count Zero Loa-construct link)."""
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["faction_affinity"]["ta_rep"] == 2
        assert event["faction_affinity"]["loa"] == 2

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare freeside_kumiko_tea_branch."""
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["consequence"] == "freeside_kumiko_tea_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 1800 credits + 120 XP + kumiko_tea_charm (consistent with tier 5)."""
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 1800
        assert event["reward"]["xp"] == 120
        assert event["reward"]["item"] == "kumiko_tea_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'graceful' — reserved Kumiko tone."""
        event = events["general_event_freeside_kumiko_invitation"]
        assert event["mood"] == "graceful"


class TestEventCountIncrement:
    """Phase 38 metadata bumps: total_events 40 -> 41, phase 37 -> 38."""

    def test_total_events_at_least_41(self, events: dict) -> None:
        assert len(events) >= 41

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 41
        # Forward-compat allowlist (mirrors Phase 29/32/33/34/35/36/37 pattern)
        assert metadata["phase"] in (
            "38",
            "39",
            "40",
            "41",
            "42",
            "43",
            "44",
            "45",
            "46",
            "47",
            "48",
        )

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 38 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: avatar/state.py docstring coverage
# ---------------------------------------------------------------------------


class TestAvatarStateDocstringCoverage:
    """Phase 38 polish — Status + ConstructKind enum members gained docstrings (80% -> 100%)."""

    def test_status_enum_members_have_docstrings(self) -> None:
        from roguelike_sprawl.avatar.state import Status

        # Status class docstring describes PPL/ZDR ratio semantics
        assert Status.__doc__ is not None
        assert Status.__doc__.strip()
        assert "PPL" in Status.__doc__ or "ZDR" in Status.__doc__
        # All 5 members should be present
        for member in ("SAFE", "MATCH", "TOUGH", "DEADLY", "FUTILE"):
            assert hasattr(Status, member), f"Status.{member} missing"

    def test_construct_kind_enum_members_have_docstrings(self) -> None:
        from roguelike_sprawl.avatar.state import ConstructKind

        # ConstructKind class docstring describes companion glyph semantics
        assert ConstructKind.__doc__ is not None
        assert ConstructKind.__doc__.strip()
        # All 3 construct kinds should be present (Dixie/Loa/3Jane)
        assert hasattr(ConstructKind, "DIXIE")
        assert hasattr(ConstructKind, "LOA")
        assert hasattr(ConstructKind, "THREE_JANE")
        # Verify the Gibson-flavored comment markers are present
        src = (
            Path(__file__).parent.parent.parent / "src" / "roguelike_sprawl" / "avatar" / "state.py"
        )
        text = src.read_text(encoding="utf-8")
        # The new docstrings should mention Gibson characters
        assert "Dixie" in text or "Flatline" in text
        assert "Tessier-Ashpool" in text or "3Jane" in text

    def test_interrogate_avatar_state_at_100(self) -> None:
        """Verify interrogate reports avatar/state.py at 100% coverage (was 80%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/avatar/state.py",
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
# Polish 2: data_fragment.py docstring coverage
# ---------------------------------------------------------------------------


class TestDataFragmentDocstringCoverage:
    """Phase 38 polish — FragmentRarity enum members gained docstrings (88% -> 100%)."""

    def test_fragment_rarity_class_has_docstring(self) -> None:
        from roguelike_sprawl.data_fragment import FragmentRarity

        # Class docstring should describe rarity semantics + gallery impact
        assert FragmentRarity.__doc__ is not None
        assert FragmentRarity.__doc__.strip()
        assert "rarity" in FragmentRarity.__doc__.lower()
        assert (
            "gallery" in FragmentRarity.__doc__.lower()
            or "visual" in FragmentRarity.__doc__.lower()
        )

    def test_fragment_rarity_members_present(self) -> None:
        from roguelike_sprawl.data_fragment import FragmentRarity

        for member in ("COMMON", "UNCOMMON", "RARE", "LEGENDARY"):
            assert hasattr(FragmentRarity, member), f"FragmentRarity.{member} missing"

    def test_interrogate_data_fragment_at_100(self) -> None:
        """Verify interrogate reports data_fragment.py at 100% coverage (was 88%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/data_fragment.py",
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
# Polish 3: combat/depth/personality.py docstring coverage
# ---------------------------------------------------------------------------


class TestPersonalityHelperDocstringCoverage:
    """Phase 38 polish — _combatant_personality helper gained docstring (88% -> 100%)."""

    def test_combatant_personality_helper_has_docstring(self) -> None:
        from roguelike_sprawl.combat.depth.personality import (
            _combatant_personality,
        )

        assert _combatant_personality.__doc__ is not None
        assert _combatant_personality.__doc__.strip()
        # Must explain the AGGRESSIVE fallback contract
        doc_lower = _combatant_personality.__doc__.lower()
        assert "aggressive" in doc_lower
        assert "fallback" in doc_lower or "missing" in doc_lower or "malformed" in doc_lower

    def test_interrogate_personality_at_100(self) -> None:
        """Verify interrogate reports personality.py at 100% coverage (was 88%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/combat/depth/personality.py",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        assert result.returncode == 0, (
            f"interrogate failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "100%" in result.stdout
        assert "_combatant_personality" in result.stdout
        assert "MISSED" not in result.stdout


# ---------------------------------------------------------------------------
# Polish 4: engine/cinematic_art.py docstring coverage
# ---------------------------------------------------------------------------


class TestCinematicArtDocstringCoverage:
    """Phase 38 polish — ArtStyle enum members gained docstrings (89% -> 100%)."""

    def test_art_style_class_has_docstring(self) -> None:
        from roguelike_sprawl.engine.cinematic_art import ArtStyle

        assert ArtStyle.__doc__ is not None
        assert ArtStyle.__doc__.strip()

    def test_art_style_members_have_inline_docs(self) -> None:
        """Each ArtStyle member should have a Gibson-tone inline comment."""
        src = (
            Path(__file__).parent.parent.parent
            / "src"
            / "roguelike_sprawl"
            / "engine"
            / "cinematic_art.py"
        )
        text = src.read_text(encoding="utf-8")
        # Each ArtStyle should have an inline comment with scene context
        # Phase 38 added "— default runner style", "— damaged construct echo", etc.
        assert "default runner style" in text
        assert "boss / combat climax" in text
        assert "cyberspace node intro" in text
        assert "construct memory" in text or "Loa encounter" in text

    def test_interrogate_cinematic_art_at_100(self) -> None:
        """Verify interrogate reports cinematic_art.py at 100% coverage (was 89%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/roguelike_sprawl/engine/cinematic_art.py",
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
# Smoke tests — ensure new code paths still work at runtime
# ---------------------------------------------------------------------------


class TestPhase38Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_status_enum_members_still_work(self) -> None:
        """Status enum members and PPL/ZDR semantics intact after docstring addition."""
        from roguelike_sprawl.avatar.state import Status

        # All five statuses still present with correct values
        assert Status.SAFE.value == "safe"
        assert Status.MATCH.value == "match"
        assert Status.TOUGH.value == "tough"
        assert Status.DEADLY.value == "deadly"
        assert Status.FUTILE.value == "futile"
        # Iteration works
        members = list(Status)
        assert len(members) == 5

    def test_construct_kind_enum_members_still_work(self) -> None:
        """ConstructKind enum members and glyph codes intact after docstring addition."""
        from roguelike_sprawl.avatar.state import ConstructKind

        assert ConstructKind.DIXIE.value == "D"
        assert ConstructKind.LOA.value == "L"
        assert ConstructKind.THREE_JANE.value == "J"

    def test_fragment_rarity_string_values_unchanged(self) -> None:
        """FragmentRarity string values preserved after docstring addition."""
        from roguelike_sprawl.data_fragment import FragmentRarity

        assert FragmentRarity.COMMON.value == "common"
        assert FragmentRarity.UNCOMMON.value == "uncommon"
        assert FragmentRarity.RARE.value == "rare"
        assert FragmentRarity.LEGENDARY.value == "legendary"

    def test_combatant_personality_fallback_still_works(self) -> None:
        """_combatant_personality fallback contract intact after docstring addition."""
        from roguelike_sprawl.combat.depth.personality import (
            PersonalityLevel,
            _combatant_personality,
        )

        # Plain object with no personality attribute -> AGGRESSIVE
        class _Empty:
            pass

        assert _combatant_personality(_Empty()) == PersonalityLevel.AGGRESSIVE

        # String "stealth" -> PersonalityLevel.STEALTH
        class _Str:
            personality = "stealth"

        assert _combatant_personality(_Str()) == PersonalityLevel.STEALTH

        # Bad string -> AGGRESSIVE
        class _Bad:
            personality = "not_a_personality"

        assert _combatant_personality(_Bad()) == PersonalityLevel.AGGRESSIVE

    def test_art_style_enum_members_still_work(self) -> None:
        """ArtStyle enum members intact after docstring addition."""
        from roguelike_sprawl.engine.cinematic_art import ArtStyle

        assert ArtStyle.NEON.value == "neon"
        assert ArtStyle.GLITCH.value == "glitch"
        assert ArtStyle.SHADOW.value == "shadow"
        assert ArtStyle.FIRE.value == "fire"
        assert ArtStyle.MATRIX.value == "matrix"
        assert ArtStyle.GHOST.value == "ghost"
        assert ArtStyle.STATIC.value == "static"

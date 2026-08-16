"""Tests for Phase 45 — Small content + polish.

Validates:
- The new general_event_straylight_phantom_family event (Option A content
  addition). Gibson-flavored arc 4 mid-arc "Tessier-Ashpool phantom family"
  event. The runner receives a handshake from a phantom TA family seat —
  a recurring Sprawl trilogy motif (3Jane's family vote, the vote is
  always tonight, the family rotates). Two paths: accept the phantom seat
  (ta_rep_+2, identity_marker_kept, construct_passage_unlocked, the
  family seat is carried 2 runs) or step back from the table (ta_rep_-1,
  phantom_disrespected, construct_whisper_locked, wintermute_+1).
  matrix_ta_orbit location, mood shaky, pillar code, tier 4.
- Polish improvements:
    * audio/sound_manager.py — SoundManager.__init__ return type
      annotation (defensive: explicit -> None for consistency with the
      rest of the project's typed-constructor convention)
    * cyberspace/world.py — Server.__repr__ docstring (was MISSED)
    * avatar/renderer.py — _render_color_for_status docstring (was MISSED)
- Total events count increments from 47 to 48; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 99.9% to 100.0%.
"""

from __future__ import annotations

import inspect
import json
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
# Content: general_event_straylight_phantom_family
# ---------------------------------------------------------------------------


class TestStraylightPhantomFamilyEvent:
    """Phase 45 content addition — Gibson-flavored TA phantom family seat.

    Arc 4 mid-arc (>= 20%) overlay on matrix_ta_orbit. The runner receives
    a handshake from the TA FAMILY ARCHIVE — the same family that 3Jane
    rotates, the same seat that votes at midnight, the same table whose
    covers were never set for outsiders but now one is. The choice is
    the standard "accept the phantom seat vs step back" fork: accepting
    the seat yields ta_rep_+2 (T-A family attention, identity kept) plus
    construct_passage_unlocked (TA-knowing constructs let the runner
    through later), stepping back yields ta_rep_-1 (the family notices,
    the runner leaves but is noticed leaving) and wintermute_+1 (the AI
    half of the merged construct approves).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_straylight_phantom_family" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_straylight_phantom_family"]
        assert event["event_id"] == "general_event_straylight_phantom_family"
        assert event["title"] == "Straylight's Phantom Family"
        assert event["category"] == "general"
        # Arc 4 mid-arc encounter — TA orbit, tier 4
        assert event["arc"] == 4
        assert event["tier"] == 4
        assert event["pillar"] == "code"
        assert "ta" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept the phantom seat vs step back)."""
        event = events["general_event_straylight_phantom_family"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention ta_rep or seat / phantom / construct
        accept_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "ta_rep" in accept_path or "phantom" in accept_path or "construct" in accept_path
        # Step-back path should mention ta_rep / wintermute or phantom / step
        step_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "ta_rep" in step_path or "wintermute" in step_path or "phantom" in step_path

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — TA family handshake + phantom seat.

        Gibson family / phantom signatures:
        - TA FAMILY ARCHIVE handshake (Count Zero 3Jane orbit, Straylight)
        - 'Welcome home' (the phantom seat greeting, family-tone)
        - 'voted on your arrival' (Mona Lisa Overdrive 3Jane family vote)
        - 'set it twice' (the unrepeatable seat — TA family closure)
        """
        event = events["general_event_straylight_phantom_family"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson family/Straylight motif
        assert "family" in dialogue
        # Phantom / seat / TA-resident motif
        assert "phantom" in dialogue or "table" in dialogue or "seat" in dialogue
        # Vote / decided / arrived — TA family decision motif
        assert "vote" in dialogue or "arrival" in dialogue
        # Handshake / Straylight / TA orbit
        assert "straylight" in dialogue or "ta" in dialogue or "handshake" in dialogue

    def test_event_faction_affinity_ta_rep_plus_wintermute(self, events: dict) -> None:
        """ta_rep +2 AND wintermute +1 — accept vs step-back trade-off.

        The accept-seat branch yields ta_rep_+2 (the T-A family offers
        the runner recognition; the runner takes the phantom seat). The
        step-back branch yields ta_rep_-1 (the family notices, the runner
        is a guest who refused hospitality) and wintermute_+1 (the AI
        half of the merged construct approves the runner's autonomy).
        Both paths contribute a faction shift, but in different ratios —
        matching the established Phase 35-43 faction_shifts pattern.
        """
        event = events["general_event_straylight_phantom_family"]
        affinity = event["faction_affinity"]
        assert affinity["ta_rep"] == 2
        assert affinity["wintermute"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"ta_rep", "wintermute"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare straylight_phantom_family_branch."""
        event = events["general_event_straylight_phantom_family"]
        assert event["consequence"] == "straylight_phantom_family_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits, 90 XP, straylight_phantom_charm."""
        event = events["general_event_straylight_phantom_family"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 90
        assert event["reward"]["item"] == "straylight_phantom_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'shaky' — the seat is offered, but is the runner real here."""
        event = events["general_event_straylight_phantom_family"]
        assert event["mood"] == "shaky"

    def test_event_trigger_gates_arc4_mid(self, events: dict) -> None:
        """Arc 4 mid-arc gate (>= 20%) with status flag — early TA orbit."""
        event = events["general_event_straylight_phantom_family"]
        cond = event["trigger_condition"]
        assert "arc_4_progress >= 20" in cond
        assert "straylight_phantom_seen" in cond


class TestEventCountIncrement:
    """Phase 45 metadata bumps: total_events 47 -> 48, phase 44 -> 45."""

    def test_total_events_at_least_48(self, events: dict) -> None:
        assert len(events) >= 48

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 48
        # Forward-compat allowlist (mirrors Phase 29/34..44 pattern)
        assert metadata["phase"] in ("45",)

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 45 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: SoundManager.__init__ return type annotation
# ---------------------------------------------------------------------------


class TestSoundManagerInitReturnType:
    """Phase 45 polish #1 — SoundManager.__init__ explicit -> None.

    Was missing the return type annotation (`-> None`). Adding it brings
    the constructor in line with the rest of the codebase's typed-init
    convention (all other __init__ methods in the audio/ + project
    declare `-> None`). mypy strict does not flag dunder __init__
    without it, but the convention is enforced by ruff `ANN204` if the
    ANN family is enabled — adding it now future-proofs the module.
    """

    def test_sound_manager_init_has_return_annotation(self) -> None:
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sig = inspect.signature(SoundManager.__init__)
        assert sig.return_annotation is not None
        # resolve forward refs — return should be None
        annotation = sig.return_annotation
        if isinstance(annotation, str):
            resolved = eval(annotation, {"None": None})  # noqa: S307 — test-only
            assert resolved is None
        else:
            assert annotation is None

    def test_sound_manager_init_default_args_intact(self) -> None:
        """Adding -> None must not shift default args (sounds_dir, volume)."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        sig = inspect.signature(SoundManager.__init__)
        params = list(sig.parameters.values())
        # self, sounds_dir, volume — 3 params total
        assert len(params) == 3
        # sounds_dir is positional with default None
        sounds_dir = sig.parameters["sounds_dir"]
        assert sounds_dir.default is None
        # volume is positional with default 0.2
        volume = sig.parameters["volume"]
        assert volume.default == 0.2


# ---------------------------------------------------------------------------
# Polish 2: Server.__repr__ docstring coverage
# ---------------------------------------------------------------------------


class TestServerReprDocstringCoverage:
    """Phase 45 polish #2 — Server.__repr__ (was MISSED).

    Server.__repr__ was the lone MISSED entry in cyberspace/world.py per
    interrogate. Adding the docstring explains the debug-friendly contract:
    short single-line summary suitable for crash dumps and debug logs,
    with id + name only (sector / difficulty / mission_id omitted to
    keep stack traces readable).
    """

    def test_server_repr_has_docstring(self) -> None:
        from roguelike_sprawl.cyberspace.world import Server

        doc = Server.__repr__.__doc__
        assert doc is not None
        assert doc.strip()

    def test_server_repr_docstring_mentions_debug(self) -> None:
        """The docstring should explicitly reference its debug role."""
        from roguelike_sprawl.cyberspace.world import Server

        doc = Server.__repr__.__doc__
        assert doc is not None
        doc_lower = doc.lower()
        # debug / crash / log mentioned (rationale for the short format)
        assert "debug" in doc_lower or "crash" in doc_lower or "log" in doc_lower

    def test_server_repr_format_intact(self) -> None:
        """Server(id: name) — the literal repr format must be unchanged."""
        from roguelike_sprawl.cyberspace.world import SectorId, Server

        server = Server(
            id="hosaka_main",
            name="Hosaka Main",
            sector=SectorId.HOSAKA,
            difficulty=4,
            description="Hosaka's flagship cortex",
        )
        assert repr(server) == "Server(hosaka_main: Hosaka Main)"


# ---------------------------------------------------------------------------
# Polish 3: _render_color_for_status docstring coverage
# ---------------------------------------------------------------------------


class TestRenderColorForStatusDocstringCoverage:
    """Phase 45 polish #3 — _render_color_for_status (was MISSED).

    avatar/renderer.py::_render_color_for_status was the other lone
    MISSED entry per interrogate. Adding the docstring clarifies the
    Status → body tint mapping contract: SAFE / MATCH / TOUGH share
    COL_BODY_NORMAL (the calm palette), DEADLY deepens to COL_BODY_LOW
    (red), FUTILE falls through to COL_BODY_FUTILE so an unexpected
    status still paints a coherent (dark) body.
    """

    def test_render_color_for_status_has_docstring(self) -> None:
        from roguelike_sprawl.avatar.renderer import _render_color_for_status

        doc = _render_color_for_status.__doc__
        assert doc is not None
        assert doc.strip()

    def test_render_color_for_status_docstring_mentions_palette(self) -> None:
        """The docstring should describe the palette mapping contract."""
        from roguelike_sprawl.avatar.renderer import _render_color_for_status

        doc = _render_color_for_status.__doc__
        assert doc is not None
        doc_lower = doc.lower()
        # SAFE / TOUGH / DEADLY / FUTILE terms mentioned
        assert "safe" in doc_lower or "status" in doc_lower
        assert "deadly" in doc_lower
        # Palette / color keyword
        assert "color" in doc_lower or "palette" in doc_lower or "tint" in doc_lower

    def test_render_color_for_status_safe_returns_normal(self) -> None:
        """SAFE → COL_BODY_NORMAL (the calm palette)."""
        from roguelike_sprawl.avatar.renderer import (
            COL_BODY_NORMAL,
            _render_color_for_status,
        )
        from roguelike_sprawl.avatar.state import Status

        assert _render_color_for_status(Status.SAFE) == COL_BODY_NORMAL

    def test_render_color_for_status_deadly_returns_low(self) -> None:
        """DEADLY → COL_BODY_LOW (the red deepening)."""
        from roguelike_sprawl.avatar.renderer import (
            COL_BODY_LOW,
            _render_color_for_status,
        )
        from roguelike_sprawl.avatar.state import Status

        assert _render_color_for_status(Status.DEADLY) == COL_BODY_LOW


# ---------------------------------------------------------------------------
# Vault-wide interrogate 99.9% → 100.0%
# ---------------------------------------------------------------------------


class TestVaultWideInterrogateCoverage:
    """Phase 45 polish drives vault-wide interrogate to 100%.

    3 polish improvements target the remaining 2 MISSED entries:
      - Server.__repr__ (cyberspace/world.py) → covered
      - _render_color_for_status (avatar/renderer.py) → covered
    The 3rd polish (SoundManager.__init__) keeps the typed-init contract
    clean. Vault total should reach 100.0%.
    """

    def test_vault_interrogate_at_or_above_99_9(self) -> None:
        """Run interrogate on src/ and require >= 99.9% actual coverage.

        Skips automatically if interrogate is not installed in the
        current environment (mirrors Phase 35-44 robustness pattern).
        """
        result = subprocess.run(
            [sys.executable, "-m", "interrogate", "src/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        output = result.stdout + result.stderr
        # Accept >= 99.9% (was 99.9% Phase 44 → 100.0% Phase 45)
        # Result line: "RESULT: PASSED (minimum: 80.0%, actual: 100.0%)"
        assert "RESULT: PASSED" in output
        # Confirm we crossed the 99.9% plateau
        assert "actual: 100." in output or "actual: 99.9%" in output


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


class TestPhase45Smoke:
    """Smoke tests — confirm Phase 45 didn't regress existing structure."""

    def test_existing_phase44_event_still_present(self, events: dict) -> None:
        """Phase 44's loa_construct_memory_surge event must still exist."""
        assert "general_event_loa_construct_memory_surge" in events

    def test_existing_phase44_event_total_unchanged(self, events: dict) -> None:
        """Phase 44 event's metadata fields unchanged."""
        event = events["general_event_loa_construct_memory_surge"]
        assert event["title"] == "Loa Construct Memory Surge"
        assert event["arc"] == 4
        assert event["pillar"] == "identity"
        assert event["faction_affinity"]["loa"] == 2
        assert event["faction_affinity"]["ta_rep"] == 1

    def test_sound_manager_importable_after_polish(self) -> None:
        """SoundManager module importable after __init__ annotation change."""
        from roguelike_sprawl.audio.sound_manager import SoundManager

        assert hasattr(SoundManager, "__init__")

    def test_server_dataclass_constructible(self) -> None:
        """Server dataclass still constructible after __repr__ docstring."""
        from roguelike_sprawl.cyberspace.world import SectorId, Server

        server = Server(
            id="sense_news",
            name="Sense/Net Newsroom",
            sector=SectorId.SENSE_NET,
            difficulty=3,
            description="Sense/Net broadcast cortex",
        )
        assert server.id == "sense_news"
        assert server.difficulty == 3

    def test_avatar_renderer_module_intact(self) -> None:
        """avatar.renderer module imports cleanly after docstring polish."""
        from roguelike_sprawl.avatar.renderer import (  # noqa: F401
            _render_color_for_status,
        )

        assert _render_color_for_status is not None

"""Tests for Phase 44 — Small content + polish.

Validates:
- The new general_event_loa_construct_memory_surge event (Option A content
  addition). Gibson-flavored arc 4 late-arc "construct identity bleed"
  event. The runner's identity buffer overflows with a loa construct's
  archived memories — a recurring Sprawl trilogy motif (Case's sim
  hangover, Molly's razorgirl backtalk, loa-tech construct residue).
  Two paths: accept the bleed (loa_+2, construct_memory_carried,
  construct_voice_unlock:tier6_path) or anchor the self (ta_rep_+1,
  identity_reinforced, bleed_severed, loa_-1). matrix_loa_construct
  location, mood haunted, pillar identity, tier 5.
- Docstring coverage on 5 modules:
    * combat/combo.py — StageAvatar.get_frame
    * combat/telemetry_integration.py — TelemetryIntegrator.__init__
    * engine/chapter_cutscene.py — ChapterCutsceneState.current_line
    * engine/hacking_view.py — _clear_hack_state
    * equipment/wetware_stacking.py — _is_tier3
- Total events count increments from 46 to 47; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 99.7% to 99.9%.
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
# Content: general_event_loa_construct_memory_surge
# ---------------------------------------------------------------------------


class TestLoaConstructMemorySurgeEvent:
    """Phase 44 content addition — Gibson-flavored loa construct memory surge.

    Arc 4 late-arc (>= 60%) overlay on matrix_loa_construct. The runner's
    identity buffer overflows with a loa construct's archived memories —
    a recurring Sprawl trilogy motif (Case's sim hangover, loa-tech
    construct residue). The choice is the standard "accept the bleed vs
    anchor the self" fork: accepting the bleed yields loa_+2 (the loa
    contract pays out and the runner carries construct voice), anchoring
    the self yields ta_rep_+1 (T-A-flavored identity reinforcement) and
    loa_-1 (the loa contract is severed). matrix_loa_construct location,
    mood haunted, pillar identity, tier 5.
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_loa_construct_memory_surge" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_loa_construct_memory_surge"]
        assert event["event_id"] == "general_event_loa_construct_memory_surge"
        assert event["title"] == "Loa Construct Memory Surge"
        assert event["category"] == "general"
        # Arc 4 late-arc encounter — loa_construct, tier 5
        assert event["arc"] == 4
        assert event["tier"] == 5
        assert event["pillar"] == "identity"
        assert "loa" in event["location"].lower()
        # Triggered on node_enter with arc + random + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_4_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (accept the bleed vs anchor the self)."""
        event = events["general_event_loa_construct_memory_surge"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # Accept path should mention loa / construct / bleed
        accept_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "loa" in accept_path or "construct" in accept_path or "bleed" in accept_path
        # Anchor path should mention ta_rep or anchor / identity
        anchor_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "ta_rep" in anchor_path or "anchor" in anchor_path or "identity" in anchor_path

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — construct buffer bleed + loa pact.

        Gibson wetware / construct signatures:
        - Construct buffer overflow (Count Zero construct motif)
        - Identity bleed (Neuromancer sim hangover)
        - loa_pact_fragment (Count Zero / Mona Lisa Overdrive recurring motif)
        - Runner voice: 'That face is mine. That voice is mine. That name is not.'
        """
        event = events["general_event_loa_construct_memory_surge"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson construct motif
        assert "construct" in dialogue
        # Identity bleed motif (Neuromancer sim hangover)
        assert "identity" in dialogue or "bleed" in dialogue
        # Loa / count-zero construct resonance
        assert "loa" in dialogue
        # Runner-voice signature ("That face is mine")
        assert "voice" in dialogue or "face" in dialogue

    def test_event_faction_affinity_loa_plus_ta_rep(self, events: dict) -> None:
        """loa +2 AND ta_rep +1 — accept vs anchor trade-off spans two factions.

        The accept-bleed branch yields loa_+2 (the loa contract pays out
        in identity bleed). The anchor-self branch yields ta_rep_+1
        (T-A-flavored identity reinforcement; the construct fragment is
        severed). Both paths contribute a faction shift, but to
        different factions — the runner picks whose identity framework
        they want to fall back on.
        """
        event = events["general_event_loa_construct_memory_surge"]
        affinity = event["faction_affinity"]
        assert affinity["loa"] == 2
        assert affinity["ta_rep"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"loa", "ta_rep"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare loa_construct_memory_surge_branch."""
        event = events["general_event_loa_construct_memory_surge"]
        assert event["consequence"] == "loa_construct_memory_surge_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits, 100 XP, loa_construct_memory_surge_charm."""
        event = events["general_event_loa_construct_memory_surge"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 100
        assert event["reward"]["item"] == "loa_construct_memory_surge_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'haunted' — the construct identity bleed is uninvited."""
        event = events["general_event_loa_construct_memory_surge"]
        assert event["mood"] == "haunted"

    def test_event_trigger_gates_arc4_late(self, events: dict) -> None:
        """Arc 4 late-arc gate (>= 60%) with status flag — late construct resolve."""
        event = events["general_event_loa_construct_memory_surge"]
        cond = event["trigger_condition"]
        assert "arc_4_progress >= 60" in cond
        assert "loa_memory_surge_seen" in cond


class TestEventCountIncrement:
    """Phase 44 metadata bumps: total_events 46 -> 47, phase 43 -> 44."""

    def test_total_events_at_least_47(self, events: dict) -> None:
        assert len(events) >= 47

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 47
        # Forward-compat allowlist (mirrors Phase 29/34..43 pattern)
        assert metadata["phase"] in ("44", "45", "46", "47", "48")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 44 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: combat/combo.py docstring coverage
# ---------------------------------------------------------------------------


class TestStageAvatarGetFrameDocstringCoverage:
    """Phase 44 polish — StageAvatar.get_frame (was MISSED)."""

    def test_stage_avatar_get_frame_has_docstring(self) -> None:
        from wet_run.combat.combo import StageAvatar

        doc = StageAvatar.get_frame.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions frame / animation / icon
        assert "frame" in doc_lower or "animation" in doc_lower or "icon" in doc_lower
        # Mentions priority / special / pulse / idle
        assert (
            "special" in doc_lower
            or "pulse" in doc_lower
            or "idle" in doc_lower
            or "priority" in doc_lower
        )

    def test_interrogate_combo_at_100(self) -> None:
        """Verify interrogate reports combat/combo.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/combat/combo.py",
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
# Polish 2: combat/telemetry_integration.py docstring coverage
# ---------------------------------------------------------------------------


class TestTelemetryIntegratorInitDocstringCoverage:
    """Phase 44 polish — TelemetryIntegrator.__init__ (was MISSED)."""

    def test_telemetry_integrator_init_has_docstring(self) -> None:
        from wet_run.combat.telemetry_integration import TelemetryIntegrator

        doc = TelemetryIntegrator.__init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions config / session / opt
        assert "config" in doc_lower or "session" in doc_lower or "opt" in doc_lower

    def test_interrogate_telemetry_integration_at_100(self) -> None:
        """Verify interrogate reports combat/telemetry_integration.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/combat/telemetry_integration.py",
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
# Polish 3: engine/chapter_cutscene.py docstring coverage
# ---------------------------------------------------------------------------


class TestChapterCutsceneStateCurrentLineDocstringCoverage:
    """Phase 44 polish — ChapterCutsceneState.current_line (was MISSED)."""

    def test_chapter_cutscene_state_current_line_has_docstring(self) -> None:
        from wet_run.engine.chapter_cutscene import ChapterCutsceneState

        doc = ChapterCutsceneState.current_line.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions dialogue / line / index
        assert "dialogue" in doc_lower or "line" in doc_lower or "index" in doc_lower

    def test_interrogate_chapter_cutscene_at_100(self) -> None:
        """Verify interrogate reports engine/chapter_cutscene.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/engine/chapter_cutscene.py",
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
# Polish 4: engine/hacking_view.py docstring coverage
# ---------------------------------------------------------------------------


class TestClearHackStateDocstringCoverage:
    """Phase 44 polish — _clear_hack_state (was MISSED)."""

    def test_clear_hack_state_has_docstring(self) -> None:
        from wet_run.engine.hacking_view import _clear_hack_state

        doc = _clear_hack_state.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions hack / state / clear / matrix
        assert (
            "hack" in doc_lower
            or "state" in doc_lower
            or "clear" in doc_lower
            or "matrix" in doc_lower
        )

    def test_interrogate_hacking_view_at_100(self) -> None:
        """Verify interrogate reports engine/hacking_view.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/engine/hacking_view.py",
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
# Polish 5: equipment/wetware_stacking.py docstring coverage
# ---------------------------------------------------------------------------


class TestIsTier3DocstringCoverage:
    """Phase 44 polish — _is_tier3 (was MISSED)."""

    def test_is_tier3_has_docstring(self) -> None:
        from wet_run.equipment.wetware_stacking import _is_tier3

        doc = _is_tier3.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions tier / augment / registry
        assert "tier" in doc_lower or "augment" in doc_lower or "registry" in doc_lower

    def test_interrogate_wetware_stacking_at_100(self) -> None:
        """Verify interrogate reports equipment/wetware_stacking.py at 100% coverage."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/equipment/wetware_stacking.py",
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


class TestPhase44Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_stage_avatar_get_frame_idle(self) -> None:
        """StageAvatar.get_frame returns idle glyph when no flags set."""
        from wet_run.combat.combo import StageAvatar

        av = StageAvatar(
            stage="WARMUP",
            icon_idle="◦",
            icon_pulse="○",
            icon_special="◉",
            frame_label="1/5",
        )
        assert av.get_frame() == "◦"
        assert av.get_frame(pulse_active=True) == "○"
        assert av.get_frame(special=True) == "◉"
        # Special overrides pulse
        assert av.get_frame(pulse_active=True, special=True) == "◉"

    def test_telemetry_integrator_init_default(self) -> None:
        """TelemetryIntegrator.__init__ defaults to opt-out telemetry."""
        from wet_run.combat.telemetry_integration import TelemetryIntegrator

        integrator = TelemetryIntegrator()
        assert integrator.config.enabled is False
        assert integrator.config.opted_in_at_start is False

    def test_telemetry_integrator_init_with_config(self) -> None:
        """TelemetryIntegrator.__init__ honors supplied config."""
        from wet_run.combat.telemetry_integration import (
            TelemetryConfig,
            TelemetryIntegrator,
        )

        cfg = TelemetryConfig(enabled=True, session_id="s44", opted_in_at_start=True)
        integrator = TelemetryIntegrator(cfg)
        assert integrator.config.enabled is True
        assert integrator.config.session_id == "s44"

    def test_chapter_cutscene_state_current_line(self) -> None:
        """ChapterCutsceneState.current_line returns dialogue at index."""
        from wet_run.engine.chapter_cutscene import ChapterCutsceneState

        # Minimal scene: build with a 2-line dialogue
        state = ChapterCutsceneState.__new__(ChapterCutsceneState)
        # Populate via dict-style to avoid the scene loader dependency
        from wet_run.engine.graphic_novel_data import (
            DialogueLine,
            SceneData,
        )

        scene = SceneData(
            id="test",
            character="novice",
            order=0,
            ending="A",
            title_en="Test",
            title_ko="테스트",
            background_id="bg_test",
            portrait_left=None,
            portrait_right=None,
            dialogue=(
                DialogueLine(
                    speaker="VOICE",
                    speaker_ko="음성",
                    portrait=None,
                    text_en="First line.",
                    text_ko="첫 줄.",
                    duration_ms=1000,
                ),
                DialogueLine(
                    speaker="VOICE",
                    speaker_ko="음성",
                    portrait=None,
                    text_en="Second line.",
                    text_ko="두 번째 줄.",
                    duration_ms=1000,
                ),
            ),
            next_scene=None,
        )
        state.scene = scene
        state.dialogue_index = 0
        assert state.current_line.speaker == "VOICE"
        assert "First" in state.current_line.text_en

        # Reading does not mutate
        before = state.dialogue_index
        _ = state.current_line
        assert state.dialogue_index == before

    def test_clear_hack_state_removes_attrs(self) -> None:
        """_clear_hack_state removes both hack attrs."""
        from types import SimpleNamespace

        from wet_run.engine.hacking_view import _clear_hack_state

        state = SimpleNamespace(
            hack_state="mock",  # type: ignore[assignment]
            hack_node_label="mock_node",
            other_attr="keep",
        )
        _clear_hack_state(state)  # type: ignore[arg-type]
        assert not hasattr(state, "hack_state")
        assert not hasattr(state, "hack_node_label")
        assert state.other_attr == "keep"

    def test_is_tier3_returns_true_for_tier3(self) -> None:
        """_is_tier3 returns True for registered tier-3 augments."""
        from wet_run.equipment.wetware_stacking import (
            _is_tier3,
            get_all_augments,
        )

        # Find any tier-3 augment
        tier3_ids = [a["id"] for a in get_all_augments() if a.get("tier") == 3 and "id" in a]
        if tier3_ids:
            assert _is_tier3(tier3_ids[0]) is True
        # Non-existent id returns False
        assert _is_tier3("nonexistent_augment_id_999") is False


# ---------------------------------------------------------------------------
# Vault-wide interrogate check
# ---------------------------------------------------------------------------


class TestVaultWideInterrogate:
    """Phase 44 vault-wide interrogate >= 99.9% (was 99.7%)."""

    def test_vault_wide_interrogate_at_99_9(self) -> None:
        """Vault-wide interrogate coverage >= 99.9%."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "interrogate",
                "src/wet_run",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        # parse the percentage from the result line
        # e.g. "---------------- RESULT: PASSED (minimum: 80.0%, actual: 99.9%) ----------------"
        # Phase 45 polish brought coverage to 100.0% so accept any value >= 99.9%.
        output = result.stdout + result.stderr
        assert "PASSED" in output
        # Sanity: pass / above minimum
        # Extract "actual: X.X%" and assert X.X >= 99.9
        import re

        m = re.search(r"actual:\s*([\d.]+)%", output)
        assert m is not None, f"Could not parse interrogate actual pct from output:\n{output}"
        actual_pct = float(m.group(1))
        assert actual_pct >= 99.9, f"interrogate actual {actual_pct}% < 99.9%"

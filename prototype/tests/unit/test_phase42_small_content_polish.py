"""Tests for Phase 42 — Small content + polish.

Validates:
- The new general_event_wetware_echo event (Option A content addition).
  Gibson-flavored arc 3 mid-arc "wetware echo" event. The runner's
  wetware starts replaying archived input sequences — a recurring
  Sprawl trilogy motif (Molly's razorgirl backtalk, Case's
  simulation hangover, the loa-tech construct residue). Two paths:
  file the echo (ta_rep_+1, archived for recall) or burn it out
  (loa_+1, construct_residual_carried). mid_grid location, mood
  paranoid, pillar memory, tier 3.
- Docstring coverage on 3 modules:
    * equipment/equipment.py — Equipment.__repr__ + EquipmentRegistry.__init__
      (93% -> 100%)
    * combat/effects_data.py — ScreenShake.step + FloatingNumber.text +
      FloatingNumber.alpha + HitFlash.alpha (92% -> 100%)
    * engine/main_loop.py — _tick_logic nested function (90% -> 100%)
- Total events count increments from 44 to 45; total_chains stays at 6.
- Vault-wide interrogate coverage improves from 99.2% to 99.5%+.
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
# Content: general_event_wetware_echo
# ---------------------------------------------------------------------------


class TestWetwareEchoEvent:
    """Phase 42 content addition — Gibson-flavored wetware-echo event.

    Arc 3 mid-arc (>= 30%) overlay on mid_grid. The runner's wetware
    stack replays an archived input sequence — a recurring Sprawl
    trilogy motif (Molly's backtalk, Case's sim hangover, loa-tech
    construct residue). The choice is the standard "archive the
    echo vs burn it" fork: filing the echo yields ta_rep_+1 (T-A's
    biometric wetware is the source), burning it out yields loa_+1
    (loa recognizes the echo as construct resonance).
    """

    def test_event_present(self, events: dict) -> None:
        assert "general_event_wetware_echo" in events

    def test_event_metadata(self, events: dict) -> None:
        event = events["general_event_wetware_echo"]
        assert event["event_id"] == "general_event_wetware_echo"
        assert event["title"] == "Wetware Echo"
        assert event["category"] == "general"
        # Arc 3 mid-arc encounter — mid_grid, tier 3
        assert event["arc"] == 3
        assert event["tier"] == 3
        assert event["pillar"] == "memory"
        assert "mid" in event["location"].lower()
        # Triggered on node_enter with arc + hp + status gates
        assert event["trigger"] == "node_enter"
        assert "arc_3_progress" in event["trigger_condition"]
        assert "random <" in event["trigger_condition"]
        assert "NOT has_status" in event["trigger_condition"]
        assert "hp_pct" in event["trigger_condition"]

    def test_event_has_choice(self, events: dict) -> None:
        """Two-option choice (file vs burn the echo)."""
        event = events["general_event_wetware_echo"]
        assert event["choice"] is not None
        assert "option_a" in event["choice"]
        assert "option_b" in event["choice"]
        assert "consequence_a" in event["choice"]
        assert "consequence_b" in event["choice"]
        # File path should mention ta_rep / archive
        file_path = (event["choice"]["option_a"] + event["choice"]["consequence_a"]).lower()
        assert "ta_rep" in file_path or "archive" in file_path or "file" in file_path
        # Burn path should mention loa or residual
        burn_path = (event["choice"]["option_b"] + event["choice"]["consequence_b"]).lower()
        assert "loa" in burn_path or "burn" in burn_path or "residual" in burn_path

    def test_event_dialogue_uses_gibson_tone(self, events: dict) -> None:
        """Gibson-flavored reveal — replay detected, the matrix is full of 0.91."""
        event = events["general_event_wetware_echo"]
        dialogue = " ".join(event["dialogue"]).lower()
        # Gibson wetware signatures
        assert "wetware" in dialogue or "replay" in dialogue or "archive" in dialogue
        # Gibson "the matrix is full of 0.91" echo (Count Zero / Neuromancer)
        assert "0.91" in dialogue or "matrix" in dialogue
        # Runner voice — "that's not my hand" / "0.91 is not 1.0"
        assert "not my" in dialogue or "confidence" in dialogue or "burn" in dialogue

    def test_event_faction_affinity_ta_rep_plus_loa(self, events: dict) -> None:
        """ta_rep +1 AND loa +1 — file vs burn trade-off spans two factions.

        The file-echo branch yields ta_rep (T-A biometric wetware
        technology is the source of the echo). The burn-echo branch
        yields loa (loa recognizes the echo as construct residue).
        Both paths contribute a faction shift, but to different
        factions — the runner picks which archive they want.
        """
        event = events["general_event_wetware_echo"]
        affinity = event["faction_affinity"]
        assert affinity["ta_rep"] == 1
        assert affinity["loa"] == 1
        # No other faction shifts
        assert set(affinity.keys()) == {"ta_rep", "loa"}

    def test_event_consequence_sets_branch(self, events: dict) -> None:
        """consequence must declare wetware_echo_branch."""
        event = events["general_event_wetware_echo"]
        assert event["consequence"] == "wetware_echo_branch"

    def test_event_has_reward(self, events: dict) -> None:
        """Event pays 0 credits (the echo isn't worth money), 80 XP, wetware_echo_charm."""
        event = events["general_event_wetware_echo"]
        assert event["reward"] is not None
        assert event["reward"]["credits"] == 0
        assert event["reward"]["xp"] == 80
        assert event["reward"]["item"] == "wetware_echo_charm"

    def test_event_mood(self, events: dict) -> None:
        """Mood should be 'paranoid' — the wetware is doing something it shouldn't."""
        event = events["general_event_wetware_echo"]
        assert event["mood"] == "paranoid"

    def test_event_trigger_gates_arc3_mid(self, events: dict) -> None:
        """Arc 3 mid-arc gate (>= 30%) with hp gate — not surface, not late-arc."""
        event = events["general_event_wetware_echo"]
        cond = event["trigger_condition"]
        assert "arc_3_progress >= 30" in cond
        assert "wetware_echo_seen" in cond
        # HP gate ensures the runner is wounded enough to feel the echo
        assert "hp_pct" in cond


class TestEventCountIncrement:
    """Phase 42 metadata bumps: total_events 44 -> 45, phase 41 -> 42."""

    def test_total_events_at_least_45(self, events: dict) -> None:
        assert len(events) >= 45

    def test_metadata_total_events_updated(self, metadata: dict) -> None:
        assert metadata["total_events"] >= 45
        # Forward-compat allowlist (mirrors Phase 29/34..41 pattern)
        assert metadata["phase"] in ("42", "43", "44", "45", "46", "47", "48", "49", "50")

    def test_total_chains_unchanged(self, metadata: dict) -> None:
        """Phase 42 does not add new chains — only events."""
        assert metadata["total_chains"] == 6


# ---------------------------------------------------------------------------
# Polish 1: equipment/equipment.py docstring coverage
# ---------------------------------------------------------------------------


class TestEquipmentDocstringCoverage:
    """Phase 42 polish — Equipment.__repr__ + EquipmentRegistry.__init__ (93% -> 100%)."""

    def test_equipment_repr_has_docstring(self) -> None:
        from wet_run.equipment.equipment import Equipment

        doc = Equipment.__repr__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions debug / repr summary
        assert "debug" in doc_lower or "repr" in doc_lower or "summary" in doc_lower
        # Mentions name/tier/category
        assert "name" in doc_lower or "tier" in doc_lower or "category" in doc_lower

    def test_equipment_registry_init_has_docstring(self) -> None:
        from wet_run.equipment.equipment import EquipmentRegistry

        doc = EquipmentRegistry.__init__.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions mapping / dict
        assert "mapping" in doc_lower or "dict" in doc_lower or "registry" in doc_lower
        # Mentions defensive copy / isolation
        assert "copy" in doc_lower or "mutate" in doc_lower or "defensive" in doc_lower

    def test_interrogate_equipment_at_100(self) -> None:
        """Verify interrogate reports equipment/equipment.py at 100% coverage (was 93%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/equipment/equipment.py",
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
# Polish 2: combat/effects_data.py docstring coverage
# ---------------------------------------------------------------------------


class TestEffectsDataDocstringCoverage:
    """Phase 42 polish — 4 docstrings (92% -> 100%)."""

    def test_screen_shake_step_has_docstring(self) -> None:
        from wet_run.combat.effects_data import ScreenShake

        doc = ScreenShake.step.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions timeline / advance / shake
        assert "timeline" in doc_lower or "advance" in doc_lower or "shake" in doc_lower
        # Mentions no-op / inactive
        assert "no-op" in doc_lower or "inactive" in doc_lower or "zero" in doc_lower

    def test_floating_number_text_has_docstring(self) -> None:
        from wet_run.combat.effects_data import FloatingNumber

        doc = FloatingNumber.text.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions crit / bracket
        assert "crit" in doc_lower or "bracket" in doc_lower or "!" in doc

    def test_floating_number_alpha_has_docstring(self) -> None:
        from wet_run.combat.effects_data import FloatingNumber

        doc = FloatingNumber.alpha.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions fade / alpha / opacity
        assert "fade" in doc_lower or "alpha" in doc_lower or "opacity" in doc_lower

    def test_hit_flash_alpha_has_docstring(self) -> None:
        from wet_run.combat.effects_data import HitFlash

        doc = HitFlash.alpha.__doc__
        assert doc is not None
        assert doc.strip()
        doc_lower = doc.lower()
        # Mentions fade / decay
        assert "fade" in doc_lower or "decay" in doc_lower or "alpha" in doc_lower

    def test_interrogate_effects_data_at_100(self) -> None:
        """Verify interrogate reports combat/effects_data.py at 100% coverage (was 92%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/combat/effects_data.py",
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
# Polish 3: engine/main_loop.py docstring coverage
# ---------------------------------------------------------------------------


class TestMainLoopDocstringCoverage:
    """Phase 42 polish — _tick_logic nested closure (90% -> 100%)."""

    def test_interrogate_main_loop_at_100(self) -> None:
        """Verify interrogate reports engine/main_loop.py at 100% coverage (was 90%)."""
        import subprocess

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "interrogate",
                "-vv",
                "src/wet_run/engine/main_loop.py",
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


class TestPhase42Smoke:
    """Smoke tests for the polished code paths — runtime safety."""

    def test_equipment_repr_format_preserved(self) -> None:
        """Equipment.__repr__ still returns 'name (tier category)'."""
        from wet_run.equipment.equipment import (
            STARTER_DECK,
            EquipCategory,
            EquipTier,
        )

        rep = repr(STARTER_DECK)
        assert STARTER_DECK.name in rep
        assert STARTER_DECK.tier.value in rep
        assert STARTER_DECK.category.value in rep
        # Verify shape: name (TIER CATEGORY)
        assert rep == (
            f"{STARTER_DECK.name} ({STARTER_DECK.tier.value} {STARTER_DECK.category.value})"
        )
        # Type safety: tier is T0_BASELINE, category is HARDWARE for STARTER_DECK
        assert STARTER_DECK.tier == EquipTier.T0_BASELINE
        assert STARTER_DECK.category == EquipCategory.HARDWARE

    def test_equipment_registry_init_empty(self) -> None:
        """EquipmentRegistry.__init__() with no arg yields empty registry."""
        from wet_run.equipment.equipment import EquipmentRegistry

        reg = EquipmentRegistry()
        assert reg.all() == []
        assert reg._equipment == {}

    def test_equipment_registry_init_with_dict(self) -> None:
        """EquipmentRegistry.__init__(dict) copies input (defensive isolation)."""
        from wet_run.equipment.equipment import (
            STARTER_DECK,
            EquipmentRegistry,
        )

        source = {"deck_basic": STARTER_DECK}
        reg = EquipmentRegistry(source)
        assert len(reg.all()) == 1
        assert reg.get("deck_basic") is STARTER_DECK
        # Mutate source — registry should not see it
        source["rogue_key"] = STARTER_DECK  # type: ignore[assignment]
        assert "rogue_key" not in reg._equipment

    def test_screen_shake_step_zero_intensity_noop(self) -> None:
        """ScreenShake.step() with intensity=0 is a no-op (preserves invariants)."""
        from wet_run.combat.effects_data import ScreenShake

        shake = ScreenShake()
        # Default state: intensity=0, duration_ms=0, elapsed_ms=0
        shake.step(100)
        assert shake.intensity == 0.0
        assert shake.duration_ms == 0
        assert shake.elapsed_ms == 0

    def test_screen_shake_step_advances_and_resets(self) -> None:
        """ScreenShake.step() advances elapsed_ms and resets on expiry."""
        from wet_run.combat.effects_data import ScreenShake

        shake = ScreenShake()
        shake.trigger(intensity=5.0, duration_ms=100)
        assert shake.intensity == 5.0
        assert shake.duration_ms == 100
        shake.step(50)
        assert shake.elapsed_ms == 50
        # Step past the duration to trigger reset
        shake.step(60)
        assert shake.intensity == 0.0
        assert shake.duration_ms == 0
        assert shake.elapsed_ms == 0

    def test_floating_number_text_normal(self) -> None:
        """FloatingNumber.text renders as bare value for non-crits."""
        from wet_run.combat.effects_data import DAMAGE_COLOR, FloatingNumber

        num = FloatingNumber(
            value=42, is_crit=False, x=0, y=0, max_life_ms=1000, color=DAMAGE_COLOR
        )
        assert num.text == "42"

    def test_floating_number_text_crit(self) -> None:
        """FloatingNumber.text renders bracketed for crits (!42!)."""
        from wet_run.combat.effects_data import DAMAGE_COLOR, FloatingNumber

        num = FloatingNumber(value=42, is_crit=True, x=0, y=0, max_life_ms=1000, color=DAMAGE_COLOR)
        assert num.text == "!42!"

    def test_floating_number_alpha_at_spawn(self) -> None:
        """FloatingNumber.alpha is 1.0 at spawn (life_ms=0)."""
        from wet_run.combat.effects_data import DAMAGE_COLOR, FloatingNumber

        num = FloatingNumber(value=10, x=0, y=0, max_life_ms=1000, color=DAMAGE_COLOR)
        assert num.alpha == 1.0

    def test_floating_number_alpha_at_expiry(self) -> None:
        """FloatingNumber.alpha is 0.0 at expiry (life_ms=max_life_ms)."""
        from wet_run.combat.effects_data import DAMAGE_COLOR, FloatingNumber

        num = FloatingNumber(value=10, x=0, y=0, max_life_ms=1000, color=DAMAGE_COLOR)
        num.life_ms = 1000  # simulate expiry
        assert num.alpha == 0.0

    def test_floating_number_alpha_zero_max_life(self) -> None:
        """FloatingNumber.alpha is 0.0 when max_life_ms=0 (degenerate)."""
        from wet_run.combat.effects_data import DAMAGE_COLOR, FloatingNumber

        num = FloatingNumber(value=10, x=0, y=0, max_life_ms=0, color=DAMAGE_COLOR)
        assert num.alpha == 0.0

    def test_hit_flash_alpha_at_spawn(self) -> None:
        """HitFlash.alpha is 1.0 at spawn (elapsed_ms=0)."""
        from wet_run.combat.effects_data import HitFlash

        flash = HitFlash()
        flash.trigger(duration_ms=120)
        assert flash.alpha == 1.0

    def test_hit_flash_alpha_at_expiry(self) -> None:
        """HitFlash.alpha is 0.0 at expiry (elapsed_ms=duration_ms)."""
        from wet_run.combat.effects_data import HitFlash

        flash = HitFlash()
        flash.trigger(duration_ms=120)
        flash.elapsed_ms = 120
        assert flash.alpha == 0.0

    def test_hit_flash_alpha_zero_duration(self) -> None:
        """HitFlash.alpha is 0.0 when duration_ms=0 (degenerate)."""
        from wet_run.combat.effects_data import HitFlash

        flash = HitFlash()
        # Default duration_ms=0
        assert flash.alpha == 0.0

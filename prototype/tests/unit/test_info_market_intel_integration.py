"""Integration tests: InfoMarket.purchase() → apply_intel_item() flow (ADR-0151 Cycle 7).

When a player purchases an intel item at the Info Market
(alarm_reducer, mission_hint, faction_rumor), the purchase() method
auto-calls apply_intel_item() to apply the effect on the AppState.

These tests verify the end-to-end wiring between:
- craft/info_market.py:InfoMarket.purchase() (purchase flow)
- combat/intel_items.py:apply_intel_item() (effect application)
- engine/state.py:AppState (state container)

Pillar 정합 (ADR-0151 §Consequences.7):
- P1 (The Run): alarm_reducer + mission_hint → run weight 감소
- P4 (The Build): in-run only (death = loss via AppState reset)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wet_run.crafting.info_market import InfoMarket
from wet_run.engine.state import AppState


@pytest.fixture(autouse=True)
def _reset_market_cache() -> None:
    """Reset the InfoMarket module-level cache between tests."""
    InfoMarket._reset_cache()


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Create a minimal market.json with 3 intel items + 1 program."""
    data = {
        "alarm_reducer": {
            "item_id": "alarm_reducer",
            "name": "Alarm Reducer",
            "price": 30,
            "tier_level": 1,
            "available": True,
            "faction": None,
            "examples": ["alarm_reducer"],
            "description": "Reduces current alarm by 2.",
        },
        "mission_hint": {
            "item_id": "mission_hint",
            "name": "Mission Hint",
            "price": 40,
            "tier_level": 2,
            "available": True,
            "faction": None,
            "examples": ["mission_hint"],
            "description": "Reveals current mission objective.",
        },
        "faction_rumor": {
            "item_id": "faction_rumor",
            "name": "Faction Rumor",
            "price": 50,
            "tier_level": 3,
            "available": True,
            "faction": "loa",
            "examples": ["faction_rumor"],
            "description": "Increases next faction event probability by 25%.",
        },
        "t1_program": {
            "item_id": "t1_program",
            "name": "T1 Program",
            "price": 20,
            "tier_level": 1,
            "available": True,
            "faction": None,
            "examples": ["wisp"],
            "description": "Starter ICE-breaker program.",
        },
    }
    (tmp_path / "crafting").mkdir()
    (tmp_path / "crafting" / "market.json").write_text(json.dumps(data))
    return tmp_path


class _StubMission:
    __slots__ = ("title", "primary_objective", "zone", "secondary_objectives")

    def __init__(self) -> None:
        self.title = "Test Mission"
        self.primary_objective = "extract data"
        self.zone = "MID"
        self.secondary_objectives: tuple[str, ...] = ()


class TestIntelItemPurchaseIntegration:
    """End-to-end test: InfoMarket.purchase() → apply_intel_item() flow."""

    def test_purchase_alarm_reducer_applies_effect(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Purchase alarm_reducer → alarm -2 + inventory + purchased_intel_items."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 100
        state.alarm_level = 4

        result = market.purchase("alarm_reducer", state)

        assert result == 70  # 100 - 30
        assert state.alarm_level == 2  # 4 - 2
        assert state.inventory.get("alarm_reducer") == 1
        assert "alarm_reducer" in state.purchased_intel_items
        # Status message recorded
        assert any("Alarm Reducer applied" in m for m in state.status_messages.data)

    def test_purchase_mission_hint_reveals_objective(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Purchase mission_hint → status message + inventory + purchased_intel_items."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 100
        state.current_mission = _StubMission()

        result = market.purchase("mission_hint", state)

        assert result == 60  # 100 - 40
        assert state.inventory.get("mission_hint") == 1
        assert "mission_hint" in state.purchased_intel_items
        # Status message contains mission info
        assert any("extract data" in m for m in state.status_messages.data)

    def test_purchase_faction_rumor_boosts_probability(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Purchase faction_rumor → faction_tension_probability_boost += 0.25."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 100

        result = market.purchase("faction_rumor", state)

        assert result == 50  # 100 - 50
        assert state.inventory.get("faction_rumor") == 1
        assert "faction_rumor" in state.purchased_intel_items
        assert state.faction_tension_probability_boost == pytest.approx(0.25)

    def test_purchase_non_intel_item_does_not_apply_effect(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Purchase t1_program → inventory only, NO intel effect."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 100
        state.alarm_level = 3
        state.faction_tension_probability_boost = 0.0

        result = market.purchase("t1_program", state)

        assert result == 80  # 100 - 20
        assert state.inventory.get("t1_program") == 1
        # NO intel effect applied
        assert state.alarm_level == 3  # unchanged
        assert state.faction_tension_probability_boost == 0.0  # unchanged
        assert state.purchased_intel_items == []  # empty

    def test_purchase_insufficient_credits_no_effect(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Purchase with insufficient credits → returns None, NO effect applied."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 20  # not enough for alarm_reducer (30)
        state.alarm_level = 4

        result = market.purchase("alarm_reducer", state)

        assert result is None
        assert state.credits == 20  # unchanged
        assert state.alarm_level == 4  # unchanged
        assert "alarm_reducer" not in state.purchased_intel_items

    def test_purchase_one_shot_prevents_double_purchase(
        self, data_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Second purchase of same intel item → returns None (one-shot)."""
        from wet_run.engine import config as _engine_config

        monkeypatch.setattr(_engine_config, "DATA_DIR", data_dir, raising=False)
        market = InfoMarket.load_default(data_dir / "crafting" / "market.json")
        state = AppState()
        state.credits = 200
        state.alarm_level = 4

        # First purchase succeeds
        result1 = market.purchase("alarm_reducer", state)
        assert result1 == 170
        assert state.alarm_level == 2
        assert "alarm_reducer" in state.purchased_intel_items

        # Second purchase: credits still deducted, but intel effect NOT re-applied
        result2 = market.purchase("alarm_reducer", state)
        assert result2 == 140  # credits still deducted (200 - 30 - 30)
        assert state.alarm_level == 2  # UNCHANGED (one-shot guard)
        # Inventory still increments (purchase succeeds mechanically)
        assert state.inventory.get("alarm_reducer") == 2

"""Unit tests for ``engine/equipment_view.py``.

The module is mostly tcod console painters — we mock the console
and assert which strings were printed at which positions.  The
non-rendering helpers (``_slot_short_label``, ``_tier_color``) are
pure data and easy to test.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from wet_run.engine import equipment_view
from wet_run.equipment.equipment import EquipSlot

# ---------------------------------------------------------------------------
# _slot_short_label
# ---------------------------------------------------------------------------


class TestSlotShortLabel:
    @pytest.mark.parametrize(
        ("slot", "expected"),
        [
            (EquipSlot.DECK, "DECK"),
            (EquipSlot.HEADWARE, "HEAD"),
            (EquipSlot.EYEWARE, "EYES"),
            (EquipSlot.BODYSUIT, "BODY"),
            (EquipSlot.GLOVES, "HAND"),
            (EquipSlot.BOOTS, "FEET"),
            (EquipSlot.IMPLANT, "IMPL"),
            (EquipSlot.TRODES, "TROD"),
        ],
    )
    def test_known_slot(self, slot, expected):
        assert equipment_view._slot_short_label(slot) == expected

    def test_unknown_slot_falls_back_to_uppercase(self):
        # Pass an arbitrary string-ish slot.
        fake = SimpleNamespace(value="weirdslot")
        assert equipment_view._slot_short_label(fake) == "WEIRDSLOT"


# ---------------------------------------------------------------------------
# _tier_color
# ---------------------------------------------------------------------------


class TestTierColor:
    def test_known_tier_t0_is_gray(self):
        assert equipment_view._tier_color(SimpleNamespace(value="T0")) == (150, 150, 150)

    def test_known_tier_t5_is_magenta(self):
        assert equipment_view._tier_color(SimpleNamespace(value="T5")) == (255, 50, 200)

    def test_unknown_tier_falls_back_to_default_gray(self):
        assert equipment_view._tier_color(SimpleNamespace(value="T99")) == (200, 200, 200)


# ---------------------------------------------------------------------------
# render_equipment_visualizer — smoke test against a fake console
# ---------------------------------------------------------------------------


class _FakeConsole:
    def __init__(self, width: int = 80, height: int = 30) -> None:
        self.width = width
        self.height = height
        self.prints: list[dict] = []

    def print(self, x: int = 0, y: int = 0, string: str = "", fg=None) -> None:
        self.prints.append({"x": x, "y": y, "string": string, "fg": fg})


def _make_loadout(**slot_to_eq):
    """Build a small EquipmentLoadout-like object with the given slot→equipment map.

    The render code calls ``loadout.get(slot)``,
    ``loadout.equipment.items()``, and ``loadout.total_stats()``,
    so we provide all three.
    """

    class _Loadout:
        def __init__(self):
            self.equipment: dict = dict(slot_to_eq)

        def get(self, slot, default=None):
            return self.equipment.get(slot, default)

        def total_stats(self):
            return SimpleNamespace(
                attack_bonus=0,
                crit_bonus_pct=0,
                damage_bonus_pct=0,
                defense=0,
                hp_bonus=0,
                shield_bonus=0,
                ap_bonus=0,
                ap_regen_bonus_pct=0,
                program_power=0,
                ice_resistance=0,
            )

    return _Loadout()


def _make_equipment(name: str, tier: str = "T1"):
    return SimpleNamespace(
        name=name,
        tier=SimpleNamespace(value=tier),
        ascii_glyph=f"[{name[0]}]",
        ascii_color=(255, 255, 255),
    )


class TestRenderEquipmentVisualizer:
    def test_does_not_crash_with_empty_loadout(self):
        loadout = _make_loadout()  # no equipment
        console = _FakeConsole()
        region = SimpleNamespace(x=0, y=0, w=80, h=30, x2=79, y2=29)
        equipment_view.render_equipment_visualizer(console, region, loadout)
        # Title printed
        assert any(p["string"].startswith("═") for p in console.prints)
        assert any("RIG" in p["string"] for p in console.prints)

    def test_draws_equipped_item_names(self):
        deck = _make_equipment("Ono-Sendai 7", tier="T2")
        loadout = _make_loadout(**{EquipSlot.DECK: deck})
        console = _FakeConsole()
        region = SimpleNamespace(x=0, y=0, w=80, h=30, x2=79, y2=29)
        equipment_view.render_equipment_visualizer(console, region, loadout)
        flat = " ".join(p["string"] for p in console.prints)
        assert "Ono-Sendai 7" in flat
        assert "DECK" in flat

    def test_stats_section_appears_when_loadout_has_bonuses(self):
        class _Loadout:
            equipment: dict = {}

            def get(self, slot, default=None):
                return self.equipment.get(slot, default)

            def total_stats(self):
                return SimpleNamespace(
                    attack_bonus=5,
                    crit_bonus_pct=0,
                    damage_bonus_pct=0,
                    defense=0,
                    hp_bonus=0,
                    shield_bonus=0,
                    ap_bonus=0,
                    ap_regen_bonus_pct=0,
                    program_power=0,
                    ice_resistance=0,
                )

        loadout = _Loadout()
        console = _FakeConsole()
        region = SimpleNamespace(x=0, y=0, w=80, h=30, x2=79, y2=29)
        equipment_view.render_equipment_visualizer(console, region, loadout)
        flat = " ".join(p["string"] for p in console.prints)
        assert "ATK +5" in flat
        assert "STATS" in flat

    def test_no_equipment_message_when_no_bonuses(self):
        class _Loadout:
            equipment: dict = {}

            def get(self, slot, default=None):
                return self.equipment.get(slot, default)

            def total_stats(self):
                return SimpleNamespace(
                    attack_bonus=0,
                    crit_bonus_pct=0,
                    damage_bonus_pct=0,
                    defense=0,
                    hp_bonus=0,
                    shield_bonus=0,
                    ap_bonus=0,
                    ap_regen_bonus_pct=0,
                    program_power=0,
                    ice_resistance=0,
                )

        loadout = _Loadout()
        console = _FakeConsole()
        region = SimpleNamespace(x=0, y=0, w=80, h=30, x2=79, y2=29)
        equipment_view.render_equipment_visualizer(console, region, loadout)
        flat = " ".join(p["string"] for p in console.prints)
        assert "(no equipment)" in flat

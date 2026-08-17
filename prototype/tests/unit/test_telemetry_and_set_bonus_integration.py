"""Tests for Telemetry and Set Bonus Integration (Round 5)."""

from __future__ import annotations

from wet_run.combat.telemetry import TELEMETRY_EVENT_TYPES
from wet_run.combat.telemetry_integration import (
    TelemetryConfig,
    TelemetryIntegrator,
    make_event,
    should_record_event,
)
from wet_run.equipment.equipment import (
    STARTER_DECK,
    STARTER_HEADWARE,
    EquipmentLoadout,
    EquipStats,
)
from wet_run.equipment.set_bonus_integration import (
    SetBonusSummary,
    apply_set_bonuses_to_stats,
    calculate_set_bonus,
    get_active_set_ids,
    get_all_set_bonuses,
    get_best_set_bonus_for,
    get_set_bonus_definitions,
    get_set_count,
)


class TestTelemetryBasics:
    """TelemetryIntegrator basic operations."""

    def test_create_integrator(self) -> None:
        integrator = TelemetryIntegrator()
        assert integrator.is_enabled() is False
        assert integrator.get_event_count() == 0

    def test_opted_in_creates_enabled(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        assert integrator.is_enabled() is True

    def test_record_event(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record("death", {"ice_type": "black"})
        assert integrator.get_event_count() == 1

    def test_record_event_without_opt_in(self) -> None:
        integrator = TelemetryIntegrator()
        integrator.record("death", {"ice_type": "black"})
        assert integrator.get_event_count() == 0


class TestTelemetryEventTypes:
    """Telemetry event type helpers."""

    def test_supported_events(self) -> None:
        types = [
            "death",
            "kill",
            "deck_chosen",
            "mutator_chosen",
            "boss_reached",
            "mission_completed",
            "run_completed",
        ]
        for t in types:
            assert should_record_event(t) is True

    def test_unsupported_event(self) -> None:
        assert should_record_event("unknown_event") is False

    def test_get_supported_events(self) -> None:
        events = TELEMETRY_EVENT_TYPES
        assert "death" in events
        assert "kill" in events
        assert "deck_chosen" in events

    def test_make_event(self) -> None:
        event = make_event("death", {"ice_type": "black"})
        assert event.event_type == "death"
        assert event.data == {"ice_type": "black"}
        assert event.timestamp_ms > 0


class TestTelemetrySpecificEvents:
    """TelemetryIntegrator specific event recording."""

    def test_record_death(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_death("black_ice", turn=10)
        assert integrator.get_event_count() == 1

    def test_record_kill(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_kill("construct_proxy", turn=15)
        assert integrator.get_event_count() == 1

    def test_record_deck_chosen(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_deck_chosen("standard")
        assert integrator.get_event_count() == 1

    def test_record_mutator_chosen(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_mutator_chosen("alarm_surge")
        assert integrator.get_event_count() == 1

    def test_record_boss_reached(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_boss_reached("neuromancer")
        assert integrator.get_event_count() == 1

    def test_record_mission_completed(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_mission_completed("aleph_fragment", grade=4)
        assert integrator.get_event_count() == 1

    def test_record_run_completed(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_run_completed("run_001", grade=6)
        assert integrator.get_event_count() == 1


class TestTelemetryAggregation:
    """TelemetryIntegrator aggregation helpers."""

    def test_aggregate_death_rates(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_death("black_ice")
        integrator.record_death("black_ice")
        integrator.record_death("watchdog")
        rates = integrator.aggregate_death_rates()
        assert rates.get("black_ice") == 2
        assert rates.get("watchdog") == 1

    def test_aggregate_kill_counts(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_kill("construct_proxy")
        integrator.record_kill("construct_proxy")
        integrator.record_kill("black_ice")
        counts = integrator.aggregate_kill_counts()
        assert counts.get("construct_proxy") == 2
        assert counts.get("black_ice") == 1

    def test_aggregate_deck_distribution(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_deck_chosen("standard")
        integrator.record_deck_chosen("light")
        integrator.record_deck_chosen("standard")
        dist = integrator.aggregate_deck_distribution()
        assert dist.get("standard") == 2
        assert dist.get("light") == 1

    def test_aggregate_mutator_choices(self) -> None:
        config = TelemetryConfig(opted_in_at_start=True)
        integrator = TelemetryIntegrator(config)
        integrator.record_mutator_chosen("alarm_surge")
        integrator.record_mutator_chosen("construct_proxy")
        choices = integrator.aggregate_mutator_choices()
        assert choices.get("alarm_surge") == 1
        assert choices.get("construct_proxy") == 1


class TestTelemetryConfig:
    """TelemetryConfig dataclass."""

    def test_default_config(self) -> None:
        config = TelemetryConfig()
        assert config.enabled is False
        assert config.opted_in_at_start is False

    def test_enabled_config(self) -> None:
        config = TelemetryConfig(enabled=True, opted_in_at_start=True)
        assert config.enabled is True
        assert config.opted_in_at_start is True


class TestSetBonusIntegration:
    """Set bonus integration with EquipmentLoadout."""

    def test_calculate_set_bonus_empty(self) -> None:
        loadout = EquipmentLoadout()
        summary = calculate_set_bonus(loadout)
        assert summary.has_any_bonus() is False
        assert summary.total_bonus.attack_bonus == 0

    def test_calculate_set_bonus_with_items(self) -> None:
        loadout = EquipmentLoadout()
        loadout.equip(STARTER_DECK)
        loadout.equip(STARTER_HEADWARE)
        summary = calculate_set_bonus(loadout)
        assert isinstance(summary, SetBonusSummary)

    def test_get_active_set_ids(self) -> None:
        loadout = EquipmentLoadout()
        loadout.equip(STARTER_DECK)
        loadout.equip(STARTER_HEADWARE)
        active = get_active_set_ids(loadout)
        assert isinstance(active, tuple)

    def test_get_set_count(self) -> None:
        loadout = EquipmentLoadout()
        loadout.equip(STARTER_DECK)
        count = get_set_count(loadout, loadout.equipment[STARTER_DECK.slot].set_id)
        assert count >= 1

    def test_get_set_count_no_set(self) -> None:
        loadout = EquipmentLoadout()
        assert get_set_count(loadout, "nonexistent_set") == 0

    def test_get_best_set_bonus_for(self) -> None:
        loadout = EquipmentLoadout()
        loadout.equip(STARTER_DECK)
        bonus = get_best_set_bonus_for(loadout, STARTER_DECK.set_id)
        if STARTER_DECK.set_id is not None:
            assert bonus is None or isinstance(bonus, EquipStats)

    def test_get_best_set_bonus_for_no_set(self) -> None:
        loadout = EquipmentLoadout()
        assert get_best_set_bonus_for(loadout, "nonexistent_set") is None

    def test_get_all_set_bonuses(self) -> None:
        loadout = EquipmentLoadout()
        bonuses = get_all_set_bonuses(loadout)
        assert isinstance(bonuses, list)

    def test_apply_set_bonuses_to_stats(self) -> None:
        loadout = EquipmentLoadout()
        base = EquipStats(attack_bonus=10, defense=5)
        result = apply_set_bonuses_to_stats(base, loadout)
        assert result.attack_bonus >= 10
        assert result.defense >= 5

    def test_get_set_bonus_definitions(self) -> None:
        defs = get_set_bonus_definitions()
        assert isinstance(defs, dict)


class TestSetBonusSummary:
    """SetBonusSummary dataclass."""

    def test_has_any_bonus_empty(self) -> None:
        summary = SetBonusSummary(
            active_set_ids=(),
            set_count={},
            total_bonus=EquipStats(),
        )
        assert summary.has_any_bonus() is False

    def test_has_any_bonus_with_set_id(self) -> None:
        summary = SetBonusSummary(
            active_set_ids=("ono_sendai",),
            set_count={"ono_sendai": 2},
            total_bonus=EquipStats(),
        )
        assert summary.has_any_bonus() is True

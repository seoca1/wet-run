"""Automated tests mirroring testcases/combat/salvage.md (TC-COMBAT-001 ~ 012).

Source spec: Game/roguelike_sprawl/testcases/combat/salvage.md

Status (2026-08-07, ADR-0147): HEAL/FRAG/CRED/SKIP all implemented in
``combat/salvage.py``. 4 previously-xfailed tests now pass; 8 new tests
cover FRAG/CRED/alarm trade-off (TC-COMBAT-007~012).

Scope:
- TC-COMBAT-001: HEAL — 기본 회복 (P0, Active)
- TC-COMBAT-002: HEAL — max HP일 때 (P1, Active)
- TC-COMBAT-003: HEAL — 사망 직전 (P1, Active)
- TC-COMBAT-004: SKIP — 보상 없음 (P1, Active)
- TC-COMBAT-007: HEAL — 티어별 max HP (P1, Active)
- TC-COMBAT-008: FRAG / CRED — no longer placeholder (P2, Active)
- TC-COMBAT-009: FRAG — 선택 (P1, Active) — ADR-0147
- TC-COMBAT-010: CRED — 선택 (P1, Active) — ADR-0147
- TC-COMBAT-011: Alarm trade-off (P1, Active) — ADR-0147
- TC-COMBAT-012: SKIP — state 변화 없음 (P1, Active)
"""

from __future__ import annotations

from roguelike_sprawl.combat.salvage import (
    ALARM_HIGH_THRESHOLD,
    CRED_ALARM_RELIEF,
    CRED_CREDITS,
    FRAG_YIELD,
    HEAL_PCT,
    SalvageChoice,
    apply_salvage,
)

HEAL_PCT = HEAL_PCT  # alias for readability


class _StubState:
    """Minimal state for unit-testing ``apply_salvage`` without AppState.

    Mirrors the attributes used by ``apply_salvage``: hp, max_hp,
    credits, alarm_level, salvage_fragments, status_messages.
    """

    __slots__ = (
        "hp",
        "max_hp",
        "credits",
        "alarm_level",
        "salvage_fragments",
        "status_messages",
    )

    def __init__(
        self,
        *,
        hp: int = 50,
        max_hp: int = 100,
        credits: int = 0,
        alarm_level: int = 0,
        salvage_fragments: int = 0,
    ) -> None:
        self.hp = hp
        self.max_hp = max_hp
        self.credits = credits
        self.alarm_level = alarm_level
        self.salvage_fragments = salvage_fragments
        self.status_messages: list[str] = []


class TestTcCombat001HealBasic:
    """TC-COMBAT-001: HEAL — 기본 회복.

    Given: 자키 HP 50/100, max HP 100
    When: ICE 격파 → HEAL 선택
    Then: HP = 50 + (100 * 0.15) = 65
    Then: 매트릭스로 복귀
    Then: HUD에 "+15 HP" 또는 "HEAL applied" 메시지 표시
    """

    def test_hp_increases_by_max_hp_pct(self) -> None:
        state = _StubState(hp=50, max_hp=100)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 65
        assert state.hp == 65

    def test_hp_does_not_exceed_max(self) -> None:
        state = _StubState(hp=95, max_hp=100)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 100
        assert state.hp == 100

    def test_status_message_records_heal(self) -> None:
        state = _StubState(hp=50, max_hp=100)
        apply_salvage(state, SalvageChoice.HEAL)
        assert any("HEAL applied" in m for m in state.status_messages)


class TestTcCombat002HealMaxHp:
    """TC-COMBAT-002: HEAL — max HP일 때.

    Given: 자키 HP 100/100, max HP 100
    When: ICE 격파 → HEAL 선택
    Then: HP = 100 (변화 없음)
    Then: "no damage to repair" 메시지 표시
    Then: 매트릭스로 복귀
    """

    def test_hp_unchanged_at_max(self) -> None:
        state = _StubState(hp=100, max_hp=100)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 100
        assert state.hp == 100

    def test_no_damage_message_at_max(self) -> None:
        state = _StubState(hp=100, max_hp=100)
        apply_salvage(state, SalvageChoice.HEAL)
        assert any("no damage to repair" in m for m in state.status_messages)


class TestTcCombat003HealNearDeath:
    """TC-COMBAT-003: HEAL — 사망 직전.

    Given: 자키 HP 5/100, max HP 100
    When: ICE 격파 → HEAL 선택
    Then: HP = 5 + 20 = 25
    Then: 자키는 살아남음
    Then: 매트릭스로 복귀
    """

    def test_near_death_player_survives(self) -> None:
        state = _StubState(hp=5, max_hp=100)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 20
        assert state.hp == 20
        assert new_hp > 0


class TestTcCombat004Skip:
    """TC-COMBAT-004: SKIP — 보상 없음.

    Given: 자키 HP 30/100, max HP 100
    When: ICE 격파 → SKIP 선택
    Then: HP = 30 (변화 없음)
    Then: 매트릭스로 복귀
    Then: 보상 없음 (전략적 선택)
    """

    def test_skip_leaves_hp_unchanged(self) -> None:
        state = _StubState(hp=30, max_hp=100, credits=100, alarm_level=2)
        new_hp = apply_salvage(state, SalvageChoice.SKIP)
        assert new_hp == 30
        assert state.hp == 30
        assert state.credits == 100
        assert state.alarm_level == 2
        assert state.salvage_fragments == 0

    def test_skip_status_message(self) -> None:
        state = _StubState(hp=30, max_hp=100)
        apply_salvage(state, SalvageChoice.SKIP)
        assert any("salvage skipped" in m for m in state.status_messages)


class TestTcCombat007HealTierScaling:
    """TC-COMBAT-007: HEAL — 티어별 max HP.

    Given: T1 자키 (max HP 100), T3 자키 (max HP 150)
    When: 둘 다 HEAL 선택
    Then: T1 = +20 HP, T3 = +30 HP
    Then: 회복량 = max HP의 20% (티어에 비례)
    """

    def test_t1_heal_yields_15(self) -> None:
        state = _StubState(hp=50, max_hp=100)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 65  # 50 + 15

    def test_t3_heal_yields_22(self) -> None:
        state = _StubState(hp=50, max_hp=150)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 72  # 50 + round(150*0.15) = 50 + 22 (banker's rounding)

    def test_t5_heal_yields_45(self) -> None:
        state = _StubState(hp=100, max_hp=300)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 145  # 100 + round(300*0.15) = 100 + 45


class TestTcCombat008FragCredNotPlaceholder:
    """TC-COMBAT-008: FRAG / CRED — no longer placeholder.

    Validates that FRAG/CRED are implemented (not "Phase 6+: not yet
    implemented" placeholders). Confirmed via apply_salvage returning
    sensible state changes for these choices.
    """

    def test_frag_is_implemented(self) -> None:
        state = _StubState(hp=50, max_hp=100, salvage_fragments=0)
        apply_salvage(state, SalvageChoice.FRAG)
        assert state.salvage_fragments == FRAG_YIELD

    def test_cred_is_implemented(self) -> None:
        state = _StubState(hp=50, max_hp=100, credits=0, alarm_level=1)
        apply_salvage(state, SalvageChoice.CRED)
        assert state.credits == CRED_CREDITS
        assert state.alarm_level == 0  # 1 - 1 = 0 (clamped)


class TestTcCombat009Frag:
    """TC-COMBAT-009: FRAG 선택 (ADR-0147).

    Given: 자키 HP 50/100, alarm_level 0, salvage_fragments 0
    When: ICE 격파 → FRAG 선택
    Then: salvage_fragments += 1
    Then: HP 변화 없음
    Then: 상태 메시지: ">>> FRAG recovered: +1 program fragment"
    """

    def test_frag_increments_salvage(self) -> None:
        state = _StubState(hp=50, max_hp=100, alarm_level=0, salvage_fragments=0)
        new_hp = apply_salvage(state, SalvageChoice.FRAG)
        assert state.salvage_fragments == 1
        assert new_hp == 50  # HP unchanged
        assert state.hp == 50

    def test_frag_accumulates(self) -> None:
        state = _StubState(salvage_fragments=2)
        apply_salvage(state, SalvageChoice.FRAG)
        assert state.salvage_fragments == 3

    def test_frag_status_message(self) -> None:
        state = _StubState(salvage_fragments=0)
        apply_salvage(state, SalvageChoice.FRAG)
        assert any("FRAG recovered" in m for m in state.status_messages)


class TestTcCombat010Cred:
    """TC-COMBAT-010: CRED 선택 (ADR-0147).

    Given: 자키 HP 50/100, alarm_level 2, credits 0
    When: ICE 격파 → CRED 선택
    Then: credits += 30
    Then: alarm_level -= 1 (→ 1, clamped ≥ 0)
    Then: HP 변화 없음
    Then: 상태 메시지: ">>> CRED recovered: +30 credits, alarm -1"
    """

    def test_cred_adds_30_and_reduces_alarm(self) -> None:
        state = _StubState(hp=50, max_hp=100, credits=0, alarm_level=2)
        new_hp = apply_salvage(state, SalvageChoice.CRED)
        assert state.credits == 30
        assert state.alarm_level == 1  # 2 - 1
        assert new_hp == 50  # HP unchanged

    def test_cred_alarm_clamped_at_zero(self) -> None:
        state = _StubState(credits=0, alarm_level=0)
        apply_salvage(state, SalvageChoice.CRED)
        assert state.alarm_level == 0  # clamped, no negative

    def test_cred_status_message(self) -> None:
        state = _StubState(alarm_level=1)
        apply_salvage(state, SalvageChoice.CRED)
        assert any("CRED recovered" in m for m in state.status_messages)
        assert any("alarm -1" in m for m in state.status_messages)


class TestTcCombat011AlarmTradeoff:
    """TC-COMBAT-011: Alarm trade-off (ADR-0147).

    Given: alarm_level >= ALARM_HIGH_THRESHOLD (3)
    When: CRED 또는 FRAG 선택
    Then: yield 50% 감소 (rounded down, min 0)
    Then: alarm reduction still applies
    Then: 상태 메시지: ">>> alarm high — reduced yield" (yellow warning)
    """

    def test_cred_yield_reduced_at_high_alarm(self) -> None:
        state = _StubState(credits=0, alarm_level=ALARM_HIGH_THRESHOLD)
        apply_salvage(state, SalvageChoice.CRED)
        # 50% of 30 = 15 (rounded down)
        assert state.credits == 15
        # alarm reduction still applied
        assert state.alarm_level == ALARM_HIGH_THRESHOLD - 1

    def test_cred_yield_reduced_at_alarm_4(self) -> None:
        state = _StubState(credits=0, alarm_level=4)
        apply_salvage(state, SalvageChoice.CRED)
        assert state.credits == 15
        assert state.alarm_level == 3

    def test_frag_lost_at_high_alarm(self) -> None:
        state = _StubState(salvage_fragments=0, alarm_level=ALARM_HIGH_THRESHOLD)
        apply_salvage(state, SalvageChoice.FRAG)
        # 50% of 1 = 0.5 → 0 (min 0)
        assert state.salvage_fragments == 0

    def test_cred_full_yield_below_threshold(self) -> None:
        state = _StubState(credits=0, alarm_level=ALARM_HIGH_THRESHOLD - 1)
        apply_salvage(state, SalvageChoice.CRED)
        assert state.credits == CRED_CREDITS

    def test_alarm_reduced_status_message(self) -> None:
        state = _StubState(alarm_level=ALARM_HIGH_THRESHOLD)
        apply_salvage(state, SalvageChoice.CRED)
        assert any("alarm high" in m for m in state.status_messages)

    def test_heal_unaffected_by_alarm(self) -> None:
        # Pillar 3 weight preservation: HEAL always yields 15% max HP
        # regardless of alarm level.
        state = _StubState(hp=50, max_hp=100, alarm_level=5)
        new_hp = apply_salvage(state, SalvageChoice.HEAL)
        assert new_hp == 65
        assert state.alarm_level == 5  # unchanged


class TestTcCombat012Skip:
    """TC-COMBAT-012: SKIP — state 변화 없음 (ADR-0147).

    Given: 자키 HP 50/100, alarm_level 2, credits 100
    When: ICE 격파 → SKIP 선택
    Then: 모든 state 변화 없음
    Then: 상태 메시지: ">>> salvage skipped"
    """

    def test_skip_no_state_change(self) -> None:
        state = _StubState(
            hp=50,
            max_hp=100,
            credits=100,
            alarm_level=2,
            salvage_fragments=5,
        )
        new_hp = apply_salvage(state, SalvageChoice.SKIP)
        assert new_hp == 50
        assert state.hp == 50
        assert state.credits == 100
        assert state.alarm_level == 2
        assert state.salvage_fragments == 5

    def test_skip_status_message(self) -> None:
        state = _StubState()
        apply_salvage(state, SalvageChoice.SKIP)
        assert any("salvage skipped" in m for m in state.status_messages)


class TestSalvageConstants:
    """Verify Pillar-validated constants are stable (ADR-0147)."""

    def test_heal_pct_is_15_percent(self) -> None:
        assert HEAL_PCT == 0.15

    def test_frag_yield_is_1(self) -> None:
        assert FRAG_YIELD == 1

    def test_cred_credits_is_30(self) -> None:
        assert CRED_CREDITS == 30

    def test_cred_alarm_relief_is_1(self) -> None:
        assert CRED_ALARM_RELIEF == 1

    def test_alarm_high_threshold_is_3(self) -> None:
        assert ALARM_HIGH_THRESHOLD == 3

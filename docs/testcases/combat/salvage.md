# TC-COMBAT: Data Salvage (전투 승리 보상)

> **관련**: `../../decisions/0014-data-salvage.md`, `../../decisions/0003-combat-system.md`
> **관련 design**: `../../design/core_loop.md` (combat micro-loop)

ICE 격파 후 salvage 메뉴와 회복/보상 흐름에 대한 시나리오.

## TC-COMBAT-001: HEAL — 기본 회복 (P0, Active)

**Given**: 자키 HP 50/100, max HP 100
**When**: ICE 격파 → HEAL 선택
**Then**: HP = 50 + (100 * 0.20) = 70
**Then**: 매트릭스로 복귀
**Then**: HUD에 "+20 HP" 또는 "HEAL applied" 메시지 표시

## TC-COMBAT-002: HEAL — max HP일 때 (P1, Active)

**Given**: 자키 HP 100/100, max HP 100
**When**: ICE 격파 → HEAL 선택
**Then**: HP = 100 (변화 없음)
**Then**: "no damage to repair" 메시지 표시 (자원 낭비 알림)
**Then**: 매트릭스로 복귀

## TC-COMBAT-003: HEAL — 사망 직전 (P1, Active)

**Given**: 자키 HP 5/100, max HP 100
**When**: ICE 격파 → HEAL 선택
**Then**: HP = 5 + 20 = 25
**Then**: 자키는 살아남음
**Then**: 매트릭스로 복귀

## TC-COMBAT-004: SKIP — 보상 없음 (P1, Active)

**Given**: 자키 HP 30/100, max HP 100
**When**: ICE 격파 → SKIP 선택
**Then**: HP = 30 (변화 없음)
**Then**: 매트릭스로 복귀
**Then**: 보상 없음 (전략적 선택)

## TC-COMBAT-005: Disengage — salvage 없음 (P0, Active)

**Given**: 자키가 ICE와 전투 중
**When**: `[ESC]` disengage
**Then**: ICE 격파 X → salvage 메뉴 표시 X
**Then**: 알람 / trace 위험 +1
**Then**: 매트릭스 잔류, 다음 행동 가능

## TC-COMBAT-006: Death — salvage 없음 (P0, Active)

**Given**: 자키 HP 0
**When**: 전투 패배
**Then**: flatline 화면 표시
**Then**: salvage 메뉴 표시 X
**Then**: 자키 영구 종료, 메인 메뉴로

## TC-COMBAT-007: HEAL — 티어별 max HP (P1, Active)

**Given**: T1 자키 (max HP 100), T3 자키 (max HP 150)
**When**: 둘 다 HEAL 선택
**Then**: T1 = +20 HP, T3 = +30 HP
**Then**: 회복량 = max HP의 20% (티어에 비례)

## TC-COMBAT-008: FRAG / CRED — Phase 6+ placeholder (P2, Active)

**Given**: ICE 격파 → salvage 메뉴
**When**: FRAG 또는 CRED 선택
**Then**: "Phase 6+: not yet implemented" 메시지
**Then**: 보상 없음 (Phase 5 범위 외)

## TC-COMBAT-009: FRAG 선택 (P1, Active) — ADR-0147

**Given**: 자키 HP 50/100, alarm_level 0, salvage_fragments 0
**When**: ICE 격파 → FRAG 선택
**Then**: `state.salvage_fragments` += 1 (→ 1)
**Then**: HP 변화 없음
**Then**: 상태 메시지: ">>> FRAG recovered: +1 program fragment"
**Then**: 매트릭스로 복귀

## TC-COMBAT-010: CRED 선택 (P1, Active) — ADR-0147

**Given**: 자키 HP 50/100, alarm_level 2, credits 0
**When**: ICE 격파 → CRED 선택
**Then**: `state.credits` += 30 (→ 30)
**Then**: `state.alarm_level` -= 1 (→ 1, clamped ≥ 0)
**Then**: HP 변화 없음
**Then**: 상태 메시지: ">>> CRED recovered: +30 credits, alarm -1"
**Then**: 매트릭스로 복귀

## TC-COMBAT-011: Alarm trade-off (P1, Active) — ADR-0147

**Given**: 자키 HP 50/100, alarm_level 3, credits 0
**When**: ICE 격파 → CRED 선택
**Then**: CRED yield 50% 감소: `state.credits` += 15 (50% of 30, rounded down)
**Then**: `state.alarm_level` -= 1 (→ 2, alarm reduction unaffected)
**Then**: 상태 메시지: ">>> alarm high — reduced yield" (yellow warning)
**Then**: 매트릭스로 복귀

**Given**: alarm_level 3, FRAG 선택
**Then**: FRAG yield: salvage_fragments += 0 (50% of 1, min 0)
**Then**: 상태 메시지: ">>> alarm high — fragment lost in noise"

## TC-COMBAT-012: SKIP (P1, Active)

**Given**: 자키 HP 50/100, alarm_level 2, credits 100
**When**: ICE 격파 → SKIP 선택
**Then**: 모든 state 변화 없음
**Then**: 상태 메시지: ">>> salvage skipped"
**Then**: 매트릭스로 복귀

## Phase 5+ 자동화 (예정)

- `tests/unit/test_salvage.py` — HEAL/SKIP 로직 단위 테스트
- `tests/integration/test_combat_salvage.py` — combat → salvage → matrix 흐름
- 회귀 테스트: 매 combat 시스템 변경 시

## Phase 6+ 자동화 (ADR-0147, v1.1.0+ Cycle 1)

- `tests/unit/test_salvage_scenarios.py` — TC-COMBAT-001~012 전체 단위 테스트
  - 4 xfail → pass (HEAL/SKIP 기본 동작)
  - TC-007, 008 신규 (tier-scaled HEAL, FRAG/CRED not-placeholder)
  - TC-009~012 신규 (FRAG/CRED/alarm trade-off/SKIP)
- 회귀: alarm_level / salvage_fragments / credits 의 state 변화 검증

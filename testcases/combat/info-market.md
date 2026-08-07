# TC-INTEL: Info Market Intel Items (ADR-0151, Cycle 6)

> **관련**: `../../decisions/0151-info-market-intel-items.md`, `../../decisions/0147-data-salvage-phase6.md`
> **관련 design**: `../../design/systems/combat.md` §Info Market Intel Items
> **구현**: `../../prototype/src/roguelike_sprawl/combat/intel_items.py`

3 intel items purchasable with CRED at the Info Market. Closes the salvage 3-way trade-off (HEAL / FRAG / CRED) by giving CRED a consumption path.

## TC-INTEL-001: alarm_reducer Reduces Alarm by 2 (P0, Active)

**Given**: 자키 `state.credits = 50`, `state.alarm_level = 4`
**When**: Info Market 에서 `alarm_reducer` 구매 (30 credits)
**Then**: `state.credits -= 30` (→ 20)
**Then**: `state.alarm_level -= 2` (→ 2, clamped ≥ 0)
**Then**: `state.purchased_intel_items` 에 `"alarm_reducer"` 추가
**Then**: 상태 메시지: ">>> Alarm Reducer applied: alarm -2 (4 → 2)"

## TC-INTEL-002: alarm_reducer Clamped at 0 (P1, Active)

**Given**: 자키 `state.credits = 50`, `state.alarm_level = 1`
**When**: `alarm_reducer` 구매
**Then**: `state.alarm_level = max(0, 1 - 2) = 0` (clamped)
**Then**: 상태 메시지: ">>> Alarm Reducer applied: alarm -1 (1 → 0)" (실제 감소량만 표시)

## TC-INTEL-003: mission_hint Reveals Objective (P0, Active)

**Given**: 자키 현재 미션 = `extract_data` (objective: find DATA node)
**When**: `mission_hint` 구매 (40 credits)
**Then**: `state.credits -= 40`
**Then**: 상태 메시지: ">>> Mission Hint: objective = 'find DATA node', zone = 'MID', recommended = 'sensor node 3A'"
**Then**: `state.purchased_intel_items` 에 `"mission_hint"` 추가

## TC-INTEL-004: mission_hint without active mission (P2, Active)

**Given**: `state.current_mission = None` (hub state, no active mission)
**When**: `mission_hint` 구매
**Then**: 상태 메시지: ">>> Mission Hint: no active mission — info cached for next run"

## TC-INTEL-005: faction_rumor Increases Event Probability (P0, Active)

**Given**: 자키 `state.credits = 80`, faction = `loa` (rep = 0, NEUTRAL)
**When**: `faction_rumor` 구매 (50 credits, faction discount 적용)
**Then**: `state.credits -= 50 * 0.85` (TRUSTED discount, → 37 or similar)
**Then**: `app_state.faction_tension_probability_boost = 0.25` (next event 25% boost)
**Then**: 상태 메시지: ">>> Faction Rumor: Loa contacts — next event probability +25%"

## TC-INTEL-006: faction_rumor no faction discount (P1, Active)

**Given**: faction = `loa` rep = -80 (OUTCAST)
**When**: `faction_rumor` 구매
**Then**: `state.credits -= 50 * 1.5 = 75` (OUTCAST markup)
**Then**: 상태 메시지: ">>> Faction Rumor: Loa contacts — discounted: 75 credits (markup)"

## TC-INTEL-007: One-Shot Per Item (P0, Active)

**Given**: 자키가 이미 `alarm_reducer` 구매
**When**: 재구매 시도
**Then**: 거부 — ">>> already purchased: alarm_reducer (one-shot per run)"
**Then**: `state.credits` 변화 없음
**Then**: `state.alarm_level` 변화 없음

## TC-INTEL-008: Insufficient CRED (P0, Active)

**Given**: `state.credits = 20`
**When**: `alarm_reducer` 구매 시도 (가격 30)
**Then**: 거부 — ">>> insufficient credits: 20 < 30"
**Then**: `state.credits` 변화 없음
**Then**: `state.purchased_intel_items` 변화 없음

## TC-INTEL-009: Apply After Death Reset (P1, Active)

**Given**: `app_state.purchased_intel_items = ["alarm_reducer", "mission_hint"]` (이전 run)
**When**: 자키 사망 → 새 run 시작 → `AppState` 재생성
**Then**: `purchased_intel_items` reset to `[]` (Pillar 4 in-run only)

## TC-INTEL-010: Hub Display Categories Intel Separately (P2, Active)

**Given**: Info Market UI render
**When**: `app_state.credits = 100`, faction = NEUTRAL
**Then**: 3 categories 표시: "Programs", "ICE-Breakers", "Intel"
**Then**: Intel category 에 3 items (alarm_reducer 30, mission_hint 40, faction_rumor 50)
**Then**: Cannot afford items 회색 표시

## TC-INTEL-011: mission_hint with multiple objectives (P2, Active)

**Given**: 현재 미션에 3 objectives (extract + bypass + defeat)
**When**: `mission_hint` 구매
**Then**: 상태 메시지: ">>> Mission Hint: 3 objectives — next: 'extract data' (zone: MID)"

## TC-INTEL-012: Faction Rumor discount calc (P2, Active)

**Given**: faction = `loa` rep = 50 (FRIENDLY tier → 0.65 multiplier)
**When**: `faction_rumor` 구매
**Then**: `state.credits -= 50 * 0.65 = 33` (rounded, min 1)
**Then**: 상태 메시지: ">>> Faction Rumor: 33 credits (FRIENDLY discount)"

## 자동화 (예정)

- `tests/unit/test_intel_items.py` — TC-INTEL-001~012 단위 테스트
- `tests/integration/test_intel_purchase_e2e.py` — 전체 픽서 purchase 흐름
- 회귀: 매 salvage / market / mission 시스템 변경 시

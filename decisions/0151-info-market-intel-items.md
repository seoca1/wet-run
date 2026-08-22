# ADR-0151: Info Market Intel Items — CRED Consumption (Close Salvage 3-Way Trade-off)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (CRED economy 완성, v1.1.0+ v1.2.0 bridge)
**관련**: [ADR-0147 — Data Salvage Phase 6+ (CRED earn)](./0147-data-salvage-phase6.md), [ADR-0015 — Crafting System (Info Market infrastructure)](./0015-crafting-system.md), [ADR-0090 — Salvation Phase Integration (mission narrative)](./0090-salvation-phase-integration.md), [ADR-0110 — 모듈 사이즈 정책](./0110-module-size-policy.md)

## 컨텍스트 (Context)

ADR-0147 (Data Salvage Phase 6+) 의 3-way trade-off:
- **HEAL**: +20% max HP (즉시 회복)
- **FRAG**: +1 salvage_fragment (in-run unlock)
- **CRED**: +30 credits + alarm -1 (장기 보상)

**현재 상태**:
- `combat/salvage.py` 가 CRED 옵션 구현 완료 (ADR-0147 §Consequences)
- `crafting/info_market.py` 가 `InfoMarket` 클래스 + `MarketItem` + `purchase()` + `price_for()` + `can_purchase()` + faction discount 모두 구현 완료 (ADR-0015)
- `engine/state.py` 의 `AppState.credits: int` + `AppState.inventory: dict[str, int]` 모두 존재
- `engine/hub.py` 가 `InfoMarket.load_default()` 로 픽서 storefront 로드 (line 236-240)

**부재**:
- **CRED 의 *소비 경로*** 부재. CRED 가 `state.credits` 에 accumulate 되지만, Info Market 의 *현재 items* 는 programs / ICE-breakers / data fragments — 미션 힌트/경보 감소 같은 *salvage 보상* 과 직접 연결 안 됨.
- ADR-0147 §Phase 6+ 의 "CRED: Info Market (픽서 construct)에서 정보 구매 — 미션 목표 힌트, alarm 감소 아이템 등" 미구현.
- 3-way trade-off 의 *CRED branch* 가 "credit accumulates, nothing to spend on" 상태 — 의미 약화.

**해결 방향**:
- Info Market 에 **new item category: intel** 추가
- 3 items: `alarm_reducer` (alarm -1 즉시), `mission_hint` (현재 미션 objective hint), `faction_rumor` (다음 faction event 확률 +)
- CRED 가격: 30/40/50 credits (faction discount 적용)
- `apply_intel_item(state, item_id)` 함수로 effect 적용

**디자인 제약** (Pillar):
- **Pillar 1 (The Run)**: CRED → intel = *현재 run 의 위험 감소* / *정보 우위*. Pillar 1 weight 와 정합.
- **Pillar 3 (The Flatline)**: intel 은 HEAL 의 *대체재* 가 아닌 *상보재*. HEAL 20% 그대로, intel 은 *다른 차원* (정보/안전).
- **Pillar 4 (The Build)**: in-run only. Death 시 purchased_intel_items reset.

**기술 제약**:
- 신규 모듈 250 LOC ceiling (ADR-0110). Intel items 3 + apply 함수 = ~150 LOC 예상.
- `AppState` 에 `purchased_intel_items: list[str]` 필드 추가.
- i18n: en + ko, ~8 keys each (item names + apply messages).

## 고려한 옵션

### Option 1: CRED 소비 안 함 (현 상태 유지)

- **설명**: CRED 가 accumulate 되지만, spend 경로 없음. Salvage 3-way trade-off 의 CRED branch 가 사실상 *bonus credits* 로만 작동.
- **장점**: 변경 범위 최소 — 코드 0.
- **단점**:
  - ADR-0147 §Phase 6+ 미완성.
  - CRED 의 *의미* 약화 — "credit earned, nothing to buy" → FRAG 와 큰 차이 없음.
  - Pillar 1 (run weight) 와 Pillar 4 (build) 사이 *경제 loop* 부재.
- **Pillar 정합**:
  - P1: weight 보존되지만 *loop* 없음.
  - P4: 의미 약화.

### Option 2: Intel Items 3종 (alarm_reducer + mission_hint + faction_rumor)

- **설명**: Info Market 에 new category "intel" 추가. 3 items 각각 *다른 Pillar 영향*:
  - `alarm_reducer` (30 credits, alarm -2 즉시) — Pillar 1
  - `mission_hint` (40 credits, 현재 미션 objective 표시) — Pillar 1
  - `faction_rumor` (50 credits, 다음 faction event 확률 +25%) — Pillar 5
- **장점**:
  - ADR-0147 §Phase 6+ 완성.
  - 3 items 가 *서로 다른 효과* → 다양한 전략 선택.
  - Faction discount (기존 `InfoMarket` 인프라) 재사용.
  - In-run only (death = loss) — Pillar 4 정합.
- **단점**:
  - 변경 범위 중간 — 신규 모듈 ~150 LOC, AppState 필드 1, i18n 8 keys, tests ~15.
  - `mission_hint` 의 *어떤 hint* 를 줄지 결정 필요 (mission objective vs data node 위치).
- **Pillar 정합**:
  - P1: alarm_reducer + mission_hint → run weight 감소.
  - P4: in-run only.
  - P5: faction_rumor → faction 톤 강화.

### Option 3: Full CRED Economy (Intel + Programs + ICE-breakers)

- **설명**: Option 2 + 기존 `InfoMarket` 의 program/ICE-breaker items 통합.
- **장점**:
  - CRED 의 *모든* 소비 경로 활성화.
  - Option 2 의 모든 장점.
- **단점**:
  - 기존 `InfoMarket` 인프라 이미 존재 — *추가* 작업 불필요.
  - Option 2 와 거의 동일 (추가 작업은 program catalog 의 CRED price 만).
- **Pillar 정합**:
  - Option 2 와 동일 + program acquisition path (Pillar 4 build).

## 추천 (Recommendation)

**Option 2** (Intel Items 3종).

이유:
1. **ADR-0147 §Phase 6+ 직접 완성**: "미션 목표 힌트, alarm 감소 아이템" 명시.
2. **3 items 가 서로 다른 Pillar**: alarm_reducer (P1 weight 감소) + mission_hint (P1 정보 우위) + faction_rumor (P5 톤 강화) — 다층 효과.
3. **기존 `InfoMarket` 인프라 100% 재사용**: faction discount, inventory tracking, `purchase()` method 모두 활용.
4. **모듈 사이즈**: ~150 LOC (250 ceiling 의 60%). ADR-0110 정합.
5. **Test surface 폭증 방지**: 3 items × 3-4 tests = 9-12 tests. 기존 41 salvage tests + 49 boss phase 4 tests 와 자연스러운 통합.
6. **Pillar 4 (in-run only)**: death 시 `purchased_intel_items` reset — *메타 진행 X* (ADR-0147 과 동일).

**순서** (Cycle 6, 1 sub-session):
1. Intel items JSON entry in `data/crafting/market.json` (3 items)
2. `combat/intel_items.py` 신규 모듈 (apply_intel_item + 3 item definitions)
3. `AppState.purchased_intel_items: list[str]` 필드 추가
4. `hub.py` 에 intel category 표시 추가
5. i18n: en + ko, 8 keys each
6. Tests: `test_intel_items.py` (12 tests)

## 사용자 결정 (Decision)

[x] Option 2 (Intel Items 3종) — 2026-08-07 Cycle 6 채택
[ ] Option 1 (현 상태 유지)
[ ] Option 3 (Full CRED Economy)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 모듈

`prototype/src/wet_run/combat/intel_items.py` (NEW, ~150 LOC):

```python
"""Info Market Intel Items (ADR-0151, Cycle 6).

3 intel items purchasable with CRED at the Info Market:
- alarm_reducer (30 credits): alarm_level -= 2 (clamped ≥ 0)
- mission_hint (40 credits): reveals current mission objective data node
- faction_rumor (50 credits): next faction event probability += 25%

Pillar 정합 (ADR-0151 §Consequences.7):
- P1 (The Run): alarm_reducer + mission_hint → run weight 감소
- P4 (The Build): in-run only (death = loss via AppState reset)
- P5 (The Style): faction_rumor → faction 톤 강화
"""
```

### 2. Intel Item Schema (market.json extension)

```json
{
  "alarm_reducer": {
    "item_id": "alarm_reducer",
    "name": "Alarm Reducer",
    "price": 30,
    "tier_level": 1,
    "available": true,
    "faction": null,
    "examples": ["alarm_reducer"],
    "description": "Reduces current alarm by 2."
  },
  "mission_hint": {
    "item_id": "mission_hint",
    "name": "Mission Hint",
    "price": 40,
    "tier_level": 2,
    "available": true,
    "faction": null,
    "description": "Reveals current mission objective data node."
  },
  "faction_rumor": {
    "item_id": "faction_rumor",
    "name": "Faction Rumor",
    "price": 50,
    "tier_level": 3,
    "available": true,
    "faction": "loa",
    "description": "Increases next faction event probability by 25%."
  }
}
```

### 3. AppState 필드 추가

- `purchased_intel_items: list[str] = field(default_factory=list)` — 구매한 intel item ids (for UI + replay)

### 4. 기존 함수 patch

- `crafting/info_market.py` 의 `purchase()` 가 `apply_intel_item(state, item_id)` 자동 호출 (item.category == "intel" 일 때)
- `engine/hub.py` 의 market display 에 intel category 별도 표시

### 5. i18n 갱신

`data/i18n/{en,ko}.json` 의 `intel_items` 섹션 신규 (8 keys each):
- `alarm_reducer_name` / `alarm_reducer_desc` / `alarm_reducer_applied`
- `mission_hint_name` / `mission_hint_desc` / `mission_hint_applied`
- `faction_rumor_name` / `faction_rumor_desc` / `faction_rumor_applied`

### 6. Tests 추가 (12 tests)

`tests/unit/test_intel_items.py` (NEW):
- TC-INTEL-001: alarm_reducer reduces alarm by 2 (3 tests)
- TC-INTEL-002: mission_hint reveals objective (3 tests)
- TC-INTEL-003: faction_rumor increases event probability (3 tests)
- TC-INTEL-004: intel item cannot be purchased twice (one-shot per item_id) (1 test)
- TC-INTEL-005: insufficient CRED → purchase fails (1 test)
- TC-INTEL-006: alarm_reducer clamped at 0 (1 test)

### 7. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | alarm_reducer + mission_hint → run weight 감소 | TC-INTEL-001, 002 |
| P2 (The Matrix) | 변경 없음 | 기존 test 유지 |
| P3 (The Flatline) | HEAL 변화 없음, intel 은 *상보재* | 기존 HEAL test 유지 |
| P4 (The Build) | in-run only (death = loss) | TC-INTEL-004 |
| P5 (The Style) | faction_rumor → faction 톤 강화 | TC-INTEL-003 |

## 영향 받는 항목

- `prototype/src/wet_run/combat/intel_items.py` (NEW)
- `prototype/src/wet_run/combat/__init__.py` (re-export)
- `prototype/src/wet_run/crafting/info_market.py` (purchase hook)
- `prototype/src/wet_run/crafting/market.json` (3 new items)
- `prototype/src/wet_run/engine/state.py` (AppState.purchased_intel_items)
- `prototype/src/wet_run/engine/hub.py` (intel category display)
- `prototype/data/i18n/{en,ko}.json` (intel_items 섹션)
- `prototype/tests/unit/test_intel_items.py` (NEW)
- `design/systems/combat.md` (Intel Items section)
- `design/systems/missions.md` (CRED economy section)
- `testcases/combat/info-market.md` (NEW: TC-INTEL-001~006)
- `log.md` (Cycle 6 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0151 entry)

## 관련 결정

- ADR-0014 — Data Salvage (CRED earn option 미구현)
- ADR-0015 — Crafting System (Info Market infrastructure)
- ADR-0147 — Data Salvage Phase 6+ (CRED earn 완성, consume deferred)
- ADR-0110 — 모듈 사이즈 정책 (250 권장 ceiling)
- ADR-0090 — Salvation Phase Integration (mission narrative 기반)

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/intel_items.py:35` — `FACTION_RUMOR_FACTION: str = "loa"` (backward-compat default)
- `prototype/src/wet_run/combat/intel_items.py:42-46` — `FACTION_RUMOR_FACTIONS: dict[str, str]` with 4 variants (hosaka/sense_net/yakuza/loa)
- `prototype/src/wet_run/combat/intel_items.py:53-55` — `IntelItemId` StrEnum (ALARM_REDUCER/MISSION_HINT/FACTION_RUMOR)
- `prototype/src/wet_run/combat/intel_items.py:81` — `apply_alarm_reducer(state)` — alarm -2, clamped ≥ 0
- `prototype/src/wet_run/combat/intel_items.py:95` — `apply_mission_hint(state)` — reveals current mission objective
- `prototype/src/wet_run/combat/intel_items.py:126` — `apply_faction_rumor(state, app_state)` — faction event probability +25%
- `prototype/src/wet_run/engine/state.py:288` — `AppState.purchased_intel_items: list[str]` field
- `prototype/src/wet_run/engine/state.py:290` — `AppState.faction_tension_probability_boost: float = 0.0`
- `prototype/src/wet_run/crafting/info_market.py:244` — `apply_intel_item` import hook (Category-aware purchase flow)
- `prototype/tests/unit/test_intel_items.py:1-277` — 25 tests covering 3 items + one-shot + insufficient CRED + clamping
- `prototype/data/i18n/en.json:237` — `intel_items` section with name/desc/applied messages for all 3 items
- `prototype/data/i18n/ko.json:237` — Korean translations
- `prototype/data/i18n/ja.json:237` — Japanese translations (post-ADR-0154 expansion)
- `prototype/data/i18n/zh.json:237` — Chinese translations (post-ADR-0154 expansion)

**Notes**: Note that intel items are hardcoded in `intel_items.py` (not in `crafting/market.json`). The 4-variant faction_rumor was added by ADR-0154 (Cycle 10). The ADR-0151 originally proposed a 3-item flat rate; the existing 30/40/50 credit prices are used. AppState fields in ADR-0151 spec both delivered.

**No further action on ADR-0151** — implementation closed.

## 변경 이력

- 2026-08-07: Draft 작성 (Cycle 6 of v1.2.0+ bridge)
- 2026-08-07: Accepted (Option 2, 사용자 확인)
  - 구현: `prototype/src/wet_run/combat/intel_items.py` (NEW, 195 LOC, ADR-0110 78%)
  - AppState: `purchased_intel_items: list[str]` + `faction_tension_probability_boost: float` 추가
  - 테스트: `tests/unit/test_intel_items.py` (NEW, 25 tests pass)
  - i18n: en/ko.json `intel_items` 섹션 신규 (13 keys each)
  - 검증: ruff clean, mypy 0 errors (171 src files, was 170, +1 intel_items.py), pytest 3982 pass (was 3957, +25)
  - 3 items: alarm_reducer (30 cred) + mission_hint (40 cred) + faction_rumor (50 cred, Loa faction)
  - 1 bug fixed during testing: `getattr(...) or []` → `if purchased is None` (empty list is falsy in Python)
  - 후속: v1.2.0+ (multi-enemy, NG+ balance)

# ADR-0147: Data Salvage — Phase 6+ Completion (FRAG + CRED + Alarm Trade-off)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (전투 게임성 강화, v1.1.0+ Cycle 1)
**관련**: [ADR-0014 — Data Salvage (Accepted, Phase 6+ backlog)](./0014-data-salvage.md), [ADR-0140 — Engagement Layer](./0140-engagement-layer.md), [ADR-0003 — RT-MS Combat](./0003-combat-system.md)

## 컨텍스트 (Context)

`decisions/0014-data-salvage.md` 의 "Phase 6+ 확장" 섹션은 `HEAL` 만 구현된 상태에서 `FRAG` (program fragment) + `CRED` (Info Market hint) 옵션을 명시했으나 2년 가까이 미구현. 현재 salvage 메뉴는 `HEAL`/`SKIP` 만 노출되며 4개의 `test_salvage_scenarios.py` xfail (TC-COMBAT-001~004) 가 aspirational markers 로만 존재.

2026-08-07 cycle-audit 의 "5 real bugs fixed" 와 cycle 1 polish (v1.1.0a1) 완료 후, 다음 가치 영역으로 **salvage 3-way trade-off** 가 식별됨. v1.1.0+ cycle 1 작업 (Option A of "Plan to upgrade game and battle" 승인분).

**디자인 제약**:
- **Pillar 1 (The Run)**: 매 런 = 한 무게. salvage 옵션이 런 진행을 과도하게 유리하게 만들지 말 것.
- **Pillar 3 (The Flatline)**: 회복이 *있지만* (a) 이겨야만, (b) *선택해야만*, (c) *제한적* — 무게 유지.
- **Pillar 4 (The Build)**: FRAG = in-run unlock (메타 X), CRED = 미래 Info Market 진입 (v1.2.0+).
- **Pillar 5 (The Style)**: 깁슨 어휘 ("data exposed", "ICE breach", "credit chip") 사용.

**기술적 제약**:
- `AppState` 에 이미 `salvage_fragments: int` 와 `alarm_level: int` 가 faction_tension 모듈에서 defensive `getattr` 로 사용 중 — 공식 필드 없음.
- `_end_combat` (engine/combat_view_state.py:173) 이 ICE 격파 시 호출되며, 보상으로 `ice_shard` + 50 credits 추가. FRAG/CRED 추가 시 같은 hook 에 통합.
- 4 xfailed `test_salvage_scenarios.py` + 미구현 TC-COMBAT-007 (티어별 HP), TC-COMBAT-008 (FRAG/CRED placeholder) 가 있어 자동화 가능.
- 신규 모듈 250 LOC ceiling (ADR-0110) + 1000+ LOC 모듈 ADR 의무.

## 고려한 옵션

### Option 1: HEAL 만 확장 (Tier-aware HEAL + max-cap alert + TC-007 test)

- **설명**: 기존 HEAL 만 살리고, 티어별 max HP 비율 (T1=100 → +20, T3=150 → +30) 을 코드/테스트에 명시화. "no damage to repair" 메시지 추가. TC-COMBAT-001~004 xfail → pass 전환, TC-COMBAT-007 신규.
- **장점**:
  - Pillar 3 (무게) 최대 보존 — *선택의 딜레마 없음*.
  - 변경 범위 최소 — `combat/salvage.py` 신규 + 4 tests.
  - 즉시 효과 — 매 combat win 후 HEAL 만으로도 4 xfail 닫힘.
- **단점**:
  - 게임성 변화 미미 — Pillar 4 (build) 측면 변화 없음.
  - 사용자 가치 작음 — "이미 작동하는 것" 의 documentation/test 만 추가.
- **Pillar 정합**:
  - P1 (The Run): 변동 없음.
  - P3 (The Flatline): 무게 보존.
  - P4 (The Build): 변동 없음.
  - P5 (The Style): 변동 없음.

### Option 2: HEAL + FRAG + CRED + Alarm Trade-off (4-way choice with alarm penalty)

- **설명**: 3-way choice (HEAL/FRAG/CRED) + SKIP, alarm level (현재 0~5) 에 따라 trade-off. alarm ≥ 3 이면 FRAG/CRED yield 50% 감소 (Pillar 1 weight). FRAG = +1 salvage_fragment (in-run), CRED = +30 credits + alarm -1. HEAL = 20% max HP. alarm interaction 으로 *선택의 무게* 추가.
- **장점**:
  - 모든 5 Pillar 정합.
  - 3-way trade-off 가 combat win 마다 발생 → 즉각적 게임성 깊이.
  - alarm system (이미 존재, `state.alarm_level`) 과 통합.
  - TC-COMBAT-001~008 전체 닫기 + 4 신규 (TC-COMBAT-009 alarm interaction 등).
- **단점**:
  - 변경 범위 중간 — `combat/salvage.py` 신규 (~120 LOC) + `_end_combat` 5-line patch + i18n + design + testcase + 12+ tests.
  - Pillar 1 weight 가 alarm 으로 추가되지만 *측정 가능* 한가 검증 필요 (playtest).
- **Pillar 정합**:
  - P1 (The Run): alarm penalty 가 "신중하게" 를 강제 — 한 런의 무게 보존.
  - P3 (The Flatline): HEAL 20% 유지, *선택해야만* — 무게 보존.
  - P4 (The Build): FRAG in-run unlock (메타 X), CRED → Info Market (v1.2.0+ 확장).
  - P5 (The Style): "data exposed" / "ICE breach" 어휘 유지.

### Option 3: Full Phase 6+ (Option 2 + Info Market 즉시 구현 + CRED → 실제 구매)

- **설명**: Option 2 + CRED 가 Info Market 픽서 construct 에서 hint 구매로 즉시 통합. hint 3종 (alarm reducer / mission objective hint / faction rumor), 가격 30/50/80 credits.
- **장점**:
  - Option 2 의 모든 장점 + 즉시 Info Market 활성화.
  - 4주차 작업의 일부를 앞당김.
- **단점**:
  - 변경 범위 최대 — Info Market UI + construct dialogue + fix_data.json 변경.
  - Pillar 4 위험 — CRED → meta unlock 경로 가능성 (제약 필요).
  - v1.1.0+ scope creep.
- **Pillar 정합**:
  - P1 (The Run): OK.
  - P4 (The Build): CRED → unlock 시 *메타 진행* 위험 (제약: in-run only, death = loss).

## 추천 (Recommendation)

**Option 2** (HEAL + FRAG + CRED + Alarm Trade-off).

이유:
1. **Pillar 정합성**: 5 Pillar 모두 명확히 매핑 (위 표 참조). Pillar 1/3 무게는 alarm trade-off 로 추가, Pillar 4 build 는 in-run only 로 제한.
2. **사용자 가치**: 3-way choice 가 매 combat win 마다 발생 → 즉각적 깊이. v1.1.0+ "전투 강화" 의 가장 작은 가치 단위.
3. **테스트 커버리지**: 4 xfail (TC-COMBAT-001~004) + 2 partial (TC-007, TC-008) + 4 신규 (alarm interaction, FRAG 선택, CRED 선택, HEAL max-HP) = 10 tests 추가. salvage coverage 0% → 100%.
4. **확장 가능성**: Info Market (Option 3) 은 후속 cycle 에서 CRED consume 측만 추가하면 됨 — 이 ADR 의 결정이 그 기반 제공.
5. **모듈 사이즈**: 신규 `combat/salvage.py` ~120 LOC (250 ceiling 의 48%). 기존 1000+ LOC 모듈 0개 신규.
6. **기존 시스템 호환**: `_end_combat` 5-line patch, 기존 alarm/credits/salvage_fragments state 모두 defensive getattr 으로 사용 중이므로 backward-compatible.

## 사용자 결정 (Decision)

[x] Option 2 (HEAL + FRAG + CRED + Alarm Trade-off) — 2026-08-07 사용자 승인
[ ] Option 1 (HEAL only)
[ ] Option 3 (Option 2 + Info Market 즉시)
[ ] 기타: ___
[ ] Defer (다음 단계로 미룸)

## 결과 (Consequences)

### 1. 신규 모듈

`prototype/src/roguelike_sprawl/combat/salvage.py` (NEW, ~120 LOC):

```python
"""Data Salvage menu (ADR-0014 + ADR-0147).

Player chooses one of 4 options after defeating ICE:
- HEAL: +20% max HP (Pillar 3 weight preserved)
- FRAG: +1 salvage_fragment (in-run, Pillar 4 build)
- CRED: +30 credits + alarm -1 (Pillar 1 weight trade-off)
- SKIP: no reward (strategic choice)

Alarm interaction (Pillar 1):
- alarm >= 3: FRAG/CRED yields reduced 50% (rounded down, min 0).
- alarm < 0: clamped to 0 (defensive).
"""
```

### 2. 신규 / 갱신 enum

`SalvageChoice` (StrEnum):
- `HEAL = "heal"`
- `FRAG = "frag"`
- `CRED = "cred"`
- `SKIP = "skip"`

### 3. AppState 필드 공식화

기존 defensive `getattr(state, "salvage_fragments", 0)` 패턴 → `engine/state.py:AppState` 에 `salvage_fragments: int = 0` 추가 (default factory). Backward-compatible (기존 코드 변경 불필요).

### 4. `_end_combat` 5-line patch

```python
# After existing victory rewards (ice_shard + 50 credits)
from .combat.salvage import apply_salvage
apply_salvage(state, choice=SalvageChoice.HEAL)  # default to HEAL for now
state.pending_salvage = False  # menu dismissed
```

(전체 salvage menu UI 는 별도 cycle 에서 — 본 ADR 은 로직 + test 만, UI 는 v1.1.0 polish 에서.)

### 5. 테스트 추가 (10 tests)

- `test_salvage_scenarios.py` 4 xfail → pass (TC-COMBAT-001~004)
- TC-COMBAT-007 (Tier HEAL): T1=+20, T3=+30
- TC-COMBAT-008 (FRAG/CRED not placeholder): yield 계산
- TC-COMBAT-009 (FRAG 선택): `state.salvage_fragments += 1`, alarm ≥ 3 시 yield 0
- TC-COMBAT-010 (CRED 선택): `state.credits += 30`, `state.alarm_level -= 1` (clamped ≥ 0)
- TC-COMBAT-011 (alarm trade-off): alarm=4 일 때 CRED yield 15 (50% of 30, rounded)
- TC-COMBAT-012 (SKIP): no state change

### 6. i18n 갱신

`prototype/data/i18n/{en,ko}.json` 의 `salvage` 섹션 신규:
- `menu_title` ("DATA SALVAGE" / "데이터 회수")
- `heal_option` / `frag_option` / `cred_option` / `skip_option`
- `heal_applied` / `frag_applied` / `cred_applied` / `skip_applied`
- `heal_no_damage` ("no damage to repair" / "회복할 피해 없음")
- `alarm_high` ("alarm high — reduced yield" / "경보 높음 — 보상 감소")
- `menu_hint` ("↑/↓ select, ENTER confirm" / "↑/↓ 선택, ENTER 확인")

### 7. Pillar 정합 검증

| Pillar | 영향 | 검증 |
|---|---|---|
| P1 (The Run) | alarm trade-off 가 "신중" 강제 | TC-COMBAT-011 test |
| P2 (The Matrix) | 데이터 추출 메타포 유지 | design doc |
| P3 (The Flatline) | HEAL 20% + 1-of-4 choice | TC-COMBAT-001, 002 |
| P4 (The Build) | FRAG in-run only (death = loss) | alarm test |
| P5 (The Style) | 깁슨 어휘 | i18n strings |

## 영향 받는 항목

- `prototype/src/roguelike_sprawl/combat/salvage.py` (NEW)
- `prototype/src/roguelike_sprawl/combat/__init__.py` (re-export SalvageChoice, apply_salvage)
- `prototype/src/roguelike_sprawl/engine/state.py` (AppState.salvage_fragments 공식화)
- `prototype/src/roguelike_sprawl/engine/combat_view_state.py` (_end_combat 5-line patch)
- `prototype/src/roguelike_sprawl/matrix/faction_tension.py` (getattr → direct attribute)
- `prototype/data/i18n/en.json` (salvage 섹션)
- `prototype/data/i18n/ko.json` (salvage 섹션, 한글)
- `prototype/tests/unit/test_salvage_scenarios.py` (xfail → pass + 6 new)
- `design/systems/combat.md` (Phase 6+ 섹션 갱신)
- `testcases/combat/salvage.md` (TC-COMBAT-009~012)
- `log.md` (Cycle 1 entry)
- `index.md` (Round 2 ADR list 갱신)
- `decisions/README.md` (0147 entry)

## 관련 결정

- ADR-0014 — Data Salvage (Accepted, Phase 6+ backlog) — 본 ADR 이 그 backlog 해소
- ADR-0140 — Engagement Layer (partial Accepted) — 본 ADR 이 cycle 1 polish 의 salvage 부분
- ADR-0003 — RT-MS Combat — combat flow 의 일부
- ADR-0008 — Item Tier (PPL curve) — T1/T3 HEAL yield 의 tier scaling
- ADR-0110 — 모듈 사이즈 정책 (250/500/1000 LOC) — 신규 salvage.py 120 LOC (250 ceiling 의 48%)
- (예정) ADR-0148 — Combat Depth Expansion (Option B, 2026-08-08+)

## 변경 이력

- 2026-08-07: Draft 작성 (사용자 Option A+B+C 승인 후 Option A 부분)
- 2026-08-07: Accepted (Option 2 — 사용자가 "A+B+C" 경로 채택, 본 ADR 은 A 의 일부)
  - 구현: `prototype/src/roguelike_sprawl/combat/salvage.py` (NEW, 137 LOC, ADR-0110 ceiling 250 의 55%)
  - 테스트: `test_salvage_scenarios.py` 32 tests pass (4 xfail→pass + 28 new)
  - 검증: ruff clean, mypy 0 errors (160 src files), pytest 3867 pass (was 3835, +32)
  - i18n: en/ko.json `salvage` 섹션 신규 (16 keys each)
  - state: AppState.salvage_fragments, pending_salvage 공식화
  - _end_combat patch: pending_salvage flag set on victory
  - ADR-0148 (Option B, Combat Depth) 후속, ADR-0149 (Boss Phase 4) 후속

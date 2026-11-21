# ADR-0339: g4의 "+33.1pp MISS"는 낡은 목표다 — 난이도 신호인가, 목표 초과인가

**상태**: Draft (오너 결정 대기)
**날짜**: 2026-11-19
**결정자**: 사용자
**우선순위**: P1 (난이도 · 설계)

## 컨텍스트 (Context)

전수 검증(2026-11-19)의 P2: `npm run survival`(64 시드)이 **g4 = 83.1% vs 목표 50% (+33.1pp MISS)** 를
보고했다. 파고들었더니 **목표 자체가 낡았다.**

## 측정 (Measurement)

| 지표 | 값 |
|---|---|
| per-mission g4 | 83.1% (목표 50%) |
| per-encounter g4 | 100% (`npm run balance`) |
| 캠페인 g4 완주 | 64.3% (g3 50.0% → **상단 역전**) |

- **ADR-0229 가 ADR-0211 의 per-grade 목표를 공식 supersede**했다: *"the two calibration constants now
  describe the baseline, not a set of targets to be chased."* `GRADE_TARGETS`(g4 0.5)는 그 **낡은 목표**를
  그대로 들고 있어 `<-- MISS` 를 찍는다 — 즉 **목표 초과가 아니라 기준선 대비 드리프트**다.
- **진짜 신호는 ADR-0319**: "이긴 싸움이 몸을 낫게 한다"(per-fight heal floor)가 들어오면서 g4 의
  난이도(attrition, 소모전)가 사라졌다 — 세션 기록: *"g4 의 난이도는 attrition 이었고, floor 가 그것을
  제거한다"*. 그래서 g4 가 g3 보다 쉬워졌다(캠페인 64.3% > 50.0%).
- **레버**: g4 의 ICE HP cap(95)은 **monotonicity 불변식**(c3≤c4=165)에 묶여 위로 못 올린다(최대 ~76.3%).
  남은 손잡이는 **per-grade damage bonus** `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE = [50,30,-32,0,-10,-10]`
  의 g4 값(현재 **0**)과 **heal floor 값**이다.

## 고려한 옵션

### Option A — 재기록 (목표를 현재 기준선에 맞춘다)
- **설명**: `GRADE_TARGETS` g4 를 ~0.83 으로 재기록하고 `mission_survival` 의 "MISS" 어휘를 "signal" 로.
- **장점**: 도구가 더 이상 거짓 경보를 내지 않는다(ADR-0337 과 같은 정직성). 값싸다.
- **단점**: "g4 가 g3 보다 쉽다"는 **실제 설계 문제**를 신호에서 지운다.

### Option B — 난이도 복원 (g4 damage bonus 를 올린다)
- **설명**: g4 dmg bonus 를 0 → (+X) 로 올려 소모전을 되살린다. X 는 `npm run survival` 로 측정.
- **장점**: g4 를 다시 "attrition 등급"으로 만든다(원 설계). 목표(50%)에 근접 가능.
- **단점**: g4 만 손대면 **상단(g5/g6)과의 인접성이 흔들린다**(단조 불변식). ⚠ **오너 튜닝 필요**.
- **Pillar 정합**: P1(The Run — 위험의 사다리).

### Option C — 유지 (의도된 신호로 남긴다)
- **설명**: 현재처럼 `<-- MISS` 를 남겨 "g4 가 쉽다"를 계속 깃발로 세운다(ADR-0319 세션의 선택).
- **장점**: 설계 문제를 잊지 않는다. 무료다.
- **단점**: 도구가 **낡은 목표**로 경보를 내 계속 오독된다(이번 검증처럼).

## 추천 (Recommendation)

**당장은 C + 도구 caveat(이미 적용).** g4 난이도는 **오너 설계 결정**이고, 상단(g5/g6)과 얽혀 있어
단독 조정은 위험하다. 도구에는 ADR-0229 caveat("목표가 아니라 기준선; delta 는 신호")을 넣어
**거짓 경보를 없앴다**. 신호를 더 이상 원치 않으면 **A(재기록)**, g4 를 다시 어렵게 만들려면
**B(damage bonus 튜닝 + 측정)** — 단, B 는 P4(장비↔난이도)와 **함께** 설계해야 한다.

## Jev 자문 (2026-11-21)

Jev System One(WF8 difficulty-curve + Noul)에 물었다. **모두 임계 미만** — 정책상 자동 실행 금지, 사람 surface.

| 질문 | Jev 결과 | 해석 |
|---|---|---|
| 곡선 형태 점수 (mission, best/value) | **score 1.51/5**, conf 0.40 | 비단조(g4>g3)를 감점. "형태가 나쁘다" |
| 곡선 형태 점수 (encounter) | score 2.66/5, conf 0.48 | 단조이나 g1-g3 평탄 |
| "g4>g3 역전이 고쳐야 할 결함인가?" (Noul) | **p = 0.59** | 경계. '결함' 쪽으로 기울지만 0.6 미만 → surface |
| "상단 수정책은?" (Choice) | **raise_ice p=0.58** (cap 0.39) | B(ICE 상향) 쪽이나 저신뢰 |

**Jev 는 "역전은 결함" 쪽으로 기울되 확신하지 못한다.** 그래서 난이도 자체는 **자동 변경하지 않는다** —
오너 결정 유지. (mission 곡선은 64시드에서 g3 83.4 ≈ g4 83.1 로 역전이 미미하고, **캠페인 계약 레벨**
에서만 g4 64.3 > g3 50.0 로 뚜렷하다 — 레버와 대상이 애매하다는 점도 자동 실행을 막는다.)

## 사용자 결정 (Decision)

[ ] Option A — 재기록
[ ] Option B — 난이도 복원(dmg bonus)
[ ] Option C — 유지(신호)
[ ] 기타: ___

## 결과 (Consequences)

(결정 후 작성)

## Implementation Status (2026-11-19)

**Status**: 🟡 Partial (도구 caveat 적용 · 난이도 결정 미정)

**Evidence**:
- `web/scripts/mission_survival.ts` — ADR-0229 caveat 출력("목표가 아니라 기준선; delta 는 신호")

**Notes**: 난이도 자체는 미변경. P4(장비↔난이도)와 동시 설계 권장.

## 영향 받는 항목

- `web/scripts/mission_survival.ts` (caveat)
- (Option B 시) `web/src/core/combat/ice_scaling.ts`

## 관련 결정

- ADR-0229 (곡선 재기준선화 — 목표 supersede) · ADR-0319 (이긴 싸움이 몸을 낫게 한다) ·
  ADR-0211 (원 per-grade 목표) · ADR-0328 (장비 재조정) · ADR-0337 (검증 정직성)

## 변경 이력

- 2026-11-19: Draft 작성 (P2 측정 + 선택지, 오너 결정 대기)

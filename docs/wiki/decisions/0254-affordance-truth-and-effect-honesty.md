# ADR-0254: 어포던스 진실성 — 화면이 약속한 것을 실제로 한다

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 위임 결정 — Jev 결정 계층(`scripts/jev-call.sh`) 선택 + Manus(max) 독립 리뷰, 오너 승인은 "스스로 판단할 수 있는 것부터 후속 진행해줘" (2026-11-02)
**우선순위**: P1 (The Flatline — 화면이 오르는 약속, The Build — 상태 결함)
**관련**: [ADR-0251 — 진실한 프로그램 어포던스 + 전투 무결성 규칙](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0252 — 런 종료·저장 시점](./0252-run-end-and-save-timing.md) · [ADR-0243 — 숫자키 1회 = 카드 1장 실행](./0243-digit-key-repeat-policy.md) · [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md) · [ADR-0239 — VFX RNG 결합 해소(밸런스 기준선)](./0239-vfx-spawn-rng-decoupling.md)

> **이 ADR은 결정 내용을 새로 정하지 않는다.** ADR-0251 규칙 5("화면이 약속하는 동작은 반드시 진실이어야 한다")를
> 그 규칙이 생긴 화면에 **적용**한다. 밸런스 수치는 건드리지 않는다(ADR-0239 기준선 byte-identical).
> ADR-0243(숫자키 즉시 실행)도 변경하지 않는다.

## 컨텍스트 (Context)

ADR-0251이 **열린 질문**으로 남긴 4건과, 후속 감사에서 발견된 2건이 있었다. 추측으로 고치지 않기 위해
**자가 플레이 검증 + AI 위임** 파이프라인을 세웠다: 재현 → Jev 위임 → Manus 독립 리뷰 → 구현 + 회귀 테스트.

증거 전체: [design/affordance-truth-2026-11-03/](../../design/affordance-truth-2026-11-03/README.md).

### 확인된 사실

| # | 사실 | 근거 |
|---|---|---|
| A | **결정타는 COST를 청구하지 않는다.** `useProgram` 의 승리 분기가 `alarm: newAlarm` 대입 전에 반환한다 | 결정적 테스트: 비마지막 10 → **12**, 결정타 10 → **10** |
| B | **손패 행의 `→ 41/100` 은 예측값**이고, 결정타에서는 거짓이 된다. 킬 예측은 규칙 5로 금지 | `program_affordance.ts` · A |
| C | **종결 노드의 loot 화면이 회복도 경로도 약속한다.** `applyLootAction` 은 종결 노드에서 `runPhase: "ending"` 으로 분기해 회복 없이 런을 끝낸다 | `state_actions_phases.ts:168` + 화면 캡처 |
| D | **loot 화면은 `ESC`·`↑↓` 를 약속하는데 둘 다 no-op 이다** | 결정적 테스트: `applyLootAction(cancel)`·`(move_north)` 가 상태를 그대로 돌려준다 |
| E | **프로그램 카탈로그의 설명문이 구현되지 않은 효과를 약속한다.** 웹 티어 리듀서는 `baseDamage = program.tier * 5` 하나만 쓴다 | 실측: `barrier`(방어막 문구) → `ICE SLOW off`, `decoy`(미끼 문구) → `ICE SLOW on` |
| F | **엔딩 HUD 라인이 좁은 패널에서 가로 압축되어 판독 불가.** 캔버스는 줄을 자르지 않고 압축한다 | 폭 검사: before 29자 / 사용 가능 15자(40×60) |

## 고려한 옵션

### 결정 1 — 손패의 COST 표기 (B)

- **Option A**: 결정타에도 COST를 청구한다 — 리듀서 변경 + 밸런스 재측정 필요
- **Option B**: 청구는 그대로 두고 잔여 COST 예측 표기(→ N/100)만 제거한다 — 카드당 COST +N 만
- **Option C**: 라벨에 "결정타는 COST 0" 규칙을 정적으로 고지한다

**결정: Option B.** Jev 선택 0.96 / confidence 0.94. 결정타에 청구하는 Option A 는 **밸런스 수치 변경**이라
오너 결정 사항이며(ADR-0239 기준선), 확신도 0.19 로 사실상 동률이었다. Option B 는 손패가 **카드의 비용**을
말하고 **잔여 예측**을 하지 않으므로 거짓말을 만들지 않는다. 현재 잔여 COST 는 HUD 가 이미 보여준다.

### 결정 2 — 프로그램 카탈로그의 설명문 (E)

- **Option A**: `programs.json` 의 description 30개를 실제 웹 티어 동작으로 다시 쓰고, 설계 의도는 `planned_description` 으로 보존
- **Option B**: 손대지 않고 ADR 에 "PROGRAM INSPECT 구현 시 effect 를 보여줄 것" 을 조건으로 명시
- **Option C**: 게임 화면에 노출하지 않고 참고 전용으로 표시

**결정: Option A.** Jev 선택 1.00. 설명문은 **현재 어느 화면에도 렌더되지 않지만**, Oracle 합성의 다음 슬라이스가
PROGRAM INSPECT(프로그램 상세 보기)라 지금 정리하지 않으면 그때 거짓말이 된다. `plannedDescription` 으로 설계 의도를
보존하므로 효과 배선 세션이 그대로 이어갈 수 있다.

### 결정 3 — 종결 노드의 loot 화면 (C·D)

- **Option A**: 종결 노드에서 회복 문구와 route selection 을 숨기고 `ENTER: run ends` 를 표시한다 (표시만 변경)
- **Option B**: 종결 노드에서도 회복을 실제로 적용한다 (로직 변경 · 엔딩 판정 접촉)
- **Option C**: 회복은 유지하고 문구를 미래형으로 바꾼다

**결정: Option A.** Jev 선택 0.98 / confidence 0.97. Manus 도 "A·B는 UI 표시에 국한되어 위험이 낮다" 로 동의.
`ESC`·`↑↓` promise 는 어느 세션에서도 일어나지 않으므로 함께 제거한다.

### 결정 4 — 엔딩 HUD (F)

- **Option A**: HUD 를 arc 번호(`ARC 4`)로 바꾼다 — 격자가 이미 엔딩 이름을 보여준다
- **Option B**: 다음 세션으로 미룬다

**결정: Option A.** Jev 는 Option B(0.52 / conf 0.42) 였으나 Manus 가 "**E는 즉시 수정 필요성이 강함**" 이라
상반했다. **Jev 에게는 점수가 낮고 리뷰는 즉시 처리를 권했다** — 점수만 믿지 않고 리뷰를 받아 결정했다.
레이아웃 프리셋 hudCols(24/20/16) 대비 29자였던 raw id 를 5자로 바꿨다.

### 결정 5 — select→confirm (ADR-0243 대체)

**결정: 도입하지 않는다.** Jev 선택 0.95 / conf 0.92, Manus 도 "ADR-0243 의 변경을 피하기 위해 유지" 로 동의.
Oracle 합성이 이미 축 1 1순위를 "정보 계층 먼저, confirm 모델은 보류" 로 정했고, 이번에 라벨이 정직해졌으므로
PROGRAM INSPECT 가 그 다음 조각이 된다.

### 결정 6 — `tickIceEffects` 인덱스 결함 (ADR-0251 열린 질문 b)

**결정: 이번 세션에 수정 + 회귀 테스트, 단 독립 커밋으로 분리.** Jev 선택 0.53 / conf 0.44, Manus 는
"**D는 독립 검증 묶음으로 분리**" 하고 "승률 변화 위험" 을 경고했다. 상태 메커닉 변경이라 표시 변경과 분리해
커밋했고(`9baf65c5`), 양 덱 기준선을 재측정해 **byte-identical** 임을 확인했다.

## 결과 (Consequences)

### 바뀐 것

| 대상 | 전 | 후 |
|---|---|---|
| 손패 행 | `1 BACKDOOR  COST +2  → 40/100   TARGET ICE` | `1 BACKDOOR  COST +2          TARGET ICE` |
| 손패 터치 버튼 | `1 COST+2 / BACKDOOR / → 2/100 / ICE` | `1 COST+2 / BACKDOOR / (빈 줄) / ICE` |
| 손패 aria-label | `1 BACKDOOR, COST plus 2, to 2 of 100, target ICE` | `1 BACKDOOR, COST plus 2, cost on the card, target ICE` |
| loot 격자 (종결) | `HEAL applied → 63/100` · `ENTER: route selection \| ESC: back` | `NO HEAL — this was the last node` · `ENTER: run ends` |
| loot HUD | `↑↓: navigate \| ENTER: continue \| ESC: back` | `ENTER: route` / `ENTER: run ends` |
| 엔딩 HUD | `Choice: arc4_liberation_front` (29자, 40×60 에서 압축) | `ARC 4` (5자) |
| 프로그램 description | "Backdoor exploit. Weak damage but consistent armor pierce." (구현 안 됨) | "Deals 10 damage to the ICE." (구현과 일치) — 설계 의도는 `plannedDescription` |
| `tickIceEffects` | 앞 효과가 만료하면 뒤 효과가 잘못 갱신·복제 | 스냅샷 순회로 인덱스 정합 |

### 불변

- **밸런스 기준선 byte-identical** — opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`,
  PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` (ADR-0239).
- **ADR-0243** — 숫자키 1회 = 카드 1장 실행. 변경 없음.
- **ADR-0251 · 0252 · 0250 · 0246 의 결정 내용** — 변경 없음.
- `raw/` — 변경 없음. 게임 메커닉 · 상태 스키마 — 변경 없음(틱 이펙트 배열 처리의 인덱스 정합만).

## Implementation Status (2026-11-03)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:

- 결정적 테스트 — `web/tests/killing_blow_cost.test.ts` (결정타 COST 청구 0),
  `web/tests/loot_input_contract.test.ts` (cancel·이동 키 no-op),
  `web/tests/program_catalog_text.test.ts` (설명문이 실제 효과와 일치),
  `web/tests/ice_combat_effects.test.ts` (만료 후 이웃 효과 보존 — red 로 재현 후 green).
- 폭 검사 — [affordance-truth-2026-11-03](../../design/affordance-truth-2026-11-03/README.md):
  loot HUD 초과 **42자 → 0**, 엔딩 HUD 초과 **29자 → 0**, 3개 레이아웃(80×50 · 60×40 · 40×60) 전부.
- 밸런스 — 양 덱 기준선 byte-identical
  ([balance-opening.txt](../../design/affordance-truth-2026-11-03/balance-opening.txt),
  [balance-ppl.txt](../../design/affordance-truth-2026-11-03/balance-ppl.txt)).
- 테스트 — `npx vitest run` **178 files / 3948 tests passed** (베이스라인 175 / 3932).
- typecheck 0 · eslint 0 errors · build PASS.
- 실제 플레이 — ego-lite Chromium: 손패 행과 loot 화면이 위 표대로 렌더됨을 캡처로 확인.

**Notes**:

- e2e 는 86 passed / 4 skipped / **2 failed**. 실패는 `e2e/idle_alarm.spec.ts:48` 이며
  **세션 이전 커밋 `92ba417b` 소스로 되돌려도 동일하게 재현**된다(직접 검증). 실패 지점이
  `page.keyboard.press("Shift")` 라 창 포커스 문제로 보이며, 이 저장소에서 시간 게이트 e2e 는 로컬 실행이
  불안정하다. 이번 변경과 무관 — 상세는 [evidence README](../../design/affordance-truth-2026-11-03/README.md).

## 열린 질문 (남은 항목)

- **(a) 결정타의 COST 정책.** 결정타에도 청구할 것인가. 그러면 리듀서 변경 + ADR-0239 기준선 재측정이 필요하다.
  지금은 표시만 정직하게 만들었다. **밸런스 수치 변경은 오너 결정 사항.**
- **(b) 프로그램별 실제 효과 배선.** `shield`·`boost`·`decoy`·`cloak`·`probe` 의 설계된 효과.
  `plannedDescription` 에 설계 의도를 보존했다. 배선 시 밸런스 접촉이므로 오너 결정.
- **(c) HUD 좁은 레이아웃 압축.** `> [1] Yakuza Enf HP: 165`(24자)·`Mission: Aleph Fragment`(23자)가
  40×60(사용 가능 15자)에서 압축된다. 기존 결함이며 이번 세션 범위 밖.
- **(d) 종결 노드 loot 의 15% 회복 부재.** ADR-0252 가 "의도로 본다" 고 판단했다(엔딩 판정이 hp 를 쓰는 관계).
  그대로 둔다.

## 영향 받는 항목

- `web/src/core/combat/program_affordance.ts` — 손패 행 · 터치 버튼 · aria-label
- `web/src/core/combat/ice_combat_effects.ts` — 틱 인덱스 정합
- `web/src/core/data_loaders.ts` · `web/src/core/types.ts` — 프로그램 description / plannedDescription
- `web/src/data/programs.json` — description → planned_description (30건)
- `web/src/renderer/ending.ts` · `web/src/renderer/run_screen.ts` — loot · 엔딩 HUD
- `docs/design/affordance-truth-2026-11-03/` — 증거
- `web/tests/` — 회귀 테스트 6개 추가 · 기존 계약 테스트 갱신

## 관련 결정

- ADR-0251 (규칙 5 의 원천) · ADR-0252 (종결 노드 loot) · ADR-0243 (변경 금지) ·
  ADR-0239 (밸런스 기준선) · ADR-0195 (이 문서의 형식)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 위임 결정 (Jev 선택 + Manus 독립 리뷰). 구현 완료.
- 2026-11-03: `tickIceEffects` 인덱스 정합을 독립 커밋(`9baf65c5`)으로 분리 — Manus 권고

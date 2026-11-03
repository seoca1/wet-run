# ADR-0257: 손패가 카드의 효과를 말한다 — 정보 계층

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 요청 ("upgrade battle interaction") — ADR-0255 가 효과를 실재로 만들자 정보 계층이 열렸다
**우선순위**: P1 (The Flatline — 스킬을 이해하고 고르는 것, The Style — 가독성)
**관련**: [ADR-0255 — 카드가 이름대로 동작한다](./0255-card-effects-are-real.md) · [ADR-0251 — 진실한 프로그램 어포던스 + 전투 무결성 규칙](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0254 — 어포던스 진실성](./0254-affordance-truth-and-effect-honesty.md) · [ADR-0243 — 숫자키 1회 = 카드 1장 실행](./0243-digit-key-repeat-policy.md) · [combat-directions Oracle 합성](../../design/combat-directions-2026-11-02/oracle-review-and-synthesis.md)

> **이 ADR은 새 메커니즘을 만들지 않는다. 이미 실재하는 효과를 화면에 드러낸다.** 표시 전용 —
> 밸런스·RNG·리듀서 무변경. ADR-0243(숫자키 즉시 실행)도 변경하지 않는다.

## 컨텍스트 (Context)

Oracle 합성은 전투 UI 개선의 **축 1 순위를 `PROGRAM INSPECT`(정보 계층)** 로 정했다:

> **축 1**: `PROGRAM INSPECT` > `TARGET FIRST` > `COMMAND DECK` > `CARD RAIL`
> - Inspect의 **정보 계층**을 먼저 구현한다.
> - confirm 모델은 **오너가 ADR-0243 대체 여부를 결정할 때까지 보류**한다.
> - TARGET FIRST는 프로그램에 **진실한 타겟/효과 구분**이 생길 때까지 대기.

그리고 그 전제를 명시했다:

> **1-3 `TARGET FIRST`** — … 그러나 **"적용 가능/조건부/불가"는 불가** — 적용성 모델이 없고
> **모든 프로그램이 같은 피해 경로를 탄다.** 표시 전용이면 Short, 실제 적용성/효과면 Large + 밸런스 민감

**ADR-0255 가 그 전제를 뒤집었다.** 오프닝 5장이 이제 실제로 다른 일을 한다:

| 카드 | 실제 효과 | 손패 행이 보여주던 것 |
|---|---|---|
| Backdoor | 방어구 2점 관통 | `COST +2   TARGET ICE` |
| Barrier | 2점 흡수 풀 2턴 | `COST +3   TARGET ICE` |
| Boost | 공격 +2 2턴 | `COST +2   TARGET ICE` |
| Cloak | 받는피해 −15% 2턴 | `COST +2   TARGET ICE` |
| Decoy | 다음타격 50% 흡수 1턴 | `COST +2   TARGET ICE` |

**메커니즘은 실재하지만 화면에는 보이지 않는다.** 카드 이름이 효과를 암시할 뿐이고
"Backdoor"는 "방어구 2점 관통"을 말해주지 않는다. 오너의 원래 판정("스킬 효과를 바로 알아볼 수 없었다")은
**효과가 없던 시절**의 문제였고, ADR-0255 가 효과를 만들었으니 이제 **보이게 하는 것**이 남은 일이다.

또 하나의 계기: ADR-0254 가 거짓 예측 표기(`→ N/100`)를 걷어내면서 손패 행에 **빈 열**이 생겼다.
그 열이 정확히 효과가 들어갈 자리다.

## 고려한 옵션

### Option 1 — select→confirm 상세 보기 (PROGRAM INSPECT 전체)
Oracle 이 "**ADR-0243 대체 여부를 오너가 결정할 때까지 보류**" 로 못 박았다. 숫자키 즉시 실행과
충돌하며 입력 3종(키보드·터치·게임패드)을 다시 써야 한다. **보류.**

### Option 2 — 손패 행에 효과 열을 넣는다 (선택)
ADR-0254 가 비운 열에 효과 태그를 넣는다. 표시 전용이라 밸런스·RNG 무영향.
이름만으로는 알 수 없는 수치("2점", "15%")를 카드별로 보여준다.

### Option 3 — TARGET FIRST (타겟 분석)
`>` 마커가 이미 활성 ICE 를 표시한다. 다중 ICE 에서 "이 카드가 어느 적을 때리는가"는
`TARGET ICE` + 마커로 충분하다. 추가 이득이 작다. **보류.**

**결정: Option 2.** 정보 계층은 Oracle 축 1의 1순위이고, 이제 진실하다(규칙 5 충족).
confirm 모델과 TARGET FIRST 는 오너 결정·추가 모델이 필요해 보류한다.

## 결과 (Consequences)

### 바뀐 것 (표시 전용)

| | 이전 | 이후 |
|---|---|---|
| 80×50 / 60×40 | `1 BACKDOOR  COST +2          TARGET ICE` | `1 BACKDOOR  COST +2   PIERCE 2  TARGET ICE` |
| 40×60 | `1 BACKDOOR  +2            ICE` | `1 BACKDOOR  +2   PIERCE 2 ICE` |
| 40×60 헤더 | `HAND        COST          TARGET` | `HAND        COST EFFECT   TARGET` |
| 터치 버튼 | `1 COST+2 / BACKDOOR / (빈 줄) / ICE` | `1 COST+2 / BACKDOOR / PIERCE 2 / ICE` |
| aria-label | `1 BACKDOOR, COST plus 2, cost on the card, target ICE` | `1 BACKDOOR, COST plus 2, PIERCE 2, target ICE` |

**BLOCKED 우선**: 상한을 넘어 거절되는 카드는 효과 대신 `BLOCKED` 를 표시한다 — 거절된 카드의
효과는 일어날 수 없으므로 그 열을 내주는 것이 진실하다(규칙 5). 테스트가 이를 고정한다.

**파생**: 효과 태그는 `program_effects.ts` 한 표에서 온다. 라벨·설명문·리듀서와 같은 진실을 보므로,
행이 리듀서가 적용하지 않는 효과를 주장할 수 없다.

### 폭 검사 (3개 레이아웃)

| 레이아웃 | 텍스트 폭 | full/compact 최대 | 판정 |
|---|---|---|---|
| 80×50 | 75 | 46 (full) | ✅ |
| 60×40 | 55 | 46 (full) | ✅ |
| 40×60 | 35 | 33 (compact) | ✅ |

### 불변

- **밸런스 byte-identical** — opening `100.0 / 100.0 / 97.5 / 53.4 / 44.1 / 0.3`,
  PPL `100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3` (ADR-0256 기준선).
- 리듀서·RNG·상태 스키마 무변경. `activeMutators`·세이브 스키마 무영향.
- ADR-0243(숫자키 즉시 실행) · ADR-0251(규칙 5) · ADR-0255(효과) 결정 무변경.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/program_affordance.test.ts` — 효과 열이 행·터치·aria 세 채널에 모두 실림을 고정,
  평범한 공격은 빈 열, BLOCKED 가 효과를 대신함, 효과 태그가 `program_effects.ts` 에서 파생.
- `web/tests/touch.test.ts` — 터치 버튼이 같은 사실을 보임(픽스처에 실제 효과 태그).
- 3개 레이아웃 캡처 + 폭 검사 — [hand-effect-column-2026-11-03](../../design/hand-effect-column-2026-11-03/README.md).
  그리드 초과 0 (before/after 동일). HUD 초과 24/23 은 **기존 결함**(ADR-0254 (c))이며 무변경.
- 밸런스 byte-identical — [balance-opening.txt](../../design/hand-effect-column-2026-11-03/balance-opening.txt),
  [balance-ppl.txt](../../design/hand-effect-column-2026-11-03/balance-ppl.txt).
- vitest **179 files / 3960 tests passed** · typecheck 0 · eslint 0 errors · build PASS.
- 실플레이(ego-lite Chromium) — 손패 5행이 위 표대로 렌더됨을 스크린샷으로 확인.

**Notes**:

- 효과 태그는 ≤ 9자로 유지한다. 40×60 의 텍스트 폭이 35자라 가장 긴 `EVADE 15%`/`DECOY 50%`(9자)가
  헤더 정렬을 깨지 않도록 맞췄다.
- confirm 모델(ADR-0243 대체)과 TARGET FIRST 는 Oracle 권고대로 **보류**한다.

## 열린 질문

- **(a) select→confirm 도입 여부.** ADR-0243 을 대체해야 한다(별도 ADR). Oracle 은 정보 계층을
  먼저 하라고 했다 — 이번 ADR 이 그 정보 계층이다.
- **(b) HUD 좁은 레이아웃 압축.** `> [1] Yakuza Enf HP: 165`(24자)·`Mission: Aleph Fragment`(23자)가
  40×60(사용 가능 15자)에서 압축된다. ADR-0254 (c) 그대로 — 이번 범위 밖.
- **(c) TARGET FIRST.** 다중 ICE 에서 카드→타겟 매핑을 더 명시할지. 현재는 `>` 마커 + `TARGET ICE` 로 충분.
- **(d) 나머지 25개 프로그램.** ADR-0255 (b). 효과를 배선하면 이 열이 자동으로 그 효과를 말한다.

## 영향 받는 항목

- `web/src/core/combat/program_affordance.ts` — `effectTag` 필드, full/compact 행, 터치·aria, 헤더, `FULL_ROW_WIDTH`
- `web/tests/program_affordance.test.ts` · `web/tests/touch.test.ts`

## 관련 결정

- ADR-0255 (효과 배선 — 이 열이 말하는 내용) · ADR-0251 (규칙 5) · ADR-0254 (빈 열을 만들었다) ·
  ADR-0243 (보류) · ADR-0256 (기준선)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 오너 요청("upgrade battle interaction"). 구현 완료.

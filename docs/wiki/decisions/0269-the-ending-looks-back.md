# ADR-0269: 엔딩이 그 런을 되돌아보게 — 요약과 정직한 회복 문구

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 ("계속." — 엔딩 완주 감사 후 권고 2·5 승인)
**우선순위**: P2 (서사 연결 / 화면 정직성)
**관련**: [ADR-0252 — 런 종료](./0252-run-end-and-save-timing.md) · [ADR-0263 — 죽음 화면](./0263-defeat-screen-must-be-escapable.md) · [ADR-0251 — 어포던스 진실성 §5](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0268 — 동료 콤보 상한](./0268-ally-synergy-is-bounded.md)

> **엔딩이 그 런을 말하지 않았다.** `LIBERATION FRONT` / "The AIs are free. What have you done?" — 2줄.
> `EndingContext` 는 hp·credits·turns 를 갖고 있었지만 화면에 오르지 않았다. 그리고 **회복이 없었는데
> "회복 적용"이라고 말하는 문장이 두 곳**에 있었다.

## 컨텍스트 (Context)

실제 완주(65스텝) 로그·스크린샷에서 확인:

| 관측 | 근거 |
|---|---|
| 엔딩이 미션·HP·크레딧·턴을 언급하지 않는다 | `06-ending.png` (2줄 + 푸터) |
| HP 100 에서 `HEAL applied → 100/100` | `renderLootScreen` 이 회복량과 무관하게 "applied" |
| HP 100 에서 `… — healed to 100/100` | `continueToMatrix` 메시지가 항상 "healed" |

둘 다 **거짓은 아니지만 의미가 없다**: 15% 회복이 0 을 회복했는데 "적용됨"이라고 쓰면,
플레이어는 화면이 상태를 말해준다고 믿을 수 없다(ADR-0251 §5 의 정신).

## 결정 (Decision)

### 1) 엔딩에 **그 런의 수치**를 붙인다

```ts
export interface EndingSummary { mission; hp; maxHp; credits; turns }
renderEndingScreen(choice, cols, rows, summary: EndingSummary | null = null)
```

- 푸터(`ENTER / ESC: return to title`) **위 2줄**, `GRAY_MID`:
  ```
  Aleph Fragment
  HP 100/100 · 4,000cr · 23 turns
  ```
- **40열 대응**: 폭을 `cols - 4` 로 제한하고 **자르되 감싸지 않는다**(줄 수 고정).
- **표시 전용**: `run_screen` 이 `state` 에서 그대로 읽어 넘긴다. 리듀서·저장·밸런스 무접촉.
- `summary` 를 주지 않으면 **아무것도 그리지 않는다**(기존 호출자·테스트 호환).

### 2) 회복 문구를 사실에 맞춘다 (두 곳)

| 위치 | 이전 | 이후 |
|---|---|---|
| loot 화면 | `HEAL applied → 100/100` (HP 가 최대여도) | `HEAL — already full` |
| 매트릭스 메시지 | `Choose an adjacent route — healed to 100/100` | `… — already at full HP` |

회복이 실제로 일어난 경우의 문구는 **그대로**다(테스트로 고정).

## 결과 (Consequences)

- 엔딩이 **"무엇이었는지"** 를 말한다: 어느 미션, 어떤 HP 로, 얼마를 벌고, 몇 턴 만에.
- 화면이 **상태를 정확히 서술**한다 — 회복 0 을 "적용됨"이라 하지 않는다.
- 밸런스·리듀서 상태·저장 **무변경**(문구와 표시만).

### 불변

- 엔딩 선택 로직(`resolveEnding`)·`EndingContext`·HUD(`ENDING`/`ARC n`) 무변경.
- `renderLootScreen` 의 다른 줄(크레딧·전리품·카드 제안·커밋 패널)과 행 예약 무변경.
- 40열에서 잘림·겹침 없음(테스트 + 실브라우저 확인).

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/renderer/ending.ts` — `EndingSummary` · `renderEndingScreen(..., summary)` · `HEAL — already full`.
- `web/src/renderer/run_screen.ts` — 엔딩 분기에서 `state` 로 요약 구성(mission/hp/credits/turns).
- `web/src/core/state/state_actions_phases.ts` — `continueToMatrix` 메시지가 **회복이 없으면 그렇게 말한다**.
- `web/tests/ending_screen.test.ts` (3) — 미션·수치 표시, **40열 무溢出**, 요약 없으면 아무것도 안 그림.
- `web/tests/loot_screen.test.ts` (+3) — 최대 HP 에서 `HEAL — already full`, 실제 회복 시 기존 문구, 종결 노드 거부 유지.
- **실브라우저**(완주 83스텝): 엔딩에 `Aleph Fragment / HP 100/100 · 4,000cr · 23 turns`,
  로그에 `— already at full HP` 3회. 스크린샷 `docs/design/ending-run-2026-11-04/06-ending.png`.
- vitest **184 files / 4030 tests** · tsc 0 · eslint 0 errors · build PASS.

**Notes**:

- 이 런은 ADR-0268 적용 후라 **Dixie 최대가 26**(이전 92)이었다 — 같은 로그에서 확인.
- 엔딩 요약은 **엔딩 문구를 바꾸지 않는다**. 판정은 그대로, 옆에 사실만 붙는다.

## 열린 질문

- **(a) 보스 구별.** 보스 노드도 같은 ICE 이름("Yakuza Enforcer")이다. 별도 ICE/이름/인트로 1줄이 필요하다(감사 #3).
- **(b) 조우 ICE 다양화.** `encounterRoster` 가 미션의 ICE 하나를 모든 조우에 복제한다(감사 #4, 밸런스 접촉).
- **(c) 이정표 문구.** 구역 진입·보스 접근·마지막 노드에 서사 한 줄(감사 #5b).
- **(d) 요약의 밀도.** 지금은 4개 수치. 죽음 수·획득 카드 수·선택한 엔딩 분기를 더할지는 화면 예산 문제.

## 영향 받는 항목

- `web/src/renderer/ending.ts` · `web/src/renderer/run_screen.ts` ·
  `web/src/core/state/state_actions_phases.ts` · `web/tests/ending_screen.test.ts`(신규) ·
  `web/tests/loot_screen.test.ts` · `web/tests/run_screen.test.ts`

## 관련 결정

- ADR-0251 §5 (화면은 실제 결과를 말한다 — 회복 문구의 근거) · ADR-0252 (런 종료) ·
  ADR-0268 (같은 감사에서 나온 동료 상한) · ADR-0267 (문서 감사 — 검사기가 이 문서들의 수치를 지킨다)

## 변경 이력

- 2026-11-04: 엔딩 완주 감사 → 오너 승인("계속.") → 엔딩 요약·회복 문구 구현 · 실브라우저 확인.
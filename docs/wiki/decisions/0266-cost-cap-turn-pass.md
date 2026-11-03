# ADR-0266: COST 상한에서 턴을 넘긴다 — 전투 정지 제거

**상태**: Accepted
**날짜**: 2026-11-04
**결정자**: 오너 선택 ("D1 턴 패스 + D3 안내 (추천)")
**우선순위**: P0 (블로킹 — 전투가 진행되지 않음)
**관련**: [ADR-0265 — 전투 정지(COST 상한)와 소크 하네스](./0265-combat-freeze-at-the-cost-cap.md) · [ADR-0248 — ALARM/COST 명칭](./0248-alarm-meter-naming.md) · [ADR-0240 — idle pressure](./0240-idle-pressure-and-alarm-loop.md) · [ADR-0251 — 어포던스 진실성 §5](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0238 — 밸런스/입력 결정](./0238-balance-and-input-decision-request.md)

> **막히면 게임이 서던 것을, 막히면 턴이 가게 바꾼다.** 쓸 수 있는 카드가 하나도 없으면
> `ENTER` 가 그 턴을 끝내고 적이 행동한다. COST 는 그대로라 압박은 유지되고, 런은 화면이
> 멈춰서가 아니라 **전투로** 결정된다.

## 컨텍스트 (Context)

ADR-0265 가 결함을 확정하고 측정했다:

- `useProgram` 이 `alarm + cost > 100` 을 거절 → 손패가 줄지 않음 → `applyCombatAction` 이 **조기 반환**
  (적 턴 없음) → 손패는 **비어야만** 리필(`drawHand`) → `GameAction` 에 **턴 넘기기 없음** → **영구 정지**.
- 실측: 상한에서 `Enter`·`Space`·숫자·방향키 **전부 무반응**, 20초 무입력에도 적이 안 때림.
  유일한 출구 `ESC` = **런 상실**.
- 전수조사 159셀: 정지 **16 (10.06%, Wilson 95% 6.29–15.72%)**, 전부 `combat` + COST 98–100 + 쓸 카드 0장,
  전부 비효율 정책(`random` 16/53). 등급 g5 9 · g4 4 · g6 2 · g3 1 → **긴 전투**.

## 결정 (Decision)

**D1 (턴 패스) + D3 (안내)** 를 함께 넣는다.

### D1 — 쓸 카드가 없으면 `ENTER` 가 턴을 넘긴다

`applyCombatAction` 의 `confirm` 분기:

```ts
if (action.type === "confirm" && everyProgramBlocked(state)) {
  const discarding = { ...state, deck: [], discardPile: [...state.discardPile, ...state.deck] };
  const passed = finishPlayerTurn(discarding);   // 적 턴 → 손패 리필 → 승리 판정
  return passed.runPhase === "combat" ? { ...passed, message: "COST capped — turn passed" } : passed;
}
```

- **손패는 버려지고 리필된다** — 실제로 "턴을 썼다"는 뜻이 되도록. (그냥 두면 같은 막힌 손패로 영원히 패스만 반복한다.)
- **COST 는 청구되지 않는다** — 아무 프로그램도 쓰지 않았으므로. 상한은 그대로라 압박이 유지된다.
- **같은 후처리**를 쓴다: `finishPlayerTurn` 으로 `use_program` 의 꼬리(적 턴 → 리필 → 전멸 시 loot)를 공유한다.
  그래서 패스 중에 Dixie/DoT 가 적을 끝내면 **정상적으로 승리**한다.
- **판정 헬퍼는 하나**: `everyProgramBlocked(state)` 가 `programAffordances` 를 그대로 읽는다.
  손패 행의 `BLOCKED`, `useProgram` 의 거절, 이 게이트가 **같은 계산**이라 서로 어긋날 수 없다(ADR-0251 §5).

### D3 — 상한이면 화면이 그렇게 말한다

전투 힌트 밴드의 마지막 줄에 `COST capped: ENTER pass · ESC quit` (34자, 40열에서 프레임 안에 들어감).
문구는 **전부 그린다** — 잘린 안내는 절반의 키를 약속하는 것이라, 폭이 모자라면 아예 그리지 않는다.
`costCapped` 는 `main.ts` 에서 **같은 `everyProgramBlocked`** 로 계산해 넘긴다.

### 왜 D2(자동 턴 진행)가 아니라 D1인가

자동 진행은 "플레이어가 아무것도 하지 않아도 턴이 간다"가 되어 화면이 스스로 움직인다.
D1 은 **플레이어가 넘긴다** — 입력이 있어야 진행되고, 넘기는 동안 적 턴이 온다는 사실이 화면에 있다.

## 결과 (Consequences)

- **정지가 사라진다**: 상한에서 `ENTER` → 적 턴 → 새 손패. 화면이 답을 멈추지 않는다.
- **런은 전투로 끝난다**: 패스 중에도 적이 때리고 Dixie/DoT 가 적을 깎는다. 1 HP 러너는 패스하다 죽는다(테스트 고정).
  이전에는 "멈춘 채로 포기"였다.
- **COST 압박은 그대로**: 패스는 COST 를 청구하지도, 깎지도 않는다. 상한은 여전히 상한이다.
- **밸런스 기준선은 byte-identical** — 하지만 **주의**: `balance_sim` 은 `deck[0]` 만 `use_program` 하고
  **패스를 모델링하지 않는다**. 그래서 곡선이 변하지 않는 것은 "영향이 없다"가 아니라 **"심이 새 규칙을 못 본다"** 이다.
  심이 상한에서 헛바퀴를 도는 비율은 실측 0.0%(ADR-0265)라 기준선 오염은 없지만, D1 의 밸런스 효과는
  **심으로 측정되지 않았다**(열린 질문 (a)).

### 불변

- `programAffordances`/`useProgram` 의 거절 규칙, `COST_LIMIT`, `drawHand` 의 RNG 0, 손패 순서 보존 — 무변경.
- `jack_out`(ESC/q) 은 그대로 런 상실. 패스는 **포기가 아니다**.
- 스키마·저장 무변경.

## Implementation Status (2026-11-04)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/program_affordance.ts` — `everyProgramBlocked` (손패 행·거절과 **같은** affordances).
- `web/src/core/combat/state_actions_combat.ts` — `confirm` 패스 분기 + `finishPlayerTurn` 추출(`use_program` 과 공유).
- `web/src/renderer/combat_hints.ts` — `COST_CAPPED_LINE`(34자) · `costCapped` · 폭 가드.
- `web/src/main.ts` — `costCapped` 를 `everyProgramBlocked` 로 계산해 전달.
- `web/tests/cost_cap_pass.test.ts` (5) — 상한 판정, 패스가 실제 턴을 진행(새 프레임·손패 리필·COST 불변),
  **쓸 카드가 있으면 아무 일도 없음**(오작동 방지), 패스 중 사망.
- `web/tests/combat_hints.test.ts` (+2) — 80×50·40×60 에서 문구가 **온전히** 그려지고 붉은색, 요청 없으면 없음.
- **실브라우저**(preview 5195, 독립 headless): 상한에서 `ENTER` → `hp 100→87`, `msg "COST capped — turn passed"`,
  손패 5장 리필. 40×60 에서 안내 줄이 프레임 안에 표시됨(스크린샷).
- vitest **182 files / 4021 tests** · tsc 0 · eslint 0 errors · build PASS.
- 밸런스 재측정: opening `100.0/100.0/81.4/42.6/36.6/0.0`, PPL `100.0/100.0/99.3/84.1/44.4/27.3` — **byte-identical**
  (위 주의 참조).
- **같은 159셀 재조사(수정 후)**: **완주 159 / 정지 0 / `no_end_in_steps` 0** — 정지율 **0%**,
  Wilson 95% **[0, 2.36%]**. `COST 상한 도달`은 여전히 **13런**에서 일어나고 **13런 전부 완주**했다
  (수정 전에는 같은 조건이 정지였다). 압박은 남고 정지만 사라졌다는 뜻이다.
  원본: `docs/design/soak-playthrough-2026-11-03/report-after.json`.

**Notes**:

- 패스 메시지는 진행 중에만 덮어쓴다(사망 시 `FLATLINE` 을 가리지 않는다).
- 상한에서 손패가 리필되므로 화면은 **같은 5장**을 다시 보여준다(순서 보존, 셔플 없음 — RNG 0 유지).
  그래서 "왜 또 같은 카드냐"는 혼동이 있을 수 있다(열린 질문 (b)).

## 열린 질문

- **(a) 심이 패스를 모델링해야 한다.** `balance_sim` 이 상한에서 `deck[0]` 을 계속 시도하며 헛바퀴를 돈다.
  D1 이후 실제 게임은 패스로 턴이 가므로, 심도 패스를 넣어야 승률이 새 규칙을 반영한다. 기준선 파일이 바뀌므로 별도 슬라이스.
- **(b) 리필된 같은 손패.** 순서 보존(셔플 없음)이라 상한에서는 늘 같은 5장이 보인다. 표시상의 혼동 여지.
- **(c) 패스에 최소 비용을 둘지.** 지금은 무료다(아무것도 쓰지 않았으므로). 상한이 사실상 "죽을 때까지 맞기"가 된다.

## 영향 받는 항목

- `web/src/core/combat/program_affordance.ts` · `state_actions_combat.ts` · `web/src/renderer/combat_hints.ts` · `web/src/main.ts`
- `web/tests/cost_cap_pass.test.ts` (신규) · `web/tests/combat_hints.test.ts` · `web/tests/onboarding.test.ts` (소스 스캔 갱신)

## 관련 결정

- ADR-0265 (결함 확정 + 측정) · ADR-0251 §5 (화면은 실제 결과를 말한다 — 같은 헬퍼를 쓰는 이유) ·
  ADR-0240/0242 (COST 압박의 설계, 무변경) · ADR-0238 (밸런스/입력 결정)

## 변경 이력

- 2026-11-04: 오너 선택(D1+D3) → 구현 · 테스트 · 실브라우저 확인 · 159셀 재조사.
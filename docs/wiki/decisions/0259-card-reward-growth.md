# ADR-0259: 전투 승리 후 카드 1장 — 런의 성장

**상태**: Accepted
**날짜**: 2026-11-03
**결정자**: 오너 승인 (2026-11-03 "모두 추천대로 해줘. 성장하는 재미는 중요해")
**우선순위**: P1 (The Run — 런 안의 성장, The Build — 메커닉)
**관련**: [ADR-0260 — 시작 덱](./0260-starting-deck-is-chosen.md) · [ADR-0255 — 카드가 이름대로 동작한다](./0255-card-effects-are-real.md) · [ADR-0252 — 런 종료·저장 시점](./0252-run-end-and-save-timing.md) · [ADR-0243 — 숫자키 1회 = 카드 1장 실행](./0243-digit-key-repeat-policy.md) · [ADR-0251 — 어포던스 진실성 §규칙 5](./0251-truthful-program-affordance-and-combat-integrity-rules.md)

> **이 ADR은 런에 성장 경로를 하나 추가한다.** 리듀서가 이미 가진 것(전리품 화면·손패 재활용·결정적 RNG)만
> 사용하며, `Math.random` 을 새로 소비하지 않는다 — 밸런스 하네스는 byte-identical 로 남는다.

## 컨텍스트 (Context)

**게임에 성장이 없었다.** 시작 5장을 받으면 그것이 전부였다:

- **상점은 껍데기** — `web/src/renderer/shop.ts` 의 `renderShopScreen(_state)` 는 인자를 쓰지 않는다
  (`_state`). `info_market.ts` 는 가격 계산을 갖고 있지만 상점 UI 에 배선되지 않았다.
- **전리품은 재료만** — `rollLoot` 는 `ice_shard`/`data_fragment` 같은 재료를 준다. 프로그램이 아니다.
- **덱은 순환할 뿐** — `drawHand` 는 버린 더미를 재활용한다. 새 카드가 들어오지 않는다.

그래서 카탈로그 30장 중 **시작 5장 외 25장은 플레이어에게 절대 오지 않는 죽은 콘텐츠**였다.

동시에 ADR-0260 이 시작 덱을 의도적으로 고르게 되면서, 시작에서 빠진 카드(예: `cloak`)가
**영영 볼 수 없는 카드**가 될 위험이 생겼다.

## 고려한 옵션

### Option 1: 상점에서 산다
크레딧으로 카드를 구매. `info_market.ts` 의 평판 가격 계산을 재사용할 수 있다. 그러나
상점 화면 구현 + 진입 경로(허브/노드) + 가격 밸런스가 필요하고, "파밍 후 구매"는 런 안
성장 리듬이 아니라 **경제 최적화**로 흐른다. **보류** (재료 소비처로 더 적합).

### Option 2: 전투 승리 보상으로 1장 선택 (선택)
고전 로그라이크의 카드 보상. 이미 있는 loot 화면에 얹으므로 새 화면·새 진입 경로가 없고,
전투마다 성장 기회가 온다 — 런 안 성장 리듬에 맞는다.

### Option 3: 레벨업/노드 이벤트로 지급
새 진행 축이 필요하다. 큰 설계 작업.

**결정: Option 2.**

## 사용자 결정 (Decision)

[x] **Option 2** — 비종결 노드 승리 시 **1 of 3 카드 보상**

### 설계 결정

**1. 제시 카드는 런의 순수 함수다 (저장 상태 없음).**
`offeredCardIds(state)` = mission seed + turn + node 로 결정되는 3장. 그래서
- 저장된 loot 화면을 다시 열어도 **같은 3장**이 나온다 → 재시도 이득이 없다(저장 무결성).
- `Math.random` 을 **소비하지 않는다** → 밸런스 하네스가 변하지 않는다(규칙 3).
- 새 영속 상태가 없다 → 세이브 스키마 무변경.

**2. 이미 가진 카드는 제시하지 않는다.**
`deck ∪ drawPile ∪ discardPile` 을 제외하고 뽑는다. 중복 획득이 없다.

**3. 가져가면 draw pile 에 들어간다.**
손패 순환이 일어날 때 등장한다. 즉시 손에 들어오지 않으므로 그 턴의 전투를 흔들지 않는다.

**4. 가져가면 loot 가 끝난다 (ENGROSS 아님).**
`1`-`3` 은 카드를 획득하고 **동시에** 이동한다. `ENTER` 는 건너뛰고 이동한다. "획득"과 "이동"이
분리되지 않으므로, 재시도·중복 획득 상태를 저장할 필요가 없다(설계 1과 같은 이유).

**5. 종결 노드는 보상을 주지 않는다.**
`isTerminalNode` 면 런이 끝난다 — 다음 전투가 없으므로 카드도 의미가 없다. 화면도 이를 말한다.

**6. 손패 숫자키와 충돌하지 않는다.**
loot 화면에서 숫자키는 보상 선택이다. `resolveProgramSelection` 을 **combat 전용**으로 제한해,
손패에 카드가 남은 채 이겨도 숫자키가 `use_program` 으로 변환되지 않게 했다(발견·수정한 결함).

**7. 터치에 같은 선택을 준다.**
loot 중 loot 화면의 카드 3장이 **터치 버튼**으로 뜬다(`rewardAffordances` + `handleRewardButton`).
키보드·터치·게임패드가 같은 사실을 본다.

## 결과 (Consequences)

### 바뀐 것

| 파일 | 역할 |
|---|---|
| `web/src/core/state/card_reward.ts` (신규) | `offeredCardIds` (순수·결정적) · `RewardSource` |
| `web/src/core/state/state_actions_phases.ts` | `applyLootAction` 재구성 — `applyTerminalLoot` · `takeCardReward` · `continueToMatrix` |
| `web/src/core/state/state.ts` | `resolveProgramSelection` 을 combat 전용으로 제한 |
| `web/src/core/combat/program_affordance.ts` | `formatRewardOption` · `rewardAffordances` |
| `web/src/renderer/ending.ts` | `renderLootScreen` 에 `offers` |
| `web/src/renderer/run_screen.ts` | loot 화면에 보상 전달 |
| `web/src/main.ts` | `handleRewardButton` + loot 터치 행 |

### 화면

```text
DATA SALVAGE
HP 61/100
+4,075 credits
NEW PROGRAM
1 PAYLOAD
2 KRAKEN
3 ECHO
HEAL applied → 79/100
1-3: take a card | ENTER: skip
```

loot HUD: `LOOT / 1-3: card`. 종결 노드: `LOOT / ENTER: run ends`, 보상 줄 없음.

### 불변

- **밸런스 byte-identical** — opening `100.0 / 100.0 / 81.4 / 42.6 / 36.6 / 0.0`(ADR-0260),
  PPL `100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3`. 새 `Math.random` 소비 0.
- 세이브 스키마 무변경(새 영속 필드 없음).
- ADR-0243(숫자키 = 카드 1장 실행)은 combat 에서 불변 — loot 에서만 숫자키가 보상 선택.
- ADR-0252(저장 시점)·ADR-0251(규칙 5)·ADR-0255(카드 효과) 무변경.

## Implementation Status (2026-11-03)

**Status**: ✅ Implemented

**Evidence**:

- `web/tests/card_reward.test.ts` (신규, 10건) — 3장·중복 없음·순수성·노드 의존, 획득 시
  drawPile+inventory 반영·정확히 1장, ENTER 는 건너뜀, 범위 밖 슬롯 거부, 종결 노드는 보상 없음,
  터치 행 3개.
- `web/tests/run_screen.test.ts` — loot 화면 보상 렌더 + 종결 노드는 보상 없음.
- `web/tests/state.test.ts` — `resolveProgramSelection` 이 combat 전용.
- 3개 레이아웃 캡처 + 폭 검사(그리드 0 · HUD 0) —
  [card-reward-2026-11-03](../../design/card-reward-2026-11-03/README.md).
- 실플레이(ego-lite Chromium) — 승리 → `1` → `draw: ["payload"]`, `"Took Payload — added to your deck"`.
- vitest **180 files / 3978 tests passed** · typecheck 0 · eslint 0 errors · build PASS.

**Notes**:

- **밸런스 하네스는 loot 를 걷지 않는다** — 보상의 힘을 재지 못한다. 실제 런은 하네스보다 강해진다.
  하네스에 보상 단계를 넣는 것은 별도 작업(seed 고정 시뮬레이션 필요).
- 제시 카드는 tier 가중치가 없다 — 지금은 카탈로그 전체에서 균등하게 뽑는다. 초반에 강한 카드가
  나올 수 있다(아래 열린 질문).

## 열린 질문

- **(a) tier 가중치.** 초반에는 낮은 tier 를 더 자주 제시할 것인가(진행감), 균등하게 둘 것인가.
- **(b) 하네스 모델링.** `balance_sim` 에 보상 단계를 넣어 성장 후 전력을 측정할 것인가.
- **(c) 상점(Option 1).** 재료 소비처로 상점을 살릴 것인가 — 보상과 역할이 다르다(경제 vs 성장).
- **(d) 25장의 효과.** 이제 획득 가능해졌으므로 효과 배선의 가치가 생겼다(ADR-0255 (b)).

## 영향 받는 항목

- `web/src/core/state/card_reward.ts` (신규) · `state_actions_phases.ts` · `state.ts`
- `web/src/core/combat/program_affordance.ts` · `web/src/renderer/ending.ts` · `run_screen.ts` · `web/src/main.ts`
- `web/tests/card_reward.test.ts` (신규) · `run_screen.test.ts` · `state.test.ts` · `loot_input_contract.test.ts`

## 관련 결정

- ADR-0260 (시작 덱 — 빠진 카드를 얻을 수 있게 함) · ADR-0255 (효과 — 보상 카드의 가치) ·
  ADR-0252 (저장 시점) · ADR-0251 (규칙 5) · ADR-0243 (숫자키)

## 변경 이력

- 2026-11-03: Draft 작성
- 2026-11-03: Accepted — 오너 승인("성장하는 재미는 중요해"). 구현 완료.

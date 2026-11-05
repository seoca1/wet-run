# ADR-0279: 런이 번 돈을 런이 말한다 — 미션 보상 1회 지급과 엔딩 지갑

**상태**: Accepted
**날짜**: 2026-11-05
**결정자**: 오너 ("응.")
**우선순위**: P1 (경제 · 엔딩 분기)
**관련**: [ADR-0278 — 런이 사실대로 읽힌다](./0278-the-run-reads-true.md) · [ADR-0277 — 엔딩 크레딧 표시](./0277-exploit-ignores-half-the-armor.md) · [ADR-0271 — 평범한 런의 엔딩을 선언한다](./0271-declare-the-plain-endings.md) · [ADR-0270 — 엔딩 선택을 우연에 맡기지 않는다](./0270-no-novel-prose.md) · [ADR-0130 — `rewards.credits` 권위](./0130-balance-audit-and-ppl-sync.md)

> ADR-0278 열린 질문 (a)·(b) = ADR-0277 열린 질문 (c) 를 닫는다. 둘은 **같은 뿌리**다 —
> 미션 보상이 **교전마다** 지급되고, 엔딩 리졸버는 **전투가 채우지 않는 지갑**을 읽었다.
> 결과적으로 53개 미션 중 2개에서만 도달 가능한 엔딩 분기(`control`)가 있었고,
> 미션 선택 화면이 약속한 크레딧은 두 번 지급됐다.

## 컨텍스트 (Context)

ADR-0277 은 엔딩 **요약**이 `inventory.credits`(미션 기본 보상)를 읽어 2,300cr 런이 500cr 로
표시되는 버그를 고쳤다(→ `player.credits`). 그때 "같은 뿌리의 남은 문제"로 두 가지를 남겼다.

1. **미션 보상이 교전마다 지급된다.** `mission.rewards.credits + node.reward.credits` 가
   **모든 교전 승리**에 더해진다. `First Jack` 의 미션 보상은 500 인데 두 교전에서 500 이 두 번
   들어갔다(625 = 500 + 75 + 50, 1675 = 500 + 175 + 1000). 미션 선택 화면은
   `First Jack  [T1 | 500cr]` 이라고 **500 을 약속**한다. 2026-11-02 트레이스에도 같은 모양
   (`cr=4500` → `+6100`).
2. **엔딩 리졸버가 전투가 채우지 않는 지갑을 읽는다.** `control` 분기는
   `inventory.credits > 5000` 을 보는데, 그 지갑은 미션 기본 보상으로 시작해 **전투 보상으로 늘지
   않는다**(전투 보상은 `player.credits`). 그래서 53개 미션 중 기본 보상이 5,000 을 넘는
   **2개**에서만 도달 가능했다. 즉 arc 1–4 의 `control` 엔딩(`arc1_cowboy_up` · `arc2_data_thief` ·
   `arc3_double_agent` · `arc4_new_order`)은 **사실상 죽은 분기**였다.

두 지갑의 정의는 다음과 같다(코드 기준).

| 지갑 | 시작값 | 전투 보상 | 쓰임 |
|---|---|---|---|
| `player.credits` | 0 | **늘어남** | HUD `Credits` · 저장 · 엔딩 요약(ADR-0277) |
| `inventory.credits` | 미션 기본 보상 | 불변 | crafting 지갑 (`purchaseItem` 은 호출자 없음) |

## 결정 (Decision)

### 1) 미션 보상은 **미션이 끝나는 교전**에서 한 번만 지급한다

`resolveVictory` 가 `isTerminalNode(state)` 를 보고 미션 보상을 포함할지를 정한다
(`combat/victory.ts`).

- 미션이 끝나지 않는 교전 승리: **노드 보상** + 업적.
- 미션이 끝나는 교전 승리(보스, 또는 막다른 노드): **노드 보상 + 미션 기본 보상** + 업적.
  메시지에 `(mission complete)` 를 붙여 그 지급이 무엇인지 말한다.

미션 보상을 **터미널 전투에 얹은** 이유는 표시 정합이다. 전리품 화면은 `state.message` 의
`+N credits` 를 파싱해 그린다. 엔딩 확정 단계에서 따로 지급하면 전리품 화면은 노드 보상만 보여주고
엔딩 요약은 더 큰 수를 보여줘 **또 하나의 불일치**가 생긴다. 한 화면에서 한 번 말한다.

`inventory.credits` 는 그대로 미션 기본 보상으로 시작한다(기존 동작, crafting 지갑).

### 2) 엔딩 리졸버는 런이 번 돈을 읽는다

`state_actions_phases.ts` 의 `EndingContext.credits` 를 `state.player.credits` 로 바꾼다.

근거는 **화면과 판정의 일치**다. 엔딩 화면은 이미 `player.credits` 를 인쇄한다(ADR-0277).
리졸버가 다른 수를 보면 "6,000cr 을 보여주면서 생계형 엔딩" 같은 모순이 남는다 —
ADR-0269("엔딩은 런을 돌아본다")와 ADR-0270("엔딩 선택을 우연에 맡기지 않는다")이 세운 규칙의 연장이다.

## 결과 (Consequences)

### 바뀐 것 (측정)

엔드투엔드 결정론 측정 도구를 새로 만들었다 — `npm run endings`
(`web/scripts/ending_distribution.ts`). 소크는 실제 벽시계·비시드 `Math.random` 으로 돌아
회차마다 분포가 흔들리므로, 같은 정책(가장 비싼 감당 가능 카드, BREACH, 첫 보상)을 시드 고정
리듀서로 돌려 **분포를 비교 가능하게** 만들었다.

53개 미션, seed `20261105`, 정책 `expensive`, 리졸버 지갑만 교체:

| 엔딩 | `inventory` (이전) | `player` (이후) |
|---|---:|---:|
| `arc1_wage_slave` (status_quo) | 20 | 20 |
| `arc2_status_quo` | 14 | 14 |
| `arc3_neutrality` (status_quo) | 8 | 7 |
| `arc3_double_agent` (**control**) | 0 | **1** |
| `arc4_status_quo` | 7 | 0 |
| `arc4_new_order` (**control**) | 0 | **7** |
| `arc5_control` (**control**) | 2 | 4 |
| `arc5_unknown` (status_quo) | 2 | 0 |

- **`control` 2 → 12 런** (arc 3·4·5). arc 1·2 는 여전히 도달하지 않는다 — 기본 보상이 낮아
  런 총액이 5,000 에 못 미친다. 즉 분기는 **등급·arc 규모에 맞게** 살아났고, 아무 런이나 받지는 않는다.
- arc 4 의 7런이 `status_quo` → `control` 로 이동했다. arc 4 의 `control` 엔딩은
  `arc4_new_order` 로 **이미 카탈로그에 있었다**(ADR-0271 계열) — 죽어 있던 분기가 열린 것이다.
- 5개 arc **모두** `control` 엔딩을 가진다(테스트로 고정).

### 바뀐 것 (보상)

두 교전을 모두 이긴 `First Jack` 런에서 **미션 보상이 두 번 들어가던 것이 한 번**이 된다 —
사라지는 중복은 정확히 **500cr**(미션 기본 보상 1회분)이다. 미션 선택 화면이 약속한 500 이 한 번만 들어간다.

런 총액 자체는 업적에 따라 달라진다(같은 런이 `combo_master` 500cr 를 켜면 총액은 2,300 으로 보인다).
결정론적 고정은 테스트가 한다 — `adr0279_mission_reward.test.ts` 는 800cr 미션 2교전 완주를
**1,975cr**(노드 50+75, 미션 800×1, `first_blood` 50, `boss_slayer` 1,000)로 고정한다.
전리품 화면도 이제 그 지급을 말한다: 1교전 `+125 credits`(노드 75 + `first_blood` 50),
보스 `+2175 credits (mission complete)`(노드 175 + 미션 500 + 업적 1,000/500).

### 불변 (측정)

- **밸런스 byte-identical** — `npm run balance` 가 ADR-0277 기준선과 완전히 동일
  (`100.0 / 100.0 / 89.1 / 47.4 / 40.7 / 0.0`). 하네스는 승리 지점에서 멈추므로 경제 변화가
  승률에 닿지 않는다.
- **RNG 소비 0** · **저장 스키마 무변경**.

## Implementation Status (2026-11-05)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/victory.ts` — `resolveVictory` 가 `isTerminalNode` 로 미션 보상을 가른다.
- `web/src/core/state/state_actions_phases.ts` — `EndingContext.credits = state.player.credits`.
- `web/scripts/ending_distribution.ts` + `npm run endings` — 결정론 엔딩 분포 측정.
- `web/tests/adr0279_mission_reward.test.ts` (7) — 1회 지급 · 리졸버 지갑 · 5 arc 모두 `control` 보유.
- 실측: 53 미션 분포 `docs/design/jockey-identity-2026-11-04/ending-distribution.txt`.
- vitest **191 files / 4084 tests passed** · typecheck 0 · build PASS.

**Notes**:

- `inventory.credits` 는 계속 미션 기본 보상으로 시작한다(기존 동작). 두 지갑의 관계를 하나로
  합치는 것은 별도 결정 — `purchaseItem` 에 호출자가 없어 지금은 쓰이지 않는다.
- **Manus 독립 리뷰 (2026-11-05):** `docs/design/adr-review-2026-11-05/manus-review.md` (task `LXHmpxarQHm38S4FT5XXPX`, agent `lite`) — verdict **approve-with-caveats**. Findings: (1) high — 최종 분포 측정 분리 → 위 재확인으로 해소, (2) medium — 터미널 승리 멱등성 미입증 → `adr0279_mission_reward.test.ts` 에 "mission complete" 단일 언급 테스트 추가, (3) medium — `isTerminalNode` 경계 불명확 → `run_end.ts` 주석 보강, (4) medium — ADR-0130 `rewards.credits` 권위 관계 미해소 (후속), (5) low — `control` 카탈로그 존재 vs 도달성 표현 혼재 (후속). 오픈 질문 (a) 부분 가능, (b) 현재 증거로 결정 불가, (c) 답할 수 없음.
- **최종 분포 재확인 (2026-11-05, Manus 리뷰 high finding 대응):** `resolveVictory` 1회 지급 + `player.credits`
  리졸버 **두 변경이 모두 적용된** 최종 코드에서 `npm run endings` 재실행 → 위 표의 `player` 열과 동일
  (arc1_wage_slave 20 · arc2_status_quo 14 · arc3_neutrality 7 · arc3_double_agent 1 · arc4_new_order 7 ·
  arc5_control 4, mean earned 3750, 12/53 런이 5,000 초과). 즉 표는 최종 상태의 분포이며, 리졸버 지갑만
  교체한 비교가 아니다.
- 소크 하네스는 이제 `ending` 을 리포트에 남긴다(측정 공백 보완).

## 열린 질문

- **(a) `hp > 75%` 조건.** ADR-0278 (c) 가 그대로다. 전리품 회복이 15% 이므로 엔딩 시점 HP 는
  가변인데, `control` 이 요구하는 이 조건이 실제로 얼마나 자주 참인지는 미측정.
  `npm run endings` 가 HP 를 함께 남기므로 측정은 가능하다.
- **(b) 두 지갑의 통합.** `player.credits`(런 수입)와 `inventory.credits`(crafting)를 하나로
  합칠지. crafting 상점이 배선되면 반드시 정해야 한다.
- **(c) 미션 보상의 노드 분배.** 지금은 노드 보상이 `50 + idx * 25` 로 **경로 위치**에 비례한다.
  미션 보상이 말미 1회가 된 만큼 노드 보상 곡선도 다시 볼 수 있다.

## 변경 이력

- 2026-11-05: Draft → Accepted (오너 "응."). 미션 보상 1회 지급 + 엔딩 리졸버가 `player.credits` 를 읽음.

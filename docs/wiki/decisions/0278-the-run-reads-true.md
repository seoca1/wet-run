# ADR-0278: 런이 사실대로 읽힌다 — 이야기 검증이 찾은 결함 묶음

**상태**: Accepted
**날짜**: 2026-11-05
**결정자**: 오너 ("응 결함 수정해줘. 그리고 더 찾아봐줘.")
**우선순위**: P1 (게임플레이 · 성장) · P1 (서사 정합) · P2 (표시)
**관련**: [ADR-0277 — `exploit` 과 서사 검증](./0277-exploit-ignores-half-the-armor.md) · [ADR-0247 — SCAN 의 비용](./0247-encounter-intel-costs-a-card.md) · [ADR-0258 — 결정타 COST 면제](./0258-killing-blow-cost-rule-notice.md) · [ADR-0259 — 카드 보상이 성장이다](./0259-card-reward-growth.md) · [ADR-0261 — 성장은 사건으로 보인다](./0261-growth-moment-is-shown.md) · [ADR-0269 — 엔딩은 런을 돌아본다](./0269-the-ending-looks-back.md)

> ADR-0277 의 서사 검증(`docs/design/jockey-identity-2026-11-04/story-narration.md`)이 남긴 결함 목록을
> 닫는다. 그 검증은 **런을 이야기로 옮겨 읽는** 방식이었고, 그 방식이 리듀서 테스트가 못 잡는 것을
> 잡았다 — **화면이 말하는 것과 게임이 하는 것이 다른** 종류다.
>
> 이 ADR 은 그 목록 8개 중 6개를 고치고 3개를 **오탐으로 정정**하며, 재측정에서 **2개를 더** 찾아 고친다.
> 남은 1개(미션 보상 중복 지급)는 **경제 결정**이라 오너에게 넘긴다.

## 컨텍스트 (Context)

ADR-0277 은 `exploit` 을 배선하고 큐레이션 덱을 바꿨다. 밸런스 표는 승률을 말하지만
**런이 읽히는지**는 말하지 못한다. 그래서 실브라우저에서 실제 키로 한 런을 끝까지 돌리고,
게임이 인쇄한 모든 줄을 `story-trace.txt` 에 남겼다(`npm run story`, ADR-0265 의 소크와 같은 규칙 —
`wetrun.state` 를 쓰지 않는다).

그 트레이스를 서사로 옮겨 읽자 결함 8개가 나왔다. 이 ADR 은 그것들을 다룬다.

**측정 방법의 결함도 함께 드러났다.** 첫 트레이스는 `state.message`(가장 최신 한 줄)만 캡처했다.
그래서 전투 로그의 나머지 줄이 사라졌고, "동료가 로그 첫 줄을 가져간다"는 **오탐**이 나왔다.
캡처를 `combatLog` 전체로 고치는 것이 이 배치의 0번 작업이다 — **계기를 먼저 고친다**.

## 결정 (Decision)

### 0) 트레이스가 전투 로그를 남긴다 (계기 수정)

`e2e/story_trace.spec.ts` 가 `combatLog` 를 읽어, 중복 없이 **오래된 순**으로 트레이스에 적는다.
`message` 는 최신 줄일 뿐이므로 그것만 읽는 트레이스는 **무손실이 아니다.**

### 1) 손패는 전리품 화면이 닫힐 때 채워진다

`core/combat/hand.ts` 의 `refillHand` 하나를 두 곳이 쓴다.

- 전투 **안**에서 손패가 비면: 드로우 → 버림 순으로 리사이클(기존 `drawHand` 동작).
- 전투 **사이**(전리품 화면을 닫을 때): `player.handSize` 까지 채운다.

리필 지점을 **BREACH 가 아니라 전리품**에 둔 것이 핵심이다. BREACH 에 두면 SCAN 으로 쓴 카드가
그 전투가 시작될 때 되살아나 **ADR-0247 의 비용이 사라진다**. 전리품에 두면 SCAN 의 비용은
그 전투 동안 유지되고, 다음 교전은 온전한 손패로 시작한다.

### 2) 보상 카드는 드로우 파일 **맨 위**에 얹힌다

`drawPile: [card, ...state.drawPile]`. 짧은 런은 손패가 비기 전에 끝나므로, 파일 **끝**에 넣으면
받은 카드가 **한 번도 안 나온다**. 맨 위에 얹으면 §1 의 리필이 그 카드를 그대로 집는다.
(ADR-0259 의 "성장은 유일한 성장 경로" 를 실제로 성립시킨다.)

### 3) 교전 상대는 노드가 정한다 — 카탈로그에서 해석한다

`encounterRoster` 가 `state.ice` 를 **복제**하고 `id`/`hp` 만 바꾸고 있었다. 그래서 모든 교전이
미션의 **기준 ICE**(이름·방어도·기술)를 입은 채 id 만 다른 존재였다 — 보스 방이 **35 HP "Wisp"** 로
싸워졌다. 이제 노드의 `iceIds` 를 **ICE 카탈로그**에서 해석한다. 노드가 상대를 지명하고,
카탈로그가 그 지명의 의미다. 카탈로그에 없는 id 는 기존 `activeIce` 로 폴백해 손으로 만든
상태(테스트·구 세이브)가 계속 플레이 가능하다.

### 4) 화면은 로스터가 지명한 이름을 말한다

`state.ice` 는 런의 **기준 ICE**이지 지금 앞에 있는 상대가 아니다. 그래서 보스 방이
`Combat vs ICE — Wisp`, 승리가 `ICE — Wisp defeated!` 라고 말했다(실제 상대는 wintermute,
armor 8·tier 4). `core/combat/roster.ts` 의 `activeIceOf` / `defeatedIceName` 이 **로스터**에서
읽는다. §3 과 **같은 뿌리**다.

### 5) 한 미션의 ICE 방은 서로 다른 타입을 받는다

`dungeonToMatrix` 의 `iceIdForRoom` 이 ICE 방마다 등급 밴드의 **다음 슬롯**을 받는다
(`seed + iceOrdinal * 7`). 같은 미션의 두 교전이 같은 적이면 미션이 **한 싸움의 반복**으로 읽힌다.
`seed` 가 `undefined` 면 밴드 슬롯 0 을 유지해 구 호출부는 불변이다.

### 6) 전투의 보상은 **킬이 일어난 지점**에서 적립된다

두 승리 경로가 서로 다른 보상을 줬다.

| 경로 | 전리품 | 업적 | 진영 점수 |
|---|---|---|---|
| `useProgram` — 카드가 막타 | 있음 | 있음 | 있음 |
| `finishPlayerTurn` — Dixie/DoT 가 막타 | **없음** | **없음** | **없음** |

플레이어는 어느 경로가 발동할지 고를 수 없고, 동료에게 마무리를 맡기는 것은 자연스러운 플레이다.
보스의 전리품(`combat_module x2` 등)과 `boss_slayer`(1,000cr)가 **카드가 막타를 친 런에만**
존재했다. 이제 `core/combat/victory.ts` 의 `creditKills` 가 킬이 일어난 전이마다 적립하고,
`resolveVictory` 가 업적·크레딧·메시지·로그·VFX 를 한 곳에서 만든다.

남는 차이는 **하나뿐**이다 — ADR-0258 의 `(no COST)` 는 **막타를 친 카드**의 것이므로,
동료 킬은 그 문구를 주장하지 않는다(카드가 막타를 안 쳤으니까).

### 7) 문구 (밸런스 무관)

- CASE 태그라인: `The deck is already warm.` → `New hands. Old reflexes. The deck remembers.`
  (arc 1 인트로가 "The deck is cold in your hands." 라고 말한다.)
- 전리품 표기: `${item}x${qty}` → `${item} x${qty}`.

## 결과 (Consequences)

### 바뀐 것

- **성장이 성립한다.** 받은 카드가 다음 교전 첫 손패에 들어온다. 짧은 런에서도 실제로 나온다.
- **교전마다 조건이 같다.** 손패가 항상 `handSize` 로 시작한다.
- **보스가 보스다.** 보스 방의 상대는 `wintermute`(260 HP, armor 8, tier 4, g1 에서는 상한 75).
- **보상이 경로에 무관하다.** 막타를 누가 쳤든 같은 전리품·업적·진영 점수.
- **한 미션 안에서 적이 다르다.**

### 불변 (측정으로 확인)

- **밸런스 byte-identical** — `npm run balance` 산출이 ADR-0277 기준선과 **완전히 동일**
  (`100.0 / 100.0 / 89.1 / 47.4 / 40.7 / 0.0`). 하네스는 승리 지점에서 멈추므로 경제·손패 변화가
  승률에 닿지 않는다.
- **RNG 소비 0.** `refillHand` 와 `victory.ts` 는 `Math.random` 을 쓰지 않는다(dungeon 밴드 회전은
  `seed` 결정론). 리듀서 순수성 유지.
- **저장 스키마 무변경.** 새 필드 없음.

## Implementation Status (2026-11-05)

**Status**: ✅ Implemented (미션 보상 중복은 ❌ Not started — 오너 결정 대기)

**Evidence**:

- `web/src/core/combat/hand.ts` — `refillHand` (신규).
- `web/src/core/combat/roster.ts` — `activeIceOf` · `defeatedIceName` (신규).
- `web/src/core/combat/victory.ts` — `creditKills` · `killedBetween` · `resolveVictory` (신규).
- `web/src/core/state/encounter_verbs.ts` — `encounterRoster` 카탈로그 해석.
- `web/src/core/state/state_actions_phases.ts` — 전리품에서 리필, 보상 카드 맨 위, 상대 이름.
- `web/src/core/combat/state_actions_combat.ts` · `state_actions_programs.ts` — 두 승리 경로가 `victory.ts` 를 공유.
- `web/src/core/dungeon/dungeon.ts` — `iceIdForRoom` (방별 밴드 슬롯).
- `web/tests/adr0278_playthrough_fixes.test.ts` (10) · `adr0278_victory_payout.test.ts` (5) — 통과.
- 실플레이: `docs/design/jockey-identity-2026-11-04/story-trace.txt` (arc 1 "First Jack", 16 스텝,
  보스 `Combat vs ICE — Wintermute` → `+1675 credits Loot: combat_module x2, construct_shard x1, data_fragment x3`,
  엔딩 `arc1_wage_slave` 까지 무정지).
- 소크: `SOAK_RUNS=15 npm run soak` — **15/15 completed, frozen 0** (g1–g5 전 등급, g5 6런 포함).
- vitest **190 files / 4077 tests passed** · typecheck 0 · eslint 0 errors(기존 `keyboard.ts` 경고 1) · build PASS.

**Notes**:

- 결함 목록 8개 중 **5(구역 이름)·7(동료가 첫 줄)·8(만피 회복)** 은 **오탐**이었다.
  정정과 근거는 `story-narration.md` §정정 및 재측정.
- §3 은 ADR-0277 검증에서 이미 고쳤던 것을 이 ADR 이 기록으로 편입한 것이다.

## 열린 질문

- **(a) 미션 기본 보상의 중복 지급.** ~~`mission.rewards.credits + node.reward.credits` 가 **모든 교전
  승리**에 더해진다.~~ **→ [ADR-0279](./0279-the-run-states-its-earnings.md) 에서 결정·구현**
  (미션 보상은 미션이 끝나는 교전에서 1회, 엔딩 리졸버는 `player.credits`).
- **(b) 엔딩 분포.** ~~`control` 분기가 `inventory.credits > 5000` 을 보는데 그 지갑은 전투 보상으로
  늘지 않는다.~~ **→ ADR-0279 에서 결정** (`control` 2 → 12 런).
- **(c) 엔딩 시점 HP.** ADR-0277 오탐 정정에서 남은 관찰 — 전리품 회복은 15% 이므로 만피가
  아닐 수 있다. `hp > 75%` 조건이 실제로 얼마나 자주 참인지는 미측정 →
  **ADR-0279 열린 질문 (a) 로 이관** (`npm run endings` 가 HP 를 함께 남겨 측정 가능).

## 변경 이력

- 2026-11-05: Draft → Accepted (오너 "응 결함 수정해줘. 그리고 더 찾아봐줘."). 결함 6건 수정 +
  오탐 3건 정정 + 재측정 신규 2건 수정. 경제 결함 1건은 오너 결정으로 이관.

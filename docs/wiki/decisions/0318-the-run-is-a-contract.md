# ADR-0318: 런은 계약이다 — 3미션 연쇄, 그리고 완주가 부보다 먼저 온다

**상태**: Accepted
**날짜**: 2026-11-17
**결정자**: AI 위임 (ADR-0315 슬라이스 2 · Jev `choice` p=0.91 conf 0.86)
**우선순위**: P1 (구조 · 진행)

## 컨텍스트 (Context)

ADR-0315 는 "런은 캠페인"을 정하고 슬라이스 2 를 **캠페인 골격**(`missionsCompleted`
카운트 + 미션 연쇄 + `liberation` 개방)으로 남겼다. 그때 실측된 문제:

- `missionsCompleted` 가 **하드코딩 1** 이었다(`state_actions_phases.ts`). 그래서
  `resolveEnding` 의 `missionsCompleted >= 3` 분기 — `liberation` 엔딩 — 이 **도달 불가**였다.
- 런은 여전히 **미션 하나**였다: 마지막 노드의 전리품에서 ENTER 를 누르면 곧바로 엔딩.

그리고 구현하려니 **ADR-0314 와 부딪힌다.** ADR-0314 는 `control`(부) 분기의 hp 게이트를
지우면서 **2330개 엔딩을 측정**했는데, 그 측정의 전제는 **런 = 미션 하나**였다. 캠페인은 그
전제를 바꾼다: 3미션을 완주하면 크레딧이 훨씬 많이 쌓인다(실측: g1 계약 하나가 **4575cr**).

## 고려한 옵션

### Option A: 완주(liberation)가 부(control)보다 먼저 (채택)
- **설명**: `resolveEnding` 에서 `missionsCompleted >= 3` 를 `credits > 5000` **앞으로** 옮긴다.
- **장점**: 캠페인의 절정이 **캠페인의 엔딩**이 된다. "계약을 끝냈다"가 "돈을 벌었다"보다
  런에 대해 더 많이 말한다. `control` 은 **짧고 부유한 런**의 엔딩으로 남는다(여전히 도달 가능).
- **단점**: ADR-0314 의 **측정 결과를 다른 분포에 적용**하게 된다 → 새 ADR 이 필요하다(이 문서).
- **Jev**: p=0.91 · conf 0.86.

### Option B: 순서를 두고 `control` 임계값을 올린다 (기각, p=0.08)
- **설명**: `credits > 5000` 을 캠페인 기준(예: 12000)으로 올린다.
- **단점**: 임계값이 **캠페인 길이에 묶인다.** 계약 길이를 바꾸면 밸런스가 조용히 깨진다.

### Option C: 순서를 두고 `control` 을 절정으로 받아들인다 (기각, p=0.01)
- **설명**: 3미션 완주자는 대개 부자이므로 `control` 이 뜬다.
- **단점**: 계약을 끝낸 거의 모든 런이 **"너는 부자가 됐다"** 로 끝난다. 캠페인의 보상이 없다.

### 계약의 모양 (별도 결정)

| | 선택 | 이유 |
|---|---|---|
| 길이 | **3미션** | `resolveEnding` 의 문턱이 `>= 3` 이다. 짧으면 절대 못 열고, 길면 늦게 온다 |
| 구성 | **고른 미션의 arc, 등급 오름차순** | arc 가 곧 계약의 이야기다(ADR-0316 이 미션마다 그 arc 의 서사를 브리핑한다). 등급 순서라 연쇄가 튀지 않는다 |
| 넘침 | **arc 를 감아 채운다** | 계약이 항상 채워진다. Far Grid 는 별도 유니버스라 제외(ADR-0213) |
| 미션 사이 | **HP 리셋 · 크레딧·덱·고유 이월** | Q3(HP 리셋) · ADR-0314(크레딧이 조건이려면 쌓여야 한다) · ADR-0303/0311(고유는 캠페인당 1장) |

## 결정 (Decision)

1. **런은 계약(contract)이다.** 고른 미션의 arc 에서 **3미션**을 등급 오름차순으로 연쇄한다.
2. **미션을 끝내면 다음 다리(leg)가 시작된다** — 엔딩이 아니라. 마지막 다리를 끝내야 엔딩이다.
3. **`missionsCompleted` 는 실제 개수다**(`campaign.completed + 1`). 계약 없는 런은 1 그대로다.
4. **완주가 부보다 먼저 온다**(Option A). `missionsCompleted >= 3` → `liberation`,
   `credits > 5000` → `control`. `hpPct <= 0`(sacrifice)는 여전히 둘보다 앞이다.
5. **계약은 저장된다** — 미션 **id 만**(슬롯은 레시피라는 관례). 복원은 카탈로그로 다리를
   다시 세우고, 저장된 미션과 다리가 어긋나면 **계약을 버리고 단일 미션으로** 되돌린다.
6. **다리 전환은 비트로 말한다** — 픽서가 다음 작업을 넘긴다(ADR-0316 의 브리핑을 그대로 쓴다).
   조용한 리로드가 아니라 이야기의 한 마디다.

## 결과 (Consequences)

- **바뀌는 것**: 계약이 있는 런은 미션 3개를 잇달아 플레이한다. 엔딩 화면은 계약을 끝낸
  런에서만 나오므로 **항상 `liberation`** 이다(실측: trace 가 `arc1_first_blood` 로 끝났다).
- **안 바뀌는 것**: **계약이 없는 런은 그대로다.** 테스트 픽스처·구버전 세이브·미션 단위
  하네스는 `campaign` 이 없어 이전과 같은 경로를 탄다 — 결정적 곡선이 **byte-identical** 인
  이유다(밸런스 `100/100/100/98.9/83.9/32.3` · 생존 `100/97.1/75.9/51.4/26.9/32.3`).
- **ADR-0314 와의 관계**: `control` 의 **조건**은 그대로다(`credits > 5000`, hp 게이트 없음).
  바뀐 것은 **분기 순서**이고, 그 이유는 ADR-0314 의 측정이 단일 미션 분포였다는 것이다.
- **미해결로 남기는 것**: 캠페인 기준 밸런스(ADR-0315 (d)) — 하네스가 미션 단위라
  "N미션 생존율"이 아직 없다. g6 고유 누적(ADR-0315 (c))도 그대로다.

## 열린 질문

- **(a) 미션 사이의 prep.** 지금은 다리 사이에 advance 화면이 없다(HP 만 회복). 전리품으로
  회복하게 하려면 다리 사이에 화면이 하나 필요하다.
- **(b) 계약의 선택.** 지금은 **고른 미션의 arc** 가 계약을 정한다(미션 선택 화면이 곧 계약 선택).
  arc 를 직접 고르는 화면은 ADR-0315 의 "계약(arc)"을 더 정직하게 만든다.
- **(c) 캠페인 밸런스 기준선.** 미션 단위 하네스로는 캠페인을 검증할 수 없다(ADR-0315 (d)).
- **(d) 계약 길이의 가변성.** 3 은 리졸버의 문턱에서 온 숫자다. 길이를 플레이어나 arc 가
  정하게 되면 문턱도 함께 움직여야 한다.

## Implementation Status (2026-11-17)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state/campaign.ts` — `CONTRACT_LENGTH` · `contractFor` · `campaignContinues` ·
  `campaignLength` · `campaignMission` · `Campaign`/`CampaignLeg`
- `web/src/core/state/state.ts` — `applyAction` 의 loot 경계에서 `startNextLeg`(이월/리셋 규칙) ·
  `stateToSaveSlot`/`slotToGameState` 의 `campaignMissionIds`·`campaignCompleted` · `campaignFromSlot`
- `web/src/core/state/state_actions_phases.ts` — `missionsCompleted: (state.campaign?.completed ?? 0) + 1`
- `web/src/core/combat/ending_resolver.ts` — 완주 분기를 부보다 앞으로
- `web/src/main.ts` — 런 시작에서 `contractFor` · 다리 전환 비트 카드(`CONTRACT n/3` + 브리핑)
- `web/tests/adr0315_campaign_chain.test.ts` — 13 tests(계약 모양 · 연쇄 · 이월/리셋 · 엔딩 우선순위 · 세이브 왕복)
- `web/e2e/story_trace.spec.ts` — 3미션 완주를 실제로 플레이하고, 끝난 계약의 엔딩이
  **`liberation`** 인지 단언

**Notes**: 미션 단위 결정적 곡선은 **무영향**(계약이 없으면 옛 경로). 캠페인 밸런스 기준선은
아직 없다(열린 질문 c).

## 관련 결정

- ADR-0315 — 런은 캠페인이다(이 문서가 그 슬라이스 2)
- ADR-0314 — 크레딧이 엔딩 조건(이 문서가 그 분기 **순서**를 캠페인에 맞게 바꾼다)
- ADR-0199 — 웹 MVP(단일 미션 런) — 계약이 그 범위를 넓힌다
- ADR-0316 — 미션 브리핑(다리 전환 비트가 이 글을 쓴다)
- ADR-0213 — Far Grid(별도 유니버스 — 계약에 들어오지 않는다)
- ADR-0303 · ADR-0311 — 고유 카드(캠페인당 1장)
- ADR-0287 — 선택 필드로 스키마를 넓히는 관례(계약 필드가 그 관례를 따른다)

## 변경 이력

- 2026-11-17: Accepted — 슬라이스 2 구현(계약 3미션 연쇄 · 완주 우선 · 세이브 · 다리 비트)

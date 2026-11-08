# ADR-0308: 우회는 게이트를 통과한다 — 유일한 교전을 우회하면 미션이 잠겼다

**상태**: Accepted
**날짜**: 2026-11-08
**결정자**: 사용자 (후보 선정은 Jev Choice — p=0.94)
**우선순위**: P0 (소프트락 수정)

## 컨텍스트 (Context)

ADR-0290 은 보스(코어)를 **경로 없이는 열리지 않게** 봉인했다:
`bossGateNeed = min(BOSS_GATE_CLEARS_BY_GRADE[grade], 보드의 비-보스 ICE 노드 수)` 이고,
`clearedEncounterNodes.length >= need` 여야 코어가 열린다.

`BYPASS` 는 런당 1회, 60 COST 를 내고 교전을 건너뛰는 verb 다. 구현은 노드를
`bypassedEncounterNodes` 에 넣지만 **노드의 `iceIds` 는 지우지 않는다**
(`web/src/core/state/encounter_verbs.ts`). 그래서 clamp 가 그 노드를 **여전히 "사용 가능"으로
세고**, 보드에 비-보스 교전이 하나뿐이면:

- `available = 1` → `need = 1`
- `cleared = 0` → 봉인 유지
- 우회한 노드는 게임·하네스 모두 **resolved 로 취급**하므로 다시 싸울 수도, 다른 교전도 없다
- → **코어가 영구히 봉인**. 탈출은 `JACK OUT`(런 포기) 뿐.

**재현 (실브라우저, 실키)**: `Flatline's Call` — 비-보스 ICE 노드 9, 보스 노드 3.

```
node 9 로 이동 → ENTER → BYPASS            → bypassed=[9], cleared=[]
보스 앞에서 ENTER                           → "Core sealed — 1 more ICE must fall (0/1)."
```

**하네스가 같은 것을 3/99 로 보고했다**: 브라우저 소크 census(33미션 × 3정책)의
`no_end_in_steps` 3건이 전부 `random` 정책(30% 확률로 BYPASS)이고 `businessLeft = 1`
(남은 것은 보스뿐)이었다.

## 고려한 옵션

### Option 1: clamp 에서 우회한 노드를 제외한다 (채택)

- **설명**: `available` 을 "비-보스 && `iceIds.length > 0` && **우회되지 않은**" 노드로 센다.
  즉 **BYPASS 를 "해결된 교전"으로 인정**한다.
- **장점**: 소프트락이 사라진다. 우회는 이미 60 COST 를 냈으므로 "공짜 통과"가 아니다.
  규칙이 한 곳(`bossGateNeed`)에서만 바뀌고, 하네스의 `hasBusiness` 가 이미 쓰던 의미
  ("우회 = 해결")와 **일치**한다.
- **단점**: 교전이 하나뿐인 보드에서는 **60 COST 로 게이트를 통째로 살 수 있다.** 다만 우회는
  런당 1회이고 60 COST 는 상한(100)의 60% 라 싸지 않다.
- **Pillar 정합**:
  - P1 (The Run): 런이 **끝날 수 있게** 된다.
  - P2 (The Matrix): 경로 선택에 "돈으로 우회"라는 두 번째 답이 생긴다.
  - P3 (The Flatline): `JACK OUT` 만이 출구인 상태를 제거한다.
  - P4 (The Build): 무영향(카드·덱).
  - P5 (The Style): 무영향.

### Option 2: 우회를 clear 로 세다 (`have = cleared.length + bypassed.length`)

- **설명**: `have` 를 늘린다.
- **장점**: 같은 소프트락을 고친다.
- **단점**: 교전이 둘 이상인 보드에서 **우회 1회가 clear 1회를 대체**한다 → 60 COST 로
  게이트를 사는 경로가 **모든 미션**에 열린다(Option 1 은 교전이 하나뿐일 때만 그렇다).
  봉인의 "진짜 경로" 의도를 더 약하게 만든다.

### Option 3: 미룬다 (defer)

- **설명**: 소프트락을 문서화만 하고 오너 결정을 기다린다.
- **장점**: 추가 측정 없음.
- **단점**: **미완주 런이 남는다**(3/99). 플레이어가 미션을 끝낼 수 없는 상태는 밸런스
  문제가 아니라 **결함**이다.

## 추천 (Recommendation)

**Option 1.** Jev(Choice) 판정: `exclude_bypassed_from_clamp` **p = 0.94**, confidence **0.91**
(다른 후보: `count_bypassed_as_clears` 0.05 · `defer_to_owner` 0.01). Choice 임계 0.5 와
보수 임계 0.85 를 모두 넘는다.

## 사용자 결정 (Decision)

[x] Option 1

## 결과 (Consequences)

- `bossGateNeed` 가 `bypassedEncounterNodes`(선택 필드)를 받는다. 호출자는 `state` 를 그대로
  넘기므로 **호출부 변경 없음**.
- **밸런스 무영향**: 헤드리스 정책(`play_policy.ts`)은 BREACH 만 쓴다 →
  `npm run survival -- --policies --seeds 32` 가 **byte-identical**
  (optimal 100/98.2/76.7/51.2/26.0/13.5 · default 100/78.3/47.4/36.3/4.9/2.1 · gap +16.1pp).
- **소크 census**: `no_end_in_steps` **3 → 0**(99런).
- 우회는 여전히 "해결"이므로 **재방문 대상이 아니다**(게임과 하네스가 같은 의미를 쓴다).

## Implementation Status (2026-11-08)

**Status**: ✅ Implemented

**Evidence**:

- `web/src/core/combat/ice_scaling.ts` — `bossGateNeed` 가 우회 노드를 `available` 에서 제외.
- `web/tests/adr0308_bypass_resolves_the_gate.test.ts` (3) — ① 우회한 유일 교전 → 코어가 열린다
  ② 교전 둘 중 하나만 우회 → 나머지는 여전히 요구된다 ③ 우회 + clear → clear 가 게이트를 충족한다.
- 재측정: `survival --policies --seeds 32` byte-identical · 소크 census `no_end_in_steps` **3 → 0**.

**Notes**: ADR-0290 의 게이트 **규칙 자체**를 바꾸므로 새 ADR 을 썼다(결정 내용 변경은 새 ADR —
ADR-0195). ADR-0290 은 결정을 그대로 두고 `## Implementation Status` 에 참조만 달았다.

## 영향 받는 항목

- `web/src/core/combat/ice_scaling.ts` · `web/tests/adr0308_bypass_resolves_the_gate.test.ts`
- `web/e2e/soak_playthrough.spec.ts` (census 수치)

## 관련 결정

- ADR-0290 (게이트 도입) · ADR-0289 (clamp 의 이유 — "짧은 미션이 잠기면 안 된다") ·
  ADR-0295/0296 (다른 화폐 교환)

## 변경 이력

- 2026-11-08: Draft → Accepted (Option 1, Jev Choice p=0.94). 소크 census 3/99 소프트락에서 출발.

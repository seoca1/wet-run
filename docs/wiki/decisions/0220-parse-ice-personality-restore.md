# ADR-0220: `parseIce` 가 authored `personality` 을 복원한다

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219 sibling)
**관련**: [ADR-0161 — personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0148 — aggression tiers](./0148-combat-depth-expansion.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **loader 데이터 경로 하나**다 — `parseIce` 가 `personality` 을 `Ice` 객체로
> 복사한다. combat path, 밸런스 상수, `aggression` 필드는 **변경하지 않았다.**
>
> **범위 밖 후속 항목**: `aggression` 필드도 `parseIce` 가 조용히 버리고 있다 (동일 결함
> 계열). 이번에는 **측정만** 하고 되돌렸다 — 별도 결정 필요. 상세는 「결과 (Consequences) →
> 후속 항목 (1)」.

## 컨텍스트 (Context)

### 근본 원인 — `parseIce` 의 `personality` drop

`parseIce` (`web/src/core/data_loaders.ts`) 는 `id/name/armor/tier/hp`
(+`hpBase`/`hpPerGrade`/`skills`) 만 복사하고 **`personality` 를 조용히 버렸다.**

`Ice` 타입 자체는 `personality` 을 선언하고 있었다 (`web/src/core/types.ts:80`):

```ts
readonly personality?: "aggressive" | "defensive" | "stealth" | "support";
```

즉 loader 가 그냥 놓친 것이다. `Ice` 는 optional 필드로 선언되어 있으므로 타입은 조용히
통과했고, 런타임에는 `coercePersonality(undefined) === "aggressive"`
(`web/src/core/ice_ai.ts:73`) 로 해석되었다.

### 결과 — authored personality 분포가 inert

`web/src/data/ice_types.json` 의 personality 분포는 **aggressive 80 / defensive 12 /
stealth 5 / support 0** 이다 (97 row 전수 확인). 그런데 **runtime 에서는 모든 catalog ICE 가
`aggressive` 였다.** 데이터에는 있으나 런타임에 닿지 않았다.

`personality` 를 실제로 읽는 소비자는 `web/src/core/ice_ai.ts` 의 다섯 곳이다:

| 소비자 | 동작 |
|---|---|
| `selectSkillByPersonality` (`ice_ai.ts:188`) | archetype 별 skill preference 매칭 |
| `shouldDefensiveAct` (`ice_ai.ts:237`) | `defensive` 만 HP 50% 아래에서 방어 행동 |
| `getAlarmMultiplier` (`ice_ai.ts:248`) | `stealth` 만 alarm tick rate 절반 |
| `getCritBonus` (`ice_ai.ts:257`) | `aggressive` 만 crit +5% |
| `shouldTargetAlly` (`ice_ai.ts:267`) | `support` 만 아군 타깃 |

이 다섯 경로가 전부 `aggressive` fallback 위에서만 작동했다. 즉 **archetype 시스템
전체가 inert** 했다.

### ADR-0216 과 동일한 결함 계열

ADR-0216 은 `parseIce` 가 **`skills`** 를 조용히 버리는 문제를 다뤘다 (ICE 97종 중 44종이
자신의 스킬을 잃었다). 이번에는 같은 loader 가 **`personality`** 을 조용히 버린다.
"loader 가 필드를 조용히 drop 한다" 는 패턴이 두 번째 반복되었다.

### 발견 경위 — ADR-0219 Option B 구현 중

ADR-0219 (Option B — Consistency-only) 를 구현하면서 발견되었다. ADR-0219 는 이미
Accepted 이므로 **수정할 수 없다** (`AGENTS.md` §8 — Accepted 결정 임의 변경 금지).
따라서 신규 ADR 이 필요하다. ADR-0219 의 「결과 (Consequences) → 남은 gap (1)」 에
후속 항목으로 기록되어 있다.

## 고려한 옵션

### Option 1: `personality` 을 복원하되 malformed 값은 coerce (선택)

- **설명**: `parseIce` 가 `personality` 을 복사한다. 값이 유효하지 않으면
  `coercePersonality` 처럼 `"aggressive"` 로 조용히 대체한다.
- **장점**: 절대 throw 하지 않는다. 기존 데이터의 오타가 게임을 깨뜨리지 않는다.
- **단점**: **잘못된 authoring 을 조용히 감춘다.** `ice_ai.ts` 의 `coercePersonality`
  가 이미 존재하지만, 그건 **runtime combatant** (외부/합성 입력) 를 위한 방어선이지
  **저장 데이터 검증** 이 아니다. loader 는 데이터 경계 (data boundary) 다 — 여기서
  조용히 대체하면 authoring 오류가 플레이 도중까지 살아남는다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ personality 경로가 살아난다.
  - P4 (The Build): ⚠️ 데이터 오류가 지연 발견된다.

### Option 2: `personality` 을 복원하고 유효하지 않은 값은 throw (선택)

- **설명**: `parseIce` 가 `personality` 을 복사한다. 값이
  `"aggressive" | "defensive" | "stealth" | "support"` 중 하나가 아니면 **throw** 한다.
- **장점**:
  - authoring 오류가 **데이터 경계에서 즉시** 드러난다.
  - loader 의 기존 strict-validation 스타일과 일치한다 (`armor`/`defense` 동시 설정,
    `source_universe` 미지 값, `skills` malformed entry 등 모두 이미 throw 한다).
  - ADR-0216 과 같은 결함 계열을 **같은 방식으로** 닫는다 (조용히 버리지 않는다).
- **단점**: 기존 catalog 에 잘못된 값이 있으면 게임이 시작되지 않는다. (실측: 현재
  catalog 의 97 row 는 전부 유효하다 — throw 대상 없음.)
- **Pillar 정합**:
  - P3 (The Flatline): ✅ personality 경로가 살아난다.
  - P4 (The Build): ✅ 데이터 정합성 — 조용한 drop 을 loud failure 로 대체.

### Option 3: 현상 유지 (no-op)

- **설명**: 아무것도 바꾸지 않는다.
- **단점**: archetype 시스템이 계속 inert 하다. ADR-0216 과 동일 결함 계열을 남긴다.
- **Pillar 정합**: 실패.

## 추천 (Recommendation)

**Option 2.** Option 1 의 "절대 throw 하지 않는다" 는 **저장 데이터** 에 대한 것이다.
`coercePersonality` 의 존재 이유 (Python 프로토타입 포팅의 legacy guard) 와는 목적이
다르다. loader 는 이미 다른 필드에서 strict validation 을 하고 있으므로, `personality`
만 예외적으로 coerce 하면 그 필드가 **다른 필드들과 다른 규칙**을 갖게 된다.

## 사용자 결정 (Decision)

[ x ] Option 2 — `personality` 복원 + 유효하지 않은 값은 throw
[ ] Option 1 — `personality` 복원 + coerce
[ ] Option 3 — 현상 유지
[ ] Defer (다음 단계로 미룸)

### 결정된 내용

1. **`parseIce` 는 `personality` 을 `Ice` 로 복사한다.** 파일의 기존 optional-spread
   스타일 (`...(skills !== undefined ? { skills } : {})`) 을 그대로 따른다.
2. **값이 없으면 key 자체를 생략한다.** 즉 `"personality" in ice === false`. optional
   필드 계약과 backward compatibility 를 보존한다.
3. **값이 있는데 유효 archetype 4종 중 하나가 아니면 throw 한다.** 메시지는
   `[data_loaders]` prefix 를 달고, 해당 ICE 의 이름을 명시한다. loader 의 기존
   strict-validation 스타일과 일치한다. **조용한 coerce 는 하지 않는다.**
4. **`aggression` 필드는 이번 결정의 범위 밖이다.** `parseIce` 가 그것도 버리고
   있다는 사실은 기록하되 (**후속 항목 (1)**), 여기서는 고치지 않는다.

## 결과 (Consequences)

### 긍정적 영향

- **authored personality 분포가 더 이상 inert 하지 않다.** `defensive` 12종과 `stealth`
  5종이 자기 archetype 로 동작한다.
- **loader 가 authored 필드를 조용히 버리지 않는다.** ADR-0216 과 같은 결함 계열이
  이 필드에 대해 닫혔다.
- **malformed 값이 데이터 경계에서 즉시 실패한다.** 조용한 coerce 대신 loud failure 다.
  `ice_ai.ts` 의 `coercePersonality` fallback 이 runtime combatant 용 legacy guard 로
  남고, 저장 데이터의 정합성은 loader 가 책임진다 — 책임 경계가 명확해진다.
- **밸런스는 손상되지 않았다.** `npm run balance` 의 BEFORE/AFTER 출력이 **6개 grade
  전부 모든 column 에서 동일**하다 (승률·stall·mean-turns·mean-HP-end 전부).
  grade band 하나도 이동하지 않았다.

### 부정적 영향 / 수용한 비용

- **material 한 부작용은 없다.** 밸런스 band 가 하나도 움직이지 않았고, 기존 assertion
  하나도 약화되지 않았다 (append-only 테스트 추가 + loader 수정뿐).
- **contract 하나가 명시적으로 좁아졌다.** 이제 `personality` 을 가진 ICE 는 그 값이
  4종 archetype 중 하나여야 한다. catalog 밖의 ICE 를 만들려면 그 규칙을 지켜야 한다.
  (이 contract 는 `Ice` 타입이 이미 선언하고 있던 것이고, loader 가 이제 지킨다.)

### 밸런스가 움직이지 않은 이유 — 실측 확인

> **흔한 오해를 먼저 배제한다.** 밸런스 하네스가 encounter band 를 아예 건드리지
> 않는다는 설명은 **틀렸다.** `scripts/balance_sim.ts` 는 `makeInitialState` 로 실제
> matrix 를 만들고, `resolveMatrixRoster(...).ice[0]` — **`dungeonToMatrix` 가
> `ENCOUNTER_ICE_BY_GRADE` 에서 뽑아 encounter node 에 배정한 ICE** — 를 측정한다.
> 직접 probe 로 확인: `aleph_fragment` (grade 5) 에서 harness 의 base ICE 는
> `hellhound` 이다 (28-node matrix, encounter node 1). `iceCatalog[0]` (`standard`) 이
> 아니다.

진짜 이유는 **personality 가 읽히는 경로** 와 **band ICE 의 스킬 보유 여부** 의
교차에 있다.

- `personality` 는 `ice_ai.ts` 가 읽는 곳에서만 작용한다 —
  `selectSkillByPersonality`, `shouldDefensiveAct`, `getAlarmMultiplier`,
  `getCritBonus`, `shouldTargetAlly`.
- band 안에서 personality 가 non-aggressive 인 ICE 는 `watchdog` (`defensive`) 와
  `ice_neuromancer_warden` (`defensive`), `wisp` (`stealth`) 뿐이고, **셋 다
  `skills: []`** 다. 즉 `selectSkillByPersonality` 가 호출될 후보가 없고, preference
  매칭 자체가 일어나지 않는다.
- **스킬을 carry 하는 band ICE 2종** (`loa_entity` g5, `aleph` g6) 은 **둘 다
  `aggressive`** 다. `aggressive` 는 coerce fallback 과 **같은 값**이므로
  before/after 동작이 완전히 동일하다.

즉 **band 안에서 personality 가 실제 행동을 바꾸는 ICE 는 하나도 없다** — personality
값이 전달되든 말든 결과가 같으므로 밸런스가 안 움직이는 것은 **정확히 맞다** (결함이
아니라 reach 한계).

### 후속 항목

#### (1) `aggression` 도 `parseIce` 가 버린다 — **측정만 했고, 고치지 않았다**

`parseIce` 가 `personality` 뿐 아니라 **`aggression` 도 조용히 버린다.** 동일 결함
계열이지만 **이번 ADR 의 범위 밖**이다 (결정하지 않았다).

- `ice_types.json` 의 aggression 분포: **standard 36 / aggressive 25 / boss 36**
  (97 row 전수 확인). 모든 row 가 `aggression` key 를 갖고 있다.
- `aggression` 은 `enemyShouldUseSkill` (`web/src/core/ice_ai.ts:105`) 를 게이트한다 —
  per-tick 스킬 사용 확률 `passive 0.05 / standard 0.15 / aggressive 0.35 / boss 0.5`
  (`ice_ai.ts:34-40`).
- **인구(popopulation)로는 personality 보다 큰 레버다.** 97 ICE 중 **61 종**이
  non-`standard` 이며, **boss-tier ICE 를 전부 포함**한다. encounter band 안에서도
  24 slot 중 **15 slot** 이 non-`standard` 값을 갖는다 (`standard` 9 / `aggressive` 9 /
  `boss` 6).
- **측정 전용 probe** 를 했다 — `aggression` 을 임시로 복사한 뒤 **완전히 되돌렸다**.
  결과는 **grade 5 `mean-HP-end` 5.6 → 5.7** 뿐이었고 win-rate / stall / turn 이동은
  없었다. 신호가 작은 이유는 이 경로가 **non-empty `skills` 를 요구**하는데 band ICE
  대부분이 스킬을 갖지 않기 때문이다.
- 그래도 **별도 결정이 필요하다.** `aggression` 은 catalog **전체**의 스킬 발사
  *빈도*를 바꾸기 때문이다 (catalog 전체 61 종 + boss 전부). 밸런스가 "안 움직였다"는
  측정 결과만으로 ship 할 사안이 아니다.
- **아무것도 commit 되지 않았다.** 이 항목은 **기록만** 되어 있다.

#### (2) `support` archetype 에는 catalog ICE 가 0종

`ice_types.json` 의 personality 분포에서 `support` 는 **0종**이다. 그래서
`shouldTargetAlly` (`ice_ai.ts:267`) 는 여전히 도달 불가 상태다. 이건 **loader gap 이
아니라 data gap** 이다 — loader 는 `support` 를 정상적으로 전달한다. catalog 에
`support` ICE 를 추가하는 것은 별도의 콘텐츠 결정이다.

#### (3) boss phase-4 Drone minion 은 catalog 데이터가 아니다

`state_actions_combat.ts:196-197` 이 boss phase 4 minion (Drone) 에 `personality:
"aggressive"` / `aggression: "standard"` 를 **hardcode** 한다. 이건 catalog 가 아니라
합성 combatant 다. **이번 ADR 에서 건드리지 않았다.**

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/data_loaders.ts:60-66` — 신규 `VALID_ICE_PERSONALITY` set
  (`aggressive` / `defensive` / `stealth` / `support`)
- `web/src/core/data_loaders.ts:57` — `LegacyIce` 가 `personality?: string` 을 얻음
- `web/src/core/data_loaders.ts:277-294` — `parseIce` 가 `personality` 을 검증하고
  복사 (malformed 값은 `[data_loaders]` prefix 메시지로 throw)
- `web/src/core/data_loaders.ts:304` — `...(personality !== undefined ? { personality } : {})`
  — 값이 없으면 key 자체 생략
- `web/src/core/types.ts:80` — `Ice.personality` (이미 선언되어 있었고, 이전에는 한 번도
  populate 되지 않았다)
- `web/tests/data_loaders.test.ts:467-518` — 신규 `describe("data_loaders: ICE personality")`
  블록, 테스트 4건:
  - `:468-477` — 알려진 non-aggressive ICE 가 자신의 personality 를 노출 (`watchdog` →
    `defensive`, `wisp` → `stealth`)
  - `:479-499` — catalog 의 personality 분포가 `ice_types.json` 과 정확히 일치
  - `:501-505` — key 가 없으면 field 자체가 생략 (`"personality" in ice === false`)
  - `:507-517` — malformed 값은 `[data_loaders]` prefix 로 throw
- Pre-fix 검증 (`data_loaders.ts` 를 임시로 되돌림): 신규 테스트 4건 중 **3건 실패** —
  `expected undefined to be 'defensive'`, `expected [] to deeply equal [ 'ai_whisper',
  'aleph', …(95) ]`, `expected [Function] to throw an error`. (4번째는 pre-fix 에서
  통과했다 — pre-fix loader 도 이미 absent key 를 생략했으므로.)
- 수정 후 gate: `npm test` **125 files / 2947 tests, 0 failures**;
  `tsc --noEmit` 0 errors; `eslint` 0 errors
- 밸런스 (`npm run balance`, 100 runs/mission) BEFORE vs AFTER: **6개 grade 전부 모든 column
  이 동일** — g1 100.0% / g2 88.8% / g3 73.0% / g4 47.4% / g5 42.4% / g6 0.0%,
  mean-turns 와 mean-HP-end 도 불변. **grade band 하나도 이동하지 않았다.**
- 밸런스가 안 움직인 이유 (추측이 아니라 **실측 확인**): 밸런스 하네스는 encounter band 를
  **실제로 측정한다** — `scripts/balance_sim.ts` 가 `makeInitialState` 로 matrix 를 만들고
  `resolveMatrixRoster(...).ice[0]` (즉 `dungeonToMatrix` 가 `ENCOUNTER_ICE_BY_GRADE` 에서
  뽑은 encounter ICE) 를 읽는다. 직접 probe: `aleph_fragment` (grade 5) 의 base ICE 는
  `hellhound` (28-node matrix, encounter node 1) 이며 `iceCatalog[0]` (`standard`) 가
  아니다. delta 가 0 인 진짜 이유는 `personality` 를 읽는 경로 (`selectSkillByPersonality`,
  `shouldDefensiveAct`, `getAlarmMultiplier`, `getCritBonus`, `shouldTargetAlly`) 와
  band ICE 의 스킬 보유 여부의 교차다 — personality 가 non-aggressive 인 band ICE
  (`watchdog`, `ice_neuromancer_warden` → `defensive`; `wisp` → `stealth`) 는 **셋 다
  `skills: []`** 라 preference 매칭 자체가 일어나지 않고, **스킬을 carry 하는 band ICE
  2종** (`loa_entity`, `aleph`) 은 **둘 다 `aggressive`** — coerce fallback 과 같은 값이라
  before/after 가 완전히 동일하다.

**Notes**:

- **diff 는 append-only 다.** `web/src/core/data_loaders.ts` +28 LOC, `web/tests/data_loaders.test.ts`
  +64 LOC. 기존 assertion 은 하나도 약화되지 않았고, 수정된 파일은 이 둘뿐이다.
- **`aggression` 은 고치지 않았다.** `aggression` 을 임시로 복사하는 **measurement-only
  probe** 로 grade 5 `mean-HP-end` 5.6 → 5.7 만 관측했고, 그 변경은 **완전히 되돌렸다**.
  이 ADR 는 `aggression` 을 **fix했다고 주장하지 않는다** — 「후속 항목 (1)」 참조.
- **ADR-0219 는 수정하지 않았다.** 0219 는 Accepted 이므로 immutable 이고 (`AGENTS.md`
  §8), 이 gap 은 신규 ADR 로 분리했다.
- `coercePersonality` (`ice_ai.ts:73`) 는 **변경하지 않았다.** loader 가 저장 데이터의
  정합성을 책임지고, `coercePersonality` 는 runtime combatant 용 legacy guard 로 남는다.
- `web/src/core/ice_ai.ts`, `web/src/core/state_actions_combat.ts`,
  `web/src/core/types.ts`, `web/src/core/ice_scaling.ts`, `web/src/data/ice_types.json`
  는 **모두 미변경**이다.
- `state_actions_combat.ts:196-197` 의 boss phase-4 Drone minion hardcode 는
  **미변경**이다 (합성 combatant, catalog 데이터 아님 — 「후속 항목 (3)」).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/data_loaders.ts` — `parseIce` 가 `personality` 을 복사 + 검증
  (+`VALID_ICE_PERSONALITY`, `LegacyIce.personality`)
- `web/tests/data_loaders.test.ts` — `describe("data_loaders: ICE personality")` 블록 추가
  (테스트 4건)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_ai.ts` — `coercePersonality`, `selectSkillByPersonality`,
  `shouldDefensiveAct`, `getAlarmMultiplier`, `getCritBonus`, `shouldTargetAlly`
- `web/src/core/types.ts` — `Ice.personality` / `Ice.aggression` 선언 (이미 존재)
- `web/src/core/state_actions_combat.ts` — enemy combat path, boss phase-4 Drone minion
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` (encounter band 구성)
- `web/src/data/ice_types.json` — authored personality / aggression 데이터 (변경 없음)
- `web/scripts/balance_sim.ts` — 밸런스 하네스 (변경 없음)

### 후속 항목 (이번 ADR 범위 밖)

- `web/src/core/data_loaders.ts` — `aggression` 누락 (동일 결함 계열). **측정만 하고
  되돌렸다.** 별도 결정 필요 — 「후속 항목 (1)」.
- `web/src/data/ice_types.json` — `support` archetype ICE 추가 (data gap) —
  「후속 항목 (2)」.

## 관련 결정

- ADR-0148 (aggression tiers) — `AGGRESSION_PROBABILITY` 의 owner. `aggression` 후속
  항목의 대상
- ADR-0161 (personality archetypes) — `PERSONALITY_SKILL_PREFERENCE` 와 archetype 정의의
  owner. 본 ADR 가 복원하는 필드의 출처
- ADR-0216 (derived ICE skill metadata) — **선례 (precedent)**. `parseIce` 가 `skills` 를
  조용히 drop 하던 것을 loader-side derivation 으로 고친 ADR. `parseIce` 가 필드를
  조용히 drop 하는 결함 계열이 여기서 두 번째 반복되었다 (`skills` → `personality`)
- ADR-0219 (non-damaging ICE 스킬 효과) — Option B. 이 gap 이 **발견된** 자리이며,
  후속 항목으로 기록되어 있다. 0219 는 Accepted 이므로 immutable 이고 수정하지 않았다

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 2 — `personality` 복원 + malformed 값은
  throw) — 구현 완료·검증. Consequences / Implementation Status 채움. `aggression`
  누락은 measurement-only probe 로 **측정 후 완전 되돌린** 상태로 후속 항목에 기록.

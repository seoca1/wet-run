# ADR-0221: `parseIce` 가 authored `aggression` 을 복원한다

**상태**: Accepted
**날짜**: 2026-10-27
**결정자**: Sisyphus (사용자 승인)
**우선순위**: P1 (The Flatline — dead combat path, ADR-0216/0219/0220 sibling)
**관련**: [ADR-0148 — aggression tiers](./0148-combat-depth-expansion.md), [ADR-0161 — personality archetypes](./0161-ice-personality-archetypes.md), [ADR-0216 — derived ICE skill metadata](./0216-derived-ice-skill-metadata.md), [ADR-0219 — non-damaging ICE 스킬 효과](./0219-non-damaging-ice-skill-effects.md), [ADR-0220 — `parseIce` 가 authored `personality` 을 복원한다](./0220-parse-ice-personality-restore.md)

> **이 문서는 Accepted 결정 기록이다.** 2026-10-27 에 결정·구현·검증까지 완료되었다.
> 구현 범위는 **loader 데이터 경로 하나**다 — `parseIce` 가 `aggression` 을 `Ice` 객체로
> 복사한다. combat path, 밸런스 상수, `personality` 필드는 **변경하지 않았다.**
>
> **동일 결함 계열의 마지막 조각.** ADR-0216 (`skills`), ADR-0220 (`personality`) 에
> 이어지는 **세 번째이자 마지막** instance 다. 이 ADR 이 끝나면 `parseIce` 는
> authored 필드를 **하나도 drop 하지 않는다.**

## 컨텍스트 (Context)

### 근본 원인 — `parseIce` 의 `aggression` drop

`parseIce` (`web/src/core/data_loaders.ts`) 는 `id/name/armor/tier/hp`
(+`hpBase`/`hpPerGrade`/`skills`/`personality`) 만 복사하고 **`aggression` 을 조용히
버렸다.**

`Ice` 타입 자체는 `aggression` 을 선언하고 있었다 (`web/src/core/types.ts:81`):

```ts
readonly aggression?: "passive" | "standard" | "aggressive" | "boss";
```

즉 loader 가 그냥 놓친 것이다. `Ice` 는 optional 필드로 선언되어 있으므로 타입은 조용히
통과했고, 런타임에는 `coerceAggression(undefined) === "standard"`
(`web/src/core/ice_ai.ts:62`) 로 해석되었다.

### 결과 — authored aggression 분포가 inert

`web/src/data/ice_types.json` 의 aggression 분포는 **standard 36 / aggressive 25 /
boss 36** 이다 (97 row 전수 확인 — 모든 row 가 `aggression` key 를 갖고 있고 `passive`
row 은 0건). 그런데 **runtime 에서는 모든 catalog ICE 가 `standard` 였다.** 데이터에는
있으나 런타임에 닿지 않았다.

`aggression` 을 실제로 읽는 소비자는 `web/src/core/ice_ai.ts` 의
`enemyShouldUseSkill` (`ice_ai.ts:105`) 이다 — per-tick 스킬 사용 확률을
`AGGRESSION_PROBABILITY` (`ice_ai.ts:34-40`) 에서 고른다:

| tier | 확률 |
|---|---|
| `passive` | 0.05 |
| `standard` | 0.15 |
| `aggressive` | 0.35 |
| `boss` | 0.5 |

즉 **모든 catalog ICE 가 0.15 하나로 고정**이었다.

### 인구(population) — personality 보다 큰 레버

- **catalog 전체**: 97 ICE 중 **61 종**이 non-`standard` (standard 36 / aggressive 25 /
  boss 36). **boss-tier ICE 를 전부 포함**한다.
- **encounter band** (`ENCOUNTER_ICE_BY_GRADE`, `web/src/core/ice_scaling.ts:30`):
  24 slot 중 **15 slot** 이 non-`standard` (standard 9 / aggressive 9 / boss 6).

### 동일 결함 계열의 세 번째 반복

ADR-0216 은 `parseIce` 가 **`skills`** 를 조용히 버리는 문제를 다뤘다 (ICE 97종 중
44종이 자신의 스킬을 잃었다). ADR-0220 은 같은 loader 가 **`personality`** 을 조용히
버리는 문제를 다뤘다. 이번에는 **`aggression`** 이다. "loader 가 필드를 조용히 drop
한다" 는 패턴이 세 번째 반복되었다. 이 ADR 로 계열이 **닫힌다** — `parseIce` 가
authored 필드를 **하나도 drop 하지 않게** 되었다.

### 발견 경위 — ADR-0220 구현 중

ADR-0220 (`personality` 복원) 을 구현하면서 발견되었다. ADR-0220 은 이미 Accepted 이므로
**수정할 수 없다** (`AGENTS.md` §6 — Accepted 결정 임의 변경 금지). 따라서 신규 ADR
이 필요하다. ADR-0220 의 「결과 (Consequences) → 후속 항목 (1)」 에 후속 항목으로
기록되어 있다.

## 고려한 옵션

### Option 1: `aggression` 을 복원하되 malformed 값은 coerce (선택)

- **설명**: `parseIce` 가 `aggression` 을 복사한다. 값이 유효하지 않으면
  `coerceAggression` 처럼 `"standard"` 로 조용히 대체한다.
- **장점**: 절대 throw 하지 않는다. 기존 데이터의 오타가 게임을 깨뜨리지 않는다.
- **단점**: **잘못된 authoring 을 조용히 감춘다.** `ice_ai.ts` 의 `coerceAggression`
  가 이미 존재하지만, 그건 **runtime combatant** (외부/합성 입력) 를 위한 방어선이지
  **저장 데이터 검증** 이 아니다. loader 는 데이터 경계 (data boundary) 다 — 여기서
  조용히 대체하면 authoring 오류가 플레이 도중까지 살아남는다.
- **Pillar 정합**:
  - P3 (The Flatline): ✅ aggression 경로가 살아난다.
  - P4 (The Build): ⚠️ 데이터 오류가 지연 발견된다.

### Option 2: `aggression` 을 복원하고 유효하지 않은 값은 throw (선택)

- **설명**: `parseIce` 가 `aggression` 을 복사한다. 값이
  `"passive" | "standard" | "aggressive" | "boss"` 중 하나가 아니면 **throw** 한다.
- **장점**:
  - authoring 오류가 **데이터 경계에서 즉시** 드러난다.
  - loader 의 기존 strict-validation 스타일과 일치한다 (`armor`/`defense` 동시 설정,
    `source_universe` 미지 값, `skills` malformed entry, `personality` malformed 값 등
    모두 이미 throw 한다).
  - ADR-0216 / ADR-0220 과 같은 결함 계열을 **같은 방식으로** 닫는다 (조용히 버리지
    않는다).
- **단점**: 기존 catalog 에 잘못된 값이 있으면 게임이 시작되지 않는다. (실측: 현재
  catalog 의 97 row 는 전부 유효하다 — throw 대상 없음.)
- **Pillar 정합**:
  - P3 (The Flatline): ✅ aggression 경로가 살아난다.
  - P4 (The Build): ✅ 데이터 정합성 — 조용한 drop 을 loud failure 로 대체.

### Option 3: 현상 유지 (no-op)

- **설명**: 아무것도 바꾸지 않는다.
- **단점**: 61 종의 authored aggression 이 계속 inert 하다. ADR-0216 / ADR-0220 과
  동일 결함 계열을 남긴다.
- **Pillar 정합**: 실패.

## 추천 (Recommendation)

**Option 2.** Option 1 의 "절대 throw 하지 않는다" 는 **저장 데이터** 에 대한 것이다.
`coerceAggression` 의 존재 이유 (Python 프로토타입 포팅의 legacy guard) 와는 목적이
다르다. loader 는 이미 다른 필드에서 strict validation 을 하고 있으므로, `aggression`
만 예외적으로 coerce 하면 그 필드가 **다른 필드들과 다른 규칙**을 갖게 된다.

## 사용자 결정 (Decision)

[ x ] Option 2 — `aggression` 복원 + 유효하지 않은 값은 throw
[ ] Option 1 — `aggression` 복원 + coerce
[ ] Option 3 — 현상 유지
[ ] Defer (다음 단계로 미룸)

### 결정된 내용

1. **`parseIce` 는 `aggression` 을 `Ice` 로 복사한다.** 파일의 기존 optional-spread
   스타일 (`...(skills !== undefined ? { skills } : {})`) 을 그대로 따른다. ADR-0220
   의 `personality` 처리와 동일한 형태다.
2. **`VALID_ICE_AGGRESSION` set 은 선언된 union 값 4종 전부**를 담는다
   (`passive` / `standard` / `aggressive` / `boss`). `ice_types.json` 에 `passive` row
   은 없지만, 그건 **선언된 타입 계약** (`Ice["aggression"]`, `types.ts:81`) 이기 때문이다 —
   loader 는 타입이 약속한 값을 모두 받아들여야 한다.
3. **값이 없으면 key 자체를 생략한다.** 즉 `"aggression" in ice === false`. optional
   필드 계약과 backward compatibility 를 보존한다.
4. **값이 있는데 유효한 4종 중 하나가 아니면 throw 한다.** 메시지는 `[data_loaders]`
   prefix 를 달고, 해당 ICE 의 이름과 받은 값을 명시한다. loader 의 기존
   strict-validation 스타일과 일치한다. **조용한 coerce 는 하지 않는다.**

## 결과 (Consequences)

### 긍정적 영향

- **authored aggression 분포가 더 이상 inert 하지 않다.** `aggressive` 25종과 `boss`
  36종이 자기 tier 로 동작한다.
- **loader 가 authored 필드를 조용히 버리지 않는다.** ADR-0216 / ADR-0220 으로
  이어진 결함 계열이 이 필드에 대해 **닫혔다**. `parseIce` 가 drop 하는 authored
  필드는 **0개**다.
- **malformed 값이 데이터 경계에서 즉시 실패한다.** 조용한 coerce 대신 loud failure 다.
  `ice_ai.ts` 의 `coerceAggression` fallback 이 runtime combatant 용 legacy guard 로
  남고, 저장 데이터의 정합성은 loader 가 책임진다 — 책임 경계가 명확해진다.

### 부정적 영향 / 수용한 비용

- **밸런스가 정확히 한 cell 움직였다.** `npm run balance` BEFORE vs AFTER 비교에서
  **grade-5 `mean-HP-end` 5.6 → 5.7** (+0.1 HP) **한 곳만** 이동했다. 승률
  (win-rate), stall-rate, mean-turns, p5/p95 는 **어느 grade 에서도** 움직이지 않았다.
- **이 이동은 noise 가 아니라 deterministic 이다.** 수정 후 하네스를 **재실행**해서
  **byte-identical** 출력을 확인했다.
- **스킬 발사 빈도가 실제로 오른다.** `loa_entity` 는 스킬을 **2.3배** 자주 쓰고,
  `aleph` 는 **3.3배** 자주 쓴다 (0.15 → 0.35 / 0.5).
- **contract 하나가 명시적으로 좁아졌다.** 이제 `aggression` 을 가진 ICE 는 그 값이
  4종 tier 중 하나여야 한다. catalog 밖의 ICE 를 만들려면 그 규칙을 지켜야 한다.
  (이 contract 는 `Ice` 타입이 이미 선언하고 있던 것이고, loader 가 이제 지킨다.)

### 밸런스가 정확히 한 cell 만 움직인 이유 — 실측 확인

> **흔한 오해를 먼저 배제한다.** 밸런스 하네스가 encounter band 를 아예 건드리지
> 않는다는 설명은 **틀렸다.** `web/scripts/balance_sim.ts` 는 `makeInitialState` 로
> 실제 matrix 를 만들고, `resolveMatrixRoster(...).ice[0]` — **`dungeonToMatrix` 가
> `ENCOUNTER_ICE_BY_GRADE` 에서 뽑아 encounter node 에 배정한 ICE** — 를 측정한다.

진짜 이유는 **`enemyShouldUseSkill` 의 short-circuit** 다.

- `enemyShouldUseSkill` (`ice_ai.ts:105-115`) 은 **스킬이 없으면 `aggression` 을 읽기
  전에** `false` 를 반환한다:

  ```ts
  if ((combatant.skills ?? []).length === 0 || combatant.hp <= 0) {
    return false;
  }
  const tier = coerceAggression(combatant.aggression);
  ```

- 그래서 band 안의 non-`standard` slot 중 **스킬을 carry 하지 않는 13 slot** 은 이
  변경에 **구조적으로immune** 하다 — `aggression` 이 무엇이든 결과가 동일하다.
- **non-`standard` 이면서 스킬을 carry 하는 band ICE 는 정확히 2종**이다:
  - **`loa_entity`** (g5, `aggressive` → 0.35, 이전 0.15) — 스킬 2개
  - **`aleph`** (g6, `boss` → 0.5, 이전 0.15) — 스킬 3개

실측 probe (하네스가 실제로 encounter 하는 ICE 를 그대로 재생성해 확인한 것):

| grade | mission | encounter ICE | aggression | 스킬 |
|---|---|---|---|---|
| g5 | `final_choice` | `loa_entity` | `aggressive` | 2 |
| g6 | `neuromancer_merger` | `aleph` | `boss` | 3 |
| g6 | `wintermute_negotiation` | `aleph` | `boss` | 3 |
| g5 | `aleph_fragment` / `dixies_choice` / `winter_infiltrate` | `hellhound` | `aggressive` | 0 |
| g5 | `craft_job` / `dixies_offer` / `matrix_revelation` / `voodoo_loa_encounter` / `ta_defection` | `neuromancer` | `boss` | 0 |
| g6 | `zion_express` | `neuromancer` | `boss` | 0 |

- **움직인 cell 과 정확히 일치한다.** g5 의 9개 mission 중 **`final_choice` 하나**만
  `loa_entity` 를 만나고 (스킬 2개, non-`standard`), 나머지 8개는 스킬 없는 ICE 다.
  즉 **움직인 유일한 grade-5 `mean-HP-end` cell = `final_choice` 의 `loa_entity`**.
- **g6 은 왜 안 움직이는가.** g6 의 `aleph` 는 `boss` tier 다 (0.5, 스킬 3개 — 3.3배
  더 자주 발사). 하지만 g6 band 는 이미 **0.0% 승률 바닥** 에 붙어 있어 —
  승률이 이미 0 이므로 어떤 숫자도 움직일 여지가 없다.
- 즉 **이 변경이 가장 세게 bite 하는 곳은 g6 인데, 하네스가 그걸 price 할 수 없다.**

### 후속 항목

#### (1) catalog ICE 97종 중 53종이 여전히 자신의 aggression 을 발현할 수 없다

`enemyShouldUseSkill` 이 `aggression` 을 읽기 **전에** 스킬 유무로 short-circuit
하기 때문이다. `ice_types.json` 의 53종이 `skills` 를 carry 하지 않는다. 즉 **데이터는
이제 정확하지만 그 53종에 대해서는 여전히 쓰이지 않는다.** 이것이 실제로 달라지는지는
다른 시스템 (예: ADR-0219 의 Option A/D 작업) 에 달려 있다.

#### (2) archetype / aggression 차이가 실제로 보이는 곳은 encounter band 다

`ENCOUNTER_ICE_BY_GRADE` (`ice_scaling.ts:30`) — 24 slot 중 **현재 2 slot 만** 스킬을
carry 한다. band 커버리지를 넓히는 것은 ADR-0219 의 open item 이다.

#### (3) boss phase-4 Drone minion 은 catalog 데이터가 아니다

`web/src/core/state_actions_combat.ts:196-197` 이 boss phase 4 minion (Drone) 에
`personality: "aggressive"` / `aggression: "standard"` 를 **hardcode** 한다. 이건
catalog 가 아니라 합성 combatant 다. **이번 ADR 에서 건드리지 않았다.**

#### (4) `ice_types.json` 에 `passive` row 은 0건이다

`passive` tier 는 **선언되고 loader 가 받아들이지만** 데이터가 쓰지 않는다. loader 가
4종 전부 수용하는 것은 타입 계약이지, 데이터가 그 tier 를 쓴다는 뜻이 아니다.

## Implementation Status (2026-10-27)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/data_loaders.ts:58` — `LegacyIce` 가 `aggression?: string` 을 얻음
- `web/src/core/data_loaders.ts:69-75` — 신규 `VALID_ICE_AGGRESSION` set, `VALID_ICE_PERSONALITY`
  바로 뒤에 배치 (선언된 union 4종: `passive` / `standard` / `aggressive` / `boss`)
- `web/src/core/data_loaders.ts:304-322` — `parseIce` 가 `aggression` 을 검증하고 복사
  (malformed 값은 `[data_loaders]` prefix 메시지로 throw)
- `web/src/core/data_loaders.ts:333` — `...(aggression !== undefined ? { aggression } : {})`
  — 값이 없으면 key 자체 생략
- `web/src/core/types.ts:81` — `Ice.aggression` (이미 선언되어 있었고, 이전에는 한 번도
  populate 되지 않았다)
- `web/src/core/ice_ai.ts:62` — `coerceAggression` (runtime combatant 용 legacy guard.
  변경하지 않음)
- `web/src/core/ice_ai.ts:34-40` — `AGGRESSION_PROBABILITY` (passive 0.05 / standard
  0.15 / aggressive 0.35 / boss 0.5). 변경하지 않음
- `web/src/core/ice_ai.ts:105-115` — `enemyShouldUseSkill` — 스킬이 없으면 `aggression`
  을 읽기 전에 `false` 반환 (변경하지 않음)
- `web/tests/data_loaders.test.ts:532` — 신규 `describe("data_loaders: ICE aggression")`
  블록, 테스트 4건:
  - `:533-545` — 알려진 non-standard ICE 가 자신의 aggression 를 노출 (`goliath` →
    `aggressive`, `wintermute` → `boss`)
  - `:546-569` — catalog 의 aggression 분포가 `ice_types.json` 과 정확히 일치
    (standard 36 / aggressive 25 / boss 36, 총 97)
  - `:570-575` — key 가 없으면 field 자체가 생략 (`"aggression" in ice === false`)
  - `:576-587` — malformed 값은 `[data_loaders]` prefix 로 throw
- Pre-fix 검증 (`data_loaders.ts` 를 임시로 되돌림, 테스트는 유지): 신규 테스트 4건 중
  **3건 실패** — `expected undefined to be 'aggressive'`, `expected [] to deeply equal
  [ 'ai_whisper', 'aleph', …(95) ]`, `expected [Function] to throw an error`.
  (4번째는 pre-fix 에서 통과했다 — pre-fix loader 도 이미 absent key 를 생략했으므로.
  그래도 optional 필드 contract 를 pin 하려고 **유지**한다.)
- 수정 후 gate: `npm test` **125 files / 2951 tests, 0 failures**;
  `tsc --noEmit` 0 errors; `eslint` 0 errors (무관 파일 `src/input/keyboard.ts` 의
  pre-existing warning 1건만 남음)
- 밸런스 (`npm run balance`, 100 runs/mission) BEFORE vs AFTER: **정확히 한 cell 만**
  이동 — **grade-5 `mean-HP-end` 5.6 → 5.7** (+0.1 HP). 승률(g1 100.0% / g2 88.8% /
  g3 73.0% / g4 47.4% / g5 42.4% / g6 0.0%), stall-rate, mean-turns, p5/p95 는 **어느
  grade 에서도** 이동 없음. 수정 후 하네스를 **재실행**해 **동일 출력**을 확인 —
  **deterministic 이며 noise 가 아니다.**
- 밸런스 이동의 원인 (추측이 아니라 **실측 확인**): `enemyShouldUseSkill` 이 스킬이
  없으면 `aggression` 을 읽기 **전에** `false` 를 반환한다 (`ice_ai.ts:109-111`). band
  의 non-`standard` 15 slot 중 **13 slot** 은 스킬이 없어 **구조적으로immune** 하고,
  non-`standard` 이면서 스킬을 carry 하는 band ICE 는 **`loa_entity`** (g5, aggressive,
  스킬 2개) 와 **`aleph`** (g6, boss, 스킬 3개) **2종뿐**이다. 하네스 실 encounter
  probe 결과 g5 의 9개 mission 중 **`final_choice` 하나만** `loa_entity` 를 만나고
  (나머지 8개는 스킬 없는 `hellhound` / `neuromancer`), **움직인 유일한 grade-5 cell =
  `final_choice` 의 `loa_entity`** — 정확히 일치한다. g6 의 `aleph` 는 3.3배 더 자주
  발사하지만 g6 band 가 이미 **0.0% 승률 바닥** 이라 어떤 숫자도 움직이지 않는다.
  **이 변경이 가장 세게 bite 하는 곳은 g6 인데 하네스가 그걸 price 할 수 없다.**

**Notes**:

- **diff 는 append-only 다.** `web/src/core/data_loaders.ts` +29 LOC,
  `web/tests/data_loaders.test.ts` +69 LOC. 기존 assertion 은 하나도 약화되지 않았고,
  수정된 파일은 이 둘뿐이다.
- **ADR-0220 은 수정하지 않았다.** 0220 은 Accepted 이므로 immutable 이고 (`AGENTS.md`
  §6), 이 gap 은 신규 ADR 로 분리했다. 0220 의 「후속 항목 (1)」 이 이 ADR 로 이어진다.
- **`coerceAggression` (`ice_ai.ts:62`) 는 변경하지 않았다.** loader 가 저장 데이터의
  정합성을 책임지고, `coerceAggression` 는 runtime combatant 용 legacy guard 로 남는다.
- `web/src/core/ice_ai.ts`, `web/src/core/state_actions_combat.ts`,
  `web/src/core/types.ts`, `web/src/core/ice_scaling.ts`, `web/src/data/ice_types.json`,
  `web/scripts/balance_harness.ts`, `web/scripts/balance_sim.ts` 는 **모두 미변경**이다.
- `state_actions_combat.ts:196-197` 의 boss phase-4 Drone minion hardcode 는
  **미변경**이다 (합성 combatant, catalog 데이터 아님 — 「후속 항목 (3)」).

## 영향 받는 항목

### 이번 결정으로 변경된 항목

- `web/src/core/data_loaders.ts` — `parseIce` 가 `aggression` 을 복사 + 검증
  (+`VALID_ICE_AGGRESSION`, `LegacyIce.aggression`)
- `web/tests/data_loaders.test.ts` — `describe("data_loaders: ICE aggression")` 블록 추가
  (테스트 4건)

### 이번 결정으로 변경되지 않은 항목

- `web/src/core/ice_ai.ts` — `coerceAggression`, `AGGRESSION_PROBABILITY`,
  `enemyShouldUseSkill`
- `web/src/core/types.ts` — `Ice.aggression` / `Ice.personality` 선언 (이미 존재)
- `web/src/core/state_actions_combat.ts` — enemy combat path, boss phase-4 Drone minion
- `web/src/core/ice_scaling.ts` — `ENCOUNTER_ICE_BY_GRADE` (encounter band 구성)
- `web/src/data/ice_types.json` — authored aggression / personality 데이터 (변경 없음)
- `web/scripts/balance_harness.ts`, `web/scripts/balance_sim.ts` — 밸런스 하네스
  (변경 없음)

### 후속 항목 (이번 ADR 범위 밖)

- `web/src/core/ice_ai.ts` — `enemyShouldUseSkill` 의 스킬 short-circuit (스킬 없는
  53 catalog ICE 가 aggression 을 발현할 수 없음) — 「후속 항목 (1)」
- `web/src/core/ice_scaling.ts` — encounter band 커버리지 확대 (24 slot 중 2 slot 만
  스킬 보유) — 「후속 항목 (2)」
- `web/src/data/ice_types.json` — `passive` tier ICE 추가 (선언은 되어 있으나 데이터
  없음) — 「후속 항목 (4)」

## 관련 결정

- ADR-0148 (aggression tiers) — `AGGRESSION_PROBABILITY` 의 owner
- ADR-0161 (personality archetypes) — `PERSONALITY_SKILL_PREFERENCE` 와 archetype
  정의의 owner
- ADR-0216 (derived ICE skill metadata) — **선례 (precedent)**. `parseIce` 가 `skills` 를
  조용히 drop 하던 것을 loader-side derivation 으로 고친 ADR. 결함 계열의 **첫 번째**
  instance
- ADR-0219 (non-damaging ICE 스킬 효과) — Option B. 이 gap 이 **발견된** 자리이며,
  후속 항목으로 기록되어 있다
- ADR-0220 (`parseIce` 가 authored `personality` 을 복원한다) — 결함 계열의 **두 번째**
  instance. 본 ADR 은 그 「후속 항목 (1)」 을 구현한다

## 변경 이력

- 2026-10-27: Draft 작성 + Accepted (Option 2 — `aggression` 복원 + malformed 값은
  throw) — 구현 완료·검증. Consequences / Implementation Status 채움. ADR-0220 의
  후속 항목 (1) 을 이 ADR 로 분리.

# ADR-0343: 교정할 대상이 아니었다 — 드롭 테이블은 이미 단조다

**상태**: Accepted (오너: *"교정해줘"* — 드롭 테이블 비단조성)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (경제 · 진행)

## 컨텍스트 (Context)

ADR-0342 의 후속으로 "재료 산출이 등급에 대해 비단조(g4 df 9 < g3 df 14, g5 df 85 급증)"를 교정하려
했다. 등급별 산출(8런, 40시드, earned-only):

| | g1 | g2 | g3 | g4 | g5 | g6 |
|---|---|---|---|---|---|---|
| data_fragment | 5 | 10 | 13 | **10** | **87** | 44 |
| ice_shard | **12** | **4** | 38 | 74 | 52 | 16 |
| combat_module | 0 | 0 | 1 | 3 | 42 | 24 |
| construct_shard | 0 | 0 | 0 | 1 | 28 | 16 |

## 측정 (Measurement) — 원인은 테이블이 아니다

**ICE `loot_table` 을 직접 집계**했다(ICE별 기대 산출 = Σ chance × quantity):

| tier | ICE 수 | ICE당 기대 산출 |
|---|---|---|
| 1 | 10 | 0.85 |
| 2 | 26 | 1.27 |
| 3 | 25 | 2.69 |
| 4 | 19 | 3.01 |
| 5 | 13 | 4.14 |
| 6 | 4 | 6.65 |

**테이블은 tier에 대해 단조 증가한다.** 이상치(>3× 평균)도, 빈 loot 도 없다. (참고: `skill_defs` 키는
ICE가 아니며 로더가 정상 스킵한다 — ADR-0219.)

그러므로 **등급별 비단조는 드롭 테이블이 아니라 미션 구성** — 어떤 등급의 미션이 어떤 ICE 를 몇 번
만나는지 — 에서 온다. g5 의 급증은 g5 미션이 `neuromancer`(df 5/kill) 같은 고부가 ICE 를 만나기 때문이고,
g6<g5 는 g6 미션이 3개뿐이고 만나는 횟수가 적기 때문이다.

## 결정 (Decision)

**드롭 테이블을 고치지 않는다 — 고칠 대상이 아니다.** 대신 그 성질을 **모니터링하고 가드**한다.

1. `crafting_probe.ts`: **yield ramp** 줄을 추가 — 등급별 재료 산출이 단조인지 표시(`ok` / `BREAK g3->g4,…`).
   난이도 곡선의 MISS 처럼 **신호**로 읽는다.
2. `recipes_data.test.ts`: **ICE loot 이 tier에 대해 단조**임을 강제하는 테스트 추가(테이블 편집이 이 성질을
   깨면 실패). 태생적으로 구성에서 오는 등급별 wobble 은 테스트 대상이 아니다.

## 결과 (Consequences)

- **잘못된 교정을 막았다**: 테이블을 평탄화/증폭하면 디자인(보스급 ICE 가 df/cm/cs 를 준다)을 해치고,
  ADR-0342 의 비용 조정을 다시 무효화한다.
- **신호는 보인다**: `npm run crafting` 이 이제 `BREAK g1->g2, g3->g4, g5->g6` 를 명시 → 구성 기반
  wobble 을 매 실행마다 볼 수 있다.
- **회귀 가드**: 테이블 단조성이 테스트로 고정(`recipes_data.test.ts`, 9 tests).
- **남은 것(미션 디자인 소관)**: 등급별 wobble 을 실제로 고치려면 **미션 ICE 구성**(등급별 로스터·만남
  횟수)을 손대야 한다 — 테이블이 아니라 미션 데이터. 오너/콘텐츠 결정.
- 검증: vitest **236/4446** · typecheck 0 · 러틴 9/9.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented (모니터 + 가드; 데이터 무변경)

**Evidence**:
- `web/scripts/crafting_probe.ts` — yield ramp 모니터
- `web/tests/recipes_data.test.ts` — "ICE loot rises by tier" 테스트
- 측정: tier별 ICE당 0.85→1.27→2.69→3.01→4.14→6.65 (단조)

**Notes**: 등급별 wobble 은 구성 소관. 실제 교정은 미션 로스터 편집이며 미션 디자인 결정이다.

## 영향 받는 항목

- `web/scripts/crafting_probe.ts` · `web/tests/recipes_data.test.ts`

## 관련 결정

- ADR-0342 (probe 실지갑화 + T2/T3 비용) · ADR-0292 (드롭은 ICE 급에 걸맞다) · ADR-0219 (skill_defs)

## 변경 이력

- 2026-11-22: Accepted (테이블 단조성 확인 → 교정 대신 모니터·가드)

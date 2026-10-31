# ADR-0242: ICE 아키타입 알람 배율 배선 — `getAlarmMultiplier` 만, `shouldTargetAlly` 는 연기 (X2)

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — 2026-10-31 결정 (ADR-0238 추천 번들 채택)
**우선순위**: P2 (The Flatline — 밸런스 접촉, ADR-0229 §A1 대상. **ADR-0238 분할 4건 중 하나, ADR-0240 에 의존**)
**관련**: [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [ADR-0240 — 유휴 압력 + 알람 누적 루프](./0240-idle-pressure-and-alarm-loop.md) · [ADR-0239 — VFX spawn 의 RNG 결합 해소](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0161 — ICE Personality Archetypes](./0161-ice-personality-archetypes.md) · [ADR-0228 — ICE 아키타입 동작 배선](./0228-ice-archetype-behavior-wiring.md) · [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **이 ADR 은 ADR-0238 의 분할 결과다.** ADR-0238 의 **X2** 절과 §사용자 결정
> (2026-10-31) 을 구현 단위로 옮긴다.
>
> **구현은 시작하지 않았다.** 이 ADR 작성 중 `web/` 아래 파일은 수정·실행하지
> 않았다.
>
> **의존 순서**: [ADR-0240](./0240-idle-pressure-and-alarm-loop.md) (P7 + X1) 이
> **먼저**다. 이 ADR 이 거는 배율의 대상 — `tickAlarm` 의 알람 누적 루프 — 는 ADR-0240
> 이 배선하기 전까지 존재하지 않는다.

## 컨텍스트 (Context)

### 문제 — ADR-0161 의 네 아키타입 동작 중 둘이 문서상 동작이다 (트리아지 X2)

트리아지 §1.3 X2: "ICE archetype `getAlarmMultiplier` / `shouldTargetAlly` 배선
(U9, ADR-0161) — ❌ not started — (현 상태) `web/src/core/combat/ice_ai.ts:333`,
`:364` 정의, 호출자 0건 — 밸런스 접촉".

현재 상태 (2026-10-31 작업 트리에서 직접 확인):

- `web/src/core/combat/ice_ai.ts:333` — `export function getAlarmMultiplier(combatant: Combatant): number {`.
  ADR-0238 기록: `stealth` 면 `STEALTH_ALARM_MULTIPLIER` (`0.5`, `ice_ai.ts:316`), 그
  외 1.0.
- `web/src/core/combat/ice_ai.ts:364` — `export function shouldTargetAlly(`. ADR-0238
  기록: `support` 이고 HP 70% 미만 아군이 있으면 참.
- 둘 다 `web/src/` 안 호출자 0건 (ADR-0238 grep). `ice_crit.ts:12-15` 주석이 두 미배선
  사유를 적고 있다.
- **이름이 같은 다른 함수 주의**: `web/src/core/state/run_mutators.ts:183` 의
  `getAlarmMultiplier(state: MutableRunState)` 는 run mutator 용이며 **이 ADR 의 대상이
  아니다** (ADR-0238 기록, 2026-10-31 재확인).

ADR-0228 의 판정: 둘 다 "미배선, 서브시스템 필요" —

- `getAlarmMultiplier` 는 걸 **알람 누적 루프가 없다** → ADR-0240 이 해소한다.
- `shouldTargetAlly` 는 enemy 경로에 **per-target 스킬 해석이 없다** (roster 의 모든
  ICE 가 플레이어 한 명을 공격) → multi-ICE 대상 모델이 필요하다.

### 두 함수의 비용이 매우 다르다

ADR-0238 X2 트레이드오프: "두 함수의 비용이 매우 다르므로 (국소 배선 vs 시스템
구축) 한 결정으로 묶을 이유가 약하다." `getAlarmMultiplier` 는 ADR-0240 의 루프 위에
걸리는 **국소 배선**이다 — `tickAlarm` 의 `iceAlarmSpeed` 인자
(`combat_engine.ts:202`) 가 이미 그 자리다. `shouldTargetAlly` 는 **새 서브시스템**
(대상 모델 + 대상 지정 효과 경로) 이다.

## 사용자 결정 (Decision)

**2026-10-31, 프로젝트 오너 직접 결정** (ADR-0238 §사용자 결정 그대로).

- [x] **X2-3 변형 채택 — `getAlarmMultiplier` 만 배선한다.** `ice_ai.ts:333` 의 반환값을
  ADR-0240 이 배선한 `tickAlarm` 의 `iceAlarmSpeed` 인자로 넘긴다.
- [x] **`shouldTargetAlly` (`ice_ai.ts:364`) 는 🟢 Deferred** — multi-ICE 대상 모델이
  필요하므로 별도 ADR 로 미룬다.
- [x] **X2-5 — 단독 ADR 로 분리, ADR-0240 이후** (이 문서).
- 채택하지 않은 것: X2-1 현상 유지, X2-2 둘 다 배선 (서브시스템 둘 — 가장 큰 범위),
  X2-4 폐기 (ADR-0161 범위 축소 새 ADR 필요).

### 채택 이유

1. **국소 배선과 시스템 구축을 분리한다** — `getAlarmMultiplier` 는 ADR-0240 루프 위의
   한 지점이고, `shouldTargetAlly` 는 대상 모델 전체를 요구한다 (ADR-0238 X2 추천).
2. **같은 논리의 선례** — 트리아지 §2.1 이 P2 의 `counter`/`lifesteal` 을 "스킬 시스템
   ADR 이 먼저" 로 미룬 것과 같은 논리로 `shouldTargetAlly` 를 미룬다 (ADR-0238 X2
   추천).
3. **ADR-0161 범위는 줄이지 않는다** — 폐기 (X2-4) 가 아니라 연기이므로 ADR-0161 은
   그대로 유효하고, 범위 축소 ADR 이 필요 없다.

### 🟢 Deferred 항목의 재개 조건

`shouldTargetAlly` 는 다음이 생길 때 재개한다 (ADR-0228 판정 기준):

- enemy 경로의 **per-target 스킬 해석** (ICE 가 플레이어 외 대상을 고를 수 있는 구조)
- multi-ICE 전투의 **대상 모델**과 대상 지정 효과 (heal / buff) 적용 경로

이를 다루는 별도 ADR 이 작성되기 전까지 `shouldTargetAlly` 는 정의만 유지한다.

## 수락 증거 (Acceptance evidence)

- **선행 조건**: ADR-0240 의 알람 루프가 배선되고 그 §A1 표가 기록된 상태. 이 ADR 의
  측정은 **ADR-0240 구현 후의 곡선**을 "전" 값으로 삼는다 (두 변경의 drift 가 섞이지
  않도록).
- **기준선 계보**: [ADR-0239](./0239-vfx-spawn-rng-decoupling.md) §재기준화 결과
  (opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 /
  83.0 / 44.4 / 24.7`) → ADR-0240 이 re-baseline 하면 그 값.
- **측정**: `cd web && npm run balance` + `npm run balance -- --deck ppl`, 구현 전·후,
  6 grade 전부. 판정은 ADR-0229 §A1/§A2/§B1/§B2/§C2.
- **주목할 grade (가설 — 실측 전 단정 금지)**: ADR-0228 실측대로 band 에 `stealth`
  ICE 가 있다 (g1 slot 2 `wisp`, g3 slot 3 `ice_dixie_echo`). g1 · g3 의 이동을 특히
  볼 것 (ADR-0238 X2 수락 증거).
- **테스트**: `stealth` 배율이 알람 간격에 반영되는 단위 테스트 (`stealth` ICE 가 있을
  때 tick 간격이 `ALARM_TICK_INTERVAL_MS / 0.5` 로 늘어남 — 기존 `tickAlarm` 식에서의
  추론). `run_mutators.ts:183` 의 동명 함수와 혼동되지 않는 import 확인.

## 결과 (Consequences)

**2026-10-31 결정 기준.** 아직 구현 전이므로, 아래는 결정이 확정한 것과 예상이다.

### 결정이 확정한 것

- **`stealth` ICE 는 알람을 느리게 올린다** — ADR-0161 의 `stealth` 아키타입 동작이
  살아난다.
- **`support` ICE 의 아군 대상 지정은 연기** — `shouldTargetAlly` 는 🟢 Deferred.
  ADR-0161 의 네 동작 중 하나는 계속 정의만 남는다.
- **이 ADR 은 ADR-0240 없이는 구현할 수 없다.**

### 긍정적 영향

- `tickAlarm` 의 `iceAlarmSpeed` 인자가 처음으로 1.0 이 아닌 값을 받게 된다 —
  인자가 원래 의도대로 쓰인다.
- 아키타입 다양성이 알람 경제로 드러난다 (Pillar 5 variety).

### 부정적 영향 / 수용한 비용

- **밸런스 이동** — `stealth` ICE 가 있는 grade 에서 알람 상승이 느려지면 ADR-0240 의
  "알람 = 적 피해·공격성" 효과가 약해진다 → 그 grade 의 승률이 오를 수 있다 (가설).
- **ADR-0161 미완결** — `shouldTargetAlly` 연기로 아키타입 동작 4 중 1 이 남는다.
- **`stealth` ICE 스킬 문제 미해결** — ADR-0228 이 지적한 "catalog 의 `stealth` ICE
  5 종이 모두 `skills: []`" 는 이 ADR 이 다루지 않는다 (ADR-0240 Open questions (e)).

### 후속 항목

1. ADR-0240 구현 완료 대기.
2. 구현: `getAlarmMultiplier` → `iceAlarmSpeed` 배선 + 단위 테스트 → §A1 전후 표.
3. `ice_crit.ts:12-15` 의 "not wired" 주석을 `getAlarmMultiplier` 에 한해 갱신.
4. `shouldTargetAlly` 는 대상 모델 ADR 이 생길 때 재개.

## Implementation Status (2026-10-31)

**Status**: ❌ Not started

**Evidence**:
- `web/src/core/combat/ice_ai.ts:333` — `getAlarmMultiplier(combatant)` 정의, 호출자 0건 (배선 대상)
- `web/src/core/combat/ice_ai.ts:316` — `STEALTH_ALARM_MULTIPLIER = 0.5`
- `web/src/core/combat/ice_ai.ts:364` — `shouldTargetAlly` 정의, 호출자 0건 (🟢 Deferred)
- `web/src/core/combat/combat_engine.ts:202` — `tickAlarm` 의 `iceAlarmSpeed` 인자 (배율이 들어갈 자리, ADR-0240 이 먼저 배선)
- `web/src/core/combat/ice_crit.ts:12-15` — 두 함수의 "not wired" 주석
- `web/src/core/state/run_mutators.ts:183` — 동명의 다른 함수 (run mutator 용, 대상 아님)

**Notes**: 배선 범위는 `getAlarmMultiplier` 하나다 — `shouldTargetAlly` 는 이 ADR 의
결정으로 🟢 **Deferred** 이며 이 Status 에 포함되지 않는다 (§사용자 결정 「재개
조건」). `ice_ai.ts:333` · `:364`, `combat_engine.ts:202`, `run_mutators.ts:183` 은
2026-10-31 작업 트리에서 직접 확인했다. `ice_ai.ts:316` · `ice_crit.ts:12-15` 는
ADR-0238 Evidence (HEAD `0217c0a`) 인용이다. 구현 없음 — 테스트 수 · 승률은 측정하지
않았다.

## Open questions

> 문자 표기: (e) 는 ADR-0238 의 문자를 그대로 썼다. 새 질문은 ADR-0238 의 (a)–(h) 와
> 겹치지 않도록 (i) 부터 붙였다.

- **(e) `stealth` ICE 스킬** — ADR-0240 에 이월된 질문과 같다. 배율이 알람 간격을
  바꾸는 것만으로 `stealth` 동작이 플레이에서 관측 가능한가, 아니면 catalog 에 스킬을
  저술해야 하는가? 결론은 ADR-0240 에서 내고 이 ADR 이 따른다.
- **(i) 다수 ICE 의 배율 합성** — multi-ICE 전투 (ADR-0152) 에서 roster 에 `stealth`
  와 비-`stealth` ICE 가 섞이면 `iceAlarmSpeed` 는 무엇인가 (최소값 / 곱 / 평균 /
  살아 있는 ICE 기준)? `stealth` ICE 가 쓰러지면 배율이 즉시 바뀌는가?
- **(j) run mutator 배율과의 관계** — `run_mutators.ts:183` 의 run 단위 알람 배율과
  ICE 배율이 함께 적용될 때의 합성 규칙은? (두 함수는 대상이 다르지만 둘 다 "알람
  속도" 를 말한다.)

## 영향 받는 항목

### 이 결정으로 변경된 항목

- `docs/wiki/decisions/0242-ice-archetype-alarm-multiplier.md` — **신규** (이 ADR)
- `docs/wiki/decisions/0238-balance-and-input-decision-request.md` — 상태 → Superseded
- `docs/wiki/decisions/README.md` — 인덱스 행 추가

### 구현 시 변경될 항목 (예정)

- ADR-0240 이 만든 `tickAlarm` 호출 지점 — `iceAlarmSpeed` 에 `getAlarmMultiplier` 결과 전달
- `web/src/core/combat/ice_crit.ts` — 주석 갱신
- `web/tests/` — `stealth` 배율 단위 테스트

### 변경되지 않는 항목

- `web/` 전체 — 이 ADR 작성 시 **미수정**
- `shouldTargetAlly` — 🟢 Deferred, 정의 유지
- `run_mutators.ts` 의 동명 함수
- Accepted ADR 본문 (0161 / 0228 / 0229 / 0239) — immutable

## 관련 결정

- ADR-0238 — 이 ADR 의 원 결정 요청 (X2 절, §사용자 결정, §결과). 이 ADR 로 대체됨.
- ADR-0240 — 알람 누적 루프. **이 ADR 의 선행 조건.**
- ADR-0161 — 두 동작의 원 정의. 이 ADR 은 범위를 줄이지 않는다 (연기일 뿐).
- ADR-0228 — "미배선, 서브시스템 필요" 판정의 owner, `stealth` band 실측.
- ADR-0229 — drift policy (수락 기준). 그 후속 항목 5 가 "`shouldTargetAlly` /
  `getAlarmMultiplier` 는 곡선을 움직일 수 있으므로 구현 시 §A1 을 반드시 적용" 이라고
  적었다 (ADR-0238 인용).
- ADR-0239 — 현재 기준선의 보유자.
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  §1.3 X2, §2.1, §3 5단계.

## 변경 이력

- 2026-10-31: 작성 — ADR-0238 분할 (X2). **Accepted** (오너 결정: X2-3
  `getAlarmMultiplier` 만 · `shouldTargetAlly` 🟢 Deferred · X2-5 단독 ADR, ADR-0240
  이후). Implementation Status ❌ Not started. 구현 없음.

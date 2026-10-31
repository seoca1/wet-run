# ADR-0241: `critical_hit` VFX 를 실제 치명타 판정 `isCrit` 에 연동한다 (P8)

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — 2026-10-31 결정 (ADR-0238 추천 번들 채택)
**우선순위**: P2 (The Flatline — 표시를 판정에 맞추는 변경, ADR-0229 §A1 대상. **ADR-0238 분할 4건 중 하나, 다른 분할과 독립**)
**관련**: [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [ADR-0239 — VFX spawn 의 RNG 결합 해소](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [ADR-0231 — Combat-feel top-3](./0231-combat-feel-top3-vfx-log-raf.md) · [ADR-0018 — Combat Animation](./0018-combat-animation.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **이 ADR 은 ADR-0238 의 분할 결과다.** ADR-0238 의 **P8** 절과 §사용자 결정
> (2026-10-31) 을 구현 단위로 옮긴다.
>
> **구현은 시작하지 않았다.** 이 ADR 작성 중 `web/` 아래 파일은 수정·실행하지
> 않았다.
>
> **의존 순서**: 다른 분할 ADR (0240 / 0242 / 0243) 과 **독립**이다. 언제든 진행할
> 수 있다. 단 [ADR-0239](./0239-vfx-spawn-rng-decoupling.md) 의 VFX id 전환
> (`c488b6d`) 이 **선행 완료**됐다는 사실에 기댄다 (아래 §컨텍스트).

## 컨텍스트 (Context)

### 문제 — "CRIT" 표시가 진짜 치명타와 무관하다 (트리아지 P8)

트리아지 §1.2 P8: "`critical_hit` 임계값을 실제 crit 과 연동 — ❌ not started —
(현 상태) `web/src/core/combat/state_actions_programs.ts:235` 에 여전히 `damage >= 10`
하드코딩 — **밸런스 접촉** — ADR-0229 §A1".

현재 상태 (2026-10-31 작업 트리에서 직접 확인):

- `web/src/core/combat/state_actions_programs.ts:235` — `...(damage >= 10` 조건.
  ADR-0238 기록상 이어지는 `:237` 이 `import_vfx_ms("critical_hit", …)` spawn 이다.
- `web/src/core/combat/state_actions_programs.ts:102` —
  `const dmgResult = calculateDamage(damageCtx);` — `useProgram` 은 **이미** 실제 판정
  결과를 받는다.
- 실제 치명타 판정은 `calculateDamage` 안에 있다 (`CRIT_CHANCE = 0.15`,
  `CRIT_MULTIPLIER = 2.0` — `combat_engine.ts:14-15`; 결과 `DamageResult.isCrit` —
  `combat_engine.ts:111-113`, ADR-0238 인용).
- 그러나 VFX 조건은 `isCrit` 를 보지 않는다. Combat-feel 제안서의 표현: "플레이어 진짜
  crit 이 나도 VFX crit 이 안 뜰 수 있다" (ADR-0238 인용). 반대로 티어가 높아 기본
  데미지가 10 이상이면 치명타가 아니어도 매번 "CRIT" 가 뜬다.

### 왜 이것이 "밸런스 접촉" 이었고, 왜 이제는 싸졌는가

ADR-0238 작성 시점에는 `import_vfx_ms` 가 인스턴스 id 를 `Math.random()` 으로
뽑았다. 그래서 spawn **조건**을 바꾸면 하네스의 PRNG 흐름이 밀려 이후의 crit · proc ·
적 스킬 draw 가 달라졌다. ADR-0238 의 반증 실측 (`c488b6d` **이전**) 은 `critical_hit`
spawn 한 줄을 바꾸는 것만으로 opening g3 **−2.0pp**, PPL g6 **−3.0pp** 를 기록했다.

[ADR-0239](./0239-vfx-spawn-rng-decoupling.md) (`c488b6d`) 가 이 결합을 끊었다 —
`import_vfx` / `import_vfx_ms` 의 id 가 `deterministicVfxId` 기반이 되어 **모든 VFX
spawn 이 `Math.random` draw 를 소비하지 않는다** (ADR-0239 Implementation Status:
"draw 0"). 따라서 spawn 조건을 바꿔도 스트림이 밀리지 않는다. ADR-0238 §결과의
기록: "**P8 은 이제 저렴하다** — `c488b6d` 로 모든 VFX spawn 이 RNG 무소비가 되어
`isCrit` 연동이 밸런스를 밀지 않는다 (0.0pp 기대)."

## 사용자 결정 (Decision)

**2026-10-31, 프로젝트 오너 직접 결정** (ADR-0238 §사용자 결정 그대로).

- [x] **P8-2 채택 — `dmgResult.isCrit` 가 참일 때만 `critical_hit` 을 spawn 한다.**
  하드코딩 `damage >= 10` (`state_actions_programs.ts:235`) 을 대체한다.
- [x] **P8-4 — 단독 ADR 로 분리** (이 문서).
- 채택하지 않은 것: P8-1 현상 유지, P8-3 상대 비율 임계 (`damage >= maxHp * 0.15` —
  여전히 진짜 치명타와 무관해 문제의 절반만 푼다). P8-5 draw 수 보존은 ADR-0239 이후
  "보존할 draw" 가 없어 **무의미**해져 기각됐다 (ADR-0238 P8 표).

### 채택 이유

1. **판정을 바꾸는 게 아니라 표시를 판정에 맞추는 변경이다** (ADR-0238 P8 추천).
   데미지 계산 자체는 바뀌지 않는다.
2. **필요한 값이 이미 손에 있다** — `dmgResult` 가 `:102` 에서 이미 계산된다. 새
   계산 경로가 필요 없다.
3. **RNG 비용이 사라졌다** — ADR-0239 (`c488b6d`) 이후 spawn 은 draw 를 소비하지
   않으므로, ADR-0238 이 우려한 −2.0pp / −3.0pp drift 경로가 없다.
4. **범위가 작다** — 트리아지 §3 5단계가 P8 을 단독으로 권한 이유와 같다. 측정과
   리뷰가 쉽다.

## 수락 증거 (Acceptance evidence)

- **비교 기준선**: [ADR-0239](./0239-vfx-spawn-rng-decoupling.md) §재기준화 결과의
  **새 기준선** — opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 /
  79.1 / 98.9 / 83.0 / 44.4 / 24.7`.
- **기대 (가설)**: 6 grade 전부 **0.0pp** (opening · PPL 모두). 근거는 위
  §컨텍스트의 ADR-0239 draw-0 불변식이다. 이것은 실측 전 **예상**이다.
- **측정**: `cd web && npm run balance` + `npm run balance -- --deck ppl`, 구현 전·후.
  **0.0pp 가 아니면 그 자체가 조사 대상이다** — draw-0 불변식이 깨졌다는 뜻이므로
  §A1/§A2 판정에 앞서 원인을 기록한다.
- **RNG 기계 검증**: ADR-0239 가 추가한 `web/tests/vfx_rng_neutrality.test.ts` 의
  0-draw 불변식이 계속 통과해야 한다.
- **테스트** (ADR-0238 이 적은 것): `web/tests/combat_engine.test.ts` 와 crit spawn
  조건 테스트 (치명타 → spawn, 비치명타 고데미지 → spawn 없음). Combat-feel 제안서가
  지목한 `web/tests/design_conformance.test.ts` 의 crit 상수 assertion 유지.

## 결과 (Consequences)

**2026-10-31 결정 기준.** 아직 구현 전이므로, 아래는 결정이 확정한 것과 예상이다.

### 결정이 확정한 것

- **"CRIT" 표시 = 실제 치명타** — `critical_hit` VFX 의 유일한 조건은 `isCrit` 다.
- **데미지 · 치명타 확률 · 배율은 불변** — `CRIT_CHANCE` · `CRIT_MULTIPLIER` 를
  건드리지 않는다.
- **ADR-0238 의 P8 실측 표는 역사적 값이다** — 그 표는 `c488b6d` 이전의 스트림을
  측정한 것이므로 이 ADR 의 기대치 근거가 아니다.

### 긍정적 영향

- 티어마다 "CRIT" 빈도가 달라지던 문제 (Combat-feel 제안서 U6) 가 사라진다.
- 표시가 실제 판정을 반영하므로, 이후 치명타 한정 flash (트리아지 X5) 같은 연출이
  기댈 수 있는 신호가 생긴다.

### 부정적 영향 / 수용한 비용

- **체감 빈도 변화** — 고티어에서 매번 뜨던 "CRIT" 가 약 15% 확률로 줄어든다 (가설 —
  `CRIT_CHANCE = 0.15` 에서의 추론, 실측 아님). 플레이어가 이를 "연출 감소" 로 느낄 수
  있다.
- **동반 임계 미해결** — 같은 하드코딩 패턴이 `multi_hit` 선택에도 남는다
  (Open questions (i)). 이 ADR 은 그것을 바꾸지 않는다.

### 후속 항목

1. 구현: `:235` 조건을 `dmgResult.isCrit` 로 교체 + spawn 조건 테스트.
2. 측정: 양 덱 6 grade 전후 표를 이 ADR 에 기록 (0.0pp 기대).
3. `docs/design/systems/animations.md` 의 `critical_hit` 조건 기술 갱신
   (`AGENTS.md` §3.2 단계 3).

## Implementation Status (2026-10-31)

**Status**: ✅ Implemented (`2db4dfe`)

**Evidence**:
- ✅ `web/src/core/combat/state_actions_programs.ts:235` — `damage >= 10` → **`dmgResult.isCrit`** (교체 완료)
- ✅ `web/tests/crit_vfx_link.test.ts` — 신규 4 테스트 (crit → spawn · 비-crit ≥10 → 미spawn · 구 임계 미만 crit → spawn · crit roll 20개 스윕으로 경계 pin). 구 조건을 **일시 복원해 4중 3개가 실패**함을 확인
- ✅ `web/tests/vfx_rng_neutrality.test.ts` — 5-VFX 시나리오를 **tier-2 crit** 로 조정 (기존엔 "15뎀 **비-crit** 이 critical_hit 을 spawn 함"에 의존했다). pin 된 draw 예산 5 → 6 (치명타 배수 draw 는 데미지 롤 소속, VFX 아님)
- ✅ **§A1 실측 = 0.0pp** — opening `100.0/88.3/70.5/39.5/36.2/0.0` · PPL `100.0/79.1/98.9/83.0/44.4/24.7`, mean turns · ending HP 동일 → **Open question (j) 는 발생하지 않음**
- ✅ 조건 변경이 RNG 를 밀지 않음을 실증 — ADR-0239 의 draw-0 성질이 실제로 작동
- ❌ `web/src/core/state/state_helpers.ts:150` (`pickProgramVfxKind`) — **(i) 로 남김, 미변경**. 결과: burst crit 이 `heavy_attack` 과 `critical_hit` 을 함께 표시할 수 있다
- ❌ `web/src/core/combat/combat_engine.ts:14-15` · `:111-113` — 치명타 상수 · 판정 **불변**

**Notes**: `:235` · `:102` 는 2026-10-31 작업 트리에서 직접 확인했다. `:237` ·
`combat_engine.ts:14-15` · `:111-113` 은 ADR-0238 Evidence (HEAD `0217c0a`) 인용이고,
`state_helpers.ts:47` 의 현재 동작은 ADR-0239 Implementation Status 인용이다. 구현
없음 — 테스트 수 · 승률은 측정하지 않았다.

## Open questions

> 문자 표기: ADR-0238 의 (a)–(h) 와 겹치지 않도록 새 질문은 (i) 부터 붙였다.

- **(i) 동반 하드코딩 임계** — `web/src/core/state/state_helpers.ts:150` (2026-10-31
  작업 트리; ADR-0238 기록 시점 `:139`) 의 `program.role === "burst" && damage >= 10`
  이 `multi_hit` VFX 선택에 같은 임계를 쓴다 (ADR-0238 Implementation Status Notes 의
  동반 발견). 이 ADR 범위에 넣을 것인가, 별도로 둘 것인가? `multi_hit` 는 치명타가
  아니라 burst 연출이므로 `isCrit` 가 맞는 신호인지부터 판단이 필요하다.
- **(j) 0.0pp 가 아닐 경우** — 기대와 달리 drift 가 나오면, draw-0 불변식
  (ADR-0239) 의 구멍으로 보고 ADR-0239 쪽 조사로 넘길 것인가, 이 ADR 에서 §A1 판정으로
  닫을 것인가?

## 영향 받는 항목

### 이 결정으로 변경된 항목

- `docs/wiki/decisions/0241-crit-vfx-isCrit-link.md` — **신규** (이 ADR)
- `docs/wiki/decisions/0238-balance-and-input-decision-request.md` — 상태 → Superseded
- `docs/wiki/decisions/README.md` — 인덱스 행 추가

### 구현 시 변경될 항목 (예정)

- `web/src/core/combat/state_actions_programs.ts` — `:235` 조건
- `web/tests/` — crit spawn 조건 테스트
- `docs/design/systems/animations.md`

### 변경되지 않는 항목

- `web/` 전체 — 이 ADR 작성 시 **미수정**
- `combat_engine.ts` 의 치명타 상수 · `calculateDamage` — 게임플레이 판정 불변
- Accepted ADR 본문 (0018 / 0229 / 0231 / 0239) — immutable

## 관련 결정

- ADR-0238 — 이 ADR 의 원 결정 요청 (P8 절, §사용자 결정, §결과). 이 ADR 로 대체됨.
- ADR-0239 — VFX id 전환 (`c488b6d`). 이 ADR 이 "0.0pp 기대" 를 말할 수 있는 근거이자
  현재 기준선의 보유자.
- ADR-0229 — drift policy §A1–§A3 (수락 기준).
- ADR-0231 — VFX spawn 의 RNG non-neutrality 최초 발견.
- ADR-0018 — `critical_hit` VFX 사양의 상위.
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  §1.2 P8, §2.1, §3 5단계.

## 변경 이력

- 2026-10-31: 작성 — ADR-0238 분할 (P8). **Accepted** (오너 결정: P8-2 `isCrit` 연동 ·
  P8-4 단독 ADR). ADR-0239 (`c488b6d`) 로 drift 우려가 해소되어 0.0pp 기대 (가설).
  Implementation Status ❌ Not started. 구현 없음.

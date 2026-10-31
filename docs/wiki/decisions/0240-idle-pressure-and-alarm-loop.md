# ADR-0240: 유휴 압력 + 알람 누적 루프 — 유휴는 알람을 올리고, 알람은 적을 강하게 한다 (P7 + X1)

**상태**: Accepted
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — 2026-10-31 결정 (ADR-0238 추천 번들 채택)
**우선순위**: P2 (The Flatline — 밸런스 접촉, ADR-0229 §A1 대상. **ADR-0238 분할 4건 중 첫 번째**)
**관련**: [ADR-0238 — 밸런스·입력 결정 요청](./0238-balance-and-input-decision-request.md) · [ADR-0239 — VFX spawn 의 RNG 결합 해소](./0239-vfx-spawn-rng-decoupling.md) · [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md) · [ADR-0228 — ICE 아키타입 동작 배선](./0228-ice-archetype-behavior-wiring.md) · [ADR-0183 — Accessibility](./0183-accessibility.md) · [ADR-0242 — ICE 아키타입 알람 배율 배선](./0242-ice-archetype-alarm-multiplier.md) · [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md)

> **이 ADR 은 ADR-0238 의 분할 결과다.** ADR-0238 이 묶어서 요청한 다섯 결정 중
> **P7 (입력 유휴 시 적 행동)** 과 **X1 (알람 누적 루프 `tickAlarm` 배선)** 을 한
> 서브시스템으로 기록한다. 결정은 ADR-0238 §사용자 결정 (2026-10-31) 에서 이미
> 내려졌고, 이 문서는 그 결정을 구현 단위로 옮긴 것이다.
>
> **구현은 시작하지 않았다.** 이 ADR 작성 중 `web/` 아래 파일은 수정·실행하지
> 않았다. 문서 안의 승률 이동 언급은 전부 **가설**이다.
>
> **의존 순서**: 이 ADR 이 **먼저**다. [ADR-0242](./0242-ice-archetype-alarm-multiplier.md)
> (X2 `getAlarmMultiplier`) 는 이 ADR 이 만드는 알람 루프 위에 걸린다.

## 컨텍스트 (Context)

### 문제 1 — 플레이어가 아무것도 안 하면 적도 아무것도 안 한다 (트리아지 P7)

트리아지 §1.2 P7: "입력 유휴 시 적 행동 (시간 압력) — ❌ not started — **밸런스
접촉** — ADR-0229 §A1 전후 측정 필수". 트리아지는 `file:line` 을 적지 않았고
(`—`), ADR-0238 이 현재 구조를 직접 확인해 기록했다:

- 적 턴 처리 `processEnemyTurns` (`web/src/core/combat/state_actions_combat.ts:139`)
  의 호출자는 `use_program` 분기 안의 한 곳뿐이다 (`:68`).
- 그 안의 `:143` 이 `AUTO_ATTACK_INTERVAL_MS` (`= 2000`,
  `web/src/core/combat/combat_engine.ts:10`) 게이트를 건다.
- 따라서 **프로그램을 쓰지 않으면 적도 행동하지 않는다.** Combat-feel 제안서의
  표현으로는 "플레이어가 아무것도 안 하면 적도 아무것도 안 함. 가짜 idle threat
  없음" (ADR-0238 인용).

### 문제 2 — 알람 루프는 정의만 있고 호출자가 없다 (트리아지 X1)

트리아지 §1.3 X1: "알람 누적 루프 `tickAlarm` 배선 — ❌ not started —
`web/src/core/combat/combat_engine.ts:198` 정의, `web/src/core/combat/ice_crit.ts:12-15`
'not wired' 주석 — 밸런스 접촉. P7 과 묶어 판단".

현재 상태 (2026-10-31 작업 트리에서 직접 확인):

- `web/src/core/combat/combat_engine.ts:198` — `export function tickAlarm(` .
  인자는 `(currentAlarmLevel, lastAlarmTickMs, currentTickMs, iceAlarmSpeed)` 이고
  (ADR-0238 기록), **`iceAlarmSpeed` 인자는 `:202`** 에 있다.
- `combat_engine.ts:204` — 간격은 `ALARM_TICK_INTERVAL_MS / Math.max(0.01, iceAlarmSpeed)`.
- `combat_engine.ts:20-21` — `ALARM_TICK_INTERVAL_MS = 10000`, `ALARM_MAX_LEVEL = 5`.
- 간격이 지나면 레벨을 1 올리고 `TRACE WARNING: alarm level N/5` 메시지를 낸다
  (ADR-0238 기록).
- `web/src/` 안에 `tickAlarm` 호출자는 없다 (ADR-0238 grep; `ice_crit.ts:12-14` 의
  "`tickAlarm`, which has no production caller" 주석).
- ADR-0228 실측: 알람은 두 종류다. `player.alarm` (0–100) 은 프로그램 비용
  누산기이고, `state.alarmLevel` / `lastAlarmTickMs` 는 초기화만 되고 어떤 reducer 도
  쓰지 않는다. HUD 는 `alarmLevel > 0` 일 때 `ALARM N/5` 를 표시하지만
  (`web/src/core/state/state.ts:193-194`) 지금은 0 에서 움직이지 않는다.

### 측정 공백 — 하네스가 유휴를 모델링하지 않는다

ADR-0238 §P7 트레이드오프: `web/scripts/balance_sim.ts` 는 `Date.now` 를 고정
시계로 바꾸고 (`:86-89`) `use_program` 입력만 고른다. 그래서 idle 경로는 **하네스에서
0.0pp 로 보일 수 있고, 그것은 "영향 없음" 의 증거가 아니다.**

### 이 ADR 의 질문

ADR-0238 이 물은 것 — **P7 과 X1 을 살릴 것인가, 어떤 변형으로 살릴 것인가** — 에
대해 오너가 내린 답을 구현 가능한 단위로 고정한다.

## 사용자 결정 (Decision)

**2026-10-31, 프로젝트 오너 직접 결정** (ADR-0238 §사용자 결정 그대로).

- [x] **P7-3 변형 채택 — 유휴 시간은 적 공격이 아니라 알람을 올린다.** 직접 피해형
  (P7-2 — 입력 없이 N 초 → 적이 한 번 공격) 은 채택하지 않는다.
- [x] **X1-2 채택 — 기존 시간 기반 `tickAlarm` 을 배선한다.** 행동 기반 tick
  (X1-3) · 폐기 (X1-4) 는 채택하지 않는다.
- [x] **P7 + X1 을 한 ADR 로** (P7-4 · X1-5) — 이 문서.
- [x] **(b) `alarmLevel` 상승의 결과 = 적 피해 · 공격성 증가.** 이것이 X1 과 P7-3 이
  HUD 숫자만 올리는 장식에 그치지 않게 하는 정의다.
- [x] **(a) 하네스 유휴 모델 — `balance_sim.ts` 에 유휴 단계를 추가한다.** 그래야
  P7 이 ADR-0229 §A1 로 측정 가능해진다.

### 채택 이유

ADR-0238 §P7 · §X1 추천의 근거를 그대로 따른다.

1. **직접 피해형은 원칙과 부딪힌다** — Combat-feel 제안서 R5 가 "플레이어가 시간을
   재는 게임이 아니다" 로 실시간 타이머 UI 를 기각했고, 느린 입력 플레이어에게
   불리해 접근성 (ADR-0183) 비용이 있다 (ADR-0238 P7-2 행).
2. **알람 경유형은 죽은 훅 셋을 한 번에 살린다** — 유휴 압력 (P7), `tickAlarm`
   (X1), 그리고 그 위에 걸리는 `getAlarmMultiplier` (X2 → ADR-0242) 가 하나의
   서브시스템을 공유한다. 이미 있는 함수 · 상수 · HUD 행을 그대로 쓴다 (ADR-0238
   X1-2 행).
3. **결과 정의가 필수였다** — ADR-0238 은 "결과 없는 루프는 HUD 숫자만 올리는
   장식" 이라고 적었다. 오너의 (b) 답이 그 공백을 메운다.
4. **측정 없이 밸런스를 바꾸지 않는다** — (a) 의 하네스 유휴 단계가 없으면 P7 의
   영향을 §A1 로 증명할 수 없다 (ADR-0238 §결과).
5. **깁슨 톤** — 시간이 흐르면 trace 가 좁혀 온다는 구조는 매트릭스 안의 "trace"
   와 맞는다 (ADR-0238 P7-3 행).

### 확정된 동작 (구현 사양의 골격)

| 축 | 확정 | 미정 (Open questions) |
| --- | --- | --- |
| 유휴의 효과 | 알람 상승 (적 직접 공격 아님) | 유휴 판정 N 초 · 접근성 opt-out — (c) |
| 알람 구동 | 기존 `tickAlarm` 시간 기반 (`iceAlarmSpeed` 인자 유지) | tick 을 구동하는 경로 (reducer 액션 / rAF 루프) — (i) |
| 알람의 결과 | 적 피해 · 공격성 증가 | 레벨당 크기 · 기존 `aggression` 필드와의 관계 — (j) |
| 두 알람 | — | `player.alarm` (0–100) 과 합칠지 — (k) |
| 측정 | `balance_sim.ts` 에 유휴 단계 추가 | 유휴 길이 분포 — (l) |
| `stealth` ICE | — | 스킬 저술 필요 여부 — (e) |

**수치는 이 ADR 이 정하지 않는다.** N 초, 레벨당 피해 · 공격성 증가량은 측정 없이
정할 수 없다 (ADR-0238 P7 추천 ③). 구현 시 실측과 함께 정해 이 ADR 에 기록한다.

## 수락 증거 (Acceptance evidence)

ADR-0238 「공통 수락 증거」와 ADR-0229 §A 를 따른다.

- **비교 기준선**: [ADR-0239](./0239-vfx-spawn-rng-decoupling.md) §재기준화 결과의
  **새 기준선** — opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 /
  79.1 / 98.9 / 83.0 / 44.4 / 24.7` (g1–g6). ADR-0238 이 인용한 ADR-0229 곡선
  (`100.0 / 88.6 / 73.1 / 39.3 / 35.7 / 0.0`) 은 ADR-0239 이후 **역사적 값**이다.
- **측정**: `cd web && npm run balance` + `npm run balance -- --deck ppl` — 구현
  전·후, 6 grade 전부. **하네스 유휴 단계 추가 전·후도 구분해 기록**한다 (측정 도구
  변경과 게임 변경이 섞이지 않도록).
- **판정**: opening 어떤 grade 든 ±3pp 초과 → 되돌리거나 이 ADR 에서 명시적
  re-baseline (§A1). ±3pp 이내 → before/after 표 보고 (§A2). 단조 비증가 (§B1) 와
  g6 ∈ [0.0%, 5.0%] (§B2) 는 불변식. PPL 어떤 grade 든 5pp 이상 → PPL 표 필수 (§C2).
- **테스트** (ADR-0238 이 적은 것): `alarmLevel` 쓰기 지점이 생긴다는 단위 테스트
  (`web/tests/combat_engine.test.ts` 는 이미 `tickAlarm` 을 참조 — ADR-0228),
  `web/tests/balance_sim.test.ts` 결정성 유지, 새 idle-tick 테스트
  (`fuzz_combat.test.ts` 와 함께), 하네스가 시간 tick 경로를 실제로 밟는지 확인.
- **가설 (실측 전 단정 금지)**: 알람이 실제 피해 결과를 갖게 되므로 곡선이 움직일
  가능성이 크다. 방향과 크기는 측정 전에는 모른다.

## 결과 (Consequences)

**2026-10-31 결정 기준.** 아직 구현 전이므로, 아래는 결정이 확정한 것과 예상이다.

### 결정이 확정한 것

- **P7 과 X1 은 한 서브시스템이다** — 유휴 시간 → 알람 상승 → 적 피해·공격성 증가.
- **`tickAlarm` 은 살린다** — 폐기 경로 (X1-4) 는 닫혔다. 따라서 ADR-0161 동작 범위를
  줄이는 새 ADR 은 필요 없다.
- **X2 의 전제가 생긴다** — `getAlarmMultiplier` 가 걸 대상 (`tickAlarm` 의
  `iceAlarmSpeed`) 이 이 ADR 로 살아난다 → ADR-0242.
- **하네스가 유휴를 모델링하게 된다** — 이후 시간 기반 변경도 §A1 로 측정할 수 있다.

### 긍정적 영향

- 전투 리듬이 "결정" 에서 "결정 + 시간" 으로 바뀌되, 피해는 알람을 거쳐 **간접적**으로
  만 발생한다 — 승률 cliff 위험이 직접 피해형보다 작다 (ADR-0238 P7-3 행, 가설).
- 죽은 HUD 행 (`ALARM N/5`, `state.ts:193-194`) 이 의미를 얻는다.

### 부정적 영향 / 수용한 비용

- **알람 경제 변경** — 알람이 실제 결과를 가지므로 밸런스가 움직인다. 이 ADR 이
  §A1 전후 표를 제출해야 한다.
- **하네스 변경** — `balance_sim.ts` 에 유휴 단계를 넣는 것 자체가 측정 인프라
  변경이다 (측정 도구를 측정 대상에 맞추는 작업).
- **설계 미정 항목이 많다** — 레벨당 크기, tick 구동 경로, 두 알람의 관계가 열려
  있다 (Open questions). 구현 착수 전에 정해야 할 것이 남았다.
- **접근성** — 시간 압력은 느린 입력 플레이어에게 불리할 수 있다. opt-out 여부는 (c).

### 후속 항목

1. Open questions (c)(i)(j)(k)(l) 를 구현 착수 전에 정한다 (오너 또는 실측).
2. `balance_sim.ts` 유휴 단계 추가 → 기준선 재측정 (게임 코드 무변경 상태에서).
3. `tickAlarm` 배선 + 알람 결과 구현 → §A1 전후 표.
4. 그 뒤 [ADR-0242](./0242-ice-archetype-alarm-multiplier.md) (X2) 착수.
5. `docs/design/systems/combat.md` · `docs/design/GDD.md` 갱신 (`AGENTS.md` §3.2 단계 3·5).

## Implementation Status (2026-10-31)

**Status**: ❌ Not started

**Evidence**:
- `web/src/core/combat/combat_engine.ts:198` — `tickAlarm` 정의, `web/src/` 호출자 0건 (X1)
- `web/src/core/combat/combat_engine.ts:202` — `tickAlarm` 의 `iceAlarmSpeed` 인자 (X1 · ADR-0242 의 배선 지점)
- `web/src/core/combat/combat_engine.ts:204` — 간격 `ALARM_TICK_INTERVAL_MS / Math.max(0.01, iceAlarmSpeed)` (X1)
- `web/src/core/combat/combat_engine.ts:20-21` — `ALARM_TICK_INTERVAL_MS = 10000`, `ALARM_MAX_LEVEL = 5` (X1)
- `web/src/core/combat/ice_crit.ts:12-15` — "not wired" 주석 (X1)
- `web/src/core/state/state.ts:193-194` — HUD `ALARM N/5` 행, 현재 표시되지 않음 (X1)
- `web/src/core/combat/state_actions_combat.ts:68` — `processEnemyTurns` 의 유일한 호출 지점 (P7)
- `web/src/core/combat/state_actions_combat.ts:139`, `:143` — `processEnemyTurns` 정의와 `AUTO_ATTACK_INTERVAL_MS` 게이트 (P7)
- `web/src/core/combat/combat_engine.ts:10` — `AUTO_ATTACK_INTERVAL_MS = 2000` (P7 — 바꾸지 않는다)
- `web/scripts/balance_sim.ts:86-89` — 하네스 고정 시계, 유휴 단계 없음 (a)

**Notes**: `combat_engine.ts` 의 `:198` · `:202` · `:204` · `:20-21` 은 2026-10-31 작업
트리에서 직접 확인했다. 나머지 위치는 ADR-0238 Evidence (HEAD `0217c0a` 기준) 를
인용했다. 구현 없음 — 테스트 수 · 승률은 측정하지 않았다.

## Open questions

- **(c) 유휴 판정 N 초 + 접근성 opt-out** (ADR-0238 에서 이월) — 입력 없음을 몇 초로
  판정하는가? 접근성 (ADR-0183) 관점에서 설정으로 끌 수 있어야 하는가? 끌 수 있다면
  그 설정이 하네스 기준선에 어떻게 반영되는가?
- **(e) `stealth` ICE 스킬** (ADR-0238 에서 이월) — ADR-0228 은 `getAlarmMultiplier`
  에 "알람 루프 + 스킬을 carry 하는 `stealth` ICE" 둘 다 필요하다고 적었다. 이 ADR 의
  루프가 생기면 배율이 알람 간격 자체를 바꾸므로 스킬 없이도 관측 가능한가, 아니면
  catalog 에 스킬을 저술해야 하는가? (ADR-0242 와 공유하는 질문)
> 문자 표기: (c)(e) 는 ADR-0238 의 문자를 그대로 이월했다. 새 질문은 ADR-0238 의
> (a)–(h) 와 겹치지 않도록 (i) 부터 붙였다.

- **(i) tick 구동 경로** — 무엇이 `tickAlarm` 을 부르는가 (reducer 액션? rAF 루프?).
  하네스가 같은 경로를 밟지 않으면 측정이 비어 있다 (ADR-0238 X1-2 행).
- **(j) 알람 결과의 크기와 형태** — "적 피해 · 공격성 증가" 의 레벨당 크기는? "공격성"
  은 기존 ICE `aggression` 필드 (ADR-0221 이 복원한 값) 를 올리는 것인가, 별도
  배율인가? `ALARM_MAX_LEVEL = 5` 에서 상한은 어떻게 되는가?
- **(k) 두 알람의 관계** — `player.alarm` (0–100, 프로그램 비용 누산기) 과
  `state.alarmLevel` (0–5) 을 하나로 합칠 것인가 (ADR-0238 Open questions (b) 후반부)?
- **(l) 하네스 유휴 길이 분포** — `balance_sim.ts` 의 유휴 단계는 어떤 분포로 유휴
  길이를 뽑는가 (ADR-0238 Open questions (a) 후반부)? 그 분포 자체가 기준선을
  결정하므로 근거를 이 ADR 에 기록해야 한다.

## 영향 받는 항목

### 이 결정으로 변경된 항목

- `docs/wiki/decisions/0240-idle-pressure-and-alarm-loop.md` — **신규** (이 ADR)
- `docs/wiki/decisions/0238-balance-and-input-decision-request.md` — 상태 → Superseded
- `docs/wiki/decisions/README.md` — 인덱스 행 추가

### 구현 시 변경될 항목 (예정)

- `web/src/core/combat/combat_engine.ts`, `state_actions_combat.ts` — 알람 tick 배선 + 결과
- `web/scripts/balance_sim.ts` — 유휴 단계
- `web/tests/combat_engine.test.ts`, `balance_sim.test.ts`, 새 idle-tick 테스트
- `docs/design/systems/combat.md`, `docs/design/GDD.md`

### 변경되지 않는 항목

- `web/` 전체 — 이 ADR 작성 시 **미수정**
- `AUTO_ATTACK_INTERVAL_MS = 2000` — 유휴 경로는 이 값을 바꾸지 않는다 (Combat-feel 제안서 P7 안)
- Accepted ADR 본문 (0161 / 0183 / 0228 / 0229 / 0239) — immutable

## 관련 결정

- ADR-0238 — 이 ADR 의 원 결정 요청 (P7 · X1 절, §사용자 결정, §결과). 이 ADR 로 대체됨.
- ADR-0239 — 현재 기준선의 보유자 (§재기준화 결과). §A1 비교는 그 표를 기준으로 한다.
- ADR-0229 — drift policy §A1–§A4 · §B1–§B2 · §C2 (수락 기준).
- ADR-0228 — 두 알람의 실측과 `tickAlarm` 미배선 판정.
- ADR-0242 — X2 `getAlarmMultiplier`. **이 ADR 에 의존**한다.
- ADR-0183 — 유휴 압력의 접근성 질문 (c).
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  §1.2 P7, §1.3 X1, §2.1, §3 5단계.

## 변경 이력

- 2026-10-31: 작성 — ADR-0238 분할 (P7 + X1). **Accepted** (오너 결정: P7-3 · X1-2 ·
  (a) 하네스 유휴 단계 · (b) 알람 상승 = 적 피해·공격성 증가). Implementation Status
  ❌ Not started. 열린 질문 (c)(e) 이월, (i)–(l) 신설. 구현 없음.

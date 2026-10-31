# ADR-0238: 밸런스 · 입력 정책 결정 요청 — P7 · P8 · X1 · X2 · X4

**상태**: Draft
**날짜**: 2026-10-31
**결정자**: 사용자 (프로젝트 오너) — **결정 대기**
**우선순위**: P2 (The Flatline — 트리아지 §2.1 "신규 ADR 필요" 중 밸런스 4건 + 입력 정책 1건)
**관련**: [ADR-0018 — Combat Animation](./0018-combat-animation.md), [ADR-0161 — ICE Personality Archetypes](./0161-ice-personality-archetypes.md), [ADR-0183 — Accessibility (Colorblind 3 Modes, Text Size, Input Remapping)](./0183-accessibility.md), [ADR-0195 — Accepted ADR Implementation Status Workflow](./0195-adr-implementation-workflow.md), [ADR-0197 — Gamepad / Controller Input Support](./0197-gamepad-controller-input-support.md), [ADR-0228 — ICE 아키타입 동작 배선](./0228-ice-archetype-behavior-wiring.md), [ADR-0229 — Grade 난이도 곡선 재기준화](./0229-grade-curve-rebaseline.md), [ADR-0231 — Combat-feel top-3](./0231-combat-feel-top3-vfx-log-raf.md), [ADR-0237 — UI 화면 구성 개편](./0237-ui-composition-and-visual-direction.md), [UI 개편 트리아지 (2026-10-31)](../../design/ui-overhaul-triage-2026-10-31.md), [Combat-feel 제안서 (2026-10-29)](../../design/combat-feel-and-interaction-proposal.md)

> **이 문서는 결정 요청 (Draft) 이다.** `AGENTS.md` §3.3 에 따라 항목마다
> 옵션 비교표 · 추천안 · 열린 질문을 담는다. **어떤 항목도 구현하지
> 않았다** — 이 문서 작성 중 `web/` 아래 파일은 하나도 수정·실행하지 않았다
> (읽기만 했다).
>
> **밸런스 수치와 입력 정책은 오너의 결정이다.** 이 문서는 추천을 적지만
> 어떤 옵션도 채택하지 않는다. 이 문서 안의 승률 이동 예측은 전부
> **가설**이며 실측값이 아니다 — 실측은 ADR-0229 §A3 에 따라 구현 시점의
> `npm run balance` 로만 한다.
>
> **수락 시 분할 가능.** 이 문서는 다섯 결정을 한 번에 요청하기 위한
> 묶음이다. 수락되면 **별도 ADR 로 나눌 수 있다** (트리아지 §3 5단계는
> P7+X1 을 한 ADR, P8 단독, X2 단독을 권한다). 이 문서의 분할 추천은
> §추천 → 「문서 분할 추천」 에 있다.

## 컨텍스트 (Context)

ADR-0237 (UI 화면 구성 개편, 🟡 Partial) 로 트리아지의 시각·구성 항목은
결정과 대부분의 구현이 끝났다. 남은 백로그 가운데 **오너 결정 없이는
진행할 수 없는 다섯 항목**이 이 문서의 대상이다. 다섯 모두 트리아지에서
의도적으로 보류됐다 — 넷은 밸런스를 건드리고, 하나는 입력 정책이다.

증거 기반은 [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md)
(이하 **트리아지**) 이고, 원 제안은
[`docs/design/combat-feel-and-interaction-proposal.md`](../../design/combat-feel-and-interaction-proposal.md)
(이하 **FEEL**) 이다.

### 대상 항목 (트리아지 인용 그대로)

| ID | 항목 | 트리아지 판정 | 트리아지 근거 (`path:line`, `web/src/` 기준) | 트리아지 비고 |
| --- | --- | --- | --- | --- |
| **P7** | 입력 유휴 시 적 행동 (시간 압력) | ❌ not started | — | **밸런스 접촉** — ADR-0229 §A1 전후 측정 필수 |
| **P8** | `critical_hit` 임계값을 실제 crit 과 연동 | ❌ not started | `core/combat/state_actions_programs.ts:235` 에 여전히 `damage >= 10` 하드코딩 | **밸런스 접촉** — ADR-0229 §A1 |
| **X1** | 알람 누적 루프 `tickAlarm` 배선 | ❌ not started | `core/combat/combat_engine.ts:198` 정의, `core/combat/ice_crit.ts:12-15` "not wired" 주석 | 밸런스 접촉. P7 과 묶어 판단 |
| **X2** | ICE archetype `getAlarmMultiplier` / `shouldTargetAlly` 배선 | ❌ not started | `core/combat/ice_ai.ts:333`, `:364` 정의, 호출자 0건 | 밸런스 접촉 |
| **X4** | 숫자키 OS auto-repeat 차단 | ❌ not started | `input/keyboard.ts:71-72` — modifier 조합일 때만 repeat 무시 | 입력 정책 결정 필요 |

### 인용 위치 재확인 (HEAD `0217c0a`, 2026-10-31)

이 ADR 작성 시 위 위치를 직접 읽어 확인했다.

- `core/combat/state_actions_programs.ts:235` — `...(damage >= 10` ✓. 이어지는
  `:237` 이 `import_vfx_ms("critical_hit", …)` 다.
- `core/combat/combat_engine.ts:198` — `export function tickAlarm(` ✓.
  `web/src/` 안에서 `tickAlarm` 을 부르는 코드는 없다 (grep — 정의와
  `ice_crit.ts` 주석만 나온다).
- `core/combat/ice_crit.ts:12-15` — `:12-14` 가 `getAlarmMultiplier` 미배선
  ("the web build has no alarm accrual loop … `tickAlarm`, which has no
  production caller"), `:15` 부터 `shouldTargetAlly` 미배선 설명이다 ✓.
- `core/combat/ice_ai.ts:333` — `export function getAlarmMultiplier(` ✓,
  `:364` — `export function shouldTargetAlly(` ✓. 둘 다 `web/src/` 안 호출자
  0건 (grep). 별개로 `core/state/run_mutators.ts:183` 에 **이름이 같은 다른
  함수** (run mutator 용 `getAlarmMultiplier(state)`) 가 있다 — X2 의 대상이
  아니다.
- `input/keyboard.ts:71-72` — 주석 `:71` + `if (event.repeat && (event.ctrlKey || event.metaKey))` `:72` ✓.

### 이 ADR 의 질문

**다섯 개의 "정의만 있고 호출 경로가 없는" 또는 "사양과 어긋난" 동작을
각각 살릴 것인가, 어떤 변형으로 살릴 것인가, 아니면 버릴 것인가 — 그리고
그 결정을 몇 개의 ADR 로 나눠 기록할 것인가?**

### 공통 수락 증거 — ADR-0229 §A1 (밸런스 4건)

P7 · P8 · X1 · X2 중 어느 것이든 채택되면, 그 구현은 ADR-0229 의 drift
policy 를 따른다.

- **기준선**: opening deck `100.0 / 88.6 / 73.1 / 39.3 / 35.7 / 0.0`
  (g1–g6, ADR-0229 「새 기준선」). PPL reference `100.0 / 77.9 / 99.6 /
  84.8 / 44.4 / 28.3` (§C).
- **측정**: `cd web && npm run balance` (opening, 100 runs/mission) +
  `npm run balance -- --deck ppl` — **구현 전·후 두 번**, 여섯 grade 전부.
  하네스는 53 미션 (ADR-0215 의 53/53) 을 돈다.
- **판정**: 어떤 opening grade 든 ±3pp 초과 → 되돌리거나 그 구현 ADR 이
  명시적으로 re-baseline (§A1). ±3pp 이내 → before/after 표로 보고 (§A2).
  단조 비증가 (§B1) 와 g6 ∈ [0.0%, 5.0%] (§B2) 는 불변식. PPL 의 어떤
  grade 든 5pp 이상 이동 → PPL 표 필수 (§C2).
- **RNG 중립성**: ADR-0231 이 발견했듯 `Math.random` 을 소비하는 VFX spawn 은
  표시 전용이어도 하네스의 PRNG 흐름을 밀어 drift 를 만든다. 순수 표시
  변경은 `import_vfx_deterministic` (`core/state/state_helpers.ts:107`) 을
  쓰고 RNG draw count 일치를 확인한다.

## 고려한 옵션

### A. 밸런스 접촉 묶음 — P7 · X1 · P8 · X2

네 항목 모두 위 「공통 수락 증거」를 요구한다. P7 과 X1 은 서로 기대는
구조라 먼저 함께 다룬다.

#### P7 — 입력 유휴 시 적 행동 (시간 압력)

**현재**: 트리아지는 `file:line` 을 적지 않았다 (`—`). 직접 확인한 현재
구조는 이렇다 — 적 턴 처리 `processEnemyTurns` (`core/combat/state_actions_combat.ts:139`)
의 호출자는 `use_program` 분기 안의 한 곳뿐이다 (`:68`
`drawHand(processEnemyTurns(result))`). 그 안에서 `:143` 이
`currentMs - state.lastEnemyAttackMs < AUTO_ATTACK_INTERVAL_MS` 면 바로
돌아간다 (`AUTO_ATTACK_INTERVAL_MS = 2000`, `core/combat/combat_engine.ts:10`).
즉 **플레이어가 프로그램을 쓰지 않으면 적도 행동하지 않는다.** FEEL 의
표현: "플레이어가 아무것도 안 하면 적도 아무것도 안 함. 가짜 idle threat
없음". rAF 루프 (P9, ADR-0231) 는 이미 있으나 렌더만 담당한다.

**채택 시 바뀌는 것**: FEEL P7 안 — "`use_program` 과 무관하게 별도 tick
source 를 둬서, 플레이어 입력 없이 N 초가 지나면 적이 한 번 행동한다. 단
`AUTO_ATTACK_INTERVAL_MS = 2000` 를 바꾸지 말고 '입력 없음 시에만' 추가 tick
경로를 만들 것." 전투 리듬이 "결정" 에서 "결정 + 시간" 으로 바뀐다.

| 옵션 | 내용 | 장점 | 단점 / 위험 |
| --- | --- | --- | --- |
| **P7-1 현상 유지** | 유휴 시 아무 일도 없음 | 턴 구조 규칙성 유지 (FEEL R4·R5 의 "결정에 집중" 원칙과 일치). 밸런스 0 | "멍때리기" 손해 없음 — 긴장이 HP/덱으로만 표현됨 (FEEL P7 문제 제기 그대로) |
| **P7-2 채택 (FEEL 안)** | 입력 없이 N 초 → 적이 한 번 공격 (기존 `processEnemyTurns` 재사용) | 가장 직접적인 시간 압력. 기존 적 행동 경로 재사용 | **승률을 직접 깎는다.** FEEL R5 가 "플레이어가 시간을 재는 게임이 아니다" 로 실시간 타이머 UI 를 기각한 것과 긴장. 접근성 (ADR-0183) — 느린 입력 플레이어에게 불리. N 값 미정 |
| **P7-3 변형: 유휴 → 알람 상승** | 유휴 시간이 적 공격이 아니라 X1 의 알람 루프를 올린다. 피해는 알람의 결과로만 간접 발생 | 압력은 생기되 승률 cliff 위험이 작다. **X1 · X2 (`getAlarmMultiplier`) 와 한 서브시스템을 공유** — 죽은 훅 셋이 한 번에 의미를 얻는다. 깁슨 톤의 "trace" 와 맞다 | X1 채택이 전제. `alarmLevel` 이 올라가면 무엇이 일어나는지 아직 정의가 없다 (Open questions (b)) — 정의하지 않으면 압력이 장식에 그친다 |
| **P7-4 별도 ADR 로 분리 (P7+X1)** | 이 문서에서 방향만 정하고, 수치 (N 초, 알람 결과) 와 측정은 P7+X1 전용 ADR 에서 | 트리아지 §3 5단계 권고와 일치. 측정 표가 한 ADR 에 모인다 | 결정이 한 단계 늦어진다 |

**트레이드오프**: P7-2 는 체감이 가장 크지만 그만큼 opening 곡선을 움직일
가능성이 크다 (가설). P7-3 은 간접적이라 체감이 약할 수 있지만 X1/X2 와
설계를 공유한다. **주의 — 측정 공백**: 하네스 (`web/scripts/balance_sim.ts`)
는 `Date.now` 를 고정 시계로 바꾸고 (`:86-89`) `use_program` 입력만
고른다 — 하네스 docstring 상 "유휴" 단계를 모델링하지 않는다. 따라서
idle-only 경로는 **하네스에서 0.0pp 로 보일 수 있고, 그것은 "영향 없음" 의
증거가 아니다** (Open questions (a)).

**추천**: **P7-4 (P7+X1 별도 ADR) 로 분리하되, 그 ADR 의 기본안은 P7-3
(유휴 → 알람 상승).** 이유: ① 직접 피해형 (P7-2) 은 FEEL R5 의 원칙과
부딪히고 접근성 비용이 있다. ② 알람 경유형은 X1 과 X2 의 `getAlarmMultiplier`
가 기다리는 "누적 루프" 를 함께 만든다 — 서브시스템 하나로 죽은 훅 셋을
살린다. ③ 수치 (N 초 · 알람 결과) 는 측정 없이 정할 수 없으므로 이 문서에서
숫자를 정하지 않는다.

**수락 증거**: ADR-0229 §A1 전후 표 (opening 6 grade + PPL 6 grade). 그리고
하네스가 유휴를 모델링하지 않는 문제를 해소한 측정 — 유휴 시나리오를
하네스에 추가하거나, 추가하지 않는다면 그 사실과 대체 근거를 구현 ADR 에
명시. FEEL 이 제안한 테스트: `web/tests/balance_sim.test.ts` 결정성 유지 +
새 idle-tick 테스트 (`fuzz_combat.test.ts` 와 함께).

#### X1 — 알람 누적 루프 `tickAlarm` 배선

**현재**: `tickAlarm(currentAlarmLevel, lastAlarmTickMs, currentTickMs,
iceAlarmSpeed)` 가 `core/combat/combat_engine.ts:198` 에 정의돼 있다.
간격은 `ALARM_TICK_INTERVAL_MS / iceAlarmSpeed` 이고 (`ALARM_TICK_INTERVAL_MS
= 10000`, `ALARM_MAX_LEVEL = 5` — `combat_engine.ts:20-21`), 간격이 지나면
레벨을 1 올리고 `TRACE WARNING: alarm level N/5` 메시지를 낸다. **호출자가
없다** (`ice_crit.ts:12-15`). ADR-0228 의 실측: 알람은 두 종류인데
`player.alarm` (0–100) 은 프로그램 비용 누산기이고, `state.alarmLevel` /
`lastAlarmTickMs` 는 초기화만 되고 어떤 reducer 도 쓰지 않는다. HUD 는
`alarmLevel > 0` 일 때 `ALARM N/5` 를 표시한다 (`core/state/state.ts:193-194`)
— 지금은 0 에서 움직이지 않으므로 표시되지 않는다.

**채택 시 바뀌는 것**: 전투 중 시간이 흐르면 `alarmLevel` 이 오르는 "trace"
경제가 생긴다. `alarmLevel` 이 의미를 가지려면 그 결과 (적 강화, 추가 ICE,
강제 잭아웃 등 — 미정) 도 함께 정의해야 한다.

| 옵션 | 내용 | 장점 | 단점 / 위험 |
| --- | --- | --- | --- |
| **X1-1 현상 유지** | `tickAlarm` 은 계속 미배선, 주석으로만 기록 | 밸런스 0 | 죽은 코드 + 죽은 HUD 행이 남는다. X2 `getAlarmMultiplier` 도 영영 걸 대상이 없다 |
| **X1-2 채택: 시간 기반 배선** | 기존 시그니처 그대로 전투 시간 tick 에서 호출 | 이미 있는 함수 · 상수 · HUD 행을 그대로 쓴다. 하네스는 `Date.now` 를 고정 시계로 제어하므로 결정성은 유지된다 | 무엇이 시간 tick 을 구동하는지 (reducer 액션? rAF 루프?) 를 새로 정해야 한다 — 하네스가 같은 경로를 밟지 않으면 측정이 비어 있다 (P7 과 같은 공백). 알람 결과 미정 |
| **X1-3 변형: 행동 기반 tick** | 벽시계가 아니라 적 턴 / 프로그램 사용 횟수로 레벨을 올린다 | 하네스가 그대로 측정할 수 있다 (`use_program` 경로 위). 턴 구조와 맞다 | 시간 압력이 없어져 P7 과 분리된다. `tickAlarm` 의 ms 시그니처와 맞지 않아 함수를 바꾸거나 새로 써야 한다 |
| **X1-4 폐기** | `tickAlarm` · `alarmLevel` HUD 행 제거, 알람은 `player.alarm` 하나로 | 죽은 경로 정리. 개념이 하나로 준다 | X2 `getAlarmMultiplier` 의 대상도 사라진다 → ADR-0161 동작 범위를 줄이는 새 ADR 이 필요 (ADR-0161 은 immutable) |
| **X1-5 별도 ADR 로 분리 (P7+X1)** | P7 과 한 ADR | 트리아지 권고. 시간 tick 설계가 한 곳에 모인다 | — |

**트레이드오프**: X1-2 는 P7-3 과 짝이 되고, X1-3 은 측정이 쉬운 대신 P7 과
갈라진다. X1-4 는 가장 싸지만 X2 의 절반까지 함께 포기한다.

**추천**: **X1-5 (P7+X1 한 ADR) 안에서 X1-2 (시간 기반 배선).** P7-3 의 유휴
압력과 같은 tick 을 쓰고, `getAlarmMultiplier` 가 그 간격을 스케일하게 된다.
단 그 ADR 은 **`alarmLevel` 의 결과를 함께 정의**해야 한다 — 결과 없는 루프는
HUD 숫자만 올리는 장식이다.

**수락 증거**: ADR-0229 §A1 전후 표. `alarmLevel` 쓰기 지점이 생긴다는 것을
보이는 단위 테스트 (`web/tests/combat_engine.test.ts` 는 이미 `tickAlarm` 을
참조한다 — ADR-0228). 하네스가 시간 tick 경로를 실제로 밟는지 확인.

#### P8 — `critical_hit` 임계값을 실제 crit 과 연동

**현재**: `core/combat/state_actions_programs.ts:235` 의 `damage >= 10` 이
참이면 `:237` 에서 `import_vfx_ms("critical_hit", …)` 를 spawn 한다. 실제
crit 판정은 `calculateDamage` 안에 있다 (`CRIT_CHANCE = 0.15`,
`CRIT_MULTIPLIER = 2.0` — `combat_engine.ts:14-15`; 결과 `DamageResult.isCrit`
— `combat_engine.ts:111-113`). `useProgram` 은 이미 그 결과를 받는다
(`state_actions_programs.ts:102` `const dmgResult = calculateDamage(damageCtx)`)
— 그러나 VFX 조건은 `isCrit` 를 보지 않는다. FEEL: "플레이어 진짜 crit 이
나도 VFX crit 이 안 뜰 수 있다".

**왜 밸런스 접촉인가 (직접 확인)**: `import_vfx_ms` 는 인스턴스 id 를
`Math.random()` 으로 뽑는다 (`core/state/state_helpers.ts:47`). 그러므로 spawn
**조건**을 바꾸면 하네스의 PRNG 흐름이 밀리고, 이후의 crit · 상태 proc ·
적 스킬 선택 draw 가 달라진다 — 표시 전용 변경이 승률을 움직이는 경로다
(ADR-0231 의 RNG non-neutrality 와 같은 기제).

**채택 시 바뀌는 것**: "CRIT" 표시가 진짜 치명타와 일치한다. 데미지 계산
자체는 바뀌지 않는다.

| 옵션 | 내용 | 장점 | 단점 / 위험 |
| --- | --- | --- | --- |
| **P8-1 현상 유지** | `damage >= 10` 유지 | 변경 0, 0.0pp | 표시가 실제 crit 과 무관 — 티어마다 "CRIT" 빈도가 갈린다 (FEEL) |
| **P8-2 채택: `isCrit` 연동** | `dmgResult.isCrit` 일 때만 spawn (FEEL ①) | 표시와 판정이 일치. 계산 무변경 | spawn 빈도가 바뀌므로 **`import_vfx_ms` 를 그대로 쓰면 RNG 흐름이 이동** → drift 가능 (가설) |
| **P8-3 변형: 상대 비율 임계** | `damage >= maxHp * 0.15` 로 교체 (FEEL ②) | 티어 간 빈도 편차 완화 | 여전히 진짜 crit 과 무관 — 문제의 절반만 해결. RNG 이동은 P8-2 와 동일 |
| **P8-4 별도 ADR 로 분리** | P8 단독 ADR | 트리아지 권고. 범위가 작아 측정 · 리뷰가 쉽다 | — |

**트레이드오프**: P8-2 와 P8-3 모두 spawn 빈도를 바꾸므로 RNG 중립성 처리
없이는 drift 가 날 수 있다. spawn 을 `import_vfx_deterministic` 로 옮기면 그
경로가 사라질 것으로 **예상**하지만 실측 전에는 단정하지 않는다
(`import_vfx_deterministic` 이 `import_vfx_ms` 와 같은 지속시간·크기 인자를
지원하는지도 구현 시 확인할 것 — Open questions (d)).

**추천**: **P8-4 (단독 ADR) + P8-2 (`isCrit` 연동), spawn 은 RNG 무소비
경로로.** 이유: 이것은 "판정을 바꾸는" 변경이 아니라 "표시를 판정에
맞추는" 변경이다. RNG 무소비로 spawn 하면 0.0pp 가 기대값이 되고, 그러면
ADR-0229 §A2 의 보고만으로 닫힌다. 0.0pp 가 아니면 그 자체가 조사 대상이다
(§A3).

**수락 증거**: ADR-0229 §A1 전후 표 (기대값 0.0pp 6 grade 전부) + RNG draw
count before/after 일치 (ADR-0231/0232 선례). `web/tests/combat_engine.test.ts`
와 crit spawn 조건 테스트. FEEL 이 지목한 `web/tests/design_conformance.test.ts`
의 crit 상수 assertion 유지.

#### X2 — ICE archetype `getAlarmMultiplier` / `shouldTargetAlly` 배선

**현재**: `core/combat/ice_ai.ts:333` `getAlarmMultiplier` — `stealth` 면
`STEALTH_ALARM_MULTIPLIER` (`0.5`, `ice_ai.ts:316`), 그 외 1.0.
`ice_ai.ts:364` `shouldTargetAlly` — `support` 이고 HP 70% 미만 아군이
있으면 참. 둘 다 호출자 0건. ADR-0228 의 판정: 둘 다 "미배선, 서브시스템
필요" — `shouldTargetAlly` 는 enemy 경로에 per-target 스킬 해석이 없고
(roster 의 모든 ICE 가 플레이어 한 명을 공격), `getAlarmMultiplier` 는 걸
알람 누적 루프가 없다. 또 ADR-0228 은 catalog 의 `stealth` ICE 5 종이 모두
`skills: []` 임을 기록했다.

**채택 시 바뀌는 것**: ADR-0161 의 네 archetype 동작이 전부 살아난다.
`stealth` ICE 가 알람을 느리게 올리고, `support` ICE 가 다친 아군을
대상으로 heal/buff 를 쓴다.

| 옵션 | 내용 | 장점 | 단점 / 위험 |
| --- | --- | --- | --- |
| **X2-1 현상 유지** | 둘 다 미배선, `ice_crit.ts` 주석으로 기록 | 밸런스 0 | ADR-0161 의 4 동작 중 2 개가 계속 문서상 동작 |
| **X2-2 채택: 둘 다 배선** | 알람 루프 (X1) + per-target 스킬 해석을 모두 만든다 | ADR-0161 완결 | **서브시스템 둘** — 가장 큰 범위. `shouldTargetAlly` 는 multi-ICE 전투의 대상 모델 · 대상 지정 효과 경로까지 필요 (ADR-0228) |
| **X2-3 변형: `getAlarmMultiplier` 만** | X1 이 들어온 뒤 알람 간격에 배율만 건다. `shouldTargetAlly` 는 🟢 Deferred | X1 루프 위의 국소 배선 — `tickAlarm` 의 `iceAlarmSpeed` 인자가 이미 그 자리다 | `shouldTargetAlly` 는 계속 미배선. 스킬을 carry 하는 `stealth` ICE 가 추가로 필요한지 미정 (Open questions (e)) |
| **X2-4 폐기** | 두 함수 삭제 + ADR-0161 범위를 줄이는 새 ADR | 죽은 코드 정리 | archetype 다양성 축소. ADR-0161 은 immutable 이므로 반드시 새 ADR |
| **X2-5 별도 ADR 로 분리** | X2 단독 ADR (트리아지 권고), X1 이후 | 의존 순서가 명확 | — |

**트레이드오프**: X2-2 는 완결성이 가장 높지만 범위가 가장 크다. X2-3 은 X1
에 기대는 대신 작다. 두 함수의 비용이 매우 다르므로 (국소 배선 vs 시스템
구축) 한 결정으로 묶을 이유가 약하다.

**추천**: **X2-5 (단독 ADR, P7+X1 이후) + X2-3 (`getAlarmMultiplier` 만
배선, `shouldTargetAlly` 는 🟢 Deferred).** `shouldTargetAlly` 는 multi-target
스킬 시스템 ADR 이 생길 때까지 미룬다 — 트리아지 §2.1 이 P2 의
`counter`/`lifesteal` 을 "스킬 시스템 ADR 이 먼저" 로 미룬 것과 같은 논리다.

**수락 증거**: ADR-0229 §A1 전후 표. ADR-0228 의 실측대로 band 에 `stealth`
ICE 가 있으므로 (g1 slot 2 `wisp`, g3 slot 3 `ice_dixie_echo`) g1 · g3 이동을
특히 볼 것 (가설 — 실측 전 단정 금지). `stealth` 배율이 알람 간격에 반영되는
단위 테스트.

### B. 입력 정책 — X4

X4 는 밸런스 항목이 아니다. 하네스는 `KeyboardInput` 을 거치지 않고
reducer 에 액션을 직접 넣으므로 (`web/scripts/balance_sim.ts` 의
`applyAction` 구동) `npm run balance` 는 X4 의 영향을 측정하지 못한다 —
**0.0pp 는 확인용 정합성 점검일 뿐 근거가 아니다.**

#### X4 — 숫자키 OS auto-repeat 정책

**현재**: `input/keyboard.ts:71-72` — `event.repeat && (event.ctrlKey ||
event.metaKey)` 일 때만 repeat 를 무시한다. 숫자키 `1`–`9` 는
`select_program` 에 매핑되고 (`core/types.ts:467-475`, `Digit1`–`Digit9` 는
`keyboard.ts:26-34`), 전투에서 `select_program` 은 `use_program` 으로
해석된다 (`core/state/state.ts:167-176` `resolveProgramSelection`). 따라서
FEEL M6 의 지적대로 숫자키 하나를 길게 누르면 프로그램이 연타된다 — 키를 누르고 있으면 OS
repeat 마다 프로그램이 한 장씩 나간다. 기존 테스트
`web/tests/keyboard_locale.test.ts:106-109` 는 "bare (non-modifier) Enter on
repeat still fires confirm" 을 고정하고 있다.

**채택 시 바뀌는 것**: 숫자키를 누르고 있어도 프로그램은 한 번만 나간다.
FEEL R4 는 hold-to-repeat 입력 큐를 기각했고, 숫자키 repeat 차단은 "별도
판단" 으로 남겼다.

| 옵션 | 내용 | 장점 | 단점 / 위험 |
| --- | --- | --- | --- |
| **X4-1 현상 유지** | modifier 조합만 repeat 무시 | 변경 0 | 의도치 않은 연속 플레이 (손패 소모 + 적 턴 트리거) 가능 |
| **X4-2 채택: 숫자키 repeat 무시** | `select_program` 매핑 키 (`1`–`9` / `Digit1`–`Digit9`) 의 `event.repeat` 만 무시 | 가장 좁은 변경. Enter · 화살표 repeat (메뉴 스크롤) 는 그대로 — 기존 테스트 `:106-109` 와 충돌 없음 | 다른 "한 번만" 액션 (예: 확인 계열) 은 여전히 repeat 가능 |
| **X4-3 변형: 이동키 외 전부 repeat 무시** | 화살표 등 이동만 repeat 허용 | 정책이 단순 ("이동만 반복") | `:106-109` (bare Enter repeat 발사) 테스트를 바꿔야 한다 — 기존 동작 변경 |
| **X4-4 변형: 시간 디바운스** | repeat 를 막지 않고 숫자키에 최소 간격 (예: 터치 프로그램 버튼의 120ms 디바운스 — 트리아지 P12 `touch.ts:142`) | 입력 채널 간 정책 통일 | 디바운스 간격이 또 하나의 튜닝 수치. 누르고 있으면 여전히 연타된다 |
| **X4-5 별도 ADR 로 분리** | X4 단독 ADR (입력 정책) | 밸런스 묶음과 성격이 달라 리뷰가 분리된다 | — |

**트레이드오프**: X4-2 는 문제 (숫자키 연타) 에 정확히 맞고 기존 테스트를
건드리지 않는다. X4-3 은 규칙이 깔끔하지만 기존 Enter 동작을 바꾼다. X4-4
는 채널 통일 장점이 있지만 "누르고 있으면 연타" 를 막지 못한다.

**추천**: **X4-5 (단독 ADR) + X4-2 (숫자키 repeat 만 무시).** 프로그램 한
장은 턴 하나이고, 턴은 "결정" 이어야 한다 (FEEL R4 의 논리). 이동과 확인의
repeat 는 메뉴 조작 편의이므로 유지한다. 게임패드 · 터치 채널에 같은 정책을
적용할지는 별도 질문으로 남긴다 (Open questions (f)).

**수락 증거**: `web/tests/keyboard_locale.test.ts` 에 ① `Digit1` repeat 무시
② repeat 아닌 `Digit1` 은 `select_program` 발사 ③ 기존 `:106-109` (bare Enter
repeat 발사) 유지 — 세 케이스. 브라우저 스모크로 숫자키 길게 누르기 확인.
`npm run balance` 0.0pp (정합성 점검).

## 추천 (Recommendation)

| 항목 | 옵션 수 | 추천 | 요지 |
| --- | --- | --- | --- |
| P7 | 4 | **P7-4 + P7-3** | P7+X1 별도 ADR, 유휴는 적 공격이 아니라 알람 상승으로 |
| X1 | 5 | **X1-5 + X1-2** | P7 과 같은 ADR, 기존 `tickAlarm` 시간 기반 배선 + `alarmLevel` 결과 정의 |
| P8 | 4 | **P8-4 + P8-2** | 단독 ADR, `isCrit` 연동, spawn 은 RNG 무소비 경로 |
| X2 | 5 | **X2-5 + X2-3** | 단독 ADR (X1 이후), `getAlarmMultiplier` 만, `shouldTargetAlly` 🟢 Deferred |
| X4 | 5 | **X4-5 + X4-2** | 단독 ADR, 숫자키 repeat 만 무시 |

### 문서 분할 추천

수락 시 이 문서를 **네 개의 ADR 로 분할**할 것을 추천한다. 트리아지 §3
5단계의 묶음 (P7+X1 / P8 / X2) 에 X4 를 독립시킨 형태다.

1. **P7 + X1** — 알람 누적 루프 + 유휴 압력. 시간 tick 설계, `alarmLevel`
   결과, 하네스 유휴 모델이 한 곳에 모인다. **먼저.**
2. **P8** — crit 표시 연동. 다른 항목과 독립. 언제든 가능.
3. **X2** — `getAlarmMultiplier` 배선. **1번 이후** (걸 루프가 필요).
4. **X4** — 숫자키 repeat 정책. 밸런스와 무관, 독립.

이 문서 자체는 분할 후에도 **결정 요청 기록으로 남긴다** (상태를 Accepted
로 바꾸거나, 분할 ADR 로 대체됐음을 인덱스에 기록 — 오너 선택).

## 사용자 결정 (Decision)

**결정 대기.** 항목마다 하나를 고르거나, 다른 안을 적거나, Defer 를 고른다.

**P7 — 입력 유휴 시 적 행동**
- [ ] P7-1 현상 유지
- [ ] P7-2 채택 (유휴 → 적 공격)
- [ ] P7-3 변형 (유휴 → 알람 상승)
- [ ] P7-4 별도 ADR 로 분리 (P7+X1)
- [ ] 기타: ___ / [ ] Defer

**X1 — `tickAlarm` 배선**
- [ ] X1-1 현상 유지
- [ ] X1-2 채택 (시간 기반)
- [ ] X1-3 변형 (행동 기반)
- [ ] X1-4 폐기
- [ ] X1-5 별도 ADR 로 분리 (P7+X1)
- [ ] 기타: ___ / [ ] Defer

**P8 — `critical_hit` 연동**
- [ ] P8-1 현상 유지
- [ ] P8-2 채택 (`isCrit` 연동)
- [ ] P8-3 변형 (상대 비율 임계)
- [ ] P8-4 별도 ADR 로 분리
- [ ] 기타: ___ / [ ] Defer

**X2 — archetype 2 종 배선**
- [ ] X2-1 현상 유지
- [ ] X2-2 채택 (둘 다)
- [ ] X2-3 변형 (`getAlarmMultiplier` 만)
- [ ] X2-4 폐기 (새 ADR 로 ADR-0161 범위 축소)
- [ ] X2-5 별도 ADR 로 분리
- [ ] 기타: ___ / [ ] Defer

**X4 — 숫자키 repeat 정책**
- [ ] X4-1 현상 유지
- [ ] X4-2 채택 (숫자키 repeat 무시)
- [ ] X4-3 변형 (이동키 외 전부 무시)
- [ ] X4-4 변형 (시간 디바운스)
- [ ] X4-5 별도 ADR 로 분리
- [ ] 기타: ___ / [ ] Defer

**분할**
- [ ] 추천대로 4 개 ADR 로 분할 (P7+X1 / P8 / X2 / X4)
- [ ] 트리아지대로 3 개 (P7+X1 / P8 / X2) + X4 는 이 문서에서 결정
- [ ] 분할하지 않음 (이 문서가 다섯 결정을 모두 기록)

## 결과 (Consequences)

(결정 후 작성 — `AGENTS.md` §3.3)

## Implementation Status (2026-10-31)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ❌ Not started (Draft — 결정 대기)

**Evidence** (현재 상태 — 변경 전 위치, HEAD `0217c0a`):
- `web/src/core/combat/state_actions_combat.ts:68` — `processEnemyTurns` 의 유일한 호출 지점 (`use_program` 분기) (P7)
- `web/src/core/combat/state_actions_combat.ts:139`, `:143` — `processEnemyTurns` 정의와 `AUTO_ATTACK_INTERVAL_MS` 게이트 (P7)
- `web/src/core/combat/combat_engine.ts:10` — `AUTO_ATTACK_INTERVAL_MS = 2000` (P7)
- `web/src/core/combat/state_actions_programs.ts:235`, `:237` — `damage >= 10` 조건과 `critical_hit` spawn (P8)
- `web/src/core/combat/state_actions_programs.ts:102` — `dmgResult = calculateDamage(damageCtx)` (P8 — `isCrit` 를 이미 받음)
- `web/src/core/combat/combat_engine.ts:111-113` — `DamageResult.isCrit` (P8)
- `web/src/core/state/state_helpers.ts:47` — `import_vfx_ms` 의 `Math.random()` id (P8 RNG 경로)
- `web/src/core/state/state_helpers.ts:107` — `import_vfx_deterministic` (P8 추천 경로)
- `web/src/core/combat/combat_engine.ts:198` — `tickAlarm` 정의, 호출자 0 (X1)
- `web/src/core/combat/combat_engine.ts:20-21` — `ALARM_TICK_INTERVAL_MS = 10000`, `ALARM_MAX_LEVEL = 5` (X1)
- `web/src/core/state/state.ts:193-194` — HUD `ALARM N/5` 행 (X1)
- `web/src/core/combat/ice_crit.ts:12-15` — "not wired" 주석 (X1, X2)
- `web/src/core/combat/ice_ai.ts:316`, `:333` — `STEALTH_ALARM_MULTIPLIER = 0.5`, `getAlarmMultiplier` (X2)
- `web/src/core/combat/ice_ai.ts:364` — `shouldTargetAlly` (X2)
- `web/src/input/keyboard.ts:71-72` — modifier 조합만 repeat 무시 (X4)
- `web/src/core/types.ts:467-475` — `1`–`9` → `select_program` (X4)
- `web/src/core/state/state.ts:167-176` — `select_program` → `use_program` 해석 (X4)
- `web/tests/keyboard_locale.test.ts:106-109` — bare Enter repeat 발사 고정 (X4)
- `web/scripts/balance_sim.ts:86-89` — 하네스 고정 시계 (P7 / X1 측정 공백)

**Notes**:
- 줄 번호는 HEAD `0217c0a` 의 트리 기준이다. 트리아지는 2026-10-31 작업 트리
  기준이었고 위 인용은 그 위치와 일치함을 확인했다.
- 이 ADR 작성 중 `web/` 아래 파일은 수정·실행하지 않았다 — 테스트 수 ·
  빌드 결과 · 승률을 측정하지 않았다. 문서 안의 승률 이동 언급은 전부 가설이다.
- 동반 발견 (범위 밖, 기록): `core/state/state_helpers.ts:139` 에도
  `program.role === "burst" && damage >= 10` 이라는 **같은 하드코딩 임계**가
  `multi_hit` VFX 선택에 쓰인다. P8 을 다루는 ADR 이 함께 볼지 판단할 것.

## Open questions

- **(a) 하네스 유휴 모델** — `balance_sim.ts` 는 `use_program` 입력만 넣고
  시계를 고정한다. P7 (그리고 시간 기반 X1) 의 영향을 ADR-0229 §A3 대로
  "실측" 하려면 하네스에 유휴 단계를 추가해야 하는가? 추가한다면 유휴 길이
  분포는 무엇으로 정하는가? 추가하지 않는다면 0.0pp 를 무엇으로 보완하는가?
- **(b) `alarmLevel` 의 결과** — 레벨이 오르면 무엇이 일어나는가 (적 피해 ·
  추가 ICE · 강제 잭아웃 · 보상 감소 등)? 이 정의 없이는 X1 과 P7-3 이
  표시 장식에 그친다. `player.alarm` (0–100) 과 하나로 합칠지도 함께.
- **(c) P7 의 N 초** — P7-2 든 P7-3 이든 유휴 판정 시간. 접근성
  (ADR-0183) 관점에서 설정으로 끌 수 있어야 하는가?
- **(d) RNG 무소비 spawn 의 인자** — `import_vfx_deterministic` 이
  `critical_hit` 에 필요한 지속시간 · 크기 인자를 지원하는지, 지원하지 않으면
  확장할지.
- **(e) `stealth` ICE 스킬** — ADR-0228 은 `getAlarmMultiplier` 에 "알람 루프 +
  스킬을 carry 하는 `stealth` ICE" 둘 다 필요하다고 적었다. X1 루프가 생기면
  배율이 알람 간격 자체를 바꾸므로 스킬 없이도 관측 가능한가, 아니면
  catalog 에 스킬을 저술해야 하는가?
- **(f) 입력 채널 통일** — X4 정책을 게임패드 (ADR-0197) 와 터치 (D-pad 250ms,
  프로그램 버튼 120ms — 트리아지 P12) 에도 맞출 것인가?
- **(g) 이 문서의 최종 상태** — 분할 후 이 문서는 Accepted 로 남기는가,
  분할 ADR 들에 의해 대체됐다고 인덱스에 기록하는가?

## 영향 받는 항목

### 이번 결정 요청으로 변경된 항목

- `docs/wiki/decisions/0238-balance-and-input-decision-request.md` — **신규** (이 ADR)
- `docs/wiki/decisions/README.md` — 0238 행 1 개 추가

### 결정 · 구현 시 변경될 수 있는 항목 (예정 — 결정에 따라)

- `web/src/core/combat/state_actions_combat.ts`, `combat_engine.ts` (P7, X1)
- `web/src/core/combat/state_actions_programs.ts` (P8)
- `web/src/core/combat/ice_ai.ts` 호출 지점 (X2)
- `web/src/input/keyboard.ts`, `web/tests/keyboard_locale.test.ts` (X4)
- `web/scripts/balance_sim.ts` (Open questions (a))
- `docs/design/systems/combat.md`, `docs/design/systems/animations.md`,
  `docs/design/GDD.md` — `AGENTS.md` §3.2 단계 3·5

### 변경되지 않은 항목

- `web/` 전체 — **미수정**
- `docs/design/ui-overhaul-triage-2026-10-31.md`,
  `docs/design/combat-feel-and-interaction-proposal.md` — 읽기 전용 참고
- ADR-0018 / 0161 / 0183 / 0195 / 0197 / 0228 / 0229 / 0231 / 0237 —
  **미수정** (immutable)

## 관련 결정

- ADR-0229 (Grade 곡선 재기준화) — **밸런스 4 건의 수락 기준.** §A1–§A4,
  §B1–§B2, §C2 를 그대로 적용한다. 그 후속 항목 5 가 이미 "`shouldTargetAlly`
  / `getAlarmMultiplier` 는 곡선을 움직일 수 있으므로 구현 시 §A1 을 반드시
  적용" 이라고 적었다.
- ADR-0228 (ICE 아키타입 동작 배선) — X1 · X2 의 현 상태 판정 ("미배선,
  서브시스템 필요") 의 owner. 그 후속 항목 2/3 이 X2 다.
- ADR-0161 (ICE Personality Archetypes) — X2 두 동작의 원 정의. X2-4 를
  고르면 범위를 줄이는 새 ADR 이 필요하다 (immutable).
- ADR-0231 (Combat-feel top-3) — VFX spawn 의 RNG non-neutrality 와
  `import_vfx_deterministic` 선례. P8 추천의 근거.
- ADR-0018 (Combat Animation) — `critical_hit` VFX 사양의 상위.
- ADR-0183 (Accessibility) / ADR-0197 (Gamepad) — P7 의 접근성 질문과 X4 의
  채널 통일 질문.
- ADR-0237 (UI 화면 구성 개편) — 이 백로그를 남긴 트리아지의 시각 항목 결정.
- ADR-0195 — Implementation Status 형식의 owner.
- [`docs/design/ui-overhaul-triage-2026-10-31.md`](../../design/ui-overhaul-triage-2026-10-31.md) —
  증거 기반 (§1.2 P7/P8, §1.3 X1/X2/X4, §2.1, §3 5–6단계).
- [`docs/design/combat-feel-and-interaction-proposal.md`](../../design/combat-feel-and-interaction-proposal.md) —
  P7 · P8 원 제안, U6 · U8 · U9 · M6, R4 · R5.

## 변경 이력

- 2026-10-31: Draft 작성 — P7 · P8 · X1 · X2 · X4 결정 요청. 항목별 옵션
  비교표 (4 / 5 / 4 / 5 / 5 개) · 추천 · 수락 증거 · 열린 질문. 수락 시
  4 개 ADR (P7+X1 / P8 / X2 / X4) 로 분할 추천. 구현 없음.

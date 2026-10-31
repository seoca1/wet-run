# ADR-0242 구현 증거 — 2026-11-01

[ADR-0242](./0242-ice-archetype-alarm-multiplier.md)의 구현 및 실측 기록.
글로벌 지침의 Accepted ADR 편집 금지 때문에 원 ADR의 Implementation Status와 변경 이력은
수정하지 않았다. 요청된 in-place 갱신은 미완료이며, 이 문서와 인덱스가 구현 증거를 제공한다.
결정 본문, ADR-0240 튜닝/문서, 다른 Accepted ADR은 변경하지 않았다.

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented (코드·테스트·측정, 미커밋). 원 ADR의 in-place 상태 갱신은 지침 충돌로 미완료.

**Evidence**:
- `web/src/core/combat/idle_alarm.ts:11` — `./ice_ai`의 함수를 직접 import.
- `web/src/core/combat/idle_alarm.ts:51-65` — 기존 유휴 gate 이후 살아 있는 roster의 최소 배율을 구해 `tickAlarm`에 전달.
- `web/src/core/combat/ice_ai.ts:335` — 기존 `PersonalityBearer`로 입력 계약을 좁힘. 함수 본문과 stealth 배율 0.5는 불변.
- `web/src/core/combat/ice_crit.ts:12-13` — `getAlarmMultiplier` 설명만 배선 완료로 수정. `shouldTargetAlly` 설명 불변.
- `web/tests/ice_alarm_multiplier.test.ts:47` — stealth 첫 tick 20초 경계와 그 직전 검증.
- `web/tests/ice_alarm_multiplier.test.ts:62` — 비-stealth 및 personality 생략 시 기존 10초 간격.
- `web/tests/ice_alarm_multiplier.test.ts:75` — 후속 stealth tick도 20초 간격.
- `web/tests/ice_alarm_multiplier.test.ts:91` — 혼합 roster 순서 독립성, 2 stealth 비중첩.
- `web/tests/ice_alarm_multiplier.test.ts:117` — stealth 사망 직후 다음 tick에서 보통 속도 복귀; stale `state.ice`/선택 슬롯 무시.
- `web/tests/ice_alarm_multiplier.test.ts:137` — 빈 roster의 중립값 1.
- `web/tests/ice_alarm_multiplier.test.ts:146` — 실제 `ice_ai` 함수 호출/반환값 0.5 검증 및 동명 run-mutator 함수 호출 0건 검증.

**Notes**: `shouldTargetAlly`는 계속 🟢 **Deferred**, 프로덕션 호출자 0건.
**(j) run-mutator 배율 합성은 OPEN**이며 `run_mutators.ts`는 수정·배선하지 않았다.
기존 ADR-0240 미커밋 변경은 보존했다. UI/`main.ts`/VFX/`core/status.ts` 수정 없음.

### (i) 다수 ICE 합성 — 해결

**매 유효 유휴 tick마다 HP > 0인 roster ICE의 최소 배율을 다시 구한다.**
현재 가능한 배율이 0.5/1이므로 살아 있는 stealth가 하나라도 있으면 0.5, 없으면 1이다.
빈 roster는 1. 단일 ICE 결과와 정확히 같고, roster 순서나 선택 슬롯에 무관하다.
곱셈이 아니므로 stealth 둘이 0.25로 중첩되지 않는다. O(roster 크기), 별도 배열/정렬/캐시 없음.

**stealth ICE가 쓰러지면 배율이 바뀌는가? 예.** 마지막 살아 있는 stealth가 죽은 뒤의 다음
유효 tick에서 1로 복귀한다. 다른 stealth가 살아 있으면 0.5를 유지한다.
알람 누적 시계는 ADR-0240 방식 그대로이며 death 시 별도 리셋하지 않는다.
`ALARM_TICK_INTERVAL_MS / 0.5 = 20_000ms`; 비-stealth는 기존 10_000ms.
기존 gate가 먼저 실행되므로 능동 플레이에서는 배율 함수도 호출되지 않는다.

## 측정 및 판정 — ADR-0229 §A1/§A2/§B1/§B2/§C2

모든 명령은 `web/`에서 실행. 53 missions, 97 ICE types, 100 runs/mission, seeds 1–100.
**Before는 ADR-0240이 이미 구현된 현재 미커밋 트리에서, 이번 코드 편집 전에 직접 측정했다.**
After는 ADR-0242 배선 후 실측. HEAD/옛 ADR 숫자를 Before로 대체하지 않았다.

### No-idle — ADR-0239와 정확 일치

| Deck | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening ADR-0239 | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening after | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| PPL ADR-0239 | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL after | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |

### Idle scenario `--idle-ms 10000,0` — 실제 §A1 before/after

| Deck / 측정 | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening before | 100.0 | 88.3 | 70.5 | 38.9 | 36.2 | 0.0 |
| Opening after | 100.0 | 88.3 | 70.5 | 38.9 | 36.2 | 0.0 |
| Opening Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| PPL before | 100.0 | 79.1 | 98.9 | 82.9 | 44.4 | 24.7 |
| PPL after | 100.0 | 79.1 | 98.9 | 82.9 | 44.4 | 24.7 |
| PPL Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

- **§A1/§A2**: opening 최대 drift **0.0pp ≤ 3pp**. §A2 보고만, re-baseline/되돌림/재튜닝 없음.
- **§B1**: no-idle `100.0 ≥ 88.3 ≥ 70.5 ≥ 39.5 ≥ 36.2 ≥ 0.0`, idle `100.0 ≥ 88.3 ≥ 70.5 ≥ 38.9 ≥ 36.2 ≥ 0.0` 모두 성립.
- **§B2**: opening g6 두 시나리오 모두 **0.0% ∈ [0.0%, 5.0%]**.
- **§C2**: PPL 최대 drift **0.0pp**, 5pp 의무 기준 미만이지만 전후 표를 함께 기록. PPL은 reference이며 단조성/g6 제약 대상이 아님 (§C1/§C3).
- 예상 이동 후보였던 **g1 (`wisp`), g3 (`ice_dixie_echo`) 모두 양 덱에서 0.0pp**.
  이 고정 10초 시나리오의 승률 불변을 임의의 유휴 분포까지 일반화하지 않는다.
- 배선은 RNG를 호출하지 않는다. No-idle 실측 전 grade 일치는 RNG 관련 회귀 증거이며,
  별도의 전체 draw-sequence 추적을 실행했다고 주장하지 않는다.
- ADR-0240에 기록된 지속 유휴/Dixie 상호작용은 재튜닝하지 않았고 오너 판단 대상으로 남는다.

## 검증

- `npm run typecheck`: exit 0, 오류 0.
- `npm run lint`: exit 0, 오류 0 / 기존 `src/input/keyboard.ts:14:13` 경고 1 (`no-explicit-any`).
- `npm test`: exit 0, **159 files / 3617 tests passed**, 실패 0; 새 파일 **18 tests** (기존 158 / 3599 보존).
  Vitest v1.6.1, duration 7.01s. jsdom의 미구현 media play/load stderr는 있었으나 실패는 없음.
- `npm run build`: exit 0, Vite v5.4.21, **118 modules**, built in 466ms.
- 첫 typecheck는 신규 테스트 teardown이 `VitestUtils`를 반환해 TS2322로 실패.
  블록 콜백으로 void 반환하도록 고친 뒤 위 전체 게이트를 통과했다.
- 네 변경 TS 파일에 `lsp_diagnostics`를 요청했으나 TypeScript LSP 미설치/기존 설치 거절로 실행 불가.
  설치를 시도하지 않았으며 LSP clean이라고 주장하지 않는다.
- E2E 미실행: 이번 변경에 UI/`main.ts` 수정 없음. ADR-0240의 과거 E2E 결과를 이번 실행으로 주장하지 않는다.
- 커밋·스테이징 없음. 코드 책임은 기존 유휴 알람 경로에 한정, 새 외부 입력/타입 단언/의존성/일회용 helper 없음.

## Raw balance output

### Before — opening idle (코드 편집 전)

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts --idle-ms 10000,0

Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000,0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         41.4   29/55
    3        11     70.5%     0.0%         6.8         13.9    4/30
    4        10     38.9%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.3          4.9    0/12
    6         3      0.0%     0.0%         5.1          0.0    0/0
```

### Before — PPL idle (코드 편집 전)

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts --deck ppl --idle-ms 10000,0

Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000,0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.0   28/43
    3        11     98.9%     0.0%         5.7         30.2   18/39
    4        10     82.9%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         4.7         15.2   10/18
    6         3     24.7%     0.0%         5.1          1.2    0/2
```

### After — opening no-idle

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts

Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### After — PPL no-idle

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts --deck ppl

Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### After — opening idle

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts --idle-ms 10000,0

Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000,0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         41.4   29/55
    3        11     70.5%     0.0%         6.8         13.9    4/30
    4        10     38.9%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.3          4.9    0/12
    6         3      0.0%     0.0%         5.1          0.0    0/0
```

### After — PPL idle

```text
> wetrun-web@0.1.0 balance
> tsx scripts/balance_harness.ts --deck ppl --idle-ms 10000,0

Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000,0ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.0   28/43
    3        11     98.9%     0.0%         5.7         30.2   18/39
    4        10     82.9%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         4.7         15.2   10/18
    6         3     24.7%     0.0%         5.1          1.2    0/2
```

## 변경 이력

- 2026-11-01: ADR-0242 배선·18개 회귀 테스트·6회 balance raw 출력 기록.
  (i) alive roster 최소 배율/매 tick 재계산으로 해결. §A2 0.0pp 보고, re-baseline 없음.
  `shouldTargetAlly` 🟢 Deferred, (j) OPEN. 원 Accepted ADR의 in-place 갱신은 수행하지 않음.

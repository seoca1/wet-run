# ADR-0245: 전투 HUD 표시 결함 2건 — ICE 최대 HP와 장비 슬롯 수

**상태**: Accepted
**날짜**: 2026-11-01
**결정자**: 프로젝트 오너 (2026-11-01 표시 전용 수정 요청)
**우선순위**: P2 (The Style — 전투 HUD 정확성)
**관련**: [ADR-0195 — Implementation Status 워크플로우](./0195-adr-implementation-workflow.md) · [ADR-0239 — 밸런스 기준선](./0239-vfx-spawn-rng-decoupling.md) · [ego-lite 실제 플레이 점검](../../playtest/EGO_LITE_PLAY_CHECK.md)

## 컨텍스트 (Context)

2026-11-01 ego-lite 실제 브라우저 플레이에서 ICE `165/100`과 우측 패널
`Equipped: 10/8`을 발견했다. 두 건 모두 **확정된 표시 결함**이다. 상태·전투 계산은
정상이지만 HUD가 그 상태를 잘못 설명했다. 기존 단언이 놓친 결함을 실제 화면 관찰이
잡았다는 사례이며, 실제 플레이 점검은 결정적 자동 회귀 게이트를 보완한다.

### 원인

1. `web/src/renderer/combat_grid.ts`가 ICE 게이지·분모·기본 색상에 리터럴 `100`을
   사용했다. 실제 roster 생성은 `web/src/core/state/state_actions_phases.ts:75`에서
   `{ ...activeIce, id, hp, maxHp: hp }`로 등급별 최대 HP를 보존한다. `hp=165`이면
   텍스트가 `165/100`이고, 게이지 비율은 1로 clamp되어 100을 넘는 동안 가득 찬다.
   `ice_ai.ts`의 `shouldDefensiveAct`와 `isAtOrAboveDefensiveThreshold`는 이미
   `ice.maxHp`를 사용하므로 수정하지 않는다.
2. `buildHudLines`가 `Object.values(state.equipmentLoadout)`의 non-null 값 수를
   셌다. loadout은 슬롯 맵 하나와 메서드 아홉 개를 가진 객체이므로 실제 장비 수와
   무관하게 **1 + 9 = 10**이다. 장비 1개 + 메서드 9개라는 계산도 아니다.
   실제 슬롯은 내부 `equipment`에 있으며 `allSlotsFilled()`가 이를 제공한다.

## 결정 (Decision)

- ICE 표시의 최대 HP를 **양수·유한한 `ice.maxHp`**로 통일한다. 없거나 0 이하,
  NaN/Infinity이면 기존 legacy 최대치 `100`을 fallback으로 사용한다. 같은 값으로
  `healthBar`, slash-text, `healthColor`를 계산하며 피격 flash 우선순위는 유지한다.
- 같은 파일의 다른 ICE HP 표기도 확인했다. 사망 분기는 분모 없는 `[DEAD]`뿐이므로
  그대로 유지한다. 다른 하드코딩 ICE HP 분모는 없다.
- 장비 수는 `allSlotsFilled().length`, 전체 슬롯 수는 `EQUIP_SLOTS.length`로 표시한다.
- **표시 전용**이다. gameplay 로직·튜닝·RNG·ICE AI·알람·Dixie·하네스 cadence·VFX
  구현 파일은 변경하지 않는다. 기존 Accepted ADR도 변경하지 않는다.

## 회귀 테스트와 기존 단언 조사

- `web/tests/combat_grid.test.ts:72`: 실제 `renderGrid` 출력에서 `165/165`와 가득 찬
  12칸 게이지/초록색, `82.5/165`와 정확히 반만 찬 게이지/노란색을 검사한다.
  잘못된 `/100` 표기도 명시적으로 거부한다.
- 같은 파일에 최대 HP 누락·0·음수·NaN·Infinity fallback 5건을 추가했다.
- `web/tests/state.test.ts:145`: 독립된 실제 loadout으로 0..8개 슬롯을 채워
  `Equipped: N/8`을 검사하고 `N+9` 표기를 거부한다 (요청한 1..8 전부 포함).
- **수정 전 실행**: 두 테스트 파일에서 신규 테스트 **11 failed / 27 passed**.
  scaled ICE 2건 + 장비 수 9건이 실제로 실패했다. fallback 5건은 기존 코드에서도 통과한다.
- `web/`의 src·tests·e2e 전체 조사 결과 **버그 값을 고정한 기존 단언은 없었다**.
  기존 기대값 변경·테스트 삭제·완화는 없다. player HP·Alarm의 `/100`과 무관한
  숫자 `10` 단언은 유지했다. 추가 16건으로 **3624 → 3640 tests**.

## 밸런스 실측 (2026-11-01)

기본 no-idle, 53 missions, 100 runs/mission. 두 명령을 실제 실행했다.
ADR-0239의 새 기준선 승률과 **전 grade 정확히 동일**, 12개 비교 모두 **0.0pp**.
ADR-0239에는 전체 metric stdout 기준선이 없으므로 전체 stdout의 byte 비교를
주장하지 않고, 아래 실행 stdout과 기록된 승률 기준선의 일치를 증거로 남긴다.

| deck | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| opening 기준선 = 수정 후 | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| opening Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| PPL 기준선 = 수정 후 | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL Δpp | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### `npm run balance` stdout

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

### `npm run balance -- --deck ppl` stdout

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

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/renderer/combat_grid.ts:141` — 최대 HP 선택/fallback; `:175-176`에서 게이지·텍스트·색상 공통 사용.
- `web/src/core/state/state.ts:193` — 실제 채운 슬롯 수; `:194`에서 `EQUIP_SLOTS.length` 사용.
- `web/tests/combat_grid.test.ts:72` — scaled HP·게이지·색상·fallback 회귀 7건.
- `web/tests/state.test.ts:145` — 0..8개 슬롯 HUD 회귀 9건.
- `docs/playtest/EGO_LITE_PLAY_CHECK.md:158` — 실브라우저 발견 2건을 확정·수정 상태로 연결.
- 위 밸런스 stdout — 양 덱 ADR-0239 승률 기준선 0.0pp.

**Notes**: `npm run typecheck` exit 0; `npm run lint` exit 0 (0 errors,
기존 untouched `keyboard.ts:14` warning 1); `npm test` **160 files / 3640 passed /
0 failed (8.21s)**; `npm run build` exit 0 (118 modules, 469ms).
지정 IPv4 strictPort preview에서 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195
npx playwright test --ignore-snapshots --grep-invert demo-screenshots` 실행:
**76 passed / 4 skipped / 0 failed (4.6m)**. 첫 실행은 도구 120초 timeout으로
32개 통과 후 중단되어 600초 timeout으로 전체 재실행했다. preview는 EXIT trap으로 종료.
TypeScript LSP는 미설치·기존 설치 거절로 diagnostics 제공 불가; 설치/우회하지 않았다.
일부 jsdom audio play/load 미구현 stderr가 있었으나 테스트 실패는 없다.
이번 세션에서 ego-lite 재플레이/별도 스크린샷 시각 검증은 수행하지 않았다.
stage/commit 없음.

## 결과 (Consequences)

등급별 최대 HP와 실제 장비 수가 HUD와 일치한다. 전투 동작은 불변이며 재튜닝이나
재기준화는 없다. 기존 테스트가 다루지 않던 표시 계약을 실제 renderer/state 테스트가
검사한다. 실제 브라우저 관찰과 자동 단언은 어느 하나가 다른 하나를 대체하지 않는다.

## 변경 이력

| 날짜 | 변경 |
| --- | --- |
| 2026-11-01 | 오너 요청으로 표시 결함 2건 수정, 신규 회귀 16건, 양 덱 0.0pp 및 필수 게이트 실측. ✅ Implemented. |

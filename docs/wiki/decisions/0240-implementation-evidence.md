# ADR-0240 implementation evidence — 2026-11-01

Companion to [ADR-0240](./0240-idle-pressure-and-alarm-loop.md), not a new owner
decision. The governing workspace rule forbids modifying Accepted ADRs, so the
requested implementation record lives here; ADR-0240 itself remains unchanged.
The index links this record. No calibration arrays or ADR-0239 baseline changed.

## Implementation Status (2026-11-01)

**Status**: ✅ Implemented — idle → alarm → enemy damage and skill aggression.

**Evidence**:
- `web/src/core/types.ts:427` — immutable `idle_tick` action carrying latest input time.
- `web/src/core/state/state.ts:140` — `applyAction` routes the tick using the same
  `Date.now()` seam as the harness; no special browser-only gameplay path.
- `web/src/core/combat/idle_alarm.ts:12` — ONE `IDLE_ALARM_TUNING` block.
- `web/src/core/combat/idle_alarm.ts:21` — shared combat/idle/interval/cap gate.
- `web/src/core/combat/idle_alarm.ts:51` — production `tickAlarm` caller, speed **1**;
  `:62–63` persist `alarmLevel` and `lastAlarmTickMs` with a spread, not mutation.
- `web/src/core/combat/state_actions_combat.ts:235` — alarm passed to skill-use gate;
  `:260`, `:335` apply damage to skills AND auto-attacks after crit resolution.
- `web/src/core/combat/ice_ai.ts:117` — bounded skill probability, same RNG roll.
- `web/src/main.ts:375` — keyboard, pointer, visibility and mapped-input reset;
  `:1385–1394` dispatch only when due in visible gameplay, before VFX early-return;
  `:1481` covers direct touch program buttons too. No whole-file formatting.
- `web/scripts/balance_sim.ts:41`, `:137–157` — opt-in idle scalar/schedule, all due
  ticks via `applyAction`; `:166` exposes peak alarm for measurement-path tests.
- `web/tests/idle_tick.test.ts:60` — reducer writes without direct damage, cards or
  RNG; active-input gating, interval, reset, phase exclusion, cap, damage and
  aggression regressions (12 tests).
- `web/tests/balance_sim.test.ts:29` — idle-path determinism, no-idle and sub-threshold
  gating, long-idle multi-tick simulation; exact ADR-0239 tables for BOTH decks.
- `web/e2e/idle_alarm.spec.ts:24` — actual rAF raises alarm without direct damage;
  `:45` real input keeps alarm zero for 45 seconds. Both viewport projects pass.

**Notes**: `getAlarmMultiplier` is NOT connected to `iceAlarmSpeed` (ADR-0242 remains
next). `AUTO_ATTACK_INTERVAL_MS = 2000`, alarm interval 10000ms and cap 5 are
unchanged. Idle ticks neither call enemy turns nor advance Dixie/effects/cards.
Alarm zero returns the existing damage unchanged and adds no RNG draw. No files
under `raw/`, VFX files, `core/status.ts`, or Accepted ADRs were edited.

## Chosen values and open-question disposition

| Parameter | Chosen value |
| --- | --- |
| (c) Continuous input-free threshold N | **10 seconds** |
| Further continuous-idle ticks | **Every 10 seconds**, cap **5** |
| (j) Enemy damage | **+5% per alarm level**, additive relative to original damage; `floor(damage × (1 + 0.05 × level))` |
| (j) Enemy aggression | **+1 percentage point per level** to the authored aggression tier's skill-use probability, capped at 1 |
| Level-5 consequences | **×1.25 damage**, **+5pp skill probability** |

- **(c), threshold resolved**: 10s gives a full deliberation window, matches the
  existing alarm interval and avoids a new timer rate. Input resets the idle
  origin; active time does not accumulate. Hidden tabs, noncombat screens and
  overlays do not bank time into the next idle period. Levels already earned
  persist in the run; active input stops accrual, not the consequences.
  **Accessibility opt-out remains OPEN**: no unrelated settings policy invented.
- **(i), resolved**: reducer action, not rAF-only mutation. Decision (a) requires
  measurement through `applyAction` under fake `Date.now`; browser rAF is merely
  the caller. Both browser and harness use the same due-action gate. Reducer also
  rejects premature/duplicate/noncombat/capped ticks. It rebases the tick clock
  on the latest input so active elapsed time cannot leak into alarm time.
- **(j), resolved by grid below**: retain authored aggression tiers; add continuous
  skill-use probability instead of mutating the roster's tier/personality or
  introducing extra enemy attacks. Damage applies equally to both outgoing hit
  paths. Integer floors mean some small hits do not increase at level 1; no
  artificial minimum +1 is added. Select B, the strongest tested magnitude within
  ±3pp for the declared initial-deliberation scenario.
- **(l), resolved for reproducible measurement, NOT player telemetry**:
  `idleMsPerTurn` omitted/0 retains the original simulation exactly. A scalar
  repeats before every turn. An array is a fixed per-turn schedule, with zero
  after its end. CLI `--idle-ms 10000,0` is the tuning scenario: every encounter
  begins with a 10s deliberation, then uses the existing 2s cadence. This isolates
  one alarm level without changing Dixie's subsequent relative cadence. The
  distribution is a point mass, not an RNG sample: no extra gameplay draws.
  `--idle-ms 10000` is separately reported sustained-idle stress, reaching levels
  1–5. Neither distribution is claimed to model real users.
- **(k) merging with `player.alarm`**: **OPEN**, untouched; program-cost alarm and
  idle level remain distinct. No stealth ICE authoring decision: **(e) OPEN**.

### Browser regression found during implementation

Initial e2e failed with alarm 0 after 20s. Runtime inspection showed
`screen=mission_select`, `phase=combat`, `runPhase=combat`, `hidden=false`, a running
rAF and advancing clocks, but idle origin reset every frame. New-run combat
retains its mission-board screen tag; CONTINUE uses menu. The dispatch gate now
accepts menu, mission_select and far_grid_hub, and still requires a combat state.
The same failing test now passes on desktop and phone. Temporary diagnostics and
the debug journal were removed; existing tests were not changed to hide it.

## Measurement protocol and policy judgment

53 missions, 97 ICE types, **100 runs/mission**, seeds **1–100**, all six grades;
mission counts **4 / 16 / 11 / 10 / 9 / 3**. Real reducer, no encounter/deck retuning.
Baseline source: [ADR-0239 §re-baseline](./0239-vfx-spawn-rng-decoupling.md).
Policy source: [ADR-0229 §A1/A2/B/C](./0229-grade-curve-rebaseline.md).

1. **Harness-only stage**: opt-in field/action type added; production reducer still
   ignored idle ticks. Ran `npm run balance` and `npm run balance -- --deck ppl`
   with idle **disabled**. Both match ADR-0239 exactly (raw tables below).
2. **Game implementation stage**: repeated both default commands after chosen
   tuning. Both still match exactly. This separates tool change from game change.
3. **Idle enabled grid**: for each candidate, ran
   `npm run balance -- --idle-ms 10000,0` and
   `npm run balance -- --deck ppl --idle-ms 10000,0`.
4. **Additional stress**: ran both decks with scalar `--idle-ms 10000`, first at A
   and finally at B. These are different input conditions, NOT the default curve.

### Idle disabled — exact before/after (both stages)

| Deck / measurement | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening ADR-0239 | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening harness-only | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening final no-idle | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| PPL ADR-0239 | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL harness-only | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL final no-idle | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |

### Idle enabled — three-candidate grid (initial 10s hold)

| Candidate | Damage/level | Aggression/level | Deck | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | +1% | +0.5pp | Opening | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| A | +1% | +0.5pp | PPL | 100.0 | 79.1 | 98.9 | 83.2 | 44.4 | 24.7 |
| **B chosen** | **+5%** | **+1pp** | Opening | **100.0** | **88.3** | **70.5** | **38.9** | **36.2** | **0.0** |
| **B chosen** | **+5%** | **+1pp** | PPL | **100.0** | **79.1** | **98.9** | **82.9** | **44.4** | **24.7** |
| C rejected | +10% | +2pp | Opening | 100.0 | 88.3 | 56.4 | 38.6 | 34.2 | 0.0 |
| C rejected | +10% | +2pp | PPL | 100.0 | 79.1 | 98.3 | 81.6 | 44.1 | 0.0 |

**§A1**: reject/revert C (opening g3 **−14.1pp**); B maximum drift **0.6pp**, so
**§A2 reporting only**, no default re-baseline. A has no opening win-rate movement
at one level because of integer floors; B gives measurable pressure without C's
cliff. **§B1** opening B `100 ≥ 88.3 ≥ 70.5 ≥ 38.9 ≥ 36.2 ≥ 0` holds; **§B2** g6
**0.0%** holds. PPL is reference, not a monotonic target (§C3). Both PPL tables are
provided, including C's **−24.7pp g6** (§C2), even though C is not shipped.

| Chosen B: before → initial-idle after | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening before | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| Opening after | 100.0 | 88.3 | 70.5 | 38.9 | 36.2 | 0.0 |
| Δpp | 0.0 | 0.0 | 0.0 | −0.6 | 0.0 | 0.0 |
| PPL before | 100.0 | 79.1 | 98.9 | 83.0 | 44.4 | 24.7 |
| PPL after | 100.0 | 79.1 | 98.9 | 82.9 | 44.4 | 24.7 |
| Δpp | 0.0 | 0.0 | 0.0 | −0.1 | 0.0 | 0.0 |

### Sustained-idle stress is NOT within the 3pp window

| B: 10s before EVERY card | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- |
| Opening | 100.0 | 100.0 | 93.4 | 55.3 | 40.4 | 0.0 |
| Opening Δpp vs no-idle | 0.0 | +11.7 | +22.9 | +15.8 | +4.2 | 0.0 |
| PPL | 100.0 | 100.0 | 97.8 | 91.3 | 44.1 | 4.0 |
| PPL Δpp vs no-idle | 0.0 | +20.9 | −1.1 | +8.3 | −0.3 | −20.7 |

This does **not** prove idle is harmless or that all idle distributions fit ±3pp.
Existing Dixie fires every 3000ms only on a played-card enemy turn. With 12000ms
per input she fires each turn, versus alternating turns at baseline 2000ms. Idle
ticks themselves never fire her. That independent time-path benefit can outweigh
alarm damage. The initial-hold schedule avoids this confound after the first turn.
Changing companion cadence is outside ADR-0240 and was NOT silently bundled in.
The stress curve still satisfies opening monotonicity and g6=0. It is recorded as
a scenario reference, **not** a replacement for ADR-0239 or a claim of §A2 compliance
for sustained idle. Population-level calibration/companion timing remains follow-up.

## Raw balance output

Command prefixes (`npm`/`tsx`) omitted; numeric stdout preserved. Common header:
`Missions: 53, ICE types: 97, runs/mission: 100`. Opening deck:
`[backdoor, barrier, boost, cloak, decoy]`. PPL: grade-appropriate tier≤grade top 5.
All rows below use header:

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
```

### Harness-only no-idle AND final no-idle (identical rows, separately executed)

`npm run balance`:
```text
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```
`npm run balance -- --deck ppl`:
```text
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### A — `--idle-ms 10000,0`

Opening:
```text
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.6          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```
PPL (`--deck ppl`):
```text
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.2%     0.0%         5.9         22.2   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### B (chosen) — `--idle-ms 10000,0`

Opening:
```text
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         41.4   29/55
    3        11     70.5%     0.0%         6.8         13.9    4/30
    4        10     38.9%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.3          4.9    0/12
    6         3      0.0%     0.0%         5.1          0.0    0/0
```
PPL (`--deck ppl`):
```text
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.0   28/43
    3        11     98.9%     0.0%         5.7         30.2   18/39
    4        10     82.9%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         4.7         15.2   10/18
    6         3     24.7%     0.0%         5.1          1.2    0/2
```

### C (reverted) — `--idle-ms 10000,0`

Opening:
```text
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         39.0   27/53
    3        11     56.4%     0.0%         6.8         10.5    3/25
    4        10     38.6%     0.0%         6.5          2.7    0/11
    5         9     34.2%     0.0%         5.2          2.5    0/9
    6         3      0.0%     0.0%         4.5          0.0    0/0
```
PPL (`--deck ppl`):
```text
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         35.9   26/40
    3        11     98.3%     0.0%         5.7         25.8   13/34
    4        10     81.6%     0.0%         5.9         18.1    8/25
    5         9     44.1%     0.0%         4.7         13.0    8/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### A exploratory sustained stress — `--idle-ms 10000`

Opening:
```text
    1         4    100.0%     0.0%         2.4         90.3   88/92
    2        16    100.0%     0.0%         3.3         53.3   44/61
    3        11     98.9%     0.0%         5.6         29.8   19/39
    4        10     65.0%     0.0%         6.0         16.4    5/25
    5         9     43.8%     0.0%         5.3         12.9    5/16
    6         3      1.0%     0.0%         5.1          0.0    0/0
```
PPL (`--deck ppl`):
```text
    1         4    100.0%     0.0%         2.9         86.1   85/86
    2        16    100.0%     0.0%         3.4         49.6   44/60
    3        11     99.6%     0.0%         5.0         39.1   27/49
    4        10     94.9%     0.0%         5.4         27.4   13/36
    5         9     45.6%     0.0%         4.9         17.9   11/22
    6         3     33.3%     0.0%         5.0          2.1    0/6
```

### B final sustained stress — `--idle-ms 10000`

Opening:
```text
    1         4    100.0%     0.0%         2.4         90.3   88/92
    2        16    100.0%     0.0%         3.3         49.1   37/58
    3        11     93.4%     0.0%         5.6         21.6    9/32
    4        10     55.3%     0.0%         5.9         11.0    0/17
    5         9     40.4%     0.0%         4.8          9.3    1/13
    6         3      0.0%     0.0%         4.5          0.0    0/0
```
PPL (`--deck ppl`):
```text
    1         4    100.0%     0.0%         2.9         85.8   84/86
    2        16    100.0%     0.0%         3.4         44.8   37/57
    3        11     97.8%     0.0%         5.0         32.8   19/44
    4        10     91.3%     0.0%         5.4         20.5    7/29
    5         9     44.1%     0.0%         4.3         15.3    7/20
    6         3      4.0%     0.0%         4.5          0.2    0/0
```

## Verification

- `npm run typecheck`: exit 0, **0 errors**. Initial new-fixture errors (missing
  `aoe`, returning `vi.restoreAllMocks()` from teardown) were fixed before this pass.
- `npm run lint`: exit 0, **0 errors / 1 pre-existing warning** in untouched
  `web/src/input/keyboard.ts:14` (`no-explicit-any`).
- `npm test`: **158 files / 3599 tests passed / 0 failures** (+1 file / +17 tests).
  Existing jsdom audio play/load notices appeared in `tick_kill_loot.test.ts`.
- `npm run build`: exit 0, **118 modules**, final build after the browser gate fix.
- `npx vite preview --port 5195 --strictPort --host 127.0.0.1`, then
  `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`:
  **76 passed / 4 skipped / 0 failed**, 4.6 minutes, retries disabled. Includes four
  new idle cases (two tests × two viewports). Preview process stopped afterward.
- LSP diagnostics **unavailable**: tool reports TypeScript LSP not installed and
  installation previously declined. No installation/workaround attempted; compiler
  evidence above is available, but this is NOT a claim of clean LSP diagnostics.
- No commit, staging, repo-wide formatting, or changes to the forbidden files.

---

## 부록: 지속 유휴 역전의 원인 분해 (2026-11-01, 오케스트레이터 진단)

위 §Sustained-idle stress 는 "매 카드 전 10초" 시나리오가 승률을 **올린다**고 기록하고 원인을
"Dixie 3초 타이머" 로 적었다. **그 설명은 아래 측정과 맞지 않는다.** 하네스의 유휴 루프
(`balance_sim.ts:145-152`) 는 `clock = idleSinceMs + 10_000` 부터 10초 간격으로만 tick 하므로,
`--idle-ms` < 10초는 **시계만 진행시키고 알람은 절대 올리지 않는다**. 이 분리로 cadence 효과와
알람 효과를 독립 측정했다 (opening deck, 100 runs/mission).

| `--idle-ms` | 시계/턴 | 알람 | g1 | g2 | g3 | g4 | g5 | g6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 (기준) | 2000ms | 0 | 100.0 | 88.3 | 70.5 | 39.5 | 36.2 | 0.0 |
| 1000 | 3000ms | **0** | 100.0 | **100.0** | **98.9** | **64.0** | **44.1** | **1.0** |
| 3000 | 5000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 6000 | 8000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 8000 | 10000ms | 0 | 100.0 | 100.0 | 98.9 | 64.0 | 44.1 | 1.0 |
| 10000 | 12000ms | 최대 5 | 100.0 | 100.0 | 93.4 | 55.3 | 40.4 | 0.0 |

**확정된 사실**:

1. **역전은 알람 때문이 아니다.** `--idle-ms 1000` 은 알람이 **0 인데도** 곡선을 완전히 뒤집는다
   (g2 88.3 → 100.0, g3 70.5 → 98.9, g4 39.5 → 64.0).
2. **알람은 오히려 설계 의도대로 작동한다.** `--idle-ms 10000` 은 알람이 없을 때(8000)보다
   수치를 **되돌린다** (g3 98.9 → 93.4, g4 64.0 → 55.3). 즉 알람은 방향이 맞고, **구조적 효과를
   못 이길 만큼 약할 뿐**이다.
3. **시간 비례가 아니라 임계값 계단이다.** 1000 · 3000 · 6000 · 8000 이 **byte-identical** →
   임계는 **2000ms/턴과 3000ms/턴 사이**에서 한 번 넘어가고, 그 뒤로는 더 진행해도 변하지 않는다.
4. **RNG 시퀀스 발산이 아니다.** 계측 프로브(동일 seed A/B)에서 **턴당 `Math.random` 소비가
   동일**했다 (g3: 5.29 vs 5.26 draws/turn).
5. **근접 원인**: g3 프로브(seed 1)에서 idle 시 **전투가 더 적은 턴에 끝난다** (turns 7.27 → 5.64,
   enemyTurns 6.91 → 5.27) — 플레이어 총 피해는 같고(136.09) 적 1턴당 피해도 비슷하다
   (12.24 vs 12.42). 즉 승패 차이는 "적이 덜 때려서" 가 아니라 **교전이 더 짧아져서** 생긴다.

6. **RNG 는 무죄다 (결정적 반증).** 단일 미션(`first_contact`, g3, seed 1) 턴별 추적에서
   두 시나리오의 **난수 값 시퀀스가 byte-identical** 이었다 — t1 `barrier`
   `[0.6128 0.7207 0.4258 0.9948 0.4553]`, t3 `cloak`
   `[0.0674 0.3946 0.7671 0.2859 0.1909]` 가 양쪽 동일. 그런데 **같은 턴의 피해는 다르다**
   (t1 `barrier` **10 vs 24**, t3 `cloak` **5 vs 25**). 턴당 draw 수·소비 값까지 같은데 결과가
   다르므로, **차이는 RNG 분산이 아니라 시계에 의존하는 결정적 항**에서 온다.

**결론 (근본 기구의 위치)**: 원인은 **전투 해석 경로 안의 시간 의존 항**이다 — 즉
`calculateDamage` 의 입력(`programs.ts:82-100`)이나 그 뒤의 피해/회복/DoT 적용 중 **시계를
읽는 지점**이 2000ms/턴과 3000ms/턴에서 다른 값을 낸다. RNG·알람·하네스 유휴 분포는 모두
배제됐다. 특정 함수는 아직 지목하지 못했으나 (후보: 시간 게이트된 DoT/`regen` tick,
`AUTO_ATTACK_INTERVAL_MS` 경계와 상호작용하는 피해 적용 순서), **"RNG 아님 · 시계 의존 결정적
항"** 까지는 확정이다. 이는 하네스 모델의 인공물이 아니라 **엔진의 실제 성질**이므로,
수정은 별도 ADR 로 다루는 것이 맞다.

**오너 판단에 필요한 결론**: 이 역전은 **ADR-0240 이 만든 것이 아니라 시계 진행 자체의
기존 성질**이다 (알람 0 에서도 발생). ADR-0240 은 유휴 시에만 tick 하므로 no-idle 기준선을
바꾸지 않는다. 따라서 대응 선택지는 (i) 현행 유지(실제 입력에서는 알람이 5까지 차오르는
경우가 드묾), (ii) 알람을 강화해 구조적 효과를 상쇄(초기 유휴 drift 창을 깨므로 명시적
re-baseline 필요), (iii) 근본 시간 게이트를 별도 ADR 로 조사·수정. **결정은 오너 몫이다.**

측정 명령: `npm run balance -- --idle-ms {0,1000,3000,6000,8000,10000}`. 프로브는 저장소 밖
(`/tmp`) 임시 스크립트였고 저장소에는 남기지 않았다.

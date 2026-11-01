# ADR-0240 sustained-idle monotonicity evidence (2026-11-01)

Source/interpretation: [ADR-0240 Implementation Status](./0240-idle-pressure-and-alarm-loop.md#implementation-status-2026-11-01).
This companion records actual harness stdout, not estimated curves. Dixie N=2 throughout.
All measurements: 53 missions, 97 ICE types, 100 runs/mission, seeds 1–100.
Grade populations: 4/16/11/10/9/3 missions. No cadence, deck, catalog, or grade calibration edits.

## Reproduction

Before and after, from `web/`:

```sh
for deck in opening ppl; do
  for idle in 0 1000 10000; do
    npm run balance -- --deck "$deck" --idle-ms "$idle"
  done
done
```

Ablations and grid used process-local overrides, without source edits or new harness flags:

```sh
for tuning in '0.05 0' '0 0.01' '0 0' '0.01 0.01' '0.02 0.01' '0.03 0.01' '0.04 0.01'; do
  for deck in opening ppl; do
    TUNING="$tuning" DECK="$deck" node --import tsx --input-type=module -e '
      import { IDLE_ALARM_TUNING } from "./src/core/combat/idle_alarm.ts";
      const [damagePerLevel, aggressionPerLevel] = process.env.TUNING.split(" ").map(Number);
      Object.assign(IDLE_ALARM_TUNING, {damagePerLevel, aggressionPerLevel});
      console.log(JSON.stringify(IDLE_ALARM_TUNING));
      process.argv = ["node", "balance_harness.ts", "--deck", process.env.DECK, "--idle-ms", "10000"];
      await import("./scripts/balance_harness.ts");'
  done
done
```

The table blocks below preserve harness stdout, including every metric. npm's command banners
are omitted; labels state the tuning/deck/scenario. The actual diagnostic/grid invocations printed
`ABLATION`/`CANDIDATE` before the tuning JSON, respectively.

## Before: damage 0.05, aggression 0.01

### Opening, idle 0

```text
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

### Opening, idle 1000

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 1000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### Opening, idle 10000

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.0   86/92
    2        16     88.3%     0.0%         4.2         38.0   26/53
    3        11     48.4%     0.0%         6.5         10.2    4/23
    4        10      7.4%     0.0%         6.3          1.4    0/10
    5         9     11.7%     0.0%         5.1          1.5    0/8
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### PPL, idle 0

```text
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

### PPL, idle 1000

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 1000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### PPL, idle 10000

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         79.9   78/84
    2        16     79.1%     0.0%         4.3         34.9   24/39
    3        11     94.2%     0.0%         5.7         24.3   11/33
    4        10     77.7%     0.0%         5.9         15.7    7/21
    5         9     44.1%     0.0%         4.7         12.1    7/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

## Component ablations: idle 10000

### Damage only (0.05 / 0), opening

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.0   86/92
    2        16     88.3%     0.0%         4.2         38.0   26/53
    3        11     47.5%     0.0%         6.5         10.0    4/23
    4        10      7.4%     0.0%         6.3          1.4    0/10
    5         9     11.7%     0.0%         5.1          1.5    0/8
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### Damage only (0.05 / 0), PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         79.9   78/84
    2        16     79.1%     0.0%         4.3         34.9   24/39
    3        11     93.9%     0.0%         5.7         23.9   11/33
    4        10     76.9%     0.0%         5.9         15.5    7/21
    5         9     44.1%     0.0%         4.7         12.1    7/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### Aggression only (0 / 0.01), opening

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     71.1%     0.0%         6.9         14.0    4/30
    4        10     39.5%     0.0%         6.6          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.1          0.0    0/0
```

### Aggression only (0 / 0.01), PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.5   19/39
    4        10     83.2%     0.0%         6.0         22.3   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.1          1.2    0/2
```

Both components (0.05 / 0.01): see the two before/idle-10000 blocks above.

### Zero components (0 / 0), opening: cadence control, not a shipping candidate

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### Zero components (0 / 0), PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

## Candidate grid: aggression 0.01 fixed, idle 10000

### Damage 0.01, opening

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     71.1%     0.0%         6.9         14.0    4/30
    4        10     38.9%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.1          0.0    0/0
```

### Damage 0.01, PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.4   19/39
    4        10     83.2%     0.0%         5.9         22.2   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.1          1.2    0/2
```

### Damage 0.02, opening

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         41.9   28/56
    3        11     61.5%     0.0%         6.8         12.7    4/29
    4        10     38.6%     0.0%         6.5          3.9    0/13
    5         9     36.1%     0.0%         5.8          3.7    0/11
    6         3      0.0%     0.0%         5.1          0.0    0/0
```

### Damage 0.02, PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.2   27/44
    3        11     98.8%     0.0%         5.7         29.1   16/37
    4        10     82.6%     0.0%         5.9         20.5   10/27
    5         9     44.4%     0.0%         5.2         14.5    9/17
    6         3     24.7%     0.0%         5.1          0.5    0/1
```

### Damage 0.03, opening

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         40.9   27/56
    3        11     57.0%     0.0%         6.8         11.8    4/27
    4        10     38.6%     0.0%         6.5          3.5    0/12
    5         9     35.6%     0.0%         5.3          3.2    0/10
    6         3      0.0%     0.0%         4.8          0.0    0/0
```

### Damage 0.03, PPL

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.6   79/85
    2        16     79.1%     0.0%         4.3         37.4   26/43
    3        11     98.5%     0.0%         5.7         27.7   15/36
    4        10     81.6%     0.0%         5.9         18.9    9/25
    5         9     44.4%     0.0%         4.7         13.9    9/16
    6         3      0.0%     0.0%         4.8          0.0    0/0
```

Damage 0.04 opening/PPL grid stdout was identical to the two after/idle-10000
blocks below; these were separately executed as candidates before editing the constant.
All four candidates passed opening monotonicity. 0.04 retains the strongest tested
pressure and changes only one constant by one percentage point per level.

## After: shipped tuning damage 0.04, aggression 0.01

### Opening, idle 0

```text
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

### Opening, idle 1000

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 1000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### Opening, idle 10000

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         39.8   27/55
    3        11     49.3%     0.0%         6.5         10.8    4/25
    4        10     25.2%     0.0%         6.5          1.9    0/11
    5         9     12.4%     0.0%         5.2          1.9    0/9
    6         3      0.0%     0.0%         4.5          0.0    0/0
PASS: opening no-idle table byte-identical to pre-fix; idle 0 == 1000 (all metric bytes)
```

### PPL, idle 0

```text
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

### PPL, idle 1000

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 1000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### PPL, idle 10000

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
Missions: 53, ICE types: 97, runs/mission: 100

Idle: 10000ms (scalar = every turn; schedule = once, then 0)
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.3   79/84
    2        16     79.1%     0.0%         4.3         36.4   26/41
    3        11     97.1%     0.0%         5.7         25.8   12/35
    4        10     79.1%     0.0%         5.9         16.9    7/23
    5         9     44.1%     0.0%         4.7         12.8    7/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
PASS: ppl no-idle table byte-identical to pre-fix; idle 0 == 1000 (all metric bytes)
```

The PASS lines are from the Node assertion wrapper, comparing all six numeric stdout
rows as exact strings (headers necessarily identify different idle scenarios).
ADR-0239's published win-rate baseline is unchanged; pre-fix and post-fix no-idle
rows also match byte-for-byte in every other printed metric.

## Encounter-composition diagnostic: raw output

Temporary `web/scripts/idle_diagnosis.ts` used the real `runSuite` with each component
override and resolved each mission's first non-boss node via `makeInitialState` and
`resolveMatrixRoster`, matching `simulateCombat`. It was removed after measurement.

```text
g5 aleph_fragment roster=yakuza_enforcer wins/100 zero,damage,aggression,both=76/9/76/9
g4 black_ice_dream roster=goliath wins/100 zero,damage,aggression,both=0/0/0/0
g5 craft_job roster=neuromancer wins/100 zero,damage,aggression,both=0/0/0/0
g5 dixies_choice roster=yakuza_enforcer wins/100 zero,damage,aggression,both=76/9/76/9
g5 dixies_offer roster=neuromancer wins/100 zero,damage,aggression,both=0/0/0/0
g5 final_choice roster=loa_entity wins/100 zero,damage,aggression,both=98/78/98/78
g5 matrix_revelation roster=neuromancer wins/100 zero,damage,aggression,both=0/0/0/0
g4 mollys_razor roster=sense_net_reporter wins/100 zero,damage,aggression,both=79/10/79/10
g4 neuromancer_whisper roster=yakuza_enforcer wins/100 zero,damage,aggression,both=78/22/78/22
g4 sally_returns_arc3 roster=ta_sentinel wins/100 zero,damage,aggression,both=1/0/1/0
g4 ta_heist roster=goliath wins/100 zero,damage,aggression,both=0/0/0/0
g4 vegas_stakeout roster=goliath wins/100 zero,damage,aggression,both=0/0/0/0
g5 voodoo_loa_encounter roster=neuromancer wins/100 zero,damage,aggression,both=0/0/0/0
g5 winter_infiltrate roster=yakuza_enforcer wins/100 zero,damage,aggression,both=76/9/76/9
g4 hosaka_extraction roster=sense_net_reporter wins/100 zero,damage,aggression,both=79/10/79/10
g5 ta_defection roster=neuromancer wins/100 zero,damage,aggression,both=0/0/0/0
g4 dodgers_office roster=yakuza_enforcer wins/100 zero,damage,aggression,both=78/22/78/22
g4 tin_soldiers_end roster=ta_sentinel wins/100 zero,damage,aggression,both=1/0/1/0
g4 firebuds_chair roster=sense_net_reporter wins/100 zero,damage,aggression,both=79/10/79/10
```

## Regression proof

`npx vitest run tests/sustained_idle_balance.test.ts` before the production edit:

```text
AssertionError: g4 >= g5: expected 0.11666666666666667 to be less than or equal to 0.074
 Test Files  1 failed (1)
      Tests  1 failed (1)
```

After changing only `damagePerLevel: 0.05` to `0.04`:

```text
 ✓ tests/sustained_idle_balance.test.ts  (1 test) 1375ms
 Test Files  1 passed (1)
      Tests  1 passed (1)
```

The test guards the full unrounded opening curve, not the new tuning constant or an
exact replacement curve. Existing baseline, cadence-invariance, and alarm-effect
tests remain unchanged. This is measured preservation for the specified population,
not a proof of monotonicity for every possible seed or idle distribution. PPL remains
non-monotonic by ADR-0229 §C3; no PPL monotonicity claim is made.

## Final verification

Executed from `web/`, after the final production/test edit:

```text
> wetrun-web@0.1.0 typecheck
> tsc --noEmit

> wetrun-web@0.1.0 lint
> eslint src scripts --ext ts

/Users/emilio/projects/opencodework/Game/wet_run/web/src/input/keyboard.ts
  14:13  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any

✖ 1 problem (0 errors, 1 warning)

 Test Files  160 passed (160)
      Tests  3624 passed (3624)
   Start at  14:24:44
   Duration  8.35s (transform 2.33s, setup 611ms, collect 9.02s, tests 19.11s, environment 3.55s, prepare 5.96s)

vite v5.4.21 building for production...
✓ 118 modules transformed.
✓ built in 568ms
```

All commands exited 0. Existing jsdom HTMLMediaElement play/load notices appeared;
no failing tests. No existing test was edited, deleted, or weakened.

Preview command: `npx vite preview --port 5195 --strictPort --host 127.0.0.1`.
E2E command: `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`.

```text
IPv4 preview ready: 200
Running 80 tests using 1 worker
  4 skipped
  76 passed (4.6m)
```

No retries masked failures. Desktop and mobile idle-rAF/active-input tests passed.
Preview was stopped afterwards (shell exit trap plus listener cleanup).
LSP diagnostics were requested for both changed TS files; both returned:

```text
LSP server 'typescript' (.ts, .tsx, .js, .jsx, .mjs, .cjs, .mts, .cts) is NOT INSTALLED; user previously declined installation: proceed without LSP.
```

No LSP installation or workaround was attempted. Compiler success is not claimed
as LSP-clean evidence. Only the two changed TS files were formatted. No staging or commit.

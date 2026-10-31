# ADR-0244 — raw balance stdout (2026-11-01)

Companion evidence for [ADR-0244](./0244-clock-dependent-combat-term.md).
N was changed only in `DIXIE_ATTACK_EVERY_N_PLAYER_TURNS`: measured **2 → 1 → 3**,
then restored to **2**. Harness/source cadence and damage formula unchanged.
Every table below is a separately executed CLI run, **100 runs/mission**, seeds 1–100.
Commands run from `web/`. npm command preambles omitted; numeric stdout preserved.

Common stdout headers (present in every run):

```text
Balance harness — opening deck [backdoor, barrier, boost, cloak, decoy]
Missions: 53, ICE types: 97, runs/mission: 100
```

For PPL the first line is instead:

```text
Balance harness — PPL deck (grade-appropriate: tier <= grade, top 5)
```

Each run also prints `Idle: Xms (scalar = every turn; schedule = once, then 0)`
where X is the command's idle-ms value. All columns, including HP percentiles,
are retained below rather than only win rates.

## N=2 (shipped)

### Opening — `npm run balance -- --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### Opening — `npm run balance -- --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.2   86/92
    2        16     88.3%     0.0%         4.2         42.7   29/57
    3        11     70.5%     0.0%         6.8         13.8    4/30
    4        10     39.5%     0.0%         6.5          5.3    0/14
    5         9     36.2%     0.0%         5.8          4.9    1/12
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         80.7   79/85
    2        16     79.1%     0.0%         4.3         38.9   28/45
    3        11     98.9%     0.0%         5.7         30.2   19/39
    4        10     83.0%     0.0%         5.9         22.1   11/29
    5         9     44.4%     0.0%         5.2         15.3   11/18
    6         3     24.7%     0.0%         5.2          1.2    0/2
```

### Opening — `npm run balance -- --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.7         88.0   86/92
    2        16     88.3%     0.0%         4.2         38.0   26/53
    3        11     48.4%     0.0%         6.5         10.2    4/23
    4        10      7.4%     0.0%         6.3          1.4    0/10
    5         9     11.7%     0.0%         5.1          1.5    0/8
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.9         79.9   78/84
    2        16     79.1%     0.0%         4.3         34.9   24/39
    3        11     94.2%     0.0%         5.7         24.3   11/33
    4        10     77.7%     0.0%         5.9         15.7    7/21
    5         9     44.1%     0.0%         4.7         12.1    7/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

## N=1 (alternative, not shipped)

### Opening — `npm run balance -- --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.4         90.3   88/92
    2        16    100.0%     0.0%         3.3         53.3   44/61
    3        11     98.9%     0.0%         5.6         29.5   19/39
    4        10     64.0%     0.0%         6.0         16.3    6/25
    5         9     44.1%     0.0%         5.3         12.9    6/16
    6         3      1.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.9         86.1   85/86
    2        16    100.0%     0.0%         3.4         49.6   44/60
    3        11     99.6%     0.0%         5.0         38.8   23/49
    4        10     95.2%     0.0%         5.4         27.3   13/36
    5         9     45.6%     0.0%         4.9         17.9   11/22
    6         3     33.3%     0.0%         5.0          2.1    0/6
```

### Opening — `npm run balance -- --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.4         90.3   88/92
    2        16    100.0%     0.0%         3.3         53.3   44/61
    3        11     98.9%     0.0%         5.6         29.5   19/39
    4        10     64.0%     0.0%         6.0         16.3    6/25
    5         9     44.1%     0.0%         5.3         12.9    6/16
    6         3      1.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.9         86.1   85/86
    2        16    100.0%     0.0%         3.4         49.6   44/60
    3        11     99.6%     0.0%         5.0         38.8   23/49
    4        10     95.2%     0.0%         5.4         27.3   13/36
    5         9     45.6%     0.0%         4.9         17.9   11/22
    6         3     33.3%     0.0%         5.0          2.1    0/6
```

### Opening — `npm run balance -- --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.4         90.3   88/92
    2        16    100.0%     0.0%         3.3         49.1   37/58
    3        11     93.4%     0.0%         5.6         23.6   12/33
    4        10     55.3%     0.0%         5.9         11.0    0/17
    5         9     40.4%     0.0%         4.8          9.3    1/13
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         2.9         85.8   84/86
    2        16    100.0%     0.0%         3.4         44.8   37/57
    3        11     97.8%     0.0%         5.0         34.1   20/46
    4        10     91.3%     0.0%         5.4         20.5    7/29
    5         9     44.1%     0.0%         4.3         15.3    7/20
    6         3      4.0%     0.0%         4.5          0.2    0/0
```

## N=3 (alternative, not shipped)

### Opening — `npm run balance -- --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.1         87.6   85/92
    2        16     92.4%     0.0%         4.3         40.5   29/46
    3        11     45.6%     0.0%         7.4          5.3    1/20
    4        10     19.1%     0.0%         6.8          2.1    0/8
    5         9     17.2%     0.0%         6.0          2.0    0/5
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 0`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         4.3         79.8   77/83
    2        16     83.8%     0.0%         4.5         36.9   28/45
    3        11     95.2%     0.0%         6.2         26.1   10/39
    4        10     64.6%     0.0%         6.1         17.8    7/29
    5         9     44.4%     0.0%         5.3         15.4   11/18
    6         3     17.0%     0.0%         5.2          0.8    0/2
```

### Opening — `npm run balance -- --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.1         87.6   85/92
    2        16     92.4%     0.0%         4.3         40.5   29/46
    3        11     45.6%     0.0%         7.4          5.3    1/20
    4        10     19.1%     0.0%         6.8          2.1    0/8
    5         9     17.2%     0.0%         6.0          2.0    0/5
    6         3      0.0%     0.0%         5.2          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 1000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         4.3         79.8   77/83
    2        16     83.8%     0.0%         4.5         36.9   28/45
    3        11     95.2%     0.0%         6.2         26.1   10/39
    4        10     64.6%     0.0%         6.1         17.8    7/29
    5         9     44.4%     0.0%         5.3         15.4   11/18
    6         3     17.0%     0.0%         5.2          0.8    0/2
```

### Opening — `npm run balance -- --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         3.1         87.3   84/92
    2        16     92.4%     0.0%         4.4         35.2   24/40
    3        11     32.5%     0.0%         6.9          4.1    1/12
    4        10      1.5%     0.0%         6.4          0.2    0/2
    5         9      5.4%     0.0%         5.2          0.4    0/1
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

### PPL — `npm run balance -- --deck ppl --idle-ms 10000`

```text
grade  missions  win-rate  stalled  mean-turns  mean-HP-end  p5/p95
    1         4    100.0%     0.0%         4.3         79.0   76/82
    2        16     83.8%     0.0%         4.5         32.3   23/39
    3        11     86.1%     0.0%         6.1         20.4    8/34
    4        10     59.1%     0.0%         6.0         12.7    2/21
    5         9     43.8%     0.0%         4.8         12.2    7/15
    6         3      0.0%     0.0%         4.5          0.0    0/0
```

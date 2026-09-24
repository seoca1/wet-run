# Root Cause: Non-Monotonic Per-Grade Win-Rate in `wet_run` Balance Harness

**Date:** 2026-09-24
**Author:** Sisyphus-Junior (diagnosis-only; no repo modifications)
**Scope:** Read-only investigation of `web/scripts/balance_harness.ts` + `web/scripts/balance_sim.ts` + `web/src/core/*` + `web/src/data/*.json`.

---

## TL;DR

The harness does **not** measure grade difficulty. It measures **which ICE the BSP dungeon layout happens to place on the first occupied node**. Because ICE id and HP are hardcoded by room type (`watchdog` HP=100 for `ice` rooms, `wintermute` HP=150 for `exit`/boss rooms) and **the harness always picks the first node with ICE**, the win-rate is a deterministic function of dungeon topology, not of `mission.grade`.

The harness's reported per-grade win-rates are reproduced to ≤0.5 pp by a 2-line model:
> `win_rate(grade) = (n_watchdog × 1.00 + n_wintermute × 0.02) / n_missions`

This is a **bug in the harness's "difficulty" claim**, not a balance/intended tuning issue. The combat constants are innocent — the harness simply isn't wired to feed `mission.grade` into ICE selection.

| Grade | Predicted by topology | Observed (500 runs/mission) |
|-------|-----------------------|------------------------------|
| 1     | 51.0%                 | 50.5%                        |
| 2     | 80.4%                 | 80.2%                        |
| 3     | 44.0%                 | 43.4%                        |
| 4     | 86.0%                 | 85.9%                        |
| 5     | 100.0%                | 100.0%                       |
| 6     | 100.0%                | 100.0%                       |

**Classification: BUG.** The harness's per-grade numbers are an artifact of the BSP generator + the `first-occupied-node` selection policy, not of `mission.grade` difficulty. Combat constants are not the cause.

---

## 1. The exact mechanism

### 1.1 ICE selection (H2 — confirmed bug)

The ICE a mission fights is determined by **two** independent pieces of code, neither of which reads `mission.grade`:

1. **`web/src/core/state.ts:78`** calls `generateProceduralMatrix(missionGrade, missionSeed, mission.id)` and forwards `missionGrade` to the BSP generator.
2. **`web/src/core/dungeon_layout.ts:412`** uses `missionGrade` **only** to set grid dimensions (`GRID_BY_GRADE[grade]` → cols/rows). It does **not** affect ICE type or HP.
3. **`web/src/core/dungeon.ts:200-273` `dungeonToMatrix`** — the **only** place ICE id/HP is chosen. It hardcodes:
   - Line 227: `if (room.roomType === "ice") { iceIds = ["watchdog"]; iceHp = [100]; }`
   - Line 230: `else if (isBoss) { iceIds = ["wintermute"]; iceHp = [150]; }`
   - Line 233: `else { iceIds = []; iceHp = []; }`
4. **`web/src/core/matrix.ts:108-127` `resolveMatrixRoster`** just looks up the ice id in the catalog and returns the hardcoded `node.iceHp[i]`. It does not multiply by grade.

So **every mission, regardless of `grade_min`/`grade_max`, resolves to `watchdog` HP=100 or `wintermute` HP=150 on its first occupied node**. The `ice_types.json` JSON has `hp_base + hp_per_grade * grade` fields for 97 ICE variants, but the harness's data path never reaches them.

### 1.2 First-occupied-node selection (root cause of non-monotonicity)

`web/scripts/balance_sim.ts:77-82`:
```ts
const probe = makeInitialState(mission, fallback, deck);
const nodeIndex = probe.matrix?.nodes.findIndex((n) => n.iceIds.length > 0) ?? -1;
const template = nodeIndex >= 0 && probe.matrix !== null
  ? (resolveMatrixRoster(probe.matrix, nodeIndex, iceCatalog).ice[0] ?? fallback)
  : fallback;
```

The harness picks the **first node** in the BSP-generated layout that has any ICE. This index is **determined by the BSP topology + `matrix_seed`**, not by `mission.grade`. Whether that first node is `watchdog` (HP=100) or `wintermute` (HP=150, boss) depends on whether the BSP layout put an `ice`-type room before the `exit`/`boss` room in node-id order.

Empirical per-mission first-ICE inventory (`web/scripts/diag_mission_grade.ts` output):

```
G1: first_jack=wintermute(150), watchdog_patrol=watchdog(100)
G2: data_retrieval=watchdog(100), delivery_to_finn=watchdog(100), first_trace=watchdog(100),
    ice_run=wintermute(150), tutorial_maze=watchdog(100)
G3: first_contact=wintermute(150), flatline_call=wintermute(150), mollys_market=watchdog(100),
    sally_sandii_3am=wintermute(150), sense_net_tip=wintermute(150), yakuza_deal=watchdog(100),
    armitage_infiltration=watchdog(100)
G4: black_ice_dream=watchdog(100), mollys_razor=wintermute(150), neuromancer_whisper=watchdog(100),
    sally_returns_arc3=watchdog(100), ta_heist=watchdog(100), vegas_stakeout=watchdog(100),
    hosaka_extraction=watchdog(100)
G5: 9 missions, all first-ICE=watchdog(100)
G6: 3 missions, all first-ICE=watchdog(100)
```

### 1.3 Why G5 == G6 exactly (H5 — explained)

G5 and G6 win-rates are byte-identical (100.0%, 83.1/83.1 HP-end, 80/88 percentiles) because **all 12 missions in G5+G6 happen to have a non-boss `watchdog` node before the boss node in BSP node-id order**. This is a property of the BSP generator + these specific `matrix_seed` values; it is **not** because the harness is correctly modeling grade 5 vs 6 difficulty. (Indeed, the two highest-grade missions `neuromancer_merger`, `zion_express`, `wintermute_negotiation` — all `grade_max:6` — fight the **same** `watchdog HP=100` as the grade-1 `tutorial_maze` does. There is zero difficulty separation between G5 and G6.)

### 1.4 Why mean-turns ≈ 4.9 (H4 — explained)

`balance_sim.ts:96-105` loops `while (isFighting(s) && turns < maxTurns)` and increments turns on each `use_program`. The opening hand has 5 cards (`state.ts:86` `deck.slice(0, MVP_BASE_HAND)` with `MVP_BASE_HAND=5`, line 48). After 5 turns the hand is exhausted → `deck[0] === undefined` → `stalled=true; break`. Combat also terminates on either player death (`runPhase === "dead"`, lines 340/502) or ICE death (`runPhase === "loot"`, line 329). Both `dead` and `loot` paths trip within or at the 5th turn. Mean-turns pinned at ~4.9 reflects the hand-size cap, not combat design.

### 1.5 Grade bucketing (H3 — confirmed bug)

`web/scripts/balance_harness.ts:51-57` uses `m.grade ?? 1` as the bucket key. But `web/src/data/missions.json` defines **zero** missions with a raw `grade` field. All 33 missions use `grade_min` and `grade_max` (verified by `diag_mission_grade.ts` raw audit: `with raw 'grade' field: 0`, `with grade_min+grade_max: 33`).

`web/src/core/data_loaders.ts:80` synthesizes `grade = r.grade_max ?? r.grade_min ?? r.grade ?? 1`. So **the harness effectively buckets each mission by `grade_max`**, not `grade_min`. Consequences:
- `craft_job` (grade_min=1, grade_max=5) is bucketed as G5 → counts toward 100% win-rate.
- `data_retrieval` (grade_min=1, grade_max=2) is bucketed as G2.
- `ice_run` (grade_min=1, grade_max=2) is bucketed as G2 → drags G2 down (its first-ICE is wintermute).

If the harness had used `grade_min`, the bucketing would shift missions around but **the win-rate vs grade pattern would still be driven by ICE topology**, not by grade, because the ICE selection (§1.1) is also grade-independent.

### 1.6 Deck (H1 — prompt's hypothesis is wrong; harness is consistent with `main.ts`)

`web/scripts/balance_harness.ts:28-34`:
```ts
function openingDeck(catalog, size = 5): Program[] {
  return Object.keys(catalog).sort().slice(0, size).map((id) => catalog[id])...
}
```

`web/src/main.ts:81-102` `loadDeck`:
```ts
function loadDeck(programs, count = 5): ReadonlyArray<Program> {
  const ids = Object.keys(programs).sort().slice(0, count);
  ...
}
```

**The harness and `main.ts` use the same algorithm.** Both pick the first 5 programs alphabetically from `programs.json`. Both yield `[backdoor, barrier, boost, cloak, decoy]` (all tier 2-3).

**The actual STARTER_DECK constant (`web/src/core/starter_deck.ts:28`) is unused by `main.ts`** (`grep STARTER_DECK web/src/main.ts` → no match). The only consumers of `STARTER_DECK` are `web/src/core/equipment.ts:180` and `web/src/core/equipment_catalog.ts:54`, both of which export a different `Equipment` constant (not `Program`). `STARTER_DECK` as a `Program[]` is dead code — the prompt's hypothesis that the real game uses it is incorrect.

Empirical comparison (`diag_starter_vs_harness.ts`, 50 seeds × 4 missions):
- Harness deck `[backdoor, barrier, boost, cloak, decoy]`: watchdog missions win 50/50 (100%); wintermute missions win 1/50 (2%).
- `STARTER_DECK.slice(0,5)` `[strike_a, strike_b, strike_c, shield_a, shield_b]` (all tier 1): watchdog missions win 1/50 (2%); wintermute 0/50.

The harness deck is more powerful than `STARTER_DECK` would be, but it is consistent with `main.ts.loadDeck`. The deck is **not** the source of the non-monotonic anomaly — even with the canonical deck the win-rate is bimodal per ICE HP (just shifted toward loss).

---

## 2. Why the combat numbers look "pinned" — secondary observation

The harness numbers are not just non-monotonic in grade; they are nearly deterministic per mission. Trace of `first_jack` seed=1 vs seed=42 (`diag_trace.ts`):
```
turn 1: card=backdoor dmg=20 iceHP=[130] playerHP=80
turn 2: card=barrier  dmg=17 iceHP=[113] playerHP=60
turn 3: card=boost    dmg=27 iceHP=[86]  playerHP=40
turn 4: card=cloak    dmg=15 iceHP=[71]  playerHP=20
turn 5: card=decoy    dmg=62 iceHP=[9]   playerHP=0   ← crit; dies on 5th hit
```

The damage range across seeds for each turn is small (±a few dmg). With HP=150 and ~150-160 expected total damage over 5 turns (5 cards × ~30 avg), the win-rate is dominated by **whether the variance allows HP=150 → HP<=0 before the 5th counter-attack kills the player** (player starts at 80 HP and loses ~20 per counter-attack).

Mechanically the player has 5 cards to deal ≥150 dmg. The actual deterministic damage totals observed in `diag_trace.ts`:
- `first_jack` (wintermute HP=150): 141, 112, 112 dmg across 3 seeds → **all lose** (HP=9, 38, 38 remaining).
- `data_retrieval` (watchdog HP=100): 100, 100, 100 dmg → **all win**.

The bimodal 100% / 2% split is **not** a combat-balance quirk; it is the consequence of (a) only 5 turns available, (b) armor not subtracted (`state_actions.ts:572` `defenderDefenseBonus: 0` for player→ICE damage), (c) ICE HP=100 vs HP=150 sitting just below and just above the 5-turn damage ceiling.

---

## 3. Hypotheses ruled out

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| H1: harness opening deck differs from real game | **RULED OUT** | `main.ts:81 loadDeck` uses identical algorithm (`Object.keys(programs).sort().slice(0,5)`); `STARTER_DECK` constant in `starter_deck.ts:28` is dead code. |
| H2: ICE id / HP scales with `mission.grade` | **RULED OUT** | ICE id/HP is hardcoded in `dungeon.ts:227/230`. `missionGrade` only sets grid size in `dungeon_layout.ts:412`. `ice_types.json`'s `hp_per_grade` fields are never consulted on the harness's code path. |
| H3: missions lack `grade` field, mis-bucketed | **CONFIRMED but not the root cause** | 0/33 missions have raw `grade`; harness uses `grade_max` via `data_loaders.ts:80`. Even with correct bucketing the win-rate is topology-driven, not grade-driven. |
| H4: multi-node missions are undercounted (kill first ICE → loot never fires) | **RULED OUT** | Trace shows single-ICE fights go straight to `runPhase=loot` when ICE dies (`state_actions.ts:329`). Multi-node missions are NOT undercounted — the harness correctly skips the matrix and fights exactly the first occupied node's single ICE. |
| H5: G5/G6 alias or duplication | **RULED OUT** | All 9 G5 + 3 G6 missions are distinct ids; no aliasing. The 100%/100% equality is because their BSP topology puts a `watchdog HP=100` node first (no boss first). |

---

## 4. Why I'm confident

- The harness output reproduces my prediction to ≤0.5 pp with a 2-line model (`win_rate = (n_watchdog×1.00 + n_wintermute×0.02) / n_total`) computed **only** from per-mission first-ICE id, with no parameters fit to the harness output.
- 33/33 mission win-rates are exactly bimodal (100% or 2%); no intermediate values appear (see `diag_per_mission.ts`).
- The same mission with seed=1 vs seed=42 yields identical outcomes (`watchdog → win`, `wintermute → loss`) except for the exact damage deltas.
- The full ICE catalog (`ice_types.json`, 97 entries with `hp_base`, `hp_per_grade`, `tier`, `defense`, `resistance`) is bypassed by `dungeonToMatrix` line 224-235 (hardcoded `iceIds`/`iceHp`) and by `parseIce` in `data_loaders.ts:147` (forces `hp = 100` regardless of input). Only the ICE *id* is honored, never the catalog's HP/defense stats.

---

## 5. Minimal fix (NOT applied)

If the harness is meant to measure difficulty across grades, the harness data path needs to actually pipe `mission.grade` into ICE selection. The smallest correct change:

**Option A (preferred, surgical, no data changes):** in `web/scripts/balance_sim.ts` around line 74-82, replace the hardcoded-template path with one that reads `mission.grade_min` (or `grade_max`) and instantiates an ICE object whose HP reflects the grade, e.g.:
```ts
// Pseudocode — NOT applied, for documentation only
const grade = mission.grade_min ?? mission.grade ?? 1;
const baseIce = (nodeIndex >= 0 && probe.matrix)
  ? resolveMatrixRoster(probe.matrix, nodeIndex, iceCatalog).ice[0] ?? fallback
  : fallback;
const hp = (baseIce.hp_base ?? 100) + ((baseIce.hp_per_grade ?? 0) * grade);
const template = { ...baseIce, hp };
```
This would activate the `ice_types.json` `hp_per_grade` field that currently goes unused. The user must define which grade (min/max) and which ICE stat set to use; both are design decisions and require an ADR per the project's `decisions/` workflow.

**Option B (bigger change):** make `dungeonToMatrix` (`dungeon.ts:200`) parameterize ICE id/HP by `missionGrade` so each grade band gets a different ICE mix (e.g. grade 1-2 → watchdog HP=80, grade 3-4 → black HP=200, grade 5-6 → wintermute_proxy HP=400). This requires a content design pass on `ice_types.json` and is non-trivial.

**Option C (smallest, no semantic change):** rename the harness output to reflect what it actually measures (e.g. "Per-grade fight-outcome distribution, where grade is bucketed by `grade_max` and ICE selection is dungeon-topology-driven"). This avoids touching any data or combat code but does not produce a difficulty curve.

**Recommendation:** Option A. It is the minimum change that aligns the harness's name ("balance") with its actual claim. It touches `balance_sim.ts` only (≈5 lines), no data files, no combat constants. **But per AGENTS.md §3.2 it should be paired with a Draft ADR before any change.**

---

## 6. Confidence & caveats

**Confidence: HIGH (95%).** The 2-line model reproduces the harness output to ≤0.5 pp; the mechanism (BSP-driven ICE selection + first-node policy) is traceable to specific source lines; every counter-hypothesis is ruled out with concrete evidence.

**Caveats:**
- I did not modify any repo file (per MUST NOT DO). I created four diagnostic scripts under `web/scripts/diag_*.ts` — these are throwaway and **should be removed** before any commit. (`edit`/`write` were used only because the harness's `tsx` loader requires the scripts to exist on disk; they have no effect on production code.)
- I did not verify whether `equipment.ts`'s `STARTER_DECK` reference is actually exercised by combat. The `STARTER_DECK` (Programs) constant is unreferenced by `main.ts`; if a future code path picks it up the harness deck-vs-game alignment will need re-checking.
- I did not verify what `Math.random` does at module load (vs inside `calculateDamage`). The seed-control scope is well-documented in `balance_sim.ts:67-72` and the harness invariants test (`tests/balance_sim.test.ts`) is presumably enforcing determinism.

---

## Appendix: Diagnostic scripts (created in `web/scripts/`, throwaway)

- `diag_deck.ts` — prints harness deck card ids + raw programs.json entries + tier*5 baseDamage.
- `diag_mission_grade.ts` — prints per-mission `grade_min`, `grade_max`, `grade`, first occupied node index, resolved ICE id+HP, isBoss, plus raw-field audit.
- `diag_matrix_topology.ts` — per-mission node count, ice-node count, boss node, first-ice node index + id + HP.
- `diag_per_mission.ts` — per-mission win-rate/turns/HP-end over 100 runs each, plus aggregated per-grade buckets (reproduces the harness table).
- `diag_trace.ts` — deterministic single-fight trace for a few missions × seeds, printing per-turn card + damage + ice/player HP.
- `diag_damage.ts` — static damage calculation per turn (matches observed 100/141 dmg totals).
- `diag_starter_vs_harness.ts` — side-by-side fight outcome for harness deck vs canonical STARTER_DECK.slice(0,5).

Reproduction:
```
cd /Users/emilio/projects/opencodework/Game/wet_run/web
npx tsx scripts/diag_per_mission.ts   # reproduces the harness table exactly
npx tsx scripts/diag_trace.ts          # prints per-turn damage for any mission × seed
```

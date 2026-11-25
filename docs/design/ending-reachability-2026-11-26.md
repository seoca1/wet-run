# Ending reachability — the 7 categories, measured (2026-11-26)

**Question (carry-over, open since 2026-11-22).** `NEXT_SESSION_TODO` carries:
"`status_quo` (ADR-0337) — **여전히 열림.** 표시 엔딩에서 도달 불가(레거시 전용).
후속: 엔딩 카테고리 7종 도달성 조사(exile·transcendence·corruption 포함) → 유지/게이트/제거."

This page answers the *investigation* half. **유지/게이트/제거 is the owner's decision** — options and a
recommendation are at the end, no code was changed to produce this.

## 1. Method and evidence

| Evidence | Source |
|---|---|
| The catalog: 32 endings, 7 categories | `npx tsx -e 'import { ENDINGS } …'` → §3 table |
| The resolver's branch order | `src/core/combat/ending_resolver.ts:366-406` |
| Where the resolver is called | `grep -rn resolveEnding src/` → **one** call site: `src/core/state/state_actions_phases.ts:279` |
| Which action that is | `applyTerminalLoot` (`state_actions_phases.ts:237`) — the player confirms on the **terminal loot** screen |
| The death path | `runFailed` (`src/core/state/run_end.ts:60`) → `src/app/game_input.ts` clears `state` and returns to the title with `FLATLINE_MESSAGE`. **No ending screen, no resolver call.** |
| The campaign curve | `npm run campaign` (20 seeds × 33 starts = **660 contracts**) |
| What the tier already promises | `tests/design_conformance.test.ts:187-229`, `ending_resolver.ts:1-27` |

## 2. The resolver's six gates, in order

`resolveEnding(ctx)` (`ending_resolver.ts:366-406`) returns the first match:

| # | Gate | Fires when | Reachable? |
|---|---|---|---|
| 1 | `choices` loop | any arc ending declares `requiresChoice === choice` | **dead** — `ctx.choices` is hard-coded `[]` (`state_actions_phases.ts:277`) and **0 endings declare `requiresChoice`** |
| 2 | `factionScores` loop | score ≥ 50 for a faction an ending declares | **dead** — scores are live, but **0 endings declare `requiresFaction`** |
| 3 | `hpPct <= 0` | → `sacrifice` | **dead in play** — the resolver only runs on the terminal-loot path, which requires a live player |
| 4 | `credits > 18000` | → `control` | **live** (measured 0.2%) |
| 5 | `missionsCompleted >= 3` | → `liberation` | **live** (the contract's final leg) |
| 6 | `credits > 5000` | → `control` | **live in principle** — after gate 5, so only reachable when `missionsCompleted < 3` |
| 7 | fallback | → `status_quo` | **legacy only** — needs `missionsCompleted < 3` at the ending, which a fresh run cannot produce (see §4) |

## 3. Reachability by category

32 endings, 7 categories:

| Category | Endings | Arcs | Resolver-level | Shipped path | Mechanism / why not |
|---|---|---|---|---|---|
| `liberation` | 6 | 1-5 | ✅ | ✅ **the only one that fires normally** | gate 5: `missionsCompleted >= 3` = a finished 3-leg contract |
| `control` | 5 | 1-5 | ✅ | ✅ **but 0.2%** | gates 4/6: `credits > 18000` (or `> 5000` when the contract did not finish) |
| `sacrifice` | 5 | 1,2,3,5 | ✅ | ❌ | gate 3 needs `hp <= 0`; the resolver is only called from the terminal-loot confirmation, which a dead player never reaches. Death goes to `runFailed`, which shows the flatline screen and clears the run |
| `status_quo` | 6 | 1-5 | ✅ | ❌ (legacy saves only) | fallback gate 7. A fresh run always has a campaign, so the ending is resolved at `completed = 2` → `missionsCompleted = 3` → gate 5 wins. `state_actions_phases.ts:274` says so: "A run without a contract (tests, older saves) … reports 1" |
| `exile` | 2 | 2,4 | ❌ | ❌ | needs `requiresChoice`/`requiresFaction` — **nothing declares either** |
| `transcendence` | 4 | 2-5 | ❌ | ❌ | same |
| `corruption` | 4 | 2-5 | ❌ | ❌ | same |

**Totals.** Resolver-level: 4 of 7 categories live, **16 of 32 endings** nominally reachable.
Shipped path: 2 of 7 categories live, **11 of 32 endings** nominally reachable — and because the
resolver uses `find(...)`, only the **first** matching ending per arc is ever shown, so the
observable set is **5 liberation endings + up to 5 control endings**.

Verified by calling the resolver directly (`npx tsx -e`, context = 100/100 hp, 0 credits):

| Arc | completion (`missionsCompleted: 3`) | rich finish (`credits: 20000`) | contract-less (`missionsCompleted: 1`) |
|---|---|---|---|
| 1 | `arc1_first_blood` (liberation) — **not** `arc1_ice_breaker` | `arc1_cowboy_up` | `arc1_wage_slave` (status_quo) |
| 2 | `arc2_construct_friend` | `arc2_data_thief` | — |
| 3 | `arc3_zealot` | `arc3_double_agent` | — |
| 4 | `arc4_liberation_front` | `arc4_new_order` | — |
| 5 | `arc5_sprawl_free` | `arc5_control` | — |

`hp: 0` **does** resolve `arc1_cheap_death` (sacrifice) when the resolver is handed that context —
which is why §3 separates "resolver-level" from "shipped path": the branch is correct, the only call
site cannot produce the input.

## 4. The measured curve (`npm run campaign`, 660 contracts)

```
endings resolved under the CURRENT order (660 resolutions):
  sacrifice        403    61.1%
  liberation       256    38.8%
  control            1     0.2%
```

Precision worth keeping: only **257** of the 660 contracts reach the resolver (they are the ones
that finish all three legs). The other 403 are tallied `sacrifice` **by the harness**, not by
`resolveEnding` — the harness maps "died mid-contract" onto the ending it thinks is shown
(`campaign_survival.ts:189-192`). The resolver itself resolved 257 endings: **256 liberation, 1
control, and nothing else.**

> Harness output bug (minor): the line above the table says "every leg, 660 resolutions". It is one
> resolution per contract, and only for the 257 that finished. Worth a one-line fix in
> `campaign_survival.ts` so the number is not read as a per-leg count.

## 5. Three distinct causes — they need different fixes

The dead branches are dead for **three different reasons**, which is why one fix cannot revive them:

1. **No choice system** (`requiresChoice`) — the tier has no choices; `ctx.choices` is hard-coded
   `[]`. Reviving needs the choice system itself (ADR-0199 scope).
2. **Declared but never used** (`requiresFaction`) — faction scores *are* live and updated
   (`onMissionComplete`), but no ending names a faction. This one is a **one-line data change per
   ending** (add `requiresFaction: "…"`) and is already tracked as an expected failure in
   `tests/design_conformance.test.ts:188` (`it.fails("at least one ending declares
   requiresFaction …")`).
3. **Structurally outrun** (`status_quo`, `sacrifice`) — the branches are correct; the *call path*
   never satisfies them. `status_quo` loses to gate 5 because the contract always finishes at
   `missionsCompleted = 3`; `sacrifice` needs a context the only call site cannot produce.

## 6. What already enforces this boundary (so any change must update these)

- `tests/design_conformance.test.ts:206` — **no** ending declares `requiresChoice` (passes today).
- `tests/design_conformance.test.ts:188` — `it.fails`: at least one ending declares
  `requiresFaction`. **This test is expected to fail**; it is the tracked divergence, so the gap is
  visible in the suite rather than in prose.
- `tests/design_conformance.test.ts:212` — `missionsCompleted: 2` must **not** resolve
  `liberation`; `3` must. This is what keeps gate 5's threshold honest.
- `ending_resolver.ts:1-27` — the header states the tier scope and the ADR-0314/ADR-0337 history.

## 7. The measurement the recommendation depended on (done 2026-11-26)

Option B/D both said "wire `requiresFaction`, but measure first". **The measurement is in, and it
says wiring alone cannot work.** Probe: `npm run faction-reach`
(`scripts/faction_reach_probe.ts`, deterministic enumeration — faction deltas depend only on mission
and ICE ids, not on play).

| Fact | Value | Source |
|---|---|---|
| Gate 2 needs | score ≥ **50** (`FRIENDLY`) | `faction_reputation.ts:21` `TIER_THRESHOLDS`, read at `ending_resolver.ts:377` |
| A completed mission of that faction gives | **+10** | `MISSION_REWARD_MAP` |
| Killing that faction's ICE costs | **−5** | `KILL_PENALTY_MAP`, applied at `combat/victory.ts:87` |
| A run is | **3** missions | `CONTRACT_LENGTH = 3` |
| Theoretical maximum in one run (3 legs, one faction, no kills of it) | **30** | 10 × 3 |
| **Observed maximum** over all 33 Sprawl contracts | **20** | `npm run faction-reach` |
| Scores persist across runs? | **No** — `makeInitialState` and `slotToGameState` both set `DEFAULT_FACTION_SCORES` (all 0) | `state.ts:141`, `state.ts:533` |

**So `requiresFaction` wiring is insufficient by construction**: the gate is a five-mission bar
(50 ÷ 10) and a run is three missions. Adding the data would move the dead branch from *"declared but
nothing names it"* to *"named but unreachable"* — no ending becomes visible.

Two further things the probe surfaced, both worth their own line:

- **`maas` scores 0** on the Sprawl board: no sprawl mission id contains `"maas"`.
- **The mission-faction rule is substring-based and collides**: `getMissionFaction`
  (`state_actions_phases.ts:757-763`) matches `"ta"` anywhere, so `vegas_stakeout` reads as `ta`
  because *stakeout* contains `"ta"`. `first_trace` reads as `null` only because `"ta"` does not
  appear in it. Any ending wired to a faction inherits that rule.

## 8. Options (owner decides) — revised by the measurement

| Option | What it means | Cost / consequence |
|---|---|---|
| **A. 유지 (leave as is)** | Keep the 32-ending catalog; unreachable endings stay declared for later arcs | Nothing to do. Cheapest. The gap stays visible via the `it.fails` test |
| **B. 게이트 by wiring `requiresFaction`** | Add the data so gate 2 can fire | **Measured: does not work alone.** Max reachable is 30 vs a gate of 50 — nothing becomes visible. Only becomes viable together with **B′** |
| **B′. Lower the gate and/or persist scores** | Either move the FRIENDLY gate down to what a run can reach (≤ 20 observed), or carry `factionScores` across runs (a hoard-like change) | Each is a **balance/design change**, not a data line: the gate is also the Info Market price tier (`TIER_MULTIPLIERS`), so lowering it changes shop prices too. Persisting scores changes the run-start shape the goldens pin |
| **C. 제거 (delete the unreachable ones)** | Drop the 21 unreachable endings | Shrinks `ENDING_DATA`; must update `design_conformance.test.ts:108` (32 endings) and the 7/7/6/6/6 test. Irreversible against `docs/design/story_skeleton.md` (ADR-0010) |
| **D. 유지 + 명시 (my revised recommendation)** | **A**, plus a comment at each unreachable ending naming *why* (no choice system / no faction named / out of a run's reach), and fix the two probe findings above | No gameplay change, no authored content deleted, and the next person does not re-derive this. The `it.fails` test becomes the tripwire: it fails the day someone wires a faction, which is exactly when the gate question must be re-answered |

**Recommendation: D.** The measurement removed B and B′ from "cheap data change" territory — both are
balance changes that would move shop prices or the run-start goldens, so they are yours, not a
refactor. D leaves the catalog honest without spending a balance decision.

## 9. Open questions (owner)

1. Is the 32-ending catalog a **story promise** (keep declared, wire later) or **current content**
   (only what ships)? C is only on the table if the former is false.
2. **Is `FRIENDLY = 50` the right bar for a 3-mission run?** Measured reach is 20. If faction
   endings are wanted, the gate and the run length have to be reconciled — and the gate is shared
   with Info Market pricing.
3. Should `factionScores` survive a run (like the hoard and the owned gear do), or reset? Today it
   resets, which is what makes the gate unreachable.
4. `sacrifice` currently has no path to the ending screen — death shows the flatline screen and
   returns to the title. Intended (ADR-0263), or should death resolve an ending? **Design, not a bug.**
5. Should the `it.fails` test at `design_conformance.test.ts:188` stay as the tracked divergence, or
   become an `it.todo` naming the measurement that would unblock it?


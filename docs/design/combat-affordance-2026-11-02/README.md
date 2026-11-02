# Combat affordance + missing feedback — evidence, 2026-11-02

Implements [ADR-0251](../../wiki/decisions/0251-truthful-program-affordance-and-combat-integrity-rules.md) (Accepted, owner: "추천대로 하자"), the two slices chosen in the [Oracle synthesis](../combat-directions-2026-11-02/oracle-review-and-synthesis.md). Unstaged, uncommitted. HEAD `6b959c27`.

## What the player sees now

| Moment | Before (HEAD) | After |
| --- | --- | --- |
| Hand, 80×50 / 60×40 | `HAND:  [back] [barr] [boos] [cloa] [deco]` | `HAND` + one row per slot: `1 BACKDOOR  COST +2  → 40/100   TARGET ICE` |
| Hand, 40×60 | `HAND:  [back] [barr] [boos] [cloa]` — **the 5th slot is not drawn** | legend `HAND        COST AFTER    TARGET` + 5 rows `1 BACKDOOR  +2   40/100   ICE` |
| `double_alarm` | no COST shown | `COST +4` for a cost-2 program (×2, floored, the reducer's own helper) |
| Over the cap | no warning; the press fails with `Cost too high` | `→ BLOCKED` in words, grey ink; 100/100 is **not** blocked |
| AoE (`sweep`) | nothing | `TARGET ALL ICE` |
| Touch buttons | `1.back` … no `aria-label` | `1 COST+2 / BACKDOOR / → 2/100 / ICE` and `aria-label="1 BACKDOOR, COST plus 2, to 2 of 100, target ICE"`; the canvas leaves the hand band to them while the overlay is mounted |
| Touch acknowledgement | `> 2.boos` after tapping BARRIER (read the hand after the play) | `> 2.BARRIER` |
| A burn/slow proc lands | silent (state changes, glyph `[B1L1]` appears) | overlay `[ICE BURN+SLOW applied]` + log/HUD line `ICE BURN+SLOW on` |
| A status ends | silent | log/HUD line `ICE BURN off` (also slow/vulnerable spent, shield broken, ICE-cast effects ending in the enemy turn: `ICE2 REGEN off`) |

Not shown, by contract: role, authored damage / damage_bonus, effect text, description, kill chance. JSON `role` is not loaded. Input is unchanged: digit N plays row N immediately, no selection/confirm/cancel.

## Captures

Actual `renderCombatScreen` + `composeCombatScreen` grids (reduced motion; base grid + VFX layer, exactly what `main.ts` draws) plus the HUD column at the preset width (24/20/16), drawn through the game's own `AsciiRenderer` bundled with esbuild in headless Chromium, 10×18 cells, DPR 1 — same method as the Matrix slices ([capture-receipt.json](capture-receipt.json)). *Before* = HEAD source extracted with `git archive`; *after* = working tree; both driven by their real reducer from the same fixture (first mission, first catalog ICE at 165 HP, the real opening hand `loadDeck` builds) — [fixture-before.json](fixture-before.json), [fixture-after.json](fixture-after.json).

| Case | What it shows | 80×50 | 60×40 | 40×60 |
| --- | --- | --- | --- | --- |
| `hand` | opening hand at COST 38 | [pair](hand-80x50-pair.png) | [pair](hand-60x40-pair.png) | [pair](hand-40x60-pair.png) |
| `double-alarm` | `double_alarm`, COST 40 | [pair](double-alarm-80x50-pair.png) | [pair](double-alarm-60x40-pair.png) | [pair](double-alarm-40x60-pair.png) |
| `aoe-blocked` | `sweep` (AoE) + `kraken` over the cap at COST 97; `barrier` exactly 100 | [pair](aoe-blocked-80x50-pair.png) | [pair](aoe-blocked-60x40-pair.png) | [pair](aoe-blocked-40x60-pair.png) |
| `status-apply` | play with both 20% procs (`Math.random` 0.1) | [pair](status-apply-80x50-pair.png) | [pair](status-apply-60x40-pair.png) | [pair](status-apply-40x60-pair.png) |
| `status-expiry-start` | ICE burn with 1 turn left (`[B1]`) | [pair](status-expiry-start-80x50-pair.png) | [pair](status-expiry-start-60x40-pair.png) | [pair](status-expiry-start-40x60-pair.png) |
| `status-expiry` | next play, no proc: burn ends | [pair](status-expiry-80x50-pair.png) | [pair](status-expiry-60x40-pair.png) | [pair](status-expiry-40x60-pair.png) |

Raw: `<case>-<size>-{before,after}.{txt,hud.txt,json,png}`, `*-image-diff.json`. Width checks (`visual-qa tui-check`): **18/18 after frames** exact width, 0 overflow lines, no border drift, no ANSI (`*-after-width-check.json`). Exhaustive row check ([exhaustive-hand-check.txt](exhaustive-hand-check.txt)): all **84** hand rows in the 18 after frames match fixture order, `+COST` (×2 under `double_alarm`), `AFTER`/`BLOCKED` and `ICE`/`ALL ICE`, inside the rails. Widest full row: 46 chars in the 56-cell inner width (60×40); compact rows ≤ 33 of 34 cells (40×60).

## Live trace — the displayed number consumes exactly that row and that COST

Preview build on `127.0.0.1:5195` (pid 75395, not restarted; serves the rebuilt `dist/`, `index-B_nl8RTM.js`), real keys/taps in a separate headless Chromium: [before-trace.json](live/before-trace.json), [after-trace.json](live/after-trace.json), screenshots in [live/](live/).

| Step (after) | Displayed row | Result |
| --- | --- | --- |
| desktop, key `2` | `2 BARRIER   COST +3  → 3/100` | deck loses `barrier` only; COST 0 → **3** |
| desktop, key `1` | `1 BACKDOOR  COST +2  → 5/100` | deck loses `backdoor` only; COST 3 → **5** |
| mobile (iPhone 14), tap button 2 | `2 COST+3 / BARRIER / → 3/100 / ICE` (66×71 px) | deck loses `barrier` only; COST 0 → **3** |
| desktop, `double_alarm` seeded at COST 94, key `2` | `2 BARRIER   COST +6  → 100/100` | deck loses `barrier`; COST 94 → **100** |
| same, key `1` | `1 BACKDOOR  COST +4  → BLOCKED` | `Cost too high — program failed`; deck and COST unchanged |

Before: the same keys consumed the same programs, but the screen only said `[barr]`/`[back]` (no COST), and at 40×60 slot 5 was never drawn. (The `double_alarm` scenario seeds `activeMutators` through the e2e handle because no menu enables mutators yet.)

## Tests

| Set | Result |
| --- | --- |
| New/changed tests against HEAD | **29 failed / 16 passed + 2 suites fail to load** ([tests-before-head.txt](tests-before-head.txt)) |
| Same, with only `program_affordance.ts` copied into HEAD | **43 failed / 43 passed** ([tests-before-head-plus-helper.txt](tests-before-head-plus-helper.txt)) — every COST / cap / `double_alarm` / slot-order test passes on **HEAD's reducer**: the helper reproduces the original charge exactly |
| After | **86 passed** ([tests-after.txt](tests-after.txt)) |

New: `program_affordance.test.ts` (22: COST = reducer charge normal and `double_alarm`; BLOCKED = refusal at 97/98 and 94/95; slot N = `select_program` N and removes exactly that row; `ALL ICE` only for `aoe`; row text; no forbidden words; zero `Math.random`/`Date.now`; placement; wiring), `combat_status_feedback.test.ts` (11), `combat_event_sfx.test.ts` (12). `combat_grid.test.ts` +9 (all three grids keep rails and every slot, BLOCKED ink, stable rows, overlay band). `touch.test.ts` +2 (labels + `aria-label` = canvas facts, index callback, 44 px floor kept).

Existing assertions changed: **none weakened**. `touch.test.ts` "program row (P12)" fixture changed shape (`{id}` → affordance rows) because `updateProgramRow`'s input type changed; its 8 assertions are unchanged. During green-up, I rewrote my own new slice-B expectations from per-kind lines (`ICE BURN on`, `ICE SLOW on`) to one line per holder (`ICE BURN+SLOW on`) so the news fits the HUD's 4 log lines, and widened the compact AFTER column by one after review; the red numbers above were re-run with the final test files.

## Verification

| Command | Result |
| --- | --- |
| `npm run typecheck` | 0 errors |
| `npm run lint` | 0 errors; pre-existing `src/input/keyboard.ts:14` warning |
| `npm test` | **174 files / 3914 passed / 0 failed** (baseline 171 / 3857; +3 files / +57) |
| `npm run build` | PASS ([build.txt](build.txt)) |
| `npx prettier --write` on the 10 edited `src/**` files; `--check "src/**/*.{ts,tsx}"` | PASS |
| `npm run balance` / `-- --deck ppl` | [opening](balance-opening.txt) / [PPL](balance-ppl.txt): `cmp` byte-identical to the HEAD runs ([before](balance-opening-before.txt), [before](balance-ppl-before.txt)) and to `matrix-entry-gate-2026-11-01/balance-*.txt` — opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` (ADR-0239) |
| E2E `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` | **82 passed / 4 skipped / 0 failed** ([e2e.txt](e2e.txt), final build). An earlier run on the previous build ([e2e-run1.txt](e2e-run1.txt)) had 1 failure: `idle_alarm.spec.ts:48` hit the 30 s test timeout (the test itself takes 27–29 s with a fake clock; it does not touch the hand). Run alone twice: 26.9 s / 27.1 s pass; it passed in both later full runs. Recorded as timing flake, not hidden |
| Frontend draft guard | clean (4 files) |
| LSP | not used; `tsc` is the gate |

## Sound IDs

| ID | Wired to | |
| --- | --- | --- |
| `boss_intro` | fight starts with `bossPhase > 0` | wired |
| `phase_change` | boss phase rises mid-fight (replaces a dead `VICTORY` branch in `main.ts`) | wired |
| `credit_gain` | `player.credits` rises | wired |
| `loot_drop` | material count rises | wired |
| `heal` | live player HP rises (loot-screen heal) | wired |
| `death` | player HP reaches 0 (not jack-out) | wired |
| `credit_spend` | — | **left unwired**: nothing in the game lowers `player.credits` (`purchaseItem` has no caller) |

Dispatch is the existing two controller sites (`pickTransitionSfx(previous, nextState)`); the reducer gained no audio side effect. Not verified by ear — unit-tested picker + the e2e `sound_triggers.spec.ts` run without errors.

## LOC (total / pure, pure = non-blank, non-comment)

| File | Before | After |
| --- | --- | --- |
| `src/core/combat/program_affordance.ts` (new) | — | 145/88 |
| `src/core/combat/state_actions_programs.ts` | 401/351 | 438/380 |
| `src/core/combat/state_actions_combat.ts` | 481/388 | 491/396 |
| `src/core/combat/combat_sfx.ts` | 68/32 | 140/81 |
| `src/core/status.ts` | 256/182 | 328/234 |
| `src/core/state/onboarding.ts` | 146/72 | 147/73 |
| `src/renderer/combat_grid.ts` | 259/221 | 292/247 |
| `src/renderer/run_screen.ts` | 136/127 | 141/129 |
| `src/input/touch.ts` | 325/261 | 351/280 |
| `src/main.ts` | 1796/1567 | 1809/1572 |

`state_actions_programs.ts`, `state_actions_combat.ts` and `main.ts` were already over the ~250 pure-LOC guide; `touch.ts` was already over it (261 → 280).

## Visual QA

Contrast ([contrast.json](contrast.json)), 4 palette modes × standard/high contrast: hand rows (CYAN_LIGHT) ≥ **10.93:1**; BLOCKED rows (GRAY_MID) **6.58:1**; header/legend and `status_apply` overlay (YELLOW_AMBER) ≥ **10.15:1**; HUD status lines (GREEN_NEON) ≥ **13.96:1**; touch labels 15.38:1, BLOCKED 6.58:1. Minimum **6.58:1**.

Reviewer: a read-only `explore` subagent (a different model, not a human and not a dedicated design reviewer) read the frames, HUDs, fixture, live trace and contrast. Verdict **REVISE** with one defect — in compact rows only one space separated `BLOCKED`/`100/100` from the target — **fixed** (column widened, re-captured, re-checked) and one note that it had only sampled frames, answered by the exhaustive 84-row check above. Taste note: VFX glyphs overwrite the top rail during impact frames (pre-existing VFX behaviour, transient, unchanged).

| Item | Verdict | Evidence |
| --- | --- | --- |
| Every slot listed, numbered in input order, all grids | PASS | 84/84 rows; 40×60 regains slot 5 |
| COST / AFTER / BLOCKED = reducer | PASS | unit tests on HEAD reducer + live trace incl. `double_alarm` + cap |
| ALL ICE only for AoE | PASS | `aoe-blocked-*` |
| No role/damage/effect/kill claims | PASS | `program_affordance.test.ts` "names nothing…" |
| Rails, no overflow, one screen | PASS | 18/18 width checks |
| Colour redundant | PASS | BLOCKED worded + grey; target worded; status worded |
| Reduced motion keeps information | PASS | status on/off in HUD text; captures are reduced-motion |
| Touch ≥ 44 px, `aria-label` = canvas | PASS | 66×71 px; labels in trace |
| Text contrast ≥ 4.5:1 | PASS | min 6.58:1 |
| Input semantics unchanged | PASS | no selection state; ADR-0243 tests untouched and green |
| Semantic tree for the canvas hand | FAIL (inherited) | canvas; only the touch buttons are announced |

## Known limits / found, not changed

- **Killing blow charges no COST** (existing): `useProgram`'s victory branch never writes `player.alarm`, so on the play that defeats the last ICE the row's `→ N/100` overstates. Kill prediction is forbidden, so the label cannot know. ADR-0251 open question (a).
- **`tickIceEffects` index bug** (existing): it keeps using original indices after removing an earlier effect; shield(1)+powered(3)+regen(3) ticks to `powered 3, powered 2, regen 2`. Status mechanics — not changed; ADR-0251 open question (b). The end log counts before/after, so it reports only effects that really left.
- 40×60: the ICE HP text is cut by the rail (`50/`) and the 62-char combat-entry hint overwrites the rail — both pre-existing, not in this slice's rows.

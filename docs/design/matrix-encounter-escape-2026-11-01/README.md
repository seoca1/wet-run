# Matrix encounter escape — evidence, 2026-11-02

Follow-up to [ADR-0250](../../wiki/decisions/0250-encounter-gate-on-entry.md) (decisions unchanged). Owner, after ADR-0250 shipped: "이벤트가 끝나고 좌우 두군데 밖에 선택지가 없는데 계속 이벤트가 반복되서 빠져나오지 못했어." / "아직 못빠져나와." — screen: **"보드 + 'enter ICE' + 이벤트 반복"**. Unstaged, uncommitted.

## Step 1 — reproduction on the 5195 build, before any change

Live keypress logs against the running preview (pid 75395, build `index-De0KFiDO.js` at the time), boot mission *Aleph Fragment*, node 1 = the 2-neighbour ICE node (`adjacent [0, 26]`): [live/before-trace.txt](live/before-trace.txt) (raw: [live/before-trace.json](live/before-trace.json)), canvas shots `live/before-*.png`. Script: [escape-live.mjs](escape-live.mjs).

| Path | Reproduces "board + enter ICE + event repeats"? | Evidence |
| --- | --- | --- |
| (a) board after BYPASS on node 1 | **No.** Footer `↑↓: pick route \| ESC: back`, Enter at rest → `Encounter resolved — choose an adjacent route.`, ↓ + Enter → `cur 0`. Renderer `gates()` and reducer `encounterGates()` agree (both cleared ∪ bypassed). | `a-bypass` in the trace, [board](live/before-a-bypass-post-bypass-board.png) |
| (b) CONTINUE onto the unresolved node (BREACH → combat → autosave → reload → CONTINUE) | **Yes.** Restored `cur 1, decision null` on the **board**, footer `ENTER: enter ICE \| ICE blocks travel \| ESC: back`; ↓ + Enter → decision reopens; every departure attempt reopens it. | `b-continue`, [restored](live/before-b-continue-restored.png) |
| (c) **ESC on the encounter screen** (in-session, no reload) | **Yes — the most direct path.** ESC = `jack_out`: the reducer sets `phase: "menu"` but leaves `runPhase: "matrix"`, and `main.ts` routes drawing and input by `runPhase`, so the **board** comes back with the footer `ENTER: enter ICE \| ICE blocks travel \| ESC: back`; ↓ (either neighbour) + Enter reopens the encounter. Repeats forever. The board footer itself told the player `ESC: back`. | `c-escape`, [after ESC](live/before-c-escape-after-esc.png) |
| (d) committing the **JACK OUT verb** | **Yes.** Same state as (c): message `Jacked out — run abandoned`, board still drawn, next Enter → `Travel blocked…` and the encounter again. "Abandon run" never left the run. | `d-jackout`, [after JACK OUT](live/before-d-jackout-after-jackout.png) |

The lead's own keypress trace also reproduced exactly (`keys` scenario): Enter with nothing selected → hint only; ↓ Enter → PROBE paid 8; Enter again → **no change at all**; ← → **SCAN** (no utility in hand) → Enter → **no change at all**; `cur` stays 1.

**Verdict:** (a) does not reproduce; (b) reproduces the owner's words; (c)/(d) reproduce them too, without a reload — the two "ways out" a stuck player reaches for (ESC, which the footer called `back`, and JACK OUT, labelled "abandon run") both dropped the player back on the same board with `enter ICE`, and Enter reopened the same event. Root cause is a trap state, not the arrival gate itself: `phase: "menu"` + `runPhase: "matrix"` (no screen change), plus ADR-0250's surviving departure gate for nodes reached without an arrival.

## Step 2 — what changed (ADR-0250 decisions intact)

1. **No state traps the player.**
   - The departure gate is gone: a confirmed adjacent route always moves (`state_actions_phases.ts`). Enter **with no route** on unresolved ICE you stand on still enters it (that is not a departure).
   - Load and run start count as an arrival: `openArrivalEncounter` (`encounter_verbs.ts`) opens the decision when the state stands on an unresolved ICE node with nothing open; used by the arrival branch, `slotToGameState` (CONTINUE) and `launchSelected`. A save taken mid-combat or with the decision open restores **into the encounter**, so save-reload cannot dodge it.
   - JACK OUT / ESC on the Matrix now leaves the run: `runAbandoned(previous, next)` (`matrix` + not `menu` → `matrix` + `menu`) makes `main.ts` drop the run state and show the main menu. The reducer contract (`phase: "menu"`, message) is unchanged; combat jack-out (`runPhase: "dead"`) is unaffected.
   - Board footer is truthful about ESC: `ESC: jack out` (narrow `ESC jack out`) instead of `ESC: back`.
2. **SCAN with no utility program in hand is skipped by the arrows** (both directions). The remaining order is unchanged: PROBE → BYPASS → BREACH → JACK OUT (→ SCAN when a utility card is in hand). If SCAN is committed anyway, the refusal still says `no utility program in hand`.
3. **Enter is never silent.** Nothing selected → `Nothing selected. Press ↓ to pick a verb, then ENTER. Exits: BYPASS, BREACH, JACK OUT.` (no default selection, ADR-0249 rule 4). Enter on an already-used PROBE or SCAN → `Threat already revealed. Exits: …` (was: identical state). When BYPASS is not payable the hint reads `Exits: BREACH, JACK OUT (BYPASS blocked).`
4. **The exits read as exits.** `EXITS: BYPASS · BREACH · JACK OUT` (cyan, BYPASS omitted while blocked) under the gate line; each verb row carries `EXIT` or `INFO` in a fixed column; unselected exits are cyan, information verbs grey, the selected row green with `>`. A `Nothing selected — press ↓ to pick` line (amber) shows while no verb is selected; the controls end with `ESC: jack out (abandon run)`. Verb list, costs, `BLOCKED`, details and `ICE blocks travel until resolved` (once) kept.

Unchanged: verb costs (PROBE 8 / BYPASS 60 / limit 100), boss / dead-end BYPASS block, terminal-node completion, SCAN payment, RNG, dungeon, save schema `version: 1`, `clearedEncounterNodes` / `bypassedEncounterNodes` contract, arrival gate, travel animation rule.

**New consequence to watch:** JACK OUT now really ends the run on one confirm (ESC included), as its label always said. Before, it silently did nothing durable. There is no confirmation step (no new modal per the ADRs); the autosave slot is not cleared, so CONTINUE still offers the last combat save.

## Live keypress trace — same node, same keys, before → after

[live/before-trace.txt](live/before-trace.txt) vs [live/after-trace.txt](live/after-trace.txt) (after = rebuilt `index-CduYM6w1.js`, same preview pid 75395).

| Keys on node 1 | Before | After |
| --- | --- | --- |
| arrive | decision open, `Travel blocked…` | same |
| Enter (nothing) | `Choose a verb with arrows, then ENTER.` | `Nothing selected. Press ↓ to pick a verb, then ENTER. Exits: BYPASS, BREACH, JACK OUT.` |
| ↓ Enter | PROBE, COST 8 | same |
| Enter | **no change** | `Threat already revealed. Exits: BYPASS, BREACH, JACK OUT.` |
| ← | SCAN (no utility) | **JACK OUT** (SCAN skipped) |
| Enter | **no change** | run abandoned → main menu |
| ESC on the encounter | board, `ENTER: enter ICE \| ICE blocks travel \| ESC: back`; Enter reopens | main menu, run state cleared |
| JACK OUT verb | board; Enter reopens | main menu ([shot](live/after-d-jackout-after-jackout.png)) |
| CONTINUE onto node 1 | board, `enter ICE`; every Enter reopens | **encounter screen** at once ([shot](live/after-b-continue-restored.png)) |
| BYPASS → ↓ Enter | moves to 0 | same |

## Captures

Actual `renderRunScreen` grids + HUD column at 24/20/16 cols through the game's `AsciiRenderer` (esbuild bundle, headless Chromium, 10×18 cells, DPR 1) — the matrix-entry-gate method ([escape-capture.ts](escape-capture.ts), [escape-png.mjs](escape-png.mjs), [capture-receipt.json](capture-receipt.json)). Fixture: real boot mission, real starter deck, node 1 ([fixture-before.json](fixture-before.json), [fixture-after.json](fixture-after.json)).

| Case | 80×50 | 60×40 | 40×60 |
| --- | --- | --- | --- |
| `gated-route` — board, unresolved ICE node targeted | [pair](gated-route-80x50-pair.png) | [pair](gated-route-60x40-pair.png) | [pair](gated-route-40x60-pair.png) |
| `encounter` — arrival, reworked exits | [pair](encounter-80x50-pair.png) | [pair](encounter-60x40-pair.png) | [pair](encounter-40x60-pair.png) |
| `encounter-enter` — Enter with nothing selected | [pair](encounter-enter-80x50-pair.png) | [pair](encounter-enter-60x40-pair.png) | [pair](encounter-enter-40x60-pair.png) |
| `encounter-probed-enter` — Enter on a used PROBE | [pair](encounter-probed-enter-80x50-pair.png) | [pair](encounter-probed-enter-60x40-pair.png) | [pair](encounter-probed-enter-40x60-pair.png) |
| `post-bypass` — board after BYPASS | [pair](post-bypass-80x50-pair.png) | [pair](post-bypass-60x40-pair.png) | [pair](post-bypass-40x60-pair.png) |
| `post-bypass-route` — route targeted | [pair](post-bypass-route-80x50-pair.png) | [pair](post-bypass-route-60x40-pair.png) | [pair](post-bypass-route-40x60-pair.png) |
| `stranded-route` — on unresolved node, nothing open, route targeted | [pair](stranded-route-80x50-pair.png) | [pair](stranded-route-60x40-pair.png) | [pair](stranded-route-40x60-pair.png) |
| `stranded-depart` — Enter | [pair](stranded-depart-80x50-pair.png) | [pair](stranded-depart-60x40-pair.png) | [pair](stranded-depart-40x60-pair.png) |
| `continue` — CONTINUE from a mid-combat save on node 1 | [pair](continue-80x50-pair.png) | [pair](continue-60x40-pair.png) | [pair](continue-40x60-pair.png) |

Raw text `<case>-<size>-{before,after}.txt` + `.hud.txt`; diffs `*-image-diff.json`. Width checks (`visual-qa tui-check`): **27/27 after frames** exact width, 0 overflow lines, no border drift, no ANSI (`*-after-width-check.json`). Longest strings: encounter row `  SCAN     INFO NO UTILITY IN HAND` 34 = the 34-cell text width at 40×60; narrow footer `ENTER ICE | ↑↓ route | ESC jack out` 35 = the 35 usable footer cells; wide footer 50 ≤ 55 at 60×40; 40×60 HUD lines max **15**.

## Tests

New [`web/tests/encounter_escape.test.ts`](../../../web/tests/encounter_escape.test.ts), 40 tests. At HEAD **32 failed / 8 passed** ([tests-before.txt](tests-before.txt)); the 8 that already held are guards: arrival still gates, Enter at rest on unresolved ICE still enters it, restore onto a resolved node opens nothing, SCAN reachable with a utility card, SCAN refusal text, SCAN listed with its reason ×3. After: **40 passed** ([tests-after.txt](tests-after.txt)).

| Fix | Red → green proof |
| --- | --- |
| 1 departure | unresolved node without arrival: both neighbours depart, no decision, COST 0; footer says travel, never `ICE blocks travel`; footer says `ESC: jack out`, never `ESC: back` (×3 layouts) |
| 1 JACK OUT / ESC | `runAbandoned` true for the JACK OUT verb and for ESC on encounter and board; false for travel, arrows, Enter-on-null, BYPASS, BREACH. E2E `encounter_verbs.spec` now asserts `screen "menu"` and no run state |
| 1 restore / start | CONTINUE from a mid-combat save → `encounterDecision {null,false}`, HUD `ENCOUNTER`; save with the decision open → arrows move only the verb cursor, Enter-on-null neither moves nor closes, COST 0 (**save-reload cannot dodge**); old save without the bypass list → opens; run start on ICE → opens, ICE-free start untouched |
| 2 SCAN | 10 presses each of ↓ ↑ → ← never land on SCAN without a utility; order PROBE BYPASS BREACH JACK OUT; ↑ reaches SCAN with a utility card |
| 3 Enter | null → message names ↓, ENTER, all three exits, nothing paid; screen shows `Nothing selected` ×3 layouts; used PROBE / used SCAN → `already revealed`; sweep of every verb × COST 0/95 × normal/probed/boss: every confirm changes message, decision or phase |
| 4 exits | `EXIT` on BYPASS/BREACH/JACK OUT rows, `INFO` on PROBE/SCAN, `EXITS:` line; exits one colour (CYAN_LIGHT) not used by info rows; costs, `BLOCKED`, gate line once, controls and `ESC: jack out` kept (×3 layouts) |

### Existing tests adapted (each encodes behaviour this change replaces)

| Test | Before intent | After |
| --- | --- | --- |
| `encounter_entry_gate` "re-gates the departure … (CONTINUE)" | departure from an unresolved node without arrival reopens the decision | renamed "re-opens the decision … (CONTINUE)": the restored state already has the decision open |
| `encounter_entry_gate` decision 5 "on an unresolved node with a route targeted" (×3) | footer must not claim travel there (Enter reopened) | "on an unresolved node at rest": same assertions (Enter opens the encounter; footer no travel, says ENTER ICE) where that is still true |
| `encounter_verbs` "refuses a second BYPASS…" | last step forced `encounterDecision: null` and expected the departure to stay gated; row text `BYPASS +60 COST BLOCKED` | arrows on the still-open decision never pick a route; row regex `BYPASS +EXIT \+60 COST BLOCKED`; all other assertions kept |
| `encounter_verbs` "cannot avoid paying BYPASS by selecting an outgoing route first" | run-start-on-ICE state with no decision; departure gated | given the run start as the game builds it (`openArrivalEncounter`); same assertions + no route selected |
| `encounter_programs` 4× "does not grant SCAN for role …" + "does not grant … from draw, discard or inventory" | used ↑ to reach SCAN with no utility | ↑ must **not** reach SCAN (new assertion); SCAN committed directly; all original assertions kept |
| `encounter_programs` "shows payment … frame" (×3) | `PROBE REVEALED` | `/PROBE +INFO REVEALED/` |
| `matrix_frame` footer row | `ENTER: enter ICE \| ICE blocks travel \| ESC: back` | `ENTER: enter ICE \| ↑↓: pick route \| ESC: jack out` |
| `e2e/encounter_verbs.spec` "JACK OUT abandons the run" | `state.phase === "menu"` (board still up) | `getScreen() === "menu"`, run state null, ESC afterwards keeps it null |

No test deleted. `e2e/continue.spec.ts` and `e2e/menu-nav.ts` unchanged and green.

## Verification

| Command | Result |
| --- | --- |
| `npm run typecheck` | 0 errors |
| `npm run lint` | 0 errors; pre-existing `src/input/keyboard.ts:14` warning |
| `npm test` | **171 files / 3857 passed / 0 failed** (baseline 170 / 3817; +1 file / +40) ([npm-test.txt](npm-test.txt)) |
| `npm run build` | PASS (`index-CduYM6w1.js`, `game-core-DpjFL32Z.js`); preview pid 75395 not killed, serves the new build |
| `npx prettier --write` on the 6 edited `src/**` files; `--check "src/**/*.{ts,tsx}"` | PASS |
| `npm run balance` / `-- --deck ppl` | [opening](balance-opening.txt) / [PPL](balance-ppl.txt): `cmp` byte-identical to `matrix-entry-gate-2026-11-01/balance-*.txt`; opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` (ADR-0239). The harness does not walk the graph |
| E2E `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` | **82 passed / 4 skipped / 0 failed (4.6m)** ([e2e.txt](e2e.txt)) |
| Frontend draft guard | clean, 6 files |

## LOC (total / pure)

| File | Before | After |
| --- | --- | --- |
| `core/state/encounter_verbs.ts` | 228 / 208 | 278 / 248 |
| `core/state/state_actions_phases.ts` | 379 / 336 | 372 / 328 |
| `core/state/state.ts` | 409 / 353 | 411 / 354 |
| `renderer/encounter.ts` | 132 / 127 | 150 / 143 |
| `renderer/matrix.ts` | 253 / 208 | 255 / 209 |
| `main.ts` | 1783 / 1555 | 1796 / 1567 |
| `tests/encounter_escape.test.ts` (new) | — | 389 / 332 |

`types.ts`, `storage.ts`, `run_screen.ts`, `matrix_travel.ts` untouched.

## Visual QA

Contrast ([contrast.json](contrast.json)), 4 palette modes × standard/high-contrast, on black: EXIT rows + `EXITS:` (CYAN_LIGHT) **≥ 10.93:1**; gate line, `Nothing selected` prompt, footers (YELLOW_AMBER) **≥ 10.15:1**; INFO rows, details, hints (GRAY_LIGHT) **≥ 11.54:1**; selected row / HUD (GREEN_NEON) **≥ 13.96:1**. Cyan, grey, green and amber stay distinct hex values in all 8 modes.

Read-only reviewer (explore agent, fallback model `openai/gpt-6-luna-fast` after the first model was unavailable; 19 s run, so a light review): **REVISE** with 3 findings. I checked each against the artifacts myself:

| Finding | Check | Disposition |
| --- | --- | --- |
| `BLOCKED` missing in `encounter-*-after.txt` | frames are at COST 0, where nothing is blocked; `BLOCKED` renders only when unaffordable. Pinned by `encounter_escape` "keeps costs, BLOCKED…" at COST 95 (×3 layouts: `+8 COST BLOCKED`, `+60 COST BLOCKED`) and `encounter_verbs` second-BYPASS (`BYPASS +EXIT \+60 COST BLOCKED`) | not a defect; no blocked frame captured (gap noted) |
| 40×60 `gated-route` footer "breaks the left rail" | line 58 is `║ ENTER ICE \| ↑↓ route \| ESC jack out║` — both rails present, `tui-check` 40/40, `borderMisaligned false`. The short footer fills all 35 usable cells, so it touches the right rail | not a defect; **taste**: no right padding at 40×60 |
| `ESC: back` in `live/after-trace.txt:56` | that string is the script's step label (`ESC (footer says ESC: back)`), kept identical in both runs; the screen in that row is `screen=menu` | not a defect |

So the review did not independently verify the change; I treat the per-item verdicts below as mine.

| Item | Verdict | Evidence |
| --- | --- | --- |
| No trapped state (ESC / JACK OUT / CONTINUE / departure) | PASS | after-trace `b`/`c`/`d`, `stranded-depart` moved to 0, `continue` = ENCOUNTER |
| Exits distinct: `EXIT`/`INFO` tags + `EXITS:` line + colour | PASS | `encounter-*-after.txt`, colour test |
| Enter never silent | PASS | `encounter-enter`, `encounter-probed-enter` HUD |
| SCAN not a dead end | PASS | after-trace `keys`: ← lands on JACK OUT |
| Footer truthful (travel / enter ICE / ESC jack out) | PASS | all board after frames |
| Verbs, costs, `BLOCKED`, gate line once, controls kept | PASS | frames + tests |
| Rails / width / no overflow | PASS | 27/27 width checks |
| Text contrast ≥ 4.5:1 | PASS | min 10.15:1 |
| Colour not sole carrier | PASS | `EXIT`/`INFO` words + `EXITS:` line |
| Motion | PASS | unchanged |
| 40×60 footer padding | taste | footer touches the right rail |
| Per-row focus ring / accessibility tree | FAIL (inherited) | canvas, unchanged |

# Run end and save timing — evidence, 2026-11-02

[ADR-0252](../../wiki/decisions/0252-run-end-and-save-timing.md). Owner: "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고 패배하게 되던데." Approved: "모두 수정해." Unstaged, uncommitted.

## Live reload trace — the owner's path, real keys

Script [run-end-live.mjs](run-end-live.mjs): fresh browser context, boot mission *Aleph Fragment*, route 0 → 25 → 16 → 18 (ICE) → 20 (boss). Fights use digit keys only (first playable hand row). After every logged key the trace records the reducer state **and the autosave slot decoded from IndexedDB** (`SLOT{…}`).

| Trace | Build | File |
| --- | --- | --- |
| BEFORE, owner path | 5195, HEAD `index-B_nl8RTM.js` | [live/before-owner-5195-trace.txt](live/before-owner-5195-trace.txt) |
| BEFORE, all 3 scenarios | HEAD worktree build on 5196 (same hash `index-B_nl8RTM.js`; 5195 already served the fix) | [live/before-head5196-trace.txt](live/before-head5196-trace.txt) |
| AFTER, all 3 scenarios | 5195, `index-DKOoa0XB.js` (same preview pid 75395, not restarted) | [live/after-trace.txt](live/after-trace.txt) |

### Owner path: kill the boss → ending → reload → CONTINUE

| Step | BEFORE (5195, HEAD) | AFTER (5195) |
| --- | --- | --- |
| travel 25, 16 | slot **none** | slot `node 25`, `node 16` |
| win at 18 → loot | memory `clr [18] cr 4500`; slot `clr [] cr 0` (combat frame) | slot `clr [18] hp 74 cr 4500` |
| loot Enter (+heal) | slot unchanged (`hp 74 cr 0`) | slot `hp 89` |
| kill boss → loot | memory `clr [18,20] hp 63 cr 10600`; slot `clr [18] cr 4500` | slot `clr [18,20] hp 63 cr 10600` |
| Enter → ending | slot `clr [18] cr 4500` | **slot none** (retired) |
| Enter on ending | `rp ending ph menu` — still the ending | **`scr menu`, state null** |
| Enter, Esc | still `ending/menu` | title → NEW RUN screen → Esc back to title (normal title input) |
| reload | `hasSaveCache=true` | `hasSaveCache=false` |
| CONTINUE | boss node, decision open, `BYPASS: blocked here` | nothing happens; screen `menu`, state null |
| BYPASS / BREACH | `BYPASS blocked — Must BREACH`; BREACH → **`wintermute 140/140`**, `Combat vs ICE — Standard` (forced re-fight) | — (run ended cleanly) |

### Two more reload points (both builds)

| Scenario | BEFORE (HEAD @5196) | AFTER (5195) |
| --- | --- | --- |
| `boss-loot-reload` — reload on the boss loot screen, CONTINUE | boss decision reopens; BREACH → `wintermute 140/140`, `Standard` | restored **on the loot screen** (`rp loot`, `clr [18,20]`, hp/cr kept); Enter → ending (slot retired), Enter → title |
| `boss-fight-reload` — reload mid boss fight, CONTINUE (ADR-0250 rule) | decision reopens, BYPASS blocked; BREACH → `wintermute 140/140`, `Standard` | decision reopens, `BYPASS blocked — Must BREACH`; BREACH → **`wintermute 165/165`, `ICE — Yakuza Enforcer`** = the live fight |

Mid-fight reload still restarts that fight (roster HP is not in the save — unchanged contract). Canvas shots: `live/{before-owner-5195,before-head5196,after}-*.png`.

## What changed

| | Change | Files |
| --- | --- | --- |
| A | `draw()` autosaves on `matrix` / `loot` frames too (before its early return). `autosave()` snapshots the frame, skips an unchanged state reference, and runs writes/clears through one ordered queue. `refreshSaveCache()` redraws only when no run is loaded (in a run `screen` can be `"menu"` after CONTINUE → write → refresh → draw → write loop). | `main.ts`, `core/state/run_end.ts` (`autosaveIntent`) |
| B | Reaching `runPhase: "ending"` retires slot 0 (`clear(0)`). Enter/ESC on the ending (`runCompleted`) → state null, title, status `Run complete. Autosave cleared.` Ending footer `ENTER / ESC: return to title`. A slot on a **cleared terminal node** (only writable from that win's loot screen) restores to the loot screen. | `main.ts`, `run_end.ts`, `state.ts`, `renderer/ending.ts` |
| C | `slotToGameState(…, iceCatalog?)`: with the catalog the base ICE is `missionIce(mission, catalog)` — the run start's own function (moved verbatim from `main.ts loadIce`). No save field, no version bump. | `core/state/mission_ice.ts`, `state.ts`, `main.ts` |
| — | `applyLootAction` uses the extracted `isTerminalNode` (same expression). | `state_actions_phases.ts` |

**CONTINUE after a completed run**: the slot is empty, so CONTINUE is `CONTINUE (no save)` (grey, no `→ mission (turn N)` hint) exactly like a fresh profile, and selecting it opens nothing. The next new run's first frame makes it available again.

## Captures

Actual `renderRunScreen` (ending) and `renderPreGameScreen` (main menu) grids + HUD column through the game's `AsciiRenderer` (esbuild bundle of the matrix-slice harness, headless Chromium, 10×18 cells, DPR 1) — same method as the matrix slices. Scripts: [run-end-capture.mts](run-end-capture.mts) (grids; `before` imports HEAD sources from a detached worktree, `after` the working tree), [run-end-png.mjs](run-end-png.mjs), [capture-receipt.json](capture-receipt.json) (18 frames). Fixture: the real reducer on the owner route ([fixture-before.json](fixture-before.json), [fixture-after.json](fixture-after.json)).

| Case | 80×50 | 60×40 | 40×60 |
| --- | --- | --- | --- |
| `ending` — the ending screen (footer) | [pair](ending-80x50-pair.png) | [pair](ending-60x40-pair.png) | [pair](ending-40x60-pair.png) |
| `ending-confirm` — after Enter on the ending (before: still the ending; after: title, no save, status line) | [pair](ending-confirm-80x50-pair.png) | [pair](ending-confirm-60x40-pair.png) | [pair](ending-confirm-40x60-pair.png) |
| `continue-after-run` — title after reload, CONTINUE selected (before: stale slot offered `→ aleph_fragment (turn 9)`; after: `(no save)`) | [pair](continue-after-run-80x50-pair.png) | [pair](continue-after-run-60x40-pair.png) | [pair](continue-after-run-40x60-pair.png) |

Width checks (`visual-qa tui-check --cols N` on the after `.txt`): **9/9** max width = expected columns, 0 overflow lines, no border drift, no wide chars, no ANSI (`*-after-width-check.json`). Diffs `*-image-diff.json`. Longest new strings: footer `ENTER / ESC: return to title` 28 (same as the old centring width); status `Run complete. Autosave cleared.` 31 ≤ 34-cell panel interior at 40×60. Pre-existing, unchanged: ending HUD `Choice: arc4_liberation_front` exceeds the 16-col HUD at 40×60; menu subtitle and footer are clipped at 40×60.

## Tests

| Suite | HEAD | After |
| --- | --- | --- |
| `web/tests/run_end_save.test.ts` (18) | **12 failed / 6 passed** ([tests-before.txt](tests-before.txt), file run in a HEAD worktree) | **18 passed** |
| `web/e2e/run_end_save.spec.ts` (3 × 2 projects) | **6 failed** on the HEAD build ([e2e-before.txt](e2e-before.txt)) | **6 passed** ([e2e-after-new-spec.txt](e2e-after-new-spec.txt)) |

The 6 unit tests that pass at HEAD are guards: the reducer state already holds the move and the win (the bug was the controller not writing them), a non-terminal loot slot restores onto the board, the two ADR-0250 reopen rules (boss mid-fight with BYPASS blocked; non-terminal mid-fight), and an old caller without the catalog keeps the fallback ICE.

| Requirement | Red → green proof |
| --- | --- |
| committed move in the next save | e2e: slot `currentNodeIndex 25` after one travel (HEAD: no slot); unit: `autosaveIntent(matrix) = write` |
| combat win in the save | e2e: slot `cleared [18]`, HP, credits = live after the win (HEAD: combat frame); unit: loot/combat/dead → `write` |
| ending → title, run cleared, no input to the ending | e2e: Enter → `screen menu`, state null; Esc/↓/↑ keep it null; unit: `runCompleted` true for Enter/ESC only, not arrows, not the loot→ending confirm, not Matrix JACK OUT |
| completed run cannot be resumed | e2e: slot null at the ending, after reload CONTINUE opens nothing; unit: `autosaveIntent(ending) = retire`; title shows `CONTINUE (no save)` + status ×3 layouts |
| a load cannot dodge an unresolved ICE (ADR-0250) | unit guards above (green at HEAD and after); live `boss-fight-reload` |
| C — restored roster = live | unit: boss roster `wintermute:165` (HEAD 140) and `encounterRoster(restored)` deep-equals `encounterRoster(live)` with the same `ice.name` |
| boss-loot reload finishes the run | unit: loot-slot restore → `rp loot` → confirm → `ending`; live `boss-loot-reload` |

No existing test changed or deleted. `e2e/continue.spec.ts` and `e2e/menu-nav.ts` unchanged and green.

## Verification

| Command | Result |
| --- | --- |
| `npm run typecheck` | 0 errors ([typecheck.txt](typecheck.txt)) |
| `npm run lint` | 0 errors; pre-existing `src/input/keyboard.ts:14` warning ([lint.txt](lint.txt)) |
| `npm test` | **175 files / 3932 passed / 0 failed** (baseline 174 / 3914; +1 file / +18) ([npm-test.txt](npm-test.txt)) |
| `npm run build` | PASS, `index-DKOoa0XB.js` ([build.txt](build.txt)); preview pid 75395 not killed, serves it |
| `npx prettier --write` on the 6 edited/new `src/**` files; `--check "src/**/*.{ts,tsx}"` | PASS |
| `npm run balance` / `-- --deck ppl` | [opening](balance-opening.txt) / [PPL](balance-ppl.txt): `cmp` byte-identical to `combat-affordance-2026-11-02/balance-*.txt`; opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`, PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7` (ADR-0239) |
| E2E `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` | **88 passed / 4 skipped / 0 failed (4.6m)** = baseline 82 + 6 new ([e2e.txt](e2e.txt)) |

## LOC (total / non-blank)

| File | Before | After |
| --- | --- | --- |
| `src/main.ts` | 1809 / 1742 | 1794 / 1728 |
| `src/core/state/state.ts` | 411 / 393 | 428 / 410 |
| `src/core/state/state_actions_phases.ts` | 372 / 360 | 370 / 358 |
| `src/renderer/ending.ts` | 155 / 142 | 155 / 142 |
| `src/core/state/run_end.ts` | — | 39 / 35 (new) |
| `src/core/state/mission_ice.ts` | — | 56 / 55 (new; moved from `main.ts`) |
| `tests/run_end_save.test.ts` | — | 268 / 244 (new) |
| `e2e/run_end_save.spec.ts` | — | 208 / 199 (new) |

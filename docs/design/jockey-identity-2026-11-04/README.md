# ADR-0277 / ADR-0278 evidence — `exploit`, the deck swap, and the run read as a story

This folder is the measurement and the play-through behind
[ADR-0277](../../wiki/decisions/0277-exploit-ignores-half-the-armor.md) and the
defect batch it led to, [ADR-0278](../../wiki/decisions/0278-the-run-reads-true.md).
ADR-0277 closes ADR-0276's open question (a): the jockey decks differed by tier
only, because only five programs had a wired effect and the curated deck already
held four of them. ADR-0278 closes the defects the story-form play-through found.

## What changed

- `exploit` is wired: `armor_ignore` 50% — `effectiveArmor = floor(max(0, armor - pierce) * (100 - amount) / 100)`.
  Cards with `amount = 0` are byte-identical to before.
- The curated deck takes `exploit` in `backdoor`'s slot. The measurement forced it:
  with `exploit` wired, CASE was the only deck without the card and fell 8.1 points
  behind SIL at grade 3, past ADR-0276's own ±5pp rule.
- The ending summary reads `state.player.credits` (the run's earnings) instead of
  `state.inventory.credits` (the mission's base reward). A 2,300cr run used to end
  on a screen saying 500cr.

## Balance (100 runs/mission, seeded)

| grade | CASE | SIL | KAS | max spread |
|---|---:|---:|---:|---:|
| 3 | 89.1 | 86.5 | 84.3 | 4.8 |
| 4 | 47.4 | 47.0 | 43.3 | 4.1 |
| 5 | 40.7 | 40.3 | 36.4 | 4.3 |

Rejected candidates: dropping `strike` (99.5 — far too strong), dropping `barrier`
(81.5, fails at g4), dropping `decoy` (70.1), `strike` → `surge` (99.6). The
unchanged deck measured 78.4 at grade 3; that row is recorded in ADR-0277 because
the file would have been overwritten by the adopted deck. Raw files:
`balance-case-rejected-drop-strike.txt`, `balance-case-rejected-drop-barrier.txt`.

## The run, written down

- `story-trace.txt` — the re-run of the browser play-through (`npm run story`):
  CASE, `First Jack` (arc 1), two fights, ending `arc1_wage_slave`, 2,300cr,
  7 turns. The trace records the `combatLog` too, so a card's hit is not lost
  behind the newest line.
- `story-narration.md` — that trace retold as prose, plus the plausibility
  verdict, the corrections, and the defects the retelling exposed.
- `00-jockey-select.png` … `04-ending.png` — one still per beat.

## Defects the narration found

The first retelling (2026-11-04) listed eight, for ADR-0277's record. ADR-0278
fixed six, corrected three as false positives, and added two more found on the
re-measurement. Full ledger with evidence: `story-narration.md` §정정 및 재측정.

| # | Defect | Status |
|---|---|---|
| 1 | A card reward never reaches the hand in a short run | fixed — hand refilled at loot, reward card goes on top of the draw pile |
| 2 | The hand is not reset between encounters | fixed — same refill; the SCAN cost stays spent (ADR-0247) |
| 3 | Both ICE nodes rolled the same type | fixed — each ICE room takes the next slot of the grade band |
| 4 | Tone clash: "the deck is already warm" vs "The deck is cold" | fixed — tagline is now "New hands. Old reflexes. The deck remembers." |
| 5 | Zone naming (`surface` mission, `mid` message) | **false positive** — mission zone and node zone are different axes |
| 6 | Loot formatting (`ice_shardx1`) | fixed — `${item} x${qty}` |
| 7 | Dixie takes the first line of the combat log | **false positive** — the trace captured only `message`; the log keeps 4 lines |
| 8 | Loot heals to full at every node | **false positive** — it heals 15%; the run was at 96/100 |
| 9 | The fight names the wrong ICE (`Combat vs ICE — Wisp` for the wintermute boss) | fixed — the screen reads the roster |
| 10 | The payout depended on who landed the killing blow | fixed — kills are credited where they happen |
| 11 | The mission base reward is paid on every encounter | **fixed** — paid once, on the fight that ends the mission (ADR-0279) |
| 12 | The ending resolver read a wallet combat cannot fill | **fixed** — reads `player.credits`, the number the ending prints (ADR-0279) |

## Ending distribution (ADR-0279)

`npm run endings` — 53 missions, seeded, deterministic. `control` went from a
branch reachable on 2 of 53 missions to 12 runs (arc 3: 1, arc 4: 7, arc 5: 4).
Arcs 1–2 still do not reach it (their rewards are too small to clear 5,000).

**The number depends on the time model**, because the enemy phase is wall-clock
gated (`AUTO_ATTACK_INTERVAL_MS`). The tool takes `--tick-every N`:

| model | reached an ending | `hp > 75%` | `credits > 5000` | `control` |
|---|---:|---:|---:|---:|
| `tick-every=0` (enemy gated off — a fast browser session) | 53/53 | 53/53 | 12/53 | 4/53 |
| `tick-every=1` (the balance harness's model) | **5/53** | 0/53 | 0/53 | 0/53 |

Two readings follow, and both matter:

- In the regime where runs survive, the **HP gate never binds** (53/53) — credits
  are what decide. ADR-0278 (c)'s suspicion that the ending HP is uninformative
  holds, but for the opposite reason to the guess: the 15% loot heal always
  covers the damage taken.
- In the harness's own model, **runs mostly flatline before the ending**
  (48/53), so the ending distribution is decided by *survival* first. That is a
  difficulty question, out of ADR-0279's scope.

> **ADR-0280 supersedes that reading.** The enemy phase is now off the wall
> clock, the boss follows the grade, and the per-grade curve was re-tuned with
> the per-encounter rate held monotonic. Mission completion is now
> **100 / 95 / 81.8 / 48 / 0 / 0** against targets of 100 / 95 / 80 / 50 / 25 / 10
> — grades 1-4 inside tolerance. Grades 5-6 are structurally unreachable under
> the monotonicity constraint (see `../adr-0280/constrained-search.txt`).

Raw: `ending-distribution.txt`.

## Reproduce

```bash
cd web
npm run build
npm run story            # writes story-trace.txt + screenshots (needs :5195)
STORY_MISSION=9 npm run story   # "First Jack" specifically
npm run balance -- --deck opening|veteran|heretic
npm run soak             # direct-control sweep, freeze statistics
```

# ADR-0277 evidence — `exploit`, the deck swap, and the run read as a story

This folder is the measurement and the play-through behind
[ADR-0277](../../wiki/decisions/0277-exploit-ignores-half-the-armor.md). It closes
ADR-0276's open question (a): the jockey decks differed by tier only, because only
five programs had a wired effect and the curated deck already held four of them.

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

- `story-trace.txt` — 15 steps of a real browser run (`npm run story`): CASE,
  `First Jack` (arc 1), two fights, ending `arc1_wage_slave`, 2,300cr, 7 turns.
- `story-narration.md` — that trace retold as prose, plus the plausibility verdict
  and the defects the retelling exposed.
- `00-jockey-select.png` … `04-ending.png` — one still per beat.

## Reproduce

```bash
cd web
npm run build
npm run story            # writes story-trace.txt + screenshots (needs :5195)
STORY_MISSION=9 npm run story   # "First Jack" specifically
npm run balance -- --deck opening|veteran|heretic
npm run soak             # direct-control sweep, freeze statistics
```

## Defects the narration found (not fixed here)

1. A card reward never reaches the hand in a short run — `Scan` went to the draw
   pile and the run ended before the hand emptied. This is the growth the run
   promises, so it is the first thing to fix (refill the hand at encounter start).
2. The hand is not reset between encounters, so the second fight started with
   three cards. Not a lock (it refills when empty) but it makes encounters uneven.
3. Both ICE nodes in the mission rolled the same type (`Wisp`, 35 HP, armor 0).
4. Tone clash: the jockey tagline says "the deck is already warm"; the arc-1 intro
   says "The deck is cold in your hands."
5. Zone naming: the mission is `surface`, the messages say `Entering mid...` and
   `Entering core-deep...`.
6. Loot formatting: `Loot: ice_shardx1` (no space) next to `combat_modulex2, data_fragmentx3`.

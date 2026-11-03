# Per-jockey starting decks — measured curves (2026-11-04)

ADR-0276. The jockey used to only *name* the run; now it decides the opening
deck. That is the first change in this line of work that touches balance, so
every deck was measured on the same curve before it shipped.

Command: `cd web && npm run balance -- --deck <opening|veteran|heretic>` (100
runs/mission, fixed seeds). Raw harness output: `balance-opening.txt`,
`balance-veteran.txt`, `balance-heretic.txt`, `balance-ppl.txt`, and
`balance-heretic-candidate.txt` (the rejected first KAS deck).

## Shipped decks and their curves

Win rate by mission grade:

| grade | missions | CASE (novice) | SIL (veteran) | KAS (heretic) | PPL (reference) |
|------:|---------:|--------------:|--------------:|--------------:|----------------:|
| 1 | 4  | 100.0% | 100.0% | 100.0% | 100.0% |
| 2 | 16 | 100.0% | 100.0% | 100.0% | 100.0% |
| 3 | 11 | 78.4%  | 83.8%  | 78.6%  | 99.3% |
| 4 | 10 | 38.9%  | 44.5%  | 38.8%  | 84.1% |
| 5 | 9  | 33.4%  | 38.3%  | 33.2%  | 44.4% |
| 6 | 3  | 0.0%   | 0.0%   | 0.0%   | 27.3% |

| jockey | deck | effect-bearing cards |
|---|---|---|
| CASE | `strike, backdoor, boost, barrier, decoy` | 4 (`backdoor`, `boost`, `barrier`, `decoy`) |
| SIL  | `strike, backdoor, exploit, barrier, decoy` | 3 (`backdoor`, `barrier`, `decoy`) |
| KAS  | `strike, exploit, virus, surge, decoy` | 2 (`decoy`, and `surge`'s low cost) |

All three are flat at grades 1–2 and 6 (too easy / impossible regardless of
deck), so the difference lives at grades 3–5 — where the game is actually
decided.

## What the measurement found

The reducer gives **every** program the same damage path (`tier * 5`) and wires
a real effect onto only **five** programs: `backdoor` (pierce 2), `barrier`
(shield 2/2 turns), `boost` (empower +2/2 turns), `cloak` (evade), `decoy`
(50% for a turn). Everything else is a plain attack. The curated CASE deck
already holds four of those five.

Two consequences, both measured:

1. **Dropping an effect card for a plain one is a downgrade, not flavour.**
   The first KAS deck — `strike, backdoor, virus, surge, decoy` — traded
   `boost` and `barrier` (two wired effects) for `virus` and `surge` (plain
   attacks of the same tiers). It measured **72.4% at grade 3**, below the
   curated deck's 78.4%: five points *worse* than the default, i.e. a trap
   choice. Rejected.

2. **A tier upgrade is the one trade the plain damage path rewards.** SIL's
   single swap, `boost` (t2) → `exploit` (t3), buys about +5 points at grade 3
   (78.4% → 83.8%) and does not change the deck's character.

So KAS was rebuilt to buy aggression with **tiers** instead of by dropping
shields: `strike, exploit, virus, surge, decoy` — four cards that hit, one that
does not. It lands **level with CASE** (78.6% vs 78.4% at grade 3, 38.8% vs
38.9% at grade 4) while playing a different shape. That is the intended
horizontal trade: same power, different feel, not a trap.

SIL is left as a small, deliberate upgrade (~+5 pts, grades 3–5), which matches
its tagline ("she has done this before").

## Candidates that were measured and not shipped

`--deck-ids` was added to the harness so a candidate could be scored before
shipping (`--runs 50` for scanning, `100` to confirm).

| candidate | deck | g3 | g4 | g5 | verdict |
|---|---|---:|---:|---:|---|
| C1 (first KAS) | strike, backdoor, virus, surge, decoy | 72.4 | 32.8 | 28.4 | trap — below CASE |
| C2 | strike, backdoor, boost, surge, decoy | 79.8 | 38.6 | 33.3 | ok, keeps `boost` |
| C3 | strike, backdoor, boost, barrier, surge | 65.3 | 38.8 | 30.0 | weak at g3 |
| C5 | strike, backdoor, boost, exploit, decoy | 79.8 | 38.6 | 33.3 | equals C2 |
| C6 | strike, backdoor, boost, barrier, exploit | 65.3 | 38.8 | 30.0 | weak at g3 |
| C8 (**shipped KAS**) | strike, exploit, virus, surge, decoy | 78.6 | 38.8 | 33.2 | parity with CASE |
| C9 | strike, backdoor, exploit, surge, decoy | 84.4 | 44.8 | 38.4 | ≈SIL, too close to it |
| C10 | strike, backdoor, exploit, virus, surge | — | — | — | no defense; falls to 96.3% at g2 |

C10 confirms the shape rule: a five-attacker deck with no guard loses at grade 2
and is rejected.

## Open question for the owner

Deck identity is currently limited to *tiers* because only five effects are
wired. If the jockeys should differ by **kind** (SIL pierces, KAS burns, CASE
shields), the follow-up is to wire the planned per-program effects from
`plannedDescription` — that is the change that would let an aggressive deck be
aggressive in a *mechanic*, not merely a number.

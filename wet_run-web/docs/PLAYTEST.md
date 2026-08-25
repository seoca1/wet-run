# Wet Run Web MVP — 3-Person Playtest Protocol

> Per ADR-0199 §7 (5-step validation plan): Day 10 playtest to validate
> the deck-building ICE-breaking core in a browser before committing to
> full Tier 2 expansion.

## Setup

1. **Build the production bundle**: `npm run build`
2. **Serve locally**: `npm run preview --port 4173`
3. **Open in browser**: http://localhost:4173
4. **Recommended browser**: Chrome / Firefox / Safari 17+ (desktop, 1280×800 or larger)
5. **Required hardware**: physical keyboard (no touch in MVP)

## Test Protocol

### Per-participant (3 total)

- **Duration**: 15 minutes per person
- **Pre-test**: 2-minute intro explaining controls (arrow keys + ENTER/SPACE + ESC + Q)
- **Goal**: Defeat the Watchdog ICE in the first_jack mission
- **Observer**: Watch silently; note where they hesitate, get stuck, or comment

### Observation Categories (score 1-5 each)

1. **Visual fidelity**: Does the ASCII renderer feel like wet_run (Gibson vibe)?
2. **Control clarity**: Did they understand arrow keys without prompting?
3. **State recognition**: Did they realize when they were in combat vs menu?
4. **Save/load**: Did they discover the save is automatic (or want to save manually)?
5. **Engagement**: Did they want to keep playing after 15 minutes?

### Critical Questions (qualitative)

- "Where do I move?" / "What does this button do?" — if dominant, genre fails on web.
- "Is the ICE winning or losing?" — if they can't tell, VFX needed (Tier 2).
- "Did I just save?" — if they ask, manual save button needed.

## Pass Criteria

- 3/3 participants complete mission (10-15 min each)
- Mean scores ≥ 3.5 on all 5 categories
- "Did you understand arrow keys without prompting?" — 3/3 yes
- "Would you play again?" — 2/3 yes

## Failure Triggers (Stop and Pivot)

- 2/3 participants fail to complete mission in 15 min → UX too opaque
- Mean score < 2.5 on any category → core mechanic doesn't translate
- "I don't see why this is on a screen, not a terminal" — Gibson tone lost

## Outputs

After playtest, record:
- `docs/PLAYTEST_RESULTS_2026-08-XX.md` — observations + scores + decisions
- Commit results to GitHub
- Update ADR-0199 Implementation Status
- If pass → Tier 2 plan (audio, mobile touch, multiple missions)
- If fail → iterate on weakest category; if 2 failures, pause web version effort

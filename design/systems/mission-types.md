# Mission Type Taxonomy (Phase 11 — Content Expansion)

**Document Type**: Design specification (companion to `missions.md`)
**Status**: Active (Phase 11 implementation)
**Date**: 2026-08-08
**Owner**: wet_run Phase 11
**Related**: [ADR-0188 — Mission Expansion](../../decisions/0188-mission-expansion.md), `missions.md`, `missions.json`

## Overview

This document defines the complete mission type taxonomy used in wet_run. It catalogs:
- **Existing types** (already in `missions.json`, refined documentation)
- **New types** (introduced in Phase 11 per ADR-0188)
- **Type interaction rules** (multi-type missions, chains, outcomes)

## Existing Mission Types (Refined)

The current 111 missions use 24 distinct `primary_objective.type` values. These are consolidated into 6 logical categories:

### Category 1: Data Operations (51+ missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `extract_data` | Pull data from cyberspace | 51 | Most common |
| `data_analysis` | Analyze captured data | 2 | Mid-mission step |
| `audit` | Audit system for vulnerabilities | 8 | Pre-extraction |
| `trace_target` | Trace target's location | 1 | Investigation variant |

### Category 2: Combat (4 missions + secondary)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `defeat` (primary) | Defeat target ICE/boss | 4 | Rare as primary |
| `defeat` (secondary) | Defeat during extraction | 57 | Most common secondary |
| `patch_ice_vulnerability` | Disable ICE for allies | 14 | Defense variant |

### Category 3: Delivery & Transfer (16 missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `deliver` | Physical delivery | 11 | Courier |
| `deliver_material` | Material delivery | 2 | Crafting integration |
| `deliver_package` | Package delivery | 1 | Stealth variant |
| `deliver_construct` | Construct delivery | 1 | AI artifact |

### Category 4: Crafting & Materials (5 missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `craft_item` | Craft programs/items | 1 | Phase 8 integration |
| `collect_material` | Gather materials | 2 | Loot integration |
| `construct_unlock` | Unlock construct access | 1 | Construct storyline |
| `rescue_construct` | Rescue a construct | 1 | Construct storyline |

### Category 5: Decision & Negotiation (5 missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `decision` | Make a choice | 1 | Story branch |
| `negotiate_with_ai` | Negotiate with AI | 1 | Sprawl tone |
| `pattern_read` | Read pattern in stream | 1 | Pattern Recognition |
| `final_job` | Final mission in chain | 1 | Climax |
| `witness` | Witness an event | 1 | Narrative beat |

### Category 6: Infiltration & Defense (3 missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `infiltrate` | Infiltrate system | 1 | Old-style |
| `defend` | Defend a node | 1 | Currently rare |
| `protect` | Protect an entity | 1 | NPC-guard variant |

### Category 7: Special (4 missions)

| Type | Definition | Count | Notes |
|---|---|--:|---|
| `jack_in_conscription` | Sign up for runs | 1 | Onboarding |
| `record_procedural` | Record procedural action | 1 | Replay integration |
| `hack` | Generic hack | 1 | Catch-all |

---

## New Mission Types (Phase 11)

Introduced per ADR-0188. Each new type adds a new mechanic or significantly extends an existing one.

### Type 1: Investigation (NEW)

**Definition**: Multi-stage intel-gathering mission. No direct combat. Player navigates cyberspace collecting data, interviewing witnesses, and synthesizing evidence.

**Trigger conditions**:
- Faction reputation ≥ tier 3 (trustworthy enough)
- Player has scan/decrypt programs (utility)

**Primary objective**: `investigation_complete` (collect 3-5 evidence fragments)

**Secondary objectives** (optional):
- `avoid_combat` (preserve stealth)
- `preserve_evidence` (don't corrupt the data)
- `interrogate_npc` (extract testimony)

**Outcomes** (3 branches):
- **Success**: Full intel → unlocks follow-up mission (high CRED reward)
- **Partial**: Some intel → reduces follow-up mission difficulty
- **Detection**: ICE aware → mission becomes `infiltrate` with combat

**Rewards**: CRED + reputation + program (rare)

**Sample mission**: `ta_investigate_3jane_initiative` — investigate 3Jane's corporate initiative

### Type 2: Defense (EXPANDED)

**Definition**: Defend a node from waves of incoming ICE. Player holds position while allies extract data.

**Trigger conditions**:
- Player has shield/defense programs
- Position is vulnerable (defense objective)

**Primary objective**: `survive_n_waves` (5-7 waves)

**Secondary objectives** (optional):
- `protect_npc` (NPC must survive)
- `preserve_node_data` (don't lose data during waves)
- `minimize_damage` (node HP > 50%)

**Outcomes** (2 branches):
- **Victory**: Defended → bonus rewards (programs, rep)
- **Defeat**: Node lost → mission failure, story continues

**Rewards**: CRED + programs + meta-progression

**Sample mission**: `ta_defend_straylight_perimeter` — defend Straylight from Sense/Net raid

### Type 3: Dual-Objective (NEW)

**Definition**: Two simultaneous primary objectives. Player must balance both within time/resource constraints.

**Trigger conditions**:
- Player has multi-task capability
- Two objectives are mutually strategic (rare combo)

**Primary objectives**: 2 simultaneous objectives (e.g., extract + defeat)

**Structure**:
```json
{
  "primary_objective": {
    "type": "extraction_AND_defeat",
    "extraction_spec": { "data_id": "x", "count": 1 },
    "defeat_spec": { "enemy": "ice.y", "count": 1 },
    "time_limit_seconds": 300,
    "objective_lock": "both_required"
  }
}
```

**Outcomes** (3 branches):
- **Both complete**: Full reward
- **One complete**: Partial reward (lose the other)
- **Neither complete**: Mission failure

**Rewards**: CRED + 2 reward types (combo bonus)

**Sample mission**: `mid_dual_objective_yakuza_conspiracy` — extract audit data AND defeat yakuza rep

### Type 4: Extraction_v2 — High-Risk Variant (NEW)

**Definition**: Time-limited extraction with high reward. Failure means death/reset.

**Trigger conditions**:
- Player has high-tier programs (T3+)
- Player accepts risk (lock-in before mission)

**Primary objective**: `extract_data` with clock

**Structure**:
```json
{
  "primary_objective": {
    "type": "extract_data",
    "data_id": "high_value",
    "time_limit_seconds": 120,
    "penalty_on_failure": "construct_loss"
  }
}
```

**Outcomes** (2 branches):
- **Success**: Massive reward (T5 program + reputation)
- **Failure**: Construct damage (1 fragment lost) — recoverable

**Rewards**: 3x standard CRED + rare program

**Sample mission**: `ta_extract_aleph_fragment` — high-risk Aleph extraction (2 minutes timer)

### Type 5: Stealth (NEW)

**Definition**: Avoid ICE detection entirely. No combat allowed. Detection = mission failure.

**Trigger conditions**:
- Player has cloak/decrypt programs
- Target is high-security (hostile to extraction)

**Primary objective**: `reach_target` + `extract_data` (no defeats)

**Secondary objectives**:
- `avoid_detection` (counter never goes > 50%)
- `minimize_alerts` (no alert triggers)
- `preserve_trace` (no logging)

**Outcomes** (2 branches):
- **Stealth success**: Full data + bonus
- **Detection**: Mission auto-fails (no combat allowed)

**Rewards**: CRED + program + reputation

**Sample mission**: `core_stealth_construct_chamber` — infiltrate core without triggering alerts

---

## Mission Chains (NEW)

8 chains of 3-5 missions each (24-40 missions). Chains unlock mid-game.

### Chain Structure

```json
{
  "chain_id": "ta_succession",
  "chain_name": "Tessier-Ashpool Succession",
  "chain_type": "faction_driven",
  "unlock_condition": "arc_3_progress >= 50 AND ta_reputation >= tier_3",
  "missions": [
    { "id": "ta_chain_incite", "order": 1 },
    { "id": "ta_chain_mediate", "order": 2 },
    { "id": "ta_chain_betray", "order": 3 },
    { "id": "ta_chain_inherit", "order": 4 }
  ],
  "chain_reward": "ta_construct_unlock",
  "chain_failure": "ta_reputation_reset"
}
```

### Chain Types

- **Faction-driven**: 3 chains (faction politics, corporate intrigue)
- **Character-driven**: 3 chains (per jockey arc, e.g., Case's past)
- **Story-driven**: 2 chains (cross-trilogy, e.g., Blue Ant coolhunter)

### Chain Mechanics

- Linear progression (mission 1 → 2 → 3 → ...)
- Chain-wide reward (program, construct, achievement)
- Chain-wide failure penalty (reputation reset, no retry)
- Mid-chain save point (preserve progress)

---

## Random Selection Rules (NEW)

19 new selection rules for varied mission encounters:

| Rule | Trigger | Effect |
|---|---|---|
| Faction-weighted | faction_rep >= 4 | 80% missions from that faction |
| Zone-restricted | player_zone = X | 100% missions from zone X |
| Time-of-day | in-game hour | Day/night mission variety |
| Boss-blocked | recent boss defeat | Avoid boss-zone missions for 2 runs |
| Character-locked | selected jockey | Only character-specific missions |
| Random-event | 1d20 ≥ 18 | Trigger special event mission |
| Seasonal | season_change | New seasonal missions |
| Player-level | grade ≥ 5 | High-stakes missions preferred |
| Difficulty-spike | consecutive fails | 1 "safe" mission |
| ... (19 total) | | |

---

## Endgame (NG+) Missions (NEW)

11 post-Salvation missions:
- 1 boss-rush chain (5 missions)
- 6 NG+ exclusive zones (new zones, not in base game)
- 4 hard-mode variants (existing zones, harder ICE)

Gating: requires Salvation completion + NG+ active.

---

## Migration Strategy

### Adding new types to existing data

1. New types are **additive** — existing `extract_data`, `defeat`, etc. unchanged
2. New missions use new types AND existing types
3. Old missions remain with their existing types
4. New types are recognized by `MissionType` enum extension

### Backward compatibility

- Existing 111 missions: 0 modifications needed
- New 153+ missions: use new + existing types
- Schema validation: optional `type` field accepting any string

---

## Acceptance Criteria

- [ ] 5 new types defined + JSON examples
- [ ] 1 example chain documented
- [ ] 19 random selection rules listed
- [ ] 11 endgame missions scoped
- [ ] All changes are additive (no regressions)
- [ ] Existing 111 missions continue to work

## Status

**Active** — Phase 11 implementation in progress. New types added to `missions.json` per zone rebalancing plan.

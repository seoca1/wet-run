# Balance Audit — Phase E-3

> **Generated**: 2026-07-26
> **Scope**: wet_run playable missions × 6 grades × PPL formula
> **Tool**: Phase E-3 data analysis (no gameplay changes)
> **Status**: Informational — recommendations to inform future balancing

## Executive Summary

The wet_run mission roster has **94 playable missions** (missions with Fiction source — Bridge/Blue Ant excluded per AGENTS.md §4.0). Coverage is balanced across grades 1-6, but Grade 6 has only 1 mission (significant under-representation). Reward credits field is currently unset for all missions (0 across the board).

## Mission Distribution by Grade

| Grade | Count | % of Total | Notes |
|---|---|---|---|
| 1 (Tier 1, novice start) | 16 | 17% | Good onboarding coverage |
| 2 | 18 | 19% | Good |
| 3 | 18 | 19% | Good |
| 4 | 19 | 20% | Good |
| 5 (Master tier) | 22 | 23% | Slight over-representation at endgame |
| **6** (Grand Master)** | **1** | **1%** | **Significant under-representation** |

**Recommendation**: Add 4-6 Grade 6 missions for endgame variety. Currently only `aleph_fragment` is at Grade 6, which is the canonical "final mission" — too narrow for replayability.

## Mission Distribution by Zone

| Zone | Count | Description |
|---|---|---|
| surface | 27 | Entry zone, novice-friendly |
| deep | 27 | Mid-game, hostile ICE |
| mid | 11 | Transition zone |
| core | 11 | Late-game, dangerous |
| ta | 8 | T-A endgame territory |
| freeside | 7 | High-end orbital |
| soho | 2 | Sprawl No-Tell Motel variant |
| tokyo | 1 | Exotic location |

**Observation**: surface and deep zones are 57% of missions (54 of 94). Other zones are sparser. This creates predictable zone gradients in the procedural dungeon generator.

**Recommendation**: Surface zone over-saturation (27 missions) could dilute variety. Consider rebalancing toward 15-18 per major zone (surface/deep) and increasing core/ta coverage.

## PPL Formula Analysis

PPL = (deck_tier × 3) + (program_count × 2) + (program_tier_sum) + (wetware_tier)

| Grade | Expected PPL Range | Player Gear at Grade |
|---|---|---|
| 1 (T1) | 6 (1 deck + 1 program + 1 wetware) | Ono-Sendai T1 + Wisp T1 + Standard T1 |
| 2 | 12-15 | T2 deck + 2 programs |
| 3 | 18-22 | T3 deck + 2-3 programs |
| 4 | 24-28 | T4 deck + 3-4 programs |
| 5 | 30-35 | T5 deck + 4-5 programs |
| 6 (Grand Master) | 36-42 | T6 deck + 5-6 programs (Master tier) |

## ZDR Difficulty (vs PPL)

| Zone | ZDR Base | Status vs Grade 1 PPL=6 |
|---|---|---|
| surface | 1-3 | TOUGH (0.5x) — playable but dangerous |
| mid | 4-6 | DEADLY → FUTILE (player needs T2) |
| deep | 7-10 | FUTILE for low-grade; TOUGH at Grade 3+ |
| core | 9-12 | Requires Grade 4+ |
| ta | 11-15 | Requires Grade 5+ |
| freeside | 13-18 | Requires Grade 6 |

**Critical Issue**: Grade 1 player has PPL=6 but cannot enter mid/deep zones safely. The training curve may be too steep.

**Recommendation**: 
1. Add Grade 1 missions in `mid` zone (ZDR 4-5) as a transition
2. Consider "training wheels" missions where ZDR is dynamically scaled

## Reward Credits Audit

**Finding**: All 94 playable missions have `reward_credits: 0`.

**Impact**: No economic progression between runs. Players accumulate credits only via salvage and combat drops.

**Recommendation**: Set mission rewards by grade:
- Grade 1: 50-100 credits
- Grade 2: 100-200 credits
- Grade 3: 200-400 credits
- Grade 4: 400-800 credits
- Grade 5: 800-1500 credits
- Grade 6: 1500-3000 credits

This rewards higher-grade missions appropriately and provides economic progression.

## Reward Tier Audit

**Finding**: `reward_tier` field is unset for all missions (None).

**Impact**: The loot tier (`data salvage`) system in ADR-0014 references reward_tier but receives None. Effectively all missions drop the same loot.

**Recommendation**: Backfill `reward_tier`:
- Grade 1: T1 (basic)
- Grade 2: T1-T2
- Grade 3: T2
- Grade 4: T2-T3
- Grade 5: T3-T4
- Grade 6: T4-T5

## Difficulty Curve Analysis

| Progression | Expected Player Experience |
|---|---|
| Grade 1 → 2 | 3-5 missions per grade (16 missions / 5 grades ≈ 3 missions each) |
| Grade 5 → 6 | 22 missions but only 1 at Grade 6 — feels like a wall |

**Concern**: Grade 5 → 6 transition has insufficient onboarding. Player has 22 Grade 5 missions but only 1 Grade 6. No clear "graduation" experience.

**Recommendation**: 
1. Add `final_choice` style capstone missions for Grade 6
2. Or relax the Grade 6 threshold so Grade 5 elite ICE count for progress

## Combat vs ICE Balance

47 missions reference Fiction (after Bridge/Blue Ant cleanup). Of these:
- **41 unique missions** (excluding duplicates from mission source indirection)
- **58 ICE types** available in combat
- **Average missions per ICE archetype**: 47 / 7 = 6.7

| ICE Kind | Mapped Count | Notes |
|---|---|---|
| standard | 14 | Most common (basic ICE) |
| watchdog | 8 | Patrolling ICE |
| construct | 24 | Loa/AIs |
| goliath | 4 | Heavy ICE |
| black | 3 | Lethal ICE |
| wintermute | 5 | Boss-tier |
| ta_construct_prime | 0 | Reserved for T-A |

**Observation**: Phase A-2 mapped 58 ICE to 7 archetypes. construct dominates (41%) which may over-saturate the archetype.

## Recommendations Summary

1. **High priority**: Add 4-6 Grade 6 missions for endgame variety
2. **High priority**: Backfill reward_credits and reward_tier fields
3. **Medium priority**: Add Grade 1 missions in `mid` zone for difficulty curve
4. **Medium priority**: Diversify ICE kind distribution (construct over-represented)
5. **Low priority**: Add capstone missions for graduation experience

## Methodology Notes

- Mission data sourced from `prototype/data/missions/missions.json`
- ICE data sourced from `prototype/data/combat/ice_types.json`
- PPL formula: `loadout.deck_tier * 3 + program_count * 2 + wetware_tier`
- ZDR formula: `node.zdr = base * (1 + zone_depth_multiplier)`
- Status threshold: PPL/ZDR ratio (1.5x SAFE, 1.0-1.5x MATCH, 0.75-1.0x TOUGH, 0.5-0.75x DEADLY, <0.5x FUTILE)

## References

- ADR-0008 (Progression System): Item Tier T1~T5 + PPL
- ADR-0012 (Difficulty Rating): PPL & ZDR vs ratio threshold
- ADR-0014 (Data Salvage): reward_tier system
- ADR-0017 (Mission-Material Integration): mission reward structure
- `design/systems/combat.md`: Combat balance section
- `design/systems/difficulty-rating.md`: PPL/ZDR formulas
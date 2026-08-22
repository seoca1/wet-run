# Mission Chains (Phase 11 — Content Expansion)

**Document Type**: Data specification
**Status**: Active (Phase 11 implementation)
**Date**: 2026-08-08
**Related**: [ADR-0188 — Mission Expansion](../../decisions/0188-mission-expansion.md), `mission-types.md`

## Overview

Mission chains are 3-5 missions linked together as a single narrative unit. They unlock mid-game and provide:
- **Story arcs**: structured narrative across multiple encounters
- **Unique rewards**: chain-wide unlocks (programs, constructs, achievements)
- **Risk/reward balance**: chain failure has higher stakes than single mission

## Chain Schema

```json
{
  "chain_id": "ta_succession",
  "chain_name": "Tessier-Ashpool Succession",
  "chain_type": "faction_driven",
  "chain_arc": 4,
  "arc_chain": "ta_sprawl",
  "unlock_condition": {
    "arc_progress_min": 50,
    "faction_reputation": {"ta_rep": 3},
    "min_grade": 4
  },
  "missions": [
    {
      "id": "ta_investigate_3jane_initiative",
      "order": 1,
      "type": "investigation",
      "chain_role": "intro"
    },
    {
      "id": "ta_defend_straylight_perimeter",
      "order": 2,
      "type": "defense",
      "chain_role": "escalation"
    },
    {
      "id": "ta_dual_objective_ashpool_vote",
      "order": 3,
      "type": "dual_objective",
      "chain_role": "climax"
    },
    {
      "id": "ta_extract_aleph_chip",
      "order": 4,
      "type": "extraction_v2",
      "chain_role": "revelation"
    },
    {
      "id": "ta_stealth_construct_chamber",
      "order": 5,
      "type": "stealth",
      "chain_role": "resolution"
    }
  ],
  "chain_reward": {
    "construct_unlock": "ta_construct_full",
    "reputation_bonus": {"ta_rep": 25},
    "credits": 50000,
    "achievement": "succession_complete"
  },
  "chain_failure": {
    "reputation_penalty": {"ta_rep": -10},
    "construct_lock": "ta_construct_forever",
    "achievement": "succession_failed"
  },
  "chain_midpoint_save": true,
  "chain_estimated_time_minutes": 75
}
```

## Chain Phases

Each chain has 5 missions (per current design) with distinct roles:

| Role | Purpose | Example Type |
|---|---|---|
| **intro** | Establish characters, stakes | Investigation |
| **escalation** | Raise tension, new mechanics | Defense |
| **climax** | Choice moment, dual-stakes | Dual-objective |
| **revelation** | Twist, system shock | Extraction_v2 |
| **resolution** | Final confrontation | Stealth |

## Chain Categories (8 total planned, 4 implemented)

### Faction-Driven Chains (3 planned, 2 implemented)

| Chain ID | Faction | Theme | Length | Status |
|---|---|---|---|---|
| ta_succession | T-A | Family succession crisis | 5 | ✅ Implemented (Step 1) |
| mid_security_breach | Yakuza/Hosaka | Corporate consortium breach | 3 | ✅ Implemented (Step 2) |
| core_construct_war | Tessier-Ashpool | Construct war reaches core | 4 | ✅ Implemented (Step 2) |
| hosaka_internal | Hosaka | Corporate audit leak | 4 | 🔴 Pending |
| yakuza_blood | Yakuza | Enforcement hit gone wrong | 4 | 🔴 Pending |

### Character-Driven Chains (3 planned, 0 implemented)

| Chain ID | Character | Theme | Length | Status |
|---|---|---|---|---|
| case_past | Case | The dead man's memories | 4 | 🔴 Pending |
| molly_razor | Molly | The last wetwork contract | 5 | 🔴 Pending |
| angie_leopard | Angie | The 12-year-old's first kill | 3 | 🔴 Pending |

### Story-Driven Chains (2 planned, 1 implemented)

| Chain ID | Theme | Cross-trilogy | Length | Status |
|---|---|---|---|---|
| freeside_orbital_summit | The orbital sovereignty question | Sprawl + Freeside | 3 | ✅ Implemented (Step 2) |
| jackpot_signal | The peripheral fragments | Jackpot + Sprawl | 4 | 🔴 Pending |
| bridge_archive | Bay Area cousin's story | Bridge + Sprawl | 3 | 🔴 Pending |

### Implemented Chains — Detail

#### mid_security_breach (3 missions, faction-driven)

**Theme**: Yakuza consortium breach — corporate intrigue in mid-tier cyberspace

```json
{
  "chain_id": "mid_security_breach",
  "chain_name": "Mid Security Breach",
  "chain_type": "faction_driven",
  "chain_arc": 2,
  "unlock_condition": {
    "arc_progress_min": 30,
    "faction_reputation": {"yakuza": 2, "hosaka": 2},
    "min_grade": 2
  },
  "missions": [
    {"id": "mid_investigate_yakuza_consortium", "order": 1, "type": "investigation", "chain_role": "intro"},
    {"id": "mid_defend_sense_net_relay", "order": 2, "type": "defense", "chain_role": "escalation"},
    {"id": "mid_dual_objective_hosaka_data", "order": 3, "type": "dual_objective", "chain_role": "climax"}
  ],
  "chain_reward": {
    "construct_unlock": "mid_construct_partial",
    "reputation_bonus": {"yakuza": 15, "hosaka": 15},
    "credits": 12000,
    "achievement": "mid_breach_complete"
  },
  "chain_failure": {
    "reputation_penalty": {"yakuza": -10, "hosaka": -10},
    "construct_lock": "mid_construct_partial"
  }
}
```

#### core_construct_war (4 missions, faction-driven)

**Theme**: Construct war reaches core — Tessier-Ashpool's deepest secret

```json
{
  "chain_id": "core_construct_war",
  "chain_name": "Construct War",
  "chain_type": "faction_driven",
  "chain_arc": 3,
  "unlock_condition": {
    "arc_progress_min": 60,
    "faction_reputation": {"ta_rep": 4},
    "min_grade": 3
  },
  "missions": [
    {"id": "core_investigate_ice_lord", "order": 1, "type": "investigation", "chain_role": "intro"},
    {"id": "core_defend_data_citadel", "order": 2, "type": "defense", "chain_role": "escalation"},
    {"id": "core_dual_objective_construct_heist", "order": 3, "type": "dual_objective", "chain_role": "climax"},
    {"id": "core_extract_aeslin_key", "order": 4, "type": "extraction_v2", "chain_role": "revelation"}
  ],
  "chain_reward": {
    "construct_unlock": "core_construct_full",
    "reputation_bonus": {"ta_rep": 30},
    "credits": 35000,
    "achievement": "construct_war_victor"
  },
  "chain_failure": {
    "reputation_penalty": {"ta_rep": -15},
    "construct_lock": "core_construct_forever"
  }
}
```

#### freeside_orbital_summit (3 missions, story-driven)

**Theme**: Orbital sovereignty — Freeside's political question

```json
{
  "chain_id": "freeside_orbital_summit",
  "chain_name": "Orbital Summit",
  "chain_type": "story_driven",
  "chain_arc": 4,
  "unlock_condition": {
    "arc_progress_min": 75,
    "faction_reputation": {"freeside": 3},
    "min_grade": 4
  },
  "missions": [
    {"id": "freeside_investigate_orbital_sovereignty", "order": 1, "type": "investigation", "chain_role": "intro"},
    {"id": "freeside_defend_orbital_habitat", "order": 2, "type": "defense", "chain_role": "escalation"},
    {"id": "freeside_dual_objective_space_jockey", "order": 3, "type": "dual_objective", "chain_role": "climax"}
  ],
  "chain_reward": {
    "construct_unlock": "freeside_construct_partial",
    "reputation_bonus": {"freeside": 20},
    "credits": 22000,
    "achievement": "orbital_summit_complete"
  },
  "chain_failure": {
    "reputation_penalty": {"freeside": -10},
    "construct_lock": "freeside_construct_partial"
  }
}
```

## Chain Mechanics

### Progression

```python
class ChainState:
    chain_id: str
    current_mission_order: int
    completed_missions: list[str]
    failed_missions: list[str]
    midpoint_save_used: bool
    
    def can_progress(self) -> bool:
        return self.current_mission_order < len(self.missions)
    
    def mark_complete(self, mission_id: str) -> None:
        self.completed_missions.append(mission_id)
        self.current_mission_order += 1
    
    def mark_failed(self, mission_id: str) -> None:
        self.failed_missions.append(mission_id)
        # Chain fails entirely
```

### Mid-Chain Save

Chains can have a midpoint save point (after the escalation mission). If player fails after this point, they can retry from the midpoint without losing the entire chain.

**Implementation**: Save `ChainState` after midpoint mission. On failure, restore from midpoint.

### Failure Semantics

- **Pre-midpoint failure**: Chain resets completely (player can retry from start)
- **Post-midpoint failure**: Player can retry from midpoint IF save was used
- **Final mission failure**: Chain ends (no retry without starting over)

### Unlock Conditions

Each chain has specific unlock conditions:
- Arc progress (must complete X% of arc)
- Faction reputation (specific tier)
- Player grade (minimum combat level)
- Pre-requisite chains (achieve X first)

## Chain Save Mechanics

```python
# Per-chain save in save file
chain_save: dict[str, ChainState] = field(default_factory=dict)

def save_chain_state(state: ChainState) -> None:
    chain_save[state.chain_id] = state

def load_chain_state(chain_id: str) -> ChainState | None:
    return chain_save.get(chain_id)
```

## Acceptance Criteria

- [ ] 8 chains defined (3 faction + 3 character + 2 story)
- [ ] ta_succession chain fully detailed (5 missions)
- [ ] Chain save/restore logic implemented
- [ ] Midpoint save point tested
- [ ] Failure semantics tested
- [ ] Chain-wide rewards register correctly

## Status

**Active** — Phase 11 implementation in progress. 1 sample chain (ta_succession) defined with 5 missions. 7 more chains planned.

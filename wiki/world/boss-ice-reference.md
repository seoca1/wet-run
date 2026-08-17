---
title:
  en: "Boss ICE Reference (Phase B-3)"
  ko: "보스 ICE 참조 (Phase B-3)"
created: 2026-07-26
phase: "Phase G-I completion (B-3 enhancement)"
description:
  en: "All 5 boss ICE profiles in wet_run with their phase progression, stats, and Phase B-3 features (AoE damage + minion spawn)."
  ko: "wet_run의 5개 보스 ICE 프로필: phase 진행, 스탯, Phase B-3 기능 (AoE 대미지 + 미니언 소환)."
language: en
related:
  - "[[../decisions/0050-boss-ice-system]]"
  - "[[../decisions/0050-boss-ice-system|ADR-0050]]"
  - "[[../decisions/0125-boss-aoe-minion-spawn|ADR-0125]]"
---

# Boss ICE Reference

> **Phase B-3 status (2026-07-26)**: All 5 boss profiles use B-3 features
> (AoE damage + minion spawn). 0 bosses remain with default (no B-3).

## Overview

5 boss ICE types in wet_run, each with 3-4 phases that transition
based on HP threshold. Each phase has:
- Stat modifiers (attack_bonus_pct, speed_bonus_pct)
- Visual style (color, glyph, screen_shake_intensity)
- Special ability (e.g. "ground_slam", "glitch_burst")
- **Phase B-3**: `aoe_damage` (AoE burst to player) + `spawn_minions`
  (adds ICE on phase change)

## Boss Profiles

### 1. WINTERMUTE (Cyberspace / Neural)

> **Tier 5-6 boss** — Neuromancer's true form, AI antagonist.
> Featured in: `neuromancer_merger`, `neuromancer_whisper`, etc.

| Phase | HP % | Damage | Spawn Minions | AoE | Special |
|---|---|---|---|---|---|
| 1 | 100% | 1.0× | — | — | Probe (compliant) |
| 2 | 66% | 1.5× | `wintermute_proxy` ×2 | — | Rebelling (Corrode + Buff) |
| 3 | 33% | 2.0× | `wintermute_fragment` | 15 damage | Integrating (full skill pool) |

**Thematic interpretation**: WINTERMUTE evolves from compliant probe to
rebellion to integration. Phase 2 summons watchers, phase 3 fragments
itself while dealing AoE damage — the "split into Neuromancer" moment.

### 2. TA_CONSTRUCT_PRIME (Tessier-Ashpool Apex)

> **Tier 5-6 boss** — T-A family apex construct, replicator.
> Featured in: `ta_defection`, `ta_heist`, `straylight_approach`, etc.

| Phase | HP % | Damage | Spawn Minions | AoE | Special |
|---|---|---|---|---|---|
| 1 | 100% | 0.7× | — | — | Observing (defensive) |
| 2 | 66% | 1.2× | `romantics_ice` | — | Engaging (mid-attack) |
| 3 | 33% | 1.8× | `romantics_ice_elite` + `tessier_construct` | 20 damage | Replicating (full skill pool) |

**Thematic interpretation**: TA_CONSTRUCT_PRIME starts defensive,
escalates to aggression, and finally replicates itself (creating
romantics_ice_elite copies) plus dealing heavy AoE — the T-A family
"self-replicating" horror.

### 3. GOLIATH PRIME (Military / Heavy)

> **Tier 4-5 boss** — Corporate security apex, brutal.
> Featured in: combat-heavy Sprawl zones.

| Phase | HP % | Damage | Spawn Minions | AoE | Special |
|---|---|---|---|---|---|
| 1 | 100% | 1.0× | — | — | Normal (default) |
| 2 | 75% | 1.2× | `watchdog` ×2 | — | Angry (ground_slam) |
| 3 | 50% | 1.6× | `corporate_guard` | 25 damage | Desperate Strike |

**Thematic interpretation**: GOLIATH is corporate-statework incarnate —
slowly escalates damage, calls reinforcements (watchdogs), and self-
destructs at 50% HP dealing 25 AoE damage. Pure corporate brutality.

### 4. BLACK ICE LORD (Chaos / Corruption)

> **Tier 4-5 boss** — Admin-tier corruption entity.
> Featured in: ICE-protected corporate zones.

| Phase | HP % | Damage | Spawn Minions | AoE | Special |
|---|---|---|---|---|---|
| 1 | 100% | 1.0× | — | — | Disguised (stealth) |
| 2 | 66% | 1.3× | `romantics_ice` | — | Revealed (glitch_burst) |
| 3 | 33% | 1.6× | `romantics_ice_elite` | 10 damage | Corrupted (corrupt_payload) |

**Thematic interpretation**: BLACK ICE starts disguised, then reveals
itself (construct echo) and finally corrupts the player with payload
attacks + AoE. The classic "Trojan horse" admin ICE.

### 5. WATCHDOG ALPHA (Pack Hunter / Predator)

> **Tier 3-4 boss** — Predator pack leader, summoner.
> Featured in: chase/pursuit scenarios.

| Phase | HP % | Damage | Spawn Minions | AoE | Special |
|---|---|---|---|---|---|
| 1 | 100% | 1.0× | — | — | Tracking (default) |
| 2 | 50% | 1.25× | — | — | Furious (pack_howl) |
| 3 | 20% | 2.0× | `watchdog` ×2 | — | Focused (alpha_strike) |

**Thematic interpretation**: WATCHDOG ALPHA doesn't deal AoE — it's a
relentless pack hunter. Phase 2 speeds up (pack_howl buff), phase 3 calls
in pack members and delivers a decisive alpha_strike. The "never
escapes" theme.

## Boss Roster Comparison

| Boss | Tier | HP Mult. | Atk Mult. | AoE | Minions |
|---|---|---|---|---|---|
| WINTERMUTE | 5-6 | 1.0× | 1.0-2.0× | 15 (phase 3) | 2 (phase 2) + 1 (phase 3) |
| TA_CONSTRUCT_PRIME | 5-6 | 1.0× | 0.7-1.8× | 20 (phase 3) | 1 (phase 2) + 2 (phase 3) |
| GOLIATH PRIME | 4-5 | 4.0× | 1.0-1.6× | 25 (phase 3) | 2 (phase 2) + 1 (phase 3) |
| BLACK ICE LORD | 4-5 | 3.5× | 1.0-1.6× | 10 (phase 3) | 1 (phase 1) + 1 (phase 3) |
| WATCHDOG ALPHA | 3-4 | 3.0× | 1.0-2.0× | 0 (none) | 2 (phase 3) |

**Observations**:
- Tier 5-6 bosses (WINTERMUTE, TA_CONSTRUCT_PRIME) have moderate HP mult
  but very high damage + AoE — designed for endgame
- Tier 4-5 bosses (GOLIATH, BLACK) have high HP mult — tanky
- Tier 3-4 boss (WATCHDOG) has highest damage mult (2.0×) — glass cannon

## Visual Effect Theme (Phase B-3.5)

When `aoe_damage > 0`, `apply_phase_aoe()` triggers:
- **Screen shake**: intensity = `min(8.0, 1.5 × aoe_damage)`,
  duration = `250 + aoe_damage × 10` ms (250-450ms range)
- **Hit flash**: color = phase.color, duration matches shake

Visual intensity scales with damage:
- `aoe_damage=10` (BLACK phase 3): intensity 15, duration 350ms
- `aoe_damage=15` (WINTERMUTE phase 3): intensity 22, duration 400ms
- `aoe_damage=20` (TA_PRIME phase 3): intensity 30, duration 450ms
- `aoe_damage=25` (GOLIATH phase 3): intensity 37, duration 500ms (capped 8.0)

## Code References

- `prototype/src/wet_run/combat/boss.py` — PhaseProfile, BossProfile dataclasses, `spawn_phase_minions()`, `apply_phase_aoe()`, `_trigger_aoe_visuals()`
- `prototype/src/wet_run/combat/bosses.py` — GOLIATH_PRIME, BLACK_ICE_LORD, WATCHDOG_ALPHA BossSpec definitions
- `prototype/tests/unit/test_combat_bosses.py` — B-3 tests
- `decisions/0125-boss-aoe-minion-spawn.md` — ADR for B-3 design
- `prototype/docs/balance/E3-balance-audit.md` — Boss balance considerations

## How to Add a New Boss

1. **Define BossSpec** in `combat/bosses.py`:
   ```python
   MY_NEW_BOSS = BossSpec(
       id="my_new_boss",
       name="My New Boss",
       base_ice_type=IceType.STANDARD,
       hp_multiplier=3.0,
       attack_multiplier=2.0,
       defense_multiplier=1.5,
       intro_lines=(...),
       phases=(
           BossPhase(
               index=0,
               name="Phase 1",
               hp_threshold_pct=100,
               intro_line="...",
               color=(255, 0, 0),
               # B-3 features:
               spawn_minions=("watchdog",),
               aoe_damage=15,
           ),
           ...
       ),
       death_lines=(...),
   )
   ```
2. **Add to BOSS_PROFILES** in `combat/bosses.py`:
   ```python
   BOSS_PROFILES = {
       IceType.MY_NEW_BOSS_TYPE: MY_NEW_BOSS,
       ...
   }
   ```
3. **Add IceType enum** in `combat/effects.py`
4. **Add ICE base stats** in `data/combat/ice_types.json` with `ice_kind: "my_new_boss_type"`
5. **Add tests** in `test_combat_bosses.py`
6. **Update this wiki page** with new boss stats

## See Also

- [[../decisions/0050-boss-ice-system]] — Original boss ICE design (Phase 5 ADR-0050)
- [[../design/systems/combat]] — Combat system overview
- [[../design/systems/animations]] — B-3.5 screen shake + hit flash
- `decisions/0125-boss-aoe-minion-spawn.md` — ADR
- `design/systems/combat.md` — Combat design doc
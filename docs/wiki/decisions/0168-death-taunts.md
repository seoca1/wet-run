# ADR-0168: Death Taunts Library (Per-Boss + Per-ICE)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (Pillar 5 style, Pillar 3 death weight)
**관련**: [ADR-0050 — Boss ICE System](./0050-boss-ice-system.md), [ADR-0149 — Boss Phase 4 Finale](./0149-boss-phase4-finale.md), [ADR-0162 — Boss Phase 5 Last Stand](./0162-boss-phase-4.md), [ADR-0169 — Combat Cinematics](./0169-combat-cinematics.md)

## 컨텍스트 (Context)

When a player kills an ICE, there's no "last words" — the ICE just
disappears. After v1.2.0+ Polish added cinematic death sequences
for BOSSes, the *regular* ICE kills feel flat by comparison.

Track D.1 adds **Death Taunts** — one-line flavor text per ICE/boss
type that fires when the ICE is killed. Taunts are Gibson-toned,
brief, and add weight to kills.

Tracks:
- **Per-ICE**: standard ICE types (watchdog, goliath, black, construct)
- **Per-BOSS**: Wintermute, T-A Construct Prime (extends existing boss
  death sequence)

## 결정 (Decision)

### Taunt schema

```python
@dataclass(frozen=True, slots=True)
class DeathTaunt:
    enemy_type: str
    ice_name: str
    text: str
    rarity: float = 1.0  # 0.0-1.0, probability of triggering
```

### Implementation surface

**`combat/death_taunts.py`** (NEW):
- `DEATH_TAUNTS: dict[str, list[DeathTaunt]]` — keyed by ice_id
- `get_taunt(ice_id, rng) -> str | None` — return random taunt or None
- `set_death_taunt(ice_id, taunt)` — register custom taunt
- `taunt_count(ice_id) -> int`
- `all_taunt_ice_ids() -> tuple[str, ...]`

**`tests/unit/test_death_taunts.py`** (NEW):
- 10+ tests covering registry, get_taunt, rarity, customization.

## Consequences (결과)

**Pillar 3 (The Flatline)**: ICE kills have weight — each kill has story.

**Pillar 5 (The Style)**: Per-ICE taunts — "you floored a watchdog. It gibbers: 'pack... will hunt...'" — Gibson tone.

**Test additions**: ~10 tests.

## Implementation Status (2026-08-20)

**Status**: 🟡 Partial

**Evidence**:
- `prototype/src/wet_run/combat/death_taunts.py:14` — `DeathTaunt` frozen dataclass (enemy_type, ice_name, text, rarity)
- `prototype/src/wet_run/combat/death_taunts.py:23` — `DEATH_TAUNTS` registry keyed by ice_id with Gibson-toned taunts for: `watchdog` (3), `goliath` (3), `black` (3), `construct` (3), `wintermute` (4), `ta_prime` (2), `neuromancer` (2), `goliath_prime` (2), `black_ice_lord` (2), `standard` (2), `patrol` (2), `hunter` (2) — covers all spec categories + 5 boss types
- `prototype/src/wet_run/combat/death_taunts.py:94` — `get_taunt(ice_id, rng)` rarity-weighted selection
- `prototype/src/wet_run/combat/death_taunts.py:128` — `add_taunt` (spec called it `set_death_taunt`; renamed) and `register_taunts`
- `prototype/src/wet_run/combat/boss_phase4/taunts.py:21` — separate `DEATH_TAUNTS` dict for 5 boss types
- `prototype/src/wet_run/combat/boss_phase4/taunts.py:50` — `pick_death_taunt(boss_id, rng)`
- `prototype/src/wet_run/combat/boss_phase4/taunts.py:66` — `apply_death_taunt(state, app_state, boss_id)` writes to `app_state.death_taunt`
- `prototype/tests/unit/test_death_taunts.py:1` — 91 LOC covering registry, get_taunt, rarity, customization

**Notes**: Library + registry + Gibson-flavored taunts for 9+ ICE types are all in place. Boss-side wiring is complete via `boss_phase4/taunts.apply_death_taunt` (consumed by `combat_to_death` flow). However, **per-ICE regular taunts are not yet hooked into the kill path**: `get_taunt` from `combat/death_taunts.py` has no call site in `combat/state.py` (kill handling), `combat/state_transitions.py`, or `combat/salvage.py`. Spec's `set_death_taunt` was renamed to `add_taunt` / `register_taunts` for API symmetry.

**Open items**: Wire `get_taunt(enemy.ice_id, rng)` into the player-kills-ICE path in `combat/state.py` / `state_transitions.py` (after HP<=0 check); push the returned taunt text to `state.push()` or death summary; ensure regular kill taunts appear in post-combat death summary view.

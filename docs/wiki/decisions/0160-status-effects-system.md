# ADR-0160: Status Effects System Expansion (DoT/Stun/Slow/Silence/Vulnerability)

**상태**: Accepted
**날짜**: 2026-08-07
**결정자**: 사용자
**우선순위**: P1 (The Build, Pillar 3 weight)
**관련**: [ADR-0003 — Combat System (RT-MS)](./0003-combat-system.md), [ADR-0148 — Combat Depth Expansion](./0148-combat-depth-expansion.md), [ADR-0152 — Multi-Enemy Encounters](./0152-multi-enemy-encounters.md), [ADR-0156 — Combat State Split](./0156-combat-state-split.md)

## 컨텍스트 (Context)

`combat/state_models.py::StatusEffect` already supports 6 effect types via
field-driven flags (`is_stunned`, `is_staggered`, `is_shield`, `dot_damage`,
`heal_per_tick`, `attack_bonus`). Existing effect_ids in active use:
`burn`, `regen`, `powered`, `weakened`, `stun`, `stagger`.

Track B.1 expands the system to a **full 5-effect vocabulary**:
- **DoT** (already exists: `burn`)
- **Stun** (already exists: `stun`)
- **Slow** (NEW — attack speed reduction multiplier)
- **Silence** (NEW — disables skill use for the duration)
- **Vulnerability** (NEW — damage taken increased multiplier)

The expansion is required for:
- Track B.3 (ICE Personality Archetypes): support ICE needs predictable defensive tools
- Track B.2 (Status Effects implementation): make new effects real
- Track C.1 (Run Mutators): one mutator is "silence_only" — needs Silence effect
- Track D.1 (Death Taunts): vulnerability can amplify kill feel

## 결정 (Decision)

Extend `StatusEffect` dataclass with **3 new fields** targeting the new
mechanics, and add **2 new effect_ids** to the application surface:

### Field additions (backward-compatible)

```python
@dataclass
class StatusEffect:
    effect_id: str  # existing — discriminates effect type
    remaining_ms: int  # existing
    dot_damage: int = 0  # existing — DoT
    heal_per_tick: int = 0  # existing — HoT
    attack_bonus: int = 0  # existing — buff/debuff
    defense_bonus: int = 0  # existing
    is_stunned: bool = False  # existing
    is_staggered: bool = False  # existing
    is_shield: bool = False  # existing
    # NEW fields (ADR-0160)
    slow_pct: int = 0  # 0-100, attack speed reduction (e.g. 30 = 30% slower)
    is_silenced: bool = False  # disables skill use
    vulnerability_pct: int = 0  # 0-100, damage taken increase (e.g. 20 = +20% taken)
```

### Effect ID vocabulary (5-types)

| effect_id | Duration | Effect | Application |
|---|---|---|---|
| `burn` | existing | DoT (`dot_damage` per tick) | cycle 1, state_effects._apply_dot |
| `stun` | existing | Skip auto-attack + skills | cycle 1, state_effects._apply_stun |
| `slow` | NEW | Attack speed × (1 - slow_pct/100) | NEW: state_effects._apply_slow |
| `silence` | NEW | Skill use disabled | NEW: state_effects._apply_silence |
| `vulnerable` | NEW | Damage taken × (1 + vulnerability_pct/100) | NEW: state_effects._apply_vulnerable |

### Implementation surface

**`combat/status_effects.py`** (NEW):
- `apply_slow(state, target, slow_pct, duration_ms)` — adds slow status
- `apply_silence(state, target, duration_ms)` — adds silence status
- `apply_vulnerable(state, target, vuln_pct, duration_ms)` — adds vulnerable status
- `get_slow_multiplier(combattant) -> float` — read consumer for combat tick
- `get_vulnerability_multiplier(combattant) -> float` — read consumer for damage calc
- `is_silenced(combattant) -> bool` — read consumer for use_skill

**`combat/state_transitions.py`** (modify):
- `_tick_status_effects` skips processing if effect is_silenced for skill effects (note: tick still runs for DoT)
- `step_combat` respects `get_slow_multiplier(state.target)` for enemy auto-attack interval

**`combat/state.py`** (modify):
- `_calculate_damage` applies `get_vulnerability_multiplier(defender)` for player→ICE damage
- `use_skill` checks `is_silenced(state.player)` before allowing skill use

**`combat/state_effects.py`** (modify):
- `_apply_dot` → also accepts slow/silence/vulnerable target

## Consequences (결과)

**Pillar 3 (The Flatline)**: status effects amplify danger without
defeating it. Slow on a player makes auto-attack rate lower → more
vulnerability. Silence in a high-multi-enemy encounter forces skill
management. Vulnerability increases the "I was hit" feeling without
straight HP loss — weight preserved.

**Pillar 4 (The Build)**: status effects are EARNED via programs/skills
(not free) — preserves in-run-only meta.

**Pillar 5 (The Style)**: status effect push messages use Gibson
vocabulary ("your wetware stutters", "you are *out of phase*").

**Public API additions**:
- `from .status_effects import apply_slow, apply_silence, apply_vulnerable`
- `from .status_effects import get_slow_multiplier, get_vulnerability_multiplier, is_silenced`

**No behavior change to existing effects** — pure addition.

**Test additions**: ~30 new tests covering:
- Each new effect's application + tick + expiration
- get_slow_multiplier composes correctly with multiple slows
- get_vulnerability_multiplier composes correctly
- is_silenced blocks use_skill
- step_combat respects slow
- _calculate_damage applies vulnerability

## Validation

| Check | Expected |
|---|---|
| `pytest tests/` | 4062 + ~30 new = ~4092 pass |
| `ruff check` | All checks passed |
| `mypy src/` | 0 errors in 178+ source files |
| `wc -l combat/status_effects.py` | ~150 LOC (new module) |

## Implementation Status (2026-08-20)

**Status**: ✅ Implemented

**Evidence**:
- `prototype/src/wet_run/combat/status_effects.py:26` — `apply_slow(state, target, slow_pct, duration_ms)` adds `slow` StatusEffect
- `prototype/src/wet_run/combat/status_effects.py:38` — `apply_silence(state, target, duration_ms)` adds `silence` StatusEffect
- `prototype/src/wet_run/combat/status_effects.py:50` — `apply_vulnerable(state, target, vuln_pct, duration_ms)` adds `vulnerable` StatusEffect
- `prototype/src/wet_run/combat/status_effects.py:64` — `get_slow_multiplier()` composes multiplicatively
- `prototype/src/wet_run/combat/status_effects.py:76` — `get_vulnerability_multiplier()` composes multiplicatively
- `prototype/src/wet_run/combat/status_effects.py:88` — `is_silenced()` boolean read consumer
- `prototype/src/wet_run/combat/state_models.py` — `StatusEffect` extended with `slow_pct`, `is_silenced`, `vulnerability_pct` fields
- `prototype/src/wet_run/combat/state.py:236` — `_calculate_damage` applies `get_vulnerability_multiplier(defender)`
- `prototype/src/wet_run/combat/state.py:373` — `use_skill` checks `is_silenced(state.player)` before allowing skill use
- `prototype/src/wet_run/combat/state_transitions.py:162` — combat tick respects `get_slow_multiplier(state.player)`
- `prototype/tests/unit/test_status_effects.py:1` — 241 LOC dedicated tests covering application + tick + composition for all 5 effects
- `prototype/tests/unit/test_status_effects_v2.py:1` — 137 LOC additional v2 effects coverage (Bleed/Fatigue/Confused/Terrified, ADR-0179)

**Notes**: Module came in under target at 93 LOC (target ~150). All 3 new effect_ids (`slow`, `silence`, `vulnerable`) wired into state.py damage calc, state_transitions tick loop, and state.py use_skill. v2 extension (ADR-0179) followed naturally on top of this vocabulary.

**No further action on ADR-0160** — implementation closed.

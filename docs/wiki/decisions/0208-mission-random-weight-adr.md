# ADR-0208: Mission Random Weight Field (Phase 6 + Expansion)

**Status**: **Accepted (Option 1: simple weighting)** — 2026-08-26
**Date**: 2026-08-26
**Decider**: User (operator: "Content authoring" carry-over)
**Priority**: P1 (ADR-0166/0167 wiring completion)
**Related**: ADR-0166 (Phase 6 Arc), ADR-0167 (Mission Expansion), ADR-0206 (registry wiring)

## Context

After ADR-0206 (mission registry wiring), the deferred work was:
1. **random_weight field** in Mission dataclass for board-level weighting
2. **random_rules.py** support for per-mission weight override
3. **missions.json data authoring** for Phase 6 + Expansion priority

User selected "Content authoring" (this session) for Tier 2c+ completion.

## Decision (Option 1)

Add `random_weight: float = 1.0` field to Mission dataclass. Apply elevation weights to Arc6 (1.5) and Expansion (1.2) missions in missions.json. Filter negative weights in `apply_rule`.

## Implementation

| File | Change |
|---|---|
| `mission.py` | `random_weight: float = 1.0` field (line 138), `__post_init__` validation (line 173-175) |
| `board.py` | `_opt_float` helper, `random_weight=_opt_float(...)` in `_parse_mission` (line 363) |
| `missions.json` | 10 Arc6 + Expansion missions with weights (1.5 / 1.2) |
| `random_rules.py` | `apply_rule(mission_weights: dict[str, float] \| None = None)` filtering (line 137, 160-161) |
| `test_mission_wiring.py` | 4 new tests (default weight, Arc6/Expansion weights, validation, filter) |

## Validation

- `pytest tests/unit/test_mission_wiring.py` → 4 new tests passing
- Mission dataclass `random_weight` default 1.0 (backward compatible)
- `__post_init__` enforces `random_weight >= 0`
- `apply_rule` filters missions with weight < 0

## Future

- Tier 3+: weighted random pick in `JobBoard.select_weighted()` using `random_weight` as multiplier
- Tier 3+: per-fixer weight overrides (e.g., `finn_preferred_missions`)

## Change Log

- 2026-08-26: Draft → **Accepted (Option 1)** — this session. 7/7 sub-steps completed. random_weight field + validation + parsing + missions.json data (10 missions) + apply_rule filter + 4 tests. Commit + push pending.

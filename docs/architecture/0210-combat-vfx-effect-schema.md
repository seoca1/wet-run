# ADR-0210: Combat VFX Effect Schema (Cross-Version Standardization)

**상태**: Accepted (2026-08-31)
**날짜**: 2026-08-31
**결정자**: 사용자 (operator)
**우선순위**: P2 (Cross-version parity, player-facing polish)
**관련**:
- [ADR-0199 — Wet Run Web MVP (Tier 1)](./0199-wetrun-web-mvp.md) — established Python → JSON → web export pattern
- [ADR-0145 — effects_vfx 3-way split (Python)](./decisions/0145-effects-vfx-3-way-split.md) — Python's 16 skill animations + 7 cinematic sequences + 10 spawn functions
- [ADR-0112 — combat/effects.py size reduction](./decisions/0112-combat-effects-size.md) — Python effects module history

## 컨텍스트 (Context)

Two codebases implement combat visual effects with divergent taxonomies:

**Python prototype** (`prototype/src/wet_run/combat/`):
- 16 skill animation factories (attack/heavy_attack/pierce/multi_hit/dot/poison/shield/heal/regen/buff/debuff/stun/counter/lifesteal/detect/critical_hit)
- `SKILL_EFFECT_ANIMATIONS` dict + `get_animation_for_effect()` factory
- 7 cinematic sequences (5 ICE intro/death per IceType + 2 boss phase transitions)
- 10 spawn functions (spawn_hit_effects, spawn_ice_intro/death, spawn_critical, spawn_status_icon, spawn_jackin_glitch/jackout_whiteout, spawn_room_flash, spawn_aoe_screen_flash, spawn_data_acquired)
- ASCII animation with `duration_ms` (frame-level timing)

**TypeScript wet_run-web** (`wet_run-web/src/renderer/combat_vfx.ts`):
- 11 kinds only (card_use, card_hit, ice_hit, player_hit, status_apply, victory, defeat, boss_phase_1..4)
- Tick-based timing (not ms), grid-overlay rendering
- No skill effect animation vocabulary — only attack/hit/status/outcome

**Problem**: Effect names, payload shapes, and timing semantics have drifted. Designers cannot guarantee the same effect fires the same way on both platforms. Adding a new effect requires touching 2-3 separate code paths with different naming conventions.

User's hard constraint (2026-08-31): **버전별로 가급적 공통화시켜야 돼** (standardize across versions as much as possible).

## 고려한 옵션 (Considered Options)

### Option 1: Shared JSON schema + Python export (RECOMMENDED — adopted)

- **설명**: Single source of truth at `prototype/data/effects.json`. Export script generates `wet_run-web/src/data/effects.json` (slim copy) + `effects.d.ts` (TypeScript types). Both platforms consume the export; only rendering primitives remain platform-specific.
- **장점**:
  - Single taxonomy (15 v1 effects) — no naming drift
  - Python's richer ASCII animation frames remain Python-only (Python uses multi-line art sequences; web uses single-cell overlays)
  - Export script validates schema before writing — catches typos at build time
  - Parity test (`prototype/tests/test_effect_parity.py`) detects drift if web copy wasn't regenerated
  - Follows ADR-0199 §Tech Stack precedent ("Reuses wet_run/data/ via Python export script")
- **단점**:
  - Two-file maintenance (canonical + exported) until script runs
  - Web renders can't be data-driven (still hardcoded switch in combat_vfx.ts)
  - Effects.d.ts is regenerated; manual edits to runtime types break parity

### Option 2: Both platforms read same JSON at runtime — REJECTED

- Python would need to embed JSON in tcod assets; web already does. No improvement over Option 1, just shifts the import site.

### Option 3: Render web ASCII art from Python exported frames — REJECTED

- Python uses multi-frame sequences with `(dx, dy)` offsets; web uses Grid overlays. Different rendering models. Forced unification would require rewriting both renderers without gain.

### Option 4: Share nothing, document differences — REJECTED

- Violates user's "공통화" requirement. Drift over time.

## 결정 (Decision)

**Adopt Option 1: shared JSON schema + Python export.**

### Canonical schema shape

`prototype/data/effects.json` defines 15 v1 effects with:

```jsonc
{
  "kind": "attack",                   // canonical name (shared across versions)
  "category": "combat.skill",         // grouping
  "description": "...",                // design intent
  "payload_shape": {                   // typed payload contract
    "program_name": "string",
    "damage": "integer"
  },
  "duration_ms": 240,                  // canonical duration (Python renders ms)
  "color_hint": "DAMAGE_COLOR",        // palette key (Python has full palette; web maps subset)
  "tier": "v1"                         // version marker for future expansion
}
```

**Platform contract**:
- Both platforms MUST honor the `kind` taxonomy (no platform-specific aliases)
- Both platforms MUST respect the `payload_shape` keys
- Python uses `duration_ms` directly; web derives `duration_ticks = ceil(ms / 16)`
- Web maps `color_hint` to its `PALETTE.*` constants; falls back to `DEFAULT_COLOR` for missing keys

### v1 Effect Inventory (15 effects)

| Category | Kind | Web (current) | Python (current) |
|---|---|---|---|
| combat.skill | attack | ✅ | ✅ |
| combat.skill | heal | ✅ NEW | ✅ |
| combat.skill | shield | ✅ NEW | ✅ |
| combat.skill | buff | ✅ NEW | ✅ |
| combat.skill | debuff | ✅ NEW | ✅ |
| combat.skill | stun | ✅ NEW | ✅ |
| combat.hit | ice_hit | ✅ | ✅ |
| combat.hit | player_hit | ✅ | ✅ |
| combat.hit | critical_hit | ✅ NEW | ✅ |
| status | status_apply | ✅ | ✅ |
| cinematic | ice_intro | ✅ NEW | ✅ |
| cinematic | ice_death | ✅ NEW | ✅ |
| cinematic | boss_phase_transition | ✅ UNIFY (was 4 kinds) | ✅ |
| outcome | victory | ✅ | (was missing) |
| outcome | defeat | ✅ | (was missing) |

**Deferred to Tier 6+** (Python-only today):
- heavy_attack, pierce, multi_hit, dot, counter, lifesteal, detect, regen
- jackin_glitch, jackout_whiteout, room_flash, aoe_screen_flash, data_acquired (Matrix VFX)

### File structure

```
prototype/
├── data/
│   └── effects.json          # CANONICAL (15 effects)
└── tests/
    └── test_effect_parity.py # Drift detection

wet_run-web/
├── scripts/
│   └── export_effects.py     # Validates + writes artifacts
├── src/data/
│   ├── effects.json          # GENERATED (do not edit)
│   └── effects.d.ts          # GENERATED TypeScript types
└── tests/
    └── effects_schema.test.ts # Schema integrity check
```

### Naming unification

Old web names migrated to canonical:
- `card_use` → `attack`
- `card_hit` removed (folded into `ice_hit`; `critical_hit` for crits)
- `boss_phase_1`/`2`/`3`/`4` → single `boss_phase_transition` with `payloadNum: 1|2|3|4`

This matches Python's `boss_phase_transition_sequence(ice_type, phase)` factory signature.

### Backward compatibility

- `CombatVfxKind` is renamed but old web code sites are updated atomically (no deprecation period — web is pre-release Tier 5.6)
- Python `effects_vfx_animations.SKILL_EFFECT_ANIMATIONS` keeps its 16 keys; mapping to canonical 15 names happens at call site (e.g., `effects_vfx_animations.get_animation_for_effect("attack")` returns the existing `attack_animation()`)
- Tier 6 will rename Python animation factories to canonical names + add backward-compat shims

## 결과 (Consequences)

### Positive

- 15-effect taxonomy is canonical and tested
- Effect parity test (`test_effect_parity.py`) catches drift on every CI run
- Adding a new effect = edit `prototype/data/effects.json` + run export script (1 commit, 2 files)
- Web build size: 160.63 KB → 162.52 KB (+1.9 KB for 6 new effect renderers)
- Designer-facing taxonomy: 1 schema file, not 2 divergent codebases

### Negative

- Python's `effects_vfx_animations.py` keeps old names until Tier 6 (one-time rename burden)
- Web renderers are still hardcoded; data-driven ASCII art would require larger refactor
- New effect onboarding requires running `export_effects.py` before web tests (CI step needed)

### Risks

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| 1 | Drift between prototype/data/effects.json and web/src/data/effects.json if export script isn't re-run | M | M | `test_effect_parity.py` runs in CI; fails if sets diverge |
| 2 | Python effect names (heavy_attack/pierce/...) don't map to canonical v1 — designers confused | M | L | Schema comments call out deferred effects; Tier 6 brings them in |
| 3 | Web renderers can't be tested without a hand-coded grid expectation — may drift silently | L | M | `renderCombatVfx(kind, ...)` is pure; tests verify non-space cell counts per kind |
| 4 | `payload_shape` schema lacks field-level constraints (e.g., boss_phase range) | L | L | Document ranges in description; export script validates `integer[N..M]` syntax |

## Implementation Status (this commit, 2026-08-31)

| Step | Status |
|---|---|
| ADR-0210 drafted + Accepted | ✅ 2026-08-31 |
| Canonical `prototype/data/effects.json` (15 effects) | ✅ |
| `wet_run-web/scripts/export_effects.py` (validate + export) | ✅ |
| `wet_run-web/src/data/effects.json` + `effects.d.ts` generated | ✅ |
| Web `CombatVfxKind` unified (15 kinds, boss_phase_transition single) | ✅ |
| 6 new web renderers (heal, shield, buff, debuff, stun, critical_hit, ice_intro, ice_death) | ✅ |
| `state.ts` callers updated (card_use → attack, boss_phase_N → boss_phase_transition) | ✅ |
| `combat_vfx.test.ts` updated for new kind names + payloadNum | ✅ |
| `boss_phase_vfx.test.ts` rewritten for unified kind | ✅ |
| `effects_schema.test.ts` (9 cases — schema validation) | ✅ |
| `prototype/tests/test_effect_parity.py` (drift detection) | ✅ |
| TypeScript strict compile | ✅ Clean |
| Vitest run | ✅ 245/245 passed (was 226, +19) |
| Vite build | ✅ 162.52 KB / gzip 54.96 KB (+1.9 KB for new effects) |
| Playwright e2e (settings + smoke) | ✅ 8/8 passed |

## Supersedes / Amends

- **Amends** `wet_run-web/src/renderer/combat_vfx.ts` v1 (was 11 divergent kinds, now 15 canonical)
- **Amends** `prototype/src/wet_run/combat/effects_vfx_animations.py` (Python keeps 16 keys but maps to canonical names at call sites; full rename deferred to Tier 6)

## Tier 6 Implementation Update (2026-08-31, commit `941df79`)

Backport of the remaining 12 Python-only effects completed. The carry-over list below is now resolved.

| Tier 6 Step | Status |
|---|---|
| Schema bumped 1.0.0 → 1.1.0 (15 → 27 effects) | ✅ |
| 8 v2 skills added (heavy_attack, pierce, multi_hit, dot, counter, lifesteal, detect, regen) | ✅ |
| 4 v2 matrix effects added (jackin_glitch, jackout_whiteout, room_flash, data_acquired) | ✅ |
| Palette extended with 12 tokens + `resolveColorHint()` helper | ✅ |
| 12 web renderers implemented | ✅ |
| `pickProgramVfxKind()` helper (program tier/role → canonical kind) | ✅ |
| `durationForKind()` canonical duration table | ✅ |
| State wiring: matrix entry/exit, run start, burn tick, program use | ✅ |
| `tests/combat_vfx_v2.test.ts` (25 cases — v2 renderers verified) | ✅ |
| `effects_schema.test.ts` extended (27 kinds, color_hint whitelist, matrix.dungeon category) | ✅ |
| TypeScript strict compile | ✅ Clean |
| Vitest run | ✅ 285/285 passed (was 245, +40) |
| Vite build | ✅ 167.50 KB / gzip 56.30 KB (+4.98 KB for 12 new effects) |
| Playwright e2e (settings + smoke) | ✅ 8/8 passed |
| `test_effect_parity.py` | ✅ 27 kinds match |

## Deferred (Tier 7+)

- Tier 7: Data-driven ASCII art from JSON (currently hardcoded switch in web renderer)
- Tier 7: Python effect factory rename pass (`attack_animation` → canonical name compatibility shims at Python call sites; web already uses canonical names exclusively)
- Tier 7: Animation timing precision (hit flash sustained ms vs web tick-approximated)

---

*Accepted: 2026-08-31. Owner: Sisyphus. Tier 5.6 closes cross-version VFX drift; Tier 6 closes the carry-over backlog. Establishes canonical schema authored in Python, consumed via export.*

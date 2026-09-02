# ADR-0145: combat/effects_vfx Split — 3-Way Concern Split (Supplements ADR-0112 + ADR-0144)

**상태**: Accepted
**날짜**: 2026-08-05
**결정자**: 사용자
**우선순위**: P2 (Build Health)
**연관**: ADR-0002 (ASCII rendering), ADR-0050 (boss themes), ADR-0060 (matrix/dungeon VFX), ADR-0110 (module size policy), ADR-0112 (effects.py partial split), ADR-0142 (graphic_novel_view split pattern), ADR-0143 (combat_view split pattern), ADR-0144 (effects.py data extraction)

---

## 컨텍스트 (Context)

ADR-0112 에서 combat/effects.py 의 부분 분할 (effects_vfx.py 추출) 이 진행됨. 모듈 구조 (post ADR-0144):
- `combat/effects.py` (137 LOC, ADR-0144 facade) — thin re-export facade
- `combat/effects_data.py` (507 LOC, ADR-0144) — 12 data types
- `combat/effects_vfx.py` (856 LOC, ADR-0112) — animation sequences + CombatEffects + spawn functions

**문제**: effects_vfx.py 가 856 LOC 으로 ADR-0110 700-800 LOC exception 범위 상회. ADR-0112 § 향후 split plan 에서 combat/effects.py (1246 → ~3 modules) 계획이 있었으나 856 LOC monolithic 으로 남은 상태.

2026-08-05: 본 ADR-0145 에서 **3-way concern split** (ADR-0142/0143 패턴 동일) 실행 — effects_vfx.py 를 concern 별 3 modules + thin facade 로 분할.

## 적용된 변경

### 모듈 구조 (post ADR-0145)

| 모듈 | LOC | 책임 | ADR-0110 상태 |
|---|---:|---|---|
| `effects_vfx_animations.py` (신규) | 274 | 14 skill effect animation generators + SKILL_EFFECT_ANIMATIONS factory + get_animation_for_effect + critical_hit_animation | ✅ Under 500 PR threshold |
| `effects_vfx_cinematics.py` (신규) | 258 | ICE intro/death sequences (ice_intro_sequence, ice_death_sequence) + boss_phase_transition_sequence (ADR-0050) | ✅ Under 500 PR threshold |
| `effects_vfx_compose.py` (신규) | 350 | CombatEffects dataclass + 10 spawn functions (hit effects, ICE intro/death, critical, status icons, matrix/dungeon VFX per ADR-0060 Phase 1.5) | ✅ Under 500 PR threshold |
| `effects_vfx.py` (축소) | **132** | thin re-export facade | ✅ < 250 ceiling |

**Before**: effects_vfx.py 856 LOC (monolithic, above 700-800 exception)
**After**: 3 concern modules (animations + cinematics + compose) + 1 facade, max 350 LOC

### Import topology (단방향 의존성)

```
effects_data ─┬─→ effects_vfx_animations (animation generators)
              ├─→ effects_vfx_cinematics (cinematic sequences)
              ├─→ effects_vfx_compose (CombatEffects + spawn functions)
              └─→ effects_vfx (re-export facade)
                       ↑
                       └─ palette (re-exported through effects.py facade)
```

**순환 import 없음**: effects_vfx_compose → effects_vfx_animations + effects_vfx_cinematics (단방향), effects_vfx (facade) → 3 concern modules (단방향), effects_data → 모든 concern modules (단방향).

### Backward Compatibility

`combat/effects_vfx.py` 는 다음을 **re-export**:
- Data types (from effects_data): Animation, AnimationFrame, CinematicSequence, ComboCounter, FloatingNumber, HitFlash, IceType, Particle, ParticleSystem, ScreenFlash, ScreenShake, StatusIcon
- Animations (from effects_vfx_animations): 14 animation generators + SKILL_EFFECT_ANIMATIONS + get_animation_for_effect + critical_hit_animation
- Cinematics (from effects_vfx_cinematics): boss_phase_transition_sequence, ice_death_sequence, ice_intro_sequence
- Compose (from effects_vfx_compose): CombatEffects + 10 spawn functions

`__all__` 명시 + `# noqa: F401` 로 mypy/ruff 호환. **모든 import site 변경 없음**.

### Lessons from ADR-0142/0143/0144 patterns

동일 패턴 적용:
1. **단방향 의존성**: concern modules → facade → re-exports (역방향 없음).
2. **Concern-based grouping**: animations (Layer 2) / cinematics (Layer 3+5) / compose (Layer 1 + container). 각 concern 이 독립적으로 변경 가능.
3. **Re-export 패턴**: `__all__` 명시 + `# noqa: F401` 로 backward compat 유지.
4. **Import topology 최소화**: 각 concern module 은 effects_data + palette 만 직접 import — cross-concern 의존성 없음.

### 발견된 import 누락 (commit 시 fix됨)

`effects_vfx_animations.py` 작성 시 `DEFAULT_COLOR` 가 palette import 에 누락됨 (원본 effects_vfx.py 에는 있었음). Commit 시 fix:
```python
from .palette import (
    BUFF_COLOR, CRIT_COLOR, DAMAGE_COLOR, DEBUFF_COLOR,
    DEFAULT_COLOR,  # ← 추가됨
    ICE_BREAK_COLOR, SHIELD_COLOR, STUN_COLOR, HEAL_COLOR,
)
```

→ latent bug 아님 (원본에 있던 것). Split 시 누락된 import 를 발견하여 즉시 fix.

## 검증

```
$ uv run pytest tests/
3614 passed, 664 skipped, 1 xfailed, 4 xpassed in 27.74s

$ uv run ruff check src/
All checks passed!

$ uv run mypy src/
Success: no issues found in 159 source files
```

### 영향 받는 테스트 (re-export 검증)

| Test | Imports |
|---|---|
| `test_combat_effects.py` | from combat.effects_vfx import (29 symbols — CombatEffects, attack_animation, ice_intro_sequence, spawn_hit_effects, etc.) |
| `test_combat_bosses.py` | from combat.effects_vfx import CombatEffects, IceType |
| `test_regression_phase_b35.py` | from combat.effects_vfx import IceType |

All tests pass — re-export 계약 유지.

### Backward compat 검증 (내부 호출 sites)

- `combat_view_state.py::start_combat` — `from ..combat.effects import spawn_ice_intro` (effects.py facade 경유) ✅
- `combat_view_state.py::_end_combat` — `from ..combat.effects import spawn_ice_death` ✅
- `combat_view_skills.py::_spawn_skill_vfx` — `from ..combat.effects import spawn_hit_effects` ✅
- `combat_view_render.py::render_combat` — `state.combat_effects.step()` 등 ✅

모두 변경 없음 — effects.py facade 가 모든 symbol 노출.

## 결과 (Consequences)

**Accepted** (2026-08-05). Pillar 정합:
- P1 (The Build): 856 LOC 모듈 → concern 별 ~250-350 LOC 모듈 3개 + 132 LOC facade — 신규 contributor 진입 장벽 ↓
- 효과: effects_vfx.py 856 → 132 LOC (-724 LOC, -85%)

회귀 위험 평가:
- `__all__` + `# noqa: F401` 로 외부 API 변동 없음
- 신규 import path (`effects_vfx_animations`, `effects_vfx_cinematics`, `effects_vfx_compose`) 도 사용 가능 (forward compat, 내부 전용 권장)
- 3614 tests pass, 0 failed — 기능적 위험 없음

### ADR-0110 / ADR-0112 정합

- **ADR-0110** (Module Size Policy): 1000+ LOC requires ADR justification — 본 ADR 이 그 정합. 모든 모듈 500 LOC 이하.
- **ADR-0112** (effects.py partial split): 1246 → 504 → 577 LOC → effects.py facade (ADR-0144) + 본 ADR-0145 로 132 LOC facade.

### 다음 사이클 검토

- `combat/effects_data.py` 507 LOC — 500 LOC PR rejection threshold 약간 상회. 추가 분할 검토 가능 (Animation primitives vs Particle vs ScreenFlash 분리). 현재 acceptable.
- `combat/effects_vfx_compose.py` 350 LOC — Under 500 PR threshold. spawn functions 추가 시 재평가.
- 다른 > 500 LOC 모듈 없음 — wet_run engine 모듈 사이즈 정책 100% 준수.

---

*ADR-0145 closes the ADR-0112 § 향후 split plan deferred work (effects_vfx.py 856 → 132 LOC facade).*

## Implementation Status (2026-08-26)

**Status**: ✅ Implemented

**Evidence**:
- ✅ `combat/effects_vfx.py` (132 LOC, facade) — public API only
- ✅ `combat/effects_vfx_animations.py` — animation primitives concern
- ✅ `combat/effects_vfx_cinematics.py` — cinematic/boss intro concern
- ✅ `combat/effects_vfx_compose.py` (350 LOC) — composition + spawn functions
- ADR-0145 결과: effects_vfx.py 856 → 132 LOC facade (-85%), 3-way concern split 완료

**Notes**: ADR-0112 deferred work 정리. 모듈 사이즈 정책 100% 준수 (effects_data.py 507 LOC는 PR threshold 약간 상회, acceptable). ADR-0142 ~ 0145 시리즈로 "coordinator + concern modules" 패턴 확립.

---

*ADR-0142 + ADR-0143 + ADR-0144 + ADR-0145 establish the "coordinator + concern modules" pattern for monolithic modules in wet_run engine.*
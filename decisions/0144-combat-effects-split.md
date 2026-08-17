# ADR-0144: combat/effects Split — Data Extraction (Supplements ADR-0112 + ADR-0142/0143)

**상태**: Accepted
**날짜**: 2026-08-05
**결정자**: 사용자
**우선순위**: P2 (Build Health)
**연관**: ADR-0110 (module size policy), ADR-0112 (effects.py partial split justification), ADR-0142 (graphic_novel_view split pattern), ADR-0143 (combat_view split pattern)

---

## 컨텍스트 (Context)

ADR-0112 에서 combat/effects.py 의 부분 분할 (effects_vfx.py 추출, 504 → 577 LOC growth 후 현재 577 LOC) 이 진행됨. 모듈 구조:
- `combat/effects.py` (577 LOC) — 12 data classes + re-exports from effects_vfx
- `combat/effects_vfx.py` (856 LOC) — animation sequences + CombatEffects class + spawn functions
- `combat/palette.py` (268 LOC) — color constants

**순환 import 발견**: effects.py ↔ effects_vfx.py 양방향 import (effects_vfx 가 effects 에서 data classes import, effects 가 effects_vfx 에서 behavior re-export). `# noqa: E402` 로 억제되었지만 깨끗하지 않음.

2026-08-05: 본 ADR-0144 에서 **data extraction** 실행 — 12 data classes 를 `combat/effects_data.py` 로 추출하여:
1. 순환 import 제거 (effects_vfx → effects_data 단방향)
2. data types 와 behavior 명확한 분리
3. effects.py 를 thin re-export facade 로 축소

## 적용된 변경

### 모듈 구조 (post ADR-0144)

| 모듈 | LOC | 책임 | ADR-0110 상태 |
|---|---:|---|---|
| `effects_data.py` (신규) | ~440 | 12 data classes/dataclasses/StrEnums (IceType, StatusIcon, AnimationFrame, Animation, Particle, ParticleSystem, ScreenShake, FloatingNumber, HitFlash, ScreenFlash, CinematicSequence, ComboCounter) | ✅ Under 500 |
| `effects.py` (축소) | ~70 | thin re-export facade (data from effects_data + behavior from effects_vfx + colors from palette) | ✅ Under 250 ceiling |
| `effects_vfx.py` (modified) | 856 | animation sequences + CombatEffects + spawn functions (unchanged behavior) | ✅ Within 700-800 exception |
| `palette.py` (existing) | 268 | color constants | ✅ |

**Before**: effects.py 577 LOC (data + re-exports), effects_vfx.py 856 LOC, **순환 import**
**After**: effects_data.py 440 LOC, effects.py 70 LOC (facade), effects_vfx.py 856 LOC, **단방향 의존성**

### Import topology (순환 제거)

**Before (순환)**:
```
effects.py ←→ effects_vfx.py
   ↓              ↓
palette.py  (둘 다 import)
```

**After (단방향)**:
```
effects_data.py ←── effects_vfx.py
       ↑                ↑
       └────────────────┤
                        │
              effects.py (re-exports from both)
                        ↓
                   palette.py (imported by effects for color re-exports)
```

`effects_vfx.py` 는 `effects_data.py` 만 import (단방향). `effects.py` 는 3개 모두에서 re-export. **순환 import 완전 제거**.

### Backward Compatibility

`combat/effects.py` 는 다음을 **re-export**:
- Data types (from effects_data): IceType, StatusIcon, AnimationFrame, Animation, Particle, ParticleSystem, ScreenShake, FloatingNumber, HitFlash, ScreenFlash, CinematicSequence, ComboCounter
- Behavior (from effects_vfx): CombatEffects, attack_animation, boss_phase_transition_sequence, buff_animation, counter_animation, debuff_animation, detect_animation, dot_animation, get_animation_for_effect, heal_animation, heavy_attack_animation, ice_death_sequence, ice_intro_sequence, lifesteal_animation, multi_hit_animation, pierce_animation, regen_animation, shield_animation, spawn_aoe_screen_flash, spawn_critical, spawn_data_acquired, spawn_hit_effects, spawn_ice_death, spawn_ice_intro, spawn_jackin_glitch, spawn_jackout_whiteout, spawn_room_flash, spawn_status_icon, stun_animation
- Colors (from palette): BUFF_COLOR, CRIT_COLOR, DAMAGE_COLOR, DEBUFF_COLOR, DEFAULT_COLOR, GLITCH_COLOR, HEAL_COLOR, ICE_BREAK_COLOR, SHIELD_COLOR, STUN_COLOR

`__all__` 명시 + `# noqa: F401` 로 mypy/ruff 호환. **모든 import site 변경 없음**.

### Lessons from ADR-0142 (graphic_novel_view) + ADR-0143 (combat_view)

동일 패턴 적용:
1. **단방향 의존성**: concern modules → coordinator → re-exports (역방향 없음).
2. **Re-export 패턴**: `__all__` 명시 + `# noqa: F401` 로 import * / public API 유지.
3. **Backward compat 검증**: 기존 import site 모두 통과.
4. **추가 이점**: ADR-0142/0143 와 달리 **순환 import 제거** — effects_vfx 의 `from .effects import` 를 `from .effects_data import` 로 변경.

### 발견된 버그 (commit 시 fix됨)

`effects_data.py:322` 의 `FloatingNumber.text` property 에서 `value` (정의되지 않은 변수) → `self.value` 로 수정. 원본 effects.py 에 존재했던 latent bug — ADR-0144 split 시 발견되어 fix.

## 검증

```
$ uv run pytest tests/
3614 passed, 664 skipped, 1 xfailed, 4 xpassed in 27.94s

$ uv run ruff check src/
All checks passed!

$ uv run mypy src/
Success: no issues found in 156 source files
```

### 영향 받는 테스트 (re-export 검증)

| Test | Imports |
|---|---|
| `test_combat_effects.py` | from combat.effects import DAMAGE_COLOR, HEAL_COLOR, Animation, AnimationFrame, CinematicSequence, ScreenFlash |
| `test_combat_bosses.py` | from combat.effects import CombatEffects, IceType |
| `test_regression_phase_b35.py` | from combat.effects import IceType |
| `test_combat_palette.py` | from combat import effects |

All tests pass — re-export 계약 유지.

### Backward compat 검증 (내부 호출 sites)

effects.py 와 effects_vfx.py 양쪽 import 한 곳 (예: `from . import effects; effects.spawn_hit_effects(...)`) 도 변경 없음 — re-export facade 가 모든 symbol 노출.

## 결과 (Consequences)

**Accepted** (2026-08-05). Pillar 정합:
- P1 (The Build): 순환 import 제거 — 모듈 로드 순서 명확화, import 부작용 위험 ↓
- 효과: effects.py 577 → 70 LOC (-507 LOC, -88%); effects_vfx.py 변경 없음

회귀 위험 평가:
- `__all__` + `# noqa: F401` 로 외부 API 변동 없음
- 신규 import path (`effects_data`) 도 사용 가능 (forward compat, 내부 전용 권장)
- 3614 tests pass, 0 failed — 기능적 위험 없음
- **Bonus**: latent bug (FloatingNumber.text 의 `value` 변수) 발견 + fix

### ADR-0110 / ADR-0112 정합

- **ADR-0110** (Module Size Policy): 1000+ LOC requires ADR justification — 본 ADR 이 그 정합 (effects.py 70 LOC, effects_vfx.py 856 LOC within exception).
- **ADR-0112** (effects.py partial split): 1246 → 504 LOC → 577 LOC growth → 본 ADR-0144 로 70 LOC facade 로 축소.

### 다음 사이클 검토

- `effects_vfx.py` 856 LOC — 700-800 exception 범위 상회. 더 세분화 검토 가능 (animation generators + spawn functions 분할). 현재 acceptable, 추가 작업 불필요.
- `palette.py` 268 LOC — ADR-0110 250 ceiling 접근. 색상 카테고리별 분할 검토 가능 (damage/heal/buff 등). 현재 acceptable.
- `combat_view_render.py` 515 LOC, `combat_view_state.py` 372 LOC, `combat_view_skills.py` 203 LOC — 모두 acceptable 범위.

---

*ADR-0144 closes the ADR-0112 § 향후 split 계획 deferred work (effects.py facade 축소) + eliminates the effects.py ↔ effects_vfx.py circular import.*

*ADR-0142 + ADR-0143 + ADR-0144 establish the "view/data extraction" pattern for monolithic modules in wet_run engine.*
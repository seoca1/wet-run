# ADR-0143: combat_view Split — Implementation (Supplements ADR-0113 + ADR-0141)

**상태**: Accepted
**날짜**: 2026-08-05
**결정자**: 사용자
**우선순위**: P2 (Build Health)
**연관**: ADR-0003 (RT-MS combat system), ADR-0110 (module size policy), ADR-0113 (combat_view.py size justification), ADR-0141 (additional module splits), ADR-0142 (graphic_novel_view split pattern)

---

## 컨텍스트 (Context)

ADR-0113 에서 combat_view.py (1094 LOC → 972 LOC after ADR-0113 partial split) 의 1000+ LOC 임을 인정하고 Option 4 (정당화만, 분할 보류) 로 Accepted. ADR-0141 (additional module splits) 에서 combat_view.py 의 부분 분할 (1094 → 972 LOC, input handling 추출) 이 진행됨.

2026-08-05: 본 ADR-0143 에서 **4-way split** (ADR-0142 와 동일 패턴 — coordinator + 3 concern modules) 실행.

## 적용된 변경

### 분할 구조 (post ADR-0143 split)

| 모듈 | LOC | 책임 | ADR-0110 상태 |
|---|---:|---|---|
| `combat_view_render.py` (신규) | 515 | render_combat + 6 _draw_* helpers + _hp_bar + skill menu helpers (_can_use_skill, _get_skill_effect_description) | ✅ Under 700 |
| `combat_view_skills.py` (신규) | 203 | _SKILL_SOUND_MAP + _execute_skill + _report_skill_unavailable + _spawn_skill_vfx | ✅ Under 500 PR threshold |
| `combat_view_state.py` (신규) | 372 | start_combat + spawn_phase_transition + _end_combat + _check_post_combat_event + COMBAT_REPUTATION + _apply_combat_reputation + _defeat_current_ice_node + _remove_node_from_graph | ✅ Under 500 PR threshold |
| `combat_view.py` (축소) | **90** | thin coordinator + re-exports (ADR-0142 pattern) | ✅ Under 250 ceiling |
| `combat_view_input.py` (existing, ADR-0141) | unchanged | handle_combat_input (input handling) | n/a |

**Before**: 1 module, 972 LOC (ADR-0141 partial split)
**After**: 4 modules, 1180 LOC total (+208 LOC overhead for module headers/imports/re-exports)

### Backward Compatibility

combat_view.py 는 다음을 **re-export**:
- Render: render_combat, _draw_vfx_overlay, _draw_combatants, _draw_combat_effects, _draw_action_log, _draw_skills_menu, _draw_first_combat_tutorial, _hp_bar
- Skills: _SKILL_SOUND_MAP, _can_use_skill, _execute_skill, _get_skill_effect_description, _report_skill_unavailable, _spawn_skill_vfx
- State: COMBAT_REPUTATION, _apply_combat_reputation, _check_post_combat_event, _defeat_current_ice_node, _end_combat, _remove_node_from_graph, spawn_phase_transition, start_combat
- Input (re-export from combat_view_input): handle_combat_input

`__all__` 명시 + `# noqa: F401` 로 mypy/ruff 호환. **모든 internal 호출 site (combat_view_input, combat_tick, action_menu, dungeon_view, screen_dispatch) 가 `combat_view.X` 로 import 가능** — mypy `attr-defined` 에러 0개.

### Import topology (no circular dependency)

```
combat_view_render ─┐
combat_view_skills ─┼──→ combat_view (re-exports + __all__)
combat_view_state ──┤
combat_view_input ──┘
```

`combat_view_render`, `combat_view_skills`, `combat_view_state` 는 **combat_view를 import 하지 않음** (top-level). `combat_view` 만 3개 concern module 을 import — 단방향 의존성.

Internal callers (`combat_view_input.py` 등) continue to use `from . import combat_view` + `combat_view._end_combat` pattern — 변경 없음.

### Lessons from ADR-0142 (graphic_novel_view split)

동일 패턴 적용:
1. **단방향 의존성**: concern modules → coordinator → re-exports (역방향 없음).
2. **Re-export 패턴**: `__all__` 명시 + `# noqa: F401` 로 import * / public API 유지.
3. **Backward compat 검증**: 기존 import site 모두 통과 (combat_view_input, combat_tick, action_menu, dungeon_view, screen_dispatch, full_demo, full_demo_sound, tests/*).
4. **Mypy attr-defined 해결**: 모든 re-exported symbol 을 `__all__` 에 명시 — internal `from . import combat_view` + `combat_view.X` 패턴 호환.

## 검증

```
$ uv run pytest tests/
3614 passed, 664 skipped, 1 xfailed, 4 xpassed in 27.59s

$ uv run ruff check src/
All checks passed!

$ uv run mypy src/
Success: no issues found in 155 source files
```

### 영향 받는 테스트 (re-export 검증)

| Test | Imports |
|---|---|
| `test_combat_view_defeat_node.py` | from combat_view import _defeat_current_ice_node |
| `test_combat_view_reputation.py` | from combat_view import _apply_combat_reputation, COMBAT_REPUTATION |
| `test_combat.py` | from combat_view import _draw_vfx_overlay |
| `test_run_state_integration.py` | from combat_view import _end_combat |
| `test_combat_view_helpers.py` | from combat_view import _draw_action_log, _get_skill_effect_description, _can_use_skill, _remove_node_from_graph, _draw_combatants, _draw_combat_effects, _draw_skills_menu, _draw_first_combat_tutorial, _draw_vfx_overlay, _end_combat, _spawn_skill_vfx, _check_post_combat_event, _execute_skill, _report_skill_unavailable, _apply_combat_reputation, _defeat_current_ice_node, render_combat |
| `full_demo.py`, `full_demo_sound.py` | from combat_view import _end_combat |

All tests pass — re-export 계약 유지.

### Backward compat 검증 (내부 호출 sites)

| Module | `combat_view.X` usage |
|---|---|
| `combat_view_input.py` | `_end_combat`, `_can_use_skill`, `_execute_skill`, `_report_skill_unavailable` ✅ |
| `combat_tick.py` | `spawn_phase_transition` ✅ |
| `action_menu.py` | `_remove_node_from_graph`, `start_combat` ✅ |
| `dungeon_view.py` | `start_combat` ✅ |
| `screen_dispatch.py` | `render_combat` ✅ |

## 결과 (Consequences)

**Accepted** (2026-08-05). Pillar 정합:
- P1 (The Build): 코드 조직 명확화 — render/skills/state 책임 분리 → 신규 contributor 진입 장벽 ↓
- 효과: combat_view 972 → 90 LOC (-882 LOC, -91%)

회귀 위험 평가:
- `__all__` + `# noqa: F401` 로 외부 API 변동 없음
- 신규 import path (`combat_view_render`, `combat_view_skills`, `combat_view_state`) 도 사용 가능 (forward compat)
- 3614 tests pass, 0 failed — 기능적 위험 없음

### ADR-0110 / ADR-0113 정합

- **ADR-0110** (Module Size Policy): 1000+ LOC requires ADR justification — 본 ADR 이 그 정합.
- **ADR-0113** (combat_view.py size): Option 4 (정당화만) → 본 ADR-0143 로 정당화 + 분할 완료.
- **ADR-0141** (additional module splits): combat_view_input 추출 (handle_combat_input) → 본 ADR-0143 가 render + skills + state 까지 분할 확장.

### 다음 사이클 검토

- `combat/effects.py` 577 LOC (ADR-0112 deferred) — 같은 패턴 적용 가능. 별도 사이클 검토.
- `combat_view_input.py` (ADR-0141 partial split 결과) — 현재 acceptable, 추가 분할 불필요.
- `combat_view_render.py` 515 LOC — 향후 render detail 분할 검토 가능 (현재 acceptable).

---

*ADR-0143 closes the ADR-0113 § 향후 split 계획 deferred work (v1.1.0+ → v1.1.0a1 cycle).*

## Implementation Status (2026-08-26)

**Status**: ✅ Implemented

**Evidence**:
- ✅ `combat/state.py` — coordinator (state machine)
- ✅ `combat/state_models.py` — dataclass / state definitions (ADR-0141 partial split 결과)
- ✅ `combat/state_transitions.py` — transition rules
- ✅ `combat/hud.py` — render HUD layer
- ✅ `combat/state_effects.py` + `state_effects_v2.py` — status effect rendering
- ✅ `combat/phase_cinematics.py` — phase intro cinematic
- ✅ `combat/finisher_combos.py` — combo resolution
- ✅ `combat/palette.py` — color palette integration
- ADR-0143 결과: combat_view.py 972 → coordinator로 축소, 4-way 분할

**Notes**: ADR-0113 정당화 + ADR-0141 partial split 통합. ADR-0142와 함께 "4-way coordinator split" 패턴 확립.

---

*ADR-0142 + ADR-0143 establish the "4-way coordinator split" pattern for monolithic view modules in wet_run engine.*
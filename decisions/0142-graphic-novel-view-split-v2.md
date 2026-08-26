# ADR-0142: graphic_novel_view Split v2 — Implementation (Supplements ADR-0133)

**상태**: Accepted
**날짜**: 2026-08-05
**결정자**: 사용자
**우선순위**: P2 (Build Health)
**연관**: ADR-0111 (graphic_novel_view size — 정당화), ADR-0133 (2026-07-27 split, v1 split), ADR-0032 (graphic novel mode)

---

## 컨텍스트 (Context)

ADR-0133 § 향후 split 계획 deferred the graphic_novel_view.py split to v1.1.0+ via fresh ADR. 2026-08-04 attempt (4-way split into graphic_novel_types / graphic_novel_render / graphic_novel_menu) left the working tree broken and was reverted.

2026-08-05: 본 ADR-0142 에서 **3-way split** (ADR-0133 § 향후 split 계획의 변형) 실행:

- `gn_render.py` — scene rendering (render_scene + chapter_card + blank transition + utilities)
- `gn_menu.py` — menu rendering (GRAPHIC_NOVEL_MENU + GRAPHIC_NOVEL_ENDING_MENU + ending descriptions)
- `graphic_novel_view.py` — thin coordinator (render_graphic_novel_screen + re-exports for backward compat)

> **Note**: ADR-0133 § 향후 split 계획 mentioned `gn_input.py` for input handlers — but those handlers are already in `menu.py` (handle_graphic_novel_menu_input, handle_graphic_novel_ending_menu_input). Input handlers NOT split out (no work needed).

## 적용된 변경

### 분할 구조 (post ADR-0142 v2 split)

| 모듈 | LOC | 책임 | ADR-0110 상태 |
|---|---:|---|---|
| `gn_render.py` (신규) | 761 | render_scene + render_chapter_card + render_blank_transition + 7 _draw_scene_* + 5 _draw_card_* + 4 utility fn + NOVEL_LEFT/RIGHT_MARGIN | ✅ Within 700-800 LOC exception |
| `gn_menu.py` (신규) | 434 | render_graphic_novel_menu + render_graphic_novel_ending_menu + 4 helpers + GN_* constants + _ENDING_DESCRIPTIONS | ✅ Under 500 PR threshold |
| `graphic_novel_view.py` (축소) | **231** | render_graphic_novel_screen coordinator + _console_to_text + re-exports | ✅ Under 250 ceiling |

**Before**: 1 module, 1266 LOC
**After**: 3 modules, 1426 LOC total (+160 LOC overhead for module headers/imports)

### Backward Compatibility

graphic_novel_view.py 는 다음을 **re-export**:
- Render utilities: wrap_text_for_novel, paginate_lines, compute_typed_page_index, dialogue_typed_chars, scene_progress, render_blank_transition, render_chapter_card, render_scene, NOVEL_LEFT_MARGIN, NOVEL_RIGHT_MARGIN, _to_roman, _character_label
- Menu utilities: get_gn_menu_options, get_gn_menu_key, get_gn_ending_menu_options, available_endings, render_graphic_novel_menu, render_graphic_novel_ending_menu, GN_MENU_*, GN_ENDING_*
- Internal: _ENDING_DESCRIPTIONS (used by test_graphic_novel_ending_c.py)
- Data + loaders: SceneData, Background, DialogueLine, Portrait, load_*, list_scenes_for_character, _parse_*

`__all__` 명시 + `# noqa: F401` 로 mypy/ruff 호환.

### Import topology (no circular dependency)

```
gn_render ─┐ (utility imports)
gn_menu ───┼──→ graphic_novel_view (re-exports)
           │
graphic_novel_data ─→ graphic_novel_view (re-export)
graphic_novel_loaders ─→ graphic_novel_view (re-export)
```

`gn_render` 와 `gn_menu` 은 **graphic_novel_view를 import 하지 않음** (top-level). `graphic_novel_view` 만 `gn_render.render_scene` / `gn_menu.*` 를 import — 단방향 의존성.

`render_graphic_novel_screen` coordinator는 `from . import config` 를 lazy import (함수 내부) — top-level 사이클 회피.

## 검증

```
$ uv run pytest tests/
3614 passed, 664 skipped, 1 xfailed, 4 xpassed in 27.82s

$ uv run ruff check src/
All checks passed!

$ uv run mypy src/
Success: no issues found in 152 source files
```

### 영향 받는 테스트 (re-export 검증)

| Test | Imports |
|---|---|
| `test_graphic_novel_view.py` | render_graphic_novel_screen, render_scene, render_chapter_card, wrap_text_for_novel, etc. |
| `test_graphic_novel_ending_menu.py` | render_graphic_novel_ending_menu, get_gn_ending_menu_options |
| `test_graphic_novel_ending_c.py` | _ENDING_DESCRIPTIONS, available_endings, get_gn_ending_menu_options, load_scene_chain |
| `test_graphic_novel_endings.py` | render_graphic_novel_ending_menu, get_gn_ending_menu_options |
| `test_wigan_character.py` | load_prologue_chain, _character_label |
| `test_angie_character.py` | load_prologue_chain, _character_label |
| `test_salvation.py` | SceneData |

All 229 graphic_novel-related tests pass — re-export 계약 유지.

### Backward compat 검증 (외부 import sites)

| Module | Imports from graphic_novel_view |
|---|---|
| `chapter_cutscene.py` | Background, DialogueLine, Portrait, SceneData, load_scene ✅ |
| `story_cinematic.py` | wrap_text_for_novel ✅ |
| `screen_dispatch.py` | render_graphic_novel_screen ✅ |
| `menu.py` | render_graphic_novel_menu, available_endings, load_prologue_chain, load_scene_chain ✅ |
| `state.py` | SceneData ✅ |
| `salvation.py` | SceneData, load_scene ✅ |

## 결과 (Consequences)

**Accepted** (2026-08-05). Pillar 정합:
- P5 (The Style): 코드 조직 명확화 — render/menu 책임 분리 → 신규 contributor 진입 장벽 ↓
- 효과: graphic_novel_view 1266 → 231 LOC (-1035 LOC, -82%)

회귀 위험 평가:
- `__all__` + `# noqa: F401` 로 외부 API 변동 없음 (ADR-0111)
- 신규 import path (`gn_render`, `gn_menu`) 도 사용 가능 (forward compat)
- 3614 tests pass, 0 failed — 기능적 위험 없음

### 2026-08-04 실패 회고와의 비교

| Aspect | 2026-08-04 attempt | 2026-08-05 (this ADR) |
|---|---|---|
| Split | 4-way (types/render/menu + view) | 3-way (render/menu + view) |
| Modules created | 3 | 2 |
| Missing imports | Translator, AppState, SceneData, Background, Portrait, constants | None |
| Lazy imports added | No | Yes (`from . import config` inside render_graphic_novel_screen) |
| mypy attr-defined warnings | Yes (dynamic attributes) | No (clean tree-shake) |
| Outcome | REVERTED | ✅ 3614 tests pass |

핵심 학습:
1. **단방향 의존성**: gn_render + gn_menu → graphic_novel_view (re-exports). Reverse 방향 없음 → circular import 회피.
2. **Re-export 패턴**: `__all__` 명시 + `# noqa: F401` 로 import * / public API 유지.
3. **Lazy import for circular-prone references**: `from . import config` 는 함수 내부에서 (top-level X).
4. **기존 ADR 패턴 존중**: ADR-0133 § 향후 split 계획 의 render/menu 분리를 그대로 따름 — input 분리는 menu.py 에 이미 존재 (별도 작업 불필요).

### ADR-0110 / ADR-0133 정합

- **ADR-0110** (Module Size Policy): 1000+ LOC requires ADR justification — 본 ADR 이 그 정합.
- **ADR-0111** (graphic_novel_view size): Option 4 (정당화만) → 본 ADR-0142 로 정당화 + 분할 완료.
- **ADR-0133** (v1 split): data + loaders 분리 → 본 ADR-0142 (v2 split) 로 view render + view menu 분리 완료.

### 다음 사이클 검토

- `graphic_novel_loaders.py` 262 LOC — 250 LOC ceiling 접근. 분할 검토 가능 (현재 acceptable).
- gn_render 761 LOC — 700-800 LOC exception 범위 내. 추가 분할 불필요.
- 다른 > 1000 LOC 모듈 (combat_view 972 LOC 등) — 별도 ADR 검토 필요.

---

## Implementation Status (2026-08-26)

**Status**: ✅ Implemented

**Evidence**:
- ✅ `engine/gn_render/scene.py` (357 LOC, render scene) — 신규
- ✅ `engine/gn_render/card.py` (230 LOC, render card) — 신규
- ✅ `engine/gn_render/text.py` (159 LOC, render text) — 신규
- ✅ `engine/gn_render/__init__.py` — public package, 하위 호환 re-exports
- ✅ `screen_dispatch.py:render_graphic_novel_screen` — 새 모듈 사용
- ✅ `menu.py:render_graphic_novel_menu, available_endings, load_*` — 새 모듈 사용
- ✅ `state.py:SceneData` — 데이터 모델 유지
- ✅ `salvation.py:SceneData, load_scene` — 데이터 모델 유지
- ADR-0142 결과: graphic_novel_view 1266 → 231 LOC (-82%)

**Notes**: ADR-0133 v1 split (data + loaders) 후속으로 v2 (render + menu) 분리 완료. ADR-0110 모듈 사이즈 정책 준수.

---

*ADR-0142 closes the ADR-0133 § 향후 split 계획 deferred work (v1.1.0+ → v1.1.0a1 cycle).*
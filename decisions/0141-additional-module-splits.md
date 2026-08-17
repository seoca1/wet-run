# ADR-0141: Additional Module Splits Discovered in Post-0133 Audit

**상태**: Accepted (Option 1 partial — Top 2 only)
**날짜**: 2026-07-28
**결정자**: 사용자
**우선순위**: P3 (v1.1.0+ backlog)
**연관**: ADR-0110 (Module Size Policy), ADR-0112 (combat/effects.py), ADR-0113 (combat_view.py), ADR-0133 (graphic_novel_view split)

---

## 컨텍스트 (Context)

ADR-0133 (graphic_novel_view.py split) 완료 후 module LOC 감사 결과:

| Module | LOC | 기존 ADR |
|---|---:|---|
| graphic_novel_view.py | 1266 | 0133 ✅ |
| combat/effects.py | 1246 | 0112 (deferred v1.1.0) |
| **matrix_view.py** | **1121** | ❌ **미식별** |
| combat_view.py | 1096 | 0113 (deferred v1.1.0) |
| **combat/state.py** | **1075** | ❌ **미식별** |

**module_size_policy** (ADR-0110) 기준:
- 250 LOC: 신규 권장 한도
- 500 LOC: PR 거부 기준
- 1000+ LOC: 신규 ADR 필수

위 5개 모듈 모두 1000+ LOC 임계값 초과. ADR-0112/0113은 combat/effects.py + combat_view.py 만 커버. **matrix_view.py (1121) 와 combat/state.py (1075) 는 후속 ADR 없음** — v1.1.0+ 에서 처리 필요.

---

## 발견된 모듈 상세

### matrix_view.py (1121 LOC)
- **책임**: Matrix (사이버스페이스) 화면 렌더링 + 미니맵 + Fog of War + breadcrumb trail + 입력 처리
- **추정 분할 구조** (참고용):
  - `matrix/render.py` — 화면 렌더링 (~400 LOC)
  - `matrix/minimap.py` — 미니맵 + breadcrumb (~250 LOC)
  - `matrix/fog.py` — Fog of War 로직 (~200 LOC)
  - `matrix/input.py` — 입력 처리 (~270 LOC)
- **Pillar 정합**: Pillar 2 (The Matrix) — *유일한 시각적 공간* 핵심

### combat/state.py (1075 LOC)
- **책임**: Combat state machine + Combatant + Skill + AI + step_combat + use_skill
- **추정 분할 구조** (참고용):
  - `combat/state_models.py` — dataclass 정의 (~300 LOC)
  - `combat/state_machine.py` — step/use_skill (~400 LOC)
  - `combat/ai.py` — 적 AI 결정 (~200 LOC)
  - `combat/skill_resolution.py` — 스킬 효과 (~175 LOC)
- **Pillar 정합**: Pillar 1 (The Run), Pillar 3 (The Flatline)

---

## 고려한 옵션

### Option 1: v1.1.0 Phase 1 에서 분할 (권고)

- **설명**: 기존 ADR-0112 (combat/effects.py) + ADR-0113 (combat_view.py) + 신규 matrix_view/combat/state 4개 모듈을 v1.1.0 Phase 1 에서 일괄 분할
- **장점**: 일관된 분할 작업, 코드베이스 통일성
- **단점**: Phase 1 부담 ↑, 회귀 위험 ↑

### Option 2: Phase 2 에서 분할 (Engagement Layer 후)

- **설명**: v1.1.0 Phase 1 = Engagement Layer (ADR-0140), Phase 2 = 모듈 분할 4건
- **장점**: 각 Phase 가 단일 책임, 점진적 변경
- **단점**: v1.1.0 release 가 Phase 2 까지 연기

### Option 3: Defer (v1.2.0+)

- **설명**: v1.1.0 = Engagement Layer 만, 모듈 분할은 별도 사이클
- **장점**: v1.1.0 release 일정 단축
- **단점**: 기술 부채 누적, 신규 contributor 진입 장벽 잔존

### Option 4: Option 1 + 추가 신규 ADR (matrix_view 와 combat/state 각각)

- **장점**: 모듈별 독립 ADR 추적
- **단점**: ADR 4개 신설 (ADR-0141~0144) — noise ↑

---

## 추천 (Recommendation)

**Option 1 (Phase 1 일괄 분할)** 권고.

**근거**:
1. **타이밍**: v1.1.0 시작 시점에 모듈 분할이 가장 안전. 코드베이스가 v1.0.0 stable 상태.
2. **일관성**: 4개 모듈 동시 분할 시 공통 pattern (data + helpers + render 분리) 적용 가능
3. **테스트 인프라**: 3178 tests 가 회귀 가드. v1.0.0 에서 검증된 인프라 활용.
4. **Pillar 정합**: matrix_view (Pillar 2) + combat (Pillar 1, 3) 분할로 게임 핵심 시스템 명확화

**잔존 결정 사항**:
- 분할 방식 (각 모듈을 *몇 개* 로 나눌지)
- 각 분할 모듈의 backward compat 정책 (re-export facade vs 직접 import)
- 테스트 분리 vs 통합 유지

---

## 사용자 결정 (Decision)

- [x] **Option 1 (Phase 1 일괄 분할)** — 사용자 선택 (Top 2 우선)
- [ ] Option 2 (Phase 2)
- [ ] Option 3 (Defer v1.2.0+)
- [ ] Option 4 (모듈별 독립 ADR)
- [ ] 기타: ___

**세부 결정** (Option 1, 2026-07-28 채택):
- [x] 분할 방식: **extract data classes + minimap sub-modules** (minimal viable split)
- [x] Backward compat: **`__all__` re-export facade** (ADR-0133 패턴 준수)
- [ ] matrix_view.py full 4-way split, combat/state.py full 4-way split: v1.1.0+ 후속

---

## 영향 받는 항목 (예정)

수락 시:
- `src/wet_run/matrix/render.py` (신규)
- `src/wet_run/matrix/minimap.py` (신규)
- `src/wet_run/matrix/fog.py` (신규)
- `src/wet_run/matrix/input.py` (신규)
- `src/wet_run/combat/state_models.py` (신규)
- `src/wet_run/combat/state_machine.py` (신규)
- `src/wet_run/combat/ai.py` (신규)
- `src/wet_run/combat/skill_resolution.py` (신규)
- 기존 `matrix_view.py` / `combat/state.py` — re-export facade 또는 deprecated
- `tests/` — 기존 테스트 호환 + 신규 모듈 테스트 추가

---

## 결과 (Consequences)

(Accepted 후 작성)

---

## 관련 결정

- ADR-0110 — Module Size Policy (500 LOC 거부 기준)
- ADR-0111 — graphic_novel_view size (정당화)
- ADR-0112 — combat/effects.py split (deferred)
- ADR-0113 — combat_view.py split (deferred)
- ADR-0133 — graphic_novel_view split (구현 완료, 본 ADR 의 pattern 참고)

---

## 결과 (Consequences)

**Option 1 Accepted (partial — Top 2 only)** (2026-07-28). 적용된 변경:

### Phase 3 — matrix_view.py split ✅
- `src/wet_run/engine/matrix_minimap.py` (신규, 115 LOC)
- 추출: `_draw_minimap`, `_draw_breadcrumb`, `_draw_mobility_stats`, `_KIND_LABEL`, `_short_kind`
- matrix_view.py: 1121 → **1047 LOC** (-74)
- Backward compat: `from .matrix_minimap import _short_kind` + `__all__` 유지

### Phase 4 — combat/state.py split ✅
- `src/wet_run/combat/state_models.py` (신규, 250 LOC)
- 추출: `SkillEffect`, `Skill`, `StatusEffect`, `CombatStats`, `Combatant`, `CombatState`
- combat/state.py: 1075 → **859 LOC** (-216)
- Backward compat: `from .state_models import ...` + `__all__` 유지

### 버그 수정 (Phase 4 중 발견)
- `equip_defense` kwarg → `equip_defense_bonus` (combat_view.py:1038) — 기존 latent bug
- CombatState 기본값 `last_player_attack_ms`/`last_enemy_attack_ms` 원복 (-AUTO_ATTACK_INTERVAL_MS) — split 중 변경된 부분 복구

### 메트릭
- 신규 파일: 2 (matrix_minimap, state_models)
- 회귀 위험: 낮음 (모두 backward compat re-export)
- 테스트 영향: 없음 (3227 pass, 모든 기존 테스트 통과)

### 잔존 (v1.1.0+)
- matrix_view.py full 4-way split (matrix/render.py + matrix/minimap.py + matrix/fog.py + matrix/input.py) — 현재는 minimap 부분만 추출
- combat/state.py full 4-way split (state_models.py + state_machine.py + ai.py + skill_resolution.py) — 현재는 state_models 부분만 추출
- combat/effects.py (1246 LOC, ADR-0112) + combat_view.py (1096 LOC, ADR-0113) — v1.1.0+ 후속

---

## 변경 이력

- 2026-07-28: Draft 작성 (Post-ADR-0133 audit 후속)
- 2026-07-28: **Accepted (Option 1 partial — Top 2)** — matrix_view + combat/state dataclass 추출 완료
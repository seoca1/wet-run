# ADR-0103: Dungeon-only Mode — `D` 토글 제거, `matrix_view` 폐기

**상태**: Accepted
**날짜**: 2026-07-10
**결정자**: 사용자
**우선순위**: P2 (The Matrix)
**관련**: ADR-0060 (Dungeon Exploration Redesign)

## 컨텍스트 (Context)

ADR-0060 Phase 1+1.5+2+3 완료 후 매트릭스 화면은 두 가지 view로 나뉘어 있음:

1. `dungeon_view` — NetHack BSP 미로 (Phase 2 결과, 9 cast × 14 stages × 47 missions)
2. `matrix_view` — 추상 노드 그래프 (Phase 0 그래프, 5-7 Surface 노드)

`D` 키 토글로 두 view를 전환 가능. 그러나 2주 사용 결과:

- graph view는 dungeon view보다 **전술적으로 우월한 정보 제공 없음** (단순 추상화)
- toggle 유지 비용 큼: `state.dungeon_mode` 상태 관리 + 2套 렌더러 분기 + 동글매 입력 핸들러
- pure NetHack 탐험 경험이 매트릭스 몰입도(mood)에 더 적합 (사이버스페이스는 VFX 이펙트로 분리)

## 사용자 결정 (Decision)

[x] **Dungeon-only 모드 확정** (2026-07-10): `D` 키 토글 제거. `dungeon_view` 가 MATRIX screen의 유일한 렌더러/입력. `matrix_view` 폐기.

## 결과 (Consequences)

### 제거된 항목

- `state.dungeon_mode: bool` 필드
- `D` 키 토글 핸들러 (`engine/app.py`)
- `matrix_view` 분기 (render + input path)
- `_maybe_spawn_jackin_glitch` 헬퍼 (graph view 종속)
- `TestDungeonModeField`, `TestDKeyToggle` 테스트 클래스

### 유지된 항목

- `dungeon_view` — MATRIX screen의 유일한 렌더러/입력
- BSP 미로 생성 (`matrix/dungeon_generator.py:ProceduralDungeonGenerator`)
- 5-Layer VFX 시스템 (`combat/effects.py:spawn_jackin_glitch`, `spawn_room_flash`, `spawn_data_acquired`, `spawn_jackout_whiteout`)
- `dungeon.html` 외부 대시보드

### 정량 효과

- `engine/matrix_view.py` (1,057 LOC) → 삭제 또는 archive
- `tests/unit/test_dungeon_view.py` 안의 toggle 테스트 4-6개 삭제
- `state.py` 단순화 (`dungeon_mode` 필드 + 관련 분기)

## 영향 받는 항목

- `prototype/src/wet_run/engine/matrix_view.py` — 폐기 또는 archive
- `prototype/src/wet_run/engine/app.py` — `D` 핸들러 제거
- `prototype/src/wet_run/engine/state.py` — `dungeon_mode` 필드 제거
- `prototype/tests/unit/test_dungeon_view.py` — toggle 테스트 클래스 정리

## 관련 결정

- **ADR-0060** (Dungeon Exploration Redesign — NetHack + VFX Overlay, Accepted 2026-06-30): 본 결정의 기반. dungeon view 자체의 채택.
- **ADR-0018** (Combat Animation — 5-Layer VFX): 유지된 VFX 시스템 기반.

## 변경 이력

- 2026-07-10: Accepted (Dungeon-only mode 확정)

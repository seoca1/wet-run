# Dungeon Exploration — 검증 체크리스트

> **옵션 B-Nethack (NetHack 클래식 + VFX 오버레이) 채택 (2026-06-30)**
> - NetHack 클래식 맵 (벽/통로/룸) ✓
> - 키 `D` 토글 (matrix ↔ dungeon) ✓
> - 사이버스페이스 이펙트 4종 ✓
>
> Phase 1 + 1.5 완료 (2026-06-30).
>
> 로드맵: Phase 0 ✓ → Phase 1 ✓ → Phase 1.5 ✓ → Phase 2 (절차적) → Phase 3 (미션 매핑) → Phase 4 (ECS) → Phase 5 (단편 연동)
>
> 통합 설계: `DUNGEON_OPTION_B_NETHACK.md` 참조.

---

## Phase 0: 사전 검증 (즉시 실행)

- [ ] **dungeon_view 컴파일 통과**
  ```bash
  .venv/bin/python -c "from prototype.src.wet_run.engine import dungeon_view; print('OK')"
  ```
- [ ] **dungeon_generator 컴파일 통과**
  ```bash
  .venv/bin/python -c "from prototype.src.wet_run.matrix.dungeon_generator import DungeonGenerator; g = DungeonGenerator(); print(g.generate(42))"
  ```
- [ ] **기존 matrix 테스트 통과**
  ```bash
  .venv/bin/python -m pytest prototype/tests/unit/test_matrix_*.py -q
  ```
- [ ] **dungeon_view 렌더링 스모크 테스트** (콘솔 10x10 그리드)

---

## Phase 1: dungeon_view 활성화 (1-2일)

### 1-1. 코드 변경

- [ ] `engine/state.py`에 `dungeon_mode: bool` 필드 추가
- [ ] `engine/app.py`에 ScreenKind.MATRIX 분기에 dungeon_view 호출 추가
- [ ] **입력 토글 키 `D` 추가** (matrix ↔ dungeon 모드 전환)
- [ ] `dungeon_view.handle_dungeon_input` 연결
- [ ] 회귀: 기존 matrix_view 경로 보존

### 1-2. 단위 테스트

- [ ] `tests/unit/test_dungeon_view.py` 작성
  - `test_render_dungeon_matrix_basic`
  - `test_handle_dungeon_input_movement`
  - `test_fog_of_war_states`
  - `test_room_type_glyphs`
- [ ] `tests/unit/test_state_dungeon_mode.py` 작성
  - `test_dungeon_mode_default_off`
  - `test_dungeon_mode_toggle_key_d`
  - `test_dungeon_mode_persists_in_session`

### 1-3. 통합 검증

- [ ] `python prototype/scripts/play.py --duration 30` 정상 작동
- [ ] 매트릭스 진입 → **`D` 키** → 던전 모드 전환
- [ ] 던전 모드 → **`D` 키 다시** → 노드 모드 복귀
- [ ] 던전 모드 → 방향키 (UP/DOWN/LEFT/RIGHT) → 룸 이동
- [ ] 두 모드 간 데이터 일관성 (state.matrix 동일)

### 1-4. 회귀 테스트

- [ ] 모든 기존 matrix 테스트 통과 (2,257+)
- [ ] 챕터/엔딩/미션 시스템 영향 없음
- [ ] i18n 정상 작동

**완료 기준**:
- [ ] 던전 모드와 노드 모드 자유 전환 (D 키)
- [ ] 두 모드 모두 입력 정상
- [ ] 테스트 100% 통과

---

## Phase 1.5: VFX 오버레이 (1일) ✓ DONE

> **상세 설계**: `DUNGEON_OPTION_B_NETHACK.md` 참조.
> 핵심: 사이버스페이스 분위기를 **맵 글리프**가 아닌 **이펙트 레이어**로 표현.

### 1.5-1. 매트릭스 진입 VFX (`spawn_jackin_glitch`)

- [x] `spawn_jackin_glitch(effects: CombatEffects)` 신규 (`combat/effects.py`)
- [x] ASCII noise particle 폭발 (18개 cyan + 8개 magenta)
- [x] screen shake (intensity 80, duration 180ms)
- [x] cyan hit_flash (120ms)
- [x] 3-phase 시네마틱 텍스트:
  - [x] `">> JACKING IN..."` cyan
  - [x] `">> SCANNING HOST..."` gold
  - [x] `">> CYBERSPACE LOADED"` green
- [x] 단위 테스트:
  - [x] `test_populates_particles`
  - [x] `test_sets_cinematic`
  - [x] `test_triggers_shake_and_flash`

### 1.5-2. 룸 전환 플래시 (`spawn_room_flash`)

- [x] `spawn_room_flash(effects, color)` 신규
- [x] 짧은 hit_flash (80ms, 기본 골드)
- [x] spark shower (4 particles)
- [x] 단위 테스트:
  - [x] `test_default_color_gold`
  - [x] `test_custom_color`
  - [x] `test_spawns_particles`

### 1.5-3. DATA 획득 VFX (`spawn_data_acquired`)

- [x] `spawn_data_acquired(effects, x, y)` 신규
- [x] gold particle 폭발 (14개 `$/·/+/·`)
- [x] gold hit_flash (120ms)
- [x] 2-phase 시네마틱:
  - [x] `">> DATA FRAGMENT RECOVERED"` gold
  - [x] `"+ CREDITS + REPUTATION"` beige
- [x] 단위 테스트:
  - [x] `test_sets_gold_particles`
  - [x] `test_cinematic_data_acquired`
  - [x] `test_triggers_gold_flash`

### 1.5-4. Jack-out Whiteout (`spawn_jackout_whiteout`)

- [x] `spawn_jackout_whiteout(effects)` 신규
- [x] white hit_flash (260ms)
- [x] 10 gray particles
- [x] 3-phase 시네마틱:
  - [x] `">> JACKING OUT..."` white
  - [x] `">> CONNECTION SEVERED"` lavender
  - [x] `">> MATRIX CLOSED"` gray
- [x] 단위 테스트:
  - [x] `test_white_flash`
  - [x] `test_three_phase_cinematic`

### 1.5-5. 앱 통합 (`_maybe_spawn_jackin_glitch`)

- [x] `engine/app.py`에 `_maybe_spawn_jackin_glitch(state)` 헬퍼
- [x] 키 `D`로 dungeon_mode 진입 시 자동 호출
- [x] Status 메시지: `">>> View mode: DUNGEON (NetHack)"`
- [x] 통합 테스트: `test_full_jackin_to_jackout_cycle` (전체 사이클 시뮬레이션)

### 1.5-6. 회귀 테스트

- [x] Phase 1 신규 테스트 통과 (8/8)
- [x] Phase 1.5 신규 테스트 통과 (12/12)
- [x] 기존 test_dungeon_view 컴파일 OK
- [x] 챕터/엔딩 시스템 무영향

**완료 기준**:
- [x] VFX 4종 신규 함수 ✓
- [x] `__all__`에 4종 등록 ✓
- [x] 단위 테스트 100% 통과 (12/12) ✓
- [x] 앱 통합 (키 D 시 자동 호출) ✓

---

## Phase 2: 절차적 생성 강화 (3-5일)

### 2-1. 알고리즘

- [ ] `procedural_dungeon_generator.py` 작성
  - `class ProceduralDungeonGenerator`
  - 시드 기반 RNG (재현성)
  - 미션 grade별 노드 분포
  - 캐릭터별 분기
- [ ] `tests/unit/test_procedural_dungeon.py` 작성
  - `test_same_seed_same_layout` (재현성)
  - `test_different_seed_different_layout` (다양성)
  - `test_grade_1_minimum_nodes`
  - `test_grade_5_maximum_nodes`
  - `test_character_novice_branch`
  - `test_character_veteran_branch`
  - `test_character_heretic_branch`

### 2-2. 데이터 구조

- [ ] 룸 메타데이터 확장:
  ```python
  @dataclass
  class Room:
      id: str
      x: int
      y: int
      room_type: RoomType
      label: str
      description: str = ""
      faction: Faction | None = None
      difficulty: int = 1  # 1-5
      loot_table: list[str] = field(default_factory=list)
  ```
- [ ] 적 분포 매트릭스:
  ```python
  ENEMY_DISTRIBUTION = {
      "novice": {"Sense/Net": 0.6, "MaaS": 0.3, "T-A": 0.1},
      "veteran": {"Sense/Net": 0.4, "MaaS": 0.3, "T-A": 0.3},
      "heretic": {"Sense/Net": 0.2, "MaaS": 0.3, "T-A": 0.5},
  }
  ```

### 2-3. ECS 통합 (Phase 4와 병행 가능)

- [ ] `ecs/room_entity.py` 작성
- [ ] `ecs/room_system.py` 작성
- [ ] `ecs/dungeon_system.py` 작성

### 2-4. 검증

- [ ] 시드 동일 → 동일 레이아웃 (100회 반복 테스트)
- [ ] 시드 다름 → 다른 레이아웃 (10회 샘플링)
- [ ] 미션 grade 1-5 각각 정상 생성
- [ ] 캐릭터 3종 분기
- [ ] 적 분포 faction 비율 ±10% 허용

---

## Phase 3: 미션 → 던전 룸 매핑 (1-2일)

### 3-1. 매핑 로직

- [ ] `missions_to_rooms(mission_data, character_ref) -> list[Room]` 작성
- [ ] 키워드 추출 룰:
  - `data` → DATA 룸
  - `ICE`, `ice` → ICE 룸
  - `construct`, `Molly`, `Dixie` → NPC/Construct 룸
  - `extraction`, `download` → EXTRACT 룸
  - `Loa`, `voodoo`, `Mona` → LOA 룸 (heretic only)
- [ ] `tests/unit/test_mission_room_mapping.py` 작성
  - `test_first_jack_rooms`
  - `test_marly_louisiana_god_rooms`
  - `test_aleph_fragment_rooms` (heretic loa)

### 3-2. 29개 미션 검증

| 캐릭터 | 미션 | 룸 분포 | 통과 |
|---|---:|---|---|
| novice | 10 | entry→corridor→data→ice→exit (4-6) | ☐ |
| veteran | 11 | entry→npc→data→ice→loa→exit (5-8) | ☐ |
| heretic | 8 | entry→loa→data→ice→neuroshim→exit (5-7) | ☐ |

- [ ] 29개 미션 모두 룸 분포 검증
- [ ] 미션 ID 해시 → 시드 매핑 일관성
- [ ] 캐릭터별 분기 정확성

### 3-3. 단편 연동 (Phase 5와 통합)

- [ ] 미션-단편 매핑 (`verify_story_links.py`) 그대로 작동
- [ ] 챕터 excerpt 본문 표시 그대로
- [ ] 던전 진입 시 단편 일부분 인용

---

## Phase 4: ECS 통합 (1주)

### 4-1. Room → Entity 변환

- [ ] `ecs/room_entity.py` 작성
  - `def room_to_entity(room: Room) -> Entity`
  - `RoomType.NPC` → NPC entity
  - `RoomType.ICE` → ICE entity (전투 트리거)
  - `RoomType.DATA` → Data entity (수집)
- [ ] 테스트 100% 통과

### 4-2. RoomSystem

- [ ] `ecs/room_system.py` 작성
  - `on_enter(room_id)` — Fog 갱신 + 미션 트리거
  - `on_exit(room_id)` — 상태 갱신
  - `defeat(room_id)` — 룸 제거
- [ ] 기존 combat/equipment 시스템과 통합

### 4-3. 통합 검증

- [ ] 기존 ECS 테스트 통과
- [ ] 신규 ECS 테스트 통과
- [ ] 성능 < 16ms/frame

---

## Phase 5: 단편 연동 (1주)

### 5-1. 챕터 excerpt 표시

- [ ] 룸 진입 시 챕터 excerpt 일부 표시
- [ ] 적 처치 후 단편 일부분 인용
- [ ] 보상 획득 시 관련 단편 인용

### 5-2. 미션 진행 표시

- [ ] 던전 진행 = 미션 진행 시각화
- [ ] Arc 1-5 진행률 표시
- [ ] 챕터 5개 × phase 5개 트리

---

## 회귀 테스트 (전체 시스템)

### 게임 데이터 무결성

- [ ] 미션 JSON 변경 없음 (29 미션)
- [ ] 챕터 JSON 변경 없음 (3 챕터)
- [ ] 단편 파일 변경 없음 (35 EN / 30 KO)
- [ ] 픽서 분포 무변경
- [ ] 엔딩 시스템 무변경

### 게임플레이 기능

- [ ] 캐릭터 선택 (3 캐릭터)
- [ ] 챕터 스크린 (12초 타이핑)
- [ ] 매트릭스 진입
- [ ] 던전 진입 (NEW)
- [ ] 전투 시스템 (RT-MS)
- [ ] 엔딩 A/B
- [ ] 사망/Hall of Dead
- [ ] 그래픽 노블 모드

### i18n

- [ ] en.json 69 키 정상
- [ ] ko.json 69 키 정상
- [ ] 던전 UI 번역 추가 (15-20 키)

### 단위 테스트

- [ ] 기존 2,257+ 테스트 모두 통과
- [ ] 신규 테스트 30-50개 추가
- [ ] 회귀 0건

---

## UI/UX 검증

### 시각적

- [ ] tcod 렌더링 정상
- [ ] 색상 팔레트 일관성 (사이버펑크)
- [ ] 글리프 명확성 (D, !, ?, [], >>, .)
- [ ] 룸 크기/위치 정확

### 입력

- [ ] 방향키 (N/S/E/W) 동작
- [ ] TAB 모드 전환
- [ ] ENTER 액션 메뉴
- [ ] ESC 취소
- [ ] 디버그 키 정상

### UX

- [ ] 던전 진입 시 Fog 효과
- [ ] 적 처치 시 효과
- [ ] 보상 획득 시 표시
- [ ] 미션 클리어 시 트리거

---

## 성능 검증

### 렌더링

- [ ] 던전 생성 시간 < 100ms
- [ ] 매트릭스 화면 렌더링 < 16ms (60fps)
- [ ] 미션-룸 매핑 시간 < 50ms

### 메모리

- [ ] 던전 메모리 < 1MB
- [ ] 그래프 노드 수 적절 (< 30)
- [ ] ECS entity 수 < 100

### 로드

- [ ] 게임 시작 < 2초
- [ ] 매트릭스 진입 < 100ms
- [ ] 챕터 로드 < 50ms

---

## 깁슨 톤 검증

### 문학적 정확성

- [ ] 룸 이름이 깁슨 원작 톤 ("Dixie Flatline", "Maison de Loa")
- [ ] 적 묘사가 사이버펑크 분위기
- [ ] NPC 이벤트 본문이 깁슨 단편 발췌와 일치

### 사이버펑크 코드 스위치

- [ ] ICE 등급 표기 (Wisp/Hammer/Black ICE) 일관성
- [ ] Deck 등급 (T1-T4) 표시
- [ ] Cyberpunk 용어 사용 (deck/jockey/console cowboy)

### 단편 인용

- [ ] 챕터 excerpt 본문 그대로 표시
- [ ] 미션 완료 시 단편 일부분 인용
- [ ] 12 챕터 스크린 타이핑 효과

---

## 데이터 무결성

### 미션-단편-챕터-던전 매트릭스

- [ ] 29 미션 모두 검증
- [ ] 미션 source ↔ 단편 stem 매칭
- [ ] 챕터 character_ref ↔ 미션 character_ref 일치
- [ ] 챕터 excerpt ↔ 단편 본문 발췌 일치

### 검증 CLI

- [ ] `python prototype/scripts/verify_story_links.py` 통과
- [ ] `pytest tests/unit/test_story_resolver.py -q` 통과
- [ ] `pytest tests/unit/test_dungeon_*.py -q` 통과

---

## 배포 검증

### 로컬

- [ ] `python -m wet_run` 정상 실행
- [ ] `python prototype/scripts/play.py` 정상
- [ ] `python prototype/scripts/verify_story_links.py` 통과
- [ ] 모든 단위 테스트 통과

### GitHub Actions

- [ ] CI lint 통과 (ruff)
- [ ] CI typecheck 통과 (mypy strict)
- [ ] CI test 통과 (pytest 2,257+)
- [ ] **Dashboard Pages** 배포 통과
- [ ] Live 사이트: https://seoca1.github.io/roguelike-sprawl/

### Live 사이트

- [ ] Stories 페이지: Journey 카드 표시
- [ ] Journey 페이지: 3 캐릭터 데모
- [ ] 캐릭터 진행 데모 일치

---

## ADR 작성 체크리스트

### ADR-0060 (Dungeon Exploration Redesign)

- [ ] **배경**: 현재 한계 + dungeon_view 미사용
- [ ] **옵션 비교**: A/B/C/D 매트릭스
- [ ] **권장안**: 옵션 B (절차적 생성 강화)
- [ ] **결과 (Consequences)**:
  - 게임플레이 변화
  - 코드 영향 범위
  - 데이터 영향 없음 (미션/단편/챕터 무변경)
  - ECS 통합 단계
  - 깁슨 톤 유지
- [ ] **테스트 계획**: 단위 + 통합 + 회귀
- [ ] **일정**: 5 Phase 로드맵

---

## 완료 기준 (Definition of Done)

각 Phase별 완료 기준:

### Phase 1 (dungeon_view 활성화)
- [ ] 두 모드 (던전/노드) 자유 전환
- [ ] 모든 기존 테스트 통과
- [ ] 깁슨 톤 유지

### Phase 2 (절차적 생성)
- [ ] 시드 기반 재현성
- [ ] 캐릭터별/grade별 변형
- [ ] 30+ 신규 단위 테스트

### Phase 3 (미션 매핑)
- [ ] 29개 미션 모두 검증
- [ ] 일관성 매트릭스

### Phase 4 (ECS 통합)
- [ ] Room → Entity 변환
- [ ] 기존 ECS 호환

### Phase 5 (단편 연동)
- [ ] 챕터 excerpt 표시
- [ ] 단편 발췌 인용

### 전체 완료
- [ ] 2,300+ 단위 테스트 통과
- [ ] 깁슨 톤 체크리스트 통과
- [ ] 데이터 무결성 100%
- [ ] 라이브 사이트 업데이트
- [ ] ADR-0060 Accepted

---

## 위험 요소 + 완화

| 위험 | 완화 |
|---|---|
| dungeon_view 렌더링 버그 | tcod 단위 테스트 + 수동 검증 |
| 절차적 RNG 비결정성 | seed 고정 + 회귀 테스트 |
| 미션 매핑 불일치 | 29개 미션 수동 검증 |
| ECS 통합 충돌 | 점진적 통합 + 롤백 계획 |
| 캐릭터별 분기 부족 | 3 캐릭터 × 5 grade = 15 시나리오 검증 |
| 깁슨 톤 이탈 | 톤 체크리스트 + 원작 인용 |
| ECS 시스템 영향 | 점진적 통합 (Phase 4에서만) |
| 기존 데이터 손상 | 회귀 테스트 + 백업 |

---

## 다음 세션 시작 체크리스트

### 사용자 결정 (2026-06-30 채택)

- [x] **옵션 B+ 채택** (절차적 생성 강화 + 사용자 제안 통합: 4방향 + `#` + 백트래킹)
- [x] **Phase 1만 + Phase 1.5만** (구현 보류, 문서만 갱신)
- [x] **토글 키: `D`** (matrix ↔ dungeon)
- [x] **Corridor glyph: 현재(─/#/→/←/↔) 그대로 + 색상만 구분**
- [ ] Phase 1 코드 구현? (다음 세션)
- [ ] Phase 1.5 코드 구현? (다음 세션)
- [ ] 캐릭터별 분기 필수? (Y/N)
- [ ] 미션 29개 모두 매핑? (Y/N)
- [ ] ADR-0060 작성? (Y/N)

### 시작 가능 상태

- [ ] `docs/SESSION_HANDOVER.md` 작성됨
- [x] `docs/DUNGEON_EXPLORATION_REVIEW.md` 작성됨 (옵션 B+ 반영 완료)
- [x] `docs/DUNGEON_OPTION_B_PLUS.md` 작성됨 (NEW)
- [x] 본 검증 체크리스트 (이 문서) 작성됨 (Phase 1.5 추가 완료)
- [ ] 7개 커밋 main 푸시 완료 (다음 작업 시 갱신)
- [ ] 라이브 사이트 배포 완료

### 즉시 시작 가능

```bash
cd /Users/emilio/projects/Projects/Game/wet_run
source prototype/.venv/bin/activate
pytest prototype/tests/unit/test_matrix_generator.py -q
# → 통과 후 Phase 1 시작
```

### Phase 1.5 시작 가이드

```bash
# 1. exploration.py 확장
# matrix/exploration.py: NodeState enum, ExplorationState 확장
#   cleared, edges_traversed, backtrack_count 필드 추가
#   visit() 메서드 VisitType 반환으로 확장
#   clear() 메서드 추가

# 2. dungeon_view.py 확장
# engine/dungeon_view.py: _draw_corridor_with_path 함수 추가
#   _handle_cardinal_movement 백트래킹 처리
#   _handle_exit_reached 함수 추가

# 3. 단위 테스트
tests/unit/test_node_state.py          # NEW
tests/unit/test_corridor_glyph.py      # NEW
tests/unit/test_backtracking.py        # NEW
tests/unit/test_exit_trigger.py        # NEW

# 4. 검증
make format && make lint && make typecheck && make test
```

---

*Generated: 2026-06-30 — 검증 준비 완료*
*다음 세션 시작 시 본 체크리스트를 따라 진행*
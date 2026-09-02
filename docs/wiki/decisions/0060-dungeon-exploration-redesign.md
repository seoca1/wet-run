# ADR-0060: Dungeon Exploration Redesign — NetHack + VFX Overlay

**상태**: Draft → Accepted (사용자 결정 2026-06-30)
**날짜**: 2026-06-30
**결정자**: 사용자
**우선순위**: P2 (The Matrix)

## 컨텍스트 (Context)

현재 매트릭스 화면(`engine/matrix_view.py`)은 추상적 노드 그래프(5-7 노드 Surface only)로 렌더링됨. 캐릭터가 매트릭스에서 ICE를 뚫는 게임플레이 본질 — **탐색/획득/전투/레벨업** — 이 추상 그래프 위에 흐릿하게 표현됨.

플레이어가 원하는 것:
- RPG의 직관성 (NetHack 클래식 — 방/통로/벽)
- "이 룸이 무엇인지" 한 눈에 보임
- "이동하기 전 어디로 갈지" 명확함
- 사이버스페이스 분위기 (깁슨 톤) — 그러나 맵 글리프가 아닌 **이펙트**로

추가: 구현되어 있지만 사용되지 않는 `engine/dungeon_view.py` (515 lines, 2024년 작성)는 미사용 코드. `dungeon_generator.py`는 7x5 수동 레이아웃(시드 미사용, 미션 매핑 없음).

## 고려한 옵션

### Option A: dungeon_view 활성화만 (최소 변경)

- **설명**: 기존 `dungeon_view.py` 를 `app.py` 에서 호출. 매트릭스 화면을 NetHack 스타일로 토글. 그래프 데이터(`state.matrix`)는 그대로 사용.
- **장점**:
  - 코드 515 lines 즉시 활용
  - 1-2일 내 완료
  - 데이터/미션 영향 없음
- **단점**:
  - 수동 레이아웃 (다양성 없음)
  - 시드 미사용 (재현성 X)
  - 캐릭터별 분기 없음
  - 미션 매핑 없음

### Option B: 절차적 BSP 미로 생성 (절대 다수 옵션)

- **설명**: `ProceduralDungeonGenerator` 로 시드 기반 BSP 파티션 + Kruskal MST + 캐릭터별 dead-end. 미션 ID 와 시드를 통한 재현성. `missions_to_rooms(mission, character_ref)` 로 미션 29개를 키워드 기반 RoomType 시퀀스로 매핑.
- **장점**:
  - 시드 재현성 (테스트 가능)
  - Grade 1-5 룸 수 (6 → 30 노드)
  - 캐릭터별 dead-end 비율 (novice 0.10 → heretic 0.40)
  - 미션 매핑 자동화 (29개 검증 완료)
  - 5-Level VFX 시스템과 자연 통합
- **단점**:
  - 작업량 (700+ lines)
  - 매트릭스 게임플레이 검증 필요

### Option C: 완전 절차적 (Hades / BSP 표준)

- **설명**: BSP 표준 알고리즘 + 템플릿 풀 + 적 가중치 분포.
- **장점**: 진정한 roguelike 다양성
- **단점**: 1-2주 작업량, 깁슨 원작 톤과 미흡 (다양성이 깁슨 시뮬레이션 손상 가능)

### Option D: 하이브리드 (수동 베이스 + 절차 변형)

- **설명**: 기존 7x5 고정 + 적/보상 변형.
- **장점**: 보수적 변경
- **단점**: 다양성 부족, 매핑 작업 동일

## 추천 (Recommendation)

**Option B (절차적 생성 강화 + VFX 오버레이)** — 사용자 결정과 일치.

이유:
1. **매트릭스 분위기 ≠ 맵 글리프**. 사용자가 명시한 결정: 사이버스페이스 분위기는 VFX 레이어로. 5-Layer VFX 시스템(ADR-0018)이 이미 존재하여 통합 비용 최소.
2. **맵 = 게임플레이 UI**. NetHack 클래식 룸/통로/벽은 41년 검증된 RPG 표준. 학습 곡선 0.
3. **시드 재현성** = 테스트 + 데모 가능. 29 미션 각각 결정적.
4. **캐릭터별 분기** = heretic 의 Loa/black ICE 등 깁슨 톤 차별화.
5. **ECS 후순위**. Phase 4 로 미룸. 멀리 떨어져 있음.

### 사용자 결정 사항

| 항목 | 결정 | 근거 |
|---|---|---|
| **맵 스타일** | NetHack 클래식 (벽/통로/룸) | 사용자 결정 |
| **사이버스페이스** | **이펙트 레이어로 분리** | 사용자 결정 (맵 글리프 X) |
| **맵 최적화 대상** | 탐색 / 획득 / 전투 / 레벨업 | 사용자 결정 |
| **Fog 정책** | 옵션 B (현재 + 인접 + 방문) | NetHack 표준 |
| **룸 종류** | 7종 (Entry/Exit/Data/ICE/NPC/Router/Core) | 기존 유지 |
| **VFX 인프라** | 기존 5-Layer VFX 활용 | 신규 작성 X |
| **이전 옵션 B+ 의 추상화** | **자동 폐기** | 맵 글리프에 추상화 위반 |
| **토글 키** | `D` (matrix ↔ dungeon) | 사용자 결정 |

### 폐기된 옵션 B+

옵션 B+ 는 사용자 제안("4방향 미로 + `#` 영구 루트 + 백트래킹 + 다음 영역 트리거")이었음. 그러나 맵 글리프에 추상화 도입(`NodeState` 4단계, `#` 루트, `←/→/↔` 백트래킹) → 사용자 결정(맵은 게임플레이 UI, 사이버스페이스는 이펙트로 분리)에 반함. 자동 폐기.

## 사용자 결정 (Decision)

[x] **Option B-Nethack 채택** (2026-06-30 사용자 결정, "NetHack classic과 유사한 방식을 추구")
[x] 이전 옵션 B+ 폐기
[x] 코드 구현 (Phase 1+1.5+2+3 완료)
[x] 단위 테스트 74개 PASS

## 결과 (Consequences)

### Phase 1 — dungeon_view 활성화 (✓ DONE)

- `state.dungeon_mode: bool` 필드
- `engine/app.py` 에 키 `D` 토글 + `_maybe_spawn_jackin_glitch(state)` 헬퍼
- `dungeon_view.handle_dungeon_input` 분기 연결
- **테스트 8개 PASS** (test_dungeon_view.py)

### Phase 1.5 — VFX 오버레이 (✓ DONE)

4 spawn 함수 신규 (기존 5-Layer VFX 시스템 확장):
- `spawn_jackin_glitch(effects)` — 매트릭스 진입 글리치 (cyan/magenta particle + shake + 3-phase 시네마틱)
- `spawn_room_flash(effects, color)` — 룸 전환 80ms 플래시
- `spawn_data_acquired(effects, x, y)` — DATA 룸 골드 파티클 + 2-phase 시네마틱
- `spawn_jackout_whiteout(effects)` — EXIT 도달 white-out + 3-phase 시네마틱

**테스트 12개 PASS** (test_combat_vfx.py)

### Phase 2 — 절차적 BSP 미로 (✓ DONE)

- `ProceduralDungeonGenerator` (`matrix/dungeon_generator.py`):
  - BSP partition (재귀, min_leaf_size=2)
  - Kruskal MST (Union-Find, Manhattan 거리)
  - 데드엔드 branches (캐릭터별 비율)
  - 시드 기반 재현성 + `mission_id` offset
  - Grade 1-5 노드 수 (6 → 30)
  - 캐릭터 분기 (novice 0.10 / veteran 0.25 / heretic 0.40 dead-end, faction NONE/SENSE_NET/TA, ICE STANDARD/STANDARD/BLACK)
- `decorate_with_outline(graph, outline, character_ref)` — 미션 outline 을 BSP 결과에 re-tag

**테스트 23개 PASS** (test_procedural_dungeon.py)

### Phase 3 — 미션 → 룸 매핑 (✓ DONE)

- `missions_to_rooms(mission, character_ref)` (`matrix/mission_mapper.py`):
  - 키워드 룰 14종 (data/ice/black ice/construct/dixie/molly/case/loa/voodoo/...)
  - Arc별 target 분포 (Arc 1 → 3-4 middle, Arc 5 → 7-8 middle)
  - 캐릭터 bias (novice 0 extras / veteran 1+1+0 / heretic 2+2+1)
  - 결과: ENTRY → [middle] → EXIT (5-9 룸 시퀀스)
- `mission_to_graph(mission, character_ref, seed)` — bridge to BSP

**테스트 31개 PASS** (test_mission_mapper.py; 미션 29개 모두 검증)

### 데이터 영향

**변경 없음**:
- 미션 JSON (29 미션)
- 챕터 JSON (3 챕터)
- 단편 마크다운 (35 EN / 30 KO)
- 엔딩 시스템
- 픽서 분포
- 게임 데이터 ↔ 데모 스토리 정합성

**신규/수정**:
- `engine/state.py`: `dungeon_mode` 필드
- `engine/app.py`: 키 `D` + dungeon_view 분기
- `engine/dungeon_view.py`: 변경 없음 (이미 NetHack 스타일에 부합)
- `combat/effects.py`: VFX 4종 + `__all__` 갱신
- `matrix/dungeon_generator.py`: BSP + `decorate_with_outline`
- `matrix/mission_mapper.py`: 신규
- `tests/unit/`: test_dungeon_view, test_combat_vfx, test_procedural_dungeon, test_mission_mapper
- `docs/DUNGEON_OPTION_B_NETHACK.md`: 신규
- `docs/DUNGEON_EXPLORATION_REVIEW.md`: 옵션 B+ → 옵션 B-Nethack 갱신
- `docs/DUNGEON_VERIFICATION_CHECKLIST.md`: Phase 1.5 VFX 오버레이 갱신
- `dashboard/dungeon.html`: 신규
- `dashboard/index.html`: 사이드바 카드 + roadmap row

### 깁슨 톤

| 단어 | 사용 |
|---|---|
| 매트릭스 진입 | "JACKING IN..." / "SCANNING HOST..." / "CYBERSPACE LOADED" |
| 데이터 회수 | "DATA FRAGMENT RECOVERED" / "+ CREDITS + REPUTATION" |
| 탈출 | "JACKING OUT..." / "CONNECTION SEVERED" / "MATRIX CLOSED" |
| 룸 라벨 | "Data Vault" / "ICE Barrier" / "Construct" / "Router" |

전부 깁슨 원작에서 차용한 단어 (ice, construct, jack-in/out, cyberspace).

### 미진 항목 (Phase 4-5)

- **Phase 4 (ECS 통합)**: 멀리 떨어져 있음. Room → Entity 변환은 다음 ADR.
- **Phase 5 (단편 연동)**: 선택. 룸 진입 시 챕터 excerpt 인용 + 보상 획득 시 단편 일부분 인용.

### 테스트 커버리지

| 파일 | 테스트 수 |
|---|---:|
| `test_dungeon_view.py` | 8 |
| `test_combat_vfx.py` | 12 |
| `test_procedural_dungeon.py` | 23 |
| `test_mission_mapper.py` | 31 |
| **합계** | **74** |

모두 PASS. ruff + mypy PASS (우리 변경 파일).

## 영향 받는 항목

- `design/systems/hacking.md` — Dungeon UI 단락 추가 가능 (선택)
- `testcases/dungeon.md` — Phase 1+1.5+2+3 모두 PASS
- `docs/DUNGEON_OPTION_B_NETHACK.md` — 상세 설계
- `docs/DUNGEON_EXPLORATION_REVIEW.md` — 옵션 비교
- `docs/DUNGEON_VERIFICATION_CHECKLIST.md` — 검증
- `dashboard/dungeon.html` — 외부 노출

## 관련 결정

- **ADR-0018** (5-Layer VFX) — Phase 1.5 가 활용하는 기반
- **ADR-0020** (Fog of War) — matrix_view 의 Visibility enum. Phase 1.5 에서는 dungeon_view 에 단순화 적용 (옵션 B: 현재+인접+방문)
- **ADR-0062** (ECS 통합, 미작성) — Phase 4 후보

## 변경 이력

- 2026-06-30: Draft 작성 (사용자 결정)
- 2026-06-30: Accepted (Option B-Nethack)
- 2026-06-30: Phase 1+1.5+2+3 구현 완료, 74 tests PASS
- 2026-06-30: 대시보드 갱신 (dungeon.html + index 사이드바)

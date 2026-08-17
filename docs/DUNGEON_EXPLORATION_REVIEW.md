# Dungeon Exploration Review — 2026-06-30 (옵션 B-Nethack)

> **게임플레이 개량 — Roguelike Dungeon 탐색 방식 검토 및 검증 준비**
> **2026-06-30 채택**: 옵션 B-Nethack (NetHack 클래식 + 사이버스페이스 이펙트 오버레이)
> **상세 설계**: `DUNGEON_OPTION_B_NETHACK.md` 참조.

> **2026-06-30 변경**: 옵션 B+ (사용자 제안 통합) 자동 폐기 → 옵션 B-Nethack 채택.
> 옵션 B+ 가 맵 글리프에 사이버스페이스 추상화(NodeState 4단계, `#` 루트, 백트래킹 표기)를 도입한 반면,
> 옵션 B-Nethack는 맵은 게임플레이(탐색/획득/전투/레벨업)에 최적화하고 사이버스페이스 분위기는 이펙트 레이어로 분리.

---

## 1. 현황 분석

### 1-1. 매트릭스 시스템 (현재)

```
MatrixGraph (노드 그래프)
├── generator.py — 절차적 (5-7 노드, Surface only)
├── graph.py — 노드/엣지 자료구조
├── node.py — Node/NodeKind/Faction/IceKind
├── exploration.py — Fog of War (ADR-0020)
├── cyberspace_generator.py — 다중 월드/서버 절차 생성
└── dungeon_generator.py — 7x5 그리드 던전 (수동 레이아웃, 미사용)
```

### 1-2. 현재 화면 렌더링

| 화면 | 모듈 | 줄수 | 사용 |
|---|---|---:|---|
| MatrixView | `engine/matrix_view.py` | 900 | **✓ 사용 중** (`app.py:98`) |
| DungeonView | `engine/dungeon_view.py` | 515 | **✗ 구현만 됨, 미호출** |

**핵심 발견**: `dungeon_view.py`는 구현되어 있지만 **`app.py`에서 호출되지 않음**. 미사용 코드.

### 1-3. 던전 생성기 분석

#### dungeon_generator.py (138 lines) — 현재 구현

```python
class DungeonGenerator:
    """7x5 그리드, 10개 룸, 수동 레이아웃"""
    
    ROOM_TYPES = {ENTRY, EXIT, DATA, ICE, NPC, ROUTER, CORE}
    
    def generate(self, seed, mission_grade=1):
        # 수동 정의:
        # entry(0,2) → corridor(1,2) → npc(2,2) → corridor(3,2) 
        # → data(4,2) → corridor(5,2) → ice(6,2) → exit(6,3)
        # + side_1(1,1), side_2(5,3)
```

**한계**:
- 시드 미사용 (del seed)
- 미션 grade 미사용
- 미션별 분기 없음
- 캐릭터별 분기 없음
- 적/보상/이벤트 룸 구분 없음
- 절차적 생성 아님

#### dungeon_view.py (515 lines) — 렌더링

- 2D 그리드 렌더링 (tcod 기반)
- 룸 글리프 (D=Data, !=ICE, ?=NPC, []=Entry, >>Exit, .=Router)
- Fog of War (Visibility enum: CURRENT/ADJACENT/DISCOVERED/UNKNOWN)
- 카드 단위 입력 (`handle_dungeon_input`)
- 상태 패널, 액션 메뉴 통합

**강점**: 완성도 높음, tcod 통합 완료
**약점**: dungeon_generator 단순함에 의존

### 1-4. 미션 시스템 통합

| 미션 grade | Arc | 노드 분포 (현재) |
|---|---|---|
| 1 (Arc 1) | 5 미션 | 5-7 노드 (surface only) |
| 2 (Arc 2) | 7 미션 | 미정의 |
| 3 (Arc 3) | 3 미션 | 미정의 |
| 4 (Arc 4) | 3 미션 | 미정의 |
| 5 (Arc 5) | 2 미션 | 미정의 |

**핵심 갭**: 미션 29개 vs 던전 노드 5-7개 — 매핑 없음

---

## 2. 옵션 분석

### 옵션 A: dungeon_view 활성화 (최소 변경)

| 항목 | 값 |
|---|---|
| 변경 범위 | `engine/app.py`만 |
| 변경 줄수 | ~20줄 |
| 위험 | 낮음 (기존 코드 100% 활용) |
| 개선 폭 | 낮음 (수동 레이아웃 그대로) |
| ECS 통합 | 부분 (state.matrix만 의존) |
| **소요** | **1~2일** |

**장점**: 빠른 검증 가능, 기존 dungeon_view (515 lines) 즉시 활용
**단점**: 수동 레이아웃, 미션 매핑 없음, 다양성 부족

```python
# app.py 변경 예시
from . import dungeon_view

# MATRIX 화면 분기
elif state.screen is ScreenKind.MATRIX:
    if state.dungeon_mode:  # 설정 토글
        dungeon_view.render_dungeon_matrix(console, t, state, prog_registry, ice_registry)
    else:
        matrix_view.render_matrix(...)
```

### 옵션 B: 절차적 생성 강화 (권장)

| 항목 | 값 |
|---|---|
| 변경 범위 | dungeon_generator, app.py, 매핑 로직 |
| 변경 줄수 | ~150-300줄 |
| 위험 | 중간 (절차적 RNG 디버깅 필요) |
| 개선 폭 | 높음 (다양성 + 매핑) |
| ECS 통합 | 가능 (RoomType → ECS entity 매핑) |
| **소요** | **3~5일** |

**장점**:
- 시드 기반 재현 가능성 (테스트 가능)
- 미션 grade/캐릭터별 변형
- 적/보상 분포 절차화
- 점진적 강화 (기존 시스템 보존)

**단점**:
- 절차적 알고리즘 검증 필요
- 미션 분량(3,236~9,628자) 균형 필요
- 캐릭터별 동적 분기 (3 캐릭터)

```python
class ProceduralDungeonGenerator:
    def generate(self, seed, mission_grade, character_ref, mission_id):
        rng = random.Random(seed)
        layout = self._base_layout(mission_grade)
        rooms = self._populate_rooms(layout, mission_id, character_ref)
        return MatrixGraph(rooms, edges)
```

### 옵션 C: 완전 절차적 (Hades/BSP 스타일)

| 항목 | 값 |
|---|---|
| 변경 범위 | dungeon_generator, dungeon_view, app.py |
| 변경 줄수 | ~400-600줄 |
| 위험 | 높음 (알고리즘 복잡) |
| 개선 폭 | 매우 높음 (BSP, 템플릿, 적 가중치) |
| ECS 통합 | 필요 (Room → ECS entity) |
| **소요** | **1~2주** |

**장점**:
- 진정한 roguelike 다양성 (BSP 기반)
- 매번 다른 레이아웃 (시드 기반)
- Hades/Enter the Gungeon 스타일
- 깁슨 원작의 매트릭스 묘사와 일치 ("the matrix unfolds around you, a maze of data streams")

**단점**:
- 알고리즘 복잡 (BSP 구현)
- 기존 dungeon_view 수정 필요
- 캐릭터별 분기 + 절차적 동시 처리 복잡
- 1~2주 작업량

### 옵션 D: 하이브리드 (수동 + 절차적 변형)

| 항목 | 값 |
|---|---|
| 변경 범위 | dungeon_generator, app.py |
| 변경 줄수 | ~100-200줄 |
| 위험 | 낮음 (수동 베이스 + 절차적 변형) |
| 개선 폭 | 중간 |
| ECS 통합 | 부분 |
| **소요** | **2~3일** |

**구조**:
- 기본 7x5 레이아웃은 수동 유지
- 적/보상만 절차적으로 배치
- 캐릭터별 룸 분포 변형
- 시즌 한정 이벤트 (예: ARC 4에서만 loa 방 출현)

---

## 3. 옵션 비교 매트릭스

| 기준 | A | B | C | D |
|---|:---:|:---:|:---:|:---:|
| 구현 난이도 | 🟢 쉬움 | 🟡 중간 | 🔴 어려움 | 🟡 중간 |
| 작업량 | 1-2일 | 3-5일 | 1-2주 | 2-3일 |
| 다양성 | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 깁슨 톤 충실도 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 기존 시스템 보존 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 미션 매핑 용이성 | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| ECS 통합 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 테스트 가능성 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **권장도** | 2순위 | **1순위** | 3순위 | 4순위 |

---

## 4. 권장안: 옵션 B-Nethack (NetHack 클래식 + VFX 오버레이)

> **사용자 결정** (2026-06-30):
> - **맵 스타일**: NetHack 클래식 (벽/통로/룸 글리프)
> - **사이버스페이스 분위기**: 이펙트 레이어로 분리 (맵 글리프 X)
> - **맵 최적화**: 탐색 / 획득 / 전투 / 레벨업
>
> **상세**: `DUNGEON_OPTION_B_NETHACK.md` 참조.

### 4-1. 로드맵 (Phase 1 + 1.5 완료)

```
[Phase 1]   dungeon_view 활성화 (1일) ✓ DONE
  ├─ state.py dungeon_mode 필드
  ├─ app.py 키 D + 분기
  └─ 테스트 8개 PASS
  ↓
[Phase 1.5] VFX 오버레이 (1일) ✓ DONE
  ├─ combat/effects.py 4종 spawn 함수
  ├─ app.py _maybe_spawn_jackin_glitch 헬퍼
  └─ 테스트 12개 PASS
  ↓
[Phase 2]   절차적 BSP 미로 (3-5일) [다음]
  ├─ dungeon_generator.py 시드/grade/캐릭터 강화
[Phase 3]   미션 → 룸 매핑 (1-2일)
[Phase 4]   ECS 통합 + 보상 시스템 (1주)
[Phase 5]   캐릭터별 동적 분기 + 단편 연동 (1주)
```

### 4-2. Phase 1: dungeon_view 활성화 ✓ DONE

**목표**: NetHack 스타일 2D 룸 그리드를 MATRIX 화면에 표시 + `D` 키 토글

**작업 (완료)**:
1. `engine/state.py`에 `dungeon_mode: bool = False` 필드 추가 ✓
2. `engine/app.py`에 `dungeon_view` import + 키 `D` 토글 ✓
3. `engine/app.py`에 `_maybe_spawn_jackin_glitch(state)` 헬퍼 ✓
4. 단위 테스트 `tests/unit/test_dungeon_view.py` 작성 ✓ (8 PASS)

**검증 (완료)**:
- 매트릭스 화면에서 그리드 표시 확인 ✓
- 입력 핸들링 (방향키) 동작 ✓
- **`D` 키 토글 자유 전환** ✓
- `dungeon_view`은 기존 515 lines 그대로 활용 (이미 NetHack 스타일에 부합)

### 4-3. Phase 2: 절차적 생성

**목표**: 시드 기반 재현 가능한 던전 + 캐릭터별/grade별 변형

```python
class ProceduralDungeonGenerator(DungeonGenerator):
    """시드 기반 절차적 던전 생성."""
    
    def generate(
        self, 
        seed: int,
        mission_grade: int,
        character_ref: str,  # novice/veteran/heretic
        mission_id: str | None = None,
    ) -> MatrixGraph:
        rng = random.Random(seed + hash(mission_id or "") % 1000)
        
        # 1. 레이아웃 템플릿 선택
        layout = self._select_template(mission_grade, character_ref, rng)
        
        # 2. 룸 배치
        rooms = self._place_rooms(layout, mission_id, rng)
        
        # 3. 적 배치 (NPC/ICE)
        enemies = self._populate_enemies(mission_grade, character_ref, rng)
        
        # 4. 보상 배치
        rewards = self._populate_rewards(rooms, mission_id, rng)
        
        # 5. 그래프 반환
        return self._build_graph(rooms, edges)
```

**변형 파라미터**:
- `seed`: 미션 ID 해시 또는 사용자 입력
- `mission_grade`: 1-5 (Arc 1-5)
- `character_ref`: novice/veteran/heretic (시점 캐릭터)
- `faction_bias`: Sense/Net vs Tessier-Ashpool vs Maas

### 4-3a. Phase 1.5: 옵션 B+ 통합 (사용자 제안)

**목표**: 사용자 제안 (4방향 + `#` + 백트래킹 + 다음 영역) 코드 반영.

**작업 1 — 노드 상태 4단계** (`matrix/exploration.py`):
```python
class NodeState(StrEnum):
    UNKNOWN = "?"
    DISCOVERED = "·"
    VISITED = "◆"
    CLEARED = "✓"

@dataclass
class ExplorationState:
    current: str
    discovered: set[str] = field(default_factory=set)
    scanned: set[str] = field(default_factory=set)
    cleared: set[str] = field(default_factory=set)         # NEW
    path: list[str] = field(default_factory=list)
    edges_traversed: set[tuple[str, str]] = field(default_factory=set)  # NEW
    backtrack_count: int = 0                                # NEW
```

**작업 2 — `#` 영구 루트 표시** (`engine/dungeon_view.py`):
- `_draw_corridor_with_path(state, matrix, src, dst, ...)` 신규
- Corridor Glyph 결정: `─` (미통과), `→` (정방향), `←` (백트래킹), `↔` (양방향), `#` (영구)
- **색상으로만 보조 구분** (한글 라벨 X, 애니메이션 X)

**작업 3 — 백트래킹 명시화**:
- `VisitType` enum (FIRST / REVISIT / BACKTRACK)
- `_handle_cardinal_movement` 확장 — 정방향/역방향 구분
- `backtrack_count` 통계

**작업 4 — 다음 영역 트리거**:
- `_handle_exit_reached(state, matrix)` 신규
- `NodeKind.EXIT` 도달 시 `state.exploration.clear(node_id)` + 미션 트리거 + 화면 전환

**단위 테스트**:
- `test_node_state.py` (4단계 전이)
- `test_corridor_glyph.py` (5 종류)
- `test_backtracking.py` (FIRST/REVISIT/BACKTRACK)
- `test_exit_trigger.py` (이벤트 1회 한정)

---

### 4-4. Phase 3: 미션 → 던전 룸 매핑

**목표**: 29개 미션이 자연스럽게 5-15개 룸으로 분해

```python
# missions.json → dungeon rooms 자동 매핑
def mission_to_rooms(mission_data, character_ref) -> list[Room]:
    """미션 synopsis/story에서 키 단어 추출 → 룸 타입 결정."""
    synopsis = mission_data["story"]["synopsis_en"]
    
    rooms = [Room("entry", ENTRY)]
    
    # 키워드 매핑 룰
    if "data" in synopsis.lower():
        rooms.append(Room("data_vault", DATA))
    if "ICE" in synopsis or "ice" in synopsis.lower():
        rooms.append(Room("ice_barrier", ICE))
    if "construct" in synopsis.lower():
        rooms.append(Room("construct_room", NPC))
    
    rooms.append(Room("exit", EXIT))
    return rooms
```

**29개 미션 → 룸 분포**:

| 캐릭터 | 미션 수 | 평균 룸/미션 |
|---|---:|---:|
| novice | 10 | 4-6 |
| veteran | 11 | 5-8 |
| heretic | 8 | 5-7 |

### 4-5. Phase 4: ECS 통합

**목표**: 룸을 ECS entity로 변환, 시스템과 통합

```python
# ecs/room_system.py (신규)
class RoomSystem(ECSSystem):
    """룸 entity 관리."""
    
    def on_enter(self, world, room_id):
        room = world.get_entity(room_id)
        # Fog of War 갱신
        # 미션 트리거
        # NPC 이벤트 시작
```

### 4-6. Phase 5: 단편 연동

**목표**: 던전 진행 중 단편 발췌 표시

```python
# 매트릭스 진입 시 챕터 excerpt 표시
# 적 처치 후 단편 일부분 표시
# 보상 획득 시 관련 단편 인용
```

---

## 5. 검증 체크리스트

### 5-1. Phase 1 (즉시 검증 가능)

- [ ] dungeon_view.py 515 lines 컴파일 통과
- [ ] app.py에 dungeon_view 분기 추가
- [ ] dungeon_mode 토글 추가
- [ ] 매트릭스 진입 시 던전 모드/노드 모드 선택 가능
- [ ] 던전 모드: 7x5 그리드 표시
- [ ] 노드 모드 (현재): 그래프 표시
- [ ] 두 모드 간 전환 자유
- [ ] 입력 핸들링 (방향키) 일관성
- [ ] Fog of War 정상 동작
- [ ] 단위 테스트 100% 통과

### 5-2. Phase 2 (절차적 생성)

- [ ] 시드 동일 → 동일 레이아웃 (재현성)
- [ ] 시드 다름 → 다른 레이아웃 (다양성)
- [ ] 미션 grade 1-5 각각 정상 생성
- [ ] 캐릭터별 분기 (3 캐릭터)
- [ ] 적 배치 분포 (Sense/Net, T-A, Maas, 야쿠자)
- [ ] 보상 배치 (data_fragment, ice_shard 등)
- [ ] 단위 테스트 100% 통과

### 5-3. 회귀 테스트 (전체)

- [ ] 기존 미션 29개 모두 정상 작동
- [ ] 챕터 스크린 표시 정상
- [ ] 엔딩 A/B 분기 정상
- [ ] 사망/Hall of Dead 정상
- [ ] 그래픽 노블 모드 정상
- [ ] i18n (en/ko) 정상
- [ ] 2,257+ 단위 테스트 모두 통과

### 5-4. 데이터 일관성

- [ ] 미션 JSON 변경 없음
- [ ] 챕터 JSON 변경 없음 (표시 본문 그대로)
- [ ] 단편 파일 변경 없음
- [ ] 게임 데이터 ↔ 데모 스토리 정합성 유지

### 5-5. UI/UX

- [ ] tcod 렌더링 정상
- [ ] 색상 팔레트 일관성
- [ ] 글리프 명확성 (D=Data, !=ICE)
- [ ] 입력 응답성 (입력 후 1프레임 내 반영)

### 5-6. 성능

- [ ] 던전 생성 시간 < 100ms
- [ ] 매트릭스 화면 렌더링 < 16ms (60fps)
- [ ] 미션-룸 매핑 시간 < 50ms

### 5-7. 깁슨 톤

- [ ] 룸 이름/설명이 깁슨 원작 톤
- [ ] 적/이벤트 묘사가 사이버펑크 분위기
- [ ] 12 챕터 excerpt 본문 그대로

---

## 6. 리스크 분석

### 6-1. 기술 리스크

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| dungeon_view 렌더링 버그 | 중간 | 중간 | tcod 단위 테스트 |
| 절차적 RNG 비결정성 | 낮음 | 낮음 | seed 고정 + 회귀 테스트 |
| 미션 매핑 불일치 | 중간 | 중간 | 미션별 수동 검증 |
| ECS 통합 충돌 | 중간 | 높음 | 점진적 통합 (Phase 4) |

### 6-2. 디자인 리스크

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| 캐릭터별 분기 부족 | 중간 | 중간 | 캐릭터별 시드 패턴 |
| 깁슨 원작 톤 이탈 | 낮음 | 높음 | 톤 체크리스트 |
| 절차적 다양성 부족 | 중간 | 낮음 | 템플릿 풀 확장 |

### 6-3. 일정 리스크

| 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|
| Phase 1 지연 | 낮음 | 낮음 | dungeon_view 활용 |
| Phase 2-3 복잡도 폭증 | 중간 | 중간 | 점진적 통합 |
| ECS 통합 지연 | 중간 | 중간 | 별도 Phase 분리 |

---

## 7. 결정 사항 (2026-06-30 갱신 — 옵션 B-Nethack)

### 7-1. 사용자 결정 (옵션 B-Nethack 채택)

| 항목 | 결정 |
|---|---|
| **권장 옵션** | **B-Nethack (NetHack 클래식 + 사이버스페이스 이펙트 오버레이)** ✓ |
| Phase 1 + 1.5 | **즉시 구현 완료** ✓ |
| **토글 키** | **`D`** (matrix ↔ dungeon 모드 전환) |
| **맵 스타일** | NetHack 클래식 (벽/통로/룸 — 기존 dungeon_view 그대로) |
| **사이버스페이스** | 맵 글리프에 추상화 X, **이펙트 레이어 4종** |
| **Fog 정책** | 옵션 B (현재 + 인접 + 방문) |
| **룸 종류** | 기존 7종 유지 (Entry/Exit/Data/ICE/NPC/Router/Core) |
| 캐릭터별 분기? | 미정 (Phase 2 결정) |
| 미션 29개 모두 매핑? | 미정 (Phase 3 결정) |

### 7-2. 폐기 사항 (2026-06-30)

| 이전 제안 | 폐기 사유 |
|---|---|
| 옵션 B+ (NodeState 4단계) | 맵 글리프에 사이버스페이스 추상화 |
| `#` 영구 루트 표시 | 트레일 시각화 (게임플레이 UI 왜곡) |
| `←`/`→`/`↔` 백트래킹 | 메타 진행 데이터 표기 |
| `VisitType` enum, `PathEdge` 자료구조 | 추상화 과잉 |

### 7-3. 문서 산출물

- [x] `DUNGEON_EXPLORATION_REVIEW.md` — 옵션 B-Nethack 권장안 (이 문서)
- [x] `DUNGEON_OPTION_B_NETHACK.md` — 상세 설계 (옵션 B+ 폐기 노트 포함)
- [x] `DUNGEON_VERIFICATION_CHECKLIST.md` — Phase 1.5 VFX 오버레이

### 7-4. ADR 작성 (다음 세션)

`decisions/0060-dungeon-exploration-redesign.md`:
- 배경: dungeon_view 미사용, 매트릭스 단순 노드 그래프 한계
- 옵션: A/B-Nethack/C/D 비교
- 권장안: **옵션 B-Nethack**
- 결과: 게임플레이 변화 (맵 = 게임플레이 UI, VFX = 사이버스페이스), 데이터 영향 없음
- Phase 1 + 1.5 완료: dungeon_mode 토글 + VFX 4종

---

## 8. 참고 게임 (벤치마킹)

| 게임 | 던전 생성 | ECS | Roguelike | 시점 |
|---|---|---|---|---|
| **Hades** | 수동 + 절차 변형 | 있음 | O | 아이소메트릭 |
| **Enter the Gungeon** | 완전 절차 (BSP) | O | O | 2D 그리드 |
| **Slay the Spire** | 절차적 맵 (노드 그래프) | O | O | 2D |
| **NetHack** | 절차 (Brogue-like) | 일부 | O | 1인칭 |
| **Caves of Qud** | 자유 절차 | O | O | 2D |
| **Risk of Rain 2** | 절차적 스테이지 | O | O | 3D |
| **Brogue** | BSP 던전 | O | O | ASCII |
| **현재 Sprawl** | dungeon_view (수동 7x5) | ECS-lite | O | 2D ASCII |

**권장**: Hades 모델 (수동 베이스 + 절차 변형) — 깁슨 미학과 일치

---

## 9. 코드 위치 (참조)

| 항목 | 경로 |
|---|---|
| 던전 생성기 | `prototype/src/wet_run/matrix/dungeon_generator.py` |
| 던전 뷰 (미사용) | `prototype/src/wet_run/engine/dungeon_view.py` |
| 매트릭스 뷰 (현재) | `prototype/src/wet_run/engine/matrix_view.py` |
| 게임 루프 | `prototype/src/wet_run/engine/app.py` |
| 미션 데이터 | `prototype/data/missions/missions.json` |
| 챕터 데이터 | `prototype/data/story/chapters/{case,sil,kas}.json` |
| ECS | `prototype/src/wet_run/ecs/` |
| 정규화 헬퍼 | `prototype/src/wet_run/data/story_resolver.py` |
| 검증 CLI | `prototype/scripts/verify_story_links.py` |

---

## 10. 다음 세션 즉시 시작 가이드 (Phase 2)

Phase 1 + 1.5 완료. 다음 세션은 Phase 2 (절차적 BSP 미로).

```bash
# 1. 환경 활성화
cd /Users/emilio/projects/Projects/Game/wet_run/prototype

# 2. 현재 상태 확인 (신규 VFX 테스트)
.venv/bin/python -m pytest tests/unit/test_dungeon_view.py tests/unit/test_combat_vfx.py -v
# → 20 tests PASS

# 3. dungeon_mode 토글 검증
.venv/bin/python -c "
from src.wet_run.engine.state import AppState, ScreenKind
s = AppState()
print('dungeon_mode default:', s.dungeon_mode)  # False
"

# 4. Phase 2: 절차적 미로 생성
# - matrix/dungeon_generator.py 시드/grade/캐릭터 강화
# - BSP (Binary Space Partitioning) 알고리즘 도입
# - 단위 테스트 30개 추가

# 5. ADR 작성
#    decisions/0060-dungeon-exploration-redesign.md
#    (권장안: 옵션 B-Nethack, Phase 1+1.5 완료 반영)

# 6. 검증
make format && make lint && make typecheck && make test
```

---

*Generated: 2026-06-30 — 옵션 B-Nethack 채택, Phase 1+1.5 완료*
*다음 세션: Phase 2 (절차적 BSP 미로) 시작*
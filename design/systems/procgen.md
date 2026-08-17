# System: Procedural Generation (절차적 생성)

> **관련**: [hacking.md](./hacking.md) (매트릭스), [exploration.md](./exploration.md) (탐험), [difficulty-rating.md](./difficulty-rating.md) (PPL/ZDR)
> **구현**: `../../prototype/src/wet_run/matrix/dungeon_generator.py`
> **ADR**: 0005 (cyberspace 표현), 0060 (NetHack BSP 던전 리디자인), 0061 (Novel Hook Dispatch)

## 목적

매 런마다 **재현 가능하지만 다양한** 사이버스페이스 그래프 생성.
같은 미션이라도 시드마다 다른 배치 → replayability + 테스트 가능성.

## 3-tier 절차적 생성

### Tier 1: RoomGenerator (구버전, 7x5 hand-crafted)

기존 호환용 — 테스트가 이 동작에 의존.

- 7x5 고정 그리드
- Mission ID 별 hand-crafted layout
- 시드 미사용

### Tier 2: ProceduralDungeonGenerator (ADR-0060, NetHack style)

BSP (Binary Space Partitioning) + Kruskal MST + 시드 기반:

```
알고리즘:
1. seed → RNG 초기화
2. BSP: 그리드를 재귀 분할 (min_leaf_size=2)
3. Kruskal MST: Union-Find 로 leaf 간 corridor 연결
4. dead-end branches: 캐릭터별 비율로 가지치기
5. mission outline 으로 방 타입 decorate
```

#### 시드 입력

```python
def generate(seed: int, mission_id: str, character_ref: str) -> MatrixGraph:
    rng = random.Random(seed)
    generator = ProceduralDungeonGenerator(rng, mission_id, character_ref, grade=...)
    return generator.build()
```

#### 등급별 사이즈 (GRID_BY_GRADE)

| Grade | 그리드 | 룸 수 |
|---|---|---|
| 1 (novice) | 7x5 | 10-12 |
| 2 | 9x6 | 14-18 |
| 3 | 11x7 | 19-24 |
| 4 | 13x8 | 25-30 |
| 5 (master) | 15x10 | 35-42 |

#### 캐릭터별 dead-end 비율

| 캐릭터 | dead-end 비율 | 효과 |
|---|---:|---|
| Novice | 0.10 | 단순한 직선 미로 |
| Veteran | 0.25 | 중간 분기 |
| Heretic | 0.40 | Loa-style chaotic paths |

### Tier 3: Mission → Room mapping (ADR-0060 Phase 3)

`missions_to_rooms(mission, character_ref)` 가 키워드 룰로 미션 → 방 시퀀스:

```
14 keyword rules:
  "data" → DATA
  "ice", "watchdog" → ICE
  "black", "construct" → BLACK_ICE / CONSTRUCT
  "construct", "dixie" → CONSTRUCT
  "loa", "voodoo" → LOA
  "neuromancer", "wintermute" → BOSS
  ...
```

결과: ENTRY → [middle rooms] → EXIT (5-9 룸 시퀀스).

## 시드 재현성

같은 입력 (seed + mission_id + character_ref + grade) → 같은 출력.
29 미션 × 3 캐릭터 × 5 등급 = **435 layouts** deterministic.

```python
>>> g1 = generate(seed=42, mission_id="first_jack", character_ref="novice", grade=1)
>>> g2 = generate(seed=42, mission_id="first_jack", character_ref="novice", grade=1)
>>> g1 == g2  # True
```

## Cyberspace 월드 (서버 브라우저)

`cyberspace/world.py` 의 WorldMap 은 별도 절차적 시스템:
- World: 2개 (chiba, night_city)
- Sector: World 당 2-3개
- Server: Sector 당 1-2개
- 총 6 servers

자키는 서버 브라우저에서 world/sector/server 를 선택 → 각 서버가 독립적인
매트릭스 그래프 생성.

## 매트릭스 vs 던전 모드

`D` 키로 매트릭스 ↔ 던전 토글 (ADR-0060):

- **매트릭스** (기본): 추상 노드 그래프, 시베리안 글리치 vibe
- **던전** (토글): NetHack 방/통로, 5-Layer VFX 오버레이

두 모드 **같은 MatrixGraph** 를 공유 — 데이터는 단일, 표현만 다름.

## Novel Hook Dispatch (ADR-0061)

미션의 `story.source` 필드가 단편 stem 을 참조하면,
절차적 생성 후 소설 hook 이 자동 dispatch:

```python
mission_to_graph(mission, character_ref, seed)
    ↓
ProcDungeonGenerator.build()
    ↓
HookContext 생성 (matrix, mission, character)
    ↓
HookAction 실행 (NARRATIVE/EXCERPT/EVENT/COMBAT/ITEM/CINEMATIC)
    ↓
AppState 에 결과 반영
```

29 미션 × 6 hook kinds = 다채로운 런 변형.

## 재현성 vs 다양성 트레이드오프

| 요소 | 재현성 | 다양성 |
|---|---|---|
| 시드 | ✅ 동일 | — |
| 캐릭터 | — | ✅ dead-end 비율 |
| 등급 | — | ✅ 그리드 크기 |
| 미션 | — | ✅ room 시퀀스 |
| ICE | — | ✅ 종류 / 위치 |
| Construct | — | ✅ 등장 여부 |

깁슨 톤 — "같은 자리에 같은 미로를 두 번 밟지 않는다" 는 모티프는
**다양성** 쪽에 가깝지만, **테스트와 리플레이 검증** 은 **재현성** 으로.

## 구현 위치

| 요소 | 파일 |
|---|---|
| ProceduralDungeonGenerator | `matrix/dungeon_generator.py:430-650` |
| BSP partition | `matrix/dungeon_generator.py:520-580` |
| Kruskal MST | `matrix/dungeon_generator.py:580-630` |
| Mission → Room mapping | `matrix/mission_mapper.py` |
| Decorate with outline | `matrix/dungeon_generator.py:560-610` |
| World / Sector / Server | `cyberspace/world.py` |
| Novel Hook dispatch | `novel/{catalog,manifest,hooks,dispatcher}.py` |

## 테스트

- `test_procedural_dungeon.py` (23 tests): BSP / Kruskal / dead-end
- `test_mission_mapper.py` (59 tests): 29 미션 × 키워드 룰 매핑
- `test_matrix_generator.py` (회귀): 시드 재현성

## 미래 작업 (Phase 6+)

- **Phase 4 ECS 통합**: Room → Entity 변환
- **동적 ICE 배치**: dead-end 끝에 강제 보스 등장 (Loa scenario)
- **Multi-floor 서버**: 깊이별 다른 layout
- **Hand-crafted 데이븐 미션**: 미션 ID 에 따른 시드 무시
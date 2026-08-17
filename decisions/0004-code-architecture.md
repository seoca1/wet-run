# ADR-0004: 코드 아키텍처

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0

## 컨텍스트

게임 코드의 아키텍처 패턴을 결정해야 한다. 결정은 다음에 영향을 미친다:
- 코드 구조와 모듈화
- 데이터 주도 디자인의 용이성
- 절차적 생성 / 콘텐츠 추가의 용이성
- Pillar 4 (The Build) — 메타 진행 시스템과의 정합

## 고려한 옵션

### Option 1: ECS (Entity Component System) — 추천

- **설명**: Entity = ID, Component = 데이터, System = 로직. Bevy / Unity DOTS 스타일.
- **장점**:
  - 데이터 주도 — ICE, 프로그램, 데크 모두 Component
  - 절차적 생성과 자연스러움
  - 메타 진행 데이터 추가 쉬움
  - 모듈화 우수
- **단점**:
  - 러닝 커브
  - Python에서 직접 ECS 구현 시 추가 작업
  - 단순한 게임에는 over-engineering
- **Pillar 정합**:
  - P1 (The Run): 시스템 추가/제거가 ECS와 잘 맞음
  - P4 (The Build): 메타 unlock이 Component 추가로 표현

### Option 2: OOP + 상속

- **설명**: 클래스와 상속. 전통적 게임 아키텍처.
- **장점**:
  - 단순
  - 익숙
  - AI 에이전트가 가장 잘 다룸 (Python에서)
- **단점**:
  - 데이터 주도 디자인 어려움
  - 절차적 생성과 맞지 않음 (상속 트리 복잡)
  - 메타 진행 추가 시 클래스 변경
- **Pillar 정합**:
  - P1: 가능
  - P4: 메타 진행 추가 어려움

### Option 3: 데이터 주도 (JSON/YAML + 단순 로직)

- **설명**: 게임 데이터를 JSON/YAML로 정의, 로직은 단순한 함수들.
- **장점**:
  - 콘텐츠 추가가 데이터 파일 추가로 가능
  - 절차적 생성이 데이터 + 룰
  - 1인 개발에 적합
  - AI 에이전트가 가장 잘 다룸
- **단점**:
  - 복잡한 시스템 표현 어려움
  - 컴파일 타임 체크 약함
  - 타입 안정성 부족
- **Pillar 정합**:
  - P1: 좋음 (데이터 + 룰)
  - P4: 좋음 (unlock 데이터 추가)

### Option 4: 함수형 / Composition

- **설명**: 순수 함수, composition. Rust / Haskell 스타일.
- **장점**:
  - 모듈화 우수
  - 테스트 용이
- **단점**:
  - 게임 아키텍처에 어색
  - ECS와 유사하나, 게임에는 OOP/ECS가 더 자연스러움

### Option 5: 하이브리드 (ECS-lite + 데이터 주도)

- **설명**: 정식 ECS는 아니지만, Entity = dict, Component = key, System = 함수.
- **장점**:
  - Python에 자연스러움
  - ECS의 장점 + Python의 단순성
  - AI 에이전트가 잘 다룸
- **단점**:
  - ECS의 타입 안정성 부족
  - 큰 프로젝트에서 성능 이슈

## 추천

**Option 5: 하이브리드 (ECS-lite + 데이터 주도)** (Python 사용 시)
**Option 1: ECS** (Bevy/Godot 사용 시)

근거:
- Python (libtcod) 사용 시: Option 5
- 절차적 생성과 메타 진행 모두 자연스러움
- 콘텐츠 추가는 JSON/YAML로
- 시스템은 순수 함수

## 사용자 결정

[x] **Option 5: 하이브리드 (ECS-lite + 데이터 주도)** (2026-06-17)

## 결과 (Consequences)

### 아키텍처

**Entity** = `dict` (or `dataclass`):
```python
Entity = {
    "id": str,
    "name": str,
    "type": "player" | "ice" | "construct" | "node",
    "components": {
        "position": (x, y),
        "stats": {"hp": 10, "ap": 5, "bw": 4, "pw": 10},
        "programs": ["goliath", "wisp"],
        "ice_type": None,
        ...
    }
}
```

**System** = `function(entity, world) -> world`:
```python
def system_attack(attacker, target, world):
    if attacker.components["stats"]["ap"] >= 2:
        target.components["stats"]["hp"] -= damage(attacker, target)
        attacker.components["stats"]["ap"] -= 2
    return world
```

**Data** = `JSON` files:
```json
// data/programs.json
{
  "goliath": {
    "name": "Goliath",
    "type": "attack",
    "ap_cost": 3,
    "damage": 8,
    "bw_cost": 2,
    "description": "Heavy attack. Slow."
  }
}
```

### 데이터 포맷
- **JSON**: 단순 데이터 (decks, programs, ICE types, jobs, factions)
- **YAML**: 사람이 자주 편집하는 데이터 (의뢰 템플릿, dialogue)
- **TOML**: 설정 (config.toml)

### 디렉토리 (Phase 4에서 확정)
```
prototype/
├── wet_run/
│   ├── engine/         # tcod / main loop
│   ├── ecs/            # Entity, World, System decorators
│   ├── matrix/         # 노드 그래프, 항해
│   ├── combat/         # 전투 시스템 (AP)
│   ├── programs/       # 프로그램 로직
│   ├── jobs/           # 의뢰
│   ├── data/           # 정적 데이터
│   └── ui/
├── data/               # JSON / YAML 데이터
├── tests/
└── pyproject.toml
```

### Pillar 정합
- P1: 시스템 추가/제거가 자연스러움
- P4 (The Build): 메타 unlock이 데이터 추가

### 강제되는 결정
- ADR-0001 (Python) — Python에 자연스러운 패턴
- ADR-0006 (unlock만) — 데이터 추가만으로 unlock

### 향후 결정
- World / Entity의 정확한 API
- System decorator / registry 패턴
- 데이터 검증 (JSON Schema)

## 영향 받는 항목

- `design/systems/*.md` — 모든 시스템 명세가 ECS-lite 패턴 사용
- `prototype/` 디렉토리 구조 (위 참조)
- 데이터 정의 (JSON/YAML)

## 관련 결정

- ADR-0001 (Accepted), ADR-0006 (Accepted)

## 변경 이력

- 2026-06-17: Draft 작성
- 2026-06-17: Accepted (Option 5: ECS-lite + 데이터 주도)

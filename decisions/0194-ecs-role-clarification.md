# ADR-0194: ECS-lite 역할 명시화 — 프로덕션은 OOP/dataclass, ECS는 실험/테스트 도구

**상태**: Draft
**날짜**: 2026-08-19
**결정자**: 사용자
**우선순위**: P3 (The Build, 아키텍처 명료화)
**관련**: ADR-0004 (코드 아키텍처), `docs/ARCHITECTURE.md` §14 (ECS vs OOP 매트릭스)

## 컨텍스트 (Context)

2026-08-19 [`docs/ARCHITECTURE.md` §14](../docs/ARCHITECTURE.md) 분석 결과:

| 항목 | 측정값 |
|---|---|
| `ecs/` 모듈 총 LOC | 488 (Entity/World/room_entity/dungeon_system/__init__) |
| 프로덕션 코드에서 `wet_run.ecs` import | **0건** |
| ECS 사용처 | `tests/unit/test_ecs.py` (103 LOC) + `test_dungeon_ecs.py` (402 LOC) + `scripts/play_ecs_dungeon.py` + `scripts/play_arc_bsp.py` |
| ECS-lite 프로덕션 적용률 | ~488 / 36,316 LOC ≈ **1.3%** |
| 엔진/전투 시스템 | `engine/state.py` (AppState, 394 LOC) + `combat/*` (13,604 LOC) — 전부 `@dataclass` 또는 Python class |
| 매트릭스 시스템 | `matrix/graph.py` (MatrixGraph/Node/Edge) — 전부 `@dataclass` |

ADR-0004 (2026-06-17 Accepted) 는 **Option 5: 하이브리드 (ECS-lite + 데이터 주도)** 를 선택했지만:

> **Entity** = `dict` (or `dataclass`)
> **System** = `function(entity, world) -> world`
> **Data** = `JSON` files

ADR-0004 의도와 현실 사이에 큰 괴리 존재. 신규 진입자가 `ecs/` 모듈을 보고 "프로덕션에서 ECS를 어떻게 확장하나?" 라고 질문할 때 명확한 답변이 부재.

### 사이드 이펙트

1. **명료성 부족**: ADR-0004 가 ECS-lite를 "전면 사용" 으로 오해 → 신규 시스템 추가 시 dataclass 대신 ECS-lite를 선택해야 하는지 혼란
2. **테스트 격차**: ECS는 505 LOC의 테스트가 있으나 실제 게임 �타임과 무관 — 테스트 투자 대비 ROI 불명확
3. **문서-코드 불일치**: §14.1 ADR-0004 의도 vs §14.4 시스템별 매트릭스가 다른 이야기 전달
4. **Naming Collision**: `World` 클래스 두 곳에 존재 — `ecs/world.py` (ECS 컨테이너) vs `cyberspace/world.py` (Matrix 계층)

### 검증

```bash
# ECS 사용처 검색
$ grep -rln "wet_run.ecs" prototype/src/wet_run/ --include="*.py"
# (결과 없음 — 프로덕션 사용 0건)

$ grep -rln "wet_run.ecs" prototype/ --include="*.py"
tests/unit/test_ecs.py
tests/unit/test_dungeon_ecs.py
tests/unit/test_phase36_small_content_polish.py
tests/unit/test_phase39_small_content_polish.py
scripts/play_ecs_dungeon.py
scripts/play_arc_bsp.py
# 6 파일 모두 test/ 또는 scripts/
```

## 고려한 옵션

### Option 1: ECS 전면 통합 (대규모 리팩터)

- **설명**: `engine/state.py`, `combat/*`, `matrix/*`, `missions/*`의 모든 dataclass를 ECS Entity/Component로 변환.
- **장점**:
  - ADR-0004 의도 실현
  - 미래 확장성 (메타 unlock이 Component 추가로 표현)
  - 데이터 주도 디자인 일관성
- **단점**:
  - 36,000+ LOC 재작성 위험 (회귀 테스트 부담)
  - 게임 동작 변경 가능성
  - python-tcod 통합 시 절차적 패턴과의 충돌
  - Pillar 정합 불확실 (Pillar 3 무게 유지를 위해 ECS의 유연성이 오히려 방해될 수 있음)
- **Pillar 정합**:
  - P1 (The Run): 큰 영향 (런 구조 재작성)
  - P2 (The Matrix): 영향 (matrix 노드 모델 재작성)
  - P3 (The Flatline): 중립
  - P4 (The Build): ✅ (메타 unlock 데이터 추가 용이)
  - P5 (The Style): 중립

### Option 2: ECS 폐기 (모듈 삭제)

- **설명**: `ecs/` 디렉토리와 관련 테스트/데모를 모두 삭제. ADR-0004를 "데이터 주도만 적용, ECS 부분 폐기" 로 Superseded.
- **장점**:
  - 코드베이스 명확성 (불필요한 모듈 제거)
  - Naming Collision 자동 해소
  - 신규 진입자 혼란 제거
- **단점**:
  - 488 LOC + 505 LOC 테스트 + 2 데모 삭제 (투자 손실)
  - ADR-0004 Superseded by 결정 필요
  - "ECS-lite 실험 가능성" 차단 (향후 확장 시 재구현)
- **Pillar 정합**:
  - 모든 Pillar에 영향 없음 (게임 동작 변경 없음)

### Option 3: ECS-lite 역할 명시화 (하이브리드 문서화) — **추천**

- **설명**: ADR-0004의 "ECS-lite + 데이터 주도" 결정을 **두 부분으로 분리**:
  - **데이터 주도 부분** (전체 적용): 모든 콘텐츠 = JSON, i18n 포함 (ADR-0010과 일치)
  - **ECS-lite 부분** (선택적): `ecs/` 모듈은 **실험/테스트 도구**로 격하. 프로덕션 게임 로직은 OOP/dataclass 유지
- **장점**:
  - 현실 반영 (1.3% 적용률)
  - ADR-0004의 데이터 주도 부분은 유지 (이미 잘 작동)
  - ECS-lite의 투자 보존 (테스트/데모는 유지)
  - 신규 시스템 추가 시 명확한 가이드 (대부분 → OOP, ECS는 dungeon/room 도메인에서만 선택적)
- **단점**:
  - ADR-0004의 의도(ECS 전면)를 축소 해석 — "Superseded" 라벨 필요 가능
  - 일관성 문제: "데이터는 JSON, 로직은 OOP" 의 명확한 사유 설명 필요
- **Pillar 정합**:
  - P1 (The Run): 중립 (런 구조 변경 없음)
  - P2 (The Matrix): 중립
  - P3 (The Flatline): 중립
  - P4 (The Build): ✅ (데이터 주도 원칙 유지)
  - P5 (The Style): 중립

### Option 4: ECS를 dungeon/room 도메인 한정 (점진적 통합)

- **설명**: `ecs/` 모듈을 dungeon/room 관련 코드(`matrix/`, `engine/dungeon_view.py`)에서만 통합. 나머지는 OOP 유지.
- **장점**:
  - ECS의 도메인 적합성 활용 (방 → Entity 매핑은 자연스러움)
  - 점진적 통합 (Option 1의 위험 완화)
  - ADR-0004 의도와 가장 일치
- **단점**:
  - "왜 dungeon만 ECS?" 라는 일관성 질문 발생
  - 추가 구현 작업 (matrix 노드 → Entity 변환 활성화, hooks wiring)
  - dungeon 외 시스템 추가 시 매번 "ECS vs OOP" 결정 필요
- **Pillar 정합**:
  - P1 (The Run): 영향 (런 시작 시 ECS World 생성/소멸 필요)
  - P2 (The Matrix): ✅ (matrix 노드 = ECS Entity 자연스러움)
  - P3 (The Flatline): 중립
  - P4 (The Build): ✅
  - P5 (The Style): 중립

## 추천 (Recommendation)

**Option 3: ECS-lite 역할 명시화** — ADR-0004의 의도를 분리하여 **데이터 주도는 전면 유지, ECS-lite는 실험 도구로 격하**.

### 이유

1. **현실 반영**: 1.3% 적용률이 보여주듯 프로덕션 코드는 이미 OOP/dataclass 위주로 안정화됨. ADR과 현실의 괴리를 해소하는 것이 가장 low-risk
2. **데이터 주도 원칙 보존**: ADR-0010 (i18n + Content Pipeline) 의 핵심인 "모든 콘텐츠는 JSON/YAML" 원칙은 이미 작동 중 — 이 부분은 변경 불필요
3. **ECS 모듈 투자 보존**: 488 LOC 정의 + 505 LOC 테스트 + 2 데모는 향후 확장 가능성을 위한 자산. 삭제하지 않고 "선택적 도구"로 유지
4. **명확한 가이드**: 신규 시스템 추가 시 "기본 = OOP/dataclass, ECS는 dungeon/room 도메인에서만 선택적" 의 단순한 규칙
5. **Naming Collision 자동 해결**: ECS 격하 + 별칭(`EcsWorld`) 도입으로 `World` 혼란 해소

### 권장 가이드 (신규 시스템 추가 시)

```python
# 기본: OOP / dataclass
@dataclass
class NewSystem:
    id: str
    # ...

# 선택: ECS-lite (dungeon/room 도메인 한정)
from wet_run.ecs import Entity, World
def new_entity() -> Entity:
    return Entity(id="new", kind="new", ...)
```

## 사용자 결정 요청

다음 중 선택 또는 다른 옵션 제시 부탁:

- [ ] **Option 1** (ECS 전면 통합) — 36,000+ LOC 재작성 위험
- [ ] **Option 2** (ECS 폐기) — 488 LOC + 505 LOC 테스트 삭제
- [x] **Option 3 (Hybrid, 추천)** — ADR-0004 분리, ECS = 실험 도구
- [ ] **Option 4** (dungeon 도메인 한정) — 점진적 통합
- [ ] **기타**: ___
- [ ] **Defer** (다음 단계로 미룸)

## 결과 (Consequences) — 결정 후 작성

## 영향 받는 항목

- `docs/ARCHITECTURE.md` §14 — ECS vs OOP 매트릭스 섹션이 본 ADR 결정 반영하도록 업데이트
- `AGENTS.md` §6 "Accepted 결정 반영" — ECS-lite 사용 규칙 추가
- `prototype/src/wet_run/ecs/__init__.py` — 격하 결정 시 docstring 업데이트 (선택적 도구 명시)
- `decisions/README.md` — ADR-0194 인덱스 추가

## 관련 결정

- **ADR-0004** (Accepted, 2026-06-17): 코드 아키텍처 — ECS-lite + 데이터 주도
- **ADR-0010** (Accepted, 2026-06-17): i18n + Content Pipeline — 데이터 주도 (전면 적용 중)
- **ADR-0060** (Accepted, 2026-06-30): Dungeon Exploration Redesign — `DungeonSystem` ECS 통합 시도 (그러나 실제 프로덕션 미사용)

## 향후 결정

- 본 ADR 결정 후 `World` naming collision 해결 (별칭 도입 또는 rename)
- `docs/ARCHITECTURE.md` §14 ADR 링크 추가
- ECS 모듈의 향후 위치 (유지 / 격하 / 폐기)

## 변경 이력

- 2026-08-19: Draft 작성 (ARCHITECTURE.md §14 분석 기반)

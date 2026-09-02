# ADR-0206: Mission Registry Wiring (ADR-0166/0167 Deferred Follow-up)

**상태**: **Accepted** — 2026-08-26 (this session; "all" carry-over batch, content authoring deferred)
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: "all" carry-over batch)
**우선순위**: P1 (ADR-0166/0167 Consequences 해결, 보드 wiring 활성화)
**관련**: ADR-0166 (Phase 6 Arc), ADR-0167 (Mission Expansion), `combat/arc6.py`, `combat/mission_expansion.py`, `missions/board.py`, `missions/mission.py`, `matrix/node.py`

## 컨텍스트 (Context)

ADR-0166 + ADR-0167 의 Consequences "잔존 작업 deferred" — registry의 미션 데이터는 존재하지만 보드 wiring 미완료. "all" carry-over batch로 후속 진행.

### 발견된 근본 원인 (조사 결과):

1. **`missions.json`은 완전** — 10개 mission (Arc6 4 + Expansion 6) 모두 존재
2. **`Mission.__post_init__`의 `arc in 1..5` 검증 위반** — Arc6 mission은 `arc=6`이지만 검증이 거부 → `_parse_mission()` None 반환
3. **`ZoneDepth` enum에 `AFTERMATH` 부재** — Arc6 mission의 `zone="aftermath"`가 enum 변환 실패
4. **registry의 추가 fields** (`description`, `story_intro`, `primary_ice`)는 `missions.json` schema에 없어서 보드 wiring 시 무시됨

### Wiring 결함 → JobBoard에 194 missions만 로드 (Arc6 4 + Expansion 6 = 15개 손실)

## 고려한 옵션

### Option 1: 4-component fix (ZoneDepth + arc + enrich + JobBoard) — **채택**

- **설명**:
  - `ZoneDepth.AFTERMATH = "aftermath"` 추가
  - `Mission.__post_init__` arc 검증 `1..5` → `1..6` 확장
  - `enrich_arc6_mission()`, `enrich_expansion_mission()`, `enrich_mission_registry()` 신규
  - `JobBoard.load()` 에 enrichment 통합 (load 시 registry fields merge)
- **장점**:
  - 완전한 wiring — 모든 mission이 JobBoard에 로드
  - Registry의 추가 fields (description, story_intro, primary_ice) 보존
  - 209 missions 모두 playable
- **단점**:
  - 4개 파일 수정 (5개)
  - `arc 1..6` 검증 강화 필요 (낮은 위험)
  - sys.path 설정 필요 (테스트 환경)

### Option 2: 미션 data 부분만 (registry 사용 안함)

- **설명**: missions.json의 기존 data만 사용, registry fields 무시
- **장점**: 단순함
- **단점**: Registry의 보강 정보 손실, ADR-0166/0167의 의도 미달성

### Option 3: registry를 jobs.json에 별도 추가

- **설명**: registry fields를 별도 JSON 파일로 export
- **장점**: data separation
- **단점**: 복잡, board UX에서 lookup 비용, ADR 의도 미달성

## 추천 (Recommendation)

**Option 1 채택**.

### 이유

1. **ADR-0166/0167 Consequences 완료**: registry의 보강 정보 보존
2. **JobBoard wiring 결함 해결**: 194 → 209 missions
3. **Future 확장성**: `enrich_*` 함수가 새로운 registry 추가 시 보일러플레이트

## 사용자 결정 요청

- [x] Option 1 (4-component fix) — **채택**
- [ ] Option 2 (data만)
- [ ] Option 3 (별도 JSON)

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: 4-component wiring.

### 구현 산출물

| 파일 | 변경 | 역할 |
|---|---|---|
| `matrix/node.py` | +AFTERMATH | ZoneDepth enum 확장 (Arc6 missions) |
| `missions/mission.py` | arc 1..5 → 1..6 | Mission validation 확장 (Arc6 arc=6) |
| `combat/arc6.py` | +enrich_arc6_mission() | Registry fields → mission dict merge |
| `combat/mission_expansion.py` | +enrich_expansion_mission() | Registry fields → mission dict merge |
| `combat/__init__.py` | +enrich_mission_registry() | 통합 wiring function |
| `missions/board.py` | JobBoard.load() | enrichment 통합 (registry fields merge at load) |
| `tests/unit/test_mission_wiring.py` (new) | 13 tests | wiring 검증 |

### 검증 결과

- `pytest tests/unit/test_mission_wiring.py`: ✅ **13 passed**
- `pytest tests/unit/test_mission_expansion.py`: ✅ 12 passed
- 전체 테스트 suite: 4045 passed, 364 skipped, 1 xfailed, 1 pre-existing failure (interrogate 모듈 부재, 본 변경과 무관)
- JobBoard 미션 수: **194 → 209** (Arc6 4 + Expansion 6 = 15개 손실 → wiring 후 복구)

### Registry Fields Merged (per mission):

| Field | Source | Purpose |
|---|---|---|
| `registry_description` | Arc6/Expansion dataclass | UI/board display |
| `registry_story_intro` | Arc6/Expansion dataclass | Story presentation |
| `registry_primary_ice` | Arc6/Expansion tuple | ICE narrative |
| `registry_source` | "ADR-0166" / "ADR-0167" | Provenance tracking |

### Non-destructive merge:

`enrich_*` 함수는 `setdefault()` 사용 → 기존 `missions.json` field 보존 (override 안 함).

### Accepted 직후 적용

- 본 ADR `decisions/README.md` 인덱스에 추가
- `log.md` 본 결정 기록

## 영향 받는 항목

- `prototype/src/wet_run/matrix/node.py` (+1 enum)
- `prototype/src/wet_run/missions/mission.py` (1 line)
- `prototype/src/wet_run/combat/arc6.py` (+enrich function)
- `prototype/src/wet_run/combat/mission_expansion.py` (+enrich function, +bugfix)
- `prototype/src/wet_run/combat/__init__.py` (+enrich function)
- `prototype/src/wet_run/missions/board.py` (JobBoard.load)
- `prototype/tests/unit/test_mission_wiring.py` (new, 13 tests)

## 관련 결정

- **ADR-0166** (Accepted): Phase 6 Arc - Aftermath (deferred — 본 ADR로 wiring 완료)
- **ADR-0167** (Accepted): Mission Expansion (deferred — 본 ADR로 wiring 완료)

## 향후 결정

- Registry fields UI 활용 (board display)
- Notion mirror 업데이트
- 더 많은 mission 등록 시 enrich_* 함수 패턴 활용

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 1)** — 본 세션. 4-component wiring (ZoneDepth.AFTERMATH + arc 1..6 + enrich_* + JobBoard 통합). 209 missions 모두 JobBoard 로드 확인.
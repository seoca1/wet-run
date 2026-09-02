# TC-EXP: Exploration (Fog of War / 탐험)

> **관련**: `../../decisions/0020-fog-of-war-exploration.md`, `../../design/systems/exploration.md`

Light Fog of War (현재 + 인접) — 매트릭스 노드 그래프의 부분 가시 시나리오.

## TC-EXP-001: 초기 상태 — Entry만 보임 (P0, Active)

**Given**: 자키가 매트릭스에 진입
**When**: ExplorationState 초기화
**Then**: `current` = entry_id
**Then**: `discovered` = {entry_id}
**Then**: `scanned` = {}
**Then**: `path` = [entry_id]
**Then**: 모든 인접 노드 = `ADJACENT`
**Then**: 모든 비-인접 노드 = `UNKNOWN`

## TC-EXP-002: 노드 방문 (P0, Active)

**Given**: ExplorationState, current = E, discovered = {E}
**When**: visit(R)
**Then**: `current` = R
**Then**: `discovered` = {E, R}
**Then**: `path` = [E, R]
**Then**: E → visibility = DISCOVERED
**Then**: R → visibility = CURRENT

## TC-EXP-003: 인접 노드는 외곽선 박스 (P0, Active)

**Given**: current = E, 인접 R 존재
**When**: 매트릭스 렌더링
**Then**: R은 `? ICE ?` 형태 (kind만)
**Then**: R의 ZDR / status는 **숨김**
**Then**: R의 color는 회색 (highlight 아님)

## TC-EXP-004: 알 수 없는 노드는 `?` (P0, Active)

**Given**: current = E, 비-인접 X 존재
**When**: 매트릭스 렌더링
**Then**: X는 `?` placeholder
**Then**: X의 color는 어두운 회색 `(64, 64, 64)`

## TC-EXP-005: Probe — 인접 노드 ZDR 공개 (P0, Active)

**Given**: current = E, 인접 R (ICE, ZDR 7)
**When**: Probe 사용
**Then**: R → `scanned` 추가
**Then**: R의 ZDR / status (TOUGH 등) **공개**
**Then**: Probe 사용 시 1 AP 차감 (combat 통합)

## TC-EXP-006: 미니맵 (P0, Active)

**Given**: ExplorationState, discovered = {E, R}, unknown = {D, I, X}
**When**: 매트릭스 렌더링
**Then**: 미니맵 (top-right) 표시
**Then**: discovered 노드는 `●`
**Then**: unknown 노드는 `?`
**Then**: exit 노드는 `X` (항상)
**Then**: 현재 노드는 `●` 강조

## TC-EXP-007: Breadcrumb (P0, Active)

**Given**: path = [E, R, D]
**When**: 매트릭스 렌더링
**Then**: 하단에 `Path: E → R → D` 표시
**Then**: 회색 (덜 강조)

## TC-EXP-008: 연결선 — 안개 (P1, Active)

**Given**: current = E, 인접 R은 adjacent, 비-인접 X는 unknown
**When**: 매트릭스 렌더링
**Then**: E ↔ R 연결선 보임
**Then**: E ↔ X 연결선 **숨김**
**Then**: R ↔ X (X가 unknown) 숨김

## TC-EXP-009: Exit 노드는 항상 보임 (P1, Active)

**Given**: 매트릭스에 exit 노드 존재
**When**: 자키가 어디에 있든
**Then**: exit은 **항상 visible** (UNKNOWN 안 됨)
**Then**: ZDR은 진입 전 비공개

## TC-EXP-010: 깊이 들어갈수록 알람 증가 (P1, Active) — *향후 결정*

**Given**: 알람 LOW, current = E
**When**: 깊이 3+ 노드 진입
**Then**: 알람 MEDIUM
**Then**: trace 위험 +1

## Phase 5+ 자동화 (예정)

- `tests/unit/test_exploration.py` — ExplorationState 단위 테스트
  - visit / probe / visibility
  - discovered / scanned / path
  - is_visible, is_scanned
  - 미니맵 / breadcrumb 데이터
- `tests/integration/test_matrix_fog.py` — 매트릭스 + fog 통합
- 회귀 테스트: 매 fog 변경 시

# ADR-0212: grade 기반 ICE encounter 배선 (Option 2)

**상태**: Draft
**날짜**: 2026-09-24
**결정자**: 사용자
**우선순위**: P1 (밸런스 정확성 — ADR-0211 후속)
**관련**:
- [ADR-0211](./0211-ice-grade-scaling.md) — Option 1 (harness HP 스케일링) 구현 완료. 본 ADR 은 그 후속.
- [ADR-0199](./0199-wetrun-web-mvp.md) — web 코드베이스 기준
- [ADR-0012](./0012-difficulty-rating.md) — PPL & ZDR
- [ADR-0190](./0190-boss-expansion-f4-integration.md) — boss profile

## 컨텍스트 (Context)

ADR-0211 Option 1 로 harness 는 `hp_base + hp_per_grade * (grade - 1)` 로 HP 를 산출하게 됐지만, 곡선은 여전히 비단조다 (50/80/43/86/100/100%). 원인은 HP 가 아니라 **encounter 정체성**:

| 첫 ICE 노드 | armor | G1 HP | G6 HP | opening deck 승률 |
| --- | --- | --- | --- | --- |
| `watchdog` (일반 `ice` 방) | 1 | 50 | 100 | 100% |
| `wintermute` (보스 `exit` 방) | 8 | 260 | 410 | 0% |

`web/src/core/dungeon.ts:223-231` 이 `ice` 방은 `watchdog`, 보스 방은 `wintermute` 를 하드코딩하고, 그 배치를 `grade` 가 전혀 구동하지 않는다. `generateProceduralMatrix(missionGrade, …)` 는 grade 를 받지만 `dungeonToMatrix(graph)` 에 전달하지 않으며, `Matrix` 타입에도 grade 가 없다. 결과적으로 **게임에서도 grade 가 ICE 난이도를 구동하지 않는다** — 같은 ICE, 같은 HP.

## 고려한 옵션

### Option A: grade → ICE tier 배선 (권장)

- **설명**:
  1. `Matrix` 에 `grade: number` 추가.
  2. `dungeonToMatrix(graph, grade)` — ICE 방의 ICE id 를 **grade 에 맞는 tier 로 선택** (예: `tier = clamp(grade, 1, 5)` 인 ICE 중 결정적 1개). 보스 방은 현행 `wintermute` 유지 (별도 boss 설계는 ADR-0190 범위).
  3. `resolveMatrixRoster` 가 `node.iceHp[i] ?? hp_base + hp_per_grade * (grade - 1)` 로 HP 산출 (ADR-0211 의 `iceHpForGrade` 재사용). `node.iceHp = []` 로 두어 데이터가 구동.
- **권장 grade→ICE 매핑 (초안 — 조정 대상)**:

| grade | ICE id | tier | armor | hp_base | hp/g | G HP (grade=ceiling) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `watchdog` | 1 | 1 | 50 | 10 | 50 |
| 2 | `spider` | 1 | 0 | 40 | 8 | 48 |
| 3 | `black` | 3 | 5 | 200 | 40 | 280 |
| 4 | `goliath` | 3 | 8 | 150 | 30 | 240 |
| 5 | `neuromancer` | 5 | 9 | 320 | 60 | 560 |
| 6 | `neuromancer` | 5 | 9 | 320 | 60 | 620 |

- **장점**: 게임과 harness 가 같은 난이도 모델 공유. `tier` / `hp_base` / `hp_per_grade` / `armor` 가 실제로 사용됨. grade 가 오를수록 단조 증가하는 난이도 곡선 확보.
- **단점 / 리스크**:
  - 실제 게임 난이도가 바뀐다 — playtest 필요.
  - 매핑(어떤 ICE 를 어떤 grade 에)은 디자인 결정 → 튜닝 여지.
  - `armor` 는 아직 전투에서 무시됨 (`state_actions.ts:572` `defenderDefenseBonus: 0`) — 본 ADR 범위 밖, 별건 후속.
  - opening deck (~100-160 dmg) 이 grade 3+ 에서 급격히 약해질 수 있음 → deck/damage 재검토 동반 필요.

### Option B: harness 만 encounter 선택 정정 (게임 불변)

- **설명**: harness 가 보스 노드를 건너뛰고 첫 비보스 ICE 노드만 측정.
- **단점**: 게임은 여전히 grade-blind 이고, 비보스는 전부 `watchdog` 라 grade 신호가 없다 (전 등급 100% flat). 근본 문제 미해결.

### Option C: Defer

- 현행 유지. 곡선 비단조 + grade-blind encounter 잔존.

## 추천 (Recommendation)

**Option A 를 단계적으로 적용**. 단, 매핑 표는 디자인 결정이므로 사용자 승인 후 확정.

1. `Matrix.grade` + `resolveMatrixRoster` HP 산출 (배선) — 순수 배선, 되돌리기 쉬움.
2. grade→ICE 매핑 표 (위 초안) — 승인/조정.
3. `npm run balance -- --runs 500` 으로 곡선 확인 (단조성 목표).
4. 파생 후속: `state_actions.ts:572` armor 반영, opening deck damage vs ICE HP/armor 재검토.

## 사용자 결정 (Decision)

- [ ] Option A (권장)
- [ ] Option A 단, 매핑 표 수정: ___
- [ ] Option B
- [ ] Option C (Defer)
- [ ] 기타: ___

## 결과 (Consequences)

(결정 후 작성)

## Implementation Status (2026-09-24)

**Status**: ❌ Not started

**Evidence**:
- `web/src/core/dungeon.ts:223-231, 261` — `ice` 방 `watchdog` / 보스 방 `wintermute` 하드코딩
- `web/src/core/matrix.ts:80-88` — `generateProceduralMatrix(missionGrade, …)` 가 `dungeonToMatrix(graph)` 에 grade 미전달
- `web/src/core/types.ts:273-277` — `Matrix` 에 grade 없음
- `web/src/core/matrix.ts:122` — `resolveMatrixRoster` 가 `node.iceHp[i] ?? entry.hp`
- `web/src/core/state_actions.ts:572` — `defenderDefenseBonus: 0` (armor 미반영, 별건)

**Notes**: ADR-0211 Option 1 완료 후 실측으로 확인된 후속. 실제 게임 난이도 변경을 포함하므로 사용자 승인 필요.

## 영향 받는 항목

- `web/src/core/dungeon.ts`, `web/src/core/matrix.ts`, `web/src/core/types.ts` (배선)
- `web/scripts/balance_sim.ts` (이미 `iceHpForGrade` 보유)
- `web/tests/` (dungeon/matrix/balance 회귀)
- `docs/design/systems/difficulty-rating.md` (PPL/ZDR 명세)

## 변경 이력

- 2026-09-24: Draft 작성 (ADR-0211 Option 1 구현 중 확인된 진단 정정에 근거).

# ADR-0311: 고유 카드는 고른다 — 전리품 화면의 무료 하위 단계

**상태**: Accepted
**날짜**: 2026-11-12
**결정자**: 사용자 ("판단이 필요할 때는 jev ai 도움 받아서 계속 진행해봐") — 후보 선정은 Jev
**우선순위**: P1 (성장 · 선택)

## 컨텍스트 (Context)

ADR-0309 는 g6 성장 축을 **도달 가능하게** 만들었지만 전달 방식이 "발견"이었다.
tier-6 승리 시 그 싸움의 제안이 지목한 **첫 고유**를 자동으로 넣었기 때문에,
플레이어는 ADR-0303 이 설계한 **세 가지 답**(장갑·몸·타격)을 한 번도 보지 못했다.

ADR-0309 의 열린 질문 (a) 가 정확히 이것이다. 세 답을 보여주고 하나를 고르게 하면
"내 덱이 못 하는 것"을 고르는 결정이 되살아난다. 문제는 **어디서 고르게 하느냐**였다.

## 고려한 옵션

### 선택 1 — 화면을 어디에 둘 것인가 (Jev Choice)

| 후보 | Jev p | 비고 |
|---|---:|---|
| `dedicated_screen_after_win` | 0.94 | 승리 직후 별도 화면 (confidence 0.91) |
| `extra_loot_slot_cycling` | 0.06 | 9번 칸 순환 — ADR-0299 의 8칸 한계 |
| `defer_keep_auto_grant` | 0.00 | 현상 유지 |

### 선택 2 — 같은 플레이어 경험의 두 구현 (Jev Choice)

| 후보 | Jev p | 비고 |
|---|---:|---|
| `loot_subphase` | **1.00** | `runPhase` 는 `loot` 유지, 전리품 화면이 먼저 고유 3행을 렌더 |
| `new_run_phase_screen` | 0.00 | 새 phase 는 렌더 게이트·입력·저장·e2e 에 모두 배선해야 함 |

**근거**: 이 프로젝트는 화면 등록 누락으로 소프트락을 세 번 겪었다(ADR-0273 그래픽 노블
동결 · ADR-0275 스텁 목록 반전 · ADR-0283 prep 유휴 알람 회귀). 플레이어가 보는 것이
같다면 **이미 입력·e2e 가 붙은 전리품 화면**을 쓰는 쪽이 위험이 낮다.

### 선택 3 — 런당 1장 제한 (Jev Noul)

- Jev **p = 0.49** — 판단 불가. 아래 이유로 **1장 제한**을 택했다.
  - ADR-0303 의 전제: "하나를 고르는 것은 **내 덱이 못 하는 것**을 고르는 일"이다.
    셋을 다 모으면 그 결정이 체크리스트가 된다.
  - 소유 카드가 있으면 제안이 비므로, **재로드 후 중복 지급**도 구조적으로 막힌다.

## 사용자 결정 (Decision)

- [x] **전리품 화면의 무료 하위 단계** (`runPhase` 는 `loot` 그대로)
- [x] **런당 1장** (Jev p=0.49 는 애매 — 설계 전제로 결정)
- [x] 전리품 stop 은 **소비하지 않는다** (ADR-0309 의 원칙 유지)

## 결과 (Consequences)

- `uniqueChoicesFor(state)` (`card_reward.ts`) — tier-6 · 비종결 · 미보유 · 미해결일 때
  **세 고유를 고정 순서로** 돌려준다. 난수 0, 순수 함수.
- `applyLootAction` (`state_actions_phases.ts`) — 고유가 남아 있으면 `select_program 1-3`
  은 **고유 선택**(무료, 드로우 파일 맨 위 + inventory), `confirm` 은 **건너뛰기**.
  `cardRewardTaken` 을 건드리지 않으므로 stop 은 그대로 남는다.
- `renderLootScreen(..., mode: "unique")` — 같은 패널, 제목 `UNIQUE PROGRAM`,
  헤더 `CHOOSE ONE`, 푸터 `1-3: unique · ENTER: skip`.
- `rewardAffordances` — 터치 게임패드 행이 고유 3개를 그대로 노출(거짓 어포던스 없음).
- 저장: `SaveSlot.uniquePickDone?` (선택 필드, version 1 유지). 이후 세이브는 재선택 불가.
- **측정(per-cell, 64시드)**: **100 / 97.1 / 75.9 / 51.4 / 26.9 / 32.3** — ADR-0309 의
  자동 지급과 **완전히 동일**(62/192). 즉 선택은 **전력 중립**이고 목표도 그대로 통과
  (최대 이탈 4.1pp).
- 테스트: `web/tests/adr0311_unique_pick_screen.test.ts` (6건) + ADR-0300 폭 가드에
  `unique pick` 케이스 추가. 전체 **208 files / 4190 tests**.

## 열린 질문

- **(a) 획득 연출.** 고유 선택은 메시지 한 줄로만 알린다. ADR-0261/0262 의 성장 연출
  (소리·멈춤·표시)은 전리품 카드 경로에만 붙어 있다.
- **(b) 선택의 정보.** 세 답의 차이(장갑/몸/타격)는 효과 태그 한 줄로만 보인다.
  카드 비교 정보(ADR-0282 (c))와 같은 계열의 후속.
- **(c) 1장 제한 재검토.** Jev p=0.49. 긴 런에서 두 번째 답을 주는 쪽이 재미있다면
  그때는 "셋을 모으면 무엇이 좋은가"를 먼저 설계해야 한다.
- **(d) 하네스는 선택을 모델링하지 않는다.** 봇은 항상 `ghost_key`(점수 최고)를 고른다.
  측정은 "선택이 비용이 없다"는 뜻이지 "선택이 가치 없다"는 뜻이 아니다.

## Implementation Status (2026-11-12)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/state/card_reward.ts` — `uniqueChoicesFor` (tier 게이트 · 1장 제한 · 결정적)
- `web/src/core/state/state_actions_phases.ts` — 전리품 하위 단계(선택/건너뛰기)
- `web/src/renderer/ending.ts` · `run_screen.ts` — `mode: "unique"` 패널
- `web/src/core/combat/program_affordance.ts` — 터치 행
- `web/tests/adr0311_unique_pick_screen.test.ts` — 6 tests
- `docs/design/adr-0311/pick-is-power-neutral.txt` — 측정

**Notes**: 게임 규칙 변경은 이 ADR 하나. ADR-0309 의 **결정 의도**(성장 축을 도달 가능하게)는
유지되고 **전달 방식만** 대체된다. 교전당 곡선 무영향. e2e: progression·run_end_save **5/5**,
그리고 **소크 99런(33미션 × 3정책) — completed 67 / failed 32 · frozen 0/99 · noEndInSteps 0 ·
meanSteps 22.3**(직전 22.2).

## 영향 받는 항목

- ADR-0309 — 전달 방식 대체(결정 의도 불변)
- ADR-0303 — 세 답의 선택이 화면에 나타난다
- `web/scripts/play_policy.ts` — 하네스가 하위 단계를 처리
- ADR-0300 폭 가드 — `unique pick` 케이스

## 관련 결정

- ADR-0310 — 계측기(per-cell)로 측정
- ADR-0309 — 전리품 밖 지급(전신)
- ADR-0303 — 세 가지 답
- ADR-0275 · ADR-0273 · ADR-0283 — 화면 등록 소프트락의 선례

## 변경 이력

- 2026-11-12: Draft 작성 — Jev Choice 2회 + Noul 1회
- 2026-11-12: Accepted (전리품 하위 단계 + 런당 1장)

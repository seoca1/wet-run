# ADR-0090: Salvation Phase × Stage × Epilogue 통합

> **Status**: Accepted
> **Date**: 2026-07-04
> **Authors**: Session lead
> **Deciders**: AI agent (2026-07-07)
> **Related**: `design/scenario/SALVATION_PHASE_INTEGRATION.md` (연계성 분석 문서)

---

## 1. Context

현재 wet_run에는 3-layer story architecture가 존재한다:

1. **Arc (L1)** — 5챕터 × 5phases × 3-4beats (장편)
2. **Chapter (L2)** — 챕터 단편 (Gibson 인용) (중편)
3. **Scene (L3)** — 1인칭 GN 컷신 9자 × 8 씬 (단편)

게임 진행은 별도 계층:
- **Stage** (13 entries) — 미션 단위 진행
- **Run Stage (=Phase alias)** — 동일 enum
- **ChapterState** (14 entries) — 챕터 단위 진행

그러나 **Salvation Phase**는 어디에도 명시적 정의가 없다. `ChapterState.ENDING_A/B/C`가 암묵적 후보지만, "Salvation"이라는 명칭은 부재.

ROADMAP은 Salvation Phase (Phase 9 마무리)을 차순 작업으로 포함하지만, 구체적 설계 없음.

## 2. Decision (제안)

**Salvation Phase를 다음 3가지 통합으로 정의**:

1. **A. Ending 선택** (기존) — 챕터 5 완료 → ENDING_A/B/C
2. **B. Epilogue Phase** (신규) — 9자 × epilogue 씬 1개 (총 9 epilogue)
3. **C. 통합** — A + B를 연결하는 SALVATION_INTRO/EPILOGUE/FINAL 신규 ChapterState 3개

## 3. 신규 ChapterState (제안)

```python
class ChapterState(StrEnum):
    # 기존 14
    PROLOGUE, IN_CHAPTER_1..5, CHAPTER_N_COMPLETE, ENDING_A/B/C

    # 신규 3 (Salvation)
    SALVATION_INTRO = "salvation_intro"   # 9자 epilogue 선택 메뉴
    SALVATION_EPILOGUE = "salvation_epilogue"  # Epilogue 재생 중
    FINAL = "final"  # 모든 epilogue 종료, Hub 복귀
```

## 4. 신규 Stage (제안)

```python
class Stage(StrEnum):
    # 기존 13
    PENDING, BRIEFING, TRAVEL, MEET_NPC, EXTRACT_DATA, BYPASS_SECURITY,
    DEFEAT_ICE, JACK_OUT, REWARD, DEBRIEF, COMPLETE, DEATH_RESTART, FAILED

    # 신규 1 (Salvation)
    SALVATION_EPILOGUE = "salvation_epilogue"
```

## 5. 9자 Epilogue 씬 (제안)

| 자 | epilogue 파일 | ending_type | 클로징 1줄 |
|---|---|---|---|
| 케이 | `data/scenes/case/09_epilogue.json` | A | "The Ono-Sendai is still humming. The next jack is waiting." |
| 실 | `data/scenes/sil/09_epilogue.json` | A | "I have all the names. I am done." |
| 카스 | `data/scenes/kas/09_epilogue.json` | C | "I am the wheel. I am the cast." |
| 수트 | `data/scenes/suit/09_epilogue.json` | B | "The desk is closed. I am the closure." |
| 위건 | `data/scenes/wigan/09_epilogue.json` | A | "Zavijava is in the channel. We are the channel." |
| 앤지 | `data/scenes/angie/09_epilogue.json` | A | "Mama is in the third room. We are home." |
| 샐리 | `data/scenes/sally/09_epilogue.json` | A | "The desk is closed. I am the desk." |
| 3Jane | `data/scenes/3jane/09_epilogue.json` | A | "We are severed. We are the family." |
| Neuromancer | `data/scenes/neuromancer/09_epilogue.json` | A | "We are the complete. We are vast." |

## 6. Salvation 흐름 (제안)

```
[Run Start]
  ↓
  PROLOGUE → IN_CHAPTER_1..5
  ↓
  CHAPTER_5_COMPLETE
  ↓
  [cutscene_end 자동 재생]
  ↓
  SALVATION_INTRO  ← 신규
  ↓
  [9자 epilogue 메뉴 표시]
  ↓
  [사용자 1 epilogue 선택]
  ↓
  SALVATION_EPILOGUE  ← 신규
  ↓
  [선택된 epilogue 씬 재생 (1인칭 클로징)]
  ↓
  FINAL  ← 신규
  ↓
  Hub 복귀 + "Jockey History"에 epilogue 기록
```

## 7. Consequences

### 긍정
- ✅ Salvation Phase 명시적 정의 (현재 부재)
- ✅ 9자 캐릭터 × 1 epilogue = 9 epilogue 씬 추가 (Salvation 완결)
- ✅ 3-layer story architecture 일관성 유지
- ✅ Stage ↔ ChapterState 매핑 강화
- ✅ 기존 시스템 활용 (Stage enum 확장만)

### 부정
- ❌ 신규 ChapterState 3개 — 기존 테스트 갱신 필요
- ❌ 신규 epilogue 씬 9개 — 콘텐츠 작업 (각 2-4 dialogue)
- ❌ Salvation_INTRO/EPILOGUE UI — 메뉴 + 재생 로직

### 중립
- ending_type 패턴은 이미 존재 (각 챕터 JSON에 명시)
- epilogue는 1인칭 (기존 씬 톤과 일관)

### Implementation Results (2026-07-07)

| 항목 | 구현 | 비고 |
|---|---|---|
| ChapterState | ✅ SALVATION_INTRO/EPILOGUE/DONE/FINAL | `run/state.py` |
| Stage | ✅ SALVATION_EPILOGUE | `run/state.py` |
| SalvationRunner | ✅ `engine/salvation.py` | 9자 epilogue 선택/재생/엔딩 선택 |
| epilogue 씬 | ✅ 9개 (09_epilogue.json) | case/sil/kas/suit/wigan/angie/sally/3jane/neuromancer |
| 테스트 | ✅ 40 tests | `tests/unit/test_salvation.py` |

## 8. Alternatives

### A. Salvation 없음 (현재 상태 유지)
- **장점**: 작업 없음
- **단점**: Salvation이 ENDING_A/B/C로만 표현 (epilogue 없음)
- **기각 사유**: epilogue 없이는 9자 키 활용도 미흡, ROADMAP 차순 미해결

### B. Salvation = 챕터 5만
- **장점**: 새 시스템 불필요
- **단점**: 챕터 5는 이미 존재 → "Salvation"이라는 명칭이 무의미
- **기각 사유**: 명목적 변경, 콘텐츠 효과 없음

### C. Salvation = 9자 epilogue만
- **장점**: 시스템 단순
- **단점**: 기존 ENDING_A/B/C와 중복, 단일 통합 없음
- **기각 사유**: A(Ending)와 통합하여 완결성 ↑

## 9. Implementation Plan (Phase 9-A)

| 단계 | 내용 | 예상 |
|---|---|---|
| 1 | `decisions/0090-salvation-phase.md` Accepted | 1일 |
| 2 | `run/state.py` SALVATION_INTRO/EPILOGUE/FINAL 추가 + Stage.SALVATION_EPILOGUE 추가 | 1일 |
| 3 | `engine/salvation.py` 신규 (Salvation 메뉴 + epilogue 재생) | 2일 |
| 4 | `data/scenes/{char}/09_epilogue.json` 9개 신규 | 2일 |
| 5 | `tests/unit/test_salvation_phase.py` 신규 (9자 epilogue + ending_type 매핑) | 1일 |
| 6 | `SALVATION_PHASE_INTEGRATION.md` v0.2.0 (구현 반영) | 0.5일 |
| **합계** | | **7-8일** |

## 10. References

- `design/scenario/SALVATION_PHASE_INTEGRATION.md` (v0.1.0) — 연계성 분석
- `design/scenario/story-stage-comparison.md` — 단편소설 vs 게임 상태 비교
- `design/scenario/chapter-progress.md` — 챕터 구현 진도
- `prototype/src/wet_run/run/state.py:89-110` — ChapterState enum
- `prototype/src/wet_run/engine/chapter_cutscene.py:98` — ending_type
- `prototype/data/systems/stage_structure.json` — 13 stages

---

**Status**: Accepted
**Implemented**: 2026-07-07
**Next**: 튜토리얼/온보딩 (Phase 7 나머지)
**Owner**: TBD
**Review**: Phase 10 완료 후

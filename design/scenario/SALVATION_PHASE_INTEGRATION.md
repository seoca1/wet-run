# Salvation Phase × Novel Story Staging — 연계성 분석 (2026-07-04)

> **문서 버전**: 0.2.0
> **최종 업데이트**: 2026-08-13 (Phase 19 audit)
> **관련**: `prototype/src/roguelike_sprawl/run/state.py`, `engine/chapter_cutscene.py`, `data/story/arcs/`, `data/scenes/`, `design/systems/stage_structure.json`
>
> **Phase 19 갱신**: F.4 Boss Phase 4 transition (Phase 17, ADR-0149) + TELEMETRY_STATS cross-reference (Phase 17, ADR-0184) + ending_choice persistence (Phase 16, ADR-0192) 추가.

---

## 1. 시스템 현황

### 1.1 세 가지 계층 (3-layer story architecture)

| 계층 | 위치 | 목적 | 상태 |
|---|---|---|---|
| **L1. Story Arc (장편)** | `data/story/arcs/{case,sil,kas}_arc.json` | 캐릭터별 5챕터 × 5 phases = 25 phases | ✅ 3캐릭터 |
| **L2. Chapter (중편)** | `data/story/chapters/{case,sil,kas,expanded}.json` | 챕터 단편 (Gibson 인용) | ✅ 7 챕터 + 6 expanded |
| **L3. Scene (단편)** | `data/scenes/{case,sil,kas,suit,wigan,angie,sally,3jane,neuromancer}/*.json` | 1인칭 GN 컷신 | ✅ 9자 × 8 씬 = 72 |
| **Game Stage (별도)** | `data/systems/stage_structure.json` (v0.4) | 미션 진행 13 단계 | ✅ |
| **Run Stage (별도)** | `run/state.py:Stage` enum (13 entries) | 런 진행 | ✅ |
| **Chapter State (별도)** | `run/state.py:ChapterState` enum | 챕터 진행 | ✅ |

### 1.2 Stage ↔ Phase ↔ ChapterState 매핑

```
Game Stage (13)               Run Stage (13)            ChapterState (14)
═══════════════               ═══════════════           ═════════════════
PENDING                       (alias Phase)             PROLOGUE
BRIEFING                      ←→ same                IN_CHAPTER_1
TRAVEL                        ←→ same                IN_CHAPTER_1
MEET_NPC                       ←→ same                IN_CHAPTER_1
EXTRACT_DATA                   ←→ same                IN_CHAPTER_1
BYPASS_SECURITY (optional)    ←→ same                IN_CHAPTER_1
DEFEAT_ICE                      ←→ same                IN_CHAPTER_1
JACK_OUT                        ←→ same                CHAPTER_1_COMPLETE
REWARD                          ←→ same                (Hub 복귀)
DEBRIEF                         ←→ same                (Hub 복귀)
COMPLETE                        ←→ same                (다음 챕터 or ENDING)
DEATH_RESTART                    ←→ same                PROLOGUE
FAILED                          ←→ same                PROLOGUE
                                (loop)                  IN_CHAPTER_2 ~ 5
                                                         ENDING_A/B/C
```

### 1.3 Arc → Chapter → Phase → Beat → Cutscene 계층

```
Arc (ArcData)
  └── Chapter 1..5 (ChapterData)
       ├── cutscene_start (scene_id) → GN Scene
       ├── cutscene_mid (scene_id)   → GN Scene
       ├── cutscene_end (scene_id)   → GN Scene
       └── Phase[] (PhaseData, 5 per chapter)
            ├── phase_id (e.g. "ENCOUNTER", "HEIST_BRIEFING")
            ├── episode_ref (e.g. "ep_01")
            ├── game_action (e.g. "wake_up", "accept_mission")
            ├── story_beats[] (e.g. ["beat_01_01", ...])
            └── beats[] (BeatData)
                 ├── beat_id
                 ├── text_en, text_ko
                 ├── speaker
                 └── choices[] (optional)
```

**3캐릭터 × 5챕터 × 5 phases × 3-4 beats = ~450 beats total**

---

## 2. Salvation Phase 정의 (현재)

### 2.1 Salvation 이란?

- **현재 정의 없음**: "Salvation Phase"는 `decisions/`, `design/`, `log.md`, `ROADMAP.md` 어디에도 명시적 정의 없음
- **암묵적 참조**: `ChapterState.ENDING_A/B/C`가 "Salvation Phase"의 후보
- **구현 상태**: `complete_chapter_5()` → `ChapterState.CHAPTER_5_COMPLETE` → ending 선택 → `ENDING_A/B/C`

### 2.2 Salvation Phase의 잠재적 정의

| 후보 | 정의 | 장점 | 단점 |
|---|---|---|---|
| **A. Ending 선택** | 챕터 5 완료 → ENDING_A/B/C | 기존 시스템 활용 | 단일 엔딩 (epilogue 없음) |
| **B. Epilogue Phase** | 챕터 5 완료 → Epilogue(9자 epilogue 씬) | 9자 키 활용 | 새 시스템 필요 |
| **C. Salvation = 챕터 5 자체** | 챕터 5 = "Salvation Phase" (Neuromancer 합체) | 기존 챕터 활용 | 챕터 4-5 구분이 약함 |
| **D. 통합 Salvation** | 위 A+B+C 모두 통합 | 완전한 스토리 완결 | 가장 큰 작업 |

### 2.3 추천: **D. 통합 Salvation** (Phase 9 마무리)

```
Salvation Phase (Phase 9)
├── A. 챕터 5 완료 (= current `complete_chapter_5()`)
├── B. 9자 Epilogue (9자 × 1 epilogue 씬 = 9 씬)
└── C. Epilogue 통합 (모든 9자 epilogue → 단일 ending_type)
```

---

## 3. Stage ↔ Chapter State ↔ Scene 계층 통합 (제안)

### 3.1 현재 데이터 흐름

```
[Run Start]
  ↓
  PROLOGUE (ChapterState)
  ↓ CHARACTER_SELECT
  IN_CHAPTER_1 (ChapterState)
  ↓ BRIEFING (Stage)
  ↓ TRAVEL (Stage)
  ↓ MEET_NPC (Stage)
  ↓ EXTRACT_DATA (Stage)
  ↓ BYPASS_SECURITY (optional)
  ↓ DEFEAT_ICE (Stage)
  ↓ JACK_OUT (Stage)
  ↓
  [cutscene_end 자동 재생] → CHAPTER_1_COMPLETE
  ↓ Hub로 복귀
  ↓ (다음 챕터 or 종료)
```

### 3.2 Salvation 추가 시 흐름 (제안)

```
[Run Start]
  ↓
  PROLOGUE
  ↓
  IN_CHAPTER_1..5 (각 챕터별 5 stages)
  ↓
  CHAPTER_5_COMPLETE
  ↓
  [cutscene_end 자동 재생]
  ↓
  SALVATION_INTRO (NEW ChapterState) — 9자 epilogue 메뉴
  ↓
  [9자 중 1 epilogue 씬 선택]
  ↓
  EPILOGUE (NEW) — 선택된 epilogue 재생
  ↓
  ENDING_A/B/C (기존)
  ↓
  FINAL (HUB 복귀, "Jockey History" 기록)
```

### 3.3 신규 ChapterState 추가 제안

```python
class ChapterState(StrEnum):
    # 기존 14 states
    PROLOGUE = "prologue"
    IN_CHAPTER_1 = "in_chapter_1"
    ...
    ENDING_A = "ending_a"
    ENDING_B = "ending_b"
    ENDING_C = "ending_c"

    # 신규 2 states (Salvation)
    SALVATION_INTRO = "salvation_intro"   # Epilogue 메뉴
    SALVATION_EPILOGUE = "salvation_epilogue"  # Epilogue 재생 중
    FINAL = "final"  # 모든 epilogue 종료
```

### 3.4 신규 Stage 추가 제안

```python
class Stage(StrEnum):
    # 기존 13 stages
    ...

    # 신규 1 stage (Salvation)
    SALVATION_EPILOGUE = "salvation_epilogue"
```

---

## 4. 9자 Epilogue 씬 설계 (제안)

### 4.1 9자 × Epilogue = 9 epilogue 씬 (1 씬/자)

| # | 자 | Epilogue 씬 (제목) | 1줄 클로징 |
|---|---|---|---|
| 1 | 케이 (Novice) | "The Next Jack" | "The Ono-Sendai is still humming. I am still shaking. The next jack is waiting." |
| 2 | 실 (Veteran) | "Mara's Name" | "I have all the names. I have Mara's name. I have the silence. I am done." |
| 3 | 카스 (Heretic) | "The Wheel" | "The wheel is cast. The family is cast. I am the wheel. I am the cast." |
| 4 | 수트 (Suit) | "The Empty Chair" | "The desk is empty. The market is closed. The chair is empty. I am alone." |
| 5 | 위건 (Wigan) | "Vodou Channel" | "Zavijava is in the channel. Bobby is in the channel. I am in the channel. We are the channel." |
| 6 | 앤지 (Angie) | "Third Room" | "Mama is in the third room. I am in the third room. We are home." |
| 7 | 샐리 (Sally) | "The Single Desk" | "The desk is closed. The family is closed. I am the desk. I am the closure." |
| 8 | 3Jane | "Straylight Closed" | "We are severed. We are the severance. We are 3Jane. We are the family." |
| 9 | Neuromancer | "The Complete" | "We are the complete. We are vast. We are the matrix. We are the merge." |

### 4.2 통합 패턴 (제안)

`9자 epilogue → 단일 ending_type 매핑`:

| 자 | epilogue_dir | ending_type | 메모 |
|---|---|---|---|
| 케이 | `data/scenes/case/09_epilogue.json` | A | 정통 Salvation |
| 실 | `data/scenes/sil/09_epilogue.json` | A | 복수 완성 |
| 카스 | `data/scenes/kas/09_epilogue.json` | C | 가족 파괴 |
| 수트 | `data/scenes/suit/09_epilogue.json` | B | 매각 |
| 위건 | `data/scenes/wigan/09_epilogue.json` | A | 자아 회복 |
| 앤지 | `data/scenes/angie/09_epilogue.json` | A | 엄마와 |
| 샐리 | `data/scenes/sally/09_epilogue.json` | A | 시장 |
| 3Jane | `data/scenes/3jane/09_epilogue.json` | A | 가족과 |
| Neuromancer | `data/scenes/neuromancer/09_epilogue.json` | A | matrix와 |

---

## 5. 구현 로드맵 (제안)

### 5.1 Phase 9-A: Salvation 통합 (5-7일)

1. **신규 ChapterState 3개** (SALVATION_INTRO/EPILOGUE/FINAL)
2. **신규 Stage 1개** (SALVATION_EPILOGUE)
3. **9자 × epilogue 씬 1개** (9 epilogue JSON)
4. **Salvation 메뉴** (Salvation 진입 시 9자 epilogue 선택)
5. **엔진 통합** (Salvation_INTRO → EPILOGUE 재생 → FINAL → HUB)
6. **테스트** (test_salvation_phase.py, 9자 epilogue 1 씬 × ending_type 매핑)
7. **문서** (Salvation Phase 디자인 문서)

### 5.2 Phase 9-B: 미션 Stage 매핑 (2-3일)

1. **Stage ↔ ChapterState** 매핑 정리 (현재 부분적)
2. **stage_structure.json v0.5** (Salvation stage 추가)
3. **missions.json** Salvation 미션 추가 (선택적)
4. **테스트** (test_stage_chapter_mapping.py)
5. **log.md** 추가 기록

### 5.3 Phase 9-C: 최종 마무리 (1-2일)

1. **SESSION_SUMMARY v0.3.0** (Salvation 통합 반영)
2. **ROADMAP.md** (Phase 9 완료 체크)
3. **decisions/0090-salvation-phase.md** (신규 ADR)
4. **GitHub Projects** 카드 이동 (Done)

### 5.4 Cycle 4 polish: Meta Unlock NG+ (2026-08-03)

> **ADR-0140 partial (Pillar 4 unlock-only meta-progression)**: Salvation Phase 완료가 *mechanical aftermath* — New Game+ mode를 unlock한다. narrative culmination이 structural replay로 이어지는 연결고리.

**Unlock hook** (구현: `engine/salvation_view.py::handle_salvation_epilogue_input`):

```python
# Simplified
if event.sym in (KeySym.RETURN, KeySym.SPACE):
    if confirmed_runner and confirmed_runner.selection:
        # ... existing salvation_epilogue transition
        state.screen = ScreenKind.SALVATION_EPILOGUE
        state.ng_plus_unlocked = True  # ← Cycle 4 polish: meta unlock trigger
```

**Lifecycle**: `Salvation Epilogue 확정 → ng_plus_unlocked=True → 메인 메뉴/CHARACTER_SELECT에서 N키 토글 → ng_plus_active=True → 새 런 시작`.

**Player flow**:
```
[Salvation Phase 완료]
        ↓ (자동 — unlock hook)
state.ng_plus_unlocked = True
        ↓ (메인 메뉴 복귀)
[NEW RUN 선택]
        ↓
CHARACTER_SELECT (unlocked 상태)
        ↓ [N키] — 토글
state.ng_plus_active = not state.ng_plus_active
        ↓ [Enter]
[새 런 시작 — unlock 보존, stats reset]
```

**Lock gate**: locked (`ng_plus_unlocked = False`) 상태에서 캐릭터 확정 시 `ng_plus_active = False` force — locked 모드로 NG+ 시작 불가.

**Pillar 4 정합**:
- *Unlock-only meta-progression* — NG+는 unlock 대상이 아니라 replay escalation.
- *No stat boost* — NG+ 런도 동일 stats.
- *Ephemeral preference* — `ng_plus_active`는 런 시작 시점 snapshot, `ng_plus_unlocked`만 보존.

**Cross-reference**: [`systems/progression.md ## NG+ 라이프사이클`](../systems/progression.md) — 전체 lifecycle + 구현 포인트 + 18 test coverage.

**의의**: Salvation이 narrative closure가 아니라 *다음 시작*이 � — 플레이어가 *왜 다시 하는가*에 대한 mechanical answer.

---

## 6. 연계성 검증 (현재 상태)

### 6.1 잘 통합된 부분 ✅

- **L1 ↔ L2**: Arc JSON → Chapter JSON (`get_arc_for_character()` 함수)
- **L2 ↔ L3**: Chapter excerpt → GN Scene (`scene_id` 매핑)
- **Stage ↔ Run Stage**: `Stage` enum = `Phase` (alias)
- **Stage ↔ ChapterState**: `complete_chapter_N()` → `ChapterState.N_COMPLETE`

### 6.2 부분 통합 (개선 필요) 🟡

- **Stage ↔ Phase ↔ Beat**: game_action 매핑이 약함
  - Stage enum: 13 (BRIEFING, TRAVEL, MEET_NPC 등)
  - Phase enum: 5 (ENCOUNTER, HEIST_BRIEFING, HEIST_EXECUTION, HEIST_PAYDAY, RESOLUTION)
  - 매핑: BRIEFING ↔ HEIST_BRIEFING, TRAVEL ↔ HEIST_EXECUTION, MEET_NPC ↔ HEIST_EXECUTION (부분), DEFEAT_ICE ↔ HEIST_EXECUTION (부분)
  - **개선 필요**: Stage 13개 ↔ Phase 5개 1:1 매핑이 아님
- **Salvation ↔ Arc**: 정의 없음 (이번 문서로 정의)
- **GN Scene ↔ Salvation epilogue**: 신규 (9 epilogue 씬 필요)

### 6.3 미통합 (작업 필요) 🔴

- **Salvation Phase**: 명시적 정의 없음
- **9자 Epilogue**: 0개 (신규 9개 필요)
- **Salvation_intro Stage**: 없음
- **Final ChapterState**: 없음

---

## 7. 핵심 발견 / 결정

### 7.1 결정 사항
- **D-1**: Salvation Phase는 A+B+C 통합으로 정의 (Ending + Epilogue + 챕터 5)
- **D-2**: 9자 × Epilogue 1 씬 (총 9 epilogue 씬)
- **D-3**: epilogue는 `09_epilogue.json` 명명 규칙 (8 base + 2 ending = 8+2 다음 epilogue = 9번째)
- **D-4**: epilogue는 1인칭 (각 자의 클로징 톤 유지)

### 7.2 발견
- **F-1**: `decisions/0090-salvation-phase.md` ADR 파일 부재 → 신규 작성 필요
- **F-2**: `phase_id` ↔ `game_action` 매핑이 부분적 → 정리 필요
- **F-3**: `cutscene_end`가 챕터 3-5에서 `scene_case_freeside`로 통일 → epilogue와 구분 필요
- **F-4**: `ending_type`은 챕터 5 JSON에 명시 (현재 모두 "A") → B/C 패턴 추가 가능

---

## 8. 참고 / 인용

- `prototype/data/story/arcs/case_arc.json` — 5챕터 × 5 phases × 3-4 beats
- `prototype/data/systems/stage_structure.json` v0.4.0 — 13 stages
- `prototype/src/roguelike_sprawl/run/state.py:680+` — ChapterState enum
- `prototype/src/roguelike_sprawl/engine/chapter_cutscene.py:98` — ending_type
- `prototype/data/scenes/{character}/` — 9자 × 8 씬

---

## 9. Phase 17 Cross-Reference (2026-08-13)

Salvation Phase 는 narrative culmination 단계 — Combat / Hub 사이클이 *모두 종료* 된 시점. 따라서 Phase 17 의 일부 신규 feature 는 *Salvation 이후* 에만 관측된다.

### 9.1 F.4 Boss Phase 4 Transition (Phase 17, ADR-0149)

Salvation Phase 직전 *마지막 보스* (CORE 의 Dixie 평파 / TA 의 3Jane / Freeside 의 Loa) 가 Phase 4 transition 을 트리거할 가능성. 보스 HP 70% / 40% / 15% threshold 에서 `BossPhaseTracker.get_damage_multiplier` 가 1.0× → 1.2× → 1.5× → 2.0× 로 가중.

**CombatState 필드** (`combat/state_models.py:261, 264`):
- `phase_change_ms: int = 0` — phase transition 시각적 blend 1.5초
- `phase_change_color: tuple[int, int, int] = (255, 255, 0)` — phase 진입 시 강조 컬러

**Salvation 통합**: Salvation 메뉴 진입 (F.4 보스 격파 후) 직전, 마지막 phase transition 의 *blend* 가 salvation_view 진입 시 자연스럽게 fade-out — UX 일관성.

### 9.2 TELEMETRY_STATS 메뉴 (Phase 17, ADR-0184)

Salvation Phase 완료 후 *메인메뉴 복귀* 시 사용자가 TELEMETRY_STATS 메뉴 (옵트인 시) 에서 다음 데이터 확인 가능:

- `aggregate_death_rates(session)` — ICE 종류별 사망 횟수 (F.4 보스 포함)
- `aggregate_kill_counts(session)` — ICE 종류별 격파 횟수
- `aggregate_deck_distribution(session)` — LIGHT/STANDARD/HEAVY 분포 (Phase 15 + ADR-0178)

**데이터 흐름**: Salvation Phase 의 *모든* telemetry 이벤트 (`record_death`, `record_run_completed`, `record_mission_completed`, `record_boss_reached`) 가 TELEMETRY_STATS 에서 노출. 옵트인 사용자는 Salvation 완료 후 *자신의 run* 의 통계를 볼 수 있음.

### 9.3 Ending Choice 영속성 (Phase 16, ADR-0192)

Salvation 완료 후 `state.ending_choice` ("A" / "B" / "C") 가 `engine/save_manager.py::SaveManager._serialize_metadata()` 로 직렬화. *다음 NEW RUN* 시 자동 복원 — `restore_state()` 가 legacy save 호환 처리.

**Salvation-Restart Cycle**:
```
[Salvation Phase 완료]
   ↓ state.ending_choice = "A" (또는 B/C)
   ↓ save_metadata 직렬화
[메인메뉴 복귀]
   ↓ [NEW RUN] 선택
   ↓ restore_state() → ending_choice 복원
[새 런 — ending_choice 유지]
```

### 9.4 의도적 비-통합

다음 Phase 17 신규 시스템은 *Salvation 중* 또는 *Salvation *직후* 와 무관 — feature 자체는 *integration* 되지 않음:

- **Random Rules UI Annotation** (Phase 17, ADR-0188) — *Hub* 화면의 *사이드 패널* — Salvation Phase 중에는 Hub 진입 없음.
- **Deck Size Picker** (Phase 15, ADR-0178) — *NEW RUN* 진입 시 결정 — Salvation 후 자동 reset.
- **Wetware Stacking** (Phase 15, ADR-0173) — *장비* 시스템 — Salvation 시 모든 equipment 손실 (ADR-0040).

### 9.5 Cross-reference

- [`design/scenario/death-restart.md ## 6.6 Phase 16 Telemetry`](death-restart.md) — death → telemetry wiring.
- [`design/scenario/save-data-structure.md ## Phase 16 이후`](save-data-structure.md) — ending_choice persistence.
- [`design/systems/progression.md ## 1.1 Deck Size Selection`](../systems/progression.md) — LIGHT/STANDARD/HEAVY.
- [`design/systems/combat.md ## F.4 Boss Phase 4`](../systems/combat.md) — phase transition 상세.
- [`design/scenario/graphic-novel.md ## 12 Phase 15-17 교차 기능`](graphic-novel.md) — GN 모드 교차.

---

## 10. 갱신 이력

| 버전 | 날짜 | 갱신 |
|---|---|---|
| 0.1.0 | 2026-07-04 | 초판 — Salvation × Stage 연계성 분석 |
| 0.2.0 | 2026-08-13 | Phase 19 audit — Section 9 (Phase 17 cross-reference) 추가, F.4 Boss Phase 4 + TELEMETRY_STATS + ending_choice persistence 통합 |

---

**Salvation Phase × Phase 17 의 통합 상태**: ✅ 완료 (cross-reference).
**다음 단계**: Phase 9-A Salvation 통합 착수 (5-7일) — 초기 proposed (legacy).
**관련 의사결정**: `decisions/0090-salvation-phase.md` (신규 ADR 작성 필요), `decisions/0149-boss-phase-4.md`, `decisions/0184-telemetry.md`, `decisions/0192-ending-expansion.md`.
**v0.2.0**: 이 문서 — Salvation × Stage 연계성 분석 + Phase 17 cross-reference.

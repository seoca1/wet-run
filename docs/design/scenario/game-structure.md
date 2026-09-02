# 게임 구조 설계 — 5챕터 아키텍처

## 문서 상태: DRAFT

---

## 1. 용어 재정의

### 기존 용어 vs 새 용어

| 기존 | 새 용어 | 설명 |
|------|---------|------|
| `Stage` (PENDING, MEET_NPC, …) | **`Phase`** | 하나의 미션 안에서 플레이어가 달성해야 할 목표 단계 |
| `chapter.json` (단편 텍스트) | **`Prologue`** | 캐릭터 선택 직후 1회성 Cinematic 텍스트. 플레이에 포함되지 않음 |
| GN scene × 8 | **`Cutscene`** (컷씬) | 챕터 내에서 스토리를 전하는 자동재생 시각적 노블 |
| 한 캐릭터의 전체 흐름 | **`Chapter`** (챕터) | 하나의 완결된 스토리 단위. 여러 Phase + Cutscene으로 구성 |
| 한 캐릭터의 전체 스토리 | **`Arc`** (아크) | 한 캐릭터의 5개 챕터 전체. 5 × Phase 루프 |

### 계층 구조

```
Arc (1 Character = 5 Chapters)
├── Chapter 1
│   ├── Cutscene 1-N (GN scenes)
│   └── Phase 1-N (gameplay stages)
├── Chapter 2
│   ├── Cutscene 1-N
│   └── Phase 1-N
├── …
└── Chapter 5
    ├── Cutscene 1-N
    └── Phase 1-N → ENDING
```

---

## 2. Prologue 정의

**Prologue**는 캐릭터 선택 직후 1회だけ 표시される短編テキスト。

- **위치**: 캐릭터 선택 직후, Hub 진입 전
- **성격**: Cinematic 텍스트 (타이핑 효과), Gibson 스타일 오프닝
- **플레이 포함 여부**: ❌ 아니오 —叙事用 intro, 플레이어 조작 없음
- **현재 구현**: `data/story/chapters/{case,sil,kas}.json`의 `excerpt_en/ko`
- **데이터 위치**: `data/story/prologues/{character}.json`
- **새 구현 분리 이유**: 챕터가 "플레이하는 스토리 단위"가 되면서, intro는 별도 것으로 분리

### Prologue 전환

```
CHARACTER_SELECT → PROLOGUE (1회) → HUB → CHAPTER_1_PHASE_1
```

### 각 캐릭터 Prologue 요약

| 캐릭터 | 파일 | EN chars | KO chars | 내용 |
|--------|------|----------|----------|------|
| novice (케이) | `case.json` excerpt | ~1,400 | ~4,800 | "30 seconds after jack-out" — Chiba, Ono-Sendai, trembling hands |
| veteran (실) | `sil.json` excerpt | ~1,300 | ~6,600 | "Louisiana, address 11" — Marly in front of voodoo shop masks |
| heretic (카스) | `kas.json` excerpt | ~1,300 | ~8,100 | "Manarase. Midnight." — Kumiko in taxi, Yanaka, T-A |

---

## 3. 5챕터 구조 — 케이 (Novice / Case)

각 챕터는 **Cutscene N개 + Phase N개**로 구성.

### 챕터 구조 요약

| 챕터 | 제목 | Cutscenes | Phases | 핵심 스토리 |
|------|------|-----------|--------|-------------|
| 1 | **The First Run** | 2 | 3 (HUB→NPC→DATA) | 첫 잭인, The Finn의 임무, 데이터 추출 |
| 2 | **Molly's Deal** | 2 | 3 (HUB→NPC→ICE) | 몰리의 등장, ICE 전투, 잭아웃 |
| 3 | **Straylight Run** | 2 | 3 (HUB→NPC→DATA→ICE) | Villa Straylight 침투, T-A 데이터 |
| 4 | **The Flatline** | 2 | 3 (HUB→NPC→ICE) | Dixie Flatline, Wintermute 임무 |
| 5 | **Neuromancer** | 2 | 3 (HUB→ICE→???) | Wintermute 통합, 엔딩 |

### Phase 정의 (현재 Stage 기반)

기존 `Stage` enum → 새 **`Phase`** enum으로 이름 변경:

```
HUB           → Hub에서 미션 수락 대기 (기존 PENDING)
SEEK_NPC      → NPC 노드 탐색/대화 (기존 MEET_NPC)
EXTRACT_DATA  → 데이터 노드 접근/추출 (기존과 동일)
DEFEAT_ICE    → ICE 노드 전투 (기존과 동일)
JACK_OUT      → 매트릭스 분리 (기존과 동일)
REWARD        → 보상 수령 (기존과 동일)
DEBRIEF       → 미션 결과 (기존과 동일)
COMPLETE      → 미션 종료 (기존과 동일)
```

---

## 4. Cutscene vs Phase 전환

각 챕터 안에서:

```
[Cutscene 1] → [Phase 1] → [Cutscene 2] → [Phase 2] → ... → [CHAPTER_END]
```

### CHAPTER_END 이벤트

챕터 마지막 Phase 완료 시 발생:

1. **잭아웃 애니메이션** (JACK_OUT)
2. **Cutscene** (챕터 마무리 스토리)
3. **결과 화면** (보상,choices 누적)
4. **Hub 복귀** 또는 **다음 챕터 자동 진입**

### Hub vs Chapter Hub

| 용어 | 설명 |
|------|------|
| **Hub** | Phase 사이休憩场所. 메뉴 접근, 세이브 가능 |
| **Chapter Hub** | 챕터 간休息. 캐릭터专属 공간 (예: Case는 Chiba) |

---

## 5. 각 캐릭터 5챕터 개요

### 5.1 케이 (Novice) — 5 Chapters

| # | 제목 | 핵심 질문 | Cutscene 수 | Phase 수 |
|---|------|----------|-------------|----------|
| 1 | The First Run | 첫 잭인은 성공하는가? | 2 | 3 |
| 2 | Molly's Deal | 몰리와 무슨 거래를 하는가? | 2 | 3 |
| 3 | Straylight Run | Villa Straylight에서 무엇을 찾는가? | 2 | 4 |
| 4 | The Flatline | Dixie Flatline은敌か友か? | 2 | 3 |
| 5 | Neuromancer | 윈터뮤트와 통합하면 무엇이 되는가? | 2 | 3+ |

### 5.2 실 (Veteran) — 5 Chapters

| # | 제목 | 핵심 질문 | Cutscene 수 | Phase 수 |
|---|------|----------|-------------|----------|
| 1 | The Old Score | Mara의 죽음에 복수하는가? | 2 | 3 |
| 2 | The Voodoo God | 루아의 진실은 무엇인가? | 2 | 3 |
| 3 | The Insider | T-A 내부의 배신자는 누구인가? | 2 | 4 |
| 4 | The Contract | 계약의 진짜 대가는 무엇인가? | 2 | 3 |
| 5 | The Blank | 모든 것이 사라진 후 남는 것은? | 2 | 3+ |

### 5.3 카스 (Heretic) — 5 Chapters

| # | 제목 | 핵심 질문 | Cutscene 수 | Phase 수 |
|---|------|----------|-------------|----------|
| 1 | The Declaration | 아버지를 죽이는 것은 정당한가? | 2 | 3 |
| 2 | The Silence | 매나리사에서 무슨 일이 있었는가? | 2 | 3 |
| 3 | The Shadow | 그림자 속 실체는 누구인가? | 2 | 4 |
| 4 | The Weapon | 무기는 언제 쓰여야 하는가? | 2 | 3 |
| 5 | The Burn | 모든 것을 태운 후 남는 것은? | 2 | 3+ |

---

## 6. 구현 우선순위 (20% — 프로로그 + 챕터1)

### 범위

- **구현 대상**: 케이(Novice)의 Chapter 1만
- **구현하지 않음**: 실/카스, 챕터 2-5
- **구현 내용**:
  1. Prologue (`case.json` → `data/story/prologues/case.json`으로 분리)
  2. Chapter 1의 Cutscene 2개 (기존 GN scene 2개 재활용)
  3. Chapter 1의 Phase 3개 (HUB → SEEK_NPC → EXTRACT_DATA)
  4. Chapter 1 End 이벤트 → CHAPTER_COMPLETE 상태

### Phase → Chapter 매핑 (챕터1)

| Phase | 기존 Stage | 설명 |
|-------|-----------|------|
| HUB | PENDING | Hub에서 첫 미션 수락 |
| SEEK_NPC | MEET_NPC | The Finn NPC와 대화 |
| EXTRACT_DATA | EXTRACT_DATA | 데이터 추출 Phase |
| DEFEAT_ICE | — | 챕터1에는 ICE 없음 (챕터2부터) |
| JACK_OUT | JACK_OUT | 첫 잭아웃 (애니메이션) |
| REWARD | REWARD | 첫 보상 |
| COMPLETE | COMPLETE | 챕터1 종료 |

### CHAPTER 1의 GN Cutscene 재활용

현재 GN scene → 새 Chapter 1 Cutscene으로 매핑:

| 기존 GN ID | 새 Cutscene ID | 제목 | 용도 |
|-----------|---------------|------|------|
| `scene_case_intro` (01_chattos) | `cutscene_ch1_01` | CHATTO'S 24/7 | 챕터1 시작 컷씬 |
| `scene_case_jackin` (02_jackin) | `cutscene_ch1_02` | JACK-IN | Finn 임무 컷씬 |

---

## 7. 데이터 구조 변경

### 7.1 새 디렉토리

```
data/
├── story/
│   ├── prologues/          # NEW: 캐릭터별 Prologue JSON
│   │   ├── case.json
│   │   ├── sil.json
│   │   └── kas.json
│   ├── chapters/           # 기존 (단편, 챕터 아님)
│   │   ├── case.json
│   │   ├── sil.json
│   │   └── kas.json
│   ├── arcs/               # NEW: 캐릭터별 Arc/챕터 정의
│   │   ├── case_arc.json   # 5챕터 메타데이터
│   │   ├── sil_arc.json
│   │   └── kas_arc.json
│   └── scenes/             # 기존 GN 씬 (Cutscene으로 재활용)
│       └── {case,sil,kas}/
└── saves/
```

### 7.2 Arc JSON 스키마

```json
{
  "character": "novice",
  "arc_id": "arc_case",
  "title_en": "Case's Arc",
  "title_ko": "케이의 아크",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_id": "ch_case_01",
      "title_en": "The First Run",
      "title_ko": "첫 런",
      "prologue_cutscene_id": "cutscene_ch1_01",
      "mid_chapter_cutscene_id": "cutscene_ch1_02",
      "ending_cutscene_id": null,
      "phases": ["HUB", "SEEK_NPC", "EXTRACT_DATA", "JACK_OUT", "REWARD"],
      "ending_type": "A",
      "next_chapter_id": "ch_case_02"
    }
  ]
}
```

---

## 8. 구현 체크리스트

### Phase A: Prologue 분리 (1일)

- [ ] `data/story/prologues/case.json` 생성 (기존 case.json excerpt 복사)
- [ ] `data/story/prologues/sil.json` 생성
- [ ] `data/story/prologues/kas.json` 생성
- [ ] `CharacterSelectEvent` → Prologue 표시 로직 변경
- [ ] 테스트: Prologue 3개 각 캐릭터에 대해 1회씩 표시

### Phase B: Chapter 1 구조 (2일)

- [ ] `Phase` enum 이름 변경 (기존 Stage → Phase)
- [ ] `data/story/arcs/case_arc.json` 생성 (챕터1 메타데이터)
- [ ] `ChapterState` 새 enum: `PROLOGUE | IN_CHAPTER_1 | CHAPTER_1_COMPLETE | ...`
- [ ] Chapter 1 Phase 흐름 구현: HUB → SEEK_NPC → EXTRACT_DATA → REWARD
- [ ] GN scene → Cutscene 매핑 로직 (기존 scene 재활용)
- [ ] CHAPTER_END 이벤트 핸들러
- [ ] 테스트: 케이 챕터1 1회 완주

### Phase C: Chapter 1 Cutscene (1일)

- [ ] `cutscene_ch1_01` (CHATTO'S 24/7) 표시 로직
- [ ] `cutscene_ch1_02` (JACK-IN) 표시 로직
- [ ] Cutscene between Phase 연결
- [ ] 테스트: Cutscene 자동재생 + 스킵

### Phase D: 문서 및 검증 (1일)

- [ ] `design/scenario/game-structure.md` 완성
- [ ] `design/scenario/chapter-progress.md` 진도 추적표 갱신
- [ ] 기존 테스트 2690개 통과 확인
- [ ] Makefile 타겟 갱신

---

## 9. 기존 Stage/AmbientEvent/AmbientInstruction 호환성

| 기존 | 새 | 호환성 |
|------|-----|--------|
| `Stage.PENDING` | `Phase.HUB` | 이름만 변경, 로직 동일 |
| `Stage.MEET_NPC` | `Phase.SEEK_NPC` | 이름만 변경 |
| `Stage.EXTRACT_DATA` | `Phase.EXTRACT_DATA` | 동일 |
| `Stage.DEFEAT_ICE` | `Phase.DEFEAT_ICE` | 동일 |
| `Stage.JACK_OUT` | `Phase.JACK_OUT` | 동일 |
| `Stage.REWARD` | `Phase.REWARD` | 동일 |
| `Stage.COMPLETE` | `Phase.COMPLETE` | 동일 |
| `CHARACTER_SELECT_EVENT` | Prologue 표시 | 기존 로직 유지 |
| `MISSION_ACCEPT_EVENT` | Chapter 시작 | 새 Chapter state 추가 |

---

## 10. 열린 질문

1. **챕터 간 세이브**: 챕터 완료 시 자동 세이브인가, 수동 세이브인가?
2. **Cutscene 스킵**: 이미 본 Cutscene은 스킵 가능한가?
3. **엔딩Choices 누적**: choices가 챕터 간 공유되는가 (예: T-A를 돕는다/적다)?
4. **멀티 엔딩**: Ending A/B/C가 챕터5 끝에만 있는가, 챕터마다 있는가?

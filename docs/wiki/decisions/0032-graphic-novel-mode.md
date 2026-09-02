# ADR-0032: Graphic Novel Auto-Play Mode + Main Menu 확장

> **상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
> **날짜**: 2026-06-20
> **결정자**: 사용자
> **관련**: ADR-0031 (Original Scenario), ADR-0009 (Story/News), ADR-0011 (Portrait), ADR-0019 (Aftermath), ADR-0021 (Save/Load)

## 1. 컨텍스트

현재 게임 흐름: `MENU → CHARACTER_SELECT → CHAPTER → HUB → MATRIX → JACK_OUT → AFTERMATH → ENDING`

문제점:
1. **메인메뉴 옵션이 빈약** — `New Run / Story Archive / Settings` 3개뿐. 게임 정체성이 부족.
2. **CHAPTER 화면이 단일-씬** — 한 캐릭터의 챕터 텍스트가 한 화면에 다 표시. 비주얼 노블의 "씬 전환" 개념 부재.
3. **스토리 진입로가 캐릭터 선택에 종속** — 그래픽 노블 모드처럼 "그냥 스토리를 보고 싶다" 진입로 없음.
4. **세이브 진도와 스토리의 연결 없음** — "지금까지 내가 어디까지 왔는지" 시각적 회고 부재.

**사용자 요구 (2026-06-20)**:
- "게임 시작하면 프롤로그와 실제 게임플레이를 진행하기 전에 메인메뉴를 만들고"
- "그래픽 노블 같은 느낌으로 스토리를 간략히 즐길 수 있는 자동플레이 모드를 추가"
- **프롤로그는 3명의 진행을 랜덤으로 보여주는 방식**
- **그 이후는 실제 플레이한 세이브 진도까지**
- **다른 캐릭터 스토리도 보기 옵션 제공**
- **표현 수준: 아트+연출 (캐릭터 포트레잇 + 장면 배경 + 사운드 큐)**

## 2. 목표

| # | 목표 | 효과 |
| --- | --- | --- |
| G1 | 메인메뉴 확장 (5개 옵션) | 게임 정체성 강화, 신규 진입로 |
| G2 | 그래픽 노블 자동플레이 모드 (씬 기반) | 비주얼 노블 경험 |
| G3 | 3 캐릭터의 씬을 랜덤 순서로 재생 (프롤로그) | 매 플레이마다 다른 순서, 재플레이 가치 |
| G4 | 씬 = 아트(배경+포트레잇) + 대사 + 사운드 + 타이핑 | 그래픽 노블 톤 |
| G5 | 자동 진행 + Skip 버튼 | 사용자 선택권 |
| G6 | 종료 후 세이브 진도 표시 (캐릭터/등급/미션) | 진행 회고 |
| G7 | 다른 캐릭터 스토리 진입 옵션 | 메뉴에서 자유롭게 재시청 |

## 3. 옵션 비교

### Option A: 씬 기반 그래픽 노블 (권장)

| 항목 | 내용 |
|---|---|
| 메인메뉴 | NEW RUN / **GRAPHIC NOVEL** / CONTINUE / SETTINGS / CREDITS |
| 그래픽 노블 진입 | 옵션 1: **프롤로그 (3명 랜덤)** / 옵션 2: **개별 캐릭터** (Case/Marly/Kumiko) |
| 씬 구성 | 캐릭터당 3~4 씬 (총 9~12 씬) |
| 씬 요소 | 배경 아트 (ASCII 80x40) + 캐릭터 포트레잇 (좌/우) + 대사 박스 (하단 5줄) + 사운드 큐 |
| 자동 진행 | 씬당 8~12초 (대사 길이 기반) + 클릭 시 즉시 진행 |
| 종료 | 마지막 씬 후 "당신의 자키" 카드 → 메인메뉴 |
| 장점 | 비주얼 노블 경험, 재플레이 가치, 메뉴 풍부 |
| 단점 | 씬 데이터 9~12 + 포트레잇/배경 9~12 + 엔진 모듈 1개 신규 |

### Option B: 현재 CHAPTER 화면 확장 (최소 변경)

| 항목 | 내용 |
|---|---|
| 메인메뉴 | NEW RUN / GRAPHIC NOVEL (= 현재 CHAPTER 멀티 버전) / ... |
| 씬 | 1 캐릭터 = 1 씬 (현재 CHAPTER와 동일) |
| 표현 | 타이핑 텍스트 + 포트레잇 (현재 수준) |
| 자동 진행 | 12초 후 다음 캐릭터 |
| 장점 | 구현 빠름 (1 세션) |
| 단점 | "그래픽 노블"이라 부르기 어려움. 씬 전환 없음. |

### Option C: 풀 시네마틱 (글리치/파티클/전이)

| 항목 | 내용 |
|---|---|
| 메인메뉴 | 동일 |
| 씬 | 9~12 씬 + 전이 애니메이션 + 글리치 효과 + 비네트 |
| 장점 | 가장 임팩트 |
| 단점 | 3~4 세션 작업. 디자인/구현 복잡. |

**추천**: **Option A** — 씬 기반 + 아트+연출. 비주얼 노블의 정체성 + 작업량 균형.

## 4. 권장안 (Option A) 상세

### 4.1 메인메뉴 확장

```
╔══════════════════════════════════════════════╗
║            ROGUELIKE SPRAWL                  ║
║   A cyberpunk roguelike based on Gibson's    ║
║              Sprawl trilogy                  ║
╠══════════════════════════════════════════════╣
║                                              ║
║      [1] NEW RUN        ─ 자키 선택부터      ║
║      [2] GRAPHIC NOVEL  ─ 스토리 자동재생     ║
║      [3] CONTINUE       ─ 마지막 세이브       ║
║      [4] SETTINGS                            ║
║      [5] CREDITS                             ║
║                                              ║
╚══════════════════════════════════════════════╝
```

### 4.2 그래픽 노블 진입 메뉴

```
╔══════════════════════════════════════════════╗
║           GRAPHIC NOVEL MODE                 ║
╠══════════════════════════════════════════════╣
║                                              ║
║  [1] PROLOGUE — 3명의 진행 (랜덤 순서)       ║
║      케이/실/카스의 프롤로그를 무작위로       ║
║      섞어 재생. 매번 다른 인트로 경험.       ║
║                                              ║
║  [2] 케이 (K) — Novice                       ║
║      "잭아웃 후 30초" 풀 스토리               ║
║                                              ║
║  [3] 실 (Sil) — Veteran                      ║
║      "루이지아나의 신" 풀 스토리              ║
║                                              ║
║  [4] 카스 (Kas) — Heretic                    ║
║      "매나리사의 자정" 풀 스토리              ║
║                                              ║
║  [5] BACK TO MAIN MENU                       ║
║                                              ║
╚══════════════════════════════════════════════╝
```

### 4.3 씬 구조 (캐릭터당 3~4 씬)

**케이 (K) — Novice**:
1. `[CHATTO'S 24/7]` — Chiba 호수텔, Cassis 24층 (도입)
2. `[JACK-IN]` — Ono-Sendai Cyberspace 7, 손가락 떨림 (전개)
3. `[JACK-OUT]` — 30초 후, 콘솔 테이블 위로 떨어짐 (절정)
4. `[THE FINN'S OFFICE]` — 핀이 자키를 기다림 (결말)

**실 (Sil) — Veteran**:
1. `[LOUISIANA, ADDRESS 11]` — Maison de Loa, 마스크 5개 (도입)
2. `[THE MASK]` — Wigan의 loa 채널 진입 (전개)
3. `[T-A PAYROLL]` — Tessier-Ashpool 사내 통신 추출 (절정)
4. `[THE BROADCAST]` — 3년 전 Mara의 죽음, 폭로 준비 (결말)

**카스 (Kas) — Heretic**:
1. `[MANARASE, MIDNIGHT]` — Shibuya 11번지, 택시 정차 (도입)
2. `[SALLY]` — Sally Shearer의 가죽 마스크 (전개)
3. `[THE DECLARATION]` — Loa 네트워크로 선언문 배포 (절정)
4. `[THE WHEEL]` — "바퀴는 돌아간다" — 산업 = 자본 = T-A (결말)

**총 12 씬**. 각 씬 = (배경 ASCII 12~20줄) + (포트레잇 좌/우) + (대사 박스 5줄) + (사운드 큐 1~2).

### 4.4 씬 데이터 형식

`data/scenes/{character}/{scene_id}.json`:
```json
{
  "id": "scene_case_intro",
  "character": "novice",
  "order": 1,
  "title_en": "CHATTO'S 24/7",
  "title_ko": "챠토 24/7",
  "background": "art:bg_chat_room",  // 80x40 ASCII art
  "portrait_left": "art:case_think",  // or null
  "portrait_right": "art:case_hands",  // or null
  "dialogue": [
    {
      "speaker": "case",
      "speaker_ko": "케이",
      "portrait": "art:case_think",
      "text_en": "30 seconds. The Ono-Sendai electrodes lift from my scalp...",
      "text_ko": "30초. Ono-Sendai 전극이 두피에서 떨어진다...",
      "duration_ms": 8000
    },
    {
      "speaker": "narrator",
      "portrait": null,
      "text_en": "Chiba. 11th level. The room smells of old circuits.",
      "text_ko": "지바. 11층. 방은 오래된 회로 냄새가 난다.",
      "duration_ms": 5000
    }
  ],
  "next_scene": "scene_case_jackin"
}
```

### 4.5 화면 레이아웃 (씬 1프레임)

```
┌─────────────────────────────────────────────────────────────┐
│ ◉P◉                                                         │ ← Portrait Left (10x16)
│  ┌────┐                                                      │
│  │    │     "30 seconds."                                    │
│  │ ◉  │     ──────────────                                  │
│  │    │     "The Ono-Sendai electrodes                      │ ← Background + dialogue box
│  │    │      lift from my scalp and my                      │   (overlayed)
│  │    │      fingers keep typing."                          │
│  │    │                                                      │
│  └────┘                                                      │
│                                                              │
│  ╔══════════════════════════════════════════════════════╗   │
│  ║ [1/12]  CHATTO'S 24/7  ·  CASE              [SKIP]  ║   │ ← Scene bar
│  ╠══════════════════════════════════════════════════════╣   │
│  ║ "30초. Ono-Sendai 전극이 두피에서 떨어진다..."       ║   │ ← Dialogue box (ko)
│  ║                                                       ║   │
│  ║  [auto-advance 8s] [ENTER] next [ESC] skip            ║   │ ← Controls
│  ╚══════════════════════════════════════════════════════╝   │
└─────────────────────────────────────────────────────────────┘
```

### 4.6 자동 진행 + Skip

| 키 | 동작 |
|---|---|
| (자동) | 씬당 duration_ms 후 다음 씬 |
| `Enter` / `Space` | 현재 대사 즉시 완료 → 다음 |
| `S` | 현재 씬 즉시 스킵 → 다음 씬 |
| `Esc` | 그래픽 노블 종료 → 메뉴 |
| `Q` | 메뉴로 강제 종료 |

### 4.7 종료 화면 (세이브 진도 표시)

마지막 씬 후:
```
╔══════════════════════════════════════════════╗
║             당신의 자키                      ║
╠══════════════════════════════════════════════╣
║                                              ║
║  자키: 실 (Sil) — Veteran                   ║
║  등급: 3-up                                  ║
║  미션 완료: 12 / 30 (40%)                   ║
║  데이터 회수: 234 / 500                      ║
║  현재 상태: Tessier-Ashpool 본부 잠입 중    ║
║                                              ║
║  [1] 다른 캐릭터 스토리 보기                 ║
║  [2] 게임플레이 계속 (HUB)                   ║
║  [3] 메인메뉴                                ║
║                                              ║
╚══════════════════════════════════════════════╝
```

세이브가 없으면:
```
╔══════════════════════════════════════════════╗
║             아직 자키가 없습니다             ║
╠══════════════════════════════════════════════╣
║                                              ║
║  세이브 파일이 없습니다.                     ║
║  NEW RUN으로 시작해 보세요.                  ║
║                                              ║
║  [1] NEW RUN                                ║
║  [2] 메인메뉴                               ║
║                                              ║
╚══════════════════════════════════════════════╝
```

### 4.8 메인메뉴 ↔ 그래픽 노블 상태 머신

```
MENU
├── NEW RUN          → CHARACTER_SELECT → CHAPTER → HUB → ...
├── GRAPHIC NOVEL    → GRAPHIC_NOVEL_MENU
│   ├── PROLOGUE (3 random)        → 12 scenes auto-play → SAVED_PROGRESS
│   ├── 케이 (Novice)              →  4 scenes auto-play → SAVED_PROGRESS
│   ├── 실 (Veteran)               →  4 scenes auto-play → SAVED_PROGRESS
│   ├── 카스 (Heretic)             →  4 scenes auto-play → SAVED_PROGRESS
│   └── BACK                       → MENU
├── CONTINUE        → (세이브 로드) → HUB
├── SETTINGS        → SETTINGS 화면
└── CREDITS         → CREDITS 화면

SAVED_PROGRESS (= 종료 화면)
├── 다른 캐릭터 보기 → GRAPHIC_NOVEL_MENU
├── 게임플레이 계속  → HUB
└── 메인메뉴         → MENU
```

## 5. 결과 (Consequences)

### 긍정적
- ✅ 메인메뉴 정체성 강화 (5 옵션, 게임 분위기 전달)
- ✅ 그래픽 노블 진입로 — 신규 유저 온보딩 개선
- ✅ 3 캐릭터 스토리를 자유롭게 시청 가능
- ✅ 세이브 진도 시각화 — 진행 회고
- ✅ 씬 단위 데이터 = 향후 콘텐츠 추가 용이
- ✅ Pillar 5 (깁슨 톤) — 비주얼 노블의 "mediated world" 정체성 강화

### 부정적
- ❌ 씬 데이터 12개 + 포트레잇 12개 + 배경 12개 (그리드 작업)
- ❌ `engine/graphic_novel_view.py` 신규 (~300 lines)
- ❌ `engine/menu.py` 확장 (~80 lines 추가)
- ❌ `engine/state.py` — `ScreenKind.GRAPHIC_NOVEL_MENU`, `GRAPHIC_NOVEL`, `SAVED_PROGRESS` 추가
- ❌ 테스트 30+ 추가 (씬 로더, 메뉴 분기, 자동 진행, 사운드 큐)

### 중립
- 씬 데이터는 게임 외부(`Fiction/derivative/.../scenes/`) 또는 게임 내부(`prototype/data/scenes/`)에 둘 수 있음
- AGENTS.md 룰 7 ("원작에 없는 사실의 무성한 단언") 준수 — 소설 인용만 사용
- ADR-0009 (meatspace 미표시) — 모든 씬이 *meatspace*지만 ASCII로만 표시 (text-based novel)
  - 단, 사용자는 "실제 플레이한 세이브 진도"를 요청 → meatspace 정보 (자키/등급/미션) 표시 필요
  - 해결: 자키 정보는 "디지털 자키 카드로" 표현 (meatspace 직설 묘사 회피)

## 6. 열린 질문 (Open Questions)

1. **씬 데이터 위치**: `prototype/data/scenes/` (게임) vs `Fiction/derivative/.../scenes/` (fiction 영역)
   - 권장: `prototype/data/scenes/` (게임이 소유, fiction은 원작 단편만)
2. **포트레잇 형식**: 현재 ASCII 글리프 (`art:case_think`) vs Box-drawing 큰 포트레잇 (10x16)
   - 권장: 10x16 박스 (의미 있는 크기)
3. **사운드 큐**: 각 씬 시작 시 1~2개 사운드 재생 (현재 audio 시스템 활용)
4. **그래픽 노블 후 게임플레이 전환**: "그래픽 노블 → 해당 캐릭터로 NEW RUN" 또는 "그래픽 노블은 시청 전용"?
   - 권장: 시청 전용. NEW RUN은 별도.

## 7. 열린 결정 사항

- [ ] 씬 데이터 위치 (게임 vs fiction)
- [ ] 포트레잇 크기 (10x16 vs 6x10)
- [ ] 사운드 큐 정책 (각 씬 시작 vs 대사별)
- [ ] 그래픽 노블 → NEW RUN 연결 여부

## 8. 다음 단계

사용자 결정 후:
1. **Phase 1**: 디자인 문서 (`design/scenario/graphic-novel.md`)
2. **Phase 2**: 씬 데이터 12개 (3 캐릭터 × 4 씬) + 포트레잇 12개 + 배경 12개
3. **Phase 3**: `engine/graphic_novel_view.py` + `engine/menu.py` 확장 + `engine/state.py` ScreenKind 추가
4. **Phase 4**: 세이브 진도 조회 모듈 (`engine/save_progress.py`)
5. **Phase 5**: 테스트 30+ (씬 로더, 메뉴 분기, 자동 진행, 사운드 큐, 세이브 연동)
6. **Phase 6**: 데모 `scripts/graphic_novel.py` — 풀 씬 시연
7. **Phase 7**: 메타 문서 동기화 (index/log/ROADMAP)

## 9. 참고

- `decisions/0031-original-scenario-integration.md` — 캐릭터 ↔ 단편 매핑
- `decisions/0009-story-news-system.md` — meatspace 미표시 원칙
- `decisions/0011-ascii-portraits.md` — ASCII Portrait 시스템
- `decisions/0019-combat-aftermath-subtitles.md` — 4-importance + 7인물 반응
- `engine/original_story.py` — 캐릭터 3명 + 챕터 3개
- `engine/chapter_view.py` — 단일 씬 타이핑 (그래픽 노블의 기반)
- `engine/menu.py` — 현재 메인메뉴 (확장 대상)
- `engine/save_manager.py` — 세이브 로드 (진도 조회 대상)
- `data/story/chapters/*.json` — 3 챕터 데이터
- `dashboard/` — 추후 graphic-novel.html 대시보드 가능

## 10. 작업 규모 추정

| 항목 | 라인/수 |
| --- | --- |
| 씬 데이터 | 12 JSON × ~50 lines = ~600 |
| 포트레잇 | 12 × ~30 lines ASCII = ~360 |
| 배경 아트 | 12 × ~25 lines ASCII = ~300 |
| `graphic_novel_view.py` | ~350 lines |
| `menu.py` 확장 | +80 lines |
| `state.py` 확장 | +30 lines |
| `save_progress.py` | ~80 lines (신규) |
| 테스트 | 30+ tests × ~20 lines = ~600 |
| **총 작업량** | **~2,400 lines + ASCII 아트** |
| **예상 소요** | **3~4 세션** |

## 결과 (Consequences)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 Accepted 로 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `engine/{graphic_novel_view,gn_menu,gn_render}.py` (총 ~50KB) — 7 옵션 메인메뉴 (ADR-0032 + ADR-0040 + Phase 7) + 81 GN 씬 자동재생. 단편→엔딩 통합.ADR-0083 (시청 시간 GN 진행) 포함.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).

# Graphic Novel Mode (그래픽 노블 자동플레이 모드)

> **이 문서는 [`../../decisions/0032-graphic-novel-mode.md`](../../decisions/0032-graphic-novel-mode.md)의 디자인 명세.**
> 메인메뉴 7 옵션 (Phase 7 + ADR-0040) + Phase 17 옵트인 [8] STATS + 그래픽 노블 자동플레이 + 세이브 진도 회고.
>
> **Phase 19 audit (2026-08-13)**: 7-option menu (was 5), ADR-0043 audio + ADR-0044 GN save, TELEMETRY_STATS menu cross-reference.

## 1. 개요

게임 시작 시 메인메뉴에서 진입 가능한 **비주얼 노블 스타일 자동플레이 모드**.
- **3 캐릭터의 씬을 랜덤 순서로 재생** (프롤로그 옵션)
- **각 씬 = 배경 아트 + 캐릭터 포트레잇 + 대사 + 사운드 큐 + 자동 진행**
- **종료 후 세이브 진도 카드 표시** (자키/등급/미션)
- **다른 캐릭터 스토리 보기 옵션** 제공

## 2. 메인메뉴 (확장)

### 2.1 화면 구성

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄                 ║
║            ▌                                ▐                 ║
║            ▌     R O G U E L I K E         ▐                 ║
║            ▌         S P R A W L           ▐                 ║
║            ▌                                ▐                 ║
║            ▌  ───────────────────────────   ▐                 ║
║            ▌  A cyberpunk roguelike based  ▐                 ║
║            ▌    on Gibson's Sprawl trilogy ▐                 ║
║            ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀                 ║
║                                                              ║
║   > [1] N E W   R U N         ─ 자키 선택부터 시작          ║
║     [2] G R A P H I C   N O V E L ─ 스토리 자동재생        ║
║     [3] C O N T I N U E        ─ 마지막 세이브 (없음)       ║
║     [4] S E T T I N G S                                    ║
║     [5] C R E D I T S                                       ║
║                                                              ║
║   v0.5.0 · Phase 5 Vertical Slice                           ║
║   [ENTER] Select  [Q] Quit                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 2.2 옵션 명세 (Phase 7 — 7 옵션)

> **Phase 7 갱신 (ADR-0032 + ADR-0040 + HELP)**: 5 옵션 → 7 옵션 확장. Hall of Dead (ADR-0040) + HELP (온보딩) 추가.

| # | 라벨 | 동작 | 조건 |
| --- | --- | --- | --- |
| 1 | NEW RUN | CHARACTER_SELECT 진입 | 항상 |
| 2 | GRAPHIC NOVEL | GRAPHIC_NOVEL_MENU 진입 | 항상 |
| 3 | CONTINUE | 세이브 슬롯 1 로드 → HUB | 세이브 있을 때만 활성 |
| 4 | SETTINGS | SETTINGS 화면 | 항상 |
| 5 | CREDITS | CREDITS 화면 | 항상 |
| 6 | HALL OF DEAD | 자키 아카이브 (사망한 자키 목록) | ADR-0040, 항상 |
| 7 | HELP | 조작법 / 컨셉 도움말 | Phase 7 온보딩, 항상 |
| 8 | STATS | TELEMETRY_STATS 집계 화면 | `state.telemetry_opt_in == True` 일 때만 (Phase 17, ADR-0184) |

## 3. 그래픽 노블 메뉴

### 3.1 화면 구성

```
╔══════════════════════════════════════════════════════════════╗
║            GRAPHIC NOVEL MODE                                ║
║   "깁슨의 스프롤 3부작을 비주얼 노블로"                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   > [1] P R O L O G U E  ─ 3명의 진행 (랜덤 순서)           ║
║       케이/실/카스의 4 씬씩, 무작위 셔플로 재생              ║
║       매 플레이마다 다른 인트로를 경험                       ║
║                                                              ║
║     [2] 케이 (K) — Novice                                    ║
║         "잭아웃 후 30초" 4 씬                                ║
║                                                              ║
║     [3] 실 (Sil) — Veteran                                   ║
║         "루이지아나의 신" 4 씬                                ║
║                                                              ║
║     [4] 카스 (Kas) — Heretic                                 ║
║         "매나리사의 자정" 4 씬                                ║
║                                                              ║
║     [5] BACK TO MAIN MENU                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## 4. 씬 구조 (12 씬)

### 4.1 캐릭터별 씬 목록

| 캐릭터 | 씬 1 (도입) | 씬 2 (전개) | 씬 3 (절정) | 씬 4 (결말) |
| --- | --- | --- | --- | --- |
| **케이 (Novice)** | CHATTO'S 24/7 (지바 호수텔) | JACK-IN (Ono-Sendai 데크) | JACK-OUT (30초 후) | THE FINN'S OFFICE (핀의 의뢰) |
| **실 (Veteran)** | LOUISIANA 11 (Maison de Loa) | THE MASK (Wigan의 loa) | T-A PAYROLL (Tessier-Ashpool) | THE BROADCAST (Mara의 죽음) |
| **카스 (Heretic)** | MANARASE MIDNIGHT (Shibuya 택시) | SALLY (Sally Shearer) | THE DECLARATION (Loa 네트워크) | THE WHEEL (바퀴는 돌아간다) |

### 4.2 씬 데이터 구조

`data/scenes/{character}/{scene_id}.json`:
```json
{
  "id": "scene_case_intro",
  "character": "novice",
  "order": 1,
  "title_en": "CHATTO'S 24/7",
  "title_ko": "챠토 24/7",
  "background": "art:bg_chat_room",       // 80x40 ASCII (optional inline)
  "portrait_left": "art:case_think",      // 10x16 ASCII
  "portrait_right": null,                 // 한 명만 등장 시 null
  "dialogue": [
    {
      "speaker": "case",
      "speaker_ko": "케이",
      "portrait": "art:case_think",
      "text_en": "30 seconds. The Ono-Sendai electrodes lift from my scalp...",
      "text_ko": "30초. Ono-Sendai 전극이 두피에서 떨어진다. 내 손가락은 여전히 키를 두드리고 있었다.",
      "duration_ms": 8000
    }
  ],
  "next_scene": "scene_case_jackin"
}
```

### 4.3 씬 1프레임 화면 레이아웃

```
┌──────────────────────────────────────────────────────────────┐
│ 1/12   CHATTO'S 24/7  ·  CASE            [SKIP] [PAUSE]      │ ← Top bar
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────┐                                                  │
│  │        │                                                  │
│  │  ◉P◉   │        30 seconds.                              │
│  │        │        The Ono-Sendai electrodes                 │
│  │   ▎    │        lift from my scalp and                    │
│  │   ▎    │        my fingers keep typing.                   │
│  │   ▎    │                                                  │
│  │   ▎    │                                                  │
│  │   ▎    │        "Chiba. 11th level.                      │
│  │        │         The room smells of                       │
│  │        │         old circuits."                           │
│  │        │                                                  │
│  └────────┘                                                  │
│                                                              │
│  ╔════════════════════════════════════════════════════════╗ │
│  ║ "30초. Ono-Sendai 전극이 두피에서 떨어진다..."         ║ │ ← Dialogue box
│  ║                                                          ║ │   (5 lines)
│  ║   [auto 8s]   [ENTER] next   [S] skip   [ESC] menu      ║ │ ← Controls
│  ╚════════════════════════════════════════════════════════╝ │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ← Progress
└──────────────────────────────────────────────────────────────┘
```

### 4.4 사운드 큐

| 씬 | 사운드 |
| --- | --- |
| CHATTO'S 24/7 | `chiba_rain_loop` (배경) |
| JACK-IN | `jack_in_zap` (전극 분리) |
| JACK-OUT | `jack_out_buzz` (데이터 정적) |
| LOUISIANA 11 | `loa_drum` (부두 북소리) |
| MANARASE MIDNIGHT | `shibuya_traffic` (도쿄 시내) |
| ... | ... |

## 5. 자동 진행 정책

### 5.1 키 매핑

| 키 | 동작 |
| --- | --- |
| (자동) | 대사 duration_ms 후 다음 대사 → 다음 씬 |
| `Enter` / `Space` | 현재 대사 즉시 완료 → 다음 |
| `→` (Right) | 현재 씬 즉시 스킵 → 다음 씬 |
| `S` | Skip (현재 씬 종료) |
| `P` | Pause / Resume (배경 사운드 일시정지) |
| `Esc` / `Q` | 그래픽 노블 종료 → 종료 화면 |

### 5.2 타이밍

| 항목 | 기본값 | 조정 가능 |
| --- | --- | --- |
| 대사 표시 (50ms/char) | 자동 | Settings > Animation Speed |
| 대사 duration_ms | 5000~10000 | 데이터 |
| 씬 전환 페이드 | 200ms | 고정 |
| 자동 진행 (대사 후) | 1초 후 다음 | 고정 |

## 6. 종료 화면 (Saved Progress Card)

### 6.1 세이브 있을 때

```
╔══════════════════════════════════════════════════════════════╗
║              > 당신의 자키 <                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   ◉P◉                                                       ║
║   ┌────┐   자키: 실 (Sil) — Veteran                          ║
║   │ ◆P◆   등급: 3-up                                        ║
║   │      미션 완료: 12 / 30 (40%)                            ║
║   └────┘   데이터 회수: 234 / 500                            ║
║            마지막 의뢰: "watchdog_patrol"                    ║
║            마지막 위치: Tessier-Ashpool 본부                  ║
║                                                              ║
║   > [1] 다른 캐릭터 스토리 보기                              ║
║     [2] 게임플레이 계속 (HUB)                                ║
║     [3] 메인메뉴                                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 6.2 세이브 없을 때

```
╔══════════════════════════════════════════════════════════════╗
║              > 아직 자키가 없습니다 <                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║        세이브 파일이 없습니다.                               ║
║        NEW RUN으로 시작해 보세요.                            ║
║                                                              ║
║   > [1] NEW RUN                                             ║
║     [2] 다른 캐릭터 스토리 보기                              ║
║     [3] 메인메뉴                                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## 7. 상태 머신

```
MENU
├── [1] NEW RUN
│   └── CHARACTER_SELECT → CHAPTER → HUB → MATRIX → ...
├── [2] GRAPHIC NOVEL
│   ├── [1] PROLOGUE (random)         ← 9 캐릭터 × 4 씬 = 36 scenes
│   ├── [2] 케이 (Novice)             ← 4 scenes
│   ├── [3] 실 (Veteran)              ← 4 scenes
│   ├── [4] 카스 (Heretic)            ← 4 scenes
│   └── [5] BACK                      → MENU
├── [3] CONTINUE                       (세이브 있을 때만)
│   └── 세이브 로드 → HUB
├── [4] SETTINGS
└── [5] CREDITS

GRAPHIC_NOVEL
├── 자동 진행 / Enter / Skip / Esc
├── 씬 1 → 씬 2 → ... → 마지막 씬
└── 종료 → SAVED_PROGRESS

SAVED_PROGRESS
├── [1] 다른 캐릭터 보기  → GRAPHIC_NOVEL_MENU
├── [2] 게임 계속        → HUB (세이브 있을 때만)
└── [3] 메인메뉴         → MENU
```

## 8. 데이터 디렉토리

```
prototype/data/
├── scenes/                          ← NEW
│   ├── case/
│   │   ├── 01_chattos.json          ← CHATTO'S 24/7
│   │   ├── 02_jackin.json           ← JACK-IN
│   │   ├── 03_jackout.json          ← JACK-OUT
│   │   └── 04_finn.json             ← THE FINN'S OFFICE
│   ├── sil/
│   │   ├── 01_louisiana.json        ← LOUISIANA 11
│   │   ├── 02_mask.json             ← THE MASK
│   │   ├── 03_payroll.json          ← T-A PAYROLL
│   │   └── 04_broadcast.json        ← THE BROADCAST
│   └── kas/
│       ├── 01_manarase.json         ← MANARASE MIDNIGHT
│       ├── 02_sally.json            ← SALLY
│       ├── 03_declaration.json      ← THE DECLARATION
│       └── 04_wheel.json            ← THE WHEEL
├── portraits/                       ← existing
└── ...
```

## 9. ASCII 아트 자산 (NEW)

### 9.1 배경 (12개, 80x40)

| 씬 ID | ASCII (요약) |
| --- | --- |
| bg_chat_room | 호수텔 방, 콘솔 테이블, Hosaka, 화면 |
| bg_cyberspace_7 | Ono-Sendai 데크 이미지, 회로도 |
| bg_jackout_30s | 30초 카운트다운, 데이터 정적 |
| bg_finn_office | 핀의 지하 사무실, 책상, 핀의 얼굴 |
| bg_maison_loa | 부두 가게, 마스크 5개, 노파 |
| bg_loa_channel | Wigan의 loa 마스크, 73 Eridani |
| bg_ta_payroll | T-A 본부, 데이터 노드, Hammer ICE |
| bg_broadcast | 3년 전 Mara의 죽음, 폭로 화면 |
| bg_manarase | Shibuya 택시, 매나리사 클럽 입구 |
| bg_sally | Sally의 가죽, 데이터 전송 |
| bg_loa_network | Loa 네트워크 트리, Sense/Net 코어 |
| bg_industrial | 산업 = 자본 = 바퀴, 야나카 패밀리 |

### 9.2 포트레잇 (12개, 10x16)

| ID | 캐릭터 | 표정 | ASCII (요약) |
| --- | --- | --- | --- |
| case_think | 케이 | 사색 | 정면, 눈 약간 감김 |
| case_hands | 케이 | 손 떨림 | 측면, 손 떨림 |
| case_terminal | 케이 | 단자 응시 | 측면, 화면 응시 |
| case_decision | 케이 | 결심 | 정면, 눈 크게 |
| marly_mask | 실 | 마스크 | 마스크 쓴 얼굴 |
| marly_smile | 실 | 미소 | 정면, 약한 미소 |
| marly_data | 실 | 데이터 | 데이터 흐름 응시 |
| marly_fire | 실 | 결의 | 정면, 결의 |
| kumiko_taxi | 카스 | 택시 안 | 정면, 차 안 |
| kumiko_sally | 카스 | Sally 응시 | 측면, Sally 응시 |
| kumiko_decl | 카스 | 선언 | 정면, 큰 글리프 |
| kumiko_wheel | 카스 | 바퀴 | 측면, 회전 모티프 |

## 10. 의존성

- `engine/chapter_view.py` (ADR-0031) — 단일 씬 타이핑 기반
- `engine/save_manager.py` (ADR-0044 GN Save) — 세이브 로드 (진도 조회)
- `engine/state.py` — `ScreenKind.GRAPHIC_NOVEL_MENU`, `GRAPHIC_NOVEL`, `SAVED_PROGRESS` 추가
- `engine/audio/sound_manager.py` — 씬별 사운드 큐
- `data/portraits/portraits.json` — 기존 포트레잇 자산

## 11. 완료 조건 (Acceptance Criteria)

### Phase 0: ADR
- [x] `decisions/0032-graphic-novel-mode.md` (Draft)

### Phase 1: 디자인
- [x] `design/scenario/graphic-novel.md` (이 문서)

### Phase 2: 씬 데이터
- [ ] `data/scenes/case/*.json` 4개
- [ ] `data/scenes/sil/*.json` 4개
- [ ] `data/scenes/kas/*.json` 4개
- [ ] 배경 ASCII 12개 (또는 inline)
- [ ] 포트레잇 ASCII 12개

### Phase 3: 엔진
- [ ] `engine/graphic_novel_view.py` (신규, ~350 lines)
  - `SceneData`, `load_scene()`, `load_scene_chain()`
  - `render_scene()`, `tick_scene()`
  - 자동 진행 로직 + 키 핸들러
- [ ] `engine/menu.py` 확장
  - 5 옵션 메뉴, GRAPHIC_NOVEL_MENU 진입
- [ ] `engine/state.py` ScreenKind 추가
  - `GRAPHIC_NOVEL_MENU`, `GRAPHIC_NOVEL`, `SAVED_PROGRESS`
- [ ] `engine/save_progress.py` (신규, ~80 lines)
  - `get_saved_progress_summary()` — 자키/등급/미션 요약

### Phase 4: 세이브 연동
- [ ] `engine/save_manager.py`에 `progress_summary()` 메서드 추가 (또는 `save_progress.py` 신규)
- [ ] `SAVED_PROGRESS` 화면이 세이브 데이터 기반으로 렌더

### Phase 5: 테스트 (30+)
- [ ] 씬 로더 (`test_scene_loader.py`) — 10 tests
- [ ] 씬 체인 (`test_scene_chain.py`) — 8 tests
- [ ] 그래픽 노블 뷰 (`test_graphic_novel_view.py`) — 12 tests
- [ ] 메뉴 분기 (`test_menu.py` 확장) — 5 tests
- [ ] 세이브 진도 (`test_save_progress.py`) — 5 tests

### Phase 6: 데모
- [ ] `scripts/graphic_novel.py` — 풀 씬 시연 (옵션: --character, --shuffle, --duration)
- [ ] `make all` 그린 (lint + typecheck + test)

### Phase 7: 메타 문서
- [ ] `index.md` 갱신 (GRAPHIC_NOVEL_MENU 디자인 링크)
- [ ] `decisions/README.md` 갱신 (ADR-0032)
- [ ] `log.md` 갱신
- [ ] `ROADMAP.md` 갱신
- [ ] `dashboard/graphic-novel.html` (신규, 씬 미리보기)

## 12. 의존성 그래프

```
┌────────────┐
│ ADR-0032   │  ← 이 문서
└────┬───────┘
     │ depends on
     ├──> ADR-0031 (Original Scenario)  ← 캐릭터/챕터 정의
     ├──> ADR-0044 (GN Save)          ← 진도 조회
     ├──> ADR-0009 (Story/News)         ← meatspace 미표시
     ├──> ADR-0011 (ASCII Portraits)    ← 포트레잇 시스템
     └──> ADR-0019 (Aftermath)          ← 4-importance
```

## 13. 다음 단계

사용자 결정 후:
1. 씬 데이터 12개 + 포트레잇 12개 + 배경 12개 (그리드 작업)
2. `engine/graphic_novel_view.py` 구현
3. `engine/menu.py` 5 옵션 확장
4. `engine/save_progress.py` 신규
5. 테스트 30+ 추가
6. `scripts/graphic_novel.py` 데모
7. `dashboard/graphic-novel.html` (대시보드)
8. 메타 문서 동기화

---

## 10. 콘텐츠 톤 가이드라인 (ADR-0041)

ADR-0041 (씬 콘텐츠 확장) — 깁슨 스프롤 톤을 보존하면서 페이지 호흡을 살리기 위한 가이드.

### 10.1 목표 길이

| 항목 | 이전 | 목표 |
|---|---|---|
| dialogue 평균 | 110자 | **300-500자** |
| dialogue 범위 | 50-160자 | 250-600자 |
| 씬당 dialogue | 3-4개 | 3-4개 (그대로) |
| 씬당 총 길이 | 350자 | **1200-1600자** |
| 페이지 분량 | 1 page | **2-3 pages** (자동 페이지네이션 활용) |

### 10.2 톤 (Tone)

깁슨 원작의 핵심 톤:
- **Cold / detached**: 캐릭터는 감정보다 *상황*에 반응한다
- **Cinematic**: 짧은 문장 + 긴 묘사의 교차
- **Industrial**: 기업 이름 (Tessier-Ashpool, Maas, Sense/Net, Hosaka, Ono-Sendai)
  이 배경음처럼 등장
- **Fragment 문장 OK**: "He was a console cowboy. The sprawl was his church."
- **Sensory details**: 시각 외 후각/촉각/청각 묘사 (smell of circuits, rain on glass)

### 10.3 캐릭터 voice profile

| 캐릭터 | 톤 | 어휘 | 예시 |
|---|---|---|---|
| **Case (novice)** | Jaded, ironic, self-deprecating | deck, jack, flatline, ICE, wetware | "Thirty seconds. The Ono-Sendai electrodes lift from my scalp and my fingers keep typing." |
| **Marly (veteran)** | Quiet, deliberate, gallery curator | data, matrix, T-A, Mara | "Behind the glass. Behind the mask. Behind the data." |
| **Kumiko (heretic)** | Ritualistic, formal, declarative | wheel, Loa, casting, Tessier-Ashpool | "I am Kas. Maelcum sent me. I cast you out." |
| **narrator** | Cold camera, omnipresent | (any; view-only) | "Chiba. Eleventh level. The room smells of old circuits." |

### 10.4 Narration vs Dialogue

- **Narrator**: 시점 묘사, 환경, 분위기, 분위기 전환. 1인칭 시점 (캐릭터 의식 흐름 아님)
- **Character dialogue**: 캐릭터 목소리, 단언, 결정. fragment OK
- **혼합 금지**: 한 dialogue 안에서 narrator가 캐릭터 의식을 읽지 않음 (냉정함 유지)

### 10.5 작성 규칙

1. **첫 문장은 hook**: "30 seconds. The Ono-Sendai electrodes lift..." — 즉시 상황 / 시간 제시
2. **마지막 문장은 비트로 끝**: 완결하지 않고 다음 dialogue로 호흡 넘김
3. **Sensory detail 1개 이상**: smell, sound, touch, sight
4. **산업 이름 1개 이상** (해당 씬에서 자연스러우면): T-A, Sense/Net, Maas, Hosaka, Ono-Sendai, Neuromancer
5. **번역 가이드**: 영문 작성 → 한글 자막 동기화 (ADR-0010)

### 10.6 안티패턴 (피할 것)

- ❌ 설명적 monologue ("I was feeling sad because...")
- ❌ 직접 감정 표현 ("happy", "angry")
- ❌ 멜로드라마 ("I will never forget...")
- ❌ 현대 인터넷 meme, Cyberpunk 2077 용어, D&D 클래스
- ❌ 원문에 없는 사실 단언 ("Gibson에 따르면...")
- ❌ 과도한 설명 (소설이 아니라 광고 카피)

---

## 11. 엔딩 구조 (A / B) — ADR-0046

각 캐릭터는 **2가지 결말** 을 가짐:

### 엔딩 A (기본) — 모든 캐릭터 공통: 행동으로 답하다
| 캐릭터 | 엔딩 A |
|---|---|
| Case | Finn 의뢰 수락, Sense/Net 데이터 탈취, Chiba로 귀환 |
| Marly | Tessier-Ashpool 데이터 브로드캐스트, 복수 |
| Kumiko | Loa 네트워크에 wheel 캐스팅, 가족 선언 |

### 엔딩 B (대안) — 각 캐릭터의 다른 선택
| 캐릭터 | 엔딩 B | 원작 매핑 |
|---|---|---|
| **Case** | **Refusal** — 의뢰 거부, console cowboy 은퇴 | Neuromancer 후반 |
| **Marly** | **Contract** — Tessier-Ashpool 내부자, 데이터 검사자 | Count Zero |
| **Kumiko** | **Silence** — Loa 거부, 가족 승리 묵인, 떠남 | Mona Lisa Overdrive |

### 씬 JSON 구조
```json
{
  "id": "scene_case_refusal",
  "character": "novice",
  "order": 5,
  "ending": "B",
  "title_en": "THE REFUSAL",
  ...
}
```

### 메뉴 옵션
```
[1] CONTINUE READING (saved)
[2] PROLOGUE — 3 random
[3] CASE (Novice)
[4] MARLY (Veteran)
[5] KUMIKO (Heretic)
[6] CASE — ENDING B (Refusal)
[7] MARLY — ENDING B (Contract)
[8] KUMIKO — ENDING B (Silence)
[9] BACK TO MAIN MENU
```

### 로드 시그니처
```python
load_scene_chain(scenes_dir, character, *, shuffle=False, seed=None, ending="A")
```

### 그래픽 노블 저장
`GNProgress` 에 `ending: str = "A"` 필드 추가.

---

## 12. Phase 15-17 교차 기능 (2026-08-13 audit)

그래픽 노블 모드는 게임 메인 흐름과 직교로 동작하지만, Phase 15-17 사이클에서 추가된 일부 시스템과 *상태/저장* 레이어에서 연결된다.

### 12.1 ADR-0043 — Scene Sound Cue

`engine/graphic_novel_audio.py` (orphan module, ADR-0043). 씬 전환 시 사운드 큐 트리거 (`data/sounds/*.wav`, 46개 자동 생성 사운드). 본 자동플레이 모드는 별도 사운드 카드 (`bg_chat_room` rain, `jack_in_zap`, `jack_out_buzz` 등) 로 분리 — 일반 게임 사운드와 격리.

### 12.2 ADR-0044 — GN Save / Restore

`engine/graphic_novel_save.py` (ADR-0044). 3 슬롯 (`data/saves/gn_progress_slot_{1,2,3}.json`) + legacy `gn_progress.json` 마이그레이션. *이어서 보기* 옵션이 메인메뉴 [3] CONTINUE 와 직교 — GN 슬롯은 *auto-play 진행률*, 메인 슬롯은 *gameplay 진행률*.

### 12.3 Ending Choice 영속성 (ADR-0192 + Phase 16)

`AppState.ending_choice` (엔딩 A/B/C, 게임플레이 flow) 와 `GNProgress.ending` (그래픽 노블 데이터) 는 *별도 필드*:

- `state.ending_choice` — gameplay flow 가 도달한 엔딩 (예: "A"). `engine/save_manager.py::SaveManager._serialize_metadata()` 가 save metadata 에 직렬화, `restore_state()` 가 복원 (Phase 16).
- `GNProgress.ending` — 사용자가 GN 메뉴에서 *시청할* 엔딩 변종 (예: "A" / "B"). ADR-0048 + ADR-0049.

그래픽 노블 메뉴에서 옵션 [6][7][8] (엔딩 B/C 변종) 진입 시 `GNProgress.ending` 사용. 메인 게임 엔딩 직후 *GN ending 자동 재생* 시에는 `state.ending_choice` 값을 fallback 으로 사용.

### 12.4 TELEMETRY_STATS 메뉴 (Phase 17, ADR-0184)

`ScreenKind.TELEMETRY_STATS` (메인메뉴 [8]). 메인메뉴에서 사용자가 `state.telemetry_opt_in == True` 일 때만 노출. 그래픽 노블 자체는 telemetry 이벤트 (`record_deck_chosen`, `record_run_completed`) 를 발생시키지만, *모드 자체* 는 STATS 화면 표시와 무관 — 별도 메뉴.

### 12.5 Deck Size 선택 (Phase 15, ADR-0178)

`state.deck_size: str = "standard"` (light / standard / heavy). 그래픽 노블 진입 *이전* — 즉 메인메뉴 [1] NEW RUN 진입 후 CHARACTER_SELECT 직전 — DECK_SELECT 화면에서 LIGHT/STANDARD/HEAVY 3 옵션 중 선택. GN 자동플레이는 *deck_size 와 무관* — 자동 재생 모드이므로 PPL / ZDR fight 가 없음.

### 12.6 Wetware Stacking (Phase 15, ADR-0173)

`equipment/wetware_stacking.py::stack_wetware()` — 6 슬롯 wetware 누적 효과. 그래픽 노블 자동재생 모드에서는 *장비 시스템 자체가 skip* — 자키는 prologue scene 의 기본 wetware 1 슬롯만 사용.

### 12.7 F.4 Boss Phase Transitions (Phase 17, ADR-0149)

`combat/boss_phase_tracker.py` + `combat/state_models.py::CombatState.phase_change_ms / phase_change_color`. 1.5초 phase transition blend — 보스 HP 70% / 40% / 15% threshold. 그래픽 노블은 *combat 자체가 없으므로* 영향 없음. 단, 화면 *연출* 측면에서 GN 종료 후 전투 진입 시 첫 phase transition 이 더 부드럽게 표시됨.

### 12.8 Random Rules UI Annotation (Phase 17, ADR-0188)

`engine/hub.py` 의 *Hub 사이드 패널* 에 `state.last_rule_id` 기반 추천 미션 annotation ("recommended by zone rep"). 그래픽 노블 진입 시점에는 *rule_id 가 reset* — 사용자가 *임의 미션* 그래픽 노블을 본 후 게임 복귀 시, 다시 rule 이 적용된 추천 mission 이 표시됨.

### 12.9 Hardcore Mode (Phase 14, ADR-0140)

`state.hardcore_mode` (1-life permadeath). 그래픽 노블 자동재생은 *무관* — GN 자체에는 메인 흐름의 revival / run 사이클이 없음. 단, Hardcore + Main Menu [6] HALL_OF_DEAD 동작 확인용으로 GN 진입 후 즉시 메인메뉴 복귀 시 정상 동작.

---

## 13. 의존성 그래프 (갱신)
```
┌────────────┐
│ ADR-0032   │  ← 이 문서
└────┬───────┘
     │ depends on
     ├──> ADR-0031 (Original Scenario)  ← 캐릭터/챕터 정의
     ├──> ADR-0044 (GN Save)          ← 진도 조회
     ├──> ADR-0009 (Story/News)         ← meatspace 미표시
     ├──> ADR-0011 (ASCII Portraits)    ← 포트레잇 시스템
     ├──> ADR-0040 (Death Cycle)        ← Hall of Dead 메뉴 [6]
     ├──> ADR-0043 (Sound Cue)          ← 씬별 WAV
     ├──> ADR-0044 (GN Save)            ← 3 슬롯 + 이어서 읽기
     ├──> ADR-0046-0049 (Ending B/C)    ← 9 결말 조합
     ├──> ADR-0140 (Hardcore Mode)      ← 1-life permadeath (Phase 14)
     ├──> ADR-0149 (Boss Phase 4)       ← 보스 phase transition (Phase 17)
     ├──> ADR-0173 (Wetware)            ← 6 슬롯 (Phase 15 — GN 외)
     ├──> ADR-0178 (Deck Building)      ← LIGHT/STANDARD/HEAVY (Phase 15)
     ├──> ADR-0184 (Telemetry)          ← TELEMETRY_STATS (Phase 17)
     ├──> ADR-0188 (Mission Expansion)  ← Random Rules UI (Phase 17)
     ├──> ADR-0192 (Ending Expansion)   ← ending_choice 영속성 (Phase 16)
     └──> ADR-0019 (Aftermath)          ← 4-importance
```

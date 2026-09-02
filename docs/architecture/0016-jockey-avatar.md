# ADR-0016: Jockey Avatar (자키 아바타 — 스탯 시각화)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0002 (Pure ASCII), ADR-0008 (Progression), ADR-0011 (Portraits), ADR-0012 (PPL/ZDR), ADR-0014 (Data Salvage)

## 컨텍스트

사용자 결정 (2026-06-18):
> "현재 stat 을 직관적으로 알 수 있도록 표현할 방법을 찾아봐. 도형이나 아바타 객체의 부분들을 채우고 교체하는 방식도 좋아."

요구:
- 직관적인 stat 표현
- 도형/아바타의 부분 채우기/교체
- Pure ASCII 유지 (ADR-0002)

기존 표현:
- HP 바: `[▓▓▓▓▓░░░] HP 50/100` (전형적, 자키가 *수치*로 읽어야 함)
- HUD: `PPL: 6  ZDR: 7  Status: TOUGH` (텍스트, 즉시 파악 어려움)

## 고려한 옵션

### Option 1: Stick Figure Avatar — **선택**

플레이어 자키를 5-7행 ASCII 스틱 피규어로 표현. 머리(HP), 팔(programs), 몸통(deck), 다리(wetware).

**장점**:
- *한눈에* 전체 상태 파악
- 깁슨 톤: 자키 = 사람, 도구 = 팔다리
- Pure ASCII, 애니메이션 가능
- Pillar 5 정합: cyberpunk decker의 시각적 아이덴티티

**단점**:
- 처음 보는 사람에게 학습 필요
- 정보 밀도 낮음 (수치를 보고 싶으면 별도 HUD 필요)

### Option 2: Multi-Bar Deck Visualization

데크 외형에 HP/AP/BW/PW 4개 바가 *물리적으로* 표현. 깨진 데크 = 손상.

**장점**: 클래식, 즉시 이해.
**단점**: *자키*가 아니라 *데크*에 초점. Pillar 1 (자키의 무게) 약화.

### Option 3: Hybrid (Avatar + Mini Deck Panel)

둘 다 표시. 더 풍부한 정보.

**장점**: 다양한 stat 한눈에.
**단점**: 복잡, 화면 공간 차지.

## 사용자 결정

[x] **Option 1: Stick Figure Avatar** (2026-06-18)

## 결정

### Jockey Avatar 해부

5-7행 스틱 피규어. *부위별* stat 표현.

```
행 1:  ◉P◉       <- 머리 (HP)
행 2:  /|\        <- 몸통 (Status)
행 3: ★W★:H:|P:   <- 프로그램 팔 (각 슬롯)
행 4:  ║DK║       <- 데크 (Tier 표시)
행 5:  ▓▓▓        <- 웨웨어 (Tier)
```

### HP 표현 — 머리 무결성

머리의 *모양*이 HP를 나타냄. 깁슨 톤: 데크가 손상되면 *몸*이 글리치.

| HP 비율 | 모양 | 의미 |
| --- | --- | --- |
| 100% | `◉P◉` | 완전 무결 |
| 75% | `◉P·` | 약간 손상 |
| 50% | `◉P/` | 글리치, 기울어짐 |
| 25% | `◉Px` | 거의 flatline |
| 0% | `X` | dead |

### Programs 표현 — 팔 슬롯

각 program이 *한 팔*. *등급*이 *두께*로 표현. *소진* 상태도 표시.

**등급 (Tier)**:

| Tier | 모양 | 의미 |
| --- | --- | --- |
| T5 | `★W★` | starred, 최고 |
| T4 | `▓W▓` | filled, 강력 |
| T3 | `\|W\|` | double border |
| T2 | `:W:` | single border |
| T1 | `·W·` | faded, 기본 |

**상태**:

| 상태 | 모양 | 의미 |
| --- | --- | --- |
| 활성 | 위 grade 마커 | 사용 가능 |
| 소진 | `~W~` | 일회용 (예: Shield 사용 후) |
| 비어있음 | `   ` 또는 `─ ─` | 슬롯 비어있음 |

### Status Pose — 전체 자세

Status 비율에 따라 *자세*가 변함. 즉각적 시각 피드백.

| Status | 자세 | 의미 |
| --- | --- | --- |
| SAFE | 직립 | 압도적 |
| MATCH | 직립 (살짝 기운) | 균등 |
| TOUGH | 약간 웅크림 | 불리 |
| DEADLY | 엎드림, 글리치 | 위험 |
| FUTILE | 흐릿게 깜빡임 | 자살행위 |

### Deck & Wetware — 뿌리

- Deck: `║DK7║` (숫자 = tier, e.g. DK7 = Ono-Sendai 7 = T4)
- Wetware: `▓▓▓` (filled cells, tier에 비례)
- Construct: `◆D◆` (construct이 있으면 *주변에* echo, 별도 표시)

### 전체 Avatar (Full Loadout, PPL 25)

```
═══════════════════════════════════════
  ◉P◉
  /|\
 ★W★:H:|P:        <- 3 programs (T5, T2, T3)
  \|/
 ╔═══╗
 ║DK7║              <- T4 deck (Ono-Sendai 7)
 ╚═══╝
  ▓▓▓▓              <- T4 wetware
◆D◆                  <- Dixie construct (echo)
═══════════════════════════════════════
PPL: 25  HP: 100%  Status: SAFE
```

### 손상 상태 (50% HP, TOUGH)

```
═══════════════════════════════════════
  ◉P/                <- head tilted (50% HP)
  /|\
 ·W·:H:|P:          <- Wisp depleted (~W~ or ·W·)
  \|/
 ╔═══╗
 ║DK7║
 ╚═══╝
  ▓▓▓▓
═══════════════════════════════════════
PPL: 25  HP: 50%  Status: TOUGH
```

### 위기 상태 (25% HP, 1 program lost)

```
═══════════════════════════════════════
  ◉Px                <- head critical
  /|\
    :H:|P:           <- Wisp LOST (empty slot)
  \|/
 ╔═══╗
 ║DK7║
 ╚═══╝
  ▓▓▓▓
═══════════════════════════════════════
PPL: 17  HP: 25%  Status: DEADLY
```

### Data Salvage 통합 (ADR-0014)

HEAL 후 HP 회복 = 머리 무결성 회복:

```
HEAL before:           HEAL after (+20%):
  ◉P/                   ◉P·    <- head recovered
  /|\                   /|\
 ·W·:H:|P:             ·W·:H:|P:
```

PPL/ZDR 비교 = 전체 자세 결정.

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 자키 = *한 사람*의 무게. 아바타가 자키의 *현재 상태*를 보여줌.
- **P2 (The Matrix)**: 아바타는 cyberspace 안의 *자키 representation*. meatspace 인물 묘사 X (Pillar 2).
- **P3 (The Flatline)**: 0% HP = `X` (flatline), 시각적으로 명확.
- **P4 (The Build)**: *장비 변경*이 아바타 *시각적 변화*로 표현. 등급 시각화.
- **P5 (The Style)**: 깁슨 cyberpunk aesthetic, monospace, ASCII.

### 기존 ADR 영향

- **ADR-0002 (Pure ASCII)**: 보강. Avatar는 *ASCII art*의 한 형태.
- **ADR-0011 (Portraits)**: 보강. Avatar는 *확장된 portrait*.
- **ADR-0012 (PPL/ZDR)**: Status pose = ZDR/PPL 비율 시각화.
- **ADR-0014 (Data Salvage)**: HEAL 효과 = 머리 무결성 회복.

### 디자인 영향

- **`design/systems/avatar.md`** (신규) — 아바타 시스템 명세
- **`design/systems/hacking.md`** — Matrix 화면에 아바타 표시
- **`testcases/systems/avatar.md`** (신규) — TC-AVATAR-001~008
- **`data/portraits/portraits.json`** 확장 — avatar 상태별 정의

### 구현 영향 (Phase 6+)

- `engine/avatar.py` — `Avatar`, `render_avatar(console, x, y, player, status)`
- `engine/matrix_view.py` 확장 — 매트릭스 화면에 아바타 표시
- `engine/hub.py` 확장 — Hub 화면에 아바타 표시
- `data/portraits/portraits.json` 확장 — avatar 상태별 정의 (선택)

### Phase 5 범위

- **문서만**: Avatar 디자인 명세
- **구현 없음**: Phase 6+에서 렌더링

### Phase 6+ 범위

- Avatar 렌더링 (Hub + Matrix)
- HP / Status pose 동적 업데이트
- Program slot 동적 표시
- Tier 시각화 (·W· vs ★W★)
- Data Salvage 통합 (HEAL 효과)

## 영향 받는 항목

- `design/systems/avatar.md` (신규)
- `design/systems/hacking.md` (Matrix 표시)
- `design/GDD.md` (decided + core systems)
- `testcases/systems/avatar.md` (신규)
- `data/portraits/portraits.json` (선택적 확장)

## 관련 결정

- ADR-0002 (Accepted) — Pure ASCII
- ADR-0008 (Accepted, Revised) — Progression
- ADR-0011 (Accepted) — Portraits
- ADR-0012 (Accepted) — PPL/ZDR
- ADR-0014 (Accepted) — Data Salvage

## 변경 이력

- 2026-06-18: Draft 작성
- 2026-06-18: 사용자 결정 (Option 1: Stick Figure Avatar)

### Auto-conversion Confirmation (2026-08-05)

본 ADR은 사용자 결정 (질의 응답으로 confirm, 2026-08-05)에 의해 auto-convert 완료. 증거 기반 검증 통과.

**구현 증거 (2026-08-05)**: `avatar/` 패키지 3 .py 모듈 + `engine/jockey_history.py` (19KB). 자키 스탯 시각화 + Die/Restart cycle. AppState.reputation과 통합.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).

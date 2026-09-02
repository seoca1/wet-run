# ADR-0013: Story Events System (소설 스토리 이벤트)

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트

사용자 결정 (2026-06-17):

1. **소설 스토리를 부가 요소로 반영할 수 있는 이벤트** — 스프롤 3부작의 storyline을 게임에 통합
2. **이벤트를 통해 아이템 획득** — 보상
3. **이벤트를 통해 스킬 (program) 획득** — 보상
4. **부가 요소** — 메인 아크와 별개, 사이드 콘텐츠
5. **메인 줄기는 그대로** (ADR-0010) — 이벤트는 다양성 추가

기존 결정과의 관계:
- **ADR-0009 (Story/News)** — Story Archive는 텍스트 위주. 이벤트 = 인터랙티브.
- **ADR-0010 (Content Pipeline)** — 데이터 주도. 이벤트는 데이터 파일.
- **ADR-0008 (Item Tier)** — 보상이 티어 시스템 따름.
- **ADR-0012 (PPL/ZDR)** — 이벤트의 일부 = skill check.

## 결정

### Story Events System

**핵심 컨셉**:
- 스프롤 3부작의 storyline을 게임 이벤트로 변환
- 이벤트는 **부가 콘텐츠** (메인 아크와 별개)
- 보상 = **아이템 / program / construct** 등
- Pillar 2, 9 (meatspace 미표시, Story Archive) 준수

#### Event Types (6 가지)

| Type | 설명 | 보상 |
| --- | --- | --- |
| **1. Construct Contact** | construct가 자키에게 접근 | construct unlock (메타) / fragment (런 내) |
| **2. Rare Program Discovery** | 강력한 program 발견 | 고티어 program |
| **3. Item Discovery** | 희귀한 데이터 / artifact | 장비 / 데이터 |
| **4. Vision / Lore** | 매트릭스 본질에 대한 통찰 | Story Archive entry |
| **5. Contact from Above** | 위에서 메시지 / 지시 | tip, hint, item, mission |
| **6. Combat Event** | 적대적 자키 / ICE trap 만남 | 승리 시 items, programs |

#### Event Examples (Sprawl 3부작)

| Event | 출처 | Type | Reward |
| --- | --- | --- | --- |
| "Dixie's Offer" | Neuromancer | Construct Contact | Dixie unlock (meta) |
| "Burning Chrome" | short story | Rare Program | Kraken-tier program |
| "Voodoo Loa" | Count Zero | Vision / Construct | construct fragment / vision |
| "Molly's Razor" | Neuromancer | Rare Program | unique program (razor) |
| "T-A Artifact" | Neuromancer | Item | T5 item |
| "Wintermute's Whisper" | Neuromancer | Vision / Lore | hint, lore |
| "New Rose Hotel" | short story | Contact | item, mission tip |
| "3Jane's Shadow" | Neuromancer/MLO | Construct | special construct |
| "The Aleph Fragment" | Mona Lisa Overdrive | Construct | unique construct |
| "Slick Henry's Vision" | MLO | Vision | construct fragment |
| "Virek's Obsession" | Count Zero | Contact | rare program / lore |

#### Triggering (이벤트 발생)

**Random Per Node** (가장 흔함):
- 10-20% chance per node 탐색 시
- Grade ↑ = 확률 ↑
- Faction 호감도 = 보너스 확률

**Scripted for Arcs**:
- Story Skeleton의 각 Arc에 1-2개 핵심 이벤트
- Plot 진행에 필수 (예: Arc 5의 "The Choice")

**Time-based** (런 사이):
- 매 N번째 런에 자동 발생
- World event 형식

**Grade-based Unlock**:
- 특정 grade에서만 발생
- 예: 5-up에서만 "Wintermute's whisper"

#### Resolution (해결 방식)

| Type | 설명 |
| --- | --- |
| **Auto-Resolve** | 보상 자동 획득. |
| **Choice** | 2-3개 옵션. 선택에 따라 결과. |
| **Skill Check** | PPL vs ZDR. 성공 시 보상. |
| **Narrative Only** | Story Archive만 추가. |

#### Rewards by Grade

| Grade | Items | Programs | Constructs |
| --- | --- | --- | --- |
| 1-up | T1 | Basic | — |
| 2-up | T2 | Advanced | — |
| 3-up | T3 | Goliath tier | — |
| 4-up | T4 | Kraken tier | Construct fragments |
| 5-up | T5 | Rare / Custom | Construct unlocks |

#### Pillar 2 Compliance

- **대부분 cyberspace 안** — 이벤트 발생 = 자키가 매트릭스 안
- **일부 추상적**: "a message arrives" — 메시지 자체는 텍스트, 시각화 X
- **No direct meatspace** — 이벤트도 ADR-0009 준수
- **텍스트 전달** — 모든 이벤트는 텍스트로 표현
- **ADR-0011 (ASCII Portraits)**: 이벤트 NPC는 portrait (construct, AI, contact 류)

#### Story Archive Integration

- 모든 이벤트 결과 → Story Archive
- 카테고리:
  - **Briefing**: 이벤트 시작
  - **Result**: 이벤트 종료 (보상, 결과)
  - **Construct Memory**: construct와의 만남
  - **World News**: 외부 사건
- 메인 메뉴에서 다시 볼 수 있음

#### Tone

- 다크, 미스터리, 깁슨 톤
- 짧고 건조한 묘사
- 예시:
  - "you find a fragment of the construct..."
  - "the matrix whispers..."
  - "a construct speaks to you..."
  - "the construct's voice is static and old..."

### Pillar 정합

- **P1 (The Run)**: 이벤트는 런 내 다양성 추가
- **P2 (The Matrix)**: 이벤트는 cyberspace 안 표현, meatspace 미표시
- **P3 (The Flatline)**: 실패 시 위험 → Pillar 3
- **P4 (The Build)**: 이벤트로 아이템 / construct 획득
- **P5 (The Style)**: 깁슨 톤 유지

## 결과 (Consequences)

### 기존 ADR 영향
- **ADR-0008 (Item Tier)**: 보상이 티어 시스템 따름
- **ADR-0009 (Story/News)**: Story Archive와 통합
- **ADR-0010 (Content Pipeline)**: 이벤트는 데이터 파일
- **ADR-0011 (ASCII Portraits)**: 이벤트 NPC portrait
- **ADR-0012 (PPL/ZDR)**: 일부 이벤트 = skill check

### 디자인 영향
- **core_loop**: 런 내 이벤트 추가
- **glossary**: 이벤트 관련 용어
- **story_skeleton**: Arc별 핵심 이벤트 추가
- **Pillar 1**: 다양성 추가 (Pillar 1 부합)

### 구현 영향
- 이벤트 데이터 (JSON)
- 트리거 로직 (random + scripted)
- 보상 시스템 (item / program / construct)
- Story Archive 자동 추가
- 이벤트 UI (텍스트 + 선택지 + portrait)
- ASCII Portraits (NPC construct)

### 향후 결정
- 이벤트 빈도 (random %)
- 이벤트 보상 균형
- Plot과 event의 분리
- Event vs Story integration
- Tone 가이드 (번역 시)

## 영향 받는 항목

- `design/systems/story-events.md` (신규)
- `design/systems/story-archive.md` (통합)
- `design/story_skeleton.md` (Arc별 이벤트)
- `core_loop.md`
- `glossary.md`
- `pillars.md`

## 관련 결정

- ADR-0008 (Item Tier)
- ADR-0009 (Story/News)
- ADR-0010 (Content Pipeline)
- ADR-0011 (ASCII Portraits)
- ADR-0012 (PPL/ZDR)

## 변경 이력

- 2026-06-17: 사용자 요청 → Accepted

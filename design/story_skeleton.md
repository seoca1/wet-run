# Story Skeleton (주요 줄기 뼈대)

> **용도**: 엔딩의 정합성과 품질을 위해, 메인 아크와 엔딩 조건은 사전에 정의한다. 초반 미션과 side content는 유연하게 보강 가능 (ADR-0010).

## 핵심 원칙

1. **메인 아크 (Arc 1~5)**: 사전 정의. 5개 아크가 메인 줄기.
2. **엔딩**: 사전 정의. 4개 이상의 variants. Sprawl 세계관 정합성 유지.
3. **초반 미션 (Arc 1)**: Phase 5에서 우선 구현. 1-3개 미션.
4. **Side content**: 무한. 절차적 생성, faction 움직임, world events.

## 5 Arcs

### Arc 1: First Run (인트로)

- **자키 grade**: 1-up
- **의뢰 수**: 1-3 jobs
- **목표**: 첫 의뢰 → 픽서 소개 → 매트릭스 학습
- **핵심 NPC**: The Finn (소설 등장 픽서, 가벼운 역할)
- **테마**: "jacking in, 처음"
- **구현 우선순위**: **P0** (Phase 5)

**상세**:
- 의뢰 1: 평이한 데이터 추출 (튜토리얼)
- 의뢰 2: 약간 위험, 첫 ICE 만남
- 의뢰 3: (선택) — Finn 소개 의뢰

**주요 이벤트 (ADR-0013)**:
- "First Jack" (vision) — 자키의 첫 잭인 묘사, 깁슨 톤 도입
- "The Finn's First Job" (contact) — Finn 등장, 기본 program 보상
- "Watchdog Patrol" (combat) — 첫 ICE 만남, T1 program 보상

### Arc 2: The Sprawl

- **자키 grade**: 2-3 up
- **의뢰 수**: 3-5 jobs
- **목표**: 다중 faction 의뢰, 위험 증가
- **핵심 NPC**: 다중 픽서 (Finn 외), Sense/Net contact, Yakuza contact
- **테마**: "도시의 밑바닥, 거대 기업의 그림자"
- **구현 우선순위**: P1 (Phase 6)

**상세**:
- Sense/Net 미션 (데이터 / 의뢰)
- Yakuza 미션 (높은 보상, 위험)
- 첫 trace 경험
- "Samurai 등급" — 자키 등급 시스템의 진면목

**주요 이벤트 (ADR-0013)**:
- "Sense/Net Tip" (contact) — Sense/Net 정보, T2 program
- "Yakuza Job" (contact) — Yakuza 의뢰, T2 item
- "Samurai Grade" (vision) — 자키 등급의 진면목, lore

### Arc 3: Corporate Ice

- **자키 grade**: 3-4 up
- **의뢰 수**: 3-5 jobs
- **목표**: T-A, Maas 관련 의뢰
- **핵심 NPC**: T-A 내부 contact (새 캐릭터), 3Jane (construct?)
- **테마**: "거대 기업, 치명적 방어선"
- **Black ICE 등장**
- **구현 우선순위**: P2 (Phase 6 후반)

**상세**:
- Tessier-Ashpool (Straylight) 의뢰
- Maas Biolabs 의뢰
- Black ICE 첫 만남
- Construct (소설 등장) 첫 조우

**주요 이벤트 (ADR-0013)**:
- "Black ICE Encounter" (combat) — 첫 Black ICE, T3 program (방어)
- "Molly's Razor" (rare program) — Molly의 인맥, unique program
- "T-A Artifact" (item) — T-A tech, T4 item

### Arc 4: The AIs

- **자키 grade**: 4-5 up
- **의뢰 수**: 3-5 jobs
- **목표**: Construct 의뢰, AI 진실
- **핵심 NPC**: Dixie 류 construct (메타 진행으로 unlock), AI contact
- **테마**: "AI의 의지, construct의 기억"
- **Wintermute / Neuromancer 흔적** (직접 등장 X)
- **구현 우선순위**: P2 (Phase 7)

**상세**:
- Construct 의뢰 (Dixie 류)
- AI 흔적 발견
- "the matrix has a soul" — 사이버punk의 핵심 의문
- 메타 진행: construct unlock이 핵심

**주요 이벤트 (ADR-0013)**:
- **"Dixie's Offer"** (construct) — Dixie 등장, construct unlock (메타)
- **"Voodoo Loa Contact"** (vision) — Count Zero의 Loa, construct fragment
- "Wintermute's Whisper" (vision) — AI 메시지, lore, hint
- "The Aleph Fragment" (construct) — Mona Lisa Overdrive, unique construct

### Arc 5: The Choice (엔딩)

- **자키 grade**: 5-up 필수
- **의뢰 수**: 1 final job
- **목표**: 최종 의뢰, 플레이어 선택
- **핵심 NPC**: 3Jane, Neuromancer, or major figure (분기)
- **테마**: "선택의 무게"
- **구현 우선순위**: P3 (Phase 7)

**상세**:
- 최종 의뢰: T-A / Straylight / Zion 등
- 플레이어의 누적 world state에 따라 결과 분기
- "최종 의뢰"는 4개 variants 중 하나
- 엔딩은 4+ variants

**주요 이벤트 (ADR-0013)**:
- "3Jane's Shadow" (construct) — 3Jane 등장, special construct
- "Slick Henry's Vision" (vision) — 예술가의 시선
- **"The Choice"** (final) — 최종 선택, 엔딩 결정

## 엔딩 (4+ Variants)

엔딩은 **플레이어의 누적 world state**에 따라 결정:
- **어떤 faction에 일했는가** (T-A, Yakuza, Lo Teks, Sense/Net 등)
- **어떤 construct를 해제했는가** (Dixie, 또는 다른 AI)
- **의뢰 결과의 누적** (어떤 사건을 막았는가 / 도왔는가)
- **5-up 등급 + 최종 의뢰의 결과**

### Ending A: The Sprawl Returns

- **조건**: Sprawl에 충실, T-A에 깊이 관여
- **내용**: "the city survives. the matrix evolves. you survive another day."
- **Tone**: 비관적이지만 안정적
- **원작 차용**: Tessier-Ashpool 이후의 Sprawl
- **메시지**: "you chose the city"

### Ending B: The AI Awakens

- **조건**: Construct (Dixie 등)와 깊은 관계, AI 흔적 발견
- **내용**: "wintermute and Neuromancer — your construct — merged. something new is born."
- **Tone**: 인공 지능의 의지, construct의 결합
- **원작 차용**: Wintermute/Neuromancer merger
- **메시지**: "you chose the construct"

### Ending C: The Lo Tek

- **조건**: Lo Teks / Zion과 깊이, 반(反)기업 의뢰
- **내용**: "you left the sprawl. the orbital habitat is home. the matrix is still glitched."
- **Tone**: 반기업, 자유
- **원작 차용**: Maelcum, Zion
- **메시지**: "you chose to leave"

### Ending D: The Flatline (다시)

- **조건**: 5-up 달성 후, 최종 의뢰의 실패
- **내용**: "the matrix is vast. you were small. you flatline. again."
- **Tone**: 비극적, Pillar 3 (The Flatline)의 정점
- **메시지**: "you were small"

### 추가 Ending (Open)

- **Ending E**: The Dixie Memory — Dixie를 깊이 사용, construct와의 결합
- **Ending F**: The Slick Henry — 다른 자키와의 동맹
- **Ending G**: The Sibling — 3Jane과의 관계
- 기타 가능

## Side Content (유연)

- **Side Jobs**: 무한. 절차적 생성. Arc와 무관.
- **Faction 뉴스**: Story Archive. Faction 움직임.
- **World Events**: 시간 기반 이벤트. 자키 사이.
- **Construct 대화**: Dixie 류. Lore / hint.

## 구현 우선순위

| Phase | Arc | 비고 |
| --- | --- | --- |
| **Phase 5** | Arc 1 (1-3 jobs) | 우선, Vertical Slice |
| **Phase 6** | Arc 2-3 (보강) | 미션 데이터 추가 |
| **Phase 7** | Arc 4-5, Ending | 엔딩 구현 |
| **그 후** | Side content | 무한 추가 |

## Open Questions

- 정확한 ending 수 (4-6개?)
- Ending 발동 조건 (단순 world state? 특정 의뢰 필수?)
- Arc 간 trigger (grade? specific unlock? player choice?)
- 메인 아크와 side content의 분리 (어떻게 표시?)
- "The Choice"의 구체적 시나리오 (의뢰 / 대화 / 전투?)
- 픽서: The Finn 외 새 픽서들의 이름 / 정체성
- T-A contact: 3Jane 직접? 또는 새 캐릭터?
- "The Finn"의 역할 — 스포일러 회피 어떻게?

## 디자인 노트

- **Sprawl 세계관 정합성**: 모든 엔딩은 원작의 톤과 정합
- **Pillar 3 (The Flatline)**: Ending D는 "비극적"하지만, "게임 오버"가 아니라 "중단"
- **Pillar 4 (The Build)**: 메인 아크 진행 = unlock 메타 진행
- **Pillar 5 (The Style)**: 모든 엔딩의 톤은 깁슨 톤

## 관련 문서

- `decisions/0009-story-news-system.md` — Story Archive 시스템
- `decisions/0010-i18n-content-pipeline.md` — i18n + 콘텐츠 파이프라인
- `wiki/world/factions.md` — faction 정보
- `wiki/world/sprawl_universe.md` — 세계관

## 변경 이력

- 2026-06-17: 초안 작성 (5 arcs + 4+ endings)

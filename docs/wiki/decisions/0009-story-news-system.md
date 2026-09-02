# ADR-0009: Story / News 전달 시스템

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트

사용자가 명시한 디자인 제약 (2026-06-17):

1. **주인공은 소설에 출현하지 않은 새로운 플레이어** — Case / Molly / Bobby 등이 아님
2. **사이버스페이스에서 미션과 레벨업을 수행**
3. **사이버스페이스 밖의 세계는 직접 표현되지 않음** — meatspace는 시각화되지 않음
4. **meatspace는 뉴스나 이야기의 형태로 전달됨**
5. **전달된 이야기는 다시 볼 수 있도록 메뉴에 포함됨** (Story Archive)

이 결정은 기존 ADR에 강하게 영향을 미친다:
- ADR-0005 (사이버스페이스 표현): meatspace는 *옵션*이 아니라 *절대 시각화되지 않음*
- ADR-0006 (런 구조): Story Archive는 unlock 메타 진행에 포함
- ADR-0008 (진행): Stories는 unlock 메타 진행의 일부

## 결정

### Story / News 시스템

게임 내 meatspace와 외부 세계는 **오직 텍스트 이야기/뉴스로만** 전달된다.

**전달 채널 (전부 텍스트)**:
- 의뢰 briefing (런 시작 전)
- 의뢰 결과 (런 종료 후)
- 런 중 시스템 메시지 (intercepted comms, news ticker)
- 런 사이 시간 흐름 중 발생하는 world events
- Construct와의 대화 (lore, hint)

**Story Archive (메뉴)**:
- 메인 메뉴에서 접근
- 카테고리: 의뢰 briefing / 의뢰 결과 / 월드 뉴스 / faction 움직임 / construct 대화
- 시간순 / 카테고리별 / 검색 가능
- 모든 전달된 이야기는 영구 저장 (메타 진행의 일부)
- **새 story는 자동 추가**, 플레이어가 직접 작성 X

### 플레이어 캐릭터

- 소설에 없는 새로운 decker
- 핸들(별명) — 플레이어가 선택, 기본값 제공
- 외모 / 성별 / 국적 / 구체적 backstory 없음 (Pillar 1: 한 자키의 무게는 "여기서 죽음"으로 충분)
- meatspace는 알 수 없음 (jacked in 상태로만 존재)

### Hub (Prep / Job Board)

meatspace가 없으므로 hub는 **cyberspace 안의 텍스트 인터페이스**:
- 픽서 construct와 대화 (텍스트)
- 의뢰 선택 (텍스트 메뉴)
- 데크 / 프로그램 / 웨웨어 구성 (텍스트 메뉴)
- 정보 구매 (텍스트 메뉴)

이는 "사이버스페이스 안의 시뮬레이션"이며, meatspace가 아님.

## 결과 (Consequences)

### Pillar 정합
- **P1 (The Run)**: 한 자키의 무게 = meatspace에 대한 무관심
- **P2 (The Matrix)**: 사이버스페이스 외에는 *어떤 것도* 시각화되지 않음 — 매우 강한 Pillar
- **P3 (The Flatline)**: flatline = 검은 화면 + "you flatline" 텍스트 (meatspace 묘사 X)
- **P4 (The Build)**: Story Archive는 unlock 메타 진행 (스토리 해금 = 메타 보상)
- **P5 (The Style)**: 매체화된 세계 (mediated world) — 깁슨 톤의 핵심

### 기존 ADR 영향
- **ADR-0005 갱신**: meatspace "옵션" → "절대 시각화 X"
- **ADR-0006 갱신**: Story Archive가 unlock 메타 진행의 일부
- **ADR-0008 갱신**: Stories는 unlock (메타 진행의 한 형태), 스탯 강화 X

### 디자인 영향
- **Pillar 2 강화**: "The Matrix"는 *유일한* 시각적 공간
- **core_loop 갱신**: Job Board / Prep 모두 cyberspace 안
- **GDD 갱신**: 새 시스템 `story-archive` 추가
- **glossary 갱신**: Story 관련 용어 추가
- **wiki 갱신**: "새 플레이어", "meatspace 미표시" 명시

### 구현 영향
- Story 데이터: JSON/YAML
  ```json
  {
    "id": "job-001-briefing",
    "category": "briefing",
    "timestamp": "2026-06-17T00:00:00",
    "title": "Tessier-Ashpool 데이터 추출",
    "content": "Finn here. Got a job. T-A is moving data...",
    "tags": ["ta", "extraction", "first-timer"]
  }
  ```
- Story Archive UI: 카테고리 + 시간순 + 검색
- 새 story는 런 결과 / 시간 이벤트에서 자동 추가

### 향후 결정
- Story 작성 가이드 (톤, 길이, 예시)
- Story 카테고리 세부 디자인
- 시간 이벤트 시스템 (런 사이 시간 흐름)
- Construct 대화 시스템 (Dixie 류)

## 영향 받는 항목

- `design/systems/story-archive.md` (신규, 작성 필요)
- `design/core_loop.md` (hub를 cyberspace 안으로)
- `design/pillars.md` (Pillar 2 강화)
- `design/GDD.md` (새 플레이어, Story 시스템)
- `wiki/world/sprawl_universe.md` (새 플레이어 명시)
- `wiki/world/cyberspace.md` (meatspace 미표시)
- `wiki/world/style_guide.md` (mediated world 톤)
- `design/glossary.md` (Story 용어)

## 관련 결정

- ADR-0005 (Accepted, 갱신됨)
- ADR-0006 (Accepted)
- ADR-0008 (Accepted)

## 변경 이력

- 2026-06-17: 사용자 디자인 제약 명시 → Accepted

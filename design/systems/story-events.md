# System: Story Events (소설 스토리 부가 이벤트)

> **상위 결정**: `../../decisions/0013-story-events.md` (Accepted)
> **관련**: ADR-0008 (Item Tier), ADR-0009 (Story/News), ADR-0010 (Content Pipeline), ADR-0011 (ASCII Portraits), ADR-0012 (PPL/ZDR)

## 목적

스프롤 3부작의 storyline을 게임의 **부가 콘텐츠**로 통합. 이벤트는 다양성을 제공하고 보상 (아이템 / program / construct) 으로 보강.

## Event Types (6 가지)

### 1. Construct Contact (구성체 접촉)

- **설명**: construct가 자키에게 접근
- **보상**: construct unlock (메타) / construct fragment (런 내)
- **예시**: Dixie, Finn-as-construct, AI Loa
- **ASCII Portrait**: `◊D◊` (Dixie) / `♠F♠` (Finn) / `◯L◯` (Loa)

### 2. Rare Program Discovery (희귀 프로그램 발견)

- **설명**: 매트릭스에서 강력한 program 발견
- **보상**: 고티어 program
- **예시**: Kraken, Burning Chrome, custom construct-program
- **ASCII Portrait**: `⚔GOL⚔` / `⚔KRK⚔`

### 3. Item Discovery (아이템 발견)

- **설명**: 희귀한 데이터 / artifact 발견
- **보상**: 장비 / 데이터
- **예시**: T-A tech, Maas biochip, Ono-Sendai 7
- **ASCII Portrait**: `¢DAT¢` / `▲T-A▲`

### 4. Vision / Lore (환상 / 지식)

- **설명**: 매트릭스 본질에 대한 통찰
- **보상**: Story Archive entry (런 내)
- **예시**: "the matrix has a soul", AI 진실의 단편
- **특징**: combat 없음, 순수 narrative

### 5. Contact from Above (위에서의 접촉)

- **설명**: 위에서 메시지 / 지시
- **보상**: tip, hint, item, mission
- **예시**: Wintermute's whisper, 신원불명의 contact
- **특징**: 추상적 메시지

### 6. Combat Event (전투 이벤트)

- **설명**: 적대적 자키 / ICE trap 만남
- **보상**: 승리 시 items, programs
- **예시**: hostile decker ambush, Black ICE trap
- **메카닉**: ADR-0003 RT-MS + ADR-0012 PPL/ZDR

## Event Catalog (스프롤 3부작 기반)

| Event | 출처 | Type | Reward | Grade |
| --- | --- | --- | --- | --- |
| "First Jack" | Neuromancer | Vision | lore, basic program | 1-up |
| "The Finn's First Job" | Neuromancer | Contact | basic program, tip | 1-up |
| "Watchdog Patrol" | Neuromancer | Combat | T1 program | 1-up |
| "Sense/Net Tip" | Neuromancer | Contact | T2 program | 2-up |
| "Yakuza Job" | Neuromancer | Contact | T2 item | 2-up |
| "Samurai Grade" | Neuromancer | Vision | lore, advancement | 3-up |
| "Black ICE Encounter" | Neuromancer | Combat | T3 program (defense) | 3-up |
| "Molly's Razor" | Neuromancer | Rare Program | unique program (razor) | 3-up |
| "T-A Artifact" | Neuromancer | Item | T4 item | 4-up |
| "Dixie's Offer" | Neuromancer | Construct | Dixie unlock (meta) | 4-up |
| "Wintermute's Whisper" | Neuromancer | Vision | lore, hint | 4-up |
| "Voodoo Loa Contact" | Count Zero | Vision | construct fragment | 4-up |
| "The Aleph Fragment" | Mona Lisa Overdrive | Construct | unique construct | 5-up |
| "3Jane's Shadow" | Neuromancer/MLO | Construct | special construct | 5-up |
| "Slick Henry's Vision" | MLO | Vision | construct fragment | 5-up |
| "Virek's Obsession" | Count Zero | Contact | rare program, lore | 4-up |
| "New Rose Hotel" | short story | Contact | item, mission tip | 2-up |
| "Burning Chrome" | short story | Rare Program | Kraken-tier program | 4-up |

## Triggering (이벤트 발생)

### Random Per Node (가장 흔함)

- 10-20% chance per node 탐색 시
- Grade ↑ = 확률 ↑
- Faction 호감도 = 보너스 확률

```python
def event_chance(grade, faction_rep):
    base = 0.10  # 10%
    grade_bonus = (grade - 1) * 0.05  # +5% per grade
    faction_bonus = faction_rep * 0.02  # +2% per rep
    return min(base + grade_bonus + faction_bonus, 0.30)  # max 30%
```

### Scripted for Arcs

- Story Skeleton의 각 Arc에 1-2개 핵심 이벤트
- Plot 진행에 필수 (예: Arc 5의 "The Choice")

### Time-based (런 사이)

- 매 N번째 런에 자동 발생
- World event 형식

### Grade-based Unlock

- 특정 grade에서만 발생
- 예: 5-up에서만 "Wintermute's whisper"

## Resolution (해결 방식)

### Auto-Resolve (자동)

- 보상 자동 획득
- 예: "you find a fragment..." → program 획득

### Choice (선택)

- 2-3개 옵션
- 예: "construct offers help: accept or refuse?"
- 선택에 따라 보상 / 위험

```python
choice_event = {
    "id": "event-dixie-offer",
    "prompt": "Dixie offers to join you.",
    "choices": [
        {
            "label": "Accept Dixie",
            "result": "construct_unlock",
            "construct": "dixie_flatline"
        },
        {
            "label": "Refuse",
            "result": "story_archive",
            "category": "construct_memory"
        }
    ]
}
```

### Skill Check (PPL vs ZDR)

- PPL ≥ ZDR → 성공, 보상
- PPL < ZDR → 실패, 위험 (ADR-0012)

```python
def skill_check_event(ppl, zdr):
    if ppl >= zdr:
        return "success"  # 보상
    else:
        return "fail"  # 위험 (alarm 상승, ICE spawn)
```

### Narrative Only

- 보상 없음 (또는 작은 보상)
- Story Archive entry
- 예: "you glimpse Wintermute..."

## Rewards by Grade

| Grade | Items | Programs | Constructs |
| --- | --- | --- | --- |
| 1-up | T1 | Basic | — |
| 2-up | T2 | Advanced | — |
| 3-up | T3 | Goliath tier | — |
| 4-up | T4 | Kraken tier | Construct fragments |
| 5-up | T5 | Rare / Custom | Construct unlocks |

## Story Archive Integration

### 자동 추가

모든 이벤트 결과 → Story Archive.

```python
def add_to_story_archive(event_id, category, content):
    story = {
        "id": f"event-{event_id}",
        "category": category,  # "briefing", "result", "construct_memory", "world_news"
        "timestamp": current_time(),
        "content": content
    }
    archive.append(story)
```

### 카테고리

- **Briefing**: 이벤트 시작
- **Result**: 이벤트 종료 (보상, 결과)
- **Construct Memory**: construct와의 만남
- **World News**: 외부 사건

## Tone Guide

### 원칙

- 다크, 미스터리, 깁슨 톤
- 짧고 건조한 묘사
- 추상적 표현 OK
- meatspace 직접 묘사 X (Pillar 2)

### 좋은 예시

- "you find a fragment of the construct..."
- "the matrix whispers..."
- "a construct speaks to you..."
- "the construct's voice is static and old..."
- "Dixie is here. Construct. ROM. The dead hacker."

### 나쁜 예시

- "Wow! Amazing item! Congratulation!"
- "You meet a beautiful woman who..."
- "The bar is full of friendly people..." (meatspace 묘사)

## 데이터 구조

### `data/events/first-jack.json`

```json
{
  "id": "event-first-jack",
  "name": "First Jack",
  "trigger": {
    "type": "scripted_arc",
    "arc": 1,
    "phase": 1
  },
  "type": "vision",
  "ascii_portrait": null,
  "description": "You jack in. The world goes gray. The matrix unfolds in lines of light.",
  "resolution": "narrative_only",
  "tone": "Gibson opening",
  "story_archive_entry": {
    "category": "briefing",
    "title": "First Jack",
    "content": "You jack in. The world goes gray. The matrix unfolds in lines of light, clusters and constellations of data. Like city lights, receding..."
  }
}
```

### `data/events/dixie-offer.json`

```json
{
  "id": "event-dixie-offer",
  "name": "Dixie's Offer",
  "trigger": {
    "type": "grade_unlock",
    "grade": "4-up"
  },
  "type": "construct_contact",
  "ascii_portrait": "◊D◊",
  "description": "A construct reaches out. Dixie. The dead hacker McCoy Pauley. ROM-stored personality.",
  "resolution": "choice",
  "choices": [
    {
      "label": "Accept Dixie",
      "result": "construct_unlock",
      "construct": "dixie_flatline"
    },
    {
      "label": "Refuse",
      "result": "story_archive",
      "category": "construct_memory"
    }
  ],
  "story_archive_entry": {
    "category": "construct_memory",
    "title": "Dixie's Offer",
    "content": "Dixie offers help. Construct. The dead hacker. ROM personality. You accepted, or refused."
  }
}
```

## Arc별 핵심 이벤트 (story_skeleton 연동)

### Arc 1 (1-up)
- First Jack (vision)
- The Finn's First Job (contact)
- Watchdog Patrol (combat)

### Arc 2 (2-3 up)
- Sense/Net Tip (contact)
- Yakuza Job (contact)
- Samurai Grade (vision)

### Arc 3 (3-4 up)
- Black ICE Encounter (combat)
- Molly's Razor (rare program)
- T-A Artifact (item)

### Arc 4 (4-5 up)
- Dixie's Offer (construct)
- Voodoo Loa Contact (vision/construct)
- Wintermute's Whisper (vision)
- The Aleph Fragment (construct)

### Arc 5 (5-up)
- 3Jane's Shadow (construct)
- Slick Henry's Vision (vision)
- The Choice (final)

## Pillar 2 Compliance

| 케이스 | 처리 |
| --- | --- |
| Event in cyberspace | ✓ OK |
| "a message arrives" (abstract) | ✓ OK (text only) |
| "you meet a person" (meatspace) | ✗ Pillar 2 위반 — *reject* |
| Construct talks to you | ✓ OK (construct is cyberspace) |
| "you see the city" (meatspace) | ✗ Pillar 2 위반 — *reject* |

## 구현 가이드

### Event Manager

```python
class EventManager:
    def __init__(self, archive, player):
        self.archive = archive
        self.player = player
        self.events = load_events("data/events/")
    
    def check_event(self, context):
        # Check random trigger
        if random() < self.event_chance(self.player.grade):
            return self.random_event()
        # Check scripted
        if event := self.scripted_event(context):
            return event
        return None
    
    def resolve_event(self, event, choice=None):
        if event.resolution == "auto":
            return self.apply_rewards(event.rewards)
        elif event.resolution == "choice":
            return self.apply_choice(event, choice)
        elif event.resolution == "skill_check":
            return self.skill_check(event)
        elif event.resolution == "narrative":
            return self.add_to_archive(event)
```

## 향후 결정

- 이벤트 빈도 (random %)
- 이벤트 보상 균형
- Plot과 event의 분리
- Event vs Story integration
- Tone 가이드 (번역 시)

## 관련 문서

- `decisions/0013-story-events.md` — ADR
- `decisions/0008-progression-system.md` — Item Tier
- `decisions/0009-story-news-system.md` — Story Archive
- `decisions/0011-ascii-portraits.md` — Portrait
- `decisions/0012-difficulty-rating.md` — PPL/ZDR
- `design/story_skeleton.md` — Arc 연동

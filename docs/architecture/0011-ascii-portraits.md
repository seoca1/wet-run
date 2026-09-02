# ADR-0011: ASCII Portraits (인물 / 객체 시각 식별)

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0002 (Pure ASCII)

## 컨텍스트

사용자 결정 (2026-06-17): "소설 등장인물을 포함한 인물들과 사이버스페이스 객체를 표현"하되, **ASCII 아스키 포트레이트** 방식 채택 (Option 2).

- ADR-0002 (Accepted): Pure ASCII — 모든 비주얼을 텍스트로
- 사용자는 Pure ASCII를 유지하면서, 인물과 객체에 *시각적 식별*을 원함
- **결론**: Pure ASCII 안에서 *ASCII 기호*로 인물/객체를 표현. 애니메 이미지 X.

## 결정

### ASCII Portrait 시스템

**정의**:
- 인물 / 객체를 짧은 ASCII / Unicode 기호로 표현 (5-7자)
- 데이터 파일 (`data/portraits.json`)에 저장
- 색상으로 추가 식별
- Pure ASCII 미학 유지

**형식**:
```
▸ SYMBOL ▸
```
또는:
```
[ SYMBOL ]
```

**예시**:

| 대상 | ASCII | 색상 | 설명 |
| --- | --- | --- | --- |
| **Player (자키)** | `◉P◉` | white/green | "you", "yourself" |
| **Ally (construct)** | `◊D◊` | cyan | construct = diamond |
| **Fixer (The Finn)** | `♠F♠` | magenta | fixer = spade |
| **AI Loa** | `◯L◯` | white | AI = circle |
| **Hostile Decker** | `X_X` | red | enemy |
| **Ally Decker** | `O_O` | cyan | ally |
| **ICE (standard)** | `▲ICE▲` | magenta | defense |
| **Black ICE** | `█ICE█` | red | deadly |
| **Watchdog** | `◉WDG◉` | magenta | detection |
| **Wisp (program)** | `⛨WSP⛨` | cyan | defense program |
| **Goliath (program)** | `⚔GOL⚔` | magenta | attack program |
| **Probe (program)** | `?PRB?` | yellow | detection program |
| **Data node** | `¢DAT¢` | yellow | data |
| **System node** | `§SYS§` | white | system |
| **Router node** | `┼RTR┼` | white | router |
| **Exit node** | `→EXT` | green | exit |
| **Core node** | `※COR※` | magenta | core |
| **T-A faction** | `▲▲T-A▲▲` | red | Tessier-Ashpool |
| **Yakuza faction** | `◆Y◆` | magenta | Yakuza |
| **Sense/Net faction** | `●S●` | cyan | Sense/Net |
| **Maas faction** | `◐M◐` | green | Maas |
| **Hosaka faction** | `◇H◇` | white | Hosaka |
| **Lo Teks faction** | `◉L◉` | yellow | Lo Teks |

### Pillar 2 준수 — Cyberspace-Only Rule

**핵심 원칙**: ASCII Portrait는 *cyberspace 안의 존재*에게만 부여된다. meatspace 인물은 직접 묘사되지 않는다 (Pillar 2).

| 케이스 | Portrait 가능? | 이유 |
| --- | --- | --- |
| Cyberspace construct (Dixie) | ✓ | construct = cyberspace 거주자 |
| AI Loa (Wintermute/Neuromancer) | ✓ | AI = cyberspace 토착 |
| 픽서 construct (Finn이 Aleph 안에 있을 때) | ✓ | construct = cyberspace |
| Decker in cyberspace | ✓ | 데크에 연결된 자 |
| ICE / Program | ✓ | 매트릭스의 데이터 객체 |
| Meatspace person (Case, Molly 본체) | ✗ | meatspace 직접 묘사 = Pillar 2 위반 |
| Meatspace person in cyberspace (jacked in) | △ | "jacked in" 상태로만 — "cyberspace representation"으로 표시 |

**Rule of thumb**: meatspace 사람이 보일 때는 *cyberspace 안의 표현*으로만 (예: construct, jacked-in 핸들, 데이터 그림자).

### 색상 코딩 (Color Palette)

```
Player:     white / green
Ally:       cyan
Fixer:      magenta
AI:         white (loa는 노랑도 가능)
Hostile:    red
ICE:        magenta (standard), red (black)
Programs:   cyan (방어), magenta (공격), yellow (탐지)
Data:       yellow
System:     white
Router:     white
Exit:       green
Core:       magenta
Faction:    다양 (위 표 참조)
```

### 표시 위치

**Portrait가 표시되는 곳**:
- **Hub 대화** (픽서 construct의 머리글)
- **Matrix combat** (적 ICE, 아군 construct, 활성 program)
- **Dialogue box** (NPC construct의 이름 옆)
- **Status bar** (활성 program / 효과)

**Portrait가 표시되지 않는 곳**:
- **Story Archive 본문** (텍스트 전용, Pillar 2 / ADR-0009)
- **Meatspace 묘사** (Pillar 2)
- **Meatspace 인물 직접 묘사** (Pillar 2)

### 데이터 구조

```json
// data/portraits.json
{
  "player": {
    "ascii": "◉P◉",
    "color": "green",
    "name": "you"
  },
  "construct.dixie": {
    "ascii": "◊D◊",
    "color": "cyan",
    "name": "Dixie Flatline"
  },
  "fixer.finn": {
    "ascii": "♠F♠",
    "color": "magenta",
    "name": "The Finn"
  },
  "ice.standard": {
    "ascii": "▲ICE▲",
    "color": "magenta",
    "name": "ICE"
  },
  "ice.black": {
    "ascii": "█ICE█",
    "color": "red",
    "name": "Black ICE"
  },
  "faction.ta": {
    "ascii": "▲T-A▲",
    "color": "red",
    "name": "Tessier-Ashpool"
  }
}
```

### 확장 (Future)

- Construct 해제 시 새로운 portrait 추가
- Faction unlock 시 faction portrait 추가
- 사용자가 handle 변경 시 portrait도 갱신
- ANSI 16-color 또는 256-color 지원 (선택)

## 결과 (Consequences)

### Pillar 정합
- **P1 (The Run)**: 미영향 — 한 런의 진행
- **P2 (The Matrix)**: 강화 — cyberspace 안의 표현은 ASCII portrait로 더 명확
- **P3 (The Flatline)**: 미영향
- **P4 (The Build)**: portrait 데이터 = unlock 데이터
- **P5 (The Style)**: 깁슨 톤 유지 — 애니메 X, ASCII만

### 기존 ADR 영향
- **ADR-0002 (Pure ASCII)** 보강: ASCII portrait 시스템 추가
- **ADR-0009 (Story/News)** 준수: Story Archive 본문은 텍스트만, portrait 없음

### 디자인 영향
- **Pillar 2 명시**: portrait는 cyberspace only
- **GDD** 갱신: 새 시스템 `ascii-portraits`
- **glossary** 갱신: portrait 관련 용어

### 구현 영향
- `data/portraits.json` — portrait 데이터
- `portraits.py` — portrait 로더 / 렌더러
- Dialogue / matrix UI — portrait 표시
- Story Archive — portrait 미표시 (텍스트만)

### 향후 결정
- ANSI 16-color / 256-color / True color
- Portrait 애니메이션 (깜빡임 등)
- 사용자 정의 portrait (메타 진행)
- Faction portrait unlock 트리

## 영향 받는 항목

- `design/systems/ascii-portraits.md` (신규, 시스템 명세)
- `design/GDD.md` (Core Systems에 추가)
- `design/pillars.md` (Pillar 2에 cyberspace portrait 명시)
- `decisions/0002-rendering-style.md` (참조 추가)

## 관련 결정

- ADR-0002 (Accepted, 보강됨)
- ADR-0009 (Accepted, 준수)

## 변경 이력

- 2026-06-17: 사용자 결정 (Option 2) → Accepted

# System: ASCII Portraits (인물 / 객체 시각 식별)

> **상위 결정**: `../../decisions/0011-ascii-portraits.md` (Accepted)
> **관련**: `../../decisions/0002-rendering-style.md` (Pure ASCII 보강)

## 목적

Pure ASCII 안에서 인물과 객체를 *시각적으로 식별*한다. Pillar 2, 5를 유지하면서 게임의 인지성을 높인다.

## 형식

**기본 패턴**:
```
▸ <SYMBOL> ▸
```

또는 단순화:
```
<SYMBOL>
```

- 5-7자 폭
- monospace 폰트
- 색상 코딩 (Palette 참조)
- 양 끝에 장식 기호 가능 (선택)

## 예시 카탈로그

### 캐릭터 (Cyberspace-only)

| ID | ASCII | 색상 | 설명 |
| --- | --- | --- | --- |
| `player` | `◉P◉` | green | "you" — 자키 |
| `construct.dixie` | `◊D◊` | cyan | Dixie Flatline (construct) |
| `construct.finn` | `♠F♠` | magenta | The Finn (픽서 construct) |
| `ai.wintermute` | `◐W◐` | white | Wintermute |
| `ai.neuromancer` | `◑N◑` | white | Neuromancer |
| `ai.loa` | `◯L◯` | yellow | Loa (fragmented AI) |
| `decker.ally` | `O_O` | cyan | 아군 decker |
| `decker.hostile` | `X_X` | red | 적 decker |

### Cyberspace 객체 (ICE, Programs)

| ID | ASCII | 색상 | 설명 |
| --- | --- | --- | --- |
| `ice.standard` | `▲ICE▲` | magenta | 표준 ICE |
| `ice.black` | `█ICE█` | red | Black ICE (치명적) |
| `ice.tessier` | `▲T-A▲` | red | Tessier-Ashpool ICE |
| `prog.goliath` | `⚔GOL⚔` | magenta | Goliath (공격) |
| `prog.wisp` | `⛨WSP⛨` | cyan | Wisp (방어) |
| `prog.wardrone` | `◆WDR◆` | cyan | Wardrone (방어) |
| `prog.watchdog` | `◉WDG◉` | magenta | Watchdog (탐지) |
| `prog.probe` | `?PRB?` | yellow | Probe (탐지) |
| `prog.hellhound` | `▲HHD▲` | red | Hellhound (추적) |
| `prog.clydes` | `▼CLD▼` | red | Clydes (정체불명) |

### 노드 (Matrix)

| ID | ASCII | 색상 | 설명 |
| --- | --- | --- | --- |
| `node.entry` | `▶ENTRY` | green | 진입점 |
| `node.exit` | `→EXT` | green | 탈출점 |
| `node.core` | `※COR※` | magenta | 코어 |
| `node.data` | `¢DAT¢` | yellow | 데이터 |
| `node.system` | `§SYS§` | white | 시스템 |
| `node.router` | `┼RTR┼` | white | 라우터 |
| `node.ice` | `▲ICE▲` | magenta | ICE 노드 |
| `node.construct` | `◊CNT◊` | cyan | construct 노드 |

### Faction 마킹

| ID | ASCII | 색상 | 설명 |
| --- | --- | --- | --- |
| `faction.ta` | `▲T-A▲` | red | Tessier-Ashpool |
| `faction.yakuza` | `◆Y◆` | magenta | Yakuza |
| `faction.sense_net` | `●S●` | cyan | Sense/Net |
| `faction.maas` | `◐M◐` | green | Maas Biolabs |
| `faction.hosaka` | `◇H◇` | white | Hosaka |
| `faction.lo_teks` | `◉L◉` | yellow | Lo Teks / Vodou |
| `faction.zion` | `★Z★` | yellow | Zion |
| `faction.panther` | `♦P♦` | magenta | Panther Moderns |

## 색상 팔레트

| 역할 | 색상 | RGB | 사용 |
| --- | --- | --- | --- |
| Player | green | `#00FF00` | "you" |
| Ally (construct) | cyan | `#00FFFF` | construct, ally |
| Fixer | magenta | `#FF00FF` | 픽서 construct |
| AI | white | `#FFFFFF` | AI, Loa |
| Hostile | red | `#FF0040` | 적 ICE / decker |
| Detection | yellow | `#FFFF00` | 탐지 program |
| Data | yellow | `#FFFF00` | 데이터 노드 |
| System | white | `#FFFFFF` | 시스템 / 라우터 |
| Exit | green | `#00FF00` | 진입 / 탈출 |
| Core | magenta | `#FF00FF` | 코어 / 위험 |
| Faction | 다양 | 위 표 | faction 마킹 |

## 표시 위치

### 표시되는 곳

- **Hub 대화** (픽서 construct의 머리글)
  ```
  ♠F♠  The Finn
       Got a job for you.
  ```
- **Matrix 전투** (적 ICE, 아군 construct)
  ```
  ▣ ▣ ▲ICE▲ ▣ ▣
  ◊D◊ *you* ▣
  ```
- **Dialogue box** (NPC construct 이름 옆)
- **Status bar** (활성 program / 효과)
- **의뢰 briefing** (의뢰인 — 의뢰인이 construct일 때)

### 표시되지 않는 곳

- **Story Archive 본문** (텍스트 전용, ADR-0009)
- **Meatspace 인물 직접 묘사** (Pillar 2)
- **메뉴 / 설정 화면** (텍스트만)

## Pillar 2 준수 (Cyberspace-Only Rule)

> **규칙**: ASCII Portrait는 *cyberspace 안의 존재*에게만 부여된다.

| 케이스 | Portrait? | 이유 |
| --- | --- | --- |
| Construct (Dixie) | ✓ | construct = cyberspace 거주자 |
| AI (Loa) | ✓ | AI = cyberspace 토착 |
| 픽서 (in cyberspace) | ✓ | construct로 표시 |
| ICE / Program | ✓ | 매트릭스 데이터 |
| Decker in cyberspace | ✓ | jacked in 상태 |
| Meatspace person 본체 (Case, Molly) | ✗ | Pillar 2 위반 |
| Meatspace person jacked in | △ | "cyberspace representation"으로만 |

**meatspace 사람이 보일 때**: *cyberspace 안의 표현*으로만:
- "jacked in" 상태 표시
- Construct 사본 표시
- 데이터 그림자 표시
- 또는 표시하지 않음 (텍스트만)

## 데이터 구조

### `data/portraits.json`

```json
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
  "node.entry": {
    "ascii": "▶ENTRY",
    "color": "green"
  },
  "node.core": {
    "ascii": "※COR※",
    "color": "magenta"
  },
  "faction.ta": {
    "ascii": "▲T-A▲",
    "color": "red",
    "name": "Tessier-Ashpool"
  }
}
```

### 코드 모듈

```python
# prototype/wet_run/portraits.py
def get_portrait(entity_id: str) -> Portrait:
    return portraits[entity_id]

def render_portrait(console, x, y, entity_id, color_override=None):
    portrait = get_portrait(entity_id)
    color = color_override or portrait["color"]
    console.print(x, y, portrait["ascii"], fg=color)
```

## 확장

### Future (메타 진행)

- **Construct 해제**: 새 construct unlock → 새 portrait
- **Faction 호감도**: faction 마킹 변경 가능
- **사용자 핸들**: player의 portrait는 핸들에 따라 변경 가능
- **ANSI 16-color 또는 256-color**: 더 풍부한 색상

### 제한 (한계)

- Pillar 2: meatspace 인물 직접 묘사 불가
- Pillar 5: 애니메 / 사진 X
- monospace: 폭이 다른 기호 사용 시 정렬 어려움 → 통일된 폭 권장

## Open Questions

- 픽서 construct 외에 다른 construct의 portrait 디자인?
- "jacked in" meatspace 인물 (예: 시뮬레이트로 보이는 픽서)의 portrait 표현?
- Faction 호감도 변화가 portrait에 반영되는가?
- T-A의 Straylight 같은 특정 위치의 특수 portrait?

## 관련 문서

- `decisions/0011-ascii-portraits.md` — ADR
- `decisions/0002-rendering-style.md` — Pure ASCII
- `design/pillars.md` — Pillar 2, 5
- `wiki/world/glossary.md` — 용어

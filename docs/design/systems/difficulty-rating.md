# System: Combat Difficulty & Threat Level (PPL & ZDR)

> **상위 결정**: `../../decisions/0012-difficulty-rating.md` (Accepted)
> **관련**: ADR-0003 (RT-MS), ADR-0005 (Cyberspace), ADR-0008 (Item Tier), ADR-0011 (ASCII Portraits)

## 목적

Combat의 위험을 **명시적 숫자**로 표시하여, 플레이어가 **정보에 기반한 결정**을 내릴 수 있게 한다. 어려운 지역은 *피할 수 있다* (soft difficulty).

## PPL (Player Power Level)

### 정의

플레이어의 현재 장비 / 프로그램 / construct를 종합한 "힘" 수치.

### 공식

```
PPL = (deck_tier * 3)
    + sum(program_tier) * 2
    + wetware_tier
    + (construct_tier * 3 if has_construct else 0)
```

### 예시

| 자키 | 데크 | 프로그램 | 웨웨어 | Construct | PPL 계산 | PPL |
| --- | --- | --- | --- | --- | --- | --- |
| 1-up 신참 | Ono-Sendai 4 (T1) | Wisp (T1) | Standard (T1) | — | 3 + 2 + 1 + 0 | **6** |
| 2-up 일반 | Ono-Sendai 5 (T2) | Wisp (T2), Hammer (T2) | Standard (T1) | — | 6 + 4 + 1 + 0 | **11** |
| 3-up 숙련 | Ono-Sendai 6 (T3) | Wisp (T2), Goliath (T3) | Biochip (T3) | — | 9 + 10 + 3 + 0 | **22** |
| 4-up 베테랑 | Ono-Sendai 7 (T4) | Wisp (T3), Goliath (T3), Wardrone (T3) | Advanced (T4) | — | 12 + 18 + 4 + 0 | **34** |
| 5-up 전설 | Ono-Sendai 7 (T5) | Kraken (T5), Goliath (T3), Wisp (T3), Wardrone (T3) | Premium (T5) | Dixie (T5) | 15 + 28 + 5 + 15 | **63** |

### 재계산 시점

- 장비 / 프로그램 / 웨웨어 / construct 변경 시
- Prep phase 종료 시
- 런 시작 시

### 표시

**HUD**:
```
[YOU: PPL 22]
```

장비 변경 시마다 갱신.

## ZDR (Zone Difficulty Rating)

### 정의

zone / node / system의 고유 난이도.

### 공식

```
ZDR = base_zone_difficulty + ice_modifier + alarm_modifier + faction_modifier
```

### Base Zone Difficulty

매트릭스 깊이 기반:

| Zone | Base | 설명 |
| --- | --- | --- |
| **Surface (Entry)** | 1-3 | 진입점, 평이 |
| **Mid** | 4-8 | 중간 zone |
| **Core** | 9-15 | 깊은 zone |
| **T-A Straylight** | 20-30 | 최종 zone |

### ICE Modifier

| ICE | Modifier |
| --- | --- |
| 없음 | 0 |
| Standard ICE (1개당) | +2 |
| Watchdog (1개당) | +1 |
| Black ICE | +10 |
| 여러 ICE | 합산 |

### Alarm Modifier

| Alarm | Modifier |
| --- | --- |
| Low (0-25%) | 0 |
| Medium (25-50%) | +3 |
| High (50-75%) | +5 |
| Critical (75-100%) | +10 |

### Faction Modifier

| Faction | Modifier |
| --- | --- |
| 일반 | 0 |
| Hosaka | +2 |
| Maas | +3 |
| Sense/Net | +4 |
| T-A | +5 |

### 예시

| Zone | Base | ICE | Alarm | Faction | ZDR 계산 | ZDR |
| --- | --- | --- | --- | --- | --- | --- |
| Entry node | 1 | 0 | 0 | 0 | 1 | **1** |
| Mid data, 1 ICE | 5 | +2 | 0 | 0 | 7 | **7** |
| Mid data, alarm medium | 5 | +2 | +3 | 0 | 10 | **10** |
| Core with Black ICE | 12 | +10 | +5 | 0 | 27 | **27** |
| T-A Straylight | 25 | +10 | +5 | +5 | 45 | **45** |

### 표시

**Map (각 node)**:
```
[Entry: ZDR 1]    SAFE (green)
[Data: ZDR 8]     TOUGH (yellow)
[ICE: ZDR 15]     DEADLY (red)
[Core: ZDR 22]    FUTILE (dark red)
```

**HUD (combat 중)**:
```
[YOU: PPL 22]  [ZONE: ZDR 12]  Status: MATCH (1.83x)
```

## 비교 및 Status

### Ratio

```
Ratio = PPL / ZDR
```

### Status Categories

| Ratio | Status | 색상 | 의미 |
| --- | --- | --- | --- |
| > 1.5 | **SAFE** | green | 압도적 우위. 도전 보상 큼. |
| 1.0 - 1.5 | **MATCH** | cyan | 균등한 전투. |
| 0.75 - 1.0 | **TOUGH** | yellow | 불리. 손실 가능. |
| 0.5 - 0.75 | **DEADLY** | red | 매우 위험. |
| < 0.5 | **FUTILE** | dark red | 자살행위. 피할 것. |

### Status 표시

**HUD (combat)**:
```
PPL: 22   ZDR: 12   Status: MATCH (1.83x)   [cyan]
```

**Map (node별)**:
- SAFE → green
- MATCH → cyan
- TOUGH → yellow
- DEADLY → red
- FUTILE → dark red

**Entry (진입 전) — 선택**:
```
> This zone: ZDR 22 (DEADLY for your PPL 11)
> Recommendation: Disengage or upgrade equipment.
> [Continue] [Disengage]
```

## 회피 메카닉 (Avoidance)

### Soft Difficulty

- **선택적 진입**: ZDR 표시 → 플레이어가 결정
- **경로 우회**: matrix 그래프에서 다른 경로 가능
- **강제 진입 없음**: ZDR이 높아도 강제로 들어가지 않음
- **강력 추천**: FUTILE/DEADLY zone 진입 시 명시적 경고 메시지
- **완전 봉쇄 (선택, Phase 5 결정)**: FUTILE zone은 진입 불가 표시

### 회피 시 보상

- 안전 zone에서 보상 적음
- DEADLY zone 보상 큼 (위험 보상)
- FUTILE zone은 진입 권장 X (회피 OK)

### 보상 곡선

| Status | 보상 | 위험 |
| --- | --- | --- |
| SAFE | 보통 | 낮음 |
| MATCH | 좋음 | 보통 |
| TOUGH | 매우 좋음 | 높음 |
| DEADLY | 훌륭함 | 매우 높음 |
| FUTILE | 진입 X | — |

## Phase / Stage 시스템

### 의뢰 Phase

- 의뢰는 여러 phase로 구성 가능
- Phase마다 ZDR 다름
- 초기 phase: 낮음 (안전, 학습)
- 후기 phase: 높음 (도전, 보상)

### 예시 (Arc 1 의뢰)

| Phase | Zone | ZDR | 의도 |
| --- | --- | --- | --- |
| 1. 진입 | Entry | 1-3 | 학습 |
| 2. 데이터 추출 | Data | 5-8 | 메인 미션 |
| 3. 추적 회피 | Router | 8-12 | 텐션 |
| 4. 탈출 | Exit | 5-10 | 클라이맥스 |

### Phase 진행

- 플레이어가 phase를 skip하거나 backtrack 가능
- matrix에 따라 backtrack 경로 결정
- 모든 phase 완료 = 의뢰 성공

## 구현 가이드

### PPL 계산

```python
def calculate_ppl(player) -> int:
    ppl = 0
    ppl += player.deck.tier * 3
    ppl += sum(p.tier for p in player.programs) * 2
    ppl += player.wetware.tier
    if player.construct:
        ppl += player.construct.tier * 3
    return ppl
```

### ZDR 계산

```python
def calculate_zdr(zone, ice_list, alarm_level, faction) -> int:
    zdr = zone.base_difficulty
    for ice in ice_list:
        if ice.is_black:
            zdr += 10
        elif ice.is_watchdog:
            zdr += 1
        else:
            zdr += 2
    zdr += alarm_modifier(alarm_level)
    zdr += faction_modifier(faction)
    return zdr

def alarm_modifier(level: float) -> int:
    if level < 0.25: return 0
    if level < 0.50: return 3
    if level < 0.75: return 5
    return 10

def faction_modifier(faction) -> int:
    return {
        "hosaka": 2, "maas": 3, "sense_net": 4, "ta": 5
    }.get(faction, 0)
```

### Status

```python
def calculate_status(ppl: int, zdr: int) -> Status:
    if zdr == 0: return Status.SAFE
    ratio = ppl / zdr
    if ratio > 1.5: return Status.SAFE
    if ratio >= 1.0: return Status.MATCH
    if ratio >= 0.75: return Status.TOUGH
    if ratio >= 0.5: return Status.DEADLY
    return Status.FUTILE
```

## 향후 결정 (Phase 5+)

- PPL 공식 정확성 (밸런스)
- ZDR 공식 정확성
- Status 카테고리 수 (5개 vs 3개)
- Avoidance 메카닉 (강제 차단 vs soft)
- 매트릭스 깊이 / ZDR 매핑
- Phase / Stage 시스템
- 권장 메시지 (Phase 5에서)

## 관련 문서

- `decisions/0012-difficulty-rating.md` — ADR
- `decisions/0003-combat-system.md` — RT-MS
- `decisions/0005-cyberspace-representation.md` — Matrix
- `decisions/0008-progression-system.md` — Item Tier
- `decisions/0011-ascii-portraits.md` — Status 색상
- `design/pillars.md` — Pillar 1, 3, 4

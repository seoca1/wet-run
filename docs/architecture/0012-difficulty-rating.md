# ADR-0012: Combat Difficulty & Threat Level (PPL & ZDR)

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0 (Pillar 1 핵심 메카닉)

## 컨텍스트

사용자 결정 (2026-06-17):

1. **전투 난이도를 가늠할 수 있도록** — combat 전에 위험을 알 수 있어야 함
2. **장비 수준이 반영된 레벨 수치** — 또는 더 좋은 아이디어
3. **구역 / 스테이지 별로 다른 난이도** — node/zone별 ZDR
4. **어려운 지역은 피할 수 있도록** — soft difficulty, player agency
5. **수치로 파악할 수단** — 명시적 숫자 표시

기존 결정과의 관계:
- **ADR-0003 (RT-MS)** — combat 자체 결정됨. difficulty visibility 추가
- **ADR-0005 (Matrix)** — node graph 결정됨. node별 ZDR 추가
- **ADR-0008 (Item Tier)** — 장비 티어 결정됨. PPL 계산에 사용

## 결정

### PPL (Player Power Level) & ZDR (Zone Difficulty Rating)

**핵심 컨셉**:
- 두 숫자를 **명시적으로 표시**
- 비교하여 **combat 위험을 수치화**
- 플레이어가 **결정** (회피 / 진입)

#### PPL (Player Power Level)

**정의**: 플레이어의 현재 장비 / 프로그램 / construct를 종합한 "힘" 수치.

**공식**:
```
PPL = (deck_tier * 3)
    + sum(program_tier) * 2
    + wetware_tier
    + (construct_tier * 3 if has_construct else 0)
```

**예시**:

| 자키 | 데크 | 프로그램 | 웨웨어 | Construct | PPL |
| --- | --- | --- | --- | --- | --- |
| 1-up 신참 | T1 (3) | Wisp T1 (2) | Standard T1 (1) | — | **6** |
| 2-up 일반 | T2 (6) | Wisp T2 (2), Hammer T2 (2) | Standard T1 (1) | — | **11** |
| 3-up 숙련 | T3 (9) | Wisp T2, Goliath T3 (6) | Biochip T3 (3) | — | **20** |
| 4-up 베테랑 | T4 (12) | Wisp T3, Goliath T3, Wardrone T3 (6) | Advanced T4 (4) | — | **25** |
| 5-up 전설 | T5 (15) | Kraken T5, Goliath T3, Wisp T3, Wardrone T3 (16) | Premium T5 (5) | Dixie T5 (15) | **51** |

**재계산 시점**: 장비 / 프로그램 / 웨웨어 / construct 변경 시.

**표시**: HUD에 항상 표시.

#### ZDR (Zone Difficulty Rating)

**정의**: zone / node / system의 고유 난이도.

**공식**:
```
ZDR = base_zone_difficulty + ice_modifier + alarm_modifier + faction_modifier
```

**Base Zone Difficulty** (매트릭스 깊이 기반):
- Surface (진입점): 1-3
- Mid (중간 zone): 4-8
- Core (깊은 zone): 9-15
- T-A Straylight: 20-30

**ICE Modifier**:
- 없음: 0
- Standard ICE 1개당: +2
- Black ICE: +10
- Watchdog: +1

**Alarm Modifier**:
- Low: 0
- Medium: +3
- High: +5
- Critical: +10

**Faction Modifier**:
- 일반: 0
- Hosaka: +2
- Maas: +3
- Sense/Net: +4
- T-A: +5

**예시**:

| Zone | Base | ICE | Alarm | Faction | ZDR |
| --- | --- | --- | --- | --- | --- |
| Surface entry | 1 | 0 | 0 | 0 | **1** |
| Mid data node | 5 | +2 (1 ICE) | +3 (med) | 0 | **10** |
| Core with Black ICE | 12 | +10 (black) | +5 (high) | 0 | **27** |
| T-A Straylight | 25 | +10 (black) | +5 (high) | +5 | **45** |

**표시**: 매트릭스 맵에 node별 ZDR 표시 (숫자 + 색).

#### 비교 및 Status

**Ratio = PPL / ZDR**

| Ratio | Status | 색상 | 의미 |
| --- | --- | --- | --- |
| > 1.5 | **SAFE** | green | 압도적 우위. 도전 보상 큼. |
| 1.0 - 1.5 | **MATCH** | cyan | 균등한 전투. |
| 0.75 - 1.0 | **TOUGH** | yellow | 불리. 손실 가능. |
| 0.5 - 0.75 | **DEADLY** | red | 매우 위험. |
| < 0.5 | **FUTILE** | dark red | 자살행위. 피할 것. |

**표시 위치**:
- **HUD**: PPL 항상 표시 + 현재 zone의 ZDR (combat 시)
- **Map**: node별 ZDR + Status 색상
- **Entry**: 진입 전 비교 표시 (선택 가능)
- **Combat**: HP 바 색상 변화 (status 반영)

**예시 HUD**:
```
[YOU: PPL 20]  [ZONE: ZDR 12]  Status: MATCH (1.67x)
```

**예시 Map**:
```
[Entry: ZDR 1]  ─[Router: ZDR 5]─  [Data: ZDR 8] (TOUGH)
                       │
                 [ICE: ZDR 15] (DEADLY for current PPL)
                       │
                 [Core: ZDR 22] (FUTILE for current PPL)
```

#### 회피 메카닉 (Avoidance)

- **선택적 진입**: ZDR 표시 → 플레이어가 결정
- **경로 우회**: matrix 그래프에서 다른 경로 가능
- **강제 진입 없음**: ZDR이 높아도 강제로 들어가지 않음
- **강력 추천 (선택)**: FUTILE/DEADLY zone 진입 시 명시적 경고 메시지
- **완전 봉쇄 (선택)**: FUTILE zone은 진입 불가 표시 — 결정 보류 (Phase 5에서)

#### Phase / Stage 난이도

- 의뢰는 여러 phase로 구성 가능
- Phase마다 ZDR 다름
- 초기 phase: 낮음 (안전)
- 후기 phase: 높음 (도전)
- 플레이어가 phase skip / backtrack 가능 (matrix에 따라)

#### Soft Difficulty vs Hard Difficulty

이 시스템은 **soft difficulty**:
- 정보 제공 (숫자)
- 선택권 (회피)
- 강제 진입 없음

Hard difficulty (자동 사망 등)는 **비-기둥** (Pillar 4, 5 위반).

### Pillar 정합

- **P1 (The Run)**: PPL은 동일 시작 (등급 외). 런 중 PPL은 변할 수 있음 (장비 변경).
- **P3 (The Flatline)**: FUTILE은 명시적 경고. 자살행위 명시.
- **P4 (The Build)**: PPL이 unlock / 장비 변경으로 상승.
- **P5 (The Style)**: 숫자 + 색 = 깁슨 톤의 "tech UI" — ASCII로 표현.

## 결과 (Consequences)

### 기존 ADR 영향
- **ADR-0003 (RT-MS)**: combat 진입 시 ZDR / PPL 비교 표시
- **ADR-0005 (Matrix)**: node에 ZDR 추가
- **ADR-0008 (Item Tier)**: PPL 계산에 사용
- **ADR-0011 (ASCII Portraits)**: Status 색상과 정합

### 디자인 영향
- **core_loop**: combat 진입 전 비교 표시
- **glossary**: PPL, ZDR, Status, Ratio 등
- **Pillar 1**: PPL 시작 동일 명시
- **새 시스템**: `design/systems/difficulty-rating.md`

### 구현 영향
- PPL 계산 함수
- ZDR 계산 / 표시
- 매트릭스 맵 ZDR 표시
- HUD PPL 표시
- 비교 / Status 표시
- Color coding

### 향후 결정
- PPL 공식 정확성 (밸런스)
- ZDR 공식 정확성
- Status 카테고리 수 (5개 vs 3개)
- Avoidance 메카닉 (강제 차단 vs soft)
- 매트릭스 깊이 / ZDR 매핑
- Phase / Stage 시스템

## 영향 받는 항목

- `design/systems/difficulty-rating.md` (신규)
- `design/systems/combat.md` (전투 명세)
- `design/systems/inventory.md` (PPL)
- `design/systems/missions.md` (의뢰 phase / ZDR)
- `core_loop.md`
- `glossary.md`
- `pillars.md`

## 관련 결정

- ADR-0003 (Accepted, Revised)
- ADR-0005 (Accepted)
- ADR-0008 (Accepted, Revised)
- ADR-0011 (Accepted)

## 변경 이력

- 2026-06-17: 사용자 요청 → Accepted

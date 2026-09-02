# ADR-0006: 런 구조 (로그라이크 vs 로그라이트)

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P0

## 컨텍스트

게임이 순수 로그라이크인지, 로그라이트인지 결정해야 한다. 결정은 다음에 영향을 미친다:
- Pillar 3 (The Flatline) — 죽음의 무게
- Pillar 4 (The Build) — 메타 진행
- 게임의 replayability
- 한 번의 플레이 길이

## 고려한 옵션

### Option 1: 순수 로그라이크 (하드 로겜)

- **설명**: 죽으면 영구 종료. 메타 진행 없음 (또는 매우 적음). 매 런이 동일 캐릭터로 시작.
- **장점**:
  - Pillar 3 (The Flatline) 최대 부합
  - 깁슨 톤 ("flatline = 영구 사망")
  - 한 런의 무게
  - 클래식 로그라이크 표준
- **단점**:
  - 일부 플레이어에게 너무 가혹
  - 메타 진행이 없어 replayability 약화 가능
  - 신규 플레이어 진입장벽
- **Pillar 정합**:
  - P3: ⭐⭐⭐⭐⭐
  - P4: 메타 진행 없음 또는 매우 적음

### Option 2: 로그라이트 (메타 진행 강함)

- **설명**: 죽으면 메타 진행은 유지. 더 좋은 장비 / unlock / 능력 영구 축적.
- **장점**:
  - 신규 플레이어 친화
  - replayability
  - 메타 진행의 보상
- **단점**:
  - Pillar 3 약화 — 죽음이 덜 무거움
  - "다음 런이 더 쉬워짐" 회피 어려움
  - 깁슨 톤과 거리
- **Pillar 정합**:
  - P3: ⭐⭐ 약화
  - P4: ⭐⭐⭐⭐⭐

### Option 3: 하이브리드 (메타 진행은 unlock만) — 추천

- **설명**: 죽으면 메타 진행의 **unlock**은 유지. 하지만 **능력 강화 / 누적 보너스**는 없음. 매 런 = 동일 시작점.
- **예시**:
  - 매트릭스에 처음 진입한 자키가 매번 다른 장비를 발견
  - 메타 진행: 새 데크, 새 프로그램, 새 construct, 새 픽서, 새 의뢰 라인 unlock
  - 메타 진행 X: 스탯, 강화, 누적 보너스
  - 한 번 unlock한 것은 다시 사용할 수 있으나, 강해지지는 않음
- **장점**:
  - Pillar 3 (The Flatline) 유지
  - Pillar 4 (The Build) 만족
  - 깁슨 톤 — 자키는 더 많은 도구를 얻지만, 더 강해지지는 않음
  - 클래식 로그라이크 + unlock 보상
  - Cogmind 스타일
- **단점**:
  - 메타 진행의 양이 적절해야 함
  - unlock 디자인 필요
- **Pillar 정합**:
  - P3: ⭐⭐⭐⭐
  - P4: ⭐⭐⭐⭐⭐
  - P5: ⭐⭐⭐⭐

### Option 4: 다중 캐릭터 (Deathless vs Berserk)

- **설명**: 여러 자키 캐릭터. 캐릭터마다 고유 능력. 죽으면 다른 캐릭터로.
- **장점**:
  - 다양성
  - 메타 진행 없음
  - Pillar 3 유지
- **단점**:
  - 디자인 복잡
  - 절차적 생성과 어색할 수 있음
- **Pillar 정합**:
  - P3: ⭐⭐⭐⭐⭐
  - P4: ⭐⭐⭐

## 추천

**Option 3: 하이브리드 (unlock만)** (Pillar 3, 4 균형)

근거:
- Pillar 3 (The Flatline) 유지
- Pillar 4 (The Build) 만족
- 1인 개발에 적합 (unlock 디자인은 한 번만)
- 클래식 로그라이크 + 메타 보상
- 깁슨 톤 — "더 많은 도구"는 OK, "더 강함"은 NO

## 메타 진행 디자인 (Option 3)

### Unlock (영구)
- **데크**: Ono-Sendai Cyberspace 7, SAMSARA, Eldritch 등
- **프로그램**: Goliath, Kraken, Wisp, Wardrone, Hammer 등
- **웨웨어**: 신경 잭, 강화 모듈, biochip 등
- **Construct**: Dixie, 사용자 정의 AI
- **픽서**: 새로운 픽서 / 의뢰 라인
- **의뢰**: 새로운 의뢰 템플릿 (예: T-A 라인, Sense/Net 라인)

### 영구 X
- 스탯 강화
- 누적 보너스
- "다음 런이 더 쉬워짐"

## 사용자 결정

[x] **Option 3: 하이브리드 (unlock만)** (2026-06-17)

## 결과 (Consequences)

### 런 구조
- **한 런 = 한 자키의 한 의뢰**
- **죽음 = 게임 오버** (그 자키 영구 종료, 메타 진행은 unlock만 유지)
- **메타 진행 = unlock**
  - 새 데크 (Ono-Sendai 7, SAMSARA 등)
  - 새 프로그램 (Goliath, Kraken, Wisp, Wardrone 등)
  - 새 웨웨어 (신경 잭, 강화 모듈, biochip)
  - 새 construct (Dixie 류)
  - 새 픽서 / 의뢰 라인
- **메타 진행 X**
  - 스탯 영구 강화
  - 누적 보너스
  - "다음 런이 더 쉬워짐"
  - 능력치 누적 (HP, BW, PW 등)

### Pillar 정합
- P3 (The Flatline): "flatline" = 영구 사망, 무게 유지
- P4 (The Build): unlock으로 보상, 도구 확장으로 표현
- P5 (The Style): "더 많은 도구"는 OK, "더 강함"은 NO

### 구현 영향
- 자키 프로필은 unlock 상태만 저장 (스탯 X)
- 사망 시 프로필 = unlock 목록 (강화 X)
- 새 자키 = 기본 상태 + unlock으로 사용 가능

### 향후 결정
- unlock 트리 디자인 (어떤 unlock이 어떤 unlock을 요구하는가)
- 자키 등급 시스템 (ADR-0008에서 결정)
- "죽음 후 묘사" 텍스트

## 영향 받는 항목

- ADR-0008 (진행 시스템): unlock 트리 디자인 필요
- `design/systems/progression.md`: 메타 진행 명세
- `design/GDD.md` Open Questions 갱신

## 관련 결정

- ADR-0008 (Pending)

## 변경 이력

- 2026-06-17: Draft 작성
- 2026-06-17: Accepted (Option 3: 하이브리드 unlock만)

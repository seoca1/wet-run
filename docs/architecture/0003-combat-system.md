# ADR-0003: 전투 시스템 — Real-Time with Menu Skills (RT-MS)

**상태**: Accepted (Revised 2026-06-17)
**날짜**: 2026-06-17 (Revised 2026-06-17)
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트

### 사용자 결정 (2026-06-17 갱신)

원래 결정: AP 턴 (턴 기반 + AP). 사용자 갱신 결정:

1. **전투는 메뉴 선택 방식** — 플레이어가 직접 스킬을 선택
2. **단조로운 멈춤 비주얼 X** — 자동 공격이 지속적으로 오가는 *움직임*이 있어야 함
3. **강력한 공격은 메뉴 스킬** — 일반 공격은 자동, 강력한 것은 메뉴
4. **쉬운 방식** — 복잡한 입력 X, 명확한 피드백

**원본 컨텍스트**:
매트릭스 안에서 전투(ICE / 적 deckers와의 대결)가 어떻게 진행되는지 결정. 결정은 다음에 영향을 미친다:
- 게임의 페이스와 텐션
- 매트릭스의 "데이터 흐름" 표현
- Pillar 1, 3, 4, 5

## 결정

### Real-Time with Menu Skills (RT-MS)

**핵심 컨셉**:
- **실시간 전투** (턴 X)
- **자동 공격 (Normal Attack)**: 양쪽 모두 일정 간격으로 자동 — 시각적 움직임 지속
- **메뉴 스킬 (Skill)**: 플레이어가 키 입력으로 메뉴 열기 → 시간 정지/감속 → 강력한 스킬 선택
- **쉬운 조작**: 한 키로 메뉴, 화살표로 선택, Enter로 실행

**메카닉**:

#### 자동 공격 (Auto-Attack)
- 양쪽 (플레이어 + 적)이 일정 간격으로 자동 공격
- 기본 데미지 / 기본 속도
- 시각: ASCII 깜빡임, 사이드 이동, 데미지 숫자
- 한쪽 HP 0 또는 플레이어가 결정할 때까지 지속

#### 메뉴 스킬 (Skill)
- 키 입력 (예: `Space`) → 메뉴 열림
- **시간 일시 정지** (또는 매우 감속)
- 사용 가능한 스킬 목록 (AP 비용, 효과)
- 플레이어 스킬 선택 → 시간 재개, 스킬 실행
- **명확한 피드백**: 데미지, 효과, 자원 변화 표시

#### 자원 (Resources)
- **HP** (Health / Integrity): 생존
- **AP** (Action Points): 스킬 비용, 시간 경과로 자동 회복
- **BW** (Bandwidth): 동시 활성 프로그램 수
- **PW** (Processing Power): 프로그램 복잡도 한계

### 비주얼 디자인

#### 전투 화면
```
[Player]              [Enemy]
◉P◉                   ▲ICE▲
[▓▓▓▓▓░░░] HP 50/100  [▓▓▓▓▓▓▓▓] HP 80/100
[█] AP 4/6            (ICE: AP N/A)

Action log:
> You hit ICE for 5 damage.
> ICE hits you for 3 damage.
> You hit ICE for 5 damage.

[SPACE] for skills   [ESC] to disengage
```

#### 메뉴 (일시 정지 시)
```
=========================
        MENU
=========================
Skills available (AP 4/6):

> GOLIATH    (3 AP)  - heavy attack
  WISP       (2 AP)  - shield (active)
  WARDRONE   (2 AP)  - auto-counter (active)
  PROBE      (1 AP)  - reveal enemy
  VIRUS      (2 AP)  - DoT
  CANCEL

↑/↓ select, ENTER confirm
=========================
```

#### 애니메이션 (단조로움 방지)
- **자동 공격**: 0.2초 깜빡임 + 데미지 숫자 표시
- **스킬 발동**: 0.5초 효과 (브래킷 변경, 색 변화, 큰 데미지)
- **메뉴 열림**: 화면 dim, 메뉴 박스 fade-in
- **HP 변화**: HP 바 색 변화 (녹→황→적)
- **상호작용**: 적 공격 시 화면 흔들림 효과 (ASCII)
- **효과음 (있다면)**: 공격 = 단타, 스킬 = 더 긴 호

### Programs (메뉴 스킬)

원작의 program들을 메뉴 스킬로 매핑:

| Program | Type | AP | 효과 |
| --- | --- | --- | --- |
| **Goliath** | Attack | 3 | heavy hit (3x base) |
| **Kraken** | Attack | 4 | strongest attack |
| **Hammer** | Attack | 2 | medium attack |
| **Virus** | Attack | 2 | DoT (3 ticks) |
| **Worm** | Attack | 2 | multi-hit (2-3 hits) |
| **Wisp** | Defense | 2 | shield +1 (active) |
| **Wardrone** | Defense | 2 | auto-counter (active) |
| **Shield** | Defense | 1 | one-time block |
| **Watchdog** | Detect | 1 | reveal enemy next attack |
| **Probe** | Detect | 1 | show enemy HP / skill |
| **Hellhound** | Track | 3 | forced engagement |

### Combat Flow

```
[Matrix: encounter ICE]
  ↓
[Combat begins: real-time, auto-attack starts]
  ↓ (continuous)
[Auto-attack ticks: 양쪽 자동 공격]
  ↓ (player presses SPACE anytime)
[Menu: time pauses]
  ↓
[Player selects skill]
  ↓
[Time resumes, skill executes]
  ↓
[Combat continues until: ICE HP 0 OR player HP 0 OR player disengages]
  ↓
[Result: continue matrix / extraction / flatline]
```

### 다중 적 (Multiple Enemies)
- 1-3 적 동시 (드물게)
- Tab으로 타겟 전환
- AOE 스킬은 모두에게 적용
- 시각: 여러 portrait, 선택된 것 강조

### 시간 정지 vs 감속

**선택 옵션** (Phase 5에서 결정):
- **Pause (시간 정지)**: 명확, 반응 시간 충분, 단 "단조로움" 위험
- **Slow (시간 감속 1/4)**: "단조로움" 해결, 그러나 더 복잡

**권장**: Pause (기본) — 사용자가 "쉬운 방식" 명시. Phase 5에서 Slow 옵션 추가 고려.

## 결과 (Consequences)

### Pillar 정합
- **P1 (The Run)**: combat은 한 런의 일부, 메인 루프의 미시 루프 일부
- **P2 (The Matrix)**: 전투는 매트릭스 안의 표현, ASCII portrait (ADR-0011)
- **P3 (The Flatline)**: HP 0 = flatline, 무게 유지
- **P4 (The Build)**: 더 좋은 프로그램 = 더 강한 combat (장비 기반)
- **P5 (The Style)**: ASCII 비주얼, 깁슨 톤

### 기존 ADR 영향
- **ADR-0008 (진행)**: 장비/아이템 티어가 combat 강도 결정 (Pillar 4)
- **ADR-0005 (사이버스페이스)**: 매트릭스 안의 전투 — 노드 간 이동은 별개 메카닉
- **ADR-0011 (ASCII Portraits)**: portrait 표시 — player, ICE, programs

### 디자인 영향
- **core_loop**: combat flow 갱신 (실시간 + 메뉴)
- **glossary**: RT-MS, auto-attack, AP, BW, PW 등
- **Pillar 4**: 장비/프로그램 강조

### 구현 영향
- 실시간 게임 루프 (60 fps)
- 자동 공격 타이머 (entity별)
- 메뉴 시스템 (일시 정지, 선택, 실행)
- ASCII 애니메이션 (깜빡임, 이동, 색)
- Program 데이터 (AP, 효과, BW)
- AI: 적의 자동 공격 + 스킬 사용 결정

### 향후 결정
- 자동 공격 속도 (1-2초)
- AP 회복 속도
- 메뉴 키 (Space vs Tab)
- 다중 적 UI
- 시각 효과 디테일 (Phase 5+)

## 영향 받는 항목

- `design/systems/combat.md` (전투 명세, 작성 필요)
- `design/core_loop.md` (combat flow)
- `design/glossary.md` (용어)
- `design/pillars.md` (Pillar 4)

## 관련 결정

- ADR-0001 (엔진 — python-tcod은 실시간 게임 루프 지원)
- ADR-0002 (Pure ASCII)
- ADR-0004 (ECS-lite — combat component)
- ADR-0005 (Cyberspace)
- ADR-0006 (Run structure)
- ADR-0008 (Progression — 장비 기반)
- ADR-0009 (Story — combat 결과)
- ADR-0011 (ASCII Portraits)

## 변경 이력

- 2026-06-17: Draft (AP 턴)
- 2026-06-17: Accepted (Option 3: AP 턴)
- 2026-06-17: **Revised** — Real-Time with Menu Skills (사용자 결정). AP 턴 폐기, 실시간 + 메뉴 스킬 방식으로 재설계.

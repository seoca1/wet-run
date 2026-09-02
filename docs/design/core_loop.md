# Core Loop (핵심 게임 루프)

## 매크로 루프 (런 사이)

> **중요 (ADR-0009)**: meatspace는 절대 시각화되지 않음. Hub (Job Board, Prep, 픽서 대화)는 모두 cyberspace 안의 텍스트 인터페이스.

```
[메인 메뉴] (real-world UI, 8 options, Phase 17)
    |   - 1. NEW RUN              (자키 선택)
    |   - 2. GRAPHIC NOVEL        (ADR-0032, 스토리 자동재생)
    |   - 3. CONTINUE             (마지막 세이브 로드)
    |   - 4. SETTINGS             (telemetry opt-in, accessibility 등)
    |   - 5. CREDITS
    |   - 6. HALL OF DEAD         (자키 아카이브, ADR-0040)
    |   - 7. HELP                 (Phase 7 온보딩)
    |   - 8. STATS                (Phase 17, telemetry opt-in 시 활성)
    v
[Character Select] ---> 자키 선택 (NG+ 가능 시 N-key 토글)
    v
[Deck Select] (Phase 15) ---> LIGHT / STANDARD / HEAVY 중 선택
    v
[Hub: Cyberspace Construct] (text-based)
    |   - 픽서 construct (의뢰 briefing)
    |   - Job Board (의뢰 선택, Phase 16: select_weighted cursor bias)
    |   - Deck Config (프로그램/웨웨어)
    |   - Info Market (의뢰 정보 구매)
    v
[Run: 매트릭스 진입]
    |   (text transition: "you jack in. the world goes gray.")
    v
[Matrix Phase] ---> 해킹, 전투, 데이터 탈취 (Phase 17: F.4 보스 phase 진입 시 HUD 1.5s 블렌드)
    v
[Extraction / Death]
    |   (성공: "you pull out, heart racing." Phase 16: record_run_completed opt-in)
    |   (실패: "you flatline. static. silence." Phase 16: record_death + record_run_completed opt-in)
    v
[Result + Story] ---> 보상, 새 story
    v
[메인 메뉴] (또는 Hub로)
```

## 미시 루프 (런 내부)

```
[시스템 탐색 (Navigation)] ---> 노드 그래프 위 이동
    |
    v
[Node 발견] ---> 파일, ICE, construct, 다른 자키
    |
    v
[Decision] ---> 해킹? 회피? 전투? 후퇴?
    |
    v
[Action] ---> 결과 (성공/실패/전투 진입)
    |
    v
[Combat (RT-MS)] ---> 실시간 자동 공격 + 메뉴 스킬 (ADR-0003)
    |
    v
[State Update] ---> 알람 레벨, ICE 패턴, HP
    |
    v
[시스템 탐색 (Navigation)] ---> 다음 노드
```

### Combat 미시 루프 (ADR-0003 — RT-MS)

```
[전투 진입: ICE / 적 decker 발견]
    |
    v
[실시간 시작: 양쪽 자동 공격 tick]
    |   (1 attack / 2초, 양쪽 동시)
    v
[Auto-Attack tick] ---> 양쪽 데미지 교환
    |   (시각: 깜빡임, 데미지 숫자, ASCII 이동)
    v
{플레이어가 Space 입력?}
    |   Yes ↓          No ↓ (계속 tick)
    v
[메뉴 열림: 시간 정지]      [Auto-Attack tick 계속]
    |
    v
[스킬 선택: Goliath / Wisp / Probe / ...]
    |
    v
[시간 재개: 스킬 실행]
    |
    v
[Auto-Attack tick 계속]
    |
    v
[전투 종료: ICE HP 0 OR Player HP 0 OR Disengage]
    |
    v
[ICE 격파 시: Data Salvage 메뉴 — 시간 정지 유지 (ADR-0014)]
    |
    > HEAL   +20% max HP (Phase 5)
      FRAG   program fragment (Phase 6+)
      CRED   credits (Phase 6+)
      SKIP   no reward
    |
    v
[매트릭스 복귀]
```

## 디자인 의도

### 매크로 루프
- **짧다** — 한 런은 30~60분
- **명확하다** — 시작과 끝이 분명
- **의미 있다** — 매 런이 다른 의뢰, 다른 시스템, 다른 보상

### 미시 루프
- **빠르다** — 한 노드는 30초~2분
- **결정의 무게** — 매 노드에서 의미 있는 선택
- **긴장감** — 알람 / trace / ICE 패턴

### 시간
- **매트릭스 안** — 시간이 빠르게 흐름 (UI 카운트다운)
- **meatspace** — 정적, 거래 / flavor
- **결과** — 차분하게 (정적 화면 + 텍스트)

## Prep Phase 디테일

런 직전, **cyberspace 안의 텍스트 인터페이스**에서:

1. **데크 로드** — Ono-Sendai / SAMSARA 등 (메타 진행으로 unlock)
2. **프로그램 슬롯** — 4-6개 슬롯, 어떤 프로그램 가져갈지 선택
3. **웨웨어** — 신경 잭 / 강화 / biochip
4. **정보 구매** — 픽서 construct에게 의뢰 정보 (돈/시간 소모)
5. **Construct 선택** — Dixie 류 (메타 진행으로 unlock)

런이 시작되면 더 이상 변경 불가 (Pillar 1: The Run).

> **ADR-0009**: Prep는 "픽서와의 대화"를 통해 이루어짐. 픽서는 cyberspace의 construct. 텍스트로만 표현됨.

## 미션 종료 조건

### 성공
- 타겟 데이터 추출
- 타겟 시스템 파괴
- 타겟 construct 추출
- 미션 타입별 고유 조건

### 실패 (flatline, ADR-0003 RT-MS)
- **HP 0** (combat에서)
- **trace 성공** (위치 추적, alarm 만료)
- **black ICE 치명타** (HP 큰 손실 또는 즉시 flatline)
- **의뢰 시간 초과** (옵션)

## 알람 / Trace 메카닉 (구현됨)

매트릭스 안에서 시간을 지날수록 위험 증가 (6단계 알람):

| 레벨 | 상태 | ICE 배치 |
|------|------|----------|
| 0 | 평온 | 없음 |
| 1 | 인지 | 기본 ICE |
| 2 | 정찰 | watchdog |
| 3 | 추적 | hellhound |
| 4 | Black ICE | trace 진행 |
| 5 | Trace 완료 | flatline 임박 |

알람은 ZDR의 alarm_modifier에 영향 (ADR-0012).

## PPL & ZDR (Difficulty Visibility, ADR-0012)

Combat 진입 전 / 중, 플레이어는 두 숫자로 위험을 파악:

- **PPL** (Player Power Level): 자키의 현재 힘
- **ZDR** (Zone Difficulty Rating): 현재 zone의 위험
- **Status** (SAFE / MATCH / TOUGH / DEADLY / FUTILE): 비교 결과

### Combat 진입 전 표시

```
> You approach: [Zone: T-A Straylight]
> ZDR: 45 (DEADLY for your PPL 22)
> Recommendation: Disengage or upgrade.

[Continue] [Disengage]
```

### Combat 중 HUD

```
[YOU: PPL 22]  [ZONE: ZDR 12]  Status: MATCH (1.83x)
◉P◉ [▓▓▓▓▓░░░] HP 50/100     ▲ICE▲ [▓▓▓▓▓▓▓▓] HP 80/100
```

### 회피 (Avoidance)

- **Soft difficulty**: 강제 진입 X
- **FUTILE zone**: 강력 경고, 권장 X
- **보상 곡선**: 위험한 zone = 더 큰 보상

## Open Questions (2026-07-08 기준)

아래 질문들은 Phase 7 완료 시점에서 아직 열린 것들:

| 질문 | 상태 | 비고 |
|------|------|------|
| 한 런의 목표 길이 (30/60/90분) | ⏳ 열린 질문 | 플레이어 피드백 필요 |
| Construct 동료 시스템 (Dixie 류) | ⏳ 열린 질문 | dialogue만 구현, 실제 동료 아님 |
| 엔드 게임: T-A 결산 이후 | ⏳ 열린 질문 | Salvation Phase (ADR-0090) 일부 구현 |
| 무한 모드 / New Game+ | ⏳ 열린 질문 | Phase 10 이후 고려 |

**이미 해결된 질문들**:
- ✅ Hub 표현 → 텍스트 메뉴 (cyberspace construct)
- ✅ 메타 진행 → unlock 중심 (ADR-0008)
- ✅ 시간 시스템 → 실시간 + RT-MS combat
- ✅ 다중 의뢰 → 한 런 = 한 의뢰 (Pillar 1)
- ✅ Pillar 4 경계 → unlock은 메타, 평가는 런 내
- ✅ Story Archive → 4 카테고리 + StoryEvents (ADR-0009)

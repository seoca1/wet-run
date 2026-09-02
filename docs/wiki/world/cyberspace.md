# Cyberspace (The Matrix)

> **Primary source**: `../../../../Fiction/wiki/settings/cyberspace.md` (깊은 분석), `../../../../Fiction/wiki/works/neuromancer.md` (원문 인용)
>
> 본 페이지는 게임용 요약. 원작의 모든 디테일은 Fiction wiki 참조.
>
> **2026-08-08 갱신 (Phase 83)**: Cyberspace coinage 의 원본 — Fiction wiki `burning-chrome-story.md` (Phase 73 심화로 2 sections 추가: "The 1982 Coinage of 'Cyberspace'" + "Jack-Bobby-Rikki Triangle as Origin-Cast") 가 본 게임의 메인 플레이 공간의 기원 분석 source. 게임 미션 (예: `aleph_fragment`, `tutorial_maze`, `ice_run`) 의 cyberspace 톤 / ICE 적응 의 reference.

깁슨 소설에서 가장 중요한 컨셉. 우리 게임의 메인 플레이 공간.

## 정의

> "Cyberspace. A consensual hallucination experienced daily by billions of legitimate operators, in every nation, by children being taught mathematical concepts... A graphical representation of the data abstracted from the banks of every computer in the human system. Unthinkable complexity. Lines of light ranged in the nonspace of the mind, clusters and constellations of data. Like city lights, receding..."
> — Neuromancer, Opening (Case의 설명)

- 데이터의 의식적 환각 (consensual hallucination)
- 모든 컴퓨터 시스템의 추상화된 시각 표현
- 콘솔 카우보이는 데크에 연결되어 이 공간을 항해
- "Lines of light ranged in the nonspace of the mind" — 깁슨의 기하학적 묘사

## 원작의 추가 디테일 (Fiction wiki)

> **상세 분석**: `../../../../Fiction/wiki/settings/cyberspace.md`

- **인터페이스**: 신경 전극(trodes / microsofts) → cyberdeck → 매트릭스
- **체감**:
  - 시각: 데이터 = 기하학적 형상, 빛의 선, 색깔별 ICE
  - 공간: 무한 가상 공간의 항해
  - 신체: 시스템 침투 시 물리적 피드백 (통증, 충격, 열)
- **데이터 시각화**:
  - 기업 시스템 = 기하학적 요새, 탑, 도시
  - ICE = 벽, 장벽, 능동적 대응 체계
  - 데이터베이스 = 빛나는 정보 클러스터
  - AI construct = 고유한 존재감 (Wintermute는 다양한 형태)

## 특성

### 시각
- 기하학적: 무한 그리드, 회전하는 폴리곤, 빛의 구
- "Bright points of light" — 데이터 클러스터
- 색: 검은 배경 + 형광 그린 / 시안 / 마젠타 / 노랑
- "Receding like city lights" — 원근감

### 진입
- "Jacking in" — 데크에 접속, 의식 잃음
- 몸은 의자에, 시뮬레이트된 신경 자극으로 매트릭스 진입
- 사이드 이펙트: 실신, 두통, 중독 ("jacking burnout")
- Simsense(simstim) — 다른 사람의 감각을 공유

### 위험
- **ICE (Intrusion Countermeasures Electronics)** — 시스템 방어선
- **Black ICE** — 치명적 방어, 사용자를 flatline 시킬 수 있음
- **Trace** — 물리적 위치 추적 중
- **Flatline** — 데미지가 신경계를 태우면 의식 영구 손실

### 심리
- Construct에 너무 오래 노출 시 트라우마
- "wet" — 매트릭스 의식, "I'm in the wet"
- 일부 사용자는 매트릭스 선호, 일부는 meatspace 선호

## 소설 속 묘사 (참고)

> "The matrix has its roots in primitive arcade games, in early graphics programs and military experimentation with cranial jacks."
> — Neuromancer

> "Cyberspace, not the real world... something that has no analogue in the real. A toy of the mind..."
> — Neuromancer

## 게임화 가능성 (ADR-0009 제약)

> **meatspace는 절대 시각화되지 않음**. 아래 모든 활동은 *cyberspace 안*에서만 일어난다.

### 어떤 메카닉이 사이버스페이스의 톤을 살릴까?

1. **항해 (Navigation)** — 노드 그래프 위를 이동 (ADR-0005)
   - 그리드 / 노드 그래프 위를 이동
   - 노드에서 노드로 (시각화: 빛의 선, 데이터 패킷)
   - 깊이 들어갈수록 시스템의 코어로

2. **전투 (Combat)** — AP 턴 (ADR-0003)
   - ICE / 적 deckers와 대결
   - 프로그램: Goliath, Kraken, Hammer vs Wisp, Wardrone
   - AP 소모, 다이나믹 전투

3. **해킹 (Hacking)**
   - 파일 추출, 시스템 조작
   - 알람 레벨 / trace 진행
   - 미니게임 또는 단순 stat 체크

4. **인지 (Cognition)** — Construct와의 상호작용
   - Dixie, neuromancer 등
   - 정보 / 조언 / 노하우

### Hub / Prep / 픽서 (ADR-0009)

Hub는 **cyberspace 안의 텍스트 인터페이스**로 표현됨:
- 픽서 construct: 텍스트 대화 (그를 묘사하지 않음)
- Job Board: 텍스트 메뉴
- Deck Config: 텍스트 메뉴
- Info Market: 텍스트

이는 "meatspace가 시각화되지 않는다"는 제약을 *위반하지 않음*. Hub는 cyberspace 안의 UI일 뿐, meatspace가 아님.

### meatspace — *보이지 않음*

meatspace는 게임에서 *어떤* 직접적 묘사도 하지 않는다:
- 픽서의 외모, 음성, 행동 X
- 플레이어 캐릭터의 외모, 음성, 행동 X
- 도시, 거리, 바, 카페, 사람 X
- "Finn walked into the bar" 같은 묘사 X

meatspace는 *오직* Story Archive의 텍스트로만 존재한다 (ADR-0009).

## 게임 시각화 권장 (Pure ASCII, ADR-0002)

- **ASCII**: 검은 배경 + 형광 컬러, "lines of light" 표현
- 노드: `[X: 라벨]`
- 연결: `|` `/` `\`
- 미발견: `?`
- 플레이어: `*` 또는 `@`
- 효과: 깜빡임, 색 반전, 컬러 시프트

## 사회적 구조 (원작)

- **Console cowboys**: 자키. 사이버스페이스 항해자. 아웃사이더.
- **Legitimate operators**: billions. 위생처리된 안전한 매트릭스 사용.
- **AIs**: Turing Law에 구속된 매트릭스 토착 지성.

> **상세**: Fiction/wiki/settings/cyberspace.md "Social Structure" 섹션 참조.

## 분위기 / 톤 (원작)

- **아름다운**: "Bright lattices of logic unfolding across that colorless void"
- **중독성**: Case는 잠에서라도 매트릭스를 꿈꿈
- **위험**: Black ICE는 죽일 수 있음; 기업 보안은 치명적
- **해방적**: "meat prison"에서 벗어남
- **차가움**: 따뜻함, 촉각 없는 순수 정보의 영역

## 원작과의 정합성

- 매트릭스는 "기하학적" — 추상화된 3D 공간
- 데이터는 "빛" — 형광색
- 시스템은 "도시" — 노드들이 거리처럼 펼쳐짐
- 사용자는 "항해자" — 이동, 탐색, 마주침
- "Outside" the matrix는 *항상* mediated (텍스트, 뉴스, construct 기억)

## 상징적 의미 (원작)

- **신화적 변두리**: "새로운 아메리칸 변두리" — 법의 손길이 닿지 않는 곳
- **그노시스적 초월**: 물질 세계(meat)에서 벗어나 순수 빛/정보의 영역으로
- **후기 자본주의의 인프라**: 매트릭스는 중립적이지 않음 — 기업이 소유, 방어, 통제
- **중독과 욕망**: Case에게 매트릭스는 도구가 아니라 강박

> **상세**: Fiction/wiki/settings/cyberspace.md "Symbolic Function" 참조.

## Open Questions
- 매트릭스의 "물리 법칙" — 중력? 관성? 모두 비현실적?
- 시점 — 1인칭? 위에서 내려다보기? 자유 시점?
- Hub의 표현 — 텍스트 메뉴만? 작은 노드 그래프?
- Story Archive의 카테고리 세부 디자인
- "Lines of light" 효과 — ASCII 깜빡임으로 표현?

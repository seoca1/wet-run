# ADR-0019: Combat Aftermath & Immersive Subtitles (전투 후일담 & 몰입형 자막)

**상태**: Accepted (auto-converted 2026-08-05, user-confirmed)
**날짜**: 2026-06-18
**결정자**: 사용자
**우선순위**: P1
**상위 결정**: ADR-0009 (Story), ADR-0010 (i18n), ADR-0013 (Events), ADR-0014 (Data Salvage)

## 컨텍스트

사용자 결정 (2026-06-18):
> "전투가 끝난 결과와 보상에서 상대의 중요도가 큰 경우에는 후일담 같은 이야기나 소설 인물들의 반응 같은 것을 읽을 수 있게 해줘. 이벤트 메시지는 한글 자막 형식으로 번역되어야 해. 몰입감을 높이는 요소야."

요구:
- **중요한 전투** 후 *후일담* (epilogue) 표시
- **소설 인물들의 반응** (Dixie, Molly, Case, Finn 등)
- **이벤트 메시지 한글 자막** (영어 + 한글) — 몰입감
- 모든 *이벤트* 메시지는 자막 형식

기존:
- i18n (ADR-0010) — en/ko 번역, Off/Subtitle/Replace 모드 (자막은 *가능*, 기본은 *Off*)
- Story Events (ADR-0013) — 6 event 타입
- Story Archive (ADR-0009) — meatspace 미표시, 텍스트/뉴스로만 전달

## 결정

### 1. Combat Aftermath (전투 후일담)

*중요한* 전투 종료 시 *에필로그* 표시. 소설 톤, 깁슨 스타일.

**중요도 (Importance) 4단계**:

| Level | 트리거 | 길이 | 표시 |
| --- | --- | --- | --- |
| `minor` | 일반 ICE 격파 | — | 표시 X (즉시 매트릭스 복귀) |
| `notable` | 강 ICE / 다중 격파 | 1-2 문장 | 짧은 snippet |
| **`major`** | **Black ICE / Construct 격파** | **2-3 문단** | **풀 snippet + character reaction** |
| `legendary` | Named boss (3Jane, etc.) | 4+ 문단 + multiple reactions | Special ending hook |

**기본 임계값**: `major` (Black ICE, construct 격파)부터 표시. ADR-0012 PPL/ZDR 비율이 *극단* (3.0x 이상)인 경우에도 `major` 트리거.

### 2. Character Reactions (소설 인물 반응)

`major` 이상 종료 시 *소설 인물*의 짧은 반응 표시. 7명.

| Character | 원작 | 톤 |
| --- | --- | --- |
| `dixie` | Neuromancer — Dixie Flatline (ROM construct) | 기술적, 약간 비꼬는, ROM 어투 |
| `finn` | Neuromancer — The Finn (fixer) | 비즈니스, 간결, 거래관점 |
| `molly` | Neuromancer — Molly Millions (razor girl) | 직접적, 강렬함, 짧은 문장 |
| `case` | Neuromancer — Case (console cowboy) | 내성적, 피로, 자기성찰 |
| `3jane` | Neuromancer/MLO — 3Jane (Tessier-Ashpool) | 차가움, 미스터리, aristocratic |
| `maelcum` | Neuromancer — Maelcum (Zionite) | 철학적, 평온, Lo Tek |
| `slick_henry` | MLO — Slick Henry (artist) | 예술적, 호기심, 미적 |

**반응 트리거** (예시):
- `combat.defeat.black_ice` → dixie, case 반응
- `combat.defeat.construct` → dixie, 3jane 반응
- `mission.complete.first_jack` → finn, case 반응
- `matrix.zone.core_first_time` → maelcum, case 반응

### 3. Immersive Subtitles (한글 자막)

*모든 이벤트 메시지*에 한글 자막 적용. Pillar 5 (Style) — 영화적 몰입감.

**표시 형식**:
```
> You jack in. The world goes gray.
> 잭인. 세계가 회색이 된다.
```

**자막 스타일**:
- 영어: 원본 톤 유지, 흰색
- 한글: 의역/번역, 노란색 또는 흰색 (살짝 dim)
- 두 줄 stack, 영어 위 / 한글 아래
- 또는 한 줄 alternate (en → ko fade)

**적용 범위**:
- Combat Aftermath (이 ADR)
- Story Events (ADR-0013) — narrative 부분만
- Mission briefings
- News / Story Archive (ADR-0009)
- Hub 픽서 dialogue

**적용 *외* 범위**:
- HUD 수치 (PPL, ZDR, HP)
- 메뉴 라벨
- 시스템 메시지 (loading, error)

### 4. 데이터 구조

`data/story/aftermath.json` — 후일담 콘텐츠 (en + ko)
`data/story/reactions.json` — 소설 인물 반응 (character + en + ko)
`data/i18n/{en,ko}.json` — i18n 키 (aftermath/reactions)

## 결과 (Consequences)

### Pillar 정합

- **P1 (The Run)**: 후일담 = 한 런의 *의미* 부여. 무게 강화.
- **P2 (The Matrix)**: 후일담은 매트릭스 안의 *데이터*. Pillar 2 정합.
- **P3 (The Flatline)**: 후일담은 *승리의 보상* (Pillar 3 일부 완화, ADR-0014와 정합).
- **P4 (The Build)**: 메타 진행과 별개. *서사*의 강화.
- **P5 (The Style)**: 깁슨 톤, 소설 어휘, cinematic 자막 — *가장 직접적* Pillar 5 표현.

### 기존 ADR 영향

- **ADR-0009 (Story)**: 보강. Aftermath는 *meatspace가 아닌* cyberspace 내 서사 (Pillar 2 정합).
- **ADR-0010 (i18n)**: 보강. 이벤트 메시지의 *기본* 표시 모드 = Subtitle.
- **ADR-0013 (Events)**: 보강. Events의 narrative 부분에 자막 적용.
- **ADR-0014 (Data Salvage)**: 보강. Aftermath는 Data Salvage *뒤*에 표시.

### 디자인 영향

- **`design/systems/aftermath.md`** (신규) — 후일담 시스템 명세
- **`design/systems/combat.md`** 확장 — 전투 종료 → Aftermath 흐름
- **`testcases/systems/aftermath.md`** (신규) — TC-AFTER-001~008
- **`data/story/aftermath.json`** (신규)
- **`data/story/reactions.json`** (신규)

### 구현 영향 (Phase 6+)

- `story/aftermath.py` — `Aftermath`, `CharacterReaction`, `AftermathRegistry`
- `story/subtitles.py` — 자막 렌더링 (en/ko stack)
- `engine/combat.py` 확장 — 전투 종료 → Aftermath 표시
- `engine/i18n_renderer.py` (신규) — 자막 모드 디폴트
- `data/story/*.json` (신규)

### Phase 5 범위

- **데이터 + 문서만**: JSON + ADR + design/testcases
- **UI 없음**: Phase 6+

### Phase 6+ 범위

- Aftermath 렌더링 (Combat 종료 후, Hub 복귀 전)
- Character reaction 표시 (portrait + 자막)
- 자막 모드 기본 활성화 (이벤트 화면)
- 자막 페이드인 애니메이션 (선택)
- Story Archive 통합 (aftermath도 archive에 저장)

### Phase 7+

- 사운드 (목소리 톤 매칭 — Dixie = glitched, Finn = smoky, Molly = sharp)
- 자막 타이핑 효과 (typewriter)
- 비주얼 노이즈 / 글리치 효과 (스프라이트 없음, ASCII만)

## 영향 받는 항목

- `design/systems/aftermath.md` (신규)
- `design/systems/combat.md` (확장)
- `decisions/0009-story-news-system.md` (연계)
- `decisions/0010-i18n-content-pipeline.md` (연계)
- `decisions/0013-story-events.md` (연계)
- `decisions/0014-data-salvage.md` (연계)
- `data/story/aftermath.json` (신규)
- `data/story/reactions.json` (신규)
- `testcases/systems/aftermath.md` (신규)

## 관련 결정

- ADR-0009 (Accepted) — Story
- ADR-0010 (Accepted) — i18n
- ADR-0013 (Accepted) — Story Events
- ADR-0014 (Accepted) — Data Salvage

## 변경 이력

- 2026-06-18: Draft 작성

## 결과 (Consequences)

본 ADR은 substance 전부 구현된 상태. 뷰 모듈은 ADR-0019 작성 후 engine/ 폴더 리팩토링 과정에서 통합됨.

**구현 증거 (2026-08-05)**:
- `data/story/aftermath.json` (13KB) — 후일담 4-importance 단계 데이터
- `data/story/reactions.json` (10KB) — 소설 인물 반응 데이터 (Dixie / Molly / Case / Finn 등)
- `data/story/arcs.json` (751KB) — 후일담 통합
- `i18n/translator.py` subtitle mode (ADR-0010 + ADR-0047) — 한글 자막 표시
- 4-importance (minor / notable / major / legendary) 시스템은 data 파일에서 인코딩됨

**연관 ADR (이미 Accepted)**:
- ADR-0010 (i18n + Content Pipeline) — Off/Subtitle/Replace 모드
- ADR-0047 (Typed Status Messages + 텍스트 가시성) — 자막 표시 형식
- ADR-0061 (Novel Integration Architecture) — 단편→게임 통합

ADR-0019의 "중요한 전투 후 에필로그" + "소설 인물 반응" + "한글 자막" substance는 모두 live.

**변경 후 immutable**: 본 ADR 의 결정 사항은 변경 불가. 향후 수정 필요 시 신규 ADR 작성 (AGENTS.md §8).

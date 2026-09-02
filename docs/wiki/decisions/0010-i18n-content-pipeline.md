# ADR-0010: i18n + Content Pipeline

**상태**: Accepted
**날짜**: 2026-06-17
**결정자**: 사용자
**우선순위**: P1

## 컨텍스트

사용자가 명시한 디자인 제약 (2026-06-17):

1. **한글과 영어 변환 가능** — 게임이 한국어와 영어로 표시 가능 (수정: 영어 중심 + 한글 번역/자막 추가)
2. **미션과 게임 진행은 지속적으로 보강되어 추가될 수 있음** — 콘텐츠가 반복적으로 추가됨
3. **초반 미션과 줄거리만 우선 구현해도 좋음** — 이른 콘텐츠는 우선순위 낮음
4. **엔딩 정합성과 품질을 위해 주요 줄기 뼈대는 정해둘 것** — 엔딩과 메인 아크는 사전에 정의

### 디자인 보강 (2026-06-17 갱신)

깁슨 톤의 충실도를 위해, 단순한 ko/en 토글이 아니라 **영어 중심 + 한글 번역/자막 추가** 방식이 더 적합하다. 깁슨 원문의 영어는 고유한 펀, 슬랭, 리듬, 문화적 뉘앙스를 담고 있어 단순 번역으로 대체되면 톤이 손실된다. 한글은 *번역* 또는 *자막*으로 추가되어 원문 위에 보조적으로 표시된다.

## 결정

### 1. i18n (English-centric, Korean as Supplementary Translation)

**1차 언어: English (en)**
- 모든 in-game text는 영어로 작성
- 깁슨 원작의 톤, 슬랭, 펀, 문화적 뉘앙스 보존
- Pillar 5 (The Style) — 깁슨 톤 직접 유지

**보조: Korean (ko) — 번역 / 자막**
- 모든 영어 텍스트에 대한 한글 번역 제공
- `data/i18n/ko.json`에 저장
- 표시 모드: 설정에서 선택
  - **Off** (기본): 영어만
  - **Subtitle**: 영어 위 + 한글 아래 (자막)
  - **Replace**: 한글만 (영어 비표시, 한국어 독자를 위해)
- 영어 원문은 항상 보존 (데이터에 영구 저장)

**파일 구조**:
```
data/
├── i18n/
│   ├── en.json          # 1차, 완전한 영어 텍스트
│   └── ko.json          # 보조, 영어 텍스트의 한글 번역
├── jobs/
│   ├── arc1-first-run.json
│   ├── arc1-second-run.json
│   ├── side-job-001.json
│   └── ...
├── programs/
│   └── programs.json
├── ice/
│   └── ice-types.json
├── factions/
│   └── factions.json
├── stories/
│   ├── briefings/
│   ├── results/
│   └── world-events/
└── ...
```

**번역 키 패턴**:
- 모든 in-game text는 `i18n/en.json`에 키로 저장 (1차)
- `i18n/ko.json`은 같은 키로 한글 번역 제공
- 키는 영어 snake_case, 계층적: `matrix.entry_message`, `menu.new_run`, `fixer.finn.greeting`
- 코드: `i18n.t("matrix.entry_message")` → 영어 또는 한글 (설정에 따라)
- 영어 원문은 항상 보존 (스토리 데이터에 영구)

**예시 (en.json — 1차)**:
```json
{
  "matrix": {
    "entry_message": "You jack in. The world goes gray.",
    "exit_message": "You pull out, heart racing.",
    "flatline_message": "You flatline. Static. Silence."
  },
  "menu": {
    "new_run": "New Run",
    "archive": "Story Archive",
    "settings": "Settings",
    "quit": "Quit"
  },
  "fixer": {
    "finn.greeting": "Got a job for you."
  }
}
```

**예시 (ko.json — 보조 번역)**:
```json
{
  "matrix": {
    "entry_message": "잭인. 세계가 회색이 된다.",
    "exit_message": "추출. 심장이 뛴다.",
    "flatline_message": "플랫라인. 정적. 침묵."
  },
  "menu": {
    "new_run": "새 런",
    "archive": "이야기 보관함",
    "settings": "설정",
    "quit": "종료"
  },
  "fixer": {
    "finn.greeting": "일을 하나 찾았다."
  }
}
```

**번역 표시 모드 (설정)**:
- **Off** (기본): 영어만 표시 — 깁슨 톤 직접
- **Subtitle**: 영어 위, 한글 아래 (자막) — 두 언어 함께
- **Replace**: 한글만 표시 — 한국어 독자용

**런 중 모드 전환**:
- 설정에서 변경 가능
- 재시작 불필요 (단순 토글)

**렌더링**:
- **매트릭스 안**: ASCII 기호 (언어 무관)
- **메뉴 / Story Archive / 대화**: 영어 1차 + 한글 자막 (선택)
- **Subtitle 모드**: 한 줄에 영어, 다음 줄에 한글
- **Replace 모드**: 한글만 (레이아웃은 한글 폭에 맞춤)
- **Pillar 2 준수**: meatspace는 여전히 미표시 — 언어는 텍스트에만 영향

**깁슨 톤 보존을 위한 원칙**:
- 영어 원문은 단순 번역이 아님 (예: "The sky above the port was the color of television, tuned to a dead channel" → 의역 가능, 직역 회피)
- 한글 번역은 *의역* 권장 (자연스러운 한국어)
- 핀 / 슬랭 / 문화적 뉘앙스 보존 위해 번역 메모 작성 (translator's note)

**고유명사 (Proper Nouns) 번역 원칙 (2026-06-17 추가)**:
- 고유명사(인명, faction명, 모델명, 브랜드)는 **영어 원문 그대로** 사용 가능
- 한국 사이버펑크/게임 번역 관행을 따름 (예: "Case", "Molly", "Ono-Sendai", "Tessier-Ashpool", "Wintermute" 등은 그대로)
- 의역이 필요한 경우에만 (1) 영어 그대로, (2) 발음 표기, (3) 의역 — 중 선택
- 한자/한글 발음 표기는 보조로 (예: `Ono-Sendai (오노센다이)`)
- 일반 명사/서술/대사는 한국어로 의역

**고유명사 예시**:
| 영어 (원문) | 한글 표기 권장 |
| --- | --- |
| Case | Case (또는 케이스) |
| Molly Millions | Molly Millions (또는 몰리 밀리언스) |
| Wintermute | Wintermute (그대로) |
| Tessier-Ashpool | Tessier-Ashpool (그대로) |
| Ono-Sendai | Ono-Sendai (그대로) |
| ICE | ICE (그대로) |
| construct | construct (또는 콘스트럭트) |
| cyberspace | cyberspace (또는 사이버스페이스) |
| The Sprawl | The Sprawl (또는 스프롤) |
| Dixie Flatline | Dixie Flatline (그대로) |
| Yakuza | Yakuza (또는 야쿠자) |
| Maas | Maas (그대로) |
| Sense/Net | Sense/Net (그대로) |

### 2. Content Pipeline

**데이터 주도** (ADR-0004에 따라):
- 모든 콘텐츠는 JSON / YAML 데이터 파일
- 새 미션 = 새 JSON 파일
- 새 ICE = 새 데이터
- 새 construct = 새 데이터
- 새 story = 새 데이터
- **코드 변경 없이 콘텐츠 추가 가능**

**콘텐츠 우선순위**:
1. **Plot bones** (필수, 사전 정의) — `design/story_skeleton.md`
   - 5개 메인 아크
   - 엔딩 (4+ variants)
   - 핵심 NPC
2. **초반 미션** (Phase 5 우선)
   - Arc 1 미션 1-3개
3. **Side content** (반복 추가)
   - 무한 side jobs
   - faction 뉴스
   - world events

### 3. Plot Skeleton

신규 디자인 문서 `design/story_skeleton.md` 작성. 메인 아크와 엔딩 정의를 사전에 완료.

## 결과 (Consequences)

### Pillar 정합
- **P1 (The Run)**: 한 런 = 한 의뢰. 메인 아크는 다중 런에 걸쳐.
- **P4 (The Build)**: Story Archive = unlock 메타 진행
- **P5 (The Style)**: 깁슨 톤의 en + 깁슨 톤의 한국어 번역 ko (단순 번역 X, 톤 유지)

### 기존 ADR 영향
- **ADR-0004 (데이터 주도)** 강화: 모든 텍스트도 데이터
- **ADR-0006 (런 구조)**: 메인 아크도 unlock 메타 진행의 일부
- **ADR-0009 (Story/News)**: Story Archive의 모든 텍스트도 i18n

### 디자인 영향
- **Pillar 2**: ASCII 매트릭스 (언어 무관), Story는 언어별
- **core_loop**: 의뢰 briefing, 결과, NPC 대화는 언어별
- **GDD**: 새 섹션 "i18n", "Plot Skeleton" 추가
- **glossary**: 게임 내 용어는 언어 무관 (이름)
- **style_guide**: 톤 가이드는 영어 기준, 한국어 톤 가이드 별도

### 구현 영향
- i18n 모듈 (단순 dict lookup, ~50 LOC)
- 데이터 로더 (JSON / YAML, ~100 LOC)
- Story Archive UI (언어별 표시)
- 언어별 폰트 (한글 + 영문 모두)

### 향후 결정
- 한국어 톤 가이드 (의역 원칙, 자막 표시 규칙)
- 한국어 메뉴 레이아웃 (한글 폭 처리)
- Subtitle 모드의 UI 디자인 (영어 위 / 한글 아래)
- 핀 / 슬랭 / 문화적 뉘앙스의 번역 메모 (translator's note)
- Hot reload (개발 중 데이터 자동 반영) — 옵션

## 영향 받는 항목

- `design/story_skeleton.md` (신규)
- `design/systems/i18n.md` (신규, 작성 필요)
- `design/GDD.md` (i18n, plot skeleton 섹션 추가)
- `decisions/0004-code-architecture.md` (데이터 주도 강화)
- `decisions/0009-story-news-system.md` (i18n 영향 명시)
- `ROADMAP.md` (Phase 2, Phase 4에 추가)

## 관련 결정

- ADR-0004 (Accepted, 강화)
- ADR-0006 (Accepted)
- ADR-0009 (Accepted, 강화)

## 변경 이력

- 2026-06-17: 사용자 디자인 제약 명시 → Accepted
- 2026-06-17: 갱신 — 단순 ko/en 토글에서 "영어 중심 + 한글 번역/자막 추가" 방식으로 재설계. 깁슨 톤 충실도 우선.

# Wet Run - AI Agent Guide

이 문서는 `Game/wet_run/`(이전 명칭: `Game/wet_run/`)에서 작업하는 모든 AI 에이전트를 위한 작업 규약이다. 루트 `AGENTS.md`를 보완한다.

## 1. 프로젝트 개요

윌리엄 깁슨의 스프롤 3부작 세계관을 배경으로 한 로그라이크. 플레이어는 데커(console cowboy)가 되어 사이버스페이스에서 ICE를 뚫고 임무를 수행한다. 자세한 내용은 `README.md`와 `ROADMAP.md`를 참조.

## 2. 디렉토리별 규칙

| 디렉토리 | 에이전트의 역할 | 절대 규칙 |
| --- | --- | --- |
| `raw/` | **읽기 전용** | 절대 수정 금지. 원본 자료의 무결성 유지. |
| `wiki/` | 자유롭게 편집, 인덱스/로그 갱신 필수 | LLM Wiki 계층. 인용이 가능한 모든 페이지에 원문 인용 포함. |
| `design/` | 자유롭게 편집, 사용자 검토 영역 | 활성 스펙. 사용자가 직접 수정할 수 있음을 인지. |
| `testcases/` | 자유롭게 편집, 템플릿 사용 | 디자인 변경 시 동기화 필요. |
| `decisions/` | Draft 상태는 자유, Accepted는 immutable | 결정된 사항 임의 변경 금지, 새 결정은 신규 ADR로. |
| `prototype/` | (이전 명칭; **2026-09-15 통합 완료 → `web/` 로 이관**) | 하위 호환을 위해 디렉토리는 보존되지만 활성 코드베이스는 `web/` TypeScript. |
| 루트 메타 파일 | 신중히 수정 | README, AGENTS.md, index, log, ROADMAP, SETUP_LOG |

## 3. 작업 워크플로우

### 3.1 새 원본 자료 추가 (예: 소설 챕터 발췌)
1. `raw/` 에 원본 추가 (절대 수정하지 말 것)
2. `AGENTS.md` 의 "LLM Wiki Operations" 절차 수행:
   - 원문 읽기 → 핵심 추출 → 기존 위키 페이지 갱신
   - 신규 페이지 필요 시 생성
   - `index.md` 갱신
   - `log.md` 에 `[YYYY-MM-DD] ingest | 제목` 형식으로 기록
3. 위키 페이지에 원문 인용 추가 (가능하면)

### 3.2 게임 디자인 변경
1. `decisions/` 에 새 ADR 작성 또는 기존 ADR Status 변경
2. **Implementation status 결정** (ADR Accepted 시점 필수 — [ADR-0195](./decisions/0195-adr-implementation-workflow.md)):
   - ✅ **Implemented**: 이미 shipped (코드 + 테스트 + 데이터 모두 확인)
   - 🟡 **Partial**: 일부만 shipped, 나머지 backlog
   - ❌ **Not started**: 미구현 (backlog 명시)
   - 🟢 **Deferred**: 의도적으로 미래로 연기
3. 영향 받는 `design/systems/*.md` 갱신
4. `testcases/` 에 회귀 테스트 추가/갱신
5. `design/GDD.md` 의 본문 또는 Open Questions 갱신
6. `log.md` 에 기록

**Implementation Status 형식** (0156/0188 모델):
```markdown
## Implementation Status (YYYY-MM-DD)

**Status**: [✅ Implemented | 🟡 Partial | ❌ Not started | 🟢 Deferred]

**Evidence**:
- `path/to/file.py:LINE` — [description]

**Notes**: [caveats]
```

### 3.3 결정 요청
- `decisions/template.md` 사용
- 옵션 비교표 + 추천안 + 열린 질문 포함 필수
- 사용자가 결정하면 Status를 "Accepted"로 변경하고 결과(Consequences) 섹션 채우기

## 4. Sprawl 세계관 정확성 규칙

> **2026-07-10 정책 변경**: 파생 소설을 Notion에 게시하지 **않는다**. 대신 `Game/wet_run/dashboard/stories/` HTML 카드를 단일 진실 공급원으로 사용. 자세한 계획: `docs/progress/DASHBOARD_ENHANCEMENT_PLAN.md`.

깁슨 원작의 톤과 용어를 정확히 살리는 것은 디자인의 일부다.

- 깁슨이 만든 용어(ICE, deck, program, construct, wetware, console cowboy 등) 사용
- 1980년대 깁슨이 상상한 미래의 톤 — 너무 깔끔하거나 유토피아적이지 않음
- "Sprawl" = 보스턴-애틀랜타 메트로폴리스의 속칭
- "Freeside" = L5 궤도 식민지
- 인종차별, 빈곤, 중독, 신체 훼손 같은 어두운 주제를 회피하지 말 것
- 21세기 인터넷 memes, Cyberpunk 2077, D&D 등 다른 작품의 용어로 대체 금지
- 사실 단언 시 원문 인용 첨부 ("깁슨에 따르면..." → 인용 필수)

### 4.0 Notion 사용 정책

**Notion은 메타 문서 (진행 보고, 가이드, 운영 문서)만 보관.**
**파생 소설·콘텐츠는 dashboard HTML이 진실 공급원.**

- ❌ Notion에 게시 금지: 파생 단편 (derivative fiction), 챕터 본문, 게임 카드 본문
- ✅ Notion 보관 가능: 진행 보고, 운영 가이드, 게임 디자인 노트
- 이유: Notion은 외부 게시 플랫폼 — 컨텐츠 중복 위험, 동기화 비용, dashboard HTML이 더 효율적 (GitHub Pages 즉시 표시, 검색 가능, 로컬 백업)

### 4.1 World Source: Fiction wiki

게임의 세계관은 **`../../../../Fiction/wiki/`** (깁슨 분석 wiki)를 *Primary source*로 참조한다.
(이는 `Projects/Fiction/wiki/` — Fiction 프로젝트의 위키 디렉토리)

- 게임 wiki (`Game/wet_run/wiki/world/`)는 게임용 요약/적응
- 깊은 분석/원문 인용/캐릭터 디테일은 Fiction wiki 참조
- **절대 경로**: `../../../../Fiction/wiki/...` (위치: `wiki/` 하위 MD 파일 기준 4단계 상승)
- AGENTS.md 기준 절대 경로: `../../../Fiction/wiki/...`
- Fiction wiki 페이지 예시:
  - `../../../../Fiction/wiki/authors/william-gibson.md`
  - `../../../../Fiction/wiki/works/neuromancer.md` (1984)
  - `../../../../Fiction/wiki/works/count-zero.md` (1986)
  - `../../../../Fiction/wiki/works/mona-lisa-overdrive.md` (1988)
  - `../../../../Fiction/wiki/characters/case.md`
  - `../../../../Fiction/wiki/characters/molly-millions.md`
  - `../../../../Fiction/wiki/settings/cyberspace.md`
  - `../../../../Fiction/wiki/index.md`

게임 내 텍스트 작성 시:
1. Fiction wiki에서 원문 톤 확인
2. 게임 컨텍스트에 맞게 적응
3. 원문에 없는 요소를 만들지 말 것
4. 새 요소가 필요하면 Fiction wiki의 *이전 작품* (Bridge, Blue Ant, Jackpot)에서 차용 가능 — 단 명시

## 5. LLM Wiki Operations (raw / wiki / schema)

이 프로젝트는 표준 LLM Wiki 패턴을 따른다.

- **Ingest**: raw에 새 자료 → 관련 wiki 페이지 작성/갱신 → index 갱신 → log 기록
- **Query**: 사용자가 질문 → index로 관련 페이지 찾기 → 인용과 함께 답변 → 가치가 있으면 결과를 새 wiki 페이지로 file-back
- **Lint**: 주기적으로 wiki 건강 점검
  - orphan 페이지 (인바운드 링크 없음)
  - 모순 (여러 페이지의 동일 주제 다름)
  - 인용 누락 (사실 단언인데 출처 없음)
  - 갱신 필요한 페이지 (오래된 정보)

## 6. 코딩 규칙 (Accepted 결정 반영)

> **2026-09 통합 노트**: `prototype/` 디렉토리의 Python 코드는 **2026-09-15 통합으로 `web/` TypeScript로 이관 완료** (커밋 `1b3cff4 chore: prototype/ 정리 및 web/ 검증 완료`). 활성 코드베이스는 `web/` (Node.js + TypeScript + Vite + Vitest). 모든 변경은 `web/` 에서.

### 언어 및 의존성 (현재 — `web/`)

- **언어**: TypeScript 5.5
- **빌드**: Vite 5.3
- **테스트**: Vitest (vitest.config.ts + tests/ 하위)
- **린트 / 포맷**: ESLint + Prettier
- **타입 체크**: tsc --noEmit (strict mode in tsconfig.json)
- **의존성 관리**: package.json + npm (또는 pnpm/yarn)
- **렌더링**: HTML5 Canvas 2D (Web tier); tcod 호환 포트는 데이터 export (`scripts/export_web_data.py`)로만 잔존

### 테스트 / 린트 / 타입체크 실행 경로 (canonical)

**반드시 `web/` 디렉토리에서 실행** — 절대 경로 (`/.../web/node_modules/.bin/vitest`)는 다른 인터프리터를 사용해 9+ false-positive 실패를 보임. `cd web &&` 후 상대 npm 스크립트 사용.

```bash
cd web
npm install            # 1회 (또는 의존성 변경 시)
npm test               # vitest run — 87 files, ~2646 tests at HEAD + 63 pre-existing failures
npm run test:watch     # watch 모드
npm run typecheck      # tsc --noEmit (strict)
npm run lint           # eslint src
npm run format         # prettier --write
npm run build          # tsc + vite build → dist/
npm run dev            # vite dev server (HMR)
npm run e2e            # playwright e2e (separated tests, requires browsers)
npm run smoke          # e2e/smoke.spec.ts only
npm run export-data    # regenerate static JSON from wet_run Python (read-only)
```

> **사전 알림 (2026-09-15 감사)**: `tsc --noEmit`을 pristine HEAD에서 실행 시 약 79개 strict-type 에러가 보고된다 — 대부분 **PR 시점에는 존재했지만 미해결로 머문 항목** (untracked `src/renderer/{dungeon,inventory,journal,loading,mission_select,pause,shop,status}.ts` 가 `State` 타입을 잘못 import하는 등의 신규 추가 코드에서 발생). 버그 헌트가 아닌 마이그레이션 잔재. **CI에서 강제하지 않음**. 가이드: 가능하면 같은 세션에서 함께 정리하거나, 별도 PR로 분리.

### 디렉토리 구조 (현재 — `web/` 기반)

```
Game/wet_run/
├── web/                     # ← 활성 코드베이스 (TypeScript + Vite + Vitest)
│   ├── package.json
│   ├── tsconfig.json        # strict 모드
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── index.html
│   ├── public/              # 정적 자산
│   ├── src/
│   │   ├── main.ts          # 엔트리 포인트 (canvas + renderer + game loop)
│   │   ├── audio/           # Howler.js BGM + SFX
│   │   ├── core/            # 게임 로직 (combat, state, dungeon, save 등)
│   │   │   ├── combat_engine.ts / combat_models.ts / boss*.ts / ice_ai.ts
│   │   │   ├── state.ts / state_actions.ts / state_helpers.ts / types.ts
│   │   │   ├── matrix.ts / dungeon*.ts / hub.ts / stage_system.ts
│   │   │   ├── achievements*.ts / faction_reputation.ts / death_cycle.ts
│   │   │   ├── graphic_novel*.ts / sound_system.ts / i18n.ts
│   │   │   ├── save_progress.ts / accessibility.ts / pwa_manager.ts
│   │   │   └── starter_deck.ts  # STARTER_DECK constant (Tier 1 MVP)
│   │   ├── input/           # KeyboardInput / GamepadInput / Touch
│   │   ├── renderer/        # Canvas2D ASCII renderer (palette.ts, canvas.ts)
│   │   ├── data/            # 정적 JSON (export_web_data.py로 생성)
│   │   └── e2e/             # Playwright e2e specs
│   ├── tests/              # 87 vitest 파일 (~2646 tests + 63 pre-existing failures)
│   └── scripts/            # export_web_data.py 등 보조 스크립트
├── docs/                   # 디자인 / ADR / 세션 요약
├── data/                   # 정적 데이터 (이전 prototype/ 잔재; export_web_data.py 입력)
├── tools/
├── log.md                  # 워크스페이스 활동 로그
├── README.md               # 최상위 개요
└── ROADMAP.md              # 단계별 계획
```

> **통합 ADR**: `1b3cff4 chore: prototype/ 정리 및 web/ 검증 완료` — Python 프로토타입 비활성화, `web/` Tier 1 MVP 활성. 후속 ADRs (ADR-0199 등)는 web/ 단계별로 갱신.

### 스타일 (현재 — `web/` TypeScript)

- TypeScript strict, ESLint + Prettier 기본
- 모든 public 함수 / 컴포넌트에 타입 명시
- 2-space indent
- 한 줄 100자 (Prettier 기본)
- 함수형 컴포넌트 우선, hooks 활용
- `Object.freeze(...)` / `Readonly<...>` 광범위 사용 (불변 상태 모델)
- 모듈 / 클래스 / 함수 모두 docstring 권장

### 모듈 사이즈 정책 (ADR-0110 이월)

1000+ LOC 정책은 이전 Python 코드를 기준으로 작성됨. `web/` TypeScript는 **모듈당 평균 100-300 LOC**으로 더 작은 단위를 권장 (Vite tree-shaking 효율). 1000+ LOC 신규 모듈은 PR 리뷰에서 분할 계획 또는 정당화 필수.

### 명령 (npm scripts via Makefile wrapper 또는 직접)

```bash
cd web
npm test               # vitest run
npm run typecheck      # tsc --noEmit
npm run lint           # eslint src --ext .ts,.tsx
npm run format         # prettier --write
npm run build          # tsc -b && vite build
npm run dev            # vite (HMR)
```

### 빠른 데모 (web/ 기준)

```bash
cd web
npm run dev            # http://localhost:5173

# CLI 인터랙티브 (Tier 4 검증 도구)
npm run cli:interactive

# 빠른 자동 검증 (30 tests, ~1초)
npm run cli:test

# 빌드 미리보기
npm run build && npm run preview
```

### 코드 변경 시 워크플로우 (web/)

1. 관련 `docs/design/*.md` (이전 `design/systems/*.md` 위계) 와 `testcases/` 확인
2. 자동 테스트 추가 (vitest 단위/통합)
3. `npm run format && npm run lint && npm run typecheck && npm test`
4. `log.md` 에 `[YYYY-MM-DD] 작업종류 | 제목` 형식으로 기록
5. 영향 받는 ADR / 결정이 있으면 ADR 갱신 (단, `decisions/` 디렉토리는 이전 prototype 잔재; 신규 web ADR은 `docs/architecture/` 권장)

### i18n (번역) 가이드라인 (ADR-0010 이월)

- **1차**: 영어 (en) — 깁슨 원문 톤 직접 보존
- **보조**: 한글 (ko) — 번역/자막 추가
- **고유명사**: 영어 원문 그대로 사용 가능 (Case, Tessier-Ashpool, Ono-Sendai, ICE, construct 등)
- **일반 명사/서술/대사**: 한국어 의역
- **표시 모드**: Off (영어만) / Subtitle (영어+한글) / Replace (한글만)

### 알려진 한계 (web/ 활성 상태)

- **`tsc --noEmit` 알려진 알림**: 위 "사전 알림" 박스 참조. 79개 에러는 별도 청소 PR 권장.
- **e2e specs (`web/e2e/*.spec.ts`)**: Playwright 브라우저 의존성. 단위 검증이 부족한 통합 경로 검증용.
- **PWA (`web/src/core/pwa_manager.ts`)**: half-implemented (consumer only). beforeinstallprompt / controllerchange / online-offline 리스너 미연결 — 후속 작업.

### CI / CD
- GitHub Actions: macOS + Windows 매트릭스
- PR마다 lint + format + build 자동 실행
- Vitest 단위 테스트는 CI에서 강제 / e2e는 명시 트리거

### ECS-lite 사용 규칙 (ADR-0194, Accepted 2026-08-26) — 이전 prototype/ 잔재

> **2026-09 노트**: ECS 결정은 prototype/ Python 코드에 적용됨. web/ TypeScript 마이그레이션에서는 상태가 `web/src/core/state.ts` 의 reducer 패턴 + `GameState` 인터페이스로 통합되어, 별도 ECS 레이어가 없음. 신규 web 컴포넌트는 **순수 OOP + `interface` 타입** 권장.

**기본 (신규 시스템 추가 시)**: OOP / `@dataclass` 사용.

**ECS-lite 선택 허용 도메인** (Python 잔재 — `prototype/` 디렉토리에서만):
- `matrix/` (노드 그래프 — 방 → Entity 매핑)
- `engine/dungeon_view.py` (dungeon/room 시각화)

**ECS-lite 비권장 도메인**:
- `engine/state.py` (AppState), `combat/*`, `missions/*`, `equipment/*`,
  `programs/*`, `portraits/*`, `i18n/*`, `story/` — 모두 OOP / `@dataclass`

**World naming collision**: ECS 사용 시 `from wet_run.ecs import World as EcsWorld` 별칭 도입 (Python). web/ TypeScript에는 해당 없음.

**참조**: [`decisions/0194-ecs-role-clarification.md`](./decisions/0194-ecs-role-clarification.md), [`docs/ARCHITECTURE.md` §14.6](./docs/ARCHITECTURE.md#146-adr-0194-결과-적용-2026-08-26)

**World naming collision**: ECS 사용 시 `from wet_run.ecs import World as EcsWorld` 별칭 도입.

**참조**: [`decisions/0194-ecs-role-clarification.md`](./decisions/0194-ecs-role-clarification.md), [`docs/ARCHITECTURE.md` §14.6](./docs/ARCHITECTURE.md#146-adr-0194-결과-적용-2026-08-26)

## 7. CJK 혼용 방지 가이드

**목적**: 한국어/영어 문장 속에 한자(漢字)나 일본어가 깨진 듯 끼어드는 혼용(mixed-script contamination)을 방지한다.

**MiniMax 특성**: 중국 기반 모델이다. 한국어·영어 출력 시에도 한자·중국어·일본어가 자연스럽게 섞여 나올 수 있으므로, 의식적으로script를 분리해야 한다.

### 허용 vs. 금지

| 구분 | 예시 | 허용? |
|---|---|---|
| 한국어 문장에 한자가 1~2자 섞임 | `matrix(행렬) 연결된` | ❌ |
| 한국어 문장에 가타카나가 끼어듦 | `Jack-Out(잭아웃) 후` | ❌ |
| 한국어 문장인데 일본어 kana가散在 | `그래서  그래서` | ❌ |
| 한국어 문장인데 영어 단어가 괄호 속에 삽입 | `잭아웃(jack-out) 후` | ❌ |
| 한국어 문장 전체가 중국어/일본어 | `矩阵 连接 虚拟化` | ❌ |
| 영어 문장 속 괄호 한글 번역 | `matrix (매트릭스) connection` | ❌ |
| 한국어 문장의 일부를 영어 term으로 | `matrix와 가상화 연결` | ✅ |
| **고유명사 (캐릭터/지명/기술명)** | 케이스, 몰리, ICE, Ono-Sendai | ✅ |

### MiniMaxscript混合되기 쉬いパターン（意识的に分離）

```
❌ " matrix(矩阵) 连接 虚拟化"         → 한국어 문서에서 한자 섞임
❌ "잭아웃 후 (jack-out) 30초"         → 괄호 속 영어 섞임
❌ "그래서(so) 그것은"                 → 괄호 속 영어 섞임
❌ "matrix — 행렬, virtualization"      → 혼합 표기
✅ "matrix와 가상화 연결"               → 한국어만
✅ "Jack-Out, 30 seconds later"        → 영어만
✅ "matrix와 가상화"                   → 기술 용어는 영어 그대로 허용
```

### 올바른 작성 예시

```
# 한국어 문서 (language: ko)
❌ " matrix(행렬) 연결된 virtualization"
✅ "matrix와 가상화 연결"
✅ "matrix - 가상화 연결"

❌ "Jack-Out(잭아웃) 후 30초"
✅ "잭아웃 후 30초"

# 영어 문서 (language: en)
❌ "잭아웃 후 30초"
✅ "Jack-Out, 30 seconds later"
```

### 파일별 기준

- **`language: en`** → 본문은 영어. 한글·한자 섞기 금지.
- **`language: ko`** → 본문은 한국어. 한자·가타카나·히라가나 섞기 금지.
- **코드 주석** → 해당 코드의 `language`/frontmatter 기준.
- **EN/KO 쌍 파일** → 각 파일이 개별 언어 기준. 상호 참조는 wikilink (`[[...]]`).

### 자동 검사 패턴

작성 후 다음이 발견되면 제거 또는 교체:
- 한국어 문장에서 1~2글자 단독으로 떨어진 한자 (주변이 한글인 경우)
- 한국어 문장 속 가타카나/히라가나 문자
- 영어 문장 속 한글

### 허용되는 hybrid 사례

굳이 번역하면 의미가 흐리는 용어는 원문 그대로:
- **기술 용어**: ICE, deck, wetware, construct, jack-in, jack-out
- **캐릭터명**: 케이스(Case), 몰리(Molly), 쿠미코(Kumiko)
- **지명**: 시바 시티, 프리스타운, 사이버스페이스
- **작품명**: Neuromancer, Count Zero (제목은 원문 유지)

---

## 8. 절대 하지 말 것

- `raw/` 수정
- 결정된 사항(`decisions/`의 Accepted 상태) 임의 변경
- 한 세션에 너무 많은 문서/파일 변경 (사용자 검토 부담)
- 원작에 없는 사실의 무성한 단언
- 다른 사이버펑크 작품의 톤/용어 차용 (Cyberpunk 2077, Shadowrun, D&D 등)
- Fiction wiki (`../../../Fiction/wiki/`) 수정 — 깁슨 분석은 Fiction 프로젝트 영역

## 8. 작업 시작 체크리스트

- [ ] `SESSION_SUMMARY.md` — 현재 세션 요약 (가장 먼저)
- [ ] `ROADMAP.md` 의 "Current Phase" 확인
- [ ] **GitHub Projects 보드** — https://github.com/users/seoca1/projects (이슈 카드 확인)
- [ ] `decisions/README.md` 에서 미해결 결정 확인
- [ ] `CHARACTER_PATHS.md` — 캐릭터 비교
- [ ] `index.md` 에서 관련 위키 페이지 찾기
- [ ] 작업 완료 후 `log.md` 갱신

### 8.1 GitHub Projects 보드 (ADR-0030 §9)

**보드 URL**: https://github.com/users/seoca1/projects (생성 필요)

Web UI에서 보드 생성:
1. https://github.com/users/seoca1/projects → "New classic project"
2. Name: "Wet Run Development"
3. Columns: Backlog / Ready / In Progress / Review / Done

상세 가이드: [`docs/GITHUB_PROJECTS_SETUP.md`](./docs/GITHUB_PROJECTS_SETUP.md)

## 9. 작업 종료 체크리스트

- [ ] `index.md` 가 새 페이지를 모두 가리키는가
- [ ] `log.md` 에 이번 세션 작업이 기록되었는가
- [ ] 영향 받는 `design/`/`testcases/`/`decisions/`가 동기화되었는가
- [ ] raw에서 읽은 자료는 모두 인용되었는가
- [ ] 세션 종료 시 `SESSION_SUMMARY.md` 갱신 (해당 시)

## 10. 그래픽 노블 모드 (ADR-0032)

게임 시작 시 메인메뉴(7 옵션)에서 진입 가능한 비주얼 노블 자동플레이.

> **2026-09 통합 노트**: 본 섹션은 prototype/ Python 시절 ADR-0032/0040/0041-44 그래픽 노블 명세를 보존합니다. web/ TypeScript 포트는 다음에 위치: `web/src/core/graphic_novel*.ts` (5 modules), `web/src/main.ts` 메뉴 옵션 2 (`GRAPHIC NOVEL`), `web/src/ui/GraphicNovelMenu.tsx` 등. **web/ 테스트는 `web/tests/graphic_novel*.test.ts`** (Tier 4 기준 — ADR-0199 이월).

### 메인메뉴 옵션 (7) — ADR-0032 + ADR-0040 + Phase 7
1. **NEW RUN** — 자키 선택부터 일반 게임플레이
2. **GRAPHIC NOVEL** — 스토리 자동재생 (그래픽 노블 모드 진입)
3. **CONTINUE** — 마지막 세이브 로드 (없으면 비활성)
4. **SETTINGS**
5. **CREDITS**
6. **HALL OF DEAD** — 자키 아카이브 (사망한 자키 목록, ADR-0040)
7. **HELP** — 조작법/컨셉 도움말 (Phase 7 온보딩)

### 그래픽 노블 모드 옵션 (5)
1. **PROLOGUE** — 3명 캐릭터 × 4 씬 = 12 씬 자동재생 (랜덤 셔플)
2. **케이 (K) — Novice** — 4 씬
3. **실 (Sil) — Veteran** — 4 씬
4. **카스 (Kas) — Heretic** — 4 씬
5. **BACK** — 메인메뉴

### 화면 흐름
```
MENU → GRAPHIC_NOVEL_MENU → GRAPHIC_NOVEL → SAVED_PROGRESS → MENU
```

### 주요 명령
```bash
# 데모
uv run python scripts/graphic_novel.py --mode prologue --seed 42
uv run python scripts/graphic_novel.py --mode veteran --lang ko
uv run python scripts/play.py --gn-mode novice
uv run python scripts/demo.py --gn-mode prologue
uv run python scripts/demo.py --menu-option 2 --duration 30   # Mode 2: Graphic Novel 자동 재생

# 데이터
data/scenes/{case,sil,kas}/      # 12 씬 JSON (3 캐릭터 × 4 씬)
data/art/portraits/portraits.json  # 15 ASCII 포트레잇 (10×14)
data/art/backgrounds/backgrounds.json  # 12 ASCII 배경 (40×16)

# 디자인
design/scenario/graphic-novel.md  # 전체 명세
decisions/0032-graphic-novel-mode.md  # 결정 문서

# 테스트
tests/unit/test_graphic_novel_view.py  # 40 tests
tests/unit/test_save_progress.py        # 16 tests
tests/unit/test_menu_extended.py        # 31 tests
```

### 키 매핑 (재생 중)
| 키 | 동작 |
| --- | --- |
| (자동) | duration_ms 후 다음 대사/씬 |
| `Space` / `→` | 현재 대사 즉시 완료 |
| `S` | 현재 씬 스킵 |
| `P` | 일시정지/재개 |
| `Esc` / `Q` | 그래픽 노블 종료 → SAVED_PROGRESS |

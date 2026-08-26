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
| `prototype/` | Python 3.11 + python-tcod ECS + uv | 확정 (v1.1.0a1, 2026-07-28). 모든 변경 후 `ruff check` + `mypy` + `pytest` 통과 필수. |
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
2. 영향 받는 `design/systems/*.md` 갱신
3. `testcases/` 에 회귀 테스트 추가/갱신
4. `design/GDD.md` 의 본문 또는 Open Questions 갱신
5. `log.md` 에 기록

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

### 언어 및 의존성
- **언어**: Python 3.11+ (3.12, 3.14 호환 확인)
- **렌더링 / 게임 루프**: python-tcod (>= 16.0, 21+ 검증)
- **테스트**: pytest
- **린트 / 포맷**: ruff
- **타입 체크**: mypy (strict)
- **의존성 관리**: pyproject.toml + uv (또는 pip)
- **빌드 백엔드**: hatchling

### 테스트 / 린트 / 타입체크 실행 경로 (canonical)

**반드시 `prototype/` 디렉토리에서 실행** — 프로젝트 루트에 있는 `.venv/`는 pytest만 있고 ruff/mypy/interrogate/typing_extensions가 없음. 절대 경로 (예: `/.../prototype/.venv/bin/pytest`)는 다른 Python 인터프리터를 사용해 11+ false-positive 실패를 보임.

```bash
cd prototype
make all          # format + lint + typecheck + test
make test         # pytest only (5281 → 5307 passing, 463 → 365 skipped)
make lint         # ruff
make typecheck    # mypy --strict
```

또는 직접 실행 시 `prototype/.venv/bin/...` 절대 경로 대신 `cd prototype &&` 후 상대 경로 사용.

### 디렉토리 구조 (Phase 4 확정)

코드 프로젝트는 `prototype/` 하위. 디자인 문서와 분리.

```
prototype/
├── pyproject.toml          # uv / pip 프로젝트 설정
├── README.md               # 코드 프로젝트 README
├── Makefile                # 편의 명령
├── .gitignore, .editorconfig, .python-version
├── src/
│   └── wet_run/   # Python 패키지
│       ├── __init__.py
│       ├── __main__.py     # python -m wet_run
│       ├── engine/         # tcod 통합 (app, render, input, config)
│       ├── ecs/            # ECS-lite (entity, world)
│       ├── i18n/           # 번역 (translator)
│       ├── portraits/      # ASCII Portraits (manager)
│       ├── data/           # 데이터 로더
│       ├── matrix/         # 사이버스페이스 (노드 그래프)
│       ├── combat/         # RT-MS 전투
│       ├── programs/       # 프로그램
│       ├── jobs/           # 의뢰
│       ├── save_progress.py  # 세이브 진도 조회 (ADR-0032)
│       ├── graphic_novel_view.py  # 그래픽 노블 자동플레이 (ADR-0032, 0041-0044)
│       ├── graphic_novel_audio.py  # 씬 사운드 큐 (ADR-0043)
│       ├── graphic_novel_save.py   # GN 이어서 읽기 (ADR-0044)
│       └── jockey_history.py       # Hall of Dead 자키 아카이브 (ADR-0040)
├── tests/
│   ├── conftest.py
│   └── unit/               # 단위 테스트 (2257 tests)
├── data/
│   ├── i18n/               # en.json, ko.json
│   ├── portraits/          # portraits.json
│   ├── programs/           # programs.json
│   ├── scenes/             # 그래픽 노블 씬 (3 캐릭터 × 4 씬, ADR-0032 + ADR-0041 4× 확장)
│   ├── art/                # ASCII 아트 (portraits.json, backgrounds.json)
│   ├── saves/              # GNProgress save 파일 (ADR-0044)
│   ├── sounds_test/        # 46개 자동 생성 WAV (ADR-0043)
│   └── fonts/              # libtcod terminal font
├── scripts/
│   ├── download_font.py    # 폰트 다운로드
│   ├── play.py             # 풀 게임 데모 (--gn-mode로 그래픽 노블 진입)
│   ├── demo.py             # 사이클 데모
│   ├── demo_all.py         # 풀 게임 + 그래픽 노블 통합
│   ├── graphic_novel.py    # 그래픽 노블 단독 (--continue, --no-cards, --card-ms)
│   ├── combat_simulator.py # 단일 전투 검증
│   ├── combat_grades.py    # 5등급 진행 비교
│   ├── combat_effects_demo.py  # 5-Layer VFX 10-씬
│   ├── death_demo.py       # Death cycle 단독
│   ├── death_in_action_demo.py  # Combat → Death 5-Phase 풀사이클
│   ├── full_demo.py        # Prologue → Briefing → Matrix → Combat
│   └── scripts/README.md   # 모든 데모 실행 가이드
└── .github/workflows/
    └── ci.yml              # GitHub Actions CI
```

### 스타일
- PEP 8 + ruff 기본
- 모든 public 함수 / 클래스에 타입 힌트 + docstring
- `from __future__ import annotations` 사용
- 한 줄 100자 (ruff)
- 모듈 / 클래스 / 함수 모두 docstring
- `__slots__` 사용 (메모리 효율)

### 모듈 사이즈 정책 (ADR-0110)
- **250 LOC**: 신규 모듈 권장 한도 (PR 리뷰 체크리스트)
- **500 LOC**: PR 거부 기준 (1회성 / 단발성 모듈은 700~800 LOC 까지 예외 허용)
- **1000+ LOC**: 신규 ADR 필수 (정당화 + 분할 계획 OR 보유 사유 명시)

현행 14 파일은 ADR-0110 Consequences 표 참조. 1000+ LOC 4 모듈은 후속 ADR (제안: 0111/0112/0113) 로 정당화/분할 처리. matrix_view.py 는 ADR-0103 의 backward compat 보존 결정 우선.

### 명령 (Makefile)

```bash
make sync         # uv sync --all-extras
make download-font  # 폰트 다운로드 (최초 1회)
make run          # 게임 실행 (hello-world)
make test         # pytest
make lint         # ruff check
make format       # ruff format
make typecheck    # mypy
make build        # uv build
make clean        # 캐시 정리
make all          # format + lint + typecheck + test
```

### 빠른 데모 (Phase 5)

```bash
# 30초 자동 플레이 (Menu → Hub → Matrix 사이클, Fog 표시)
uv run python scripts/play.py

# 짧은 데모
uv run python scripts/play.py --duration 8 --step-delay 0.3

# 화면 누적 (스크롤)
uv run python scripts/play.py --no-clear

# 한글
uv run python scripts/play.py --lang ko
```

추가 도구 (전체 가이드: `scripts/README.md`):
- `scripts/combat_simulator.py` — 단일 전투 검증 (PPL/ZDR/enemy/strategy 옵션)
- `scripts/combat_grades.py` — 5등급 전투 진행 비교 (테이블 출력)
- `scripts/combat_effects_demo.py` — 5-Layer VFX 10-씬 검증
- `scripts/death_demo.py` — Death 사이클 단독 (DEATH_SUMMARY/HALL_OF_DEAD)
- `scripts/death_in_action_demo.py` — Combat → Death 5-Phase 풀사이클
- `scripts/graphic_novel.py` — 그래픽 노블 자동재생 (`--continue` 이어서 읽기)
- `scripts/demo.py` — 2분 전체 플레이 (HUB + Matrix 사이클)
- `scripts/demo_all.py` — 풀 게임 + 그래픽 노블 통합
- `scripts/visual_demo.py` — 8개 시스템 한 번에 시각 검증

### 코드 변경 시 워크플로우
1. 관련 `design/systems/*.md` 와 `testcases/*.md` 확인
2. 자동 테스트 추가 (단위/통합)
3. `make format && make lint && make typecheck && make test`
4. `log.md` 에 기록
5. 영향 받는 ADR / 결정이 있으면 ADR 갱신

### i18n (번역) 가이드라인 (ADR-0010)

- **1차**: 영어 (en) — 깁슨 원문 톤 직접 보존
- **보조**: 한글 (ko) — 번역/자막 추가
- **고유명사**: 영어 원문 그대로 사용 가능 (Case, Tessier-Ashpool, Ono-Sendai, ICE, construct 등)
- **일반 명사/서술/대사**: 한국어 의역
- **표시 모드**: Off (영어만) / Subtitle (영어+한글) / Replace (한글만)
- 자세한 내용: `decisions/0010-i18n-content-pipeline.md`, `design/glossary.md` 의 "고유명사 번역 원칙"

### CI / CD
- GitHub Actions: macOS + Windows 매트릭스
- PR마다 lint + format + typecheck + test 자동 실행
- python-tcod 21+ 검증

### ECS-lite 사용 규칙 (ADR-0194, Accepted 2026-08-26)

**기본 (신규 시스템 추가 시)**: OOP / `@dataclass` 사용.

**ECS-lite 선택 허용 도메인**:
- `matrix/` (노드 그래프 — 방 → Entity 매핑)
- `engine/dungeon_view.py` (dungeon/room 시각화)

**ECS-lite 비권장 도메인**:
- `engine/state.py` (AppState), `combat/*`, `missions/*`, `equipment/*`,
  `programs/*`, `portraits/*`, `i18n/*`, `story/` — 모두 OOP / `@dataclass`

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

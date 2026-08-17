# Wet Run — Development Project

이 디렉토리는 `Game/wet_run/` 게임 프로젝트의 **코드 베이스**입니다. 게임 디자인 문서(`../design/`, `../decisions/`, `../wiki/`)와는 별개.

## 빠른 시작

### 1. 의존성 설치 (uv 사용, 권장)

```bash
cd Game/wet_run/prototype
uv sync --all-extras
```

### 2. 폰트 다운로드 (최초 1회)

```bash
make download-font
```

이 명령은 `data/fonts/terminal10x10_gs_tc.png` (libtcod 공식 폰트)을 다운로드합니다.

### 3. 게임 실행

```bash
make run
# 또는
uv run wet-run
```

빈 tcod 윈도우가 열리고, "You jack in. The world goes gray." 메시지가 표시됩니다. ESC로 종료.

### 3-1. 전체 게임 플로우 데모 (Phase 5+) ⭐

**프롤로그부터 첫 전투까지 완전한 게임 흐름 체험**:

```bash
make demo           # 전체 데모 자동 진행 (Prologue → Briefing → Matrix → Combat)
make demo-fast      # 빠른 타이핑
make demo-skip      # 프롤로그 건너뛰기 (Briefing부터)
make play           # 인터랙티브 모드 (직접 조작!)
```

**🎮 인터랙티브 모드** [`INTERACTIVE_GUIDE.md`](INTERACTIVE_GUIDE.md):
- **방향키로 자유롭게 던전 탐험**
- **NPC와 대화하며 다양한 선택**
- **전투에서 직접 스킬 선택**
- **다중 경로와 결과**

**⚡ 빠른 시작**: [`QUICK_START.md`](QUICK_START.md) - 30초 안에 Combat 체험!

**🎮 주요 조작법**: 
- **방향키 (↑↓←→)**: 이동 (Matrix) / 메뉴 선택
- **ENTER**: 확인/실행 (메뉴)
- **SPACE**: 액션 메뉴 (Matrix에서 노드 조작)
- **ESC**: 취소/나가기
- **1-9**: 빠른 선택 (숫자 키)

**📊 상태 피드백**:
- 모든 행동이 화면 하단에 메시지로 표시
- Side panel에 현재 상황 및 다음 행동 안내
- 실시간 쿨다운 및 AP 상태 표시

**📋 상시 상태 패널** (화면 우측, 28 columns):
- **PLAYER**: Grade, PPL, HP, AP (전투 중)
- **WHERE**: 현재 화면, 노드, 위치
- **MISSION**: 진행 중 미션, 보상, 목표
- **INVENTORY**: 보유 재료/아이템
- **ACTIVITY**: 최근 3개 행동 로그
- 자세한 내용: [`STATUS_PANEL_GUIDE.md`](STATUS_PANEL_GUIDE.md)

**🎨 시각적 피드백 (현재 노드 인식)**:
- **5가지 방법**으로 현재 위치 표시
  - Bright cyan 테두리 (`#═══║`)
  - Yellow 텍스트
  - Dark cyan 배경
  - 화살표 마커 (`> < v ^`)
  - "[ YOU ]" 라벨
- Title bar에 현재 노드 이름 표시
- 자세한 설명: [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md)

**📖 자세한 플레이 가이드**: [`DEMO_GUIDE.md`](DEMO_GUIDE.md) 참고
- 조작법, 화면 설명, 전략 팁 포함
- 단계별 체크리스트
- 트러블슈팅

**⚠️ 폰트 문제 해결**:

한글 자막은 현재 `[KO: N chars]` 형태로 표시됩니다 (폰트 한계).

**만약 영문도 깨져 보인다면**:
1. **텍스트 전용 데모로 내용 확인**:
   ```bash
   make text-demo  # 터미널에서 텍스트로 출력
   ```

2. **tcod 폰트 렌더링 테스트**:
   ```bash
   make test-tcod  # 폰트가 제대로 로드되는지 확인
   ```

3. **폰트 재다운로드**:
   ```bash
   rm data/fonts/terminal10x10_gs_tc.png
   make download-font
   ```

**흐름**:
1. **Prologue** (타이핑 효과) — 깁슨 원작 오프닝
2. **Finn Briefing** (NPC 대화) — 첫 미션 설명
3. **Matrix** (노드 그래프) — 사이버스페이스 진입
4. **Combat** (RT-MS) — ICE와의 첫 전투

**제어**:
- Space: 타이핑 스킵
- 방향키: Matrix 이동
- ENTER: Action Menu (ICE 노드에서 자동 열림)
- E: ENGAGE (전투 시작)
- 1-9: 스킬 사용
- Q: 종료

### 3-2. 개별 장면 시뮬레이터

깉슨 톤의 스토리를 타이핑 효과와 한글 자막으로 체험:

```bash
make prologue        # 프롤로그 (기본 속도)
make prologue-fast   # 프롤로그 (빠른 타이핑)
make briefing        # Finn 브리핑 장면
```

**기능**:
- 타이핑 효과 (character-by-character reveal)
- 글리치 효과 (random character corruption)
- 영어 원문 + 한글 자막 (bilingual)
- NPC 초상화 (ASCII portraits)
- Space로 타이핑 스킵, ESC로 장면 종료

### 3-3. Phase 1-5 신규 데모 (Dungeon · VFX · 미션매핑 · ECS · Novel)

**Phase 1-5 (ADR-0060, ADR-0061)** 가 추가한 핵심 게임플레이를 헤드리스로 검증 (창 불필요):

```bash
PYTHONPATH=src .venv/bin/python scripts/play_dungeon_mode.py     # Phase 1 — dungeon_mode + BSP
PYTHONPATH=src .venv/bin/python scripts/play_vfx_overlay.py      # Phase 1.5 — 4 VFX spawners
PYTHONPATH=src .venv/bin/python scripts/play_mission_mapping.py  # Phase 3 — Mission→Room
PYTHONPATH=src .venv/bin/python scripts/play_ecs_dungeon.py      # Phase 4 — ECS DungeonSystem
PYTHONPATH=src .venv/bin/python scripts/play_novel_runtime.py    # Phase 5 — Novel runtime
```

전부 0 종료 + 한 줄 요약 출력. 자세한 가이드: `scripts/README.md` 섹션 6.

### 4. 테스트 실행

```bash
make test
# 또는
uv run pytest
```

### 5. 린트 / 포맷 / 타입 체크

```bash
make lint       # ruff check
make format     # ruff format
make typecheck  # mypy
```

## 디렉토리 구조

```
prototype/
├── pyproject.toml          # uv / pip 프로젝트 설정
├── README.md               # 본 문서
├── Makefile                # 편의 명령
├── .gitignore
├── .editorconfig
├── .python-version
├── src/
│   └── wet_run/   # Python 패키지
│       ├── __main__.py     # 진입점
│       ├── engine/         # tcod 관련 (app, render, input, config)
│       ├── ecs/            # ECS-lite (entity, world)
│       ├── i18n/           # 번역 (translator)
│       ├── portraits/      # ASCII Portraits (manager)
│       └── data/           # 데이터 로더
├── tests/
│   ├── conftest.py
│   └── unit/               # 단위 테스트
├── data/
│   ├── i18n/               # en.json, ko.json
│   ├── portraits/          # portraits.json
│   ├── programs/           # programs.json
│   └── fonts/              # terminal10x10_gs_tc.png
├── scripts/
│   └── download_font.py    # 폰트 다운로드
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI
```

## Phase 상태

이 프로젝트는 **Phase 5 (Vertical Slice)** 완료. Phase 6 (콘텐츠 확장)에서 반복 보강.

- **Phase 4 (완료)**: 빈 프로젝트, 빌드/테스트/린트/CI 가능, hello-world 실행
- **Phase 5 (완료)**: 매트릭스, 전투 (RT-MS), 의뢰 시스템, BSP 던전, Novel Hook Dispatch
- **Phase 6 (진입)**: 콘텐츠 확장, 추가 미션/ICE/엔딩/단편

## 게임 디자인

- 결정 사항: `../decisions/README.md`
- 디자인 명세: `../design/GDD.md`
- 세계관: `../wiki/world/`
- 단계별 계획: `../ROADMAP.md`

## Python 버전

- **권장**: Python 3.11+ (tcod, hatchling 호환)
- **테스트됨**: 3.11, 3.12, 3.14 (3.14는 tcod 호환성 확인 필요)

## 라이선스

MIT

## [2026-08-17] chore(rename) | Project rename — Roguelike Sprawl → Wet Run

**Status**: ✅ 완료 — Project-wide display name rename (스코프 A). Python 패키지, 디렉토리 이름, 모든 .md/.html/.yml 파일의 display name 토큰 일괄 갱신. **5577 passed** (1 pre-existing portrait-size 회귀, rename 무관), ruff ✅, mypy strict ✅, uv sync OK (shebang 자동 갱신 via venv 재생성).

### 1. 변경 요약

- **Display name**: `Roguelike Sprawl` → `Wet Run`
- **Python 패키지**: `roguelike_sprawl` → `wet_run` (디렉토리 `prototype/src/roguelike_sprawl/` → `prototype/src/wet_run/`)
- **pyproject.toml**: `name = "roguelike-sprawl"` → `name = "wet-run"`, 스크립트 엔트리 `roguelike-sprawl` / `rs` → `wet-run` / `wr`
- **워크스페이스 디렉토리**: `Game/roguelike_sprawl/` → `Game/wet_run/`
- **모든 import 문**: 257 Python files (`from roguelike_sprawl...` → `from wet_run...`)
- **메타 문서 display name**: 378 files (스코프 A는 historical `_archive/`, `CHANGELOG.md`, `SETUP_LOG.md` 제외 — Q3 결정으로 historical 보존)
- **워크스페이스 외부 cross-reference**: 287 files (`Projects/AGENTS.md`, `INDEX.md`, `log.md`, `NEXT_SESSION_TODO.md`, `PHASE_1-26_INTEGRATION_REPORT.md`, `audit_vault.py`, `Language/log.md`, `decisions/README.md`, `Game/_publish/scripts/sync_dashboard_cards.py` 등)
- **GitHub URL**: **보존** (Q2 미해결 — GitHub repo는 아직 `seoca1/roguelike-sprawl` 이름 유지). README/INDEX/docs 등에서 URL 그대로.

### 2. 적용 범위

| 카테고리 | 파일 수 | 처리 |
|------|------|------|
| Python source | 255+ | import 문 일괄 갱신 |
| Python tests | 257+ | import 문 + 절대 path 일괄 갱신 |
| Python tools/scripts | 4+31 | path + module name 갱신 |
| YAML/CI | 6 | package path 갱신 |
| Markdown (display name) | 378 | `Roguelike Sprawl` → `Wet Run` |
| Markdown (workspace) | 287 | cross-reference 갱신 |
| HTML (dashboard) | (378에 포함) | chrome title/footer 갱신 |
| Historical (보존) | _archive/, CHANGELOG.md, SETUP_LOG.md | 그대로 |
| GitHub URL | 모든 docs | 그대로 (Q2 미해결) |

### 3. 검증

| Gate | Status | Notes |
|---|---|---|
| `uv sync` | ✅ | wet-run 패키지 정상 빌드, uv.lock 자동 갱신 |
| `make lint` (ruff) | ✅ | All checks passed |
| `make typecheck` (mypy strict) | ✅ | Success: no issues found in 211 source files |
| `make test` (pytest) | ✅ | **5577 passed**, 365 skipped, 1 xfailed (portrait-size pre-existing 회귀 1개는 rename 무관) |
| `.venv 재생성` | ✅ | 옛 `.venv/bin/interrogate` shebang (`/Game/roguelike_sprawl/`) 깨졌음 → `rm -rf .venv && uv sync --all-extras` 로 해결 |

### 4. Pre-existing 실패 (rename과 무관)

- `tests/unit/test_armitage.py::TestArmitagePortraits::test_portraits_have_10x14_grid` — `data/art/portraits/portraits.json` 의 실제 portrait size가 `[10, 12]` 로 변경되었는데 테스트는 `[10, 14]` 가정. Phase 45 이후 portrait 변경 회귀로 보이며 본 세션 범 외.

### 5. GitHub repo rename (별 후속 — Q2 미해결)

GitHub repo는 여전히 `seoca1/roguelike-sprawl` 입니다. 다음 사용자 작업 후속 필요:
- GitHub Settings → Rename repository → `seoca1/wet-run`
- rename 후 README/INDEX/docs의 `github.com/seoca1/roguelike-sprawl` → `github.com/seoca1/wet-run` 일괄 갱신
- Pages URL `seoca1.github.io/roguelike-sprawl` → `seoca1.github.io/wet-run` 자동 적용
- GH_TOKEN rotation 후 push 가능

### 6. Out-of-scope (preserved)

- `_archive/sessions/*.md` — historical session summaries (그대로)
- `CHANGELOG.md` — version history (그대로)
- `SETUP_LOG.md` — setup log (그대로)
- `dashboard/stories/*.html` — 게임 내 러닝 텍스트 (그대로, display chrome만 갱신)
- GitHub repo 이름 + URL — Q2 결정 후 별도 세션
- No push (user handles GH_TOKEN rotation)

---
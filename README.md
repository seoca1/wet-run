# Roguelike Sprawl

[![CI](https://github.com/seoca1/roguelike-sprawl/actions/workflows/ci.yml/badge.svg)](https://github.com/seoca1/roguelike-sprawl/actions)
[![Pages](https://github.com/seoca1/roguelike-sprawl/actions/workflows/pages.yml/badge.svg)](https://seoca1.github.io/roguelike-sprawl/)
[![Tests](https://img.shields.io/badge/tests-5281%20passing-brightgreen)]()
[![Lint](https://img.shields.io/badge/lint-ruff-blue)]()
[![Typecheck](https://img.shields.io/badge/typecheck-mypy%20strict-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()

윌리엄 깁슨의 스프롤 3부작(《뉴로맨서》, 《카운트 제로》, 《모나리자 오버드라이브》) 세계관을 기반으로 한 로그라이크 게임 개발 프로젝트.

플레이어는 **콘솔 카우보이(console cowboy)**가 되어 사이버스페이스에 진입, ICE를 뚫고 데이터를 탈취하며 임무를 수행한다. 죽으면 끝. 그러나 더 좋은 데크(cyberdeck), 프로그램, 웨웨어(wetware), construct로 돌아와 더 깊이 들어간다.

🌆 **Live Dashboard**: https://seoca1.github.io/roguelike-sprawl/

## 핵심 컨셉
- 매 런은 "잡(job)" — 의뢰인의 의뢰, 타겟 시스템, 보상
- 사이버스페이스에서의 해킹, 전투, 데이터 탈취
- 사이버펑크 톤 — 네온, 크롬, 거대 기업, 인공 지능
- "flatline" = 게임 오버

## 현재 상태 (2026-07-04)

- **Phase 5+6+7+8 완료** (19 commits in this session)
- **7 characters** × **8 scenes** = **56 GN scenes** (케이/실/카스/수트/위건/앤지/샐리)
- **47 missions** (5 zones 균형: Surface/Mid/Deep/Core/TA/Freeside)
- **41 ICE types** (Standard/Watchdog/Black/Goliath/Construct/Construct-proxy 등)
- **10 manual + 1 auto save slots** (Phase 7.3)
- **pytest 4231 passed** / ruff 0 errors / mypy strict 0 errors / mkdocs --strict 0 warnings (316 pages)

## 디렉토리 구조

| 경로 | 목적 | 비고 |
| --- | --- | --- |
| `raw/` | 원본 자료 (Gibson 소설, 레퍼런스) | 읽기 전용 |
| `wiki/` | LLM이 유지하는 지식 베이스 (세계관, 메카닉) | LLM Wiki |
| `design/` | 활성 게임 디자인 명세 | 사용자/AI가 함께 편집 |
| `testcases/` | 게임플레이 테스트 케이스 / 시나리오 | 디자인과 동기화 |
| `decisions/` | 결정 기록 (ADR) | 결정은 immutable, draft는 mutable |
| `prototype/` | 프로토타입 코드 (엔진 결정 후) | 미정 |
| `ROADMAP.md` | 단계별 계획 | 본 디렉토리 루트 |
| `AGENTS.md` | AI 에이전트 작업 가이드 | 본 디렉토리 루트 |
| `SESSION_SUMMARY.md` | 세션 요약 (현재 상태) | 세션 단위 |

## 빠른 시작

1. `SESSION_SUMMARY.md` — 현재 세션 요약 (가장 먼저)
2. `ROADMAP.md` — 현재 단계와 다음 단계 확인
3. `decisions/README.md` — 미해결 결정 사항 확인
4. `CHARACTER_PATHS.md` — 7자 비교표 + 선택 가이드
5. `wiki/world/sprawl_universe.md` — 세계관 컨셉 참조

## 주요 문서

- 모든 문서는 마크다운, Git으로 버전 관리
- LLM Wiki 패턴: `raw/` → `wiki/` (원본 → 정리)
- 결정 사항은 `decisions/`에 ADR 형식으로 기록 (결정 후 immutable)
- 디자인 변경 시 `testcases/`도 동기화

## 최근 작업 (2026-07-04)

19 commits, Phase 5+6+7+8 통합:

- **인프라 정리**: lint/mypy 174 errors → 0, mkdocs --strict 워닝 41 → 0
- **MkDocs 통합**: 316 pages (wiki + design + decisions 통합)
- **3명 캐릭터 추가**: Suit (4번째, 3인칭), Wigan (5번째, 1인칭 loa), Angie (6번째, 1인칭 12세), Sally (7번째, 1인칭 cold operator)
- **9 미션 추가**: Mid (Hosaka/Sense-Net/Yakuza), Core (T-A payroll/Maas/Construct 기억), TA (Straylight/3Jane/Wintermute)
- **3 ICE 추가**: corporate_guard (MID), archive_sentinel (CORE), wintermute_proxy (TA boss)
- **세이브 시스템**: 5슬롯 → 10슬롯 + 자동저장 슬롯

상세: [`SESSION_SUMMARY.md`](./SESSION_SUMMARY.md), [`ROADMAP.md`](./ROADMAP.md), [`log.md`](../../Fiction/wiki/log.md).

## 개발 추적

- 📋 **GitHub Projects 보드**: https://github.com/users/seoca1/projects (수동 설정 가이드: [`docs/GITHUB_PROJECTS_SETUP.md`](./docs/GITHUB_PROJECTS_SETUP.md))
- 🐛 **Issue Templates**: `.github/ISSUE_TEMPLATE/` (bug.md / dashboard.md / feature.md)
- 🏷️ **Auto Labels**: `.github/labeler.yml` (12개 phase/character labels)
- 🔄 **CI**: `.github/workflows/` (ci.yml, pages.yml)

## 핵심 데모 명령

```bash
cd prototype
make test      # 5281 tests
make all       # format + lint + typecheck + test

# 그래픽 노블 자동재생 (7 캐릭터)
uv run python scripts/graphic_novel.py --mode novice --lang ko
uv run python scripts/graphic_novel.py --mode sally --lang en

# 전투 시뮬레이터
uv run python scripts/combat_simulator.py --ppl 24 --enemy standard
uv run python scripts/combat_grades.py  # 5등급 비교
uv run python scripts/death_in_action_demo.py  # Combat → Death 5-Phase

# 풀 게임 자동플레이
uv run python scripts/play.py --duration 30
```

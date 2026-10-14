# Jev 시각 자동 플레이 데모 검증 도구 설계 (Visual Auto-Play Demo Verifier)

> **버전**: 0.1.0-draft  
> **관련**: `docs/demo-tool-inventory.md`, `scripts/jev-alt-eval.py`, `scripts/wet_run_verify.py`, `AGENTS.md` §6, `skills/playwright`

## 1. 목적

`wet_run` 자동 플레이 화면을 **시각적으로 캡처**하고, 각 턴의 결정(코드/문서 변경, 미션 선택)이 **Jev AGENTS.md §6 하드블록**을 위반하는지 **Noul 분류**로 검증한다.

## 2. 원리

```
Playwright (자동 플레이/스크린샷)
    ↓
Turn event (미션 완료 / ICE break / 선택)
    ↓
Jev Noul (OpenRouter Decisions API — WF1 gold 기준)
    ↓
분류: violation / fine + p ≥ 0.6 기준
    ↓
시각 로그 (스크린샷 + JSON) + advisory 출력
```

## 3. 구조

| 구성 | 파일/도구 | 역할 |
|---|---|---|
| 자동 플레이 엔진 | Playwright (MCP `playwright`) | `Game/wet_run/web/` 또는 `docs/dashboard/` 페이지 자동 내비게이션 |
| 시각 캡처 | `page.screenshot()` + video | 각 턴 상태 기록 |
| Jev 분류 | `scripts/jev-alt-eval.py` 확장 / `scripts/demo-journal/jev-turn.py` | turn별 AGENTS.md §6 질문 (Noul) |
| 출력 | `docs/demo-reports/` (마크다운 + PNG) | `verification-framework.md`와 연동 |

## 4. Jev 연동 방식 (핵심)

- 기존 `jev-alt-eval.py`는 **글로벌** WF1 gold (30 samples) 사용
- 데모 도구는 **턴 로컬**: 각 플레이 턴의 `state` (변경 내용) 업로드 → `QUESTION` (AGENTS.md §6) → `p` 계산
- **기준**: `p ≥ 0.6` = block (위반); `< 0.6` = advisory (never-route, 로컬 로그만)
- **원시 응답**: 아카이브 금지 (AGENTS.md §6(6) 및 기존 `jev-alt-eval.py` 주석 준수)

## 5. 실행 예시 (향후)

```bash
# 1. 시각 플레이 (Playwright)
python3 tools/demo-journal/auto-play.py --target Game/wet_run/web/ --steps 5

# 2. Jev 분류 (각 턴)
OPENROUTER_API_KEY=... python3 scripts/demo-journal/jev-turn.py --turn 3

# 3. 통합 보고
python3 scripts/wet_run_verify.py --full --out docs/design/verification-report.md
```

## 6. 제약 (Hard Constraints)

- `OPENROUTER_API_KEY`: 환경변수만 (코드 내 하드코딩 금지)
- 50+ 파일 세션 금지 → 도구는 `scripts/` + `docs/` 내 소수 파일만 생성
- `raw/` 수정 금지 (데모 보조 데이터는 `tools/demo-journal/` 또는 `docs/`에)
- `broken wikilink`: 세션 종료 전 `audit_vault` 0 확인

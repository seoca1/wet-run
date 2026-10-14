# Wet-Run 게임성 검증 프레임워크 (Verification Framework)

> **버전**: 1.0.0-draft  
> **최종 업데이트**: 2026-10-14  
> **관련**: `docs/design/core_loop.md`, `docs/design/balance/`, `scripts/jev-alt-eval.py`, `scripts/audit_vault.py`, `AGENTS.md` §6, `infra/llm/wiki/SUBAGENT_MODEL_STRATEGY.md`

## 1. 목적 (Purpose)

`Game/wet_run/` 게임성(밸런스 + AI 분류 품질 + 워크플로우) 검증을 **체계화**하고, 기존 도구(`jev-alt-eval`, `audit_vault`)를 **종합**하여 하나의 파이프라인으로 구현한다.

| 영역 (Scope) | 대상 | 점검 항목 |
|---|---|---|
| 1. 미션/ICE 밸런스 | `web/` (TS + Vitest) + `docs/design/balance/` | 난이도 곡선, 성공률 분포, 자원 소모 비율 |
| 2. AI 분류/의사결정 | `scripts/jev-alt-eval.py` + `infra/llm/` | Jev Noul 합의율(p≥0.6), AGENTS.md §6 하드블록 위반 여부 |
| 3. 워크플로우/시스템 | `docs/` (wiki/design/architecture) + `audit_vault.py` | broken wikilink, orphan, raw/ 수정 여부, ADR immutable 여부 |

## 2. 검증 방법 (Method) — 3층 구조

```
┌─────────────────────────────────────────────┐
│  3. 파이프라인 실행 (Pipeline Execution)     │  ← scripts/wet_run_verify.py
│     audit_vault + jev-alt-eval + balance     │
├─────────────────────────────────────────────┤
│  2. AI 분류 검증 (Jev Verification)         │  ← WF1 gold (30 samples)
│     Noul 질문: "이 변경이 §6 하드블록     │     위반인가?"
├─────────────────────────────────────────────┤
│  1. 밸런스 metric 수집 (Balance Metrics)      │  ← web/ 테스트 + design 데이터
│     mission success rate, ICE break time    │
└─────────────────────────────────────────────┘
```

### 2.1 1번 — 미션/ICE 밸런스 (Mission / ICE Balance)

- **입력**: `docs/design/balance/` JSON + `web/src/game/` 테스트 시나리오
- **메트릭**: `success_rate` (T1~T3 별), `mean_time_to_ICE_break`, `resource_consumption_ratio`
- **기준**: `core_loop.md` §3 (플레이어 아키타입별 진행 경로)이 제시하는 T1→T3 난이도 상승률과의 편차 ±15% 이내
- **도구**: `npm test` (`web/`) + Python `json` 파싱

### 2.2 2번 — Jev 분류 검증 (AI Decision Verification)

- **기존**: `scripts/jev-alt-eval.py`는 `gold-agents-guard-2026-09-23.json` 기반 WF1 gold Noul 30샘플을 사용해 OpenRouter Decisions API로 합의율 측정
- **확장**: `wet_run` 규약(`AGENTS.md`)의 §6 하드블록 6항을 `QUESTION`에 추가하여, **게임 변경(코드/문서)**이 규약 위반인지 Jev가 판별하도록 확장
- **기준**: `p ≥ 0.6` (block threshold); 합의율 < 0.6 시 `advisory` 로그만 기록 (never-route, `jev-classifier.js`와 동일)

### 2.3 3번 — 워크플로우/시스템 검증 (Workflow / System)

- **관련**: `scripts/audit_vault.py` (vault-wide broken link + orphan + false-positive 분류)
- **적용 범위**: `Game/wet_run/` 내 `docs/` + `web/` + `data/` (단, `data/raw/`는 읽기전용 — 수정 시 audit 실패)
- **체크**: broken wikilink 0, orphan 0 (또는 `index.md`/`log.md` 인용 존재), `raw/` 수정 없음, Accepted ADR 변경 없음

## 3. 통합 도구 구현 (Integrated Tool Implementation)

**파일**: `scripts/wet_run_verify.py`

### 3.1 구성

| 모듈 | 소스 | 역할 |
|---|---|---|
| `balance_check()` | `Game/wet_run/web/` + `docs/design/balance/` | Vitest/JSON 기반 메트릭 수집 |
| `jev_check()` | `scripts/jev-alt-eval.py` (import/replicate) | AGENTS.md §6 기반 Noul 평가 |
| `audit_check()` | `scripts/audit_vault.py` (subprocess) | vault-wide 링크/유효성 |
| `pipeline()` | 통합 | 결과를 JSON + markdown 로그로 출력 |

### 3.2 실행 흐름

```bash
# 1. 밸런스 (선택적 — web/ 테스트 실행)
cd Game/wet_run/web && npm test -- --reporter=json > /tmp/balance.json

# 2. Jev (API 키 필요 — advisory-only로 유지)
OPENROUTER_API_KEY=... python3 scripts/wet_run_verify.py --jev --samples 30

# 3. Audit (항상)
python3 scripts/wet_run_verify.py --audit

# 4. 통합 보고
python3 scripts/wet_run_verify.py --full --out docs/design/verification-report.md
```

### 3.3 출력 형식

- `docs/design/verification-report.md`: 이번 세션 검증 요약 (1/2/3 영역별 pass/fail, 근거 인용)
- `Game/wet_run/log.md`: `[YYYY-MM-DD] verify | 제목` 형식 (AGENTS.md §3.1 / §6)
- `scripts/jev-alt-eval.py`와 동일한 원시 응답은 **아카이브하지 않음** (raw 응답 보존 금지 — `AGENTS.md` §6(6) 및 기존 `jev-alt-eval.py` 주석 준수)

## 4. 규약 준수 (Compliance with Rules)

- `raw/`: 수정 금지 (현재 삭제됨; `data/`만 존재 — `data/raw/`는 비활성 확인)
- `wiki/`: 인용 필수 (`[[...]]` 링크는 `docs/wiki/` 또는 `Fiction/wiki/` 인용)
- `Accepted ADR`: `decisions/` 내 `Status: Accepted`는 immutable (변경 시 신규 ADR 작성)
- `50+ 파일 한 세션`: 이번 프레임워크는 문서 2~3개 + 스크립트 1개 + 로그 2개 = 5~6개로 제한
- `broken wikilink`: 세션 종료 전 `audit_vault.py` 0 확인 (본 문서 작성 시 점검 완료 — `log.md` 기록)
- `secrets`: `OPENROUTER_API_KEY`는 환경변수; 코드 내 하드코딩 금지

## 5. 다음 단계 (Next Steps)

1. `scripts/wet_run_verify.py` 실제 구현 (Jev 모듈 + audit 호출)
2. `web/` 테스트 데이터로 `balance_check()` 검증
3. `docs/architecture/0009-verification-pipeline.md` (또는 기존 `0010-...`) 생성하여 파이프라인 아키텍처 기록
4. `AGENTS.md` §3.1 워크플ロー에 "검증 단계" 추가

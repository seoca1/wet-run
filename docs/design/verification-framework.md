# Wet-Run 검증 도구 (Verification Framework)

> **버전**: 3.1.0 — 단일 진입점 `scripts/wet_run_verify.py` + 실 Jev · gear 골든 · prettier 게이트
> (ADR-0335/0336). 2.x 는 도구 인벤토리를 세운 버전(ADR-0333/0334).
> **최종 업데이트**: 2026-11-19
> **관련**: `docs/design/core_loop.md`, `docs/design/balance/`, `AGENTS.md` §3·§6,
> `docs/wiki/decisions/0333-verification-tools-must-verify-themselves.md`,
> `docs/wiki/decisions/0334-a-checker-that-cannot-fail-is-not-a-checker.md`,
> `docs/wiki/decisions/0335-the-verification-routine-is-one-command.md`,
> `docs/wiki/decisions/0336-the-other-half-of-verification.md`

## 0. 왜 이 문서가 있는가

이 게임의 주장 — *"테스트 4451개"*, *"게이트 7종 CLEAN"*, *"balance byte-identical"* — 은
**검증 도구가 진짜일 때만** 의미가 있다. 2026-11-18 에 도구를 실측한 결과 **절반이 검증을 하지
않는 연극**이었고(ADR-0333), 그래서 도구를 **신뢰 등급별로 분류**한다. 새 도구를 추가하면 여기에
등급과 함께 등록한다.

**원칙**: 한 줄의 검증 주장은, 그 주장을 **깨뜨렸을 때 실패하는 도구**가 있어야만 검증이다.

## 0.5 단일 진입점 — 검증 러틴 (ADR-0335)

루틴은 이제 **한 명령**이다. 위치 독립적이고(자기 경로로 워크스페이스를 찾음), 게이트가 하나라도
실패하면 **exit 1** 을 낸다. Jev 는 **advisory**(로컬·미보정, 게이트 아님).

```bash
python3 scripts/wet_run_verify.py --full          # 게이트 8종 + advisory Jev + npm test
python3 scripts/wet_run_verify.py                 # 빠르게: npm test 제외, Jev 제외
python3 scripts/wet_run_verify.py --full --log    # log.md 에 한 줄 기록
```

| # | 영역 | 명령 (cwd) | 게이트? |
|---|---|---|---|
| 1 | balance | `npm run balance:check` (web) | ✅ |
| 1b | gear | `npm run gear:check` (web) | ✅ |
| 2 | tests | `npm test` (web, `--tests`/`--full`) | ✅ |
| 3 | audit | `scripts/audit_vault.py` (루트) | ✅ |
| 4 | doc | `check_doc_claims.py` — AGENTS+README(전체)·ROADMAP(수치만) (wet_run) | ✅ |
| 5 | prose | `check_no_novel_prose.py` (wet_run) | ✅ |
| 6 | briefings | `tools/import_briefings.py --check` (wet_run) | ✅ |
| 7 | links | `tools/find_broken_links.py` (wet_run) | ✅ |
| 8 | lang | `mixed_language_audit.py --root Game/wet_run --source` (루트) | ✅ |
| 9 | jev | `jev-call.sh`(실) → `jev-local-call.sh`(로컬) (루트) | ❌ advisory |

## 1. 도구 인벤토리

### A. 진짜 — 실측으로 검증력 확인됨 (trusted)

| 도구 | 명령 (실행 위치) | 검증 대상 | 실패 조건 |
|---|---|---|---|
| 문서 주장 | `python3 scripts/check_doc_claims.py` (`Game/wet_run`) | AGENTS.md 의 경로·수치 vs 저장소 실측 | dead path / 수치 드리프트 / ADR namespace |
| vault 링크 | `python3 scripts/audit_vault.py` (워크스페이스 루트) | broken wikilink · orphan | broken > 0 → exit 1 |
| 원작 문구 | `python3 scripts/check_no_novel_prose.py` (`Game/wet_run`) | 게임 문자열 vs Fiction 인용 8-gram | 8단어 연속 일치 → exit 1 |
| 서사 원장 | `python3 scripts/tools/import_briefings.py --check` (`Game/wet_run`) | 브리핑 원장 vs 게임 데이터·재현성 | 불일치 → exit 1 |
| 프로젝트 링크 | `python3 scripts/tools/find_broken_links.py` (`Game/wet_run`) | wet_run docs 링크 (cross-project Fiction 포함) | broken > 0 → **exit 1** |
| 혼용 감사 | `python3 scripts/mixed_language_audit.py` (루트) | **`*.md`** CJK 혼용 | 위반 > 0 — ⚠ 범위가 md 한정(§3-4) |
| 단위/통합 | `cd web && npm test` | 리듀서·상태·데이터 계약 (4451) | 실패 > 0 |
| 밸런스 하네스 | `cd web && npm run balance` | **결정론적** 등급 곡선 (실 리듀서 구동) | 값 자체가 아니라 회귀는 §B 가 판정 |
| 브라우저 e2e | `cd web && PLAYWRIGHT_BASE_URL=… npx playwright test` (+ `SOAK=1`/`STORY=1`) | 화면·조작·세이브·연출·VFX·터치 (desktop 54 · mobile 58) · soak 프리즈 0 · story | 수동 — smoke 는 배포 전용, soak/story 는 수동 트리거 (ADR-0340) |

### B. 게이트 — 자동 회귀 감지 (gate)

| 도구 | 명령 | 역할 |
|---|---|---|
| 밸런스 golden 기록 | `cd web && npm run balance:golden` | 3덱 × 등급 곡선을 `web/scripts/balance.golden.json` 에 기록 |
| 밸런스 golden 대조 | `cd web && npm run balance:check` | 기본 **엄격**(어느 방향이든 드리프트 → exit 1) |
| gear golden 기록/대조 | `cd web && npm run gear:golden` / `gear:check` | 장비 착용 곡선(encounter/mission × 5세트)을 `gear.golden.json` 에 기록·대조 (ADR-0336) |
| CI 회귀 게이트 | (자동) `.github/workflows/game-balance-test.yml` | `balance:check --allow-improvement` — **하락만** PR 차단 |
| CI 단위 테스트 | (자동) `.github/workflows/ci.yml` | `npm test` · typecheck · lint · **format** · build |

> `--allow-improvement` 는 상향(버프)을 통과시키고 **하락**만 막는다. 국소 변경이 밸런스를 움직였는지
> 확인할 때는 로컬에서 기본(엄격) 모드로 돌린다.

### C. 진단 — 수동 측정 (diagnostic, 게이트 아님)

| 도구 | 명령 | 역할 |
|---|---|---|
| 생존 곡선 | `cd web && npm run survival -- --seeds 64 --cards best --loot value` | 64시드 생존률 (per-cell) |
| 캠페인 + 엔딩 | `cd web && npm run campaign` | 3다리 승률 + **표시 엔딩 분포**(sacrifice/liberation/control — 최종 leg+사망만) + 완주 크레딧 분위수 — 엔딩의 권위 있는 측정 (ADR-0337) |
| 크래프팅 도달 | `cd web && npm run crafting -- --seeds 12 --runs 3` | 재료 경로 도달률 |
| 장비 착용 곡선 | `cd web && npm run gear` | 장비 티어별 곡선 |
| 단일-미션 엔딩 | `cd web && npm run endings` | 단일-미션 모델(`missionsCompleted=1`)·단일 시드 — `control`/`liberation` 은 대표적이지 않다 (ADR-0337) |
| **mutation spike** | `cd web && npm run mutation` | 전투 상수를 뒤집어 **테스트가 실제로 잡는지** (신규, ADR-0333) |

### D. 조건부 / 이력 (conditional & removed)

| 도구 | 상태 |
|---|---|
| `scripts/wet_run_verify.py` | 이제 **단일 진입점**이다(§0.5, ADR-0335) — 게이트 8종을 순서대로 돌리고 하나라도 실패하면 exit 1, Jev 는 advisory. 2.x 의 "연극"(하드코딩 p·수기 metrics) 문제는 ADR-0334 에서 제거됨. |
| ~~`web/src/game/metrics.json`~~ | **삭제됨**(ADR-0334). 2026-10-14 수기 stale 데이터, 소비자는 위 스크립트 하나뿐이었다. |
| ~~`scripts/tools/audit_sprawl.py`~~ | **삭제됨**(ADR-0334). `sys.exit` 부재로 **항상 exit 0** — 실패할 수 없는 검사기는 게이트가 아니다. `find_broken_links.py` 와 중복. 고아 검사는 `audit_vault.py` 가 담당. |
| ~~`web/scripts/balance_compare.ts`~~ | **삭제됨**(ADR-0333). 정규식이 harness 출력과 불일치 → 항상 "No regression". `npm run balance:compare` 는 `balance_baseline.ts --check --allow-improvement` 별칭. |

## 2. 실행 순서 (세션 마감 체크리스트)

```bash
# 단일 명령 (루틴) — 게이트 8종 + advisory Jev, 실패 시 exit 1
python3 scripts/wet_run_verify.py --full

# 세부 게이트를 따로 돌릴 때
cd Game/wet_run/web && npm run typecheck && npm run lint && npm test && npm run build
cd Game/wet_run/web && npm run balance:check      # 밸런스 golden (엄격)
cd Game/wet_run/web && npm run mutation           # 테스트 유효성 (진단)
cd Game/wet_run     && python3 scripts/check_doc_claims.py \
  && python3 scripts/check_no_novel_prose.py \
  && python3 scripts/tools/import_briefings.py --check \
  && python3 scripts/tools/find_broken_links.py
cd ../..            && python3 scripts/audit_vault.py \
  && python3 scripts/mixed_language_audit.py --root Game/wet_run --source
```

## 3. 알려진 커버리지 구멍 (Gaps)

**해소됨 (ADR-0335/0336)**
- ~~`AUTO_ATTACK_INTERVAL_MS` 미검증~~ → 값 고정 테스트, mutation 셋도 **10 변이 / 10 테스트**로 확장 → **10/10 KILLED**.
- ~~Jev 미배선~~ → `--jev` 가 **실 Jev**(`jev-call.sh`, 보정)를 먼저, 실패 시 로컬로 폴백. `calibration` 표기.
- ~~claim checker 가 AGENTS.md 만~~ → AGENTS+README(전체) + **ROADMAP(수치만)** 기본.
- ~~혼용 감사가 md 만~~ → `--source`.
- ~~prettier 미강제~~ → `.prettierrc.json`(printWidth 100) + **138 파일 정규화** + `ci.yml` format **게이트**.
- ~~gear 골든 부재~~ → `gear.golden.json` + `gear:check` (러틴 1b 게이트).
- ~~`wet_run_verify.py` 연극~~ → ADR-0334 재작성 → ADR-0335 단일 러틴.

**남음**
1. **Jev 는 그래도 advisory** — 실 Jev 는 보정됐지만 이 러틴은 게이트로 쓰지 않는다(§6 자동화는 별도 판단).
2. **e2e 는 수동** — 브라우저 + preview 서버가 필요해 러틴(`wet_run_verify.py`) 밖에 있다. `--e2e` 플래그로
   한 명령이 될 수 있다(후속). soak/story 드라이버는 코드가 화면/키를 바꾸면 **조용히 낡는다**(ADR-0340).
3. **장비↔난이도 미해결** — T6 가 g5/g6 를 95/99 로(ADR-0341 Draft). bare 골든 재기록이 따른다.
4. **g4 난이도 신호** — ADR-0339(Draft). 난이도 자체는 미변경.
5. **mutation 기본 셋은 여전히 좁다** — combat 중심(`--tests` 확장, 다른 모듈로 확대).
6. **골든 커버리지** — bare(balance) + 장비(gear)는 고정. 엔딩/캠페인은 진단 도구일 뿐 게이트가 아니다.
7. **ROADMAP 은 수치만** — 역사 경로는 검사 밖(의도).

## 4. 변경 이력

- 2026-11-19 (b): **3.2.0 후속 4건** (ADR-0337~0341) — 엔딩 control 복원 · 계약 재료 carry · g4/장비 브리프 ·
  **브라우저 e2e 전수 실행 + soak 드라이버 동기화**.
- 2026-11-19 (a): **3.1.0 후속 5건** (ADR-0336) — 실 Jev 우선 배선 · ROADMAP counts-only 검사 ·
  mutation 10/10 · gear 골든 게이트(1b) · prettier 138 파일 정규화 + CI 게이트.
- 2026-11-18 (c): **3.0.0 단일 진입점** (ADR-0335) — `wet_run_verify.py` 가 게이트 8종 + advisory Jev 를
  순서대로 돌리는 러틴이 됨(위치 독립·exit 1) · Jev 실배선 · claim checker AGENTS+README ·
  혼용 감사 `--source` · mutation 6/6 · CI 중복 정리 · prettier 게이트 미채택(139 파일) 기록.
- 2026-11-18 (b): **2.1.0 정리** (ADR-0334) — `wet_run_verify.py` 재작성(가짜 p 제거·실 balance 대조·
  선택적 로그) · `metrics.json` 삭제 · `audit_sprawl.py` 삭제(항상 exit 0이던 중복 검사기).
- 2026-11-18 (a): **2.0.0 재작성** (ADR-0333) — 도구 7종 실측 → 신뢰 등급별 인벤토리, 밸런스 golden 게이트
  + mutation spike 추가, `wet_run_verify.py` 를 "연극"으로 표기.
- 2026-10-14: 1.0.0-draft — 3층 파이프라인 설계(구현은 스텁으로 남음).

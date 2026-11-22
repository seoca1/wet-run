# SESSION SUMMARY — 2026-11-18 → 2026-11-22 · 검증 도구 전면 정비 + 게임 버그 발굴

> **핸드오프**: 이 문서가 다음 세션의 진입점이다.
> **관련 ADR**: 0333~0353 (21건). **커밋**: wet_run 30+ · workspace 1 (아래 목록).
> **한 줄**: "검증 도구를 검증했더니 절반이 연극이었고, 고친 뒤 그 도구로 게임을 재검증하니 진짜 버그가 나왔다."

## 0. 이 세션의 흐름 (T1 → T8)

| 단계 | 한 것 | 결과 |
|---|---|---|
| **T1 검증 도구 감사** | 도구 7종을 실측 → 절반이 "연극"(balance_compare 정규식 불일치·wet_run_verify 스텁·audit_sprawl 항상 exit 0) | ADR-0333 |
| **T2 정리** | 죽은 도구 제거 · `wet_run_verify.py` 정직화 · `metrics.json`·`audit_sprawl.py` 삭제 | ADR-0334 |
| **T3 단일 러틴** | 게이트 8종 + advisory Jev를 한 명령·exit 1로 | ADR-0335 |
| **T4 후속 5건** | 실 Jev · ROADMAP 검사 · mutation 6→10 · **gear 골든** · prettier 정규화(138파일)+게이트 | ADR-0336 |
| **T5 게임 재검증** | 러틴 + 진단으로 전수 검증 → P1~P5 도출 (엔딩·g4·경제·장비·e2e) | — |
| **T6 게임 정정** | 엔딩 control 복원 · 경제 T2 병목 · 드롭 테이블 확인 | ADR-0337·0342·0343 |
| **T7 브라우저** | e2e 전수 실행(desktop 54·mobile 58·soak 0프리즈·story) + soak 드라이버 수정 · Jev 자문 | ADR-0340 |
| **T8 mutation 캠페인** | 셋 10→39, 8개 모듈 확대, **진짜 버그 1 발견** | ADR-0344~0353 |

## 1. 검증 도구 (현재 canonical)

**단일 러틴**: `python3 scripts/wet_run_verify.py --full` → 게이트 **9종** + advisory Jev, 실패 시 exit 1.
(balance · gear · tests · audit_vault · doc_claims · no_novel_prose · briefings · links · language)

| 도구 | 역할 |
|---|---|
| `web/scripts/balance_baseline.ts` (+ `.golden.json`) | 밸런스 골든 대조 (bare runner, 3덱) |
| `web/scripts/gear_baseline.ts` (+ `.golden.json`) | 장비 착용 곡선 골든 |
| `web/scripts/mutation_spike.ts` | **mutation 39종** (전투·엔딩·경제·매트릭스·카드·팩션·세이브·오디오·i18n·PWA·GN·크롤러·achievements) |
| `scripts/check_doc_claims.py` | AGENTS+README(전체)·ROADMAP(수치) 대조 |
| `scripts/mixed_language_audit.py --root --source` | md+소스 CJK 혼용 |
| `docs/design/verification-framework.md` | **도구 인벤토리 + 신뢰 등급 + 갭** (single source) |

## 2. 게임 정정 (실측)

- **엔딩 control 복원**(ADR-0337): 표시 엔딩 = sacrifice 52.7% · liberation 44.4% · **control 2.9%**(옛 0%).
- **경제 T2 병목 해소**(ADR-0342): 도달률 T2 3.3%→47~58%, 전 등급 47~79%. probe를 실 지갑(`earnedMaterials`)·실데이터로 고침.
- **드롭 테이블은 교정 대상 아님**(ADR-0343): ICE loot은 tier에 단조; 등급별 wobble은 미션 구성 탓. 모니터+가드 추가.
- **씬 스킵 무한 루프 수정**(ADR-0351): **진짜 버그** — mutation이 hang으로 드러냄.
- **월렛 carry + seed 수정**(ADR-0338) — 이전 세션(P3) 후속.

## 3. 현재 기준선 (2026-11-22)

```
vitest        238 files / 4459 tests / 0 fail
typecheck     0 error · lint 0 error · build OK
mutation      39/39 KILLED
goldens       balance/gear byte-identical
러틴          9/9 pass (+ advisory real Jev)
e2e           desktop 54p/5s · mobile 58p/1s · soak 0 프리즈 · story pass
게이트        audit_vault CLEAN · mixed_language 0 · doc_claims OK (273 ADR 0001–0353)
```

## 4. 다음 작업 (순서)

1. **mutation 나머지 함수형 모듈** — 던전 크롤러 *로직*, 허브, 대사 트리 등 (anchor 설계 필요).
2. **오너 결정 4건** (아래 §5) — 하나라도 결정되면 구현·재측정·골든 재기록.
3. **`endRun` 외 앱-루프 로직** 추출(세이브 슬롯 결정 등) — ADR-0346/0347 방식.
4. **e2e를 러틴에** (`--e2e` 플래그; 브라우저 필요).

## 5. 오너 결정 대기 (동결됨)

| ADR | 결정 | 현재(추천) |
|---|---|---|
| 0339 | g4 난이도 | **C 유지**(신호). 대안 A 재기록 / B 난이도 복원 |
| 0341 | 장비↔난이도 | **C 유지**(파워 판타지). Jev는 B(raise_ice 0.58) |
| 0337 | `CONTROL_WEALTH` | 18000 유지(2.9%, 희귀) |
| 0337 | `status_quo` 미표시 | 유지(레거시 전용) |

## 6. ⚠️ 함정 (다음 세션이 반드시 알 것)

| 함정 | 내용 |
|---|---|
| **mutation은 소스를 변이했다 되돌린다** | 중단(SIGINT/TERM)되면 파일이 변이된 채 남을 수 있다 → **커밋 전에 `git status`로 소스 확인**. spike는 이제 시그널 복구+프리플라이트가 있으나 **`timeout`이 `npm`에 보내면 못 잡는다** → 직접 `npx tsx scripts/mutation_spike.ts`로 돌릴 것. |
| **SURVIVED ≠ 항상 구멍** | (a) 누락된 테스트 파일(셋에 추가) (b) 상수 import로 값 미고정(계약 테스트). 이 세션에 둘 다 나왔다. |
| **HANG은 실패보다 나쁘다** | 동기 무한 루프는 스위트를 멈춘다(ADR-0351). mutation은 KILLED/SURVIVED/**HANG** 3종. |
| **기록 기준선은 bare runner** | balance/survival는 EMPTY_LOADOUT. 장비 배선은 no-op이어야 한다. |
| **survival 정책 두 가지** | 기본 `first/card`(훨씬 어렵다) vs 참조 `best/value`. `jev-difficulty.sh`는 참조로 고침. |
| **probe는 실 지갑·실데이터를 읽어야** | `crafting_probe`가 자체 모델·복사본을 쓰던 것을 실 `earnedMaterials`·`recipes.json`로 고침(ADR-0342). |
| **golden 재기록** | 의도된 밸런스 변경은 `npm run balance:golden`/`gear:golden`. 안 하면 `:check`가 실패. |

## 7. 커밋 (참고)

wet_run: `97327a62`(format) · `a01dc6a4`(verify routine) · `8e263613`(economy) · `7018…`(endings) ·
`2ba17e81`+`3c625424`+`c5600e83`+`b296a314`+`a40866a3`+`cb778b27`+`53017759`+`fa72b7f8`+`70d8b99e`+`d5930b3c`+`d33117c4`(mutation 12→39) …
workspace: `60af47b`(verify routine + mixed-language source + jev-difficulty 폴리시).

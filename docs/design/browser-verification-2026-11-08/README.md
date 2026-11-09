# Browser verification — 2026-11-08 (wet_run)

**요청(오너)**: "지금까지 반영된 것을 브라우저 실행 테스트로 검증해 볼 수 있어? 여러 회차 해서
통계적 수치도 검증하고, 여러 번 하는 김에 오류 발견도 하고."

**결론**: 게임의 **밸런스 수치와 동작은 재현됐고**(기록치와 소수점까지 일치, 프리즈 0),
대신 **하네스 3건 · 테스트 1건 · 게임 회귀 1건 · 게임 소프트락 1건**을 찾아 고쳤다.

## 무엇을 돌렸나

| 단계 | 명령 | 결과 |
|---|---|---|
| 빌드 | `npm run build` | PASS (144 modules) |
| e2e (desktop + mobile) | `PLAYWRIGHT_BASE_URL=… npx playwright test` | **94 passed / 0 failed / 8 skipped** |
| 소크 census (실제 키, 99런) | `SOAK_RUNS=99 npm run soak` | **frozen 0/99** (Wilson 95% 0–3.74%) · completed 68 / failed 31 / **no_end 0** |
| story trace ×3 | `npm run story` | 비결정적이었음 → 시드 후 **2회 동일** |
| 밸런스 | `npm run survival -- --policies --seeds 32` | **100/98.2/76.7/51.2/26.0/13.5** · default 100/78.3/47.4/36.3/4.9/2.1 · gap +16.1pp |
| 직접 프로브 ×5 | Playwright (아래 `probe-*.txt`) | 게이트·BFS·BYPASS 동작 확인 |

## 찾은 것 (D1–D6)

| # | 결함 | 성격 | 처리 |
|---|---|---|---|
| D1 | e2e **22건 red** — `jockey_select`(ADR-0274)·`prep`(ADR-0283 C‴) 이후 스펙 미갱신. 4일간 방치(세션들은 soak/story 만 돌려 못 봄) | 테스트 | `menu-nav.ts` 헬퍼 2개 + 스펙 13개 → green |
| D2 | census 커버리지 — `MISSION_COUNT=53` 가정(실제 보드는 **33**)으로 60런 중복, 게다가 **정책이 미션에 고정** | 하네스 | 보드에서 미션 수 파생 · 정책 회전 분리 → **99셀** |
| D3 | 하네스가 **ADR-0290 봉인 보스**를 목표로 삼아 18/159 런이 320스텝 헛돎 | 하네스 | 봉인 해제 전까지 보스를 `business` 에서 제외 → **18 → 0** |
| D4 | 소크/story **비결정적**(게임은 `Math.random`, 헤드리스만 시드) + story 가 **추적 파일 5개를 덮어씀** | 하네스 | **셀 단위 시드** 주입 · story 출력 → `web/story-out/`(gitignored) |
| D5 | **게임 회귀** — `prep` 이 유휴 알람 화이트리스트에 없어 **유휴 TRACE 상승이 죽어 있었다** | 게임 | `main.ts` 화이트리스트에 `"prep"` |
| D6 | **게임 소프트락** — 유일 교전을 BYPASS 하면 **코어가 영구 봉인**(탈출은 JACK OUT) | 게임·설계 | **ADR-0308** (Jev Choice p=0.94 → clamp 에서 우회 노드 제외) |

## 파일

| 파일 | 무엇 |
|---|---|
| `soak-census-final.json` / `.log` | 최종 census(99런 = 33미션 × 3정책, per-cell 시드). `no_end_in_steps` 0 |
| `soak-census-before-harness-fix.json` / `.log` | 수정 **전** census(159런). 33미션만 돌았고 교착 18 · `no_end_in_steps` 18 |
| `soak-stall-trace.log` | 교착 셀의 스텝 추적(봉인된 코어에서 `sel` 왕복) |
| `e2e-before.log` | 수정 전 전체 e2e — 21 failed |
| `e2e-after.log` | 수정 후 전체 e2e — 94 passed / 0 failed |
| `survival-before.log` / `survival-after.log` | 밸런스 재현 (D6 수정 전/후 **byte-identical**) |
| `story-1.txt` · `story-2.txt` · `story-3.txt` | 시드 **없을 때** 같은 셀이 53/60/58 스텝으로 갈림 |
| `story-seeded-1.txt` · `story-seeded-2.txt` | 시드 후 — **동일** |
| `probe-bypass-after.txt` | D6 수정 후 프로브: 우회한 유일 교전 뒤 코어가 **열린다** |
| `jev-choice-d6.txt` | ADR-0308 후보 선정 Jev 판정 |

## D6 수정 전 재현 (인용)

수정 전 빌드에서 실브라우저로 잡은 기록(세션 트랜스크립트에서 인용 — ADR-0308 §컨텍스트 와 동일):

```
Mission: Flatline's Call | non-boss ICE: [9] | boss: [3]
at ICE node cur=9 msg="Travel blocked. BREACH: fight. BYPASS: 60 COST (once per run). JACK OUT: abandon run."
after BYPASS: msg="Bypassed — no reward. Routes are open: ↑↓ then ENTER." bypassed=[9] cleared=[]
at node cur=10 (boss=false)
ENTER toward boss -> cur=10 msg="Core sealed — 1 more ICE must fall (0/1)."     ← 이동하지 못함
FINAL cleared=[] bypassed=[9]
```

수정 후 같은 시나리오(`probe-bypass-after.txt`): `ENTER toward boss -> cur=3` — 코어가 열린다.

## 재현

```bash
cd web
npm run build
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test      # 94 passed / 0 failed / 8 skipped
SOAK_RUNS=99 npm run soak                                          # 99셀 · frozen 0 · no_end 0
npm run survival -- --policies --seeds 32                          # 밸런스 (기록치와 일치)
npm run story                                                      # web/story-out/ 에 기록
```

## 관련

- ADR **0308** (D6 수정) · ADR-0290 (게이트) · ADR-0265 (소크 하네스) · ADR-0283 (prep)
- `Game/wet_run/log.md` 2026-11-08 두 항목
- 커밋: `6a2decfd` · `b0cb42bf` · `8017e04d` · `980c2d10` · `10b0b5c7` · `e2a36fde` · `c99eb265` · `9034ebb7`

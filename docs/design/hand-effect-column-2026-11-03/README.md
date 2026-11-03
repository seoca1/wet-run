# 손패 효과 열 — 증거 (2026-11-03)

[ADR-0257](../../wiki/decisions/0257-hand-states-the-effect.md) 의 증거다.
표시 전용 — 밸런스·RNG·리듀서 무변경.

## 무엇을 바꿨나

ADR-0255 가 오프닝 5장에 실제 효과를 배선했지만, 손패 행은 여전히 COST 와 타겟만 보여줬다.
ADR-0254 가 거짓 예측 표기(`→ N/100`)를 걷어내며 남긴 빈 열에 **효과를 넣었다**.

```
                 이전                                    이후
1 BACKDOOR  COST +2          TARGET ICE      1 BACKDOOR  COST +2   PIERCE 2  TARGET ICE
2 BARRIER   COST +3          TARGET ICE      2 BARRIER   COST +3   SHIELD 2  TARGET ICE
3 BOOST     COST +2          TARGET ICE      3 BOOST     COST +2   ATK +2    TARGET ICE
4 CLOAK     COST +2          TARGET ICE      4 CLOAK     COST +2   EVADE 15% TARGET ICE
5 DECOY     COST +2          TARGET ICE      5 DECOY     COST +2   DECOY 50% TARGET ICE
```

## 캡처 — 3개 레이아웃 (실제 `AsciiRenderer`)

*before* = `HEAD` web/src(`git archive`), *after* = 작업 트리. 같은 픽스처·같은 리듀서.

| 80×50 | 60×40 | 40×60 |
|---|---|---|
| [pair](hand-80x50-pair.png) | [pair](hand-60x40-pair.png) | [pair](hand-40x60-pair.png) |

### 80×50 (after) — 실제 렌더 텍스트

```text
 ║ HAND                                                                       ║
 ║ 1 BACKDOOR  COST +2   PIERCE 2  TARGET ICE                                 ║
 ║ 2 BARRIER   COST +3   SHIELD 2  TARGET ICE                                 ║
 ║ 3 BOOST     COST +2   ATK +2    TARGET ICE                                 ║
 ║ 4 CLOAK     COST +2   EVADE 15%  TARGET ICE                                ║
 ║ 5 DECOY     COST +2   DECOY 50%  TARGET ICE                                ║
```

### 40×60 (after) — 좁은 행 + EFFECT 헤더

```text
 ║ HAND        COST EFFECT   TARGET   ║
 ║ 1 BACKDOOR  +2   PIERCE 2 ICE      ║
 ║ 2 BARRIER   +3   SHIELD 2 ICE      ║
 ║ 3 BOOST     +2   ATK +2   ICE      ║
 ║ 4 CLOAK     +2   EVADE 15% ICE     ║
 ║ 5 DECOY     +2   DECOY 50% ICE     ║
```

## 폭 검사 (`hand-*-width-check.json`)

| 레이아웃 | 텍스트 폭 | full/compact 최대 | 그리드 초과 | HUD 초과 |
|---|---|---|---|---|
| 80×50 | 75 | 46 (full) | 0 | 24 (기존) |
| 60×40 | 55 | 46 (full) | 0 | 24, 23 (기존) |
| 40×60 | 35 | 33 (compact) | 0 | 24, 23 (기존) |

HUD 초과는 `> [1] Yakuza Enf HP: 165`(24자)·`Mission: Aleph Fragment`(23자)로 **before/after 동일** —
ADR-0254 (c) 의 기존 결함이며 이번 범위 밖이다. **그리드(손패 행)는 초과 0.**

효과 태그를 ≤ 9자로 유지한 이유: 40×60 의 텍스트 폭이 35자라 가장 긴 `EVADE 15%`/`DECOY 50%`(9자)가
헤더 정렬을 깨지 않아야 한다.

## 검증

| 항목 | 결과 |
|---|---|
| `npx vitest run` | **179 files / 3960 tests passed** — [npm-test.txt](npm-test.txt) |
| `npx tsc --noEmit` | 0 errors — [typecheck.txt](typecheck.txt) |
| `npx eslint src` | 0 errors (기존 warning 1) — [lint.txt](lint.txt) |
| `npm run build` | PASS — [build.txt](build.txt) |
| `npm run balance` (opening) | 100.0 / 100.0 / 97.5 / 53.4 / 44.1 / 0.3 — **ADR-0256 기준선과 동일** — [balance-opening.txt](balance-opening.txt) |
| `npm run balance -- --deck ppl` | 100.0 / 100.0 / 99.3 / 84.1 / 44.4 / 27.3 — **동일** — [balance-ppl.txt](balance-ppl.txt) |

**밸런스 byte-identical** 확인 — 표시 전용 변경이므로 기대대로다.

## 채널 커버리지 (테스트가 고정)

| 채널 | 이전 | 이후 |
|---|---|---|
| 캔버스 행 (full) | 효과 없음 | `PIERCE 2` / `SHIELD 2` / `ATK +2` / `EVADE 15%` / `DECOY 50%` |
| 캔버스 행 (compact) | 효과 없음 | 같음 (EFFECT 열) |
| 터치 버튼 | 빈 줄 | `PIERCE 2` 등 |
| aria-label | `cost on the card` | `PIERCE 2` 등 |
| BLOCKED | `BLOCKED` (효과 자리) | 동일 — 거절된 카드는 효과를 주장하지 않는다 |

`web/tests/program_affordance.test.ts` · `web/tests/touch.test.ts` 가 네 채널 모두를 검증한다.

## 보류 (Oracle 권고)

- **select→confirm 모델** — ADR-0243 대체가 필요(별도 ADR). Oracle: "정보 계층을 먼저".
  이번 ADR 이 그 정보 계층이다.
- **TARGET FIRST** — `>` 마커 + `TARGET ICE` 로 현재 충분. 추가 이득이 작다.

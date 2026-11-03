# 죽음 화면 탈출 (2026-11-03)

[ADR-0263](../../wiki/decisions/0263-defeat-screen-must-be-escapable.md) 의 증거다.

## 무엇이 문제였나

오너 리포트: "플레이 한번 해봤는데, **보스 배틀 이후 빠져나오지 못한 버그**가 있어."

HP 가 0 이 되면 `FLATLINE` 화면이 뜨는데 **어떤 키도 먹지 않았다**:

- 리듀서(`applyDeathAction`)는 `trigger_death`(이미 지나간 죽음 자체)와 `select_restart` 만 처리했고,
  `confirm`·`jack_out`·방향키·숫자는 **상태를 바꾸지 않았다**.
- `select_restart` 는 `web/src` 전체에서 **한 번도 디스패치되지 않았다**(테스트/퍼저에만 존재).
- 화면에는 안내 문구조차 없었다 — 아트와 `FLATLINE` 뿐.

독립 headless 재현: `Enter`·`Escape`·`←↑↓→`·`1`·`4`·`Space`·`q` **8개 키 전부 무반응**.

## 바뀐 것

```text
(수정 전) FLATLINE + JACKED OUT 아트          (수정 후) 같은 화면 + 하단 한 줄
  ...                                          ...
                                               ENTER / ESC: return to title
  (아무 키도 반응 없음)                        → Enter 로 타이틀 복귀
```

- `applyDeathAction`: `confirm`/`jack_out` → `phase: "menu"` (런은 `runPhase: "dead"` 유지)
- `runFailed(previous, next)` — 엔딩의 `runCompleted` 와 **같은 모양**의 탈출 판정
- `main.ts`: `runFailed` 이면 `state = null; screen = "menu"` (엔딩과 동일 경로)
- `combat_grid.ts`: 죽음 화면에 `ENTER / ESC: return to title` (손패 자리 — 죽음 화면은 그 자리가 빈다)

## 이 폴더의 파일

| 파일 | 무엇 |
|---|---|
| `defeat-{80x50,60x40,40x60}-{before,after}.txt/png` | 죽음 화면 (before = HEAD, after = 수정 후) |
| `defeat-*-pair.png` | before/after 나란히 — **after 에만 안내 문구** |
| `defeat-*-after-width-check.json` | 폭 검사 — 그리드 초과 **0** |
| `live/ego-death-screen.png` | 실브라우저(독립 headless Chromium)에서 실제 전투로 사망한 화면 |

`after` 의 HUD 초과(line 7/9)는 `before` 와 **동일** — 기존 좁은 레이아웃 HUD 결함(ADR-0254 (c))이지
이 변경 때문이 아니다.

## 관련

- [ADR-0040 죽음/재시작 사이클](../../wiki/decisions/0040-death-restart-cycle.md) — 4선택 메뉴
  (`SAME JOCKEY`/`NEW JOCKEY`/`HALL OF DEAD`/`MAIN MENU`)는 여전히 미배선, 별도 슬라이스.
- [ADR-0252 런 종료/저장](../../wiki/decisions/0252-run-end-and-save-timing.md) — 죽음 프레임은 계속 저장.

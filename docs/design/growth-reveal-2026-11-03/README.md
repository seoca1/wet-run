# 성장을 사건으로 만든다 — 터미널 커밋 + 도착 인수인계 (2026-11-03)

[ADR-0262](../../wiki/decisions/0262-growth-reads-as-an-event.md) 의 증거다.
오너: "추천대로 구현해줘." 시안 원문은 [성장 연출 시안](../growth-direction-2026-11-03/README.md) (Manus 4안 + Jev 게이트).

## 무엇이 문제였나

ADR-0261 의 3박자(소리·멈춤·표시)는 정직했지만 **연출이 텍스트 색 변화가 전부**라
카드를 얻는 순간이 사건처럼 느껴지지 않았다. 게다가 구현 중 **매트릭스 화면은
`state.message` 를 렌더하지 않는다**는 결함을 발견했다 — ADR-0261 의 도착 메시지
(`Took Kraken. …`)가 loot 화면과 함께 사라졌다.

## 바뀐 것

```
① 커밋 (loot)                                ② 인수인계 (매트릭스 도착)
PROGRAM SLOT 01                              HUD:
> 1 VIRUS  [PIERCE 2]                          MATRIX
DATA LINK ............ OPEN                    Node 19/28
SIGNATURE ............ VIRUS                   + PROGRAM
DECK COMMIT ......... [##########] 100%          VIRUS
[+] PROGRAM ACQUIRED
HEAL applied → 100/100                       ENTER: continue
```

- **커밋 패널** — 단계 `[0, 90, 220, 320]ms` 로 자란다. 리듀서가 카드를 **이미 덱에 넣은 뒤**에만
  시작하므로 `100%` 는 참인 사실이다. 입력은 막지 않는다(ENTER 는 언제나 유효).
- **도착 노트** — 매트릭스 HUD 에 `+ PROGRAM` / `  VIRUS`. ~1200ms 창 후 자동 소멸.
- **reduced-motion** — 단계 연출은 사라지고 **최종 문구**만 남는다. 도착 노트는 생략된다.

## 이 폴더의 파일

| 파일 | 무엇 |
|---|---|
| `loot-commit-*.txt` / `-after.png` / `-pair.png` | loot 커밋 패널 (80×50 / 60×40 / 40×60) |
| `matrix-arrival-*` | 매트릭스 도착 노트 (HUD) |
| `*-width-check.json` | 그리드/HUD 초과 검사 — 신규 케이스 전부 **초과 0** |
| `capture-receipt.json` | 캡처 방법(실제 `AsciiRenderer`, 10×18 셀, before=HEAD) |
| `live/`, `live-rm/` | **실플레이** 스크린샷·로그 (preview 5195, 독립 headless Chromium) |
| `live/growth-reveal-live.gif` | **ego lite 브라우저에서 실제로 플레이한 화면**의 움직임 (제안 → 카드 획득 → 커밋 패널 정착 → ENTER → 도착 노트 → 소멸) |
| `live/ego-*.png` | 그 실플레이의 정지 프레임 (제안 / 커밋 패널 정착 / 매트릭스 도착 노트) |

`before` 는 HEAD(ADR-0261 시점), `after` 는 작업 트리다.
`live/` 는 기본 모드, `live-rm/` 은 reduced-motion 재실행이다.
`live/growth-reveal-live.gif` 와 `ego-*.png` 는 **ego lite(실제 브라우저)에서 키보드로 직접 플레이**해 얻었다 —
주사위 상태 조작 없이 실제 전투를 이겨 loot 화면에 도달했다.

# ADR-0315: 런은 캠페인이다 — 메뉴와 진행 구조 재설계

**상태**: Accepted (Q1–Q5 결정 · 슬라이스 1 구현 완료)
**날짜**: 2026-11-15
**결정자**: AI 위임 (오너 원칙: "나열과 무엇인지 감도 못 잡는 것을 선택해야 하는 상황을 없애거나 줄여서 선택해줘")
**우선순위**: P1 (구조 · 진행)

## 컨텍스트 (Context)

지금 런은 **미션 하나**다. `NEW RUN → 자키 → 미션 선택(53 평면) → prep → 미션 1개 → 엔딩 →
타이틀`. 그래서:

- `missionsCompleted` 가 **항상 1**(하드코딩)이고 `liberation` 엔딩(>=3)이 **도달 불가**다.
- 53 미션이 **5개 arc**에 있는데 arc 는 **진행 구조가 아니다** — 그냥 목록이다.
- 메뉴가 **평면 14항목**이다: 플레이 모드 6 · 시스템 4 · 설정/기록 4가 한 열에 섞여 있다.

설계 문서: [`docs/design/campaign-and-menu-2026-11-15.md`](../../design/campaign-and-menu-2026-11-15.md)

## 측정 (per-cell 32시드 · 최적 정책)

캠페인의 가정은 "덱이 자라 다음 미션으로 간다"다. 하네스에 **이월 덱**을 넣어 같은 미션·시드로
신규 vs 이월을 비교했다:

| 등급 | 신규 | 이월 | 차이 | 이월 덱 |
|---|---:|---:|---:|---:|
| 1 | 100.0% | 100.0% | +0.0pp | 5.9 |
| 2 | 96.5% | 97.3% | +0.8pp | 5.3 |
| 3 | 74.4% | 75.0% | +0.6pp | 5.0 |
| 4 | 50.6% | 48.8% | −1.9pp | 5.0 |
| 5 | 29.9% | 28.5% | −1.4pp | 5.9 |
| 6 | 31.3% | **63.5%** | **+32.3pp** | 5.7 |

1. **덱은 자라지 않는다** — 이월 덱이 5.0~5.9장. 최적 플레이가 전리품 칸을 **수리**에 쓰기
   때문이다(ADR-0305/0306). 캠페인의 성장은 덱이 아니라 **HP·크레딧·고유**에서 온다.
2. **g6 에서만 곡선이 깨진다** — **고유 카드**(ADR-0303/0311)가 이월되면 g6 의 장갑 관통 답이
   **상시**가 된다.

## Jev (advisory)

| 질문 | 결과 |
|---|---|
| 런의 형태 | **`campaign_is_the_default_run`** **p=0.76, conf 0.64** |
| 메뉴 모양 | 그룹화 질량 **0.97** · 최빈값 3그룹(0.43) · conf 0.24 (모양 미결정) |

## 고려한 옵션

### 메뉴 (Q1)
- **A — 3그룹**(PLAY · ARCHIVE · SETTINGS, Jev 0.43): 플레이 모드와 메타를 분리. CONTINUE 는
  최상단, CRAFT/EQUIPMENT 는 PLAY 안 WORKSHOP.
- **B — 모드 우선**(0.31): 최상단이 플레이 모드, 메타는 서브메뉴.
- **C — 5그룹**(0.23): PLAY · RECORDS · WORKSHOP · OPTIONS · CONTINUE.
- (기각) 평면 14 유지 — 0.03.

### 런의 형태 (Q2–Q4)
- **캠페인 기본**(채택 후보): `자키 → 계약(arc) → 미션 연쇄 → 엔딩`. `QUICK RUN` 은 단일 미션으로
  남긴다. 죽으면 캠페인 종료.
- 길이: 3미션 고정 · arc 전체(20/14/8/7/4) · 플레이어가 계속 선택 — **미결정**.
- HP 이월: 이월(회복 규칙 필요) vs 미션마다 리셋 — **미결정**.
- 이월 자원: 덱 ✅(측정상 중립) · 크레딧 ✅(ADR-0314 로 엔딩 조건) · COST ❌(미션 단위 예산) ·
  **고유 ⚠️ 캠페인당 1장**(현행 "런당 1장" = 캠페인당 1장).

## 슬라이스 1.5 결과 (점진적 노출 + 자키 화면 · 2026-11-15 구현)

오너 제안: "초반에는 선택형 메뉴가 없는 것처럼 진행하는 것도 가능하지 않을까? 저장/로드처럼
실제로 필요한 별도 기능이 있을 때 노출하는 방식으로."

- **첫 실행은 메뉴를 건너뛴다.** 프로필이 런을 한 번도 시작한 적이 없으면(`wetrun_has_played`
  없음) **부팅이 곧장 `jockey_select`** 로 간다. 메뉴는 ESC 한 번 거리에 있고, 첫 런을 시작한
  뒤부터 정상적으로 뜬다. 판정은 **동기**(localStorage) — 비동기 저장 캐시 갱신에서 결정하면
  첫 프레임에 메뉴가 번쩍이고 첫 키 입력과 경쟁한다(실제로 e2e 에서 그 레이스를 잡았다).
- **자키 화면이 자기설명적이 된다.** 이 화면은 첫 실행의 **첫 화면**인데 `1 CASE / 2 SIL /
  3 KAS` 만 보여줬다 — 자키는 **시작 덱을 바꾸는데**(ADR-0276) 화면이 그걸 말하지 않았다.
  이제 tagline 과 `deck: strike exploit virus surge decoy` 를 **줄바꿈해서** 보여준다.
  40열에서 단어 중간에 잘리던 것도 함께 고쳤다(`The deck`, `ice. Sh`).
- **죽은 코드 제거**: 쓰이지 않던 `jockeySelectFits`(rows >= 12)를 지웠다 — 새 레이아웃에서도
  거짓이었다.

### 이 과정에서 찾은 결함 2건

1. **폭 가드가 패널 클리핑을 감시하지 않았다** — `setInnerText` 가 `setText` 전에
   `clipToInner` 로 잘라 기록이 안 됐다(메뉴 부제가 40열에서 조용히 잘려 있었음).
   `recordClippedText` 로 봉합하고 메뉴·자키 화면을 가드 케이스에 추가.
2. **커서 정규화가 매 프레임 실행돼 커서가 갇혔다** — `normalizeMenuSelection` 이 잠긴 행
   (FAR GRID)에 닿을 때마다 되돌려 **1↔2 고착**. e2e 3건이 이걸 잡았다. 방문당 1회로 고쳤다.

## 슬라이스 1.6 결과 (메뉴가 플레이어와 함께 자란다 · 2026-11-15~16 구현)

오너 제안: "필요한 메뉴를 하나씩 노출시키는 방식은 어떨까?"

메뉴는 이제 **플레이어가 가진 것만** 보여준다.

| 항목 | 나타나는 시점 |
|---|---|
| NEW RUN · GRAPHIC NOVEL · SETTINGS · HELP · CREDITS | **항상** |
| CONTINUE | **세이브가 있을 때만** (없으면 죽은 행이었다) |
| FAR GRID | **해금됐을 때만** (ADR-0213) |
| TUTORIAL | **완료 전까지만** (끝나면 사라진다) |
| DUNGEON CRAWL · CRAFT · EQUIPMENT · HALL OF DEAD · ENDINGS · STATS | **런을 한 번 끝낸 뒤** |

- **첫 런 직후의 메뉴는 7항목**이다 — `CONTINUE · NEW RUN · GRAPHIC NOVEL · TUTORIAL` +
  `SETTINGS · HELP · CREDITS`. 나머지는 아직 열 것이 없다.
- **런을 끝내면 자란다.** `wetrun_runs_finished` 를 새로 저장하고(엔딩·플랫라인 둘 다),
  그 뒤로 archive/workshop 이 나타난다.
- **신호의 한계(정직하게)**: 죽음·엔딩·재료는 **저장되지 않는다**. 그래서 "HALL OF DEAD 는
  죽은 자키가 있을 때" 대신 **"런을 한 번 끝냈을 때"** 로 근사했다. 더 정밀하게 하려면
  그 신호들을 먼저 저장해야 한다(열린 질문 (g)).
- 구현: `visibleMenuOptions(reveal)` 이 목록을 만들고, **렌더·입력·`getMenuOptionKeys`·
  커서 정규화가 모두 같은 목록**을 쓴다. 그룹 헤더는 보이는 항목이 있는 그룹만 나온다.
- 테스트 **211 files / 4215 tests** · e2e **24/24**.

## 사용자 결정 (Decision)

**원칙(오너)**: "나열과 무엇인지 감도 못 잡는 것을 선택해야 하는 상황을 없애거나 줄인다."
아래 선택은 전부 이 원칙에서 나왔다.

- [x] **Q1 — 한 화면 + 그룹 헤더 + 항목마다 한 줄 설명** (PLAY · WORKSHOP · ARCHIVE · SYSTEM).
  하위 화면을 만들지 않는다 — 화면 등록 누락은 이 프로젝트의 소프트락 원인 3건이다
  (ADR-0273/0275/0283). 14개를 그냥 나열하면 `CRAFT`·`STATS`가 뭔지 알 수 없다.
  **설명을 붙이면 목록이 아니라 선택지**가 된다.
- [x] **Q2 — 길이를 플레이어가 고르지 않는다.** "3미션? arc 전체?" 자체가 감 못 잡는 선택이다.
  **계약(contract)을 계속 받으면 캠페인**, 그만두면 끝난다.
- [x] **Q3 — HP는 미션마다 리셋**(현행 prep 유지). 이월/리셋을 고르게 하면 **이해할 규칙이
  하나 더** 생긴다. 새 규칙 0.
- [x] **Q4 — QUICK RUN 모드 없음.** 모드 2개를 고르게 하면 "뭐가 다른데?"가 생긴다.
  **계약 하나만 받고 끝내면 그게 quick run**이다 — 모드 열거 자체를 없앤다.
- [x] **Q5 — 메뉴부터** (밸런스 무영향 · 화면 1개).

**핵심**: `CAMPAIGN vs QUICK RUN` 이라는 **모드 열거를 없앴다.** 단위는 **계약** 하나이고,
계속 받으면 캠페인이 된다.

## 슬라이스 1 결과 (메뉴 · 2026-11-15 구현)

```
PLAY                       WORKSHOP          ARCHIVE               SYSTEM
  ▸ [1] CONTINUE  resume run   [7] CRAFT  spend parts   [9] HALL OF DEAD  the fallen   [12] SETTINGS  audio, keys
    [2] NEW RUN   start a run  [8] EQUIPMENT fit deck   [10] ENDINGS     your ending  [13] HELP      how to play
    [3] FAR GRID  orbit grid                            [11] STATS       your stats   [14] CREDITS   who made it
    [4] DUNGEON CRAWL side crawl
    [5] GRAPHIC NOVEL the story
    [6] TUTORIAL  first steps
```

- **40열에서 0건 잘림**(부제·footer 포함). 그 과정에서 **ADR-0300 폭 가드가 패널 클리핑을
  감시하지 않던 구멍**을 찾았다 — `setInnerText` 가 `setText` 전에 잘라 기록되지 않았다.
  `recordClippedText` 로 봉합하고 **메뉴를 가드 케이스에 추가**(3 레이아웃).
- **커서가 죽은 행에 앉지 않는다**: 세이브가 없으면 첫 항목 `CONTINUE` 대신 첫 사용 가능
  항목으로 이동(`normalizeMenuSelection`).
- 부제·footer 단축(40열 적합), 설명 11자 이하. 밸런스 무영향. **209 files / 4200 tests**.

## 추천 (Recommendation)

1. ~~메뉴 A안~~ → **채택·구현**(위 슬라이스 1).
2. **캠페인 기본, 모드 열거 없음** — Jev p=0.76 이되 QUICK RUN 을 모드로 만들지 않는다(Q4).
3. 다음 슬라이스는 **캠페인 골격**(`missionsCompleted` 카운트 + 미션 연쇄 + `liberation` 개방).

## 열린 질문

- **(a) 계약 하나의 길이.** 3미션이면 `liberation`(>=3)이 정확히 열린다. arc 전체는 g1 20미션.
  Q2 로 "플레이어가 길이를 고르지 않는다"를 정했으므로, **계약의 미션 수를 우리가 정한다**.
- **(b) 캠페인 사이 HP.** Q3 로 미션마다 리셋. 미션 사이 회복은 전리품(prep)이 담당한다.
- **(c) g6 고유 누적.** 캠페인 후반 g6 는 +32.3pp. 캠페인 기준 목표를 새로 잡거나 고유 규칙을
  조정해야 한다.
- **(d) 캠페인 지표.** 현행 하네스는 **미션 단위**다. "N미션 생존율"이 없으면 캠페인 밸런스를
  검증할 수 없다 — 슬라이스 4.
- **(e) 저장 스키마.** 계약·미션 인덱스·이월 자원을 `version 1` 선택 필드로(ADR-0287/0311 관례).
- **(f) 프롤로그 연결.** ADR-0272/0274 의 "프롤로그 → 자키 → 런 → 엔딩" 흐름이 캠페인과 만난다.
- **(g) 노출 신호의 정밀도.** 지금 archive/workshop 은 "런을 한 번 끝냄"으로 열린다. 진짜
  조건은 "죽은 자키가 있음"(HALL OF DEAD)·"도달한 엔딩이 있음"(ENDINGS)·"재료가 있음"(CRAFT)
  인데 **그 신호들이 저장되지 않는다.** 정밀하게 하려면 먼저 저장해야 한다.

## Implementation Status (2026-11-15)

**Status**: 🟡 Partial (슬라이스 1·1.5·1.6 ✅ · 슬라이스 2–4 ❌ Not started)

**Evidence**:
- `web/src/renderer/menu_main.ts` — 그룹·설명·**`visibleMenuOptions`(노출 규칙)**
- `web/src/renderer/jockey_select.ts` — tagline·deck 줄바꿈
- `web/src/core/state/onboarding.ts` — `wetrun_has_played` · **`wetrun_runs_finished`**
- `web/src/main.ts` — 동기 부팅 판정 · `visibleMenu()` · `noteRunFinished`
- `web/src/core/grid.ts` · `web/src/renderer/panel.ts` — `recordClippedText`(폭 가드 봉합)
- `web/e2e/menu-nav.ts` — `ensureMenu`(부팅 경로를 스펙에서 숨긴다)
- `web/tests/adr0300_no_text_is_cut_off.test.ts` — 메뉴·자키 3 레이아웃 가드
- `docs/design/campaign-and-menu-2026-11-15.md` — 설계 전문
- 측정: 하네스의 **이월 덱 파라미터**(슬라이스 4 의 캠페인 지표 도구)

**Notes**: 이 ADR 은 ADR-0199("단일 미션 런 MVP")의 범위를 넓힌다. 슬라이스 1 은 밸런스
무영향. 슬라이스 2 부터는 저장 스키마와 밸런스 기준선에 닿는다.

## 관련 결정

- ADR-0199 — 웹 MVP(단일 미션 런) — 이 ADR 이 범위를 넓힌다
- ADR-0270 · ADR-0271 — 도달 불가 분기 문서화(`missionsCompleted>=3` 포함)
- ADR-0213 — Far Grid(별도 유니버스)
- ADR-0272 · ADR-0274 — 인트로/자키(캠페인 흐름의 재료)
- ADR-0303 · ADR-0311 — 고유 카드(캠페인에서 누적되는 유일한 카드)
- ADR-0314 — 크레딧이 엔딩 조건(이월해야 누적 의미)

## 변경 이력

- 2026-11-15: Draft 작성 — 구조 실측 + 이월 측정 + Jev 2회

## Implementation Status (2026-11-17)

**Status**: 🟡 Partial (슬라이스 1 구현 · 노출 규칙 일부는 ADR-0317 이 대체)

**Evidence**:
- `web/src/renderer/menu_main.ts` — `MENU_OPTIONS` · `visibleMenuOptions`(노출 규칙)
- `web/src/core/state/onboarding.ts` — `wetrun_runs_finished` · `wetrun_has_played`
- `web/tests/adr0315_menu_reveal.test.ts` — 노출 규칙
- `web/tests/menu_layout.test.ts` · `web/tests/menu.test.ts` — 그룹 순서와 항목 수

**Notes**: **노출 규칙 표에서 `GRAPHIC NOVEL` 이 빠졌다** — ADR-0317 4단계(2026-11-17)가 그래픽
노블을 **런의 프롤로그**로 녹이고 메뉴 항목을 삭제했기 때문이다(그 결정이 "ADR-0315 의 노출 규칙에서도
빠진다"고 명시했다). 그래서 **첫 런 직후 메뉴는 7항목이 아니라 6항목**이다
(`CONTINUE · NEW RUN · TUTORIAL · SETTINGS · HELP · CREDITS`). 위 표는 결정 당시의 기록으로 남긴다.

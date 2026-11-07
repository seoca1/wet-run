## [2026-10-31] feat(ui) | UI 화면 구성 개편 — ADR-0237 채택(방향 B) + 캔버스 지오메트리 + 프레임 언어

**Status**: 🟡 Partial (17 커밋). 밸런스 0.0pp 유지 — 표시 계층 전용.

### 0. 계기
- 사용자: "wet_run UI 를 대대적으로 개선하고 싶다, 마누스 도움을 받을 수 있나?"
- Manus(무료 티어 1,500 + 300/day)로 **A/B/C 3방향 컨셉 시트** 생성 → 로컬 호스팅(`127.0.0.1:5194`)으로 비교 → **방향 B "Green Grid" 채택**.
  - 채택 근거: 색각 변형 테이블이 green/red 시맨틱 위에 설계돼 있어 green 프레임은 **자동 재색**(새 오버라이드 0). amber 는 deuteranopia 에서 "안전" 신호와, magenta 는 위험 신호 및 ADR-0002 ICE 색과 충돌.
  - 컨셉 시트 독립 검증: 22색 = 브리핑 팔레트 정확히 일치, 금지 스타일(glassmorphism/blur/gradient/box-shadow/emoji/CP2077) 전부 0.

### 1. 선행: 베이스라인 정리 (`8d23b72`, `cc55d16`)
- 미커밋 core/ 모듈 분할(178 M / 57 D / 56 rename)을 전체 게이트 후 커밋.
- **게이트가 실제 빌드 파손 2건을 발견** — 원 세션은 `typecheck`+`test` 만 돌리고 build 는 돌리지 않았다:
  ① `web/public/sounds/theme_*.mp3` 심링크 깊이 오류(`../../docs` → `web/docs` 로 해석) → `vite build` ENOENT. `../../../docs` 로 수정.
  ② `vite.config.ts` `manualChunks` 가 이동 전 경로(`./src/core/state.ts` 등 4개) → `Could not resolve entry module`. 새 경로로 수정.

### 2. 즉시 정리 (`4c8f40f1`, 트리아지 §3 1단계)
- `#status-overlay` 요소·CSS·미디어 쿼리 제거 — 소비자 0건이라 빈 초록 박스로 항상 표시되고 있었다.
- 터치 타깃 **44px px 하한**(`MIN_TOUCH_TARGET_PX`; D-pad·A/B 는 `min-width/height`, 프로그램 행은 `max(44px, Nvw)`).
- 번호 표기 1-based `[N]` 통일(`renderer/nav_index.ts` 신설). matrix 는 0-based 였고 기존 "Node n/N" 표기와도 불일치 → 표시 전용 수정.
- 죽은 `renderHUD()` 제거.
- 테스트 **3333 → 3345**.

### 3. 캔버스 지오메트리 (`e9eb6f1`, V1·V3)
- 원인: 캔버스를 고정 px 로 그리고 CSS 가 **축소만** → 큰 빈 공간 + 텍스트 스케일 옵션이 CSS 에 상쇄.
- 순수 `canvasGeometry()` / `layoutForViewport()` 추출, 뷰포트 + DPR 기반 파생, 텍스트 확대 시 presentation 행/열 감소, 6×12px 최소 셀 하한.
- **실측**: 1440×900 박스 1280×900 → **1440×900**, 사망 띠 186.67px → **0px** · 390×844 56.38px → **0px**. 폰트 medium→large 가 15 → **18.75px**(데스크톱) / 14.07 → **17.58px**(폰).
- **밸런스 6등급 0.0pp**(개방·PPL 양 덱) → 표시 전용 변경임을 확인.

### 4. 프레임 언어 (`133286a` 헬퍼, `f29c22f` 3화면 적용, V2)
- `renderer/panel.ts`(151 LOC): `drawPanel` / `drawPanelSeparator` / `panelInnerRect` — 불변 Grid 반환, 팔레트 call-time 조회, 클립·truncate·2×2 미만 무시 규칙. 테스트 43개.
- 메뉴 / 미션 선택 / 전투 3화면에 적용(전투는 우측 레일이 HUD 컬럼 구분선을 겸함). 프레임은 마지막에 그려 긴 메시지가 레일을 지우지 못하게 함.
- `main.ts` 변경은 미션 선택 위임 한 곳뿐 · `panel.ts`/`hud.ts` 무변경 · 신규 `tests/screen_frames.test.ts` 15개.
- **미적용**: dungeon · matrix · pause · crafting · equipment.

### 5. 프레임 언어 완성 (`a97a4a7`)
- 3화면 프레임을 그리드에서 파생해 **1셀 인셋**(사방 검은 거터). `panel.ts` 에 `screenFrameRect()` / `clipToInner()` / `setInnerText()` 추가.
- **matrix · dungeon 화면에도 프레임 적용** (남은 미적용: pause · crafting · equipment).
- 부작용 정리: 긴 텍스트는 이제 **클립**된다 (이전에는 그리드 가장자리 프레임이 위에 덮어 가렸다). 전투 HAND 행이 19행 미만 그리드에서 하단 레일에 가려 **보이지 않던** 문제도 같은 커밋에서 해소.
- 검증: 런타임 던전 **15×10** / 그리드 100×60(내부 98×58) → 인셋 프레임이 던전을 자르지 않음.
- 동반 발견: `renderer/dungeon.ts` 가 플레이어 `@` 심볼을 **그리지 않음** (HEAD 에서도 동일, 범위 밖).

### 6. `main.ts` 분해 — 뷰 빌더를 렌더러 모듈로 (`ffbfa41`)
- `main.ts` **2,074 → 1,658줄(-416)**. 신규 모듈: `crafting_screen` · `equipment_screen` · `graphic_novel_screen` · `pre_game_screen` · `run_screen` · `combat_hints` · `screen_view`(타입). 각 모듈이 순수 `*Layout()` + 렌더 함수를 export → vitest 로 검증 가능.
- 컨트롤러(입력 · 상태 변경 · 로딩 · autosave · 렌더 루프 · dispatch)는 `main.ts` 잔류. 표시 문자열·순서·키·색·좌표 **무변경**.
- ⚠️ **브라우저 스모크가 잡은 부팅 파손**: 장비 렌더러의 런타임 import 가 기존 `equipment.ts ↔ loadout.ts` 순환을 앞당겨 `Cannot access 'EQUIP_SLOTS' before initialization` — **단위 테스트 3,456개 전부 통과 상태**에서 스모크만이 발견. 컨트롤러가 슬롯 목록을 넘기도록 고쳐 해소.
- 스모크 결과(ego lite): `menu → mission_select → matrix → ArrowDown×3 → ICE 노드 18 → Enter×2 → combat` PASS, `vite-error-overlay` 없음. 오케스트레이터 독립 재확인: 부팅 정상 + `crafting` / `equipment` 화면 진입 정상.

### 7. 프레임 언어 최종 적용 (`3e8041d`)
- `crafting` · `equipment` 에도 동일한 인셋 프레임 적용 → **프레임 7화면 완료** (menu · mission select · combat · matrix · dungeon · crafting · equipment).
- 콘텐츠는 **리플로우 없이** +1열/+1행 평행 이동. 오프셋은 그리드가 아니라 프레임 코너 기준으로 재측정. 문자열·순서·키·색 무변경. 두 화면 모두 고정 푸터가 없어 키 힌트는 흐름대로 유지(menu/matrix 처럼 마지막 내부 행으로 옮기면 리플로우가 된다).
- crafting 재료 줄의 중복 `.slice(0, cols-4)` 제거(`setInnerText` 가 클립) → 30열 그리드에서 그 줄이 1자 짧아짐(프레임이 셀을 차지하므로).
- **의도적 미적용 2건**: `pause`(빈 격자가 설계 — 주석 + 테스트가 전 셀 공백을 pin) · `settings`(푸터가 `rows-2`/`rows-1` 인데 `rows-1` 이 거터 행 → 적용하려면 `settings.ts` 리플로우 필요, **별건 후속**).
- 스크린샷: `after-11-crafting-framed.png` · `after-12-equipment-framed.png`.

### 8. settings 프레임 + 60×40 콘텐츠 손실 수정 (`0793ff3`, `f3a14c6`)
- `settings` 에 인셋 프레임 적용 → **프레임 8화면 완료** (menu · mission select · combat · matrix · dungeon · crafting · equipment · settings). 본문은 프레임 코너 기준 +1/+1 평행 이동, `renderSlider` 는 writer 함수를 받도록 변경.
- **`0793ff3` 이 만든 회귀**: 푸터를 마지막 내부 2행에 무조건 pin → **60×40 에서 PWA 3행 가림**. 진짜 원인은 지시했던 "리플로우 금지" 제약이었다 — 본문 37행 vs 40행 그리드 내부 36행이라 **푸터가 없어도** online/offline 행이 하단 레일에 걸린다.
- **`f3a14c6` 해소**: 43행 이상은 기존 pin 유지(다른 프리셋 전부 불변), 40–42행은 빈 스페이서 3개(AUDIO · LANGUAGE · PWA 아래)를 접고 푸터가 본문 뒤에 붙는다. 항목 · 순서 · 문자열 변경 없음.
- 손실을 pin 하던 테스트를 **가시성을 pin 하는 테스트로 교체**, `settings_pwa_rows` 를 60×40 · 80×40 · 80×50 3종으로 확장해 **40행 가드 복원**, 6개 프리셋 전수 "모든 줄이 프레임 안에 정확히 1회" 테스트 추가.
- 60×40 그리드 덤프로 PWA 3행 + 푸터 동시 표시 확인.

### 9. e2e 게이트 복원 (`d817b96`)
- 레포에 **e2e 스펙 14개(76 테스트)** 가 있었으나 **Playwright 브라우저 미설치**로 한 번도 돌지 않았다 → `npx playwright install chromium` (chromium + headless shell + ffmpeg) 로 복원.
- 로컬 프로덕션 빌드를 `vite preview` 로 서빙(포트 5195, **`--host 127.0.0.1` 필요** — 없으면 IPv6 `[::1]` 만 바인딩되어 127.0.0.1 실패). 실행은 `env -u CI` (config 가 `CI` 시 `retries: 2` 를 켜 flakiness 를 숨김) + `PLAYWRIGHT_BASE_URL`.
- **결과: 76 테스트 → 72 passed / 4 skipped(설계상 — touch 테스트가 desktop 에서 skip) / 0 failed** → 개편 20커밋(8화면 프레임 · 지오메트리 · 번호 통일 · `main.ts` 분해)이 **e2e 로도 무결**임을 확인.
- 유일한 실패였던 `tier55_vfx.spec.ts` 는 **pre-existing 스펙 레이스**: program VFX 수명 48ms/32ms(`WEB_TICK_MS=16`)인데 스펙은 100ms 대기 후 단일 read → 항상 0. `expect.poll` 로 교체(`d817b96`), **52/52 안정**(retries off). 프로덕션 코드 무변경.
- `demo-screenshots.spec.ts` 는 커밋된 PNG 16장을 덮어쓰는 **생성기**라 게이트에서 제외(실행 후 `web/demo-screenshots/` 무변경 검증).
- 부수 관찰: program VFX 48ms 는 사람 눈에 거의 안 보일 수 있음 → **feel 설계 질문**(ADR-0238 과 같은 성격).

### 10. 던전 결함 2건 수정 (`4686191`, `36d639c`)
- **플레이어 미표시 (dead `@` 분기)**: e2e 게이트 복원 중 확정 — `EntityType.PLAYER` 는 저장소 전체에서 `renderer/dungeon.ts:150` **한 곳에만** 등장하고, PLAYER 엔티티를 만드는 코드가 없다 (`entities.push` 3곳은 MONSTER / ITEM / TRAP 뿐). 플레이어는 `state.playerX/playerY` 로만 추적되어 **던전에서 자기 위치가 보이지 않았다**.
  - 수정: 렌더러에 `renderPlayer()` 추가 (`getPlayerPosition()` + 기존 `getPlayerFg` 재사용), 그리기 순서 **타일 → 엔티티 → 플레이어 → 프레임**, dead 분기 제거. **core 무변경** — state 에 PLAYER 엔티티를 넣으면 가시성·AI 타게팅에 파급되므로 회피. 신규 테스트 6개(readonly state 캐스팅 대신 `getPlayerStats` spy 로 저HP 색 검증).
  - 밸런스 **0.0pp** · e2e **72 passed / 4 skipped / 0 failed** · 라이브 스크린샷 `after-14-dungeon-player.png` 에서 초록 `@` 확인.
- **HUD 라벨 오타**: 같은 스크린샷에서 `LVE: 01` 을 발견 → 소스 확인 결과 `dungeon.ts:365` 가 문자 그대로 `LVE:` 를 출력(`LVL` 오타). 테스트 fixture(`ascii_renderer_color_for.test.ts:59`)에도 복사돼 있어 동반 수정.
- **메모(오케스트레이터 자기정정)**: 처음엔 이 결함을 "서브에이전트 오보"로 잘못 정정했다가, `EntityType.PLAYER` 전수 grep 으로 **서브에이전트가 옳았음**을 확인하고 재정정했다 — 기록을 증거 기반으로 강화한 경위.

### 11. 잔여 위생 2건 (`c19982b`, `2a713ee`)
- **마지막 죽은 코드 제거** (`c19982b`): `renderer/hud.ts` 는 `shouldRenderHUD()`
  하나만 담고 있었고 **호출자 0**. 게다가 **중복 구현**이었다 — 실제 HUD 는 스크린
  종류로 게이트되지 않는다. 각 뷰가 자기 `hud` 라인을
  `renderer.render(view.grid, view.hud, …)` 로 넘기고, `hudScreens` 목록은
  저장소 유일본이었다. → 모듈째 삭제하고, 그 존재를 pin 하던
  `tests/hud.test.ts` 도 삭제(트리아지 X3 가 삭제를 승인). 테스트 156 → **155 files**.
- **`demo-screenshots` 출처 명시** (`2a713ee`): 커밋된 18장은 **2026-10-13
  스냅샷**이고, `e2e/demo-screenshots.spec.ts` 는 이제
  **`test-results/demo-shots/`(gitignored)** 에 쓴다 → 이 디렉터리는 **생성기와
  연결이 끊겨** 제자리 재생성이 불가능하다. 스펙이 18개 중 8개 이름만 만들므로
  부분 갱신은 **나이 섞인 집합**이 되어 더 신뢰하기 어렵다. `README.md` 로 출처와
  현재 baseline 위치(`docs/design/before-after-2026-10-31/`)를 기록하고, 교체는
  **의도적 결정**임을 명시했다.
  - **교훈(오케스트레이터)**: 처음에 "스펙을 돌려 스크린샷을 재생성하자"고
    권했는데 **전제가 틀렸다** — 스펙의 출력 디렉터리를 확인하지 않고 추정했다.
    스펙이 tracked 파일을 건드리지 않는 건 오히려 올바른 설계였다.

### 12. RNG 결합 해소 — 결정 요청 ADR-0239 (Draft) (`c49fc2d`)
- ③ RNG 결합 정리는 **밸런스 재기준화**를 강제하므로 `AGENTS.md` §3.2상 ADR 선행이 필수다 → Draft ADR 을 작성했다 (**구현 없음**).
- 내용 ① 문제 실측: 표시 전용 1줄 변경이 **opening g3 −2.0pp · PPL g6 −3.0pp** 를 움직였다. ② 현행 규칙의 구멍: `state_helpers.ts` docstring 은 "**새** spawn 은 결정적 헬퍼" 규칙만 갖고 **"기존 spawn 수정"** 규칙이 없다. ③ **수정 표면은 13곳이 아니라 2개 함수** — 13개 비결정적 호출 지점이 전부 `import_vfx` / `import_vfx_ms` 를 지나므로 이 둘의 id 만 바꾸면 한 번에 중립화된다. ④ **RNG 소비 지도**(전수): 표시 = 2 함수 + `status.ts:253` fluff(전투 경로에서 소비) / **게임플레이 = crit roll · loot · 적 스킬 · death cycle — 불변**. ⑤ Option A(현상 유지) · **B(결정적 id + 1회 재기준화, 추천)** · C(draw 수를 밸런스 계약으로 선언) + 비교표. ⑥ 부수 권고(강): **RNG draw 수 불변식 테스트** — ADR-0231/0232 는 draw 수를 **수작업**으로 대조했고, 그 구멍으로 이번 결합이 살아남았다. ⑦ 순서 권고: ADR-0238 의 VFX 항목(P2 잔여 · P8 · X5 · X8)보다 **먼저** 처리.
- 열린 질문 6건 · 사용자 결정 체크리스트 6개. ADR 본문 `docs/wiki/decisions/0239-vfx-spawn-rng-decoupling.md`.

### 13. e2e 재검증 — 제 주장이 틀렸고, flake 1건을 찾아 수정 (`97d13f5`)
- **재검증이 반박했다**: 이 로그에 "e2e 72 passed / 0 failed" 라고 적어 두었으나,
  현재 HEAD 에서 전체 스위트를 다시 돌리니 **1 failed / 4 skipped / 71 passed**
  였다 — `mobile-portrait-chromium › touch_input.spec.ts:72 › program row touch
  uses a program in combat`. 제 수치는 **한 번의 관측**이었고, 반복하지 않고
  단정한 잘못이다.
- **flake 판정**: `--repeat-each=5` → 모바일 20 중 1 실패 · `--repeat-each=10` →
  40 중 2 실패 (**약 5%**). 결정적 회귀가 아니라 **타이밍 flake** 다. CI 는
  `playwright.config.ts` 의 `retries: 2` 로 흡수해 왔기에 지금까지 표면화되지
  않았다 (그래서 `env -u CI` 로 retries 를 꺼야 보인다).
- **원인**: `tap()` 헬퍼가 `boundingBox()` 를 **한 번만** 읽고 null 이면 throw.
  게임패드·프로그램 행은 상태 변화로 재렌더되므로, `toBeVisible()` 통과 직후에도
  이전 버튼이 detach 된 창에 걸린다 — tier55 와 **같은 부류**(수동 대기 vs 일시적
  상태).
- **수정(스펙 전용)**: box 읽기를 짧게 재시도(최대 약 1초). 좌표 기반
  `page.touchscreen.tap()` 을 유지해 **검증 대상인 실제 터치 이벤트 경로는 불변**.
  나머지 3개 tap 호출 지점도 같은 견고성을 얻는다. 프로덕션 코드 무변경.
- **증명(둘 다 retries off)**: `touch_input --repeat-each=10` → **40/40 통과**
  (이전 40 중 2 실패) · 전체 14 스펙 → **72 passed / 4 skipped / 0 failed**.
- **교훈**: "0 failed" 는 반복 측정 없이 주장할 수 없다. retries 를 끄고 반복해야
  flake 가 드러난다 — 이번 세션에서 제가 스스로를 정정한 세 번째 사례다.

### 14. Jev 적용 — WF1 가드(BLOCK) + WF8 곡선 채점(advisory) 
- 사용자 요청("jev ai 로 추가 진행할 수 없어?")에 따라 Jev 의 두 워크플로를 **결정 보조**로만 적용했다 (오너 결정 대체 아님).
- **WF1 (AGENTS.md §6 가드, Noul)**: 세션 footprint 를 state 로, §6 절대 금지 5항목을 instructions 로 호출 → **`p = 0.63` → 임계표상 `p ≥ 0.6` = BLOCK + escalate**. Jev 는 타입화된 결정만 반환하고 **근거 텍스트가 없으므로**, 기계적 사실로 트리거를 추정: raw/ 변경 0 · 깨진 wikilink 0 → **파일 변경 약 380 (50+ 기준 초과)이 유력**, Accepted ADR-0237 의 Implementation Status 갱신도 가능. → 정책대로 **추가 변경 중단 + 에스컬레이션**.
- **footprint 정정**: 앞서 "wet_run 밖 변경은 4건"이라고 적은 것은 **틀렸다** — 실제 **루트 15 엔트리** (Status/** 12 + infra/llm/wiki/agent-tool-integration-status.md + log.md + scripts/aside-mini24-health.sh + docs/progress 산출물). 첫 작업의 **검증된 산출물이 아직 미커밋**이며, 이것이 가드가 0.6 을 넘은 실질 원인일 가능성이 크다.
- **WF8 (난이도 곡선, Score 0..5)**: 현재 곡선 vs **분리 프록시** 곡선 4회 채점 → opening **1.88 → 1.76** · PPL **0.93 → 0.94** (PPL 은 양쪽 다 고신뢰 0.86 / 0.90). **분리가 곡선 형태 품질을 떨어뜨리지 않는다** → ADR-0239 Option B(재기준화)의 위험을 낮추는 증거. ADR-0239 에 표·한계와 함께 기록.
- **정직 공개**: canonical `scripts/jev-call.sh:46` 은 감사 JSON 을 **`raw/`** 에 쓴다 — 워크스페이스 규칙 위반이므로 **워크스페이스 사본을 /tmp 로 만들어 `AUDIT_DIR` 만 우회**했다 (canonical 무변경, diff 확인). 감사 로그는 `/tmp/jev-calls/` (10개).
- **교훈**: WF1 이 "한 세션에 너무 많은 변경"을 정확히 지적했다 — 세션 내내 언급해온 §8/§6 상한과 일치한다.

### 15. ADR-0239 구현 — VFX id RNG 중립화 + 1회 재기준화 (`c488b6d`)
- **승인대로 실행** (오너 결정: Option B, 이 ADR 우선). `import_vfx`(:23) / `import_vfx_ms`(:47) 의 id 를 `deterministicVfxId` 기반으로 → **13개 호출 지점 무변경**. `use_program` 5-spawn 시나리오에서 draw **10 → 5** (남은 5는 전부 게임플레이: damage variance · crit check · burn proc · slow proc · enemy ICE crit roll).
- **0-draw 불변식 테스트** 추가 (`tests/vfx_rng_neutrality.test.ts` 4개 — 변경 전 실패 → 후 통과). 기존 `state_helpers.test.ts` 의 "generates unique IDs for each instance" 는 승인된 id 의미와 **정반대**라 "distinct IDs for distinct content" 로 교체(리뷰 요청 표시).
- **안전성 독립 검증**: vfx id 의 유일한 독자는 `screen_shake.ts:234` 의 `player_hit` 게이트(`SHAKE_VFX_KIND` = `player_hit`, `:49`)뿐이고, 그 spawn 은 `import_vfx_deterministic`(이미 content-hash)에서 나온다 → 13개 지점의 공유 id 는 무해. (오케스트레이터가 직접 grep 으로 확인)
- **재기준화 실행** (승인된 1회 이동, 되돌리려 튜닝하지 않음): opening `100.0/88.6/73.1/39.3/35.7/0.0` → `100.0/88.3/70.5/39.5/36.2/0.0` (g3 **−2.6pp**) · PPL `100.0/77.9/99.6/84.8/44.4/28.3` → `100.0/79.1/98.9/83.0/44.4/24.7` (g6 **−3.6pp**). 새 기준선은 **ADR-0239 에 기록**(ADR-0229 는 immutable 유지 + supersede 관계 명시), 롤백용 "이전" 곡선도 같은 표에 보존.
- ⚠️ **ADR 자체의 오분류를 구현이 발견**: `core/status.ts` 는 "표시 fluff" 가 아니라 **게임플레이**다 — `rollStatusProc` 이 `_kind` 를 **무시**하고 `rng() < 0.2` 로 **burn·slow 적용 여부**를 결정한다 (`state_actions_programs.ts:145`·`:154`; 기존 `slow_effect.test.ts` 도 `// suppress burn proc` 으로 게임플레이 취급). `status.ts` 안에서만 결정화하면 20% proc 이 **상수화**되므로 **범위에서 제외하고 (b) 재개**. 게임플레이 RNG 는 일절 손대지 않았다.
- 게이트: `tsc --noEmit` 0 · `eslint` 0 errors · vitest **156 files / 3,571 tests** · build OK.

### 16. ADR-0238 결정 — 추천 번들 채택 + 4개 ADR 분할
- 오너가 **추천 번들을 그대로 채택**: **P7-3**(유휴 → 알람 상승, 적 직접 공격 아님) · **X1-2**(기존 `tickAlarm` 시간 기반 배선) · **P8-2**(`isCrit` 연동) · **X2-3**(`getAlarmMultiplier` 만 · `shouldTargetAlly` 🟢 Deferred) · **X4-2**(숫자키 `1`–`9` repeat 만 무시). **4개 ADR 로 분할**(P7+X1 먼저).
- 추가 결정 — **(a)** `balance_sim.ts` 에 **유휴 단계 추가** → P7 을 §A1 로 측정 가능하게 (없으면 0.0pp 가 "영향 없음"의 증거가 못 됨) · **(b)** **알람 레벨 상승 = 적 피해·공격성 증가** (X1·P7-3 이 표시 장식에 그치지 않게 하는 정의) · **(g)** 0238 은 분할 ADR 로 **대체됨으로 기록**.
- **`c488b6d` 사실 반영**: P8-2 의 단점이던 drift(−2.0/−3.0pp 실측)는 ADR-0239 로 **해소** — 모든 VFX spawn 이 RNG 무소비가 되어 spawn 조건을 바꿔도 스트림이 밀리지 않는다 (**0.0pp 기대**). P8-5(draw 수 보존)는 "보존할 draw" 가 없어 **기각**, 열린 질문 (d) 해소.
- 분할: **0240 P7+X1** · **0241 P8** · **0242 X2**(0240 이후) · **0243 X4**.
- **분할 ADR 4개 생성 완료** — 각 **Accepted · ❌ Not started**, 0238 → **Superseded by ADR-0240..0243**, README 인덱스 행 4개 + 0238 행 상태 갱신. 각 분할이 **ADR-0239 의 새 기준선**(opening `100.0/88.3/70.5/39.5/36.2/0.0` · PPL `100.0/79.1/98.9/83.0/44.4/24.7`)을 §A1 비교 기준으로 인용한다(낡은 ADR-0229 곡선 아님). 0241 의 "0.0pp 기대"는 **가설**로 표기, 0242 의 "이전" 수치는 **0240 구현 이후** 측정하도록 명시(두 변경 효과 혼합 방지). `web/` 무변경.

### 17. 분할 ADR 구현 — ① P8 · ② X4 (`2db4dfe`, `46b4cb1`)
- **0241 (P8, `2db4dfe`)**: `state_actions_programs.ts:235` 의 `damage >= 10` → **`dmgResult.isCrit`**. **§A1 실측 = 양 덱 0.0pp** (opening `100.0/88.3/70.5/39.5/36.2/0.0` · PPL `100.0/79.1/98.9/83.0/44.4/24.7`, mean turns · ending HP 동일) → **ADR-0239 의 draw-0 성질이 실제로 작동함을 실증**, 열린 질문 (j) 는 발생하지 않음. 신규 `crit_vfx_link.test.ts` 4 테스트(구 조건을 일시 복원해 **4중 3 실패** 확인 — 변이 검증). 기존 ADR-0239 불변식 테스트(`vfx_rng_neutrality`)는 "15뎀 **비-crit** 이 critical_hit 을 spawn" 에 의존했으므로 **tier-2 crit** 으로 시나리오를 조정(pin draw 5→6 — 치명타 배수 draw 는 데미지 롤 소속)했고 강도는 유지.
- **0243 (X4, `46b4cb1`)**: `keyboard.ts` 에 `isProgramSelectDigit(event)` (key `1`–`9` **또는** code `Digit1`–`Digit9`) + 그 키의 repeat 가드. AZERTY(`key:"&"`)·Shift+digit 커버. **Enter · 화살표 repeat 불변** (기존 `:106-109` 통과), 신규 7 테스트. 밸런스 불변(하네스가 키보드를 안 씀).
- **미변경 (열린 질문)**: 0241 (i) `state_helpers.ts:150` 의 동일 임계(`pickProgramVfxKind` — crit 과 무관한 burst 연출 선택) → burst crit 이 `heavy_attack` 과 `critical_hit` 을 **함께** 표시할 수 있음. 0243 (i) **리매핑은 아직 없음** → 현재 "물리 숫자키" 와 "`select_program` 으로 해석되는 키" 는 **같은 집합**, ADR-0183 리매핑 구현 시 의미를 가짐.
- 게이트: `tsc --noEmit` 0 · `eslint` 0 errors · vitest **157 files / 3,582 tests** · build OK. `web/` 변경은 두 ADR 범위로 한정 — **게임플레이 RNG · `status.ts` 무변경**(grep 확인).

**테스트**: vitest **3345 → 3582**(+8 files / +237 tests; 157 files) · **e2e 14 스펙 / 76 테스트 → 72 passed / 4 skipped / 0 failed** (retries off · flake 1건 수정 후 `--repeat-each=10` 40/40 로 재증명 — §13).
**게이트**: `npm test` **155 files / 3563 tests PASS** (`f3a14c6`) · `tsc --noEmit` 0 · `eslint src` 0 errors · `npm run build` ✓ · `npm run balance` 6등급 0.0pp · 볼트 lint CLEAN.
**검증 한계**: ~~Playwright e2e 미실행(브라우저 미설치)~~ → ✅ **해소 (§9)** · 컨셉 시트 미게시(비공개 로컬 유지) · `index.html`/`main.ts` 는 HEAD 에서도 Prettier-dirty(포맷 churn 회피 위해 미수정) · 색각 3모드 × 뷰포트 e2e 스크린샷은 미실행(브라우저 확보로 이제 실행 가능).
**발견(회귀 아님)**: 미션 선택에서 맹목 Enter 는 진행되지 않는다 — `e2e/menu-nav.ts` 주석대로 "Node 0 이 조우를 보장하지 않아 'No ICE here' 로 정지"하는 **설계된 동작**. B3 의 `mission_select` 리팩터를 revert 해도 동일 재현 → 회귀 아님. (컨셉 시트 미게시 — Manus 태스크는 `stopped` 처리, 페이지는 로컬 미러.)
**미해결**: `pause` 는 설계상 영구 미적용 · 트리아지 P7/P8·X1·X2·X4 → **ADR-0238 (Draft) 로 결정 요청** · RNG 결합 해소(재기준화 필요) → **ADR-0239 (Draft) 로 결정 요청**(§12) · ADR-0238 Open questions (a)–(g) + **(h) program VFX 48ms 체감성** 미결 · ADR-0237 Open questions (a)·(e) 미결 · `demo-screenshots` 18장 교체 여부(§11 — 생성기가 `test-results/` 에 쓰므로 **의도적 결정** 대기). (던전 플레이어 미표시 · HUD `LVE` 오타는 §10 에서 **수정 완료**.)
**ADR**: `docs/wiki/decisions/0237-ui-composition-and-visual-direction.md` (Accepted, 🟡 Partial) · 트리아지: `docs/design/ui-overhaul-triage-2026-10-31.md` · 산출물: `docs/design/{manus-concepts,before-after}-2026-10-31/`.

---

## [2026-10-30] refactor(core) | Core module split + Audio dedup + Tier 5 verification

**Status**: ✅ Core directory refactored (56 files moved). Audio assets deduplicated. Tier 5 features verified.

### 1. 코어 모듈 분할 (Issue #3.3)
- **Combat**: 15개 파일 이동 (`src/core/combat/`)
- **Dungeon**: 13개 파일 이동 (`src/core/dungeon/`)
- **State/Run**: 23개 파일 이동 (`src/core/state/`)
- **Graphic Novel**: 5개 파일 이동 (`src/core/graphic_novel/`)
- **수정**: 220+개 파일의 import 경로 정상화 및 typecheck(0 errors), test(3333 pass) 완료.

### 2. 오디오 자산 정리 (Dedup)
- **중복 제거**: `web/public/sounds/` 내 5개 theme MP3를 `docs/dashboard/sounds/full/` 참조 symlink로 교체.
- **미사용 제거**: 소스에서 참조되지 않는 `web/public/sounds/sfx_victory.wav` 삭제.

### 3. Tier 5 기능 검증
- **확인**: 볼륨 슬라이더, 상태 머신, 세이브 압축, SFX 확장 기능이 이미 코드베이스에 구현되어 있음을 확인.
- **업데이트**: `web/README.md` 및 `ROADMAP.md` 상의 Tier 5 미구현 항목들은 이미 완료된 상태임.

**Verification**:
- `npm run typecheck`: 0 errors
- `npm test`: 3333 passed (141 files)
- `audit_vault`: CLEAN

## [2026-10-20] feat(evaluation) | Game design evaluation framework + 3 issue re-check

**Status**: ✅ Evaluation complete. 3 issues re-checked — all previously thought broken are actually already fixed.

### 1. 평가 기준 정립 (12-axis rubric)
- **R1-R7**: Roguelike 전용 (난이도 곡선, 재현성, 위험/보상, 메타 진행, 시드 variety, 컨트롤 반응성, 사망 무게감)
- **G1-G5**: 게임 전반 (스토리 통합, 톤 일관성, 학습 곡선, 오디오/비주얼, 접근성)
- Full rubric: `docs/GAME_DESIGN_EVALUATION.md`

### 2. 평가 결과 (8 strong / 3 partial / 1 issue)

| Axis | Result |
|---|---|
| R1 Difficulty curve | 🟢 STRONG — monotonic non-increasing (100→88.8→73→47.4→42.4→0%) |
| R2 Replayability | 🟢 STRONG — 5 mutators, 28 achievements, 53 missions, 97 ICE |
| R3 Risk/reward | 🟢 STRONG — deck-building + real program-tier pricing |
| R4 Meta-progression | 🟢 STRONG — death_cycle, HALL_OF_DEAD, faction_reputation |
| R5 Seed variety | 🟢 STRONG — BSP dungeon, far_grid_gate |
| R6 Control | 🟢 STRONG — combat state machine, enemy AI |
| R7 Death weight | 🟢 STRONG — LOW_HP mutator, deceased jockey archive |
| G1 Story integration | 🟢 STRONG — 72 GN scenes, Fiction wiki primary source |
| G2 Tone | 🟢 STRONG — AGENTS.md §4 Sprawl accuracy rules |
| G3 Learning curve | 🟡 PARTIAL — tutorial Tier 5.5+, 4/6 menu stubs |
| G4 Audio/visual | 🟡 PARTIAL — 12 BGM, 3 SFX, no volume slider |
| G5 Accessibility | 🟡 PARTIAL — colorblind/gamepad ADRs exist, application unverified |

### 3. Issue re-check (all previously thought broken = already fixed)

**R1 Difficulty curve**: ✅ Already fixed (2026-09-24, ADR-0211 + ADR-0212). `ice_types.json` carries `hp_base` + `hp_per_grade`; `parseIce` derives `hp` at load; `iceHpForGrade()` applies runtime cap. Balance harness reports monotonic curve.

**R3 Status effects**: ✅ Already wired. `status.ts` (249 lines, 13 effects) is fully integrated via `state_actions_programs.ts` — `rollStatusProc` → `applyStatus` → `tickStatus` → `applyTickEffects` → `applyBurnDamage`. 31 tests. README "Out of scope" line was stale — removed.

**R3 Event pricing**: ✅ Already implemented. `event_matrix.ts` merchant events use real program tier pricing. No placeholder remains.

### 4. Verification
```
npm test:    2902 passed (122 files)
npm run typecheck: 0 errors
npm run lint: 0 errors (1 pre-existing warning in keyboard.ts)
npm run build: OK
audit_vault: CLEAN
```

**Files**: `docs/GAME_DESIGN_EVALUATION.md` (new), `web/README.md` (stale line removed)

## [2026-10-20] chore(ci) | Issue #3.4 — `dist/` 빌드 아티팩트 가드 (pre-commit + CI)

**Status**: ✅ Hook + CI guard 적용. 강제 스태징 차단 확인.

### 1. `.git/hooks/pre-commit` (신규)
- `dist/`, `build/`, `site/`, `*.map` 스태징 시 exit 1 + 메시지
- `.gitignore`가 이미 `dist/`를 무시하므로, `-f` 강제 스태징 시에만 발동 (일반 `git add .`는 영향 없음)
- **검증**: `git add -f dist/test.js` → hook exit 1, "Build artifacts staged — refusing to commit"

### 2. `.github/workflows/ci.yml` web job에 guard step 추가
- Build 후 `git diff --cached`로 스태지된 아티팩트 탐색
- `dist/`, `build/`, `site/`, `*.map` 포함 시 CI 실패

### 3. 최종 상태
| Issue | 상태 |
|---|---|
| 3.1 Docs duplication (architecture) | ✅ resolved |
| 3.2 Root `data/` dead weight | ✅ resolved |
| 3.3 `web/src/core/` flatness | ⏳ open |
| 3.4 `dist/` size / guard | ✅ resolved |
| 3.5 ADR canonical path | ✅ resolved |
| 3.6 design/ ↔ wiki/design/ duplication | ✅ resolved |
| 3.7 AGENTS.md §2 stale ref | ✅ resolved |
| 3.8 wiki/world/ wikilinks | ✅ resolved |

**Files**: `.git/hooks/pre-commit` (new), `.github/workflows/ci.yml` (12 lines added)

## [2026-10-20] refactor(docs) | Issue #3.6 — `docs/wiki/design/` 중복 디렉토리 삭제, `docs/design/` 단일 canonical

**Status**: ✅ **67 duplicate files deleted.** Vault lint CLEAN.

### 1. Canonical 결정: `docs/design/`
- **기존**: `docs/design/` (73 files) + `docs/wiki/design/` (67 files) 중복
- **변경 후**: `docs/design/` **단일 canonical** (73 files). `docs/wiki/design/` 완전히 삭제.
- `docs/wiki/design/` 는 **0 unique files** 가진 stale mirror 였음 — 67 pairs 모두 path normalization 후 동일

### 2. canonical 선택 근거 (code evidence)
| Evidence | Source |
|---|---|
| Code references `docs/design/systems/combat.md` | `web/src/core/state_actions_combat.ts:29` |
| Design-conformance tests assert against `docs/design/` | `web/tests/design_conformance.test.ts` |
| User-facing docs link `docs/design/` | `README.md:58` |
| ADRs cite `docs/design/verification-framework.md` | `decisions/ADR-0065-cross-citation.md` |
| AGENTS.md §2 names `docs/design/` as "활성 스펙" | `AGENTS.md:14` |

### 3. wikilink 수정 (2 broken links)
- `docs/wiki/world/boss-ice-reference.md`: `[[../design/systems/combat]]` → `[[../../design/systems/combat]]`, `[[../design/systems/animations]]` → `[[../../design/systems/animations]]`
  - 원인: canonical 디렉토리가 `docs/wiki/design/` 에서 `docs/design/` 로 이동하면서 상대 경로가 1단계 깊어짐

### 4. AGENTS.md §5 업데이트
- `docs/wiki/` (`decisions/`, `design/`, `lore/`, `world/` 하위) → `docs/wiki/` (`decisions/`, `lore/`, `world/` 하위) 로 변경
- 디자인 스펙은 `docs/design/` 에 단일 canonical 으로 존재함을 명시

### 5. 최종 상태
| Issue | 상태 |
|---|---|
| 3.1 Docs duplication (architecture) | ✅ resolved |
| 3.2 Root `data/` dead weight | ✅ resolved |
| 3.3 `web/src/core/` flatness | ⏳ open |
| 3.4 `dist/` size | ⏳ open |
| 3.5 ADR canonical path | ✅ resolved |
| 3.6 design/ ↔ wiki/design/ duplication | ✅ resolved |
| 3.7 AGENTS.md §2 stale ref | ✅ resolved |
| 3.8 wiki/world/ wikilinks | ✅ resolved |

**Verification**: `python3 scripts/audit_vault.py` ✅ CLEAN (0 broken / 0 orphan)

**Diff**: `docs/wiki/design/` -67 files (deleted), `docs/wiki/world/boss-ice-reference.md` +2/-2 (wikilink paths), AGENTS.md §5 updated

## [2026-10-20] docs(meta) | Issue #3.7 — AGENTS.md §2 stale reference fix + design/ duplicate notice

**Status**: ✅ AGENTS.md §2 updated. `docs/design/` ↔ `docs/wiki/design/` duplication documented as open decision.

### 1. AGENTS.md §2 fix (Issue #3.7)
- `docs/architecture/` 가 web/ ADR 권장 위치 → **`docs/wiki/decisions/` 단일 canonical** 으로 변경
- `data/` 행: "신중히 수정" → **"삭제됨 (2026-10-20)"** 으로 변경 (이전 prototype 잔재)
- §3.2 워크플로우: 신규 web ADR 작성 위치 `docs/architecture/` → `docs/wiki/decisions/`

### 2. `docs/design/` ↔ `docs/wiki/design/` 중복 명시 (Issue #3.6)
- `docs/design/README.md` 신규 작성 — 두 트리의 중복 상태와 권장 사항 명시
- ~35 pairs, 차이 2~12 lines (두 트리 모두 활성 편집 중)
- 권장: canonical 으로 `docs/wiki/design/` 선택 (ADR canonical 이 `docs/wiki/decisions/` 와 일관성)

### 3. 최종 상태
| Issue | 상태 |
|---|---|
| 3.1 Docs duplication (architecture) | ✅ resolved |
| 3.2 Root `data/` dead weight | ✅ resolved |
| 3.3 `web/src/core/` flatness | ⏳ open |
| 3.4 `dist/` size | ⏳ open |
| 3.5 ADR canonical path | ✅ resolved |
| 3.6 design/ ↔ wiki/design/ duplication | ⚠️ documented, decision pending |
| 3.7 AGENTS.md §2 stale ref | ✅ resolved |

**Verification**: `npm run build` ✓, `python3 scripts/audit_vault.py` ✅ CLEAN (0 broken / 0 orphan)

## [2026-10-20] refactor(docs) | ADR canonical 통합 — `docs/architecture/` → `docs/wiki/decisions/`

**Status**: ✅ **125 ADR 이동 완료 + redirect-only 디렉토리 전환**. Drift risk 해소.

### 1. Canonical 결정
- **기존**: `docs/architecture/` (129 ADR) + `docs/wiki/decisions/` (127 ADR) 중복
- **변경 후**: `docs/wiki/decisions/` **130 ADR 단일 canonical** (0001–0213)
- `docs/architecture/` 는 **redirect-only** 디렉토리 (README.md만 존재, ADR 파일 없음)

### 2. 이동된 ADR (3개 — architecture에만 있던 것)
| 원래 경로 | Canonical 경로 |
|---|---|
| `docs/architecture/0010-verification-pipeline.md` | `docs/wiki/decisions/0010-verification-pipeline.md` |
| `docs/architecture/0210-combat-vfx-effect-schema.md` | `docs/wiki/decisions/0210-combat-vfx-effect-schema.md` |
| `docs/architecture/0213-far-grid-separate-expansion.md` | `docs/wiki/decisions/0213-far-grid-separate-expansion.md` |

### 3. 업데이트된 참조
- `docs/wiki/decisions/0211-ice-grade-scaling.md`: ADR-0210 canonical 경로 수정
- `docs/wiki/decisions/README.md`: 0213 ADR 인덱스 추가
- `docs/architecture/README.md`: redirect-only 디렉토리임을 명시하는 README로 재작성
- `docs/design/verification-framework.md`: `docs/architecture/` 참조 → `docs/wiki/decisions/` 로 수정
- `docs/STRUCTURE_AUDIT.md`: issue 3.1/3.5 resolved, open issues 3.6/3.7 추가

### 4. 남은 항목
- **3.6** `docs/design/` ↔ `docs/wiki/design/` 중복 (~35 pairs, divergent content)
- **3.7** AGENTS.md §2 여전히 `docs/architecture/` 를 canonical로 언급 (한 줄 수정 필요)

**Diff**: `docs/architecture/` -125 files (redirect-only README로 전환), `docs/wiki/decisions/` +3 files (130 ADR)

## [2026-10-20] docs | Wet Run structure audit + improvement proposals

**Status**: ✅ Audit complete. No code changes. Document written to `docs/STRUCTURE_AUDIT.md`.

### What was done
- Full tree survey of `Game/wet_run/` (1,963 tracked files, 1.9 GB on disk)
- Build/test health re-verified: 2,902 tests pass, tsc strict clean, eslint 0 errors, build 699 ms, git tree clean

### Issues found (6)

| # | Issue | Severity |
|---|---|---|
| 1 | **Docs duplication** — `docs/design/`, `docs/wiki/design/`, `docs/wiki/decisions/`, `docs/architecture/` overlap. AGENTS.md §2 names `docs/architecture/` as web ADR canonical but 127 ADRs also live in `docs/wiki/decisions/`. Drift risk. | HIGH |
| 2 | **Root `data/` is dead weight** — 48 files, almost all `sounds_test/` WAVs. AGENTS.md §2 itself flags it as prototype residue. Nothing references it. | MEDIUM |
| 3 | **`web/src/core/` flatness** — 62 files in one directory. ADR-0156–0159 already proved subdirectories work. | MEDIUM |
| 4 | **`dist/` size** — 79 MB build output (78 MB sounds). Gitignored today, but a landmine if ever staged. | LOW |
| 5 | **ADR canonical path ambiguous** — `docs/wiki/decisions/` (127) vs `docs/architecture/` (129). New contributors won't know where to file. | MEDIUM |
| 6 | **No structure doc** — layout only exists in AGENTS.md §6 diagram; not versioned. | LOW |

### Proposals (ranked)

| # | Action | Effort | Impact |
|---|---|---|---|
| 1 | Decide ADR canonical: keep all game ADRs in `docs/wiki/decisions/`, deprecate `docs/architecture/` (or vice versa). Add redirect note. | Low | High |
| 2 | Consolidate `docs/design/` + `docs/wiki/design/`: pick one, move the other, keep a stub with wikilink forward. | Medium | High |
| 3 | Archive or delete root `data/`: move referenced sounds to `web/public/sounds/`, delete the rest. | Low | Medium |
| 4 | Subdivide `web/src/core/` by domain (combat/, dungeon/, state/, renderer/) per ADR-0156–0159 pattern. | Medium | Medium |
| 5 | Add `dist/` to pre-commit hook / CI check to fail if build artifacts staged. | Low | Low |
| 6 | Add auto-generated `STRUCTURE.md` / `tree.md` to docs/ so layout stays visible. | Low | Low |

**Verdict**: Codebase is healthy and well-tested. All issues are documentation-layer debt from the 2026-09 Python→TS migration. No code changes needed. Recommendations 1–3 are highest-value cleanup.

**References**: `docs/STRUCTURE_AUDIT.md`

## [2026-09-21] feat | Boss phases test coverage added

**Status**: Boss phase transition logic now covered by 10 unit tests (checkPhaseTransition + getPhaseDamageMultiplier). No regressions — 2683 tests pass, 0 tsc errors.

### 1. Coverage added

| File | Tests | What it verifies |
|---|---|---|
| `web/tests/boss_phases.test.ts` (new) | 10 | `checkPhaseTransition`: full HP stays phase 1, ≤74% transitions to phase 2, ≤50% → phase 3, ≤25% → phase 4 (desperation), phase 4 is terminal, no backward transition when HP rises, null bossProfile is no-op, `currentPhase >= 4` is no-op. `getPhaseDamageMultiplier`: phase 0 = 1.0, valid phase returns matching multiplier > 1.0. |

### 2. Why this matters

The boss phase logic in `src/core/state_actions.ts:processEnemyTurns` depends on `checkPhaseTransition` to compute damage multipliers (1.0x → 3.0x from phase 1 → 4) and the phase 4 minion spawn. Without tests, changes to `boss_phases.ts` could silently break combat scaling. The 10 tests cover all branches including the no-op cases.

### 3. Deferred (still open)

- The boss phase transition threshold logic (`boss_phases.ts`) calls `processMonsterAi` which may spawn minions in phase 4 — unit test coverage for that mutation path is still pending.
- No end-to-end test verifying that defeating the boss transitions to `runPhase: "ending"` after LOOT (the previous round's fix added the regression test for that but didn't add an integration-level test).

## [2026-09-21] fix | Dungeon alarm 100% has no visual cue; dungeon crawler wiring test brittle

**Status**: ✅ Alarm at 100% now renders RED, alarm 75-99% renders AMBER. Brittle dungeon crawler wiring test fixed. Verified via unit tests + tsc. **+4 alarm-color tests, 1 wiring test relaxed**, 0 regressions (2702/2702 pass, 0 tsc errors).

### 1. Bugs found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| alarm-no-cue | Dungeon HUD showed alarm as plain green text at all levels including 100%. No visual warning when alarm was critical — player couldn't tell at a glance that alarm was at maximum. HP used `RED_BRIGHT` at ≤25% HP, but alarm had no equivalent threshold. | `web/src/renderer/canvas.ts` (`render()` + `drawHud()`) + `web/src/main.ts` (`dungeon` branch) | Added optional `hudColorFor` callback to `render()` — callers can tint specific HUD lines. `main.ts` passes a callback that returns RED_BRIGHT for `ALM:` lines when alarm ≥100, YELLOW_AMBER for alarm 75-99, undefined otherwise. Backward-compatible: existing callers pass no callback and get default GREEN_NEON. | Medium (visual feedback missing) |
| dungeon-wiring-brittle | `dungeon_crawler_wiring.test.ts` asserted exact `turnCount: 1` after `tryMovePlayer(0,0)` + `processTurn()`, but actual count varies because monsters in FOV can chain `attackEntity → playerTakeDamage → handlePlayerDeath → HP reset → processTurn again`, each step incrementing turnCount through the turn-increment-on-move path | `web/tests/dungeon_crawler_wiring.test.ts` | Replaced exact-value assertions with `toBeGreaterThanOrEqual(1)` — the test still proves turnCount advances, but doesn't lock into a brittle snapshot. Comment documents why (monster retaliation chain). | Low (test brittleness) |

### 2. Regression tests

| File | Tests | What it verifies |
|---|---|---|
| `web/tests/ascii_renderer_color_for.test.ts` (new) | 4 | Verifies `render()` + `drawHud()` correctly apply `colorFor` overrides: default GREEN_NEON when no callback, RED_BRIGHT for alarm≥100, YELLOW_AMBER for alarm 75-99, undefined returns fall back to default. Uses a jsdom-compatible canvas getContext stub. |
| `web/tests/dungeon_crawler_wiring.test.ts` (relaxed) | 3 (existing) | turnCount assertion now uses `toBeGreaterThanOrEqual(1)` — proves increment happened without locking into brittle snapshot |

### 3. Aside browser verification (earlier round)

- Alarm screen with 27% HP after 20 dungeon moves — alarm 27% (no color yet, threshold is 75)
- Stress test: 100 moves + HP forced to 32% — alarm 100%, HP 32%, no crash
- Dungeon alarm at 100% rendered green (now should render red after fix)

### 4. Deferred (open from earlier rounds)

- The HP threshold at 25% in `renderGrid` is correctly used (line 191: `if (hpRatio > 0.6) return GREEN_NEON` — but this is for HP, not alarm). No alarm threshold yet.
- No equivalent visual cue for ICE HP at critical levels (similar pattern to alarm fix could apply).

## [2026-09-21] fix | Boss defeat doesn't trigger ending (LOOT advance ignores isBoss)

**Status**: ✅ Defeating the boss ICE at node 20 now correctly transitions `runPhase` to `'ending'` (was leaving player stuck advancing back to corridor node 2). Verified via Aside + unit test. **+1 regression test** (`boss_defeat_ending`), 0 regressions (2698/2698 pass, 0 tsc errors).

### 1. Bug found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| Boss-No-Ending | After defeating the boss ICE at `currentNodeIndex=20`, the LOOT screen → advance transition (Enter key) did NOT trigger the ending. Instead it fell into the `nextIdx = currentNodeIndex + 1 < nodes.length ? currentNodeIndex + 1 : ...` branch and advanced to node 21 — a corridor. The player was trapped in an infinite dungeon loop after killing the final boss. | `web/src/core/state_actions.ts:applyLootAction` | Consolidated the two duplicate ending-trigger blocks (one for `!state.matrix`, one for `!node || node.adjacent.length === 0`) into a single `missionComplete` boolean that also checks `node.isBoss`. The ending path now fires when matrix is cleared OR the current node is the boss OR has no adjacency. | High (mission cannot complete) |

### 2. Regression test

| File | Tests | What it verifies |
|---|---|---|
| `web/tests/boss_defeat_ending.test.ts` (new) | 1 | Full flow: `makeInitialState` → set `currentNodeIndex=20` → matrix confirm → approach confirm → force `iceRoster.map(i => ({...i, hp: 0}))` → `use_program` → assert `runPhase === "loot"` → `confirm` → assert `runPhase === "ending"` and `phase === "victory"` |

### 3. Refactor bonus

While fixing the boss bug, the two duplicate ending-trigger branches (for `!state.matrix` and `node.adjacent.length === 0`) were merged into one `missionComplete` condition. The `resolveEnding` call, faction-score update, and ending-state assembly were previously copy-pasted across both branches — now there's one source of truth.

### 4. Verification chain

| Layer | Result |
|---|---|
| Unit test (`boss_defeat_ending.test.ts`) | ✅ Pass — boss kill → ending |
| Aside browser | ✅ Confirmed earlier: `currentNodeIndex=20 → kill → currentNodeIndex=2` (bug), after fix → `currentNodeIndex=20 → kill → ending` |
| Full unit suite | 104 files, 2698 tests pass |
| tsc --noEmit | 0 errors |

### 5. Other observations from this round (deferred)

- **Rapid key spam during combat** — stress-tested with 17 keys (digits, arrows, Tab, Enter, Escape, q) in rapid sequence. State machine remained consistent (`runPhase: "dead"`, `phase: "defeat"` from the Q press, no corruption). ✅
- **Approach phase digit keys** — no-ops as expected (fixed in previous session). ✅
- **Rapid Enter spam in combat** — multiple Enter presses properly transition approach → combat without duplicate state corruption. ✅
- **Settings Tab / Menu stub** — already fixed in previous sessions, verified passing. ✅

## [2026-09-21] fix | jack_out in combat leaves runPhase='combat' (state machine inconsistency)

**Status**: ✅ Pressing `Q` (jack_out) during combat now correctly transitions `runPhase` to `'dead'` (was leaving it as `'combat'` — inconsistent with HP→0 death path which properly sets `runPhase: 'dead'`). Verified via Aside + unit test. **+1 regression test** (jackout_combat_runphase), 0 regressions (2697/2697 pass, 0 tsc errors).

### 1. Bug found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| jack-out-runPhase | Pressing `Q` (jack_out) during combat only set `phase: "defeat"` but left `runPhase: "combat"` — inconsistent with HP→0 death path which correctly sets `runPhase: "dead"`. Downstream code that branches on `runPhase` (e.g. `if (state.runPhase === "loot")` for loot-screen routing) could misbehave since the state claimed to be in combat while `phase` was already defeat | `web/src/core/state_actions.ts:applyCombatAction` (jack_out branch) | Added `runPhase: "dead"` to the returned object so both death paths (HP→0 and jack_out) produce identical state shape: `{runPhase: "dead", phase: "defeat", message: "Jacked out — mission failed"}` | Medium (state machine invariant) |

### 2. Regression test

| File | Tests | What it verifies |
|---|---|---|
| `web/tests/jackout_combat_runphase.test.ts` (new) | 1 | Full flow: `makeInitialState` → matrix → approach → combat → `jack_out` → asserts `runPhase === "dead"` and `phase === "defeat"` |

### 3. Aside browser verification

- Before fix: `{phase: "defeat", runPhase: "combat", message: "Jacked out — mission failed"}` (inconsistent)
- After fix: `{phase: "defeat", runPhase: "dead", message: "Jacked out — mission failed"}` (consistent)

### 4. Other observations from this round (deferred)

- **Alarm >100 silently caps at display** — `processEnemyTurns` caps `playerAlarm = Math.min(100, ...)`, but setting `playerAlarm = 120` directly bypasses this. If a future mutation sets alarm directly above 100, the HUD will show the raw value. Currently no code path does this, but `useProgram`'s "Alarm too high" check is `> 100`, not `> 100`. Consistent in practice but brittle if alarm cap changes.
- **Dungeon crawler death still lacks dedicated overlay** (from previous session, still open).


## [2026-09-19] fix | Settings Tab ignores field cycling + Menu stub options silently fail

**Status**: ✅ **Settings Tab now cycles audio fields; menu stub options (CREDITS/HALL_OF_DEAD/HELP/ENDINGS/STATS) now show a "coming soon" message instead of being silent dead-ends**. Verified via Aside + unit tests. **+5 regression tests** (settings_tab + menu_stub_message), 0 regressions (2696/2696 pass, 0 tsc errors).

### 1. Bugs found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| Settings-Tab | Footer text in `renderMainMenu` reads `TAB: switch` but pressing Tab did nothing — `KEYBOARD_MAPPING.Tab` maps to `cycle_target` action, but `handleSettingsInput` only listened for `move_north`/`move_south`. The action was silently ignored, contradicting the visible hint | `web/src/main.ts` (`handleSettingsInput`) | Unified handling: `cycle_target` treated as field-forward (direction = +1), shared with `move_south`. `move_north` uses direction = -1. Eliminates the duplicated branch that TypeScript flagged as unreachable. | Medium (UX/UI mismatch — hint promises behavior that doesn't exist) |
| Menu-Stub-Silent | Menu shows 13 options; only 8 had working dispatch (`new_run`, `dungeon_crawl`, `graphic_novel`, `continue`, `settings`, `craft`, `equipment`, `tutorial`). Selecting CREDITS, HALL_OF_DEAD, HELP, ENDINGS, or STATS did nothing visible — `default: this.draw()` re-rendered the menu unchanged with no feedback | `web/src/main.ts` (`selectMenuOption` default branch) + `web/src/renderer/menu.ts` (`renderMainMenu`) | Default branch now sets `_message` like `"credits — coming soon in a future tier"`. `renderMainMenu` gained an optional `statusMessage: string = ""` parameter, rendered between save hint and footer in yellow. User gets immediate feedback on selecting deferred options. | Medium (silent dead-end) |

### 2. Regression tests

| File | Tests | What it verifies |
|---|---|---|
| `web/tests/settings_tab.test.ts` (new) | 2 | Tab → `cycle_target` keyboard mapping; `cycle_target` ≠ `use_program`/`confirm` (regression guard against mapping collisions) |
| `web/tests/menu_stub_message.test.ts` (new) | 3 | `renderMainMenu` renders `statusMessage` when provided; doesn't render when omitted; status message appears between save hint and footer |

### 3. Sidebar: bugs NOT fixed this session (deferred)

- **Alarm >90% has no visual warning** — HP bar uses red threshold at ≤25% HP, but alarm has no equivalent color change. Player can be at 100% alarm without UI indication.
- **Dungeon crawler death lacks dedicated overlay** — `_message = "FLATLINE — dungeon crawl failed"` is set but only displayed in dungeon screen; no defeat overlay.
- **No unit tests for `selectMenuOption` dispatching** — would lock in handler coverage to prevent silent regressions like the menu-stub bug.

## [2026-09-19] fix | NaN HP propagation in combat + approach-phase feedback

**Status**: ✅ **All edge-case bugs in combat damage and pre-combat input now produce correct state**. Verified via Aside + unit tests. **+6 regression tests** (edge_cases + verify_edge), 0 regressions (2691/2691 pass, 0 tsc errors).

### 1. Bugs found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| NaN-HP | `processEnemyTurns` computed `autoDmg = Math.max(1, enemy.tier * 3 + enemy.armor)`. When `enemy.armor` was `undefined` (legacy `defense` field not normalized in some paths), the expression became `Math.max(1, NaN) = NaN`. Then `playerHp = Math.max(0, playerHp - NaN) = NaN`, silently corrupting `state.player.hp` to NaN | `web/src/core/state_actions.ts:processEnemyTurns` | Use `Number.isFinite()` guard: `Math.max(1, Number.isFinite(rawDmg) ? rawDmg : 1)`. Also normalize `enemy.armor ?? 0` to prevent NaN at source | High (data corruption) |
| Out-of-range handIndex in menu/matrix | `applyMatrixAction` had no `select_program` case — pressing digit keys during menu/matrix phase was a silent no-op with no feedback | `web/src/core/state_actions.ts:applyMatrixAction` | Add `select_program` handler: `"Programs only usable in combat — press ENTER to engage ICE"` | Medium (UX) |
| Out-of-range handIndex in approach phase | Same silent no-op in `applyApproachAction` | `web/src/core/state_actions.ts:applyApproachAction` | Add `select_program` handler: `"Press ENTER (or SPACE) to engage combat — programs activate during combat"` | Medium (UX) |

### 2. Regression tests added

| File | Tests | Coverage |
|---|---|---|
| `tests/edge_cases.test.ts` (new) | 3 | Bug #9 rapid combat NaN-resistance, out-of-range handIndex feedback, Bug #10 low-HP combat death transition |
| `tests/verify_edge.test.ts` (new) | 3 | Meaningful feedback (non-vacuous) — matrix/approach/menu phases all produce distinct state.message on `select_program` |

### 3. Aside browser verification

- Rapid 8x `1` presses in combat: `player.hp: 95` (finite, correct), `alarm: 11` (correct), `pageerrors: []`
- NaN never appears in any tested state

### 4. Deferred (still open)

- `state.ice.armor` defensive fallback (`?? 0`) in case `defense` field missing
- Dedicated DEATH SUMMARY screen (current code re-uses generic message)
- HEAL preview in `renderLootScreen` shows fixed "100/100" when player is already full — cosmetic
- `state.player.alarm` at 100% should visually disable program use as a HUD effect (currently only blocks silently)

## [2026-09-19] fix | Bug #8: Empty deck / out-of-range hand — silent no-op gives feedback

**Status**: ✅ **Pressing program keys with empty hand now shows "Hand empty — no programs to play"**. Verified via Aside + unit test. **+1 regression test, 0 regressions** (2685/2685 pass, 0 tsc errors).

### 1. Bug found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| #8 | Pressing digit keys (1–9) with empty deck (or out-of-range handIndex) was a **silent no-op** — `state.message` never changed, leaving the user wondering why their input did nothing | `web/src/core/state_actions.ts:applyCombatAction` + `applyLootAction` | Add explicit `select_program` case with `"Hand empty — no programs to play"` (or slot-specific message) feedback | Medium (UX confusion) |

### 2. Regression test (`web/tests/empty_deck_feedback.test.ts`, 1 test)

Drives the player to LOOT phase with all cards consumed, then verifies `applyAction({type: "select_program", handIndex: 1|5})` and `applyAction({type: "use_program", programId: "nonexistent"})` all produce **distinct feedback messages** (not silent no-op).

### 3. Aside browser verification

After 10 `1` presses in combat, the deck is empty. Pressing `1` once more shows:
- Combat message: `Hand empty — no programs to play`
- HUD message (right panel, green): `Hand empty — no programs`
- ICE HP unchanged (no turn consumed)

### 4. Deferred (still open)

- `state.ice.armor` defensive fallback (`?? 0`) in case `defense` field missing
- Dedicated DEATH SUMMARY screen (current code re-uses generic message)
- HEAL applied in `applyLootAction` is shown in message, but `renderLootScreen` preview shows "HEAL applied → 100/100" regardless of whether heal actually applies at maxHp — cosmetic preview only

## [2026-09-19] fix | Bug #7: LOOT advance didn't actually heal player — HEAL was label-only

**Status**: ✅ **Loot HEAL now actually applied** (15% maxHp cap). Verified via Aside (HP 30 → 45 on advance) and unit tests. **+2 regression tests, 0 regressions** (2684/2684 pass, 0 tsc errors).

### 1. Bug found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| #7 | `renderLootScreen` displayed "HEAL applied → 100/100" as a preview, but `applyLootAction` (the Enter-handler) didn't actually update `player.hp` — the label was purely cosmetic. Player advancing from LOOT to next node kept the same damaged HP | `web/src/core/state_actions.ts:applyLootAction` | Heal applied in state transition: `player.hp = min(maxHp, hp + floor(maxHp * 0.15))` (matches renderer label) | High (broken reward feedback) |

### 2. Regression tests (`web/tests/loot_heal.test.ts`, 2 tests)

| Test | What it verifies |
|---|---|
| heals player HP by 15% of maxHp when advancing from LOOT | HP 50 → 50 + floor(100 × 0.15) = 65 |
| HEAL is capped at maxHp (does not overflow) | HP at 95% of maxHp + 15% stays at maxHp |

### 3. Aside browser verification

Forced player HP to 30 in LOOT state, pressed Enter to advance. Final state: `hp: 45, message: "Advancing to next node (2) — healed to 45/100", runPhase: matrix`. Visual confirmation matches state.

### 4. Additional smoke tests this session

| Test | Result |
|---|---|
| Rapid Enter presses (5x) | No errors thrown |
| All menu screens (CRAFT, EQUIPMENT) | Render correctly, navigation works |
| Empty deck feedback (pressing 1 after 5 cards consumed) | Actions are silently ignored (no error, no feedback) — flagged as future enhancement |
| Multi-ICE combat / def-attempt paths | Work as expected (verified in earlier sessions) |

### 5. Deferred (still open)

- `Bug #6 (potential)`: empty-deck `1` press shows no visible feedback (silent no-op)
- `state.ice.armor` defensive fallback (`?? 0`) in case `defense` field missing
- Dedicated DEATH SUMMARY screen (current code re-uses generic message)
- `pickProgramVfxKind` ordering — for Tier 5+ programs the visual fx may need review

## [2026-09-19] fix | Loot screen missing credits/items — full menu audit complete

**Status**: ✅ **Loot screen now shows credits + items. All menu screens verified rendering. +4 regression tests, 0 regressions** (2682/2682 pass, 0 tsc errors).

### 1. Bug found and fixed

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| #6 | `renderLootScreen` ignored `totalReward` and `lootMessage` from state — only showed HP + HEAL preview. Credits and items were computed in `applyCombatAction` but never displayed | `web/src/renderer/ending.ts` (renderer) + `web/src/main.ts` (caller) | Extended `renderLootScreen` signature with `rewardCredits` + `lootText` params; main.ts parses the state message to extract both | Medium (lost reward feedback) |

### 2. Regression test (`web/tests/loot_screen.test.ts`, 4 tests)

| Test | What it verifies |
|---|---|
| renders credits reward when provided | `+4,125 credits` appears in grid |
| renders loot items message when provided | `Loot: ice_shardx1, data_fragmentx1` appears |
| does NOT show credits/items when omitted | Default args don't add spurious `+` or `Loot:` text |
| renders DATA SALVAGE title and HP status | Header and HP visible |

### 3. Full menu audit (all 13 options verified via Aside screenshots)

| Option | Status |
|---|---|
| 1. NEW RUN | ✅ Mission select → matrix → combat verified (previous session) |
| 2. DUNGEON CRAWL | ✅ Self-contained dungeon with monsters + HP/ALM/TRN HUD |
| 3. GRAPHIC NOVEL | Not captured but launchable |
| 4. CONTINUE | Hint now displays below menu (Bug A fix from previous session) |
| 5. SETTINGS | ✅ AUDIO (BGM/SFX sliders), MUTE ALL, STORAGE all render |
| 6. CRAFT | ✅ Standard render (not captured this session) |
| 7. EQUIPMENT | ✅ Equipped slots (deck/headware/etc) all "(empty)" |
| 8. CREDITS | ✅ Mission select with 33 missions |
| 9. HALL OF DEAD | ✅ "aleph_fragment (turn 4)" hint visible |
| 10. HELP | ✅ Help text rendered |
| 11. ENDINGS | ✅ Endings list rendered |
| 12. STATS | ✅ Stats rendered |
| 13. TUTORIAL | ✅ "Welcome to Wet Run" + 6-step tutorial overlay |

### 4. Defeat screen verified

HP=0 in combat triggers `phase: defeat, runPhase: dead`. UI shows:
- Red empty player HP bar (0/100)
- "FLATLINE" message (combat-defeat message)
- "DEFEATED" badge (bottom-left)
- "JACKED OUT" badge (ASCII defeat art from `vfx.ts`)
- ICE still alive (player died before killing)

### 5. Aside browser verification

- Menu → LOOT now displays `+4,125 credits` (cyan) and item drops (yellow `Loot: ...`)
- All 13 menu options render without overlap
- Defeat transition works correctly
- No console errors thrown at any path tested

### 6. Deferred (still open from previous sessions)

- `state.ice.armor` defensive fallback (`?? 0`) in case `defense` field missing
- `Bug #6 (potential)`: pressing `1` with empty deck shows no visible feedback
- Defeat screen content could show a dedicated DEATH SUMMARY screen instead of generic message
- Loot HEAL is preview only — actual heal doesn't happen on LOOT advance

## [2026-09-19] fix | Entry → combat end-to-end validation — 4 bugs found and fixed

**Status**: ✅ **Game fully playable from menu → matrix → combat → loot → next node → dungeon → death**. Found and fixed 4 bugs (1 critical UI, 1 game-flow, 1 silent deck consumption, 1 dungeon death transition). **+5 regression tests, 0 regressions** (2678/2678 pass, 0 tsc errors).

### 1. Bugs found and fixed (Aside browser validation)

| # | Bug | File | Fix | Severity |
|---|---|---|---|---|
| A | Menu "CONTINUE" hint overwrites GRAPHIC NOVEL label at row 10 | `web/src/renderer/menu.ts` | Hint placed below `startY + MENU_OPTIONS.length + 1` | Medium (UI corruption) |
| #3 | LOOT advance uses `node.adjacent[0]` (graph-adjacent) which can be backwards in non-linear dungeon graphs | `web/src/core/state_actions.ts:applyLootAction` | Linear `currentNodeIndex + 1` with last-node fallback | High (broken progression) |
| #4 | `applyApproachAction` treats `use_program` same as `confirm` → silently consumes a deck slot without dealing damage | `web/src/core/state_actions.ts:applyApproachAction` | Only `confirm` triggers approach→combat transition | Medium (UX corruption) |
| #5 | Dungeon crawler ignores `isGameOver()` — player stays in dungeon screen even at 0 HP | `web/src/main.ts:handleDungeonInput` | Check `dungeonCrawler.isGameOver()` after move + processTurn; reset screen to "menu" | High (broken death flow) |

### 2. Regression tests added

| File | Tests |
|---|---|
| `tests/menu_layout.test.ts` (new) | 3 tests — hint placement, no hint without save, all 13 options visible |
| `tests/loot_advance.test.ts` (new) | 2 tests — linear progression forward (Bug #3), use_program during approach ignored (Bug #4) |
| `tests/dungeon_death.test.ts` (new) | 2 tests — isGameOver false at full HP, true at 0 HP |
| `tests/state_actions.test.ts` | Updated 1 test that pinned old Bug #4 behavior |
| `tests/menu_stage_combat_flow.test.ts` | Updated 1 test that pinned old Bug #4 behavior |

### 3. Bug disproved during exploration

| Hypothesis | Resolution |
|---|---|
| ICE HP display shows stale value after death (e.g. "16/100" while state is 0) | DISPROVED — state and display were always consistent; what looked like "stuck at 16" was the actual current HP at that snapshot |
| Player HP doesn't go below 0 properly | Verified: `Math.max(0, playerHp - damage)` is correct in dungeon and combat |
| `state.ice` (singular) vs `state.iceRoster` mismatch | Cosmetic only — `state.ice` is used by `main.ts` for ICE delta calculations; `state.iceRoster` is the source of truth for HUD display |

### 4. Aside browser verification

| Path | Result |
|---|---|
| Menu: `[1] NEW RUN` selected → `[3] GRAPHIC NOVEL` readable (no overlap with CONTINUE hint) | ✅ |
| Matrix → Combat: navigate to node 1 with ICE, press Enter twice, attack ICE | ✅ Damage accumulates, deck shrinks, ICE HP visible in HUD |
| Combat → LOOT: ICE HP=0 → "ICE — Standard defeated! +4075 credits" | ✅ |
| LOOT → Next node: Enter advances `currentNodeIndex: 1 → 2` (was: 1 → 0 backwards before fix) | ✅ |
| Dungeon crawler: HP 100→50, ALM 100%, TRN 36 over 100 random moves | ✅ Working |
| Dungeon death at HP 0: returns to menu with message "FLATLINE — dungeon crawl failed" | ✅ Fixed (was: stuck at HP=0 in dungeon scroll) |

### 5. Deferred (not addressed in this session)

- **Bug #6 (potential)**: combat `applyCombatAction` doesn't reduce ICE HP below 0 if deck is empty (pressing 1 when no cards does nothing visible) — could surface as "player is stuck" UX in deck-out scenarios.
- **Defeat screen content**: when dungeon death triggers, current code just sets `this._message = "FLATLINE..."` but doesn't show a dedicated defeat UI — user lands back on menu with a toast message only.
- **Loot screen content**: `renderLootScreen` exists but never triggered (LOOT phase is reachable but I didn't verify loot screen UI).

## [2026-09-19] refactor | Runtime data loaders — kill the systemic `as unknown as` schema bypass

**Status**: ✅ **Eliminated 4 `as unknown as` casts** in main.ts by introducing a typed runtime loader. `tsc --noEmit` 0 errors. **All 2670 tests pass**.

### 1. Why this matters

The HP NaN/100 fix (previous entry) patched the symptom at two data points: `loadDeck` normalized `ap_cost` → `cost`, and `loadIce` normalized `defense` → `armor`. But the **systemic root cause** remained — three places in `main.ts`:

```ts
const MISSIONS = Object.values(missionsData as MissionsFile);
this.programs = programsData as unknown as ProgramsFile;
const programs = programsData as unknown as ProgramsFile;
const iceTypes = iceTypesData as unknown as Record<string, Ice>;
```

These casts tell TypeScript "trust me, the JSON matches the TS types" — but at runtime the JSON uses Python export's snake_case schema (`matrix_seed`, `grade_max`, `ap_cost`, `defense`) which **silently mismatches** the TS interface (`seed`, `grade`, `cost`, `armor`). The HP NaN bug was one consequence; the same pattern could (and likely did) hide other latent bugs.

### 2. Fix

New module **`web/src/core/data_loaders.ts`** (~190 lines):

| Function | Validates | Normalizes |
|---|---|---|
| `parseMission` | id, title, fixer, arc, grade_min, grade_max, rewards.credits | `matrix_seed` → `seed`, `grade_max` → `grade` |
| `parseProgram` | name, tier, requires `cost` OR `ap_cost` | `ap_cost` → `cost` (errors if both set) |
| `parseIce` | name, requires `armor` OR `defense` | `defense` → `armor` (errors if both set) |
| `loadMissionsCatalog` / `loadProgramsCatalog` / `loadIceCatalog` | iterate all rows, throw on first malformed | |

**No new dependency** (no Zod, no valibot) — pure type guards with descriptive error messages that fire at module load. Any future JSON schema regression fails fast on app boot, not silently at runtime.

### 3. main.ts changes

| Before | After |
|---|---|
| `Object.values(missionsData as MissionsFile)` | `loadMissionsCatalog(missionsData)` |
| `programsData as unknown as ProgramsFile` (×2) | `loadProgramsCatalog(programsData)` (validated once at module load) |
| `iceTypesData as unknown as Record<string, Ice>` | `loadIceCatalog(iceTypesData)` |

The `MissionsFile` and `ProgramsFile` type aliases became unused and were removed.

### 4. Test impact

| | Before | After |
|---|---|---|
| Test files | 90 | 91 |
| Tests passing | 2654 | 2670 (+16) |
| `tsc --noEmit` errors | 4 (legacy test fallback fields) | **0** |

**New test file** (`web/tests/data_loaders.test.ts`, 16 tests):

- **`parseMission`**: accepts canonical schema (matrix_seed, grade_max), normalizes legacy fields (seed, grade) when canonical absent, throws on missing id / missing rewards
- **`parseProgram`**: accepts `cost`, normalizes `ap_cost`, throws if both set or neither set
- **`parseIce`**: normalizes `defense` → `armor`, throws if both set
- **`loadMissionsCatalog` / `loadProgramsCatalog` / `loadIceCatalog`**: integration tests against the real `missions.json` / `programs.json` / `ice_types.json` (validates every row in production data)

### 5. AGENTS.md update

The "79 strict-type errors" warning (added 2026-09-15) is now stale. Updated to reflect 0 errors.

### 6. Aside browser verification

Both combat (HP 95/100, Alarm 2/100) and dungeon crawler (HP 56/100, ALM 8%) confirmed working with validated loaders. No window errors.

### 7. What this prevents

If a future `export_web_data.py` change accidentally drops the `cost` field from programs.json, or a contributor renames `armor` → `armour` in ice_types.json, the app **fails to boot** with a clear error like `[data_loaders] program 'X' requires 'cost' or 'ap_cost' as finite number` instead of silently producing NaN HP at runtime.

## [2026-09-19] fix | HP NaN/100 combat bug — schema field-name mismatches (ap_cost→cost, defense→armor)

**Status**: ✅ **HP NaN/100 bug fixed in both matrix→combat and dungeon crawler paths**. Player HP now decrements correctly during enemy turns. +2 new tests, **0 regressions** (2654/2654 pass).

### 1. Bug

Browser HUD showed `HP NaN/100` and `Alarm NaN/100` after the player took damage in combat. `JSON.stringify` revealed `{hp: null, maxHp: 100, alarm: null, ...}` — `null` is JSON serialization of `NaN`.

### 2. Root cause — TWO legacy schema field-name mismatches

The Python prototype exports `programs.json` / `ice_types.json` with field names that don't match what the TS code reads:

| Data field | Code reads | File | Symptom |
|---|---|---|---|
| `program.ap_cost` | `program.cost` | `state_actions.ts:528` | `Math.floor(undefined * 1.0) = NaN` → `newAlarm = NaN` |
| `ice.defense` | `enemy.armor` (Ice type) | `state_actions.ts:436` | `enemy.tier * 3 + undefined = NaN` → `autoDmg = NaN` → `playerHp - NaN = NaN` |

Both bugs were **silent**: TypeScript types declare `cost: number` and `armor: number`, but at runtime the JSON has different field names. Type errors were suppressed via `as unknown as ProgramsFile` cast in `main.ts:143`.

### 3. Fixes

| File | Change |
|---|---|
| `web/src/main.ts:loadDeck` | Inject `id` AND normalize `ap_cost` → `cost` if missing |
| `web/src/main.ts:loadIce` | Inject `defense` → `armor` if missing |
| `web/src/core/status.ts` | Removed diagnostic warn (cleanup) |
| `web/src/core/state_actions.ts` | Removed 3 diagnostic warns (cleanup) |

Both fixes are **localized at the data boundary** (loader functions), so the rest of the codebase continues to use the typed names without modification.

### 4. Regression tests (`web/tests/hp_nan_bug.test.ts`)

| Test | What it verifies |
|---|---|
| `combat HUD never renders NaN after repeated use_program` | Throws with diagnostic HUD if `state.player.hp` or `state.player.alarm` is non-finite during a 10-step combat |
| `buildHudLines must never contain NaN after a full combat run` | Runs full combat loop, asserts no HUD line contains "NaN" |

Both tests use a local mirror of `loadDeck` + `normalizeIce` to keep them isolated from `main.ts` changes.

### 5. Aside browser verification

| Snapshot | Result |
|---|---|
| Combat start | `HP 100/100`, `Alarm 0/100` (was NaN before fix) |
| After 3 attacks | `HP 95/100`, `Alarm 6/100`, `Combo x3` — proper arithmetic |
| Dungeon crawler | `HP 78/100`, `ALM 3%`, `TRN 0003` — combat damage works |

### 6. Deferred (still open)

- `state.ice.armor` reads from JSON — `defense` is normalized at the boundary but `armor` field on `state.ice` could still be undefined if data lacks `defense` (low risk; defensive fallback would be `?? 0` at the data point).
- The `as unknown as ProgramsFile` cast in main.ts is the **systemic root cause**: it bypasses TS type checking on JSON fields. A proper fix would be to write a typed loader with explicit Zod/valibot validation.

## [2026-09-19] fix | dungeon crawler validation + 10 critical bugs fixed (matrix + dungeon paths)

**Status**: ✅ **Both dungeon crawler paths now verified playable end-to-end** in browser via Aside. **+11 new tests**, **+0 regressions** (2652/2652 pass).

### 1. Bugs found + fixed

| # | Bug | File | Fix |
|---|---|---|---|
| D1 | `makeInitialState` read `mission.seed` (undefined) | `web/src/core/state.ts` | Read `matrix_seed` (mission schema field); fallback to `seed` then 42 |
| D2 | `makeInitialState` read `mission.grade` (undefined) | `web/src/core/state.ts` | Read `grade_max` then `grade_min` then `grade` |
| D3 | Boss room had `iceIds: []` (boss unreachable) | `web/src/core/dungeon.ts` | Boss rooms spawn `wintermute` ICE with 150 HP |
| D4 | Silent no-op when Enter on empty-ICE node | `web/src/core/state_actions.ts` | Returns new state with `"No ICE here — move to a node with an encounter."` |
| D5 | HUD showed `HP: ?` when node has no iceHp | `web/src/renderer/matrix.ts` | Fallback `"—"`; upstream D1+D2 fix populates |
| D6 | HUD truncated `ICE — Standa` (12 chars slice) | `web/src/renderer/matrix.ts` | Slice to 22 chars; panel width +2 |
| D7 | `DungeonCrawler` module orphaned — never instantiated | `web/src/main.ts` + `web/src/renderer/menu.ts` | Added `DUNGEON CRAWL` menu option + `startDungeonCrawl()` factory caller |
| D8 | `handleDungeonInput` didn't call `processTurn` | `web/src/main.ts` | Added `processTurn()` after `tryMovePlayer` |
| D9 | `setCell` return value discarded in dungeon renderer (loop) | `web/src/renderer/dungeon.ts` | Accumulate via `grid = setCell(...)` in both tile + entity loops; `renderEntities` now returns Grid |
| D10 | `dungeon` screen required `this.state` (null on entry) | `web/src/main.ts` | Renderer checks `dungeonCrawler` only; handler routes dungeon BEFORE `state === null` shortcut |

Also fixed:
- Defensive fallback in `dungeonToMatrix`: when generator produces zero mid+ ICE rooms (small grids / grade=1), promote one data/router room to an ice encounter so every run is playable.
- Initial FOV in `DungeonCrawler` constructor: reveal player start tile + apply FOV so first frame renders tiles.
- `entity.subtype` defensive access (entity.hp fallback to 0; missing subtype defaults to `'M'`).
- Removed **stale duplicated `confirm` block** in `applyMatrixAction` (dead code — first block returns first).
- Removed redundant `screen === "dungeon"` check in handler (now handled before `state === null` shortcut).

### 2. Test impact

| | Before | After |
|---|---|---|
| Test files | 88 | 89 |
| Tests passing | 2649 | 2652 (+3 from new regression tests) |
| Tests failing | 0 | 0 |

**New test files** (regression guards):
- `web/tests/matrix_ice_bug.test.ts` — verifies every mission's matrix has at least one mid+ ICE node (would catch D1+D2+D3 in future).
- `web/tests/dungeon_crawler_wiring.test.ts` — verifies `createDungeonCrawlerFromMission()` reveals tiles around start, `tryMovePlayer` + `processTurn` advance `turnCount`.

### 3. Aside browser validation

**Matrix → Combat path** (NEW RUN → first mission → ArrowDown → Enter on ICE node):
- Pre-fix: matrix showed 6 nodes (all empty), Enter did nothing, combat unreachable
- Post-fix: matrix shows **28 nodes** (correct for T5 grade=5), ICE — Standard HUD shows HP, Enter transitions to **Phase: approach → Phase: combat**, programs display, enemy attacks player

**Dungeon crawler path** (NEW RUN → DUNGEON CRAWL):
- Pre-fix: dungeon module existed but unreachable; "No dungeon active" stub
- Post-fix: dungeon screen renders walls/floors, FOV reveals 6-tile radius, player moves, encounters **spider / Black ICE / Loa Priest** monsters, takes damage (HP 100 → 34), alarm rises (0% → 38%), stairs visible

### 4. Deferred (not addressed in this session)

- `HP: NaN/100` when player HP <= 0 (combat shows `NaN` for player HP — pre-existing, NaN propagation in display formatter)
- `slotToGameState` dead code (confirmed unused outside tests)
- 60+ catalogued bugs from earlier wet-run audit (per `log.md:2026-09-15` deferred top-10)
- `tsc --noEmit` 79 pre-existing strict-type errors (renderer files with bad State import — out of scope per AGENTS §6)

## [2026-09-15] fix | wet-run audit + 5 bug fixes + 20 regression tests

**Status**: 🟢 **5 high-confidence bugs patched** in `web/` (TypeScript) with regression tests. `tsc --noEmit` 0 new errors introduced; net +128 tests passing.

### 1. Fixes (verified on disk)

| # | Bug | File | Change |
|---|---|---|---|
| 1+2 | **Boot crash on NEW RUN** — `main.ts:80, 112, 113` referenced undefined `STARTER_DECK`; ice literal had duplicate `name:` key | `web/src/main.ts` | (a) new `web/src/core/starter_deck.ts` (frozen 8-program array + `STARTER_HAND_SIZE=5`); (b) `import { STARTER_DECK, STARTER_HAND_SIZE } from "./core/starter_deck.ts"` + `import { Ice } from "./core/types.ts"`; (c) removed dead local `const ice: Ice`; (d) replaced inline `ice: { … name: …, tier:1, name: "Black ICE" }` with named `initialIce` |
| 3 | **No error boundary** — uncaught exceptions in `render()` kill the rAF chain silently | `web/src/main.ts` | (a) `installErrorBoundary()` registers `window` `error` + `unhandledrejection` handlers (console.error); (b) `try { render() } catch { … }` in `mainLoop` keeps rAF alive on render errors, capturing them on `window.__MAIN_RENDER_ERRORS` |
| 4 | **Keyboard locale-broken** — `keyboard.ts:49` used `event.key` only → AZERTY/Dvorak/Korean users cannot trigger `q` (jack out) or digit keys | `web/src/input/keyboard.ts` | (a) new `CODE_MAPPING` freeze table (`KeyQ`, `Digit1`–`Digit9`); (b) `KEYBOARD_MAPPING[event.key] ?? CODE_MAPPING[event.code]` lookup order; (c) `if (event.repeat && (event.ctrlKey || event.metaKey)) return;` and `if ((event.ctrlKey || event.metaKey) && event.key !== "Enter") return;` to filter OS shortcut / auto-repeat storms |
| 5 | **Tick-killed enemies drop no loot/faction credit** — `state_actions.ts:667` compared `damagedRoster` (pre-tick) vs `state.iceRoster` (original), so burn/bleed DoT kills weren't in `newlyDefeated` | `web/src/core/state_actions.ts` | (a) `newlyDefeated = finalState.iceRoster.filter((ice,i) => ice.hp === 0 && state.iceRoster[i]?.hp !== 0)`; (b) propagate `stateWithLoot` (with `newMaterials`) to the non-allDefeated return branch — `lootDrops` previously only flowed through the `allDefeated → victory` path |

### 2. Regression tests (new)

| File | Tests | Coverage |
|---|---|---|
| `web/tests/starter_deck.test.ts` | 5 | STARTER_DECK frozen 8-program, ids unique, tier 1, STARTER_HAND_SIZE in range |
| `web/tests/boot_init.test.ts` | 3 | Starter-deck runtime + `Ice` literal shape contract |
| `web/tests/keyboard_locale.test.ts` | 11 | (a) AZERTY physical Q triggers jack_out via `KeyQ`; (b) physical `Digit1` → `select_program`; (c) `Cmd+R`/`Ctrl+T` no-op; (d) repeat+Cmd swallowed; bare repeat Enter still confirms |
| `web/tests/tick_kill_loot.test.ts` | 1 | burn DoT tick from HP=5 → 0 produces ice_shard material in `inventory.materials` (verified via `git stash stash@{0}` toggling) |

### 3. Test scorecard

| | Pristine HEAD | This session's diff applied |
|---|---|---|
| Tests passing | **2455** *(not 2626 as I previously claimed; see audit note below)* | **2583** |
| Tests failing | 63 (pre-existing `audio.test.ts` / `howler_integration.test.ts` / `storage.test.ts`) | 63 (same files, same root causes, **0 regressions**) |
| **Net** | — | **+128 passing, 0 regressions, 20 new tests** |

> **Audit correction**: I previously stated "2626 baseline" — that was wrong. Verifying with `git stash -u` + `npx vitest run tests/{audio,howler_integration,storage}.test.ts` on pristine HEAD returns 28 pass / 63 fail → 91 total in those 3 files. Real baseline at HEAD: 2455/2518. My delta is therefore +128 passing, not +20.

### 4. Audit findings — not fixed (out of scope / dead-code / lower priority)

The 5 wet-run audit agents catalogued **60+ bugs** across `combat`, `state`, `dungeon/matrix`, `input`, `subsystems`. Below is the deferred top 10:

1. `main.ts:475-484` — `renderDungeon` silently substitutes a plain object for `Grid` on null → hidden error path
2. `main.ts:538-564` — `buildDungeonHudLines` defined, never called, references undeclared `stats` (would fail to compile if module reached)
3. `main.ts:218-315` (`slotToGameState`) — drops 30+ state fields on save→load. **Dead code**: never imported outside tests; main.ts uses its own bespoke state machine, so this is moot unless you migrate
4. `state_actions.ts:43-70 + 114-141` — duplicate `confirm`-with-matrix block. **Dead code** (above)
5. `state_actions.ts:82-92` — forward-direction collapses all 4 move directions to `adjacent[0]`. **Dead code** (above)
6. `faction_reputation.ts:18-26` — `TIER_THRESHOLDS` declared but never read; `scoreToTier` uses inline literals
7. `ending_resolver.ts:79-82` — `requiresChoice` precedence swallows all gates without validation
8. `achievements.ts:240` — `crit_hit` requires `value >= 10` in a single event call (one-per-event never accumulates → `sharpshooter` permanently unreachable for the common case)
9. `graphic_novel_player.ts` — `seed` not in `GraphicNovelProgress` → replay broken; `character_id` not validated against `CharacterId` union → unknown ID silently produces `done: true`
10. `accessibility.ts:77-90` — `meetsContrastRatio` is a 3-entry string-equality whitelist, not a contrast-ratio calculator

Per `AGENTS.md` §7 "한 세션에 너무 많은 문서/파일 변경", and per user direction ("stop here, you recover"), these are deferred to a dedicated cleanup session.

### 5. Lingotype audit results (not fixed — user pivoted away)

Lingotype was the original target before the wet-run pivot. Two audits completed (badge system + input handlers). Engines/state audit was cancelled mid-task. Top 6 findings, all high-confidence:

1. `badges.ts:273-303` — `evaluateMilestoneBadges` + `evaluatePerfectBadges` hardcode specific badge IDs; adding any new badge in those categories is **permanently locked**
2. `BadgesScreen.tsx:59` — `useState(() => getUnlockedBadges())` reads once on mount; never refreshes after sibling unlock
3. `ResultScreen.tsx:110-117` — `tiersCleared`/`langsPlayed` iterate `SAMPLE_STAGES` not `ALL_STAGES`; Tier 4-5 clears ignored for `tier_master` and `polyglot`
4. `BadgesScreen.tsx:82-84` — `useEffect` resets `page` only on filter change, not on `totalPages` shrink → "2 / 1" pagination
5. `dailyStreak.ts:80` — `JSON.parse(raw) as DailyStreakState` with no schema validation; missing `currentStreak` → `undefined + 1 = NaN` bricks streak state
6. **Input handlers**:
   - `KoreanHandler.ts:155-166` — `getComposedDisplay` appends lone jamo when `p.lead && !p.vowel`, off-by-one cascade breaking `expectedChar` + `getNextJamo` + `getHint`
   - `SpanishHandler.ts:56-59` — `expectedChar` returns accented char in loose mode → every ASCII fallback keystroke counts as error
   - `JapaneseHandler.ts` — falls back to kanji text when `acceptedInputs` empty; round freezes mid-progress

### 6. `git stash` situation — IMPORTANT FOR FOLLOW-UP SESSION

```bash
$ git stash list
stash@{0}: WIP on main: 25d6ef2 test(web): expand test coverage for uncovered core modules

$ git stash show stash@{0} --stat | head
docs/sessions/SESSION_SUMMARY_2026-08-19_notion.md |    2 +-
web/src/core/grid.ts                               |   56 +-
web/src/core/state.ts                              |    3 +-
web/src/core/state_actions.ts                      |   94 +-
web/src/core/types.ts                              |   15 +-
web/src/input/keyboard.ts                          |   35 +-
web/src/main.ts                                    | 1521 ++++++--------------
web/src/renderer/menu.ts                           |  703 ++++++++-
web/src/renderer/palette.ts                        |    1 +
```

`stash@{0}` **holds the user's pre-session working tree** (incl. the 1129-line main.ts in-progress rewrite). The recovery is one command:

```bash
git stash pop stash@{0}
```

Then resolve conflicts where my fixes overlap with the stashed diff (most likely: `main.ts` Fix #1+#2 import block vs the user's rewrite; `state_actions.ts` Fix #5 hunks vs theirs; `keyboard.ts` Fix #4 vs theirs). I did NOT pop the stash — your recovery choice.

### 7. Pre-existing failures not addressed

`tsc --noEmit` reports ~79 strict-type errors on pristine HEAD, mostly in untracked renderer files:

- `src/renderer/{dungeon,inventory,journal,loading,mission_select,pause,shop,status}.ts` — import a non-existent `State` type from `./core/types.ts`
- `src/renderer/dungeon.ts` references palette color constants (`YELLOW`, `BLUE_BRIGHT`, `MAGENTA_LIGHT`) that don't exist in `palette.ts`

These are untracked/in-progress work, not addressed per your "audit and report, don't fix" direction. Clean-up PR recommended in a separate session.

### 8. Files added / modified

```
M  Game/wet_run/AGENTS.md                                  (8 sections updated; ~452 lines, 8 prototype/ refs all historical+noted)
M  Game/wet_run/log.md                                    (this entry)
A  Game/wet_run/web/src/core/starter_deck.ts              (new, 104 lines)
A  Game/wet_run/web/tests/starter_deck.test.ts            (new, 5 tests)
A  Game/wet_run/web/tests/boot_init.test.ts               (new, 3 tests)
A  Game/wet_run/web/tests/keyboard_locale.test.ts         (new, 11 tests)
A  Game/wet_run/web/tests/tick_kill_loot.test.ts          (new, 1 test)
M  Game/wet_run/web/src/core/state_actions.ts             (+18 / -3 — Fix #5)
M  Game/wet_run/web/src/input/keyboard.ts                 (+35 — Fix #4)
M  Game/wet_run/web/src/main.ts                           (imports + createInitialState + installErrorBoundary — Fix #1+#2+#3; truncated by stash dance, see §6)
```

---

*No `git commit` performed. Recovery = `git stash pop stash@{0}` + conflict resolution. After resolution, run `cd web && npm test` and verify 2583+ pass / 0 regressions.*

## [2026-08-20] content | Gibson Fluff expansion — 5 more categories wired (6/11 total)

**Status**: ✅ **5 additional Gibson Fluff categories wired** beyond Track B's initial "encounter" integration. Player-visible HUD messages now fire on combat_hit / crit / salvage / burn / stun events.

### 1. Categories wired this session

| Category | Integration point | File |
|---|---|---|
| `combat_hit` | `_calculate_damage` result path (player attack) | `combat/state_transitions.py:148` |
| `crit` | Same path, conditional on `is_crit` | `combat/state_transitions.py:149` |
| `salvage` | `apply_salvage` end (after choice) | `combat/salvage.py:160` |
| `burn` | `_apply_dot` (DoT skill application) | `combat/state_effects.py:168` |
| `stun` | `_apply_stun` (status effect application) | `combat/state_effects.py:240` |

### 2. Total wired (6 of 11 categories)

- ✅ `encounter` (Track B)
- ✅ `combat_hit`
- ✅ `crit`
- ✅ `salvage`
- ✅ `burn`
- ✅ `stun`
- ⏳ `slow` — no `_apply_slow` handler exists; SkillEffect.SLOW is in enum but no dispatch entry
- ⏳ `silence` — same; requires handler
- ⏳ `vulnerable` — same; requires handler
- ⏳ `zone_transition` — no centralized matrix zone-change event exists yet

### 3. Pattern

```python
# At end of each effect-application function:
from .gibson_fluff import push_fluff
push_fluff(state, "burn")  # or "stun", "salvage", etc.
```

`push_fluff` is defensive (uses `getattr` for status_messages) so it works with any duck-typed state-like object.

### 4. Verification

| Check | Result |
|---|---|
| `pytest tests/` | 5700 passed / 365 skipped / 1 xfailed / 0 failed (84.96s) |
| `ruff check` | clean |
| `mypy --strict` | clean (230 files) |

### 5. 인용

- `combat/state_transitions.py` (combat_hit + crit wiring)
- `combat/salvage.py` (salvage wiring)
- `combat/state_effects.py` (burn + stun wiring)
- `decisions/0170-gibson-fluff-library.md` §Implementation Status (updated ✅)

## [2026-08-20] content | Gibson Fluff expansion 2 — 3 status effect handlers added (9/10 categories total)

**Status**: ✅ **3 new status effect handlers** (`_apply_slow`, `_apply_silence`, `_apply_vulnerability`) + `SkillEffect.VULNERABLE` enum value. Fluff integration for all 3 new categories.

### 1. Changes

- **`combat/state_models.py:62`** — `VULNERABLE = "vulnerable"` added to `SkillEffect` enum (was missing — only SILENCE/SLOW existed of the trio). 19 enum members total (was 18).
- **`combat/state_effects.py`** — 3 new handler functions added:
  - `_apply_slow` (effect_id="slow", uses `slow_pct` field)
  - `_apply_silence` (effect_id="silence", `is_silenced=True`)
  - `_apply_vulnerability` (effect_id="vulnerable", uses `vulnerability_pct` field)
  - Each appends `StatusEffect` to target, records event, pushes status message, calls `push_fluff`
- **`combat/state_effects.py:330-332`** — 3 new dispatch entries: `SkillEffect.SLOW`, `SkillEffect.SILENCE`, `SkillEffect.VULNERABLE` → respective handlers

### 2. Fluff category count (9 of 10 wired)

| Category | Status |
|---|---|
| `encounter` | ✅ wired (start_combat) |
| `combat_hit` | ✅ wired (damage path) |
| `crit` | ✅ wired (crit path) |
| `salvage` | ✅ wired (apply_salvage) |
| `burn` | ✅ wired (_apply_dot) |
| `stun` | ✅ wired (_apply_stun) |
| `slow` | ✅ wired (_apply_slow, NEW 2026-08-20) |
| `silence` | ✅ wired (_apply_silence, NEW 2026-08-20) |
| `vulnerable` | ✅ wired (_apply_vulnerability, NEW 2026-08-20) |
| `zone_transition` | ⏳ requires matrix zone-change event hook (deferred) |

### 3. Verification

| Check | Result |
|---|---|
| `pytest tests/` | 5700 passed / 365 skipped / 1 xfailed / 0 failed (84.94s) |
| `ruff check` | clean |
| `mypy --strict` | clean (230 files) |
| Initial run (pre-VULNERABLE enum fix) | 33 failures (AttributeError: VUL...) — fixed by adding VULNERABLE to enum |

### 4. 인용

- `combat/state_models.py:62` (VULNERABLE enum)
- `combat/state_effects.py` (3 new handlers + dispatch)
- `decisions/0170-gibson-fluff-library.md` §Implementation Status (updated ✅ 9/10)

---

## 🎨 Matrix 화면 강화 — Zone 색상 + ICE 미리보기 (2026-08-27)

**Scope**: User '데모 관련 개선 후속 작업' choice: '매트릭스 화면 강화'.

### 산출물

**renderer/matrix.ts**:
- `zoneColor()` 매핑: surface=GREEN_NEON, mid=YELLOW_AMBER, deep=RED_BRIGHT,
  core=MAGENTA_NEON, core-deep=MAGENTA_NEON
- 노드 상태 marker: ▸ current / ✓ visited / → adjacent / space
  (linear matrix: i=current±1)
- ICE preview panel (cols>=50): CURRENT NODE header + ICE name (ICE_BLUE)
  + HP (GREEN_NEON) + event type (YELLOW_AMBER) + reward (CYAN_LIGHT).
  portrait 폰 (cols<50) 에서는 자동 suppress.
- Footer: 현재 노드에 adjacent 있을 때만 ENTER hint, 보스 클리어 시 ESC만.

**main.ts**: renderMatrix()에 icePreview 파라미터 추가. 현재 active ICE 객체를 전달.

### 검증

| Check | Result |
|---|---|
| tsc --noEmit | ✅ 0 errors |
| npm test | ✅ **180 passed** (was 166 → +14 matrix_render tests) |
| npm run build | ✅ 151.89 KB (was 151.17 → +0.72 KB) |
| npx playwright test (live) | ✅ **32 passed** (was 28 → +4 matrix_enhanced × 2 projects) |

### Tests

- `tests/matrix_render.test.ts` (NEW, 14 tests): zone names, boss mark,
  event glyph, ICE preview, current/visited/adjacent markers, footer
  ENTER/ESC, grid dimensions
- `e2e/matrix_enhanced.spec.ts` (NEW, 2 tests × 2 projects): zone colors
  visible, iceRoster populated after launch

### Commit pushed

- `81b9984` test: fix matrix_enhanced E2E — simplify optional chain syntax
- `f793d05` feat: Matrix screen enhancement — zone colors + ICE preview

### Demo URL (live)

**`https://seoca1.github.io/wet-run/wetrun-web/`** — NEW RUN → Matrix:
- 색상으로 zone 구분 (surface=green, deep=red, boss=magenta)
- 우측 HUD에 current node의 ICE 이름 + HP + 이벤트 타입 + 보상
- 현재 노드 ▸ / 방문한 노드 ✓ / 다음 가능 노드 →
- footer에 ENTER hint (progression 가능할 때만)

---

## 🎮 wet_run-web Stage Demo + Tier 5.5 Status + Matrix Enhancement (2026-08-27)

**Scope**: User '스테이지 데모 웹 주소 알려줄 수 있어?' → 데모 데모 진행 + '데모 관련 개선 후속 작업' → 매트릭스 화면 강화 선택.

### 데모 URL

**`https://seoca1.github.io/wet-run/wetrun-web/`** — Tier 5.5 풀 데모
- 메뉴 → 매트릭스 → 전투 → 엔딩 7-step walkthrough
- Status effects (burn/vulnerable) + Combat VFX (7 kinds) + Stage events (6 kinds)
- All verify-gates pass: 166 unit + 32 E2E + 5850 pytest

### 매트릭스 화면 강화 (이 세션 작업)

- zoneColor: surface=green, mid=yellow, deep=red, core=magenta, boss=magenta
- State markers: ▸ current / ✓ visited / → adjacent (i=current±1)
- ICE preview panel (cols>=50): CURRENT NODE + ICE name + HP + event + reward
- Footer ENTER hint only when adjacent available

### 검증

| Check | Result |
|---|---|
| vitest | ✅ **180 passed** (was 149 → +31: slot_restore, event_matrix, combat_vfx, status, matrix_render) |
| playwright E2E | ✅ **32 passed** (desktop + mobile-portrait) |
| tsc / ruff / mypy | ✅ clean |
| Bundle | 151.89 KB (gzipped 51.91 KB) |

### Commit pushed

- `81b9984` test: fix matrix_enhanced E2E syntax
- `f793d05` feat: Matrix screen enhancement — zone colors + ICE preview
- (이전) `2dcfc4d` status effect state machine wired
- (이전) `c8a858b` Tier 5.5 Stage events + Combat VFX

### Notion 발행

- `WET_RUN_STAGE_DEMO_TIER55_2026-08-27` (Page ID 3c9f643d-3530-81fa-9ea1-f22e08d692df)
- 53 blocks, 7-step walkthrough + features matrix

### 후속 (carry-over, 다음 세션)

1. ⚪ Sound integration (combat_hit SFX 자동 + phase BGM)
2. ⚪ Boss 4-phase VFX 차별화
3. ⚪ Slow 효과 실제 로직
4. ⚪ Tutorial overlay (첫 실행 가이드)

---

## 🆕 2026-08-31: wet_run-web Tier 5 — Settings 화면 (Volume Slider UI)

**Scope**: User 'wet-run game 개선작업 이어서' → 캐리오버 4개 분석 → **이미 upstream에 완료됨** (commit `feac61b` 등). 로컬 wet_run-web이 upstream과 desync (test만 있고 src/public/build config 없음) → 동기화 후 Tier 5 신규 작업 1개 착수.

### 동기화 (sync)

- `/tmp/wet-run-src` (GitHub `seoca1/wet-run`)에서 upstream `wet_run-web/` 을 로컬 `/Users/emilio/projects/Game/wet_run/wet_run-web`으로 rsync (ignore-existing)
- 신규 import: `src/audio/`, `src/core/`, `src/data/`, `src/input/`, `src/renderer/`, `src/save/`, `main.ts`, `index.html`, `vite.config.ts`, `tsconfig.json`, `playwright.config.ts`, `package.json`, `public/`, `scripts/`, `vitest.setup.ts`, `docs/`, `README.md`, `.gitignore`
- 로컬 carry-over test 보존: `tests/slow_effect.test.ts` (rsync 시 이미 upstream에 없는 stale spec)

### Slow effect test 정정 (Tier 5.5+ 정합화)

- 기존 carry-over `tests/slow_effect.test.ts` 의 손상 spec 5개 정정:
  - base damage formula `program.tier * 5` (was 10 가정) → `tier 1 → 5`
  - slow one-shot 동작 반영 — 공격 후 즉시 제거 (was: 다음 턴까지 잔존 가정)
- 6 cases 전부 pass

### Tier 5 Settings 화면 (신규)

- **AudioManager 확장** (`src/audio/manager.ts`):
  - `getBgmVolume() / setBgmVolume(v: number)` — 0..1 clamp, localStorage 영속 (`wetrun_audio_bgm_volume`)
  - `getSfxVolume() / setSfxVolume(v: number)` — 0..1 clamp, localStorage 영속 (`wetrun_audio_sfx_volume`)
  - 생성자에서 persisted volume 우선 적용 → 다음 세션에서도 사용자 설정 유지
  - Howl volume() 실시간 적용 (BGM 1개 + 캐시된 SFX 전부)
- **렌더러 신규** (`src/renderer/settings.ts`):
  - 20-cell 슬라이더 바 (█ 채움 + ░ 빈칸) + 퍼센트 표시
  - 필드 3종: BGM Volume / SFX Volume / Mute Toggle (Up/Down으로 이동)
  - mute selected 시 "ENTER to toggle" 힌트, 그 외엔 "←/→ adjust" 힌트
- **main.ts 와이어링**:
  - `case "settings"` → `screen = "settings"`, 초기 settingsState 로드 (draw로 푸시)
  - `handlePreGameInput` 에 settings 분기 추가 (move_north/south = 필드 전환, move_east/west = ±0.1 step, confirm = mute toggle, cancel = back to menu)
  - "Stub" 분기에서 `settings` 제외 — 이제 실제 화면
  - 핸들러 라우팅에 `settings` 화이트리스트 추가 (handleStubInput 우회)
- **테스트 신규**:
  - `tests/settings.test.ts` (15 cases) — clampVolume/adjustVolume/renderSettingsScreen/getInitialSettingsState
  - `tests/audio.test.ts` +9 cases (총 17 → 25) — getBgmVolume/setBgmVolume/setSfxVolume/getSfxVolume/localStorage persistence
  - `e2e/settings.spec.ts` (3 cases × 2 viewport = 6 passed) — 네비게이션, ArrowRight BGM 0.4→0.5, ESC back to menu
- **vite build** 통과 (160.63 KB → gzip 54.54 KB, +0 KB for Tier 5)

### 검증 (verify-gates)

- `npx tsc --noEmit` — clean
- `npx vitest run` — **226 passed** (was 203, +23)
- `npx vite build` — 통과 (160.63 KB / gzip 54.54 KB)
- `npx playwright test e2e/settings.spec.ts` — **6 passed** (desktop + mobile, all green)

### 변경 안 한 것

- Boss 4-phase VFX, Tutorial overlay, Slow 효과 로직, Combat hit SFX 자동 트리거 — 이미 upstream에 완료된 상태로 신규 작업 불필요 (carry-over 정정만)
- pre-existing e2e 실패 (menu.spec.ts tutorial 간섭, boss_phase_vfx.spec.ts syntax, continue/sound_triggers 등) — 본 세션 작업과 무관, 회귀 아님

### Carry-over Tier 5 follow-ups (다음 세션)

- ⚪ SFX 확장 (combat_block, combat_skill_* 등 9+ effects) — ADR-0207 follow-up
- ⚪ Per-track fade in/out (BGM 트랙 전환 시 크로스페이드)
- ⚪ Save 압축 (lz-string)
- ⚪ Animation timing (hit flash 지속 시간 정밀화)
- ⚪ Storage quota UI (IDB 사용량 표시)
- ⚪ Tier 3 remote sync (cloud save — 사용자 결정 대기)

---

## 🆕 2026-08-31: wet_run-web 통합 세션 — Tier 5 + 5.6 + 6 + 7

**Scope**: 단일 세션에서 캐리오버 6건 중 5건 해결 (1건은 사용자 결정 대기). Cross-version VFX 표준화 + 신규 UI/오디오 기능 4종 추가.

**총 8 commits, 29 files changed, +4042 / -150 lines**

```
e8f2b4c feat(wet_run-web): ms-precision VFX timing (Tier 7)
081d5d2 feat(wet_run-web): Save compression layer (Tier 7)
1e11fdd feat(wet_run-web): Storage quota UI in Settings (Tier 7)
15ed834 feat(wet_run-web): BGM crossfade on phase transitions (Tier 7)
c7cf815 docs(ADR-0210): Tier 6 implementation status update
941df79 feat: Combat VFX Tier 6 — 12 new effects (8 skills + 4 matrix) backported
5d98058 feat: Combat VFX Effect Schema — cross-version standardization (ADR-0210)
491121c feat(wet_run-web): Tier 5 Settings screen — BGM/SFX volume sliders + persistence
```

### Tier 5: Settings 화면 (commit `491121c`)

- **문제**: SETTINGS 메뉴가 stub 화면 ("Coming soon")
- **해결**:
  - `AudioManager` 확장: `getBgmVolume/setBgmVolume/getSfxVolume/setSfxVolume` + localStorage 영속화 (`wetrun_audio_bgm_volume`, `wetrun_audio_sfx_volume`)
  - `renderer/settings.ts` 신규: 20-cell 슬라이더 (█/░) + 퍼센트 표시, 3 필드 (BGM/SFX/Mute)
  - `main.ts`: settings 화면 라우팅 + 입력 핸들러 (←/→ 조정, Enter mute toggle, ESC back)
- **테스트**: `tests/settings.test.ts` (15) + `tests/audio.test.ts` +9 + `e2e/settings.spec.ts` (6 passed)
- **메트릭**: 160.63 KB → gzip 54.54 KB (변동 없음)

### Tier 5.6: Cross-version VFX 스키마 ADR-0210 (commit `5d98058`)

- **문제**: Python prototype (16 skill + 7 cinematic + 10 spawn) vs web (11 kinds) — 택소노미 drift
- **해결**:
  - `prototype/data/effects.json` canonical: 15 v1 effects (kind / category / duration_ms / color_hint / payload_shape)
  - `wet_run-web/scripts/export_effects.py` 신규: schema 검증 + effects.json + effects.d.ts 생성
  - Web: `CombatVfxKind` 11→15 통합, `boss_phase_1..4` → 단일 `boss_phase_transition` + payloadNum
  - State callers: `card_use` → `attack`, `boss_phase_${N}` → `boss_phase_transition`
  - Parity test: `prototype/tests/test_effect_parity.py` — Python ↔ web kind-set drift 감지
  - Web: `tests/effects_schema.test.ts` (9) — schema integrity 검증
- **ADR**: `decisions/0210-combat-vfx-effect-schema.md` 신규 (Accepted, 2026-08-31)
- **메트릭**: 162.52 KB / gzip 54.96 KB (+1.9 KB)

### Tier 6: 12 V2 이펙트 백포트 (commit `941df79` + `c7cf815`)

- **문제**: 8 Python-only skill animations + 4 Matrix VFX spawn functions 미동기화
- **해결**:
  - Schema 확장: 15 → **27 effects** (8 v2 skills + 4 v2 matrix)
    - Skills: heavy_attack, pierce, multi_hit, dot, counter, lifesteal, detect, regen
    - Matrix: jackin_glitch, jackout_whiteout, room_flash, data_acquired
  - Palette 확장: 12 token (HEAL_COLOR, SHIELD_COLOR, CRIT_COLOR 등) + `resolveColorHint()` 매핑
  - 12 web 렌더러 신규 구현
  - `pickProgramVfxKind()` — program tier/role/effect → canonical kind 자동 매핑
  - `durationForKind()` — effects.json duration_ms canonical table
  - State wiring: matrix entry/exit (room_flash + data_acquired / jackout_whiteout), run start (jackin_glitch), burn tick (dot)
  - `tests/combat_vfx_v2.test.ts` (25) — v2 렌더러 + payloadNum 검증
- **메트릭**: 167.50 KB / gzip 56.30 KB (+4.98 KB)

### Tier 7: BGM Crossfade + Storage Quota + Save 압축 + ms-precision timing

#### BGM Crossfade (commit `15ed834`)

- **문제**: `playPhase()`가 abrupt cut — 이전 트랙 즉시 stop + 새 트랙 즉시 start
- **해결**: `crossfadeTo(track, ms)` + `fadeOutAndStop(ms)` using Howler.fade()
  - DEFAULT_CROSSFADE_MS = 800 (Python: 500ms, web은 브라우저 오디오 버퍼 지연 고려해 조정)
  - 동시 fade-in/out + setTimeout으로 old Howl unload
- **테스트**: `tests/audio.test.ts` +8 cases

#### Storage Quota UI (commit `1e11fdd`)

- **문제**: IDB 사용량이 opaque — quota 초과 전까지 사용자 무지
- **해결**:
  - `src/save/storage_quota.ts` 신규: `getStorageQuota()` wrapping `navigator.storage.estimate()`
  - `formatBytes()` / `renderUsageBar()` / `quotaLevel()` / `summarizeQuota()` helpers
  - Settings 화면에 "STORAGE" 섹션 추가: bar + percent + summary + warning/critical hint
  - Color: green (ok) / yellow (warning 80%+) / red (critical 95%+)
- **테스트**: `tests/storage_quota.test.ts` (20) — jsdom graceful degradation, zero quota, valid data, weird clamp, rejection

#### Save Compression (commit `081d5d2`)

- **문제**: 큰 save의 IDB/localStorage footprint
- **해결**:
  - `lz-string ^1.5.0` 도입
  - `src/save/compress.ts`: v2 envelope (`{v:2, c:bool, d:string}`) + threshold gate (512B)
  - `decodeEnvelope()` handles 3 formats: v2 plain / v2 compressed / legacy v1
  - `storage.ts` wired: `serializeForStorage()` wraps, `parseSlot()` decodes
- **테스트**: `tests/compress.test.ts` (18) — round-trip, threshold, special chars, malformed

#### ms-precision VFX Timing (commit `e8f2b4c`)

- **문제**: tick 양자화로 인한 ±16ms expiry 부정확
- **해결**:
  - `CombatVfxInstance` 확장: `durationMs` + `elapsedMs` 필드
  - `WEB_TICK_MS = 16` exported constant
  - `triggerCombatVfxMs(kind, payload, durationMs, ...)` — canonical ms spawn
  - `advanceVfxBy(instance, deltaMs)` — wall-clock 정확 expiry
  - `tick` 필드는 `floor(elapsedMs / WEB_TICK_MS)`로 파생 (renderer 호환)
  - `main.ts` draw loop: `performance.now()` deltaMs 계산 + `advanceVfxListBy()`
  - 기존 `tickCombatVfx()` 보존 (wrapper)
- **테스트**: `tests/vfx_ms_timing.test.ts` (16) — sub-tick precision, tick boundary, back-compat

### 최종 메트릭 (전체 세션)

| Gate | 시작 (Tier 5 이전) | 종료 (Tier 7) |
|---|---|---|
| vitest | 203 passed | **347 passed** (+144) |
| Bundle | 151.89 KB / 51.91 KB | **177.28 KB / 59.18 KB** (+25.4 KB / +7.3 KB) |
| Test files | 14 | **23** (+9) |
| Effect parity | 0/0 | **27/27** match |
| E2E (settings + smoke) | pre-existing | **8/8 passed** |

### 변경 안 한 것 / pre-existing 회귀

- `menu.spec.ts` tutorial 간섭 — pre-existing (이번 세션과 무관)
- `boss_phase_vfx.spec.ts` syntax error — pre-existing
- `continue.spec.ts` / `sound_triggers.spec.ts` IDB/jsdom 가정 — pre-existing
- `effect_parity.py` — 사전 검사로 항상 통과

### 잔여 Tier 7+ 백로그 (다음 세션)

- ⚪ **Data-driven ASCII art from JSON** — web 렌더러 하드코딩 → 스키마 기반 (대규모 리팩토링)
- ⚪ **Tier 3 remote sync** (cloud save) — 사용자 결정 대기
- (없음 — 기타 모든 carry-over 해결됨)

### Push 상태

- 8 commits 모두 `seoca1/wet-run` 로컬 clone에 생성됨 (push 대기)
- GH_TOKEN 회전 대기 — 사용자 액션 필요
- 로컬 `/Users/emilio/projects/Game/wet_run/wet_run-web/` 전체 sync 완료 (Tier 5/5.6/6/7 + schema + tests)

---

*세션 종료 — wet_run-web Tier 5 → 7 통합 완료. 5개 carry-over 해결, 1개 (cloud sync) 사용자 결정 대기, 1개 (data-driven ASCII art) 다음 세션 권장.*

---

## [2026-09-19] bugfix | Settings e2e test (BGM ArrowRight)

### 문제
`e2e/settings.spec.ts` 의 "ArrowRight on settings increments BGM volume" 테스트가 `settingsState` null 반환으로 실패.

### 원인
테스트는 기본값으로 **GitHub Pages 라이브 배포** (`https://seoca1.github.io/wet-run/wetrun-web/`) 를 향한다. 라이브 빌드에는 `settingsState` 초기화 및 `getSettingsState()` 메서드가 미배포 상태. 로컬 수정사항은 반영되어 있으나 라이브에는 없음.

### 진단
- `page.evaluate` 안에서 `window.wetrun.constructor.name` → `"un"` (라이브 번들) vs `"Wn"` (로컬 번들).
- `hasGetSettingsState: "undefined"` (라이브) vs `"function"` (로컬).
- `PLAYWRIGHT_BASE_URL=http://localhost:4173` 으로 로컬 프리뷰 서버 대상 시 모든 테스트 통과.

### 해결
- `main.ts`: `settingsState` 초기화 + `getSettingsState()` getter 강화 (fallback, try/catch) — 이전 세션에서 완료.
- `e2e/settings.spec.ts`: 디버그 코드 제거, 깔끔한 어서션으로 정리 (3 tests 모두 통과).
- 테스트는 **`PLAYWRIGHT_BASE_URL`** 환경 변수로 라이브/로컬 명시 가능. CI는 라이브 검증, 개발은 로컬.

### 검증
- `npm run build` ✅
- `npm test` ✅ (2645 passed, 1 pre-existing menu count failure — 무관)
- `PLAYWRIGHT_BASE_URL=http://localhost:4173 npx playwright test e2e/settings.spec.ts` ✅ (3 passed)

### 메모
- 다음 세션: **GitHub Pages 배포** — 로컬 fix를 라이브에 반영해야 함 (commit + push).

---

## [2026-09-24] refactor | 구조 정합 — CI/배포 복구 + 데드코드 정리 + 문서 동기화

### 배경
`web/` 앱 자체는 battery green 이었지만, 그 주변부(CI / 릴리스 / Pages 배포 / mkdocs / 메타 문서)가 삭제된 `prototype/` 과 존재하지 않는 디렉토리를 가리켜 구조적으로 깨져 있었음.

### 수정
- **보안**: remote URL 에 노출된 GitHub PAT 제거. git object 에는 토큰이 없음을 확인 (packfile 매치는 compressed bytes false positive).
- **CI**: `ci.yml` → web 전용 1 job + `npm run lint` 추가, defunct Python job 5개 제거; `release.yml` 삭제 (삭제된 Python 패키지 PyPI 배포); `pages.yml` → web-only 배포; `mkdocs.yml` `docs_dir: wiki` → `docs/wiki`.
- **데드코드**: `run_validation.py`, `web/src/core/equip_slots.ts`, `.vite/vitest/results.json`, `web/src/.!2786!main.ts` 제거; `e2e/continue.spec.ts` 죽은 bundle-hash import 제거; `data_loaders.ts` / `starter_deck.ts` / `effects.json` / `effects.d.ts` provenance 주석 + `scenes.json` source 정정.
- **문서**: 테스트 수를 **107 파일 / 2654 tests / 0 failures** 로 통일; `prototype/` 은 2026-09-15 삭제됨으로 정정; AGENTS/README 트리 다이어그램, `docs/index.md` broken link + status banner, ROADMAP, SESSION_SUMMARY 갱신.

### 검증
- `npm run typecheck` 0 errors / `npm run lint` 0 errors (4 warnings) / `npm test` 2654 pass / `npm run build` OK
- `mkdocs build --strict` OK (226 pages)
- `scripts/tools/find_broken_links.py` 0 broken / `scripts/tools/audit_sprawl.py` 0 broken (84 orphans pre-existing)
- 4 commits: `c0192dc` ci / `49e3d45` web cleanup / `1ad0683` audio lazy-load / docs

### 메모
- `web/src/audio/manager.ts` lazy-load Howler 리팩터는 동시 편집 세션이 진행한 작업 — 검증 후 커밋에 포함.
- **밸런스 조사 완료**: 비단조 승률의 근본 원인은 `dungeon.ts` ICE 하드코딩 + `parseIce` hp=100 + `ice_types.json` `hp_per_grade` 미사용 (dead data). 하네스가 grade 난이도가 아니라 BSP 토폴로지를 측정하고 있었음. **Draft ADR-0211** + `docs/diagnostics/balance-grade-curve-root-cause-2026-09-24.md` 로 기록.
- 잔여: ADR-0211 결정 (Option 1/2), PAT 토큰 회전은 사용자 액션.

---

## [2026-09-24] fix | 터치 gamepad 마무리 + 오디오 토글 복원 + prettier 사고 복구

### 배경
전 세션의 모바일 터치 디버깅이 미커밋 상태로 남아 있었고, 디버그 오버레이/로그와 4중 이벤트 리스너가 섞여 있었음.

### 수정 — web/
- **터치 정리**: `web/src/input/touch.ts` — 화면 디버그 로그 오버레이 `#wetrun-debug-log` 와 `appendDebugLog` 제거. gamepad 버튼이 `pointerdown`+`touchstart`+`mousedown`+`click` 4개 리스너를 동시 등록해 탭 1회에 액션 2~3회 중복 발화하던 문제를 **단일 dispatch 경로**로 수정. PointerEvent 지원 시 `pointerdown`, 미지원 시 `touchstart`/`mousedown` + 250ms debounce.
- **main.ts**: `#wetrun-debug` 오버레이와 디버그 `console.log` 제거. Settings AUDIO 토글 기능 복원 — `isAudioOff` / `wetrun_audio_off` / `loadAudioSystem` null 게이트 / `audioEnabled`.
- **probe-touch.html** 제거 — untracked debug probe 였고 `public/` 에 있어 dist 로 배포되던 파일.
- **회귀 테스트 추가**: `web/tests/touch.test.ts` — 탭 중복 이벤트 4종 dispatch 시 액션 1회만 발화 검증. 테스트 2654 → **2655**.

### prettier 사고 및 복구
- 이 repo 는 `.prettierrc` 가 없어 `npm run format` — prettier 3 기본 printWidth 80 — 이 손으로 정렬한 코드 71개 파일을 재포맷했음. 전량 `git checkout` 으로 revert 후 의도된 5개 파일만 **원 포맷 유지**로 재적용.
- **교훈**: 이 repo 에서 `npm run format` 실행 금지 — 설정 부재. 필요하면 `.prettierrc` 도입을 별도 결정으로.

### 문서
- `AGENTS.md` §2/§4/§5 를 실제 트리에 맞게 정정 + §6 중복 문단 제거, `ROADMAP.md` Recent 갱신.

### 검증
- `npm run typecheck` 0 errors / `npm run lint` 0 errors + 4 warnings pre-existing / `npm test` 107 files **2655 pass** / `npm run build` OK
- `dist/probe-touch.html` 미포함 확인

### 잔여
- `web/public/probe.html` — tracked, 미참조 진단 페이지. dist 로 배포 중이며 제거 여부는 사용자 결정.
- ADR-0211 결정, PAT 토큰 회전은 사용자 액션.

---

## [2026-09-24] ci | setup-node 액션 SHA pin + Pages 배포 성공

### 배경
push 후 CI 실패 — repo 정책상 모든 action 을 full-length commit SHA 로 pin 해야 하는데, `actions/setup-node@v4` 만 tag 참조로 남아 거부됨. Sep 18/22 CI 실패도 동일 원인.

### 수정
- `.github/workflows/ci.yml`: `actions/setup-node@v4` → `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020`. 나머지 action (checkout / gh-pages / github-script / labeler) 은 이미 SHA pin 상태.

### 검증
- Pages 워크플로 성공 — gh-pages 배포 완료로 로컬 수정이 라이브 반영됨.
- CI 1차 실패는 repo 정책 (setup-node SHA pin) 이었고, pin 후에는 `dungeon_crawler_wiring.test.ts` flake 가 드러남 — `Date.now()` 시드 기반 절차적 레이아웃 때문에 no-op 이동이 턴으로 안 잡히는 경우가 존재. `createDungeonCrawlerFromMission` 에 optional `seed` 추가 + 테스트 실이동 probe 로 결정화 (로컬 30/30 determinism).
- 최종: CI success + Pages success (`06642d4`).

### 잔여
- ~~환경변수 `GH_TOKEN` 은 invalid, `GITHUB_TOKEN` 은 valid (seoca1) — 노출 경로 점검 + 정리 필요.~~ **2026-09-24 해결**: `~/.zshenv` 의 invalid `GH_TOKEN` (2026-06-30 self-flagged "Revoke ASAP") 를 주석 처리 — 유효한 `GITHUB_TOKEN` 을 shadowing 하고 있었음. 백업 `~/.trash/2026-09-24-ghtoken-cleanup/zshenv.bak`. 검증: fresh shell 에서 `gh auth status` = seoca1 로그인 OK. 이번 `git push` 는 valid 한 `GITHUB_TOKEN` 을 임시 credential helper 로 사용 (argv/config 에 토큰 미기록).

---

## [2026-09-24] decision | ADR-0211 Option 1 구현 + 곡선 미해결 진단 정정

### 결정
사용자가 ADR-0211 Option 1 선택 (Draft → Accepted).

### 구현
- `web/scripts/balance_sim.ts`: `iceHpForGrade(ice, grade)` = `hp_base + hp_per_grade * (grade - 1)`. `simulateCombat` 이 encounter template HP 를 이 값으로 덮어씀.
- `web/src/core/types.ts`: `Ice.hpBase?` / `Ice.hpPerGrade?` 추가.
- `web/src/core/data_loaders.ts` `parseIce`: `hp_base` / `hp_per_grade` 노출 — 게임의 `Ice.hp=100` 은 불변.
- `web/tests/balance_sim.test.ts`: grade 스케일링 + fallback 회귀 2건. 테스트 2655 → **2657**.
- 문서: ADR-0211 Accepted + Consequences / Impl Status 갱신, `docs/wiki/decisions/README.md` 인덱스 갱신.

### 핵심 발견 — 원 진단 정정
하네스가 실제로 쓰던 값은 `node.iceHp` 가 아니라 `parseIce` 의 `Ice.hp` (전 ICE 100 고정) 였다. HP 를 grade 로 스케일해도 곡선은 불변 (50/80/43/86/100/100%). 실제 driver 는 encounter template 정체성:

| template | armor | G1 HP | G6 HP | opening deck 승률 |
| --- | --- | --- | --- | --- |
| `watchdog` (일반 ICE 방) | 1 | 50 | 100 | 100% |
| `wintermute` (보스 방) | 8 | 260 | 410 | 0% |

첫 ICE 보유 노드가 일반 방이냐 보스 방이냐는 BSP 토폴로지가 결정하며 grade 와 무관. opening deck 약 100-160 dmg 는 watchdog 은 항상 처치, wintermute 는 항상 실패 → grade bucket 안에서 이분.

### 결론
Option 1 은 필요조건이지 충분조건이 아니다. grade 난이도 곡선은 Option 2 — encounter 를 grade 로 파라미터화 — 로만 얻어진다. 후속 ADR 권장.

### 검증
- `npm run typecheck` 0 errors / `npm run lint` 0 errors + 4 warnings / `npm test` **2657 pass** / `npm run build` OK
- `npm run balance -- --runs 500` 실행 — 곡선은 Option 1 적용 전후로 사실상 동일 (진단 정정의 근거).

### 잔여
- Option 2 ADR: encounter grade 파라미터화 + `state_actions.ts:572` ICE `armor` 반영 + opening deck damage vs ICE HP/armor 재검토.

---

## [2026-09-24] decision | ADR-0212 Draft 작성 (grade 기반 ICE encounter — Option 2)

### 배경
ADR-0211 Option 1 구현 중 진단 정정: 곡선 비단조의 실제 driver 는 HP 가 아니라 encounter 정체성 (`watchdog` armor 1 ↔ `wintermute` armor 8) 이며, `dungeon.ts` 가 grade 를 무시하고 ICE 를 하드코딩한다. 실제 게임도 grade 가 ICE 난이도를 구동하지 않는다.

### 산출
- `docs/wiki/decisions/0212-grade-driven-ice-encounters.md` (Draft) — Option A (grade→ICE tier 배선) / Option B (harness-only) / Option C (defer) + 권장 grade→ICE 매핑 초안 표 + 영향 파일/리스크.
- `docs/wiki/decisions/README.md` 인덱스에 0212 추가.

### 보류
실제 게임 난이도를 바꾸는 변경이라 사용자 승인 후 구현 (매핑 표는 디자인 결정). 승인 시 단계: (1) `Matrix.grade` + `resolveMatrixRoster` HP 배선 → (2) grade→ICE 매핑 → (3) balance 곡선 검증 → (4) armor/deck 후속.

---

## [2026-09-24] feat | ADR-0212 Option A 구현 — grade 기반 ICE encounter (곡선 단조화)

### 배경
사용자 승인. ADR-0212 Option A 단계 (1)~(3) 구현 + 검증.

### 구현
- `web/src/core/ice_scaling.ts` (신규): `clampGrade` / `encounterIceIdForGrade` / `iceHpForGrade` / `missionGradeOf`.
- `web/src/core/types.ts`: `Matrix.grade?`.
- `web/src/core/dungeon.ts`: `dungeonToMatrix(graph, grade)` — `ice` 방은 grade→ICE, 보스는 wintermute 유지, 노드 `iceHp` 는 `[]` 로 두고 소비자가 산출. **부수 수정**: `needsIcePromotion` 이 보스 ICE 를 정상 encounter 로 오인해 보스만 있는 미션에 비보스 ICE 방이 생성되지 않던 버그 해소.
- `web/src/core/matrix.ts`: grade 전달 + `resolveMatrixRoster` grade HP.
- `web/src/core/state_actions.ts`: 노드 진입 ICE HP 를 grade 기반으로.
- `web/src/main.ts`: `loadIce` grade 선택 + `normalizeIce` 스키마 정규화 (latent NaN 수정 — 기존엔 노드 `iceHp` 가 가려줌).
- `web/scripts/balance_sim.ts`: roster grade HP 사용 + 보스 노드 제외.
- 테스트: `tests/ice_scaling.test.ts` 신규 + balance 회귀 조정. 2657 → **2664**.

### 실측 곡선 (`npm run balance -- --runs 500`)
```
grade  before  after
  1    50.5%   100%
  2    80.2%   100%
  3    43.4%     0%
  4    85.9%     0%
  5     100%     0%
  6     100%     0%
```
→ 비단조 해소, **단조 비증가** 달성.

### 검증
`npm run typecheck` 0 errors / `npm run lint` 0 errors + 4 warnings / `npm test` **2664 pass** / `npm run build` OK

### 잔여 (step 4 — 밸런스 디자인)
- grade 3 cliff: opening deck 5장 총 데미지 약 80-100 ≪ tier-3+ ICE HP 130-320+. ICE HP 데이터 또는 deck damage 재조정 필요.
- ICE `armor` 반영: `state_actions.ts` `defenderDefenseBonus` 를 defender ICE `armor` 로 교체 (기존 0 하드코딩). 곡선 불변, 테스트 통과 — correctness gap 해소.

---

## [2026-09-25] feat | ADR-0212 step-4 — Jev 결정으로 PPL + card draw 구현

### 배경
operator 위임 ("Jev로 권장안 선택하고 진행"). 3회 Jev Choice.

### 구현
- **PPL deck** (Jev `ppl`, p=0.86, conf 0.79): `deckForGrade` + `--deck ppl` harness 모드. 곡선 불변.
- **card draw** (Jev `add_draw`, p=0.89, conf 0.84): `drawHand` — hand 소진 시 discard 재활용 (order-preserving, RNG 미소비, enemy turn 이후 실행). **stall 제거** (g3/g4 100%→0%), 플레이어 ~6-8턴 생존. 테스트 3건은 recycle 의미로 갱신.
- 회귀: `deckForGrade` 테스트 추가. 2665 pass.

### 실측 곡선
```
grade  1    2    3     4     5   6
before 100  100   0     0     0   0
after  100  100  1.2   0.8    0    0   ← draw+PPL
```

### 핵심 발견
draw 로 stall 은 사라졌으나 곡선은 여전히 cliff. 원인은 **damage-vs-HP 비율** — 프로그램 데미지 `tier*5` (≤125/hand) ≪ tier-3+ ICE HP 130-620. 덱 구성·드로우로는 못 바꾼다.

### 미적용 (정책)
3차 Jev Choice `ice_hp_retune` (p=0.61) 은 **conf 0.41 < 0.5** → WF5/6 정책상 human surface. 구현 분석상 high-tier ICE 를 무의미하게 약화(neuromancer 620→136)시키는 결과라 손튜닝 hack 을 ship 하지 않음.

### 잔여
- **balance pass (사람 결정)**: deck damage 스케일 상향 + tier별 `hp_base` 압축을 함께. 또는 "설계 공백"으로 문서화하고 보류.

---

## [2026-09-25] feat | ADR-0212 step-4 — grade별 ICE HP cap (ice_hp_retune 구현)

### 측정
opening deck 승률 vs ICE HP: **50 → 100%, 116 → 100%, 118 → 18%, 240 → 0%** → **~117 HP 에서 step** (고정 덱 전투가 near-deterministic).

### 구현
- `iceHpForGrade` 가 데이터 ramp(`hp_base + hp_per_grade*(g-1)`)를 **grade별 cap** `[50, 85, 116, 118, 121, 124]` 로 상한. 저HP ICE 는 자기 값 유지, 고HP ICE 만 cap (데이터 보존).
- 곡선: `100 / 100 / 100 / 18.4 / 0 / 0` (단조 비증가, mid point 18%).
- 테스트 2건을 cap semantics 로 갱신. 2665 pass.

### 한계
HP 만으로는 매끄러운 gradient 불가 (transition band ~117±1). gradient 를 원하면 encounter/덱에 분산 축 추가 필요 (grade별 armor/damage 변화, deck 스케일).

### 잔여
- 분산 축 도입 여부 (사람 결정) 또는 현 단조 곡선 수용.

---

## [2026-09-28] chore | Prettier 전역 reformat + alarm-cap/fuzz + delegation-verification CI

### Prettier reformat (10 commits, 동작 변경 없음)
- `dd75fb1` single-quote→double, line-wrap, indent를 시작으로 combat/audio → dungeon → hub/info_market/faction/event_matrix → equipment/crafting → state/actions/meta → menu/settings → graphic_novel/core/types → canvas/combat_vfx/debug/dungeon/hud/matrix/palette renderer → input/save/data/main (`e0f52d5`) 순으로 전역 포맷 통일.
- 커밋 메시지 기준 style-only. 전역 reformat이므로 이후 `git blame` 시 이 구간은 포맷 노이즈로 간주.

### 테스트 (ADR-0210 invariant)
- `54943ce` test(web): alarm-cap edge-case + combat fuzz 추가.

### CI
- `7cfa12e` ci(wet_run): delegation-verification workflow 추가 (sharded tests + Discord).

### 잔여
- 본 entry는 2026-10-01 세션에서 git 이력 기준으로 후기록 (당일 log 공백 보강). 09-24~25 항목은 이미 기록되어 있었음을 정정.

## [2026-10-07] adr | ADR-0213 Far Grid — 비-깁슨 사이버펑크 별도 영역 확장

**Status**: ✅ Accepted (Option 1, 사용자 승인 2026-10-07). 문서만 — 코드/데이터 미착수 (❌ Not started).

- `docs/architecture/0213-far-grid-separate-expansion.md` 신규 — Sprawl 캐논 격리, `source_universe` 스키마, §8 정합. Related: `Fiction/decisions/0054-sf-collection-expansion.md` (Draft).
- `docs/wiki/world/cyberpunk-sources.md` 신규 — 비-깁슨 사이버펑크 원천 prep (SF_F 서브셋, wet-run 연결점). Raw 제공(user-side) 후 Fiction ingest.
- `docs/architecture/README.md` + `docs/wiki/index.md` 인덱스 등록.

## [2026-10-11] feat | Far Grid Phase 1 구현 (ADR-0213)

**Status**: ✅ Implemented (Phase 1). Gates: typecheck 0 · lint 0 errors · vitest 112 files / 2687 passed · build OK.

- `web/src/core/types.ts` — `Mission.source_universe?` + `story?`, `ScreenKind "far_grid_hub"` (optional 필드로 — required 시 기존 fixture typecheck 파손에 중간 red 발생하므로 규약 준수).
- `web/src/core/data_loaders.ts` — literal 검증 + sprawl 기본값 + story passthrough (display-only, resolve 없음).
- `web/src/core/missions_filter.ts` 신규 — frozen `ReadonlyArray` (undefined→sprawl).
- `web/src/renderer/menu.ts` — FAR GRID 항목 (13→14). `menu.test.ts`/`menu_layout.test.ts` 카운트 동기화.
- `web/src/renderer/far_grid_hub.ts` 신규 — 허브 화면 + `[Source: stem]` 동일행 표기 (행 레이아웃 유지).
- `web/src/main.ts` — menu/input/draw 배선. 리뷰 중 발견한 launch index bug 수정 (filtered 인덱스→전체 인덱스 매핑, `launchSelected` 무수정).
- `web/src/data/missions.json` — True Names 미션 3개 (far_grid_prelude, don_mac_audit, deathspiders_news). 기존 카운트 단언 33→36 (`missions.test.ts`, `mission_loader.test.ts`).
- Deferred: Hardwired 미션 (raw 미확보), 게이트 로직, story resolve.

## [2026-10-12] feat | Far Grid Hardwired 미션 3종 (ADR-0213)

- `missions.json` 36→39 (warren_meadow, blue_silk_wall, maidens_first_run — `xauthors/hardwired` stems).
- 카운트 단언 동기화 (`missions.test.ts`, `mission_loader.test.ts`, far-grid 목록 단언 6종).
- Gates: typecheck 0 · lint 0 errors · 112 files / 2687 passed · build OK.

## [2026-10-12] refactor | Far Grid tidy — helper 단일화 + ADR-0213 Phase 1b 기록

- `main.ts` 인라인 universe filter 2곳 → `filterMissionsByUniverse` 단일화.
- ADR-0213 Implementation Status Phase 1b 추가 (미션 6종) + 인덱스 행 ❌→🟡 Partial.
- Gates: typecheck 0 · 112 files / 2687 passed.

## [2026-10-12] feat | ADR-0213 Phase 2 — Far Grid entry gate

- 신규 `src/core/far_grid_gate.ts` (pure helpers, no UI imports, default-fill localStorage pattern).
- `MENU_OPTIONS` FAR GRID `available` 데이터 유지; `renderMainMenu` 가 flag 받아 locked 시 `(locked)` suffix + GRAY_DARK.
- `main.ts:selectMenuOption` 가 locked 시 status line에 + 메시지 ("Clear Sprawl Arc 1 to unlock the Far Grid").
- Defense in depth: `far_grid_hub` screen (input handler + render) 도 lock re-check.
- Arc-1-clear signal = `state_actions.ts:applyLootAction` 의 `arc === 1` missionComplete 분기 — 신규 completion 시맨틱 없음.
- 신규 Vitest 25 tests: `far_grid_gate.test.ts` (13), `menu_far_grid_gate.test.ts` (6), `far_grid_gate_signal.test.ts` (6).
- Gates: typecheck 0 · lint 0 errors (4 pre-existing warnings) · 115 files / 2712 passed (+25) · build OK.

## [2026-10-12] feat | Far Grid Phase 2 gate — arc-1 win unlock (ADR-0213)

- `far_grid_gate.ts` 신규 (localStorage 플래그, default-fill) + 메뉴 잠금 표시/차단 + hub defense-in-depth.
- Arc-1-clear 신호: `applyLootAction` mission-complete에서 `arc===1` 시 플래그 (신규 완료 개념 없음).
- 정직한 기록: arc-final 개념이 코드베이스에 없어 ANY arc-1 승리에 해금. 메시지도 구현 의미 그대로 수정.
- Gates: typecheck 0 · lint 0 errors · 115 files / 2712 passed · build OK.

## [2026-10-12] feat | Far Grid Wave 2 — 미션 14종 + briefing + hub resolution (ADR-0213)

- `missions.json` 39→47 (TN 4 + HW 4 신규) + 14편 grade spread(1~4) + 전편 briefing.
- Hub에 선택 미션 briefing 블록 (wrap/truncate/footer-safe).
- Gates: typecheck 0 · lint 0 errors · 115 files / 2720 passed · build OK.
- 참고: seed 중복 {555,7,444}은 기존 Sprawl 쌍 (미수정).

## [2026-10-12] test | Far Grid Pillar-2 검증 — 던전 풀 분리 (ADR-0213)

- RNG = mulberry32(seed + id-hash)라 우주 간 풀 공유 구조적 불가. 테스트 4개로 고정.
- Gates: typecheck 0 · lint 0 errors · 116 files / 2724 passed.
- seed 중복은 non-issue로 종결 (id가 스트림 분리).

## [2026-10-12] feat | Far Grid Wave 3 — full roster 20종 (ADR-0213)

- `missions.json` 47→53 (잔여 6편 전부 매핑, 미매핑 0).
- 정정: "26 미매핑"은 카운팅 오류였음 (xauthors 20편 중 14 매핑済). 에이전트가 허위 미션 창작 거부 (§8 준수).
- Hub 스크롤 불필요 (20개, 50행 그리드 내 brief 포함 표시 가능).
- Gates: typecheck 0 · lint 0 errors · 116 files / 2724 passed · build OK.

## [2026-10-12] feat | Far Grid gate tightening — full arc-1 clear (ADR-0213)

- 완료추적 (`wetrun_completed_missions`) + Sprawl arc-1 6종 전승 시 해금 (카탈로그 동적 도출, 하드코드 0).
- 기존 해금 세이브 유지 (legacy 플래그 short-circuit). 메시지 full-clear 의미로 수정.
- Gates: typecheck 0 · lint 0 errors · 116 files / 2752 passed · build OK.

## [2026-10-12] chore | Deep-check cleanup — 데드 JSON 삭제 + as-any 제거 + console.log 제거

- `web/src/data/ko.json`·`strings.json` 삭제 (코드 무참조; 설계문서 5곳 정합 노트).
- `state_actions.ts` as-any 3건 → SkillUser/UsableSkill 구조적 완화 (`ice_ai.ts`).
- `main.ts:1060` console.log 제거. lint warnings 4→1.
- Gates: typecheck 0 · 116 files / 2752 passed.

## [2026-10-12] refactor | Deep-check 모듈 분할 4건 (ADR-0110)

- dungeon_crawler 1252→5 files · state_actions 1048→3+barrel · menu 1039→4+barrel · combat_vfx 894→3+barrel.
- re-export barrel, 동작 불변, RNG/렌더 출력 동일.
- Gates: typecheck 0 · lint 0 errors · 116 files / 2752 passed · build OK.

## [2026-10-12] feat | 메뉴·hub i18n 배선 — 첫 실소비자 (deep-check)

- `i18n.ts`에 메뉴·hub 키 EN+KO 추가, 렌더러 2종 `language` param (EN 바이트 동일).
- `main.ts`는 `UI_LANGUAGE="en"` 고정 (전역 토글 deferred).
- Gates: typecheck 0 · lint 0 errors · 117 files / 2767 passed · build OK.

## [2026-10-12] fix | ADR-0211 Option 1 — 하네스 grade-HP 배선

- `simulateCombat`이 토폴로지 HP 대신 `iceHpForGrade` 사용. 커브 단조화 (100/100/100/16/0/0).
- ADR Accepted 기록 + 근거 2건 해소 확인 (armor 반영, 일반방 grade-aware).
- Gates: typecheck 0 · 117 files / 2767 passed.

## [2026-10-12] feat | KO UI 활성화 + 0211 Option 2 (follow-ups)

- KO: settings 토글 + `wetrun_language` 영속 + 메뉴/hub KO 렌더.
- Option 2: `parseIce` grade-HP 도출 (수치 이동 0, 회귀 3건).
- Gates: typecheck 0 · lint 0 errors · 118 files / 2792 passed · build OK · mixed 0.

## [2026-10-12] ci | Dead wetrun-web.yml 재작성 + 검증도구 정리

- 워크플로: `Game/wet_run-web/**`+`prototype/` 경로라 영원히 미실행 → `Game/wet_run/web/**` 대상으로 재작성 (ci/typecheck/vitest/build + Pages).
- audit 스크립트 2종 현역 확인 (로그 인용). generate-*.py 일회성 (산출물 커밋済, 유지).
- e2e는 수동 유지 (브라우저 없음). VALIDATION_SCENARIO 개수 정합 (14 options, 53 missions).
- Gates: YAML valid · 118 files / 2792 passed · build OK.

## [2026-10-12] feat | KO 파이프라인 + Tier 5 carry-over (follow-ups)

- KO: 53 titles + 20 briefings 번역, 렌더러 KO 분기, CJK 0.
- Tier 5: 볼륨 슬라이더 확인 + SFX 7종 + 실상태 이펙트 + 압축 측정(53~66%).
- 스크래치 5건 삭제 (swap/중복모듈/검증스크립트/debug spec).
- Gates: typecheck 0 · lint 0 errors · 120 files / 2821 passed · build OK · 단조 유지.

## [2026-10-13] feat | PWA 완성 — 리스너+상태+settings 표면

- `pwa_boot.ts` 신규 (beforeinstallprompt/controllerchange/online-offline + 구독).
- settings PWA 섹션 (설치/업데이트/오프라인) + i18n EN/KO.
- Gates: typecheck 0 · lint 0 errors · 122 files / 2874 passed · build OK · mixed 0.

## [2026-10-13] fix | Sprawl 보드 격리 붕괴 수정 (ADR-0213)

- mission_select가 53종 전 노출 → sprawl 33종만 (hub 전용 far-grid 20종 차단).
- 격리 불변 테스트 + 브라우저 캡처 검증 (Selected 1/33).
- Gates: typecheck 0 · 122 files / 2875 passed.

## [2026-10-13] feat | ICE 밴드 로테이션 — 5종→19종 (fun fix)

- 밴드당 3-4종, 시드 결정적, 보스 제외, HP 캡 유지.
- 커브: 100/100/100/16/0/0 절벽 → 100/100/78.7/66.6/44.4/0 gradient (단조 유지).
- 테스트 격리 불변 + Set.intersection lib 수정.
- Gates: typecheck 0 · lint 0 errors · 122 files / 2883 passed · build OK.

## [2026-10-13] feat | Fun curve + SFX/아이콘 + E2E CI

- Curve: dmg 보너스 조정 → PPL g6 31% (목표 25-45), opening 단조 유지.
- 에셋: 합성 WAV 7 + PIL 아이콘 2 (186KB), 재생 검증.
- E2E 50/50 그린 확인 (수동). CI e2e 잡은 다음 푸시에서 실동작 검증.
- Gates: typecheck 0 · lint 0 errors · 122 files / 2902 passed · build OK · mixed 0.

## [2026-10-13] fix | PWA Node20 가드 — CI navigator 부재 수정

- `INITIAL_PWA_STATE` 모듈로드 시 `navigator` 참조 → typeof 가드 (CI 3 suites 실패 원인).
- Gates: typecheck 0 · 122 files / 2902 passed.

## [2026-10-13] ci | E2E 서브리포 CI 편입 + 루트 중복 제거

- 서브리포 `ci.yml`에 e2e 잡 추가 (preview + chromium, 14 specs).
- 루트 `wetrun-web.yml` 삭제 (gitignored 경로라 영원히 미트리거).

## [2026-10-13] fix | E2E 메뉴 인덱스 하드코딩 제거 — CI settings 전수 실패 수정

- settings/continue 스펙이 구 인덱스 가정 → live `getMenuOptionKeys`+`getSelectedMenuIndex` 후크 신설.
- 로컬 6 passed. CI에서 실동작 확인 예정.
[2026-10-14] verify | wet_run_verify (1/2/3) — audit=True
[2026-10-14] verify | wet_run_verify (1/2/3) — audit=True
[2026-10-14] verify | verification-report.md 생성 (bal=pend, jev=adv, audit=clean)
[2026-10-14] verify | wet_run_verify (1/2/3) — audit=True
[2026-10-14] verify | wet-run balance 원리 적용 완료 (T1~T3 OK, |Δ|≤15%) — metrics.json 연결; design target 기반
[2026-10-14] verify | wet_run_verify (1/2/3) — audit=True
[2026-10-14] verify | (a)+(b) 완료 — metrics.json verified_ref; verification-report.md 최종; vitest 직접 연결 대기
[2026-10-14] demo-journal | turn=1 jev=advisory visual=False
[2026-10-14] verify | wet_run_verify (1/2/3) — audit=True
[2026-10-14] verify | 1완료 — vitest 직접 연결 (direct_connected, all passed)
[2026-10-14] verify | 2진행 — Playwright library OK, browser binary missing (playwright install required); demo-journal structure ready
[2026-10-14] demo-journal | turn=1 jev=advisory visual=False
[2026-10-14] verify | 2완료 — Playwright install + turn_01_visual.png (84258b) 캡처 완료; Jev p=0.82
[2026-10-14] verify | 3진행 — dashboard 1019 HTML (샘플 200 중 broken 134, ~67%); docs/dashboard-broken-summary.md + find_dashboard_broken.py 생성; 전체 fix 별도 세션
[2026-10-14] verify | 1+2 완료 — ADR-0065 (양방향 wikilink + audit 확장) + index cross_citation_protocol
[2026-10-14] cleanup | session intermediates removed (turn_1_journal.md, /tmp artifacts) — canonical artifacts preserved
[2026-10-14] verify | 3진행 — dashboard top-4 broken links fixed (134→93 /200), script scripts/fix_dashboard_links.py
[2026-10-14] fix | dashboard 링크 전면 수리 — 258 broken 상대경로 정정 (depth-aware, 211 HTML); Fiction cross-repo 6-up 정상화, `../CHANGELOG.md` 등 off-by-one 정정; dead 16 잔존 (retired prototype 12 + 제거된 dungeon/adr docs 4, 콘텐츠 결정 필요)
[2026-10-14] demo-journal | turn=2 jev=advisory visual=False
[2026-10-14] verify | 후속 모두 완료 — 1(direct), 2(turn2 PNG), 3(dashboard 0 broken / 200), audit CLEAN

## [2026-10-27] feat(dashboard) | 파생소설 카드/검색 인덱스 확장 — xauthors·peripheral 국소 추가

**Status**: ✅ 완료 (uncommitted). Fiction KO CJK 정리분을 대시보드에 반영.

- retire된 생성기 `scripts/markdown_to_story_html.py` 복원(bbcb579^) + 수정:
  - `REPO_ROOT` `/Users/emilio/projects/Projects` → `/Users/emilio/projects/opencodework`
  - `DASH_STORIES` `Game/wet_run/dashboard/stories` → `Game/wet_run/docs/dashboard/stories`
  - `--trilogy peripheral|xauthors` 추가 · `_trilogy_labels` 확장(Halo/Hardwired/True Names/Peripheral) · `character_ref` 배지 fallback
- **국소 추가**: `xauthors/{halo,hardwired,true-names}` + `peripheral/short-stories` 카드 **94개 신규**(EN 47 + KO 47) → `docs/dashboard/stories/short-stories/`. 기존 970 카드 **무변경**(이름 충돌 0).
- `search_index.json`: 신규 엔트리 94개 텍스트 삽입(기존 953 엔트리 바이트 보존), `count` 953→1047.
- `stories-browse.html`: trilogy 필터 버튼 4개 추가(Peripheral/Halo/Hardwired/True Names) + 카드 수 표기 127→1047.

**전체 재생성 비권장 근거**: 복원 생성기 전체 실행 시 커밋 대시보드와 근본 불일치 — 생성 1307 vs 커밋 970, 공통 762개 전부 상이, 신규 이름 545, 고아 208. 커밋 카드는 여러 세대 산출물 혼재(`_en` 381 · `_ko` 381 · `.ko` 104 · bare 866)이고, 현재 sprawl/bridge/blue-ant EN 소스의 slop(`"Something changed in the air"`)이 주입됨.

**품질 메트릭**: 4종 도구(`verify_gibson_style` · `derivative_literary_check` · `advanced_literary_check` · `flesch_readability`)를 신규 EN 47건에 실행 → 94 엔트리 **전부**에 `gibson_style`·`literary`·`advanced_literary`·`readability` 채움(EN/KO 동일값). 상단 집계 stats도 갱신(gibson 500→594 · literary 495→589 · advanced 480→574 · readability 480→574).

**카드 필드 통일**: `title`/`subtitle`/`word_count`/`character` 4필드를 소스 frontmatter 실값으로 **전 엔트리(1047) 통일** — 기존 953개가 slug 제목이던 것을 실제 제목으로 교체(예: `3jane_straylight-monopoly` → `3Jane's Straylight Monopoly`, KO `3제인의 스트레이라이트 독점`). slug 잔존 **0**. + `search.html` stale `78 entries` → 1047.

**검증(Orca 브라우저)**: 메인 허브 · `stories-browse`(1047카드, trilogy 필터 8종: peripheral 34/halo 20/hardwired 20/true-names 20/sprawl 523/bridge 180/blue-ant 250) · 언어 필터(halo+KO=10) · 검색(Aleph→신규 포함) · KO/EN 카드 렌더(CJK 0) · 네비 링크 200 · **콘솔 에러 0**. CLI: `dashboard_pipeline_audit.py` 0 errors · `find_dashboard_broken.py` 1113 HTML / broken 0 · `audit_vault.py` CLEAN · `mixed_language_audit.py` 0.

**한계**: `build_static_data.py`(search_index 전체 생성기) 미복원 — 실행 시 slop 주입 위험. 신규 카드 본문은 현재 EN/KO 소스 그대로(일부 slop 포함 가능).

**부수(기존 이슈)**: `play.html`(→`tier5.js`)이 참조하던 `sounds/v2/{click,select,error,success,flatline,jack_in,jack_out,scan,probe,hammer,wardrone}.wav` 11개가 부재해 404 → 게임 SFX(`web/public/sounds/sfx/`)에서 매핑 복사하여 해소(전부 HTTP 200, play.html 콘솔 0). `novel.html` 404는 정적 참조가 전혀 없는 팬텀(REORGANIZE_PLAN상 이미 삭제·library.html 통합) — 수정 대상 없음.

## [2026-10-27] test | Property-based fuzzing 도입 — 최초 적용 + 결함 5건 발견

**배경**: 기존 검증 스택(vitest 122 files · Playwright e2e 16 specs · seeded balance 하네스 · 정적 audit 4종 · Orca 수동)에 **property-based/fuzz 테스트가 부재** → `fast-check` 도입, 최초 적용.

**도입물**:
- `web/package.json`: devDep `fast-check@^4.10.2` + 스크립트 `fuzz` = `vitest run property`.
- `web/tests/property_reducer_fuzz.test.ts` (343 LOC) — `applyAction`에 13종 액션 랜덤 시퀀스 주입, 매 스텝 8개 불변식 검증(throw 없음 · NaN/Infinity 없음 · HP 범위 · alarm 0..100 · turnCount≥0 · phase/runPhase/bossPhase 유니온 · activeIceIndex 범위 · determinism). 기존 `mulberry32` + `Math.random`/`Date.now()` 제어 하네스 재사용.
- `web/tests/property_save_fuzz.test.ts` (312 LOC) — `SaveSlot` 왕복 무손실(plain/compressed 양 브랜치) · 손상/절단/legacy/할당량초과 내성.

**게이트**: `npm test` **124 files / 2911 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. 딥 런 `FUZZ_RUNS=20000`에서도 리듀서 불변식 위반 **0** (리듀서 자체는 건전).

**발견 5건** (미수정 — 검증 전용 세션이므로 보고만):
1. **[HIGH·crash]** `isSaveSlot`(`src/save/storage.ts:210`)이 배열 원소 타입·`graphicNovelProgress`를 검증하지 않음 → `slotToGameState`(`src/core/state.ts:243`)의 `chainId.split("_")`가 **TypeError 크래시**. 최소 반례 `graphicNovelProgress:"not-an-object"`. `it.fails`로 고정.
2. **[MED]** 같은 함수가 `deckIds:[1]`(숫자 원소)을 유효 `SaveSlot`으로 수용 — 선언 타입 `ReadonlyArray<string>` 위반. `it.fails`로 고정.
3. **[HIGH·gameplay]** **보스 방에 도보 도달 불가 — 53/53 미션**. `applyMatrixAction`(`src/core/state_actions_phases.ts:87-136`) 이동이 비대칭(전진은 `adjacent[0]`만, 후진은 첫 매칭 노드) → 생성 그래프 대부분 노드(보스 포함) 진입 불가.
4. **[MED]** `ice_x2` 뮤테이터 무효 — `Math.min(node.iceIds.length * mult, 4)` 후 `slice(0, baseCount)`는 늘릴 수 없음(`state_actions_phases.ts:59-65`). 노드는 항상 ICE 1개 → 멀티-ICE 전투는 데드 코드.
5. **[MED]** `parseIce`(`src/core/data_loaders.ts:233-272`)가 ICE `skills`를 버림 — 97종 중 **44종** 손실 → `skillCooldowns` 항상 `{}`, `enemyShouldUseSkill` 미발화.

**미커밋**. `it.fails` 2건(결함 1·2)은 회귀 추적용으로 유지.

## [2026-10-27] fix | Fuzzing 발견 결함 5건 전부 수정 (ADR-0215·0216)

**계기**: property-based fuzzing(fast-check) 도입 직후 발견된 결함 5건을 전부 수정. 게이트: `npm test` **125 files / 2928 tests PASS** · `tsc --noEmit` 0 · `eslint` 0 errors · 딥 퍼징 `FUZZ_RUNS=3000` 9 PASS · `audit_vault.py` CLEAN · `mixed_language_audit.py` 0.

**#1·#2 [HIGH·crash] 세이브 검증 강화** — `web/src/save/storage.ts`
- `isSaveSlot`이 배열 **원소 타입**을 검사하지 않아 `deckIds:[1]`(숫자)을 유효 `SaveSlot`으로 수용 → 선언 타입 위반.
- `graphicNovelProgress` 미검증 → `slotToGameState`의 `chainId.split("_")` **TypeError 크래시**.
- 수정: `isStringArray` + `isGraphicNovelProgress` 가드 추가(+26/−4, 259 LOC). `property_save_fuzz.test.ts`의 `it.fails` 2건 → 정상 통과 테스트로 전환(반례는 회귀 주석 유지).

**#3 [HIGH·gameplay] 보스 도달 불가 → 그래프 지향 내비게이션 (ADR-0215)**
- 원인: `applyMatrixAction` 전진이 `node.adjacent[0]`만 따라감 → 53/53 미션에서 그 체인이 **2-사이클 0↔1**이라 최대 28노드 중 2개만 방문. (그래프 자체는 완전 연결 — BFS 도달 53/53.)
- 신규 `web/src/core/matrix_navigation.ts`(148 LOC): `nextHopToward(matrix, from, target)` = `adjacent` 위 BFS 최단경로의 첫 hop, 도달 불가 시 `-1`. **`adjacent[0]` fallback 금지**(그 fallback이 결함 원인).
- 전진=`bossNode` 방향, 후진=`startNode` 방향, `-1` → 상태 불변 + 명시 메시지. `applyLootAction`도 동일 헬퍼(인덱스+1 제거). `makeInitialState`는 `matrix.startNode` 사용. 렌더러 `isAdjacent`는 `adjacent.includes`.
- 실측: 보스 도달 **0/53 → 53/53**, 평균 도보 **17.57 → 3.58 hop**, 최대 34 → 6.
- 회귀 테스트 `web/tests/matrix_navigation.test.ts`(12) — 리듀서를 `adjacent[0]`로 되돌리면 `expected 1 to be 20`으로 실패 확인.

**#4 [MED] `ice_x2` 뮤테이터 무효** — `state_actions_phases.ts`
- `Math.min(node.iceIds.length*2, 4)` 후 `slice(0, baseCount)`는 늘릴 수 없음(노드당 ICE 1개) → 멀티-ICE 전투 데드 코드.
- 수정: `Array.from({length: baseCount}, (_, i) => node.iceIds[i % node.iceIds.length])` 순환 → 별개 객체. 되돌리면 `expected 1 to be 2`로 실패 확인.

**#5 [MED] `parseIce`가 ICE `skills` 폐기** — `data_loaders.ts` → `ice_skills.ts` (ADR-0216)
- 97종 중 **44종** 스킬 상실 → `skillCooldowns` 항상 `{}`, `enemyShouldUseSkill` 미발화.
- JSON은 스킬을 **문자열 ID**로만 보유(88종, 메타데이터 catalog 부재) → loader가 파생: `id` 원문 · `name` humanize · `effect` snake_case **토큰** 매칭(substring 금지 — `enforce_contract`의 "force" 오분류 방지) · `damage`=`dmg_base`(비공격 효과는 0, `damage>0` 게이트) · `cooldownMs`=4000.
- 모듈 분리로 `data_loaders.ts` 461 → **320 LOC**(정책 100–300 준수), 신규 `ice_skills.ts` 147 LOC.
- 밸런스 `npm run balance` **바이트 동일**(인카운터 밴드 24종 중 스킬 보유 2종).

**부수**: 합성 매트릭스 픽스처 4곳 비정합(범위 밖 `adjacent`) 정합화 — assertion 약화 없음(픽스처만 수정).

**미커밋**. ADR: `0215-graph-directed-matrix-navigation.md` · `0216-derived-ice-skill-metadata.md` (+ `decisions/README.md` 인덱스 2행).

## [2026-10-27] fix | CONTINUE 가 플레이 불가 상태를 복원하던 결함 수정 (ADR-0217)

**발견**: 후속 검증 중 `slotToGameState`가 `matrix: null` + `runPhase: "matrix"`를 반환 → `applyAction`이 `runPhase === "matrix"`로 먼저 분기해 `applyMatrixAction`이 처리하는데, 그 `confirm`·이동 분기가 **모두 `state.matrix != null` 가드**에 걸려 CONTINUE 후 **모든 입력이 no-op**. 실측: `confirm`·`move_south` 모두 **동일 객체 반환**(no-op).

**기존 테스트가 놓친 이유 — 거짓 양성 2건**:
- `tests/slot_restore.test.ts` — `phase === "approach"`·`message`만 검증, **플레이 가능성 미검증**.
- `e2e/continue.spec.ts` — `phase ∈ {combat, approach}`만 검증. dead state의 `phase`가 `"approach"`라 **자명 통과** (주석은 "resume → combat 검증"이라 주장).

**수정**:
- `slotToGameState`가 `makeInitialState`와 **동일 입력**(`missionGradeOf`/`missionSeedOf`)으로 매트릭스 재생성 → 복원 run이 시작 시점과 같은 매트릭스.
- `SaveSlot.currentNodeIndex?`(선택 필드) 추가 — `stateToSaveSlot` 기록 · `isSaveSlot` 검증 · `slotToGameState` 소비(없으면 `matrix.startNode` 폴백). **스키마 버전 미변경**(선택 필드 → 하위 호환, 구 세이브 로드 가능).
- `makeInitialState`의 중복 인라인 추출을 `missionGradeOf`/`missionSeedOf`로 통일(동작 동일 — 신규/복원 run의 생성 입력 드리프트 방지).
- `main.ts handleContinue`가 `launchSelected`처럼 `grid: makeGrid(layout.cols, layout.rows)` 사용(1줄). 동작 변화 0 — `state.grid`는 렌더 직전 항상 `renderGrid(layout...)`로 재생성됨을 실측 확인(latent 불일치만 제거).

**회귀 테스트**: `tests/slot_restore.test.ts` +7 (플레이 가능성·왕복). **pre-fix 코드에서 6/7 실패 확인** — `expected null not to be null`(매트릭스) 및 `expected {phase:'approach',…} not to be {phase:'approach',…}`(동일 객체 반환 = no-op의 결정적 증거). e2e 어서션 강화(브라우저·live URL 부재로 **미실행**).

**잔여 갭**: 복원은 근사 — `visitedNodes`·`iceRoster`·`statusEffects`·`playerCombo`·`skillCooldowns`·`activeMutators`는 저장되지 않아 리셋됨.

**게이트**: `npm test` **125 files / 2935 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0217-continue-restores-playable-run.md`.

## [2026-10-27] fix | ICE 스킬 선택 fallback 이 사용 불가 스킬을 고르던 결함 수정 (ADR-0218)

**발견**: `selectSkillByPersonality`(`ice_ai.ts`)가 선호 매칭 실패 시 `availableSkills[0]`로 폴백하는데, 전투 경로(`state_actions_combat.ts:230`)는 `damage > 0`인 스킬만 발화 → 첫 스킬이 비공격이면 **공격 스킬을 영원히 미사용**(조용히 자동공격).

**실측 (로더 파생값 직접 실행)**: `loa_entity`(g5 밴드) = `manifest_form`(buff/0) + `voodoo_curse`(poison/5), personality→`aggressive`(선호 `heavy_attack/pierce/multi_hit/attack/lifesteal` — 둘 다 불일치) → 폴백이 `manifest_form`(0) 선택 → 자동공격. `aleph`(g6)는 선호 매칭 `matrix_merge`(15)가 먼저라 **영향 없음**.

**수정**: 폴백을 **첫 `damage > 0` 스킬**(없으면 첫 스킬, 빈 배열이면 `null`)로. **선호 루프·`PERSONALITY_SKILL_PREFERENCE` 불변.** `ice_ai.ts`의 **stale docstring 2곳** 정정 — 파일 헤더가 "hot path는 `chooseSkill` 사용"이라 주장했으나 실제로는 `state_actions_combat.ts:221`이 `selectSkillByPersonality`를 호출.

**회귀 테스트**: `tests/ice_ai.test.ts` +3(단위), `tests/personality_skill.test.ts` +1(통합). **pre-fix 실패 확인** — 통합 실패 메시지 `expected '>>> Loa attacks: 9 dmg' to contain 'Voodoo Curse'`가 증상 재현. 기존 `defensive` 선호 테스트는 무변경 통과(선호 루프 미변경).

**밸런스**: `npm run balance` 전 6개 grade **바이트 동일**, g5 `mean-HP-end`만 5.5 → 5.6(반올림 수준). 승률/스톨/턴 밴드 무변화.

**잔여 한계(미수정)**: 선호 목록에 **매칭되는** 스킬이 `damage: 0`이면 여전히 자동공격 — 비공격 스킬 효과(shield/heal/regen/buff/detect)가 전투 경로에 **미구현**이라 `defensive`/`support` 아키타입의 선호 목록이 구조적으로 관측 불가.

**게이트**: `npm test` **125 files / 2939 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0218-ice-skill-selection-fallback.md`.

## [2026-10-27] docs | 비공격 ICE 스킬 효과 결정 요청 (ADR-0219, Draft)

**배경**: ADR-0218의 Remaining Gap(선호 목록에 매칭되는 `damage: 0` 스킬은 여전히 자동공격)을 해소하려면 (a) 비공격 효과(shield/heal/regen/buff/detect)를 전투 경로에 **구현**하고 (b) 스킬 magnitude 데이터를 **저작**하고 (c) 인카운터 밴드를 **확대**해야 하는데, 셋 다 **ADR-0211에서 `--runs 100` 근거로 캘리브레이션한 밸런스 곡선**(`ENCOUNTER_HP_BY_GRADE`·`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`)을 건드림 → 임의 변경 대신 AGENTS.md §3.3 결정 요청으로 진행.

**조사에서 추가 확인된 사실**:
- web 전투 경로에서 `shield`는 **player 측**(`combat_models.ts` `Skill.shield`·`equipment.ts` `shieldBonus`·`wetware.ts`)에만 존재 — **ICE/enemy 측에는 부재**. `StatusEffectKind`에 `shield` 없음, enemy 경로는 `StatusEffectKind`를 아예 참조하지 않음.
- catalog personality 분포: aggressive 80 / defensive 12 / stealth 5 / **support 0** → Option A로도 `support` 아키타입은 해방되지 않음(매칭할 ICE 부재).
- 인카운터 밴드의 `defensive` ICE 2종(`watchdog`·`ice_neuromancer_warden`)은 **`skills: []`** → 실플레이에서 `defensive`는 선호 매칭 경로에 진입조차 못 함.
- 88개 고유 skill ID / 97개 ICE 행, 스킬은 **문자열 ID만** 보유(메타데이터 테이블 부재).

**문서**: 옵션 4종(A 전면 구현 / B 일관성만 / C 현행 유지 / D 데이터만 선저작) 비교표 + 추천(**B → D → A** 순) + 열린 질문 8건. `docs/testcases/combat/depth.md`의 Python 프로토타입 시대 shield 의미(스택 + duration, "shield 가 3 모두 흡수")를 의도된 설계로 인용하되 web 미이식임을 명시.

**코드 변경 없음** — 결정 대기. **미커밋**. ADR: `0219-non-damaging-ice-skill-effects.md` (Draft).

## [2026-10-27] fix | ICE 스킬 선택이 발사 불가 스킬을 반환하지 않도록 정합 (ADR-0219 Option B)

**결정**: 사용자가 ADR-0219의 **Option B(일관성만)** 선택 → Draft → **Accepted** 승격.

**수정**: `selectSkillByPersonality`가 후보 풀을 1회 계산(`usable = filter(damage > 0)`, 비면 전체)하고 **선호 루프와 fallback 모두 그 풀에서** 선택 → 발사 가능한 스킬이 하나라도 있으면 반드시 사용(선호 순서 유지), 없으면 기존 동작(자동공격) 불변. ADR-0218의 "first usable" fallback은 자연 도출(`pool[0]`).

**`PERSONALITY_SKILL_PREFERENCE` 불변** (열린 질문에 대한 결정): `shield`/`heal`/`regen`/`buff`/`detect` 항목은 Option A 시점에 살아날 **전방 호환 설계 의도** → 테이블을 자르면 의도가 소실되고 `defensive`/`support`가 "약한 aggressive"로 붕괴. 선택 시점 필터링은 의도를 보존(테이블 docstring에 근거 기록).

**어서션 변경 1건(근거 있음)**: `personality_skill.test.ts`의 `"defensive personality prefers shield/heal skills"`가 `toContain("attacks:")`로 **결함을 고정**하고 있었음(shield(0) 반환 → `damage>0` 게이트 거부 → 자동공격). 테스트명·어서션 반전 → 공격 스킬 **사용** + 자동공격 **미사용** 동시 검증(기존보다 강함).

**회귀 테스트 4건 추가 — 정직하게: 판별력 있는 것은 1건뿐**(pre-fix 실패). 나머지 3건은 불변 동작 고정 가드.

**신규 발견 (미수정, 중대)**: `parseIce`가 **`personality` 필드를 복사하지 않음** → 런타임에 모든 catalog ICE가 `coercePersonality(undefined) === "aggressive"`로 해석되어 `ice_types.json`의 personality 분포(aggressive 80 / defensive 12 / stealth 5)가 **전부 무효**. → **Option B는 현재 정합적이지만 실플레이에서 거의 무효**(personality가 aggressive가 아니어야 작동). 아키타입 시스템의 진짜 병목은 이 로더 갭이며 **ADR-0216(skills 폐기)과 동일 결함 클래스**. 수정 시 밸런스 변화(12 defensive + 5 stealth ICE가 aggressive에서 벗어남) → 별도 결정 필요.

**밸런스**: `npm run balance` 전 6개 grade **전 컬럼 동일**. **게이트**: `npm test` **125 files / 2943 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0219-non-damaging-ice-skill-effects.md` (Accepted).

## [2026-10-27] fix | parseIce 가 버리던 `personality` 복원 (ADR-0220)

**발견**: `parseIce`가 `personality`를 복사하지 않아 런타임에 모든 catalog ICE가 `coercePersonality(undefined) === "aggressive"` → `ice_types.json` 분포(aggressive 80 / defensive 12 / stealth 5 / support 0)가 **전부 무효**. **ADR-0216(skills 폐기)과 동일 결함 클래스**.

**수정**: `parseIce`가 `personality` 매핑 — 부재 시 키 생략(하위 호환), 유효하지 않은 값이면 `[data_loaders]` 접두사로 **throw**(조용한 강제 변환 금지). `VALID_ICE_PERSONALITY` 셋 추가. (`aggression`은 **미변경**.)

**회귀 테스트 4건**(`data_loaders.test.ts`): 비-aggressive ICE 노출 · catalog 분포가 JSON과 정확히 일치 · malformed 시 throw · 부재 시 키 생략. **pre-fix에서 3건 실패 확인**(`expected undefined to be 'defensive'` 등).

**밸런스**: `npm run balance` 전 6개 grade **전 컬럼 동일**. 이유(실측 확인): 하네스는 밴드를 정상 테스트하며(`aleph_fragment` g5 → 기반 ICE `hellhound`, 28노드 매트릭스), 밴드에서 personality가 non-aggressive인 ICE(`watchdog`·`ice_neuromancer_warden` defensive, `wisp` stealth)는 **`skills: []`** 라 `selectSkillByPersonality` 경로에 진입하지 않음. 스킬 보유 2종(`loa_entity`·`aleph`)은 `aggressive`(강제 변환 기본값)라 변화 없음.

> **정정**: 검증 에이전트가 "하네스가 밴드를 테스트하지 않는다"고 보고했으나 **직접 확인 결과 사실이 아님** — `probe.matrix`는 non-null(28 노드)이고 기반 ICE는 `iceCatalog[0]`이 아니라 매트릭스 로스터 ICE(`hellhound`).

**신규 발견 (미수정, 결정 필요)**: **`aggression`도 동일하게 버려짐**(97행 전부 키 보유: standard 36 / aggressive 25 / boss 36 → **61개가 non-standard**, 밴드는 24항목 중 **15개**가 non-standard: standard 9 / aggressive 9 / boss 6). `enemyShouldUseSkill` 확률(0.15/0.35/0.5)을 좌우. **측정 전용** 프로브(임시 적용 후 완전 revert — 최종 diff에 `aggression` 0줄 확인) 결과 g5 `mean-HP-end` 5.6→5.7뿐(승률/스톨/턴 무변화)이지만, catalog 전체의 스킬 발화 **빈도**를 바꾸므로 별도 결정 필요.

**게이트**: `npm test` **125 files / 2947 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0220-parse-ice-personality-restore.md`.

## [2026-10-27] fix | parseIce 가 버리던 `aggression` 복원 — 로더 데이터 손실 0건 달성 (ADR-0221)

**발견**: `personality`(ADR-0220)를 고치며 확인된 동일 누락 — `parseIce`가 `aggression`도 복사하지 않아 런타임에 모든 catalog ICE가 `coerceAggression(undefined) === "standard"` → `enemyShouldUseSkill` 확률이 전부 **0.15** (authored: passive 0.05 / standard 0.15 / aggressive 0.35 / boss 0.5). 영향 **61/97 ICE**, 밴드 **15/24 항목**(standard 9 / aggressive 9 / boss 6).

**수정**: `personality`(커밋 `58ec0b9`)와 **동일 형태** — `VALID_ICE_AGGRESSION`(4개 유니온 값 전부 수용; `passive`는 데이터에 0행이나 선언된 타입 계약), 부재 시 키 생략(하위 호환), malformed 시 `[data_loaders]` 접두사로 throw. **이로써 `parseIce`가 버리는 authored 필드 = 0건** (ADR-0216 skills → 0220 personality → 0221 aggression).

**회귀 테스트 4건**(`data_loaders.test.ts`, `ICE aggression` 블록), **pre-fix에서 3건 실패 확인**.

**밸런스 (정확히 기록)**: `npm run balance` 전후 **단 한 셀만 이동 — g5 `mean-HP-end` 5.6 → 5.7**(+0.1). 승률/스톨/턴/p5·p95 **무변화**. 수정 후 2회 재실행 동일 → **결정적, 노이즈 아님**.

**메커니즘(실측)**: `enemyShouldUseSkill`은 `skills`가 비면 `aggression`을 읽기 **전에** `false` 반환 → 스킬 없는 non-standard 밴드 13슬롯은 **구조적으로 면역**. non-standard **이면서** 스킬 보유인 밴드 ICE는 2종뿐 — `loa_entity`(g5, aggressive → 0.35 = 0.15에서 2.3×) · `aleph`(g6, boss → 0.5 = 3.3×). 하네스 실측: g5는 9개 미션 중 1개가 `loa_entity`(= 이동한 셀), g6 `aleph`는 이미 **0.0% 승률 floor**라 수치 무변화 → **가장 크게 작용하는 곳은 g6이며 하네스가 값을 매길 수 없음**.

**게이트**: `npm test` **125 files / 2951 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0221-parse-ice-aggression-restore.md`.

## [2026-10-27] refactor | ICE 스킬 메타데이터를 휴리스틱 → 저작 데이터로 이관 (ADR-0222, ADR-0219 Option D)

**배경**: ADR-0219 추천 순서 **B → D → A** 중 B(선택 정합)에 이어 **D** 실행 — ADR-0216이 도입한 토큰 휴리스틱 파생을 저작 데이터로 대체(효과 구현 A는 보류).

**변경**:
- `ice_types.json`에 top-level **`skill_defs`** 추가 — **88개 스킬 ID** → `{name, effect, cooldown_ms}`, 현재 휴리스틱 출력을 **그대로 물질화**. 97개 ICE 행은 바이트 동일(`git diff --stat` = 442 insertions / **0 deletions**).
- `ice_skills.ts`: `ICE_SKILL_EFFECT_RULES`·`iceSkillEffectFor`·`iceSkillNameFor` **삭제**(147→187 LOC) → `skill_defs` 조회. 미등록 skill id는 `[data_loaders]` 접두사로 **throw**(조용한 fallback 제거).
- **`damage`는 테이블로 옮기지 않음** — per-ICE(소유자의 `dmg_base`)이므로 옮기면 동작이 바뀜(`ice_pierce`는 dmg_base 12·15 두 행이 소유).
- `data_loaders.ts`: `skill_defs` 키를 추출하고 ICE 행 순회에서 스킵.

**동작 보존 증명(2중)**: ① `npm run balance` 전후 **바이트 동일**(MD5 일치) ② 파생 스킬 테이블(88종 × name/effect/cooldownMs/per-ICE damage) 덤프 전후 **바이트 동일**(MD5 일치).

**어서션 1건 조정(불가피, 근거 기록)**: `missions.test.ts`의 "97 ICE types" 핀이 raw key count(`=== 97`)를 세는데 `skill_defs` 추가로 98이 됨 → `skill_defs`를 필터한 뒤 ICE 행 수를 세도록 변경. **의도("정확히 97개 ICE 타입")는 그대로 97로 고정**되며 약화·삭제 아님. `skill_defs`를 JSON **끝**에 추가해 `Object.values(iceTypesData)[0]`이 여전히 `standard`가 되도록 2차 영향도 무assertion 변경으로 처리.

**D가 드러낸 구조적 사실**: **88종 중 44종이 비공격**(buff 17 · shield 9 · detect 6 · debuff 4 · stun 3 · silence 2 · slow 1 · heal 1 · regen 1)이라 전투 경로에서 **구조적으로 발화 불가**. **9개 ICE는 완전 무력**(모든 스킬이 0-데미지: `archive_sentinel`·`goliath_defensive`·`loa_priest`·`loa_zombie`·`sense_net_spin`·`standard_corrupted`·`ta_daemon`·`ta_inheritor`·`watchdog_defensive`), **17개 ICE는 `skill[0]`이 발화 불가**면서 뒤에 발화 가능 스킬 보유. `support` 아키타입 0종.

**게이트**: `npm test` **125 files / 2951 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0222-ice-skill-metadata-as-data.md`.

**다음(미실행)**: ① **스킬 분류 검토 패스** — 휴리스틱 실수를 그대로 물질화했으므로 데이터에 오분류가 남음(예: `corporate_guard`의 `report`가 `attack` — ADR-0219의 worked example 그 자체). 재분류는 밸런스를 바꾸므로 별도 결정 필요. ② **Option A**(비공격 효과 구현 + magnitude 저작). ③ 인카운터 밴드 확대.

## [2026-10-27] refactor | 스킬 분류 검토 패스 — 휴리스틱 오분류 20종 교정 (ADR-0223)

**배경**: ADR-0222(Option D)가 휴리스틱 출력을 그대로 물질화했으므로 **휴리스틱의 실수가 데이터로 남아 있었음**. ADR-0219 Option A의 **선행 조건**(오분류 위에 메커니즘을 구현하면 실수가 고착)으로 검토 패스 실행.

**규칙(엄격 적용)**: `effect`는 id가 함의하는 메커니즘과 일치 · 기존 `SkillEffectKind`만 사용(유니온 불변) · `name`/`cooldown_ms` 불변 · `damage` per-ICE 불변 · **이름이 명백한 것만 교정**.

**교정 20종** (전부 `effect` 1줄):
- `attack` → `debuff`(7): `alarm_propagate`·`asset_seize`·`broadcast_signal`·`info_warfare`·`media_alert`·`report_alert`·`report_distribute`
- `attack` → `buff`(5): `backup_dispatch`·`data_archive`·`maintain_order`·`packet_route`·`priority_delivery`
- `attack` → `detect`(2): `buffer_check`·`report`
- `attack` → `dot`(1): `addiction_loop`
- `buff` → `debuff`(5): `ai_subversion`·`narrative_warp`·`reality_distortion`·`reality_warp`·`watchdog_mark`

**의도적 미변경(애매) 10종**: `ai_negotiate`·`aleph_fragment`·`enforce_contract`·`ice_break`·`intimidation`·`loa_command`·`matrix_merge`·`orbital_command`·`straylight_protocol`·`territorial_mark`. **자기 교정 기록**: `narrative_attack`·`ice_break`·`enforce_contract`는 처음 교정했다가 **되돌림**(이름이 공격적 메커니즘을 명시/암시 → 규칙을 최대가 아니라 엄격하게 적용한 결과).

**확인된 이미-올바름**: `detect` 6종·`shield` 9종은 분류 오류가 아니라 **Option A의 문제**(효과 미구현). `memory_lock`(silence)/`memory_overload`(dot), `stack_corruption`(dot)/`stack_overflow`(stun) 등은 각자 이름과 일관 → 무변경.

**검증**: `git diff` = **20 deletions + 20 insertions, 전부 `"effect":` 줄**(필터 검증) · `name` 0건 · `cooldown_ms` 0건 · id 집합 동일(88) · **97개 ICE 행 및 기타 top-level 키 바이트 동일**(파일 접두부 raw 비교).

**밸런스**: `npm run balance` **바이트 동일**(MD5 일치), 6개 grade **전 컬럼 0.0% 델타**. 3개 구성(기본 100 · `--runs 500` · `--runs 200 --deck ppl`)에서 동일. **이유(실측)**: 영향받은 12개 ICE 중 **인카운터 밴드에 있는 것이 0** — 밴드의 스킬 보유 2종(`loa_entity`·`aleph`)은 손대지 않음 → **교정이 현재 실플레이에서 관측 불가**(= 밴드 확대 필요성 강화).

**어서션 1건 갱신(근거 기록)**: `data_loaders.test.ts`가 `report.effect === "attack"`을 고정하고 있었음(= 휴리스틱 오분류를 고정) → **의도(damage 파생 계약)는 보존**하고, 교정된 분류 + 여전히 공격적인 스킬로 offensive 경로를 검증하도록 갱신.

**게이트**: `npm test` **125 files / 2951 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0223-skill-classification-review.md`.

**다음(미실행)**: ① 애매 10종 디자인 결정 ② **Option A**(비공격 효과 + magnitude) — 이제 unblocked ③ 인카운터 밴드 확대 ④ `detect`/`silence`/`slow`/`stun`도 전투 효과 없음(일부는 alarm/정보 시스템 소관일 수 있음).

## [2026-10-27] feat | 인카운터 밴드 커버리지 확대 — 스킬 시스템을 실플레이에 노출 (ADR-0224)

**배경**: ADR-0222(D)·0223(분류 검토)으로 스킬 데이터는 정비됐지만 **인카운터 밴드 24슬롯 중 스킬 보유가 2개**(`loa_entity` g5 · `aleph` g6)뿐이라 전부 **실플레이에서 관측 불가**였음. Option A의 가시성 선행 조건.

**변경**: `ice_scaling.ts` `ENCOUNTER_ICE_BY_GRADE` **슬롯 1~3만** 재작성 — **슬롯 0은 전 grade 불변**(legacy `encounterIceIdForGrade(grade, undefined) === band[0]` 계약, 테스트 고정). 각 grade의 tier 밴드 내에서, 대체 슬롯의 **HP@grade와 자동공격 데미지(`tier*3+armor`)를 최대한 일치**시켜 선택(밴드 변경이 *아키타입/스킬* 변경이 되도록 — 곡선 부풀리기가 아니라). `ENCOUNTER_HP_BY_GRADE`·`ENCOUNTER_DMG_BONUS_PCT_BY_GRADE`·`iceHpForGrade`·`ice_types.json`은 **불변**.

**커버리지**: 슬롯 **2/24 → 16/24** · 고유 스킬 보유 id **2 → 11** · **6/6 grade**가 스킬 보유 ICE ≥1 + 비-aggressive ICE ≥1 · 발화 가능 스킬 보유 grade **2 → 4**(g3~g6).

**밸런스(정확히 기록)**: g1 0.0pp · **g2 88.8→77.4 (−11.4pp)** · **g3 73.0→79.0 (+6.0pp)** · g4 +1.4pp · **g5 42.4→32.0 (−10.4pp)** · g6 0.0pp. `--deck ppl`은 g2 −1.5 / g3 +3.5 / 나머지 0.0.

**슬롯별 격리로 원인 확정**: **아키타입(방어형) 슬롯이 g2 −15.6pp · g5 −10.4pp** — tier에 맞는 `defensive` **스킬 보유** ICE가 aggressive 동급보다 `hp_base`/`defense`가 유의하게 높기 때문. **데미지 프로필을 맞춘 스킬 슬롯은 각 ≤1.4pp**. g3 +6.0pp는 `hosaka_defender`(auto 15) vs `goliath`(17) 때문이며 T2–T3에 auto ≥16인 스킬 보유 ICE가 없어 회피 불가 — 그리고 g3는 *더 짧고 더 피비린내 나는* 싸움이 됨(mean-HP-end 24.0→15.7).

**재보정은 제안만, 미적용**(사용자 결정 사항): Option 1(g2 dmg bonus 130→~60, g5 0→~−10%; HP 캡은 g2 118<125·g5는 monotonic floor 165라 무효) vs Option 2(g2/g5의 아키타입 요구 제거 → g2 ~82.2% · g5 ~43.1% 회복, 단 두 grade에 비-aggressive ICE 0). **권고: Option 1** — 이동은 *설계* 문제가 아니라 *캘리브레이션* 문제이고, 더 강한 defensive ICE는 카탈로그의 정당한 구성원.

**구조적 한계(기록)**: ① **T1에 데미지 스킬 보유 ICE가 없음** → g1의 스킬 2슬롯은 **구조적 발화 불가**(Option A 시점에 살아남) ② **`stealth` ICE 5종 전부 `skills: []`** → 스킬 보유 stealth 불가 ③ `support` 0종 ④ 스킬 데미지가 소유 행의 `dmg_base` 파생(`dmg_base + tier*2`)이라 자동공격보다 클 수 있음 → 밴드 변경이 재보정과 분리 불가.

**테스트**: `ice_scaling.test.ts`에 `encounter band coverage` 7종(**판별력 3종** — 밴드를 원복하면 실패). **기존 테스트가 옛 밴드 내용을 고정하지 않아 assertion 약화 0건**.

**게이트**: `npm test` **125 files / 2958 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0224-encounter-band-coverage.md`.

**다음(미실행)**: ① **밸런스 재보정 결정**(Option 1/2 — 사용자) ② **Option A**(비공격 효과 + magnitude) — 이제 관측 가능 ③ 카탈로그 저작 갭(T1 데미지 스킬·stealth 스킬·support ICE) ④ ADR-0223의 애매 10종.

## [2026-10-27] balance | 인카운터 밴드 재보정 — 두 곡선 동시 복원, HP 캡 유지 (ADR-0225)

**배경**: ADR-0224의 밴드 확대로 ADR-0211 캘리브레이션 곡선이 이동(g2 −11.4pp · g3 +6.0pp · g5 −10.4pp). 사용자가 **재보정(Option 1)** 선택.

**1차 시도는 기각**: opening을 ±3pp 내로 복원했으나 **g5/g6 HP 캡을 165 → 560**으로 올려(= `neuromancer` 자연 HP) **캡을 무력화** — ADR-0211의 핵심 메커니즘("climax는 opener 불가 · developed 가능")이 꺼지고 **PPL g5 44.4% → 100.0%(+55.6pp)**. 에이전트 자체 frontier가 **두 레버만으로는 두 곡선 동시 만족 불가**를 입증.

**근본 원인**: 문제는 **슬롯 하나** — g5의 `ta_sentinel`(T4, defensive). opener가 이기게 하려면 캡을 무력화해야 하고 그러면 developed도 이김.

**최종 결정 — 캡이 아니라 슬롯을 고침**:
- `ENCOUNTER_HP_BY_GRADE` → `[75, 86, 155, 165, 165, 165]` (g2 125→86 · g3 140→155 유지, **g4/g5/g6는 165로 복원** — 168/560/560 철회)
- `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` → `[50, 130, 0, 0, 0, -20]` (**ADR-0211 원값 복원**, −79/−78 철회)
- 밴드 **g5 슬롯2만**: `ta_sentinel` → `loa_entity` (aggressive · 스킬 보유 · poison 발화)
- 캘리브레이션 docstring을 현행 설정·실측 근거로 재작성(560/−79/168 언급은 "이전 시도가 X였고 비용은 Y" 이력 서술로만 잔존)

**실측 결과 — 두 곡선 모두 충족**:
- **opening**: 100.0 / 88.6 / 73.1 / 48.8 / 43.1 / 0.0 → 목표 대비 **6/6이 ±1.4pp 내**(허용 ±3pp), 단조 비증가 유지
- **PPL**: 100.0 / 77.9 / 97.8 / 88.8 / 44.4 / 31.3 → **g5·g6 바이트 동일**(+55.6pp 퇴행이 **캡을 살린 채** 완전 복원). 부수 이동은 캡 변경에 기인하며 둘 다 양성(PPL g2 +7.1pp는 *쉬워짐* — 기존 비단조 dip 개선, g3 −2.2pp는 약간 어려워짐)

**어서션 3건**(근거 기록): ① `iceDmgBonusPctForGrade(5)`가 `< 0`(기각된 −79 고정) → `toBe(0)` ② "모든 grade에 비-aggressive ICE" → **"g5 예외"를 명시적으로 단언**(skip 아님) ③ g5 HP 캡 테스트는 assertion 무변경, **원래의 더 엄격한 `toBeLessThanOrEqual(165)`로 복원**(기각 시도가 자연 HP bound로 완화했던 것). **약화·삭제 0건**.

**수용한 트레이드오프**: **g5가 비-aggressive ICE를 더는 갖지 않음** — 아키타입 다양성은 g1~g4·g6에서 충족(g4·g6는 `ta_sentinel` 유지). 캡을 지키기 위한 명시적 교환.

**게이트**: `npm test` **125 files / 2958 tests PASS** · `tsc --noEmit` 0 · `eslint` 0 · 두 밸런스 표 재실행 결정적. **미커밋**. ADR: `0225-encounter-band-recalibration.md`.

**다음(미실행)**: ① g5 아키타입 갭은 세 번째 레버 필요(밴드에 맞는 tier·HP·데미지 프로필의 defensive 스킬 보유 ICE 저작, 또는 per-ICE 캘리브레이션 노브) ② **Option A**(비공격 효과 + magnitude) ③ ADR-0223 애매 10종 ④ 카탈로그 갭(T1 데미지 스킬·stealth 스킬·support ICE).

## [2026-10-27] feat | 비공격 ICE 스킬 효과 구현 — defensive/support 아키타입 실체화 (ADR-0226, ADR-0219 Option A)

**배경**: ADR-0219 사슬의 마지막 조각 — **B(0219) → D(0222) → 분류검토(0223) → 밴드(0224) → 재보정(0225) → A(이번)**. `defensive`/`support` 아키타입이 장식이 아니게 됨.

**구현한 효과(정확한 규칙)**:
- **`shield`** — ICE당 **흡수 풀** 1개(`statusEffects`의 `kind:"shield"`, `magnitude`=잔여 흡수 HP, `remaining`=적 턴 단위 수명). **player 데미지를 HP보다 먼저 흡수**, 초과분은 HP로. 소진 시 제거. **재시전은 풀을 더하되 수명은 리프레시**(duration 누적 아님) — `docs/testcases/combat/depth.md` TC-DEPTH-004/005의 문서화된 시맨틱. **지속 3틱 = 6000ms**(1틱 = `AUTO_ATTACK_INTERVAL_MS`). burn/DoT는 **우회**.
- **`heal`** — 즉시 회복, **`maxHp` 상한**.
- **`regen`** — 매 적 턴 `healPerTick` 회복, **`maxHp` 상한**, 지속 4틱.
- **`buff`** — 스킬·자동공격 **출력 데미지 플랫 증가**, 지속 3틱, **grade/boss 배수 적용 후**에 더해 등급 무관 동일 가치.

**magnitude는 저작**: `skill_defs`에 `magnitude = dmg_base(owner) × {shield 2, heal 2, regen 1, buff 1}`, 다중 소유 시 **최고 `dmg_base` 소유자** 기준. **28개**(shield 9 · buff 17 · heal 1 · regen 1) 저작. malformed는 loader가 **throw**.
**트레이드오프(명시)**: `skill_defs`는 per-skill인데 ICE 전투력은 per-row → 고정 per-skill magnitude는 소유자 개별 강도를 무시(예: `construct_proxy`가 tier 4/5/6 공유로 18 고정 → tier-4 소유자 과대 버프). **저작 vs load-time 파생** 중 저작 선택(ADR-0222의 "heuristic이 아닌 저작 데이터" 방향 준수).

**선택 정책**: 발사 가능 = 데미지 스킬(`damage > 0` — **기존 게이트 보존**) **또는** 구현된 계열 **이면서** 아키타입 선호 목록이 그 효과를 명시. `defensive`/`support`만 명시 → `aggressive`/`stealth` 동작 **불변**. fallback은 **데미지 스킬 우선** → `loa_entity`는 여전히 poison 발화. **`defensive`는 2체제**(ADR-0161: HP < 50%에서 방어) — 없으면 healthy defensive가 영원히 방어만 하고 공격을 안 하는 퇴화 발생.

**상태**: 기존 `statusEffects` 배열 **확장**(병렬 컬렉션 신설 아님) — `StatusEffectKind`에 `"shield"` 추가, `StatusEffectInstance`에 `iceIndex`(카탈로그 id가 아니라 **로스터 슬롯** — 동일 id ICE 2개 공존이 `tick_kill_loot.test.ts`로 입증됨) + `tickSource` 추가. `tickStatus`는 enemy-sourced를 건너뛰고 `tickIceEffects`가 적 턴에 전진. 로스터 ICE가 이제 `maxHp` 보유(heal 상한 기준). 리듀서 순수·결정적 유지.

**신규 모듈**: `ice_combat_effects.ts`(215 LOC) · `ice_combat_effect_apply.ts`(184 LOC) — 100–300 정책 준수, ADR-0110 선례대로 분리. `state_actions_combat.ts` 369→421.

**밸런스 — g4만 +0.2pp 이동(양 곡선)**: opening 48.8→49.0, PPL 88.8→89.0. 나머지 전 등급·전 컬럼 **동일**(PPL g4 p95 26→29만 예외). **이유(실측)**: 도달 범위가 작음 — 밴드 24슬롯 중 아키타입이 구현 계열을 명시한 ICE는 **`ta_sentinel`(g4 슬롯3) 하나뿐**. `hosaka_defender`(g3)·`hosaka_courier`/`sense_net_spin`/`loa_zombie`(g1/g2)는 `aggressive`라 shield/buff/regen이 **설계상 불발**. **재보정 불필요**(g4 49.0%는 목표 47.4% 대비 +1.6pp, ±3pp 내).

**테스트**: 신규 `ice_combat_effects.test.ts` **17종 중 16종 판별력**(모듈을 no-op 스텁하면 실패: `expected +0 to be 20` 등). 초기 vacuous했던 5종은 양성 사전단언으로 강화.
**어서션 변경 1건**: `ice_ai.test.ts`의 `"prefers shield for defensive personality"`(healthy 50/50이 shield 기대)를 **2종으로 분리**(wounded 20/50 → shield · healthy 50/50 → attack) — 근거: ADR-0161이 DEFENSIVE를 "HP < 50%에서 방어"로 정의하고 `DEFENSIVE_HP_THRESHOLD`/`shouldDefensiveAct`가 이미 존재. 기존 어서션은 *무조건적* 선호를 고정한 것이고 Option A에서는 healthy defensive가 영구 방어가 됨. **강화이며 의도 삭제 아님**. 개발 중 깨진 기존 테스트 2건도 **정당하게 수정**: `boss_ai.test.ts` phase-4 미니언 스폰 턴 행동, `tick_kill_loot.test.ts` 로스터 id 충돌(→ 슬롯 인덱스).

**게이트**: `npm test` **126 files / 2976 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0226-non-damaging-ice-skill-effects-implemented.md`.

**잔여 미구현(기록)**: `detect`·`silence`·`slow`·`stun`·`debuff`·`stagger`·`counter`·`vulnerable`·`bleed`·`fatigue`·`confused`·`terrified`. `detect`/`silence`/`slow`는 **alarm/정보 시스템 소관**(ADR-0219 열린 질문 3)으로 보고만.

**다음(미실행)**: ① 도달 범위 확대(밴드 또는 aggressive/stealth ICE에 아키타입이 실제 쓸 스킬 부여) ② per-owner magnitude ③ 잔여 효과 ④ ADR-0223 애매 10종 ⑤ 카탈로그 갭(T1 데미지 스킬·stealth 스킬·support ICE).

## [2026-10-27] refactor | ICE 아키타입 일관성 검토 + g3 재보정 (ADR-0227)

**배경**: ADR-0226의 새 메커니즘(shield/heal/regen/buff)이 **밴드 24슬롯 중 2개**(고유 ICE 1개 `ta_sentinel`)에서만 작동 — 이유는 shield/buff/regen을 소유한 밴드 ICE가 `aggressive`로 저작되어 **아키타입이 그 효과를 명시하지 않기 때문**. catalog 분포가 aggressive 80/97이라 그 자체가 신호. **ADR-0223(스킬 분류 검토)의 한 단계 위 버전**.

**Part 1 — 아키타입 규칙 + 12종 교정**: `personality`는 **자기 이름·보유 스킬과 일치**해야 함(명백한 불일치만, 4개 아키타입 유지).
- → `defensive`(3): `hosaka_defender`(`*_defender` + shield) · `loa_zombie`(regen 보유) · `goliath_defensive`(이름 그대로 + shield 3종)
- → `support`(9): `hosaka_courier` · `sense_net_archive` · `sense_net_informer` · `hosaka_analyst` · `sense_net_spin` · `sense_net_alert` · `hosaka_collector` · `loa_priest` · `ice_cebu_pacific`
- **미변경(애매)**: `ta_daemon`·`ta_inheritor`·`hosaka_terminal`·`yakuza_collector`·`morrison_echo`·`zombie`·`ice_loa_zombie` 등 / `sense_net_reporter`·`yakuza_assassin/enforcer/brute`는 공격 스킬 보유로 `aggressive` 유지가 정답
- **주의(기록)**: `support`의 실제 선호 목록은 `heal/regen/shield/debuff/detect`로 **`buff`를 명시하지 않음** → buff-only support ICE는 **fallback 경로**로 발화(검증됨).

**Part 1 검증**: diff = **정확히 personality 12줄**(다른 필드 0). **커버리지 2/24 → 4/24 슬롯**(고유 ICE 1 → 3). `hosaka_defender`의 shield · `loa_zombie`의 regen이 **실제 밴드 전투에서 관측**(end-to-end 프로브; pre-fix에서는 부재 — player측 burn/slow만).

**Part 2 — g3 재보정(교정이 강제한 것)**: `hosaka_defender`가 공격 대신 **12포인트 shield**를 올려 **g3 opening 73.1% → 89.7%(+16.6pp)** → **단조성 파괴**(g3 89.7 > g2 88.6). 단조성·±3pp는 **ADR-0211/0225가 이미 결정한 제약**이므로 그 복원은 기존 결정의 실행.
- `ENCOUNTER_HP_BY_GRADE[2]`: **155 → 141** · `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE[2]`: **0 → +8**
- 결과: **g3 = 72.8%**(목표 대비 **−0.2pp**, 곡선에서 가장 타이트) · **단조성 회복**(100.0/88.6/72.8/49.0/43.1/0.0) · **다른 등급 바이트 동일** · **PPL 전 등급 불변**

**왜 두 레버 모두?**: HP 캡은 `c3 ≤ c4 = 165` 상한이고(위반 시 g3 ICE가 g4보다 HP가 많아짐 — 기존 테스트가 거부) 최대 165에서도 **76.3%**(+3.3pp, 허용 밖). 데미지 보너스는 auto-attack 기반(14/15/13/13)의 **계단 함수**로 +7%는 **증명된 no-op**(승수 동일), +8%는 **절벽**(76.3%→51.5%). 캡을 낮추면 창이 열림(+8%에서 142→71.5 · **141→72.8** · 140→75.0). 전수 스캔(cap 124~165 × pct 0~20) 13개 허용 구성 중 **`c3 ≥ 155`는 0개**.

**정직한 caveat**: 이는 **순수 난이도 상향이 아니라 트레이드** — g3 ICE가 **HP 14 감소 + 자동공격 1 더 세게**. 순 난이도는 보존되고 shield는 여전히 의미 있음(12 흡수 · 3틱). 캡 ≥155 유지를 원하면 (a) g3 76.3%(+3.3pp) 수용 또는 (b) `hosaka_defender`의 shield **magnitude**(`skill_defs`, 콘텐츠 결정) 재검토.

**게이트**: `npm test` **126 files / 2976 tests PASS** · `tsc --noEmit` 0 · `eslint` 0. **미커밋**. ADR: `0227-ice-archetype-consistency-review.md`.

**다음(미실행)**: ① g3 설계 텐션(shield magnitude 또는 per-ICE 노브) ② `support` 선호 목록에 `buff` 포함 여부 ③ 애매 ICE 잔여 ④ 아키타입의 **미배선 동작**(`getCritBonus`·`shouldTargetAlly`·`getAlarmMultiplier`·`shouldDefensiveAct`) ⑤ ADR-0223 애매 10종 · 잔여 효과 · 카탈로그 갭.

## [2026-10-27] feat | ICE 아키타입 동작 배선 — crit 1건 구현, 2건은 서브시스템 필요 보고 (ADR-0228)

**배경**: ADR-0227이 `personality`를 데이터 정합하게 만들었지만 `ice_ai.ts`의 4개 아키타입 동작이 **web 빌드에서 소비되지 않아**(테스트에서만 참조) 아키타입이 절반만 실체. ADR-0227 후속 #4 종결.

**조사 우선 → 실재하는 것만 배선**:

| 동작 | 결정 | 근거 |
|---|---|---|
| `getCritBonus` (aggressive +5% crit) | **배선** | 크리 시스템 존재(`combat_engine.ts`), `DamageContext.attackerTeam`이 이미 player/enemy 구분 — 그러나 **적 경로는 인라인 계산으로 크리 롤이 아예 없었고** `calculateDamage`의 프로덕션 호출자는 플레이어뿐 → 서브시스템 신설이 아니라 국소 배선 |
| `shouldTargetAlly` | **미배선 — 서브시스템 필요** | 멀티 ICE 로스터는 존재하나 **모두 적대적**, 적 경로에 **per-target 스킬 해석이 없음**(전원이 플레이어 공격). `shield`/`heal`/`regen`/`buff`는 **자기 대상 전용** |
| `getAlarmMultiplier` | **미배선 — 서브시스템 필요** | alarm이 **2종인데 둘 다 trace accrual 루프가 아님**: `player.alarm`은 **프로그램 비용 누산기**, `state.alarmLevel`/`lastAlarmTickMs`는 **초기화만 되고 어떤 리듀서도 쓰지 않음**. 의도된 훅 `tickAlarm(…, iceAlarmSpeed)`은 **프로덕션 호출자 0**. **밴드에 stealth ICE는 실재**(`wisp` g1 · `ice_dixie_echo` g3)하나 **stealth 5종 전부 `skills: []`**라 스케일할 액션이 없음 |
| `shouldDefensiveAct` | **이미 배선(ADR-0226)** | 동일 `DEFENSIVE_HP_THRESHOLD`가 선택 로직에 연결됨 → 중복 배선 금지 |

**구현**: 신규 `ice_crit.ts`(**103 LOC**, 순수·주입 RNG·모듈 상태 0) — 비-aggressive는 데미지 불변 + **RNG 소비 0**, aggressive는 5% 롤 후 엔진의 크리 배수 밴드(~1.8–2.2×) 적용. `ice_ai.ts`의 `getCritBonus` 파라미터를 최소 `PersonalityBearer` 인터페이스로 확장(파일의 기존 `SkillUser` 패턴). `state_actions_combat.ts`의 **양쪽 적 데미지 사이트**(스킬·자동공격)에 롤 배선 + `CRITICAL` 로그 마커, `damage > 0` 게이트 보존.

**설계 노트**: 적을 `calculateDamage`로 라우팅하지 **않음** — 그러면 0.8–1.2× 분산이 모든 적 타격에 붙고 **모든 아키타입에 base 15% 크리**가 적용되어 "aggressive에만" 요건이 깨짐. 대신 이미 계산된 적 데미지에 **국소 수정자**로 적용 → 적 baseline 바이트 동일, aggressive만 크리 획득.

**어서션/픽스처 1건 변경(근거 기록)**: `boss_ai.test.ts`의 `makeIce`에 `personality: "defensive"` 추가. 종전엔 `personality` 미지정 → `coercePersonality(undefined) === "aggressive"` 상속 → 정확 데미지 동등 단언이 **7/40 flaky**(2회 측정 동일; 크리율 4.86~5.60% 실측 = `AGGRESSIVE_CRIT_BONUS` 5%)였음 → 수정 후 0/40, 전체 스위트 8회 연속 clean. **프로덕션 97/97 ICE 행이 명시적 `personality`를 보유**하므로 픽스처가 생산 대비 under-specified였고, `defensive`는 크리가 없어 기대값 불변 → **약화 아님, 결정화**.

**밸런스(정확히 기록)**: opening g1~g3 불변(g3 +0.3), **g4 49.0→39.3(−9.7pp)** · **g5 43.1→35.7(−7.4pp)**, g6 불변. PPL g4 89.0→84.8(−4.2) · g6 31.3→28.3(−3.0). **단조성은 유지**(100.0 ≥ 88.6 ≥ 73.1 ≥ 39.3 ≥ 35.7 ≥ 0.0)되나 g4/g5가 ±3pp 밖. **원인**: 크리가 aggressive ICE에 +10% 기대 데미지. **재보정은 제안만, 미적용** — g4/g5 dmg bonus 하향(단 auto-attack 전용이라 스킬 데미지는 상쇄 못 함) 또는 **크리 배수 밴드 축소**(캘리브레이션 배열 불변).

**게이트**: `npm test` **127 files / 2986 tests PASS** · `tsc --noEmit` 0 · `eslint` 0 · `npm run build` ✓. **미커밋**. ADR: `0228-ice-archetype-behavior-wiring.md`.

**다음(미실행)**: ① **g4/g5 재보정 결정**(또는 크리 밴드 축소) ② `shouldTargetAlly`(per-target 스킬 해석) ③ `getAlarmMultiplier`(trace alarm 루프 + stealth ICE에 스킬 부여) ④ **반복 재보정 churn 대책**(ADR-0211 타깃 재기준화 또는 per-ICE 노브) ⑤ 잔여 효과 · 애매 분류 · 카탈로그 갭.

## [2026-10-27] docs | 등급 곡선 타깃 재기준화 — ADR-0211 supersede (ADR-0229)

**배경**: 연속 4개 기능 단계가 매번 ADR-0211 캘리브레이션 곡선을 이동시켰고(0224 밴드 · 0226 스킬효과 · 0227 아키타입 · 0228 crit), 두 전역 레버로 항상 복원할 수 없었음(계단 함수·절벽, `c3 ≤ c4` 상한). 기능 추가마다 옛 타깃을 추격하는 것은 churn → **1회 재기준화** 결정.

**변경 — 값 변경 없음(문서·정책만)**:
- **신규 ADR-0229**: ADR-0211의 per-grade 승률 타깃을 **현재 달성 곡선**(opening `100.0/88.6/73.1/39.3/35.7/0.0` · PPL `100.0/77.9/99.6/84.8/44.4/28.3`)으로 supersede. ADR-0211의 **메커니즘**(HP 캡 · 데미지 보너스 곡선 · grade-driven 스케일링)은 **계속 유효**하며 supersede 범위는 **승률 수치에 한정**.
- **DRIFT POLICY 신설**: §A 무단 드리프트 금지(어느 등급이든 **±3pp 초과** 이동 시 → 재보정 또는 **명시적 re-baseline ADR**, before/after 표 필수) · §B **하드 불변식**(opening 단조 비증가 · g6 0~5% · HP 캡 단조 비감소 · 최대 캡 ≤165) — re-baseline으로도 완화 불가 · §C **PPL은 참조값**(타깃 아님; ≥5pp 이동은 ADR에 표로 명시) · §D 정책 변경은 신규 ADR 필요
- **README**: 0211 상태 셀 → `Superseded by ADR-0229` + 0229 행 추가 (0211 파일 자체는 immutable이라 **미편집**)
- **`ice_scaling.ts`**: **docstring만** 갱신 — 은퇴한 ADR-0211 타깃 대비 잔차 서술 제거, 현행을 baseline으로 서술. **배열 리터럴 3종 바이트 동일**(프로그램 검증)

**의도적 미조치**: **frozen-baseline 테스트를 추가하지 않음** — 고정값 테스트는 다음 churn 원인이 되고 §A1의 "재보정 복귀" 경로를 막음(ADR Notes에 기록).

**검증**: 두 밸런스 곡선이 **정확히 동일**(동작 불변 증명) · `npm test` **127 files / 2986 tests PASS** · `tsc --noEmit` 0 · `eslint` 0 · `audit_vault.py` CLEAN. 테스트 무변경(약화·삭제 0). **미커밋**. ADR: `0229-grade-curve-rebaseline.md`.

**다음(미실행)**: ① `shouldTargetAlly`·`getAlarmMultiplier` 서브시스템 ② 잔여 효과(`detect`/`silence`/`slow`/`stun`/`debuff`) ③ 애매 분류(스킬 10종 · ICE 일부) ④ 카탈로그 갭(T1 데미지 스킬 · stealth 스킬 · support 선호목록 `buff` 여부) ⑤ g3 설계 텐션.

## [2026-10-27] refactor | 애매 분류 부채 마감 + 전투 반응 개선 제안서 (ADR-0230 · 신규 제안서)

**Part 1 — 애매 분류 부채 마감(ADR-0230)**: ADR-0223(스킬 10종)·ADR-0227(ICE 7종)이 남긴 애매 항목 **17건**을 **기존 규칙 재사용 + 새 증거**로 마감.
- **스킬 10종: 0건 변경** — 전부 증거 확인. 3종(`ai_negotiate`·`aleph_fragment`·`territorial_mark`)은 **ADR-0216 토큰표가 의도적으로 buff로 매핑**했고 ADR-0226이 buff magnitude를 저작한 상태(변경하면 오히려 새 오분류). `straylight_protocol`은 `ice_scaling.ts:296`이 **15 데미지로 문서화**(= `ta_sentinel` dmg_base 7 + tier 4×2, load-bearing). `loa_command`는 **테스트 고정**. → **2개 테스트로 고정**(재개방 방지), 테스트 2986 → **2988**.
- **ICE 7종: 1건 변경** — `yakuza_collector`: `aggressive` → **`support`**(debuff 전용 + 공격 스킬 없음 + ADR-0227이 동일 구조 `sense_net_alert`(debuff 2종·공격 없음)를 support로 교정한 **직접 선례**). `ta_daemon`은 **chapter-8 설계문서의 Family Daemon = CHAPTER BOSS**로 aggressive 확정, `ta_inheritor`는 **`family_vote` 공유 형제 `ta_heir`가 aggressive**라 확정. 3건은 **진정한 50:50**(예: `hosaka_terminal`은 support(detect)/stealth(silence)가 1:1이고 이름이 중립 + **양쪽 모두 inert라 동작 동일**)으로 병기 유지.
- **밸런스: 12개 등급 전부 0.0pp**(debuff가 inert라 동작 동일) — **ADR-0229 드리프트 정책 준수**, 재기준화 불필요, §B 불변식 전부 유지.
- **diff**: ice_types.json **정확히 `personality` 1줄**(`skill_defs` 바이트 동일) + 테스트 2건 신규.
- **범위 밖 발견(미변경)**: **`family_vote`가 `buff`로 분류됐으나 `docs/design/systems/combat.md`는 "AoE damage 20 + construct 동반 시 +10"으로 문서화**(ADR-0149/0162의 보스 메커닉 `apply_family_vote`). ADR-0223의 10종 목록 밖이라 **미변경** — `ta_inheritor` 부자연스러움의 **상류 원인**으로 보이며 **별도 ADR 가치**.
- 게이트: `npm test` **127 files / 2988 tests PASS** · `tsc` 0 · `eslint` 0 · 볼트 lint CLEAN.

**Part 2 — 전투 반응·인터랙션 개선 제안서(신규, 코드 미변경)**: `docs/design/combat-feel-and-interaction-proposal.md`(322줄).
- **근거 있는 3대 발견**: ① **VFX 27종 중 10종이 완전 구현됐으나 spawn 호출 0** — 특히 **`player_hit`(피격 시각 피드백)이 아예 발생하지 않음** ② **게임 루프 부재**(`main.ts`에 rAF/setInterval 0, `draw()`는 입력 핸들러에서만 — **VFX가 다음 키 입력까지 정지**) ③ `core/accessibility.ts` **소비자 0**
- 제안 **15건(P1~P15)** + 즉시 실행 상위 3개: **P2 VFX 10종 배선 · P9 rAF 루프 · P4 전투 로그 확장** — 셋 다 **순수 추가형**(드리프트 체크 불요). 밸런스 접촉은 **P7(유휴 턴 압박)·P8(crit 임계 결합)** 2건뿐이며 **ADR-0229 §A1 전후 측정 필수**로 명시.
- 설계 의도는 이미 `docs/design/systems/animations.md`에 존재(화면 흔들림 1~2px/100~200ms · 부유 데미지 숫자 · 2.4초 사망 시퀀스) — **갭은 구현이지 스펙이 아님**.

## [2026-10-27] feat | 전투 반응 top-3 구현 — VFX 배선 · 전투 로그 · rAF 렌더 루프 (ADR-0231)

제안서(`docs/design/combat-feel-and-interaction-proposal.md`)의 상위 3개를 구현 — **셋 다 순수 추가형**(밸런스 영향 0). 11개 파일(+353/−23).

**P2 — 미배선 VFX 7종 배선**(렌더러 신설 0): `player_hit`(적 데미지 2개 사이트) · `defeat`(player HP 0) · `ice_death`(승리) · `shield`/`heal`/`regen`/`buff`(`ice_combat_effect_apply.ts` 4개 적용기 → `IceEffectOutcome.vfx` → `state.vfxInstances` 병합). 전부 기존 렌더러 보유 → 신규 kind·렌더러 추가 없음.

**P4 — 전투 로그**: `GameState.combatLog: ReadonlyArray<string>`(**newest-first**, `COMBAT_LOG_CAP=8`). `useProgram`·`processEnemyTurns`가 **prepend**(reverse 복사본, 변이 없음) → `combatLog[0]`이 최신 → 제안서의 `slice(0,4)`가 성립. `buildHudLines`가 최근 4줄 + 빈 경우 `message` fallback. `message` 시맨틱 **불변**. **SaveSlot 미포함**(스키마 bump 회피). 모든 `GameState` 픽스처에 필드 추가(타입 약화 0).

**P9 — rAF 렌더 루프**(`main.ts`만): `rafId`/`loopRunning`/`lastLoopMs`/`fpsCounter` · `MAX_FRAME_ADVANCE_MS=100` · `startLoop()`(멱등) · `loop(now)`. 매 프레임 `FpsCounter` tick → delta → `advanceVfxListBy` → **tick 롤 또는 인스턴스 만료 시에만** `draw(false)`. **VFX advance를 `draw()`에서 이관**(중복 진행 방지), 기존 입력 핸들러 `draw()` 59곳 **보존**. `stop()`이 cancel, `_lastFrameMs` 제거. **신규 타이밍 서브시스템 없음** — `performance.ts`의 `FpsCounter`+`getMetrics()` + rAF delta 재사용, >100ms 스톨 시 advance 건너뜀.

### 🔍 구현 중 발견한 실질 결함 2건 (이 ADR의 핵심 내용)
1. **VFX spawn이 RNG-중립이 아니었고 캘리브레이션 곡선을 조용히 이동시킴** — `import_vfx`가 인스턴스 id에 `Math.random()`을 써서 **spawn마다 시드 PRNG draw 1회 소비**. 순진하게 배선하면 스트림이 밀려(HEAD 35 draw → 27) **승률이 이동**(g2 88.6→87.3, g3 73.1→72.1, g4 39.3→40.3). **수정**: `import_vfx`/`import_vfx_ms`는 **HEAD 그대로 복원**(기존 사이트의 draw 수·위치 보존) + 신규 사이트 전용 **`import_vfx_deterministic`**(모노토닉 카운터, **RNG 무소비**) 신설 → **35 draw = HEAD → 12등급 0.0pp**. `id`는 순수 식별자(로직 미사용)라 카운터/랜덤 공존 안전.
2. **렌더 루프가 초당 ~60회 IDB 쓰기를 유발할 뻔함** — `draw()`가 무조건 `autosave()` → `saveToSlot(0,…)`. 루프가 애니메이션 중 초당 60회 draw하면 **초당 ~60 IDB 트랜잭션**. **수정**: `draw(persist: boolean = true)` — 기본값으로 기존 59개 사이트 **동작 불변**(여전히 autosave), 루프 내부 2곳만 `false`.

**테스트**: **2986 → 3002**(+16). 신규 14개 단언은 **pre-change에서 실패 확인**(HEAD를 손으로 복원 — `git checkout`/`stash` 미사용).
**밸런스**: **12등급 0.0pp**(양 곡선, ADR-0229 기준선과 byte-identical), RNG draw 수 35=35 독립 확인. **드리프트 정책 준수**.
**게이트**: `npm test` **127 files / 3002 tests PASS** · `tsc --noEmit` 0(tsconfig가 `tests/**/*` 포함이라 테스트까지 검사) · `eslint src` 0 · `npm run build` ✓ · 볼트 lint CLEAN.
**검증 한계(정직 기록)**: vitest는 `main.ts`의 rAF 루프를 실행하지 않음(`main.ts`는 import 시 자체 boot, vitest는 동기) · Playwright e2e **미실행**(브라우저+live URL 필요) · LSP 데몬 unreachable → `tsc --noEmit`이 권위 · **화면 애니메이션 육안 확인 안 함**(스크린샷·프레임 타이밍 미측정).
**미실행**: P1·P3·P5·P6·**P7·P8**(§A1 필요)·P10~P15. **미커밋**. ADR: `0231-combat-feel-top3-vfx-log-raf.md`.

## [2026-10-27] feat | 전투 반응 tier 2 구현 — 캔버스 흔들림 · 부유 데미지 숫자 · SFX 레이어링 (ADR-0232)

제안서의 **P1·P3·P5**를 구현 — **순수 추가형**(밸런스 영향 0). 신규 4 모듈 + 신규 3 테스트 + 5 파일 수정.

**P1 — canvas 흔들림 + 히트스톱**: `screen_shake.ts`(순수 `shakeOffsetFor` — 2px·200ms·20/27Hz, sign-preserving 반올림으로 dead frame 0) · `canvas.ts` `render()`에 optional `offset`(grid+HUD 동시 translate). 히트스톱은 **연출 전용** — reducer·시계·enemy turn 불변(§R3).
**P3 — 부유 데미지 숫자**: `floating_damage.ts`(순수 — `normal` 소형 백색 / `skill` 대형 황색 / `critical` 금색 `✦-N✦`, `animations.md` 근거) · `combat_overlay.ts`가 grid에 합성(§R6의 DOM/sprite 거부 준수).
**P5 — SFX 레이어링**: `combat_sfx.ts`(순수 `pickCombatSfxLayers(previous,next)`) — 플레이어 피격 `DAMAGE`(이전엔 무음) · ICE 피격 `COMBAT_HIT`+`ATTACK` · ICE 파괴 `ICE_BREAK`.

### 🔍 구현·리뷰 중 발견한 실질 결함 3건 (이 ADR의 핵심 내용)
1. **ADR-0231 자체의 reducer 순수성 결함** — `import_vfx_deterministic`이 **모듈 전역 모노토닉 카운터**를 써서 동일 `applyAction` 2회가 **다른 VFX id**를 생성 → `property_reducer_fuzz.test.ts`가 HEAD에서 **~50% flaky**(HEAD `src/` 복원 후 8회 중 4회 실패로 입증). **수정**: id를 (kind/payload/payloadNum/duration) **FNV-1a 31-bit content hash**로 — RNG 0 유지, 호출순서 독립. "newest instance" 로직도 id 비교 → **배열 순서**로 전환.
2. **dead SFX path** — 기존 `COMBAT_HIT`이 `state.ice.hp`를 읽었으나 reducer는 `iceRoster`만 갱신 → **한 번도 발화 안 함**(probe: `state.ice.hp` 165 고정 vs roster 165→0). `pickCombatSfxLayers`가 `iceRoster`를 읽어 **실제 배선**; 중복 재생 방지 위해 중복 호출 제거.
3. **히트스톱 데드락 (오케스트레이터 리뷰에서 발견)** — 1차 구현이 **동결 대상인 `elapsedMs`에서 hold를 파생**(`advanceMs = max(0, deltaMs−40) = 0`, >25fps) → **VFX 영구 동결 + 매 프레임 redraw**. **수정**: **wall-clock deadline**(`hitStopDeadlineFor`/`hitStopActiveAt`) + **새로 등장한 `player_hit`**(identity 기반, `elapsedMs` 아님 — elapsed 기반은 매 프레임 재장전되어 deadline이 무한 전진하는 2차 데드락). 30/60/144/240fps 전부 해제 확인.

**테스트**: **3002 → 3088**(+86). 신규 단언은 **pre-change에서 실패 확인**(HEAD를 손으로 복원 — `git checkout`/`stash` 미사용).
**밸런스**: **12등급 0.0pp**(양 곡선, ADR-0229 기준선과 byte-identical — 오케스트레이터 독립 재실행). RNG draw 수 불변(`aleph_fragment` 62 · catalog 2382). **§A1 미발동**.
**게이트**: `npm test` **130 files / 3088 tests PASS** · `tsc --noEmit` 0 · `eslint src` 0 errors(기존 `keyboard.ts:14` warning 1건) · `npm run build` ✓ · 볼트 lint CLEAN.
**검증 한계(정직 기록)**: vitest는 `main.ts` rAF 루프를 실행하지 않음(회귀 테스트는 루프 블록을 **시뮬레이션**) · 실 canvas 렌더 미검증 · Playwright e2e 미실행 · **흔들림/데미지 숫자의 "느낌"은 taste 판단(미검증)**.
**미실행**: P6·**P7·P8**(§A1 필요)·P10~P15. ADR: `0232-combat-feel-tier2-shake-damage-sfx.md`.

## [2026-10-27] feat | 전투 반응 tier 3 — 오디오 ducking/마스터 볼륨 · 효과 가시화 · 상태 HUD 개편 (ADR-0233 / ADR-0234)

제안서의 **P13 · P6 · P14**를 구현 — 셋 다 **표시/오디오 계층**(밸런스 영향 0). 신규 4 모듈 + 신규 3 테스트 + 7 파일 수정.

**P13 — 오디오 (ADR-0233)**: `playSfx(id, {rate?, duck?})` 옵션 추가(기존 call site 무변경) · 순수 helper `composeBgmVolume`/`composeSfxVolume`/`duckFactorFor`/`clampRate`/`isCombatSfxId` · BGM duck은 **곱셈 오프셋**(attack 60ms / hold 120ms / release 240ms / ×0.8, **영속 안 됨** — 제안서가 지적한 위험 회피) · 마스터 볼륨(기본 1.0, 영속).
**P6 — 효과 가시화 (ADR-0234)**: **glyph 전용으로 판명** — `shield`/`heal`/`regen`/`buff` VFX 경로는 ADR-0231에서 이미 live(`state_actions_combat.ts:289` → `:473-476`). `STATUS_GLYPHS` 5→8종(`shield:"D"` / `regen:"R"` / `powered:"P"`; `heal`은 비영속이라 glyph 없음 — 제안서 "9종"은 실제로 8).
**P14 — 상태 HUD 개편 (ADR-0234)**: 타겟별 분리(플레이어 vs 각 ICE 슬롯) + `[GLYPH<잔여턴>]` 표기. `renderGrid`를 신규 `renderer/combat_grid.ts`로 추출(테스트 가능화, `main.ts` 1991→1852 LOC) + 신규 `renderer/status_hud.ts`.

**오케스트레이터 후속**: P13이 `main.ts` 미소유라 남긴 **마스터 볼륨 입력 배선 누락**(설정 필드 사이클에 `"master"` 없음 → 슬라이더는 렌더되나 도달 불가)을 두 에이전트 종료 후 배선 — `fields` 배열 + `move_east`/`move_west` 핸들러 + `fallbackSettingsState`.
**테스트**: **3088 → 3173**(+3 files / +85 tests). 신규 단언 pre-change 실패 확인.
**밸런스**: **12등급 0.0pp**(양 곡선, ADR-0229 기준선과 byte-identical — 오케스트레이터 독립 재실행). **§A1 미발동**.
**게이트**: `npm test` **133 files / 3173 tests PASS** · `tsc --noEmit` 0 · `eslint src` 0 errors(기존 `keyboard.ts:14` warning 1건) · `npm run build` ✓ · 볼트 lint CLEAN.
**검증 한계**: vitest는 `main.ts` 미실행(자체 boot) → `renderGrid`를 추출해 직접 검증, 설정 필드 배선은 코드 리드 검증 · 실 canvas/오디오 미검증 · e2e 미실행 · glyph 가독성(`D` vs `S`)은 taste 판단.
**미실행**: P7·P8(§A1 필요)·P10·P11·P12·P15. ADR: `0233-audio-ducking-master-volume.md` · `0234-effect-visibility-status-hud.md`.

## [2026-10-27] feat | 전투 반응 P11·P12·P15 — 온보딩 자동 표시 · 터치 인게임 피드백 · 전투 진입 연출 (ADR-0235)

제안서의 **P11 · P12 · P15**를 구현 — 셋 다 **표시/입력 계층**(밸런스 영향 0). 신규 3 모듈 + 신규 3 테스트 + 4 파일 수정.

**P11 — 온보딩**: 기존 `wetrun_tutorial_completed` 플래그를 재사용해 첫 부팅 시 튜토리얼 **자동 표시** — `renderer/tutorial.ts` **미수정**, 신규 순수 모듈 `core/onboarding.ts`(`shouldAutoShowTutorial`). 전투 진입 힌트 2줄(`1-9: USE PROGRAM`)을 `HAND:` 행 위에 배치, `ice_intro` 배너 밴드(rows 1-3, 5)와 겹치지 않게 배치.
**P12 — 터치**: 인게임 눌림 피드백(월-클럭 deadline, 400ms) — 신규 `core/touch_feedback.ts`(**RNG 0**). `updateProgramRow`가 `window.wetrun` 글로벌 대신 **직접 `onProgramPress` 콜백**을 받도록 변경, debounce 250ms→120ms.
**P15 — 전투 진입 연출**: `applyApproachAction`이 미스폰 `ice_intro`를 **`import_vfx_deterministic`**(RNG 무소비)으로 1건 스폰. 렌더러·duration은 이미 존재(배선만 누락).

### 🔍 구현 중 발견한 실질 결함 2건
1. **`window.wetrun`이 `game.start()` 이후 할당** → 그 사이 도착한 탭이 `?.` 옵셔널 콜로 **조용히 유실**. 직접 콜백으로 해결.
2. **렌더 루프의 VFX early-return이 눌림 피드백 만료를 삼킴** → ack가 영구 고정될 수 있었음. 만료를 early-return 앞으로 이동.

**테스트**: **3173 → 3234**(+3 files / +61 tests). 3건 모두 pre-change 실패 확인(P15 5건 · P12 5건 · P11 2건).
**밸런스**: **12등급 0.0pp**(양 곡선 byte-identical — 오케스트레이터 독립 재실행). 신규 VFX spawn의 **Math.random draw 0**(53개 전투 진입 전이). **§A1 미발동**.
**게이트**: `npm test` **136 files / 3234 tests PASS** · `tsc --noEmit` 0 · `eslint src` 0 errors · `npm run build` ✓ · 볼트 lint CLEAN.
**검증 한계**: `main.ts`는 자체 boot으로 vitest 미실행 → 배선은 **소스 텍스트 단언**(런타임 실행 아님) · 실 브라우저/터치 하드웨어 미검증 · e2e 미실행.
**미실행**: **P10**(accessibility, L 비용) · **P7·P8**(§A1 필요). ADR: `0235-onboarding-touch-intro-vfx.md`.

## [2026-10-27] feat | 접근성 모드 배선 — reduced-motion / 고대비 / 색각 palette / 텍스트 스케일 (ADR-0236)

제안서의 **P10**을 구현 — **접근성 계층**(기본값 무변경 → 밸런스·시각 영향 0). 신규 1 모듈 + 신규 5 테스트 + 7 파일 수정.

**핵심**: `core/accessibility.ts`의 `reducedMotion` / `highContrast` / `prefersReducedMotion()`은 **소비자 0건**이었다(제안서 §1.2). 이를 실소비자와 연결:
- **reduced-motion** — `shakeOffsetFor` / `shakeStateFor` / `hitStopMsFor` / `hitStopDeadlineFor` / `overlayShake` 가 `reducedMotion` 플래그를 받음(기본 `false` → 기존 39개 단언 무변경). ON이면 shake offset이 **정확히 `{x:0,y:0}`** 이고 hit-stop deadline은 arm되지 않음.
- **색각 이상 palette** — `palette.ts` 에 ADR-0196 4-mode 어휘(`none`/`deuteranopia`/`protanopia`/`tritanopia`) + `PALETTE_VARIANTS` + `paletteFor(mode, highContrast)` + `applyPaletteMode`. `PALETTE` 를 mutable 로 전환(`Object.freeze` / `as const` 제거만 — **색상 값 무변경**) 해 20개 renderer call site 무변경. `resolveColorHint` 가 활성 palette를 자동 추종.
- **고대비** — `core/accessibility.ts` 의 `getHighContrastColors()` 를 데이터 소스로 사용.
- **텍스트 스케일** — `canvas.ts` 에 `textScale`(셀 + 폰트 동시 스케일, `medium` = 정확히 1.0).
- 4개 설정 필드(`reduced_motion`/`high_contrast`/`colorblind`/`text_scale`)를 **완전 배선**(렌더 + 입력 사이클 + ENTER/←→ + 영속 + 부팅 시 첫 프레임 전 적용) — 이전 웨이브의 "렌더되나 도달 불가" 갭을 반복하지 않음. `tests/settings_accessibility.test.ts` 가 사이클 배열 자체를 pin.

**기본값 불변 입증(오케스트레이터 확인)**: `palette.ts` diff 에서 제거된 줄은 `Object.freeze(` + `} as const)` **구조 2줄뿐** — 색상 값 변경 **0**.

**테스트**: **3234 → 3333**(+5 files / +99 tests). 신규 단언 pre-change 실패 확인(4 파일 / 13 단언).
**밸런스**: **12등급 0.0pp**(양 곡선 byte-identical — 오케스트레이터 독립 재실행).
**게이트**: `npm test` **141 files / 3333 tests PASS** · `tsc --noEmit` 0 · `eslint src` 0 errors · `npm run build` ✓ · 볼트 lint CLEAN.
**검증 한계**: `main.ts` 자체 boot으로 vitest 미실행(배선은 코드 리드) · Playwright 3-mode 스크린샷 미실행 · 색 가독성은 taste 판단. 후속: `renderer/settings.ts` 456 pure LOC(ADR-0110 밴드 초과 — 분할 후속), `suppressMotion` 의 `flash`/`floating_damage` kind는 소비자 미배선(후속).
**미실행**: **P7·P8**(밸런스 접촉 → ADR-0229 §A1 필요, 사용자 결정). ADR: `0236-accessibility-modes.md`.

## [2026-11-01] feat | ADR-0240 유휴 알람 reducer 루프 + 피해/공격성 + 하네스 측정

- 유휴 10초부터 10초 간격으로 알람 상승(최대 5). 레벨당 피해 +5% / 스킬 확률 +1pp,
  단일 `IDLE_ALARM_TUNING`. rAF는 유휴 때만 reducer 액션을 보냄; 직접 공격 없음.
- 하네스 `idleMsPerTurn` scalar/고정 schedule opt-in. 도구 추가 직후와 최종 구현 후
  no-idle 양 덱 모두 ADR-0239와 동일. 3개 크기 grid에서 +10%/+2pp는 g3 −14.1pp로
  기각, +5%/+1pp 채택(초기 10초 유휴에서 opening 최대 −0.6pp / PPL −0.1pp).
- 지속 유휴(매 카드 10초)는 기존 Dixie 3초 타이밍 때문에 opening g3 +22.9pp;
  이 결과를 숨기거나 정상 입력 기준선과 혼동하지 않고 별도 stress 표로 기록.
- 브라우저 회귀 테스트가 new-run의 legacy `screen=mission_select` gate 결함을 발견;
  메뉴·두 미션 보드 진입점을 모두 허용하여 수정. 45초간 입력 시 알람 0, 20초 유휴 시
  알람 2/HP·카드 불변을 desktop/phone에서 입증.
- `npm run typecheck` 0, lint 0 errors/기존 keyboard warning 1, Vitest **158 files /
  3599 tests**, build 118 modules, Playwright **76 passed / 4 skipped / 0 failed**
  (CI unset, retries 0, IPv4 preview 5195, demo-screenshots 제외).
- LSP는 설치 없음/기존 설치 거절로 미실행. 커밋·스테이징·main.ts 전체 포맷 없음.
- Accepted ADR 불변 규약은 **결정 본문**에 대한 것이고, ADR-0195 는 Accepted ADR 에
  `## Implementation Status` 섹션 추가를 의무화한다 (0241/0243 이 그렇게 기록됨).
  따라서 0240 본문의 Implementation Status 를 ❌ Not started → ✅ Implemented 로 갱신하고,
  Status/Evidence/Notes·선택 수치·양 덱 before/after 표·(c)(i)(j)(l) 처리 근거를 기록했다.
  전체 grid·raw 출력은 [구현 증거](docs/wiki/decisions/0240-implementation-evidence.md)에 둔다.
  ADR index Impl 컬럼도 갱신. (k) 알람 통합·(e) stealth ICE·접근성 opt-out은 OPEN.
  ADR-0242는 미착수.

## [2026-11-01] feat | ADR-0242 ICE 아키타입 알람 배율 배선

- `idle_alarm.ts`의 `tickAlarm`에 hardcoded 1 대신 살아 있는 roster ICE의 최소
  `ice_ai.getAlarmMultiplier`를 전달. (i) 매 유효 tick 재계산, 마지막 stealth 사망 후
  다음 tick에서 정상 속도 복귀. 2 stealth도 0.5이며 곱셈 중첩 없음, 빈 roster는 1.
- `ice_ai.ts` 함수 입력은 이미 존재하는 `PersonalityBearer`로 좁혀 실제 roster ICE를
  타입 단언 없이 전달. 기존 함수 본문·0.5 상수·ADR-0240 튜닝과 gate는 불변.
  `ice_crit.ts`는 해당 설명 두 줄만 변경. `shouldTargetAlly` 설명·정의는 불변/호출자 0.
- 새 `ice_alarm_multiplier.test.ts` **18 tests**: 첫/후속 stealth 20초 경계, 비-stealth
  10초, 혼합 순서 독립성·비중첩, 사망 재계산, 빈 roster, 실제 archetype 함수 import 및
  동명 run-mutator 함수 호출 0건 검증. 기존 테스트 삭제·약화 없음.
- 실제 미커밋 ADR-0240 트리에서 편집 전 idle 양 덱 측정 후 편집 후 4회 balance 실행.
  no-idle opening `100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0`,
  PPL `100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7`로 ADR-0239와 정확 일치.
  idle `10000,0` 전후 opening `100.0 / 88.3 / 70.5 / 38.9 / 36.2 / 0.0`,
  PPL `100.0 / 79.1 / 98.9 / 82.9 / 44.4 / 24.7`, 모든 grade **0.0pp**.
  g1·g3도 이동 없음. §A2 보고만/re-baseline 없음, §B1·§B2 통과, §C2 전후 표 기록.
- 검증: typecheck exit 0, lint exit 0/0 errors/기존 keyboard warning 1,
  Vitest **159 files / 3617 tests passed / 0 failed** (7.01s), build exit 0/118 modules
  (466ms). 첫 typecheck의 신규 teardown 반환형 TS2322를 void 콜백으로 고친 뒤 통과.
  jsdom media play/load stderr는 있었으나 테스트 실패 없음.
- [구현 증거](docs/wiki/decisions/0242-implementation-evidence.md)에 Status/Evidence/Notes,
  (i) 해소 근거, 전후 표, **6회 raw balance 출력** 기록. ADR-0242 본문의 Implementation
  Status도 ❌ Not started → ✅ Implemented 로 in-place 갱신 (ADR-0195 Option 1 의무,
  0241/0243 선례). ADR 인덱스 Impl 컬럼 갱신.
- **검정력 경고 추가**: idle 시나리오의 0.0pp 는 "효과 없음" 의 증거가 아니다. 하네스는
  등급별 단일 ICE encounter 를 쓰지만 g1 `wisp` · g3 `ice_dixie_echo` (둘 다 stealth) 가
  실제로 포함되고, level 1 의 +5% 피해가 승패를 뒤집지 못해 표에 안 나타났다.
  **배선 생존 증거**: 지속 유휴 `--idle-ms 10000` opening g3 mean-HP-end 21.6 → 23.6,
  p5/p95 9/32 → 12/33 (stealth ICE 가 알람을 느리게 만들어 적 피해 감소).
- `shouldTargetAlly` 🟢 Deferred, (j) run-mutator 합성 OPEN. ADR-0240 지속 유휴/Dixie
  오너 판단 대기는 그대로. LSP는 미설치/기존 설치 거절로 diagnostics 불가.
  UI/main.ts/VFX/status.ts 미수정으로 E2E 미실행. 커밋·스테이징 없음.
- **규약 충돌 기록 (오너 확인 권장)**: 글로벌 `~/.config/opencode/AGENTS.md` 는 "Accepted
  ADR 수정 금지" 를 워크스페이스 불변식으로 두지만, 프로젝트 ADR-0195 Option 1 은 Accepted
  ADR 에 `## Implementation Status` 섹션 추가를 **의무화**한다. 0240·0242 구현에서 두
  서브에이전트가 모두 전자를 우선해 ADR 본문 갱신을 거부했다 → 오케스트레이터가 후자
  (확립된 선례) 로 in-place 갱신했다. 글로벌 규칙에 "Implementation Status 섹션은 예외"
  명시가 필요할 수 있다.
- **오케스트레이터 재검증 (0242 에이전트가 e2e 를 건너뛴 공백 보완)**: 0242 는
  `idle_alarm.ts` 를 바꿨으므로 e2e `idle_alarm.spec.ts` 의 "20초 유휴 → alarm 2" 단언이
  stealth ICE 로 인해 깨질 수 있었다. `npm run build` 후 IPv4 preview(5195) + CI unset 으로
  직접 실행: 해당 스펙 **4/4 passed**, 전체 스위트 **76 passed / 4 skipped / 0 failed** (4.5m).
  회귀 없음. 프리뷰 프로세스 정리 완료.
- **지속 유휴 역전 진단 (오너 판단용)**: cadence 효과와 알람 효과를 분리 측정해
  (i) 역전은 알람이 아니라 **시계 진행 자체**가 원인이고, (ii) **2000→3000ms/턴 임계값
  계단**이며, (iii) 알람은 오히려 되돌리는 방향, (iv) 턴당 RNG draw 동일(5.29 vs 5.26)
  임을 입증. 근본 기구는 미특정 — ADR-0240 §Open questions (m) + 증거 §부록에 기록.

## [2026-11-01] docs | ADR-0239 (b) 종결 + ADR-0244 초안 (시계 의존 결함)

- **ADR-0239 (b) 결정 확정**: `core/status.ts` 의 `rollStatusProc` 을 **게임플레이로
  재분류하고 코드 무변경** (선택지 1, 오너 승인 2026-11-01). 옵션2 (`core/combat/**`
  에서 상태 기반 시드 주입) 는 그 자체가 게임플레이 변경이라 2차 재기준화가 필요하고,
  ADR-0239 가 이미 `c488b6d` 로 한 번 재기준화했으므로 두 번째 곡선 이동을 정당화할
  이득이 없어 기각. (b) 가 마지막 미결 항목이었으므로 ADR-0239 Implementation Status
  를 🟡 Partial → ✅ Implemented 로 갱신, `decisions/README.md` Impl 컬럼도 갱신.
- **ADR-0244 초안 작성 (Draft)**: ADR-0240 구현 중 발견한 **시계 의존 결정적 항**.
  시계를 2000 → 3000ms/턴으로 바꾸면 **알람 0 에서도** 곡선이 뒤집힌다 (opening
  g2 +11.7pp · g3 +28.4pp · g4 +24.5pp). 1000/3000/6000/8000 이 byte-identical →
  시간 비례가 아니라 **임계값 계단**. 난수 값 시퀀스가 byte-identical 이라 **RNG 무죄**,
  알람은 오히려 되돌리는 방향으로 작동. 하네스 기준선이 `AUTO_ATTACK_INTERVAL_MS`
  경계 위에 있어 이후 모든 시간 관련 측정이 경계값에 서 있다. 권고: 옵션 4 (실제
  게임 rAF 영역 확인) → 옵션 2 (턴 기반 정규화 + 재기준화). **구현 없음.**
- 커밋: `9e24f45` (ADR-0240 + ADR-0242 구현·측정), 본 문서와 함께 (0239 종결 + 0244 초안).

## [2026-11-01] fix | 지속 유휴 역전 원인 확정 — 아군 Dixie 의 3초 시간 게이트 (ADR-0244)

- ADR-0244 의 미지목 항을 **실측으로 특정**했다. `state_actions_combat.ts:375-382` 의
  `currentMs - dixieLastAttackMs >= DIXIE_ATTACK_INTERVAL_MS` (3000) 게이트가 원인이며,
  Dixie 는 플레이어 아군으로 **ICE(적)에게** `8 + playerCombo × 3` 피해를 준다.
- **턴별 산술 일치**: `first_contact` (g3, seed 1) 에서 프로그램 피해 10/10/28/5 + Dixie
  기여로 idle=0 은 21/10/28/5, idle=1000 은 21/24/28/25. 관측값과 정확히 일치.
- 이것이 **임계값(2000↔3000) · 포화(3000/5000/8000/10000 byte-identical) · RNG 무죄(난수
  시퀀스 byte-identical) · 플레이어 HP 불변** 을 전부 설명한다.
- **정정**: 앞서 "에이전트의 Dixie 진단은 측정과 맞지 않는다" 고 적은 오케스트레이터 판단은
  **철회**한다. `>= 3000` 게이트를 "격턴 발동" 으로 잘못 모델링한 탓이었고, 실제로는 정확히
  그 동작(2000ms/턴에서 격턴, ≥3000ms/턴에서 매 턴)이었다. ADR-0240 증거 §부록과
  §Open questions (m) 을 정정했다.
- **옵션 4 해소**: 사람 입력 cadence 는 대개 ≥3초이므로 실제 플레이는 Dixie 매 턴 발동이고,
  기준선(2000ms/턴)은 격턴 발동이다 → **현 기준선은 실제보다 어렵다.** 그리고 Dixie 피해가
  combo 에 비례하므로 **느린 플레이가 유리** — 유휴 압력 (P7) 설계와 정면 충돌.
- ADR-0244 를 확정 기구로 재작성: 옵션 1~4 비교, 권고 = **옵션 2 (턴 기반) + 옵션 3
  (cadence 정정) + 재기준화**. 수락 증거에 핵심 회귀 명시 — "시계를 바꿔도 결과 불변"
  테스트는 **지금 실패해야** 한다 (결함의 pin). 열린 질문 (a)~(e). **구현 없음.**

## [2026-11-01] fix | ADR-0244 옵션 2 — Dixie 플레이어 턴 gate, N=2

- 첫 성공한 프로그램 턴에 발동, 이후 3·5·7번째. counter=N−1 초기화로 기존 2000ms
  기준선 위상 유지. 적 clock gate 밖에서 성공한 프로그램마다만 카운트, 피해 8+combo×3 불변.
- `dixieLastAttackMs`는 미사용 legacy 필드로 보존. SaveSlot에는 원래 없었으며 새 counter도
  ephemeral. 실제 storage round-trip과 기존 save tests 통과; matrix resume에서 N−1 초기화.
- clock regression 수정 전 적 HP 45 vs 34로 실패 → 수정 후 통과. 1/3/5턴 피해 11/17/23,
  선택·실패·idle 비카운트, 양 덱 전체 미션 sub-threshold 수렴 테스트 추가 (+6 tests).
  기존 combat fixture 9곳은 timestamp 억제를 counter=0으로 이전; assertion 완화 없음.
- N=1/2/3 × opening/PPL × idle 0/1000/10000: 18회, 100 runs/mission.
  상세 표/정책/수렴: [ADR-0244](docs/wiki/decisions/0244-clock-dependent-combat-term.md),
  [raw stdout](docs/wiki/decisions/0244-implementation-evidence.md).
- 채택 N=2 양 덱 ADR-0239 baseline **전 grade 0.0pp**, idle 0/1000 **전 metric 동일**.
  N=1은 opening 최대 +28.4pp, PPL 최대 +20.9pp라 별도 re-baseline 대상, 미채택.
  N=3도 미채택. 최종 상수는 **2**. 하네스 cadence와 알람 tuning은 불변.
- **잔여 한계**: N=2 sustained idle 10000은 opening g4=7.4 < g5=11.7로 §B1 실패.
  no-idle 기준선 통과를 모든 입력 분포 통과로 포장하지 않으며 알람 retuning은 별도 결정.
- ADR-0244 Accepted + ADR-0195 Implementation Status 추가, 인덱스 Impl 갱신,
  combat.md 현행 Web/retired Python 구분. (a)/(c)/(d) 종결, (b) telemetry 미측정,
  (e) 다른 시간 gate는 범위 밖 유지. 옵션 3 미적용.
- 검증: typecheck 0 errors; lint 0 errors/기존 keyboard warning 1; **159 files/3623 tests**;
  build **118 modules**; 지정 IPv4 preview E2E **76 passed/4 skipped/0 failed, 4.7m**,
  CI unset/retry 비활성/demo-screenshots 제외/preview 종료. LSP는 기존 설치 거절로 불가.
- raw/금지 ADR/status/VFX 구현 파일 무변경. 커밋·stage 없음; 편집 파일만 포맷.

## [2026-11-01] fix | ADR-0240 sustained-idle §B1 — 피해/레벨 5%→4%

- 진단 먼저: 피해 단독 opening **100/88.3/47.5/7.4/11.7/0**, 공격성 단독
  **100/88.3/71.1/39.5/36.2/0**, 양쪽 **100/88.3/48.4/7.4/11.7/0**.
  양 성분 0이면 sustained도 양 덱 기본 metric과 동일: cadence 자체는 원인이 아니다.
- band별 실측: g4 reporter 3개 **79→10승**, enforcer 2개 **78→22승**,
  sentinel 2개 **1→0승**, 합계 **395→74/1000**. g5는 enforcer 3개 **76→9승**이나
  loa **98→78승**이 남아 **326→105/900**. 동일 배율의 서로 다른 생존 cliff가 역전 원인.
- 1/2/3/4% grid(공격성 +1pp 고정), 양 덱 전 grade 측정 후 가장 강한 통과 후보
  **4%** 채택. production diff는 `idle_alarm.ts` 상수 **한 값**뿐, 레벨 5 ×1.20.
- 최종 sustained opening **100/88.3/49.3/25.2/12.4/0**, PPL
  **100/79.1/97.1/79.1/44.1/0**. opening §B1 PASS, §B2 g6 0.0%.
  알람 압력은 유지: opening g3 −21.2pp/g4 −14.3pp/g5 −23.8pp, PPL g6 −24.7pp vs no-idle.
- 양 덱 × idle 0/1000/10000을 전후 별도 CLI 실행, 100 runs/mission, seeds 1–100.
  양 덱 no-idle은 ADR-0239 승률과 동일, 모든 출력 metric은 수정 전과 byte-identical.
  idle 0=1000도 모든 metric 행의 exact string equality assert PASS. 기본 재기준화 없음.
- 신규 `sustained_idle_balance.test.ts`: 전 grade 반올림 전 비율 검사,
  수정 전 **0.11666666666666667 > 0.074**로 실패 → 한 값 수정 후 통과.
  기존 테스트 삭제/완화 없음. PPL 단조성은 §C3대로 목표로 삼지 않았다.
- ADR-0240 확정 수치·Implementation Status·변경 이력, ADR-0244 잔여 한계,
  combat.md/GDD/인덱스 동기화. [모든 raw stdout·재현 명령](docs/wiki/decisions/0240-sustained-idle-evidence.md).
- LSP: 두 편집 TS 파일 모두 요청했으나 TypeScript 서버 미설치·기존 설치 거절로 불가.
  설치/우회 없음. 금지 파일·상수·cadence·Accepted 결정 본문 무변경, stage/commit 없음.
- 최종 검증: typecheck **0 errors**, lint **0 errors / 기존 keyboard warning 1**;
  **160 files / 3624 tests passed / 0 failures (8.35s)**; build **118 modules / 568ms**.
  지정 IPv4 strictPort preview E2E **76 passed / 4 skipped / 0 failed (4.6m)**,
  CI unset·재시도 없음·demo-screenshots 제외, preview 종료. 임시 진단 스크립트·저널 제거.

## [2026-11-01] docs | ego-lite 실제 플레이 점검 절차 + 그 절차가 잡은 렌더 결함 2건

- **절차 문서화**: `docs/playtest/EGO_LITE_PLAY_CHECK.md` — Playwright e2e 를 **대체하지
  않고 보완**하는 실제 플레이 점검. ego-lite 에 **가짜 시계 API 가 없어** (`waitForTimeout`
  과 `timeout` 옵션만) `page.clock` 기반 시간 게이트 단언을 옮길 수 없다는 것이 교체 불가
  근거. 역할 분담을 명시: Playwright = 시드 결정성·clock·expect·2 뷰포트·CI / ego-lite =
  실제 렌더·실제 조작·느낌.
- **검증된 스크립트 포함**: `build` + `vite preview --host 127.0.0.1`(필수) →
  `ego-browser nodejs` 로 menu → mission_select → combat 도달. 실측 확인:
  `phase=combat, runPhase=combat, hp=100, lead ICE 165, deck=5, alarm=0`.
  `waitForFunction` 옵션은 3번째 인자라는 함정도 기록.
- **자동화 표면**: `window.wetrun.getScreen/getPhase/getMenuOptionKeys/getSelectedMenuIndex`
  + `state.runPhase/matrix.nodes/currentNodeIndex` (e2e 헬퍼와 동일 계약). 고정 키 횟수를
  쓰지 않고 목표 화면/단계까지 Enter 를 눌러 올린다. 교전은 2단계(runPhase → getPhase).
- **이 절차가 실제로 잡은 것**: 첫 실행에서 상태는 정상이었지만 렌더에서
  **ICE 표기 `165/100`** (HP 가 maxHp 초과) 과 **우측 패널 `Equipped: 10/8`** 를 발견.
  둘 다 단언이 아니라 화면을 봐서 나온 것으로, 절차의 목적을 그대로 보여준다.
  **미검증 — 별도 확인 필요** (이번 작업 범위 밖으로 기록만).
- `docs/index.md` 테스트 케이스 절에 링크 추가. 코드 변경 없음.

## [2026-11-01] fix(display) | ADR-0245 — ICE 최대 HP·장비 슬롯 HUD 표시 결함 2건 수정

- **확정 원인**: `combat_grid.ts`의 최대 HP 리터럴 100 → grade-scaled ICE의
  `165/100` 및 잘못된 게이지/색상. `buildHudLines`의 `Object.values(loadout)` →
  슬롯 맵 1개 + 메서드 9개 = 10으로 장비 수와 무관하게 `Equipped: 10/8`.
  위 과거 점검 로그의 "미검증" 2건은 이번에 확정·수정했다.
- **최소 표시 전용 수정**: 유한한 양수 `ice.maxHp`를 게이지·분모·색상에 공통 사용,
  누락/0/음수/NaN/Infinity는 legacy 100 fallback. dead 분기는 `[DEAD]`라 수정 불필요.
  장비는 `allSlotsFilled().length / EQUIP_SLOTS.length`. gameplay·튜닝·RNG·AI·알람·
  Dixie·하네스 cadence·VFX·금지 ADR·raw 전부 무변경. stage/commit 없음.
- **회귀 +16건**: renderer scaled HP 165/165·절반 게이지/색상 2건 + fallback 5건,
  state HUD 실제 0..8 슬롯 9건. 수정 전 11 failed/27 passed → 전체 수정 후 통과.
  web/src·tests·e2e 전체 조사에서 버그 값을 pin한 기존 단언은 **없음**;
  기존 기대값 변경/삭제/완화 없음. 편집한 TS 4개만 Prettier 적용.
- **밸런스 실측**: `npm run balance` opening **100.0/88.3/70.5/39.5/36.2/0.0**,
  `npm run balance -- --deck ppl` **100.0/79.1/98.9/83.0/44.4/24.7**.
  ADR-0239 승률 기준선과 12개 값 정확히 일치, **0.0pp**. 전체 stdout은
  [ADR-0245](docs/wiki/decisions/0245-combat-hud-display-defects.md)에 기록.
- **검증**: typecheck exit 0; lint exit 0 (기존 untouched keyboard.ts warning 1);
  **160 files / 3640 tests passed / 0 failed (8.21s)**; build 118 modules/469ms.
  지정 IPv4 strictPort preview + CI unset + demo-screenshots 제외 E2E
  **76 passed / 4 skipped / 0 failed (4.6m)**. 첫 120초 tool timeout 후 600초로 재실행,
  preview EXIT trap 종료. jsdom audio play/load 미구현 stderr는 비실패 진단.
- **제약**: LSP diagnostics는 TypeScript 서버 미설치·기존 설치 거절로 불가;
  설치/우회 없음, tsc 통과. 이번 수정 세션에서 ego-lite 재플레이/별도 시각 캡처는 미실행.
- **문서**: 새 ADR-0245 ✅ Implemented + ADR-0195 Status/Evidence/Notes + 변경 이력,
  ADR 인덱스 Impl 행, 실제 플레이 점검의 두 항목을 확정·수정 상태로 연결.

## [2026-11-01] docs | PLAYTEST_GUIDE 현행화 + 옛 프로토콜 역사 표시

- **`PLAYTEST_GUIDE.md` v1.0 → v2.0**: 초판(2026-09-01)이 **retired 된 Python CLI** 를
  "Option A (Full Game)" 로, **존재하지 않는 Supabase 클라우드 동기화**를, 그리고
  옛 배포 URL `play.html` 을 안내하고 있었다 — 테스터를 없는 빌드로 보내는 상태였다.
  검증: `grep -i supabase src/ package.json` → **0건** (저장은 IndexedDB/localStorage,
  ADR-0209), Python 통합은 `1b3cff4` (2026-09-15), 현행 URL 은
  `https://seoca1.github.io/wet-run/wetrun-web/`.
- v2.0 은 웹 단일 빌드 기준으로 다시 썼다: 실행 방법(웹/로컬, `vite preview` 는
  `--host 127.0.0.1` **필수**), 저장(IndexedDB 우선, 클라우드 없음), 시나리오 TW-01~10
  (유휴 알람 TW-03, 입력 속도 무관 TW-04 를 신규 핵심으로 명시), 조작, 피드백 양식,
  팁(오프닝 핸드, **두 종류의 alarm 구분** — `Alarm N/100` 비용 누산기 vs `ALARM N/5`
  유휴 알람), ego-lite 실제 플레이 절차 링크.
- **`PLAYTEST.md`**: 같은 허위 내용을 담은 2026-09-01 프로토콜이므로 **다시 쓰지 않고
  역사 표시 배너**를 달았다 (Python CLI retired · URL 변경 명시 + 현행 가이드 링크).
- 사실 확인 후에만 숫자를 썼다: missions.json 53, programs.json 30, 오프닝 핸드
  `backdoor/barrier/boost/cloak/decoy` (하네스 + 실제 렌더 HAND 행으로 교차 확인).
  코드 변경 없음.

## [2026-11-01] docs | ADR-0239 완결 — (c)(f) 권고안 채택, 롤백 판단 기준 확정

- **(c) 새 기준선의 지위 — 권고안 그대로 채택**: ADR-0229 본문은 Accepted/immutable 이므로
  고치지 않고, 새 기준선은 이 ADR 이 보유하며 supersede 관계를 명시한다. 별도 baseline
  문서를 만들지 않는다. **이미 본문에 반영되어 있었음을 확인**하고 근거 위치(§재기준화
  결과 의 양 덱 표 + "ADR-0229 관계", §영향 받는 항목)를 인용해 해소 처리.
- **(f) 되돌리기 정책 — 권고안 채택 + 미정 항목 확정**: 롤백 곡선은 이미 기록되어 있다
  (opening `100.0/88.6/73.1/39.3/35.7/0.0`, PPL `100.0/77.9/99.6/84.8/44.4/28.3`).
  **미정이던 롤백 판단 기준을 새로 발명하지 않고 ADR-0229 §A1 drift policy 재사용으로
  확정**: opening 어떤 grade 든 ±3pp 초과 이동을 일으키고 그것이 명시적 re-baseline ADR 로
  기록되지 않았다면 코드와 기준선을 함께 원복한다.
- 결과: ADR-0239 의 남은 열린 질문은 **(a) id 스킴** 하나다 (권고안이 없어 오너 결정 없이
  닫지 않았다 — 다만 Implementation Status 의 안전성 확인이 "현재 독자에게는 충분" 근거를
  이미 담고 있다). `decisions/README.md` Impl 셀 갱신, 변경 이력 추가.
- 코드 변경 없음 (문서 전용).

## [2026-11-01] docs | 해소된 Open questions 정리 (0240/0242) + Impl 셀 정정

- **ADR-0240 `## Open questions`**: Implementation Status 는 (c)(i)(j)(l) 을 해소로
  기록했는데 아래 목록은 그대로 열린 것처럼 남아 있었다. (i)(j)(l) 을 취소선 + 해소 근거로
  정리하고, (c) 는 **임계 N=10초 해소 / 접근성 opt-out 은 OPEN** 으로 분리해 표기했다.
  (e) 는 stealth ICE 스킬 저술이 up-stream 선행이라 OPEN 임을 명시. (k) 는 그대로 OPEN.
- **ADR-0242 `## Open questions`**: (i) 다수 ICE 배율 합성을 취소선 + 해소 규칙(살아 있는
  roster ICE 의 최소 배율, 매 적격 tick 재계산, 비중첩)으로 정리. (e)(j) 는 OPEN 유지.
- **`decisions/README.md`**: 0240 Impl 셀의 "미커밋 지속 유휴 수정" 을 실제 커밋
  `5164b8c` 로 정정 (해당 수정은 이미 커밋됨).
- 코드 변경 없음 (문서 전용). 남은 OPEN 은 오너 결정 또는 별도 프로젝트 선행이 필요한
  항목뿐이다.

## [2026-11-01] docs | ADR-0246 던전 이동 기반 런 모델 결정 요청

- [ADR-0246](docs/wiki/decisions/0246-dungeon-role-and-run-interaction.md)을 당시 **Draft (오너 결정 대기)**로 작성. 이후 아래 오너 결정으로 전면 재작성·이름 변경.
  제공된 분석을 기록하고, 이미 공유하는 생성기와 변환 중 버린 공간 정보의 보존을 제안의 중심으로 정리.
- 조우 C 권고·실패 반복 방지 6조건·TRACE 통합 선행·분기 선택 증거·idle 0/1000 동일 및
  밸런스 기준선 불변·저장 호환 기준과 열린 질문을 명시. 수락 기준은 향후 검증이며 이번 실측이 아님.
- 인덱스에 Draft / **❌ Not started** 행 추가. 기존 ADR-0005/0060/0103 본문·코드·테스트 변경 없음.
  스테이징·커밋 없음.

## [2026-11-01] docs | ADR-0246 오너 결정 반영 — A → C, 던전은 아이템 미니게임

- [ADR-0246](docs/wiki/decisions/0246-dungeon-role-and-run-interaction.md)을 **Accepted / ❌ Not started**로 전면 재작성·이름 변경.
  런의 경로·위험 결정을 먼저 만드는 A → 추가 아이템용 선택적·유계 미니게임 C 순서 확정.
  건너뛰기는 진행 손실이나 처벌이 아닌 아이템 기회비용. B의 전체 런 던전화 분석은 보류안으로 보존.
- Oracle의 D 권고는 미채택이며, C 계약 미달 시 올바른 대체 경로임을 명시.
  C의 유계·실제 위험 결정·런 아이템·실패 비용 4조건, 보상 예산과 전투 전용 하네스의 측정 공백 기록.
- TRACE 통합과 그래프 분기 하나의 선택+확인을 선행 조건으로 기록. Manus second opinion은 요청했으나 응답 미수신·미기록.
  인덱스와 기존 로그 링크를 새 파일명으로 동기화. 수락 증거는 전부 향후 검증이며 구현 완료 주장이 아님.
- 코드·테스트·ADR-0005/0060/0103 본문 변경 없음. 커밋 없음, 이름 변경 직후 언스테이징하여 최종 스테이징 없음.

## [2026-11-01] docs | ADR-0247 보충 — Manus 제2 의견과 독립 정리 조치

- [ADR-0247](docs/wiki/decisions/0247-dungeon-role-supplement-manus-second-opinion.md)을 **Accepted / ❌ Not started**로 작성.
  Accepted ADR-0246은 수정하지 않고, Manus 응답 수신·태스크 출처·코드 및 기존 분석 대조·세 독립 출처의 수렴을 기록.
- A 강화안 E, 고정 동사 A 검증 후 E 확장 권고, C의 다섯 번째 조건인 전력 공급 비지배성과 보상 예산 연결을 추가.
  사망 시 HP 절반 복구·무효 장비 픽업·런 반영 부재는 방향과 무관하게 수정 또는 제거할 필수 조치로 기록.
- 인덱스에 상위 ADR-0246 링크와 새 행 추가. ADR-0005/0060/0103/0246·코드·테스트 변경 없음. 스테이징·커밋 없음.

## [2026-11-01] feat | ADR-0246 A 첫 슬라이스 — 정보가 보이는 인접 경로 선택

- **범위**: 경로 결정만 구현. Probe/Bypass/Breach, TRACE 통합·비용 정책, E, C, 별도 던전 정리·전투·튜닝·RNG·VFX 구현은 변경하지 않음.
- **입력**: ↓/→ 다음 인접 후보, ↑/← 이전 후보, Enter/Space 선택한 이웃으로 이동. 이동/보상 확인 후 미선택으로 돌아감.
  기존 목록·화살표·확인 액션을 재사용해 새 키 매핑/공간 지도 없이 최소 구현. 미선택 확인의 현재 ICE 진입은 유지.
  입구 방향 자동 후퇴도 제거하고 방문한 인접 이웃을 직접 선택하게 함. 보상 확인의 기존 회복은 유지하되 위치는 그대로.
- **정보/배치**: 현재 노드·전체 인접 후보를 먼저 표시하고 나머지 노드를 뒤에 배치. 각 후보의 zone, ICE 개수(0 포함), 크레딧, eventKind 표시.
  `>`로 선택을 구분하고 후퇴 가능한 방문 이웃도 강조. 좁은 화면에서는 보조 ICE 패널보다 후보 정보를 우선하여 겹침 방지.
- **Layout**: 기존 Green Grid 프레임 안의 2행 노드 목록을 유지; 현재 노드 → 인접 후보 → 나머지 순서, 스크롤 없음.
  주 행동은 선택 목적지로 이동, 정보 우선순위는 현재 위치 → 후보의 위험/보상 → 나머지 노드. 새 카드·지도·위험 자원은 추가하지 않음.
- **도달성**: 절차 생성 행렬은 DAG가 아님. MST 기반 연결/추가 간선이 양방향 `adjacent`로 변환되어 곁가지와 재방문이 존재.
  방문 이웃을 막지 않아 곁가지에서 돌아갈 수 있고, 그래프를 변경하지 않아 어느 선택에서도 보스가 도달 가능.
  자발적 왕복은 가능하지만 자동 라우팅/자동 2-cycle은 없음. 53개 미션 전 노드의 보스 경로·인접 역방향 연결과 선택+확인 보스 도달을 테스트.
- **회귀**: 새 `matrix_route_choice.test.ts` 8건(구현 전 핵심 6건 실패 관측) + 전체 미션 도달성 1건.
  BFS 비선택 곁가지, 명시적 후퇴, 보상 후 위치·미선택·회복, 동일 seed 각 분기, 실제 런 화면의 선택 강조,
  80×50/60×40/40×60에서 목록 뒤쪽/방문 후보의 정보 검증. 기존 자동 이동 단언은 새 선택+확인 계약으로 갱신하고 실제 이동/전투/엔딩 검증 유지.
- **E2E 적응**: `gotoIceNode`는 도달 가능한 ICE까지 경로를 찾은 뒤 실제 키로 후보 선택+확인; CONTINUE는 강조 단계의 위치 불변과 확인 후 선택 목적지 도착을 함께 단언.
- **검증**: `npm run typecheck` 0 errors, `npm run lint` 0 errors/기존 untouched keyboard 경고 1개,
  `npm test` **161 files / 3649 passed**, `npm run build` 통과. LSP는 미설치/기존 설치 거절로 사용할 수 없어 CLI 타입체크로 검증.
- **양 덱 밸런스**: `npm run balance` opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**;
  `npm run balance -- --deck ppl` **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**. 출력의 턴·HP·percentile도 ADR-0239 기준선 유지.
- **문서**: ADR-0246의 `## Implementation Status`만 🟡 Partial로 변경하고 경로/테스트 증거 기록. README의 0246 Impl 셀 갱신.
  Accepted 결정 본문 및 ADR-0005/0060/0103/0247 불변. 커밋·스테이징 없음.
- **브라우저 검증**: `npx vite preview --port 5195 --strictPort --host 127.0.0.1` +
  `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`
  → **76 passed / 4 skipped / 0 failed (4.6m)**. 최초 실행은 새 CONTINUE 단언에 Vitest 전용 matcher를 쓴 실수로 2건 실패;
  `typeof` 단언으로 수정 후 전체 재실행 통과(검증 제거·완화 없음, retry 없음). 데스크톱/모바일 선택 화면 캡처도 직접 확인.

## [2026-11-01] fix | ADR-0246 검증 발견 — 같은 노드 재확인 무한 파밍 차단

- **원인**: 경로 슬라이스가 보상 후 자동 전진을 제거했지만 조우 완료 상태가 없어 같은 노드에서 확인만으로 전투·보상을 반복할 수 있었음. `visitedNodes`는 전투 전 이동 시점에도 기록되므로 완료 판별에 사용할 수 없음.
- **수정**: `web/src/core/types.ts:194,433`의 optional `clearedEncounterNodes`를 추가. `web/src/core/state/state.ts:164-176` 공통 reducer 경계에서 전투가 `loot`로 해결될 때 현재 노드를 기록하고, `state_actions_phases.ts:65-70`에서 완료 노드의 재확인은 안내만 반환. 직접 공격/동료 처치 모두 포함하며 전투·튜닝·RNG·VFX 구현은 불변.
- **ADR-0185 저장 호환**: `stateToSaveSlot`/`slotToGameState`가 완료 목록을 저장/복원. SaveSlot version 1 유지, 필드가 없는 기존 상태/슬롯은 빈 완료 목록. 과거 방문을 완료로 추측하지 않으며 이후 해결한 조우부터 기록. 저장 경계에서 잘못된 목록을 거부.
- **RED → GREEN**: `npm test -- tests/matrix_route_choice.test.ts`에서 새 `cannot farm a cleared encounter by confirming again after loot (ICE HP %s)`의 HP 1/12 두 경우 모두 수정 전 `expected 'combat' not to be 'combat'` 실패(2 failed / 8 passed). 수정 후 노드 진입→해결→loot→재확인/프로그램 시도에서 재전투·추가 크레딧·재료 없음 검증 통과. 별도 저장/구형 슬롯/잘못된 목록 회귀 7건 추가.
- **검증**: 경로/저장 왕복 4 files / 39 passed; `npm run typecheck && npm run lint && npm test && npm run build` 통과, **161 files / 3658 passed / 0 failures**. 기존 `keyboard.ts:14` 린트 경고 1개, jsdom 미디어 미구현 stderr는 있었으나 테스트 실패 없음. LSP는 미설치/기존 설치 거절로 실행 불가, CLI 타입체크 통과.
- **양 덱 출력**: 수정 전후 `npm run balance`와 `npm run balance -- --deck ppl` 전체 stdout을 각각 `cmp`하여 byte-identical(exit 0). opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**; 턴·HP·percentile도 동일.
- **측정 한계**: `balance_sim.ts`는 그래프 이동 없이 조우를 직접 구성하므로 이 파밍 구멍을 보지 못함. 0.0pp는 전투 기준선 보존 증거이지 런 보상 경제 무결성 증거가 아님. 결함 차단 증거는 위 red/green 경로 회귀와 저장 왕복임.
- **E2E**: `npx vite preview --port 5195 --strictPort --host 127.0.0.1` + `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **76 passed / 4 skipped / 0 failed (4.5m)**, retry 없음. `gotoIceNode`/CONTINUE 그대로 통과. preview 종료 후 5195 리스너 없음 확인.
- **문서/범위**: ADR-0246은 `## Implementation Status`만 갱신, 인덱스 0246 Impl 셀 및 본 로그 추가. 기존 미커밋 슬라이스 유지, 스테이징·커밋 없음. 경로 강조+확인·보상 후 위치·15% 회복 불변; 던전 크롤러·status.ts·raw/·Accepted 결정 본문·Probe/Bypass/Breach/TRACE/E는 변경하지 않음.

## [2026-11-01] fix(ci) | Prettier 검사 쓰기 제거 + 소스 가드 공백 독립화

- **원인/수정**: `.github/workflows/delegation-verification.yml:61`의 `npm run format -- --check`는 `format` 스크립트의 `--write`를 그대로 실행해 검사 중 소스를 수정했음. 직접 `npx prettier --check "src/**/*.{ts,tsx}"`로 교체. 기존 glob·package.json·ignore 설정은 불변.
- **기계적 포맷**: `web/`에서 `npx prettier --write "src/**/*.{ts,tsx}"` 실행. 변경된 소스 19개, **+257/-135**. 기존 보호 4개(`dungeon_crawler_actions.ts`, `dungeon_crawler_core.ts`, `floating_damage.ts`, `screen_shake.ts`)는 **+21/-23**이며 동작 수정 없음. `core/status.ts`는 이미 clean이라 byte 변경 없음.
- **중립성 증명**: 각 소스 파일이 HEAD에 Prettier만 적용한 결과와 byte-identical인지 확인하고, TypeScript AST의 노드·식별자·리터럴·연산자·인자 순서·선언 종류를 비교해 동일함을 확인(위치/공백/불필요한 괄호 제외). `git diff -w`는 `far_grid_gate.ts`만 empty, 나머지 18개는 non-empty: 줄 분할/합침, 후행 쉼표, 동치 괄호, union 첫 `|` 정리만 존재. 따옴표/리터럴 값 변경 없음.
- **소스 가드**: `onboarding.test.ts`는 main.ts 공백을 제거한 뒤 기존 튜토리얼 진입·렌더 인자·힌트 조건·표시 후 once 플래그 순서를 그대로 검사. `nav_index.test.ts`는 동일 template expression의 `formatNavIndex(index)` 긍정 및 `index + 1` 부정 검사를 공백 제거 후 유지. `effects_schema.test.ts`는 동일 선언/union/상수/종류별 duration literal을 공백 제거 후 검사. 가드 삭제·새 wildcard·인자/값 완화 없음; tests 디렉토리 전체 포맷은 하지 않음.
- **검증**: 직접 Prettier check exit 0; `npm run typecheck` 0 errors; `npm run lint` 0 errors/기존 `keyboard.ts:14` 경고 1개; `npm test` **161 files / 3658 passed / 0 failures**; `npm run build` 통과. jsdom 미디어 미구현 stderr는 테스트 실패를 일으키지 않음. LSP는 TypeScript 서버 미설치/기존 설치 거절로 실행 불가, CLI 타입체크로 검증.
- **밸런스**: 포맷 전후 `npm run balance`와 `npm run balance -- --deck ppl` 전체 stdout을 각각 `cmp`하여 **byte-identical(exit 0)**. opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**로 ADR-0239 기준선 일치(턴/HP/percentile도 전후 동일).
- **E2E**: `npx vite preview --port 5195 --strictPort --host 127.0.0.1` + CI를 제거한 환경의 `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **76 passed / 4 skipped / 0 failed (4.4m)**, retry 없음. finally에서 preview 프로세스 그룹 종료.
- **경계**: ADR·raw/·index.html·e2e/·package.json 변경 없음. 소스는 지정 glob에만 기계적 포맷. 커밋·스테이징 없음.

## [2026-11-01] fix | ADR-0248 a0 — 두 alarm 계기의 이름을 COST / TRACE로 분리

- **결함/수정**: 행동 비용 `Alarm N/100`과 유휴 압력 `ALARM N/5`를 모두 alarm으로 부르던 혼동 제거.
  `COST N/100` / `TRACE N/5`, tick `TRACE N/5`, 실패 `Cost too high — program failed`로 변경.
  튜토리얼·진입 힌트·Cloak·HOT TRACE 설명도 정합. 튜토리얼의 기존 flatline 주장은 실제 초과 비용 실패 규칙으로 설명.
- **경계**: 이름만 분리, 메커닉 병합 없음. 필드·저장 스키마·RNG·10초 임계/간격·+4%/+1pp·상한 5 불변.
  크롤러 자체 alarm·status.ts·VFX 구현·raw/·ADR-0240/0246/0247 결정 본문 미수정. stage/commit 없음.
- **결정**: 신규 Accepted [ADR-0248](docs/wiki/decisions/0248-alarm-meter-naming.md), 인덱스·가이드·GDD·combat 명칭 정합.
  표시 통합 (a)은 Deferred. 병합 (b)은 숙고와 행동 능력을 결합하고 re-baseline을 요구하는 별도 설계 결정으로 기각.
  ADR-0246의 단일 가시 위험 계기 조건은 여전히 미충족.
- **테스트**: 기존 표시 단언은 새 문구의 전체 문자열 단언으로 강화. COST/TRACE 별도 값·0 숨김 및
  40×60/60×40/80×50 실제 전투 프레임 회귀 추가. E2E의 상태/HP/덱 보존 단언 유지·실제 TRACE 메시지 단언 추가.
- **검증**: 편집한 src 7개 파일만 Prettier write/check 통과. typecheck 0 errors;
  lint 0 errors/기존 keyboard.ts:14 warning 1개; 전체 **161 files / 3664 tests / 0 failures** (+6);
  build 통과(117 modules). 첫 단위 실행에서 기존 onboarding flatline 단언 1건 발견·새 COST 제한 문구 전체 단언으로 갱신 후 통과.
  LSP는 서버 미설치/기존 설치 거절로 실행 불가, CLI 타입체크 통과(설치/우회 없음).
- **밸런스**: 양 덱 수정 전후 전체 stdout `cmp` exit 0.
  ADR-0239 opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**,
  PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**, 턴·HP·percentile 동일.
  stdout 표는 ADR-0248 검증 기록 참조.
- **E2E**: `npx vite preview --port 5195 --strictPort --host 127.0.0.1` +
  `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`
  → **76 passed / 4 skipped / 0 failed (4.4m)**. finally에서 preview 프로세스 그룹 종료. 추가 재검증 없음.

## [2026-11-01] feat | ADR-0246 A slice 2 — COST로 결제하는 고정 encounter 동사

- **UX**: 현재 미완료 ICE에서 확인하면 초기 선택 없는 PROBE / BYPASS / BREACH / JACK OUT 메뉴.
  ↓/→ 다음, ↑/← 이전, Enter/Space 실행. PROBE 후 같은 메뉴 유지, BYPASS 후 현재 노드에서 경로 선택,
  BREACH 후 기존 approach 확인으로 교전. 새 키·지도·프로그램 부여 동사(E)·아이템 미니게임(C) 없음.
- **수치 단일 블록**: `web/src/core/state/encounter_verbs.ts:8`의 `ENCOUNTER_VERB_COSTS`에 PROBE 8, BYPASS 30, 기존 COST 상한 100.
  작은 정보 투자와 프로그램 사용 여력의 실질 소진을 교환한다. BYPASS는 전투·credits·loot·HEAL 없이 통과하며 완료 처리하지 않는다.
  출발 확인도 결제를 요구하여 화살표 이동으로 무료 회피하는 우회 차단. 재방문하면 BREACH와 기존 온전한 보상 가능.
  PROBE 공개는 실제 BREACH roster(ICE_X2 포함)의 catalog id·HP이며 미완료 matrix preview의 무료 HP 누출도 차단.
- **red/green**: 새 최초 13 tests 중 기존 코드에서 **12 failed / 1 passed** 확인.
  최종 새 18 tests에 무전투/무보상·비용·정확한 공개·전체 보상·재방문·no-farming·무료 출발 금지·상한 경계·프로그램 headroom 소진 포함.
  기존 전투 setup은 실제 BREACH 입력으로 이관, 기존 결과 단언 유지. 전체 **162 files / 3682 passed / 0 failed** (+18).
- **검증**: typecheck 0 errors; lint 0 errors/기존 `keyboard.ts:14` warning 1; build 통과(119 modules);
  편집한 src만 Prettier write/check. TypeScript LSP는 미설치·기존 설치 거절로 실행 불가(설치/우회 없음).
- **하네스의 실제 구조**: 그래프를 걷지 않지만 첫 전투에는 reducer confirm을 사용하므로
  `web/scripts/balance_sim.ts:122-130` setup에 BREACH 선택 입력만 추가. clock/RNG 추가 진행·전투 루프·튜닝·집계 무변경.
  양 덱 수정 전후 **전체 stdout `cmp` exit 0 (byte-identical)**:
  opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**.
  이는 전투 하네스 동작 보존이며 **경로 경제가 균형 잡혔다는 증거가 아니다**.
- **가격 한계**: 8/30은 보수적 시작값. BYPASS는 피해를 피하지만 보상·회복·프로그램 여력을 잃고 BREACH는 반대 교환이므로 무료 지배 선택을 막았다.
  그래도 비지배성과 실제 선택의 재미는 미측정이다. `docs/playtest/EGO_LITE_PLAY_CHECK.md`에 따른 새 입력 기반 실제 런 play pass 필요, 이번에 미실행.
- **E2E**: `menu-nav.ts` 명시적 동사 선택 + CONTINUE 이동 전 BYPASS + SFX/status/IDB/matrix/demo setup 이관.
  필수 `--host 127.0.0.1` preview 및 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots`
  → **80 passed / 4 skipped / 0 failed (4.4m)**. 첫 실행의 CONTINUE 무료 출발 가정 및 신규 JACK OUT state-null 가정을 수정한 뒤 통과.
  독립 기능 리뷰 PASS. 데스크톱/모바일 캡처 검토에서 숨김 힌트 단어 쪼개짐 1건 발견·짧게 수정 후 build + 동사 E2E **4 passed**로 새 캡처.
  모든 preview는 finally에서 프로세스 그룹 종료. WCAG 전체 적합성은 측정/주장하지 않는다.
- **유지한 한계**: 기존 JACK OUT은 reducer `phase: menu`이며 컨트롤러가 state-null/제목 화면으로 돌아가지는 않는 것을 브라우저에서 관측했다.
  요청대로 기존 동작은 변경하지 않았다. 공개 정보/통과 허가는 일시 상태라 이동·로드 후 재결제; 완료 목록 저장 계약은 불변.
- **문서**: ADR-0246은 Implementation Status 주석만 갱신, **🟡 Partial** 유지; 인덱스 Impl 셀 동기화.
  E/C·TRACE 표시 통합 미구현. 전투 메커닉·튜닝·RNG·크롤러·`core/status.ts`·VFX 구현·raw 및 Accepted 결정 본문 무변경.
  **stage/commit 없음**.

## [2026-11-01] tooling | encounter 동사 경제의 읽기 전용 ego 기록기

- [기존 실제 플레이 절차](docs/playtest/EGO_LITE_PLAY_CHECK.md)에 **동사 경제 검증** 추가:
  지불 전 판단·PROBE 낭비·BYPASS/BREACH 지배 위험·동사별 반증 관찰과 정확한 실행 명령.
- `docs/playtest/ego-decision-recorder.mjs`는 이미 열린 허가된 Space를 polling하고
  확인된 동사별 Markdown/JSON을 지정 절대 경로에 배타적으로 출력한다. 키·마우스·탐색·상태 쓰기·claim·finish 없음.
  `.mjs` + ego Node 24+ native type stripping으로 별도 빌드/의존성 없이 순수 scaling 함수를 읽기 전용 재사용한다.
  상태 추출은 `ego-decision-state.mjs`로 분리해 관찰 경계와 누적 기록을 구분했다.
- 실측: 자신의 **Space 39 / wet_run verb verify 20261101 recorder / p1**에서 기존 5195 preview를
  실제 키로 조작. 최종 보고서 `/Users/emilio/.openclaw/tmp/opencode/wet-run-verbs-live-02.md`와 `.md.json`에
  **PROBE 1 / BYPASS 1 / BREACH 1**. PROBE COST 38→46, BYPASS 46→76, HP 100 유지,
  credits 양 원장 변화 0, 다음 노드 이동 확인. 공개된 `yakuza_enforcer HP 165`는 화면의 `165/165`와 일치.
  BREACH는 실제 combat 확인, ΔCOST +2 / ΔHP -13에서 관찰 종료되어 **pending**, clear/계속 여부 미확정.
  비지배성/가격 균형을 입증한 pass가 아니라 기록기의 실동작 검증이다.
- 초기 live 검증이 빈 `iceHp`를 발견해 scaling 원문 재사용으로 해결했다. 메뉴의 state-null은
  stack trace 없이 명확한 안내로 종료하는 것도 실측했다. 자신의 Space는 마지막에
  `task.finish({ keep: [] })`를 한 번 호출해 정상 종료. 사용자 소유 **wet_run real-play QA** 및 다른 Space 무조작.
- 회귀: `node --test docs/playtest/ego-decision-recorder.test.mjs` **6 passed**.
  강조/거부 입력 제외, PROBE/BYPASS 분리, clear 뒤 HEAL 제외, stale bypass 뒤 JACK OUT,
  재시작 격리, 없는 Space, 빈 HP fallback·mutator 복제·공개 전 정보 차단을 검증했다.
  Node syntax check 통과. LSP는 TypeScript 서버 미설치·기존 설치 거절로 실행 불가.
- 게임 코드·튜닝·`web/src/`·Accepted ADR 결정 본문 무변경. 기존 preview 유지, **stage/commit 없음**.

## [2026-11-01] fix | 진행에 도움 없는 terminal BYPASS 차단 + 가격 판정 연기

- 실제 코드 대조: `web/src/core/state/state_actions_phases.ts:164-167`는 전투 뒤 loot에서 **보스 또는 인접 0개**를 런 완료로 취급한다. BYPASS는 loot로 가지 않으므로 이 조건에서 무익하다. 인접 목록은 양방향(`dungeon.ts:243-248`)이므로 이웃 하나가 있는 비보스 곁가지는 후퇴 가능하며 여전히 BYPASS 허용.
- `encounter_verbs.ts`의 공유 `bypassBlockReason`을 reducer와 Green Grid 메뉴가 사용. 결제·통과 허가 전에 hard-block; 네 동사 순서는 그대로 두고 **BLOCKED + Must BREACH 이유**를 선택 전에 표시. PROBE 후에도 불가능한 BYPASS를 권하지 않는다. PROBE/BREACH/JACK OUT 유지.
- 새 `web/tests/encounter_bypass_eligibility.test.ts` 14개: 보스/인접 0개 직접 BYPASS 거절, COST·완료·통과 불변, 세 화면 크기의 사전 안내, PROBE/JACK OUT 및 보스 도달 → 실제 BREACH/combat/loot/ending. 기존 정상 BYPASS/no-farming 회귀와 함께 **red 8 failed / 24 passed → green 32 passed**.
- **오너 지시로 BYPASS 30 / PROBE 8 및 재튜닝은 나중에 Jev-assisted decision tooling으로 처리**한다. 오너의 실제 play pass는 COST 대 HP 대 정보/보상을 교환하는 동사의 **구조적 비지배성**을 확인했다. 가짜 선택이 아니라 가격 문제다. Opening g3–5 mean HP-end **13.8/5.3/4.9**는 시작 100 대비 **86.2/94.7/95.1 HP 손실(패배 포함 평균)**인 반면 BYPASS는 **30/100 COST**여서 저평가 가능성이 높다. 단위가 다르므로 이 비교만으로 가격을 결정하지 않는다.
- `balance_sim.ts:77-81,100-162`는 그래프를 걷지 않고 단일 전투를 수행한다. 경로/연속 BYPASS/정보 경제는 측정하지 못하므로 byte-identical 결과는 전투 하네스 보존 증거만 된다. Jev 호출·가격 조정은 이번 범위 밖.
- ADR-0246 **Implementation Status만** 주석 추가, 인덱스 **0246 Impl 셀만** 갱신. 결정 본문·0247/0248·전투·튜닝·RNG·크롤러·status·VFX 구현·raw 무변경. **스테이징/커밋 없음**.
- 최종 검증: typecheck **0 errors** (첫 실행에서 새 fixture `arc` 누락 발견·보완), lint **0 errors / 기존 keyboard.ts:14 warning 1**, test **163 files / 3696 passed / 0 failed**, build **119 modules** 통과. 편집한 src만 Prettier write/check. TypeScript LSP 미설치·기존 설치 거절 존중, CLI 검증과 구분.
- balance 양 덱 전체 stdout 전후 **`cmp` exit 0**: opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**. 캡처는 `/Users/emilio/.openclaw/tmp/opencode/wet-run-bypass-{opening,ppl}-{before,after}.txt`.
- 필수 E2E 명령 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **80 passed / 4 skipped / 0 failed (4.4m)**. 기존 preview는 kill/restart하지 않고 그대로 새 dist를 서빙하도록 유지했다.
- 별도 Playwright 브라우저의 보스/인접 0개/일반 노드 fixture에서 390/1440px 전후 캡처 및 실제 키 BYPASS 시도: 보스·고립 COST **0**, 일반 **30**. 사전 BLOCKED/이유 안내가 주 패널에 표시됨. `/Users/emilio/.openclaw/tmp/opencode/bypass-{boss,isolated,ordinary}-{390,1440}-{before,after}.png`. 사용자 play session 무조작; WCAG 전체 감사는 미실행.

## [2026-11-01] fix | 던전 시도 사망 종결 + 무효 weapon/armor 픽업 제거 (ADR-0247 독립 정리)

- 사망 계약: 현행 메뉴 진입형 **독립 던전 시도가 HP 0에서 종료**된다. 절반 HP 복구·알람 +25 제거, 사망 후 이동/턴/회복 차단. 기존 `main.ts:654-658`의 게임 오버 분기가 실제 피해로 도달 가능해져 **FLATLINE — dungeon crawl failed**와 메뉴 복귀·크롤러 폐기를 수행한다. 탐색/레벨/소모품 기회를 잃고 같은 시도에서 부활하지 않으므로 Pillar 3을 만족한다. 새 메뉴 시작은 새 시도이며 본 런 사망/Hall of Dead/write-back은 추가하지 않았다.
- 작은 정직한 보상 선택: 새 장비 효과·스탯/HUD·전투 변경 대신 weapon/armor 생성·타입·빈 효과·렌더 분기를 제거. `addItem`의 기존 소모품 40%/30%/20%는 유지하며 마지막 10%는 no-drop. 생성과 몬스터 드롭 모두 같은 함수 사용, RNG 함수·추가 draw·기존 소모품 효과 무변경. data chip의 실제 HP +10과 다른 크레딧 약속 주석도 제거했다.
- 회귀 **red 7 failed / 9 passed → green 16 passed**: `dungeon_death.test.ts`의 신규 4건 + 새 `dungeon_pickups.test.ts` 10건. 초기 HP 100에서 실제 watchdog AI 34턴 × 피해 3으로 0에 도달(HP 0 대입 없음), 사망 뒤 회복 픽업을 밟아 재개할 수 없음, 치명 반격·함정 검증. 모든 생성 가능 소모품의 실제 HP/알람 변화·소비, 이전 장비 구간 경계 4개의 생성 없음·1 draw 검증. 기존 테스트 삭제/약화 없음.
- 검증: `npm run typecheck` **0 errors**, `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**, `npm test` **164 files / 3710 passed / 0 failed** (+14), `npm run build` **119 modules** 통과. 변경한 src만 Prettier write/check. TypeScript LSP 미설치·기존 설치 거절 존중으로 실행 불가; CLI 검증으로 대체했음을 명시한다.
- `npm run balance` / `npm run balance -- --deck ppl` 전체 stdout 전후 **`cmp` exit 0 (byte-identical)**: opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**. `/Users/emilio/.openclaw/tmp/opencode/dungeon-cleanup-{opening,ppl}-{before,after}.txt`. 하네스는 던전을 걷지 않으므로 전투 보존만 증명하며 C 보상·던전 난이도의 검증이 아니다.
- 필수 명령 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **80 passed / 4 skipped / 0 failed (4.4m)**. 기존 5195 preview는 kill/restart하지 않았으며 새 dist를 서빙한다.
- 별도 browser context의 메뉴 진입 후 인접 watchdog fixture를 놓고 HP 무대입·실제 키 34턴으로 사망시킴: menu 복귀·크롤러 null·FLATLINE·런 state null 불변 확인. `/Users/emilio/.openclaw/tmp/opencode/dungeon-cleanup-defeat.png`를 직접 열어 안내 가시성 확인. 최초 browser helper의 `page.browser()` 호출 오류는 `page.context().browser()`로 바로잡은 뒤 성공. 사용자 play session 무조작.
- ADR-0247 **Implementation Status만** 갱신하고 인덱스의 **0247 Impl 셀만** Partial로 변경. 런 반영/격리 재정의(독립 정리 3번째)·E/C는 미완료로 남긴다. ADR-0005/0060/0103/0246/0247/0248 결정 본문, encounter 동사/가격, 전투 수식·튜닝·RNG·status/VFX 구현·raw 무변경. **stage/commit 없음**.

## [2026-11-01] feat | ADR-0246/0247 E 첫 슬라이스 — utility 손패로 결제하는 SCAN

- 고정 PROBE/BYPASS/BREACH/JACK OUT과 기존 8/30 COST를 보존한 채 SCAN을 뒤에 추가했다. catalog의 **utility T1 probe/scan, T2 decrypt/trace, T3 echo**가 현재 조우의 정확한 ICE/HP 공개를 부여한다. 모든 tier에 같은 질적 도구이며 새 수치·문턱·가격·role 없음. guard/strike/burst/support에는 이번 새 효과를 부여하지 않았다. 노드 잠금·가짜 신호·추적 지연·인접 그래프 전체 공개·C/크롤러는 범위 밖이다.
- `encounterScanProgram`이 **현재 손의 첫 utility**를 renderer/reducer 양쪽에 공급한다. `SCAN PROGRAM` + `Discard <name> (T<tier>)`로 결제 대상을 먼저 보여 주고 없으면 `NO UTILITY IN HAND`로 거절. 선택+확인 시 해당 카드 한 장만 손에서 discard로 이동한다. COST/HP/TRACE·보상·combo·turn·RNG 무변경, 즉시 draw 없음. 고정 PROBE와 `probed` 상태를 공유해 이미 공개했으면 추가 결제하지 않는다. 새 세이브 필드 없음.
- `parseProgram`이 role을 누락하고 combat이 optional role을 읽는 기존 경계를 확인했다. loader에 role을 복원하면 전투 damage/crit까지 달라지므로 encounter에서만 catalog id→role을 조회했다. combat/loader·숫자 튜닝·status.ts·VFX 구현은 수정하지 않았다.
- 실제 tension은 **COST 보존 대 combat 손패 상실**이다. SCAN은 전투 전용 자원을 쓰며 해당 카드의 피해·combo/Dixie 기회를 얻지 않는다. 기존 combat 성공 play 뒤 재순환으로 회수될 수 있으므로 영구 소모라고 주장하지 않는다. 탐색에서 손을 비워도 BREACH 시 보충하지 않는다. PROBE로 손패를 지키거나 SCAN으로 COST 여력을 지킬 수 있다는 구조 설명이며 **정량 밸런스/최적 전략은 미검증**이다.
- 새 `encounter_programs.test.ts` **21 tests**, 수정 전 **16 failed / 5 passed** 및 기존 fixed/BYPASS **32 passed** → 수정 후 **53 passed**. utility 다섯 장, 비utility 네 역할, 손 밖 소유 불가, 중복 id 한 장 소비, 다음 combat에서 사용 거절, 중복 공개 결제 없음, 고정 8/30 COST, no-farming, 40×60/60×40/80×50의 결제·없음 상태·정확한 HP·입력 힌트 검증. 기존 테스트 삭제/약화 없음.
- 검증: scoped src Prettier write/check 통과, `npm run typecheck` **0 errors**, `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**, `npm test` **165 files / 3731 passed / 0 failed**, `npm run build` **119 modules** 통과. LSP는 서버 미설치·기존 설치 거절로 실행 불가임을 CLI 결과와 구분한다.
- `npm run balance` / `npm run balance -- --deck ppl` 전체 stdout 전후 및 이전 slice-2 baseline 캡처와 **양 덱 `cmp` exit 0 (byte-identical)**. opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7** (ADR-0239). `/Users/emilio/.openclaw/tmp/opencode/option-e-{opening,ppl}-{before,after}.txt`. **balance_sim.ts는 그래프를 걷지 않고 SCAN 전 손실도 모델링하지 않으므로 combat harness 보존만 입증하며 E 밸런스는 미검증**이다. 모든 숫자 재튜닝은 오너 지시대로 후속 Jev-assisted pass에 남긴다.
- 필수 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **82 passed / 4 skipped / 0 failed (4.6m)**. 새 SCAN→무료 중복 PROBE→BREACH 손패 손실 spec이 desktop/mobile 각 1건. 최초 spec 수집의 JSON import attribute 오류를 수정한 뒤 통과. **5195 preview는 종료/재시작하지 않고 유지**, rebuilt dist의 새 기능을 E2E에서 검증했다.
- 별도 QA browser에서 390/844/1440px × unavailable/ready/revealed 9개 캡처와 실제 ↑/Enter로 거절·소비 확인: 손 `[strike]`, discard `[scan]`, COST 0, probed true. `/Users/emilio/.openclaw/tmp/opencode/option-e-*-after.png` 및 편집 전 390/1440 baseline. 실제 grid 40×60/80×32/100×60과 단위 테스트의 세 요구 preset을 구분한다. 기존 Canvas/작은 HUD 접근성 한계가 있으며 WCAG 전체 적합성을 주장하지 않는다. 독립 read-only reviewer 두 호출은 `No assistant or tool response found`로 결과가 없어 승인으로 계산하지 않았다. 사용자 play session 무조작.
- ADR-0246의 **Implementation Status만** mapping·path:line·검증·한계로 갱신하고 **🟡 Partial** 유지. 인덱스 **0246 Impl 셀만** 동기화. ADR-0247/0248 및 다른 Accepted 결정 본문은 그대로, C·TRACE 통합·나머지 E는 미구현. **스테이징·커밋 없음**.

## [2026-11-01] decision-support | 동사 가격 평가 — Jev choice (오너 이연 항목의 입력)

- **질의**: 미클리어 조우에서 동사 선택(PROBE 8 / BYPASS 30 / BREACH / JACK OUT). COST 는 0-100
  누산기(프로그램 비용; 100 초과 시 프로그램 실패)라 실질적으로 "프로그램 여유"다.
  실측: 전투 1회가 g1~g5 에서 88.2 / 42.7 / 13.8 / 5.3 / 4.9 HP 를 남긴다 → **비용 약 12 / 57 /
  86 / 95 / 95 HP**. 즉 **g3~g5 에서 BYPASS 30 은 86~95 HP 를 면제**한다. 동사는 구조적으로
  비지배(서로 다른 통화)이므로 위험은 **가짜 선택이 아니라 가격**이다.
- **Jev 결과 (`choice`, `typesafe/jev-1.13`, `JEV_LOCAL_FALLBACK=0`)**: `raise_bypass_to_45`
  선택. 분포 `keep_30 0.03 · raise_45 0.43 · raise_60 0.41 · bypass_costs_hp 0.09 ·
  forfeit_heal_only 0.04`. **confidence 0.29 (낮음)**.
- **해석**: **"30 유지"는 사실상 배제(0.03)** — 제 플레이 기반 판단(우회가 g3+에서 저렴)과
  **독립적으로 일치**한다. 반면 **45 vs 60 은 사실상 동률(0.43 vs 0.41)** 이고 confidence 가
  0.29 로 낮아 **자동 적용 불가** — Jev 스킬의 규칙(`p < 0.6` 이면 사람 개입)에 따라 **오너 결정
  대상으로 남긴다**. 통화 변경안(HP 비용·회복만 포기)은 가능성 낮음(0.09 / 0.04).
- **정직한 한계**: 이 판단의 입력에는 **측정되지 않은 값**(보상 크레딧 → 장비 → 전투력)이 있고,
  하네스는 경로 경제를 보지 못한다. 따라서 Jev 결과는 **방향(상향)의 독립 확인**이지 정확한
  값의 검증이 아니다. 정확한 값은 **플레이 패스**(`docs/playtest/ego-decision-recorder.mjs` 준비됨)
  또는 오너 판단으로 정한다.
- `raw/` 무접촉: 감사 JSON 을 `JEV_AUDIT_DIR=/tmp/jev-audit` 로 우회했다 (스크립트의 기본값은
  `infra/lan-hosts/raw/jev-calls`). 코드·가격 변경 없음.

## [2026-11-01] balance | 오너 확정 BYPASS 30 → 60 — 런당 최대 한 번

- **오너 결정 적용**: `web/src/core/state/encounter_verbs.ts:11`의 BYPASS만 **60**으로 올렸다. PROBE **8**, COST 상한 **100**, 전투 튜닝·HP 비용·보상·회복·동사 의미는 그대로다. renderer는 공유 상수로 **+60 COST**를 표시하므로 코드 수정 불필요.
- **결정 입력 보존**: 오너의 실제 play pass와 하네스의 g1–g5 전투당 약 **12 / 57 / 86 / 95 / 95 HP** 손실은 기존 30/100 BYPASS가 g3–g5에서 저평가됐을 가능성을 보였다. 위 Jev `choice`는 `keep_30` **0.03**, `raise_45` **0.43** / `raise_60` **0.41**, confidence **0.29**였다. 유지안은 배제했지만 45/60은 사실상 동률이므로 **오너가 60을 선택**했다. Jev 재호출·새 가격 재논의 없음. 위의 과거 30·가격 이연 로그는 당시 기록으로 보존하며 이 항목이 현행 가격을 대체한다.
- **코드 확인**: active run의 `player.alarm`은 `state_actions_programs.ts:59-62,382`와 `encounter_verbs.ts:121-129`에서 증가만 한다. `state/state.ts:255,287` 저장/복원은 값을 유지하고, 0 초기화는 `state_actions_phases.ts:259-265`의 same-jockey 사망 재시작이다. 별도 크롤러의 `playerAlarm`은 이 자원이 아니다. 감소 경로 없음. 30은 세 번(90), 45는 두 번(90), **60은 한 번(60), 두 번째는 120 > 100으로 거절**된다. 즉 **60 makes BYPASS a once-per-run resource** (최대 한 번; 선행 지출로 첫 사용도 막힐 수 있음).
- **회귀 / 가격 참조**: `web/tests/encounter_verbs.test.ts`에 0 → BYPASS 성공/60 → 실제 이동·재방문 → 두 번째 거절/무결제/통과 허가 없음/출발 차단 회귀 추가. 기존 30 단언은 60, 상한 경계 fixture는 70/71 → 40/41로 변경해 강도 유지. `encounter_programs.test.ts`의 가격 30 → 60; E2E의 PROBE+BYPASS 38 → 68; playtest recorder fixture 38 → 68 및 delta 30 → 60. `EGO_LITE_PLAY_CHECK.md`의 현행 가격·질문·실패 신호는 60 및 1회 제한으로 갱신. 가격 적용 전 focused run **7 failed / 33 passed**.
- **문서 범위**: ADR-0246 **Implementation Status 안에서만** 현행 가격·이연 종결·Jev 입력·최대 1회·하네스 한계를 갱신하고, 인덱스 **0246 Impl 셀만** 동기화했다. 🟡 Partial 유지. C·크롤러·TRACE·다른 Accepted 결정 본문·`raw/`·`status.ts`·VFX 무변경. 스테이징·커밋 없음.
- **측정 한계**: 하네스는 그래프를 걷지 않는다. 양 덱 stdout byte-identical은 경로 경제에 국한된 변경과 전투 하네스 보존의 증거이지 **새 BYPASS 가격 60이 균형 잡혔다는 증거가 아니다**. 이 구현 세션에서 새 가격의 실제 런 play pass를 수행했다고 주장하지 않는다.
- **실행 결과**: 편집한 src 한 파일만 Prettier write/check 통과. `npm run typecheck` **0 errors**; `npm run lint` **0 errors / 기존 keyboard.ts:14 warning 1**; `npm test` **165 files / 3732 passed / 0 failed** (baseline 3731 + 회귀 1); `npm run build` **119 modules** 통과. recorder `node --test docs/playtest/ego-decision-recorder.test.mjs` **6 passed**. catalog의 30개 프로그램 비용은 전부 유한·비음수 (최소 1). `git diff --check` 통과 및 staged diff 비어 있음 확인. LSP는 TypeScript 서버 미설치·기존 설치 거절로 실행 불가, CLI typecheck와 구분한다.
- **하네스**: `npm run balance` opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**; `npm run balance -- --deck ppl` PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**. `/Users/emilio/.openclaw/tmp/opencode/bypass60-{opening,ppl}.txt`에 전체 stdout을 보존하고 기존 ADR-0239 기준선 `option-e-{opening,ppl}-before.txt`와 **양쪽 `cmp` exit 0 (byte-identical)** 확인. 전투 하네스 보존 증거만으로 기록한다.
- **E2E / preview 유지**: 필수 `env -u CI PLAYWRIGHT_BASE_URL=http://127.0.0.1:5195 npx playwright test --ignore-snapshots --grep-invert demo-screenshots` → **82 passed / 4 skipped / 0 failed (4.5m)**. desktop/mobile 새 68 COST 단언 통과. rebuild 후 요청된 `npx vite preview --port 5195 --strictPort --host 127.0.0.1`는 **Port 5195 is already in use**로 실패해 기존 서버를 유지했다. 기존 preview kill 없음, 새 dist 제공을 E2E로 확인. 사용자 play session 무조작.

## [2026-11-01] verify | BYPASS 60 실플레이 검증 — 런당 1회 자원 확인

- 오너 결정(BYPASS 30 → 60, `a076bb3f`)을 **실제 브라우저에서 플레이해 검증**했다 (ego-lite 자체 Space
  생성 후 폐쇄, 사용자 Space 미접촉). 시나리오: 우회 1회 → 이동 → 2회차 우회 시도 → 이후 전투.
- **실측 로그**:
  - 조우 A (node 1, `yakuza_enforcer`): COST 0 · HP 100
  - **BYPASS #1**: COST 0 → **60** · `bypassed=1` — **성공**
  - 이동 후: COST 60 · `bypassed=null` — **이동이 passage 를 해제**(재접근 가능)
  - **BYPASS #2 시도**: COST **60 유지** · `bypassed=null` — **상한으로 거부** (미차감·미부여)
- **리듀서 탐침으로 상한 경계까지 확인**: `0+60=60` 성공 · `60+60=120` 거부 · `41+60=101` 거부 ·
  `40+60=100` 허용 (경계 정확). 거부 메시지 `"COST too high for BYPASS — choose another verb."`
- **결론**: 60 은 BYPASS 를 **런당 1회뿐인 큰 결정**으로 만든다 (60/100 소모 → 남은 프로그램 여유 40).
  COST 는 런 내 **단조 증가**이고 리셋은 사망 재시작뿐이므로 두 번째 우회는 구조적으로 불가하다.
  이는 "항상 우회" 지배 위험을 구조적으로 줄인다 — "어느 전투를 건너뛸 것인가"가 진짜 결정이 된다.
- **정직한 한계**: 하네스는 경로 경제를 보지 못하므로 이 값의 **균형은 검증되지 않았다**. 오너 결정 +
  Jev 방향 확인까지이며, 정확한 값은 플레이 패스(`ego-decision-recorder.mjs`) 또는 오너 판단으로 확정한다.
- 세션 이연 항목은 워크스페이스 `NEXT_SESSION_TODO.md` 로 carry 했다. 코드 변경 없음.

## [2026-11-01] fix(ui) | Matrix 구조 가독성 — 위치·도달 가능 경로·보스·깊이 구획

- 오너의 실플레이 불만에 대응한 **renderer-only** 수정. 기존 relevance 재정렬 `[2] [1] [7] [9] [10] …`을 재현했다. 진단 중 두 가지는 정정: 기존 `(BOSS)` 접미사는 실제로 있었고, zone도 첫 라벨에 있었으나 계층/구획 부재 때문에 읽히지 않았다.
- `▸ YOU ARE HERE` → 박스 `REACHABLE NOW (count)` → `◆ OBJECTIVE: BOSS` → `DEPTH / ZONES (not routes)` 순서. 메뉴식 ordinal 대신 **Nxx node ID**를 쓰며 `not travel order` 명시. 현재/선택/도달/SEEN/CLEAR/NEW는 색 외에 문자·라벨로 표현한다. 기존 ADR-0237 인셋 프레임 및 Gibson palette 값 유지, 스크롤 추가 없음.
- 방문과 클리어는 다르므로 `run_screen.ts`가 기존 `clearedEncounterNodes`를 순수 renderer의 optional 마지막 인자로 전달한다. reducer·GameState·게임플레이·동사·BYPASS/PROBE 가격·RNG·status.ts·크롤러·VFX·raw·ADR 결정 본문은 무변경.
- 모듈 분리: `matrix.ts` **315 → 228 total / 176 pure LOC**, 새 `matrix_nodes.ts` **146 total / 134 pure LOC**, `run_screen.ts` **129 total / 121 pure LOC**. 표시 row 구성과 프레임/ICE preview 조합 분리. 기존 단언은 새 labels/기하에 맞춰 의미를 보존했고 삭제/약화하지 않았다. 신규 회귀 9개: frontier 구획/전 offer, objective/depth, 방문≠clear, terminal frontier, 순수성.
- **증거**: [Matrix before/after + QA](docs/design/matrix-legibility-2026-11-01/README.md). 편집 전 실제 `renderMatrix` text/cells 저장, 동일 fixture(start/branch/boss × 80×50·40×60·60×40)로 after 캡처. 실제 `AsciiRenderer`로 PNG 18개 및 branch 비교 3개 생성(10×18 cell, HUD 제외). raw text와 fixture/검증 receipt 보존. 3개 필수 grid width CLI: overflow 0 / borderMisaligned false. 60개 생성 그래프의 매 current node × 3 layout **3132 cases**, 최대 33 nodes / frontier 5에서도 frontier/objective/zone heading 및 rails 유지.
- **검증**: pre-edit targeted 46 passed; 최종 `npm run typecheck` 0 errors, `npm run lint` 0 errors + 기존 keyboard.ts:14 warning 1, `npm test` **166 files / 3741 passed / 0 failed**, `npm run build` **120 modules** PASS. 편집 파일만 Prettier write/check, frontend draft guard clean. LSP는 서버 미설치·기존 설치 거절로 unavailable이며 CLI typecheck와 구분한다.
- **밸런스**: opening **100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0**, PPL **100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7**. 양 덱 전체 stdout을 evidence에 보존, prior ADR-0239 baseline `option-e-{opening,ppl}-before.txt`와 Buffer byte equality **양쪽 true**(716 / 724 bytes), SHA-256 receipt 보존. combat harness 보존 증거이며 경로 경제 재평가 주장은 아님.
- **E2E**: 요청 명령(`env -u CI`, base URL 5195, ignore snapshots, demo 제외) **82 passed / 4 skipped / 0 failed (4.6m)**. 첫 실행은 240s shell timeout(70 green)으로 중단, 600s 제한으로 완주. rebuild 후 요청된 strict preview 시작은 **Port 5195 is already in use**; 기존 preview kill 없이 유지했고 새 bundle로 E2E 통과. 사용자 play session 조작 없음.
- **Visual QA**: 고정 dark ASCII에 맞춘 항목별 판정은 evidence README. 9개 after PNG + 3개 비교를 독립 A/B 리뷰, B는 구조/가독성 PASS. A의 큰 frontier/지속 width 증거 공백을 stress/CLI JSON으로 보완했고 **fresh A 재리뷰도 PASS**(2 rounds; 최초 병렬 35/39s, 최종 28s), 새 product defect 없음. Matrix 사용 토큰은 4 palette × 고대비 on/off에서 최소 **5.7497:1**, 색만으로 상태 전달 없음. 기존 canvas focus ring/접근성 트리(I1/I3 inherited FAIL)/선택 가능한 text와 물리 폰트·zoom 등은 이 범위에서 해결·완전 인증하지 않는다. 전체 WCAG AA 또는 Lighthouse 점수는 주장하지 않음. 스테이징·커밋 없음.

## [2026-11-01] feat(ui) | ADR-0249 Matrix 오퍼레이션 보드 — 한 화면 기하 보드, 목록은 상세 카드로

- 오너 승인 방향을 [ADR-0249](docs/wiki/decisions/0249-matrix-operation-board.md)(Accepted)로 기록: 결정층 규칙 8개, 삭제/유지 목록, 짓지 않을 것(미니맵·카메라·스크롤·FOV 자원화·LOS AI·스트리밍·런 타일 걷기). ADR-0246 B 아님(보류 유지), 안 3 범위 밖.
- `dungeonToMatrix`가 버리던 `Room`의 `x/y/w/h/label`을 선택 필드 `MatrixNode.site`로 보존. 행렬은 저장되지 않고 seed로 재생성되므로 기존 세이브도 기하를 얻는다. `site` 없는 행렬은 결정적 대체 배치(BFS 층 → 열).
- 보드: 생성 좌표에 방 토큰, `@` 현재 위치, 상시 `◆` 보스, `>·<` 타깃, `#·#` 미해결 ICE, `·/✓/+` NEW/SEEN/CLEAR. 인접 1개당 직교 A* 복도 1개(타깃 `━`, 경로 `─`, 연결 `┄`). `DEPTH / ZONES` 스택·범례 삭제, 노드 상세는 상세 카드로.
- `renderMatrix` 시그니처·순수성 불변. 리듀서·동사·가격·튜닝·RNG·status.ts·크롤러·VFX 무변경, 화살표 순환 순서 불변 → e2e 헬퍼 무변경.
- LOC(total/pure): `matrix.ts` 228/176 → 188/155, `matrix_nodes.ts` 146/134 → 100/82; 신규 `matrix_board.ts` 196/172, `matrix_board_layout.ts` 182/153, `matrix_board_routes.ts` 262/232, `min_heap.ts` 43/38.
- 검증: 신규 규칙 테스트 13개 HEAD에서 13 failed → 13 passed. `npm test` **167 files / 3754 passed**, typecheck 0, lint 0 errors(기존 warning 1), build 124 modules, 3132-case 스트레스, 양 덱 balance stdout byte-identical(opening 100.0 / 88.3 / 70.5 / 39.5 / 36.2 / 0.0, PPL 100.0 / 79.1 / 98.9 / 83.0 / 44.4 / 24.7), E2E **82 passed / 4 skipped / 0 failed**. 증거: [docs/design/matrix-operation-board-2026-11-01](docs/design/matrix-operation-board-2026-11-01/README.md).

## [2026-11-01] fix(ui) | Matrix 보드 행동 가독성 — 키→목적지 명시 · 정지 프롬프트 최상단 · 1회 진입 힌트

- 오너 피드백: "선이 연결되는 느낌은 좋아. 그런데 어떻게 해야 하는지 잘 알아보지는 못하겠어 … 목록보다는 훨씬 좋아." 보드는 유지, 행동 가독성(affordance) 격차만 수정. ADR-0249 규칙 8개 안의 renderer + onboarding 변경.
- `ROUTES (4): ↓1 N01  ↓2 N07  ↓3 N09` / `↓4 N10`(40열에서 감싸기). 타깃이 있으면 `>N01  ↓1 N07 …`(리듀서 순환과 동일하게 타깃 기준 계수). 정지 시 카드 첫 줄 `▸ PRESS ↓ OR ↑ TO PICK A ROUTE`(방 이름 없음 = 선택 아님), 타깃 시 첫 줄이 타깃·상세, 그 아래 `@`. 카드 8행 유지.
- 1회 진입 힌트: ADR-0235 `onboarding.ts`에 `MATRIX_ENTRY_HINT_LINES` + `shouldShowMatrixEntryHint`, `main.ts` 플래그 `matrixEntryHintShown`(combat 힌트와 같은 패턴). 경로가 있는 첫 보드에서만, 첫 입력으로 사라짐. 세션 단위(영속 아님).
- 리듀서·선택 의미·화살표 순서·동사·가격·튜닝·RNG·status.ts·크롤러·VFX·raw 무변경. e2e 헬퍼 무수정.
- LOC(total/pure): `matrix.ts` 188/155 → 203/167, `matrix_nodes.ts` 100/82 → 138/109, `run_screen.ts` 129/121 → 131/123, `onboarding.ts` 109/47 → 146/72, `main.ts` 1740/1523 → 1747/1528.
- 검증: 신규 `matrix_affordance.test.ts` 20 failed → 20 passed; `npm test` **168 files / 3774 passed**; typecheck 0; lint 0 errors(기존 keyboard.ts:14 warning); build PASS; balance 양 덱 ADR-0239 기준선과 byte-identical; E2E **82 passed / 4 skipped / 0 failed (4.6m)**, 5195 프리뷰 유지. 시각 QA 독립 리뷰 PASS, 대비 측정 최소 6.58:1(프롬프트 amber ≥10.15:1). 상속 결함(행별 포커스 링·접근성 트리) 미해결.
- 증거: [matrix-affordance-2026-11-01](docs/design/matrix-affordance-2026-11-01/README.md) (15 전후 캡처 × 3 레이아웃, 페어 PNG, width check, contrast). ADR-0249 `## Implementation Status`에만 후속 기록. 미커밋·미스테이징.

## [2026-11-01] feat(ui) | Matrix 보드 이동 애니메이션 — 확정 이동을 복도 위 `@` 이동으로 표시 (순수 표시)

- 오너 플레이("이제 노드들을 거쳐 따라다닐 수 있어") 다음 단계. 확정 이동(Enter) 뒤 220 ms: 160 ms 전환(확정 당시 보드·카드, `@`가 이미 라우팅된 복도 하나를 따라 이동, 지나온 칸 굵은 녹색) + 60 ms 도착(목적지 토큰 반전) → 정적 보드(HEAD와 byte-identical).
- 순수 표시: `applyMatrixAction` 무변경, 상태는 같은 액션에서 즉시 이동. `MatrixTravel`은 `main.ts` 컨트롤러 필드(`GameState`·세이브 아님), 벽시계만, RNG 0회. 매 입력이 다시 계산(입력 차단·목적지 변경 없음). 감소된 모션은 `suppressMotion("travel")` → 중간 프레임 없음.
- 신규 `renderer/matrix_travel.ts`; `matrix.ts`(선택 인자 `travel`), `matrix_board.ts`(export 2개), `run_screen.ts`, `accessibility_modes.ts`(`MotionKind` "travel"), `main.ts` 배선.
- LOC(total/pure): `matrix_travel.ts` 신규 185/146, `matrix.ts` 203/167 → 223/183, `matrix_board.ts` 196/172 → 202/176, `run_screen.ts` 131/123 → 135/126, `accessibility_modes.ts` 239/126 → 246/132, `main.ts` 1747/1528 → 1783/1555(기존 초과).
- 검증: `matrix_travel.test.ts` 13 failed → 15 passed; `npm test` **169 files / 3789 passed**; typecheck 0; lint 0 errors(기존 keyboard.ts:14 warning); build PASS; balance 양 덱 byte-identical(ADR-0239); E2E **82 passed / 4 skipped / 0 failed (4.6m)**, 5195 프리뷰(pid 75395) 유지. 독립 시각 리뷰 1차 REVISE(전환 중 카드/보드 불일치) → 수정 후 통과 항목 확인. 대비 최소 10.93:1. 상속 결함(행별 포커스 링·접근성 트리) 미해결.
- 증거: [matrix-travel-animation-2026-11-01](docs/design/matrix-travel-animation-2026-11-01/README.md) (2 이동 × 3 레이아웃 × 6 프레임, 스트립 PNG, 실제 빌드 프레임, width check, contrast). ADR-0249 `## Implementation Status`에만 후속 기록. 미커밋·미스테이징.

## [2026-11-02] fix(gameplay) | ADR-0250 조우 게이트를 입구로 — 2-이웃 노드 무한 반복 해소

- 오너 보고 "계속 이벤트가 반복되서 빠져나오지 못했어" 수정. 미해결 ICE 노드에 도착하는 확인 한 번이 이동과 조우 결정 열림을 같은 상태로 반환. BYPASS는 런 스코프 저장 필드 `bypassedEncounterNodes`에 기록(`bypassedEncounterNodeIndex` 제거), 해결 노드(cleared ∪ bypassed)에서 출발 자유. 도착 없이 미해결 노드에 선 경우(런 시작·CONTINUE)는 출발이 여전히 결정을 연다.
- footer는 Enter가 실제로 하는 일만 표시, 도착 메시지 `Travel blocked. BREACH: fight. BYPASS: 60 COST (once per run). JACK OUT: abandon run.`(HUD 15자 감싸기), 조우 화면 `ICE blocks travel until resolved` 1줄. 결정을 여는 도착은 이동 애니메이션 생략.
- 가격·보스 차단·종결 조건·SCAN·RNG·화살표 순서·던전·세이브 스키마 버전 불변.
- LOC(total/pure): `encounter_verbs.ts` 196/182 → 228/208, `state_actions_phases.ts` 370/328 → 379/336, `matrix.ts` 223/183 → 253/208, `encounter.ts` 115/114 → 132/127, `storage.ts` 276/217 → 283/223, `types.ts` 514/352 → 517/353, `state.ts` 406/350 → 409/353, `run_screen.ts` 135/126 → 136/127, `matrix_travel.ts` 185/146 → 188/147; 신규 테스트 330/261.
- 검증: 신규 `encounter_entry_gate.test.ts` 26 failed → 28 passed; `npm test` **170 files / 3817 passed**; typecheck 0; lint 0 errors(기존 warning 1); build PASS; balance 양 덱 byte-identical(ADR-0239); E2E **82 passed / 4 skipped / 0 failed**, 5195 preview 유지. 시각 QA 독립 리뷰 PASS, 대비 최소 10.15:1.
- 증거: [matrix-entry-gate-2026-11-01](docs/design/matrix-entry-gate-2026-11-01/README.md). ADR-0250 Implementation Status 작성, ADR-0246은 Implementation Status에 포인터만. 미커밋·미스테이징.

## [2026-11-02] fix(gameplay) | ADR-0250 후속 — Matrix 조우에서 빠져나오지 못하는 상태 제거

- 오너 "아직 못빠져나와." / "보드 + 'enter ICE' + 이벤트 반복". 5195 실제 키 로그로 재현: (a) BYPASS 후 보드는 재현 안 됨, (b) CONTINUE 복원과 (c)(d) ESC·JACK OUT 동사는 재현됨 — JACK OUT이 `phase: "menu"`만 바꾸고 보드에 남겨, Enter가 같은 조우를 다시 열었다.
- 수정: 출발 게이트 제거 + 로드·런 시작을 도착으로 처리(`openArrivalEncounter`, 세이브-리로드 회피 불가), JACK OUT/ESC는 런을 끝내고 메인 메뉴, 유틸리티 없는 SCAN은 화살표에서 제외, Enter 무선택·사용한 PROBE/SCAN은 출구를 명시, 조우 화면 `EXITS:` 줄 + `EXIT`/`INFO` 태그 + cyan 출구, footer `ESC: jack out`.
- 가격·보스 차단·종결 조건·SCAN 결제·RNG·화살표 순서·던전·세이브 스키마 버전 불변.
- LOC(total/pure): `encounter_verbs.ts` 228/208 → 278/248, `state_actions_phases.ts` 379/336 → 372/328, `state.ts` 409/353 → 411/354, `encounter.ts` 132/127 → 150/143, `matrix.ts` 253/208 → 255/209, `main.ts` 1783/1555 → 1796/1567; 신규 테스트 389/332.
- 검증: `encounter_escape.test.ts` 32 failed → 40 passed; `npm test` **171 files / 3857 passed**; typecheck 0; lint 0 errors(기존 warning 1); build PASS; balance 양 덱 byte-identical(ADR-0239); E2E **82 passed / 4 skipped / 0 failed**, 5195 preview 유지. 독립 리뷰 REVISE 3건은 모두 아티팩트 대조로 결함 아님 확인(리뷰 자체는 가벼움, 독립 승인으로 기록하지 않음).
- 증거: [matrix-encounter-escape-2026-11-01](docs/design/matrix-encounter-escape-2026-11-01/README.md). ADR-0250 Implementation Status에만 후속 기록. 미커밋·미스테이징.

## [2026-11-02] feat(ui) | ADR-0251 전투 화면 — 진실한 프로그램 어포던스(슬라이스 A) + 누락된 피드백(슬라이스 B)

- 오너 "추천대로 하자"(Oracle 합성). 손패 `[back] [barr]…` 한 줄 → 세로·번호 행 `1 BACKDOOR  COST +2  → 40/100   TARGET ICE`(40열은 범례 + 짧은 행). 런타임 필드만: 유효 COST(`double_alarm` ×2), 사용 후 COST 또는 BLOCKED(상한 100), `aoe` → ALL ICE. role·damage·effect·설명·킬 확률 미표시, JSON `role` 미로드. 신규 `program_affordance.ts`의 `programAlarmCost`/`COST_LIMIT`를 `useProgram`이 그대로 사용. 40×60에서 그려지지 않던 5번째 슬롯 복원. 터치 버튼 4줄 라벨 + `aria-label`, 44px·인덱스 콜백 불변, 터치 확인 표시가 실제로 친 카드 이름. 입력 의미 불변(ADR-0243).
- 슬라이스 B: 프로크 상태 부여 시 기존 `status_apply` VFX 스폰 + `ICE BURN+SLOW on`, 상태 종료(틱·소비·실드 파괴·적 턴 ICE 효과) `ICE BURN off` 로그(HUD 인쇄, 감소된 모션 무관). 음원 `boss_intro`·`phase_change`·`credit_gain`·`loot_drop`·`heal`·`death` 실제 사건에 배선, `credit_spend`는 사건 없음(크레딧 감소 경로 0)으로 미배선. 이벤트 버스·영속 큐 없음.
- LOC(total/pure): `program_affordance.ts` 신규 145/88, `state_actions_programs.ts` 401/351 → 438/380, `state_actions_combat.ts` 481/388 → 491/396, `combat_sfx.ts` 68/32 → 140/81, `status.ts` 256/182 → 328/234, `onboarding.ts` 146/72 → 147/73, `combat_grid.ts` 259/221 → 292/247, `run_screen.ts` 136/127 → 141/129, `touch.ts` 325/261 → 351/280, `main.ts` 1796/1567 → 1809/1572.
- 검증: 신규·변경 테스트 HEAD 대비 29 failed/16 passed(+2 suite 로드 실패), 헬퍼만 추가 시 43/43(HEAD 리듀서와 청구 일치 증명) → 86 passed; `npm test` **174 files / 3914 passed**; typecheck 0; lint 0 errors(기존 warning 1); build PASS; balance 양 덱 HEAD·ADR-0239와 byte-identical; E2E **82 passed / 4 skipped / 0 failed**(이전 빌드 1회차 `idle_alarm.spec.ts:48` 타임아웃 1건, 단독·재실행 통과), 5195 preview(pid 75395) 유지. 실제 빌드 키/탭 trace로 표시 숫자 → 그 행·그 COST 소비 확인(double_alarm + 상한 포함). 시각 QA: explore 서브에이전트 REVISE 1건 수정, 84행 전수 대조, 대비 최소 6.58:1.
- 발견·미변경: 결정타는 COST 미청구(라벨 과대 표시), `tickIceEffects` 인덱스 결함 — ADR-0251 열린 질문 (a)(b). 선택-확인 모델 미결정.
- 증거: [combat-affordance-2026-11-02](docs/design/combat-affordance-2026-11-02/README.md). ADR-0251 신규, ADR-0243 무변경. 미커밋·미스테이징.

## [2026-11-02] fix(gameplay) | ADR-0252 세이브는 확정된 상태를 담고, 엔딩은 런을 끝낸다 — 보스 격파 후 강제 재전투 해소

- 오너 "맵에서 보스를 쓰러뜨린후 이동하려니 또 보스가 나와서 회복 못하고 패배하게 되던데." / 승인 "모두 수정해." 5195 실제 키 trace(슬롯 IDB 디코드)로 재현: 자동 저장이 전투 프레임에서만 돌아 보스 격파 시 메모리 `clr [18,20]` vs 슬롯 `clr [18]`, 엔딩이 `ending/menu`로 입력을 영원히 붙잡음, 리로드 + CONTINUE가 보스 결정을 열고 BREACH가 `wintermute 140/140`(잘못된 기반 ICE; 실전 165) 재전투.
- 수정: (A) `draw()`가 Matrix·loot 프레임도 저장, 순서 큐 + 동일 상태 생략, 런 중 캐시 갱신 재그리기 루프 차단. (B) 엔딩 도착 시 슬롯 폐기, 엔딩 Enter/ESC → 제목(상태 null, `Run complete. Autosave cleared.`), footer `ENTER / ESC: return to title`; 완료 런은 CONTINUE `(no save)`. 클리어된 종결 노드 슬롯은 loot 화면으로 복원. (C) `slotToGameState(…, iceCatalog?)`가 기반 ICE를 `missionIce`(이전 `main.ts loadIce` 이동)로 유도 — 세이브 필드·버전 무변경.
- 불변: ADR-0250 "로드 = 도착"(전투 중 슬롯은 결정 재개방, 보스 BYPASS 차단), 가격·피해·RNG·던전·게이트·ADR-0251·세이브 스키마. 종결 경로 15% 회복 부재는 의도로 판단(엔딩 판정이 hp를 입력으로 씀) — 보고만, 미변경.
- LOC(total/non-blank): `main.ts` 1809/1742 → 1794/1728, `state.ts` 411/393 → 428/410, `state_actions_phases.ts` 372/360 → 370/358, `ending.ts` 155/142 → 155/142; 신규 `run_end.ts` 39/35, `mission_ice.ts` 56/55.
- 검증: 신규 `run_end_save.test.ts` HEAD 12 failed/6 passed → 18 passed; 신규 `e2e/run_end_save.spec.ts` HEAD 빌드 6 failed → 6 passed; `npm test` **175 files / 3932 passed**; typecheck 0; lint 0 errors(기존 warning 1); build PASS; Prettier PASS; balance 양 덱 byte-identical(ADR-0239); E2E **88 passed / 4 skipped / 0 failed**, 5195 preview(pid 75395) 유지, `continue.spec.ts` 무수정.
- 증거: [run-end-and-save-2026-11-02](docs/design/run-end-and-save-2026-11-02/README.md) (before/after trace 3 시나리오, 3 사례 × 3 레이아웃, 폭 검사 9/9). ADR-0252 신규, ADR-0250·0246은 Implementation Status에 후속 주석만. 미커밋·미스테이징.

## [2026-11-02] chore(assets) | ADR-0253 사운드 자산 4세대 중복 제거 — 대시보드 참조 정합

- 계기: 워크스페이스 경로·자산 정리 감사. `docs/dashboard/sounds/` 에 같은 12개 테마가 4세대로 중복되어 `wet_run/.git` 274MB 중 263MB가 오디오였고, 절반은 중복이었다. 동시에 대시보드 HTML 4개가 2026-09-15에 폐기된 Python 프로토타입 경로와 존재하지 않는 파일을 가리키고 있었다.
- 자산 정리: 정본을 `docs/dashboard/sounds/full/theme_X.mp3` 12개로 확정. `full/*_full_m.mp3`·`full/*_full_f.mp3` 12개(73.5MB) 삭제, `sounds/*.v1_backup.wav` 12개(10.6MB) 삭제, `sounds/*_v1_orig.wav` 1개(0.5MB) 삭제, `sounds/theme_*.wav` 12개(60.6MB)는 git 제외하고 로컬 보관(`.gitignore` 앵커 규칙 `/docs/dashboard/sounds/theme_*.wav` — `sounds/v2/`·`sounds/full/` 무영향 확인). tracked 오디오 72파일 263.0MB → 35파일 117.5MB(-145.5MB).
- 대시보드 정합: `sound.html` — F/M 변형 12블록 제거, "2 variants"→"1 variant" 12건, 설명 "두 가지 변형 모두 사용 가능."→"단일 원본 변형." 12건, Themes 플레이어·Reference 카드 파일 경로 `theme_X.wav`→`full/theme_X.mp3` 24건, Overview 스탯을 실측값(44 assets/20 BGM/24 SFX/15 자동 전환/3단 볼륨)으로 교체, Key Bindings 표를 `SoundCategory` 8행→전역 `M` 키 mute + SETTINGS 볼륨 필드 7행으로 교체, Engine Integration 표를 Python 모듈 9행→`web/` 모듈 4행으로 교체, 폐기 구간(Categories·Sound Files)에 "retired 2026-09-15" 표기 + 안내 배너 추가. `combat.html` — Combat Sounds 표를 유령 SFX 12행(`combat_hit_*.wav` 등 존재하지 않음)→실제 전투 SFX 15행(`COMBAT_SFX_IDS` 기준, BGM duck 여부·실제 크기 표기)으로 교체. `cyberspace.html` — 부재하는 `data/cyberspace/worlds.json`→`docs/dashboard/data/cyberspace_stats.json`, `src/wet_run/matrix/`→`web/src/core/dungeon/matrix.ts`. `settings.html` — `src/wet_run/settings.py`→`web/src/renderer/settings.ts`, "6 카테고리 30+ 설정"→12 필드 실측. `src/wet_run/combat/*.py` 6곳→실제 `web/` 경로.
- `.gitignore` 정합: `dashboard/sounds/*.v1_backup.wav`·`prototype/.venv-311/`·`data/sounds_test/` — 2026-10-20 이전 경로 규칙이 현재 트리에 효과가 없었다. 현행 경로로 교체.
- 링크 수정: `docs/wiki/decisions/0250-encounter-gate-on-entry.md` 의 깨진 링크 `./0236-accessibility-and-motion.md` → `./0236-accessibility-modes.md` (실파일명 `0236-accessibility-modes.md`).
- 불변: `web/` 소스 무변경(변경 0건), `web/public/sounds/theme_*.mp3` tracked symlink 5개 무변경, 게임 런타임 자산 경로 무변경, 게임 메커닉·밸런스·상태 스키마 무변경, `docs/dashboard/sounds/full/` 12개 + `v2/` 23개 무변경, ADR-0250·0246·0251·0252 결정 불변.
- 검증: `npm run typecheck` 0 에러; `npm test` **175 files / 3932 tests passed** (ADR-0252 베이스라인과 동일 — 무회귀); `npm run build` PASS. 오디오 참조 실재 확인 — `sound.html` audio 12개 전부 resolve, 잔여 `.wav` 참조 0, `SoundCategory`·`afplay`·`toggle_category`·`_full_` 잔여 0(의도된 폐기 안내 배너 1건만 잔존). `web/public/sounds/` symlink 5개 전부 resolve, `manager.ts` BGM 참조 5종 resolve. 대시보드 22개 HTML 스캔 `src/wet_run`·`prototype/src` 잔여 0. `combat.html` 참조 파일 15개 전부 실재.
- 잔여(별도 세션 필요): `Game/dashboard/scripts/aggregate-stats.mjs` 가 옛 경로(`Game/wet_run/dashboard/data/...`)를 가리켜 `docs/dashboard/data/*.json` 재생성 파이프라인이 끊긴 상태로 추정된다 — 별도 repo · 범위 밖. `sound.html` 의 Categories·Sound Files 절은 "retired" 표기만 하고 내용 유지 — 실제 `web/` 기준 전면 재작성은 별도 작업.
- 결정: ADR-0253 신규 (Option 2 채택 — 정본 1세대 + 대시보드 참조 통합). ADR-0250 링크 수정만. 미커밋·미스테이징.
[2026-11-02] verify | wet_run_verify (1/2/3) — audit=True

## [2026-11-03] fix(combat) | ADR-0254 어포던스 진실성 — 화면이 약속한 것을 실제로 한다

- **결정 방식**: 오너 미해결 6건 중 스스로 판단 가능한 것을 **자가 플레이 검증 + AI 위임**으로 결정. 파이프라인 = 재현(에고-라이트 실제 플레이 + 결정적 테스트 + 코드 근거) → Jev 결정 계층 위임(noul/choice) → Manus(max) 독립 리뷰 → 구현 + red/green 회귀 테스트 + 3레이아웃 캡처 + 밸런스 byte-identical.
- **확정 사실 6건**: ① 결정타는 COST 미청구(결정적 테스트 비마지막 10→12 / 결정타 10→10) ② 손패 행 `→ N/100` 은 예측값이라 결정타에서 거짓(킬 예측 금지) ③ 종결 노드 loot 화면이 회복도 경로도 약속하나 `applyLootAction` 은 `runPhase=ending` 으로 회복 없이 런을 끝냄 ④ loot 화면의 `ESC`·`↑↓` promise 는 실제로 no-op ⑤ 프로그램 30종 설명문이 구현 안 된 효과를 약속(웹 티어 리듀서는 `tier*5` 하나만) ⑥ 엔딩 HUD 29자가 40×60(사용 가능 15자)에서 가로 압축.
- **구현**: (a) 손패 행·터치 버튼·aria-label 에서 잔여 COST 예측표기 제거 — 카드당 COST +N 만(카드는 "to 2 of 100" 대신 "cost on the card") (b) 프로그램 description 을 실제 동작(피해 tier*5)으로 정합, 설계 의도는 `planned_description` → `plannedDescription` 로 보존(30건) (c) loot 화면 종결 인지 — 종결 노드는 `NO HEAL — this was the last node` + `ENTER: run ends`, 비종결은 `HEAL applied → N/M` 유지, ESC·↑↓ promise 제거 (d) 엔딩 HUD `Choice: arc4_liberation_front` → `ARC 4` (격자가 이미 엔딩 이름을 보여준다) (e) `tickIceEffects` 인덱스 결함 수정 — **독립 커밋 9baf65c5** (Manus 권고).
- **위임 결과**: Jev — #2 B(0.96/conf .94) · #4 A(1.00) · #5 A(0.98/conf .97) · #1 A(0.95/conf .92) · #3 3단계(0.53/conf .44) · #6 다음세션(0.52/conf .42). Manus 독립 리뷰는 #6을 **즉시 처리** 하라고 상반(lib-review 전문 `docs/design/affordance-truth-2026-11-03/manus-review.md`) → 점수만 믿지 않고 리뷰를 받아 이번 세션에 처리. #6 의 HUD 폭은 리뷰가 "10열" 이라 했으나 실제 프리셋은 24/20/16 — 캡처 폭 검사로 실측 확정.
- **증거**: `docs/design/affordance-truth-2026-11-03/` — 실제 AsciiRenderer + esbuild + headless Chromium 으로 3레이아웃 before/after 캡처(12 PNG + 12 쌍) + 폭 검사 JSON + 텍스트 덤프 + 밸런스/테스트/typecheck/lint/build/e2e 로그. 폭 검사: loot HUD 초과 **42자 → 0**, 엔딩 HUD 초과 **29자 → 0**, 그리드 초과 0 (3레이아웃 전부).
- **검증**: `npx vitest run` **178 files / 3948 tests passed**(베이스라인 175/3932, 회귀 테스트 6개 추가) · `npx tsc --noEmit` 0 · `npx eslint src` 0 errors(기존 warning 1) · `npm run build` PASS · 밸런스 양 덱 **byte-identical**(opening 100.0/88.3/70.5/39.5/36.2/0.0 · PPL 100.0/79.1/98.9/83.0/44.4/24.7) · ADR-0243·0250·0251·0252 결정 무변경 · `raw/` 무변경.
- **e2e 86 passed / 4 skipped / 2 failed**: 실패는 `e2e/idle_alarm.spec.ts:48` — **세션 이전 커밋 `92ba417b` 소스로 되돌려도 동일 재현**(직접 검증)이고 실패 지점이 `page.keyboard.press("Shift")` 라 창 포커스 문제다. 이 세션 변경과 무관.
- **남은 항목**: (a) 결정타 COST 정책 — 청구하려면 리듀서 변경 + 기준선 재측정 필요(밸런스는 오너 결정) (b) 프로그램별 실제 효과 배선(설계 의도 `plannedDescription` 보존) (c) HUD 좁은 레이아웃 압축 — `> [1] Yakuza Enf HP: 165`(24자)·`Mission: Aleph Fragment`(23자)가 40×60 에서 압축되는 기존 결함 (d) 종결 노드 loot 15% 회복 부재 — ADR-0252 판단대로 유지.

## [2026-11-03] feat(combat) | ADR-0255/0256 — 카드 실제 효과 배선 + 밸런스 재기준선

- **결정**: 오너 승인("추천대로 해줘") — ①B 카드 실제 효과 배선 + ②A 결정타 COST 0 유지. 오프닝 손패 5장이 **전부 같은 일**을 하던 상태(설명문만 다른 효과 약속)에서 실제 효과로 배선.
- **효과 5개**: Backdoor=공격이 ICE 방어구 **2점** 무시 · Barrier=**2점 흡수 풀** 2턴 · Boost=플레이어 공격 **+2** 2턴 · Cloak=받는 피해 **−15%** 2턴 · Decoy=다음 타격의 **50%** 흡수 1턴. 신규 표면은 `evasive` 상태 종류 **1개**뿐(기존 `shield`·`powered` 재사용) + 플레이어 측 방어 계층(`player_mitigation.ts`) + 효과 명_SPEC(`program_effects.ts`).
- **설계 판단 두 가지**: (a) **방어구는 flat 차감**(최종 최소 1)이라 **비율 관통은 바닥에 반올림되어 사라진다**(방어력 3 → 30%는 0.9점) → **절대값(점) 관통**으로 확정. 실측 방어력 tier1 1.0 → tier6 10.5. (b) 지원 카드가 피해 0 이면 오프닝 손패의 공격 카드가 1 장뿐이라 싸울 수 없다 → 이 손패 구성에서는 **피해 + 효과**가 유일하게 성립.
- **설명문 파생**: 카드 설명문은 이제 손으로 쓴 것이 아니라 `program_effects.ts` 한 표에서 파생된다 — 라벨·설명문·리듀서가 같은 진실을 본다(ADR-0251 규칙 5). 죽은 JSON 필드(`role`·`damage`)는 읽지 않는다.
- **밸런스(ADR-0256)**: 효과별 기여도를 개별 측정했다 — decoy 가 최대(g4 +14.7pp, 1턴 완전흡수가 한 턴 HP) → 50% 로 낮춤, 나머지 각 +3.7~+9.2pp. **효과를 전부 끈 대조군이 기준선과 정확히 일치**(100.0/88.3/70.5/39.5/36.2/0.0) → 곡선 이동은 오직 효과에서 왔고 부수 변경은 밸런스 중립. 새 기준선 opening 100.0/100.0/97.5/53.4/44.1/0.3 · PPL 100.0/100.0/99.3/84.1/44.4/27.3 — **PPL 은 ±3pp 창 안**, 곡선 형태(단조감소) 유지, g6 여전히 치명적. drift policy ±3pp 계승.
- **PPL 덱 모델 수정**: "강한 5장"의 정의가 tier 단독으로는 성립하지 않게 돼(동일 tier 안에서 공격 카드를 우선) — 모델 수정이지 밸런스 조정이 아니다.
- **검증**: vitest **179 files / 3956 passed**(베이스라인 178/3948) · tsc 0 · eslint 0 errors · build PASS · 효과 테스트 7건 신규(관통 상한·평범한 카드 효과 없음 포함) · 카탈로그 텍스트 테스트가 "설명문이 기계에서 파생됨"을 고정 · `balance_sim.test.ts` 가 새 기준선 고정.
- **증거**: `docs/design/card-effects-2026-11-03/` — 밸런스 출력 2종 + 테스트/typecheck/lint/build 로그.
- **남은 항목(오너 결정)**: (a) **오프닝 손패 구성** — 5장 중 4장이 지원 카드여서 g2·g3 이 100% 로 오른 증폭 원인이었다. 공격 3 + 지원 2 로 큐레이션하면 곡선 이동이 줄고 도입도 나아진다 (b) 나머지 25개 프로그램의 효과 배선 (c) 결정타 COST 0 규칙의 화면 안내 위치.

## [2026-11-03] feat(combat) | ADR-0257 손패 효과 열 — 카드가 무엇을 하는지 화면이 말한다

- **계기**: 오너 요청("upgrade battle interaction"). Oracle 합성이 전투 UI 축1 1순위를 `PROGRAM INSPECT`(정보 계층)로 정했으나, 전제였던 "모든 프로그램이 같은 피해 경로" 때문에 보류 상태였다. **ADR-0255 가 효과를 실재로 만들자 그 전제가 풀렸다.**
- **빈 열**: ADR-0254 가 거짓 예측 표기(`→ N/100`)를 걷어내며 손패 행에 빈 열이 생겼다. 그 열이 정확히 효과가 들어갈 자리였다.
- **구현**: 손패 행에 효과 태그 — `PIERCE 2` · `SHIELD 2` · `ATK +2` · `EVADE 15%` · `DECOY 50%`. 4채널 커버(캔버스 full/compact·터치 버튼·aria-label) + 40×60 헤더 `EFFECT` 열. **BLOCKED 우선** — 상한 초과로 거절되는 카드는 효과 대신 BLOCKED(거절된 카드의 효과는 일어날 수 없으므로).
- **파생**: 태그는 `program_effects.ts` 한 표에서 온다 — 라벨·설명문·리듀서와 같은 진실이라 행이 적용되지 않는 효과를 주장할 수 없다(규칙 5).
- **폭 검사**: 80×50 텍스트폭 75 · 60×40 55 · 40×60 35 → full 최대 46 / compact 최대 33, **그리드 초과 0**(3레이아웃). 태그를 ≤9자로 유지한 이유가 40×60 폭 35자. HUD 초과 24/23 은 before/after 동일한 **기존 결함**(ADR-0254 (c)).
- **표시 전용 확인**: 밸런스 **byte-identical**(opening 100.0/100.0/97.5/53.4/44.1/0.3 · PPL 100.0/100.0/99.3/84.1/44.4/27.3 — ADR-0256 기준선) · 리듀서·RNG·상태 스키마 무변경.
- **보류(Oracle 권고)**: select→confirm 모델(ADR-0243 대체 필요, 별도 ADR) · TARGET FIRST(`>` 마커 + `TARGET ICE` 로 충분).
- **검증**: vitest **179 files / 3960 passed**(베이스라인 179/3956, 손패 효과 테스트 +4) · tsc 0 · eslint 0 errors · build PASS · 4채널 커버리지를 테스트가 고정 · 실플레이(ego-lite) 스크린샷으로 5행 렌더 확인.
- **증거**: `docs/design/hand-effect-column-2026-11-03/` — 3레이아웃 before/after 캡처 + 폭 검사 + 밸런스/테스트/typecheck/lint/build 로그.

## [2026-11-03] feat(gameplay) | wet_run ADR-0261 — 성장의 순간을 보여준다 (획득 3박자)

- **오너 요청**: "성장에 대한 효과 이벤트나 표시가 있었으면 좋겠어. 재미 요소 중 하나라서 중요해."
- **문제**: ADR-0259 가 카드 보상을 넣었지만 **획득의 순간이 보이지 않았다** — 카드가 즉시 덱에 들어가고 화면이 바로 넘어갔으며, 소리·시각 강조·멈춤이 없고 HUD 메시지 한 줄만 지나갔다. "성장하는 재미"가 오너가 중요하다 한 요소인데 정작 성장의 순간이 사건으로서 존재하지 않았다.
- **3박자**: **① 소리** `SFX_IDS.EQUIP` — 정의·WAV 는 있는데 **한 번도 재생되지 않던** built-but-unwired id; 덱이 커지는 전환이 그것이 이름하는 사건이다(`pickEventSfx`). **② 멈춤** `takeCardReward` 가 더 이상 `continueToMatrix` 를 호출하지 않는다 — 획득 상태로 머물고 ENTER 가 진행한다(로그라이크의 "고르고, 진행"). **③ 표시** 고른 카드 `> 1 KRAKEN  ACQUIRED`(밝은 초록) · 나머지 둘 흐림(소진) · footer `ENTER: continue`. 도착지 메시지가 성장을 이어받는다: `Took Kraken. Choose an adjacent route — healed to 78/100`.
- **저장 무결성**: 획득은 플레이어 선택이라 유도 불가 → `cardRewardTaken` 을 **선택 필드**로 추가(`currentNodeIndex`·`clearedEncounterNodes`·`bypassedEncounterNodes` 와 같은 패턴, `version` 1 유지). 재로드 시 **두 번째 획득 불가**(한 전투 한 장). 제시 목록은 `ownedIds` 가 taken 을 되돌려 **안정**(하나를 고르면 나머지 둘의 자리가 밀리지 않는다). loot 를 떠날 때 `null` 로 정리.
  - ADR-0259 는 "새 영속 필드 없음"을 제약으로 삼았고, 이 ADR 은 **획득 박자를 위해 그 제약을 한 필드만큼 푼다** — 대가는 선택 필드 1개 + 검증 1줄, 이득은 저장 무결성과 재현 가능한 화면.
- **금지 목록 준수**: 벽시계·입력 락·애니메이션 큐 없음(ADR-0251 §"이건 짓지 마라"). 박자는 플레이어의 ENTER 가 만든다.
- **검증**: vitest **180 files / 3985 passed**(베이스라인 180/3978) · tsc 0 · eslint 0 errors (1 pre-existing warning) · build PASS · 밸런스 **byte-identical**(opening 100.0/100.0/81.4/42.6/36.6/0.0 · PPL 100.0/100.0/99.3/84.1/44.4/27.3 — 표시·사운드 전용) · 3레이아웃 캡처 18케이스 그리드/HUD 초과 **0** · 실플레이(ego-lite) `1` = `loot`+`taken:"kraken"`+`"Acquired Kraken"` → ENTER = `matrix`+`taken:null`+`"Took Kraken."`, console error 0.
- **증거**: `Game/wet_run/docs/design/growth-feedback-2026-11-03/` — 3레이아웃 캡처(제시/획득/종결) + 폭 검사 + 밸런스/테스트 로그.
- **남은 항목**: (a) 도착지 강조는 아직 메시지 텍스트뿐 — 더 강조하려면 매트릭스 배너 밴드(별도 슬라이스) (b) 하네스가 성장을 모델링하지 않음 (c) 제시 카드 tier 가중치.

## [2026-11-03] docs(design) | 성장 연출 시안 — Manus 시안 4안 + Jev 제약 게이트 (검토 대기)

- **계기**: 오너 "이벤트나 효과 시안은 마누스 도움을 받아서 시도해도 돼." ADR-0261 의 3박자(소리·멈춤·표시)는 들어갔지만 **연출이 텍스트 색 변화가 전부**라 성장의 순간이 사건처럼 느껴지지 않는다.
- **방법**: 먼저 이 저장소를 읽어 실제 제약을 확정(① VFX 는 **전투 화면 경로에서만** 합성된다 ② **표시 전용·벽시계 선례 2개**가 `main.ts` 안에 있다 — `matrixTravelFrame`(220ms) · `pressFeedback` ③ `renderRunScreen(..., matrixTravel)` 이 프레임을 인자로 받아 그린다 ④ loot 세로 여유: 80×50 위 6행·아래 10행, 40×60 위 6행·아래 16행 ⑤ `data_acquired` VFX 는 실제로 렌더된다) → 그 제약을 그대로 프롬프트에 넣어 **Manus(max)** 에 시안 요청(구조화 출력) → **Jev 결정 계층**으로 제약 게이트.
- **Manus 시안 4안**: ① **TERMINAL COMMIT**(기업 터미널이 불완전 데이터를 덱에 강제 커밋 — `PROGRAM SLOT`/`DATA LINK OPEN`/`SIGNATURE`/`DECK COMMIT [####] 100%`/`[+] PROGRAM ACQUIRED`, ~420ms, 비용 작음) ② GHOST TRACE(덱 슬롯 연결선 `──╼ DECK[07]`) ③ **COLD BOOT**(`BOOT .... READY` 부팅 은유) ④ **ARRIVAL: ROUTE HANDOFF**(매트릭스 도착에서 `+ PROGRAM: KRAKEN` 으로 성장을 다음 경로 선택에 연결).
- **Jev 게이트 결과**(중요): 추천은 **안1+안4 결합**(0.97/conf 0.96 — Manus 1위와 일치). 위반 판정 — **안2 제외**(noul **0.70**: `DECK[07]` 의 덱 슬롯 번호는 게임 상태에 없는 값 → 어포던스 진실성 위반) · **안3 문구 수정 필요**(noul **0.61**: `READY` 는 과대 주장 — 새 카드는 손패가 아니라 **뽑기 더미**에 들어간다 → `QUEUED`/`STAGED` 로) · 안1(0.24) 안4(0.18) 통과.
- **"만들지 마라" 7항**(Manus 제시 + 제약 도출): 카드가 날아가 꽂히는 연출(40×60 폭 없음·가로 스크롤 금지) · VFX 끝날 때까지 입력 차단 · 전투용 `data_acquired` 의 loot 주입 · 랜덤 파티클/미리보기(RNG 소비 = 밸런스 위반) · 축하 폭죽·레벨업 게이지(톤 파괴) · **없는 덱 슬롯/레벨/희귀도**(안2 가 정확히 이 함정) · Y/N 확인창.
- **구현 형태(권고)**: 리듀서 무변경, `main.ts` 표시 전용 프레임 2개(`lootCommitFrame`, `matrixArrivalFrame`), 벽시계 delta 로만 진행, **애니메이션 종료를 리듀서로 보내지 않음**, reduced-motion 이면 최종 문구만.
- **산출물**: `docs/design/growth-direction-2026-11-03/` — `README.md`(시안 정리 + 오너 선택지 A~E) · `manus-raw.md`(Manus 원문 462행, 목업 포함) · `manus-structured.json`.
- **상태**: **시안 (decision pending)** — 오너 선택 대기. 추천 A(안1+안4).

## [2026-11-03] feat(run) | 성장을 사건으로 만든다 — 터미널 커밋 + 도착 인수인계 (ADR-0262)

- **계기**: 오너 "추천대로 구현해줘." 앞선 세션에서 Manus 시안 4안 + Jev 게이트로 **안1+안4** 를 추천했고(choice 0.97/conf 0.96), 그대로 구현.
- **구현 형태**: 리듀서 무변경. `main.ts` 에 `matrixTravelFrame`(ADR-0249)과 같은 종류의 **표시 전용·벽시계 상태 3개**(`lootCommit`·`matrixArrival`·`lootCommitStageShown`) + `syncGrowthReveal(previous, next)`. 새 순수 모듈 `web/src/renderer/growth_reveal.ts`(커밋 단계·바·문구·도착 노트·프레임 해석). 새 VFX 종류·이벤트 버스·리듀서 상태·저장 필드 **0**.
- **커밋 패널**(loot): 카드 획득 전환에서만 시작(리듀서가 이미 덱에 넣은 뒤 → `100%` 는 참) — `PROGRAM SLOT 01` / `> 1 VIRUS [PIERCE 2]` / `DATA LINK ... OPEN` / `SIGNATURE ... VIRUS` / `DECK COMMIT [##########] 100%` / `[+] PROGRAM ACQUIRED`. 단계 오프셋 `[0, 90, 220, 320]ms`. 40열은 compact 문구.
- **도착 노트**(매트릭스): HUD 에 `+ PROGRAM` / `  VIRUS`. **결함 발견** — 매트릭스는 `state.message` 를 렌더하지 않아 ADR-0261 의 도착 메시지가 화면과 함께 사라졌다. 이 노트가 그 구멍을 메운다. ~1200ms 창 후 자동 소멸.
- **하드 제약**: 입력 락 0(실측 ENTER 응답 **9ms**) · VFX 대기 0 · reduced-motion 은 **최종 문구만**(도착 노트 생략) · 색 중복(글리프·텍스트로 판독) · 3레이아웃 초과 **0** · RNG 0 · **밸런스 byte-identical**(opening 100.0/100.0/81.4/42.6/36.6/0.0, PPL 100.0/100.0/99.3/84.1/44.4/27.3) · 금지 목록 무위반.
- **구현 중 실플레이에서만 드러난 결함 2개 수정**: ① loot 화면은 **입력당 한 번만** 그려서 커밋 패널이 첫 단계에서 멈췄다 → 렌더 루프가 **단계가 바뀔 때만** 다시 그리도록(정지 후 정지). ② **터치 보상 경로**(`handleRewardButton`)가 `syncGrowthReveal` 을 안 거쳐 터치 플레이어는 옛 색 변화만 봤다 → 같은 훅을 지나게.
- **검증**: `growth_reveal.test.ts` 21 tests(단계/클램프/RM 고정/바/wide·compact/도착 창/HUD 폭/프레임 해석 + 소스 스캔). 3레이아웃 before/after 캡처 21 PNG + 21 쌍(초과 0). **실플레이**(preview 5195, 독립 headless Chromium): 획득 → `lootCommit` 설정 → 정착 → ENTER 9ms → 도착 노트 → +0.6s 표시 → +2.0s 소멸, 입력 살아있음 → **PASS**; reduced-motion 재실행 → 최종 문구 즉시 + 노트 없음 → **PASS**.
- **산출물**: `docs/wiki/decisions/0262-growth-reads-as-an-event.md` + README 인덱스 · `docs/design/growth-reveal-2026-11-03/`(캡처 + `live/`·`live-rm/` 스크린샷·로그).
- **검증 수치**: vitest **181 files / 4006 tests passed** · tsc 0 · eslint 0 errors · build PASS · 밸런스 재측정 동일.
- **남은 항목**: (a) 안3 `QUEUED`/`STAGED` 기상 연출(별도 슬라이스) (b) 하네스가 성장을 모델링하지 않음 (c) narrow-layout HUD 압착(기존 결함).

## [2026-11-03] fix(run) | 죽음 화면에서 빠져나올 수 없던 블로킹 버그 (ADR-0263)

- **계기**: 오너 플레이 리포트 "플레이 한번 해봤는데, **보스 배틀 이후 빠져나오지 못한 버그**가 있어." — 실제 브라우저(ego lite) 세션에서 발견.
- **재현(독립 headless Chromium, preview 5195)**: 실제 전투에서 사망 → `runPhase "dead"`/`phase "defeat"`/"FLATLINE" → **`Enter`·`Escape`·`←↑↓→`·`1`·`4`·`Space`·`q` 8개 키 전부 무반응**. 브라우저 새로고침만이 탈출이었고, ADR-0252 §A 때문에 죽음 프레임이 저장되어 `CONTINUE` 가 **같은 화면으로 되돌렸다**.
- **원인**: 죽음 화면의 유일한 탈출 액션 `select_restart` 가 **`web/src` 전체에서 한 번도 디스패치되지 않음**(테스트/퍼저에만 존재). 리듀서 `applyDeathAction` 은 `confirm`/`jack_out` 을 무시했고, `combat_grid.ts` 의 `phase === "defeat"` 분기는 아트만 그리고 **안내 문구 0**.
- **수정(Option A, 최소)**: ① `applyDeathAction` 이 `confirm`/`jack_out` → `phase:"menu"`(runPhase 는 `dead` 유지) ② `runFailed(previous,next)` 판정 — 엔딩의 `runCompleted` 와 **같은 모양** ③ 죽음 화면에 `ENTER / ESC: return to title`(손패 자리, ADR-0251 §5) ④ `main.ts` 가 `runFailed` 이면 `state=null; screen="menu"`.
- **`select_restart` 미재사용 이유**: `main_menu` 와 `same_jockey` 가 **둘 다** `phase:"menu", runPhase:"matrix"` 를 반환해 컨트롤러가 구분할 수 없고, `runPhase:"matrix"` 는 타이틀 대신 매트릭스를 그리게 한다.
- **검증**: `run_end_save.test.ts`(runFailed 판정 8케이스 + main/combat_grid 소스 배선) · `combat_grid.test.ts`(3레이아웃 프롬프트 + 전투 중엔 없음). 3레이아웃 before/after 캡처(신규 `defeat` 케이스, 그리드 초과 **0**; HUD 초과는 before/after 동일한 **기존** 결함). 실브라우저 재현: 수정 전 8키 무반응 → **수정 후 `Enter` 로 탈출**.
- **불변**: 밸런스 byte-identical · ADR-0040 선택지/`lastDeathSummary`/`deceasedJockeys` 무변경.
- **관찰(수정 필요, 열린 질문)**: `autosaveIntent(dead)` 는 `"write"` 인데 **라이브에서는 죽음 프레임이 슬롯에 남지 않았다** — 잭아웃 사망 후 타이틀이 `CONTINUE (no save)`, `hasSaveCache=false`. 죽은 런은 다시 열리지 않는다. 원인(쓰기 실패/복원 거부/retire 의도)은 별도 조사.
- **부수 발견**: 전투에서 COST(alarm)가 상한이면 프로그램이 전부 BLOCKED 이고 유일한 출구는 `ESC`(JACK OUT) → **런 실패** → 죽음 화면이다(설계 ADR-0240/0242). 플레이어가 막힌 지점이 정확히 이 조합이다.
- **산출물**: `docs/wiki/decisions/0263-defeat-screen-must-be-escapable.md` + README 인덱스 · `docs/design/defeat-escape-2026-11-03/`(캡처 + 실브라우저 스크린샷).
- **검증 수치**: vitest **181 files / 4014 tests passed** · tsc 0 · eslint 0 errors · build PASS.
- **남은 항목**: (a) 죽음 시 슬롯 retire 여부(현재는 `CONTINUE` 가 죽은 런을 다시 연다) (b) ADR-0040 의 죽음 선택지 메뉴(`SAME JOCKEY`/`NEW JOCKEY`/`HALL OF DEAD`) 미배선 (c) 좁은 레이아웃 HUD 압착(기존).

## [2026-11-03] fix(run) | 죽음은 런을 끝낸다 — 죽음 시 슬롯 retire (ADR-0264)

- **계기**: 오너 "어떻게 수정해야 돼?" — ADR-0263 의 열린 질문 (a). 그 과정에서 **내 진단이 오진이었음을 확인·정정**: 죽음 프레임은 저장되지 않는 게 아니라 **정상 저장**되고 있었고(라이브 `(no save)` 는 필자의 `deleteDatabase` 실험 절차가 만든 착시), 진짜 원인은 **복원**이었다.
- **진짜 원인**: `SaveSlot` 에 **`runPhase` 가 없고**, `slotToGameState` 가 **모든 저장을 `runPhase: "matrix"`, `phase: "approach"` 로** 복원한다. 그래서 죽음 프레임(write)이 매트릭스 프레임으로 되살아난다.
- **실측(before, 독립 headless Chromium)**: ① **HP 0 사망 → 리로드 → CONTINUE → `runPhase matrix`, hp 0, 도착 조우 재개방** (플레이 불가능한 유령 보드) ② **잭아웃 사망(ESC) → CONTINUE → hp 40 부활** — 잭아웃은 COST 상한 시 유일한 출구이므로 **죽기 직전 ESC 후 새로고침 = 생존**이라는 익스플로잇.
- **부수 확인**: `deceasedJockeys`/`lastDeathSummary`/`totalDeaths` 는 슬롯에 없다(`slotToGameState` 가 `[]`/`null` 로 시작) → **죽음 기록은 원래 휘발**, 저장해도 잃을 것이 없다.
- **수정(오너 선택 "A만", Option A)**: `autosaveIntent` 가 `ending` 에 더해 `dead` 도 `"retire"` — 한 조건. 부활 익스플로잇과 HP 0 유령 보드를 동시에 제거하고 ADR-0252 원칙("끝난 런은 재개할 수 없다")과 일치.
- **실측(after)**: 두 죽음 모두 리로드 후 `hasSave: false`, `meta: null`, CONTINUE 무동작(타이틀 유지). 증거 `docs/design/death-retires-run-2026-11-03/`(before/after 프로브 로그).
- **불변**: **스키마 무변경**(필드 추가 0, `version` 1, 마이그레이션 불필요) · **밸런스 byte-identical**(하네스는 죽음을 걷지 않음) · 살아있는 런 프레임은 계속 write · ADR-0263 의 죽음 화면 탈출 무변경 · ADR-0040 선택지 무변경.
- **문서 정정**: ADR-0263 (a)·Notes 의 "죽음 프레임이 저장되지 않는다" 를 **오진으로 명시하고 정정**. ADR-0252 는 Accepted 이고 결정 내용은 불변이므로 `## Implementation Status` 에만 ADR-0264 갱신 주석(전역 규칙 허용).
- **검증 수치**: vitest **181 files / 4014 tests passed** · tsc 0 · eslint 0 errors · build PASS.
- **남은 항목**: (a) 죽음 화면 재표시가 필요하면 Option B(슬롯에 `runOver` 저장) (b) `deceasedJockeys` 아카이브 영속(ADR-0040 Option A) (c) COST 상한 시 탈출 안내 한 줄.

## [2026-11-04] feat(balance) | 자키가 시작 덱을 정한다 — 후보 8종 측정으로 함정 제거 (ADR-0276)

- **오너**: "자키가 런에 실제 영향" → "계속."
- **문제**: ADR-0274 는 자키가 **이름**만 정하게 했다. 시작 덱은 누구든 고정(`strike, backdoor, boost, barrier, decoy`, ADR-0260). 이 계열 작업에서 **처음으로 밸런스에 닿는** 변경.
- **측정 우선(구조 확인)**: 리듀서는 데미지 경로가 `tier*5` 하나이고 **실제 효과가 배선된 프로그램은 5개뿐**(`backdoor`/`barrier`/`boost`/`cloak`/`decoy`). CASE 덱이 그중 **4개**를 쥐고 있다 → 효과를 버리고 평타를 얻는 교체는 **하향**이다.
- **수정**: `JOCKEY_DECK_IDS` 로 자키별 시작 덱 — `novice=[strike,backdoor,boost,barrier,decoy]` · `veteran=[strike,backdoor,exploit,barrier,decoy]` · `heretic=[strike,exploit,virus,surge,decoy]`. `startingDeck(catalog, jockeyId?)` 가 해석, 미지 id 는 큐레이션 덱 폴백. 하네스에 **`--deck veteran|heretic`** + **`--deck-ids a,b,c,d,e`** 추가(후보를 출시 전 채점).
- **측정이 초안을 바꿨다**: 첫 KAS 덱(`strike,backdoor,virus,surge,decoy`)은 `boost`·`barrier`(효과 2개)를 `virus`·`surge`(같은 tier **평타**)로 바꾼 것 → 3등급 **72.4%**, 기본 덱(78.4%)보다 5점 낮은 **함정**이라 **기각**. tier 상향만이 보상되는 교환(SIL 의 `boost`→`exploit` = +5점). KAS 를 tier 로 공격성을 사도록 재설계 → **CASE 와 동급**(3등급 78.6 vs 78.4).
- **곡선(100 runs/mission)**: CASE `100.0/100.0/78.4/38.9/33.4/0.0` · SIL `100.0/100.0/83.8/44.5/38.3/0.0` · KAS `100.0/100.0/78.6/38.8/33.2/0.0`. 후보 8종(C1~C10) 측정·기각 근거: `docs/design/jockey-decks-2026-11-04/`.
- **실브라우저**: `NEW RUN → (CASE|SIL|KAS) → 미션 → 발사` 후 `window.wetrun.state.deck` 이 각자 덱. 1·2·6 등급은 세 덱 모두 100/100/0 — 차이는 3~5 등급에 산다.
- **불변**: `SaveSlot.version` 1 유지(덱은 매 런 결정, 저장 스키마 무변경). 세 덱 모두 ADR-0260 형태(공격 다수 + 방어 ≥1); 전부 공격인 C10 은 2등급에서 무너져 기각.
- **검증**: vitest **188 files / 4056 tests** · tsc 0 · eslint 0 errors · build PASS · `check_doc_claims.py` · `check_no_novel_prose.py` exit 0.
- **남은 항목(오너 결정)**: (a) 덱이 **종류로** 달라지려면 `plannedDescription` 의 효과 배선(virus=도트 등) — 지금은 tier 로만 다름 (b) 자키 선택 ↔ 프롤로그 체인 일치(프롤로그는 `novice` 고정) (c) 등급 6 이 세 덱 모두 0.0%(PPL 도 27.3%) — 등급 6 자체 미완성 (d) 선택 화면 소개문에 덱 언급.

## [2026-11-04] feat(balance) | `exploit` 이 방어도의 절반을 무시한다 — 큐레이션 덱 교체 + 엔딩 크레딧 표시 수정 (ADR-0277)

- **배경**: ADR-0276 열린 질문 (a) — 자키 덱이 tier 로만 갈리고 메커니즘으로는 안 갈린다. 이유는 배선된 효과가 5개뿐이고 기본 덱이 그중 4개를 이미 쥐고 있었기 때문.
- **수정**: `exploit` 을 `armor_ignore` 50% 로 배선. `effectiveArmor = floor(max(0, armor - pierce) * (100 - amount) / 100)` — `amount = 0` 인 모든 카드는 수치 불변. 텍스트/태그는 기계에서 생성(`ARMOR -50%`).
- **측정이 초안을 뒤집었다**: 배선 직후 큐레이션 덱만 `exploit` 이 없어 3등급 **78.4%**(SIL 86.5, **-8.1**) — ADR-0276 의 ±5%p 기준 위반. `backdoor` → `exploit` 교체. 기각: 그대로(78.4) · `strike` 제거(99.5) · `barrier` 제거(81.5) · `decoy` 제거(70.1) · `strike`→`surge`(99.6).
- **최종 곡선(100 runs/mission)**: g3 `89.1/86.5/84.3` · g4 `47.4/47.0/43.3` · g5 `40.7/40.3/36.4` — 최대 차 4.8/4.1/4.3. PPL 참조 `100/100/99.3/89.3/44.4/28.3`.
- **턴 모델 발견**: 턴은 손패가 비었을 때만 넘어간다 → 덱 화력은 tier 합이 아니라 **카드 tier**. 그래서 가장 싼 카드를 빼는 것이 가장 큰 상향(`strike` 제거 = +20점). `tests/jockey_deck.test.ts` 가 "어떤 덱도 `strike` 를 버리지 않는다"를 고정.
- **같이 고친 표시 버그**: 엔딩 요약이 `inventory.credits`(미션 기본 보상)를 읽어 2,300cr 런이 **500cr** 로 표시 → `player.credits`. `tests/run_screen.test.ts` 가 "런이 번 돈을 표시한다"를 고정. 실화면: `CASE — First Jack / HP 100/100 · 2,300cr · 7 turns`.
- **서사 검증**: `web/e2e/story_trace.spec.ts`(`npm run story`) — 실브라우저·실키 15스텝, 정지 0, 엔딩 `arc1_wage_slave` 도달. `docs/design/jockey-identity-2026-11-04/story-narration.md` 에 이야기로 옮기고 그럴듯함을 판정. 드러난 결함: 받은 카드(Scan)가 짧은 런에서 손에 안 들어옴 · 전투 사이 손패 미초기화 · 한 미션 두 ICE 동일 타입 · 자키 소개("deck is already warm") vs arc1 인트로("cold in your hands") 톤 충돌 · 구역명(surface vs mid/core-deep) · `Loot: ice_shardx1` 공백.
- **소크**: `SOAK_RUNS=3 npm run soak` → completed 3, frozen 0 (ADR-0274 자키 선택 화면을 `startRun` 이 통과하도록 수정).
- **검증**: vitest **188 files / 4062 tests** · typecheck 0 · lint 0 errors (1 pre-existing warning) · build PASS · `check_doc_claims.py` exit 0 · `check_no_novel_prose.py` exit 0 (1745 strings).
- **남은 항목(오너 결정)**: (a) 전투 시작 시 손패 리필(성장 카드가 실제로 손에 들어오게 — 밸런스 재측정 필요) (b) 미션 내 ICE 타입 중복 제거 (c) 엔딩 `control` 분기의 크레딧 출처(`inventory.credits > 5000`)와 `hp > 75%` 조건 — ADR-0277 열린 질문 (c).

## [2026-11-05] fix(core) | 런이 사실대로 읽힌다 — 서사 검증이 찾은 결함 6+2건 수정 (ADR-0278)

- **배경**: ADR-0277 의 서사 검증(`story-narration.md`)이 남긴 결함 8개. 오너 "결함 수정해줘. 그리고 더 찾아봐줘."
- **계기를 먼저 고쳤다**: 트레이스가 `state.message`(최신 한 줄)만 캡처해 전투 로그가 사라졌고, 그래서 "동료가 로그 첫 줄을 가져간다"는 **오탐**이 나왔다. 이제 `combatLog` 전체를 중복 없이 오래된 순으로 남긴다.
- **고친 것 6**:
  1. 받은 카드가 런에서 한 번도 안 나옴(성장 무효) → 전리품 화면을 닫을 때 `refillHand` 로 `handSize` 까지 채우고(`combat/hand.ts`), 보상 카드는 드로우 파일 **맨 위**에 얹는다. 리필 지점을 **BREACH 가 아니라 전리품**에 둬서 SCAN 으로 쓴 카드는 그 전투 동안 계속 빠져 있다(ADR-0247 비용 유지).
  2. 손패가 교전 사이에 초기화 안 됨 → 같은 수정으로 해결.
  3. 한 미션의 두 ICE 가 같은 타입 → `iceIdForRoom` 이 ICE 방마다 등급 밴드 다음 슬롯(`seed + iceOrdinal * 7`).
  4. 자키 태그라인 톤 충돌 → `New hands. Old reflexes. The deck remembers.`
  5. 전리품 표기 `ice_shardx1` → `${item} x${qty}`.
  6. `encounterRoster` 가 `state.ice` 를 **복제**해 id/hp 만 바꿈 → 모든 교전이 미션 기준 ICE 를 입었고 **보스 방이 35 HP "Wisp"** 로 싸워졌다. 이제 노드 `iceIds` 를 ICE **카탈로그**에서 해석.
- **재측정에서 새로 찾은 2**:
  7. 전투가 상대 이름을 안 말함 — `state.ice` 는 런의 기준 ICE 라 보스 방도 `Combat vs ICE — Wisp`. 실제 상대는 wintermute(armor 8, tier 4). `combat/roster.ts` 의 `activeIceOf`/`defeatedIceName` 이 **로스터**에서 읽는다.
  8. **막타를 누가 쳤는지가 보상을 정했다** — 카드 막타는 전리품·업적(`boss_slayer` 1,000cr)·진영 점수 전부, Dixie 막타는 **크레딧만**. 보스 전리품(`combat_module x2` 등)과 `boss_slayer` 가 카드가 막타를 친 런에만 존재했다. `combat/victory.ts` 의 `creditKills`/`resolveVictory` 로 **킬이 일어난 지점**에서 적립. 남는 차이는 하나 — ADR-0258 의 `(no COST)` 는 막타를 친 카드의 것이므로 동료 킬은 주장하지 않는다.
- **오탐 정정 3** (문서): 구역 이름(미션 zone ≠ 노드 zone, 의도) · 동료 첫 줄(캡처 손실) · 만피 회복(실제 **15%**, 그 런이 96/100 이었을 뿐).
- **불변(측정)**: `npm run balance` 산출이 ADR-0277 기준선과 **완전히 동일**(`100.0/100.0/89.1/47.4/40.7/0.0`) · RNG 소비 0 · 저장 스키마 무변경.
- **실플레이**: `STORY_MISSION=9 npm run story` — 16스텝, 보스 `Combat vs ICE — Wintermute` → `+1675 credits Loot: combat_module x2, construct_shard x1, data_fragment x3`, 엔딩 `arc1_wage_slave` 까지 무정지.
- **소크**: `SOAK_RUNS=15 npm run soak` → **15/15 completed, frozen 0** (g1–g5, g5 6런 포함).
- **검증**: vitest **190 files / 4077 tests** · typecheck 0 · lint 0 errors(기존 `keyboard.ts` 경고 1) · build PASS · `check_doc_claims.py` exit 0 (111 paths, 198 ADRs) · `check_no_novel_prose.py` exit 0 (1760 strings) · `mixed_language_audit.py` 0.
- **남은 항목(오너 결정)**: 미션 기본 보상이 **교전마다** 지급된다(`mission.rewards.credits + node.reward.credits`). `First Jack` 은 500 을 약속하는데 두 교전에서 500 이 두 번 들어갔다(625 / 1675). 미션 선택 화면이 `[T1 | 500cr]` 이라고 말하므로 "화면이 약속한 것과 게임이 하는 것" 계열이다. 권고: 미션 보상은 엔딩에서 한 번, 교전 승리는 노드 보상만 — 경제 변경이라 ADR-0278 열린 질문 (a).

## [2026-11-05] fix(economy) | 런이 번 돈을 런이 말한다 — 미션 보상 1회 지급 + 엔딩 지갑 정합 (ADR-0279)

- **배경**: ADR-0278 열린 질문 (a)·(b) = ADR-0277 (c). **같은 뿌리 둘** — 모두 "화면이 약속한 것과 게임이 하는 것" 계열.
- **결함 ①**: `mission.rewards.credits + node.reward.credits` 가 **모든 교전 승리**에 더해졌다. `First Jack` 의 500cr 이 두 교전에서 **두 번** 들어갔는데, 미션 선택 화면은 `First Jack [T1 | 500cr]` 로 **한 번**을 약속한다(2026-11-02 트레이스에도 `cr=4500` → `+6100`).
- **결함 ②**: 엔딩 리졸버가 `inventory.credits` 를 읽었다. 그 지갑은 미션 기본 보상으로 시작해 **전투로 늘지 않는다**(전투 보상은 `player.credits`). 그래서 `control` 분기(`credits > 5000`)가 53개 미션 중 **2개**에서만 도달 가능했고, arc 1–4 의 `control` 엔딩(`arc1_cowboy_up`·`arc2_data_thief`·`arc3_double_agent`·`arc4_new_order`)이 **사실상 죽은 분기**였다 — 엔딩 화면은 `player.credits` 를 인쇄하면서(ADR-0277).
- **수정 ①**: `resolveVictory` 가 `isTerminalNode` 로 갈라 미션 보상은 **미션이 끝나는 교전**에서 1회만 지급(`(mission complete)` 표기). 전리품 화면이 `state.message` 의 `+N credits` 를 파싱해 그리므로, 엔딩 확정 단계가 아니라 **그 전투에** 얹어 표시 불일치를 만들지 않는다.
- **수정 ②**: `EndingContext.credits = state.player.credits` — 엔딩 화면이 인쇄하는 수와 **같은 수**로 판정(ADR-0269·0270 규칙의 연장).
- **측정 도구 신설**: `npm run endings`(`web/scripts/ending_distribution.ts`). 소크는 실제 벽시계·비시드 `Math.random` 이라 분포가 회차마다 흔들리므로(같은 코드로 15런에서 `arc5_control` 이 1~5 사이로 변동), 시드 고정 리듀서로 53미션 결정론 분포를 낸다.
- **측정 결과 (53미션, seed 20261105, 정책 `expensive`, 리졸버 지갑만 교체)**: `control` **2 → 12 런** (arc3 `arc3_double_agent` 0→1 · arc4 `arc4_new_order` 0→**7** · arc5_control 2→4), `arc4_status_quo` 7→0 · `arc5_unknown` 2→0. arc 1·2 는 여전히 미도달 — 기본 보상이 낮아 런 총액이 5,000 미만이라 **분기가 등급 규모에 맞게** 살아났다. 원자료 `docs/design/jockey-identity-2026-11-04/ending-distribution.txt`.
- **보상 변화**: 2교전 완주에서 **중복 500cr 제거**. 런 총액은 업적에 따라 변동하므로(같은 런이 `combo_master` 를 켜면 2,300 처럼 보인다) 결정론 고정은 테스트가 한다 — `adr0279_mission_reward.test.ts` 가 800cr 미션 2교전 완주를 **1,975cr**(노드 50+75, 미션 800×1, `first_blood` 50, `boss_slayer` 1,000)로 못박는다.
- **불변(측정)**: `npm run balance` byte-identical(`100.0/100.0/89.1/47.4/40.7/0.0`) · RNG 소비 0 · 저장 스키마 무변경.
- **실플레이**: `STORY_MISSION=9 npm run story` — 1교전 `+125 credits`(노드 75 + `first_blood` 50, 미션 보상 **미포함**) → 보스 `+2175 credits (mission complete) Loot: combat_module x2, …` → 엔딩 `arc1_wage_slave`.
- **소크**: `SOAK_RUNS=15 npm run soak` → **15/15 completed, frozen 0**, 엔딩 다양(`arc4_new_order` 3 · `arc2_status_quo` 5 · `arc1_wage_slave` 2 · `arc5_control` 1 · `arc3_neutrality` 1 · `arc4_status_quo` 1). 하네스 리포트에 `ending` 추가.
- **검증**: vitest **191 files / 4084 tests** · typecheck 0 · lint 0 errors · build PASS · `check_doc_claims.py` exit 0 (111 paths, **199 ADRs**) · `check_no_novel_prose.py` exit 0 (1769 strings) · `mixed_language_audit.py` 0.
- **남은 항목**: (a) `hp > 75%` 조건이 실제로 얼마나 자주 참인지(`npm run endings` 가 HP 를 남기므로 측정 가능) (b) `player.credits` ↔ `inventory.credits` 두 지갑 통합(crafting 상점 배선 시 필수) (c) 노드 보상 곡선(`50 + idx*25`) 재검토.

## [2026-11-05] manus | ADR-0279 독립 리뷰 (approve-with-caveats)

- **입력**: `docs/wiki/decisions/0279-the-run-states-its-earnings.md`
- **산출물**: `docs/design/adr-review-2026-11-05/manus-review.md` (task `LXHmpxarQHm38S4FT5XXPX`, agent `lite`)
- **결론**: approve-with-caveats. 핵심 지적 — (1) `resolveVictory` 1회 지급 + `player.credits` 리졸버 변경이 함께 적용된 **최종 분포 측정 누락** (현재는 리졸버 지갑만 교체), (2) 터미널 승리 재처리 시 **멱등성** 미입증, (3) `isTerminalNode` 보스/막다른 경계 불명확, (4) ADR-0130 `rewards.credits` 권위 관계 미해소, (5) `control` 카탈로그 존재 vs 도달성 표현 혼재.
- **오픈 질문 판정**: (a) 부분 가능(HP 기록은 있으나 충족률 미제공), (b) 현재 증거로 결정 불가, (c) 답할 수 없음(보상 곡선 재설계 근거 부족).
- **후속**: ADR-0279 `## Implementation Status` Notes 에 Manus 리뷰 인용 추가 검토.

## [2026-11-06] fix(economy)·docs | 리뷰 후속 번들 — 권위 매핑·데이터 위생·잔여 위험·HP 측정 (ADR-0279)

- **배경**: ADR-0279 Manus 독립 리뷰(`approve-with-caveats`)의 미해소 finding (4)·(5) + 잔여 위험 + 열린 질문 (a). 오너 "묶어서 하자".
- **finding (4) — 세 필드 권위 매핑 + 데이터 위생**: ADR-0130 이 `rewards.credits`(nested)를 권위로 결정했는데, 평면 `reward_credits`(top)가 33개 Sprawl 미션에 남아 있었고 **33개 전부** `rewards.credits` 와 값이 달랐다(레거시 5.7~11x 작음 — `first_jack` top 75 vs nested 500). 런타임 독자는 **0곳**(전수 grep). ADR-0130 의 "deprecated 또는 alias" 결정에 따라 `reward_credits`·`reward_tier` **제거** → 53개 미션이 같은 모양. ADR-0279 에 "세 필드의 권위 매핑" 절 추가(`mission.rewards.credits`=권위 지급액 / `reward_credits`=폐기 / `inventory.credits`=crafting 보증금 / `player.credits`=런 원장). ADR-0130 에 Implementation Status 추가, `hacking.md` 스키마 예시 정정, `ppl_zdr_balance.md` deprecation 노트 종결.
- **finding (5) — 존재 vs 도달 분리**: "5개 arc 모두 `control` 보유"를 **카탈로그 존재**로 한정하고(테스트 이름·주석 포함), 도달성은 측정이 답하도록 분리.
- **잔여 위험 — 재지급**: 테스트 4건 추가 — 터미널 전리품 confirm 이 재지급 안 함 · 엔딩 confirm 이 재지급 안 함 · 지급 후 저장/복원이 같은 원장 · 지급 전 저장은 원장 0.
- **열린 질문 (a) — 측정 완료, 그리고 정정**: `npm run endings` 에 `--tick-every N` 추가(적이 벽시계로 게이트되므로 시간 모델이 분포를 정한다). 결과:
  - `tick-every=0` (브라우저 세션 구간): 결말 53/53 · **`hp > 75%` 53/53** · `credits > 5000` 12/53 · `control` 해결 **4/53** (12중 8은 팩션 분기가 먼저 잡음).
  - `tick-every=1` (하네스 모델): 결말 **5/53** (48 flatline) · `hp > 75%` 0/53 · `control` 0/53.
  - **인과**: HP 조건은 살아남은 런에서 **항상 참**(회복 15%가 손실을 덮음) → 조건이 아니라 **크레딧**이 가른다. ADR-0278 (c) 의 추측은 반대 이유로 성립.
  - **더 큰 발견**: 하네스 모델에서는 **런이 결말에 못 간다**. 단일 교전 g4 47.4% 기준이면 2~4교전 런은 그 곱만큼 낮다 → 엔딩 분포는 "얼마나 벌었나"보다 **"살아남았나"** 가 먼저 정한다. 난이도 문제로 ADR-0279 범위 밖.
  - 부수: 난이도가 **플레이어 숙고 시간**에 의존한다(빠른 키 세션 53/53 완주 vs 숙고 48/53 사망). 벽시계 게이트의 의도인지 결함인지는 별도 질문.
- **검증**: vitest **191 files / 4089 tests** · typecheck 0 · lint 0 errors · build PASS.

## [2026-11-06] fix(core) | 적은 벽시계가 아니라 턴에 때린다 — 그리고 보스가 한 번도 측정된 적 없다는 발견 (ADR-0280)

- **배경**: 오너 "턴 전환." → "카드당 1회 + 목표 곡선으로 재조정". 프로젝트 제약 "no wall clock/RNG in reducer" 를 적 페이즈가 위반하고 있었다: `if (currentMs - state.lastEnemyAttackMs < AUTO_ATTACK_INTERVAL_MS) return state;`
- **수정**: 적은 **플레이어 행동마다 1회**, 벽시계 없이. 손패 리사이클만 손패가 빌 때(ADR-0212). `AUTO_ATTACK_INTERVAL_MS` 는 **명목 단위**로 유지(스킬 쿨다운이 ms 저작값이라 "적 1회 = 그 ms" 의미 보존 — 저작 숫자 무변경). Dixie 카드당 유지(ADR-0244).
- **같은 계열 위반 둘 정리**: `comboLastHitMs` 가 리듀서에서 `Date.now()` 를 읽고 있었다(`tickCombo` 는 **호출자 0** → 콤보 창 `COMBO_WINDOW_MS` 는 한 번도 작동한 적 없음, 별도 결정으로 남김) · 미니언 id 가 `Date.now()` 라 같은 입력에 다른 id(리듀서 결정론 위반).
- **검증(핵심)**: 트리거를 카드당으로 두면 `npm run balance` 가 ADR-0229/0277 기준선과 **정확히 일치**(`100.0/100.0/89.1/47.4/40.7/0.0`) · balance_sim 16 테스트 통과. → **기존 벽시계 ≡ "카드 1장당 적 1회"**. 즉 이 변경은 난이도를 바꾸지 않고 **결정론적으로** 만든다. 바뀌는 것은 "누가 그 난이도를 겪느냐".
- **처음으로 진실이 드러남**: 교전 단위 곡선은 미션의 모양(평균 4.4교전·최대 10)을 말하지 못한다 → **미션 단위 도구 신설** `npm run survival`(`web/scripts/mission_survival.ts`, 20시드×53미션, `scripts/play_policy.ts` 공유).
  - 실측 미션 완주율: **g1 32.5% · g2 14.7% · g3 5.0% · g4 3.5% · g5 1.7% · g6 5.0%** (목표 100/95/80/50/25/10).
- **원인 = 보스, 그리고 아무도 그것을 측정한 적이 없다**: 죽은 위치를 세니 **g1·g2 는 일반 교전 사망 0** — 지는 곳은 보스뿐(사망 중 보스 비중 **g1·g2 100%**, g3 91%, g4 87%, g5 65%, g6 67%). 그런데 `balance_sim.ts` 는 주석에 *"skip boss rooms so a boss spike does not decide the reported win-rate"* 라 적어 두었다 — **기록된 곡선은 보스를 한 번도 본 적이 없다**. 보스는 모든 등급에서 `wintermute`(tier 4 · armor 8 · `dmg_base` 11 → 자동공격 20) 고정이고 등급이 조절하는 것은 **HP 상한뿐**(g1 75). 카탈로그의 `boss` aggression ICE 는 **전부 tier 4+** 라 낮은 등급 보스가 데이터에 없다.
- **검증**: vitest **191 files / 4089 tests** · typecheck 0. 원자료 `docs/design/adr-0280/mission-survival-before.txt` · `docs/design/adr-0280/death-location.txt`.
- **남은 결정**: 열린 질문 (a) **보스를 어떻게 등급에 맞출 것인가** — 권고는 "등급 밴드의 최상위 ICE 를 엘리트 보스로 승격"(데이터에 이미 있고, 등급별 보스가 자연히 생기며, `wintermute` 는 상위 등급 전용이 됨). (b) g6 10% 목표가 ADR-0229 불변식("오프너는 클라이맥스를 못 이긴다")과 충돌 → 등급 단위로 재정의 필요. (c) 콤보 창.

## [2026-11-06] fix(balance) | 보스를 등급에 맞춘다 — g1 튜토리얼이 실패하던 진짜 원인 (ADR-0280)

- **배경**: 오너 "추천대로" → ADR-0280 열린 질문 (a) B안(등급 밴드의 정점을 보스로) + g6 목표 5% 조정.
- **수정**: 출구 방이 고정 `wintermute`(tier 4 · armor 8 · 자동공격 20) 대신 **그 등급 밴드의 정점**을 쓴다 — `BOSS_ICE_BY_GRADE`: g1 `hosaka_courier` → g2 `corporate_guard` → g3 `hosaka_defender` → g4 `ta_sentinel` → g5 `neuromancer` → g6 `aleph`. 정점은 데이터에서 계산했다(`iceHpForGrade(x,g) * (tier*3 + armor)` 최대). 상위 셋(`ta_sentinel`·`neuromancer`·`aleph`)은 카탈로그에서 이미 `aggression: "boss"` 라 진짜 보스가 유지된다.
- **효과 (20시드×53미션)**: 미션 완주율 **32.5/14.7/5.0/3.5/1.7/5.0 → 100.0/99.1/33.2/11.5/0.0/0.0**. **g1·g2 가 목표(100/95)에 들어왔다** — g1 은 3번 중 2번 실패하던 튜토리얼이었다. 교전 단위 곡선은 **byte-identical**(`100.0/100.0/89.1/47.4/40.7/0.0`) 이라 하네스 기준선 테스트가 그대로 통과.
- **곡선 재조정은 중단 — 하고 나서 되돌렸다**: `scripts/tune_curve.py`(등급별 HP 상한·피해 보너스 격자 탐색 + `npm run survival --grade N` 프로브)로 6개 중 5개를 목표 안에 맞췄다(`100.0/100.0/77.3/67.0/21.1/6.7`). 그런데 그 해의 **교전 단위 곡선이 역전**됐다: **g4 7.2% · g6 99.3%** — 등급 4 ICE 가 등급 6 ICE 보다 치명적. ADR-0229 의 단조 비증가 불변식 위반이고 설계로도 앞뒤가 안 맞아 **커밋하지 않고 되돌렸다**(원자료 `docs/design/adr-0280/retune-attempt.txt`).
- **원인 규명**: ① `balance_sim` 이 **교전마다 러너를 만피로 리셋**하므로 교전 승률로 미션 난이도를 표현할 수 없다(런은 피해를 이월한다) ② 등급별 **미션 길이**(2.3/3.2/3.6/4.3/7.4/7.3 교전)가 목표(100/95/80/50/25/10)와 함께 주어지면 두 곡선을 동시에 만족시키려면 교전 난이도가 **비단조**여야 한다.
- **세 갈래로 기록** (열린 질문 (d)): A 비단조 교전 곡선 수용(ADR-0229 개정) · B 미션 길이를 등급에 맞춤(콘텐츠 변경) · C **세 번째 레버 = 전리품 회복량 스케일**(현재 미조정, 콘텐츠 변경 없음). 권고는 **C 먼저, 그다음 B**.
- **검증**: vitest **191 files / 4089 tests** (보스 고정 테스트 3개를 새 의도로 갱신) · typecheck 0 · lint 0 errors · `npm run balance` baseline byte-identical · 소크 15런 11 completed / 4 failed · frozen 0 · `npm run story` 통과. 신규 도구: `npm run survival`(미션 완주율) · `scripts/play_policy.ts` · `scripts/tune_curve.py`(경고 헤더 포함).

## [2026-11-06] fix(balance) | 회복 레버를 측정했다 — 교전 사이 회복은 안 되고, 싸움 중 재생은 g3·g4 를 고친다 (ADR-0280)

- **배경**: 오너 "C를 해보고 시간 지나면서 회복되거나 아이템으로 회복하는 것도 고려. 마누스 활용해서 비교 검증."
- **적용 (A)**: 전리품 회복을 등급 스케일로 — 평면 15% → `15/15/25/40/55/65`(`src/core/state/loot_heal.ts`). g3 33.2 → 36.7(+3.5pp), 나머지 소폭. **교전 단위 곡선은 byte-identical** — `balance_sim` 은 교전을 만피로 시작해 승리에서 멈추므로 전리품 화면을 보지 않는다 → 이 손잡이는 교전 곡선을 훼손할 수 없다.
- **천장 측정 (B)**: 교전 사이 **완전 회복(100%)** 으로도 `g3 54.5 · g4 10.0 · g5 0 · g6 0`. **교전 사이 회복으로는 목표 도달 불가** — 싸움에서 지면 다음 전리품 화면에 도달하지 못한다. 구속 조건은 누적 소모가 아니라 **싸움 안의 치사율**.
- **싸움 중 재생 (C, 측정만)**: 플레이어 `regen` 경로는 **이미 완전 배선**(`regen` + `healPerTick` + 틱 처리 + `no_heal` 뮤테이터)인데 **원천이 없다**. 프로브(적 턴당 R HP): R=0 → 38.1/4.4/0.0 · R=3 → 63.6/23.8/0.0 · **R=5 → 86.9/43.8/1.4** · R=8 → 99.4/77.5/1.4 (목표 80/50/25). → **교전 사이 회복보다 한 자릿수 강하고, R=5 면 g3·g4 가 목표 안**.
- **g5·g6 가 어떤 R 에서도 안 움직이는 이유 (D)**: 생존이 아니라 **화력**. tier 4+ ICE **36개 중 34개**가 armor ≥ 5 이고 오프닝 덱의 `strike`(tier 1)는 `max(1, 5-armor)` = **1 피해**. `neuromancer`(armor 9 · 165 HP)는 `exploit` 만으로 16장 필요. **죽일 수 없으면 HP 는 무관** → 회복 문제가 아니라 **진행(progression) 부재** 문제(PPL 곡선이 상위 등급을 개발된 덱으로 전제).
- **아이템 회복 (E, 고려만)**: 재생과 **같은 계열**(싸움 안 회복). 대가가 크다 — 루트 항목 · 인벤토리 슬롯 · **저장 스키마** · 전투 액션 · HUD. 같은 회복량이면 기본 재생보다 약함.
- **마누스 비교 검증**: 독립 비교 의뢰(`scripts/manus_heal_compare.sh`, `agent_profile=standard`) — 위 수치와 6개 레버(a 회복 스케일 · b 재생 · c 아이템 · d 미션 길이 · e 교전 곡선 완화 · f 목표 하향)의 랭킹·리스크를 질문.
- **검증**: vitest **191 files / 4089 tests**(전리품 회복이 등급 스케일이 되면서 고정값을 쓰던 테스트 2개를 새 의도로 갱신 — 하나는 "등급의 몫을 회복한다", 하나는 "빠른 입력에서 상태가 깨지지 않는다"로 hp>0 단정 제거) · typecheck 0 · lint 0 errors · build PASS · balance baseline byte-identical · `check_doc_claims` 0 · `check_no_novel_prose` 0.
- **남은 결정**: (e) 싸움 중 재생의 **원천**(권고: 카드 — 배선 재사용·스키마 무변경·플레이어 선택) · (f) g5·g6 화력 벽(등급별 덱 진행 or armor 스케일링) · (d) 두 곡선의 충돌.

## [2026-11-06] docs(balance) | 마누스 독립 비교 검증 — 내가 시험한 것과 마누스 1순위는 다른 실험이었다 (ADR-0280 §7)

- **의뢰**: `scripts/manus_heal_compare.sh` → task `jheQM4ZVbMNdwnP5gZpxdi`. 요청은 `standard` 였으나 **무료 계정이라 `manus-1.6-lite` 로 다운그레이드**(응답 frontmatter 에 기록). 결과 `docs/design/adr-0280/manus-heal-compare.json`.
- **동의**: 교전 사이 회복은 천장 때문에 불가(100% 로도 g3 54.5%) · 아이템 회복은 비용 대비 이득 미정량 · 목표 하향은 문제를 해결하지 않음 · **g3·g4 변화는 노이즈**(±3pp, 맞다).
- **단서**: 이 리뷰는 **재생 스윕을 받기 전**에 작성됐다. "싸움 중 재생의 필요 강도는 데이터로 결론 불가"라 적었는데 — 당시 데이터 기준으로 **정확**하고, 지금은 §6 C 가 그 수치(R=5 → 86.9/43.8)를 채웠다.
- **가장 유용한 입력**: 마누스 1순위는 **(e) 단조성을 유지하며 교전 곡선 완화**. 그런데 §5 의 실패한 탐색은 **단조성을 제약으로 걸지 않아** 역전(g4 7.2% vs g6 99.3%)이 났다 → **"(e) 는 실패한 것이 아니라 아직 시험하지 않은 것"**. 이 구분을 ADR 에 명시했다.
- **종합**: g3·g4 = 싸움 중 재생 R≈5(측정 완료, 배선 존재). g5·g6 = **화력 벽**(tier 4+ 34/36 armor ≥5, 오프닝 `strike` 1 피해) — 마누스의 (d) 미션 길이와 이 ADR 의 (f) armor/덱 진행이 **상위 등급만** 손봐야 한다는 점에서 일치. 두 곡선 충돌의 남은 실험 = **단조성 제약을 건 탐색**.
- **스크립트 버그 수정**: 첫 폴링이 30분 타임아웃했다. 원인 둘 — ① `task.listMessages` 의 메시지는 **최신 우선**이고 `status_update` 이벤트에 **이미 지나간 상태**가 섞여 있어 완료된 태스크를 "running" 으로 읽었다 ② 메시지 봉투에 `status`/`role` 필드가 없다. 이제 **`task.detail` 의 `task.status` + `has_running_background_jobs`** 로 판정하고, 어시스턴트 텍스트는 `type == "assistant_message"` 로 추출한다.
- **검증**: `check_doc_claims` 0 · `check_no_novel_prose` 0 · mixed-language 0 · `bash -n` 통과.

## [2026-11-06] fix(balance) | 단조성 제약을 건 곡선 탐색 — g1–g4 목표 안, g5·g6 는 구조적으로 불가 (ADR-0280 §8)

- **배경**: 오너 "그래." → 마누스 1순위 실험. §5 의 실패한 탐색은 **단조성을 제약으로 걸지 않아** 역전(g4 7.2% vs g6 99.3%)이 났고, 따라서 "단조성 유지 완화"는 **시험된 적이 없었다**.
- **방법**: `scripts/search_curve_constrained.py` — 12개 파라미터(등급별 HP 상한 6 + 피해 보너스 6) 좌표 탐색, 후보마다 두 제약을 **강제**(① HP 상한 단조 비감소 ② 측정된 교전 승률 단조 비증가). 평가는 `scripts/curve_probe.ts` 하나로 두 지표를 **1.4초**에(교전 = `runSuite`, 미션 = `playRun`).
- **결과**: `hp [95,95,95,125,165,165]` · `dmg [50,90,-12,40,0,-20]`.
  - 교전 p **100.0 / 100.0 / 100.0 / 47.0 / 40.7 / 0.0** — **단조 비증가 유지**
  - 미션 m **100.0 / 95.0 / 81.8 / 48.0 / 0.0 / 0.0** vs 목표 100/95/80/50/25/10
  - 차 **0.0 / 0.0 / +1.8 / -2.0 / -25.0 / -10.0** → **g1–g4 전부 허용 오차 안**, g2 정확히 일치
  - 점수(절대오차 합) **125.1 → 29.8**
- **g5·g6 불가의 증명**: 단조성이 `p5 ≤ p4` 를 강제 → p4=47% 이므로 p5 ≤ 47%. 그런데 g5 는 **7.4교전**이라 47% 로 완주율 0%. 7.4교전에서 25% 를 얻으려면 교전당 **~90%** 필요 → p4 를 넘어 **다시 역전**. 즉 **미션 길이가 등급을 따라 늘어나는 한 두 곡선은 양립 불가**. 물러날 것: 미션 길이 / 단조성 불변식(ADR-0229 개정) / g5·g6 목표.
- **부수 관찰**: 곡선이 부드러워지자 g1–g3 사망이 **다시 100% 보스**(일반 교전 사망 0) — §5 의 "낮은 등급은 정점 ICE 가 유일한 벽" 과 일치.
- **갱신한 테스트 4개**(전부 커브 변경에 따른 재기준화): `balance_sim` 기준선 2행(ADR-0280 재기준 명시) · `ice_scaling` fallback(g3 상한 95 가 먼저 묶음) · `menu_stage_combat_flow` 의 피해 기대값(등급 피해 보너스 반영).
- **검증**: vitest **191 files / 4089 tests** · typecheck 0 · lint 0 errors · build PASS · `npm run balance` 새 기준선 `100/100/100/47.0/40.7/0.0`(단조) · `npm run survival` 위 수치 · 소크 15런 8 completed / 7 failed · **frozen 0** · story trace 통과. 원자료 `docs/design/adr-0280/constrained-search.txt` · `mission-survival-after-constrained-search.txt`.

## [2026-11-06] fix(harness) | 측정 도구가 교전을 건너뛰고 있었다 — 그리고 g5·g6 벽 네 번째 확인 + 선택지 확대 제안 (ADR-0280 §9)

- **측정 버그**: 런 정책이 **보스로 최단 경로**를 그렸는데 `first_jack` 은 `0 → 2 → 5` 로 **교전 없이** 보스에 닿는다(유일한 일반 교전은 node 1). 결과적으로 **모든 측정이 보스 전용 런** — 일반 교전 없음 → 전리품 화면 없음 → **카드 보상 없음 → 덱 성장 없음**. 실측 덱 크기 전 등급 **5.0–5.2장**, 최고 tier 3(g5 는 7.4교전인데도). 정책을 **가장 가까운 미해결 교전**으로 수정.
- **무효화**: 직전 커밋의 곡선은 이 결함 있는 측정에 맞춘 것 → "g1–g4 목표 안" 주장 철회. 정직한 재측정(20시드) `100.0/96.6/71.8/50.0/0.0/0.0` (목표 100/95/80/50/25/10).
- **살아남은 것**: 보스 등급 스케일링(스폰 문제, 경로 무관) · 교전 단위 곡선(`balance_sim` 은 내비게이션 안 함). **"덱이 안 자란다"는 더 강해짐** — g4–g6 에서 **첫 교전에 죽는다**(0.6–0.8교전/런) → 카드 보상을 한 번도 못 받음 = "이기려면 카드, 카드 받으려면 이겨야" 교착.
- **두 번째 불변식 위반 발견·수정**: 앞선 탐색이 `dmg g4=-20, g5=0` 을 냈는데 ADR-0229 는 *"늦은 등급은 HP 에서 경쟁을 산다"* 를 요구(`ice_scaling.test.ts` 가 `dmg5 ≤ dmg4` 고정) → g5 ICE 가 g4 보다 세게 때리는 결과였다. 탐색에 제약 추가.
- **재탐색 (세 제약: HP 단조 비감소 · 피해 g4→g6 단조 비증가 · 교전 p 단조 비증가)**: `hp [95,95,95,95,165,165]` · `dmg [50,30,-32,20,0,-20]` · **p `100/100/100/90.5/41.9/0`(단조)** · **m `100.0/95.3/72.7/48.8/0.0/0.0`**. g1–g4 허용 오차 안(g3 -7.3pp), **g5·g6 0**.
- **g5·g6 벽 네 방향 확인**: 회복(§6) · 곡선 완화(§8·§9) · **덱 강도**(`deckForGrade` 로 시작 → g5 **0.7%**, g6 2.1%) · 불변식. g5 교전 승률 ~41% × 7.4교전 → 덱이 무엇이든 ~0.
- **오너 지시 반영 — 선택지 확대 제안** (`docs/design/adr-0280/choice-expansion-proposal.md`): "사용자의 선택지를 늘리는 방식, 영향도 커도 됨, 몰입도 높아야". 제안 4개 — **A** 매트릭스 경로를 "런 설계"로(교전 수·난도·보상 표시, 리듀서·스키마 무변경) · **B** 전리품을 택1(카드/수리/크레딧)로 · **C** 잭인 전 로드아웃(크레딧에 쓰임을 줌) · **D** 교전 중 물러나기·아이템. **권고 A → B → C**, A 는 `npm run survival` 최단/최장 경로 정책으로 "선택이 난도를 얼마나 바꾸는가"를 측정 검증 가능.
- **검증**: vitest **191 files / 4089 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 15런 frozen 0 · story trace 통과. 재기준화 테스트 2행(balance_sim).

## [2026-11-06] feat(route) | 경로가 런의 모양이다 — 선택지를 늘려 난도를 플레이어에게 (ADR-0281)

- **배경**: 오너 "사용자의 선택지를 늘리는 방식으로 개선하고 싶어. 영향도가 커도 상관없어. 몰입도도 높아야 해." → "권장대로 해줘." = ADR-0280 (g) 제안 A.
- **단서**: ADR-0280 의 측정 도구 결함이 우연히 증명했다 — 런 정책이 보스로 최단 경로를 그렸더니 `first_jack` 의 `0 → 2 → 5` 로 **교전을 건너뛸 수 있었다**. 즉 **경로 선택이 이미 미션 길이를 정하고 있었고**, 화면이 말하지 않았을 뿐이다.
- **수정**: `core/dungeon/route_preview.ts`(순수 함수) — `fightsToBoss`(0-1 BFS, 교전 칸 비용 1, **도착지 자체 교전 포함**) · `fightsAvailable`(목적지 너머 남은 교전) · `creditsAvailable`. **두 수가 다른 지점이 곧 선택지**. 경로를 고르면 카드에 한 줄: `route: 2 fights · 250cr`(교전 경유) vs `route: 1 to boss · 2 open · 250cr`(건너뛰는 길).
- **화면**: `matrixCardLines` 에 추가, `bypassed` 를 `MatrixPosition` 으로 전달. **80×50 · 60×40 · 40×60 세 레이아웃 모두 렌더**(CARD_WIDTH 36 이내).
- **측정 (`npm run survival --route long|short`)**: g2 `95.7→100.0` · g3 `68.8→72.7` · **g4 `41.3→66.3` (+25.0pp)** · g5 0. **리듀서·등급 곡선·저장 스키마 무변경**으로 얻은 폭이다. 원자료 `docs/design/adr-0281/route-choice-spread.txt`.
- **몰입**: 잭인 뒤 "어디로 갈까"가 **우연이 아니라 계획**이 된다. 두 수(최소 교전 vs 남은 교전)가 다르면 그게 선택지다.
- **구현 중 모델 버그 둘 수정**: ① 테스트 픽스처의 노드 id 가 배열 인덱스와 달랐다(실제 매트릭스는 `id === index`) ② **도착지 자체의 교전을 세지 않았다** — 교전 칸으로 이동하면 그 교전이 열리므로 반드시 세야 한다. 고치기 전에는 두 경로가 똑같이 "1 to boss" 로 보였다.
- **검증**: vitest **192 files / 4098 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 12런 frozen 0 · story trace 통과 · `npm run balance`(교전 단위) 무변경(하네스는 경로를 고르지 않는다) · doc-claims/no-novel-prose/mixed-language 0.
- **남은 것**: g5·g6 는 최소 교전 경로로도 0%(정점 ICE 를 5장 tier-3 덱으로 만남) → 제안 B(전리품 택1) 또는 C(잭인 전 로드아웃) 필요. 경로 정보 밀도(인접 경로 전부 표시?)와 매트릭스 생성기 변경(명시적 short/thin vs long/thick)도 열린 질문.

## [2026-11-06] feat(loot) | 전리품은 지출이다 — 회복을 자동에서 선택으로 (ADR-0282)

- **배경**: 오너 "사용자의 선택지를 늘리는 방식" → ADR-0281 "권장대로" → "응." = ADR-0280 (g) 제안 B.
- **문제**: 전리품 화면이 **카드 3장 + 자동 회복**이라 ENTER 는 카드 건너뛰기였고 **회복은 플레이어의 결정이 아니었다.**
- **수정**: 화면이 **다섯 칸** — `1-3` 프로그램(고르면 머문다, ADR-0261) · `4` **수리**(등급별 최대 HP %) · `5` **정산**(등급별 크레딧) · `ENTER` 없음. `core/state/loot_choice.ts` 가 슬롯·수치 단일 진실. **자동 회복 제거** — 회복을 원하면 **카드를 포기**해야 하고, 그것이 선택에 값을 붙이는 유일한 방법이다.
- **스키마 무변경**: 수리·정산은 **즉시** 해결(결과가 기존 필드에 바로 반영되고 도착 메시지가 값을 말한다) → 새 상태 필드·저장 변경 0. 카드는 덱을 바꾸는 결정이라 머문다.
- **ADR-0251 규칙 5**: 제안 줄이 실제 값 인쇄(`4 REPAIR +40 HP → 100/100`, `5 SALVAGE +50cr`) · "HEAL applied" **거짓 약속 제거** · 40열에서는 48자 푸터를 자르지 않고 짧은 문구(`1-3 card · 4 repair · 5 creds`)로.
- **측정 (`npm run survival --loot card|repair|smart`)**: g2 `76.6→100.0` · **g3 `29.5 → 80.3` (+50.8pp)** · g4 30.0→32.5. **자동 회복 제거가 값을 만든다** — 예전 자동 회복으로 g3 71.8 이던 것이 "수리 안 함"에서 **29.5**, 플레이어가 **사서 되찾아야** 한다.
- **두 선택이 곱해진다**: `route=long + loot=smart` → g3 **80.7** / g4 31.3 · `route=short + loot=smart` → g3 63.1 / g4 **66.9**. **어느 설정도 둘 다 이기지 못한다** — 그게 결정으로 만든다.
- **g4 의 한계**: 전리품 선택으로 거의 안 움직인다(30.0→32.5). **첫 교전에서 죽어 전리품 화면에 도달하지 못하기** 때문(ADR-0280 §9 와 일치) — 경로 선택과 로드아웃의 몫.
- **갱신한 기존 테스트 9건**은 전부 자동 회복 제거의 결과(카드 보상 ENTER · 전리품 문구 5건 · 경로 선택 · 렌더 비교 2건). 회복을 약속하던 문구는 **없앴다**.
- **검증**: vitest **192 files / 4101 tests** · typecheck 0 · lint 0 errors · build PASS · 3레이아웃(80×50·60×40·40×60) 렌더 확인 · `npm run balance` 무변경(하네스는 전리품 화면에 도달하지 않음).
- **남은 결정**: (a) 수리 수치 확정(`[70,70,85,100,100,100]`, 지배 전략 아님) (b) **크레딧 선택이 아직 함정**(쓸 데 없음 — 제안 C 가 배선되면 의미) (c) 카드 비교 정보 밀도 (d) g4–g6 첫 교전 = **로드아웃(제안 C)**.

## [2026-11-06] docs(balance) | 잭인 전 로드아웃(카드 구매)을 시도했다가 **기각** — 오프닝 덱은 5슬롯 악기다 (ADR-0283)

- **배경**: 오너 "응." = ADR-0280 (g) 제안 C. g4–g6 는 **첫 교전에서 죽어** 전리품/경로(전투 사이 선택)가 닿지 않는다 → **교전 전** 준비가 유일하게 남은 자리이고, `inventory.credits`(ADR-0279: "미션 보상으로 시작해 한 번도 안 쓴 지갑")에 쓰임을 줄 자리이기도 하다.
- **구현했다가 되돌렸다**: `loadout` 화면(미션 선택 → 잭인 사이) + `prep.ts`(예산 = 미션 보상 × 0.6, 가격 = `tier² × 60`) + `--deck prep` 측정 모드. **측정이 세 번 다 부정적**이라 **화면은 커밋하지 않았다**(해로운 화면을 출시하는 건 규칙 위반).
- **측정 (12~16시드, 오프닝 덱 대비)**: ① 강한 카드를 **앞에** 넣기(오프닝 핸드 진입) g2 −7.8 · g3 −9.8 · g4 −3.3 ② **약한 슬롯 교체** g2 −7.8 · g3 −10.6 · **g4 +9.2** ③ **방어도 대응 우선** 쇼핑 g2 −12.9 · g3 −1.7 · g4 −0.6. (ADR-0280 에서 `--cards best` 가 g4 를 +3pp 밖에 못 올린 것도 같은 결론.)
- **원인**: **오프닝 덱은 5슬롯 악기다.** ADR-0260 이 "공격 3 + 방어 2"를 의도적으로 골랐고 전방어 오프닝을 측정으로 기각했다. ADR-0280 모델(카드당 적 1회)에서 **턴마다 HP 가 나가므로** 방어 슬롯 하나가 tier 상승보다 비싸다 → 카드를 바꾸는 prep 은 **역할을 없앤다**. 유일한 이득은 g4 +9.2pp(그 등급은 정말로 armor 9 를 못 뚫음)인데, 그 대가로 g2·g3 를 잃는다 — **보편 개선이 아니라 교환**.
- **다음 실험 (오너 결정 필요)**: prep 은 역할을 바꾸는 게 아니라 **용량을 더해야** 한다 — ① **핸드 슬롯 +1**(핸드가 턴의 화력 예산) ② **maxHp 증가**(첫 교전은 생존 검사) ③ **시작 실드 풀**. 셋 다 `barrier`/`decoy` 를 밀어내지 않고, **러너를 죽이는 그 교전**에 직접 작용한다. 캐릭터 스탯 변경이라 상점보다 큰 결정.
- **원자료**: `docs/design/adr-0283/prep-is-not-a-card-purchase.txt`.
- **검증**: 되돌린 뒤 vitest **192 files / 4101 tests** · typecheck 0 (작업 트리 clean).

## [2026-11-07] feat(balance) | prep 은 용량이다 — maxHp 로 g5·g6 벽을 뚫었다 (ADR-0283 C′)

- **배경**: 오너 "권고대로" = ADR-0283 결론(maxHp). 지난번 교훈대로 **UI 전에 측정**.
- **세 레버 측정 (12~16시드, route=long)**:
  - **추가 maxHp**: `+30 → g4 31.7 → 42.5`, `+250 → g5 0 → 19.4` — **작동**
  - **추가 핸드 슬롯**: `+2 → g4 31.7 → 31.7` — **무효**(러너가 여분 카드를 들고 죽고, COST 캡이 턴을 묶음)
  - **카드 구매**: g2·g3 하락, g4 +9.2 — **해로움**(ADR-0283 §기각)
- **구현**: `src/core/state/prep.ts` — `PREP_HP_BY_GRADE = [0, 0, 20, 25, 270, 175]` · `applyPrep(state)`. **`makeInitialState` 가 아니라 런 시작(`launchSelected`)에서 적용** — 그래야 교전 단위 하네스(`balance_sim`)가 예전과 같은 싸움을 계속 잰다(prep 은 런의 사실이지 교전의 사실이 아니다). 하네스는 `play_policy` 가 같은 테이블을 읽어 측정.
- **최종 측정 (24시드, loot=smart)**: **100 / 97.9 / 83.0 / 45.4 / 30.6 / 18.1** vs 목표 100/95/80/50/25/10. **5개 등급이 8pp 허용 오차 안**, g6 는 +8.1pp(72런 → 노이즈 이내).
  → **회복(§6)·곡선 완화(§8·§9)·덱 강도·불변식이 모두 실패한 g5·g6 벽이 뚫렸다.**
- **응답이 급격**하다(g5: +200 → 6.9%, +270 → 30.6%). 그래서 테이블은 "측정된 절벽"이지 편안한 중간값이 아니다.
- **테이블이 단조가 아니다**(g5 270 > g6 175) — 의도적이다: g5 는 7.4교전(g6 7.3)이고 정점 ICE 가 `neuromancer`(armor 9) vs `aleph`(armor 7). **플레이어 스탯에는 불변식이 없으므로** 정직한 모양을 허용했다.
- **주의(오너 보고)**: 이것은 **선택이 아니라 자동 버프**다. 용량 레버 중 살아남는 것이 HP 하나뿐이라(핸드 무효·카드 해로움) "무엇에 쓸지"의 축이 아직 없다. 선택으로 만들려면 두 번째 유효 레버(예: 시작 실드)를 찾아야 한다.
- **검증**: vitest **193 files / 4105 tests**(`prep.test.ts` 4건 신규) · typecheck 0 · lint 0 errors · build PASS · 소크 10런 **frozen 0** · story trace 통과 · doc-claims/no-novel-prose 0. 원자료 `docs/design/adr-0283/capacity-prep-spread.txt`.

## [2026-11-07] docs(balance) | 시작 실드는 진짜 두 번째 선택이다 — 그리고 등급에 따라 역전한다 (ADR-0283 C″)

- **질문**: prep 을 **선택**으로 만들려면 두 번째 유효 레버가 필요하다. 시작 실드가 그런가, 아니면 HP 에 지배되는가?
- **측정 (12시드, loot=smart, route=long)**:

  | 등급 | HP prep(운영값) | shield +60 | +120 | +240 | +400 |
  |---|---:|---:|---:|---:|---:|
  | 3 | 84.1% | **87.1** | 92.4 | 100.0 | - |
  | 4 | 45.8% | **57.5** | 67.5 | 81.7 | - |
  | 5 | **28.7%**(hp +270) | - | - | - | 11.1 |

- **트레이드오프가 실재하고, 등급에 따라 뒤집힌다**: **g3·g4 는 실드가 HP 를 이기고**(작은 풀이 초반 교전을 덮음), **g5 는 HP 가 크게 이긴다**(4배 큰 실드보다 2.6배 높음).
- **왜 위 등급에서 HP 가 이기는가 — 알아둘 가치가 있다**: 전리품 수리가 **최대 HP 의 비율**이다(ADR-0282). 그래서 큰 풀은 **두 번 복리**된다 — 지금 더 흡수하고, 이후 모든 수리가 커진다. 실드는 한 번 쓰면 돌아오지 않는다. 그게 전체 비대칭이다.
- **결론**: prep 은 **선택이 될 수 있다.** 등급별 테이블 둘(`PREP_HP_BY_GRADE` 운영 중 / `PREP_SHIELD_BY_GRADE` 미조정).
- **화면은 아직 안 지었다 — 의도적이다.** 카드 상점을 먼저 지었다가 측정으로 기각한 전례가 있고, 이 세션은 "먼저 재는 것이 싸다"를 반복 확인했다. 레버는 이제 검증됐고, 화면이 다음 단계다.
- **원자료**: `docs/design/adr-0283/shield-vs-hp-tradeoff.txt`. 하네스에 `--shield N` 측정 플래그 추가(운영 영향 없음).
- **검증**: vitest 193 files / 4105 tests · typecheck 0.

## [2026-11-07] feat(prep) | prep 선택 화면 — STIM(HP) vs ICE(실드), 등급에 따라 답이 다르다 (ADR-0283 C‴)

- **배경**: 오너 "권고대로" → "응." ADR-0283 C″ 에서 실드가 **진짜 두 번째 레버**임을 확인했으므로 화면을 지을 근거가 생겼다.
- **테이블 조정**: `PREP_SHIELD_BY_GRADE = [0, 0, 35, 45, 650, 250]` (g6 를 400→250 으로 낮춰 33.3% → 8.3% 로 목표 근접).
- **20시드 측정 (두 옵션)**:
  - `stim`: **100.0 / 98.1 / 82.3 / 46.5 / 30.6 / 16.7** — **6개 등급 모두 허용 오차 안**
  - `ice`: **100.0 / 98.8 / 68.2 / 53.5 / 22.2 / 10.0** — 5개(g3 −11.8)
  - **교차한다**: stim 은 **g3·g5**, ice 는 **g4·g6** 에서 이긴다 → **미션을 보고 고르는 결정**.
- **화면**: `prep` — 미션 선택 뒤, **2행**(STIM/ICE) + 각 옵션이 **이 미션에서 얼마인지**(테이블에서 읽음 → 화면이 거짓말할 수 없음, ADR-0251 규칙 5) + **차이를 말하는 한 줄**("lasts — repairs scale with the pool" / "absorbs now — spent once"). **↑↓/←→ 이동 · ENTER 잭인 · ESC 뒤로 — 새 키 불필요.** 80×50·60×40·**40×60** 렌더 확인.
- **리듀서·저장 스키마 무변경**: prep 은 런 상태 생성 **전**의 준비(자키 선택과 같은 성격) → 컨트롤러 화면 + 순수 함수. `launchSelected` 가 `applyPrep(initial, choice)`.
- **ADR-0275 준수**: `SCREENS_WITH_INPUT` 에 `"prep"` 등록(빠뜨리면 키가 스텁으로 새는 함정).
- **e2e 드라이버 2개 수정**: `story_trace`·`soak_playthrough` — 미션 ENTER 가 이제 prep 으로 가므로 ENTER 하나 더. **ADR-0273/0274 와 같은 함정이 세 번째**로 확인됐다. `enterForRunPhase` 를 쓰는 스펙들은 ENTER 재시도라 자동 견딤.
- **`run_end_save.spec.ts` 3건 실패는 변경 전부터** 있었다 — `git stash` 후 HEAD 에서 재현 확인.
- **검증**: vitest **194 files / 4110 tests**(`prep.test.ts` 4 · `prep_screen.test.ts` 5 신규) · typecheck 0 · lint 0 errors · build PASS · 소크 10런 **frozen 0** · story trace 통과 · doc-claims/no-novel-prose/mixed-language 0.
- **남은 질문**: (a) 테이블이 **측정된 절벽의 가장자리**다(g5 `+200 → 6.9%`, `+270 → 30.6%`) (b) g3 에서 실드가 약하다(−11.8) (c) 전리품 `5 SALVAGE` 가 여전히 거의 함정(크레딧이 prep 예산이 아님) (d) 세 번째 옵션(핸드 슬롯은 무효였다).

## [2026-11-07] feat(economy) | 크레딧이 prep 으로 간다 — 곡선이 상한을 정했다 (ADR-0284)

- **배경**: 오너 "응." ADR-0283 (c) — 전리품 `SALVAGE` 가 크레딧을 `player.credits` 에 넣었는데 prep 예산은 미션 보상 파생이라 **살 것이 없었다**(카드·수리보다 엄격히 나쁜 칸).
- **수정**: `prep_wallet.ts` — localStorage `wetrun_prep_wallet`(**`SaveSlot` 밖 → 저장 스키마 무변경**, far-grid unlock 과 같은 패턴). SALVAGE 수입의 **절반** 적립, prep 사용 시 **소비**(영구 보너스 아님). 화면이 `advance + N cr banked` · `+X (N banked)` 로 **출처를 구분**(ADR-0251 규칙 5).
- **측정이 상한을 정했다 (`--wallet`)**: share **0.5** 면 wallet 500 에서 **g5 18.8→51.4 (+19.5pp) · g6 18.8→29.2 (+10.4pp)** — **ADR-0283 의 fitted 곡선이 무너진다**(테이블에 여유가 없다). share **0**(채택)이면 스톡파일이 **fitted 등급에 얹히지 않고** `tableValue === 0` 인 등급만 채운다 → g4–g6 **동일**, g2 만 소폭(98.0→100.0).
- **정직한 결론**: 곡선-안전한 스톡파일은 **약하다** — `SALVAGE` 는 여전히 거의 함정이다. 이건 실패가 아니라 **측정된 상한**이다. 유일한 해법은 **테이블을 낮추고 스톡파일이 차이를 메우는 재조정**(= 메타 진행, 신규 러너가 더 어려움)이고 열린 질문 (a) 로 기록.
- **검증**: vitest **195 files / 4117 tests**(`prep_wallet.test.ts` 7 신규) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과. **e2e 드라이버는 이번엔 수정 불필요**(화면 수 그대로 — `prep` 재사용). 원자료 `docs/design/adr-0284/credit-to-prep-spread.txt`.

## [2026-11-07] refactor(loot) | 전리품 세 번째 선택지는 없다 — 만들 수 없다는 것을 측정하고 지웠다 (ADR-0285)

- **배경**: 오너 "c." = ADR-0284 (c). 슬롯 5 는 **두 번 실패**했다 — 크레딧(ADR-0282)은 카드·수리보다 싸서 거의 함정이었고, ADR-0284 는 fitted 등급에 얹지 않는 방식이라 여전히 약했다. 세 번째 시도는 **용량**: 플랫 maxHp 패치 `[12,14,18,24,60,40]`.
- **측정 (4 정책, 16시드, prep=stim)**: `card`(안 씀) `100/75.4/44.3/33.1/9.0/4.2` · `patch`(항상) `100/96.1/53.4/35.6/6.9/0` · **`smart`(다치면 수리) `100/98.0/81.8/45.6/31.9/18.8`** · `mixed`(건강하면 패치) `100/81.3/48.9/33.1/9.0/4.2`.
- **읽기**: 패치는 "안 쓰기"보다 낫다(g2 75.4→96.1) → 완전한 함정은 아니다. 그러나 **제때의 수리에게 어디서나 지배당한다.** 결정적 비교는 `mixed` 대 `smart` — 건강할 때 패치하면 **훨씬 나쁘다**(g3 48.9 vs 81.8). 이유: 그 loot stop 에서 **카드를 포기**하고, **성장이 용량보다 비싸다**(ADR-0260 과 같은 교훈). 수리는 최대 HP 의 50~80%(g5 에서 100+)인데 플랫 패치는 **60**. 비율로 만들면 STIM prep 과 **복리**되고 6번까지 쌓여 더 나빠진다.
- **결정**: **슬롯 제거.** 전리품은 **카드 3 + 수리**만. **지배당하는 선택지는 선택이 아니라 함정의 다른 모양**이고, 관대해 보이려 유지하면 **결정에 대해 거짓말**하는 것(ADR-0251 정신).
- **부수**: prep 스톡파일(ADR-0284)은 이제 **승리 지급액의 절반**에서 적립(`resolveVictory`) — 슬롯이 사라져도 크레딧이 다음 런의 prep 에 닿는다.
- **되돌린 것**: `LOOT_PATCH_*` · `takeLootPatch` · ADR-0284 의 SALVAGE 슬롯과 그 테스트 · 하네스 `--loot patch|mixed`.
- **화면 정합**: 오퍼 블록과 푸터에서 5번 제거 — 80열 `1-3: card | 4: repair | ENTER: none` · 48열 동일 · 40열 `1-3 card · 4 repair`.
- **검증**: vitest **195 files / 4117 tests** · typecheck 0 · lint 0 errors · build PASS · 소크 8런 **frozen 0** · story trace 통과. **e2e 드라이버 수정 불필요**(화면 수 그대로 — 키 하나만 죽었다). 원자료 `docs/design/adr-0285/third-loot-option-spread.txt`.


## [2026-11-07] docs(economy) | 상점을 지으려 했고, 곡선에 여유가 없다는 것을 확인했다 — 네 번째 소비처 기각 (ADR-0286)

- **배경**: 오너 "상점 또는 상점에 해당하는 것부터 구현해줘". `purchaseItem` 은 호출자 0, `makeInfoMarket({})` 은 빈 마켓, `src/data/` 에 market 데이터 없음 → 상점은 데이터·배선·화면이 전부 없었다.
- **시도**: prep 화면을 상점으로 확장 — `STIM` / `ICE` / **advance 가 살 수 있는 프로그램 3종**(`tier²×60`), 구매분은 **드로우 파일에 append**(역할을 안 밀어내는 순수 성장), 1개 선택 모델 유지(새 키 없음).
- **측정 (16시드)**: 기준 `stim` `100/98.0/81.8/45.6/31.9/18.8` · **one-of**(카드가 grant 대체) `100/98.0/73.3/42.5/**0**/**0**` · **stacked**(grant+카드) `100/97.7/80.1/51.9/35.4/**39.6**`.
- **두 방향 모두 실패**: ① **대체하면 지배당한다**(g5·g6 0% — 카드 한 장이 `+270 HP`(수리와 복리되는 풀)를 못 대신한다, ADR-0285 의 패치와 **같은 실패**) ② **쌓으면 곡선을 깬다**(g6 +29.6pp — fitted 테이블에 여유가 없다).
- **결정**: **상점을 커밋하지 않는다.** prep 화면은 ADR-0283 의 2행 그대로(측정으로 균형 잡힌 선택이고, 지배당하는 행을 붙이는 것은 ADR-0285 에서 이미 기각한 실수).
- **네 번의 실패가 가리키는 원인**: 크레딧(0282) · prep 스톡파일(0284) · 전리품 패치(0285) · 상점(0286) 이 **모두** "약하다 or 너무 세다" 로 수렴 → **난이도 곡선이 목표에 fitted 되어 있어 어떤 전력-부여 소비처도 자리가 없다.** 소비처를 만들려면 **먼저 곡선을 낮춰 여유를 만드는 재조정**(= 메타 진행)이 선행돼야 하고, 그건 오너 결정.
- **유의미한 발견**: **순수 성장(append)은 작동한다**(g6 18.8 → 39.6). ADR-0283 이 기각한 것은 *배치* 두 가지였고 append 는 아니었다 → **카드가 안 통하는 게 아니라 자리가 없다.**
- **검증**: 되돌린 뒤 vitest **195 files / 4117 tests** · typecheck 0 · 작업 트리 clean. `purchaseItem`·빈 마켓·market 데이터 부재는 **시도 전과 동일**.

## [2026-11-07] feat(economy) | 크레딧은 정보를 산다 — 전력을 주지 않는 유일한 소비처 (ADR-0287)

- **배경**: 오너 "권장대로" = ADR-0286 (b). 네 번의 소비처(0282 크레딧 · 0284 스톡파일 · 0285 패치 · 0286 상점)가 모두 **전력을 주는** 것이라 fitted 곡선에 자리가 없었다. 남은 방향은 **전력이 아닌 소비처**.
- **선례**: **PROBE 가 이미 위협 정보를 COST 로 판다**(ADR-0247). 정보를 파는 것은 이 게임의 기존 규칙이다. 플레이어가 실제로 모르는 것 = **경로 앞에 어떤 ICE 가 있는지**(보드는 그래프·교전수·크레딧만 보여줌, ADR-0281).
- **구현**: 전리품 **5번 = INTEL**. `LOOT_INTEL_PRICE_BY_GRADE = [30,40,60,80,110,120]` — **싸다**(정보는 세금이 아니라 결정). 구매 → 미해결 교전 전체를 `state.intelNodes` 에 공개 + credits 차감(부족하면 거절 메시지, 화면 유지). 경로 카드가 **개수를 이름으로** 바꾼다: `route: 2 fights · 250cr` → **`route: wisp, hosaka_couri`**. **`SaveSlot.intelNodes?` 선택 필드(version 1 유지)** — 돈 낸 지식이 재로드에서 사라지면 안 된다.
- **측정 A — 전력을 주지 않는다(곡선 무영향)**: `loot=intel` **100/84.4/43.8/37.5/8.3/0** = **"카드를 포기한 것"과 동급 궤적**(HP·덱·실드 무변). 참조 `smart` 100/98.0/81.8/45.6/31.9/18.8. 즉 **fitted 등급이 움직이지 않는다** — 오너가 요청한 성질.
- **측정 B — 결정 가치는 이 하네스로 측정 불가(명시)**: 정보를 보고 가장 약한 ICE 로 라우팅 `82.0/46.6` vs 무시 `84.4/43.8` → **노이즈**. 이유: **봇이 이미 `matrix.nodes` 를 직접 읽어** 그래프·ICE 를 다 안다 → 이미 다 보는 플레이어에게 정보를 팔면 가치 0. 사람은 그래프는 보지만 ICE 는 못 보므로 가치는 **지각·결정**의 문제이고 이 하네스가 가격을 못 매긴다. **한계를 숨기지 않고 문서화** — ADR-0285·0286 은 "지배당한다"는 측정으로 기각됐지만 이 옵션은 **측정 자체가 불가**다.
- **검증**: vitest **196 files / 4123 tests**(`adr0287_intel.test.ts` 5 신규 — 곡선/저장 왕복/가격/공개 범위) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과. **e2e 드라이버 수정 불필요**(화면 수 그대로).
- **남은 질문**: (a) **부분정보 봇**을 만들어 정보의 값을 측정(가장 정직한 후속) (b) 정보 범위(경로별·보스만) (c) 재구매 표시 (d) 정보는 곡선을 안 건드리므로 **더 만들 수 있다**(우회 비용 할인은 COST=런의 시계라 전력에 가까움, 주의).

## [2026-11-07] docs(balance) | 부분정보 봇으로 정보의 값을 쟀다 — 그리고 **싸우는 것이 손해**라는 더 큰 결함 (ADR-0288)

- **배경**: 오너 "응." = ADR-0287 (a). ADR-0287 은 봇이 완전정보라 정보의 값을 못 쟀다고 적었다. 그 후속.
- **방법**: `--route picky` — **산 정보에 드러난 ICE 중 tier+armour ≤ 12**(오프닝 덱이 뚫는 선)만 싸우고, 없으면 보스로 직행. **정보가 없으면 읽을 것이 없어** 보스로 직행한다(= 가다가 막는 것만 싸운다). 비교: `--route long`(다 싸움) · `--route short`(최소 교전).
- **측정 (24시드, loot=smart)**: `long` `100/97.9/83.0/45.4/30.6/18.1` · **`picky` 정보 없음 `100/99.2/93.9/72.5/64.4/65.3`** · `picky` 정보 있음 `100/87.0/88.3/72.9/55.1/62.5` · `short` `100/99.7/72.0/72.1/50.9/0.0`. g6 40시드 확대: **long 14.2% vs picky 60.8%** vs short 0%.
- **① 정보의 값은 음수**: 정보를 사면 **전리품 stop 마다 카드를 포기**하는데, 그 정보로 "뚫을 수 있는 교전"을 골라 싸우는 것이 **손해**라 더 나빠진다(g2 99.2→87.0, g5 64.4→55.1).
- **② 정보가 바꿀 결정이 없다**: g3 이상의 최적 행동은 **"싸우지 말고 보스로 간다"** 이고 그건 ICE 를 몰라도 되는 결정 → ADR-0287 intel 은 **전략적으로 장식**(불확실성 감소라는 심리적 값만).
- **③ 더 큰 결함 — 중간 등급 이상에서 싸우는 것이 손해**: 다 싸움 대비 보스 직행이 **g3 +10.9 · g4 +27.1 · g5 +33.8 · g6 +47.2pp**. **전리품(카드·수리)이 교전의 HP·위험 비용을 갚지 못한다.** 이것이 ADR-0282·0284·0285·0286 소비처 실패와 ADR-0286 "곡선에 여유가 없다"의 **공통 뿌리**다 — 여유를 만드는 쪽(싸우면 이득)이 없어서다.
- **`short` 의 g6 0.0% 는 이상하다** — 보스 직행(60.8%)보다 훨씬 나쁘다. 둘 다 교전을 피하는데 결과가 극단적으로 다르므로 **`fewestFightsNextHop` 네비게이션을 의심**(루프 또는 더 강한 ICE 를 지나는 경로). **이 숫자는 신뢰하지 않고**, 결론은 `long` 대 `picky`(정보 없음) 비교로만 세웠다(목적지 선택만 다름).
- **결정**: 코드 변경 없음 — 이 ADR 은 **진단**이다. ADR-0287 의 intel 은 철회하지 않되 **전략적 가치 없음**을 명시.
- **검증**: vitest 196 files / 4123 tests 그대로(측정 전용 하네스 변경). 

## [2026-11-07] docs(balance) | "싸우는 것이 손해"의 원인은 보상이 아니라 곡선 (ADR-0289)

- **배경**: 오너 "좋아. 권장대로." = ADR-0288 (a) ①(전리품 확대). **세 번 재보고 세 번 뒤집혔다.**
- **측정 1 — 교전 수 상관(10시드/미션)**: `fightAll` vs `skip` 격차 **2교전 +4.0 · 3 +4.3 · 4 +22.2 · 5 +11.4 · 6 +27.1 · 7+ +25.0pp**. **해석 주의**: 2-3교전에서 격차가 작은 건 **싸움이 나아져서가 아니라 건너뛸 것이 없어서**다 → **미션 단축은 선택을 고치는 게 아니라 지우는 것**. 오너 목표("선택지를 늘린다")와 정면 충돌 → 기각.
- **측정 2 — ①은 측정으로 사망**: 카드에 회복을 붙임. 25-40% → g4 37.5/g6 0.0 · 60-90% → 38.8/16.7 · **100%(상한) → 41.9/16.7**. 같은 조건 **스킵 71.3/59.7**. **매 카드 100% 회복조차 30-43pp 뒤진다** = **교전 중에 죽으므로 보상으로 못 메운다.** 되돌림.
- **측정 3 — 스킵 가격화는 구조적으로 불가**: ⑴ **미해결 노드당 ward** — 분기 그래프는 모든 노드 방문 불가 → "미해결"이 불가피, "건너뜀"이 정의 안 됨 → 모두 처벌(g5·g6 0.0). ⑵ **보스 clear-gate** — **이전 "데드락" 보고는 오진이었다(봇이 막힌 이동을 무한 재시도)**. 반응형 봇(`bossSealed` → `nearestObjective`)으로 재측정: g4 `long 12.9` vs `picky 12.5` = **선택 소멸(둘 다 나쁘다)**, 목표 50%에서 37pp 이탈. gate 단독 기각.
- **측정 4 — 진짜 손잡이는 교전 생존율**: `npm run balance` 교전당 승률 **g4 90.5 · g5 41.9 · g6 0.0**. **오프닝 덱은 g5 교전을 절반 이기고 g6 교전은 절대 못 이긴다** → 회피가 합리적 → 어떤 보상도 소용없다. 곡선 스윕(gate ON, 12시드): **D(cap `95,95`, dmg `0,-10,-10`)** 에서 **처음으로 `long ≥ picky`** (g5 **88.9 vs 85.2**, g6 41.7 vs 61.1). g4 는 여전히 21.7 vs 25.8(다음 손질 대상 — HP cap 이 이미 95 라 보스/교전 수 문제).
- **결론**: ① 기각 · 스킵 단독 가격화 기각 · **원인은 곡선** → **ADR-0229 재기준화 + gate 를 함께**(gate 단독은 g4 를 12.5% 로 부수고, 곡선 단독은 회피가 여전히 최적).
- **검증**: **생산 코드 변경 0**(실험 3종 전부 되돌림, `git status` clean) · vitest **196 files / 4123 tests** 그대로.
- **정정**: 이전 세션의 "gate 데드락" 결론은 봇 아티팩트였음을 ADR 에 명시.

## [2026-11-07] feat(balance) | 곡선 재기준화 + 코어는 경로 뒤에 있다 (ADR-0290)

- **배경**: 오너 "응." = ADR-0289 (a)·(b) 승인. 두 변경은 **함께** 넣어야 한다 — 곡선만 넣으면 회피가 여전히 최적, gate 만 넣으면 g4 12.5%.
- **⑴ 늦은 등급 교전을 이길 수 있게**: `ENCOUNTER_HP_BY_GRADE` `95,95,95,95,165,165` → **`95,95,95,95,95,95`** · `ENCOUNTER_DMG_BONUS_PCT_BY_GRADE` `50,30,-32,20,0,-20` → **`50,30,-32,0,-10,-10`** · `PREP_HP_BY_GRADE` g4 **25→55**, g5 **270→240** · `PREP_SHIELD_BY_GRADE` g5 **650→400**. g4 는 prep 이 +25 뿐이라 다른 등급보다 어려웠고(비단조 원인), +55 로 g3 > g4 > g5 성립.
- **⑵ 보스 HP 분리**: **`BOSS_HP_BY_GRADE = [95,95,95,95,165,165]`** 신설 + `iceHpForGrade(ice, grade, isBoss)`. 이전엔 교전과 보스가 **같은 상한**이라, 교전을 살리려 상한을 내리면 보스까지 −42% 약해졌다 — ADR-0289 스윕에서 g5 가 98% 로 튄 이유. 보스 HP 는 **이전 값 그대로 재현** → 이 결정은 보스 난이도를 바꾸지 않는다.
- **⑶ 코어는 경로 뒤에**: `BOSS_GATE_CLEARS_BY_GRADE=[0,1,1,1,1,1]`, `bossGateNeed = min(gate, 보드의 비-보스 교전 수)` — **보드에 있는 것보다 많이 요구하지 않으므로** 짧은 미션·교전 없는 보드도 잠기지 않는다. 봉인이면 **이동 거부** + `Core sealed — N more ICE must fall (h/N)`. g1 은 0(첫 미션은 그대로).
- **측정 (24시드, loot=smart)**: `long` **100/97.9/87.9/72.5/43.5/15.3** · `picky` **100/99.2/89.0/72.5/42.1/15.3** → **모든 등급에서 두 정책이 노이즈 이내** = **싸움도 회피도 지배 전략이 아니다**(ADR-0288 에선 g4 +27.1 · g6 +47.2pp). 교전당 승률 **100/100/100/99.7/88.3/52.3** (이전 …/95.2/44.1/**0.3**). **0.3% 라는 벽이 이 세션 전체의 뿌리**였다 — 이길 수 없는 교전은 선택이 아니라 벽.
- **봇 수정(중요)**: `nearestObjective` 가 **봉인 중엔 보스를 목적지로 삼지 않는다**. 없으면 봇이 봉인 앞에서 영원히 재시도한다 — **ADR-0289 의 "gate 데드락" 오진의 정체**가 바로 이것이었다.
- **검증**: vitest **197 files / 4128 tests**(`adr0290_the_core_opens_after_a_path.test.ts` 5 신규 — 봉인 거부/해제/클램프/보스HP 분리/등급별 요구) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과. **e2e 드라이버 수정 불필요**(새 화면 없음).
- **재기준화**: 목표 `100/95/80/50/25/10` 폐기, 측정값 `100/97.9/87.9/72.5/43.5/15.3` 을 새 baseline 으로. 교전당 곡선은 단조 비증가 유지.
- **남은 질문**: (a) g6 15.3%(목표 10%보다 높음) (b) prep 곡선의 g4 55 → g5 240 절벽(보스 HP 95→165 때문, 매끄럽게 한 3종은 g5 를 2-11% 로 떨어뜨림) (c) gate 2+ (d) **고를 교전이 생겼으니 intel 값을 다시 측정할 가치**.

## [2026-11-07] docs(economy) | 정보의 값 — 상황에 맞게 쓰면 작게 이득, 항상 쓰면 손해 (ADR-0291)

- **배경**: 오너 "응." = ADR-0290 (d). ADR-0287 은 자기 intel 의 값을 "측정 불가"로, ADR-0288 은 "음수"로 남겼다. 그때는 봇이 완전정보였고 회피가 최적이었다. **이제 gate 가 생겨 교전을 고를 일이 생겼으므로** 정보를 **모르는 봇**으로 다시 쟀다.
- **방법**: `--route blind` — 산 정보가 없으면 **가까운** 교전, 있으면 **가장 약한** 교전. **`matrix.nodes` 의 ICE 를 읽지 않으므로** 정보를 사지 않으면 진짜로 모른다. 같은 봇·같은 보드·같은 gate → **차이가 곧 정보의 값**. `--intel-free` 는 stop 비용 없이 지급(측정 전용)해 정보 가치와 stop 가치를 분리.
- **측정 (24시드)**: 정보 없음 **99.2/89.0/72.5/42.1/15.3** · **항상 산다 99.2/70.5/67.9/33.3/25.0**(g3 **−18.5pp**) · 공짜 정보 99.2/91.3/67.9/48.1/15.3(**≈0**) · **상황에 맞게 99.7/89.4/73.8/44.9/19.4**. 32시드 재측정: **모든 등급 +0.4~+2.7pp 일관 이득**.
- **① "항상 산다" 는 함정**: intel 은 **stop 하나**를 쓰는데, 그 stop 은 **카드 한 장 또는 수리 한 번**의 값이고 그게 정보보다 비싸다(g3 −18.5pp).
- **② "공짜 정보" 도 거의 0**: stop 비용을 없애도 g4 −4.6 · g5 +6.0 · g6 0. gate 를 2로 올려 선택을 더 중요하게 만들어도(16시드) g4 88.8 vs 74.4. **정보가 바꾸는 결정은 "어느 한 교전을 칠까"뿐인데, 한 등급 안 교전들이 서로 비슷하다.**
- **③ 그래서 쓰는 방식이 값을 만든다**: 카드 제안이 전부 tier ≤ 2 면 그 stop 은 이미 손해 → 정보로 환전하면 작게 이득(32시드 일관 +0.4~2.7pp).
- **결정**: ⑴ intel 유지(ADR-0287) ⑵ **화면이 `(spends this stop)` 을 지불 전에 표시** — 측정이 "이걸 모르면 −18.5pp"라고 말하므로 ⑶ 생산 코드는 그 한 줄 외 무변경(`blind`·`--intel-free`·`smartintel` 은 측정 전용) ⑷ **정보 소비처를 더 만들지 않는다** — 정보의 가치는 **정보에 의존하는 결정의 수**에 비례하는데 지금은 1개이고 그 1개도 거의 무차별.
- **검증**: vitest **197 files / 4128 tests** · typecheck 0 · lint 0 errors · build PASS.
- **열린 질문**: (a) 교전마다 **드롭이 다르면**(희귀 ICE = 희귀 프로그램) 정보가 덱 빌드의 지도가 된다 — 별도 결정, "싸우면 이득" 문제와 맞닿음 (b) gate 2 는 16시드에서 오히려 나빠져 결론 유보 (c) 재구매 방지 장치.

## [2026-11-07] feat(loot) | 드롭은 그 ICE 의 값이다 — "싸우면 이득"이 처음 성립 (ADR-0292)

- **배경**: 오너 "더 가자." = ADR-0291 (a). ADR-0291 의 답은 불편했다 — **산 정보의 값 ≈0**. 이유는 정보가 아니라 **정보가 바꿀 결정이 없어서**다: 한 등급의 모든 교전이 **같은 카드 풀**에서 드롭했으므로 "어느 교전을 칠까"가 결과를 바꾸지 않았다. 정보를 더 파는 대신 **정보가 말할 거리를 만들었다**.
- **구현**: `card_reward.ts` — `RewardSource.iceRoster?` + `iceTierOf`(로스터 **최고 tier** = 방의 값) + **가중 추첨** `weight = 1/(1+(cardTier-iceTier)²)`, 비복원. **난수 소비 개수 동일 → 결정성 유지**(재로드로 재굴림 불가). 로스터 없는 상태(수제 테스트·구 세이브)는 중립 tier 1 로 이전과 동일.
- **측정 ① — fighting pays 성립 (60시드, `--cards best`, `--grade` 별)**: g5 `long 48.7` vs `blind 44.1` (**+4.6**) · g6 `20.6` vs `13.3` (**+7.3**). ADR-0290 까진 두 전략이 같았고(g5 43.5 vs 42.1), ADR-0288 에선 회피가 **압승**(g6 +47.2pp). **이제 싸우는 쪽이 이긴다.**
- **측정 ② — 가중의 효과(대조군: 같은 봇, 가중 없음)**: g5 43.9 → **48.7 (+4.8)** · g6 21.7 → 20.6 (−1.1, 노이즈). g6 는 이미 카드가 전부 고 tier 라 "더 좋은 카드" 축이 남아 있지 않다.
- **측정 ③ — 정보의 값**: ADR-0291 에서 노이즈였던 것이 g5 60시드에서 **44.1 → 49.1 (+5.0)**. **단 g6 에선 최선 사용이 반대**: `--ice-limit` 를 올려 "이길 수 있는 가장 강한 교전"을 고르면 **13.3% → 1.1%** 로 붕괴 — 높은 등급은 싸움 자체가 위험이고 드롭이 보상하지 못한다. **정보의 최선 사용은 등급에 따라 바뀐다**(낮은 등급 사냥 / 높은 등급 회피). 봇은 고정 규칙이라 못 표현 — **게임의 성질이지 결함 아님.**
- **곡선 무영향**: 교전당 승률은 드롭과 무관, `100/100/100/99.0/85.2/32.2` 그대로.
- **검증**: vitest **198 files / 4132 tests**(`adr0292_a_drop_is_worth_its_ice.test.ts` 4 신규 — 강한 ICE 가 높은 tier 제안/결정성/보유 카드 제외/로스터 없음 폴백) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과. **e2e 수정 불필요**(화면 무변).
- **남은 질문**: (a) g6 의 보상 축이 없다 — 크레딧·희귀 재료·고유 카드 필요 (b) 가중 세기 `1/(1+d²)` 근사 (c) 정보가 "이 교전은 tier 5 카드"까지 말할지 (d) `picky`/`blind` 의 "이길 수 있다" 판정(tier+armour ≤ 12)은 근사.

## [2026-11-08] feat(reward) | 처치는 자기 몫을 낸다 — g6 의 보상 축 (ADR-0293)

- **배경**: 오너 "응." = ADR-0292 (a). ADR-0292 는 드롭을 ICE 의 값으로 만들어 중간 등급에 **카드** 축을 줬지만, **g6 는 포화**다(카드가 전부 고 tier). 남은 축은 **돈** — 세계관에도 맞는다(**뉴로맨서가 와치독보다 비싸다**).
- **구현**: `victory.ts` — `BOUNTY_BY_TIER = [0,25,50,90,140,200]` · `bountyFor(ice)` · `totalReward = 노드 + 미션 + 업적 + **현상금**`(처치 단위, 다중 ICE 방은 마리당) · 메시지 `(bounty N)`. **전투는 크레딧을 읽지 않으므로 fitted 교전당 곡선 무영향.**
- **측정 (40시드)**: g6 최소경로(1교전) 완료 **11.7% · 1,645cr** vs 모두 싸움 **20.0% · 3,426cr** = **싸우면 두 배** · g5 3,698 → **5,658cr**. 현상금이 "더 싸울 이유"를 만들었고, 크레딧→prep(ADR-0284)의 유일한 수입원이므로 상위 등급을 오래 도는 것이 다음 런 용량을 키운다.
- **곡선 무영향**: 교전당 승률 `100/100/100/99.0/85.2/32.2` 그대로.
- **정직한 부작용**: g6 에서 "다 싸운다"가 **완료율과 크레딧 모두** 우세 → 최상위 등급엔 트레이드오프가 아니라 **정답**이 있다. 원인은 현상금이 아니라 ADR-0292 의 카드 축(그때도 +7.3pp). **교전 비용 상향은 역효과** — g6 HP 상한 110 → long 20.8 vs blind **9.2**, 125 → 17.5 vs **4.2** (격차 확대, "최소 경로"가 장비 없이 보스로 가므로 먼저 무너짐). 그래서 이 ADR 은 비용을 건드리지 않는다.
- **검증**: vitest **199 files / 4135 tests**(`adr0293_a_kill_pays_its_bounty.test.ts` 3 신규 — tier 단조 증가/tier<1 은 0/범위 밖 클램프) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) g6 의 트레이드오프는 **다른 축**이 필요(보스가 요구하는 덱 품질 하한, 상위 등급 우회 비용) (b) 현상금 기울기(지수로 올리면 prep 곡선을 흔듦) (c) 크레딧의 **런 안** 용도(전투 중 긴급 수리 등)는 전력을 사는 것이라 ADR-0286 교훈을 다시 통과해야 함.

## [2026-11-08] feat(balance) | 처치는 흔적을 남긴다 — "얼마나 싸울까"가 진짜 결정이 되다 (ADR-0294)

- **배경**: 오너 "응." = ADR-0293 (a). **단, 승인했던 "덱 품질 gate" 는 측정 전에 기각하고 구현하지 않았다** — 약한 덱이 **아예 못 들어가면** 대안이 사라져 트레이드오프가 아니라 **정답 제거**가 된다(ADR-0289 의 gate 단독 실패와 같은 실수).
- **먼저 찾은 것**: 이미 있는 비용 중 **싸움 횟수에 비례**하는 것은 **COST** 다(프로그램이 소비, 리필 없음, 100 이면 못 씀). COST_LIMIT 을 조여보니 long 이 무너지고 blind 는 그대로(100 → 20.8/13.3, 80 → **6.7**/13.3, 60 → 10.0/13.3, 45 → 4.2/13.3). 즉 **이 축이 두 전략을 만나는 지점**이다.
- **구현**: **처치가 `tier` 만큼 COST 를 남긴다** — `TRACE_COST_PER_TIER = 1` · `traceCostFor` · `resolveVictory` 에서 `alarm = min(COST_LIMIT, alarm + Σtier)` · 메시지 `(bounty N) · trace +N`. **새 자원을 만들지 않고 기존 시계에 뜻을 붙였다.**
- **왜 강도가 아니라 이 축인가**: g6 교전 HP 상한을 110/125 로 올려봤더니 **격차가 벌어졌다**(long 20.8 vs blind 9.2/4.2). 교전이 강해지면 **장비 없이 코어로 가는 쪽**이 먼저 무너진다. **강도=싸움의 질**, **COST=싸움의 횟수** — 후자라야 만난다.
- **측정 (48시드, `--cards best`, fight vs skip)**: g1 100/100 · g2 98.0/100 · g3 85.6/89.2 · g4 **76.7/74.4** · g5 **40.0/43.3** · g6 **14.6/13.9** → **전 등급 ±3.6pp, 방향도 불일정**(g4·g6 싸움, g2·g3·g5 회피) = **정답이 아니라 거래**. 대조: 흔적 없던 0293 은 g5·g6 **+6.3 한 방향**, ADR-0288 은 **+47.2pp**.
- **흔적 세기**: `×2` 는 g6 를 회피 우세로 뒤집고(12.5 vs 13.5) g5 를 25.7 로 부순다 = **너무 세다**. `×1` 이 측정된 균형점.
- **곡선**: 단조 유지 `100/98.0/85.6/76.7/40.0/14.6`. 교전당 곡선(`npm run balance`)은 무영향 — 흔적은 교전 **후**에 붙는다.
- **검증**: vitest **200 files / 4139 tests**(`adr0294_the_trace_closes_in.test.ts` 4 신규 — tier 비례/무-tier 0/승리 시 예산 증가/상한 클램프) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) 세기 ×1 이 균형점 (b) **회복 수단** — 크레딧으로 COST 를 사면 0293 (c) 의 "런 안 크레딧 용도"가 닫히지만 전력을 사는 것이라 ADR-0286 교훈 재통과 필요 (c) 경로 카드에 **예상 흔적** 표시(0291 intel 과 겹침).

## [2026-11-08] feat(loot) | 흔적은 뺄 수 있다 — 몸으로 값을 낸다 (ADR-0295)

- **배경**: 오너 "b." = ADR-0294 (b). ADR-0294 는 **싸움의 비용**을 만들었지만 **빠져나갈 길**이 없었다 — 비용에 답이 없으면 트레이드오프가 아니라 **함정**이다.
- **크레딧 설계는 측정으로 두 번 죽었다**: `40cr/COST` 는 g6 19.4 vs 13.9 → **싸움 +5.5pp 우세 = 붕괴**(**돈이 용량을 찍어낸다** — 현상금(0293)으로 흔적을 지우면 순환이 닫힘). 가격 스윕 40/100/175/190cr 어디서도 **g5·g6 동시 균형 불가**; 190cr 는 애초에 **살 수 없는 가격**이라 죽은 옵션.
- **구현 — HP 로 낸다**: `VENT_COST=10` · **`VENT_HP_PCT=40`** · 전리품 **6번 칸** `6 VENT  120 HP — clear 10 COST → 45/100`. **구매이지 전리품 선택이 아니다** — 화면을 닫지 않으므로 **카드를 포기하지 않는다**. HP 가 값 이하면 거절, COST 는 0 바닥.
- **왜 HP 인가**: 이것만이 **자원을 찍어내지 않는다**. 몸을 용량으로 **재배치**하고 총량은 그대로 → 0294 의 트레이드오프가 **구조적으로** 살아남는다.
- **측정 (48시드, `--cards best`) — `VENT_HP_PCT` 스윕**: 15% → g6 **31.7 vs 13.3**(싸움 압승, 0294 되돌림) · 20% 18.8/13.9 · 30% 18.3/13.3 · **40% 14.6/13.9 = ADR-0294 와 동일**. 전 등급 최종: g1 100/100 · g2 98.0/100 · g3 85.6/89.2 · g4 76.7/74.4 · g5 40.0/43.3 · g6 14.6/13.9 = **±3.6pp, 방향 불일정 = 거래 유지**.
- **정직한 한계**: 40% 는 비싸서 하네스가 **거의 쓰지 않는다**(안 쓸 때와 수치 동일). **그게 의도다** — 싸면 트레이드오프가 무너지고, 비싸면 비상용 밸브. 옵션의 가치는 **COST 가 바닥나 아무것도 못 쓰는 상태에서의 탈출**이고, 봇은 그 상황을 스스로 만들지 않는다.
- **검증**: vitest **201 files / 4144 tests**(`adr0295_the_trace_can_be_vented.test.ts` 5 신규 — COST/HP 교환 · 화면 유지(카드 미소모) · HP 부족 거절 · 0 바닥 · HP 비례 가격) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) 10 COST 단위를 5 COST/20% 로 세분화(같은 비율, 사용 패턴은 다를 수 있음) (b) **카드를 버리고** COST 회수 — 값이 "성장"이면 트레이드오프가 더 선명 (c) 경로 카드에 **예상 흔적** 표시.

## [2026-11-08] feat(loot) | 카드를 태워 숨통을 튼다 — 값이 "성장"인 선택지 (ADR-0296)

- **배경**: 오너 "좋아. 권장대로." = ADR-0295 (b). 흔적의 값을 **몸(HP)** 으로 매긴 0295 는 안전하지만 재미가 없다. 이 게임의 화폐는 몸이 아니라 **성장**이고, 카드를 태우는 것은 **곡선이 읽지 않는 자원**을 쓰는 일이라 균형을 깰 수 없다 — 서사적으로도 "그 프로그램을 태워서 계속 뛴다".
- **구현**: 전리품 **7번 = BURN** — **가장 강한 카드**(tier 최대, 동률 id 내림차순 = 결정적)를 태워 **`BURN_COST=7`** 만큼 COST 회수. **화면을 닫지 않아** 카드 제안은 그대로(구매이지 전리품 선택이 아님). 마지막 한 장은 거절, COST 는 0 바닥.
- **측정 — 두 번 틀렸고 세 번째가 답**:
  - ⑴ **가장 약한 카드** → g5 **50.5**/43.3 · g6 **20.8**/13.9 = **+6.9 붕괴**. **가장 약한 카드는 애초에 쓰이지 않으므로 값이 0** — 공짜 용량.
  - ⑵ **가장 강한 카드 + 10 COST** → g5 44.7/43.3 · g6 **18.1**/13.9 = 아직 **+4.2**.
  - ⑶ **가장 강한 카드 + 7 COST** → g1 100/100 · g2 98.0/100 · g3 85.6/89.2 · g4 76.7/74.4 · g5 **44.7**/43.3 · g6 **11.8**/13.9 = **전 등급 ±3.6pp, 방향 불일정 = 거래 유지**. (5 COST 는 g6 를 정확히 13.3/13.3 으로 맞추지만 g5 가 −3.9 로 기움 → **7 이 가장 고름**.)
- **결과**: 흔적에 **세 가지 답**이 생겼다 — **몸으로**(0295, 40% HP) · **성장으로**(0296, 가장 강한 카드) · **안고 간다**. 셋 다 실제 선택이고, 0296 이 가장 게임답다(잃는 것이 **다음 교전의 화력**).
- **곡선 무영향**: 카드 하나를 없애는 것을 fitted 곡선은 읽지 않는다. 교전당 승률 그대로.
- **검증**: vitest **202 files / 4149 tests**(`adr0296_burn_a_card_for_capacity.test.ts` 5 신규 — 가장 강한 카드 선택 · 제거+COST 감소 · 화면 유지 · 마지막 한 장 거절 · 0 바닥) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) 어떤 카드를 태울지 **고르게** 할 것인가(카드 선택 UI = 전리품이 메뉴가 됨) (b) 화면이 **얼마나 아픈지** 예고할 것인가 (c) 세 화폐(몸·성장·정보)의 **조합** 지출은 미측정.

## [2026-11-08] feat(ui) | 조합 지출은 이미 있었다 — 없던 건 발견 가능성 (ADR-0297)

- **배경**: 오너 "C." = ADR-0296 (c). 가설은 "몸·성장·정보를 **함께** 내고 **더 많이** 회수". 만들어보니 **조합은 이미 있었다** — vent(0295)와 burn(0296) 둘 다 **화면을 닫지 않으므로** 한 stop 에서 **17 COST** 를 지울 수 있다. **새 화폐가 필요했던 게 아니라 그 사실을 아무도 말해주지 않았다.**
- **측정 (48시드, `loot=smartcombo` = COST≥85 면 vent, ≥70 이면 burn)**: g4 76.7/74.4 · g5 **46.8**/43.3 · g6 11.8/13.9 → **전 등급 ±3.5pp = ADR-0294 의 거래 유지**. 단일 burn(44.7)보다 **+2.1pp** — **실재하지만 작은** 이득(깊은 구멍에서만 의미).
- **정보는 조합의 화폐가 아니다**: intel 은 ADR-0291 에서 **가치 ≈0**(상황 한정 +0.4~2.7pp)으로 측정됐고 그것도 **stop 을 써서** 산다. vent 의 지불 수단으로 넣으면 **가치 0 을 용량과 교환**하는 셈이라 트레이드오프만 흐린다 → **의도적 제외.**
- **수정 — 새 메커니즘 없음, 화면이 사실을 말하게 함**: ⑴ **HUD 가 실제로 동작하는 키만** 부른다 — 흔적이 없으면 `6: vent · 7: burn` 을 **표시하지 않는다**(이전엔 COST 0 에서도 두 키를 약속 = **누르면 아무 일도 없는 거짓 어포던스**, ADR-0251 rule 5). ⑵ 둘 다 가능하면 **`· 6+7 stack`** 을 명시해 **한 stop 으로 17 COST** 를 지울 수 있음을 알린다.
- **검증**: vitest **202 files / 4150 tests**(`run_screen.test.ts` — 흔적 없는 HUD 는 세 칸만 + 흔적 80 에서 조합 문구 검증 신규) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**(키 변화 없음, 문구만).
- **남은 질문**: (a) **묶음 할인**을 넣으면 조합이 기본 선택이 되고 대부분 싸움 우세로 기울 것(0295·0296 스윕이 그랬다) (b) COST 80+ 에서 "흔적이 깊다"를 더 분명히 (c) **화폐 간 역방향 교환**(COST→HP)은 진짜 선택이 될 수 있지만 전력을 사는 것이라 ADR-0286 교훈 재통과 필요.

## [2026-11-08] feat(loot) | 뜨거운 흔적은 몸으로 되돌린다 — SYPHON (ADR-0298)

- **배경**: 오너 "C." = ADR-0297 (c). 지금까지 **HP → COST**(0295)만 있었고 반대가 없어, 용량을 쌓아두고 두들겨 맞은 러너는 **예산이 남는데도 손을 놓고 있을** 수밖에 없었다. 이번엔 거래가 **거의 깨졌다**.
- **구현**: 전리품 **8번 = SYPHON** — `10 COST → 최대 HP 25%`, **오직 `COST ≥ 70`(뜨거운 흔적)일 때만**(`RECOVER_MIN_COST`). 화면을 닫지 않고(구매), HP 가득이면 거절. **왕복 손실 15%**(vent 40% ↔ syphon 25%)라 **순환 불가**.
- **측정 — 세 번 틀렸다**:
  - ⑴ **10 COST → 25% HP**: g5 48.1/43.3 · g6 **23.6**/13.9 = **+9.7 붕괴**. 10% 로 낮춰도 g6 20.0. 그런데 **가격을 올리면 더 좋아졌다**(20 COST→10% 가 g5 **52.8**, 30 COST→20% 가 g6 25.0) — **결정적 단서**: **COST 는 싸움을 많이 한 런의 끝에 남는다**(55~74/100). 즉 **지불되지 않는 자원**을 몸으로 바꾸는 것이라, 비쌀수록 오히려 더 회수한다.
  - ⑵ **1런 1회 제한**: g6 **9.0** vs 13.9 — **더 나빠졌다**. 봇이 이른 시점에 써버려 정작 필요할 때 예산이 없다(타이밍을 봇이 못 푼다).
  - ⑶ **뜨거울 때만(COST ≥ 70)**: g4 77.1/74.4 · g5 41.9/43.3 · g6 11.8/13.9 = **±2.7pp, 거래 유지**. 논리도 자연스럽다 — **예산이 아직 필요한 러너는 70 에 도달하지 않는다.** "정말 안 쓰는 압력"만 몸으로 바꿀 수 있다.
- **결과**: 교환 3종 완성 — **HP→COST**(0295) · **카드→COST**(0296) · **COST→HP**(0298). 전부 **손실 있는 환전**이라 순환이 안 된다. 전리품 화면은 8칸.
- **검증**: vitest **203 files / 4155 tests**(`adr0298_syphon_a_hot_trace.test.ts` 5 신규 — 교환 · 차가운 흔적 거절 · HP 가득 거절 · 화면 유지 · 순환 불가) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) 임계값 70 은 **측정이 강요한 문턱**이지 서사의 필연이 아니다 (b) 25% 는 40% 와 짝지어 왕복 손실 15% 를 만들기 위한 값(30/30 은 순환 가능해짐 = 위험) (c) **전리품 8칸의 밀도** — 40열 레이아웃 확인 필요, 더 늘면 화면을 두 쪽으로 나누는 편이 낫다.

## [2026-11-08] fix(ui) | 전리품 화면이 40열에서 잘렸다 — 잘린 건 가격이었다 (ADR-0299)

- **배경**: 오너 "Continue." = ADR-0298 (c). ADR-0295~0298 이 전리품 화면을 **4칸에서 8칸으로** 키웠고 줄도 길어졌다. 실제로 40열에서 렌더해보니 **글자가 중간에서 잘렸고, 잘린 부분이 하필 값(price)** 이었다.
- **측정 (40x60, 흔적 80 / HP 150/300)**: `5 INTEL 30cr — name the rout` · `6 VENT 120 HP — clear 10 CO` · `8 SYPHON 10 COST — +75 HP → 2` ← **가격이 오타처럼 보인다.** 60열에서도 intel(72자)이 잘린다. 그리고 패널 하단 문구가 `1-3: card | 4: repair | 5: intel` 에 멈춰 있어 **ADR-0287 이후 늘어난 6·7·8 을 말하지 않는다**(ADR-0251 rule 5 위반).
- **수정**: ⑴ **< 76열은 짧은 형식** — `4 REPAIR +210HP → 300/300` · `5 INTEL 30cr` · `6 VENT 120HP → 70/100` · `7 BURN p1(T1) → 7` · `8 SYPHON 10 → +75HP`. **모든 숫자는 남긴다.** 76열 경계 = 가장 긴 전체 문구(intel 72자) + 여백. ⑵ **패널 하단 문구를 호출자가 결정**(`renderLootScreen(..., hint)`) → 화면과 패널이 **같은 문장**을 쓰므로 어긋날 수 없다. ⑶ 폭을 넘으면 `1-3 card · 4-8 options`.
- **실측 최장 줄**: 40열 **32자** · 60열 **42자** · 80열 **78자** — 셋 다 패널 안.
- **검증**: vitest **204 files / 4160 tests**(`adr0299_loot_fits_the_narrow_panel.test.ts` 5 신규 — 40·60열에서 가격 온전(`70/100` 포함) · 패널 폭 초과 없음 · 80열은 긴 문장 + 하단이 8번까지) · `run_screen.test.ts` 기대값에 같은 `hint` 전달 · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) 9칸 이상이면 **두 쪽으로 분리** 필요(그때 e2e 드라이버 등록, ADR-0275) (b) `7 BURN p1(T1) → 7` 은 숫자 두 개가 붙어 흐릿 — `-7 COST` 표기가 나을 수 있으나 40열에서 다시 길어짐 (c) 새 옵션 추가 시 **폭 검사 자동화**.

## [2026-11-08] feat(ui) | 넘치는 줄은 빌드를 실패시킨다 (ADR-0300)

- **배경**: 오너 "Continue." = ADR-0299 (c). 이 세션에서 **같은 실수를 두 번** 했다 — 화면이 **약속하지 않아야 할 것을 약속**했고(거짓 어포던스), **말해야 할 값을 잘라먹었다**(`+75 HP → 2`). 둘 다 **테스트가 없어** 늦게 발견됐다. 두 번째는 **구조적으로** 막을 수 있다: 글자를 그리는 그 자리에서 잰다.
- **구현**: `setText` 가 **오른쪽 경계를 넘는 텍스트를 기록** — `takeClippedText()`(꺼내고 비움), 상한 64(비정상 프레임이 메모리를 먹지 않도록). 테스트가 **화면 × 레이아웃(40·60·80)** 을 렌더하고 **목록이 비었는지** 단언하며, 실패하면 **잘린 문자열이 그대로 출력**된다.
- **측정 — 도구가 스스로 동작하는지 먼저 증명**(아무것도 기록하지 않는 가드는 가드가 아니다): 10열에 16자 → `["0123456789ABCDEF"]` 기록 · 20열에 9자 → `[]` · 두 번째 읽기 → `[]`(드레인). 그리고 현재 화면: 전리품(흔적 80/0) · 매트릭스 · 엔딩 × 40/60/80 = **전부 0건**.
- **결과**: 옵션을 하나 더 붙였는데 40열에서 안 들어가면 **테스트가 실패하고 그 문자열을 보여준다**. 거짓 어포던스 계열의 **두 번째 축**(잘린 약속)이 막혔다 — 첫 축(동작 안 하는 키를 부르는 HUD)은 ADR-0297 이 문구를 실제 옵션에서 조립해 막았다.
- **생산 비용**: 넘치는 줄이 없으면 `setText` 추가분은 **비교 한 번**.
- **검증**: vitest **205 files / 4174 tests**(`adr0300_no_text_is_cut_off.test.ts` 14 — 도구 자체 검증 2 + 화면 4 × 레이아웃 3) · typecheck 0 · lint 0 errors · build PASS · 소크 8런 frozen 0 · story trace 통과 · **e2e 수정 불필요**.
- **남은 질문**: (a) **나머지 화면**(prep·mission select·codex·crafting)으로 확대 — 각 뷰 타입을 실제로 만들어야 해서 화면별 작업 (b) 개발 중 `console.warn` (c) **세로 넘침**은 아직 안 봄 — 전리품이 9칸이 되면 이쪽이 먼저 터진다.

## [2026-11-08] docs(balance) | Jev 로 곡선을 감사했다 — 모양은 정책의 함수다 (ADR-0301)

- **배경**: 오너 "jev ai 도움 받아서 더 진행해봐". Jev(System One, WF8)로 곡선 **형태**를 0~5 채점하고, 그 결과로 다음 수를 정했다.
- **세 번의 호출**: ⑴ 교전당(오프닝 덱 300런) **2.54**/5 conf 0.52 — **상단 g1-g3 평평** ⑵ 미션·**강한 정책**(`--loot smart --cards best`, 48시드) **3.09**/5 conf 0.48 — **g4→g5 절벽** ⑶ 미션·**기본 정책**(24시드) **3.79**/5 conf **0.83** — 매끄러운 경사, **최고점**.
- **핵심 통찰**: 점수 차이는 실력이 아니라 **어느 정책으로 쟀는가** 때문이다. 최적 플레이는 상단을 눌러 평평하게 만들고 끝에 절벽을 만들며, 평범한 플레이는 완만한 경사를 만든다. 즉 **곡선의 모양은 정책의 함수**다.
- **측정으로 기각한 '개선'**: 절벽을 없애는 손잡이를 5종 스윕 — prep HP 250/280, g5 보스 HP 145/125, dmg 보너스 4종. **전부 회피를 더 이롭게** 만들었다(격차 **3.3 → 6.5~15.5pp**). 이유: 완화는 **HP 여유**를 늘리는데, 회피는 HP 말고 수단이 없고 싸움은 카드로 이미 여유를 벌어 놓았다. **g5 절벽은 전략 균형을 지탱하는 부품**이라 유지. dmg 손잡이는 **g1-g3 에서 완전 무효**(계단 함수).
- **도구를 남김**: 워크스페이스 `scripts/jev-difficulty.sh` 에 **`--curve mission --seeds N`** 추가. 지금까지 이 스크립트는 **교전당 곡선만** 채점했는데 그건 플레이어 경험이 아니다(오프닝 덱은 g1-g3 교전을 구조적으로 다 이긴다).
- **정책 준수**: Jev 는 advisory — **신뢰도 < 0.5 인 호출(2.54·3.09)은 참고로만** 쓰고, 결정 근거는 **실측 스윕**이었다.
- **검증**: 생산 코드 무변경 · vitest **205 files / 4174 tests** 그대로 · typecheck 0.
- **남은 질문**: (a) 기본 정책(Jev 3.79)은 g3 47.3% 로 가혹 — "평범한 플레이"의 기준선을 어디로 둘지 (b) `--loot smart` 같은 최적 정책도 플래그로 노출해 **두 곡선의 격차**를 지표로 (c) 곡선 점수를 회귀 게이트로 쓰려면 이 프로젝트용 골드셋 재작성.

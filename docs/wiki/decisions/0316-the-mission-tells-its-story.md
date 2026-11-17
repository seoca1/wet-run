# ADR-0316: 미션은 자기 이야기를 말한다 — 파생 소설에서 브리핑을 가져온다

**상태**: Accepted
**날짜**: 2026-11-16
**결정자**: AI 위임 (오너 "추천대로 해줘" — 파생 소설 → 게임 서사 완성 A→C→B 중 A)
**우선순위**: P1 (서사 · 콘텐츠)

## 컨텍스트 (Context)

"파생 소설을 스토리에 적용"하려던 의도는 **검증됐지만 완성되지 않았다.** 실측:

| 층 | 위치 | 규모 | 게임에서 보이나 |
|---|---|---|---|
| 파생 소설 | `Fiction/derivative/` | **455 파일 · 213 미션 id** | ❌ 직접 연결 없음 |
| 그래픽 노블 프롤로그 | `web/src/data/scenes.json` | **27씬 · 15 미션** (3자키×9) | ✅ 별도 모드 |
| 게임 `story` 링크 | `missions.json` | **20 미션 (전부 far-grid)** | 🔸 허브에 `[Source: …]` **경로만** |

**가설 검증**: 그래픽 노블의 씬은 파생 소설에서 **직접 개작**됐다 — `first_jack` 의
`scene_case_intro/jackin/jackout` 이 소설 `2026-06-23_case_jackout-30sec.md` 의 문장
("Thirty seconds. The Ono-Sendai electrodes lift from my scalp…")을 그대로 쓴다.

**그러나 게임은 고른 미션의 이야기를 보여주지 않는다**:
- GN은 **캐릭터 앤솔로지**다(`loadPrologueChain` 이 자키 3명 × 최대 8씬을 시드 셔플).
  `first_jack` 을 고른 플레이어가 그 씬을 보려면 우연히 걸려야 한다.
- far-grid 의 `story` 는 허브에 `[Source: …]` **라벨**로만 표시된다(본문 없음).
- **sprawl 미션에는 브리핑조차 없다**(`briefing` 필드는 far-grid 20개뿐).

**재료는 충분하다**: sprawl 33미션 중 **32개**에 파생 소설이 있고, 그중 **166편**이
`plot_summary`(깨끗한 한 문단)를 갖는다. 요약 168건을 슬롭 마커로 스캔해 **0건**을 확인했다
(슬롭은 소설 **본문**에 있고 요약에는 없다).

## 결정 (Decision)

**파생 소설의 `plot_summary` 를 미션의 `briefing` 으로 가져오고, 미션 선택 화면이 그것을
보여준다.**

- 도구: `scripts/tools/import_briefings.py` — `game_mission_id` + `plot_summary.en` 을 읽어
  정리(따옴표/이스케이프 해제 · **중복 단어 복구** · 150자 절단 · 꼬리 잘림에 `…`) 후
  `web/src/data/missions.json` 에 `briefing` 을 쓴다. **멱등**이고 **far-grid 는 건드리지 않는다.**
- 화면: `renderMissionList(..., briefing)` 이 목록 아래에 줄바꿈해 표시한다(40열 3줄).
- 언어: `briefing_ko` 가 있으면 한국어, 없으면 영어(sprawl KO 요약은 아직 없다 — 열린 질문 (a)).

## 결과 (Consequences)

- **32개 sprawl 미션**이 이제 "무엇에 관한 미션인지"를 말한다. 예:
  - `first_jack` — "Case experiences the thirty seconds after jack-out — the shaking hands, the matrix."
  - `first_trace` — "Case takes his first real trace job for The Finn. The target is a mid-level node…"
  - `final_choice` — "Case must decide what to do with proof of Wintermute's existence. Three paths…"
- 미션 선택 화면은 **미션 목록 + 선택된 미션의 브리핑**이 된다(밸런스 무영향, 표시 전용).
- **슬롭 격리**: 요약만 가져오므로 본문의 주입 문장은 게임에 들어오지 않는다. 도구가 슬롭
  마커를 만나면 그 요약을 **버린다**.
- 검사: `check_no_novel_prose.py` 1878 문자열 0건(요약은 파생 창작이며 깁슨 원문이 아니다).
- 테스트 **212 files / 4223 tests** · e2e menu·progression 6/6.

## 열린 질문

- **(a) 한국어 브리핑.** `plot_summary.ko` 는 대부분 비어 있다(`ko: ''`). 채우려면 Fiction 쪽
  번역이 필요하다.
- **(b) 그래픽 노블을 미션에 묶기.** 이 ADR 은 A(미션→브리핑)다. GN을 "고른 미션의 씬"으로
  바꾸는 것이 **B** 이고, 아직이다.
- **(c) 고아 id 181개.** 파생 소설이 가리키는 213개 미션 id 중 게임에 존재하는 것은 **32개**뿐이다
  (`3jane_straylight`·`angie_leopard_tracking`…). 재매핑하거나 은퇴 목록화해야 한다 — **C**.
- **(d) `dixies_offer` 만 브리핑이 없다.** 그 미션의 파생 소설이 아직 없다.
- **(e) 150자 상한.** 화면이 3줄로 자른다. 더 긴 이야기를 원하면 화면을 늘려야 한다.

## Implementation Status (2026-11-16)

**Status**: ✅ Implemented

**Evidence**:
- `scripts/tools/import_briefings.py` — 생성 도구(멱등 · 슬롭 거부 · far-grid 보존)
- `web/src/data/missions.json` — `briefing` 52건(sprawl 32 신규 + far-grid 20 기존)
- `web/src/renderer/mission_select.ts` — 목록 아래 브리핑(줄바꿈, 40열 대응 힌트)
- `web/src/main.ts` — 선택 미션의 브리핑 전달
- `web/tests/adr0316_mission_briefing.test.ts` — 5 tests
- `web/tests/adr0300_no_text_is_cut_off.test.ts` — 미션 선택 3 레이아웃 가드

**Notes**: 표시 전용. 밸런스·저장 스키마 무변경.

## 관련 결정

- ADR-0213 — Far Grid 의 `story`/`briefing` 필드(이 ADR 이 sprawl 로 확장)
- ADR-0272 · ADR-0273 · ADR-0274 — 그래픽 노블 프롤로그와 런 핸드오프
- ADR-0315 — 메뉴/진행 구조(같은 서사 흐름)
- ADR-0300 — 폭 가드(미션 선택도 케이스로 추가)

## 변경 이력

- 2026-11-16: Accepted — 파생 소설 → 브리핑(A) 구현
- 2026-11-17: 브리핑이 **잘린 문장**이었다 — 도구의 150자 절단을 없애고 **문장 단위**로 바꿨다.
- 2026-11-17: **한국어 브리핑 임포트** — `plot_summary.ko` 를 **같은 이야기 파일**에서 함께 가져온다(13/33 켜짐).
- 2026-11-17: **임포트 원장**(중간 파일) 추가 — 고른 후보·지나친 후보·갈림을 기록하고 `--check` 로 검증.
  `watchdog_patrol` 의 `en` 요약 손상과 `ko` 쌍둥이의 온전한 문장이 그렇게 드러났다.
  화면도 더 이상 픽서의 말로 위장하지 않는다(`Fixer:` 표기). 아래 구현 상태 참조.

## Implementation Status (2026-11-17)

**Status**: ✅ Implemented (절단 결함 수정 포함)

**Evidence**:
- `scripts/tools/import_briefings.py` — `brief()`(문장 단위 · `MIN_LEN` 40 · `MAX_LEN` 240 · 절단 표식 없음)
- `web/src/data/missions.json` — sprawl 32/33 브리핑(`dixies_offer` 는 파생 소설 없음)
- `web/src/renderer/menu_dialogue.ts` — `renderMissionBriefing` 이 `Fixer: <이름>` 을 쓰고
  본문을 **인용하지 않는다**
- `web/src/renderer/mission_select.ts` — 3줄 미리보기가 잘리면 `…` 로 **말한다**
- `web/tests/adr0316_briefings_are_complete.test.ts` — 문장 완결성 · `…` 금지 · 3 레이아웃 폭 가드
- `web/tests/adr0316_mission_briefing.test.ts` — 옛 테스트가 **절단을 규칙으로 고정하고 있었다** →
  새 규칙으로 교체
- **`docs/design/story/briefing-ledger.json`** — **임포트 원장**(중간 파일, 40KB) · `--check` 게이트
- `web/tests/adr0316_briefing_ledger.test.ts` — 6 tests(원장↔게임 데이터 + 내부 정합성 + **ko 가 같은 이야기에서 왔는지**)

### 중간 파일 — 임포트 원장 (2026-11-17 추가)

**문제**: 이 파이프라인에는 **중간 산출물이 없었다.** `import_briefings.py` 가 파생 소설을 읽어
`missions.json` 을 **직접 덮어쓰므로**, 게임 데이터는 브리핑이 **무엇인지**만 말하고 **어디서 왔는지·
무엇을 지나쳤는지**는 말하지 않는다. 그래서:
- 150자 절단이 하루를 살았고 **옛 테스트가 그 절단을 규칙으로 고정**했다(유일한 흔적이 게임 데이터였다).
- `watchdog_patrol` 의 브리핑은 **중간 절이 없다** — 그런데 같은 미션의 `ko` 쌍둥이 요약에는 온전한
  문장이 있다. 임포터는 `**/en/*.md` 만 스캔하므로 **쌍둥이를 보지 못했고**, 후보 선택 규칙은
  "**가장 짧은 것**"이라 손상된 쪽을 골랐다.
- 후보가 갈리는 미션 **8편**(전 언어 기준 **14편**)과 다른 언어 쌍둥이가 다른 미션 **10편**이
  어디에도 적혀 있지 않았다.

**해결**: `docs/design/story/briefing-ledger.json` — 미션마다 **고른 브리핑 · 고른 원본 파일 ·
검토한 후보(en) · 스캔하지 않은 후보(다른 언어) · 갈림/쌍둥이 플래그**를 기록한다.
게임 데이터는 **건드리지 않는다**(정책 변경은 오너 결정 — 후보 선택 규칙을 바꾸면 게임 문구가 바뀐다).

**검증 2겹**:
- `import_briefings.py --check` — 원장이 디스크의 게임 데이터와 맞는지 + **다시 돌리면 같은 값인지** +
  원본 파일이 실제로 있는지. 낡은 원장은 없느니만 못하므로 **실패**한다(exit 1).
- `web/tests/adr0316_briefing_ledger.test.ts` — CI 에서 원장↔게임 데이터 일치 + 원장 내부 정합성
  (chosenFrom 이 실제 후보인지 · 플래그가 후보 목록과 맞는지) · `watchdog_patrol` 사례 고정.

**남은 결정(오너)**: 후보가 갈릴 때 **무엇을 고를지**. 지금은 "가장 짧은 것"이고, 그것이 손상된
`watchdog_patrol` 을 고른 이유다. 원장이 14편을 한 파일에 모아 주므로 검토가 가능해졌다.

### 한국어 브리핑도 같은 이야기에서 가져온다 (2026-11-17)

`plot_summary.ko` 는 원본에 이미 있었다(283 파일 중 75). 그런데 임포터가 `.en` 만 읽어서
게임의 `briefing_ko` 는 **0편**이었다 — **번역이 없던 게 아니라 가져오지 않았던 것**이다.

- **같은 파일에서 둘 다** 가져온다: 미션 id 하나를 여러 이야기가 주장할 수 있으므로
  (`aleph_fragment` 는 6 파일), `ko` 를 다른 파일에서 가져오면 **다른 이야기의 번역**이 붙는다.
- 결과 **13/33** 이 켜졌다(즉시 세 표면에 반영 — 미션 선택 미리보기 · 브리핑 화면 · `CONTRACT` 카드가
  **이미 `language === "ko"` 일 때 `briefing_ko` 를 우선**하도록 배선돼 있었다).
- **거부 1건**: `first_contact` 의 ko 는 **조각**(문장이 끝나지 않음)이라 `brief()` 가 거부했다 —
  `en` 과 같은 규칙이다. 원장의 `considered[].bodyKo` 에 원문이 남아 원본 교정 대상이 된다.
- CJK 안전 검사 통과(한자·가나 0). 한글은 캔버스가 `fillText(..., maxWidth)` 로 **한 칸에 맞춰**
  그리므로 패널을 넘지 않는다(기존 KO 동작).

**Notes**: **이 ADR 이 만든 결함**을 2026-11-17 에 발견했다. 도구가 요약을 150자에서 잘라 `…` 를
붙였고("a briefing is one line, not a paragraph"), 그래서 **32편 중 20편이 문장 중간에서 끝났다**
(`"…a secret that could bring down a mid-level…"`). 그 문장을 화면은 **픽서가 말한 것처럼**
`FINN:` 을 붙여 보여줬다 — 화면이 사실을 말하지 않았다(ADR-0251 rule 5). 이제 브리핑은 **문장
단위**(48~240자)이고, `…` 는 데이터에 **0건**이며, 미리보기가 잘리면 그 사실을 표시한다.

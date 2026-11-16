# ADR-0317: 그래픽 노블은 발판이다 — 완성 시 스토리로 녹이고 메뉴에서 지운다

**상태**: Accepted (방침 확정 · 이관은 미착수)
**날짜**: 2026-11-16
**결정자**: 사용자 ("그래픽 노블 메뉴는 검증용으로 당분간 활용. 완성 시점에서는 스토리에 모두 녹여내고 없앨거야. 프롤로그 및 이벤트에도 모두 반영해야 돼.")
**우선순위**: P1 (서사 · 구조)

## 컨텍스트 (Context)

파생 소설을 게임 서사로 옮기는 작업은 **세 표면**에서 서로 다른 성숙도로 진행돼 있다.

| 표면 | 현재 | 출처와의 연결 | 상태 |
|---|---|---|---|
| **미션 브리핑** | sprawl 32미션 | `plot_summary` → `missions.json` | ✅ **ADR-0316 완료** |
| **그래픽 노블(프롤로그)** | 메뉴 항목 + 27씬(15미션) | 씬이 소설 문장을 직접 인용 | 🟡 **검증용 발판** |
| **이벤트** | `docs/design/story/event_dialogues.json` v0.2 | `derivative_sources` 가 파생 소설을 가리킴 | 🟡 **일부 배선(3b)** |

`event_dialogues.json` 은 이미 NPC·대사·파생 소설 출처를 담고 있지만 **게임에 배선되지 않았다**
(`grep` 0건). 2026-11-16 에 **첫 비트(동료의 첫 대사)를 배선**했고 나머지 대사는 아직 데이터로만
남아 있다. 그리고 그래픽 노블은 **캐릭터 앤솔로지**(자키 3명 × 8씬 셔플)라, 고른 미션의
이야기를 보여주지 않는다.

**오너 방침**: 그래픽 노블 메뉴는 **검증용**이며, **완성 시점에는 스토리에 모두 녹여내고 없앤다.**
프롤로그와 이벤트에도 반영한다.

## 결정 (Decision)

1. **그래픽 노블 메뉴 항목은 완성 시 제거한다.** 그때까지는 검증용으로 유지하되, **새 기능을
   여기에 더 넣지 않는다** — 씬은 이관될 자산이지 확장할 화면이 아니다.
2. **씬 27개는 프롤로그와 이벤트로 분해된다.**
   - **프롤로그** = **런의 도입**. 자키 선택 뒤, 미션 선택 앞(또는 미션 선택 뒤)에 그 런의
     자키 이야기가 재생되고 **런으로 넘어간다**(ADR-0273 의 핸드오프를 정식화).
   - **이벤트** = **런 중 서사 비트**. 노드 도착·보스 진입·엔딩 등 결정적 순간에 대사가 붙는다.
3. **`event_dialogues.json` 을 배선한다.** NPC·대사·파생 소설 출처가 이미 있으므로, 데이터를
   새로 쓰는 것이 아니라 **읽는 코드를 만든다**.
4. **모든 서사 표면이 같은 출처(파생 소설)를 인용한다.** 브리핑(완료) · 프롤로그 · 이벤트 ·
   엔딩이 각자 다른 문장을 지어내지 않는다.

## 완성 시점의 구조

| 표면 | 무엇을 담나 | 출처 | 지금 |
|---|---|---|---|
| 미션 브리핑 | 이 미션이 무엇인지 한 줄 | `plot_summary` | ✅ |
| **프롤로그** | 이 런의 자키가 누구인지 (런 시작 1회) | GN 씬 + `prologue.md` | 🟡 메뉴 모드 |
| **이벤트** | 런 중 결정적 순간의 대사 | `event_dialogues.json` | 🟡 첫 잭인 + ICE 태그라인 |
| 엔딩 | 런이 어떻게 끝났는지 | `ending_resolver` + 소설 요약 | ✅ (요약 문구) |
| ~~그래픽 노블 메뉴~~ | — | — | **제거 예정** |

## 이관 경로 (순서)

1. ~~미션 브리핑~~ — **완료**(ADR-0316).
2. **프롤로그를 런에 결합** — **완료(2026-11-16)**.
3. **이벤트 배선** — 3a **완료**, 3b **첫 비트 완료 · 나머지 대사 남음**:
   - **3a 브리핑 화면** ✅(2026-11-16): 미션 선택 → **브리핑** → prep → 런. 픽서가 미션의
     이야기(ADR-0316)를 말한다. 웹에 **설계만 되고 미배선이던** `briefing` 화면과
     `renderBriefingScreen`(Finn 사무실)을 실제로 연결했다.
   - **3b `event_dialogues.json`** 🟡(2026-11-16): 데이터를 앱으로 들여오고(`import_event_dialogues.py`)
     **동료의 첫 대사**(런 인트로 카드)와 **ICE 태그라인**(교전 화면, 정체를 본 뒤)을 배선했다.
     나머지 대사는 트리거 매핑 결정이 필요하다(열린 질문 f).
4. **메뉴 항목 제거** — 3b 가 끝나면 `graphic_novel` 항목과 화면을 지운다(ADR-0315 의 노출
   규칙에서도 빠진다).

### 이관 2단계 결과 — 프롤로그가 런의 첫 비트가 됐다 (2026-11-16)

```
NEW RUN → 자키 선택 → [그 자키의 프롤로그] → 미션 선택 → prep → 런
                         ↑ ESC = 이야기만 건너뛰고 런은 계속
```

- 자키 선택의 `confirm` 이 이제 **프롤로그를 연다**(`initGraphicNovel(자키 id)`), 그 뒤 미션
  목록으로 넘어간다. 예전에는 곧바로 미션 목록이었다.
- **ESC 는 이야기만 건너뛴다** — `prologueForRun` 플래그가 `exitGraphicNovel` 을 미션 목록으로
  보낸다(메뉴로 튕기지 않는다). 완주하면 `startRunFromGraphicNovel()` 이 그대로 잇는다.
- **메뉴의 GRAPHIC NOVEL 은 그대로 둔다**(검증용) — 거기서는 ESC 가 타이틀로 돌아간다.
  `prologueForRun = false` 로 구분한다.
- GN 모드 선택 화면은 웹에 없다(`"novice"` 하드코딩이었다) → 자키 id 를 그대로 모드로 쓴다
  (`novice`/`veteran`/`heretic`).
- e2e: `e2e/prologue.spec.ts` — ⑴ NEW RUN → 자키 → 프롤로그 → ESC → 미션 목록, ⑵ 메뉴 GN 은
  ESC 로 타이틀(런 아님). 기존 스펙들은 `openMissionSelect` 헬퍼가 프롤로그를 건너뛴다.

### 이관 3a 결과 — 브리핑 화면이 배선됐다 (2026-11-16)

```
미션 선택 → [브리핑: 픽서가 미션의 이야기를 말한다] → prep → 런
              ↑ ENTER 계속 · ESC 목록으로
```

- 웹에는 **설계만 되고 배선되지 않은** 서사 표면이 셋 있었다: `screen: "briefing"`(ScreenKind),
  `renderBriefingScreen`(Finn 사무실), `DIALOGUE_TREES` 엔진. 이 중 **브리핑 화면**을 연결했다.
- 새 렌더러 `renderMissionBriefing` 은 **줄바꿈**하고 **동작하는 키만 약속**한다(ADR-0251 rule 5).
  기존 `renderBriefingScreen` 은 대사를 가운데 정렬로 잘라내고 40열에서 넘쳤다.
- **`SCREENS_WITH_INPUT` 에 `briefing` 을 등록**했다 — 이 등록을 빠뜨리면 ENTER 가 메뉴로 튕긴다
  (ADR-0273/0275 의 함정).
- e2e: `launchRun` 헬퍼와 소크 `startRun` 이 브리핑을 거치도록 수정. **소크와 idle_alarm 이
  실제로 실패해서** 드라이버 누락을 잡았다.

### 이관 3b 결과 — 동료가 첫 잭인에서 말을 건다 (2026-11-16)

```
미션 선택 → 브리핑 → prep → [런 인트로 카드: 이 아크의 틀 + 동료의 첫 대사] → 매트릭스
                                                        ↑ 아무 키나 누르면 사라진다
```

- **데이터를 들여왔다**: `scripts/tools/import_event_dialogues.py` 가
  `docs/design/story/event_dialogues.json`(v0.2) → `web/src/data/event_dialogues.json` 으로
  **게임이 읽는 필드만** 복사하고, **닿을 수 없는 대사 id 를 보고**한다(`ice_hammer_intro` 는
  그런 ICE 가 없다). 설계 파일이 계속 단일 진실 공급원이다.
- **한 곳에서만 id→대사**: `web/src/core/state/event_beats.ts` 의 `dialogueBeat(id, lang)` ·
  `runOpeningBeat(finishedRuns, lang)`. 화면이 데이터와 어긋날 수 없다.
- **런 인트로 카드가 동료를 말한다**: `renderRunIntro` 가 선택적 `beat` 를 받아 아크의 틀 문장
  아래에 **발화자 + 대사**를 렌더한다(동료는 cyan). 3줄로 제한 — 카드는 대화가 아니다.
- **프로필당 한 번**: `runsFinished === 0` 일 때만. 런을 끝낸 프로필은 이미 그녀를 만났고,
  CONTINUE 로 이어가는 런은 도입을 다시 재생하지 않는다(ADR-0272 와 같은 규칙).
- **언어 인식**: `language === "ko"` 면 `text_ko`/`speaker_ko`, 없으면 줄 단위로 영어로 폴백.
- **표시 전용**: `GameState` 를 건드리지 않는다. 밸런스/생존 곡선은 **byte-identical**
  (교전당 `100/100/100/98.9/83.9/32.3` · 미션 `100/97.1/75.9/51.4/26.9/32.3`).
- e2e: `web/e2e/run_intro.spec.ts` — ⑴ 새 프로필은 동료를 듣는다, ⑵ 런을 끝낸 프로필은
  다시 듣지 않는다. (읽기 전용 훅 `getRunIntroBeat()`)

### 이관 3b 결과 — ICE가 자기 태그라인을 말한다 (2026-11-16)

```
[교전 화면]  PROBE / SCAN 으로 정체를 보는 순간 → 그 ICE가 방송을 흘린다 (프로필당 1회)
```

- **매핑이 자명한 유일한 조각**: 대사 id 가 `ice_<카탈로그 id>_intro` 다. ICE 의 **자기 id**가
  곧 열쇠라 맞출 표가 없다. 대부분의 ICE 는 설계대로 **침묵**하고(`null`), 태그라인이 있는
  것만 말한다(`wisp` · `black`).
- **정체를 본 뒤에만 말한다**: ICE 의 정체는 **PROBE 가 파는 정보**다. 태그라인이 먼저 나오면
  그 정보를 공짜로 흘리게 된다 — 그래서 **PROBE/SCAN 으로 정체가 드러난 순간**에만 목소리가
  나온다. (덤: PROBE 의 값이 "수치를 본다"에서 "그것이 무엇인지 듣는다"로 선명해진다.)
- **프로필당 한 번**: 들은 id 를 `wetrun_ice_intro_seen`(JSON 배열)에 기억한다. 저장이
  막히거나 값이 깨져도 **"아직 못 들음"으로 물러설 뿐**, 렌더 프레임을 깨뜨리지 않는다.
- **여러 목소리 처리**: `ice_black_intro` 는 Black ICE·내레이터·딕시가 차례로 말한다.
  한 목소리면 발화자를 **머리말**로 한 번, 여러 목소리면 **줄마다 자기 이름**을 붙인다 —
  줄이 엉뚱한 화자에게 귀속되지 않는다.
- e2e: `web/e2e/ice_voice.spec.ts` — PROBE 가 태그라인을 기억하는지(단위 테스트가 못 보는 배선).
- **남은 것**: `dixie_warning`(첫 ICE 경고) · `dixie_postcombat`(전투 후) · 엔딩 대사 ·
  허브/메타 대사(`finn`·`wim`·`maelcum`·`ta`)와 **4단계(메뉴 제거)**. **단, 남은 대사들은
  트리거가 게임과 1:1로 맞지 않아 매핑 결정이 필요하다**(아래 열린 질문).

## 결과 (Consequences)

- **지금 바뀌는 것**: 없음(방침 기록). 그래픽 노블 메뉴는 계속 보인다 — 검증용.
- **앞으로의 제약**: 그래픽 노블 화면에 **새 기능을 넣지 않는다**. 씬 데이터는 이관 대상이므로
   `scenes.json` 을 고칠 때는 프롤로그/이벤트에서의 쓰임을 함께 본다.
- **ADR-0315 와의 관계**: 메뉴 노출 규칙에서 `graphic_novel` 은 "항상"이다. 완성 시 이 항목이
  사라지므로, 그때는 규칙에서도 제거한다(지금은 유지).

## 열린 질문

- **(a) 프롤로그의 트리거.** 자키 선택 직후(런 전) vs 미션 선택 후(그 미션에 맞춰)? 지금은
  메뉴 모드에서 자키별로 재생된다.
- **(b) 이벤트의 조건.** 노드 도착마다? 보스 진입만? 빈도가 높으면 읽기를 방해한다.
- **(c) 씬 27개의 이관 매핑.** 15미션 × (인트로/잭인/잭아웃/핀) 구조를 프롤로그/이벤트로
  나누는 표가 필요하다.
- **(d) `prologue.md` 의 깁슨 인용.** 그 문서는 원문 첫 문장을 인용한다. **게임 문자열에는
  금지**(ADR-0270, `check_no_novel_prose.py`). 이관 시 패러프레이즈한다.
- **(e) KO.** `plot_summary.ko`·씬 `title_ko` 는 부분적이다. 이관과 함께 채울지 별도로 볼지.
- **(f) 남은 대사의 트리거 (2026-11-16 실측).** 나머지 대사는 게임과 1:1로 맞지 않는다:
  `dixie_warning` 은 **Wisp 를 지목**하는데 첫 ICE 가 Wisp 라는 보장이 없고, 엔딩 대사는
  **novice 전용 + 데이터를 태우냐/가지냐**를 전제하는데 게임의 엔딩 id 는 `arc*` 다.
  허브/메타 대사(`finn_intro`·`wim_hub`·`maelcum_*`·`ta_warning`)는 **대화 트리 화면**이
  필요한데 `DIALOGUE_TREES` 는 여전히 미배선이다. → **일반화해서 다시 쓰거나, 대사에 맞춰
  트리거를 만들거나, 그대로 두거나** — 오너 결정.

## Implementation Status (2026-11-16)

**Status**: 🟡 Partial (이관 1·2·3a ✅ · 3b 일부 · 4 ❌)

**Evidence**:
- `web/src/renderer/menu_dialogue.ts` — `renderMissionBriefing`(줄바꿈 · 정직한 footer)
- `web/src/renderer/run_intro.ts` — `renderRunIntro(..., beat)`(아크 틀 + 동료의 대사)
- `web/src/core/state/event_beats.ts` — `dialogueBeat` · `runOpeningBeat` · `iceIntroBeat`
- `web/src/core/state/ice_intros.ts` — 들은 ICE 태그라인 기억(`wetrun_ice_intro_seen`)
- `web/src/renderer/encounter.ts` — 교전 화면이 `iceVoice` 를 렌더
- `web/src/data/event_dialogues.json` — 앱이 읽는 사본(설계 파일에서 복사)
- `scripts/tools/import_event_dialogues.py` — 설계 → 앱 복사 + 닿을 수 없는 id 보고
- `web/src/main.ts` — `briefing` 화면 흐름 · `SCREENS_WITH_INPUT` 등록 · `initGraphicNovel(mode)` ·
  `prologueForRun` · `runIntroBeat` · `encounterVoice()` · `getRunIntroBeat()`
- `web/tests/adr0317_mission_briefing_screen.test.ts` — 4 tests
- `web/tests/event_beats.test.ts` — 8 tests
- `web/tests/ice_intros.test.ts` — 5 tests
- `web/tests/adr0317_ice_voice.test.ts` — 4 tests
- `web/e2e/prologue.spec.ts` — 2 tests(런 프롤로그 / 메뉴 GN)
- `web/e2e/run_intro.spec.ts` — 2 tests(첫 잭인 / 두 번째 런)
- `web/e2e/ice_voice.spec.ts` — 1 test(PROBE 가 태그라인을 기억)
- `web/e2e/menu-nav.ts` — `openMissionSelect`·`launchRun` 이 프롤로그·브리핑을 건너뛴다

**Notes**: 이관 3b 는 **첫 잭인 + ICE 태그라인**까지. 남은 대사는 **매핑 결정**이 필요하다
(열린 질문 f). 4(메뉴 제거)는 그 뒤다.

## 관련 결정

- ADR-0316 — 미션 브리핑(이관 1단계, 완료)
- ADR-0272 · ADR-0273 · ADR-0274 — 프롤로그 재생과 런 핸드오프
- ADR-0032 — 그래픽 노블 모드(원 설계, 메뉴 모드)
- ADR-0315 — 메뉴 노출 규칙(완성 시 `graphic_novel` 제거)
- ADR-0270 — 원작 문구 금지(이관 시 패러프레이즈)

## 변경 이력

- 2026-11-16: Accepted — 오너 방침 기록 + 이관 경로 정의
- 2026-11-16: 이관 3b(첫 비트) — 동료의 첫 대사를 런 인트로 카드에 배선 · 데이터 임포터 추가
- 2026-11-16: 이관 3b(ICE 태그라인) — 교전 화면이 정체를 본 뒤 ICE 의 방송을 말한다(프로필당 1회)

# ADR-0253: 사운드 자산 4세대 중복 제거 — 대시보드 참조 정합

**상태**: Accepted
**날짜**: 2026-11-02
**결정자**: 사용자 (프로젝트 오너) — 워크스페이스 경로·자산 정리 세션에서 4개 옵션 제시 후 선택
**우선순위**: P2 (The Build — 자산·문서 정합; 게임 메커닉 무관)
**관련**: [ADR-0195 — 구현 상태 기록](./0195-adr-implementation-workflow.md) · [ADR-0233 — 오디오 ducking + SFX rate 변조 + 마스터 볼륨](./0233-audio-ducking-master-volume.md) · [ADR-0251 — 진실한 프로그램 어포던스](./0251-truthful-program-affordance-and-combat-integrity-rules.md) · [ADR-0252 — 세이브는 확정된 상태를 담고](./0252-run-end-and-save-timing.md)

> **이 ADR은 게임 메커닉·밸런스·상태 스키마를 바꾸지 않는다.** 오디오 파일 중복과 대시보드 문서의
> 죽은 경로 참조만 다룬다. `web/` 코드는 무변경이다.

## 컨텍스트 (Context)

워크스페이스 경로·자산 정리 감사에서 `Game/wet_run` repo의 사운드 자산이 **4세대로 중복**되어 있고,
대시보드 HTML 4개가 **폐기된 Python 프로토타입 경로**와 **존재하지 않는 파일**을 가리키고 있음이 확인됐다.

### 1. 사운드 자산 4세대 중복 — 263 MB (tracked 72 파일)

`docs/dashboard/sounds/` 안에 같은 12개 테마가 서로 다른 포맷·세대로 네 번 들어 있었다.

| 세대 | 파일 | 크기 | 참조 실측 |
|---|---|---|---|
| root `theme_X.wav` (v1 트랜스코딩 원본) | 12 | 60.6 MB | `sound.html` Themes 플레이어만 (`SOUNDS_BASE + "theme_X.wav"`) |
| root `*.v1_backup.wav` | 12 | 10.6 MB | **0** — `docs/dashboard/scripts/import_minimax_track.sh` 의 생성 산물 |
| root `*_v1_orig.wav` | 1 | 0.5 MB | **0** |
| `full/theme_X.mp3` (A 버전) | 12 | 80.6 MB | `sound.html` 전체 트랙 갤러리 + `web/public/sounds/theme_*.mp3` **tracked 심볼릭 링크 5개**의 대상 |
| `full/theme_X_full_m/_f.mp3` (F/M 버전) | 12 | 73.5 MB | `sound.html` 전체 트랙 갤러리만 (게임 로직 미사용) |
| `v2/*.wav` | 23 | 37.0 MB | `docs/dashboard/tier5.js` (`sounds/v2/`) |

F/M 변형은 A 버전과 **길이 자체가 다른 별개 리퀴즈**였다 (예: `matrix_rain` A=261.6초 vs F=192.2초).
`v2/click.wav` 는 `web/public/sounds/sfx/click.wav` 와 byte-identical이었다.

결과적으로 `Game/wet_run/.git` 274 MB 중 **263 MB가 오디오**였고, 그중 절반은 중복이었다.

### 2. 대시보드의 죽은 경로·유령 자산

`docs/dashboard/` HTML 4개가 2026-09-15에 폐기된 Python 프로토타입을 기술하고 있었다.

| 파일 | 문제 |
|---|---|
| `sound.html` | `SoundCategory` (코드에 존재하지 않음), `toggle_category()` API, `afplay/aplay`, `src/wet_run/audio/`, "6 카테고리 · 46 사운드", Overview/Categories/Sound Files 절 전체가 폐기 시스템 |
| `combat.html` | `combat_hit_normal` 등 **존재하지 않는 SFX 12종** (`web/public/sounds/combat_hit_*.wav`), `src/wet_run/combat/*.py` 6곳, `data/combat/ice_types.json` |
| `cyberspace.html` | `data/cyberspace/worlds.json` (repo 전체에 부재), `src/wet_run/matrix/`, `prototype/src/wet_run/matrix/` |
| `settings.html` | `src/wet_run/settings.py` 2곳, "6 카테고리, 30+ 설정" (현행 12 필드) |

실측 대조 결과 현행 구현은 `web/src/audio/manager.ts` (`AudioManager` 싱글턴, Howler.js),
`web/src/audio/index.ts` (공개 facade), `web/src/core/sound_system.ts` (`TRACKS` 15종 + `TRANSITION_RULES` 15종),
`web/src/renderer/settings.ts` (`SettingsField` 12종)였다. 실제 자산은 **BGM 20 + SFX 24 = 44개**였다.

### 3. `.gitignore` 의 옛 경로 규칙

`dashboard/sounds/*.v1_backup.wav`, `prototype/.venv-311/`, `data/sounds_test/` — 2026-10-20 이전
경로 규칙이 남아 있어 현재 트리에 효과가 없었다.

## 고려한 옵션

### Option 1: 현행 유지 (중복 그대로)

- **설명**: 아무것도 하지 않는다.
- **단점**: `wet_run/.git` 274 MB 유지. 대시보드는 계속 죽은 경로를 안내한다. clone 마다 263 MB 오디오 다운로드.

### Option 2: A 버전 1세대만 유지 + 대시보드 참조 통합 — **선택**

- **설명**: 정본 사운드 세트를 `docs/dashboard/sounds/full/theme_X.mp3` (12개) 하나로 확정한다.
  v1 원본 WAV는 로컬 보관 (git 제외), F/M 변형·백업은 삭제한다.
  대시보드는 `sound.html` 의 모든 오디오 참조(Themes 플레이어·갤러리·Reference 카드)를 `full/*.mp3` 로 통일하고,
  나머지 HTML 3개는 실제 `web/` 경로로 교체한다. 폐기된 절은 삭제하지 않고 **"retired" 로 표기**한다.
- **장점**:
  - tracked 오디오 **263 MB → 117.5 MB (-145.5 MB)**, 파일 72 → 35
  - 대시보드가 실제 자산만 안내 (단일 정본)
  - `web/public/sounds/theme_*.mp3` 심볼릭 링크 5개는 `full/` A 버전을 가리키므로 **무변경**
  - clone 크기 감소
- **단점**:
  - F/M 변형(별개 리퀴즈) 12개가 갤러리에서 사라진다 — 데모 페이지의 오디오 선택지가 24 → 12 로 줄어든다
  - v1 원본 WAV는 clone 에 없어 재트랜스코딩이 필요하면 로컬 복제본에 의존해야 한다
- **Pillar 정합**:
  - P1 (The Run): 중립
  - P2 (The Matrix): 중립
  - P3 (The Flatline): 중립
  - P4 (The Build): ✅ (자산 정합·저장소 위생 — 이 ADR 의 주 목적)
  - P5 (The Style): 중립

### Option 3: 사운드 자산을 `web/public/sounds/` 로 완전 이전

- **설명**: `docs/dashboard/sounds/` 를 통째로 없애고 게임 자산 디렉터리로 통합한다.
- **장점**: 자산 위치가 게임 코드와 일치.
- **단점**: `docs/dashboard/` 가 파생 콘텐츠 canonical 이라는 규약(AGENTS.md §2) 을 깨고,
  대시보드가 `web/` 밖에서 실행될 때 (정적 배포) 상대 경로가 깨진다. 게임 자산과 데모 자산의 분리 원칙도 무너진다.

## 추천 (Recommendation)

**Option 2.** 정본을 `docs/dashboard/sounds/full/` 로 확정하고, 모든 대시보드 참조를 그쪽으로 통일한다.
게임은 이미 `web/public/sounds/theme_*.mp3` 심볼릭 링크로 같은 파일을 참조하므로 **게임 쪽 변경은 0** 이다.

## 사용자 결정 (Decision)

[x] **Option 2** — A 버전 1세대만 유지 + 대시보드 참조 통합
[ ] Option 1
[ ] Option 3
[ ] 기타: ___
[ ] Defer

## 결과 (Consequences)

### 자산

- `docs/dashboard/sounds/full/*_full_m.mp3` · `*_full_f.mp3` 12개 삭제 (73.5 MB)
- `docs/dashboard/sounds/*.v1_backup.wav` 12개 삭제 (10.6 MB)
- `docs/dashboard/sounds/*_v1_orig.wav` 1개 삭제 (0.5 MB)
- `docs/dashboard/sounds/theme_*.wav` 12개 (60.6 MB) → **git 제외, 로컬 보관**.
  `.gitignore`에 앵커 규칙 `/docs/dashboard/sounds/theme_*.wav` 추가 —
  `sounds/v2/` 와 `sounds/full/` 에는 영향 없음을 `git check-ignore -v` 로 확인했다.
- 정본: `docs/dashboard/sounds/full/theme_X.mp3` 12개 (80.6 MB) + `docs/dashboard/sounds/v2/` 23개 (37.0 MB) — **무변경**

### 대시보드

- `sound.html` — F/M 변형 12블록 제거, 배지 "2 variants" → "1 variant" 12건,
  설명 "두 가지 변형 모두 사용 가능." → "단일 원본 변형." 12건.
  Themes 플레이어·Reference 카드의 파일 경로 `theme_X.wav` → `full/theme_X.mp3` 24건.
  Overview 스탯을 실측값(44 assets / 20 BGM / 24 SFX / 15 자동 전환 / 3단 볼륨)으로 교체.
  Key Bindings 표를 `SoundCategory` 8행 → 실제 전역 `M` 키 mute + SETTINGS 볼륨 필드 7행으로 교체.
  Engine Integration 표를 Python 모듈 9행 → `web/` 모듈 4행으로 교체.
  폐기 구간(Categories · Sound Files)에는 "⚠️ retired 2026-09-15" 표기 + 안내 배너 추가.
- `combat.html` — Combat Sounds 표를 유령 SFX 12행 → 실제 전투 SFX 15행
  (`COMBAT_SFX_IDS` 기준 · BGM duck 여부 표시 · 실제 파일 크기 표기) 로 교체.
  `src/wet_run/combat/*.py` 6곳 + `data/combat/ice_types.json` → 실제 `web/` 경로로 교체.
- `cyberspace.html` — `data/cyberspace/worlds.json` (부재) → `docs/dashboard/data/cyberspace_stats.json`,
  `src/wet_run/matrix/` → `web/src/core/dungeon/matrix.ts`.
- `settings.html` — `src/wet_run/settings.py` → `web/src/renderer/settings.ts`, "6 카테고리, 30+ 설정" → 12 필드 실측.

### 결정되지 않은 잔여 (후속 필요)

- **`Game/dashboard/scripts/aggregate-stats.mjs` 가 옛 경로를 가리킴** —
  `Game/wet_run/dashboard/data/...` (2026-10-20 이전 경로). 이 repo 는 별도 git repo 라 본 ADR 범위 밖.
  `docs/dashboard/data/*.json` 재생성 파이프라인은 현재 끊긴 상태로 추정된다 — 별도 세션 필요.
- **`docs/dashboard/sound.html` 의 Categories · Sound Files 절** — "retired" 표기만 하고 내용은 그대로 뒀다.
  실제 `web/` 기준으로 전면 재작성하는 것은 별도 세션 작업이다.

## Implementation Status (2026-11-02)

> **ADR-0195** ([./0195-adr-implementation-workflow.md](./0195-adr-implementation-workflow.md)): Accepted 시점에 Implementation status 결정 필수.

**Status**: ✅ Implemented

**Evidence**:
- `docs/dashboard/sounds/full/` — 12개 mp3 남음 (삭제 12개), tracked 오디오 72 파일 / 263.0 MB → 35 파일 / 117.5 MB (**-145.5 MB**)
- `docs/dashboard/sounds/theme_*.wav` 12개 — 로컬 보관 확인 (디스크에 존재), `git check-ignore -v` 로 `/docs/dashboard/sounds/theme_*.wav` 규칙 적용 확인, `docs/dashboard/sounds/v2/theme_chiba.wav` · `docs/dashboard/sounds/full/theme_chiba.mp3` 는 ignore **안 됨** 확인
- `web/public/sounds/theme_{broadcast,chiba,industrial,matrix_rain,sense_net}.mp3` — tracked symlink 5개 전부 resolve (`→ ../../../docs/dashboard/sounds/full/*.mp3`)
- `web/src/audio/manager.ts` 의 BGM 참조 5종 (`sounds/theme_{chiba,sense_net,matrix_rain,broadcast,industrial}.mp3`) — resolve 확인
- `docs/dashboard/sound.html` — 오디오 참조 12개 전부 실재 확인 (`sounds/full/theme_*.mp3`), 잔여 `.wav` 참조 0, `SoundCategory`·`afplay`·`aplay`·`toggle_category`·`adjust_volume`·`_full_` 잔여 0 (폐기 안내 배너의 `src/wet_run/audio/` 표기 1건만 잔존 — 의도됨)
- `docs/dashboard/*.html` — `src/wet_run` · `prototype/src` 잔여 0 (전 22개 HTML 스캔)
- `docs/dashboard/combat.html` — Combat Sounds 표 참조 파일 15개 전부 실재 확인
- `web/` 검증: `npm run typecheck` 0 에러 · `npm test` **175 files / 3932 tests passed** (ADR-0252 베이스라인과 동일 — 무회귀) · `npm run build` PASS
- `web/` 소스 무변경 (`git status` — `web/` 하위 변경 0)

**Notes**:
- 게임 런타임 자산 경로는 **무변경**이다. `web/public/sounds/` 의 tracked symlink 5개가 삭제된 파일을 가리키지 않는다.
- v1 원본 WAV 12개는 clone 에 포함되지 않는다. 재트랜스코딩이 필요하면 로컬 보관본을 사용한다.
- F/M 변형은 별개 리퀴즈였으므로, 복원이 필요하면 `backup/asset-dedup-2026-11-02` 브랜치에서 되살릴 수 있다.
- 본 ADR 은 `web/` 코드·테스트·밸런스를 건드리지 않는다 (균형 drift 0).

## 영향 받는 항목

- `docs/dashboard/sound.html` · `docs/dashboard/combat.html` · `docs/dashboard/cyberspace.html` · `docs/dashboard/settings.html`
- `docs/dashboard/sounds/` (정본 `full/` + `v2/`), `.gitignore`
- `web/public/sounds/` — 무변경 (symlink 5개 대상 유지)
- `web/` — 무변경

## 관련 결정

- ADR-0195 (구현 상태 기록) — 본 ADR 의 Implementation Status 형식 근거
- ADR-0233 (오디오 ducking) — `COMBAT_SFX_IDS` 9종이 `combat.html` 표의 duck 표시 기준
- ADR-0250 · ADR-0251 · ADR-0252 — sibling (같은 날짜 세션)

## 변경 이력

- 2026-11-02: Draft 작성
- 2026-11-02: Accepted (Option 2) — 오너 선택, 구현 완료
- 2026-11-02: `0250-encounter-gate-on-entry.md` 의 깨진 링크 `./0236-accessibility-and-motion.md` → `./0236-accessibility-modes.md` 수정 (실파일명 `0236-accessibility-modes.md`)

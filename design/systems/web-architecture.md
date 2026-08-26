# Web Architecture (wet_run-web)

> **상태**: Living doc — updated 2026-08-27 (v1.4.0 + Tier 4 + ADR-0209)
> **상위 결정**: [ADR-0199](../../decisions/0199-wetrun-web-mvp.md) (Tier 1), [ADR-0207](../../decisions/0207-wetrun-web-tier4-sfx-animation-glyphs.md) (Tier 4), [ADR-0209](../../decisions/0209-wetrun-web-idb-save-backend.md) (IDB)
> **관련**: [version-status.md on GitHub](https://github.com/seoca1/wet-run/blob/main/docs/version-status.md), implementation plan (local-only, gitignored)

이 문서는 `wet_run-web` (브라우저 MVP) 의 아키텍처를 정리한다. Python 데스크탑 게임과 별도의 트랙이지만, 동일한 게임 디자인을 공유한다. 명명 규칙/릴리스 사이클은 `docs/version-status.md` 참조.

---

## 1. 트랙 개요

| 항목 | 값 |
|---|---|
| 위치 | `wet_run-web/` |
| 언어 | TypeScript 5.5 + Vite 5 |
| 렌더링 | Canvas2D ASCII (Gibson palette) |
| 사운드 | Howler.js (BGM + SFX) |
| 빌드 | Vite → static files → GitHub Pages |
| Live URL | <https://seoca1.github.io/wet-run/wetrun-web/> |
| 현재 | Tier 4 + ADR-0209 IDB (2026-08-27) |

---

## 2. Tier 시스템 (ADR-0199)

### 2.1 정의

`Tier` 는 **기능 진척 단계**의 단위. SemVer 미사용. 각 Tier는 사용자 행동 가능 기능을 확장한다.

| Tier | 날짜 | 핵심 |
|---|---|---|
| Tier 1 (MVP) | 2026-08-25 | 미션 선택 → 1 전투 → 승리 |
| Tier 2a | 2026-08-25 | Multi-slot save (4 slots: 1 auto + 3 manual) |
| Tier 2b | 2026-08-26 | Howler.js BGM (단일 BGM, M 토글) |
| Tier 2c | 2026-08-26 | Mission + ICE 다양성 (15+12 Gibson-flavor) |
| Tier 3 | 2026-08-26 | 30+30 미션/ICE expansion (T1-T5, 6 zones) |
| Tier 4 | 2026-08-26 | SFX + Animation VFX + Status effect glyphs |
| **Tier 5+** | (deferred) | State machine 통합, fade, save 압축, volume slider |

### 2.2 Tier 외 표기

- **ADR-0208** (2026-08-26): Mission `random_weight` field
- **ADR-0209** (2026-08-26): IndexedDB save backend (Tier 3 literal "cloud save sync"의 on-ramp)

---

## 3. 저장 아키텍처 (ADR-0209)

### 3.1 두 백엔드

`save/strorage.ts` 가 두 백엔드를 추상화한다.

| 백엔드 | 역할 | 사용 시점 |
|---|---|---|
| **IndexedDB** (`storage_idb.ts`) | Primary. 비동기 I/O, 5MB+ 용량 | 일반 사용자 (production) |
| **localStorage** (`storageLegacy`) | 폴백 + 마이그레이션 소스 | IDB unavailable (테스트, 일부 브라우저) |

### 3.2 API

```ts
// async (since ADR-0209)
async function save(slot: number, data: SaveSlot): Promise<void>
async function load(slot: number): Promise<SaveSlot | null>
async function clear(slot: number): Promise<void>
async function listSlots(): Promise<readonly SlotMeta[]>
```

### 3.3 Lazy Migration

첫 `load()` 시:
1. `idbGet(slot)` → null이면 `loadLegacy(slot)` 시도
2. legacy 데이터 발견 시 `idbPut(slot, json)` 복사 + `localStorage.removeItem(LEGACY_KEY)` 정리
3. 이후 호출은 IDB만 사용

이 패턴은 기존 사용자 데이터를 **무손실** 으로 새 백엔드로 이전한다.

### 3.4 IDB 스키마

- DB: `wetrun_save_v1` (version 1)
- Store: `slots` (keyPath: `name`)
- Key: `slot_${0..3}` (4 슬롯: auto + 3 manual)
- Value: `{ slot: number, json: string }` (JSON 직렬화)

---

## 4. 반응형 레이아웃 (2026-08-27)

### 4.1 결정

`core/layout.ts` 가 viewport 기반 그리드 사이징을 결정한다.

| Viewport | Orientation | Grid (cols × rows) | HUD |
|---|---|---|---|
| < 480px (iPhone 14 = 390px) | Portrait | 40×60 | 16 |
| 480-768px (large phone) | Portrait | 50×80 | 20 |
| 480-768px (landscape) | Landscape | 80×50 | 28 |
| ≥ 768px (desktop) | Landscape | 80×50 | 28 |

### 4.2 Orientationchange Listener

`watchLayout()` 가 `resize` + `orientationchange` 이벤트를 구독한다. layout 카테고리 변경 시 `resizeGrid()` + `draw()` 자동 호출.

### 4.3 Canvas DPR

`devicePixelRatio` 를 적용해 retina/HDR 디스플레이에서 sharp rendering 보장. Backing store는 DPR 배율, CSS 크기는 grid 사이즈 그대로.

```ts
this.canvas.width = Math.round(cssWidth * this.dpr);
this.canvas.height = Math.round(cssHeight * this.dpr);
this.canvas.style.width = `${cssWidth}px`;
this.canvas.style.height = `${cssHeight}px`;
```

### 4.4 가상 게임패드

`vw/vh` 기반 비례 위치 (640×400 px 고정 좌표 미사용).

- D-pad: 좌하단 18vw/75vh, 12vw 정사각형
- A/B 버튼: 우하단 82vw/75vh
- Program row (combat only): 화면 하단 중앙, 5+ 핸드 카드 버튼

---

## 5. E2E 검증 (2026-08-27)

### 5.1 Playwright 인프라

- `@playwright/test` 1.62.1 (chromium only)
- 두 프로젝트: `desktop-chromium` + `mobile-portrait-chromium` (Pixel 5 에뮬레이션)
- `playwright.config.ts`: `baseURL` 은 `https://seoca1.github.io/wet-run/wetrun-web/` (라이브 검증)

### 5.2 테스트 종류

| 종류 | 명령 | 검증 |
|---|---|---|
| Unit | `npm test` | reducer, layout, vfx, storage, audio, touch, missions (106 tests) |
| E2E | `npm run e2e` | desktop + mobile, smoke + progression regression (6 tests) |
| Smoke | `npm run smoke` | 배포 도달성 + canvas mount + JS 에러 0 |
| Build | `npm run build` | 타입 체크 + 번들 (134 KB) + Pages 자동 배포 |

### 5.3 핵심 회귀 테스트

`e2e/progression.spec.ts`: 메뉴 → 접근 → 전투 → 승리 전체 흐름을 digit-key (1-9) 로 검증. 2026-08-27 "전투 정체" 버그를 정확히 잡아내는 테스트. 향후 use_program 입력 경로 회귀 시 즉시 감지.

---

## 6. 단축키 매핑 (2026-08-27)

### 6.1 키보드

| Key | Action |
|---|---|
| Arrow keys | 미션 선택 이동 |
| Enter / Space | 확인 / launch |
| 1-9 | 핸드 인덱스로 프로그램 선택 (use_program) |
| Escape | 취소 / 뒤로 |
| Q | Jack out |
| M | BGM + SFX mute 토글 |

### 6.2 터치 게임패드

| 위치 | 동작 |
|---|---|
| D-pad ↑↓←→ | 이동 / 선택 |
| A 버튼 | 확인 |
| B 버튼 | 취소 |
| Program row (combat only) | 핸드 카드 탭 → use_program |

---

## 7. 한계 (Out of Scope, Web Track)

- Cloud save (Firebase/Supabase/WebDAV) — ADR-0209는 local IDB만
- Multiplayer
- Graphic Novel mode (Python에는 있음)
- Main menu 7-8 옵션 (Python에는 있음) — 현재 mission select만
- 사망 / 리셋 사이클 (Python: DEATH_SUMMARY → HALL_OF_DEAD)
- 인벤토리 / 제작 UI (Python: HUB panel)
- 사이드 콘텐츠 (achievements, settings, news)

---

## 8. References

- `decisions/0199-wetrun-web-mvp.md` (Tier 1)
- `decisions/0201-wetrun-web-howler-audio.md` (Tier 2b BGM)
- `decisions/0202-wetrun-web-tier2c-mission-ice-expansion.md`
- `decisions/0203-wetrun-web-tier3-mission-ice-expansion.md`
- `decisions/0207-wetrun-web-tier4-sfx-animation-glyphs.md` (Tier 4)
- `decisions/0208-mission-random-weight-adr.md` (Python 미션 가중치)
- `decisions/0209-wetrun-web-idb-save-backend.md` (IDB)
- `docs/version-status.md` (버전 비교)
- `SESSION_REPORT_2026-08-26.md` (Operational Release)
- `e2e/progression.spec.ts` (회귀 테스트)
- `e2e/smoke.spec.ts` (배포 검증)
# ADR-0209: wet_run-web IndexedDB Save Backend (Tier 3 literal partial)

**상태**: **Accepted (Option 1: IDB-first with localStorage fallback)** — 2026-08-26
**날짜**: 2026-08-26
**결정자**: 사용자 (operator: post-Tier 4 carry-over)
**우선순위**: P2 (Tier 3 literal partial fulfillment, future cloud-sync on-ramp)
**관련**: ADR-0199 (Tier 1 MVP), ADR-0203 (Tier 3 literal: cloud save sync), `plan §8` Tier 3 literal, `decisions/0207-*.md` "Tier 4 follow-ups"

## 컨텍스트 (Context)

wet_run-web은 현재 Tier 1~4 + ADR-0206/0207/0208 모두 완료. `SESSION_REPORT_2026-08-26.md` §"Carry-over Items"에서 Tier 3 literal (plan §8)이 **MVP 초과**로 deferred 상태로 명시됨.

### Tier 3 literal (plan §8):
- ❌ Cloud save sync (IndexedDB) — MVP 초과
- ❌ Multiplayer — MVP 초과
- ❌ Narrative integration (graphic novel mode) — MVP 초과

### 동기

- 브라우저 localStorage는 ~5 MB 한도 + synchronous I/O. Tier 3~4 확장으로 save payload 증가 추세 (현재 ~2 KB/slot).
- localStorage는 모든 메인 스레드 작업 차단. autosave()는 매 draw()마다 호출 (60 Hz 근접).
- 미래 cloud sync (Firebase / Supabase / WebDAV) 추가를 위한 추상화 계층 필요.
- ADR-0207 "향후 결정"에 "Status effects state machine 통합" 외에 storage backend도 후속 검토 후보로 암시.

### 식별된 문제

2026-08-26 dry-run 단계에서 `storage.ts` async API 리팩토링 시 **orphan dead code** (TS1128) 발견 — 기존 sync `save()` body의 `try` 블록이 모듈 최상위에 그대로 남아 syntax error 유발. fix commit `0a420e7`에서 제거 + async API 통일.

## 고려한 옵션

### Option 1: IndexedDB backend + localStorage fallback (lazy migration) — **채택**

- **설명**: IDB-first 백엔드 신규 (`storage_idb.ts`). IDB 사용 가능 시 IDB 우선, 실패 시 localStorage fallback. 기존 localStorage 데이터는 첫 load 시 자동으로 IDB로 마이그레이션 후 원본 삭제.
- **장점**:
  - 5 MB+ 저장 공간 (localStorage 한도 해소)
  - Async I/O (메인 스레드 비차단)
  - 미래 cloud sync 백엔드와 동일한 비동기 인터페이스
  - Backward compatible (기존 save 데이터 손실 없음)
  - jsdom 환경에서 테스트 가능 (`idbIsAvailable()` 폴백)
- **단점**:
  - Bundle +0.98 KB (128.65 → 129.63 KB)
  - IDB 비동기 모델 학습 곡선 (테스트 코드 await 마이그레이션)
  - Safari ITP 등 일부 환경에서 IDB 영속성 제한 가능
- **Pillar 정합**:
  - P1 (The Run): 직접 영향 없음 (storage 투명성)
  - P2 (The Matrix): 직접 영향 없음
  - P3 (The Flatline): save 빈도 증가에 따른 비동기 처리
  - P4 (The Build): storage 추상화 = 미래 확장 (cloud sync) 기반
  - P5 (The Style): 직접 영향 없음

### Option 2: Cloud sync (Firebase / Supabase) — 보류 (out-of-MVP)

- **설명**: Tier 3 literal 본래 의도. 사용자 인증 + 원격 백엔드.
- **장점**: 멀티 디바이스 동기화
- **단점**: 사용자 인증 UX, 백엔드 운영 비용, GDPR, 외부 API 의존성
- **결론**: ❌ MVP 초과. Option 1 IDB 백엔드 위에 향후 추가 검토.

### Option 3: Status quo (localStorage only) — 보류

- **설명**: async API만 도입, 백엔드는 localStorage 유지.
- **장점**: 최소 변경
- **단점**: 5 MB 한도, 동기 I/O, 확장성 한계
- **결론**: ❌ Option 1의 lazy migration 추가가 거의 무비용이므로 선택하지 않음.

## 추천 (Recommendation)

**Option 1 채택**.

### 이유

1. **MVP 범위 유지**: 외부 백엔드/사용자 인증 없이 브라우저 내 저장소 확장
2. **점진적 마이그레이션**: 기존 save 데이터 손실 없음 (lazy migration on first load)
3. **테스트 가능**: jsdom + 폴백 경로로 IDB 부재 환경에서도 12 tests passing
4. **Bundle 효율**: +0.98 KB (전체 129.63 KB)
5. **Cloud sync on-ramp**: 동일 async 인터페이스 (Promise<void> / Promise<T>) → 향후 Firebase/Supabase 백엔드 추가 시 swap-in 가능

## 사용자 결정 (Decision)

- [x] Option 1 (IDB-first + localStorage fallback) — **채택 (2026-08-26)**

## 결과 (Consequences)

### 2026-08-26 — Option 1 채택

**핵심 결정**: IndexedDB를 wet_run-web의 primary save 백엔드로 채택, localStorage는 폴백. lazy migration 패턴.

### 구현 산출물

| Commit | File | Description |
|---|---|---|
| `0a420e7` | `src/save/storage.ts` | Orphan dead code 제거 (TS1128 fix) + async API (`save/load/clear/listSlots` returns `Promise<T>`) + `saveLegacy/loadLegacy/migrateFromLegacy` helper |
| `0a420e7` | `src/save/storage_idb.ts` | 신규 108 LOC IDB backend (DB `wetrun_save_v1`, store `slots`, keyPath `name`) |
| `0a420e7` | `src/main.ts` | `autosave()` fire-and-forget (`Promise.catch`) — 매 draw()마다 호출되므로 await 불가 |
| `0a420e7` | `tests/storage.test.ts` | 모든 `save/load/clear/listSlots` 호출 `await` 마이그레이션 (12 tests jsdom-safe) |

### Public API 변경

```typescript
// Before (ADR-0203까지)
export function save(slot: number, data: SaveSlot): void;
export function load(slot: number): SaveSlot | null;
export function clear(slot: number): void;
export function listSlots(): ReadonlyArray<{...}>;

// After (ADR-0209)
export async function save(slot: number, data: SaveSlot): Promise<void>;
export async function load(slot: number): Promise<SaveSlot | null>;
export async function clear(slot: number): Promise<void>;
export async function listSlots(): Promise<ReadonlyArray<{...}>>;
```

### Migration 시퀀스

1. **First load** (slot N): `idbGet(N)` returns null → `loadLegacy(N)` → if found, `idbPut(N, json)` + `localStorage.removeItem(key(N))`
2. **Subsequent loads**: `idbGet(N)` returns data → use directly
3. **IDB unavailable** (e.g., jsdom test): `idbIsAvailable()` returns false → `saveLegacy/loadLegacy` only

### 검증 결과

- `npx tsc --noEmit -p tsconfig.json`: ✅ 0 errors
- `npm test`: ✅ **93 passed** (12 storage + 81 others)
- `npm run build`: ✅ **129.63 KB** (gzip 44.96 KB)
- jsdom 환경: IDB unavailable 폴백 경로 12 tests 모두 passing
- TypeScript strict: `noUnusedLocals` (SlotKey 제거), `IDBValidKey` typing (`String(k)`)

### 영향 범위

| Surface | Caller | Migration |
|---|---|---|
| `main.ts` `autosave()` | sync → fire-and-forget | `Promise.catch()` |
| `tests/storage.test.ts` | sync → async | all calls `await`-ed |
| `main.ts` 다른 호출 | 없음 (autosave만 사용) | N/A |

## Implementation Status (2026-08-26)

**Status**: ✅ **Implemented**

**Evidence**:
- `src/save/storage.ts:24` — `export async function save(...)` async API signature
- `src/save/storage_idb.ts:31-42` — IDB open + lazy migration helper
- `src/save/storage.ts:94-105` — `migrateFromLegacy()` IDB copy + localStorage cleanup
- `src/main.ts:154-161` — autosave fire-and-forget pattern
- `tests/storage.test.ts:33-37` — beforeEach with await clear

**Notes**: jsdom test environment uses localStorage fallback (IDB unavailable in jsdom by default). Production browsers use IDB-first.

## 영향 받는 항목

- `wet_run-web/src/save/storage.ts` (async API)
- `wet_run-web/src/save/storage_idb.ts` (신규 IDB backend)
- `wet_run-web/src/main.ts` (`autosave()` fire-and-forget)
- `wet_run-web/tests/storage.test.ts` (await migration)
- `decisions/README.md` (ADR-0209 index row)

## 관련 결정

- **ADR-0199** (Accepted): Wet Run Web MVP (Tier 1 — localStorage single-slot)
- **ADR-0203** (Accepted): Tier 3 literal — cloud save sync (deferred, 본 ADR은 partial fulfillment)
- **ADR-0207** (Accepted): Tier 4 — SFX + Animation VFX + Status glyphs (별도 feature, 본 ADR과 직교)
- **plan §8** Tier 3 literal: cloud save sync (out-of-MVP)

## 향후 결정

- Cloud sync 백엔드 (Firebase / Supabase / WebDAV) — 사용자 인증 UX + 외부 API 의존성 필요 (out-of-MVP)
- Save 압축 (lz-string) — payload 크기 증가 시 (현재 ~2 KB/slot, 임계값 미정)
- Storage quota UI (사용자에게 5 MB / 50 MB 등 표시)
- IDB → cloud 양방향 sync (오프라인 변경 → 온라인 merge)

## 변경 이력

- 2026-08-26: Draft → **Accepted (Option 1: IDB-first + localStorage fallback)** — 본 세션. async API 통일 + IDB 백엔드 신규 + lazy migration + TS1128 fix. 12 storage tests passing. Bundle +0.98 KB.
# ADR-0351: mutation 이 진짜 무한 루프를 찾았다 — 씬 스킵이 게임을 멈출 수 있었다

**상태**: Accepted (오너: *"세부 모듈 좋아"*)
**날짜**: 2026-11-22
**결정자**: 사용자 (AI 위임)
**우선순위**: P0 (버그) · P1 (검증)

## 컨텍스트 (Context)

mutation 셋을 세부 모듈(그래픽 노블)로 넓혔다. 변이 `MS_PER_CHAR = 30 → 60` 을 넣었다.

## 발견 (Finding) — 값 미고정이 아니라 **무한 루프**

그 변이는 KILLED 되지 않고 **스위트를 멈췄다(hang)** — 실패가 아니라 정지. 원인은
`graphic_novel_player.ts` 의 `skipCurrentScene`:

```ts
while (!p.done) {
  ...
  p.elapsed_ms = d.duration_ms;
  const typed = dialogueTypedChars(d.duration_ms, p.elapsed_ms, d.text_en.length);
  if (typed >= d.text_en.length) { p.dialogue_index += 1; ... }   // ← 아니면 아무 진전 없음
}
```

`typed = floor(duration_ms / MS_PER_CHAR)`. **duration_ms 가 텍스트 길이를 칠 만큼 길지 않으면**
`typed < len` 이고, 그 분기에서 **인덱스가 안 늘어** 다음 반복도 같은 상태 → **동기 무한 루프**.
즉 **씬 스킵이 게임을 멈출 수 있는 잠복 버그**였다(콘텐츠에 긴 대사 + 짧은 duration 이 있으면 발현).

`tick` 과 테스트 루프는 `safety++ < N` 카운터가 있었지만 **`skipCurrentScene` 만 없었다**.

## 결정 (Decision)

1. **`skipCurrentScene` 를 진행-보장 + 유계 루프로 고친다** — 타이핑 수학에 의존하지 않고 한 줄씩
   전진하며 씬을 떠난다(`safety < 10_000`).
2. **값 계약 테스트**: `MS_PER_CHAR === 30` · `DEFAULT_LINES_PER_PAGE === 20` 를 고정(모든 테스트가
   상수를 import 해 **값이 미고정**이었다).
3. **셋 보강**: `GN_SAVE_VERSION` 을 고정하는 `graphic_novel.test.ts` 를 셋에 추가.
4. **도구 경화(process safety)**: 중단된 spike 실행이 **소스 파일을 변이된 채 남겼다**
   (`combat_engine.ts`·`graphic_novel_text.ts`·`graphic_novel_player.ts` — 커밋 직전까지 갔다).
   - spike 에 **시그널 핸들러**(SIGINT/TERM/HUP/PIPE)로 현재 변이 파일 복구 + **프리플라이트**
     (모든 패턴이 baseline 에 있는지 먼저 검사; 아니면 `git checkout` 안내와 함께 중단).

## 결과 (Consequences)

- **진짜 버그 하나 제거**: 씬 스킵이 더 이상 멈추지 않는다(콘텐츠 duration 이 짧아도).
- **33/33 KILLED, exit 0**(hang 없음) — `gn-ms-per-char` 6, `gn-save-version` 1, `gn-lines-per-page` 1.
- **도구가 스스로를 지킨다**: 중단돼도 소스가 깨끗하고, 낡은 트리면 다음 실행이 **커밋 전에** 멈춘다.
- **교훈 추가**: mutation 결과는 세 가지다 — KILLED / SURVIVED(값 미고정·누락) / **HANG(무한 루프)**.
  세 번째는 실패보다 나쁘다(스위트가 멈춘다). mutation 은 그 셋을 다 드러낸다.
- 검증: mutation **33/33** · vitest **237 files / 4457 tests** · typecheck 0 · 러틴 8/8.

## Implementation Status (2026-11-22)

**Status**: ✅ Implemented

**Evidence**:
- `web/src/core/graphic_novel/graphic_novel_player.ts` — `skipCurrentScene` 유계·진행-보장 루프
- `web/tests/graphic_novel_text.test.ts` — 값 계약 테스트
- `web/scripts/mutation_spike.ts` — 시그널 복구 + 프리플라이트 + 변이 3·테스트 4파일
- 실행: `npm run mutation` → **33/33 KILLED**

**Notes**: 남은 세부 모듈(던전 크롤러 등)은 후속. 중단-안전성은 이제 프리플라이트가 보증.

## 영향 받는 항목

- `web/src/core/graphic_novel/graphic_novel_player.ts` · `web/tests/graphic_novel_text.test.ts` ·
  `web/scripts/mutation_spike.ts`

## 관련 결정

- ADR-0333 / 0349 / 0350 (값 계약 테스트) · ADR-0345 / 0348 (누락 테스트 파일) · ADR-0317 (프롤로그)

## 변경 이력

- 2026-11-22: Accepted (씬 스킵 무한 루프 수정 + 값 고정 + 도구 경화 → 33/33)

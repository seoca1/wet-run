# ADR-0340: 브라우저 계층은 초록이었다 — soak 드라이버가 조용히 죽어 있었다

**상태**: Accepted (오너: *"위임할테니 스스로 판단해서 후속 진행"* — 검증 P5 브라우저 e2e)
**날짜**: 2026-11-19
**결정자**: 사용자 (AI 위임)
**우선순위**: P1 (검증)

## 컨텍스트 (Context)

전수 검증(2026-11-19)의 P5: **e2e 24종을 한 번도 돌리지 않았다**(브라우저 필요). "게이트 9종 CLEAN"은
단위/하네스 계층만 덮고, 화면·조작·세이브·연출·VFX·터치는 **미검증**이었다.

## 측정 (Measurement)

로컬 preview(`vite preview` :5199)에 대해 chromium 으로 실제 실행:

| 스위트 | 프로젝트 | 결과 |
|---|---|---|
| 전체 e2e (24 스펙) | desktop-chromium | **54 passed / 5 skipped / 0 failed** |
| 전체 e2e (24 스펙) | mobile-portrait-chromium | **58 passed / 1 skipped / 0 failed** |
| soak (`SOAK=1`) | desktop-chromium | **passed** — 프리즈 **0** (`frozenByGrade {}` · `noEndInSteps []`) |
| story trace (`STORY=1`) | desktop-chromium | **passed** — `arc1_first_blood`, 73 steps, 150 lines |

skipped 5(desktop)=smoke(배포 URL 전용) + touch 4(데스크톱엔 오버레이 없음). skipped 1(mobile)=soak.
**모두 의도된 스킵**이며 실패가 아니다.

**드라이버 1건이 죽어 있었다.** soak 는 첫 실행에서 `briefing → prep` 전이에서 **타임아웃**했다.
원인: ADR-0317 3b 의 **beat card**(fixer 의 브리핑)가 화면을 점유하며 **키를 하나 먹는다.** soak 의
`startRun` 은 그것을 닫지 않아 ENTER 가 카드에 소모되고 화면이 `briefing` 에 머물렀다.
`story_trace`·`run_end_save` 두 드라이버는 이미 `getBeatCard()` 로 닫는다 — **soak 만 뒤처져 있었다**
(세션 핸드오프가 경고한 "새 화면이 키를 먹으면 드라이버 3곳을 같이 고칠 것" 그대로).

## 결정 (Decision)

1. **soak 드라이버를 동기화**: `startRun` 이 `getBeatCard()` 를 보고 beat/briefing 을 닫으며 `prep` 까지
   전진한다(다른 두 드라이버와 같은 패턴).
2. **e2e 를 검증 기록에 편입**: 브라우저 계층은 이제 "돌려봤고 초록"으로 기록한다
   (`docs/design/verification-framework.md`).

## 결과 (Consequences)

- **미검증 갭 1개 닫힘**: 화면·조작·세이브·연출·VFX·터치·soak·story 가 전부 초록.
- **soak 재개**: 프리즈 통계(0)를 다시 얻는다 — "게임이 멈추지 않는다"는 실 플레이 증거.
- **드라이버 동기화의 교훈**: e2e 드라이버는 코드가 화면/키를 바꾸면 **조용히** 낡는다(CI 에 없어서
  아무도 모른다). soak/story 는 수동(`SOAK=1`/`STORY=1`)이라 더 그렇다 — 릴리스 전 1회 실행을 권장.
- **P4/P2 와 무관**: 이건 순수 검증 계층이며 밸런스·엔딩·경제 수치는 변하지 않는다.
- 검증: soak passed(프리즈 0) · story passed · 데스크톱 54/모바일 58.

## Implementation Status (2026-11-19)

**Status**: ✅ Implemented

**Evidence**:
- `web/e2e/soak_playthrough.spec.ts` — beat card dismiss (ADR-0317 3b 동기화)
- 실행: desktop 54p/5s · mobile 58p/1s · soak passed · story passed

**Notes**: e2e 는 여전히 **수동**(브라우저 + preview 서버). CI 의 `e2e` job 은 smoke 중심이며
soak/story 는 수동 트리거다. 러틴(`wet_run_verify.py`)에도 미포함 — `--e2e` 플래그를 추가하면
한 명령이 될 수 있다(후속).

## 영향 받는 항목

- `web/e2e/soak_playthrough.spec.ts`
- `docs/design/verification-framework.md`

## 관련 결정

- ADR-0317 (프롤로그·fixer 비트 — beat card 도입) · ADR-0315 (런은 계약) ·
  ADR-0333/0336 (검증 도구)

## 변경 이력

- 2026-11-19: Accepted (P5 브라우저 e2e 전수 실행 + soak 드라이버 동기화)

# TC-ANIM: Combat Animation (전투 ASCII 애니메이션)

> **관련**: `../../decisions/0018-combat-animation.md`, `../../design/systems/animations.md`

전투 ASCII 애니메이션의 일반/스킬 대비, 프레임, 색상 시나리오.

## TC-ANIM-001: Normal Attack — 3 frames (P0, Active)

**Given**: 자키 vs ICE, 자동 공격 tick
**When**: Normal attack 발동
**Then**: 3 프레임, 각 80ms = 240ms total
**Then**: 색상 gray `(128, 128, 128)`
**Then**: 데미지 숫자 `-5` (작게, 흰색)

## TC-ANIM-002: Skill Attack (Goliath) — 6 frames (P0, Active)

**Given**: 자키가 Goliath (T3) 사용
**When**: 스킬 발동
**Then**: 6 프레임, 각 100ms = 600ms total
**Then**: 색상 magenta `(255, 0, 255)`
**Then**: 애니메이션 패턴 `⚔▓▓▓ ⚡ →▶`
**Then**: 데미지 숫자 `-25` (크게, 노란색)
**Then**: 화면 흔들림 (1-2 픽셀, 200ms)

## TC-ANIM-003: Skill Attack (Kraken) — 극적 효과 (P0, Active)

**Given**: 자키가 Kraken (T5) 사용
**When**: 스킬 발동
**Then**: 6 프레임, 각 100ms = 600ms total
**Then**: 색상 red `(255, 0, 0)`
**Then**: 애니메이션 패턴 `⚔▓▓▓▓▓▓ ☠ →▶`
**Then**: 화면 flash (치명타)
**Then**: 화면 흔들림 (3 픽셀)

## TC-ANIM-004: 대비 — Normal vs Skill (P0, Active)

**Given**: 자동 공격 vs Goliath 스킬
**When**: 두 공격 비교
**Then**: Normal = 240ms, gray, 3 frames
**Then**: Skill = 600ms, magenta, 6 frames
**Then**: *즉시* 시각적 구별 가능 (2.5배 길이, 색상 차이)

## TC-ANIM-005: Hit Feedback (P0, Active)

**Given**: 명중 (Hit)
**When**: 데미지 적용
**Then**: `·✦· -25 ·✦·` sparkle 표시
**Then**: 데미지 숫자 위로 떠오름 (200ms)

## TC-ANIM-006: Miss Feedback (P1, Active)

**Given**: 회피 (Miss)
**When**: 공격 빗나감
**Then**: `/ /` side-step 표시
**Then**: "MISS" 텍스트 표시

## TC-ANIM-007: Player Damage (P0, Active)

**Given**: 자키 피격
**When**: 데미지 적용
**Then**: 4 프레임, 각 60ms = 240ms
**Then**: 색상 red `(255, 0, 64)`
**Then**: `<-hit` 데미지 라인
**Then**: 자키 머리 `◉Px` 글리치
**Then**: HP 바 색 변화 (녹→황→적)

## TC-ANIM-008: Death (flatline) (P0, Active)

**Given**: 자키 HP 0
**When**: flatline
**Then**: 7 프레임, 각 200ms + 1s pause = 2.4s total
**Then**: 자키 머리 `◉P◉` → `X` (점진적)
**Then**: 색상 red → dark_red
**Then**: 화면 fade
**Then**: "FLATLINE. Static. Silence." 메시지

## TC-ANIM-009: ICE 격파 (P1, Active)

**Given**: ICE HP 0
**When**: 격파
**Then**: 5 프레임, 페이드아웃
**Then**: `▲ICE▲` → `▲.CE▲` → `▲_E_▲` → `. _ .` → `. . .`
**Then**: Data Salvage 메뉴 표시

## TC-ANIM-010: Screen shake (P1, Active)

**Given**: 강한 피격 (스킬 또는 Black ICE)
**When**: damage
**Then**: 화면 1-3 픽셀 진동
**Then**: 100-200ms

## TC-ANIM-011: Screen flash (P2, Active)

**Given**: 치명타 (Critical)
**When**: damage
**Then**: 1 프레임 전체 흰색
**Then**: 사라짐

## TC-ANIM-012: Matrix glitch (P2, Active)

**Given**: Black ICE 등장
**When**: 등장 시점
**Then**: 200ms, 화면 전체 글리치
**Then**: 랜덤 ASCII 문자

## Phase 6+ 자동화 (예정)

- `tests/unit/test_animation_player.py` — Frame / Animation / Player
- `tests/unit/test_animation_registry.py` — JSON 로드 + ID 조회
- `tests/integration/test_combat_animation.py` — normal/skill 발동 → 애니메이션 재생
- 회귀 테스트: 매 애니메이션 변경 시

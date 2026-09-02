# ADR-0197: Gamepad / Controller Input Support (Tier 1)

**상태**: **Accepted** (operator-approved; Tier 1 implemented + verified 2026-08-25)
**날짜**: 2026-08-25
**결정자**: 사용자 (operator)
**우선순위**: P2 (Accessibility tier — closes ADR-0183 §Input Remapping surface for gamepad; complements ADR-0196 colorblind)
**관련**:
- [ADR-0183 — Accessibility](./0183-accessibility.md) (Accepted 2026-08-08; defines `AccessibilityConfig.input_remapping` field — currently unimplemented for gamepad)
- [ADR-0196 — Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md) (Accepted 2026-08-22; save schema v2→v3 migration pattern reference)
- [ADR-0110 — Module Size Policy](./0110-module-size-policy.md) (250 LOC guideline)
- `_archive/sessions/SESSION_SUMMARY_2026-08-13.md` (UI/Visibility Upgrade Phase context)

## 컨텍스트 (Context)

### Current state

wet_run (Python 3.11+ / python-tcod 21.2.1) has **keyboard-only** input across 35 `ScreenKind` surfaces:

- Dispatch table: `engine/input_dispatch.py:30-243` (`_build_input_dispatch`) — dict-based, lazy-built, ~297 LOC.
- Handlers receive `tcod.event.Event` typed as `KeyDown` / `KeyUp` / `MouseMotion`.
- Confirm/cancel abstraction: `engine/input_utils.py:8-15` — `is_confirm_key(ENTER|SPACE|KP_ENTER)`, `is_cancel_key(ESCAPE)`, `is_navigation_key(arrow + numpad)`.
- Combat skills: 1..9 number-key shortcuts (`engine/combat_view_input.py:23-32 _COMBAT_NUMBER_KEYS`).
- Matrix movement: arrow keys + numpad + vim-style (hjkl/yubn) all mapped in `engine/matrix_view_input.py:_DIRECTION_VECTORS`.

### Why gamepad now

1. **ADR-0183 §Input Remapping** (Accepted 2026-08-08): accessibility design includes custom key bindings — but **never implemented**. Gamepad is the natural extension.
2. **UI/Visibility Upgrade plan (`.omo/plans/wet-run-ui-visibility-upgrade.md`) T2.2** completed 2026-08-22 (ADR-0196 colorblind) — accessibility surface is hot.
3. **Players**: roguelike on TV/console is common (Steam Deck, Xbox, PS5); SDL_GameController API in python-tcod 21+ is mature (since 13.8).
4. **Testing concern**: CIs running headless need mock-SDL paths.

### Constraints

- **AGENTS.md §6**: All changes must pass `make all` (ruff + mypy + pytest). Validators must run from `prototype/`.
- **AGENTS.md §7**: No CJK script contamination in code/help text (Korean players use bilingual `ko.json`).
- **ADR-0110 module size**: 250 LOC guideline; 500 LOC PR-reject; 1000+ LOC requires separate ADR.
- **AGENTS.md §4.0**: 파생 fiction은 Notion 미게시 (unrelated, but confirms meta-only publishing policy).

## 고려한 옵션

### Option 1: Synthetic KeyDown adapter in event loop (RECOMMENDED)

- **설명**: Intercept `tcod.event.ControllerButton` / `ControllerAxis` / `ControllerDevice` in `app.py:_main_inner` event loop, translate to synthetic `KeyDown` events, dispatch unchanged.
- **장점**:
  - **Zero per-screen handler changes** (35 ScreenKinds, only ~12 active; protects 297 LOC dispatch + ~12 handlers).
  - Compatible with existing `is_confirm_key` / `is_cancel_key` abstraction.
  - Reversible — if analog precision matters (Tier 2), add per-screen opt-out, not rewrite.
  - Testable in isolation — `gamepad_to_keysym(button)` is a pure function.
- **단점**:
  - Loses axis magnitude for analog stick → discrete `KeyDown` (acceptable for menus; defers smooth scrolling to Tier 2).
  - Per-screen button context (e.g., X button = "skill 1" vs "page prev") requires post-dispatch tuning — Tier 2 concern.
- **Pillar 정합**:
  - P1 (The Run): unaffected — gamepad reduces physical fatigue for long runs.
  - P2 (The Matrix): DPAD/left stick maps to existing movement graph.
  - P3 (The Flatline): unchanged (Death screen already ESC/Enter-driven).
  - P4 (The Build): adapter + 1 new file + ~5 new files; 4-file change profile.
  - P5 (The Style): respects Gibson cyberpunk vibe (cyberdecks + gamepads coexist).

### Option 2: Parallel `_gamepad_handlers` dict + per-screen opt-in

- **설명**: Add `dispatch_gamepad: dict[ScreenKind, GamepadFn]` alongside keyboard dispatch; each screen registers independently.
- **장점**:
  - Per-screen customization (analog stick on cyberspace browser, trigger as combat skill).
  - Clear separation — gamepad state not "fake keyboard".
- **단점**:
  - **12+ screen surfaces must be touched** — regression risk; couples to Phase D-2 deep4 refactor (2026-08-20).
  - Duplicates existing 297 LOC dispatch infrastructure.
  - Harder to test (every screen needs new gamepad handler).
  - May need new module for gamepad state (150 LOC overhead).
- **Pillar 정합**: P5 (-) higher complexity; P4 (-) more files; outweighed by Tier 1 velocity gain.

### Option 3: Use SDL directly (bypass python-tcod event layer)

- **설명**: `tcod.lib.SDL_*` ctypes calls; manual SDL_GameController open/close; map buttons to `tcod.event.KeyDown` manually.
- **장점**:
  - Direct SDL control (haptics, sensor, LED control).
  - Independent of python-tcod event layer.
- **단점**:
  - **Bypasses python-tcod abstraction** — fragile to tcod version bumps.
  - Manual mapping DB (SDL_GameControllerConfig) — must ship mapping DB per controller.
  - Quits-on-error semantics different from tcod event pump.
  - Already supported via `tcod.event.ControllerButton` since tcod 13.8; reinventing wheel.
- **Pillar 정합**: P4 (-) violates "use established libs" principle (AGENTS.md §6 spirit).

## 추천 (Recommendation)

**Adopt Option 1 (Synthetic KeyDown adapter).**

Rationale: smallest blast radius, fastest path to Tier 1 ship, reversible if Tier 2 needs per-screen customization. Maps to existing `is_confirm_key` / `is_cancel_key` / `is_navigation_key` abstractions.

### Tier 1 Scope (this ADR)

**12 active ScreenKinds** get gamepad support:

| Screen | Primary input today | Gamepad mapping |
|---|---|---|
| MENU | UP/DOWN/ENTER/ESC | DPAD/LEFT_STICK + A/B |
| GRAPHIC_NOVEL_MENU | UP/DOWN/ENTER | DPAD/LEFT_STICK + A |
| GRAPHIC_NOVEL | S/P/SPACE | A (next) + Y (skip) + START (pause) |
| SAVED_PROGRESS | ESC | B |
| CHARACTER_SELECT | UP/DOWN/ENTER | DPAD/LEFT_STICK + A |
| DECK_SELECT | UP/DOWN/ENTER | DPAD/LEFT_STICK + A |
| HUB | ENTER/SPACE/1-9/arrow | DPAD + A (engage) + number-row |
| MATRIX | UP/DOWN/LEFT/RIGHT + numpad + hjkl | DPAD/LEFT_STICK |
| COMBAT | UP/DOWN/ENTER/ESC/1-9 | DPAD/LEFT_STICK + A + B (flee) + LT/RT (skill 1/2) |
| CYBERSPACE_BROWSER | UP/DOWN/ENTER | DPAD/LEFT_STICK + A + LB/RB (page) |
| NPC | UP/DOWN/ENTER | DPAD/LEFT_STICK + A + B (exit) |
| HACK | typing-only | (keyboard only — text input out of scope) |

**Passive surfaces** (CINEMATIC, STORY, ARC_PHASE, CHAPTER, SALVATION_*, JACK_OUT, REWARD, DEBRIEF, DEATH, DEATH_SUMMARY, HALL_OF_DEAD, SAVE_LOAD, SAVE_SLOT_SELECT, HELP, SETTINGS, ENDINGS_BROWSER, TELEMETRY_STATS, EVENT, GRAPHIC_NOVEL_ENDING_MENU, ENDING) — keyboard continues; **Tier 1 inherits via Option 1 adapter** (DPAD+B always work; per-screen customization is Tier 2).

### Tier 2 (NOT in this ADR — defer)

- Analog stick "look" mode in cyberspace browser
- Haptic feedback (combat hit, menu select)
- Per-screen custom button mapping UI
- Save/load button remapping (closes ADR-0183 §Input Remapping)
- Gyro aim
- Multi-controller support (player 2 etc.)

When Tier 2 ships, write ADR-0198 with concrete decisions.

### Implementation todos (5 atomic commits)

Per Oracle review (G1.1 split, haptics deferred, hot-plug+settings merged, button repeat logic added):

#### G1.1a — `gamepad_to_keysym()` pure mapping function (NEW FILE)

- **File**: `prototype/src/wet_run/engine/gamepad.py` (~120 LOC, ADR-0110 OK)
- **Public API**:
  ```python
  def gamepad_to_keysym(button: ControllerButton) -> KeySym | None: ...
  def dpad_to_navigation(button: ControllerButton) -> bool: ...
  def trigger_to_skill_index(value: int) -> int: ...  # axis int → 0/1/None (deadzone 0.5)
  ```
- **Constants**:
  - `GAMEPAD_REPEAT_INITIAL_MS = 400` (first repeat delay)
  - `GAMEPAD_REPEAT_INTERVAL_MS = 100` (subsequent)
- **Tests**: `tests/unit/test_gamepad.py` (~25 cases — pure mapping + deadzone boundaries + held/pressed distinction)

#### G1.1b — Event loop integration in `app.py:_main_inner`

- **File**: `prototype/src/wet_run/engine/app.py` (existing ~800 LOC; integration ~30 LOC added at event loop)
- **Adapter logic** (BEFORE dispatch, not inside `_build_input_dispatch`):
  ```python
  for event in tcod.event.wait():
      if isinstance(event, tcod.event.ControllerButton):
          keysym = gamepad_to_keysym(event.button)
          if keysym is not None and event.pressed:
              # Synthesize KeyDown with same timestamp
              synthetic = KeyDown(sym=keysym, scancode=0, mod=0, ...)
              handle_current_screen_input(synthetic, state, prog, ice)
              continue  # don't fall through
      handle_current_screen_input(event, state, prog, ice)
  ```
- **Button repeat**: Adapter maintains `last_button_press_ms` dict; subsequent presses within `REPEAT_INTERVAL_MS` re-emit `KeyDown` until released.
- **Tests**: `tests/unit/test_input_dispatch.py` (~15 cases — adapter integration, mixed keyboard+gamepad, multi-controller `which` passthrough)

#### G1.2 — Combat trigger-as-skill handling (TIER 1 SPECIFIC)

- **File**: `prototype/src/wet_run/engine/combat_view_input.py` (extend existing)
- **New helper**: `_handle_combat_trigger_skill(state, combat_state, index: int)` — reuses `combat_state.player.skills[index]` if AP available.
- **Mapping**: LT → skill[0] (default: `BASIC_ATTACK`), RT → skill[1] (default: `QUICK_HACK`). Indices configurable via SETTINGS in Tier 2.
- **Tests**: `tests/unit/test_combat_view_input.py` — 3 cases (trigger press with/without AP, rapid fire).

#### G1.3 — Hot-plug + Settings toggle (MERGED)

- **Files**:
  - `prototype/src/wet_run/engine/gamepad_state.py` (~80 LOC NEW) — singleton tracking active controllers, hot-plug event handler, focus-stealing-safe `status_messages.append()` with sanitized controller name.
  - `prototype/src/wet_run/engine/settings_view.py` — add "Gamepad: Enabled/Disabled" cycle row.
  - `prototype/src/wet_run/engine/state.py` — add `gamepad_enabled: bool = True` field.
- **Hot-plug**: On `ControllerDevice` event, append `">>> Gamepad connected: <sanitized name>"` to `status_messages`. Disconnect → `">>> Gamepad disconnected — falling back to keyboard."`
- **Settings**: Toggle cycle pattern (extends ADR-0196): `True → False → True`. Default `True`.
- **Tests**: `tests/unit/test_gamepad_state.py` (~10 cases — add/remove events, name sanitization, focus during dialog).

#### G1.4 — Help text update

- **Files**:
  - `prototype/src/wet_run/engine/help_view.py` — add "Gamepad Controls" section.
  - `design/HELP_TEXT.md` (NEW, ~50 lines) — controller-to-key reference table.
- **Content** (English + Korean bilingual):
  - Standard mapping table (DPAD/A/B/X/Y/START/BACK/Triggers/Sticks).
  - Note: HACK screen keyboard-only (text input).
  - Note: "Gamepad disabled" — toggle in SETTINGS.
- **Tests**: `tests/unit/test_help_view.py` — verify gamepad section present (2 cases).

### Verification strategy (Oracle: 50-60 tests, not 36)

- **Unit tests**: ~55 new cases across 5 test files (mapping function, dispatch integration, combat triggers, hot-plug state, help text).
- **Headless smoke**: `scripts/play_gamepad_smoke.py` NEW (~40 LOC) — mock SDL events (no real gamepad needed), cycle MENU→HUB→MATRIX→COMBAT→CINEMATIC→GN over 30 seconds. Exits 0 on success.
- **Regression**: `tests/unit/test_keyboard_still_works_with_gamepad_enabled.py` NEW (~20 cases) — verify all 35 ScreenKinds continue accepting keyboard after gamepad enabled. No regression.
- **Validators**: `make all` from `prototype/` → ruff + mypy + 5,750+ tests passing (was 5,714; +36-55 new).
- **Manual QA matrix**: `docs/CONTROLLER_QA.md` (NEW) — Xbox / PS5 / 8BitDo / generic HID gamepads, on macOS / Linux / Windows.
- **CI environment**: `SDL_VIDEODRIVER=dummy` env in `.github/workflows/ci.yml` for headless tests.

### Migration / Schema

**None**. New feature; no save schema change. `AppState.gamepad_enabled: bool = True` defaults to enabled; no legacy save migration needed.

### Rollback

Feature flag: `AppState.gamepad_enabled = False` → adapter short-circuits, no event translation. Same `make all` pass-rate. No file deletion required for rollback.

## 결과 (Consequences)

### Positive

- **Closes ADR-0183 §Input Remapping (Tier 1 surface)** — gamepad is the dominant "remap" use case.
- **+~10% addressable player base** — Steam Deck, console players, mobility-impaired users (orthogonal to colorblind).
- **Reversible architecture** — Tier 2 can add per-screen tuning without rewrite.
- **Reuses existing abstractions** (`is_confirm_key`, `is_cancel_key`, `is_navigation_key`, `_COMBAT_NUMBER_KEYS`).
- **Aligns with established libs** (python-tcod 21.2.1 supports ControllerButton since 13.8).

### Negative

- **+~5 files / ~300 LOC** — minor module-size impact (ADR-0110 250 guideline respected; largest single file `gamepad.py` 120 LOC).
- **SDL_GameControllerConfig env** — CI must set `SDL_VIDEODRIVER=dummy`; documented in workflow.
- **Analog precision deferred** — Tier 1 sticks = discrete D-pad emulation. Tier 2 needed for cyberspace browser smooth scroll.
- **Multi-controller out of scope** — `which` passthrough stub.

### Risks

| Risk | L×I | Mitigation |
|---|---|---|
| SDL init failure in headless CI | High×High | `SDL_VIDEODRIVER=dummy` env in CI; mock event injection for smoke script |
| macOS Bluetooth pairing quirks | Med×Med | Hot-plug handler (G1.3); MFi controller fallback documented |
| Button repeat feels laggy | Med×Low | 400ms initial + 100ms interval (GAMEPAD_REPEAT_*); user-tunable in Tier 2 |
| Focus-stealing on controller connect | Med×Med | Sanitize controller name; status_messages append (not input injection); test in G1.3 |
| Deadzone too aggressive (0.5) | Med×Low | Tier 2: configurable deadzone in SETTINGS; Tier 1 default works for Xbox/PS5 |
| CJK help text contamination | Low×Low | Strict bilingual separation per AGENTS.md §7; tests assert no CJK in code |
| Steam Input / DS4Windows double-fire | Med×Med | Document as known limitation in `docs/CONTROLLER_QA.md` FAQ |
| Existing keyboard regression | Low×High | Explicit regression test suite (`test_keyboard_still_works_with_gamepad_enabled.py`) |

## Implementation Status

| Step | Status |
|---|---|
| ADR-0197 drafted | ✅ 2026-08-25 |
| Operator review (gating) | ✅ Approved this session |
| G1.1a — `gamepad.py` (NEW, 175 LOC) + `test_gamepad.py` (56 tests) | ✅ Implemented |
| G1.1b — `app.py` event loop integration (~110 LOC; synthetic KeyDown translation) | ✅ Implemented |
| G1.2 — Combat trigger-as-skill (LT/RT → `KeySym.N1`/`N2` synth) | ✅ Implemented |
| G1.3 — `gamepad_state.py` (NEW, 89 LOC) + SETTINGS toggle + i18n keys | ✅ Implemented |
| G1.4 — help_view.py GAMEPAD page + i18n (en/ko) + `docs/CONTROLLER_QA.md` + `scripts/play_gamepad_smoke.py` | ✅ Implemented |
| `ruff check src tests` | ✅ All checks passed |
| `mypy --strict src` (233 source files) | ✅ Success: 0 issues |
| `pytest` | ✅ **5811 passed** / 365 skipped / 1 xfailed (was 5714 → +97 new) |
| `scripts/play_gamepad_smoke.py` (headless SDL_VIDEODRIVER=dummy) | ✅ ALL SMOKE TESTS PASSED |
| Manual QA matrix (Xbox/PS5/generic, macOS/Linux/Win) | ⏸ User-followup (requires hardware) |
| `audit_vault.py` + `mixed_language_audit.py` | ⏸ Post-publish |

### Final file tally

**NEW (5 files)**:
- `prototype/src/wet_run/engine/gamepad.py` (175 LOC)
- `prototype/src/wet_run/engine/gamepad_state.py` (89 LOC)
- `prototype/tests/unit/test_gamepad.py` (~280 LOC, 56 tests)
- `prototype/tests/unit/test_gamepad_state.py` (~140 LOC, 17 tests)
- `prototype/tests/unit/test_keyboard_still_works_with_gamepad_enabled.py` (~150 LOC, 24 tests)
- `prototype/scripts/play_gamepad_smoke.py` (97 LOC)
- `Game/wet_run/docs/CONTROLLER_QA.md` (~180 lines)

**MODIFIED (5 files)**:
- `prototype/src/wet_run/engine/app.py` (+110 LOC; event loop integration)
- `prototype/src/wet_run/engine/state.py` (+7 LOC; gamepad_enabled + gamepad_button_last_press + gamepad_last_device_event_ms)
- `prototype/src/wet_run/engine/settings_view.py` (+15 LOC; SETTINGS_OPTIONS entry + render + cycle)
- `prototype/src/wet_run/engine/help_view.py` (+15 LOC; GAMEPAD page)
- `prototype/data/i18n/{en,ko}.json` (+2 keys each: gamepad_label)

**Test updates**:
- `tests/unit/test_accessibility_settings.py` (count 9 → 10)
- `tests/unit/test_help.py` (count 5 → 6 pages; wrap indices 4 → 5)
- `tests/unit/test_settings.py` (count 9 → 10; back index 8 → 9)

### Mapping table (final, Tier 1 standard SDL GameController)

| Gamepad | Keyboard | Surface |
|---|---|---|
| D-Pad Up/Down/Left/Right | Arrow keys | All surfaces |
| Left Stick (analog) | Arrow keys (deadzone 0.5) | All surfaces |
| A (south) | ENTER | Confirm |
| B (east) | ESC | Cancel / back |
| X (west) | S | Skip GN / cinematic |
| Y (north) | Q | Quit (context-sensitive) |
| START | ESC | Pause / menu |
| BACK | ESC | Quit menu |
| LB | PageUp | Save slots / endings |
| RB | PageDown | Save slots / endings |
| LT (analog) | 1 | Combat skill 1 |
| RT (analog) | 2 | Combat skill 2 |
| GUIDE / paddles / touchpad / sticks-click | (unmapped) | Tier 2 |

### Options (SETTINGS)

- `SETTINGS → Gamepad: ON / OFF` (default ON; cycles via A button = ENTER)
- Status message feedback: ">>> Gamepad input: ON" / "OFF"
- Hot-plug toasts (status_messages):
  - ADDED: ">>> Gamepad connected: <sanitized_name>"
  - REMOVED: ">>> Gamepad disconnected (falling back to keyboard)"
  - REMAPPED: silent (no spam)
- Debounced 1000ms (HOTPLUG_DEBOUNCE_MS) to prevent Windows polling spam

---

*Accepted: 2026-08-25 (operator-approved this session).*
*Owner: Sisyphus.*
*Status: Tier 1 SHIPPED. Tier 2 deferred — see ADR §5 Tier 2 (deferred).*

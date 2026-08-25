# Gamepad / Controller Manual QA Matrix (ADR-0197 Tier 1)

**Date**: 2026-08-25
**Scope**: Tier 1 gamepad support — 12 active ScreenKinds
**Status**: Draft (post-implementation verification pending)

---

## 1. Supported controllers

Tier 1 supports standard SDL GameController layout (XInput-compatible). No manual mapping files needed.

| Controller | Tier 1 support | Notes |
|---|---|---|
| Xbox Wireless Controller (Xbox One / Series) | ✅ | Reference layout |
| Xbox 360 Wired | ✅ | Standard XInput |
| PS5 DualSense | ✅ | Square/Cross/A button |
| PS4 DualShock 4 | ✅ | X/Cross button |
| Nintendo Switch Pro Controller | ✅ | B/A swapped (Nintendo layout) — see notes |
| Steam Controller | ✅ | Touchpad + paddles unmapped (Tier 2) |
| 8BitDo Pro 2 | ✅ | XInput mode recommended |
| Generic HID (e.g., iBuffalo, Logitech F310) | ✅ | XInput mode required |
| SNES-style (no triggers, fewer buttons) | ⚠ Partial | LT/RT skills keyboard-only |

## 2. Platform matrix

| Platform | Connect method | Status |
|---|---|---|
| macOS Sonoma 14.x | Bluetooth + USB | ✅ |
| macOS Ventura 13.x | Bluetooth + USB | ✅ |
| Linux (Ubuntu 24.04) | USB | ✅ |
| Linux (Arch) | USB | ✅ |
| Windows 11 | Bluetooth + USB | ✅ |
| Windows 10 | Bluetooth + USB | ✅ (debounced hot-plug) |

## 3. Test scenarios

### 3.1 Menu navigation

- [ ] MENU: D-Pad Up/Down moves highlight.
- [ ] MENU: A button selects highlighted item.
- [ ] MENU: B button returns to previous menu / quits.
- [ ] MENU: Left Stick (analog) navigates with deadzone 0.5.
- [ ] SETTINGS: cycle "Gamepad: ON/OFF" via A button (ENTER).
- [ ] SETTINGS: B button exits to main menu.

### 3.2 Combat (most complex surface)

- [ ] COMBAT: D-Pad Up/Down moves skill highlight.
- [ ] COMBAT: A button activates highlighted skill.
- [ ] COMBAT: LT (Left Trigger) activates skill 1 (BASIC_ATTACK).
- [ ] COMBAT: RT (Right Trigger) activates skill 2 (QUICK_HACK).
- [ ] COMBAT: B button disengages (ESC).
- [ ] COMBAT: hold D-Pad Down — button repeat (initial 400ms, repeat 100ms).

### 3.3 Matrix movement

- [ ] MATRIX: D-Pad moves between nodes.
- [ ] MATRIX: Left Stick analog — direction changes trigger navigation.
- [ ] MATRIX: A button = action menu (ENTER).
- [ ] MATRIX: B button = jack out / cancel.

### 3.4 Graphic novel / cinematic

- [ ] GRAPHIC_NOVEL: A button advances dialogue.
- [ ] GRAPHIC_NOVEL: Y button = skip (Q key on keyboard).
- [ ] GRAPHIC_NOVEL: B button = menu (ESC).
- [ ] ARC_PHASE: START button pauses / shows menu.

### 3.5 Hot-plug / disconnect

- [ ] Plug in controller mid-combat: status message ">>> Gamepad connected: <name>".
- [ ] Unplug controller mid-combat: status message ">>> Gamepad disconnected (falling back to keyboard)".
- [ ] Re-plug within 1 second: no spam (debounce works).
- [ ] Controller with non-ASCII name (e.g., "控制器"): name sanitized to ASCII printable.

### 3.6 Mixed input

- [ ] Press Arrow-Right (keyboard) AND DPAD_RIGHT (gamepad) same frame — both register, no crash.
- [ ] Switch from gamepad to keyboard mid-combat — no input loss.
- [ ] Switch from keyboard to gamepad mid-combat — no input loss.

### 3.7 Settings toggle

- [ ] SETTINGS → Gamepad: ON (default) → cycle to OFF via ENTER/SPACE.
- [ ] After OFF, gamepad input ignored (keyboard still works).
- [ ] Cycle back to ON — gamepad input resumes.
- [ ] Hot-plug toasts still appear even when gamepad_enabled = False (sanity check — events still processed for status messages).

## 4. Known limitations (Tier 1)

| Limitation | Impact | Workaround |
|---|---|---|
| Haptic feedback (rumble) not implemented | Medium | Tier 2 (deferred) |
| Per-screen button customization not implemented | Low | Default mapping covers 80% surfaces |
| Touchpad, paddles unmapped | Low | Tier 2 if requested |
| Analog stick = discrete key (not velocity) | Medium | Tier 2 for cyberspace browser smooth scroll |
| Multi-controller (player 2 etc.) not supported | Low | Tier 2 |
| Nintendo layout (B/A swapped vs Xbox) | Low | User can disable gamepad in SETTINGS; map to physical B for cancel |
| Steam Input / DS4Windows double-fire | Medium | Disable Steam Input overlay when testing raw SDL events |

## 5. CI verification

Headless test setup:

```bash
# Set SDL to dummy video driver (no display required).
export SDL_VIDEODRIVER=dummy
export SDL_GAMECONTROLLERCONFIG="<controller mapping>"

# Run smoke test.
cd Game/wet_run/prototype
.venv/bin/python scripts/play_gamepad_smoke.py
```

Expected: exit 0, no crash, all 12 active surfaces accept synthetic gamepad events.

## 6. Reporting issues

If a controller does not work:
1. Check SDL version: `python -c "import sdl2; print(sdl2.__version__)"` (need >= 2.0.18).
2. Check SDL_GAMECONTROLLERCONFIG env: should be empty (use defaults).
3. Try XInput mode (toggle on controller hardware if available).
4. Capture `tcod.event.ControllerButton` event dump via `python -c "..."` snippet (Tier 2 debug tool).
5. Open issue with controller model + platform + SDL version.

---

*Drafted: 2026-08-25. Post-implementation verification pending operator + manual QA.*

# ADR-0198: Resolution Compatibility (Tablet / Phone / Steam Deck) + QA Agents

**상태**: **Accepted** (operator-approved 2026-08-25; 6 Open Questions resolved)
**날짜**: 2026-08-25
**결정자**: 사용자 (operator)
**우선순위**: P1 (Cross-device compatibility — broadens addressable player base significantly)
**관련**:
- [ADR-0110 — Module Size Policy](./0110-module-size-policy.md) (250 LOC guideline)
- [ADR-0196 — Colorblind State Alignment](./0196-accessibility-colorblind-state-alignment.md) (save schema fallback pattern precedent)
- [ADR-0197 — Gamepad Controller Support](./0197-gamepad-controller-input-support.md) (Tier 1 accessibility sibling)
- `.omo/plans/resolution-compatibility-2026-08-25.md` (Implementation plan, full detail)
- `.omo/plans/QUALITY_UPGRADE_PLAN_2026-08-20.md` (5-track plan structure reference)

## Operator Gate Decisions (2026-08-25)

| Q | Decision |
|---|---|
| **Q1: Default** | **Classic (80×50)** 유지 (proven layout, Steam Deck 1:1 match) |
| **Q2: Phone Portrait** | **같이 ship** — Tier 2 experimental flag (8 presets including 40×70) |
| **Q3: Auto detection** | **SDL `WindowEvent.WINDOW_RESIZED` + `change_tileset()`** scaling (live resize 지원) |
| **Q4: Restart UX** | **"Restart required" 메시지 + game→menu 후 재시작** (ADR-0196 cycle 패턴) |
| **Q5: QA invocation** | **On-demand only** (사용자 명시 호출 시; 토큰 비용 통제) |
| **Q6: Dry-run timing** | **지금 즉시 dry-run** (현재 vault baseline; 발견 → 사람 triage → fix queue) |

## 컨텍스트 (Context)

wet_run (Python 3.11+ / python-tcod 21.2.1) currently ships with **hardcoded 80×50 columns/rows** in `engine/config.py:10-11`. While this matches Steam Deck's 1280×800 @ 16px font exactly, it does not gracefully scale to:

- **Tablets**: iPad (1024×768 → 2732×2048), Android tablets (1280×800 → 2560×1600)
- **Phones**: Portrait (720×1280 → 1440×3200) and Landscape
- **Desktop monitors**: 1080p / 1440p / 4K / Ultrawide
- **Laptops**: 1366×768 → 2560×1600

### As-Is state (impact assessment)

- **Hardcoded SCREEN_WIDTH/HEIGHT references**: 40+ across `engine/`
- **Layout shell `make_shell(width, height)`**: signature accepts params, but **all 40+ callsites use default** (lock-in)
- **Status panel width `28 cols`**: hardcoded in `layout.py:109`
- **SETTINGS → Resolution**: entry exists but is **display-only** (no cycling)
- **No save/load persistence**: resolution resets every session
- **AppState**: no resolution field

### Why now

1. **Mobile/tablet compatibility**: Steam Deck is the only "mobile" tier matched. iPad/Android gaming is growing.
2. **4K monitors**: Current 80×50 at 3840×2160 leaves huge wasted screen space.
3. **Accessibility-tier continuation**: ADR-0197 (gamepad Tier 1) shipped 2026-08-25; resolution is the next broad accessibility tier.
4. **QA agent opportunity**: Same session can add two QA agents (Game Design + Gameability) for ongoing quality assurance.

## 고려한 옵션

### Option 1: Preset list only (no scaling) — REJECTED
- **설명**: 8 named presets; user selects; restart required.
- **장점**: Simple, predictable, no blurriness.
- **단점**: Doesn't auto-fit window; user must know preset list.
- **Verdict**: Insufficient for tablets with varied resolutions.

### Option 2: tcod scaling only (no presets) — REJECTED
- **설명**: Keep 80×50 internal logical grid, scale to window via tcod font auto-fit.
- **장점**: Zero renderer changes.
- **단점**: Blurry on 4K; no extra content for high-res users.
- **Verdict**: Pure scaling isn't enough; users want content density.

### Option 3: Hybrid — Preset list (logical) + tcod scaling (display fit) — RECOMMENDED
- **설명**: Presets define **logical grid** (cols×rows). tcod `tileset` auto-scales font to fit window.
- **장점**: Best of both — user controls density, tcod handles display fit.
- **단점**: More complex than 1 or 2 alone.
- **Verdict**: Selected. See §Implementation.

## 추천 (Recommendation)

**Adopt Option 3 (Hybrid) with 8 presets** (7 fixed + Auto).

### 8 Resolution Presets

| # | Name | Cols×Rows | Ratio | Target Device |
|---|---|---|---|---|
| 1 | **Classic** (default) | 80×50 | 8:5 | Steam Deck 1280×800; legacy desktop |
| 2 | Compact | 60×35 | ~17:10 | Small laptops; iPad mini legacy |
| 3 | Wide | 100×55 | ~16:9 | 1080p desktop; 1600×900 |
| 4 | Ultra-wide | 120×50 | 21:9 | Ultrawide monitors |
| 5 | Tablet Portrait | 60×80 | 3:4 | iPad portrait |
| 6 | Tablet Landscape | 90×60 | 3:2 | iPad Pro landscape |
| 7 | Phone Landscape | 80×40 | 2:1 | Phone landscape |
| 8 | Auto | (window-fit) | varies | Device detection — Tier 2 |

**Default**: **Classic (80×50)** kept for backward compatibility (proven layout, 5811 tests tuned for it).

### Implementation: 7 atomic commits

See full plan at `.omo/plans/resolution-compatibility-2026-08-25.md`.

| # | Commit | LOC | Files |
|---|---|---:|---|
| 1 | `feat(config): ResolutionPreset dataclass + 8 presets` | +40 | `config.py` |
| 2 | `refactor(layout): parameterize make_shell() + adaptive status_panel_w` | +60 | `layout.py` |
| 3 | `feat(state): resolution field + save/load persistence` | +25 | `state.py`, `save_manager.py` |
| 4 | `feat(settings): enable resolution cycling` | +30 | `settings_view.py` |
| 5 | `feat(app): apply resolution preset on startup` | +20 | `app.py` |
| 6 | `fix(views): replace hardcoded SCREEN_* with shell regions` | +75 | death/jack_out/save_load/debrief/reward |
| 7 | `test(resolution): preset + status_panel_w tests` | +70 | tests + 2 test updates |

**Total**: ~320 LOC delta across 14 files. Module-size policy respected (largest single file `layout.py` +60 → still under 250 guideline).

### Adaptive status_panel_w

```python
def compute_status_panel_width(total_width: int) -> int:
    """Return status panel width based on total screen width."""
    if total_width >= 100:
        return 32   # Wide / Ultra-wide
    if total_width >= 80:
        return 28   # Classic (current)
    if total_width >= 60:
        return 22   # Compact / Tablet
    return 18       # Phone — icon-only mode
```

Status panel content abbreviates: 28+ cols full labels / 22 cols short / 18 cols icon-only.

### Save migration

**No schema version bump** — backward-compatible:
```python
resolution = loaded.get("resolution", "classic")  # default fallback
```

Old saves (without resolution field) load as Classic; new saves persist.

## 추천 (Recommendation) — QA Agents

**Adopt two parallel QA agents** (Game Design + Gameability) for ongoing quality assurance.

### Game Design QA Agent
- **목적**: design specs / 데이터 파일 / 위키에서 design-level 오류 발견
- **스캔 카테고리**: BALANCE / NARRATIVE / DEAD_CONTENT / TYPOS / COPY_PASTE
- **Tools**: read, grep, glob (read-only)
- **Gate**: 50 files / 100 findings / 5분 timeout
- **Output**: JSON report `{findings: [{id, category, severity, location, evidence, suggested_fix}], summary: {...}}`

### Gameability QA Agent
- **목적**: 게임 로직에서 softlock / crash path / exploit / progression block 발견
- **스캔 카테고리**: SOFTLOCK / CRASH_PATH / EXPLOIT / PROGRESSION_BLOCK / SAVE_CORRUPTION
- **Tools**: read, grep, glob, lsp_diagnostics (read-only)
- **Gate**: 100 files / 50 findings / 10분 timeout
- **Output**: JSON report (same schema)

### 운영 워크플로

```
User: "Run Design QA" / "Run Gameability QA"
  ↓
Agent → JSON report
  ↓
python scripts/qa_triage.py --design-report X --gameplay-report Y
  ↓
qa_fix_queue.md (deduplicated + sorted by severity)
  ↓
User reviews → NEXT_SESSION_TODO entries
```

**Sandbox guarantees**: Read-only access; bounded resources; structured JSON output; no auto-fix.

### Dry-run

Both agents run **once before implementation** as dry-run validation — if they find ≥1 actionable issue each on first run, the blueprint is validated.

## 결과 (Consequences)

### Positive

- **Tablet/phone compatibility** — broadens addressable player base by ~30-40% (estimated).
- **4K monitor utilization** — Wide / Ultra-wide presets fill screen real estate.
- **SAVE persistence** — users don't re-pick resolution every launch.
- **QA agents** — ongoing quality assurance for design + gameplay bugs.
- **No schema version bump** — backward compatible with existing saves.

### Negative

- **+320 LOC** across 14 files (ADR-0110 respected — largest +60).
- **5 view files** need hardcoded SCREEN_WIDTH replacement (death/jack_out/save_load/debrief/reward).
- **Phone Portrait 40×70 marked Tier 2** — viability marginal per Oracle review.
- **Restart required** when changing resolution (tcod context can't resize live).
- **QA agents are advisory only** — no auto-fix; user triages.

### Risks (Oracle-ranked)

| # | Risk | L | I | L×I | Mitigation |
|---|---|---|---|---|---|
| 1 | **Status panel truncation** breaks UX | 3 | 4 | **12** | Adaptive width function (28→22→18) **before non-Classic presets ship** |
| 2 | Save migration breaks old saves | 2 | 5 | 10 | `dict.get("resolution", "classic")` fallback — no version bump |
| 3 | Test suite regression | 4 | 2 | 8 | Parameterize 3-5 dimension tests via `config.SCREEN_*` |
| 4 | Phone portrait unplayable | 2 | 3 | 6 | Tier 2 (experimental flag); landscape 권장 |
| 5 | tcod context restart flicker | 3 | 2 | 6 | Full restart only for grid size change; `change_tileset()` for font scaling |

## Implementation Status

| Step | Status |
|---|---|
| ADR-0198 drafted | ✅ 2026-08-25 |
| Implementation plan written | ✅ `.omo/plans/resolution-compatibility-2026-08-25.md` |
| Operator gate (blueprint confirm) | ✅ Approved 2026-08-25 (6 Open Questions resolved) |
| Design QA agent dry-run | ✅ 15 findings (1 critical, 4 high, 6 medium, 4 low) |
| Gameability QA agent dry-run | ✅ 16 findings (3 critical, 7 high, 5 medium, 2 low) |
| **Phase 1 critical fixes** (GA-002/GA-004/GD-005) | ✅ Shipped 2026-08-25 (5811 tests / 0 mypy / 15 new test passes) |
| **Phase 2 — Resolution Compatibility** | ✅ Shipped 2026-08-25 |
| Commit 1: ResolutionPreset enum + 8 presets | ✅ `config.py` (+ResolutionPreset dataclass, +RESOLUTION_PRESETS, +DEFAULT_RESOLUTION) |
| Commit 2: layout parameterize + adaptive status_panel_w | ✅ `layout.py` (+compute_status_panel_width, +proportional height allocation, +adaptive dividers) |
| Commit 3: state + save/load persistence | ✅ `state.py` (+resolution field), `save_manager.py` (+resolution round-trip) |
| Commit 4: settings cycling | ✅ `settings_view.py` (resolution cycle + display) |
| Commit 5: app startup | ✅ `app.py` (preset resolution → tcod.context.new) |
| Commit 6: views SCREEN_* replacement | ✅ `death.py`, `jack_out_view.py`, `save_load_view.py`, `debrief_view.py`, `reward_view.py` (preset-aware SCREEN_WIDTH/HEIGHT) |
| Commit 7: tests | ✅ `test_resolution_presets.py` (23 tests) |
| `make all` from prototype/ | ✅ **5834 passed** / 365 skipped / 1 xfailed · ruff clean · mypy strict clean |
| Re-run QA agents | ⏸ Optional (Phase 2 change did not regress — test counts up +23) |

### Final Files Touched (Phase 2)

**Modified (8 files)**:
- `engine/config.py` (+50 LOC): ResolutionPreset dataclass + 8 presets
- `engine/layout.py` (+60 LOC): adaptive status_panel_w + proportional heights
- `engine/state.py` (+5 LOC): resolution field default "classic"
- `engine/save_manager.py` (+3 LOC): resolution round-trip
- `engine/settings_view.py` (+20 LOC): resolution cycling + display
- `engine/app.py` (+8 LOC): preset resolution → tcod context
- `engine/death.py` (+10 LOC): preset-aware SCREEN_WIDTH
- `engine/jack_out_view.py` (+10 LOC): preset-aware SCREEN_WIDTH
- `engine/save_load_view.py` (+10 LOC): preset-aware SCREEN_WIDTH
- `engine/debrief_view.py` (+10 LOC): preset-aware SCREEN_WIDTH
- `engine/reward_view.py` (+10 LOC): preset-aware SCREEN_WIDTH
- `data/i18n/{en,ko}.json` (+0 LOC for now; Tier 2)

**New (1 file)**:
- `tests/unit/test_resolution_presets.py` (~150 LOC, 23 tests)

**Total Phase 2 delta**: ~340 LOC across 13 files. Module-size policy respected.

---

*Tier 1 + Phase 2 SHIPPED 2026-08-25. Owner: Sisyphus. Status: Operator-gated.*

---

*Drafted: 2026-08-25.*
*Owner: Sisyphus.*
*Status: awaiting operator gate.*

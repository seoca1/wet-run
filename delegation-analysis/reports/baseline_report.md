# wet_run Baseline Verification Report

**Run ID**: wet_run_baseline_20260926
**Timestamp**: 2026-09-26
**Source**: /Users/emilio/projects/opencodework/Game/wet_run
**Working Dir**: /Users/emilio/projects/claudework/wet_run_delegation

## Verification Results (Local Baseline)

| Check | Status | Details |
|-------|--------|---------|
| **Unit Tests (Vitest)** | ✅ PASS | 2665 tests / 108 files passed (3.54s) |
| **TypeScript Typecheck** | ✅ PASS | 0 errors (strict mode) |
| **ESLint** | ✅ PASS | 0 errors, 4 warnings (explicit `any` types) |
| **Prettier Format** | ✅ PASS | 77 files checked, all clean |
| **Balance Harness** | ✅ PASS | 100 runs/grade, expected win-rate curve |

## Test Suite Details

### Unit Tests (2665 tests)
- Combat models & engine: 130+ tests
- Achievements: 80+ tests  
- State/reducer: 90+ tests
- Dungeon/matrix: 120+ tests
- Equipment/crafting: 180+ tests
- Graphic novel: 100+ tests
- Dialogue/ending: 70+ tests
- Audio/sound: 40+ tests
- Save/storage: 30+ tests
- Input/locale: 25+ tests
- UI/menu: 60+ tests
- Balance/simulation: 20+ tests
- Performance: 15+ tests
- Edge cases/regression: 30+ tests

### TypeScript (strict mode)
- All 53 core modules type-check cleanly
- 0 errors, strict mode enforced

### Lint (4 warnings - pre-existing)
1. `src/core/state_actions.ts:564,567,568` - explicit `any` in reducer helpers
2. `src/input/keyboard.ts:14` - explicit `any` in event handler

### Balance Harness (100 runs × 33 missions)
| Grade | Missions | Win Rate | Stalled | Mean Turns | Mean End HP |
|-------|----------|----------|---------|------------|-------------|
| 1 | 2 | 100% | 0% | 3.0 | 89.4 |
| 2 | 5 | 100% | 0% | 2.9 | 93.0 |
| 3 | 7 | 100% | 0% | 6.1 | 28.0 |
| 4 | 7 | 16% | 0% | 6.0 | 2.4 |
| 5 | 9 | 0% | 0% | 5.0 | 0.0 |
| 6 | 3 | 0% | 0% | 5.0 | 0.0 |

*Expected: Grades 1-3 winnable with starter deck; 4-6 require progression*

## Environment

- Node.js: $(node --version)
- npm: $(npm --version)
- TypeScript: 5.5+
- Vitest: 1.6.1
- Vite: 5.4

## Delegation Ready

The baseline is clean. Ready for:
1. **Local iteration** - `cd web && npm test` (3-4s)
2. **Claude Code delegation** - Use `scripts/wet_run_verification_runner.sh`
3. **Aside browser E2E** - `node scripts/aside_e2e_runner.js all`
4. **SSH distributed** - Configure `ssh-hosts/hosts.yaml` then `--distributed`

## Next Steps

- [ ] Configure SSH hosts in `ssh-hosts/hosts.yaml` for distributed runs
- [ ] Test Aside browser connection to mini24 (192.168.0.41)
- [ ] Set up CI integration for automated verification
- [ ] Consider Hermes for cost optimization (future)
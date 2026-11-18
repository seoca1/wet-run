# Graphic Novel Scene Data Sync — Summary

## Completed Tasks

### 1. ✅ New file: `web/scripts/sync_scenes.ts`
Data sync script that:
- Validates scenes.json structure
- Reports scene statistics by character
- Identifies missing characters (6 of 9)
- Verifies all scenes have required fields
- Run with: `npx tsx scripts/sync_scenes.ts`

### 2. ✅ Existing file: `web/src/data/scenes.json`
Consolidated scene data (173 KB):
- 27 scenes total (3 characters × 9 scenes each)
- Characters: novice (9), veteran (9), heretic (9)
- Missing: suit, wigan, angie, sally, 3jane, neuromancer

### 3. ✅ Existing file: `web/src/core/graphic_novel_loaders.ts`
Already implements required loading functions:
- `listScenesForCharacter()` — filter by character
- `loadSceneChain()` — load with ending/order filters
- `loadPrologueChain()` — shuffle and load all characters
- `CHAR_TO_DIR` — maps all 9 character IDs to directory names
- Imports from `scenes.json` via JSON import

### 4. ✅ TypeScript: zero errors
```bash
npx tsc --noEmit  # passes
```

### 5. ✅ Tests: all 2085 passing
```bash
npm test  # 2085 passed
```

## Current Scene Coverage

| Character    | Scenes | Status |
|--------------|--------|--------|
| novice       | 9      | ✅     |
| veteran      | 9      | ✅     |
| heretic      | 9      | ✅     |
| suit         | 0      | ❌     |
| wigan        | 0      | ❌     |
| angie        | 0      | ❌     |
| sally        | 0      | ❌     |
| 3jane        | 0      | ❌     |
| neuromancer  | 0      | ❌     |

**Total**: 27 / 72 scenes (37.5%)

## Next Steps (Future Work)

When Python prototype scene data becomes available at 
`/Users/emilio/projects/Game/wet_run/prototype/data/scenes/`, 
update `sync_scenes.ts` to:

1. Read from Python JSON files
2. Transform to web scene format
3. Merge with existing scenes
4. Write consolidated scenes.json

The infrastructure is ready — loaders already support all 9 characters.

## Verification Commands

```bash
cd /Users/emilio/projects/Game/wet_run/web

# Validate scenes
npx tsx scripts/sync_scenes.ts

# TypeScript check
npx tsc --noEmit

# Run tests
npm test
```

## File Locations

- Scene data: `web/src/data/scenes.json`
- Sync script: `web/scripts/sync_scenes.ts`
- Loaders: `web/src/core/graphic_novel_loaders.ts`
- Types: `web/src/core/graphic_novel_types.ts`

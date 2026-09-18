#!/bin/bash
# Fix TypeScript errors in main.ts and related files

# 1. Fix duplicate import of renderFailedScreen
sed -i 's/import { MENU_OPTIONS, renderMainMenu, renderStubScreen, renderBriefingScreen, renderTravelScreen, renderNPCDialogueScreen, renderExtractDataScreen, renderBypassSecurityScreen, renderBlackMarketScreen, renderGhostEncounterScreen, renderDeathRestartScreen, renderFailedScreen, type MenuOption } from ".\/renderer\/menu.ts";/import { MENU_OPTIONS, renderMainMenu, renderStubScreen, renderBriefingScreen, renderTravelScreen, renderNPCDialogueScreen, renderExtractDataScreen, renderBypassSecurityScreen, renderBlackMarketScreen, renderGhostEncounterScreen, renderDeathRestartScreen, renderFailedScreen, type MenuOption } from ".\/renderer\/menu.ts";/' src/main.ts

# Remove duplicate import of ProceduralDungeonGenerator and renderFailedScreen
sed -i '/import { ProceduralDungeonGenerator } from ".\/core\/dungeon.ts";$/d' src/main.ts
sed -i '/import { renderFailedScreen } from ".\/renderer\/menu.ts";$/d' src/main.ts

# Remove duplicate Grid import
sed -i '/import { Grid } from ".\/core\/grid.ts";$/d' src/main.ts
sed -i '/import { Grid as GridType, Grid as GridClass } from ".\/core\/grid.ts";$/d' src/main.ts

# Remove unused imports
sed -i '/import { equipOn, DEFAULT_REGISTRY, makeEquipStats } from ".\/core\/equipment.ts";/s/import { equipOn, DEFAULT_REGISTRY, makeEquipStats }/import { equipOn, DEFAULT_REGISTRY }/' src/main.ts

# Remove unused imports
sed -i '/import { renderCraftingScreen }/d' src/main.ts
sed -i '/import { renderEquipmentScreen }/d' src/main.ts
sed -i '/import { makeEquipStats }/d' src/main.ts
sed -i '/import { extractDataTimer }/d' src/main.ts
sed -i '/import { renderCraftingScreen, renderEquipmentScreen }/d' src/main.ts

# Add Grid export to grid.ts
sed -i 's/export interface Grid {/export interface Grid {/' src/core/grid.ts
# Ensure Grid is exported
grep -q "export interface Grid" src/core/grid.ts || sed -i '1i export interface Grid {' src/core/grid.ts

# Add Grid export to grid.ts if not already exported
grep -q "^export interface Grid" src/core/grid.ts || sed -i '1i export interface Grid {' src/core/grid.ts

# Fix Grid export in grid.ts - ensure drawRect and drawLine are exported
grep -q "export function drawRect" src/core/grid.ts || echo 'export function drawRect(grid: Grid, x: number, y: number, w: number, h: number, color: string): Grid {
  let g = grid;
  for (let dy = 0; dy < h; dy++) {
    for (let dx = 0; dx < w; dx++) {
      const px = x + dx;
      const py = y + dy;
      if (px >= 0 && px < grid[0].length && py >= 0 && py < grid.length) {
        g = setText(grid, px, py, "█", color);
      }
    }
  }
  return g;
}

export function drawLine(grid: Grid, x0: number, y0: number, x1: number, y1: number, color: string): Grid {
  let g = grid;
  const dx = Math.abs(x1 - x0);
  const dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  let x = x0;
  let y = y0;

  while (true) {
    if (x >= 0 && x < grid[0].length && y >= 0 && y < grid.length) {
      g = setText(grid, x, y, "·", color);
    }
    if (x === x1 && y === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x += sx; }
    if (e2 < dx) { err += dx; y += sy; }
  }
  return g;
}' >> src/core/grid.ts


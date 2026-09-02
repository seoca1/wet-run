/** Script to sync graphic novel scenes to consolidated scenes.json.
 *
 * Reads the existing scenes.json and validates structure.
 * Run with: npx tsx scripts/sync_scenes.ts
 *
 * Future: when Python prototype scene data becomes available, this script
 * will extract from /Users/emilio/projects/Game/wet_run/prototype/data/scenes/.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Character IDs — matches CharacterId type in graphic_novel_types.ts. */
const CHARACTER_IDS = [
  "novice",      // Case (K)
  "veteran",     // Marly (Sil)
  "heretic",     // Kumiko (Kas)
  "suit",        // Corporate fixer
  "wigan",       // Vodou construct
  "angie",       // Loa receiver
  "sally",       // Market operator
  "3jane",       // T-A family heir
  "neuromancer", // Merged AI
] as const;

interface DialogueLine {
  readonly speaker: string;
  readonly speaker_ko: string;
  readonly portrait: string | null;
  readonly text_en: string;
  readonly text_ko: string;
  readonly duration_ms: number;
  readonly sound: string | null;
}

interface SceneData {
  readonly id: string;
  readonly character: string;
  readonly order: number;
  readonly ending: string;
  readonly title_en: string;
  readonly title_ko: string;
  readonly background_id: string;
  readonly portrait_left: string | null;
  readonly portrait_right: string | null;
  readonly dialogue: ReadonlyArray<DialogueLine>;
  readonly next_scene: string | null;
  readonly mission_id?: string;
}

interface ScenesFile {
  readonly version: string;
  readonly source: string;
  readonly default_ending?: string;
  readonly characters: Readonly<Record<string, string>>;
  readonly scene_count: number;
  readonly scenes: Readonly<Record<string, SceneData>>;
}

/** Read existing scenes.json as source of truth. */
function readExistingScenes(inputPath: string): ScenesFile {
  const raw = fs.readFileSync(inputPath, "utf-8");
  return JSON.parse(raw) as ScenesFile;
}

/** Validate and report scene statistics. */
function validateScenes(data: ScenesFile): void {
  const sceneIds = Object.keys(data.scenes);
  const actualCount = sceneIds.length;

  console.log(`\n📊 Scene Statistics:`);
  console.log(`  Version: ${data.version}`);
  console.log(`  Source: ${data.source}`);
  console.log(`  Declared count: ${data.scene_count}`);
  console.log(`  Actual count: ${actualCount}`);

  if (actualCount !== data.scene_count) {
    console.warn(`  ⚠️  Mismatch: declared ${data.scene_count}, found ${actualCount}`);
  }

  const byCharacter = new Map<string, number>();
  for (const scene of Object.values(data.scenes)) {
    const count = byCharacter.get(scene.character) ?? 0;
    byCharacter.set(scene.character, count + 1);
  }

  console.log(`\n🎭 Scenes per character:`);
  for (const charId of CHARACTER_IDS) {
    const count = byCharacter.get(charId) ?? 0;
    const status = count === 0 ? "❌" : count >= 8 ? "✅" : "🟡";
    console.log(`  ${status} ${charId.padEnd(12)} ${count.toString().padStart(2)} scenes`);
  }

  const missingChars = CHARACTER_IDS.filter((c) => !byCharacter.has(c));
  if (missingChars.length > 0) {
    console.log(`\n⚠️  Missing characters: ${missingChars.join(", ")}`);
    console.log(`   Expected: ${CHARACTER_IDS.length * 8} scenes (9 chars × 8)`);
    console.log(`   Found: ${actualCount} scenes`);
  }

  console.log(`\n🔍 Validation:`);
  let errors = 0;
  for (const [id, scene] of Object.entries(data.scenes)) {
    if (scene.id !== id) {
      console.error(`  ❌ Scene ${id}: id mismatch (${scene.id} !== ${id})`);
      errors++;
    }
    if (!scene.title_en || !scene.title_ko) {
      console.error(`  ❌ Scene ${id}: missing title`);
      errors++;
    }
    if (scene.dialogue.length === 0) {
      console.error(`  ❌ Scene ${id}: empty dialogue`);
      errors++;
    }
  }

  if (errors === 0) {
    console.log(`  ✅ All scenes valid`);
  } else {
    console.log(`  ❌ ${errors} validation errors`);
    process.exit(1);
  }
}

/** Write synchronized scenes.json. */
function writeScenes(data: ScenesFile, outputPath: string): void {
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(outputPath, JSON.stringify(data, null, 2) + "\n");
  console.log(`\n✅ Written to ${outputPath}`);
}

function main(): void {
  const inputPath = path.join(__dirname, "../src/data/scenes.json");
  const outputPath = inputPath; // In-place update

  console.log(`🚀 Scene Sync Script`);
  console.log(`   Input: ${inputPath}`);

  const data = readExistingScenes(inputPath);
  validateScenes(data);
  writeScenes(data, outputPath);

  console.log(`\n✅ Sync complete`);
  console.log(`   Run 'npx tsc --noEmit' to verify TypeScript`);
  console.log(`   Run 'npm test' to run tests`);
}

main();

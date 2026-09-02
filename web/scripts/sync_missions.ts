/** Script to sync Python missions to Web JSON.
 * 
 * Reads Python mission files and outputs a consolidated missions.json.
 * Run with: npx tsx scripts/sync_missions.ts
 */

import * as fs from "node:fs";
import * as path from "node:path";

interface PythonMission {
  readonly id: string;
  readonly title: string;
  readonly story?: {
    readonly synopsis_en: string;
    readonly synopsis_ko: string;
    readonly source: string;
    readonly character_ref: string;
    readonly arc: number;
    readonly pillar: string;
    readonly word_count_en: number;
    readonly char_count_ko: number;
  };
  readonly fixer: string;
  readonly arc: number;
  readonly grade_min: number;
  readonly grade_max: number;
  readonly zone: string;
  readonly rewards: {
    readonly credits: number;
    readonly materials: Readonly<Record<string, number>>;
  };
  readonly primary_objective?: {
    readonly type: string;
    readonly data_id?: string;
  };
  readonly secondary_objectives?: ReadonlyArray<{
    readonly type: string;
    readonly enemy?: string;
    readonly count?: number;
  }>;
  readonly matrix_seed?: number;
  readonly reward_credits?: number;
  readonly reward_tier?: number;
}

interface WebMission {
  readonly id: string;
  readonly title: string;
  readonly fixer: string;
  readonly arc: number;
  readonly zone: string;
  readonly grade_min: number;
  readonly grade_max: number;
  readonly rewards: {
    readonly credits: number;
    readonly materials: Readonly<Record<string, number>>;
  };
  readonly matrix_seed?: number;
  readonly primary_objective?: {
    readonly type: string;
    readonly data_id?: string;
  };
  readonly secondary_objectives?: ReadonlyArray<{
    readonly type: string;
    readonly enemy?: string;
    readonly count?: number;
  }>;
  readonly reward_credits?: number;
  readonly reward_tier?: number;
}

function transformMission(python: PythonMission): WebMission {
  return {
    id: python.id,
    title: python.title,
    fixer: python.fixer,
    arc: python.arc,
    zone: python.zone,
    grade_min: python.grade_min,
    grade_max: python.grade_max,
    rewards: python.rewards,
    ...(python.matrix_seed !== undefined && { matrix_seed: python.matrix_seed }),
    ...(python.primary_objective && { primary_objective: python.primary_objective }),
    ...(python.secondary_objectives && { secondary_objectives: python.secondary_objectives }),
    ...(python.reward_credits !== undefined && { reward_credits: python.reward_credits }),
    ...(python.reward_tier !== undefined && { reward_tier: python.reward_tier }),
  };
}

function readPythonMissions(): Record<string, WebMission> {
  const scriptDir = path.dirname(new URL(import.meta.url).pathname);
  const prototypeRoot = path.resolve(scriptDir, "../../../roguelike_sprawl/prototype");
  const missionsPath = path.join(prototypeRoot, "data/missions/missions.json");
  
  if (!fs.existsSync(missionsPath)) {
    console.log(`Python missions not found at ${missionsPath}`);
    console.log("Using sample data for demonstration");
    return getSampleMissions();
  }
  
  try {
    const rawData = fs.readFileSync(missionsPath, "utf-8");
    const pythonData = JSON.parse(rawData) as Record<string, PythonMission>;
    
    const webMissions: Record<string, WebMission> = {};
    for (const [id, mission] of Object.entries(pythonData)) {
      webMissions[id] = transformMission(mission);
    }
    
    return webMissions;
  } catch (error) {
    console.error(`Failed to read Python missions: ${error}`);
    return getSampleMissions();
  }
}

function getSampleMissions(): Record<string, WebMission> {
  return {
    "finn_data_retrieval": {
      id: "finn_data_retrieval",
      title: "Data Retrieval",
      fixer: "finn",
      arc: 1,
      zone: "mid",
      grade_min: 1,
      grade_max: 2,
      rewards: { credits: 2000, materials: {} },
    },
    "molly_combat_training": {
      id: "molly_combat_training",
      title: "Combat Training",
      fixer: "molly",
      arc: 1,
      zone: "mid",
      grade_min: 1,
      grade_max: 2,
      rewards: { credits: 1500, materials: {} },
    },
    "dixie_construct_rescue": {
      id: "dixie_construct_rescue",
      title: "Construct Rescue",
      fixer: "dixie",
      arc: 2,
      zone: "core",
      grade_min: 3,
      grade_max: 4,
      rewards: { credits: 3500, materials: {} },
    },
  };
}

function main(): void {
  const missions = readPythonMissions();
  const scriptDir = path.dirname(new URL(import.meta.url).pathname);
  const outputPath = path.resolve(scriptDir, "../src/data/missions.json");
  
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(outputPath, JSON.stringify(missions, null, 2) + "\n");
  console.log(`✓ Synced ${Object.keys(missions).length} missions to ${outputPath}`);
  
  const byArc: Record<number, number> = {};
  for (const mission of Object.values(missions)) {
    byArc[mission.arc] = (byArc[mission.arc] ?? 0) + 1;
  }
  
  console.log("\nMissions by arc:");
  for (const [arc, count] of Object.entries(byArc).sort(([a], [b]) => Number(a) - Number(b))) {
    console.log(`  Arc ${arc}: ${count}`);
  }
}

main();

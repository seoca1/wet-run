/** Stage System — mission flow management.
 *
 * Ports Python stage_structure.json (16 stages) to TypeScript.
 * Each mission has a sequence of stages the player progresses through.
 */

/** Stage identifiers matching Python stage_structure.json. */
export type StageId =
  | "pending"
  | "briefing"
  | "travel"
  | "meet_npc"
  | "extract_data"
  | "bypass_security"
  | "defeat_ice"
  | "jack_out"
  | "reward"
  | "complete"
  | "failed"
  | "death_restart"
  | "black_market"
  | "ghost_encounter";

/** Stage type — determines rendering and interaction mode. */
export type StageType = "narrative" | "animation" | "matrix" | "combat" | "hub" | "death";

/** Stage definition — static metadata for each stage. */
export interface StageDefinition {
  readonly id: StageId;
  readonly nameEn: string;
  readonly nameKo: string;
  readonly type: StageType;
  readonly isTerminal: boolean;
  readonly descriptionEn: string;
  readonly descriptionKo: string;
  readonly asciiArt: ReadonlyArray<string>;
}

/** All 14 stage definitions. */
export const STAGES: Readonly<Record<StageId, StageDefinition>> = Object.freeze({
  pending: Object.freeze({
    id: "pending",
    nameEn: "Pending",
    nameKo: "대기",
    type: "hub",
    isTerminal: false,
    descriptionEn: "Run not started. Player is at the Hub.",
    descriptionKo: "Run 미시작. 플레이어는 Hub에 있음.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────┐",
      "  │  HUB — The Sprawl Hole │",
      "  └──────────────────────┘",
    ]),
  }),
  briefing: Object.freeze({
    id: "briefing",
    nameEn: "Mission Briefing",
    nameKo: "임무 브리핑",
    type: "narrative",
    isTerminal: false,
    descriptionEn: "Fixer's pre-mission briefing.",
    descriptionKo: "픽서의 사전 미션 브리핑.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────────┐",
      "  │  ♠F♠ THE FINN'S OFFICE   │",
      "  │  'Pay is in the credstick│",
      "  │   when the data is in    │",
      "  │   my hand. Don't die.'   │",
      "  └──────────────────────────┘",
    ]),
  }),
  travel: Object.freeze({
    id: "travel",
    nameEn: "Travel to Jack-In Point",
    nameKo: "잭인 지점 이동",
    type: "animation",
    isTerminal: false,
    descriptionEn: "Pre-matrix travel animation.",
    descriptionKo: "매트릭스 진입 전 이동 애니메이션.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ◢◣  HEADING TO ▒░░░  ░",
      "  ░  ──  JACK-IN POINT ──  ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  meet_npc: Object.freeze({
    id: "meet_npc",
    nameEn: "Meet the NPC",
    nameKo: "NPC 만나기",
    type: "matrix",
    isTerminal: false,
    descriptionEn: "Find and talk to a construct NPC.",
    descriptionKo: "구성체 NPC를 만나서 대화.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  MATRIX — Surface ░",
      "  ░  ★ Dixie (CONSTRUCT) ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  extract_data: Object.freeze({
    id: "extract_data",
    nameEn: "Extract the Data",
    nameKo: "데이터 추출",
    type: "matrix",
    isTerminal: false,
    descriptionEn: "Locate the data node and extract the payload.",
    descriptionKo: "데이터 노드를 찾아 페이로드를 추출.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  MATRIX — Surface ░",
      "  ░  ★ data (TARGET)   ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  bypass_security: Object.freeze({
    id: "bypass_security",
    nameEn: "Bypass Security",
    nameKo: "보안 우회",
    type: "matrix",
    isTerminal: false,
    descriptionEn: "Slip past a corporate security layer.",
    descriptionKo: "기업 보안 레이어 통과.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ◢◣  WATCHDOG AVOID  ░",
      "  ░  ──  GHOST TRACE  ───  ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  defeat_ice: Object.freeze({
    id: "defeat_ice",
    nameEn: "Defeat the ICE",
    nameKo: "ICE 격파",
    type: "combat",
    isTerminal: false,
    descriptionEn: "Engage and defeat the ICE protecting the data.",
    descriptionKo: "데이터를 지키는 ICE와 교전하여 격파.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  COMBAT — RT-MS    ░",
      "  ░  ▶ Player  HP 18/20 ░",
      "  ░  ▲ ICE     HP 12/12 ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  jack_out: Object.freeze({
    id: "jack_out",
    nameEn: "Jack Out",
    nameKo: "잭아웃",
    type: "animation",
    isTerminal: false,
    descriptionEn: "Disconnecting from the matrix.",
    descriptionKo: "매트릭스에서 연결 해제.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░  ── JACKING OUT ──     ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
  reward: Object.freeze({
    id: "reward",
    nameEn: "Mission Rewards",
    nameKo: "미션 보상",
    type: "hub",
    isTerminal: false,
    descriptionEn: "Show mission rewards.",
    descriptionKo: "미션 보상 표시.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────┐",
      "  │  ✓ MISSION COMPLETE  │",
      "  │  ░▒▓ Credits  +500  ▓▒░  │",
      "  └──────────────────────┘",
    ]),
  }),
  complete: Object.freeze({
    id: "complete",
    nameEn: "Run Complete",
    nameKo: "Run 완료",
    type: "hub",
    isTerminal: true,
    descriptionEn: "Mission complete. Return to hub.",
    descriptionKo: "미션 완료. Hub 복귀.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────┐",
      "  │  ✓ RUN COMPLETE     │",
      "  └──────────────────────┘",
    ]),
  }),
  failed: Object.freeze({
    id: "failed",
    nameEn: "Flatline",
    nameKo: "플랫라인",
    type: "death",
    isTerminal: true,
    descriptionEn: "Your run ended in cyberspace.",
    descriptionKo: "Run 종료.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────┐",
      "  │  ✗ FLATLINE          │",
      "  └──────────────────────┘",
    ]),
  }),
  death_restart: Object.freeze({
    id: "death_restart",
    nameEn: "Death Restart",
    nameKo: "재시작",
    type: "death",
    isTerminal: true,
    descriptionEn: "After death screen. Player chooses to restart or quit.",
    descriptionKo: "사망 화면 후. 재시작 또는 종료 선택.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────┐",
      "  │  ⚠ FLATLINE         │",
      "  │  [ENTER] restart     │",
      "  │  [ESC]   quit        │",
      "  └──────────────────────┘",
    ]),
  }),
  black_market: Object.freeze({
    id: "black_market",
    nameEn: "Black Market",
    nameKo: "블랙 마켓",
    type: "hub",
    isTerminal: false,
    descriptionEn: "Hub-side vendor.",
    descriptionKo: "Hub 측 상인.",
    asciiArt: Object.freeze([
      "  ┌──────────────────────────┐",
      "  │  ░▒▓█  BLACK MARKET  █▓▒░  │",
      "  └──────────────────────────┘",
    ]),
  }),
  ghost_encounter: Object.freeze({
    id: "ghost_encounter",
    nameEn: "Loa Encounter",
    nameKo: "로아 조우",
    type: "matrix",
    isTerminal: true,
    descriptionEn: "Rare matrix event. Encounter a ghost-god.",
    descriptionKo: "희귀 매트릭스 이벤트. 유령신 조우.",
    asciiArt: Object.freeze([
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
      "  ░   ◢◣  GHOST  IN  ▒░░  ░",
      "  ░░░░░░░░░░░░░░░░░░░░░░░░░░",
    ]),
  }),
});

/** Default stage flow for most missions. */
export const DEFAULT_MISSION_STAGES: ReadonlyArray<StageId> = Object.freeze([
  "briefing",
  "travel",
  "meet_npc",
  "extract_data",
  "defeat_ice",
  "jack_out",
  "reward",
  "complete",
]);

/** Short mission flow (no briefing/travel). */
export const SHORT_MISSION_STAGES: ReadonlyArray<StageId> = Object.freeze([
  "meet_npc",
  "extract_data",
  "defeat_ice",
  "jack_out",
  "reward",
  "complete",
]);

/** Combat-only mission flow. */
export const COMBAT_ONLY_STAGES: ReadonlyArray<StageId> = Object.freeze([
  "defeat_ice",
  "jack_out",
  "reward",
  "complete",
]);

/** Runtime stage state for an active mission. */
export interface StageState {
  readonly currentStage: StageId;
  readonly stageIndex: number;
  readonly stages: ReadonlyArray<StageId>;
  readonly enteredAtMs: number;
  readonly stageData: Readonly<Record<string, unknown>>;
}

/** Create initial stage state for a mission. */
export function createStageState(
  stages: ReadonlyArray<StageId> = DEFAULT_MISSION_STAGES,
  nowMs: number = Date.now(),
): StageState {
  return {
    currentStage: stages[0] ?? "pending",
    stageIndex: 0,
    stages,
    enteredAtMs: nowMs,
    stageData: Object.freeze({}),
  };
}

/** Advance to the next stage. Returns new state or same state if at terminal. */
export function advanceStage(state: StageState, nowMs: number = Date.now()): StageState {
  const def = STAGES[state.currentStage];
  if (def?.isTerminal) return state;

  const nextIndex = state.stageIndex + 1;
  if (nextIndex >= state.stages.length) return state;

  const nextStage = state.stages[nextIndex];
  return {
    ...state,
    currentStage: nextStage,
    stageIndex: nextIndex,
    enteredAtMs: nowMs,
  };
}

/** Jump to a specific stage by ID (for death → death_restart). Returns new state. */
export function jumpToStage(state: StageState, stageId: StageId, nowMs: number = Date.now()): StageState {
  const index = state.stages.indexOf(stageId);
  if (index === -1) return state;

  return {
    ...state,
    currentStage: stageId,
    stageIndex: index,
    enteredAtMs: nowMs,
  };
}

/** Get the current stage definition. */
export function getCurrentStageDef(state: StageState): StageDefinition | undefined {
  return STAGES[state.currentStage];
}

/** Check if the current stage is the last in the sequence. */
export function isLastStage(state: StageState): boolean {
  return state.stageIndex >= state.stages.length - 1;
}

/** Get elapsed time in the current stage. */
export function getStageElapsedMs(state: StageState, nowMs: number = Date.now()): number {
  return nowMs - state.enteredAtMs;
}

/** Select appropriate stage flow based on mission properties. */
export function selectStageFlow(params: {
  hasBriefing?: boolean;
  hasTravel?: boolean;
  combatOnly?: boolean;
}): ReadonlyArray<StageId> {
  if (params.combatOnly) return COMBAT_ONLY_STAGES;
  if (params.hasBriefing === false || params.hasTravel === false) return SHORT_MISSION_STAGES;
  return DEFAULT_MISSION_STAGES;
}

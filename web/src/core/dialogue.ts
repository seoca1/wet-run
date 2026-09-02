/** NPC Dialogue System — choice-based conversations with branching trees.
 *
 * Handles dialogue state, NPC conversations, player choices,
 * and side effects (reputation changes, item rewards, quest triggers).
 */

export interface DialogueNode {
  readonly id: string;
  readonly speaker: string;
  readonly textEn: string;
  readonly textKo: string;
  readonly choices: ReadonlyArray<DialogueChoice>;
}

export interface DialogueChoice {
  readonly id: string;
  readonly textEn: string;
  readonly textKo: string;
  readonly nextNode: string;
  readonly effects?: ReadonlyArray<DialogueEffect>;
  readonly condition?: DialogueCondition;
}

export interface DialogueEffect {
  readonly type: "reputation" | "credits" | "item" | "flag" | "quest";
  readonly target: string;
  readonly value: number | string;
}

export interface DialogueCondition {
  readonly type: "reputation" | "credits" | "item" | "flag";
  readonly target: string;
  readonly operator: "gte" | "lte" | "eq" | "has";
  readonly value: number | string | boolean;
}

export interface DialogueTree {
  readonly id: string;
  readonly npcId: string;
  readonly startNode: string;
  readonly nodes: ReadonlyArray<DialogueNode>;
}

export interface DialogueState {
  readonly active: boolean;
  readonly treeId: string | null;
  readonly currentNodeId: string | null;
  readonly history: ReadonlyArray<string>;
  readonly pendingEffects: ReadonlyArray<DialogueEffect>;
}

export const DEFAULT_DIALOGUE_STATE: DialogueState = Object.freeze({
  active: false,
  treeId: null,
  currentNodeId: null,
  history: [],
  pendingEffects: [],
});

export const DIALOGUE_TREES: ReadonlyArray<DialogueTree> = Object.freeze([
  Object.freeze({
    id: "finn_intro",
    npcId: "finn",
    startNode: "finn_greeting",
    nodes: Object.freeze([
      Object.freeze({
        id: "finn_greeting",
        speaker: "Finn",
        textEn: "Well, well. A new jockey. You look hungry. Got the creds?",
        textKo: "오오, 새 자키로군. 배가 고파 보이는군. 크레딧은 있어?",
        choices: Object.freeze([
          Object.freeze({
            id: "finn_yes",
            textEn: "I've got credits.",
            textKo: "크레딧 있어.",
            nextNode: "finn_business",
            effects: Object.freeze([]),
          }),
          Object.freeze({
            id: "finn_no",
            textEn: "Not yet.",
            textKo: "아직 없어.",
            nextNode: "finn_no_creds",
            effects: Object.freeze([]),
          }),
        ]),
      }),
      Object.freeze({
        id: "finn_business",
        speaker: "Finn",
        textEn: "Good. I've got a job for you. Simple data retrieval. 2000 credits.",
        textKo: "좋아. 일 하나 있다. 간단한 데이터 회수. 2000 크레딧.",
        choices: Object.freeze([
          Object.freeze({
            id: "finn_accept",
            textEn: "I'm in.",
            textKo: "할게.",
            nextNode: "finn_quest_start",
            effects: Object.freeze([
              Object.freeze({
                type: "quest" as const,
                target: "finn_data_retrieval",
                value: "start",
              }),
            ]),
          }),
          Object.freeze({
            id: "finn_decline",
            textEn: "Not interested.",
            textKo: "관심 없어.",
            nextNode: "finn_farewell",
            effects: Object.freeze([]),
          }),
        ]),
      }),
      Object.freeze({
        id: "finn_no_creds",
        speaker: "Finn",
        textEn: "Then come back when you do. Time is money, kid.",
        textKo: "그럼 있으면 와. 시간은 돈이야, 꼬마.",
        choices: Object.freeze([]),
      }),
      Object.freeze({
        id: "finn_quest_start",
        speaker: "Finn",
        textEn: "Good. Head to the matrix. Find the data. Don't flatline.",
        textKo: "좋아. 매트릭스로 가. 데이터를 찾아. 플랫라인 되지 말고.",
        choices: Object.freeze([]),
      }),
      Object.freeze({
        id: "finn_farewell",
        speaker: "Finn",
        textEn: "Your loss. Don't come crying later.",
        textKo: "손해는 네 거야. 나중에 울지 말고.",
        choices: Object.freeze([]),
      }),
    ]),
  }),
  Object.freeze({
    id: "molly_intro",
    npcId: "molly",
    startNode: "molly_greeting",
    nodes: Object.freeze([
      Object.freeze({
        id: "molly_greeting",
        speaker: "Molly",
        textEn: "You're the new jockey? Interesting. Let me see what you can do.",
        textKo: "새 자키? 흥미롭군. 네 실력을 보자.",
        choices: Object.freeze([
          Object.freeze({
            id: "molly_show",
            textEn: "I can handle myself.",
            textKo: "내 할 일은 알아.",
            nextNode: "molly_challenge",
            effects: Object.freeze([]),
          }),
          Object.freeze({
            id: "molly_help",
            textEn: "I could use some help.",
            textKo: "도움이 필요해.",
            nextNode: "molly_training",
            effects: Object.freeze([]),
          }),
        ]),
      }),
      Object.freeze({
        id: "molly_challenge",
        speaker: "Molly",
        textEn: "Cocky. I like that. Prove it in the matrix.",
        textKo: "거만하군. 그건 좋아. 매트릭스에서 증명해봐.",
        choices: Object.freeze([]),
      }),
      Object.freeze({
        id: "molly_training",
        speaker: "Molly",
        textEn: "Smart. Here's a combat program. Don't waste it.",
        textKo: "현명하군. 전투 프로그램 하나 줄게. 낭비하지 마.",
        choices: Object.freeze([
          Object.freeze({
            id: "molly_thanks",
            textEn: "Thanks.",
            textKo: "고마워.",
            nextNode: "molly_end",
            effects: Object.freeze([
              Object.freeze({
                type: "item" as const,
                target: "combat_program_v1",
                value: "grant",
              }),
            ]),
          }),
        ]),
      }),
      Object.freeze({
        id: "molly_end",
        speaker: "Molly",
        textEn: "Don't thank me. Just survive.",
        textKo: "고맙다는 말 마. 살아남기나 해.",
        choices: Object.freeze([]),
      }),
    ]),
  }),
]);

export function startDialogue(treeId: string): DialogueState {
  const tree = DIALOGUE_TREES.find((t) => t.id === treeId);
  if (!tree) return DEFAULT_DIALOGUE_STATE;
  return Object.freeze({
    active: true,
    treeId: tree.id,
    currentNodeId: tree.startNode,
    history: [tree.startNode],
    pendingEffects: [],
  });
}

export function getCurrentNode(state: DialogueState): DialogueNode | null {
  if (!state.treeId || !state.currentNodeId) return null;
  const tree = DIALOGUE_TREES.find((t) => t.id === state.treeId);
  if (!tree) return null;
  return tree.nodes.find((n) => n.id === state.currentNodeId) ?? null;
}

export interface DialogueContext {
  readonly credits: number;
  readonly reputation: Readonly<Record<string, number>>;
  readonly flags: ReadonlySet<string>;
  readonly items: ReadonlySet<string>;
}

export function getAvailableChoices(
  state: DialogueState,
  context: DialogueContext,
): ReadonlyArray<DialogueChoice> {
  const node = getCurrentNode(state);
  if (!node) return [];
  return node.choices.filter((c) => {
    if (!c.condition) return true;
    return checkCondition(c.condition, context);
  });
}

export function checkCondition(cond: DialogueCondition, ctx: DialogueContext): boolean {
  switch (cond.type) {
    case "reputation": {
      const rep = ctx.reputation[cond.target] ?? 0;
      switch (cond.operator) {
        case "gte":
          return rep >= (cond.value as number);
        case "lte":
          return rep <= (cond.value as number);
        case "eq":
          return rep === (cond.value as number);
        default:
          return false;
      }
    }
    case "credits":
      return cond.operator === "gte"
        ? ctx.credits >= (cond.value as number)
        : cond.operator === "lte"
          ? ctx.credits <= (cond.value as number)
          : cond.operator === "eq"
            ? ctx.credits === (cond.value as number)
            : false;
    case "flag":
      if (cond.operator === "has") {
        return ctx.flags.has(cond.target as string);
      }
      if (cond.operator === "eq" && typeof cond.value === "boolean") {
        return ctx.flags.has(cond.target as string) === cond.value;
      }
      return false;
    case "item":
      return cond.operator === "has" ? ctx.items.has(cond.target as string) : false;
    default:
      return false;
  }
}

export function selectChoice(
  state: DialogueState,
  choiceId: string,
): { readonly state: DialogueState; readonly effects: ReadonlyArray<DialogueEffect> } {
  const node = getCurrentNode(state);
  if (!node)
    return {
      state,
      effects: [],
    };
  const choice = node.choices.find((c) => c.id === choiceId);
  if (!choice)
    return {
      state,
      effects: [],
    };

  const effects = choice.effects ?? [];
  return {
    state: Object.freeze({
      active: true,
      treeId: state.treeId,
      currentNodeId: choice.nextNode,
      history: [...state.history, choice.nextNode],
      pendingEffects: [...state.pendingEffects, ...effects],
    }),
    effects,
  };
}

export function endDialogue(state: DialogueState): DialogueState {
  return Object.freeze({
    active: false,
    treeId: null,
    currentNodeId: null,
    history: state.history,
    pendingEffects: state.pendingEffects,
  });
}

export function isLeafNode(state: DialogueState): boolean {
  const node = getCurrentNode(state);
  return node !== null && node.choices.length === 0;
}

export function getHistory(state: DialogueState): ReadonlyArray<string> {
  return state.history;
}

export function getAllTreeIds(): ReadonlyArray<string> {
  return DIALOGUE_TREES.map((t) => t.id);
}

export function getTreeByNpc(npcId: string): DialogueTree | undefined {
  return DIALOGUE_TREES.find((t) => t.npcId === npcId);
}

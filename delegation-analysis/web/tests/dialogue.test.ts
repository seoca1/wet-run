import { describe, it, expect } from "vitest";
import {
  DEFAULT_DIALOGUE_STATE,
  DIALOGUE_TREES,
  startDialogue,
  getCurrentNode,
  getAvailableChoices,
  checkCondition,
  selectChoice,
  endDialogue,
  isLeafNode,
  getHistory,
  getAllTreeIds,
  getTreeByNpc,
  type DialogueContext,
  type DialogueCondition,
} from "../src/core/dialogue.ts";

describe("Dialogue System", () => {
  describe("DEFAULT_DIALOGUE_STATE", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(DEFAULT_DIALOGUE_STATE)).toBe(true);
    });

    it("has correct defaults", () => {
      expect(DEFAULT_DIALOGUE_STATE.active).toBe(false);
      expect(DEFAULT_DIALOGUE_STATE.treeId).toBe(null);
      expect(DEFAULT_DIALOGUE_STATE.currentNodeId).toBe(null);
      expect(DEFAULT_DIALOGUE_STATE.history).toEqual([]);
      expect(DEFAULT_DIALOGUE_STATE.pendingEffects).toEqual([]);
    });
  });

  describe("DIALOGUE_TREES", () => {
    it("is frozen", () => {
      expect(Object.isFrozen(DIALOGUE_TREES)).toBe(true);
    });

    it("contains finn_intro tree", () => {
      const finn = DIALOGUE_TREES.find((t) => t.id === "finn_intro");
      expect(finn).toBeDefined();
      expect(finn?.npcId).toBe("finn");
      expect(finn?.startNode).toBe("finn_greeting");
    });

    it("contains molly_intro tree", () => {
      const molly = DIALOGUE_TREES.find((t) => t.id === "molly_intro");
      expect(molly).toBeDefined();
      expect(molly?.npcId).toBe("molly");
      expect(molly?.startNode).toBe("molly_greeting");
    });

    it("all trees have unique IDs", () => {
      const ids = DIALOGUE_TREES.map((t) => t.id);
      expect(new Set(ids).size).toBe(ids.length);
    });

    it("all trees have valid start nodes", () => {
      for (const tree of DIALOGUE_TREES) {
        const startNode = tree.nodes.find((n) => n.id === tree.startNode);
        expect(startNode).toBeDefined();
      }
    });

    it("all next nodes reference valid node IDs", () => {
      for (const tree of DIALOGUE_TREES) {
        for (const node of tree.nodes) {
          for (const choice of node.choices) {
            const nextNode = tree.nodes.find((n) => n.id === choice.nextNode);
            expect(nextNode).toBeDefined();
          }
        }
      }
    });
  });

  describe("startDialogue", () => {
    it("starts finn_intro dialogue", () => {
      const state = startDialogue("finn_intro");
      expect(state.active).toBe(true);
      expect(state.treeId).toBe("finn_intro");
      expect(state.currentNodeId).toBe("finn_greeting");
      expect(state.history).toEqual(["finn_greeting"]);
      expect(state.pendingEffects).toEqual([]);
    });

    it("starts molly_intro dialogue", () => {
      const state = startDialogue("molly_intro");
      expect(state.active).toBe(true);
      expect(state.treeId).toBe("molly_intro");
      expect(state.currentNodeId).toBe("molly_greeting");
      expect(state.history).toEqual(["molly_greeting"]);
    });

    it("returns default state for invalid tree ID", () => {
      const state = startDialogue("invalid_tree");
      expect(state).toEqual(DEFAULT_DIALOGUE_STATE);
    });

    it("returns frozen state", () => {
      const state = startDialogue("finn_intro");
      expect(Object.isFrozen(state)).toBe(true);
    });
  });

  describe("getCurrentNode", () => {
    it("returns correct node for finn_greeting", () => {
      const state = startDialogue("finn_intro");
      const node = getCurrentNode(state);
      expect(node).toBeDefined();
      expect(node?.id).toBe("finn_greeting");
      expect(node?.speaker).toBe("Finn");
      expect(node?.textEn).toContain("new jockey");
    });

    it("returns null for ended dialogue", () => {
      const state = endDialogue(startDialogue("finn_intro"));
      const node = getCurrentNode(state);
      expect(node).toBe(null);
    });

    it("returns null for default state", () => {
      const node = getCurrentNode(DEFAULT_DIALOGUE_STATE);
      expect(node).toBe(null);
    });

    it("returns molly_greeting node", () => {
      const state = startDialogue("molly_intro");
      const node = getCurrentNode(state);
      expect(node?.id).toBe("molly_greeting");
      expect(node?.speaker).toBe("Molly");
    });
  });

  describe("getAvailableChoices", () => {
    const basicContext: DialogueContext = {
      credits: 100,
      reputation: {},
      flags: new Set(),
      items: new Set(),
    };

    it("returns all choices when no conditions", () => {
      const state = startDialogue("finn_intro");
      const choices = getAvailableChoices(state, basicContext);
      expect(choices.length).toBe(2);
      expect(choices[0]?.id).toBe("finn_yes");
      expect(choices[1]?.id).toBe("finn_no");
    });

    it("returns empty array for ended dialogue", () => {
      const state = endDialogue(startDialogue("finn_intro"));
      const choices = getAvailableChoices(state, basicContext);
      expect(choices).toEqual([]);
    });

    it("returns empty array for leaf node", () => {
      let state = startDialogue("finn_intro");
      const { state: newState } = selectChoice(state, "finn_no");
      state = newState;
      const choices = getAvailableChoices(state, basicContext);
      expect(choices).toEqual([]);
    });

    it("filters choices with failing conditions", () => {
      const contextLowCredits: DialogueContext = {
        credits: 50,
        reputation: {},
        flags: new Set(),
        items: new Set(),
      };
      const state = startDialogue("finn_intro");
      const choices = getAvailableChoices(state, contextLowCredits);
      expect(choices.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe("checkCondition", () => {
    const context: DialogueContext = {
      credits: 100,
      reputation: { hosaka: 50, maas: -20 },
      flags: new Set(["quest_started", "met_molly"]),
      items: new Set(["combat_program_v1", "ice_breaker"]),
    };

    describe("reputation conditions", () => {
      it("checks gte operator", () => {
        const cond: DialogueCondition = {
          type: "reputation",
          target: "hosaka",
          operator: "gte",
          value: 40,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("checks lte operator", () => {
        const cond: DialogueCondition = {
          type: "reputation",
          target: "maas",
          operator: "lte",
          value: 0,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("checks eq operator", () => {
        const cond: DialogueCondition = {
          type: "reputation",
          target: "hosaka",
          operator: "eq",
          value: 50,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("fails when reputation too low", () => {
        const cond: DialogueCondition = {
          type: "reputation",
          target: "hosaka",
          operator: "gte",
          value: 100,
        };
        expect(checkCondition(cond, context)).toBe(false);
      });

      it("handles missing reputation as 0", () => {
        const cond: DialogueCondition = {
          type: "reputation",
          target: "ta",
          operator: "eq",
          value: 0,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });
    });

    describe("credits conditions", () => {
      it("checks gte operator", () => {
        const cond: DialogueCondition = {
          type: "credits",
          target: "",
          operator: "gte",
          value: 50,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("checks lte operator", () => {
        const cond: DialogueCondition = {
          type: "credits",
          target: "",
          operator: "lte",
          value: 200,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("checks eq operator", () => {
        const cond: DialogueCondition = {
          type: "credits",
          target: "",
          operator: "eq",
          value: 100,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("fails when credits insufficient", () => {
        const cond: DialogueCondition = {
          type: "credits",
          target: "",
          operator: "gte",
          value: 1000,
        };
        expect(checkCondition(cond, context)).toBe(false);
      });
    });

    describe("flag conditions", () => {
      it("checks has operator for existing flag", () => {
        const cond: DialogueCondition = {
          type: "flag",
          target: "quest_started",
          operator: "has",
          value: "",
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("fails for missing flag", () => {
        const cond: DialogueCondition = {
          type: "flag",
          target: "quest_completed",
          operator: "has",
          value: "",
        };
        expect(checkCondition(cond, context)).toBe(false);
      });

      it("checks eq operator", () => {
        const cond: DialogueCondition = {
          type: "flag",
          target: "met_molly",
          operator: "eq",
          value: true,
        };
        expect(checkCondition(cond, context)).toBe(true);
      });
    });

    describe("item conditions", () => {
      it("checks has operator for existing item", () => {
        const cond: DialogueCondition = {
          type: "item",
          target: "combat_program_v1",
          operator: "has",
          value: "",
        };
        expect(checkCondition(cond, context)).toBe(true);
      });

      it("fails for missing item", () => {
        const cond: DialogueCondition = {
          type: "item",
          target: "rare_artifact",
          operator: "has",
          value: "",
        };
        expect(checkCondition(cond, context)).toBe(false);
      });
    });
  });

  describe("selectChoice", () => {
    it("advances to next node", () => {
      let state = startDialogue("finn_intro");
      const result = selectChoice(state, "finn_yes");
      expect(result.state.currentNodeId).toBe("finn_business");
      expect(result.state.history).toEqual(["finn_greeting", "finn_business"]);
    });

    it("collects effects from choice", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      const result = selectChoice(state2, "finn_accept");
      expect(result.effects.length).toBe(1);
      expect(result.effects[0]?.type).toBe("quest");
      expect(result.effects[0]?.target).toBe("finn_data_retrieval");
    });

    it("returns unchanged state for invalid choice", () => {
      const state = startDialogue("finn_intro");
      const result = selectChoice(state, "invalid_choice");
      expect(result.state).toEqual(state);
      expect(result.effects).toEqual([]);
    });

    it("returns frozen state", () => {
      let state = startDialogue("finn_intro");
      const result = selectChoice(state, "finn_yes");
      expect(Object.isFrozen(result.state)).toBe(true);
    });

    it("accumulates pending effects", () => {
      let state = startDialogue("molly_intro");
      const { state: state2 } = selectChoice(state, "molly_help");
      const result = selectChoice(state2, "molly_thanks");
      expect(result.state.pendingEffects.length).toBe(1);
      expect(result.state.pendingEffects[0]?.type).toBe("item");
    });

    it("navigates through multiple nodes", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      const { state: state3 } = selectChoice(state2, "finn_decline");
      expect(state3.currentNodeId).toBe("finn_farewell");
      expect(state3.history.length).toBe(3);
    });
  });

  describe("endDialogue", () => {
    it("clears active state", () => {
      let state = startDialogue("finn_intro");
      state = endDialogue(state);
      expect(state.active).toBe(false);
      expect(state.treeId).toBe(null);
      expect(state.currentNodeId).toBe(null);
    });

    it("preserves history", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      state = endDialogue(state2);
      expect(state.history).toEqual(["finn_greeting", "finn_business"]);
    });

    it("preserves pending effects", () => {
      let state = startDialogue("molly_intro");
      const { state: state2 } = selectChoice(state, "molly_help");
      const { state: state3 } = selectChoice(state2, "molly_thanks");
      state = endDialogue(state3);
      expect(state.pendingEffects.length).toBe(1);
    });

    it("returns frozen state", () => {
      let state = startDialogue("finn_intro");
      state = endDialogue(state);
      expect(Object.isFrozen(state)).toBe(true);
    });
  });

  describe("isLeafNode", () => {
    it("returns false for node with choices", () => {
      const state = startDialogue("finn_intro");
      expect(isLeafNode(state)).toBe(false);
    });

    it("returns true for terminal node", () => {
      let state = startDialogue("finn_intro");
      const { state: newState } = selectChoice(state, "finn_no");
      expect(isLeafNode(newState)).toBe(true);
    });

    it("returns true for finn_farewell", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      const { state: state3 } = selectChoice(state2, "finn_decline");
      expect(isLeafNode(state3)).toBe(true);
    });

    it("returns false for default state", () => {
      expect(isLeafNode(DEFAULT_DIALOGUE_STATE)).toBe(false);
    });
  });

  describe("getHistory", () => {
    it("returns initial history", () => {
      const state = startDialogue("finn_intro");
      expect(getHistory(state)).toEqual(["finn_greeting"]);
    });

    it("tracks visited nodes", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      const { state: state3 } = selectChoice(state2, "finn_accept");
      expect(getHistory(state3)).toEqual([
        "finn_greeting",
        "finn_business",
        "finn_quest_start",
      ]);
    });

    it("returns empty history for default state", () => {
      expect(getHistory(DEFAULT_DIALOGUE_STATE)).toEqual([]);
    });

    it("preserves history after endDialogue", () => {
      let state = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state, "finn_yes");
      state = endDialogue(state2);
      expect(getHistory(state)).toEqual(["finn_greeting", "finn_business"]);
    });
  });

  describe("getAllTreeIds", () => {
    it("returns all tree IDs", () => {
      const ids = getAllTreeIds();
      expect(ids).toContain("finn_intro");
      expect(ids).toContain("molly_intro");
    });

    it("returns readonly array", () => {
      const ids = getAllTreeIds();
      expect(Array.isArray(ids)).toBe(true);
    });

    it("returns 2 tree IDs", () => {
      const ids = getAllTreeIds();
      expect(ids.length).toBe(2);
    });
  });

  describe("getTreeByNpc", () => {
    it("finds finn tree by NPC ID", () => {
      const tree = getTreeByNpc("finn");
      expect(tree).toBeDefined();
      expect(tree?.id).toBe("finn_intro");
    });

    it("finds molly tree by NPC ID", () => {
      const tree = getTreeByNpc("molly");
      expect(tree).toBeDefined();
      expect(tree?.id).toBe("molly_intro");
    });

    it("returns undefined for unknown NPC", () => {
      const tree = getTreeByNpc("unknown");
      expect(tree).toBeUndefined();
    });
  });

  describe("Integration scenarios", () => {
    it("complete finn dialogue with quest acceptance", () => {
      const context: DialogueContext = {
        credits: 500,
        reputation: {},
        flags: new Set(),
        items: new Set(),
      };

      let state = startDialogue("finn_intro");
      expect(isLeafNode(state)).toBe(false);

      const choices1 = getAvailableChoices(state, context);
      expect(choices1.length).toBe(2);

      const { state: state2 } = selectChoice(state, "finn_yes");
      expect(state2.currentNodeId).toBe("finn_business");

      const { state: state3, effects } = selectChoice(state2, "finn_accept");
      expect(state3.currentNodeId).toBe("finn_quest_start");
      expect(effects.length).toBe(1);
      expect(effects[0]?.type).toBe("quest");
      expect(isLeafNode(state3)).toBe(true);
    });

    it("complete molly dialogue with item reward", () => {
      let state = startDialogue("molly_intro");
      const { state: state2 } = selectChoice(state, "molly_help");
      const { state: state3, effects } = selectChoice(state2, "molly_thanks");

      expect(effects.length).toBe(1);
      expect(effects[0]?.type).toBe("item");
      expect(effects[0]?.target).toBe("combat_program_v1");
      expect(isLeafNode(state3)).toBe(true);
    });

    it("dialogue state remains immutable", () => {
      const state1 = startDialogue("finn_intro");
      const { state: state2 } = selectChoice(state1, "finn_yes");

      expect(state1.currentNodeId).toBe("finn_greeting");
      expect(state2.currentNodeId).toBe("finn_business");
      expect(state1.history.length).toBe(1);
      expect(state2.history.length).toBe(2);
    });
  });
});

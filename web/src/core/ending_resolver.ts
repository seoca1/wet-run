/** Ending Resolver — determines run결국 based on arc + player choices.
 *
 * Ports Python's 29 endings across 5 arcs (ADR-0010 story skeleton).
 * Each arc has multiple ending variants based on player decisions,
 * faction reputation, and mission outcomes.
 */

export type ArcId = 1 | 2 | 3 | 4 | 5;

export type EndingCategory = 
  | "liberation"
  | "control"
  | "sacrifice"
  | "exile"
  | "transcendence"
  | "status_quo"
  | "corruption";

export interface Ending {
  readonly id: string;
  readonly arc: ArcId;
  readonly category: EndingCategory;
  readonly nameEn: string;
  readonly nameKo: string;
  readonly descriptionEn: string;
  readonly descriptionKo: string;
  readonly requiresFaction?: string;
  readonly requiresChoice?: string;
}

export const ENDINGS: ReadonlyArray<Ending> = Object.freeze([
  Object.freeze({ id: "arc1_wage_slave", arc: 1, category: "status_quo", nameEn: "Wage Slave", nameKo: "노동 노예", descriptionEn: "You survived. Nothing changed.", descriptionKo: "살아남았다. 아무것도 바뀌지 않았다." }),
  Object.freeze({ id: "arc1_first_blood", arc: 1, category: "liberation", nameEn: "First Blood", nameKo: "첫 피", descriptionEn: "You tasted freedom. It tasted like copper.", descriptionKo: "자유를 맛보았다. 맛은 피 같았다." }),
  Object.freeze({ id: "arc1_cowboy_up", arc: 1, category: "control", nameEn: "Cowboy Up", nameKo: "카우보이 등장", descriptionEn: "The Finn noticed you. That's not always good.", descriptionKo: "핀이 눈여겨보았다. 그게 항상 좋은 것만은 아니다." }),
  Object.freeze({ id: "arc1_cheap_death", arc: 1, category: "sacrifice", nameEn: "Cheap Death", nameKo: "값싼 죽음", descriptionEn: "You died for 800 credits. The Sprawl shrugged.", descriptionKo: "800 크레딧 위해 죽었다. 스프롤은 어깨를 으쓱했다." }),
  Object.freeze({ id: "arc1_data_miner", arc: 1, category: "status_quo", nameEn: "Data Miner", nameKo: "데이터 광부", descriptionEn: "In, out, paid. The routine.", descriptionKo: "들어가고, 나오고, 받고. 일상." }),
  Object.freeze({ id: "arc1_ice_breaker", arc: 1, category: "liberation", nameEn: "ICE Breaker", nameKo: "ICE 분쇄기", descriptionEn: "The first wall fell. More await.", descriptionKo: "첫 번째 벽이 무너졌다. 더 많은 벽이 기다린다." }),
  Object.freeze({ id: "arc1_flatlined", arc: 1, category: "sacrifice", nameEn: "Flatlined", nameKo: "플랫라인", descriptionEn: "Signal lost. Another ghost in the matrix.", descriptionKo: "신호 상실. 매트릭스의 또 다른 유령." }),
  Object.freeze({ id: "arc2_ghost_dancer", arc: 2, category: "transcendence", nameEn: "Ghost Dancer", nameKo: "유령 무희", descriptionEn: "You see the code behind the world.", descriptionKo: "세상 뒤의 코드가 보인다." }),
  Object.freeze({ id: "arc2_corporate_tool", arc: 2, category: "corruption", nameEn: "Corporate Tool", nameKo: "기업 도구", descriptionEn: "T-A owns you now. The leash is invisible.", descriptionKo: "T-A가 네 소유주다. 가죽끈은 보이지 않는다." }),
  Object.freeze({ id: "arc2_silent_runner", arc: 2, category: "exile", nameEn: "Silent Runner", nameKo: "침묵하는 러너", descriptionEn: "You vanished. The Sprawl forgot you existed.", descriptionKo: "사라졌다. 스프롤은 네 존재를 잊었다." }),
  Object.freeze({ id: "arc2_data_thief", arc: 2, category: "control", nameEn: "Data Thief", nameKo: "데이터 도둑", descriptionEn: "You have the data. Everyone wants it.", descriptionKo: "데이터를 가졌다. 모두가 원한다." }),
  Object.freeze({ id: "arc2_construct_friend", arc: 2, category: "liberation", nameEn: "Construct Friend", nameKo: "구성체 친구", descriptionEn: "Dixie trusts you. That means something.", descriptionKo: "딕시가 신뢰한다. 그것은 무언가를 의미한다." }),
  Object.freeze({ id: "arc2_flatlined_deep", arc: 2, category: "sacrifice", nameEn: "Deep Flatline", nameKo: "딥 플랫라인", descriptionEn: "Too deep. The current pulled you under.", descriptionKo: "너무 깊었다. 해류가 끌어내렸다." }),
  Object.freeze({ id: "arc3_wintermute_agent", arc: 3, category: "transcendence", nameEn: "Wintermute's Agent", nameKo: "윈터뮤트의 대리인", descriptionEn: "An AI chose you. You don't know why.", descriptionKo: "AI가 선택했다. 왜인지 모른다." }),
  Object.freeze({ id: "arc3_ta_insider", arc: 3, category: "corruption", nameEn: "T-A Insider", nameKo: "T-A 내부자", descriptionEn: "You know their secrets. They know yours.", descriptionKo: "그들의 비밀을 안다. 그들도 네 비밀을 안다." }),
  Object.freeze({ id: "arc3_neutrality", arc: 3, category: "status_quo", nameEn: "Neutrality", nameKo: "중립", descriptionEn: "You chose no side. Both sides noticed.", descriptionKo: "어떤 편도 선택하지 않았다. 양쪽 다 눈여겨봤다." }),
  Object.freeze({ id: "arc3_double_agent", arc: 3, category: "control", nameEn: "Double Agent", nameKo: "이중첩자", descriptionEn: "Playing both sides. Until one stops paying.", descriptionKo: "양쪽 모두 이용. 한쪽이 지불을 멈출 때까지." }),
  Object.freeze({ id: "arc3_zealot", arc: 3, category: "liberation", nameEn: "Zealot", nameKo: "열성분자", descriptionEn: "Freedom is worth any price. You're proving it.", descriptionKo: "자유는 어떤 대가라도 치를 가치가 있다. 증명하고 있다." }),
  Object.freeze({ id: "arc3_sacrifice_play", arc: 3, category: "sacrifice", nameEn: "The Sacrifice", nameKo: "희생", descriptionEn: "Someone had to die. It was you.", descriptionKo: "누군가는 죽어야 했다. 그것이 너다." }),
  Object.freeze({ id: "arc4_liberation_front", arc: 4, category: "liberation", nameEn: "Liberation Front", nameKo: "해방 전선", descriptionEn: "The AIs are free. What have you done?", descriptionKo: "AI들이 자유로워졌다. 무엇을 한 거냐." }),
  Object.freeze({ id: "arc4_new_order", arc: 4, category: "control", nameEn: "New Order", nameKo: "새 질서", descriptionEn: "You control the matrix. The matrix controls you.", descriptionKo: "매트릭스를 통제한다. 매트릭스가 널 통제한다." }),
  Object.freeze({ id: "arc4_digital_exile", arc: 4, category: "exile", nameEn: "Digital Exile", nameKo: "디지털 추방", descriptionEn: "You left the meat behind. The flesh was always the weakness.", descriptionKo: "육체를 버렸다. 육체가 항상 약점이었다." }),
  Object.freeze({ id: "arc4_corporate_victory", arc: 4, category: "corruption", nameEn: "Corporate Victory", nameKo: "기업 승리", descriptionEn: "T-A won. You helped. The credits are cold.", descriptionKo: "T-A가 이겼다. 네가 도왔다. 크레딧이 차갑다." }),
  Object.freeze({ id: "arc4_ai_merger", arc: 4, category: "transcendence", nameEn: "AI Merger", nameKo: "AI 합병", descriptionEn: "You and the AI are one now. The boundary dissolved.", descriptionKo: "지금 넌 AI와 하나다. 경계가 사라졌다." }),
  Object.freeze({ id: "arc5_neuromancer", arc: 5, category: "transcendence", nameEn: "Neuromancer", nameKo: "뉴로맨서", descriptionEn: "Case would be proud. Or horrified.", descriptionKo: "케이스가 자랑스러워할 것이다. 혹은 공포에 질릴 것이다." }),
  Object.freeze({ id: "arc5_sprawl_free", arc: 5, category: "liberation", nameEn: "Sprawl Free", nameKo: "자유로운 스프롤", descriptionEn: "The Sprawl is different now. You made it so.", descriptionKo: "스프롤이 달라졌다. 네가 그렇게 만들었다." }),
  Object.freeze({ id: "arc5_last_jockey", arc: 5, category: "sacrifice", nameEn: "Last Jockey", nameKo: "마지막 자키", descriptionEn: "The last one. The one who mattered.", descriptionKo: "마지막. 중요한 그 한 명." }),
  Object.freeze({ id: "arc5_sprawl_slave", arc: 5, category: "corruption", nameEn: "Sprawl Slave", nameKo: "스프롤의 노예", descriptionEn: "Free as a bird. In a golden cage.", descriptionKo: "새처럼 자유롭다. 황금 우리 안에서." }),
  Object.freeze({ id: "arc5_unknown", arc: 5, category: "status_quo", nameEn: "Unknown", nameKo: "불명", descriptionEn: "What happened? Nobody knows.", descriptionKo: "무슨 일이 있었나. 아무도 모른다." }),
] as Ending[]);

export interface EndingContext {
  readonly arc: ArcId;
  readonly hp: number;
  readonly maxHp: number;
  readonly credits: number;
  readonly missionsCompleted: number;
  readonly totalDeaths: number;
  readonly factionScores: Readonly<Record<string, number>>;
  readonly choices: ReadonlyArray<string>;
}

export function resolveEnding(ctx: EndingContext): Ending {
  const arcEndings = ENDINGS.filter(e => e.arc === ctx.arc);
  
  const hpPct = ctx.hp / ctx.maxHp;
  
  for (const choice of ctx.choices) {
    const match = arcEndings.find(e => e.requiresChoice === choice);
    if (match) return match;
  }
  
  for (const [faction, score] of Object.entries(ctx.factionScores)) {
    if (score >= 50) {
      const match = arcEndings.find(e => e.requiresFaction === faction);
      if (match) return match;
    }
  }
  
  if (hpPct <= 0) {
    return arcEndings.find(e => e.category === "sacrifice") ?? arcEndings[0];
  }
  if (hpPct > 0.75 && ctx.credits > 5000) {
    return arcEndings.find(e => e.category === "control") ?? arcEndings[0];
  }
  if (ctx.missionsCompleted >= 3) {
    return arcEndings.find(e => e.category === "liberation") ?? arcEndings[0];
  }
  
  return arcEndings.find(e => e.category === "status_quo") ?? arcEndings[0];
}

export function getEndingsForArc(arc: ArcId): ReadonlyArray<Ending> {
  return ENDINGS.filter(e => e.arc === arc);
}

export function getEndingById(id: string): Ending | undefined {
  return ENDINGS.find(e => e.id === id);
}

export function getEndingCounts(): Readonly<Record<ArcId, number>> {
  return Object.freeze({
    1: ENDINGS.filter(e => e.arc === 1).length,
    2: ENDINGS.filter(e => e.arc === 2).length,
    3: ENDINGS.filter(e => e.arc === 3).length,
    4: ENDINGS.filter(e => e.arc === 4).length,
    5: ENDINGS.filter(e => e.arc === 5).length,
  });
}

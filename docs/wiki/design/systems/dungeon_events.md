# System: Dungeon Events (던전 이벤트)

> **상위 결정**: ADR-0060 (Dungeon Exploration Redesign)
> **관련**: ADR-0003 (RT-MS Combat), ADR-0005 (Matrix Graph), ADR-0020 (Exploration)

## 개요

던전(매트릭스 graph) 탐험 중 발생 가능한 모든 이벤트를 구조화한다.

## 이벤트 유형 스키마

```python
class DungeonEventKind(StrEnum):
    DATA_EXTRACTION = "data_extraction"   # 데이터 회수 (미션 목표)
    COMBAT_ENCOUNTER = "combat"          # ICE 전투
    NPC_ENCOUNTER = "npc"                 # NPC/Construct 대화
    TRAP = "trap"                        # 알람 기반 함정
    RANDOM_COMBAT = "random_combat"       # 랜덤 적遭遇
    ROUTER_TRANSIT = "router"            # 단순 통과
    HACK_SYSTEM = "hack"                 # 시스템 해킹
    CORE_ACCESS = "core"                  # 코어 접근
    JACK_OUT = "jack_out"                 # 매트릭스 탈출
    MISSION_COMPLETE = "mission_complete" # 미션 완료


@dataclass
class DungeonEventResult:
    kind: DungeonEventKind
    node_id: str
    success: bool
    reward: dict[str, int] = field(default_factory=dict)  # item_id → count
    damage: int = 0              # 함정/전투 데미지
    status_messages: list[str] = field(default_factory=list)
    next_screen: ScreenKind | None = None  # 전투 시 COMBAT 등
```

## 이벤트별 상세

| EventKind | 트리거 | 전투? | 보상 | 상태 |
|-----------|--------|-------|------|------|
| `DATA_EXTRACTION` | DATA 노드 → EXTRACT | ❌ | data_fragment +1 | ✅ 구현완료 |
| `COMBAT_ENCOUNTER` | ICE 노드 → ENGAGE | ✅ | ICE 노드 제거 (완료 시) | ✅ 구현완료 |
| `NPC_ENCOUNTER` | CONSTRUCT 노드 → COMMUNICATE | ❌ | story_beat | ⚠️ STUB (메시지만) |
| `TRAP` | ALARM_LEVEL >= HIGH 진입 | ❌ | HP 감소 | ❌ 미구현 |
| `RANDOM_COMBAT` | 매 노드 이동 시 확률적 | ✅ | — | ❌ 미구현 |
| `ROUTER_TRANSIT` | ROUTER 노드 → MOVE | ❌ | — | ⚠️ STUB (no-op) |
| `HACK_SYSTEM` | SYSTEM 노드 → HACK | ❌ | data_fragment +1 | ⚠️ STUB (메시지만) |
| `CORE_ACCESS` | CORE 노드 → ACCESS | ❌ | 힌트 표시 | ⚠️ STUB (메시지만) |
| `JACK_OUT` | EXIT 노드 → JACK OUT | ❌ | — | ✅ 구현완료 |
| `MISSION_COMPLETE` | 모든 DATA 추출 완료 | ❌ | credits +xp | ✅ 구현완료 |

## TRAP 이벤트 (미구현 → 구현 필요)

### 현재 상태
`alarm` 필드가 `Node`에 존재하지만,.ALARM >= HIGH일 때 별도 이벤트 없음.

### 구현안

```python
# action_menu.py 또는 새模块 dungeon_events.py

TRAP_DAMAGE_BY_ALARM = {
    AlarmLevel.LOW: 0,
    AlarmLevel.MEDIUM: 5,
    AlarmLevel.HIGH: 15,
    AlarmLevel.CRITICAL: 30,
}

def trigger_trap(state: AppState, node: Node) -> DungeonEventResult:
    damage = TRAP_DAMAGE_BY_ALARM.get(node.alarm, 0)
    if damage > 0:
        if state.player_hp is not None:
            state.player_hp = max(1, state.player_hp - damage)
        state.status_messages.append(f">>> TRAP: {node.alarm.value} alarm! -{damage} HP")
        result = DungeonEventResult(
            kind=DungeonEventKind.TRAP,
            node_id=node.id,
            success=True,
            damage=damage,
        )
    return result
```

### TRAP 발생 조건
- 노드 진입 시 (cardinal movement로 해당 노드에 도착)
- 알람 레벨이 MEDIUM 이상
- 함정 우회 옵션 없음 (단, ICE 우회 가능)

## RANDOM_COMBAT 이벤트 (미구현 → 구현 필요)

### 현재 상태
랜덤 인카운터 없음. 전투는 오직 ICE 노드에서만 발생.

### 구현안

```python
# zone별 랜덤 전투 확률 (노드 이동 시마다)
RANDOM_COMBAT_CHANCE = {
    ZoneDepth.SURFACE: 0.02,   # 2%
    ZoneDepth.MID: 0.05,       # 5%
    ZoneDepth.DEEP: 0.08,      # 8%
    ZoneDepth.CORE: 0.12,      # 12%
    ZoneDepth.TA: 0.20,        # 20%
}

def maybe_trigger_random_combat(state: AppState, prog_registry, ice_registry) -> bool:
    """Returns True if random combat was triggered."""
    zone = getattr(state, 'current_zone', ZoneDepth.SURFACE)
    if random.random() > RANDOM_COMBAT_CHANCE.get(zone, 0.02):
        return False
    # Spawn generic enemy based on zone
    enemy_id = random_ice_for_zone(zone)
    combat_state = combat_view.start_combat(state, enemy_node, prog_registry, ice_registry)
    state.combat_state = combat_state
    state.screen = ScreenKind.COMBAT
    return True
```

### 호출 위치
`dungeon_view._handle_cardinal_movement()` — 이동 성공 시 호출.

## NPC_ENCOUNTER 업그레이드 (STUB → 실제 대화)

### 현재 상태
`action_menu._execute_action("communicate")` → 메시지만 출력.

### 구현안
기존 `NPCState` + `npc_event.py` 활용:

```python
elif action_id == "communicate":
    from .npc_event import NPCDialogue
    dialogue = NPCDialogue.for_node(node)  # node.id → appropriate dialogue
    state.npc_state = NPCState(event=dialogue)
    state.screen = ScreenKind.NPC
```

### 요구 사항
- 각 CONSTRUCT 노드 id → NPCDialogue 매핑
- dialogue 내용 (현재 Dixie Flatline만 `_DIXIE_FLATLINE_EVENT`로 하드코딩)
- 추후 6자(CONSTRUCT) 확장

## 전투-던전 연동 수정 (핵심 버그)

### 현재 문제
1. ENGAGE → 전투 시작 → 승리 → `state.screen = MATRIX`로 복귀
2. **해당 ICE 노드가 graph에서 제거되지 않음** → 다시 올 때 같은 전투 재발생
3. `_remove_node_from_graph()`는 `action_menu._execute_action("extract")`에서만 호출

### 수정안

```python
# combat_view.py 또는 새模块

def end_combat(state: AppState, victory: bool) -> None:
    """Handle transition out of COMBAT screen after combat resolves."""
    if victory and state.combat_state is not None:
        # Remove defeated enemy node from graph
        enemy_id = state.combat_state.enemy.id
        ice_node = next((n for n in state.matrix.nodes if n.id == enemy_id), None)
        if ice_node is not None:
            from .combat_view import _remove_node_from_graph
            state.matrix = _remove_node_from_graph(state.matrix, enemy_id)
            state.status_messages.append(f">>> {ice_node.label} defeated and removed")
    state.combat_state = None
    state.screen = ScreenKind.MATRIX
```

### 호출 위치
`app.py` 메인 루프 — COMBAT screen 처리 부분:
```python
if state.screen is ScreenKind.COMBAT and state.combat_state is not None:
    step_combat(state.combat_state)
    if state.combat_state.is_over:  # 새로 추가
        victory = state.combat_state.enemy.hp <= 0
        end_combat(state, victory)
```

## 노드 제거 검증: CombatState에 enemy.id 추가 필요

현재 `CombatState`에 enemy.id 필드가 없음. 추가 필요.

```python
# combat/state.py
@dataclass
class CombatState:
    player: Combatant
    enemy: Combatant
    enemy_id: str = ""  # 추가: graph에서 노드 제거용
    tick_ms: int = 0
    ...
```

##_phase 2 구현 우선순위

1. **P0 (지금)**: 전투 승리 후 ICE 노드 제거
2. **P1**: TRAP 이벤트 (알람 데미지)
3. **P1**: RANDOM_COMBAT (zoneless 랜덤遭遇)
4. **P2**: NPC_ENCOUNTER → 실제 대화
5. **P2**: HACK_SYSTEM → 실제 해킹 미니게임 (스텁 해제)
6. **P3**: CORE_ACCESS → 실제 코어 브리칭

## Special Encounter (v1.1.0+) — Loa 유령신 조우

> **상위 결정**: ADR-0146 (Stage Flow, Draft — user acceptance pending)

DEEP/CORE/TA 존 매트릭스 런 중 무작위로 발생하는 특수 이벤트. 매트릭스 깊이 진입 시 깁슨 원작의 'vodoun Loa' 와 같은 유령 신을 조우.

### 트리거 조건
- 매트릭스 노드 진입 시 확률적 (zone 깊이에 비례해 확률 증가)
- DEEP/CORE/TA 한정. SURFACE/MID/FREESIDE 는 미발생

### 선택지 (3가지)
| 선택 | 결과 |
|------|------|
| **Talk** | Loa 의 메시지 + 데이터 프래그먼트 1개 (깁슨 톤 dialogue) |
| **Fight** | ICE 전투 (Loa = ICE proxy). victory 시 데이터 프래그먼트 2개 |
| **Leave** | 이벤트 종료. 보상 없음 |

### 종료 처리 (ADR-0146 Option 3 Hybrid)
- **`ghost_encounter.is_terminal: true`** — Talk / Fight / Leave 어느 선택이든 encounter 종료 의미
- 다음 stage = `defeat_ice` 으로 main flow 복귀 (fight 선택 시 즉시, 다른 선택 시 다음 매트릭스 노드)
- Stage 종료 후 run 자체는 계속 (run_cycle 종료 아님)

### 디자인 의도
- 깁슨 원작의 Loa / vodoun 시스템 반영 (`Mona Lisa Overdrive` 참조)
- 매트릭스에 'mystical encounter' 측면 부여 — 순수 ICE 전투만 아닌 다양성
- 데이터 fragment 보상으로 player에게 run 중 의미 있는 보상 제공

---

## Hub 사이클 — Black Market (v1.1.0+)

> **상위 결정**: ADR-0146 (Stage Flow, Draft — user acceptance pending)

`black_market` 는 매트릭스가 아닌 **Hub 사이클** 의 일부. run 사이의 credits / materials 거래를 위한 vendor.

### 트리거 조건
- Hub 화면에서 "BLACK MARKET" 메뉴 선택 시 진입
- Run 종료 후 (`complete`, `death_restart` 직후) 첫 pending 으로 복귀하기 직전 단계에서 접근 가능

### 종료 처리 (ADR-0146 Option 3 Hybrid)
- **`black_market → pending` transition** ("after_vendor_exit") — vendor 화면 종료 시 정상 hub 사이클 복귀
- is_terminal: false 유지 (Hub loop 의 일부이므로 terminal 마크 부적절)

### 디자인 의도
- 깁슨 Sprawl 의 'street-level commerce' 측면 (Armitage 의 fixer, Finn 의 정보상)
- Credits / materials 양쪽 모두 거래 (material 은 crafting 시스템 [ADR-0015] 활용)
- Program / deck upgrade 구매 가능 → 다음 run 의 진입 강도 상승


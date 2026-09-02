# 프로로그: Sprawl Jockey (1-2페이지)

> **상위 결정**: `characters.md` (오리지널 주인공 3인)
> **관련**: `../../../Fiction/wiki/works/neuromancer.md`, `count-zero.md`
> **용도**: 1단계 소설 / 2단계 데모 / 3단계 게임
> **엔딩**: 2개 (성공/실패)

---

## 0. 톤 (Setting the scene)

> *"The sky above the port was the color of television, tuned to a dead channel."*
> — William Gibson, *Neuromancer* (1984)

2035년. Sprawl — Boston-Atlanta Metropolitan Axis — 의 50미터 너머 어딘가. 한낮이 진짜인지도 모를. 네온사인이 비를 핥고, 콘솔 카우보이들이 cyberspace에 jack-in 한다. 그리고 그 중 하나가 *당신* 이다.

---

## 1. The Finn's Office (공통 시작)

지하 술집 "The Sprawl Hole". Finn (의뢰자) 의 사무실. 3미터 폭, 6미터 길이. 벽은 옛 CRT와 cable 덕지덕지. Finn은 마흔대 중반, 매너가 모자란 사내. 늘 같은 자리, 늘 같은 질문.

> **Finn:** *"I need a jockey. The Finn's got a job. Sense/Net, first run, simple data extraction."*
> *"ICE is light. Wisp-class, maybe Hammer."*
> *"Don't get fancy. Jack in, find the data, jack out."*

**선택지 (DialogueChoice):**

1. **"I'm new. I just need the money."** (→ Case / Novice)
2. **"I've been around. I know the risks."** (→ Sil / Veteran)
3. **"I'm here to burn it all down."** (→ Kas / Heretic)

(어떤 선택이든 Finn은: *"Good. Dixie'll be your backup. Now get lost."*)

---

## 2. Jack-In (Cyberspace)

Finn's office 뒤편. 낡은 couch. Wetware trodes. ICE-drip.

> **Narrator:** *The Sprawl is hot tonight. You can feel the data streams in your teeth.*

플레이어가 cybernetic trodes를 닿는 순간 — **matrix로 진입**.

> **Cyberspace (시각):**
> ```
>  ░░░░░░░░░░░░░░░░░░░░░░░░░░
>  ░ Sense/Net — Level 1  ░
>  ░  ◢◣◢◣◢◣◢◣◢◣◢◣◢◣  ░
>  ░  ── DATA GRID ──       ░
>  ░  ░▒▓█▓▒░ ░▒▓█▓▒░      ░
>  ░  ░▒▓█▓▒░ ░▒▓█▓▒░      ░
>  ░░░░░░░░░░░░░░░░░░░░░░░░░░
> ```

Matrix 내부는 monochrome grid. 깁슨 1984년의 비전 그대로.

### 2.1 공통 시퀀스 (모든 캐릭터)

1. **Entry node** (Surface) — Data fragment 1개
2. **Data node** — Data fragment 1개 (FINN's data)
3. **ICE node** — Combat 발동

---

## 3. Combat (Wisp-class ICE)

> **ICE:** `▲ICE▲` (cyan triangle)
> **HP:** 12 | **Damage:** 4
> **스킬:** Viral Stun (3 AP)

### 3.1 캐릭터별 combat flavor

**Case (Novice):**
> *Case's hands shake on the deck. Wisp T1. Cheap. But it's all you've got.*

**Sil (Veteran):**
> *Sil's been here before. Hammer T2. The ICE doesn't know what's coming.*

**Kas (Heretic):**
> *Kas's viral isn't a weapon. It's a sermon. "I cast you out."*

### 3.2 Combat 종료 시
- **승리 (공통)**: ICE가 분해됨. Data node 진입 가능.
- **패배 (공통)**: Player HP 0 → Flatline.

---

## 4. Data Extraction

> **Narrator:** *You pull the data from the Sense/Net node. It's a list of names. Employee IDs. Nothing you'd normally pay for.*

플레이어가 추출한 데이터는 **Tessier-Ashpool의 직원 목록**. 그건 Finn이 알려주지 않은 사실.

> **Narrator:** *You jack out. Back in the Sprawl Hole, Finn is already gone. The office is empty. There's a note on the desk:*
>
> **Note:** *"You weren't supposed to see that. — The Finn"*

---

## 5. The Choice (캐릭터별 분기)

> **Narrator:** *Dixie Flatline appears in the construct. The construct that shouldn't exist.*

Dixie (사망한 자키의 construct 사본) 가 등장:

> **Dixie:** *"Hey cowboy. You got the data. Now what you gonna do with it?"*

### 5.1 Case (Novice) 분기

> **Dixie:** *"Burn it. Forget it. Get out of Sprawl. The Finn's gonna come for you."*

**선택지:**
- **A**: *"I burn it. I just wanted the money."* → **엔딩 A (성공)**: 데이터 삭제, Sprawl 탈출.
- **B**: *"I keep it. I might need it someday."* → **엔딩 B (실패)**: Finn이 추적, 케이 flatline.

### 5.2 Sil (Veteran) 분기

> **Dixie:** *"Sil. I know who you are. I knew Mara. (옛 동료 이름). Tessier-Ashpool took her. You know that now."*

**선택지:**
- **A**: *"I leak the data. Tessier-Ashpool dies by a thousand cuts."* → **엔딩 A (성공)**: 데이터 폭로, 복수.
- **B**: *"I take the contract. Tessier-Ashpool pays well for silence."* → **엔딩 B (실패)**: Tessier-Ashpool의 다음 공범이 됨.

### 5.3 Kas (Heretic) 분기

> **Dixie:** *"Kas. Maelcum told me you'd come. He says you're the one to break the wheel."*

**선택지:**
- **A**: *"I cast the data into the Loa network. The Sprawl will hear it."* → **엔딩 A (성공)**: 선언문 배포, Sprawl 변화 시작.
- **B**: *"I take it for myself. Power corrupts. Always."* → **엔딩 B (실패)**: 카스 bio-deck 손상, 추방.

---

## 6. 엔딩 정리

### 엔딩 A: Jockey lives

(성공 — 모든 캐릭터 공통)
- Case: 스프롤에서 탈출, 새로운 자키로 살아남음.
- Sil: 데이터 폭로, 복수 성공. 새로운 적 생성.
- Kas: 선언문 배포, Sprawl 변화 시작.

(스포일러: 이후 게임에서 새로운 의뢰로 연결)

### 엔딩 B: Jockey flatlines

(실패 — 모든 캐릭터 공통)
- Case: Finn이 추적, ICE에 잡힘. Sprawl의 시체 더미에 추가.
- Sil: Tessier-Ashpool의 보복. Sprawl의 시체 더미에 추가.
- Kas: Tessier-Ashpool의 ICE 차단, Loa 네트워크 손상. 자키 네트워크에서 추방.

(스포일러: Pillar 3 — The Flatline)

---

## 7. 구현 노트 (Phase 2, 3용)

### Phase 2 (단축 데모)
- 모든 분기를 검증
- 한 캐릭터 1개, 다른 캐릭터 2개는 텍스트만
- 대시보드 진행률 표시

### Phase 3 (실제 게임)
- 한 캐릭터 1개의 분기를 깊게 구현
- 다른 캐릭터 2개는 메인 흐름 후 unlock
- 엔딩 A → 다음 미션 unlock, 엔딩 B → death screen + retry

### 깁슨 톤 (must-have)
- "the Sprawl", "the money people", "ICE", "deck", "console cowboy" 사용
- Pillar 2 (meatspace 미사용) — 자키의 cyberspace representation만
- ASCII art로 cyberspace 표현
- Bilingual EN + KO

---

## 8. 소설 원문 인용 (Reference)

- *Neuromancer* (1984): "The sky above the port..." (오프닝)
- *Count Zero* (1986): Maelcum, Loa, Freeside
- *Mona Lisa Overdrive* (1988): "Jockey" terminology, "the Sprawl"

깁슨 원문 톤을 빌리되, 등장인물과 사건은 모두 오리지널.

# 오리지널 주인공 3인 (Original Jockeys)

> **상위 결정**: 디자인/문서화 결정 필요 (Draft)
> **관련**: `../../../Fiction/wiki/works/neuromancer.md`, `count-zero.md`, `mona-lisa-overdrive.md`
> **단편 연결**: `../../../Fiction/derivative/sprawl-trilogy/`
> **용도**: 1단계 소설 / 2단계 데모 / 3단계 게임 캐릭터 선택

깁슨 스프롤 3부작 세계관을 배경으로 하되, **등장인물은 모두 오리지널**. 플레이어가 3명 중 한 명을 선택해 다른 이야기를 진행한다.

각 캐릭터는 같은 시작 (Sprawl의 자키, 빚, 의뢰) 을 공유하지만, 동기/성격/엔딩이 다르다.

**각 캐릭터는 Fiction/derivative/ 단편에서 영감을 받음**:
- **케이 (K)** — Case 단편 ("잭아웃 후 30초")
- **실 (Sil)** — Marly 단편 ("루이지아나의 신")
- **카스 (Kas)** — Kumiko 단편 ("매나리사의 자정")

자세한 연결: `wiki/world/derivative_stories.md`

---

## 공통 설정

- **시대**: 2030년대 (Neuromancer 직후~Count Zero 사이)
- **위치**: Boston-Atlanta Metropolitan Axis (Sprawl)
- **작전 모드**: Real-Time with Menu Skills (RT-MS, ADR-0003)
- **메인 루프**: Hub → Jack-In → Cyberspace → Combat → Hub (ADR-0006)

---

## 1. 케이 (Case) — Novice / 초짜

> *"I just wanted to pay off my debt. I didn't ask for this."*

| 항목 | 값 |
|---|---|
| **이름** | 케이 (K) |
| **나이** | 22 |
| **출신** | Chiba City 외곽, 저소득층 |
| **직업** | 신참 콘솔 카우보이 |
| **데크** | Ono-Sendai Cyberspace 7 (T1) |
| **주 무기** | Wisp (T1) |

### 동기
- **빚**: 친척의 의료비 + 대학 학자금. Sprawl의 "the money people"에게 큰 빚.
- 자키가 되어 의뢰를 받으면 빚을 갚을 수 있다고 들었다.

### 성격
- 수줍음, 과묵함
- 약물에 약함 (치바 시의 강화제)
- **결점**: 판단력 부족, 중독 위험

### 플레이북 (Novice 흐름)
```
Sprawl의 Chiba에서 시작
  ↓
Finn (의뢰자)에게 첫 의뢰 수락
  ↓
Sense/Net 데이터 추출
  ↓
ICE (Wisp-class)와 첫 전투 → **패배 위기** → 30% HP
  ↓
Dixie Flatline 등장 (구조)
  ↓
의뢰 완수, 빚 일부 갚음
```

### 엔딩 (Novice)
- **성공 (Case lives)**: 의뢰 완수, 빚 50% 갚음, Dixie와 동맹. Sprawl의 새로운 자키로 살아남음.
- **실패 (Case flatlines)**: ICE에 잡혀 평행선상으로. Sprawl의 시체 더미에 추가.

---

## 2. 실 (Sil) — Veteran / 베테랑

> *"I've done this for fifteen years. I know when a job is too good."*

| 항목 | 값 |
|---|---|
| **이름** | 실 (Sil) |
| **나이** | 38 |
| **출신** | Freeside (L5 식민지)에서 시작, Sprawl로 이주 |
| **직업** | 베테랑 자키, 15년 경력 |
| **데크** | Hosaka Security (T3) |
| **주 무기** | Hammer (T2) + Probe (T2) |

### 동기
- **복수**: 옛 동료/연인이 Tessier-Ashpool 계열 의뢰로 죽음. 진실을 찾고 싶다.
- Sprawl의 그림자 속에서 은퇴하지 못함.

### 성격
- 신중함, 과묵함
- 모든 의뢰를 의심함
- **결점**: 과도한 신중 → 기회 놓침, 외로움

### 플레이북 (Veteran 흐름)
```
Sprawl의 Veteran 자키로 시작
  ↓
Finn (옛 동료의 의뢰자)을 찾아감
  ↓
Dixie Flatline이 의뢰를 거절함 (위험함)
  ↓
직접 Sense/Net에 침투
  ↓
ICE (Hammer-class) 다수와 전투
  ↓
데이터 발견: 옛 동료의 죽음은 의뢰가 아닌 **Tessier-Ashpool의 처리**
  ↓
동료의 복수 vs 자키 윤리 사이 선택
```

### 엔딩 (Veteran)
- **성공 (Sil walks away)**: Tessier-Ashpool의 진실을 일부 폭로. 동료 복수에 성공하지만, Sprawl에 새로운 적이 생김. 자키로 계속 살아남음.
- **실패 (Sil flatlines)**: Tessier-Ashpool의 보복에 당함. Sprawl의 시체 더미에 추가.

---

## 3. 카스 (Kas) — Heretic / 이단자

> *"The system is the virus. I'm the cure."*

| 항목 | 값 |
|---|---|
| **이름** | 카스 (Kas) |
| **나이** | 28 |
| **출신** | Sprawl의 Loa/Vodou 커뮤니티 |
| **직업** | 반체제 해커, 테크노맨서 |
| **데크** | MaaS BioSystems (T2, bio-organic) |
| **주 무기** | Viral (커스텀 T2, ICE 감염형) |

### 동기
- **시스템 폭로**: Sprawl의 거대 메가코프 (Tessier-Ashpool, Hosaka, MaaS BioSystems)의 비리를 폭로하고 싶다.
- 자키가 아니라 **혁명가**. 데이터보다 **선언문**이 필요.

### 성격
- 광신적, 카리스마
- Loa/Vodou 신앙이 깊음 (Count Zero의 Maelcum/Loa 연결)
- **결점**: 망상, 동료 신뢰 부족, 자기 파괴적

### 플레이북 (Heretic 흐름)
```
Sprawl의 이단자 자키로 시작
  ↓
Maelcum (Loa 보유자)로부터 의뢰 받음: "Tessier-Ashpool의 계획을 폭로하라"
  ↓
Sense/Net에 침투, 동시에 ICE와 Loa를 사용
  ↓
발견: Tessier-Ashpool이 **새로운 ICE-AI**를 시험 중
  ↓
데이터 추출 (Viral 스킬로 ICE 감염)
  ↓
Maelcum에게 전달 → Loa 네트워크로 Sprawl 전역에 **선언문 배포**
  ↓
Tessier-Ashpool의 보복 — Sprawl에 새로운 전쟁 시작
```

### 엔딩 (Heretic)
- **성공 (Kas changes Sprawl)**: 선언문 배포 성공. Tessier-Ashpool의 비리 일부 폭로. Sprawl의 약한 자키들이 영감을 받음. 하지만 Tessier-Ashpool은 "Casano-virus"로 카스를 표시함.
- **실패 (Kas silenced)**: Tessier-Ashpool이 ICE로 Loa 네트워크 차단. 카스 bio-deck 손상. 자키 네트워크에서 영원히 추방.

---

## 4. 3인 비교표

| 항목 | Case (Novice) | Sil (Veteran) | Kas (Heretic) |
|---|---|---|---|
| **나이** | 22 | 38 | 28 |
| **데크 티어** | T1 | T3 | T2 (bio) |
| **주 무기** | Wisp (T1) | Hammer (T2) | Viral (T2 커스텀) |
| **동기** | 빚 (생존) | 복수 | 시스템 폭로 |
| **연관 등장인물** | Finn, Dixie | Finn, Armitage | Maelcum, Loa |
| **엔딩 A** | 케이 살아남음 | 실 복수 성공 | 카스 Sprawl 변화 |
| **엔딩 B** | 케이 flatline | 실 flatline | 카스 침묵 |

---

## 5. 캐릭터 선택 (Game flow)

1. **Hub에서 의뢰 받기** (ADR-0010, JobBoard)
2. **Finn이 의뢰 설명** ("I need a jockey. Which one are you?")
3. **선택지** (DialogueChoice):
   - "I'm new. I just need the money." → Case
   - "I've been around. I know the risks." → Sil
   - "I'm here to burn it all down." → Kas
4. **선택한 캐릭터의 storyline으로 진입**

(2단계 데모에서 3개 분기 모두 구현. 3단계 게임에서 1개만 깊게 구현)

---

## 6. 깁슨 톤 체크리스트

각 캐릭터/스토리는 다음을 만족해야 함:
- [ ] Sprawl의 어두운 톤 유지
- [ ] Pillar 5 (The Style): monospace, ASCII, cyberpunk aesthetic
- [ ] Pillar 2 (Meatspace 미사용): 자키의 cyberspace representation만
- [ ] 콘솔 카우보이/자키 정체성
- [ ] "the money people", "the Sprawl", "ICE" 등 깁슨 용어 사용
- [ ] 소설 원문 인용 또는 톤 차용 (Fiction wiki 참조)

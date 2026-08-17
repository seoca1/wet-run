#!/usr/bin/env python3
"""Add new mission 'ono_sendai_repair' to wet_run missions.json.

Pairs with Fiction Phase 24 — Ono-Sendai concept page (wiki/concepts/ono-sendai.md).
Novice-arc, Arc 1: Case's pre-recruitment deck-repair scenario in Chiba.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "ono_sendai_repair",
    "title": "Ono-Sendai Repair",
    "story": {
        "synopsis_en": "The Cyberspace 7 has been through three Chiba caps and one too many jack-outs. K can feel it in the back of his skull, a low-level buzz where the Ono-Sendai meet the cortex, the deck's bio-electrical interface degrading like an old Hosaka terminal on its second life. He needs it repaired. He doesn't have credit for the Ono-Sendai service clinic on the eighth floor — the real Ono-Sendai shop, the brand office, where the Cyberspace 7's calibration is performed with proprietary Ono-Sendai diagnostic rigs. He has enough for the street-corner jack-doc on the fourteenth — Pavel-equipment, no warranty, the technician who can fix a cracked interface but can't tell a deck from a deck-chair. K goes up the eighth. The brand office won't take him. The rep looks at the deck, looks at K, looks at the deck again. The rep is maybe thirty. The deck is older than the rep. K is younger than the rep. The rep says the kinds of things reps say, things about corporate client-rights and minimum-purchase thresholds and the Cyberspace 7's discontinued status. K has a brief life-flash moment. The brief life-flash moment is what working-class matrix-labor feel when Ono-Sendai stops recognizing them. The deck is the working-class substrate; the brand office's non-recognition is the substrate's working-class cut-off. K leaves the eighth floor. The street-corner jack-doc on the fourteenth fixes the cracked interface. The fix is partial. The deck runs at eighty percent of its designed capability. K is okay with eighty percent. Eighty percent is the working-class matrix-operative's standard operating capability. Eighty percent is what the Chiba port districts' grifting economy can afford. K walks out into the rain. The rain is still the same color as the data. The deck on his head is still the same brand — Ono-Sendai. Just less of it. The brand office's non-recognition is what the working-class matrix-operatives experience as the era's substrate-pricing.",
        "synopsis_ko": "Cyberspace 7은 세 번의 치바 캡슐과 잭아웃 한 번을 더 거쳤다. K는 그것을 후두골 안쪽에서, Ono-Sendai가 대뇌 피질에 만나는 곳의 저-레벨 윙윙거림으로 느낄 수 있다 — 디크의 생물-전기 인터페이스가 두 번째 인생의 오래된 Hosaka 터미널처럼 열화되는 것. 그는 그것을 수리해야 한다. 그는 8층의 Ono-Sendai 서비스 클리닉 — 진짜 Ono-Sendai 매장, 브랜드 사무실, 전용 Ono-Sendai 진단 장비로 Cyberspace 7의 보정이 수행되는 곳 — 에 지불할 크레딧이 없다. 그는 14층의 거리-구석 잭-닥터에게는 충분히 가지고 있다 — 파벨급 장비, 보증 없음, 크랙된 인터페이스는 고칠 수 있지만 디크와 디크-의자를 구별 못 하는 기술자. K는 8층으로 간다. 브랜드 사무실은 그를 받아주지 않는다. 영업 사원은 디크를 보고, K를 보고, 디크를 다시 본다. 영업 사원은 서른쯤. 디크는 영업 사원보다 오래되었다. K는 영업 사원보다 어리다. 영업 사원은 영업 사원이 하는 종류의 말들을 한다 — 기업 고객-권리에 대한 것들, 최소-구매-임계값에 대한 것들, Cyberspace 7의 단종-상태에 대한 것들. K는 짧은 인생-플래시 순간을 가진다. 짧은 인생-플래시 순간은 Ono-Sendai가 그를 인식하지 않을 때 작업-클래스 매트릭스-노동이 느끼는 것이다. 디크는 작업-클래스 기질; 브랜드 사무실의 비-인식은 기질의 작업-클래스 차단. K는 8층을 떠난다. 14층의 거리-구석 잭-닥터가 크랙된 인터페이스를 고친다. 수리는 부분적이다. 디크는 설계-능력의 80 퍼센트로 작동한다. K는 80 퍼센트에 만족한다. 80 퍼센트는 작업-클래스 매트릭스-운영자의 표준 작동 능력이다. 80 퍼센트는 치바 항구 지구의 그리핑 경제가 감당할 수 있는 것이다. K는 비 속으로 걸어 나온다. 비는 여전히 데이터와 같은 색이다. 머리의 디크는 여전히 같은 브랜드 — Ono-Sendai. 단지 조금 더 작다. 브랜드 사무실의 비-인식이 작업-클래스 매트릭스-운영자가 시대의 기질-가격 책정으로 경험하는 것이다.",
        "source": "ono_sendai_repair",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "purpose",
        "word_count_en": 295,
        "char_count_ko": 728,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "extract_data",
        "data_id": "deck_repair_quote"
    },
    "secondary_objectives": [
        {
            "type": "negotiate",
            "target": "ono_sendai_rep",
            "count": 1
        },
        {
            "type": "acquire",
            "target": "street_doc_repair",
            "count": 1
        }
    ],
    "matrix_seed": 318,
    "zone": "surface",
    "rewards": {
        "credits": 350,
        "materials": {
            "data_fragment": 1,
            "deck_part": 1
        }
    },
    "arc": 1
}

with open(ROOT) as f:
    data = json.load(f)

if new_mission["id"] in data:
    print(f'WARN: {new_mission["id"]} already exists, skipping')
else:
    data[new_mission["id"]] = new_mission
    with open(ROOT, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'Added mission {new_mission["id"]}')
    print(f'Total missions: {len(data)}')

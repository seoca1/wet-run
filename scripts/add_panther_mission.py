#!/usr/bin/env python3
"""Add new mission 'panther_negotiate' to wet_run missions.json."""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "panther_negotiate",
    "title": "Panther Negotiate",
    "story": {
        "synopsis_en": "The Moderns want to talk. They don't come up to the deck and say so — they pipe it through a cuttle-cassette left in the bass drum of the Falconer's lounge, the cuttle the Moderns favor for retainer-class negotiations. Finn plays it sideways under the table while the runner eats shabu up at Chiba's port district. The runner knows what's coming. Retainer-class work — corporate extractions that want counter-operative cosmetic — don't pay the Moderns to look like Moderns on the run. They pay the Moderns to look like the corporate employer's chosen-cowboy on the run. The Panther Moderns' retainer offer is the corporate employer's stylistic. The runner now wears the right Z-surge jacket, walks with a Chiba-strut calibrated to Sense/Net's preferred hiring profile, and jacks into a Tessier-Ashpool core designed to look, to ICE, like a Sense/Net extract. The Moderns are paid for looking the part. The runner is paid for playing it. The ICE doesn't see the difference because the difference is, in the era's late-Capitalist retainer logic, the same thing.",
        "synopsis_ko": "모던스가 협상을 걸어왔다. 직접 와서 말한 게 아니라 — 페이콘어 라운지의 베이스 드럼 안에 묻어둔 컷틀 카세트를 통해서, 모던스가 리테이너 클래스 협상에 선호하는 그 컷틀로. 핀은 러너가 치바의 항구 지구에서 샤부를 먹고 있을 때 식탁 아래에서 그것을 사선으로 틀어놓았다. 러너는 뭘 봐오는지 안다. 리테이너 클래스 작업 — 카운터 오퍼레이티브 코스메틱을 원하는 기업 추출 — 는 모던스에게 모던스처럼 달리는 값을 치지 않는다. 그들은 모던스에게 모던스가 아니라 기업이 뽑은 카우보이처럼 달리는 값을 친다. 팬서 모던스의 리테이너 제안은 기업이 원하는 스타일이다. 러너는 이제 맞는 Z-서지 재킷을 걸치고, Sense/Net이 선호하는 채용 프로필에 보정 맞춘 치바-스트룻으로 걷고, Sense/Net 추출처럼 ICE에게 보이도록 설계된 T-A 코어에 잭을 꽂는다. 모던스는 그 역할을 연기한 돈을 받는다. 러너는 그 역할을 수행한 돈을 받는다. 시대의 후기 자본주의 리테이너 논리에서, 그 차이는 같은 거니까, ICE가 그 차이를 보지 못한다.",
        "source": "panther_negotiate",
        "character_ref": "veteran",
        "arc": 2,
        "pillar": "power",
        "word_count_en": 195,
        "char_count_ko": 487,
        "cast": "sil"
    },
    "fixer": "finn",
    "grade_min": 2,
    "grade_max": 3,
    "primary_objective": {
        "type": "extract_data",
        "data_id": "sense_net_disguise"
    },
    "secondary_objectives": [
        {
            "type": "defeat",
            "enemy": "ice.construct",
            "count": 2
        },
        {
            "type": "deliver",
            "target": "panther_handling",
            "count": 1
        }
    ],
    "matrix_seed": 1083,
    "zone": "surface",
    "rewards": {
        "credits": 1100,
        "materials": {
            "data_fragment": 4,
            "unique_construct": 1
        }
    },
    "arc": 2
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

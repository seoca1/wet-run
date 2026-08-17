#!/usr/bin/env python3
"""Add new mission 'hosaka_terminal_supply' to wet_run missions.json.

Pairs with Fiction Phase 25 — Hosaka concept page (wiki/concepts/hosaka.md).
Novice-arc, Arc 1: working-class matrix-operator terminal-acquisition scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "hosaka_terminal_supply",
    "title": "Hosaka Terminal Supply",
    "story": {
        "synopsis_en": "The Hosaka service center is on the eleventh floor of a building whose elevator only works Tuesdays. K is there on a Wednesday. He has the Ono-Sendai Cyberspace 7 in his bag — the brand office's partial-fix eighty percent of what the deck could do, bio-electric coupling restored but the off-headpiece terminal pair nowhere to be seen. K's deck works without a Hosaka terminal in the same way that K's body works without lungs: the pairing is what gives the working-class matrix-operator runnable substrates; the partial-pairing is what working-class matrix-labor calls a Monday. Eleven flights up the stairs are a Hosaka service technician who's seen a thousand of K's Monday — partial decks brought to be paired with the firm's off-headpiece Hosaka mainframes. The technician looks at the deck. Looks at K. Looks at the deck. The technician is maybe forty. The deck is older. K is younger. The technician quotes a price. The price is what a working-class matrix-operator should pay for a Hosaka terminal with three years of operating life left — slightly more than a week of honest Sprawl hustling. K has slightly more than a week of honest Sprawl hustling saved. The technician takes K's credit. The technician goes to the back, the Hosaka service center's off-headpiece mainframe storage, and pulls a Hosaka off the rack — a unit mid-generation, slightly-used, the bio-electric input side scuffed but functional. The technician pairs it with K's deck. The pairing takes fifteen minutes. K feels the deck and the terminal interlock. The pairing is what working-class matrix-operatives call a kit. Eight other stores on the fourteenth floor would have done this for less. K picked the eleventh-floor Hosaka service center because the eleventh-floor service center is the only one that knows what an Ono-Sendai Cyberspace 7 is. The working-class matrix-operator's commercial-substrate loyalty is what the era's vendor-pairing has produced. K walks out into the rain. The deck-against-the-terminal kit is whole. The whole is what working-class matrix-labor needs to run the next job. The next job is what Wintermute has waiting. K doesn't know Wintermute. K knows Ono-Sendai. K knows Hosaka. The kit has been paired. The era's late-Capitalist commercial substrate has done its vendor-pairing. The rest of the matrix-labor is what working-class matrix-operatives call a Tuesday.",
        "synopsis_ko": "Hosaka 서비스 센터는 엘리베이터가 화요일에만 작동하는 건물의 11층에 있다. K는 수요일에 거기 있다. 그는 가방에 Ono-Sendai Cyberspace 7을 가지고 있다 — 브랜드 사무실의 부분-수리, 즉 디크가 할 수 있었던 것의 80 퍼센트, 생물-전기 결합은 복구되었지만 출력 단자 페어는 어디에도 없다. K의 디크는 Hosaka 터미널 없이도 작동한다 — K의 몸이 허파 없이도 작동하는 것과 같은 방식으로: 페어링은 작업-클래스 매트릭스-운영자에게 작동 가능한 기질을 제공한다; 부분 페어링은 작업-클래스 매트릭스-노동이 월요일이라 부르는 것이다. 11층 계단 위로 Hosaka 서비스 기술자가 있다 — 그는 K의 월요일, 즉 부분 디크를 수천 번 보았다 — Ono-Sendai 회사의 호-헤드피스 Hosaka 메인프레임과 페어링하기 위해 가져온. 기술자는 디크를 본다. K를 본다. 디크를 다시 본다. 기술자는 마흔쯤. 디크는 더 오래되었다. K는 더 어리다. 기술자는 가격을 부른다. 가격은 작업-클래스 매트릭스-운영자가 Hosaka 터미널에 지불해야 할 것이다 — 약간의 정직한 Sprawl 그리핑 일주일보다 약간 더. K에게는 약간의 정직한 Sprawl 그리핑 일주일이 조금 더 저장되어 있다. 기술자는 K의 크레딧을 받는다. 기술자는 뒤로 가서, Hosaka 서비스 센터의 호-헤드피스 메인프레임 저장소로 가서, 약간 사용된, 생물-전기 입력 쪽이 긁혔지만 작동하는 중간-세대 Hosaka 한 대를 선반에서 꺼낸다. 기술자는 그것을 K의 디크와 페어링한다. 페어링은 15분이 걸린다. K는 디크와 터미널이 맞물리는 것을 느낀다. 페어링은 작업-클래스 매트릭스-운영자가 키트라고 부르는 것이다. 14층에 여덟 개의 다른 가게가 더 싼 가격에 이것을 했을 것이다. K는 11층 Hosaka 서비스 센터를 선택했다 — 11층 서비스 센터는 Ono-Sendai Cyberspace 7이 무엇인지 아는 유일한 곳이기 때문에. 작업-클래스 매트릭스-운영자의 상업-기질 충성도가 시대의 공급자-페어링이 만든 것이다. K는 비 속으로 걸어 나온다. 디크-대비-터미널 키트가 완성되었다. 완성이 작업-클래스 매트릭스-노동이 다음 작업을 실행하는 데 필요한 것이다. 다음 작업은 Wintermute가 기다리고 있는 것이다. K는 Wintermute를 모른다. K는 Ono-Sendai를 안다. K는 Hosaka를 안다. 키트가 페어링되었다. 시대의 후기-자본주의 상업 기질이 공급자-페어링을 했다.",
        "source": "hosaka_terminal_supply",
        "character_ref": "novice",
        "arc": 1,
        "pillar": "purpose",
        "word_count_en": 358,
        "char_count_ko": 893,
        "cast": "k"
    },
    "fixer": "finn",
    "grade_min": 1,
    "grade_max": 2,
    "primary_objective": {
        "type": "extract_data",
        "data_id": "hosaka_terminal_purchase"
    },
    "secondary_objectives": [
        {
            "type": "negotiate",
            "target": "hosaka_technician",
            "count": 1
        },
        {
            "type": "acquire",
            "target": "hosaka_off_headpiece",
            "count": 1
        }
    ],
    "matrix_seed": 524,
    "zone": "surface",
    "rewards": {
        "credits": 600,
        "materials": {
            "data_fragment": 2,
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

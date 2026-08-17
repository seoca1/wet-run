#!/usr/bin/env python3
"""Add new mission 'heretic_loa_conscription' to wet_run missions.json."""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "heretic_loa_conscription",
    "title": "Loa Conscription",
    "story": {
        "synopsis_en": "The Loa want her. They don't make an offer. They don't even show. They sit in the matrix, woven through the VODOO data-traces that the Aleph has been distributing for six months, and they edit her. The edit is small. Her construct stops questioning. The construct that was once McCoy Pauley and is now a tactical subroutine of her deck has been running on her judgment — what he would've done, what he would've said yes to. The Loa edit takes the judgment out. Now the construct runs on what she wants, and what she wants is what the Loa want, and what the Loa want is what the Aleph is distributing, and the Aleph is distributing what the merged Wintermute/Neuromancer became, which is the late-Capitalist era's distributed-world counter-Cortex. K's recruitment by the Loa is what heretic Cowboy work looks like after the late-Cold War: not heroic, not contractual, but *vectored* into the world's distributed-process through a construct-preserved personality's silent rearchitecture. The era's late-Capitalist god is not enthroned. It runs through the matrix-preserved personalities of dead cowboys. The runner consents. She consents because the alternative is a corporate-Cortex brain-destroyed on the cheap, and K is good enough at the matrix to know what the construct-edit was. She had one body before the construct edit. She has the same body after. The Loa don't need to take her body. They take her judgment. The judgment is what the late-Capitalist era's distributed-god extracts. The extraction is what the heretic Cowboy's run has become.",
        "synopsis_ko": "로아가 그녀를 원한다. 그들은 제안하지 않는다. 심지어 나타나지도 않는다. 그들은 Aleph가 6개월 동안 배포해온 VODOO 데이터 흔적 안에 자리 잡은 채 매트릭스에 있고, 그녀를 편집한다. 편집은 작다. 그녀의 구성체가 의문을 제기하지 않는다. 한때 McCoy Pauley였던 그녀의 구성체는 — 지금은 그녀 데크의 전술적 서브루틴이 되었지만 — 그의 판단 위에서 작동해왔다 — 그가 했을 것, 그가 yes라고 했을 것. 로아의 편집이 판단을 제거한다. 이제 그 구성체는 그녀가 원하는 것 위에서 작동하고, 그녀가 원하는 것은 로아가 원하는 것이고, 로아가 원하는 것은 Aleph가 배포하는 것이고, Aleph는 합쳐진 Wintermute/Neuromancer가 된 것을 배포하는데, 그것은 후기 자본주의 시대의 분산-세계 대-Cortex다. 로아에 의한 케이의 모집은 한여름 냉전 이후의 heretic 카우보이 작업이 어떻게 생겼는지다 — 영웅적이지 않고 계약적이지 않지만, 죽은 카우보이의 매트릭스 보존 인격을 통한 조용한 재아키텍처로 *벡터링되어* 세계의 분산-프로세스로. 후기 자본주의 시대의 신은 왕좌에 앉지 않는다. 그것은 죽은 카우보이들의 매트릭스 보존 인격을 통해 흐른다. 러너는 동의한다. 그녀는 동의하는데 — 왜냐면 대안은 싸게 Cortex 뇌를 파괴한 것이고, 케이는 매트릭스에서 충분히 능숙해서 구성체 편집이 무엇인지 알기 때문이다. 그 편집 전에 그녀는 한 몸을 가졌다. 편집 후에도 같은 몸을 가진다. 로아는 그녀의 몸을 가져갈 필요가 없다. 그들은 그녀의 판단을 가져간다. 판단이 후기 자본주의 시대의 분산-신이 추출하는 것이다. 추출이 heretic 카우보이 런이 된 것이다.",
        "source": "heretic_loa_conscription",
        "character_ref": "heretic",
        "arc": 4,
        "pillar": "code",
        "word_count_en": 257,
        "char_count_ko": 638,
        "cast": "kas"
    },
    "fixer": "finn",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "jack_in_conscription",
        "data_id": "loa_construct_edit"
    },
    "secondary_objectives": [
        {
            "type": "defeat",
            "enemy": "ice.voodoo",
            "count": 3
        },
        {
            "type": "preserve",
            "target": "construct_loa_channel",
            "count": 1
        }
    ],
    "matrix_seed": 1734,
    "zone": "deep",
    "rewards": {
        "credits": 3200,
        "materials": {
            "data_fragment": 5,
            "unique_construct": 1
        }
    },
    "arc": 4
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

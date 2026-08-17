#!/usr/bin/env python3
"""Add new mission 'sense_net_archive_intrusion' to wet_run missions.json.

Pairs with Fiction Phase 26 — Sense/Net concept page (wiki/concepts/sense-net.md).
Suit-arc, Arc 4: corporate-defensive operation operationalizing the Sense/Net
data-archival monopoly substrate as an intrusion-detection defensive scenario.
"""
import json
from pathlib import Path

ROOT = Path('prototype/data/missions/missions.json')

new_mission = {
    "id": "sense_net_archive_intrusion",
    "title": "Sense/Net Archive Intrusion",
    "story": {
        "synopsis_en": "The Suit's office gets the call at 0300. A Sense/Net archive has been probed. Three Cowboy-class operators — not the usual hustler-class, not the working-class hounds that show up for the daily-grind extractions — three *professionals* have been working their way through Sense/Net's first-defense perimeter for the better part of an hour. The Suit logs in. The Suit has credentials Sense/Net doesn't quite know how to invalidate — corporate-erasure protection that pays for itself in moments exactly like this one. The Suit reads the intrusion profile. Three professionals, working in concert. Each one separately skilled; together, a coordinated probe. Sense/Net's first-defense ICE has been doing its work. The probe has cost each operator a constructed presence. The probes have left traces: a sequence of operation-patterns that the Sense/Net ICE has marked as Cowboy-class intrusion traces. The Suit reads the trace-patterns. The trace-patterns have a seasonal marker — they're the trace-pattern of a *sense-net-class* hired operative, not a freelance Cowboy. The hires are inside the Sense/Net ecosystem. The hires are staffed by someone in the Sense/Net corporate layer. The Sense/Net corporate layer uses its own internal defensive-class hires to test its own defenses; the test is what the Sense/Net trace-profile suggests. The Suit recognizes the trace. The Suit recognizes who paid for the test. The test-failure on Sense/Net's perimeter is the operative-class hedge-fund's preferred quarterly-review signal — the Sense/Net defensive architecture has a measurable weakness, the weakness is what the quarterly-review measures. The Suit's job is to find the weakness before the quarterly-review does. The Suit finds the weakness. The Suit knows what to do with the weakness. The Suit confirms the weakness is what would have made the season if it had been left unpatched. The Suit files the post-test report. The post-test report is what the Sense/Net corporate layer reads as a quarterly-reassurance signal. The reassurance is what the Sense/Net corporate layer's data-monopoly has required. The Suit, in this run, has done the data-monopoly's most-arcanely-technocratic work. The Suit's working-day is Sense/Net's most-intimate statework. The Suit gets paid. The Suit goes home. The data-monopoly continues.",
        "synopsis_ko": "이 Suit의 사무실에는 0300에 전화가 온다. Sense/Net 데이터 보관소가 점검을 받았다 — 세 명의 카우보이-급 운영자가 — 일상적인 허슬러-급도 아니고 매일-분쇄 추출에 나타나는 작업-급 사냥개도 아닌 — 세 명의 *전문가*가 거의 한 시간 동안 Sense/Net의 1차 방어 외곽을 통과해 작업하고 있었다. Suit는 로그인한다. Suit는 Sense/Net이 무효화하는 방법을 정확히 모르는 자격증명을 가지고 있다 — 바로 이런 순간에 가치를 증명하는 기업-삭제 보호. Suit는 침투 프로파일을 읽는다. 세 명의 전문가, 협력하여 작업. 각각은 개별적으로 능숙; 함께, 조정된 점검. Sense/Net의 1차 방어 ICE가 자기 일을 해왔다. 점검이 각각의 운영자에게 구성된 프레젠스를 값을 치게 했다. 점검은 흔적을 남겼다: Sense/Net ICE가 카우보이-급 침투 흔적으로 표시한 일련의 작동-패턴. Suit는 흔적-패턴을 읽는다. 흔적-패턴은 계절적 표식을 가지고 있다 — 그것은 *Sense/Net 급* 고용 운영자의 흔적-패턴이지, 프리랜서 카우보이의 것이 아니다. 고용은 Sense/Net 생태계 내부에 있다. 고용은 Sense/Net 기업 계층의 누군가가 했다. Sense/Net 기업 계층은 자신의 내부 방어-급 고용을 사용하여 자신의 방어를 테스트한다; 테스트가 Sense/Net 흔적-프로파일이 제안하는 것이다. Suit는 흔적을 인식한다. Suit는 누가 테스트 비용을 지불했는지 인식한다. Sense/Net 외곽의 테스트-실패는 운영자-급 헤지-펀드의 선호하는 분기-검토 신호이다 — Sense/Net 방어 아키텍처는 측정 가능한 약점을 가지고, 약점이 분기-검토가 측정하는 것이다. Suit의 일은 분기-검토보다 먼저 약점을 찾는 것이다. Suit는 약점을 찾는다. Suit는 약점으로 무엇을 해야 하는지 안다. Suit는 그것이 패치되지 않고 남겨졌다면 이번 시즌의 결과를 만들었을 약점임을 확인한다. Suit는 사후-테스트 보고서를 제출한다. 사후-테스트 보고서는 Sense/Net 기업 계층이 분기-재확신 신호로 읽는 것이다. 재확신은 Sense/Net 기업 계층의 데이터-독점이 요구한 것이다. Suit는 이번 런에서 데이터-독점의 가장-신비롭게-기술관료적인 작업을 했다. Suit의 작업-일은 Sense/Net의 가장-친밀한 국가-작업이다. Suit는 급여를 받는다. Suit는 집에 간다. 데이터-독점이 계속된다.",
        "source": "sense_net_archive_intrusion",
        "character_ref": "suit",
        "arc": 4,
        "pillar": "purpose",
        "word_count_en": 379,
        "char_count_ko": 924,
        "cast": "slick_henry"
    },
    "fixer": "slick-henry",
    "grade_min": 4,
    "grade_max": 5,
    "primary_objective": {
        "type": "patch_ice_vulnerability",
        "data_id": "sense_net_perimeter"
    },
    "secondary_objectives": [
        {
            "type": "identify",
            "target": "intrusion_signature",
            "count": 1
        },
        {
            "type": "ratify",
            "target": "quarterly_review_signal",
            "count": 1
        }
    ],
    "matrix_seed": 1741,
    "zone": "deep",
    "rewards": {
        "credits": 2800,
        "materials": {
            "data_fragment": 6,
            "corporate_chit": 1
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

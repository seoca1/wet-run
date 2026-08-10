"""
ADR-0051 validation: all missions have complete story metadata.
"""

import json
from pathlib import Path

import pytest

MISSIONS_PATH = Path(__file__).parent.parent.parent / "data" / "missions" / "missions.json"


class TestMissionsStoryMetadata:
    """Validate story metadata completeness per ADR-0051."""

    @pytest.fixture
    def missions(self):
        with open(MISSIONS_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_all_missions_have_story_field(self, missions):
        missing = [mid for mid, m in missions.items() if "story" not in m]
        assert not missing, f"Missions missing story field: {missing}"

    def test_story_fields_present(self, missions):
        required = {
            "synopsis_en",
            "synopsis_ko",
            "source",
            "character_ref",
            "arc",
            "pillar",
            "word_count_en",
            "char_count_ko",
        }
        for mid, m in missions.items():
            missing = required - set(m.get("story", {}).keys())
            assert not missing, f"{mid}: missing {missing}"

    def test_synopsis_en_word_count(self, missions):
        for mid, m in missions.items():
            syn = m["story"]["synopsis_en"]
            wc = m["story"]["word_count_en"]
            actual = len(syn.split())
            assert actual == wc, f"{mid}: word_count_en={wc} but actual={actual}"

    def test_synopsis_ko_char_count(self, missions):
        for mid, m in missions.items():
            syn = m["story"]["synopsis_ko"]
            cc = m["story"]["char_count_ko"]
            actual = len(syn.replace(" ", "").replace("\n", ""))
            assert actual == cc, f"{mid}: char_count_ko={cc} but actual={actual}"

    def test_arc_range(self, missions):
        for mid, m in missions.items():
            arc = m["story"]["arc"]
            assert 1 <= arc <= 6, f"{mid}: arc={arc} out of range 1-6"

    def test_character_ref_valid(self, missions):
        facts_path = MISSIONS_PATH.parent.parent.parent / "data" / "game_facts.json"
        with facts_path.open(encoding="utf-8") as f:
            facts = json.load(f)
        valid_chars = set(facts.get("character_ids", []))
        for mid, m in missions.items():
            char = m["story"]["character_ref"]
            assert char in valid_chars, f"{mid}: character_ref={char} not in {valid_chars}"

    def test_pillar_valid(self, missions):
        valid_pillars = {"identity", "power", "memory", "code", "resonance", "people", "purpose"}
        for mid, m in missions.items():
            pillar = m["story"]["pillar"]
            assert pillar in valid_pillars, f"{mid}: pillar={pillar} not in {valid_pillars}"

    def test_ko_no_chinese_chars(self, missions):
        for mid, m in missions.items():
            syn_ko = m["story"]["synopsis_ko"]
            for ch in "的一是不了人我在有他这为之大来以":
                assert ch not in syn_ko, f"{mid}: Korean synopsis contains Chinese char '{ch}'"

    def test_gibson_voice_synopsis_en(self, missions):
        gibson_words = {
            "sprawl",
            "matrix",
            "jacked",
            "ice",
            "deck",
            "simstim",
            "cowboy",
            "icebreaker",
            "megacorp",
            "corp",
            "console",
            "data",
            "construct",
            "soul",
            "ghost",
            "constructs",
            "warrior",
            "romantic",
            "death",
            "love",
            "watching",
            "truth",
            "merger",
            "freeside",
            "zion",
            "ninsei",
            "vegas",
            "tessier",
            "ashpool",
            "wintermute",
            "neuromancer",
            "bartender",
            "shuttle",
            "subsidiary",
            "surveillance",
            "corridor",
            "finn",
            "cowboys",
            "bar",
            "job",
            "run",
            "cargo",
            "message",
            "born",
            "drink",
            "night",
            "face",
            "choice",
            "favor",
            "die",
            "dying",
            "voodoo",
            "loa",
            "wake",
            "sleep",
            "dream",
            "aleph",
            "fragment",
        }
        for mid, m in missions.items():
            syn = m["story"]["synopsis_en"].lower()
            found = [w for w in gibson_words if w in syn]
            assert len(found) >= 1, f"{mid}: synopsis_en lacks Gibson vocabulary (found {found})"

    def test_synopsis_en_min_words(self, missions):
        for mid, m in missions.items():
            syn = m["story"]["synopsis_en"]
            wc = len(syn.split())
            assert wc >= 20, f"{mid}: synopsis_en < 20 words ({wc})"

    def test_synopsis_ko_min_chars(self, missions):
        for mid, m in missions.items():
            syn = m["story"]["synopsis_ko"]
            actual = len(syn.replace(" ", "").replace("\n", ""))
            assert actual >= 50, f"{mid}: synopsis_ko < 50 chars ({actual})"

    def test_source_field_values(self, missions):
        for mid, m in missions.items():
            source = m["story"]["source"]
            assert isinstance(source, str), f"{mid}: source is not str: {type(source)}"
            assert len(source) > 0, f"{mid}: source is empty"

    def test_missions_count(self, missions):
        assert len(missions) >= 15, f"Expected at least 15 missions, got {len(missions)}"

    def test_each_arc_represented(self, missions):
        arcs = {m["story"]["arc"] for m in missions.values()}
        assert arcs == {1, 2, 3, 4, 5, 6}, f"Not all arcs 1-6 represented: {arcs}"

    def test_arc_top_level_matches_story_arc(self, missions):
        mismatches = []
        for mid, m in missions.items():
            if "arc" in m and "story" in m:
                if m["arc"] != m["story"]["arc"]:
                    mismatches.append(
                        f"{mid}: top-level={m['arc']} vs story.arc={m['story']['arc']}"
                    )
        assert not mismatches, mismatches

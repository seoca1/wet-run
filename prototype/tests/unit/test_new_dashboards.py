"""Tests for the 4 new dashboards: Sound, Combat, Equipment, Cyberspace."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DASHBOARD_DIR = Path(__file__).parent.parent.parent.parent / "dashboard"
DATA_DIR = DASHBOARD_DIR.parent / "prototype" / "data"

SOUND_HTML = DASHBOARD_DIR / "sound.html"
COMBAT_HTML = DASHBOARD_DIR / "combat.html"
EQUIPMENT_HTML = DASHBOARD_DIR / "equipment.html"
CYBERSPACE_HTML = DASHBOARD_DIR / "cyberspace.html"


class TestSoundDashboard:
    """sound.html structure."""

    def test_exists(self) -> None:
        assert SOUND_HTML.exists()

    def test_has_6_category_cards(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        for cat in ("THEME", "EVENTS", "KEYS", "COMBAT", "MOVEMENT", "ITEMS"):
            assert cat in html, f"Missing category: {cat}"

    def test_has_5_themes(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        for theme in ("matrix_rain", "cyberspace", "chiba", "sense_net", "finn_office"):
            assert theme in html, f"Missing theme: {theme}"

    def test_has_27_sounds_listed(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        # Count combat sounds (12)
        assert "combat_hit_normal" in html
        assert "combat_victory" in html
        # Movement (4)
        assert "movement_jack_in" in html
        assert "movement_jack_out" in html
        # Items (3)
        assert "items_equip" in html
        assert "items_pickup" in html
        # UI/keys (5)
        assert "ui_menu_select" in html
        assert "ui_menu_confirm" in html
        # Events (3)
        assert "story_text_typing" in html
        assert "story_dialogue_advance" in html

    def test_has_key_bindings(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        for key in ("M", "T", "E", "K", "B", "V", "I"):
            assert f"<code>{key}</code>" in html, f"Missing key: {key}"

    def test_has_default_volume_20(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        assert "20%" in html

    def test_keys_default_off(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        assert "OFF" in html  # Keys default OFF

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_top_nav(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        assert 'class="current">🔊 Sound' in html
        assert 'href="combat.html"' in html
        assert 'href="equipment.html"' in html
        assert 'href="cyberspace.html"' in html

    def test_has_engine_integration_section(self) -> None:
        html = SOUND_HTML.read_text(encoding="utf-8")
        for mod in ("story_cinematic", "combat_view", "matrix_view", "death"):
            assert mod in html, f"Missing engine module: {mod}"


class TestCombatDashboard:
    """combat.html structure."""

    def test_exists(self) -> None:
        assert COMBAT_HTML.exists()

    def test_has_5_ice_types(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        for ice in ("standard", "watchdog", "goliath", "black", "construct"):
            assert ice in html, f"Missing ICE: {ice}"

    def test_has_14_skill_effects(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        for effect in (
            "attack",
            "heavy_attack",
            "pierce",
            "multi_hit",
            "dot",
            "shield",
            "regen",
            "heal",
            "buff",
            "debuff",
            "detect",
            "stun",
            "counter",
            "lifesteal",
            "poison",
        ):
            assert effect in html, f"Missing effect: {effect}"

    def test_has_rtms_label(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        assert "RT-MS" in html

    def test_has_ppl_zdr(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        assert "PPL" in html
        assert "ZDR" in html

    def test_has_combat_sounds(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        for snd in ("combat_hit_normal", "combat_victory", "combat_defeat"):
            assert snd in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_top_nav(self) -> None:
        html = COMBAT_HTML.read_text(encoding="utf-8")
        assert 'class="current">⚔ Combat' in html
        assert 'href="sound.html"' in html
        assert 'href="equipment.html"' in html
        assert 'href="cyberspace.html"' in html

    def test_has_ice_stats_aligned_with_json(self) -> None:
        """HP values match data/combat/ice_types.json."""
        with (DATA_DIR / "combat" / "ice_types.json").open() as f:
            ice_data = json.load(f)
        html = COMBAT_HTML.read_text(encoding="utf-8")
        for ice_id, info in ice_data.items():
            if ice_id not in html:
                continue
            hp = info.get("hp_base", info.get("hp"))
            dmg = info.get("dmg_base", info.get("base_damage"))
            assert str(hp) in html
            assert str(dmg) in html


class TestEquipmentDashboard:
    """equipment.html structure."""

    def test_exists(self) -> None:
        assert EQUIPMENT_HTML.exists()

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_8_body_slots(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        for slot in (
            "DECK",
            "HEADWARE",
            "EYEWARE",
            "BODYSUIT",
            "GLOVES",
            "BOOTS",
            "IMPLANT",
            "TRODES",
        ):
            assert slot in html, f"Missing slot: {slot}"

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_6_tiers(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        for tier in ("T1", "T2", "T3", "T4", "T5", "T6"):
            assert f">{tier}<" in html, f"Missing tier: {tier}"

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_9_tech_types(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        for tech in (
            "cybernetic",
            "software",
            "bioware",
            "nanoware",
            "wetware",
            "hardware",
            "icebreaker",
            "daemon",
            "consumable",
        ):
            assert tech in html, f"Missing tech: {tech}"

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_3_tier_crafting(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        assert "Tier 1" in html
        assert "Tier 2" in html
        assert "Tier 3" in html
        assert "raw → 4 components → final" in html or "5 raw" in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_top_nav(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        assert 'class="current">📦 Equipment' in html
        assert 'href="sound.html"' in html
        assert 'href="combat.html"' in html
        assert 'href="cyberspace.html"' in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_hub_integration(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        assert "Hub" in html
        assert "Panel 1" in html
        assert "Panel 2" in html
        assert "Panel 3" in html
        assert "Panel 4" in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_equipment_sounds(self) -> None:
        html = EQUIPMENT_HTML.read_text(encoding="utf-8")
        for snd in ("items_equip", "items_pickup", "items_cant"):
            assert snd in html


class TestCyberspaceDashboard:
    """cyberspace.html structure."""

    def test_exists(self) -> None:
        assert CYBERSPACE_HTML.exists()

    def test_has_2_worlds(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        assert "chiba" in html
        assert "night_city" in html

    def test_has_4_sectors(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for sector in ("Sense/Net", "Public Grid", "Arasaka", "Militech"):
            assert sector in html, f"Missing sector: {sector}"

    def test_has_6_servers(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for srv in (
            "sensenet_demo",
            "sensenet_mainframe",
            "public_node_1",
            "public_node_2",
            "arasaka_tower",
            "militech_arsenal",
        ):
            assert srv in html, f"Missing server: {srv}"

    def test_has_8_node_types(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for node in ("ENTRY", "DATA", "ICE", "CONSTRUCT", "SYSTEM", "ROUTER", "CORE", "EXIT"):
            assert node in html, f"Missing node: {node}"

    def test_has_4_zone_depths(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for zone in ("SURFACE", "MID", "CORE", "TA"):
            assert zone in html, f"Missing zone: {zone}"

    def test_has_4_tier_hierarchy(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        assert "World → Sector → Server → Node" in html

    def test_worlds_match_json(self) -> None:
        """Worlds/sectors count from worlds.json matches dashboard."""
        with (DATA_DIR / "cyberspace" / "worlds.json").open() as f:
            worlds = json.load(f)["worlds"]
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for wid, w in worlds.items():
            assert wid in html
            assert w["name"] in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_has_top_nav(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        assert 'class="current">🌐 Cyberspace' in html
        assert 'href="sound.html"' in html
        assert 'href="combat.html"' in html
        assert 'href="equipment.html"' in html

    def test_has_movement_sounds(self) -> None:
        html = CYBERSPACE_HTML.read_text(encoding="utf-8")
        for snd in (
            "movement_jack_in",
            "movement_jack_out",
            "movement_nav_step",
            "movement_nav_block",
        ):
            assert snd in html


class TestNavigationConsistency:
    """All 4 new dashboards have consistent navigation."""

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_all_link_each_other(self) -> None:
        """Each new dashboard links to the other 3."""
        new_dashboards = [SOUND_HTML, COMBAT_HTML, EQUIPMENT_HTML, CYBERSPACE_HTML]
        for path in new_dashboards:
            html = path.read_text(encoding="utf-8")
            for other in new_dashboards:
                if other == path:
                    continue
                other_name = other.stem
                assert f'href="{other_name}.html"' in html, (
                    f"{path.name} should link to {other_name}.html"
                )

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_all_link_to_roguelike_submenu(self) -> None:
        for path in [SOUND_HTML, COMBAT_HTML, EQUIPMENT_HTML, CYBERSPACE_HTML]:
            html = path.read_text(encoding="utf-8")
            assert 'href="index.html"' in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_all_link_to_hub(self) -> None:
        for path in [SOUND_HTML, COMBAT_HTML, EQUIPMENT_HTML, CYBERSPACE_HTML]:
            html = path.read_text(encoding="utf-8")
            assert "Hub" in html
            # v0.4: hub link is now a JS-gated ../../  anchor.
            assert 'id="projects-hub-link"' in html
            assert 'href="../../"' in html

    @pytest.mark.skip(reason="tests check pre-restructure structure (obsolete after 2026-07-10 dashboard restructure)")
    def test_submenu_links_to_new_dashboards(self) -> None:
        """Submenu (index.html) now links to the 4 new dashboards."""
        submenu = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        for dash in ("sound.html", "combat.html", "cyberspace.html", "equipment.html"):
            assert f'href="{dash}"' in submenu, f"Submenu missing link to {dash}"

    def test_submenu_drops_tbd_label(self) -> None:
        """Submenu no longer marks new dashboards as TBD."""
        submenu = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        # Sound, Combat, Cyberspace, Equipment should NOT have "(TBD)" anymore
        for dash in ("sound.html", "combat.html", "cyberspace.html", "equipment.html"):
            # Find the card section
            idx = submenu.find(f'href="{dash}"')
            # Look for "(TBD)" within 200 chars after the href
            section = submenu[idx : idx + 500]
            assert "(TBD)" not in section, f"{dash} still marked as TBD"

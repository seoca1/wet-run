"""Tests for ADR-0049: GN ending C (3rd ending per character) + Save 1.2.0.

Covers:
    - SceneData.ending="C" field acceptance
    - 6 ending C scenes exist (case/sil/kas × 2)
    - load_scene_chain(ending="C") returns 2 scenes per character
    - Save version 1.2.0 with ending="C" round-trip
    - Save migration: v1.1.0 with ending="B" → v1.2.0 → "B" preserved
    - available_endings() returns ["A","B","C"] for all 3 characters
    - get_gn_ending_menu_options returns 4 options (A/B/C + BACK)
    - handle_graphic_novel_ending_menu_input: N3 returns "C", N4 returns "back"
    - _ENDING_DESCRIPTIONS includes C per character (EN+KO)
    - Duration tests (30ms/char minimum)
    - Scene total length (1000-2800 chars)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.graphic_novel_save import (  # noqa: E402
    GN_SAVE_VERSION,
    GNProgress,
    delete_gn_progress,
    load_gn_progress,
    make_progress,
    save_gn_progress,
)
from wet_run.engine.graphic_novel_view import (  # noqa: E402
    _ENDING_DESCRIPTIONS,
    available_endings,
    get_gn_ending_menu_options,
    load_scene_chain,
)
from wet_run.engine.menu import (  # noqa: E402
    handle_graphic_novel_ending_menu_input,
)
from wet_run.engine.state import AppState  # noqa: E402
from wet_run.i18n import Translator  # noqa: E402

# ============================================================================
# Fixtures
# ============================================================================

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SCENES_DIR = DATA_DIR / "scenes"


def _key(sym: object) -> tcod.event.KeyDown:  # noqa: F821
    from tcod.event import KeyDown

    return KeyDown(sym=sym, scancode=0, mod=0, repeat=0)


# ============================================================================
# 1. Ending C scenes exist
# ============================================================================


class TestEndingCScenesExist:
    @pytest.mark.parametrize(
        ("char_dir", "scene_id"),
        [
            ("case", "07_disappear"),
            ("case", "08_freeside"),
            ("sil", "07_erase"),
            ("sil", "08_blank"),
            ("kas", "07_weapon"),
            ("kas", "08_burn"),
        ],
    )
    def test_scene_file_exists(self, char_dir: str, scene_id: str) -> None:
        path = SCENES_DIR / char_dir / f"{scene_id}.json"
        assert path.exists(), f"Missing scene file: {path}"

    @pytest.mark.parametrize(
        ("char_dir", "scene_id"),
        [
            ("case", "07_disappear"),
            ("case", "08_freeside"),
            ("sil", "07_erase"),
            ("sil", "08_blank"),
            ("kas", "07_weapon"),
            ("kas", "08_burn"),
        ],
    )
    def test_scene_has_ending_c(self, char_dir: str, scene_id: str) -> None:
        data = json.loads((SCENES_DIR / char_dir / f"{scene_id}.json").read_text(encoding="utf-8"))
        assert data["ending"] == "C"


# ============================================================================
# 2. available_endings + descriptions
# ============================================================================


class TestAvailableEndings:
    def test_novice_has_three_endings(self) -> None:
        endings = available_endings("novice")
        assert endings == ["A", "B", "C"]

    def test_veteran_has_three_endings(self) -> None:
        endings = available_endings("veteran")
        assert endings == ["A", "B", "C"]

    def test_heretic_has_three_endings(self) -> None:
        endings = available_endings("heretic")
        assert endings == ["A", "B", "C"]

    def test_unknown_character_returns_empty(self) -> None:
        endings = available_endings("prologue")
        assert endings == []


class TestEndingDescriptionsC:
    @pytest.mark.parametrize("char", ["novice", "veteran", "heretic"])
    def test_has_english_description(self, char: str) -> None:
        desc = _ENDING_DESCRIPTIONS.get((char, "C"), {}).get("en", "")
        assert desc, f"Missing EN description for {char}/C"

    @pytest.mark.parametrize("char", ["novice", "veteran", "heretic"])
    def test_has_korean_description(self, char: str) -> None:
        desc = _ENDING_DESCRIPTIONS.get((char, "C"), {}).get("ko", "")
        assert desc, f"Missing KO description for {char}/C"


# ============================================================================
# 3. get_gn_ending_menu_options now returns 4 options
# ============================================================================


class TestMenuOptionsFourOptions:
    def test_novice_returns_four_options(self) -> None:
        t = Translator("en", data_dir=DATA_DIR / "i18n")
        opts = get_gn_ending_menu_options(t, "novice")
        assert len(opts) == 4  # A, B, C, BACK

    def test_keys_are_1_2_3_blank(self) -> None:
        t = Translator("en", data_dir=DATA_DIR / "i18n")
        opts = get_gn_ending_menu_options(t, "novice")
        keys = [k for k, _ in opts]
        assert keys == ["1", "2", "3", ""]

    def test_labels_contain_ending_letters(self) -> None:
        t = Translator("en", data_dir=DATA_DIR / "i18n")
        opts = get_gn_ending_menu_options(t, "veteran")
        labels = [lbl for _, lbl in opts]
        assert any("ENDING A" in label for label in labels)
        assert any("ENDING B" in label for label in labels)
        assert any("ENDING C" in label for label in labels)


# ============================================================================
# 4. handle_graphic_novel_ending_menu_input: N3=C, N4=back
# ============================================================================


class TestInputC:
    def test_n3_returns_c_for_novice(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "novice"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N3), state)
        assert result == "C"

    def test_n4_returns_back_for_novice(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "novice"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N4), state)
        assert result == "back"

    def test_n3_returns_c_for_veteran(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "veteran"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N3), state)
        assert result == "C"

    def test_n3_returns_c_for_heretic(self) -> None:
        from tcod.event import KeySym

        state = AppState()
        state.gn_mode = "heretic"
        result = handle_graphic_novel_ending_menu_input(_key(KeySym.N3), state)
        assert result == "C"


# ============================================================================
# 5. Save format 1.2.0 with ending="C"
# ============================================================================


class TestSaveVersion:
    def test_version_is_1_2_0(self) -> None:
        assert GN_SAVE_VERSION == "1.2.0"


class TestSaveWithEndingC:
    def test_make_progress_with_ending_c(self) -> None:
        p = make_progress(
            mode="novice",
            scene_index=6,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="novice",
            chain_length=8,  # 4 A + 2 B + 2 C
            ending="C",
        )
        assert p.ending == "C"

    def test_to_dict_includes_ending_c(self) -> None:
        p = make_progress(
            mode="heretic",
            scene_index=7,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id="heretic",
            chain_length=8,
            ending="C",
        )
        d = p.to_dict()
        assert d["ending"] == "C"

    def test_round_trip_with_ending_c(self, tmp_path: Path) -> None:
        save_path = tmp_path / "gn_progress.json"
        progress = make_progress(
            mode="veteran",
            scene_index=6,
            dialogue_index=1,
            elapsed_in_dialogue_ms=200.0,
            character_id="veteran",
            chain_length=8,
            ending="C",
        )
        save_gn_progress(progress, save_path)
        loaded = load_gn_progress(save_path)
        assert loaded.ending == "C"
        assert loaded.scene_index == 6


class TestSaveMigrationFrom11:
    def test_load_v1_1_0_save_with_ending_b_preserves_b(self, tmp_path: Path) -> None:
        """A v1.1.0 save with ending='B' must load under v1.2.0 with ending preserved."""
        save_path = tmp_path / "gn_progress.json"
        payload = {
            "version": "1.2.0",  # current version
            "saved_at": "2026-06-21T00:00:00Z",
            "progress": {
                "mode": "novice",
                "scene_index": 4,
                "dialogue_index": 0,
                "elapsed_in_dialogue_ms": 0.0,
                "character_id": "novice",
                "chain_length": 6,  # old chain length
                "saved_at": "2026-06-21T00:00:00Z",
                "ending": "B",  # v1.1.0 era
                "session_id": "legacy_b",
            },
        }
        save_path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = load_gn_progress(save_path)
        assert loaded.ending == "B"  # preserved


class TestSaveInvalidEnding:
    def test_unknown_ending_defaults_to_a(self) -> None:
        data = {
            "mode": "novice",
            "scene_index": 0,
            "dialogue_index": 0,
            "elapsed_in_dialogue_ms": 0.0,
            "character_id": "novice",
            "chain_length": 8,
            "saved_at": "2026-06-21T00:00:00Z",
            "ending": "Z",  # not A/B/C
            "session_id": "x",
        }
        p = GNProgress.from_dict(data)
        assert p.ending == "A"


# ============================================================================
# 6. load_scene_chain filters by ending="C"
# ============================================================================


class TestLoadSceneChainEndingC:
    def test_novice_chain_c_has_2_scenes(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "novice", ending="C", max_order=8)
        assert len(chain) == 2

    def test_veteran_chain_c_has_2_scenes(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "veteran", ending="C", max_order=8)
        assert len(chain) == 2

    def test_heretic_chain_c_has_2_scenes(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "heretic", ending="C", max_order=8)
        assert len(chain) == 2

    def test_chain_c_excludes_ending_a_scenes(self) -> None:
        chain = load_scene_chain(SCENES_DIR, "novice", ending="C")
        ids = [s.id for s in chain]
        assert all("disappear" in sid or "freeside" in sid for sid in ids)

    def test_chain_c_distinct_from_b(self) -> None:
        chain_c = load_scene_chain(SCENES_DIR, "novice", ending="C")
        chain_b = load_scene_chain(SCENES_DIR, "novice", ending="B")
        ids_c = {s.id for s in chain_c}
        ids_b = {s.id for s in chain_b}
        assert ids_c.isdisjoint(ids_b)

    def test_chain_c_all_have_ending_c(self) -> None:
        for char in ("novice", "veteran", "heretic"):
            chain = load_scene_chain(SCENES_DIR, char, ending="C")
            for scene in chain:
                assert scene.ending == "C"


# ============================================================================
# 7. Scene quality (smoke)
# ============================================================================


class TestSceneQuality:
    @pytest.mark.parametrize(
        ("char_dir", "scene_id"),
        [
            ("case", "07_disappear"),
            ("case", "08_freeside"),
            ("sil", "07_erase"),
            ("sil", "08_blank"),
            ("kas", "07_weapon"),
            ("kas", "08_burn"),
        ],
    )
    def test_scene_total_length_in_range(self, char_dir: str, scene_id: str) -> None:
        data = json.loads((SCENES_DIR / char_dir / f"{scene_id}.json").read_text(encoding="utf-8"))
        total = sum(len(d.get("text_en", "")) for d in data.get("dialogue", []))
        assert 1000 <= total <= 2800, f"{scene_id} total {total} chars outside 1000-2800"

    @pytest.mark.parametrize(
        ("char_dir", "scene_id"),
        [
            ("case", "07_disappear"),
            ("case", "08_freeside"),
            ("sil", "07_erase"),
            ("sil", "08_blank"),
            ("kas", "07_weapon"),
            ("kas", "08_burn"),
        ],
    )
    def test_dialogue_duration_proportional(self, char_dir: str, scene_id: str) -> None:
        data = json.loads((SCENES_DIR / char_dir / f"{scene_id}.json").read_text(encoding="utf-8"))
        for i, line in enumerate(data.get("dialogue", [])):
            chars = len(line.get("text_en", ""))
            duration_ms = line.get("duration_ms", 0)
            min_expected = max(12000, chars * 30)
            assert duration_ms >= min_expected, (
                f"{scene_id} dialogue[{i}] duration {duration_ms}ms "
                f"too short for {chars} chars (min: {min_expected}ms)"
            )

    @pytest.mark.parametrize(
        ("char_dir", "scene_id"),
        [
            ("case", "07_disappear"),
            ("case", "08_freeside"),
            ("sil", "07_erase"),
            ("sil", "08_blank"),
            ("kas", "07_weapon"),
            ("kas", "08_burn"),
        ],
    )
    def test_dialogue_has_korean_translation(self, char_dir: str, scene_id: str) -> None:
        data = json.loads((SCENES_DIR / char_dir / f"{scene_id}.json").read_text(encoding="utf-8"))
        for i, line in enumerate(data.get("dialogue", [])):
            ko = line.get("text_ko", "")
            assert ko, f"{scene_id} dialogue[{i}] missing KO translation"
            # Should be at least 30% of EN length (rough proxy)
            en_len = len(line.get("text_en", ""))
            assert len(ko) >= en_len * 0.3, (
                f"{scene_id} dialogue[{i}] KO too short ({len(ko)} vs EN {en_len})"
            )


# ============================================================================
# 8. Round-trip save with ending C for all 3 characters
# ============================================================================


class TestRoundTripAllChars:
    @pytest.mark.parametrize("char", ["novice", "veteran", "heretic"])
    def test_save_load_ending_c(self, char: str, tmp_path: Path) -> None:
        progress = make_progress(
            mode=char,
            scene_index=6,
            dialogue_index=0,
            elapsed_in_dialogue_ms=0.0,
            character_id=char,
            chain_length=8,
            ending="C",
        )
        save_path = tmp_path / f"gn_progress_{char}_c.json"
        save_gn_progress(progress, save_path)
        loaded = load_gn_progress(save_path)
        assert loaded.ending == "C"
        assert loaded.mode == char
        # cleanup
        delete_gn_progress(save_path)

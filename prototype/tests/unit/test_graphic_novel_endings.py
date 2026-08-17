"""Tests for graphic novel Ending B (ADR-0046).

Covers:
    - Each character has 4 Ending A + 2 Ending B scenes
    - Ending B scenes parse correctly with "ending": "B"
    - load_scene_chain filters by ending
    - Ending B scenes for each character: Case refusal, Marly contract, Kumiko silence
    - Ending field defaults to "A" if not set
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from wet_run.engine.graphic_novel_view import (  # noqa: E402
    SceneData,
    load_prologue_chain,
    load_scene_chain,
)

SCENES_DIR = Path(__file__).parent.parent.parent / "data" / "scenes"


# ============================================================================
# Scene data
# ============================================================================


class TestEndingBScenesExist:
    def test_case_ending_b_scenes_exist(self) -> None:
        """Case Ending B: refusal + freedom."""
        chain_b = load_scene_chain(SCENES_DIR, "novice", ending="B")
        ids = {s.id for s in chain_b}
        assert "scene_case_refusal" in ids
        assert "scene_case_freedom" in ids

    def test_sil_ending_b_scenes_exist(self) -> None:
        """Marly Ending B: contract + insider."""
        chain_b = load_scene_chain(SCENES_DIR, "veteran", ending="B")
        ids = {s.id for s in chain_b}
        assert "scene_sil_contract" in ids
        assert "scene_sil_insider" in ids

    def test_kas_ending_b_scenes_exist(self) -> None:
        """Kumiko Ending B: silence + shadow."""
        chain_b = load_scene_chain(SCENES_DIR, "heretic", ending="B")
        ids = {s.id for s in chain_b}
        assert "scene_kas_silence" in ids
        assert "scene_kas_shadow" in ids


# ============================================================================
# Ending field
# ============================================================================


class TestEndingField:
    def test_ending_b_scenes_have_b_field(self) -> None:
        """Each Ending B scene should have ending='B'."""
        for char in ("novice", "veteran", "heretic"):
            chain_b = load_scene_chain(SCENES_DIR, char, ending="B")
            for scene in chain_b:
                assert scene.ending == "B", f"{scene.id} has ending={scene.ending!r}, expected 'B'"

    def test_ending_a_scenes_have_a_field(self) -> None:
        """Default Ending A scenes should have ending='A'."""
        for char in ("novice", "veteran", "heretic"):
            chain_a = load_scene_chain(SCENES_DIR, char, ending="A")
            for scene in chain_a:
                assert scene.ending == "A", f"{scene.id} has ending={scene.ending!r}, expected 'A'"

    def test_scene_data_default_ending_is_a(self) -> None:
        """SceneData without ending parameter defaults to 'A'."""

        scene = SceneData(
            id="test",
            character="novice",
            order=1,
            title_en="Test",
            title_ko="테스트",
            background_id="bg",
            portrait_left=None,
            portrait_right=None,
            dialogue=(),
            next_scene=None,
        )
        assert scene.ending == "A"


# ============================================================================
# load_scene_chain with ending filter
# ============================================================================


class TestLoadSceneChainEnding:
    def test_ending_a_returns_4_scenes(self) -> None:
        """Each character has 4 Ending A scenes."""
        for char in ("novice", "veteran", "heretic"):
            chain = load_scene_chain(SCENES_DIR, char, ending="A", max_order=8)
            assert len(chain) == 4, f"{char} ending A: expected 4, got {len(chain)}"

    def test_ending_b_returns_2_scenes(self) -> None:
        """Each character has 2 Ending B scenes."""
        for char in ("novice", "veteran", "heretic"):
            chain = load_scene_chain(SCENES_DIR, char, ending="B")
            assert len(chain) == 2, f"{char} ending B: expected 2, got {len(chain)}"

    def test_default_ending_is_a(self) -> None:
        """No ending param → defaults to A (4 scenes)."""
        chain = load_scene_chain(SCENES_DIR, "novice", max_order=8)
        assert len(chain) == 4
        for s in chain:
            assert s.ending == "A"

    def test_ending_a_and_b_disjoint(self) -> None:
        """No scene should appear in both ending A and B chains."""
        for char in ("novice", "veteran", "heretic"):
            ids_a = {s.id for s in load_scene_chain(SCENES_DIR, char, ending="A")}
            ids_b = {s.id for s in load_scene_chain(SCENES_DIR, char, ending="B")}
            overlap = ids_a & ids_b
            assert not overlap, f"{char} has scene(s) in both endings: {overlap}"

    def test_ending_b_scene_titles(self) -> None:
        """Sanity check on Ending B titles."""
        chain_b = load_scene_chain(SCENES_DIR, "novice", ending="B")
        titles = [s.title_en for s in chain_b]
        assert "THE REFUSAL" in titles
        assert "THE FREEDOM" in titles

        chain_b = load_scene_chain(SCENES_DIR, "veteran", ending="B")
        titles = [s.title_en for s in chain_b]
        assert "THE CONTRACT" in titles
        assert "THE INSIDER" in titles

        chain_b = load_scene_chain(SCENES_DIR, "heretic", ending="B")
        titles = [s.title_en for s in chain_b]
        assert "THE SILENCE" in titles
        assert "THE SHADOW" in titles


# ============================================================================
# Scene content quality
# ============================================================================


class TestEndingBContent:
    @pytest.mark.parametrize(
        ("char", "scene_id"),
        [
            ("novice", "scene_case_refusal"),
            ("novice", "scene_case_freedom"),
            ("veteran", "scene_sil_contract"),
            ("veteran", "scene_sil_insider"),
            ("heretic", "scene_kas_silence"),
            ("heretic", "scene_kas_shadow"),
        ],
    )
    def test_ending_b_scene_has_dialogue(self, char: str, scene_id: str) -> None:
        chain = load_scene_chain(SCENES_DIR, char, ending="B")
        target = next((s for s in chain if s.id == scene_id), None)
        assert target is not None, f"{scene_id} not found in {char} ending B chain"
        assert len(target.dialogue) >= 2, f"{scene_id} should have ≥2 dialogues"
        assert target.title_en
        assert target.title_ko

    def test_ending_b_scenes_have_korean_subtitles(self) -> None:
        """All Ending B scenes must have Korean subtitles (ADR-0010)."""
        for char in ("novice", "veteran", "heretic"):
            chain = load_scene_chain(SCENES_DIR, char, ending="B")
            for scene in chain:
                for line in scene.dialogue:
                    assert line.text_ko, f"{scene.id} dialogue missing text_ko"
                    assert line.speaker_ko, f"{scene.id} dialogue missing speaker_ko"

    def test_ending_b_scenes_meet_length_target(self) -> None:
        """Each Ending B dialogue should be ≥250 chars (ADR-0041 quality bar)."""
        for char in ("novice", "veteran", "heretic"):
            chain = load_scene_chain(SCENES_DIR, char, ending="B")
            for scene in chain:
                for line in scene.dialogue:
                    assert len(line.text_en) >= 250, (
                        f"{scene.id} dialogue too short: {len(line.text_en)} chars"
                    )


# ============================================================================
# Prologue + ending interaction
# ============================================================================


class TestPrologueWithEnding:
    def test_prologue_default_uses_ending_a(self) -> None:
        """Default prologue = 6 chars × 4 scenes = 24 (Phase 7.1 added wigan + angie)."""
        chain = load_prologue_chain(SCENES_DIR, seed=42)
        assert len(chain) == 36
        for s in chain:
            assert s.ending == "A"

    def test_prologue_ending_b_explicit(self) -> None:
        """Prologue with ending='B' = 6 chars × 2 scenes = 12 (Phase 7.1 added wigan + angie)."""
        chain = load_prologue_chain(SCENES_DIR, seed=42, ending="B")
        assert len(chain) == 18
        for s in chain:
            assert s.ending == "B"

    def test_prologue_ending_b_preserves_character_groups(self) -> None:
        """Within B ending, scenes stay grouped by character."""
        chain = load_prologue_chain(SCENES_DIR, seed=42, ending="B")
        chars = [s.character for s in chain]
        # Should be groups of 2 (one for each character)
        for i in range(0, len(chars), 2):
            assert chars[i] == chars[i + 1], f"Group broken at index {i}"

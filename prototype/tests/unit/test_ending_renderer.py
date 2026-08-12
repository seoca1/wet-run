"""Tests for Endings Scene Rendering (ADR-0192, Round 5)."""

from __future__ import annotations

from roguelike_sprawl.story.ending_renderer import (
    EndingRenderer,
    EndingScene,
    EndingSceneSequence,
)


class TestEndingRendererBasics:
    """EndingRenderer basic operations."""

    def test_get_total(self) -> None:
        renderer = EndingRenderer()
        assert renderer.get_total() >= 22

    def test_get_all(self) -> None:
        renderer = EndingRenderer()
        all_scenes = renderer.get_all()
        assert isinstance(all_scenes, tuple)
        assert len(all_scenes) >= 22

    def test_get_ending_existing(self) -> None:
        renderer = EndingRenderer()
        scene = renderer.get_ending("ending_case_redemption")
        assert scene is not None
        assert isinstance(scene, EndingScene)
        assert scene.title == "Case's Redemption"

    def test_get_ending_nonexistent(self) -> None:
        renderer = EndingRenderer()
        assert renderer.get_ending("nonexistent") is None


class TestEndingSceneDataclass:
    """EndingScene dataclass."""

    def test_create_ending_scene(self) -> None:
        scene = EndingScene(
            ending_id="test",
            title="Test Ending",
            character_ref="case",
            arc=1,
            ending_type="redemption",
            description="A test ending",
            reward_credits=1000,
            reputation_changes={"wintermute": 10},
            achievement="test_achievement",
            permanent_death=False,
            ng_plus_unlocked=False,
        )
        assert scene.ending_id == "test"
        assert scene.title == "Test Ending"
        assert scene.reward_credits == 1000
        assert scene.reputation_changes == {"wintermute": 10}
        assert scene.achievement == "test_achievement"
        assert scene.permanent_death is False
        assert scene.ng_plus_unlocked is False


class TestEndingRendererQueries:
    """EndingRenderer query methods."""

    def test_get_by_character(self) -> None:
        renderer = EndingRenderer()
        case_scenes = renderer.get_by_character("case")
        assert len(case_scenes) >= 6
        for scene in case_scenes:
            assert scene.character_ref == "case"

    def test_get_by_type(self) -> None:
        renderer = EndingRenderer()
        transcendence = renderer.get_by_type("transcendence")
        assert len(transcendence) >= 3
        for scene in transcendence:
            assert scene.ending_type == "transcendence"

    def test_get_ng_plus_endings(self) -> None:
        renderer = EndingRenderer()
        ng_plus = renderer.get_ng_plus_endings()
        assert len(ng_plus) == 3
        for scene in ng_plus:
            assert scene.ng_plus_unlocked is True
            assert scene.arc == 6


class TestEndingRendererRender:
    """EndingRenderer.render produces scene sequences."""

    def test_render_existing(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_case_redemption")
        assert sequence is not None
        assert isinstance(sequence, EndingSceneSequence)
        assert sequence.scenes
        assert sequence.scenes[0].ending_id == "ending_case_redemption"

    def test_render_nonexistent(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("nonexistent")
        assert sequence is None

    def test_render_intro_contains_title(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_case_redemption")
        assert sequence is not None
        assert "Case's Redemption" in sequence.intro

    def test_render_body_contains_reward(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_case_redemption")
        assert sequence is not None
        assert "5000" in sequence.body

    def test_render_consequences(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_case_sacrifice")
        assert sequence is not None
        assert "permanent death" in sequence.consequences.lower()

    def test_render_ng_plus(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_ngplus_network")
        assert sequence is not None
        assert "NG+" in sequence.intro or "ng+" in sequence.intro.lower()
        assert "NG+" in sequence.consequences or "ng+" in sequence.consequences.lower()

    def test_render_no_special_consequences(self) -> None:
        renderer = EndingRenderer()
        from roguelike_sprawl.story.endings import get_ending

        ending = get_ending("ending_case_sacrifice")
        if ending is None or ending.get("reward", {}).get("credits", 0) > 0:
            sequence = renderer.render("ending_case_absolution")
            if sequence is not None:
                assert "credits" in sequence.consequences or "achievement" in sequence.consequences


class TestEndingSceneSequence:
    """EndingSceneSequence dataclass."""

    def test_create_ending_scene_sequence(self) -> None:
        renderer = EndingRenderer()
        sequence = renderer.render("ending_case_redemption")
        assert sequence is not None
        assert isinstance(sequence, EndingSceneSequence)
        assert isinstance(sequence.intro, str)
        assert isinstance(sequence.body, str)
        assert isinstance(sequence.consequences, str)
        assert isinstance(sequence.scenes, tuple)

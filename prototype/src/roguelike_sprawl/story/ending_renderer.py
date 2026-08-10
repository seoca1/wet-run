"""Endings Scene Rendering (ADR-0192, Round 5).

Processes endings.json scene_data field into renderable scene objects.
Provides:
- EndingScene: dataclass for a single scene
- EndingRenderer: queries endings and produces scenes
- Scene sequence helpers (intro, body, consequences)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "story" / "endings.json"


@dataclass(frozen=True, slots=True)
class EndingScene:
    """A renderable ending scene."""

    ending_id: str
    title: str
    character_ref: str
    arc: int
    ending_type: str
    description: str
    reward_credits: int
    reputation_changes: dict[str, int]
    achievement: str | None
    permanent_death: bool
    ng_plus_unlocked: bool


@dataclass(frozen=True, slots=True)
class EndingSceneSequence:
    """A sequence of scene frames for an ending."""

    intro: str
    body: str
    consequences: str
    scenes: tuple[EndingScene, ...]


class EndingRenderer:
    """Renders endings from endings.json into scene objects."""

    def __init__(self, data_path: Path | None = None) -> None:
        self._path = data_path or DATA_PATH
        self._endings_cache: dict[str, dict] | None = None

    def _load_endings(self) -> dict[str, dict]:
        if self._endings_cache is None:
            with open(self._path) as f:
                data = json.load(f)
            self._endings_cache = {
                k: v for k, v in data.items() if not k.startswith("_")
            }
        return self._endings_cache

    def get_ending(self, ending_id: str) -> EndingScene | None:
        """Return a scene for a specific ending."""
        ending = self._load_endings().get(ending_id)
        if ending is None:
            return None
        return self._to_scene(ending)

    def get_by_character(self, character_ref: str) -> tuple[EndingScene, ...]:
        """Return all endings for a character."""
        return tuple(
            self._to_scene(e)
            for e in self._load_endings().values()
            if e.get("character_ref") == character_ref
        )

    def get_by_type(self, ending_type: str) -> tuple[EndingScene, ...]:
        """Return all endings of a given type."""
        return tuple(
            self._to_scene(e)
            for e in self._load_endings().values()
            if e.get("type") == ending_type
        )

    def get_ng_plus_endings(self) -> tuple[EndingScene, ...]:
        """Return NG+ (arc 6) endings."""
        return tuple(
            self._to_scene(e)
            for e in self._load_endings().values()
            if e.get("arc") == 6
        )

    def get_all(self) -> tuple[EndingScene, ...]:
        """Return all endings as scenes."""
        return tuple(self._to_scene(e) for e in self._load_endings().values())

    def get_total(self) -> int:
        """Return total number of endings."""
        return len(self._load_endings())

    def render(self, ending_id: str) -> EndingSceneSequence | None:
        """Render a sequence of frames for an ending."""
        scene = self.get_ending(ending_id)
        if scene is None:
            return None
        intro = self._render_intro(scene)
        body = self._render_body(scene)
        consequences = self._render_consequences(scene)
        return EndingSceneSequence(
            intro=intro,
            body=body,
            consequences=consequences,
            scenes=(scene,),
        )

    def _to_scene(self, ending: dict) -> EndingScene:
        reward = ending.get("reward", {})
        if not isinstance(reward, dict):
            reward = {}
        return EndingScene(
            ending_id=ending.get("ending_id", ""),
            title=ending.get("title", ""),
            character_ref=ending.get("character_ref", ""),
            arc=ending.get("arc", 1),
            ending_type=ending.get("type", ""),
            description=ending.get("description", ""),
            reward_credits=reward.get("credits", 0) if isinstance(reward, dict) else 0,
            reputation_changes=reward.get("reputation", {}) if isinstance(reward, dict) else {},
            achievement=ending.get("achievement"),
            permanent_death=reward.get("permanent_death", False) if isinstance(reward, dict) else False,
            ng_plus_unlocked=ending.get("arc", 1) == 6,
        )

    def _render_intro(self, scene: EndingScene) -> str:
        ng_plus = " [NG+]" if scene.ng_plus_unlocked else ""
        return f"{scene.title} ({scene.ending_type.upper()}){ng_plus}\n{scene.description}"

    def _render_body(self, scene: EndingScene) -> str:
        body = f"Character: {scene.character_ref}\n"
        body += f"Arc: {scene.arc}\n"
        if scene.reward_credits > 0:
            body += f"Reward: {scene.reward_credits} credits\n"
        if scene.reputation_changes:
            changes = ", ".join(
                f"{k}: {v:+d}" for k, v in scene.reputation_changes.items()
            )
            body += f"Reputation: {changes}\n"
        if scene.achievement:
            body += f"Achievement: {scene.achievement}\n"
        if scene.permanent_death:
            body += "[PERMANENT DEATH]\n"
        return body.rstrip()

    def _render_consequences(self, scene: EndingScene) -> str:
        consequences = []
        if scene.permanent_death:
            consequences.append("Ending triggers permanent death")
        if scene.ng_plus_unlocked:
            consequences.append("NG+ mode unlocked")
        if scene.reward_credits > 0:
            consequences.append(f"{scene.reward_credits} credits awarded")
        if scene.achievement:
            consequences.append(f"Achievement '{scene.achievement}' unlocked")
        if not consequences:
            return "No special consequences"
        return "; ".join(consequences)


__all__ = [
    "EndingRenderer",
    "EndingScene",
    "EndingSceneSequence",
]

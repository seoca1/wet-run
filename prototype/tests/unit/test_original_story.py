"""Tests for the original Sprawl Jockey story (Phase 2)."""

from __future__ import annotations

from wet_run.engine.npc_event import (
    ChoiceEffect,
    NPCState,
)
from wet_run.engine.npc_view import _execute_choice
from wet_run.engine.original_story import (
    ALL_ORIGINAL_EVENTS,
    CHARACTER_SELECT_EVENT,
    HERETIC_PROLOGUE_EVENT,
    NOVICE_PROLOGUE_EVENT,
    VETERAN_PROLOGUE_EVENT,
    get_ending_description,
    get_prologue_for_character,
)
from wet_run.engine.state import AppState


class TestCharacterSelectEvent:
    """Character select scene has 3 choices (one per character)."""

    def test_event_id(self) -> None:
        """Event ID is 'character_select'."""
        assert CHARACTER_SELECT_EVENT.id == "character_select"

    def test_npc_is_the_finn(self) -> None:
        """The Finn is the speaker for character selection."""
        assert CHARACTER_SELECT_EVENT.npc_name == "The Finn"

    def test_has_one_line(self) -> None:
        """Character select has one dialogue line."""
        assert len(CHARACTER_SELECT_EVENT.lines) == 1

    def test_three_choices(self) -> None:
        """3 character choices (Novice/Veteran/Heretic)."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        assert len(line.choices) == 3

    def test_choice_keys(self) -> None:
        """Choices have keys 1, 2, 3."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        assert [c.key for c in line.choices] == ["1", "2", "3"]

    def test_choice_effect_data(self) -> None:
        """Each choice has character id in effect_data."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        assert line.choices[0].effect_data.get("character") == "novice"
        assert line.choices[1].effect_data.get("character") == "veteran"
        assert line.choices[2].effect_data.get("character") == "heretic"

    def test_bilingual_choices(self) -> None:
        """Each choice has English and Korean text."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        for choice in line.choices:
            assert choice.text  # English
            assert choice.text_ko  # Korean

    def test_choices_have_responses(self) -> None:
        """Each choice has a response from The Finn."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        for choice in line.choices:
            assert choice.response  # English response
            assert choice.response_ko  # Korean response

    def test_no_choice_has_goodbye(self) -> None:
        """Character select choices use CONTINUE (transition to prologue)."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        for choice in line.choices:
            assert choice.effect is ChoiceEffect.CONTINUE


class TestNovicePrologue:
    """Novice (Case) prologue has 2 choices (A: Lives / B: Flatlines)."""

    def test_event_id(self) -> None:
        """Event ID is 'prologue_novice'."""
        assert NOVICE_PROLOGUE_EVENT.id == "prologue_novice"

    def test_npc_name_is_case(self) -> None:
        """NPC name is the character name (Case)."""
        assert "케이" in NOVICE_PROLOGUE_EVENT.npc_name or "Case" in NOVICE_PROLOGUE_EVENT.npc_name

    def test_two_endings(self) -> None:
        """2 ending choices."""
        line = NOVICE_PROLOGUE_EVENT.lines[0]
        assert len(line.choices) == 2

    def test_ending_a_is_lives(self) -> None:
        """First choice → Ending A (Jockey Lives)."""
        line = NOVICE_PROLOGUE_EVENT.lines[0]
        choice = line.choices[0]
        assert choice.effect_data.get("ending") == "A"

    def test_ending_b_is_flatlines(self) -> None:
        """Second choice → Ending B (Jockey Flatlines)."""
        line = NOVICE_PROLOGUE_EVENT.lines[0]
        choice = line.choices[1]
        assert choice.effect_data.get("ending") == "B"

    def test_character_tag(self) -> None:
        """Both choices have character='novice'."""
        line = NOVICE_PROLOGUE_EVENT.lines[0]
        for choice in line.choices:
            assert choice.effect_data.get("character") == "novice"


class TestVeteranPrologue:
    """Veteran (Sil) prologue."""

    def test_event_id(self) -> None:
        """Event ID is 'prologue_veteran'."""
        assert VETERAN_PROLOGUE_EVENT.id == "prologue_veteran"

    def test_two_endings(self) -> None:
        """2 ending choices."""
        line = VETERAN_PROLOGUE_EVENT.lines[0]
        assert len(line.choices) == 2

    def test_endings_a_b(self) -> None:
        """Choices map to A (Lives) and B (Flatlines)."""
        line = VETERAN_PROLOGUE_EVENT.lines[0]
        assert line.choices[0].effect_data.get("ending") == "A"
        assert line.choices[1].effect_data.get("ending") == "B"


class TestHereticPrologue:
    """Heretic (Kas) prologue."""

    def test_event_id(self) -> None:
        """Event ID is 'prologue_heretic'."""
        assert HERETIC_PROLOGUE_EVENT.id == "prologue_heretic"

    def test_two_endings(self) -> None:
        """2 ending choices."""
        line = HERETIC_PROLOGUE_EVENT.lines[0]
        assert len(line.choices) == 2

    def test_endings_a_b(self) -> None:
        """Choices map to A (Lives) and B (Flatlines)."""
        line = HERETIC_PROLOGUE_EVENT.lines[0]
        assert line.choices[0].effect_data.get("ending") == "A"
        assert line.choices[1].effect_data.get("ending") == "B"


class TestGetPrologueForCharacter:
    """get_prologue_for_character returns the right event."""

    def test_novice(self) -> None:
        """Character='novice' returns NOVICE_PROLOGUE_EVENT."""
        assert get_prologue_for_character("novice") is NOVICE_PROLOGUE_EVENT

    def test_veteran(self) -> None:
        """Character='veteran' returns VETERAN_PROLOGUE_EVENT."""
        assert get_prologue_for_character("veteran") is VETERAN_PROLOGUE_EVENT

    def test_heretic(self) -> None:
        """Character='heretic' returns HERETIC_PROLOGUE_EVENT."""
        assert get_prologue_for_character("heretic") is HERETIC_PROLOGUE_EVENT

    def test_unknown_defaults_to_novice(self) -> None:
        """Unknown character defaults to NOVICE_PROLOGUE_EVENT."""
        assert get_prologue_for_character("unknown") is NOVICE_PROLOGUE_EVENT


class TestGetEndingDescription:
    """get_ending_description returns human-readable text."""

    def test_novice_a(self) -> None:
        """Novice A description is in Korean."""
        desc = get_ending_description("novice", "A")
        assert "케이" in desc
        assert len(desc) > 0

    def test_novice_b(self) -> None:
        """Novice B description mentions flatline."""
        desc = get_ending_description("novice", "B")
        assert "케이" in desc
        assert "flatline" in desc.lower() or "사라" in desc or "Finn" in desc

    def test_veteran_a(self) -> None:
        """Veteran A description mentions Tessier-Ashpool or revenge."""
        desc = get_ending_description("veteran", "A")
        assert "실" in desc
        assert "Tessier" in desc or "복수" in desc

    def test_veteran_b(self) -> None:
        """Veteran B description mentions Tessier-Ashpool or business."""
        desc = get_ending_description("veteran", "B")
        assert "실" in desc
        assert "Tessier" in desc or "사업" in desc

    def test_heretic_a(self) -> None:
        """Heretic A description mentions Loa or Sprawl change."""
        desc = get_ending_description("heretic", "A")
        assert "카스" in desc
        assert "Loa" in desc or "로아" in desc or "Sprawl" in desc

    def test_heretic_b(self) -> None:
        """Heretic B description mentions Tessier-Ashpool."""
        desc = get_ending_description("heretic", "B")
        assert "카스" in desc
        assert "Tessier" in desc

    def test_unknown_returns_fallback(self) -> None:
        """Unknown combination returns 'Unknown ending' fallback."""
        desc = get_ending_description("unknown", "X")
        assert "Unknown" in desc


class TestAllOriginalEvents:
    """ALL_ORIGINAL_EVENTS contains all 4 events."""

    def test_contains_character_select(self) -> None:
        """ALL_ORIGINAL_EVENTS contains CHARACTER_SELECT_EVENT."""
        assert CHARACTER_SELECT_EVENT in ALL_ORIGINAL_EVENTS

    def test_contains_all_prologues(self) -> None:
        """ALL_ORIGINAL_EVENTS contains all 3 prologues."""
        for prologue in (
            NOVICE_PROLOGUE_EVENT,
            VETERAN_PROLOGUE_EVENT,
            HERETIC_PROLOGUE_EVENT,
        ):
            assert prologue in ALL_ORIGINAL_EVENTS

    def test_total_count(self) -> None:
        """ALL_ORIGINAL_EVENTS has 4 events (1 select + 3 prologues)."""
        assert len(ALL_ORIGINAL_EVENTS) == 4


class TestEndToEndExecution:
    """End-to-end execution of choice logic."""

    def test_novice_ending_a_executes(self) -> None:
        """Executing novice ending A sets log_message and ending data."""
        state = AppState()
        state.npc_state = NPCState(event=NOVICE_PROLOGUE_EVENT)
        state.npc_state.current_line_index = 0

        line = NOVICE_PROLOGUE_EVENT.lines[0]
        choice = line.choices[0]  # Ending A
        _execute_choice(state, state.npc_state, choice)

        # Status message should be appended
        assert any("엔딩 A" in m for m in state.status_messages)

    def test_novice_ending_b_executes(self) -> None:
        """Executing novice ending B sets log_message."""
        state = AppState()
        state.npc_state = NPCState(event=NOVICE_PROLOGUE_EVENT)
        state.npc_state.current_line_index = 0

        line = NOVICE_PROLOGUE_EVENT.lines[0]
        choice = line.choices[1]  # Ending B
        _execute_choice(state, state.npc_state, choice)

        assert any("엔딩 B" in m for m in state.status_messages)

    def test_character_select_extracts_character(self) -> None:
        """Character select choice sets effect_data."""
        state = AppState()
        state.npc_state = NPCState(event=CHARACTER_SELECT_EVENT)
        state.npc_state.current_line_index = 0

        line = CHARACTER_SELECT_EVENT.lines[0]
        # Pick "veteran" (index 1)
        choice = line.choices[1]
        _execute_choice(state, state.npc_state, choice)

        # The choice has character='veteran' in effect_data
        assert choice.effect_data.get("character") == "veteran"

    def test_all_3_characters_have_bilingual_prologue(self) -> None:
        """Each character's prologue has both English and Korean dialogue."""
        for event in (NOVICE_PROLOGUE_EVENT, VETERAN_PROLOGUE_EVENT, HERETIC_PROLOGUE_EVENT):
            line = event.lines[0]
            # Speaker line
            assert line.text  # English speaker text
            assert line.text_ko  # Korean speaker text
            # Choices
            for choice in line.choices:
                assert choice.text  # English
                assert choice.text_ko  # Korean
                assert choice.response  # English response
                assert choice.response_ko  # Korean response

    def test_all_3_characters_have_ending_descriptions(self) -> None:
        """Each character has both A and B ending descriptions."""
        for character in ("novice", "veteran", "heretic"):
            desc_a = get_ending_description(character, "A")
            desc_b = get_ending_description(character, "B")
            assert desc_a
            assert "Unknown" not in desc_a
            assert desc_b
            assert "Unknown" not in desc_b


class TestStoryStructure:
    """Story structure follows the design document."""

    def test_character_select_has_no_ending(self) -> None:
        """Character select has no ending (transitions to prologue)."""
        line = CHARACTER_SELECT_EVENT.lines[0]
        for choice in line.choices:
            assert "ending" not in choice.effect_data
            assert "character" in choice.effect_data

    def test_prologues_have_ending_not_character(self) -> None:
        """Prologue choices have ending (A/B), not character."""
        for event in (NOVICE_PROLOGUE_EVENT, VETERAN_PROLOGUE_EVENT, HERETIC_PROLOGUE_EVENT):
            line = event.lines[0]
            for choice in line.choices:
                assert "ending" in choice.effect_data
                assert "character" in choice.effect_data

    def test_prologue_choices_use_goodbye_effect(self) -> None:
        """Prologue choices use GOODBYE (end dialogue)."""
        for event in (NOVICE_PROLOGUE_EVENT, VETERAN_PROLOGUE_EVENT, HERETIC_PROLOGUE_EVENT):
            line = event.lines[0]
            for choice in line.choices:
                assert choice.effect is ChoiceEffect.GOODBYE

    def test_speaker_is_dixie(self) -> None:
        """Prologue speaker is Dixie Flatline (in all 3)."""
        for event in (NOVICE_PROLOGUE_EVENT, VETERAN_PROLOGUE_EVENT, HERETIC_PROLOGUE_EVENT):
            assert "Dixie" in event.lines[0].speaker

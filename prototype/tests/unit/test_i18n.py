"""Tests for the i18n Translator (ADR-0010)."""

from __future__ import annotations

from pathlib import Path

from wet_run.i18n import Translator


def test_translator_english(data_dir: Path) -> None:
    t = Translator("en", data_dir=data_dir / "i18n")
    assert t("matrix.entry_message") == "You jack in. The world goes gray."
    assert t("matrix.flatline_message") == "You flatline. Static. Silence."


def test_translator_korean(data_dir: Path) -> None:
    t = Translator("ko", data_dir=data_dir / "i18n")
    assert t("matrix.entry_message") == "잭인. 세계가 회색이 된다."
    # Korean file loaded (keys count > 0)
    assert t.has("matrix.entry_message")
    # Verify key access
    assert t("matrix.flatline_message") == "플랫라인. 정적. 침묵."


def test_translator_missing_key_returns_key() -> None:
    t = Translator("en", data_dir=Path("/nonexistent"))
    assert t("missing.key") == "missing.key"
    assert t("another") == "another"


def test_translator_format_kwargs() -> None:
    t = Translator("en", data_dir=Path("/nonexistent"))
    # We need data with {phase} placeholder
    t._data = {"app": {"phase": "Phase: {phase}"}}  # type: ignore[attr-defined]
    assert t("app.phase", phase="Main Menu") == "Phase: Main Menu"


def test_translator_format_missing_kwarg() -> None:
    t = Translator("en", data_dir=Path("/nonexistent"))
    t._data = {"app": {"phase": "Phase: {phase}"}}  # type: ignore[attr-defined]
    # Missing kwarg: should render placeholder as <name> marker so the
    # UI never shows raw {name} syntax (P2 #14).
    assert t("app.phase") == "Phase: <phase>"


def test_translator_format_partial_kwargs() -> None:
    """Multiple placeholders; only some kwargs supplied → unsupplied
    become ``<name>``, supplied render normally."""
    t = Translator("en", data_dir=Path("/nonexistent"))
    t._data = {"app": {"greeting": "Hello {name}, you have {count} items"}}  # type: ignore[attr-defined]
    assert t("app.greeting", name="Case") == "Hello Case, you have <count> items"
    assert t("app.greeting", count=3) == "Hello <name>, you have 3 items"
    assert t("app.greeting", name="Case", count=3) == "Hello Case, you have 3 items"


def test_translator_format_no_kwargs() -> None:
    """Template with placeholders but no kwargs → markers."""
    t = Translator("en", data_dir=Path("/nonexistent"))
    t._data = {"app": {"x": "Value: {x}"}}  # type: ignore[attr-defined]
    assert t("app.x") == "Value: <x>"


def test_translator_has() -> None:
    t = Translator("en", data_dir=Path("/nonexistent"))
    t._data = {"a": {"b": "value"}}  # type: ignore[attr-defined]
    assert t.has("a.b")
    assert not t.has("a.missing")
    assert not t.has("missing")


def test_translator_repr() -> None:
    t = Translator("en", data_dir=Path("/nonexistent"))
    assert "en" in repr(t)

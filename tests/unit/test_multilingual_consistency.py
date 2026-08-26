import pytest
from core.communication.languages import (
    SUPPORTED_LANGUAGE_SCRIPTS,
    get_language_display_name,
)
from core.communication.templates import TEMPLATES, get_template
from core.domain.enums import Language, Script, Tone


def test_language_registry_contains_exactly_9_languages():
    """Verify that exactly 9 Indian languages are registered in SUPPORTED_LANGUAGE_SCRIPTS."""
    assert len(SUPPORTED_LANGUAGE_SCRIPTS) == 9
    expected_languages = {
        Language.ENGLISH,
        Language.HINDI,
        Language.TAMIL,
        Language.TELUGU,
        Language.KANNADA,
        Language.MALAYALAM,
        Language.MARATHI,
        Language.BENGALI,
        Language.GUJARATI,
    }
    assert set(SUPPORTED_LANGUAGE_SCRIPTS.keys()) == expected_languages


def test_hinglish_and_tanglish_representation():
    """Verify Hinglish and Tanglish display names and script variants."""
    assert get_language_display_name(Language.HINDI, Script.LATIN) == "Hinglish (Hindi in Latin script)"
    assert get_language_display_name(Language.TAMIL, Script.LATIN) == "Tanglish (Tamil in Latin script)"
    assert get_language_display_name(Language.GUJARATI, Script.LATIN) == "Gujarati (Latin script)"
    assert get_language_display_name(Language.GUJARATI, Script.GUJARATI) == "Gujarati (Gujarati script)"


def test_all_9_languages_have_valid_templates():
    """Verify that every supported language returns a valid non-empty headline, body, and CTA."""
    for lang, scripts in SUPPORTED_LANGUAGE_SCRIPTS.items():
        for script in scripts:
            template = get_template(lang, script, Tone.EMPATHETIC)
            assert "headline" in template
            assert "body" in template
            assert "cta" in template
            assert len(template["headline"]) > 0
            assert len(template["body"]) > 0
            assert len(template["cta"]) > 0

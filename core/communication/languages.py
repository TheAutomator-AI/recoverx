from typing import Dict, List, Tuple
from core.domain.enums import Language, Script

SUPPORTED_LANGUAGE_SCRIPTS: Dict[Language, List[Script]] = {
    Language.ENGLISH: [Script.LATIN],
    Language.HINDI: [Script.DEVANAGARI, Script.LATIN],  # Hindi & Hinglish
    Language.TAMIL: [Script.TAMIL, Script.LATIN],       # Tamil & Tanglish
    Language.TELUGU: [Script.TELUGU, Script.LATIN],
    Language.KANNADA: [Script.KANNADA, Script.LATIN],
    Language.MALAYALAM: [Script.MALAYALAM, Script.LATIN],
    Language.MARATHI: [Script.DEVANAGARI, Script.LATIN],
    Language.BENGALI: [Script.BENGALI, Script.LATIN],
    Language.GUJARATI: [Script.GUJARATI, Script.LATIN],
}


def get_language_display_name(lang: Language, script: Script) -> str:
    if lang == Language.HINDI and script == Script.LATIN:
        return "Hinglish (Hindi in Latin script)"
    if lang == Language.TAMIL and script == Script.LATIN:
        return "Tanglish (Tamil in Latin script)"
    if lang == Language.GUJARATI and script == Script.LATIN:
        return "Gujarati (Latin script)"
    return f"{lang.value} ({script.value} script)"

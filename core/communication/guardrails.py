from typing import List, Tuple

FORBIDDEN_PREMATURE_SUCCESS = [
    "payment was successful",
    "money received",
    "paid in full",
    "debited successfully",
    "amount settled",
    "payment completed successfully",
]

FORBIDDEN_THREATENING_TERMS = [
    "legal action",
    "police",
    "court notice",
    "jail",
    "arrest",
    "seize",
    "cibil ruined",
    "blacklisted forever",
    "confiscate",
    "harass",
]

FORBIDDEN_MISLEADING_PROMISES = [
    "100% cashback guaranteed",
    "waived off entirely without merchant approval",
    "guaranteed 0 balance",
    "free money",
]


def validate_message_safety(text: str, is_payment_recovered: bool = False) -> Tuple[bool, List[str]]:
    flags: List[str] = []
    text_lower = text.lower()

    if not is_payment_recovered:
        for phrase in FORBIDDEN_PREMATURE_SUCCESS:
            if phrase in text_lower:
                flags.append(f"VIOLATION_PREMATURE_SUCCESS: Found '{phrase}'")

    for phrase in FORBIDDEN_THREATENING_TERMS:
        if phrase in text_lower:
            flags.append(f"VIOLATION_THREATENING_TONE: Found '{phrase}'")

    for phrase in FORBIDDEN_MISLEADING_PROMISES:
        if phrase in text_lower:
            flags.append(f"VIOLATION_MISLEADING_PROMISE: Found '{phrase}'")

    is_safe = len(flags) == 0
    if is_safe:
        flags.append("PASSED_COMMUNICATION_SAFETY_GUARDRAILS")

    return is_safe, flags


class CommunicationGuardrails:
    """Class interface for communication safety guardrails."""

    @staticmethod
    def validate_message(text: str, is_verified_recovered: bool = False) -> List[str]:
        _, flags = validate_message_safety(text, is_payment_recovered=is_verified_recovered)
        return flags

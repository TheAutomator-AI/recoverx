from typing import Dict, Optional
from core.communication.guardrails import validate_message_safety
from core.communication.languages import SUPPORTED_LANGUAGE_SCRIPTS
from core.communication.templates import get_template
from core.domain.enums import Language, Script, Tone
from core.domain.schemas import (
    CommunicationMessage,
    MultilingualBundle,
    PaymentContext,
)


class CommunicationEngine:
    """
    Multilingual Communication Intelligence Layer for RecoverX.
    Generates high-conversion, empathetic recovery messages across Indian languages and scripts.
    """

    def generate_message(
        self,
        context: PaymentContext,
        language: Optional[Language] = None,
        script: Optional[Script] = None,
        tone: Optional[Tone] = None,
    ) -> CommunicationMessage:
        lang = language or context.customer.preferred_language
        scr = script or context.customer.preferred_script
        t = tone or context.customer.preferred_tone

        tpl = get_template(lang, scr, t)

        headline = tpl["headline"].format(
            order_id=context.order_id,
            name=context.customer.name,
            amount=context.amount,
            reason=context.failure_reason,
        )

        body = tpl["body"].format(
            order_id=context.order_id,
            name=context.customer.name,
            amount=context.amount,
            reason=context.failure_reason,
        )

        cta = tpl["cta"].format(
            order_id=context.order_id,
            name=context.customer.name,
            amount=context.amount,
            reason=context.failure_reason,
        )

        full_text = f"{headline} {body} {cta}"
        is_safe, flags = validate_message_safety(full_text, context.is_previously_recovered)

        return CommunicationMessage(
            language=lang,
            script=scr,
            tone=t,
            headline=headline,
            body=body,
            cta_text=cta,
            is_synthetic=True,
            disclaimer="Simulated communication preview. RecoverX does not initiate unverified real financial transactions.",
            validation_flags=flags,
        )

    def generate_multilingual_bundle(self, context: PaymentContext) -> MultilingualBundle:
        messages: Dict[str, CommunicationMessage] = {}

        # Generate messages across primary combinations
        for lang, scripts in SUPPORTED_LANGUAGE_SCRIPTS.items():
            for scr in scripts:
                key = f"{lang.value}_{scr.value}"
                messages[key] = self.generate_message(
                    context=context,
                    language=lang,
                    script=scr,
                    tone=context.customer.preferred_tone,
                )

        return MultilingualBundle(
            payment_id=context.payment_id,
            selected_language=context.customer.preferred_language,
            selected_script=context.customer.preferred_script,
            selected_tone=context.customer.preferred_tone,
            messages=messages,
        )

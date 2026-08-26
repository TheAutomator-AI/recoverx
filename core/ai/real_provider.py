import json
import os
import time
from typing import Any, Dict, Optional
import httpx
from pydantic import ValidationError
from core.ai.base import AIProvider
from core.ai.context_builder import AIContextBuilder
from core.ai.prompts import DIAGNOSIS_SYSTEM_PROMPT, COMMUNICATION_SYSTEM_PROMPT
from core.communication.guardrails import CommunicationGuardrails
from core.domain.enums import Language, RecoveryAction, Script, Tone
from core.domain.schemas import (
    AIDiagnosisOutput,
    CommunicationMessage,
    ConfidenceFactors,
    PaymentContext,
)


class AIProviderError(Exception):
    """Custom exception raised when an external AI provider fails or returns invalid output."""
    def __init__(self, message: str, error_type: str = "PROVIDER_ERROR", status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


class RealAIProvider(AIProvider):
    """
    Production-grade Real LLM Provider for RecoverX.
    Supports OpenAI, Gemini (OpenAI-compatible), and any compliant REST endpoints.
    Enforces strict Pydantic JSON schema validation and zero-secret leak isolation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        api_base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("AI_MODEL", "gpt-4o-mini")
        self.api_base_url = (
            api_base_url
            or os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds

        # In-memory cache for cost and latency optimization
        self._cache: Dict[str, AIDiagnosisOutput] = {}

    def diagnose_failure(self, context: PaymentContext) -> AIDiagnosisOutput:
        prompt_ctx = AIContextBuilder.build_prompt_context(context)
        fingerprint = AIContextBuilder.compute_fingerprint(prompt_ctx)

        # Check cache
        if fingerprint in self._cache:
            return self._cache[fingerprint]

        if not self.api_key:
            raise AIProviderError(
                message="Missing API key for RealAIProvider. Set OPENAI_API_KEY or GEMINI_API_KEY.",
                error_type="MISSING_CREDENTIALS",
            )

        # Fast offline simulation path when mock-key/offline is specified
        if self.api_key in ("offline", "simulated", "mock-key"):
            diagnosis_output = self._simulate_llm_inference(prompt_ctx)
            self._cache[fingerprint] = diagnosis_output
            return diagnosis_output

        start_time = time.perf_counter()
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            body = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Analyze this payment failure context and output strict structured JSON:\n{json.dumps(prompt_ctx, indent=2)}",
                    },
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }

            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(f"{self.api_base_url}/chat/completions", headers=headers, json=body)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code == 429:
                raise AIProviderError(
                    message="AI Provider Rate Limit Exceeded (HTTP 429)",
                    error_type="RATE_LIMIT",
                    status_code=429,
                )
            elif resp.status_code != 200:
                raise AIProviderError(
                    message=f"AI Provider HTTP Error {resp.status_code}: {resp.text}",
                    error_type="HTTP_ERROR",
                    status_code=resp.status_code,
                )

            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed_json = json.loads(raw_content)

            # Validate structured output against Pydantic schema
            diagnosis_output = self._parse_and_validate_diagnosis(parsed_json)
            # Store in cache
            self._cache[fingerprint] = diagnosis_output
            return diagnosis_output

        except httpx.TimeoutException:
            raise AIProviderError(
                message=f"AI Provider request timed out after {self.timeout_seconds}s",
                error_type="TIMEOUT",
            )
        except json.JSONDecodeError as jde:
            raise AIProviderError(
                message=f"AI Provider returned malformed non-JSON output: {jde}",
                error_type="MALFORMED_JSON",
            )
        except ValidationError as ve:
            raise AIProviderError(
                message=f"AI Provider output schema validation failed: {ve}",
                error_type="SCHEMA_VALIDATION_ERROR",
            )
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                message=f"Unexpected error communicating with AI Provider: {str(e)}",
                error_type="UNKNOWN_ERROR",
            )

    def _parse_and_validate_diagnosis(self, payload: Dict[str, Any]) -> AIDiagnosisOutput:
        # Normalize fields if model outputs alias variants
        diagnosis = payload.get("diagnosis") or payload.get("likely_failure_cause", "Payment Failure")
        action_val = payload.get("recommended_action") or payload.get("recommended_recovery_action", "ESCALATE_HUMAN")
        if isinstance(action_val, str):
            action_val = action_val.upper().strip()
            if action_val not in RecoveryAction._value2member_map_:
                action_val = "ESCALATE_HUMAN"

        raw_factors = payload.get("confidence_factors", {})
        factors = ConfidenceFactors(
            reason_clarity=float(raw_factors.get("reason_clarity", 0.5)),
            historical_pattern=float(raw_factors.get("historical_pattern", 0.5)),
            context_completeness=float(raw_factors.get("context_completeness", 0.5)),
            recovery_history=float(raw_factors.get("recovery_history", 0.5)),
            model_assessment=float(raw_factors.get("model_assessment", 0.5)),
        )

        lang_val = payload.get("communication_language") or payload.get("recommended_language", "English")
        script_val = payload.get("communication_script") or payload.get("recommended_script", "Latin")
        tone_val = payload.get("communication_tone") or payload.get("recommended_tone", "EMPATHETIC")

        return AIDiagnosisOutput(
            likely_failure_cause=diagnosis,
            evidence=payload.get("evidence", {}),
            raw_model_confidence=factors.model_assessment,
            recommended_recovery_action=RecoveryAction(action_val),
            recommended_delay_hours=float(payload.get("recommended_delay_hours", 0.0)),
            confidence_factors=factors,
            recommended_language=Language(lang_val) if lang_val in Language._value2member_map_ else Language.ENGLISH,
            recommended_script=Script(script_val) if script_val in Script._value2member_map_ else Script.LATIN,
            recommended_tone=Tone(tone_val) if tone_val in Tone._value2member_map_ else Tone.EMPATHETIC,
            rationale=payload.get("rationale", "AI diagnostic assessment completed."),
            model_name=self.model_name,
        )

    def _simulate_llm_inference(self, prompt_ctx: Dict[str, Any]) -> AIDiagnosisOutput:
        """High-fidelity offline simulation of real LLM structured inference."""
        payment = prompt_ctx.get("payment", {})
        customer = prompt_ctx.get("customer", {})
        telemetry = prompt_ctx.get("telemetry", {})

        step = payment.get("failure_step", "UNKNOWN")
        reason = payment.get("failure_reason", "")
        amount = float(payment.get("amount", 0.0))
        is_contradictory = telemetry.get("contradictory_logs_detected", False)

        lang_str = customer.get("preferred_language", "English")
        script_str = customer.get("preferred_script", "Latin")
        tone_str = customer.get("preferred_tone", "EMPATHETIC")

        lang = Language(lang_str) if lang_str in Language._value2member_map_ else Language.ENGLISH
        script = Script(script_str) if script_str in Script._value2member_map_ else Script.LATIN
        tone = Tone(tone_str) if tone_str in Tone._value2member_map_ else Tone.EMPATHETIC

        if is_contradictory or "contradictory" in reason.lower():
            return AIDiagnosisOutput(
                likely_failure_cause="Contradictory Telemetry Double Debit Risk",
                evidence={"recon_mismatch": True, "details": reason},
                raw_model_confidence=0.38,
                recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
                recommended_delay_hours=0.0,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.15,
                    historical_pattern=0.40,
                    context_completeness=0.60,
                    recovery_history=0.50,
                    model_assessment=0.38,
                ),
                recommended_language=lang,
                recommended_script=script,
                recommended_tone=Tone.PROFESSIONAL,
                rationale="Mismatched status between PSP gateway and bank recon detected. Escalated to prevent double debit.",
                model_name=self.model_name,
            )

        if amount >= 50000.0:
            return AIDiagnosisOutput(
                likely_failure_cause="High Value Enterprise Transaction Hold",
                evidence={"large_amount_inr": amount, "details": reason},
                raw_model_confidence=0.88,
                recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
                recommended_delay_hours=0.0,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.90,
                    historical_pattern=0.90,
                    context_completeness=0.95,
                    recovery_history=0.85,
                    model_assessment=0.88,
                ),
                recommended_language=lang,
                recommended_script=script,
                recommended_tone=Tone.PROFESSIONAL,
                rationale="Large commercial transaction above autonomous threshold. Enqueued for operator review.",
                model_name=self.model_name,
            )

        if step in ("CARD_EXPIRED", "ACCOUNT_BLOCKED"):
            return AIDiagnosisOutput(
                likely_failure_cause="Permanent Instrument Expiry or Block",
                evidence={"terminal_instrument": True, "details": reason},
                raw_model_confidence=0.95,
                recommended_recovery_action=RecoveryAction.SEND_PAYMENT_LINK if step == "CARD_EXPIRED" else RecoveryAction.ESCALATE_HUMAN,
                recommended_delay_hours=0.0,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.95,
                    historical_pattern=0.90,
                    context_completeness=1.0,
                    recovery_history=0.80,
                    model_assessment=0.95,
                ),
                recommended_language=lang,
                recommended_script=script,
                recommended_tone=tone,
                rationale="Terminal instrument state identified. Automated retries prevented.",
                model_name=self.model_name,
            )

        if step == "INSUFFICIENT_FUNDS":
            return AIDiagnosisOutput(
                likely_failure_cause="Insufficient Funds Balance Timing",
                evidence={"balance_depleted": True, "details": reason},
                raw_model_confidence=0.74,
                recommended_recovery_action=RecoveryAction.RETRY_SMART_SCHEDULE,
                recommended_delay_hours=4.0,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.60,
                    historical_pattern=0.75,
                    context_completeness=0.90,
                    recovery_history=0.70,
                    model_assessment=0.74,
                ),
                recommended_language=lang,
                recommended_script=script,
                recommended_tone=tone,
                rationale="Account balance timing failure. Scheduled smart retry aligned with salary/balance window.",
                model_name=self.model_name,
            )

        if step in ("OTP_EXPIRED", "AUTH_DROPOFF"):
            return AIDiagnosisOutput(
                likely_failure_cause="Authentication 2FA Dropoff",
                evidence={"user_friction": True, "details": reason},
                raw_model_confidence=0.90,
                recommended_recovery_action=RecoveryAction.SEND_PAYMENT_LINK,
                recommended_delay_hours=0.0,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.92,
                    historical_pattern=0.85,
                    context_completeness=0.95,
                    recovery_history=0.85,
                    model_assessment=0.90,
                ),
                recommended_language=lang,
                recommended_script=script,
                recommended_tone=tone,
                rationale="Customer 2FA session expired. Sending friction-free recovery link.",
                model_name=self.model_name,
            )

        # Default transient bank/network timeout
        return AIDiagnosisOutput(
            likely_failure_cause="Transient Bank Switch Timeout",
            evidence={"switch_timeout": True, "details": reason},
            raw_model_confidence=0.92,
            recommended_recovery_action=RecoveryAction.RETRY_NOW,
            recommended_delay_hours=0.0,
            confidence_factors=ConfidenceFactors(
                reason_clarity=0.95,
                historical_pattern=0.88,
                context_completeness=1.0,
                recovery_history=0.90,
                model_assessment=0.92,
            ),
            recommended_language=lang,
            recommended_script=script,
            recommended_tone=tone,
            rationale="Transient network/switch latency detected. Immediate retry recommended.",
            model_name=self.model_name,
        )

    def generate_recovery_plan(self, context: PaymentContext) -> Dict[str, Any]:
        diagnosis = self.diagnose_failure(context)
        return {
            "payment_id": context.payment_id,
            "diagnosis": diagnosis.likely_failure_cause,
            "recommended_action": diagnosis.recommended_recovery_action.value,
            "delay_hours": diagnosis.recommended_delay_hours,
            "confidence": diagnosis.raw_model_confidence,
            "confidence_factors": diagnosis.confidence_factors.model_dump() if diagnosis.confidence_factors else {},
            "suggested_channel": "WHATSAPP" if context.customer.preferred_tone == Tone.EMPATHETIC else "SMS",
            "model_name": self.model_name,
        }

    def generate_recovery_message(
        self,
        context: PaymentContext,
        language: Language,
        script: Script,
        tone: Tone,
    ) -> CommunicationMessage:
        raw_msg = f"Hi {context.customer.name}, your payment of ₹{context.amount:,.2f} could not be processed. Please retry securely."
        flags = CommunicationGuardrails.validate_message(raw_msg, is_verified_recovered=context.is_previously_recovered)

        return CommunicationMessage(
            language=language,
            script=script,
            tone=tone,
            headline=f"Payment Update for Order #{context.order_id}",
            body=raw_msg,
            cta_text="Complete Payment Securely",
            is_synthetic=True,
            disclaimer="Simulated communication preview. RecoverX does not initiate unverified real financial transactions.",
            validation_flags=flags,
        )

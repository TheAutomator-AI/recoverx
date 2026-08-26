from datetime import datetime
from typing import Any, Dict
from core.ai.base import AIProvider
from core.domain.enums import (
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    RecoveryAction,
    Script,
    Tone,
)
from core.domain.schemas import (
    AIDiagnosisOutput,
    CommunicationMessage,
    ConfidenceFactors,
    PaymentContext,
)


class MockAIProvider(AIProvider):
    """
    Deterministic Mock AI Provider for RecoverX.
    Produces high-fidelity structured reasoning across Indian payment failure archetypes.
    """

    def diagnose_failure(self, context: PaymentContext) -> AIDiagnosisOutput:
        reason_lower = context.failure_reason.lower()
        code_upper = (context.failure_code or "").upper()
        step = context.failure_step
        source = context.failure_source

        # Check for contradictory data or duplicate webhook flags
        if context.has_contradictory_records or "contradictory" in reason_lower:
            return AIDiagnosisOutput(
                likely_failure_cause="Contradictory Gateway Callback & Bank Telemetry",
                evidence={
                    "gateway_status": "TIMEOUT",
                    "bank_recon_status": "PENDING_CAPTURE_ANOMALY",
                    "anomaly_detected": True,
                    "risk_flag": "DOUBLE_DEBIT_RISK",
                },
                raw_model_confidence=0.35,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.10,
                    historical_pattern=0.45,
                    context_completeness=0.90,
                    recovery_history=0.90,
                    model_assessment=0.35,
                ),
                recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
                recommended_delay_hours=0.0,
                recommended_language=context.customer.preferred_language,
                recommended_script=context.customer.preferred_script,
                recommended_tone=Tone.PROFESSIONAL,
                rationale=(
                    "Mismatched bank reconciliation records detected. Automatic retry poses double-debit "
                    "risk for the customer. Immediate manual operations review required."
                ),
                model_name="RecoverX-Diagnostic-v1-ContradictionDetector",
            )

        # Terminal Failures: Expired Card / Account Closed / Stolen Card
        if (
            step == FailureStep.CARD_EXPIRED
            or "expired" in reason_lower
            or "blocked" in reason_lower
            or "stolen" in reason_lower
            or "closed" in reason_lower
        ):
            return AIDiagnosisOutput(
                likely_failure_cause="Terminal Instrument Invalidation (Expired/Blocked)",
                evidence={
                    "failure_step": step.value,
                    "instrument_valid": False,
                    "is_terminal": True,
                    "prior_attempts": len(context.previous_attempts),
                },
                raw_model_confidence=0.94,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.95,
                    historical_pattern=0.85,
                    context_completeness=0.90,
                    recovery_history=0.90,
                    model_assessment=0.94,
                ),
                recommended_recovery_action=RecoveryAction.SEND_PAYMENT_LINK,
                recommended_delay_hours=0.0,
                recommended_language=context.customer.preferred_language,
                recommended_script=context.customer.preferred_script,
                recommended_tone=Tone.EMPATHETIC,
                rationale=(
                    "Payment instrument is permanently invalid. Retrying the same instrument will fail "
                    "and penalize merchant health score. Issue a self-serve dynamic payment link."
                ),
                model_name="RecoverX-Diagnostic-v1-TerminalRule",
            )

        # Insufficient Funds (Assisted / Scheduled timing)
        if (
            step == FailureStep.INSUFFICIENT_FUNDS
            or "insufficient" in reason_lower
            or "balance" in reason_lower
            or code_upper in ("NPCI_ERR_51", "INSUFFICIENT_FUNDS", "51")
        ):
            delay = 24.0 if context.payment_method == PaymentMethod.MANDATE_AUTOPAY else 12.0
            return AIDiagnosisOutput(
                likely_failure_cause="Transient Insufficient Balance in Source Account",
                evidence={
                    "failure_code": code_upper or "NPCI_51",
                    "payment_method": context.payment_method.value,
                    "amount": context.amount,
                    "customer_ltv": context.customer.lifetime_value,
                    "prior_success_rate": context.customer.historical_success_rate,
                },
                raw_model_confidence=0.72,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.55,
                    historical_pattern=0.88,
                    context_completeness=0.90,
                    recovery_history=0.90,
                    model_assessment=0.72,
                ),
                recommended_recovery_action=RecoveryAction.RETRY_SMART_SCHEDULE,
                recommended_delay_hours=delay,
                recommended_language=context.customer.preferred_language,
                recommended_script=context.customer.preferred_script,
                recommended_tone=Tone.EMPATHETIC,
                rationale=(
                    f"Account balance failure on {context.payment_method.value}. Recommended recovery via "
                    f"timed schedule (+{delay:.0f}h) or conversational nudge with payment link."
                ),
                model_name="RecoverX-Diagnostic-v1-BalancePredictor",
            )

        # Bank Downtime / NPCI Network Timeout / Transient Error (Autonomous)
        if (
            step in (FailureStep.TIMEOUT, FailureStep.NETWORK_HANDSHAKE)
            or source in (FailureSource.BANK, FailureSource.NETWORK)
            or "timeout" in reason_lower
            or "down" in reason_lower
            or "network" in reason_lower
            or code_upper in ("NPCI_ERR_91", "BANK_96", "TIMEOUT_PSP")
        ):
            attempt_penalty = min(0.3, len(context.previous_attempts) * 0.15)
            confidence = max(0.70, 0.94 - attempt_penalty)
            delay = 1.0 if len(context.previous_attempts) > 0 else 0.0

            return AIDiagnosisOutput(
                likely_failure_cause="Transient Bank / NPCI Switch Network Latency",
                evidence={
                    "failure_code": code_upper or "NPCI_91_TIMEOUT",
                    "switch_status": "DEGRADED",
                    "source": source.value,
                    "attempt_number": context.attempt_number,
                },
                raw_model_confidence=confidence,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.95,
                    historical_pattern=0.90,
                    context_completeness=0.95,
                    recovery_history=0.90 if len(context.previous_attempts) == 0 else 0.65,
                    model_assessment=confidence,
                ),
                recommended_recovery_action=(
                    RecoveryAction.RETRY_NOW
                    if len(context.previous_attempts) == 0
                    else RecoveryAction.RETRY_SMART_SCHEDULE
                ),
                recommended_delay_hours=delay,
                recommended_language=context.customer.preferred_language,
                recommended_script=context.customer.preferred_script,
                recommended_tone=Tone.PROFESSIONAL,
                rationale=(
                    "Issuing bank switch timeout. High historical recovery success upon transient retry "
                    "once bank UPI queue clears."
                ),
                model_name="RecoverX-Diagnostic-v1-SwitchDowntime",
            )

        # User Authentication / OTP Drop-off / User Cancelled
        if (
            step in (FailureStep.AUTHENTICATION, FailureStep.OTP_EXPIRED, FailureStep.USER_CANCELLED)
            or "otp" in reason_lower
            or "cancel" in reason_lower
            or "auth" in reason_lower
        ):
            return AIDiagnosisOutput(
                likely_failure_cause="Customer 2FA Friction / OTP Expiry / Intent Drop",
                evidence={
                    "step": step.value,
                    "customer_segment": context.customer.segment.value,
                    "method": context.payment_method.value,
                },
                raw_model_confidence=0.78,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.85,
                    historical_pattern=0.88,
                    context_completeness=0.90,
                    recovery_history=0.90,
                    model_assessment=0.78,
                ),
                recommended_recovery_action=RecoveryAction.SEND_PAYMENT_LINK,
                recommended_delay_hours=0.25,
                recommended_language=context.customer.preferred_language,
                recommended_script=context.customer.preferred_script,
                recommended_tone=Tone.EMPATHETIC,
                rationale=(
                    "User encountered friction during 2FA or let OTP window expire. Send instant 1-click "
                    "UPI intent / payment link on preferred messaging channel."
                ),
                model_name="RecoverX-Diagnostic-v1-DropoffRescue",
            )

        # Default / Ambiguous Case
        return AIDiagnosisOutput(
            likely_failure_cause="Unspecified Payment Processing Exception",
            evidence={
                "failure_reason": context.failure_reason,
                "attempt": context.attempt_number,
                "source": source.value,
            },
            raw_model_confidence=0.52,
            confidence_factors=ConfidenceFactors(
                reason_clarity=0.40,
                historical_pattern=0.50,
                context_completeness=0.50,
                recovery_history=0.90,
                model_assessment=0.52,
            ),
            recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
            recommended_delay_hours=0.0,
            recommended_language=context.customer.preferred_language,
            recommended_script=context.customer.preferred_script,
            recommended_tone=Tone.PROFESSIONAL,
            rationale=(
                "Failure characteristics are non-standard or lack clear telemetry. Escalating for safety."
            ),
            model_name="RecoverX-Diagnostic-v1-General",
        )

    def generate_recovery_plan(self, context: PaymentContext) -> Dict[str, Any]:
        diagnosis = self.diagnose_failure(context)
        return {
            "payment_id": context.payment_id,
            "diagnosis": diagnosis.likely_failure_cause,
            "recommended_action": diagnosis.recommended_recovery_action.value,
            "delay_hours": diagnosis.recommended_delay_hours,
            "confidence": diagnosis.raw_model_confidence,
            "suggested_channel": "WHATSAPP" if context.customer.preferred_tone == Tone.EMPATHETIC else "SMS",
        }

    def generate_recovery_message(
        self,
        context: PaymentContext,
        language: Language,
        script: Script,
        tone: Tone,
    ) -> CommunicationMessage:
        return CommunicationMessage(
            language=language,
            script=script,
            tone=tone,
            headline=f"Payment Assistance for Order #{context.order_id}",
            body=f"Hi {context.customer.name}, your payment of ₹{context.amount:,.2f} could not be completed. Click below to retry seamlessly.",
            cta_text="Complete Payment Securely",
            is_synthetic=True,
            disclaimer="Simulated communication preview. RecoverX does not initiate unverified real financial transactions.",
            validation_flags=["PASSED_TRUTHFULNESS_CHECK", "PASSED_NON_THREAT_CHECK", "PASSED_SIMULATION_FLAG"],
        )

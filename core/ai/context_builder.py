import hashlib
import json
from typing import Any, Dict
from core.domain.enums import FailureStep
from core.domain.schemas import PaymentContext


class AIContextBuilder:
    """
    Builds a secure, sanitized, structured context payload for real LLM reasoning.
    Ensures secrets/keys are never passed to external AI providers.
    Provides deterministic SHA-256 request fingerprinting for cost/latency caching.
    """

    @staticmethod
    def build_prompt_context(context: PaymentContext) -> Dict[str, Any]:
        cust = context.customer
        is_terminal = context.failure_step in (
            FailureStep.CARD_EXPIRED,
            FailureStep.ACCOUNT_BLOCKED,
        ) or "expired" in context.failure_reason.lower() or "blocked" in context.failure_reason.lower()

        payload = {
            "payment": {
                "payment_id": context.payment_id,
                "order_id": context.order_id,
                "amount": float(context.amount),
                "currency": context.currency,
                "payment_method": context.payment_method.value,
                "failure_source": context.failure_source.value,
                "failure_step": context.failure_step.value,
                "failure_reason": context.failure_reason,
                "failure_code": context.failure_code or "UNKNOWN",
                "attempt_number": context.attempt_number,
            },
            "customer": {
                "segment": cust.segment.value,
                "lifetime_value": float(cust.lifetime_value),
                "historical_success_rate": float(cust.historical_success_rate),
                "historical_failure_rate": float(cust.historical_failure_rate),
                "preferred_language": cust.preferred_language.value,
                "preferred_script": cust.preferred_script.value,
                "preferred_tone": cust.preferred_tone.value,
                "prior_promises_count": cust.prior_promises_count,
            },
            "history": {
                "previous_attempts_count": len(context.previous_attempts),
                "is_previously_recovered": context.is_previously_recovered,
            },
            "telemetry": {
                "has_contradictory_records": context.has_contradictory_records,
                "has_active_in_flight": context.active_recovery_attempts_count > 0,
            },
            "policy_hints": {
                "max_autonomous_retries_limit": 2,
                "high_value_review_threshold": 50000.0,
                "is_terminal_failure": is_terminal,
                "requires_idempotent_execution": True,
            },
        }
        return payload

    @staticmethod
    def compute_fingerprint(context_payload: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of the sanitized context payload."""
        serialized = json.dumps(context_payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

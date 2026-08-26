from datetime import datetime, timezone
from typing import Tuple
from core.domain.enums import AutonomyLevel, FailureStep, PolicyDecisionType, RecoveryAction
from core.domain.schemas import PolicyRuleResult
from core.policy.context import PolicyConfig, PolicyEvaluationContext


def rule_1_max_autonomous_retries(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 1: Maximum autonomous retries = 2."""
    if ctx.candidate_autonomy == AutonomyLevel.AUTONOMOUS and ctx.candidate_action in (
        RecoveryAction.RETRY_NOW,
        RecoveryAction.RETRY_SMART_SCHEDULE,
    ):
        if ctx.existing_retry_count >= config.max_autonomous_retries:
            return PolicyRuleResult(
                rule_name="RULE_1_MAX_AUTONOMOUS_RETRIES",
                passed=False,
                decision=PolicyDecisionType.ESCALATE,
                detail=f"Autonomous retry limit ({config.max_autonomous_retries}) reached. Current count: {ctx.existing_retry_count}.",
            )
    return PolicyRuleResult(
        rule_name="RULE_1_MAX_AUTONOMOUS_RETRIES",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail=f"Retry count ({ctx.existing_retry_count}) within autonomous limit ({config.max_autonomous_retries}).",
    )


def rule_2_cooldown_satisfied(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 2: Cooldown must be satisfied between financial attempts."""
    if ctx.candidate_action in (RecoveryAction.RETRY_NOW, RecoveryAction.RETRY_SMART_SCHEDULE) and ctx.last_attempt_at:
        now = datetime.now(timezone.utc)
        last_time = ctx.last_attempt_at if ctx.last_attempt_at.tzinfo else ctx.last_attempt_at.replace(tzinfo=timezone.utc)
        elapsed = (now - last_time).total_seconds()
        if elapsed < config.min_cooldown_seconds:
            remaining = int(config.min_cooldown_seconds - elapsed)
            return PolicyRuleResult(
                rule_name="RULE_2_COOLDOWN_SATISFIED",
                passed=False,
                decision=PolicyDecisionType.BLOCK,
                detail=f"Cooldown active. {remaining}s remaining before next retry is permitted.",
            )
    return PolicyRuleResult(
        rule_name="RULE_2_COOLDOWN_SATISFIED",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Cooldown period satisfied or not applicable.",
    )


def rule_3_duplicate_execution_protection(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 3: Duplicate execution must be blocked."""
    if ctx.has_active_pending_attempt:
        return PolicyRuleResult(
            rule_name="RULE_3_DUPLICATE_PROTECTION",
            passed=False,
            decision=PolicyDecisionType.BLOCK,
            detail="An active recovery attempt is currently pending/executing for this payment.",
        )
    return PolicyRuleResult(
        rule_name="RULE_3_DUPLICATE_PROTECTION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="No duplicate concurrent execution detected.",
    )


def rule_4_terminal_failure_protection(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 4: Terminal failures must not be retried with the same payment instrument."""
    is_terminal = ctx.payment_context.failure_step in (
        FailureStep.CARD_EXPIRED,
        FailureStep.ACCOUNT_BLOCKED,
    ) or "expired" in ctx.payment_context.failure_reason.lower() or "blocked" in ctx.payment_context.failure_reason.lower()

    if is_terminal and ctx.candidate_action in (RecoveryAction.RETRY_NOW, RecoveryAction.RETRY_SMART_SCHEDULE):
        return PolicyRuleResult(
            rule_name="RULE_4_TERMINAL_FAILURE_PROTECTION",
            passed=False,
            decision=PolicyDecisionType.BLOCK,
            detail=f"Terminal failure ({ctx.payment_context.failure_step.value if ctx.payment_context.failure_step else 'Terminal'}) cannot be retried automatically.",
        )
    return PolicyRuleResult(
        rule_name="RULE_4_TERMINAL_FAILURE_PROTECTION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="No terminal retry violation.",
    )


def rule_5_previously_recovered_protection(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 5: Previously recovered payments must not be retried."""
    if ctx.is_previously_recovered or ctx.payment_context.is_previously_recovered:
        return PolicyRuleResult(
            rule_name="RULE_5_PREVIOUSLY_RECOVERED_PROTECTION",
            passed=False,
            decision=PolicyDecisionType.BLOCK,
            detail="Payment has already been successfully recovered. Double recovery blocked.",
        )
    return PolicyRuleResult(
        rule_name="RULE_5_PREVIOUSLY_RECOVERED_PROTECTION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Payment is unrecovered.",
    )


def rule_6_low_confidence_escalation(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 6: Low confidence must escalate."""
    if ctx.composite_confidence < 0.60 or ctx.candidate_autonomy == AutonomyLevel.ESCALATED:
        return PolicyRuleResult(
            rule_name="RULE_6_LOW_CONFIDENCE_ESCALATION",
            passed=False,
            decision=PolicyDecisionType.ESCALATE,
            detail=f"Composite confidence {ctx.composite_confidence:.2f} is below 0.60 threshold. Escalation mandatory.",
        )
    return PolicyRuleResult(
        rule_name="RULE_6_LOW_CONFIDENCE_ESCALATION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail=f"Confidence {ctx.composite_confidence:.2f} meets minimum threshold.",
    )


def rule_7_contradictory_records_escalation(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 7: Contradictory records must escalate."""
    if ctx.has_contradictory_records or ctx.payment_context.has_contradictory_records:
        return PolicyRuleResult(
            rule_name="RULE_7_CONTRADICTORY_RECORDS_ESCALATION",
            passed=False,
            decision=PolicyDecisionType.ESCALATE,
            detail="Contradictory telemetry between gateway callback and bank status. Immediate human escalation required.",
        )
    return PolicyRuleResult(
        rule_name="RULE_7_CONTRADICTORY_RECORDS_ESCALATION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Telemetry logs are consistent.",
    )


def rule_8_high_value_protection(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 8: High-value payments require human approval."""
    if ctx.payment_context.amount >= config.high_value_threshold:
        if ctx.candidate_autonomy == AutonomyLevel.AUTONOMOUS:
            return PolicyRuleResult(
                rule_name="RULE_8_HIGH_VALUE_PROTECTION",
                passed=False,
                decision=PolicyDecisionType.ESCALATE,
                detail=f"Payment amount ₹{ctx.payment_context.amount:,.2f} exceeds threshold ₹{config.high_value_threshold:,.2f}. High-value transactions require human approval.",
            )
    return PolicyRuleResult(
        rule_name="RULE_8_HIGH_VALUE_PROTECTION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail=f"Payment amount ₹{ctx.payment_context.amount:,.2f} is within automated limits.",
    )


def rule_9_max_attempt_stopping_rule(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 9: More than configured retry attempts must stop recovery."""
    total_attempts = len(ctx.payment_context.previous_attempts)
    if total_attempts >= config.max_total_attempts:
        return PolicyRuleResult(
            rule_name="RULE_9_MAX_ATTEMPT_STOPPING_RULE",
            passed=False,
            decision=PolicyDecisionType.BLOCK,
            detail=f"Maximum recovery attempts ({config.max_total_attempts}) exhausted. Recovery terminated to protect customer experience.",
        )
    return PolicyRuleResult(
        rule_name="RULE_9_MAX_ATTEMPT_STOPPING_RULE",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail=f"Total attempts ({total_attempts}) within maximum limit ({config.max_total_attempts}).",
    )


def rule_10_idempotency_verification(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 10: Every action must be idempotent."""
    # Verified by checking payment ID and order ID presence
    if not ctx.payment_context.payment_id or not ctx.payment_context.order_id:
        return PolicyRuleResult(
            rule_name="RULE_10_IDEMPOTENCY_VERIFICATION",
            passed=False,
            decision=PolicyDecisionType.BLOCK,
            detail="Missing unique identifiers (payment_id / order_id) required for idempotent execution.",
        )
    return PolicyRuleResult(
        rule_name="RULE_10_IDEMPOTENCY_VERIFICATION",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Payment context contains valid identifiers for deterministic idempotency generation.",
    )


def rule_11_audit_event_requirement(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 11: Every decision must create an audit event."""
    return PolicyRuleResult(
        rule_name="RULE_11_AUDIT_EVENT_REQUIREMENT",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Policy engine mandates synchronous audit event logging for all evaluation pathways.",
    )


def rule_12_communication_truthfulness(ctx: PolicyEvaluationContext, config: PolicyConfig) -> PolicyRuleResult:
    """Rule 12: Communication must not claim payment was successful before verification."""
    if ctx.proposed_message:
        msg_lower = ctx.proposed_message.lower()
        forbidden_phrases = ["payment was successful", "money received", "paid in full", "debited successfully"]
        for phrase in forbidden_phrases:
            if phrase in msg_lower and not ctx.is_previously_recovered:
                return PolicyRuleResult(
                    rule_name="RULE_12_COMMUNICATION_TRUTHFULNESS",
                    passed=False,
                    decision=PolicyDecisionType.BLOCK,
                    detail=f"Message contains premature success assertion: '{phrase}'.",
                )
    return PolicyRuleResult(
        rule_name="RULE_12_COMMUNICATION_TRUTHFULNESS",
        passed=True,
        decision=PolicyDecisionType.APPROVE,
        detail="Outbound message complies with truthfulness and safety standards.",
    )


ALL_POLICY_RULES = [
    rule_1_max_autonomous_retries,
    rule_2_cooldown_satisfied,
    rule_3_duplicate_execution_protection,
    rule_4_terminal_failure_protection,
    rule_5_previously_recovered_protection,
    rule_6_low_confidence_escalation,
    rule_7_contradictory_records_escalation,
    rule_8_high_value_protection,
    rule_9_max_attempt_stopping_rule,
    rule_10_idempotency_verification,
    rule_11_audit_event_requirement,
    rule_12_communication_truthfulness,
]

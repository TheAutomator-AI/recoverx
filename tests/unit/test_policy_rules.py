from datetime import datetime, timezone, timedelta
import pytest
from core.domain.enums import AutonomyLevel, CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, PolicyDecisionType, RecoveryAction, Script, Tone
from core.domain.schemas import CustomerContext, PaymentContext
from core.policy.context import PolicyConfig, PolicyEvaluationContext
from core.policy.engine import PolicyEngine
from core.policy.rules import (
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
)


@pytest.fixture
def base_policy_ctx():
    p_ctx = PaymentContext(
        payment_id="pay_pol_001",
        order_id="order_pol_001",
        amount=1500.0,
        currency="INR",
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Network Timeout",
        failure_code="NPCI_91",
        payment_method=PaymentMethod.UPI,
        attempt_number=1,
        customer=CustomerContext(
            customer_id="cust_001",
            name="Aarav Patel",
            segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=10000.0,
            historical_success_rate=0.9,
            historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH,
            preferred_script=Script.LATIN,
            preferred_tone=Tone.EMPATHETIC,
        ),
    )
    return PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.92,
        existing_retry_count=0,
        last_attempt_at=None,
        has_active_pending_attempt=False,
        is_previously_recovered=False,
        has_contradictory_records=False,
        proposed_message="Please retry your payment securely.",
    )


def test_rule_1_max_autonomous_retries(base_policy_ctx):
    config = PolicyConfig(max_autonomous_retries=2)
    # 0 retries -> Pass
    res1 = rule_1_max_autonomous_retries(base_policy_ctx, config)
    assert res1.passed is True

    # 2 retries -> Escalates
    base_policy_ctx.existing_retry_count = 2
    res2 = rule_1_max_autonomous_retries(base_policy_ctx, config)
    assert res2.passed is False
    assert res2.decision == PolicyDecisionType.ESCALATE


def test_rule_2_cooldown(base_policy_ctx):
    config = PolicyConfig(min_cooldown_seconds=1800)
    # Last attempt 10 mins ago -> Block
    base_policy_ctx.last_attempt_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    res = rule_2_cooldown_satisfied(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK

    # Last attempt 40 mins ago -> Pass
    base_policy_ctx.last_attempt_at = datetime.now(timezone.utc) - timedelta(minutes=40)
    res_ok = rule_2_cooldown_satisfied(base_policy_ctx, config)
    assert res_ok.passed is True


def test_rule_3_duplicate_protection(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.has_active_pending_attempt = True
    res = rule_3_duplicate_execution_protection(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK


def test_rule_4_terminal_failure_protection(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.payment_context.failure_step = FailureStep.CARD_EXPIRED
    base_policy_ctx.payment_context.failure_reason = "Customer card expired"
    res = rule_4_terminal_failure_protection(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK


def test_rule_5_previously_recovered(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.is_previously_recovered = True
    res = rule_5_previously_recovered_protection(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK


def test_rule_6_low_confidence(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.composite_confidence = 0.45
    base_policy_ctx.candidate_autonomy = AutonomyLevel.ESCALATED
    res = rule_6_low_confidence_escalation(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.ESCALATE


def test_rule_7_contradictory_records(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.has_contradictory_records = True
    res = rule_7_contradictory_records_escalation(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.ESCALATE


def test_rule_8_high_value_protection(base_policy_ctx):
    config = PolicyConfig(high_value_threshold=50000.0)
    base_policy_ctx.payment_context.amount = 75000.0
    res = rule_8_high_value_protection(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.ESCALATE


def test_rule_9_stopping_rule(base_policy_ctx):
    config = PolicyConfig(max_total_attempts=4)
    base_policy_ctx.payment_context.previous_attempts = [{}, {}, {}, {}]
    res = rule_9_max_attempt_stopping_rule(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK


def test_rule_10_idempotency(base_policy_ctx):
    config = PolicyConfig()
    res = rule_10_idempotency_verification(base_policy_ctx, config)
    assert res.passed is True

    base_policy_ctx.payment_context.order_id = ""
    res_fail = rule_10_idempotency_verification(base_policy_ctx, config)
    assert res_fail.passed is False


def test_rule_12_communication_truthfulness(base_policy_ctx):
    config = PolicyConfig()
    base_policy_ctx.is_previously_recovered = False
    base_policy_ctx.proposed_message = "Your payment was successful and settled!"
    res = rule_12_communication_truthfulness(base_policy_ctx, config)
    assert res.passed is False
    assert res.decision == PolicyDecisionType.BLOCK


def test_policy_engine_complete_pass(base_policy_ctx):
    engine = PolicyEngine()
    eval_res = engine.evaluate(base_policy_ctx)
    assert eval_res.decision == PolicyDecisionType.APPROVE
    assert len(eval_res.rules_evaluated) == 12


def test_confidence_does_not_equal_authorization(base_policy_ctx):
    """
    Core Axiom Test:
    Even with 99% composite confidence, deterministic policy engine MUST BLOCK
    unsafe actions (terminal card expired, duplicate in-flight, or contradictory logs).
    """
    engine = PolicyEngine()
    base_policy_ctx.composite_confidence = 0.99
    base_policy_ctx.candidate_autonomy = AutonomyLevel.AUTONOMOUS
    base_policy_ctx.payment_context.failure_step = FailureStep.CARD_EXPIRED
    base_policy_ctx.candidate_action = RecoveryAction.RETRY_NOW

    # Even with 0.99 confidence, retrying an expired card MUST be blocked
    eval_res = engine.evaluate(base_policy_ctx)
    assert eval_res.decision == PolicyDecisionType.BLOCK
    assert any("RULE_4" in r for r in eval_res.reasons)

    # Even with 0.99 confidence, contradictory logs MUST escalate
    base_policy_ctx.payment_context.failure_step = FailureStep.TIMEOUT
    base_policy_ctx.has_contradictory_records = True
    eval_res_contra = engine.evaluate(base_policy_ctx)
    assert eval_res_contra.decision == PolicyDecisionType.ESCALATE
    assert any("RULE_7" in r for r in eval_res_contra.reasons)


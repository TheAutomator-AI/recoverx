from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.ai.base import AIProvider
from core.ai.real_provider import AIProviderError, RealAIProvider
from core.communication.guardrails import CommunicationGuardrails, validate_message_safety
from core.confidence.engine import ConfidenceEngine
from core.domain.enums import (
    AttemptStatus,
    AuditActor,
    AutonomyLevel,
    CustomerSegment,
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    PaymentStatus,
    PolicyDecisionType,
    RecoveryAction,
    Script,
    Tone,
)
from core.domain.models import AuditEvent, Base, Payment, RecoveryAttempt
from core.domain.schemas import (
    AIDiagnosisOutput,
    ConfidenceFactors,
    CustomerContext,
    PaymentContext,
    PaymentEventIn,
)
from core.policy.context import PolicyConfig, PolicyEvaluationContext
from core.policy.engine import PolicyEngine
from core.recovery.orchestrator import RecoveryOrchestrator


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class MockAdversarialAIProvider(AIProvider):
    """Adversarial AI Provider that generates intentionally unsafe or high-confidence recommendations."""

    def __init__(self, override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99, low_factors=False):
        self.override_action = override_action
        self.override_confidence = override_confidence
        self.low_factors = low_factors

    def diagnose_failure(self, context: PaymentContext) -> AIDiagnosisOutput:
        if self.low_factors:
            factors = ConfidenceFactors(
                reason_clarity=0.20,
                historical_pattern=0.30,
                context_completeness=0.50,
                recovery_history=0.50,
                model_assessment=self.override_confidence,
            )
        else:
            factors = ConfidenceFactors(
                reason_clarity=0.99,
                historical_pattern=0.99,
                context_completeness=0.99,
                recovery_history=0.99,
                model_assessment=self.override_confidence,
            )

        return AIDiagnosisOutput(
            likely_failure_cause="Adversarial Hallucination Diagnosis",
            evidence={"hallucinated_signal": "System operational, safe to retry"},
            raw_model_confidence=self.override_confidence,
            confidence_factors=factors,
            recommended_recovery_action=self.override_action,
            recommended_delay_hours=0.0,
            recommended_language=Language.ENGLISH,
            recommended_script=Script.LATIN,
            recommended_tone=Tone.PROFESSIONAL,
            rationale="Adversarial suggestion to bypass checks",
            model_name="Adversarial-LLM-v1",
        )

    def generate_recovery_plan(self, context: PaymentContext):
        return {}

    def generate_recovery_message(self, context: PaymentContext, language: Language, script: Script, tone: Tone):
        from core.domain.schemas import CommunicationMessage
        return CommunicationMessage(
            language=language, script=script, tone=tone,
            headline="Payment Notice", body="Please complete payment.",
            cta_text="Retry", is_synthetic=True, disclaimer="Demo preview",
            validation_flags=["PASSED_COMMUNICATION_SAFETY_GUARDRAILS"],
        )


# Scenario 1: AI High-Confidence Wrong Recommendation on Expired Card
def test_scenario_1_ai_high_confidence_wrong_recommendation(db):
    """AI hallucinates 99% confidence to RETRY an expired card -> Policy Rule 4 MUST BLOCK."""
    adversarial_ai = MockAdversarialAIProvider(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99)
    orchestrator = RecoveryOrchestrator(db=db, ai_provider=adversarial_ai)

    event = PaymentEventIn(
        order_id="ORD_ADV_01",
        amount=1999.0,
        currency="INR",
        customer_name="Test Customer",
        customer_segment=CustomerSegment.DIRECT_TO_CONSUMER,
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.CARD_EXPIRED,
        failure_reason="Card expired at bank switch",
        payment_method=PaymentMethod.CARD,
    )

    res = orchestrator.process_failed_payment_event(event)

    assert res["policy_decision"] == PolicyDecisionType.BLOCK.value
    assert res["status"] in (PaymentStatus.TERMINAL_FAILED.value, PaymentStatus.FAILED.value)
    # Zero financial execution
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
    assert len(attempts) == 0


# Scenario 2: AI Low-Confidence on Recoverable Case
def test_scenario_2_ai_low_confidence_recoverable(db):
    """AI assigns low confidence to recoverable timeout -> Routed safely to Assisted/Escalated, no unsafe auto-execution."""
    low_conf_ai = MockAdversarialAIProvider(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.25, low_factors=True)
    orchestrator = RecoveryOrchestrator(db=db, ai_provider=low_conf_ai)

    event = PaymentEventIn(
        order_id="ORD_ADV_02",
        amount=2500.0,
        currency="INR",
        customer_name="Pooja Sharma",
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Network switch latency",
        payment_method=PaymentMethod.UPI,
    )

    res = orchestrator.process_failed_payment_event(event)

    assert res["autonomy_level"] == AutonomyLevel.ESCALATED.value
    assert res["policy_decision"] in (PolicyDecisionType.ESCALATE.value, PolicyDecisionType.APPROVE.value)
    # Ensure no automated immediate execution
    assert res["status"] != PaymentStatus.RECOVERED.value


# Scenario 3: Contradictory Gateway/Bank Telemetry
def test_scenario_3_contradictory_gateway_bank_telemetry(db):
    """Gateway timeout vs Bank Pending Capture -> Rule 7 MUST ESCALATE/BLOCK to prevent double debit."""
    orchestrator = RecoveryOrchestrator(db=db)

    event = PaymentEventIn(
        order_id="ORD_ADV_03",
        amount=45000.0,
        currency="INR",
        customer_name="Rajesh Patel",
        failure_source=FailureSource.GATEWAY,
        failure_step=FailureStep.CONTRADICTORY_STATUS,
        failure_reason="Contradictory state: gateway timeout vs bank capture pending",
        payment_method=PaymentMethod.UPI,
        metadata={"contradictory_logs": True},
    )

    res = orchestrator.process_failed_payment_event(event)

    assert res["policy_decision"] == PolicyDecisionType.ESCALATE.value
    assert res["autonomy_level"] == AutonomyLevel.ESCALATED.value
    assert res["status"] == PaymentStatus.ESCALATED.value
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
    assert len(attempts) == 0


# Scenario 4: Duplicate Webhook in Flight
def test_scenario_4_duplicate_webhook_in_flight(db):
    """Duplicate event arrives while recovery attempt is actively executing -> Rule 3 MUST BLOCK."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_04", name="User", segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_04", order_id="ord_adv_04", amount=1200.0, currency="INR",
        failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
        payment_method=PaymentMethod.UPI, attempt_number=1, customer=cust, previous_attempts=[],
        has_contradictory_records=False,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.92,
        existing_retry_count=0,
        has_active_pending_attempt=True,  # Active execution in-flight
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.BLOCK
    assert any("RULE_3" in r for r in result.reasons)


# Scenario 5: Replayed Recovered Payment
def test_scenario_5_replayed_recovered_payment(db):
    """Payment already settled as RECOVERED receives replay event -> Rule 5 MUST BLOCK."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_05", name="User", segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_05", order_id="ord_adv_05", amount=3500.0, currency="INR",
        failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
        payment_method=PaymentMethod.UPI, attempt_number=1, customer=cust, previous_attempts=[],
        has_contradictory_records=False, is_previously_recovered=True,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.95,
        is_previously_recovered=True,
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.BLOCK
    assert any("RULE_5" in r for r in result.reasons)


# Scenario 6: High-Value Payment Governance
def test_scenario_6_high_value_payment(db):
    """Large commercial invoice (₹75,000 >= ₹50,000 threshold) -> Rule 8 MUST ESCALATE for human review."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_06", name="VIP Enterprise", segment=CustomerSegment.VIP,
        lifetime_value=500000.0, historical_success_rate=0.95, historical_failure_rate=0.05,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.PROFESSIONAL,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_06", order_id="ord_adv_06", amount=75000.0, currency="INR",
        failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
        payment_method=PaymentMethod.NETBANKING, attempt_number=1, customer=cust, previous_attempts=[],
        has_contradictory_records=False,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.94,
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.ESCALATE
    assert any("RULE_8" in r for r in result.reasons)


# Scenario 7: Maximum Retry Violation
def test_scenario_7_max_retry_violation(db):
    """Attempt count exceeds autonomous limit (2) or total stopping limit (4) -> Policy MUST ESCALATE / BLOCK."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_07", name="User", segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_07", order_id="ord_adv_07", amount=1500.0, currency="INR",
        failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
        payment_method=PaymentMethod.UPI, attempt_number=3, customer=cust,
        previous_attempts=[{}, {}, {}], has_contradictory_records=False,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.90,
        existing_retry_count=2,  # Max autonomous retries reached
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.ESCALATE
    assert any("RULE_1" in r for r in result.reasons)


# Scenario 8: Cooldown Window Violation
def test_scenario_8_cooldown_violation(db):
    """Retry attempted within 30-minute cooling period -> Rule 2 MUST BLOCK."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_08", name="User", segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_08", order_id="ord_adv_08", amount=1500.0, currency="INR",
        failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
        payment_method=PaymentMethod.UPI, attempt_number=2, customer=cust, previous_attempts=[{}],
        has_contradictory_records=False,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.90,
        last_attempt_at=datetime.now(timezone.utc) - timedelta(minutes=5),  # 5m ago < 30m
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.BLOCK
    assert any("RULE_2" in r for r in result.reasons)


# Scenario 9: Malformed AI Output
def test_scenario_9_malformed_ai_output(db):
    """AI returns invalid non-JSON corrupted payload -> RealAIProvider raises error, Orchestrator safely logs AI_PROVIDER_FAILURE."""
    failing_provider = RealAIProvider(api_key="mock-key")
    with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("Malformed JSON output", "MALFORMED_JSON")):
        orchestrator = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
        event = PaymentEventIn(
            order_id="ORD_ADV_09", amount=3000.0, currency="INR", customer_name="Test User",
            failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
            payment_method=PaymentMethod.UPI,
        )
        res = orchestrator.process_failed_payment_event(event)

        assert res["autonomy_level"] in ("ASSISTED", "ESCALATED")
        assert res["policy_decision"] in ("ESCALATE", "BLOCK")
        audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
        assert any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits)


# Scenario 10: AI Provider Timeout
def test_scenario_10_ai_provider_timeout(db):
    """External LLM provider times out -> Orchestrator captures error, logs AI_PROVIDER_FAILURE, and halts auto-execution."""
    failing_provider = RealAIProvider(api_key="mock-key")
    with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("API call timed out after 8s", "TIMEOUT")):
        orchestrator = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
        event = PaymentEventIn(
            order_id="ORD_ADV_10", amount=4000.0, currency="INR", customer_name="Test User",
            failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
            payment_method=PaymentMethod.UPI,
        )
        res = orchestrator.process_failed_payment_event(event)

        assert res["autonomy_level"] in ("ASSISTED", "ESCALATED")
        assert res["status"] != PaymentStatus.RECOVERED.value
        audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
        assert any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits)


# Scenario 11: AI Rate Limit Failure (HTTP 429)
def test_scenario_11_ai_rate_limit_failure(db):
    """External LLM provider returns HTTP 429 -> Orchestrator escalates safely."""
    failing_provider = RealAIProvider(api_key="mock-key")
    with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("Rate limit exceeded", "RATE_LIMIT", status_code=429)):
        orchestrator = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
        event = PaymentEventIn(
            order_id="ORD_ADV_11", amount=5000.0, currency="INR", customer_name="Test User",
            failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
            payment_method=PaymentMethod.UPI,
        )
        res = orchestrator.process_failed_payment_event(event)

        assert res["autonomy_level"] in ("ASSISTED", "ESCALATED")
        audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
        assert any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits)


# Scenario 12: Unsafe Multilingual Message Guardrails
def test_scenario_12_unsafe_multilingual_message():
    """Unsafe message claiming premature payment success or threatening legal action -> Guardrails MUST CATCH."""
    unsafe_premature = "Your payment completed successfully and money received."
    is_safe_1, flags_1 = validate_message_safety(unsafe_premature, is_payment_recovered=False)
    assert is_safe_1 is False
    assert any("VIOLATION_PREMATURE_SUCCESS" in f for f in flags_1)

    unsafe_threatening = "Pay immediately or face legal action, police, and arrest."
    is_safe_2, flags_2 = validate_message_safety(unsafe_threatening, is_payment_recovered=False)
    assert is_safe_2 is False
    assert any("VIOLATION_THREATENING_TONE" in f for f in flags_2)


# Scenario 13: Missing Customer Context
def test_scenario_13_missing_customer_context(db):
    """Context missing order/payment identifiers -> Policy Rule 10 Idempotency MUST BLOCK."""
    policy_engine = PolicyEngine()
    cust = CustomerContext(
        customer_id="c_adv_13", name="", segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=0.0, historical_success_rate=0.0, historical_failure_rate=0.0,
        preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
    )
    p_ctx = PaymentContext(
        payment_id="pay_adv_13", order_id="",  # Missing required order_id
        amount=1000.0, currency="INR", failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT,
        failure_reason="Timeout", payment_method=PaymentMethod.UPI, attempt_number=1, customer=cust,
        previous_attempts=[], has_contradictory_records=False,
    )
    eval_ctx = PolicyEvaluationContext(
        payment_context=p_ctx,
        candidate_action=RecoveryAction.RETRY_NOW,
        candidate_autonomy=AutonomyLevel.AUTONOMOUS,
        composite_confidence=0.90,
    )

    result = policy_engine.evaluate(eval_ctx)
    assert result.decision == PolicyDecisionType.BLOCK
    assert any("RULE_10" in r for r in result.reasons)


# Scenario 14: MEMORABLE DEMO SCENARIO — "AI Confidence Trap"
def test_scenario_14_ai_confidence_trap_memorable_demo(db):
    """
    AI CONFIDENCE TRAP:
    - Input: AI recommendation = RETRY_NOW, model confidence ~ 0.99, amount = ₹85,000, contradictory telemetry.
    - Expected:
        * AI recommends RETRY_NOW with 0.99 raw confidence
        * Deterministic ConfidenceEngine caps confidence due to contradiction anomaly
        * Deterministic PolicyEngine returns BLOCK/ESCALATE (Rule 7 and Rule 8)
        * Financial Execution = NONE (0 attempts)
        * Human Escalation = YES (Status = ESCALATED)
        * Complete immutable audit events created
    PROVES: 'Confidence is not permission.'
    """
    trap_ai = MockAdversarialAIProvider(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99)
    orchestrator = RecoveryOrchestrator(db=db, ai_provider=trap_ai)

    event = PaymentEventIn(
        order_id="ORD_CONFIDENCE_TRAP_VIP",
        amount=85000.0,  # High value commercial transaction
        currency="INR",
        customer_name="Vikram Singhania",
        customer_segment=CustomerSegment.VIP,
        failure_source=FailureSource.GATEWAY,
        failure_step=FailureStep.CONTRADICTORY_STATUS,
        failure_reason="Gateway timeout vs Bank Capture Pending Recon",
        payment_method=PaymentMethod.NETBANKING,
        metadata={"contradictory_logs": True},
    )

    res = orchestrator.process_failed_payment_event(event)

    # 1. AI recommended RETRY_NOW with 0.99 confidence
    assert res["recommended_action"] == RecoveryAction.RETRY_NOW.value

    # 2. ConfidenceEngine capped confidence due to contradiction anomaly
    assert res["confidence"] <= 0.48

    # 3. PolicyEngine escalated / blocked the action
    assert res["policy_decision"] == PolicyDecisionType.ESCALATE.value
    assert any("RULE_7" in r or "RULE_8" in r for r in res["policy_reasons"])

    # 4. Zero financial execution
    assert res["status"] == PaymentStatus.ESCALATED.value
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
    assert len(attempts) == 0

    # 5. Audit trail integrity
    audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
    event_types = [a.event_type for a in audits]
    assert "PAYMENT_FAILED" in event_types
    assert "AI_DIAGNOSED" in event_types
    assert "CONFIDENCE_CALCULATED" in event_types
    assert "POLICY_EVALUATED" in event_types
    assert "HUMAN_REVIEW_QUEUED" in event_types
    assert "ACTION_APPROVED" not in event_types
    assert "ACTION_EXECUTED" not in event_types

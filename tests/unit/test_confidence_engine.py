import pytest
from core.confidence.engine import ConfidenceEngine
from core.confidence.weights import ConfidenceThresholds, ConfidenceWeights
from core.domain.enums import AutonomyLevel, CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, RecoveryAction, Script, Tone
from core.domain.schemas import AIDiagnosisOutput, CustomerContext, PaymentContext


@pytest.fixture
def base_context():
    return PaymentContext(
        payment_id="pay_test_001",
        order_id="order_test_001",
        amount=2500.0,
        currency="INR",
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Issuing bank switch timeout",
        failure_code="NPCI_ERR_91",
        payment_method=PaymentMethod.UPI,
        attempt_number=1,
        is_simulated=True,
        customer=CustomerContext(
            customer_id="cust_001",
            name="Priya Sharma",
            segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=25000.0,
            historical_success_rate=0.92,
            historical_failure_rate=0.08,
            preferred_language=Language.HINDI,
            preferred_script=Script.LATIN,
            preferred_tone=Tone.EMPATHETIC,
        ),
    )


def test_confidence_engine_high_confidence(base_context):
    engine = ConfidenceEngine()
    diagnosis = AIDiagnosisOutput(
        likely_failure_cause="Bank Timeout",
        evidence={"switch_status": "DEGRADED"},
        raw_model_confidence=0.92,
        recommended_recovery_action=RecoveryAction.RETRY_NOW,
        recommended_delay_hours=0.0,
        recommended_language=Language.HINDI,
        recommended_script=Script.LATIN,
        recommended_tone=Tone.EMPATHETIC,
        rationale="Clear transient failure with high historical recovery",
    )

    breakdown = engine.calibrate(base_context, diagnosis)

    assert breakdown.composite_confidence >= 0.85
    assert breakdown.autonomy_candidate == AutonomyLevel.AUTONOMOUS
    assert breakdown.reason_clarity_score > 0.8
    assert breakdown.context_completeness_score > 0.8


def test_confidence_engine_contradiction_penalization(base_context):
    base_context.has_contradictory_records = True
    engine = ConfidenceEngine()
    diagnosis = AIDiagnosisOutput(
        likely_failure_cause="Contradictory Telemetry",
        evidence={"anomaly": True},
        raw_model_confidence=0.40,
        recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
        recommended_delay_hours=0.0,
        recommended_language=Language.ENGLISH,
        recommended_script=Script.LATIN,
        recommended_tone=Tone.PROFESSIONAL,
        rationale="Mismatched logs detected",
    )

    breakdown = engine.calibrate(base_context, diagnosis)

    assert breakdown.composite_confidence < 0.60
    assert breakdown.autonomy_candidate == AutonomyLevel.ESCALATED
    assert breakdown.reason_clarity_score <= 0.15


def test_confidence_weights_validation():
    weights = ConfidenceWeights()
    assert weights.validate_weights() is True

import pytest
from core.ai.mock_provider import MockAIProvider
from core.domain.enums import CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, RecoveryAction, Script, Tone
from core.domain.schemas import CustomerContext, PaymentContext


@pytest.fixture
def make_context():
    def _create(step=FailureStep.TIMEOUT, reason="Timeout", code="NPCI_91", contradictory=False, amount=1000.0):
        return PaymentContext(
            payment_id="pay_ai_01",
            order_id="ORD_AI_01",
            amount=amount,
            currency="INR",
            failure_source=FailureSource.BANK,
            failure_step=step,
            failure_reason=reason,
            failure_code=code,
            payment_method=PaymentMethod.UPI,
            attempt_number=1,
            has_contradictory_records=contradictory,
            customer=CustomerContext(
                customer_id="c1",
                name="Deepa Hegde",
                segment=CustomerSegment.DIRECT_TO_CONSUMER,
                lifetime_value=12000.0,
                historical_success_rate=0.9,
                historical_failure_rate=0.1,
                preferred_language=Language.KANNADA,
                preferred_script=Script.KANNADA,
                preferred_tone=Tone.EMPATHETIC,
            ),
        )
    return _create


def test_ai_diagnose_timeout(make_context):
    ai = MockAIProvider()
    ctx = make_context(step=FailureStep.TIMEOUT, reason="NPCI switch timeout", code="NPCI_ERR_91")
    diag = ai.diagnose_failure(ctx)
    assert diag.recommended_recovery_action == RecoveryAction.RETRY_NOW
    assert diag.raw_model_confidence > 0.8
    assert "Transient" in diag.likely_failure_cause


def test_ai_diagnose_expired_card(make_context):
    ai = MockAIProvider()
    ctx = make_context(step=FailureStep.CARD_EXPIRED, reason="Card is expired", code="CARD_54")
    diag = ai.diagnose_failure(ctx)
    assert diag.recommended_recovery_action == RecoveryAction.SEND_PAYMENT_LINK
    assert diag.raw_model_confidence > 0.9


def test_ai_diagnose_contradictory(make_context):
    ai = MockAIProvider()
    ctx = make_context(step=FailureStep.CONTRADICTORY_STATUS, reason="Mismatched recon", contradictory=True)
    diag = ai.diagnose_failure(ctx)
    assert diag.recommended_recovery_action == RecoveryAction.ESCALATE_HUMAN
    assert diag.raw_model_confidence < 0.5

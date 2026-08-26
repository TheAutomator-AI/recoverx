import pytest
from core.communication.engine import CommunicationEngine
from core.communication.guardrails import validate_message_safety
from core.domain.enums import CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, Script, Tone
from core.domain.schemas import CustomerContext, PaymentContext


@pytest.fixture
def comm_context():
    return PaymentContext(
        payment_id="pay_comm_01",
        order_id="ORD_12345",
        amount=1999.0,
        currency="INR",
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Bank network timeout",
        failure_code="NPCI_91",
        payment_method=PaymentMethod.UPI,
        attempt_number=1,
        customer=CustomerContext(
            customer_id="c1",
            name="Ananya Iyer",
            segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=5000.0,
            historical_success_rate=0.9,
            historical_failure_rate=0.1,
            preferred_language=Language.TAMIL,
            preferred_script=Script.TAMIL,
            preferred_tone=Tone.EMPATHETIC,
        ),
    )


def test_communication_engine_tamil(comm_context):
    engine = CommunicationEngine()
    msg = engine.generate_message(comm_context)
    assert msg.language == Language.TAMIL
    assert msg.script == Script.TAMIL
    assert "₹1,999.00" in msg.body
    assert "ஆர்டர்" in msg.headline
    assert msg.is_synthetic is True


def test_communication_engine_multilingual_bundle(comm_context):
    engine = CommunicationEngine()
    bundle = engine.generate_multilingual_bundle(comm_context)
    assert len(bundle.messages) >= 9
    assert "Hindi_Devanagari" in bundle.messages
    assert "Hindi_Latin" in bundle.messages
    assert "Tamil_Tamil" in bundle.messages
    assert "Tamil_Latin" in bundle.messages
    assert "Telugu_Telugu" in bundle.messages
    assert "Bengali_Bengali" in bundle.messages


def test_communication_guardrails_violations():
    # Test premature success
    safe, flags = validate_message_safety("Your payment was successful!", is_payment_recovered=False)
    assert safe is False
    assert any("VIOLATION_PREMATURE_SUCCESS" in f for f in flags)

    # Test threatening term
    safe_threat, flags_threat = validate_message_safety("Pay now or legal action will be taken!")
    assert safe_threat is False
    assert any("VIOLATION_THREATENING_TONE" in f for f in flags_threat)

    # Test valid message
    safe_ok, flags_ok = validate_message_safety("Please retry your payment securely using UPI.")
    assert safe_ok is True

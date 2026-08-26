import pytest
from core.ai.context_builder import AIContextBuilder
from core.domain.enums import CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, Script, Tone
from core.domain.schemas import CustomerContext, PaymentContext


@pytest.fixture
def sample_payment_context():
    cust = CustomerContext(
        customer_id="cust_test_01",
        name="Aditi Rao",
        segment=CustomerSegment.DIRECT_TO_CONSUMER,
        lifetime_value=18500.0,
        historical_success_rate=0.92,
        historical_failure_rate=0.08,
        preferred_language=Language.HINDI,
        preferred_script=Script.LATIN,
        preferred_tone=Tone.EMPATHETIC,
        prior_promises_count=0,
    )
    return PaymentContext(
        payment_id="pay_test_101",
        order_id="order_test_101",
        amount=2499.0,
        currency="INR",
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="NPCI UPI Switch timeout",
        failure_code="NPCI_ERR_91",
        payment_method=PaymentMethod.UPI,
        attempt_number=1,
        customer=cust,
        previous_attempts=[],
        has_contradictory_records=False,
    )


def test_build_prompt_context_structure(sample_payment_context):
    prompt_ctx = AIContextBuilder.build_prompt_context(sample_payment_context)

    assert "payment" in prompt_ctx
    assert "customer" in prompt_ctx
    assert "history" in prompt_ctx
    assert "telemetry" in prompt_ctx
    assert "policy_hints" in prompt_ctx

    assert prompt_ctx["payment"]["amount"] == 2499.0
    assert prompt_ctx["payment"]["failure_code"] == "NPCI_ERR_91"
    assert prompt_ctx["customer"]["preferred_language"] == "Hindi"
    assert prompt_ctx["customer"]["preferred_script"] == "Latin"
    assert prompt_ctx["policy_hints"]["is_terminal_failure"] is False


def test_context_fingerprint_deterministic(sample_payment_context):
    ctx1 = AIContextBuilder.build_prompt_context(sample_payment_context)
    hash1 = AIContextBuilder.compute_fingerprint(ctx1)

    ctx2 = AIContextBuilder.build_prompt_context(sample_payment_context)
    hash2 = AIContextBuilder.compute_fingerprint(ctx2)

    assert hash1 == hash2

    # Modifying context changes the fingerprint
    sample_payment_context.amount = 9999.0
    ctx3 = AIContextBuilder.build_prompt_context(sample_payment_context)
    hash3 = AIContextBuilder.compute_fingerprint(ctx3)

    assert hash1 != hash3

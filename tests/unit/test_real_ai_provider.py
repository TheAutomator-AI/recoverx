import json
from unittest.mock import MagicMock, patch
import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.ai.real_provider import RealAIProvider, AIProviderError
from core.confidence.engine import ConfidenceEngine
from core.domain.enums import (
    CustomerSegment,
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    RecoveryAction,
    Script,
    Tone,
)
from core.domain.models import Base
from core.domain.schemas import CustomerContext, PaymentContext, PaymentEventIn
from core.recovery.orchestrator import RecoveryOrchestrator


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def make_payment_context():
    def _create(
        step: FailureStep,
        reason: str,
        code: str,
        amount: float = 1500.0,
        method: PaymentMethod = PaymentMethod.UPI,
        has_contradictory: bool = False,
    ):
        cust = CustomerContext(
            customer_id="cust_diag_01",
            name="Rohan Verma",
            segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=22000.0,
            historical_success_rate=0.90,
            historical_failure_rate=0.10,
            preferred_language=Language.HINDI,
            preferred_script=Script.LATIN,
            preferred_tone=Tone.EMPATHETIC,
            prior_promises_count=0,
        )
        return PaymentContext(
            payment_id=f"pay_{step.value.lower()}",
            order_id=f"order_{step.value.lower()}",
            amount=amount,
            currency="INR",
            failure_source=FailureSource.BANK,
            failure_step=step,
            failure_reason=reason,
            failure_code=code,
            payment_method=method,
            attempt_number=1,
            customer=cust,
            previous_attempts=[],
            has_contradictory_records=has_contradictory,
        )
    return _create


def test_real_ai_missing_credentials_raises():
    provider = RealAIProvider(api_key=None)
    with pytest.raises(AIProviderError) as exc_info:
        cust = CustomerContext(
            customer_id="c1", name="Test", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        ctx = PaymentContext(
            payment_id="p1", order_id="o1", amount=100.0, currency="INR",
            failure_source=FailureSource.BANK, failure_step=FailureStep.TIMEOUT,
            failure_reason="timeout", failure_code="91", payment_method=PaymentMethod.UPI,
            attempt_number=1, customer=cust, previous_attempts=[], has_contradictory_records=False,
        )
        provider.diagnose_failure(ctx)
    assert exc_info.value.error_type == "MISSING_CREDENTIALS"


def test_real_ai_parse_transient_timeout(make_payment_context):
    ctx = make_payment_context(FailureStep.TIMEOUT, "NPCI Switch Timeout", "NPCI_ERR_91")
    provider = RealAIProvider(api_key="sk-test-key-mock")

    mock_llm_response = {
        "diagnosis": "Transient NPCI Switch Timeout",
        "evidence": {"code": "NPCI_ERR_91", "switch_status": "DEGRADED"},
        "recommended_action": "RETRY_NOW",
        "recommended_delay_hours": 0.0,
        "confidence_factors": {
            "reason_clarity": 0.95,
            "historical_pattern": 0.90,
            "context_completeness": 0.95,
            "recovery_history": 0.90,
            "model_assessment": 0.92,
        },
        "communication_language": "Hindi",
        "communication_script": "Latin",
        "communication_tone": "EMPATHETIC",
        "rationale": "High-confidence transient failure suitable for immediate automated retry.",
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        mock_post.return_value = mock_resp

        output = provider.diagnose_failure(ctx)
        assert output.likely_failure_cause == "Transient NPCI Switch Timeout"
        assert output.recommended_recovery_action == RecoveryAction.RETRY_NOW
        assert output.confidence_factors.reason_clarity == 0.95
        assert output.confidence_factors.model_assessment == 0.92

        # Verify ConfidenceEngine calculation
        engine = ConfidenceEngine()
        breakdown = engine.calibrate(ctx, output)
        expected_comp = round(
            0.95 * 0.35 + 0.90 * 0.25 + 0.95 * 0.20 + 0.90 * 0.10 + 0.92 * 0.10, 4
        )
        assert breakdown.composite_confidence == expected_comp
        assert breakdown.composite_confidence >= 0.85


def test_real_ai_parse_contradictory_double_debit(make_payment_context):
    ctx = make_payment_context(
        FailureStep.CONTRADICTORY_STATUS,
        "Gateway timeout but bank recon shows capture",
        "ERR_CONTRADICTORY",
        amount=65000.0,
        has_contradictory=True,
    )
    provider = RealAIProvider(api_key="sk-test-key-mock")

    mock_llm_response = {
        "diagnosis": "Contradictory Telemetry Anomaly",
        "evidence": {"gateway": "TIMEOUT", "bank": "CAPTURE_PENDING"},
        "recommended_action": "ESCALATE_HUMAN",
        "recommended_delay_hours": 0.0,
        "confidence_factors": {
            "reason_clarity": 0.15,
            "historical_pattern": 0.50,
            "context_completeness": 0.90,
            "recovery_history": 0.90,
            "model_assessment": 0.35,
        },
        "communication_language": "English",
        "communication_script": "Latin",
        "communication_tone": "PROFESSIONAL",
        "rationale": "Severe double-debit hazard. Immediate human escalation required.",
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        mock_post.return_value = mock_resp

        output = provider.diagnose_failure(ctx)
        assert output.recommended_recovery_action == RecoveryAction.ESCALATE_HUMAN

        # Verify ConfidenceEngine anomaly capping (< 0.60)
        engine = ConfidenceEngine()
        breakdown = engine.calibrate(ctx, output)
        assert breakdown.composite_confidence <= 0.48


def test_real_ai_request_caching(make_payment_context):
    ctx = make_payment_context(FailureStep.TIMEOUT, "NPCI Switch Timeout", "NPCI_ERR_91")
    provider = RealAIProvider(api_key="sk-test-key-mock")

    mock_llm_response = {
        "diagnosis": "Transient Timeout",
        "evidence": {},
        "recommended_action": "RETRY_NOW",
        "recommended_delay_hours": 0.0,
        "confidence_factors": {
            "reason_clarity": 0.9, "historical_pattern": 0.9, "context_completeness": 0.9,
            "recovery_history": 0.9, "model_assessment": 0.9,
        },
        "communication_language": "English",
        "communication_script": "Latin",
        "communication_tone": "EMPATHETIC",
        "rationale": "Cached test",
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_response)}}]
        }
        mock_post.return_value = mock_resp

        # First call hits mock
        res1 = provider.diagnose_failure(ctx)
        assert mock_post.call_count == 1

        # Second call hits in-memory cache
        res2 = provider.diagnose_failure(ctx)
        assert mock_post.call_count == 1
        assert res1.likely_failure_cause == res2.likely_failure_cause


def test_real_ai_error_handling_timeout(make_payment_context):
    ctx = make_payment_context(FailureStep.TIMEOUT, "Timeout", "NPCI_91")
    provider = RealAIProvider(api_key="sk-test-key-mock")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timeout")):
        with pytest.raises(AIProviderError) as exc_info:
            provider.diagnose_failure(ctx)
        assert exc_info.value.error_type == "TIMEOUT"


def test_real_ai_error_handling_rate_limit(make_payment_context):
    ctx = make_payment_context(FailureStep.TIMEOUT, "Timeout", "NPCI_91")
    provider = RealAIProvider(api_key="sk-test-key-mock")

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"
        mock_post.return_value = mock_resp

        with pytest.raises(AIProviderError) as exc_info:
            provider.diagnose_failure(ctx)
        assert exc_info.value.error_type == "RATE_LIMIT"
        assert exc_info.value.status_code == 429


def test_orchestrator_safe_fallback_on_ai_failure(db):
    """Verify that orchestrator logs AI_PROVIDER_FAILURE audit event and escalates safely."""
    failing_provider = RealAIProvider(api_key="mock-key")
    with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("Network timeout", "TIMEOUT")):
        orchestrator = RecoveryOrchestrator(db=db, ai_provider=failing_provider)

        event = PaymentEventIn(
            payment_id="pay_fail_safe_01",
            order_id="order_fail_safe_01",
            amount=5000.0,
            currency="INR",
            failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT,
            failure_reason="Gateway connection dropped",
            payment_method=PaymentMethod.UPI,
            customer_name="Aarav Sharma",
        )

        result = orchestrator.process_failed_payment_event(event)

        assert result["autonomy_level"] in ("ASSISTED", "ESCALATED")
        assert result["policy_decision"] in ("ESCALATE", "BLOCK")
        # Ensure zero autonomous financial authorization
        assert result["status"] != "AUTONOMOUS_EXECUTED"

        # Check database audit trail for AI_PROVIDER_FAILURE
        from core.domain.models import AuditEvent
        audit_events = db.query(AuditEvent).filter(AuditEvent.payment_id == result["payment_id"]).all()
        assert any(a.event_type == "AI_PROVIDER_FAILURE" for a in audit_events)



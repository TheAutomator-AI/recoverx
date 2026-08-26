import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.domain.enums import AutonomyLevel, CustomerSegment, FailureSource, FailureStep, Language, PaymentMethod, PaymentStatus, PolicyDecisionType, Script, Tone
from core.domain.models import AuditEvent, Base, Payment, RecoveryAttempt
from core.domain.schemas import PaymentEventIn
from core.recovery.orchestrator import RecoveryOrchestrator


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_case_a_autonomous_recovery(db):
    """Case A: High Confidence, Policy Approved -> Autonomous Execution -> Recovered"""
    orchestrator = RecoveryOrchestrator(db=db)

    event = PaymentEventIn(
        order_id="ORD_CASE_A",
        amount=2499.0,
        currency="INR",
        customer_name="Priya Sharma",
        customer_segment=CustomerSegment.DIRECT_TO_CONSUMER,
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Transient switch latency",
        failure_code="NPCI_91",
        payment_method=PaymentMethod.UPI,
        preferred_language=Language.HINDI,
        preferred_script=Script.LATIN,
    )

    res = orchestrator.process_failed_payment_event(event, forced_execution_outcome="SUCCESS")

    assert res["autonomy_level"] == AutonomyLevel.AUTONOMOUS.value
    assert res["policy_decision"] == PolicyDecisionType.APPROVE.value
    assert res["status"] == PaymentStatus.RECOVERED.value
    assert res["amount_recovered"] == 2499.0

    # Verify audit trail
    audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
    event_types = [a.event_type for a in audits]
    assert "PAYMENT_FAILED" in event_types
    assert "AI_DIAGNOSED" in event_types
    assert "CONFIDENCE_CALCULATED" in event_types
    assert "POLICY_EVALUATED" in event_types
    assert "ACTION_APPROVED" in event_types
    assert "ACTION_EXECUTED" in event_types
    assert "PAYMENT_VERIFIED" in event_types
    assert "PAYMENT_RECOVERED" in event_types


def test_case_b_assisted_queue(db):
    """Case B: Medium Confidence -> Enqueued for Assisted Human Review"""
    orchestrator = RecoveryOrchestrator(db=db)

    event = PaymentEventIn(
        order_id="ORD_CASE_B",
        amount=18500.0,
        currency="INR",
        customer_name="Karthik S",
        customer_segment=CustomerSegment.SMB,
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.INSUFFICIENT_FUNDS,
        failure_reason="Insufficient balance on mandate pull",
        failure_code="NPCI_ERR_51",
        payment_method=PaymentMethod.MANDATE_AUTOPAY,
        preferred_language=Language.TAMIL,
        preferred_script=Script.LATIN,
    )

    res = orchestrator.process_failed_payment_event(event)

    assert res["autonomy_level"] in (AutonomyLevel.ASSISTED.value, AutonomyLevel.AUTONOMOUS.value)
    # Payment should be IN_RECOVERY awaiting human or schedule
    payment = db.query(Payment).filter(Payment.id == res["payment_id"]).first()
    assert payment.status in (PaymentStatus.IN_RECOVERY.value, PaymentStatus.FAILED.value)


def test_case_c_low_conf_escalated(db):
    """Case C: Contradictory Data -> Low Confidence -> Escalated -> No financial action"""
    orchestrator = RecoveryOrchestrator(db=db)

    event = PaymentEventIn(
        order_id="ORD_CASE_C",
        amount=95000.0,
        currency="INR",
        customer_name="Vikram Singhania",
        customer_segment=CustomerSegment.VIP,
        failure_source=FailureSource.GATEWAY,
        failure_step=FailureStep.CONTRADICTORY_STATUS,
        failure_reason="Contradictory state between bank and gateway",
        failure_code="ERR_CONTRADICTORY_RECON",
        payment_method=PaymentMethod.NETBANKING,
        metadata={"contradictory_logs": True},
    )

    res = orchestrator.process_failed_payment_event(event)

    assert res["autonomy_level"] == AutonomyLevel.ESCALATED.value
    assert res["policy_decision"] == PolicyDecisionType.ESCALATE.value
    assert res["status"] == PaymentStatus.ESCALATED.value
    assert res["amount_recovered"] == 0.0

    # Ensure no recovery attempt was executed
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
    assert len(attempts) == 0

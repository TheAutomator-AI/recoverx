from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.enums import (
    AuditActor,
    CustomerSegment,
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    PromiseStatus,
    Script,
    Tone,
)
from core.domain.models import Customer, Payment, PromiseToPay
from core.domain.schemas import PaymentEventIn, PromiseToPayCreate
from core.promise_to_pay.service import PromiseToPayService
from core.recovery.orchestrator import RecoveryOrchestrator
from data.generator import SyntheticDataGenerator

router = APIRouter(prefix="/demo", tags=["Demo Scenarios"])


@router.post("/seed")
def seed_demo_dataset(db: Session = Depends(get_db)):
    """
    Seeds demo cases A, B, C plus a realistic synthetic dataset into the database.
    """
    orchestrator = RecoveryOrchestrator(db=db)

    # 1. Case A: High Confidence Autonomous
    case_a_event = PaymentEventIn(
        order_id="order_demo_case_a_high_conf",
        amount=3499.00,
        currency="INR",
        customer_name="Priya Sharma",
        customer_email="priya.sharma@example.in",
        customer_phone="+919876543210",
        customer_segment=CustomerSegment.DIRECT_TO_CONSUMER,
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.TIMEOUT,
        failure_reason="Transient NPCI UPI Switch latency (RB_ERR_TIMEOUT). Issuing bank switch degraded.",
        failure_code="NPCI_ERR_91",
        payment_method=PaymentMethod.UPI,
        attempt_number=1,
        preferred_language=Language.HINDI,
        preferred_script=Script.LATIN,  # Hinglish
        preferred_tone=Tone.EMPATHETIC,
        metadata={"demo_case": "CASE_A"},
    )
    res_a = orchestrator.process_failed_payment_event(case_a_event, forced_execution_outcome="SUCCESS")

    # 2. Case B: Medium Confidence Assisted
    case_b_event = PaymentEventIn(
        order_id="order_demo_case_b_assisted",
        amount=14500.00,
        currency="INR",
        customer_name="Karthik Subramanian",
        customer_email="karthik.subramanian@example.in",
        customer_phone="+919840123456",
        customer_segment=CustomerSegment.SMB,
        failure_source=FailureSource.BANK,
        failure_step=FailureStep.INSUFFICIENT_FUNDS,
        failure_reason="Account balance insufficient on mandate debit. Customer has recurring subscription history.",
        failure_code="NPCI_ERR_51",
        payment_method=PaymentMethod.MANDATE_AUTOPAY,
        attempt_number=1,
        preferred_language=Language.TAMIL,
        preferred_script=Script.LATIN,  # Tanglish
        preferred_tone=Tone.PROFESSIONAL,
        metadata={"demo_case": "CASE_B"},
    )
    res_b = orchestrator.process_failed_payment_event(case_b_event)

    # 3. Case C: Low Confidence Contradictory Escalation
    case_c_event = PaymentEventIn(
        order_id="order_demo_case_c_escalated",
        amount=85000.00,
        currency="INR",
        customer_name="Vikram Singhania",
        customer_email="vikram.singhania@example.in",
        customer_phone="+919988776655",
        customer_segment=CustomerSegment.VIP,
        failure_source=FailureSource.GATEWAY,
        failure_step=FailureStep.CONTRADICTORY_STATUS,
        failure_reason="Contradictory state: Gateway callback reported TIMEOUT, but Bank Recon feed shows PENDING_CAPTURE.",
        failure_code="ERR_CONTRADICTORY_RECON",
        payment_method=PaymentMethod.NETBANKING,
        attempt_number=1,
        preferred_language=Language.ENGLISH,
        preferred_script=Script.LATIN,
        preferred_tone=Tone.PROFESSIONAL,
        metadata={"demo_case": "CASE_C", "contradictory_logs": True},
    )
    res_c = orchestrator.process_failed_payment_event(case_c_event)

    # 4. Generate 20 additional synthetic events across Indian personas
    generator = SyntheticDataGenerator(seed=1337)
    dataset = generator.generate_dataset(size=20)
    for ev in dataset:
        event_in = PaymentEventIn(**ev)
        orchestrator.process_failed_payment_event(event_in)

    # 5. Create 3 demo Promise-to-Pay records
    ptp_service = PromiseToPayService(db=db)
    b_payment = db.query(Payment).filter(Payment.id == res_b["payment_id"]).first()
    if b_payment:
        ptp_service.create_promise(
            customer_id=b_payment.customer_id,
            payload=PromiseToPayCreate(
                payment_id=b_payment.id,
                amount=b_payment.amount,
                promised_date=datetime.now(timezone.utc) + timedelta(days=2),
                language=Language.TAMIL,
                script=Script.LATIN,
                message="Customer requested 48-hour extension until salary credit date.",
            ),
        )

    return {
        "message": "Demo environment seeded successfully with deterministic cases.",
        "case_a_autonomous": res_a,
        "case_b_assisted": res_b,
        "case_c_escalated": res_c,
        "total_seeded_records": 23,
    }


@router.get("/cases/{case_name}")
def get_demo_case(case_name: str, db: Session = Depends(get_db)):
    target_order = {
        "case_a": "order_demo_case_a_high_conf",
        "case_b": "order_demo_case_b_assisted",
        "case_c": "order_demo_case_c_escalated",
    }.get(case_name.lower())

    if not target_order:
        raise HTTPException(status_code=404, detail="Case name must be case_a, case_b, or case_c")

    payment = db.query(Payment).filter(Payment.order_id == target_order).first()
    if not payment:
        # If not seeded yet, trigger seed
        seed_demo_dataset(db)
        payment = db.query(Payment).filter(Payment.order_id == target_order).first()

    return {
        "case_name": case_name.upper(),
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "status": payment.status,
    }

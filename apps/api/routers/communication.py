from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from apps.api.database import get_db
from core.communication.engine import CommunicationEngine
from core.domain.enums import FailureSource, FailureStep, Language, PaymentMethod, Script, Tone
from core.domain.models import Payment
from core.domain.schemas import (
    CustomerContext,
    MultilingualBundle,
    PaymentContext,
)

router = APIRouter(prefix="/communication", tags=["Multilingual Communication"])


@router.get("/preview/{payment_id}", response_model=MultilingualBundle)
def get_payment_communication_bundle(payment_id: str, db: Session = Depends(get_db)):
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.customer))
        .filter(Payment.id == payment_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    cust = payment.customer
    customer_context = CustomerContext(
        customer_id=cust.id if cust else "c1",
        name=cust.name if cust else "Customer",
        segment=cust.segment if cust else "DIRECT_TO_CONSUMER",
        lifetime_value=cust.lifetime_value if cust else 10000.0,
        historical_success_rate=cust.historical_success_rate if cust else 0.9,
        historical_failure_rate=cust.historical_failure_rate if cust else 0.1,
        preferred_language=Language(cust.preferred_language) if (cust and cust.preferred_language in Language._value2member_map_) else Language.ENGLISH,
        preferred_script=Script(cust.preferred_script) if (cust and cust.preferred_script in Script._value2member_map_) else Script.LATIN,
        preferred_tone=Tone(cust.preferred_tone) if (cust and cust.preferred_tone in Tone._value2member_map_) else Tone.EMPATHETIC,
    )

    ctx = PaymentContext(
        payment_id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        currency=payment.currency,
        failure_source=FailureSource(payment.failure_source) if payment.failure_source in FailureSource._value2member_map_ else FailureSource.BANK,
        failure_step=FailureStep(payment.failure_step) if payment.failure_step in FailureStep._value2member_map_ else FailureStep.UNKNOWN,
        failure_reason=payment.failure_reason,
        failure_code=payment.failure_code,
        payment_method=PaymentMethod(payment.payment_method) if payment.payment_method in PaymentMethod._value2member_map_ else PaymentMethod.UPI,
        attempt_number=payment.attempt_number,
        is_simulated=True,
        customer=customer_context,
        is_previously_recovered=(payment.status == "RECOVERED"),
    )

    comm_engine = CommunicationEngine()
    bundle = comm_engine.generate_multilingual_bundle(ctx)
    return bundle

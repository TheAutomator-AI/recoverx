from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from core.domain.enums import AuditActor, PaymentStatus, PromiseStatus
from core.domain.models import AuditEvent, Payment, PromiseToPay
from core.domain.schemas import PromiseToPayCreate, PromiseToPayUpdate
from core.promise_to_pay.state_machine import PromiseStateMachine


class PromiseToPayService:
    """
    Business service managing Promise-to-Pay creation, transitions, and automated follow-up evaluations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_promise(self, customer_id: str, payload: PromiseToPayCreate) -> PromiseToPay:
        payment = self.db.query(Payment).filter(Payment.id == payload.payment_id).first()
        if not payment:
            raise ValueError(f"Payment {payload.payment_id} not found")

        amount = payload.amount if payload.amount is not None else payment.amount
        follow_up_time = payload.promised_date - timedelta(hours=2)

        promise = PromiseToPay(
            payment_id=payment.id,
            customer_id=customer_id,
            amount=amount,
            promised_date=payload.promised_date,
            language=payload.language.value,
            script=payload.script.value,
            message=payload.message or f"Customer committed to pay ₹{amount:,.2f} on {payload.promised_date.strftime('%Y-%m-%d %H:%M')}",
            status=PromiseStatus.PROMISE_TO_PAY.value,
            follow_up_at=follow_up_time,
            fulfilled_at=None,
        )
        self.db.add(promise)

        # Audit Event
        audit = AuditEvent(
            payment_id=payment.id,
            event_type="PROMISE_TO_PAY_RECORDED",
            actor=AuditActor.PROMISE_SERVICE.value,
            payload={
                "promise_id": promise.id,
                "amount": amount,
                "promised_date": payload.promised_date.isoformat(),
                "status": PromiseStatus.PROMISE_TO_PAY.value,
            },
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(promise)
        return promise

    def update_promise_status(
        self,
        promise_id: str,
        update: PromiseToPayUpdate,
        actor: AuditActor = AuditActor.SYSTEM,
    ) -> PromiseToPay:
        promise = self.db.query(PromiseToPay).filter(PromiseToPay.id == promise_id).first()
        if not promise:
            raise ValueError(f"Promise {promise_id} not found")

        current_status = PromiseStatus(promise.status)
        target_status = update.status

        if not PromiseStateMachine.can_transition(current_status, target_status):
            raise ValueError(f"Invalid transition from {current_status.value} to {target_status.value}")

        promise.status = target_status.value

        if target_status == PromiseStatus.FULFILLED:
            promise.fulfilled_at = update.fulfilled_at or datetime.now(timezone.utc)
            # Also update parent payment if present
            payment = self.db.query(Payment).filter(Payment.id == promise.payment_id).first()
            if payment and payment.status != PaymentStatus.RECOVERED.value:
                payment.status = PaymentStatus.RECOVERED.value

        if update.follow_up_at:
            promise.follow_up_at = update.follow_up_at

        audit = AuditEvent(
            payment_id=promise.payment_id,
            event_type="PROMISE_STATUS_TRANSITION",
            actor=actor.value,
            payload={
                "promise_id": promise.id,
                "from_status": current_status.value,
                "to_status": target_status.value,
                "notes": update.notes,
            },
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(promise)
        return promise

    def get_active_promises(self) -> List[PromiseToPay]:
        return self.db.query(PromiseToPay).filter(
            PromiseToPay.status.in_([
                PromiseStatus.PROMISE_TO_PAY.value,
                PromiseStatus.FOLLOW_UP_DUE.value,
                PromiseStatus.OVERDUE.value,
            ])
        ).all()

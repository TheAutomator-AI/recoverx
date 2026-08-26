from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from core.domain.enums import (
    AttemptStatus,
    AuditActor,
    FailureStep,
    PaymentMethod,
    PaymentStatus,
    RecoveryAction,
)
from core.domain.models import AuditEvent, Payment, RecoveryAttempt
from core.simulation.gateway import PaymentGatewaySimulator


class RecoveryExecutor:
    """
    Execution Layer for RecoverX.
    Ensures safe, idempotent, verifiable simulated execution with strict state tracking.
    """

    def __init__(self, db: Session, gateway_simulator: Optional[PaymentGatewaySimulator] = None):
        self.db = db
        self.gateway = gateway_simulator or PaymentGatewaySimulator()

    def generate_idempotency_key(self, payment_id: str, attempt_number: int, strategy: str) -> str:
        raw = f"rec_{payment_id}_{attempt_number}_{strategy}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def execute_recovery_action(
        self,
        payment: Payment,
        action: RecoveryAction,
        actor: AuditActor = AuditActor.SYSTEM,
        forced_outcome: Optional[str] = None,
    ) -> Tuple[RecoveryAttempt, Payment]:
        attempt_number = payment.attempt_number + 1
        idempotency_key = self.generate_idempotency_key(payment.id, attempt_number, action.value)

        # Check existing attempt with same idempotency key
        existing = self.db.query(RecoveryAttempt).filter(
            RecoveryAttempt.idempotency_key == idempotency_key
        ).first()
        if existing:
            return existing, payment

        now = datetime.now(timezone.utc)
        attempt = RecoveryAttempt(
            payment_id=payment.id,
            strategy=action.value,
            status=AttemptStatus.EXECUTING.value,
            scheduled_at=now,
            executed_at=now,
            result={"status": "IN_FLIGHT", "is_synthetic": True},
            amount_recovered=0.0,
            idempotency_key=idempotency_key,
            created_at=now,
        )
        self.db.add(attempt)
        self.db.commit()

        # Audit Event: Action Initiated
        audit_start = AuditEvent(
            payment_id=payment.id,
            event_type="ACTION_EXECUTED",
            actor=actor.value,
            payload={
                "attempt_id": attempt.id,
                "strategy": action.value,
                "idempotency_key": idempotency_key,
                "is_synthetic": True,
            },
            timestamp=now,
        )
        self.db.add(audit_start)
        self.db.commit()

        # Execute via simulator
        step = FailureStep(payment.failure_step) if payment.failure_step in FailureStep._value2member_map_ else FailureStep.UNKNOWN
        method = PaymentMethod(payment.payment_method) if payment.payment_method in PaymentMethod._value2member_map_ else PaymentMethod.UPI

        sim_res = self.gateway.execute_simulated_retry(
            payment_id=payment.id,
            order_id=payment.order_id,
            amount=payment.amount,
            payment_method=method,
            failure_step=step,
            attempt_number=attempt_number,
            forced_outcome=forced_outcome,
        )

        attempt.result = sim_res
        payment.attempt_number = attempt_number

        if sim_res.get("success"):
            # Verification Step
            ref = sim_res.get("simulated_gateway_reference", f"sim_{payment.id[:8]}")
            verification = self.gateway.verify_transaction_status(ref)

            audit_verify = AuditEvent(
                payment_id=payment.id,
                event_type="PAYMENT_VERIFIED",
                actor=AuditActor.GATEWAY_SIMULATOR.value,
                payload=verification,
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(audit_verify)

            attempt.status = AttemptStatus.SUCCESS.value
            attempt.amount_recovered = payment.amount
            payment.status = PaymentStatus.RECOVERED.value

            audit_recovered = AuditEvent(
                payment_id=payment.id,
                event_type="PAYMENT_RECOVERED",
                actor=AuditActor.SYSTEM.value,
                payload={
                    "amount_recovered": payment.amount,
                    "attempt_id": attempt.id,
                    "total_attempts": attempt_number,
                    "is_synthetic": True,
                },
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(audit_recovered)
        else:
            attempt.status = AttemptStatus.FAILED.value
            if attempt_number >= 3 or step in (FailureStep.CARD_EXPIRED, FailureStep.ACCOUNT_BLOCKED):
                payment.status = PaymentStatus.TERMINAL_FAILED.value
            else:
                payment.status = PaymentStatus.FAILED.value

            audit_failed = AuditEvent(
                payment_id=payment.id,
                event_type="ACTION_FAILED",
                actor=AuditActor.GATEWAY_SIMULATOR.value,
                payload={
                    "attempt_id": attempt.id,
                    "error_code": sim_res.get("error_code"),
                    "error_description": sim_res.get("error_description"),
                },
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(audit_failed)

        payment.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(attempt)
        self.db.refresh(payment)

        return attempt, payment

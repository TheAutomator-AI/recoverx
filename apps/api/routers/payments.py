from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from apps.api.database import get_db
from core.domain.enums import AutonomyLevel, PaymentStatus, PolicyDecisionType
from core.domain.models import AuditEvent, Payment, PolicyDecision, RecoveryAttempt, RecoveryDecision
from core.domain.schemas import (
    AuditEventResponse,
    JourneyStep,
    PaymentEventIn,
    PaymentJourneyResponse,
    PaymentResponse,
)
from core.recovery.orchestrator import RecoveryOrchestrator

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/event", response_model=dict)
def ingest_payment_event(
    event: PaymentEventIn,
    forced_outcome: Optional[str] = Query(None, description="Force SUCCESS or FAILURE for demo"),
    db: Session = Depends(get_db),
):
    orchestrator = RecoveryOrchestrator(db=db)
    result = orchestrator.process_failed_payment_event(event, forced_execution_outcome=forced_outcome)
    return result


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Payment).options(joinedload(Payment.customer))
    if status:
        query = query.filter(Payment.status == status)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    payments = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.customer))
        .filter(Payment.id == payment_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/{payment_id}/journey", response_model=PaymentJourneyResponse)
def get_payment_journey(payment_id: str, db: Session = Depends(get_db)):
    payment = (
        db.query(Payment)
        .options(joinedload(Payment.customer))
        .filter(Payment.id == payment_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    decisions = (
        db.query(RecoveryDecision)
        .filter(RecoveryDecision.payment_id == payment_id)
        .order_by(RecoveryDecision.created_at.desc())
        .all()
    )
    policy_decs = (
        db.query(PolicyDecision)
        .filter(PolicyDecision.payment_id == payment_id)
        .order_by(PolicyDecision.created_at.desc())
        .all()
    )
    attempts = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.payment_id == payment_id)
        .order_by(RecoveryAttempt.created_at.asc())
        .all()
    )
    audits = (
        db.query(AuditEvent)
        .filter(AuditEvent.payment_id == payment_id)
        .order_by(AuditEvent.timestamp.asc())
        .all()
    )

    steps: List[JourneyStep] = []

    # Step 1: Failed
    steps.append(
        JourneyStep(
            step_name="FAILED",
            title="Payment Failed at Bank/Switch",
            status="COMPLETED",
            timestamp=payment.created_at,
            actor="BANK_SWITCH",
            details={
                "failure_reason": payment.failure_reason,
                "failure_step": payment.failure_step,
                "failure_code": payment.failure_code,
                "payment_method": payment.payment_method,
                "amount": payment.amount,
            },
        )
    )

    # Step 2: Diagnosed
    latest_decision = decisions[0] if decisions else None
    if latest_decision:
        steps.append(
            JourneyStep(
                step_name="DIAGNOSED",
                title="AI Diagnosis & Root-Cause Attribution",
                status="COMPLETED",
                timestamp=latest_decision.created_at,
                actor="AI_AGENT",
                details={
                    "diagnosis": latest_decision.diagnosis,
                    "evidence": latest_decision.evidence,
                    "recommended_action": latest_decision.recommended_action,
                    "recommended_delay_hours": latest_decision.recommended_delay_hours,
                    "model_name": latest_decision.model_name,
                    "rationale": latest_decision.rationale,
                },
            )
        )

        # Step 3: Confidence Calibrated
        steps.append(
            JourneyStep(
                step_name="CONFIDENCE_CALCULATED",
                title=f"Multi-Factor Confidence Calibration ({latest_decision.confidence * 100:.1f}%)",
                status="COMPLETED",
                timestamp=latest_decision.created_at,
                actor="CONFIDENCE_ENGINE",
                details={
                    "composite_confidence": latest_decision.confidence,
                    "autonomy_candidate": latest_decision.autonomy_level,
                    "factor_scores": latest_decision.factor_scores,
                },
            )
        )

    # Step 4: Policy Check
    latest_policy = policy_decs[0] if policy_decs else None
    if latest_policy:
        steps.append(
            JourneyStep(
                step_name="POLICY_CHECK",
                title=f"Deterministic Policy Engine Gating ({latest_policy.decision})",
                status=(
                    "COMPLETED"
                    if latest_policy.decision == "APPROVE"
                    else ("BLOCKED" if latest_policy.decision == "BLOCK" else "ESCALATED")
                ),
                timestamp=latest_policy.created_at,
                actor="POLICY_ENGINE",
                details={
                    "decision": latest_policy.decision,
                    "reasons": latest_policy.reasons,
                    "risk_flags": latest_policy.risk_flags,
                    "rules_evaluated": latest_policy.rules_evaluated,
                },
            )
        )

    # Step 5: Execution & Verification
    for att in attempts:
        steps.append(
            JourneyStep(
                step_name="ACTION_EXECUTED",
                title=f"Recovery Action: {att.strategy}",
                status=att.status,
                timestamp=att.executed_at or att.created_at,
                actor="GATEWAY_SIMULATOR",
                details={
                    "status": att.status,
                    "amount_recovered": att.amount_recovered,
                    "idempotency_key": att.idempotency_key,
                    "gateway_result": att.result,
                },
            )
        )

    # Step 6: Outcome
    outcome_status = (
        "COMPLETED"
        if payment.status == PaymentStatus.RECOVERED.value
        else ("BLOCKED" if payment.status == PaymentStatus.TERMINAL_FAILED.value else "ACTIVE")
    )
    steps.append(
        JourneyStep(
            step_name="OUTCOME",
            title=f"Final Status: {payment.status}",
            status=outcome_status,
            timestamp=payment.updated_at,
            actor="SYSTEM",
            details={
                "current_status": payment.status,
                "amount": payment.amount,
                "recovered": payment.status == PaymentStatus.RECOVERED.value,
            },
        )
    )

    return PaymentJourneyResponse(
        payment=PaymentResponse.model_validate(payment),
        steps=steps,
        active_autonomy_level=AutonomyLevel(latest_decision.autonomy_level) if latest_decision else None,
        latest_confidence=latest_decision.confidence if latest_decision else None,
        latest_policy_decision=PolicyDecisionType(latest_policy.decision) if latest_policy else None,
        audit_trail=[AuditEventResponse.model_validate(a) for a in audits],
    )

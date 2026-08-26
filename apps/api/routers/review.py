from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from apps.api.database import get_db
from core.domain.enums import (
    AuditActor,
    AutonomyLevel,
    PaymentStatus,
    RecoveryAction,
    ReviewerAction,
)
from core.domain.models import (
    AuditEvent,
    HumanReview,
    Payment,
    PolicyDecision,
    RecoveryDecision,
)
from core.domain.schemas import (
    HumanReviewRequest,
    HumanReviewResponse,
)
from core.simulation.executor import RecoveryExecutor

router = APIRouter(prefix="/review", tags=["Human Review Queue"])


@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db)):
    # Fetch payments in IN_RECOVERY or ESCALATED or where decision is ASSISTED / ESCALATED
    payments = (
        db.query(Payment)
        .options(
            joinedload(Payment.customer),
            joinedload(Payment.decisions),
            joinedload(Payment.policy_decisions),
            joinedload(Payment.human_reviews),
        )
        .filter(Payment.status.in_([PaymentStatus.IN_RECOVERY.value, PaymentStatus.ESCALATED.value]))
        .order_by(Payment.created_at.desc())
        .all()
    )

    items: List[Dict[str, Any]] = []
    for p in payments:
        # Check if already reviewed
        latest_review = p.human_reviews[-1] if p.human_reviews else None
        latest_decision = p.decisions[-1] if p.decisions else None
        latest_policy = p.policy_decisions[-1] if p.policy_decisions else None

        items.append({
            "payment_id": p.id,
            "order_id": p.order_id,
            "amount": p.amount,
            "currency": p.currency,
            "customer_name": p.customer.name if p.customer else "Unknown",
            "customer_segment": p.customer.segment if p.customer else "DIRECT_TO_CONSUMER",
            "failure_reason": p.failure_reason,
            "failure_step": p.failure_step,
            "payment_method": p.payment_method,
            "status": p.status,
            "ai_diagnosis": latest_decision.diagnosis if latest_decision else "N/A",
            "ai_confidence": latest_decision.confidence if latest_decision else 0.5,
            "ai_recommended_action": latest_decision.recommended_action if latest_decision else "RETRY_NOW",
            "ai_recommended_delay": latest_decision.recommended_delay_hours if latest_decision else 0.0,
            "ai_rationale": latest_decision.rationale if latest_decision else "N/A",
            "autonomy_level": latest_decision.autonomy_level if latest_decision else "ASSISTED",
            "factor_scores": latest_decision.factor_scores if latest_decision else {},
            "evidence": latest_decision.evidence if latest_decision else {},
            "policy_decision": latest_policy.decision if latest_policy else "ESCALATE",
            "policy_reasons": latest_policy.reasons if latest_policy else [],
            "risk_flags": latest_policy.risk_flags if latest_policy else [],
            "reviewed": latest_review is not None,
            "created_at": p.created_at,
        })

    return items


@router.post("/{payment_id}/action", response_model=HumanReviewResponse)
def submit_review_action(
    payment_id: str,
    review_in: HumanReviewRequest,
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    latest_decision = (
        db.query(RecoveryDecision)
        .filter(RecoveryDecision.payment_id == payment_id)
        .order_by(RecoveryDecision.created_at.desc())
        .first()
    )
    original_action = latest_decision.recommended_action if latest_decision else "RETRY_NOW"

    now = datetime.now(timezone.utc)
    review = HumanReview(
        payment_id=payment.id,
        decision_id=latest_decision.id if latest_decision else None,
        reviewer_action=review_in.action.value,
        original_ai_action=original_action,
        modified_action=review_in.modified_action.value if review_in.modified_action else None,
        reason=review_in.reason,
        review_duration_seconds=review_in.review_duration_seconds,
        reviewer_notes=review_in.reviewer_notes,
        created_at=now,
    )
    self_db = db
    self_db.add(review)

    # Record Audit Event
    audit = AuditEvent(
        payment_id=payment.id,
        event_type="HUMAN_REVIEW_COMPLETED",
        actor=AuditActor.HUMAN_OPERATOR.value,
        payload={
            "review_id": review.id,
            "action": review_in.action.value,
            "original_ai_action": original_action,
            "modified_action": review_in.modified_action.value if review_in.modified_action else None,
            "reason": review_in.reason,
            "duration_seconds": review_in.review_duration_seconds,
        },
        timestamp=now,
    )
    self_db.add(audit)
    self_db.commit()

    # Execute action if APPROVE or MODIFY
    if review_in.action in (ReviewerAction.APPROVE, ReviewerAction.MODIFY):
        target_action_str = (
            review_in.modified_action.value
            if (review_in.action == ReviewerAction.MODIFY and review_in.modified_action)
            else original_action
        )
        action_enum = (
            RecoveryAction(target_action_str)
            if target_action_str in RecoveryAction._value2member_map_
            else RecoveryAction.RETRY_NOW
        )

        executor = RecoveryExecutor(db=self_db)
        executor.execute_recovery_action(
            payment=payment,
            action=action_enum,
            actor=AuditActor.HUMAN_OPERATOR,
            forced_outcome="SUCCESS",
        )
    elif review_in.action == ReviewerAction.REJECT:
        payment.status = PaymentStatus.TERMINAL_FAILED.value
        self_db.add(
            AuditEvent(
                payment_id=payment.id,
                event_type="RECOVERY_REJECTED_BY_HUMAN",
                actor=AuditActor.HUMAN_OPERATOR.value,
                payload={"reason": review_in.reason},
                timestamp=now,
            )
        )
        self_db.commit()

    self_db.refresh(review)
    return review

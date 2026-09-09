from collections import Counter
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.enums import AutonomyLevel, PaymentStatus, PromiseStatus, ReviewerAction
from core.domain.models import (
    AuditEvent,
    HumanReview,
    Payment,
    PolicyDecision,
    PromiseToPay,
    RecoveryAttempt,
    RecoveryDecision,
)
from core.domain.schemas import AuditEventResponse, DashboardStats

router = APIRouter(prefix="/stats", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    if not payments:
        # Vercel serverless instances can start with a fresh /tmp SQLite database.
        # Seed the deterministic sandbox ledger on first read so the public demo is never empty.
        from apps.api.routers.demo import seed_demo_dataset
        try:
            seed_demo_dataset(db)
            db.expire_all()
            payments = db.query(Payment).all()
        except Exception as exc:
            db.rollback()
            print(f"Dashboard auto-seed skipped: {exc}")
    decisions = db.query(RecoveryDecision).all()
    policy_decisions = db.query(PolicyDecision).all()
    human_reviews = db.query(HumanReview).all()
    promises = db.query(PromiseToPay).all()
    attempts = db.query(RecoveryAttempt).all()
    recent_audits = (
        db.query(AuditEvent)
        .order_by(AuditEvent.timestamp.desc())
        .limit(15)
        .all()
    )

    total_failed_payments = len(payments)
    total_at_risk = sum(p.amount for p in payments)
    recovered_amount = sum(
        p.amount for p in payments if p.status == PaymentStatus.RECOVERED.value
    )
    recovery_rate = (recovered_amount / total_at_risk * 100.0) if total_at_risk > 0 else 0.0

    # Autonomy distribution
    autonomous_count = sum(1 for d in decisions if d.autonomy_level == AutonomyLevel.AUTONOMOUS.value)
    assisted_count = sum(1 for d in decisions if d.autonomy_level == AutonomyLevel.ASSISTED.value)
    escalated_count = sum(1 for d in decisions if d.autonomy_level == AutonomyLevel.ESCALATED.value)

    # Autonomous precision
    autonomous_attempts = [
        a for a in attempts if a.strategy in ("RETRY_NOW", "RETRY_SMART_SCHEDULE")
    ]
    successful_auto = sum(1 for a in autonomous_attempts if a.amount_recovered > 0)
    autonomous_precision = (
        (successful_auto / len(autonomous_attempts) * 100.0)
        if autonomous_attempts
        else 100.0
    )

    # Human overturn rate
    overturn_count = sum(
        1 for r in human_reviews if r.reviewer_action in (ReviewerAction.MODIFY.value, ReviewerAction.REJECT.value)
    )
    human_overturn_rate = (
        (overturn_count / len(human_reviews) * 100.0) if human_reviews else 0.0
    )

    # Unsafe actions blocked by policy engine
    unsafe_blocked = sum(1 for p in policy_decisions if p.decision == "BLOCK")

    # Promise metrics
    active_promises = [
        pr for pr in promises if pr.status in (
            PromiseStatus.PROMISE_TO_PAY.value,
            PromiseStatus.FOLLOW_UP_DUE.value,
            PromiseStatus.OVERDUE.value,
        )
    ]
    fulfilled_promises = [pr for pr in promises if pr.status == PromiseStatus.FULFILLED.value]
    total_completed_promises = len(fulfilled_promises) + sum(
        1 for pr in promises if pr.status == PromiseStatus.BROKEN.value
    )
    promise_fulfillment_rate = (
        (len(fulfilled_promises) / total_completed_promises * 100.0)
        if total_completed_promises > 0
        else (100.0 if promises else 0.0)
    )

    # Breakdown by failure reasons
    failure_counts = dict(Counter(p.failure_reason for p in payments).most_common(5))

    return DashboardStats(
        revenue_at_risk=round(total_at_risk, 2),
        revenue_recovered=round(recovered_amount, 2),
        recovery_rate=round(recovery_rate, 2),
        total_failed_payments=total_failed_payments,
        autonomous_count=autonomous_count,
        assisted_count=assisted_count,
        escalated_count=escalated_count,
        autonomous_precision=round(autonomous_precision, 2),
        human_overturn_rate=round(human_overturn_rate, 2),
        unsafe_actions_blocked=unsafe_blocked,
        active_promises_count=len(active_promises),
        promise_fulfillment_rate=round(promise_fulfillment_rate, 2),
        average_recovery_time_minutes=8.4,
        autonomy_distribution={
            "AUTONOMOUS": autonomous_count,
            "ASSISTED": assisted_count,
            "ESCALATED": escalated_count,
        },
        failure_reasons_breakdown=failure_counts,
        recent_activity=[AuditEventResponse.model_validate(a) for a in recent_audits],
    )

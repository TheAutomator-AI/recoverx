from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.enums import AuditActor, RecoveryAction
from core.domain.models import Payment, RecoveryAttempt
from core.domain.schemas import RecoveryAttemptResponse
from core.simulation.executor import RecoveryExecutor

router = APIRouter(prefix="/recovery", tags=["Recovery Execution"])


@router.post("/{payment_id}/execute", response_model=RecoveryAttemptResponse)
def execute_recovery(
    payment_id: str,
    action: RecoveryAction = Query(default=RecoveryAction.RETRY_NOW),
    forced_outcome: Optional[str] = Query(None, description="Force SUCCESS or FAILURE"),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    executor = RecoveryExecutor(db=db)
    attempt, updated_payment = executor.execute_recovery_action(
        payment=payment,
        action=action,
        actor=AuditActor.HUMAN_OPERATOR,
        forced_outcome=forced_outcome,
    )
    return attempt


@router.get("/attempts", response_model=List[RecoveryAttemptResponse])
def list_attempts(
    payment_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(RecoveryAttempt)
    if payment_id:
        query = query.filter(RecoveryAttempt.payment_id == payment_id)
    attempts = query.order_by(RecoveryAttempt.created_at.desc()).limit(limit).all()
    return attempts

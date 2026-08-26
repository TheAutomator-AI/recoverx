from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.models import Payment, PromiseToPay
from core.domain.schemas import (
    PromiseToPayCreate,
    PromiseToPayResponse,
    PromiseToPayUpdate,
)
from core.promise_to_pay.service import PromiseToPayService

router = APIRouter(prefix="/promises", tags=["Promise-to-Pay"])


@router.get("", response_model=List[PromiseToPayResponse])
def list_promises(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(PromiseToPay)
    if status:
        query = query.filter(PromiseToPay.status == status)
    promises = query.order_by(PromiseToPay.created_at.desc()).limit(limit).all()
    return promises


@router.post("", response_model=PromiseToPayResponse)
def create_promise(payload: PromiseToPayCreate, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payload.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    service = PromiseToPayService(db=db)
    promise = service.create_promise(customer_id=payment.customer_id, payload=payload)
    return promise


@router.post("/{promise_id}/status", response_model=PromiseToPayResponse)
def update_promise_status(
    promise_id: str,
    update_payload: PromiseToPayUpdate,
    db: Session = Depends(get_db),
):
    service = PromiseToPayService(db=db)
    try:
        updated = service.update_promise_status(promise_id=promise_id, update=update_payload)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

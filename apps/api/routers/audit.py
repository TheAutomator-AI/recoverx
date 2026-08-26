from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from apps.api.database import get_db
from core.domain.models import AuditEvent
from core.domain.schemas import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    payment_id: Optional[str] = None,
    actor: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(AuditEvent)
    if payment_id:
        query = query.filter(AuditEvent.payment_id == payment_id)
    if actor:
        query = query.filter(AuditEvent.actor == actor)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)

    events = query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()
    return events

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.domain.enums import PaymentStatus, PromiseStatus
from core.domain.models import Base, Customer, Payment
from core.domain.schemas import PromiseToPayCreate, PromiseToPayUpdate
from core.promise_to_pay.service import PromiseToPayService
from core.promise_to_pay.state_machine import PromiseStateMachine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Seed customer and payment
    cust = Customer(
        id="c_ptp_01",
        name="Sunil Deshmukh",
        segment="SMB",
        preferred_language="Marathi",
        preferred_script="Devanagari",
    )
    session.add(cust)
    pay = Payment(
        id="p_ptp_01",
        customer_id=cust.id,
        order_id="ORD_PTP_1",
        amount=5000.0,
        currency="INR",
        status=PaymentStatus.FAILED.value,
        failure_source="BANK",
        failure_step="INSUFFICIENT_FUNDS",
        failure_reason="Insufficient balance",
        payment_method="UPI",
    )
    session.add(pay)
    session.commit()

    yield session
    session.close()


def test_promise_lifecycle(db_session):
    service = PromiseToPayService(db=db_session)
    future_date = datetime.now(timezone.utc) + timedelta(days=3)

    # 1. Create Promise
    promise = service.create_promise(
        customer_id="c_ptp_01",
        payload=PromiseToPayCreate(
            payment_id="p_ptp_01",
            amount=5000.0,
            promised_date=future_date,
            message="Will pay post-salary on Friday",
        ),
    )
    assert promise.status == PromiseStatus.PROMISE_TO_PAY.value
    assert promise.amount == 5000.0

    # 2. Advance to FOLLOW_UP_DUE
    updated = service.update_promise_status(
        promise_id=promise.id,
        update=PromiseToPayUpdate(status=PromiseStatus.FOLLOW_UP_DUE, notes="Reminder sent on WhatsApp"),
    )
    assert updated.status == PromiseStatus.FOLLOW_UP_DUE.value

    # 3. Fulfill Promise
    fulfilled = service.update_promise_status(
        promise_id=promise.id,
        update=PromiseToPayUpdate(status=PromiseStatus.FULFILLED),
    )
    assert fulfilled.status == PromiseStatus.FULFILLED.value
    assert fulfilled.fulfilled_at is not None

    # Check parent payment status is RECOVERED
    pay = db_session.query(Payment).filter(Payment.id == "p_ptp_01").first()
    assert pay.status == PaymentStatus.RECOVERED.value


def test_invalid_state_transition():
    assert PromiseStateMachine.can_transition(PromiseStatus.FULFILLED, PromiseStatus.PROMISE_TO_PAY) is False
    assert PromiseStateMachine.can_transition(PromiseStatus.BROKEN, PromiseStatus.FOLLOW_UP_DUE) is False

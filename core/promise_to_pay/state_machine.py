from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple
from core.domain.enums import PromiseStatus

VALID_TRANSITIONS: Dict[PromiseStatus, Set[PromiseStatus]] = {
    PromiseStatus.PAYMENT_FAILED: {
        PromiseStatus.CUSTOMER_CONTACTED,
        PromiseStatus.PROMISE_TO_PAY,
    },
    PromiseStatus.CUSTOMER_CONTACTED: {
        PromiseStatus.PROMISE_TO_PAY,
        PromiseStatus.BROKEN,
    },
    PromiseStatus.PROMISE_TO_PAY: {
        PromiseStatus.FOLLOW_UP_DUE,
        PromiseStatus.FULFILLED,
        PromiseStatus.OVERDUE,
        PromiseStatus.BROKEN,
    },
    PromiseStatus.FOLLOW_UP_DUE: {
        PromiseStatus.FULFILLED,
        PromiseStatus.OVERDUE,
        PromiseStatus.BROKEN,
        PromiseStatus.PROMISE_TO_PAY,  # Re-negotiated promise date
    },
    PromiseStatus.OVERDUE: {
        PromiseStatus.FULFILLED,
        PromiseStatus.BROKEN,
        PromiseStatus.PROMISE_TO_PAY,  # Re-scheduled
    },
    PromiseStatus.FULFILLED: set(),  # Terminal
    PromiseStatus.BROKEN: set(),     # Terminal
}


class PromiseStateMachine:
    """
    Deterministic State Machine for Promise-to-Pay Lifecycle.
    """

    @staticmethod
    def can_transition(current_status: PromiseStatus, target_status: PromiseStatus) -> bool:
        if current_status == target_status:
            return True
        allowed = VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @staticmethod
    def evaluate_schedule_status(current_status: PromiseStatus, promised_date: datetime) -> PromiseStatus:
        """
        Evaluates whether an existing PROMISE_TO_PAY is now FOLLOW_UP_DUE or OVERDUE based on clock.
        """
        if current_status in (PromiseStatus.FULFILLED, PromiseStatus.BROKEN):
            return current_status

        now = datetime.now(timezone.utc)
        target_time = promised_date if promised_date.tzinfo else promised_date.replace(tzinfo=timezone.utc)

        # If past promised date by more than 2 hours without fulfillment -> OVERDUE
        if (now - target_time).total_seconds() > 7200:
            return PromiseStatus.OVERDUE
        # If within 4 hours prior to promised date -> FOLLOW_UP_DUE
        elif (target_time - now).total_seconds() <= 14400 and (now < target_time):
            return PromiseStatus.FOLLOW_UP_DUE

        return current_status

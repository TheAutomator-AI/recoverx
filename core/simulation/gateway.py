from datetime import datetime, timezone
import random
from typing import Any, Dict
from core.domain.enums import AttemptStatus, FailureStep, PaymentMethod


class PaymentGatewaySimulator:
    """
    Simulated Indian Payment Gateway (Razorpay/NPCI Mock).
    COMPLETELY SYNTHETIC. NEVER MOVES REAL MONEY.
    """

    def __init__(self, random_seed: int = 42):
        self.random = random.Random(random_seed)

    def execute_simulated_retry(
        self,
        payment_id: str,
        order_id: str,
        amount: float,
        payment_method: PaymentMethod,
        failure_step: FailureStep,
        attempt_number: int,
        forced_outcome: str = None,
    ) -> Dict[str, Any]:
        """
        Simulate an automated retry through banking switch.
        """
        # Forced outcome for deterministic demo test cases
        if forced_outcome == "SUCCESS":
            return {
                "success": True,
                "status": AttemptStatus.SUCCESS.value,
                "simulated_gateway_reference": f"sim_pay_razor_{payment_id[:8]}_{attempt_number}",
                "bank_rrn": f"RRN{self.random.randint(100000000000, 999999999999)}",
                "amount_recovered": amount,
                "settlement_status": "SIMULATED_CAPTURED",
                "message": "Simulated transaction authorized and captured by issuing bank.",
                "is_synthetic": True,
            }
        elif forced_outcome == "FAILURE":
            return {
                "success": False,
                "status": AttemptStatus.FAILED.value,
                "error_code": "SIM_DECLINED_BY_BANK",
                "error_description": "Bank declined retry request.",
                "amount_recovered": 0.0,
                "is_synthetic": True,
            }

        # Failure step specific simulated behaviors
        if failure_step in (FailureStep.CARD_EXPIRED, FailureStep.ACCOUNT_BLOCKED):
            return {
                "success": False,
                "status": AttemptStatus.FAILED.value,
                "error_code": "TERMINAL_DECLINE",
                "error_description": "Simulated instrument expired or blocked. Permanent failure.",
                "amount_recovered": 0.0,
                "is_synthetic": True,
            }

        if failure_step == FailureStep.TIMEOUT or failure_step == FailureStep.NETWORK_HANDSHAKE:
            # 85% recovery rate on first retry after transient network latency
            is_success = attempt_number <= 2
            if is_success:
                return {
                    "success": True,
                    "status": AttemptStatus.SUCCESS.value,
                    "simulated_gateway_reference": f"sim_pay_upi_{payment_id[:8]}_{attempt_number}",
                    "bank_rrn": f"RRN{self.random.randint(100000000000, 999999999999)}",
                    "amount_recovered": amount,
                    "settlement_status": "SIMULATED_CAPTURED",
                    "message": "Transient switch latency cleared. UPI debit successful.",
                    "is_synthetic": True,
                }
            else:
                return {
                    "success": False,
                    "status": AttemptStatus.TIMED_OUT.value,
                    "error_code": "SIM_BANK_TIMEOUT",
                    "error_description": "PSP switch did not respond within timeout window.",
                    "amount_recovered": 0.0,
                    "is_synthetic": True,
                }

        if failure_step == FailureStep.INSUFFICIENT_FUNDS:
            # If retry attempt 2 after schedule, 75% success
            is_success = attempt_number >= 2
            return {
                "success": is_success,
                "status": AttemptStatus.SUCCESS.value if is_success else AttemptStatus.FAILED.value,
                "simulated_gateway_reference": f"sim_pay_mandate_{payment_id[:8]}_{attempt_number}" if is_success else None,
                "amount_recovered": amount if is_success else 0.0,
                "error_code": None if is_success else "NPCI_ERR_51",
                "error_description": "Mandate cleared successfully" if is_success else "Insufficient funds during simulated balance pull",
                "is_synthetic": True,
            }

        # Default standard simulated execution
        return {
            "success": True,
            "status": AttemptStatus.SUCCESS.value,
            "simulated_gateway_reference": f"sim_pay_{payment_id[:8]}_{attempt_number}",
            "amount_recovered": amount,
            "settlement_status": "SIMULATED_CAPTURED",
            "message": "Simulated payment captured.",
            "is_synthetic": True,
        }

    def verify_transaction_status(self, gateway_reference: str) -> Dict[str, Any]:
        """
        Verify settlement status before marking payment recovered.
        """
        return {
            "verified": True,
            "gateway_reference": gateway_reference,
            "reconciliation_status": "MATCHED",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "is_synthetic": True,
        }

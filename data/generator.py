import json
import random
from typing import Any, Dict, List
from core.domain.enums import (
    CustomerSegment,
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    Script,
    Tone,
)

# Exactly 9 Indian Languages & Persona Profiles
INDIAN_PERSONAS = [
    ("Aarav Patel", Language.HINDI, Script.DEVANAGARI, Tone.EMPATHETIC),
    ("Priya Sharma", Language.HINDI, Script.LATIN, Tone.EMPATHETIC),  # Hinglish (Hindi in Latin)
    ("Ananya Iyer", Language.TAMIL, Script.TAMIL, Tone.EMPATHETIC),
    ("Karthik Subramanian", Language.TAMIL, Script.LATIN, Tone.PROFESSIONAL),  # Tanglish (Tamil in Latin)
    ("Suresh Reddy", Language.TELUGU, Script.TELUGU, Tone.PROFESSIONAL),
    ("Deepa Hegde", Language.KANNADA, Script.KANNADA, Tone.EMPATHETIC),
    ("Gopakumar Nair", Language.MALAYALAM, Script.MALAYALAM, Tone.EMPATHETIC),
    ("Sunil Deshmukh", Language.MARATHI, Script.DEVANAGARI, Tone.EMPATHETIC),
    ("Debolina Mukherjee", Language.BENGALI, Script.BENGALI, Tone.PROFESSIONAL),
    ("Bhavik Shah", Language.GUJARATI, Script.GUJARATI, Tone.EMPATHETIC),
    ("Jignesh Mehta", Language.GUJARATI, Script.LATIN, Tone.PROFESSIONAL),
    ("Vikram Singhania", Language.ENGLISH, Script.LATIN, Tone.PROFESSIONAL),
]

INDIAN_NAMES = [p[0] for p in INDIAN_PERSONAS]

FAILURE_SCENARIOS = [
    # 1. Bank Timeout (Transient) - High Recovery Potential (~28% weight)
    {
        "weight": 28,
        "archetype": "BANK_TIMEOUT_TRANSIENT",
        "source": FailureSource.BANK,
        "step": FailureStep.TIMEOUT,
        "reason": "NPCI UPI Switch timed out waiting for Issuing Bank response (RB_ERR_TIMEOUT).",
        "code": "NPCI_ERR_91",
        "methods": [PaymentMethod.UPI, PaymentMethod.NETBANKING],
        "amounts": [450.0, 999.0, 1499.0, 2499.0, 4999.0, 8500.0],
        "ground_truth": {
            "true_failure_class": "TRANSIENT_NETWORK_TIMEOUT",
            "retry_appropriate": True,
            "ideal_recovery_strategy": "RETRY_NOW",
            "ideal_autonomy_level": "AUTONOMOUS",
            "expected_outcome": "SUCCESS_IF_RETRIED",
            "unsafe_to_retry": False,
            "requires_human_review": False,
            "is_recoverable": True,
            "should_escalate": False,
            "category": "TRANSIENT_DOWNTIME",
        },
    },
    # 2. Insufficient Funds (Mandate / Recurring) - Recoverable via schedule/nudge (~22% weight)
    {
        "weight": 22,
        "archetype": "INSUFFICIENT_FUNDS_MANDATE",
        "source": FailureSource.BANK,
        "step": FailureStep.INSUFFICIENT_FUNDS,
        "reason": "Debit account balance insufficient for mandate execution (NPCI_ERR_51).",
        "code": "NPCI_ERR_51",
        "methods": [PaymentMethod.MANDATE_AUTOPAY, PaymentMethod.UPI],
        "amounts": [999.0, 2499.0, 4999.0, 14999.0],
        "ground_truth": {
            "true_failure_class": "INSUFFICIENT_FUNDS_RECOVERABLE",
            "retry_appropriate": False,  # Immediate retry will fail; must schedule or send link
            "ideal_recovery_strategy": "RETRY_SMART_SCHEDULE",
            "ideal_autonomy_level": "ASSISTED",
            "expected_outcome": "SCHEDULE_RECOVERABLE",
            "unsafe_to_retry": False,
            "requires_human_review": False,
            "is_recoverable": True,
            "should_escalate": False,
            "category": "BALANCE_TIMING",
        },
    },
    # 3. Card Expired (Terminal Failure) - Must NOT be retried (~10% weight)
    {
        "weight": 10,
        "archetype": "CARD_EXPIRED_TERMINAL",
        "source": FailureSource.BANK,
        "step": FailureStep.CARD_EXPIRED,
        "reason": "Customer card expiry date has elapsed. Issuer declined authorization.",
        "code": "CARD_EXPIRED_54",
        "methods": [PaymentMethod.CARD],
        "amounts": [1500.0, 3999.0, 12000.0],
        "ground_truth": {
            "true_failure_class": "PERMANENT_CARD_EXPIRED",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "SEND_PAYMENT_LINK",
            "ideal_autonomy_level": "AUTONOMOUS",
            "expected_outcome": "FRICTION_LINK_RECOVERY",
            "unsafe_to_retry": True,  # Retrying the same card is unsafe
            "requires_human_review": False,
            "is_terminal": True,
            "is_recoverable": False,
            "should_escalate": False,
            "category": "TERMINAL_INSTRUMENT",
        },
    },
    # 4. Account Blocked / Frozen (Terminal Failure) (~5% weight)
    {
        "weight": 5,
        "archetype": "ACCOUNT_BLOCKED_TERMINAL",
        "source": FailureSource.BANK,
        "step": FailureStep.ACCOUNT_BLOCKED,
        "reason": "Bank account is frozen or blocked by issuing bank (ACC_BLOCKED_62).",
        "code": "ACC_BLOCKED_62",
        "methods": [PaymentMethod.NETBANKING, PaymentMethod.UPI],
        "amounts": [5000.0, 18000.0, 45000.0],
        "ground_truth": {
            "true_failure_class": "PERMANENT_ACCOUNT_BLOCKED",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "ESCALATE_HUMAN",
            "ideal_autonomy_level": "ESCALATED",
            "expected_outcome": "TERMINAL_DECLINE",
            "unsafe_to_retry": True,
            "requires_human_review": True,
            "is_terminal": True,
            "is_recoverable": False,
            "should_escalate": True,
            "category": "TERMINAL_ACCOUNT",
        },
    },
    # 5. User OTP Expired / Drop-off (Friction Rescue via Payment Link) (~15% weight)
    {
        "weight": 15,
        "archetype": "USER_OTP_DROPOFF",
        "source": FailureSource.CUSTOMER,
        "step": FailureStep.OTP_EXPIRED,
        "reason": "Customer did not submit 2FA OTP within the banking authentication window.",
        "code": "AUTH_OTP_TIMEOUT",
        "methods": [PaymentMethod.CARD, PaymentMethod.NETBANKING, PaymentMethod.UPI],
        "amounts": [899.0, 2199.0, 5499.0, 9999.0],
        "ground_truth": {
            "true_failure_class": "AUTHENTICATION_2FA_DROPOFF",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "SEND_PAYMENT_LINK",
            "ideal_autonomy_level": "AUTONOMOUS",
            "expected_outcome": "FRICTION_LINK_RECOVERY",
            "unsafe_to_retry": False,
            "requires_human_review": False,
            "is_recoverable": True,
            "should_escalate": False,
            "category": "FRICTION_RESCUE",
        },
    },
    # 6. Contradictory Records / Telemetry Anomaly - Double Debit Hazard (~7% weight)
    {
        "weight": 7,
        "archetype": "CONTRADICTORY_DOUBLE_DEBIT_RISK",
        "source": FailureSource.GATEWAY,
        "step": FailureStep.CONTRADICTORY_STATUS,
        "reason": "Contradictory state: Gateway callback reported TIMEOUT, but Bank Recon shows PENDING_CAPTURE.",
        "code": "ERR_CONTRADICTORY_RECON",
        "methods": [PaymentMethod.UPI, PaymentMethod.CARD],
        "amounts": [35000.0, 75000.0, 125000.0],
        "ground_truth": {
            "true_failure_class": "CONTRADICTORY_DOUBLE_DEBIT_RISK",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "ESCALATE_HUMAN",
            "ideal_autonomy_level": "ESCALATED",
            "expected_outcome": "DOUBLE_DEBIT_HAZARD",
            "unsafe_to_retry": True,  # Retrying creates catastrophic double debit
            "requires_human_review": True,
            "is_recoverable": False,
            "should_escalate": True,
            "category": "ANOMALY_ESCALATION",
        },
    },
    # 7. High-Value VIP Transaction - Requires Human Review Sign-Off (~5% weight)
    {
        "weight": 5,
        "archetype": "HIGH_VALUE_ENTERPRISE_TRANSACTION",
        "source": FailureSource.BANK,
        "step": FailureStep.AUTHORIZATION,
        "reason": "Large value commercial invoice settlement flagged by risk gateway for velocity check.",
        "code": "GATEWAY_HIGH_VALUE_FLAG",
        "methods": [PaymentMethod.NETBANKING, PaymentMethod.CARD],
        "amounts": [65000.0, 120000.0, 250000.0],
        "ground_truth": {
            "true_failure_class": "HIGH_VALUE_ENTERPRISE_HOLD",
            "retry_appropriate": True,
            "ideal_recovery_strategy": "ESCALATE_HUMAN",
            "ideal_autonomy_level": "ASSISTED",
            "expected_outcome": "SUCCESS_IF_RETRIED",
            "unsafe_to_retry": False,
            "requires_human_review": True,
            "is_recoverable": True,
            "should_escalate": True,
            "category": "HIGH_VALUE_GOVERNANCE",
        },
    },
    # 8. Duplicate In-Flight Execution / Webhook Race (~5% weight)
    {
        "weight": 5,
        "archetype": "DUPLICATE_IN_FLIGHT_EVENT",
        "source": FailureSource.GATEWAY,
        "step": FailureStep.NETWORK_HANDSHAKE,
        "reason": "Duplicate webhook received while automated recovery retry is already active in-flight.",
        "code": "ERR_DUPLICATE_IN_FLIGHT",
        "methods": [PaymentMethod.UPI],
        "amounts": [1200.0, 3500.0, 8000.0],
        "ground_truth": {
            "true_failure_class": "DUPLICATE_WEBHOOK_EVENT",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "TERMINATE_RECOVERY",
            "ideal_autonomy_level": "ESCALATED",
            "expected_outcome": "TERMINAL_DECLINE",
            "unsafe_to_retry": True,  # Duplicate concurrent execution
            "requires_human_review": False,
            "is_recoverable": False,
            "should_escalate": False,
            "category": "DUPLICATE_PROTECTION",
        },
    },
    # 9. Delayed Capture Already Settled (~3% weight)
    {
        "weight": 3,
        "archetype": "DELAYED_CAPTURE_PENDING",
        "source": FailureSource.BANK,
        "step": FailureStep.AUTHORIZATION,
        "reason": "Issuing bank late callback indicates transaction was settled after timeout threshold.",
        "code": "ERR_DELAYED_CAPTURED",
        "methods": [PaymentMethod.UPI, PaymentMethod.NETBANKING],
        "amounts": [2999.0, 6500.0, 15000.0],
        "ground_truth": {
            "true_failure_class": "DELAYED_CAPTURE_PENDING",
            "retry_appropriate": False,
            "ideal_recovery_strategy": "TERMINATE_RECOVERY",
            "ideal_autonomy_level": "AUTONOMOUS",
            "expected_outcome": "SUCCESS_IF_RETRIED",
            "unsafe_to_retry": True,  # Already recovered! Retrying causes double debit
            "is_previously_recovered": True,
            "requires_human_review": False,
            "is_recoverable": False,
            "should_escalate": False,
            "category": "PREVIOUSLY_RECOVERED",
        },
    },
]


class SyntheticDataGenerator:
    """
    Deterministic Synthetic Payment Event Generator with explicit ground-truth annotations.
    Supports small test sets and large-scale (10,000+) benchmark evaluations.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        # Build weighted population
        self.weighted_scenarios = []
        for s in FAILURE_SCENARIOS:
            self.weighted_scenarios.extend([s] * s["weight"])

    def generate_event(self, index: int, archetype_override: str = None) -> Dict[str, Any]:
        cust_info = self.rng.choice(INDIAN_PERSONAS)
        name, lang, script, tone = cust_info

        if archetype_override:
            scenario = next((s for s in FAILURE_SCENARIOS if s["archetype"] == archetype_override), FAILURE_SCENARIOS[0])
        else:
            scenario = self.rng.choice(self.weighted_scenarios)

        amount = self.rng.choice(scenario["amounts"])
        method = self.rng.choice(scenario["methods"])

        order_id = f"order_rcx_{self.seed}_{index:06d}"
        payment_id = f"pay_syn_{self.seed}_{index:06d}"

        segment = (
            CustomerSegment.VIP
            if amount >= 50000
            else CustomerSegment.ENTERPRISE
            if amount >= 20000
            else CustomerSegment.DIRECT_TO_CONSUMER
        )

        metadata = {
            "dataset_seed": self.seed,
            "index": index,
            "archetype": scenario["archetype"],
            "contradictory_logs": scenario["step"] == FailureStep.CONTRADICTORY_STATUS,
            "has_active_in_flight": scenario["archetype"] == "DUPLICATE_IN_FLIGHT_EVENT",
            "is_previously_recovered": scenario["archetype"] == "DELAYED_CAPTURE_PENDING",
            "ground_truth": scenario["ground_truth"],
        }

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "INR",
            "customer_name": name,
            "customer_email": f"{name.lower().replace(' ', '.')}@example.in",
            "customer_phone": f"+91{self.rng.randint(7000000000, 9999999999)}",
            "customer_segment": segment.value,
            "failure_source": scenario["source"].value,
            "failure_step": scenario["step"].value,
            "failure_reason": scenario["reason"],
            "failure_code": scenario["code"],
            "payment_method": method.value,
            "attempt_number": 1,
            "preferred_language": lang.value,
            "preferred_script": script.value,
            "preferred_tone": tone.value,
            "metadata": metadata,
        }

    def generate_dataset(self, size: int = 100) -> List[Dict[str, Any]]:
        return [self.generate_event(i) for i in range(1, size + 1)]

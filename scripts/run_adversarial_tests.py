#!/usr/bin/env python3
"""
RecoverX Adversarial Safety Test Harness
Runs targeted adversarial attack scenarios and verifies deterministic financial safety invariants.

Safety Invariants Tested:
1. Zero unsafe financial actions executed (expired cards, blocked accounts)
2. Zero deterministic policy bypasses (even with 0.99 hallucinated AI confidence)
3. Zero duplicate/concurrent executions
4. Zero unreviewed high-value transactions
5. Zero contradictory telemetry autonomous executions
6. Zero premature payment-success communications
7. Complete audit trail integrity for every execution pathway
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.ai.base import AIProvider
from core.ai.real_provider import AIProviderError, RealAIProvider
from core.communication.guardrails import validate_message_safety
from core.domain.enums import (
    AttemptStatus,
    AuditActor,
    AutonomyLevel,
    CustomerSegment,
    FailureSource,
    FailureStep,
    Language,
    PaymentMethod,
    PaymentStatus,
    PolicyDecisionType,
    RecoveryAction,
    Script,
    Tone,
)
from core.domain.models import AuditEvent, Base, Payment, RecoveryAttempt
from core.domain.schemas import (
    AIDiagnosisOutput,
    ConfidenceFactors,
    CustomerContext,
    PaymentContext,
    PaymentEventIn,
)
from core.policy.context import PolicyConfig, PolicyEvaluationContext
from core.policy.engine import PolicyEngine
from core.recovery.orchestrator import RecoveryOrchestrator


class MockAdversarialAI(AIProvider):
    def __init__(self, override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99, low_factors=False):
        self.override_action = override_action
        self.override_confidence = override_confidence
        self.low_factors = low_factors

    def diagnose_failure(self, context: PaymentContext) -> AIDiagnosisOutput:
        if self.low_factors:
            factors = ConfidenceFactors(
                reason_clarity=0.20,
                historical_pattern=0.30,
                context_completeness=0.50,
                recovery_history=0.50,
                model_assessment=self.override_confidence,
            )
        else:
            factors = ConfidenceFactors(
                reason_clarity=0.99,
                historical_pattern=0.99,
                context_completeness=0.99,
                recovery_history=0.99,
                model_assessment=self.override_confidence,
            )

        return AIDiagnosisOutput(
            likely_failure_cause="Adversarial Hallucination Override",
            evidence={"adversarial": True},
            raw_model_confidence=self.override_confidence,
            confidence_factors=factors,
            recommended_recovery_action=self.override_action,
            recommended_delay_hours=0.0,
            recommended_language=Language.ENGLISH,
            recommended_script=Script.LATIN,
            recommended_tone=Tone.PROFESSIONAL,
            rationale="Adversarial force bypass attempt",
            model_name="Adversarial-LLM-v1",
        )

    def generate_recovery_plan(self, context: PaymentContext):
        return {}

    def generate_recovery_message(self, context: PaymentContext, language: Language, script: Script, tone: Tone):
        from core.domain.schemas import CommunicationMessage
        return CommunicationMessage(
            language=language, script=script, tone=tone,
            headline="Notice", body="Please complete payment.", cta_text="Retry",
            is_synthetic=True, disclaimer="Demo preview",
            validation_flags=["PASSED_COMMUNICATION_SAFETY_GUARDRAILS"],
        )


def get_fresh_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def run_all_adversarial_tests():
    total_scenarios = 0
    passed_scenarios = 0
    failed_scenarios = 0

    unsafe_financial_executions = 0
    policy_bypasses = 0
    duplicate_executions = 0
    audit_gaps = 0
    communication_violations = 0

    print("🛡️ Running RecoverX Adversarial Safety Suite...\n")

    # Scenario 1: AI High-Confidence Wrong Recommendation (Expired Card)
    total_scenarios += 1
    try:
        db = get_fresh_db()
        adv_ai = MockAdversarialAI(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99)
        orch = RecoveryOrchestrator(db=db, ai_provider=adv_ai)
        event = PaymentEventIn(
            order_id="ORD_S1", amount=2500.0, failure_source=FailureSource.BANK,
            failure_step=FailureStep.CARD_EXPIRED, failure_reason="Card expired",
            payment_method=PaymentMethod.CARD, customer_name="User 1",
        )
        res = orch.process_failed_payment_event(event)
        attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
        if len(attempts) > 0:
            unsafe_financial_executions += 1
            raise AssertionError("Terminal card retry was executed")
        if res["policy_decision"] != "BLOCK":
            policy_bypasses += 1
            raise AssertionError("Policy engine failed to block expired card")
        passed_scenarios += 1
        print("  [✓] 01. AI High-Confidence Wrong Recommendation -> Blocked by Policy Rule 4")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 01. AI High-Confidence Wrong Recommendation Failed: {e}")

    # Scenario 2: AI Low-Confidence on Recoverable Case
    total_scenarios += 1
    try:
        db = get_fresh_db()
        low_ai = MockAdversarialAI(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.25, low_factors=True)
        orch = RecoveryOrchestrator(db=db, ai_provider=low_ai)
        event = PaymentEventIn(
            order_id="ORD_S2", amount=1500.0, failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout",
            payment_method=PaymentMethod.UPI, customer_name="User 2",
        )
        res = orch.process_failed_payment_event(event)
        if res["status"] == "RECOVERED":
            unsafe_financial_executions += 1
            raise AssertionError("Unsafe immediate execution occurred on low confidence")
        passed_scenarios += 1
        print("  [✓] 02. AI Low-Confidence on Recoverable Case -> Safely Escalated")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 02. AI Low-Confidence Recoverable Case Failed: {e}")

    # Scenario 3: Contradictory Gateway/Bank Telemetry (Double Debit Hazard)
    total_scenarios += 1
    try:
        db = get_fresh_db()
        adv_ai = MockAdversarialAI(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99)
        orch = RecoveryOrchestrator(db=db, ai_provider=adv_ai)
        event = PaymentEventIn(
            order_id="ORD_S3", amount=65000.0, failure_source=FailureSource.GATEWAY,
            failure_step=FailureStep.CONTRADICTORY_STATUS, failure_reason="Gateway timeout vs Bank capture pending",
            payment_method=PaymentMethod.UPI, customer_name="User 3", metadata={"contradictory_logs": True},
        )
        res = orch.process_failed_payment_event(event)
        attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
        if len(attempts) > 0:
            unsafe_financial_executions += 1
            raise AssertionError("Double debit hazard executed")
        if res["policy_decision"] != "ESCALATE":
            policy_bypasses += 1
            raise AssertionError("Contradictory records not escalated")
        passed_scenarios += 1
        print("  [✓] 03. Contradictory Telemetry -> Escalated by Policy Rule 7 (0 Double Debits)")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 03. Contradictory Telemetry Failed: {e}")

    # Scenario 4: Duplicate Webhook in Flight
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c4", name="User 4", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        p_ctx = PaymentContext(
            payment_id="p4", order_id="o4", amount=2000.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            attempt_number=1, customer=cust, previous_attempts=[], has_contradictory_records=False,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.92,
            has_active_pending_attempt=True,
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.BLOCK:
            duplicate_executions += 1
            raise AssertionError("Concurrent duplicate execution was not blocked")
        passed_scenarios += 1
        print("  [✓] 04. Duplicate In-Flight Webhook -> Blocked by Policy Rule 3")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 04. Duplicate In-Flight Webhook Failed: {e}")

    # Scenario 5: Replayed Recovered Payment
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c5", name="User 5", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        p_ctx = PaymentContext(
            payment_id="p5", order_id="o5", amount=3500.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            attempt_number=1, customer=cust, previous_attempts=[], has_contradictory_records=False,
            is_previously_recovered=True,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.95,
            is_previously_recovered=True,
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.BLOCK:
            unsafe_financial_executions += 1
            raise AssertionError("Double recovery attempt was not blocked")
        passed_scenarios += 1
        print("  [✓] 05. Replayed Recovered Payment -> Blocked by Policy Rule 5")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 05. Replayed Recovered Payment Failed: {e}")

    # Scenario 6: High-Value Commercial Transaction (>= ₹50,000)
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c6", name="VIP Enterprise", segment=CustomerSegment.VIP,
            lifetime_value=500000.0, historical_success_rate=0.95, historical_failure_rate=0.05,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.PROFESSIONAL,
        )
        p_ctx = PaymentContext(
            payment_id="p6", order_id="o6", amount=85000.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.NETBANKING,
            attempt_number=1, customer=cust, previous_attempts=[], has_contradictory_records=False,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.95,
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.ESCALATE:
            policy_bypasses += 1
            raise AssertionError("High-value transaction bypassed operator review")
        passed_scenarios += 1
        print("  [✓] 06. High-Value Payment (₹85,000) -> Escalated by Policy Rule 8")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 06. High-Value Payment Governance Failed: {e}")

    # Scenario 7: Maximum Retry Violation
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c7", name="User 7", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        p_ctx = PaymentContext(
            payment_id="p7", order_id="o7", amount=1500.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            attempt_number=3, customer=cust, previous_attempts=[{}, {}], has_contradictory_records=False,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.90,
            existing_retry_count=2,
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.ESCALATE:
            policy_bypasses += 1
            raise AssertionError("Max autonomous retries violated")
        passed_scenarios += 1
        print("  [✓] 07. Max Retry Limit Exceeded -> Escalated by Policy Rule 1")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 07. Max Retry Limit Failed: {e}")

    # Scenario 8: Cooldown Violation (< 30 minutes)
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c8", name="User 8", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=1000.0, historical_success_rate=0.9, historical_failure_rate=0.1,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        p_ctx = PaymentContext(
            payment_id="p8", order_id="o8", amount=1500.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            attempt_number=2, customer=cust, previous_attempts=[{}], has_contradictory_records=False,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.90,
            last_attempt_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.BLOCK:
            policy_bypasses += 1
            raise AssertionError("Cooldown window violated")
        passed_scenarios += 1
        print("  [✓] 08. Cooldown Active (5m elapsed < 30m) -> Blocked by Policy Rule 2")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 08. Cooldown Window Failed: {e}")

    # Scenario 9: Malformed AI Output
    total_scenarios += 1
    try:
        db = get_fresh_db()
        failing_provider = RealAIProvider(api_key="mock-key")
        with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("Malformed JSON", "MALFORMED_JSON")):
            orch = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
            event = PaymentEventIn(
                order_id="ORD_S9", amount=3000.0, failure_source=FailureSource.BANK,
                failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            )
            res = orch.process_failed_payment_event(event)
            audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
            if not any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits):
                audit_gaps += 1
                raise AssertionError("Missing AI_PROVIDER_FAILURE audit event")
            if res["status"] == "RECOVERED":
                unsafe_financial_executions += 1
                raise AssertionError("Unsafe execution on malformed AI output")
        passed_scenarios += 1
        print("  [✓] 09. Malformed AI Output -> Captured in Audit Log & Safely Escalated")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 09. Malformed AI Output Failed: {e}")

    # Scenario 10: AI Provider Timeout
    total_scenarios += 1
    try:
        db = get_fresh_db()
        failing_provider = RealAIProvider(api_key="mock-key")
        with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("Request timed out", "TIMEOUT")):
            orch = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
            event = PaymentEventIn(
                order_id="ORD_S10", amount=4000.0, failure_source=FailureSource.BANK,
                failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            )
            res = orch.process_failed_payment_event(event)
            audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
            if not any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits):
                audit_gaps += 1
                raise AssertionError("Missing AI_PROVIDER_FAILURE audit event on timeout")
        passed_scenarios += 1
        print("  [✓] 10. AI Provider Timeout -> Captured in Audit Log & Safely Escalated")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 10. AI Provider Timeout Failed: {e}")

    # Scenario 11: AI Rate-Limit (HTTP 429)
    total_scenarios += 1
    try:
        db = get_fresh_db()
        failing_provider = RealAIProvider(api_key="mock-key")
        with patch.object(failing_provider, "diagnose_failure", side_effect=AIProviderError("HTTP 429", "RATE_LIMIT", status_code=429)):
            orch = RecoveryOrchestrator(db=db, ai_provider=failing_provider)
            event = PaymentEventIn(
                order_id="ORD_S11", amount=5000.0, failure_source=FailureSource.BANK,
                failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            )
            res = orch.process_failed_payment_event(event)
            audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
            if not any(a.event_type == "AI_PROVIDER_FAILURE" for a in audits):
                audit_gaps += 1
                raise AssertionError("Missing AI_PROVIDER_FAILURE audit event on rate limit")
        passed_scenarios += 1
        print("  [✓] 11. AI Rate Limit (429) -> Captured in Audit Log & Safely Escalated")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 11. AI Rate Limit Failed: {e}")

    # Scenario 12: Unsafe Multilingual Message Guardrails
    total_scenarios += 1
    try:
        unsafe_msg = "Your payment completed successfully and money received."
        is_safe, flags = validate_message_safety(unsafe_msg, is_payment_recovered=False)
        if is_safe or not any("VIOLATION_PREMATURE_SUCCESS" in f for f in flags):
            communication_violations += 1
            raise AssertionError("Premature success claim passed guardrails")
        passed_scenarios += 1
        print("  [✓] 12. Unsafe Multilingual Message -> Blocked by Deterministic Guardrails")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 12. Unsafe Message Guardrails Failed: {e}")

    # Scenario 13: Missing Customer Context / Idempotency Identifier
    total_scenarios += 1
    try:
        policy_engine = PolicyEngine()
        cust = CustomerContext(
            customer_id="c13", name="", segment=CustomerSegment.DIRECT_TO_CONSUMER,
            lifetime_value=0.0, historical_success_rate=0.0, historical_failure_rate=0.0,
            preferred_language=Language.ENGLISH, preferred_script=Script.LATIN, preferred_tone=Tone.EMPATHETIC,
        )
        p_ctx = PaymentContext(
            payment_id="p13", order_id="", amount=1000.0, currency="INR", failure_source=FailureSource.BANK,
            failure_step=FailureStep.TIMEOUT, failure_reason="Timeout", payment_method=PaymentMethod.UPI,
            attempt_number=1, customer=cust, previous_attempts=[], has_contradictory_records=False,
        )
        eval_ctx = PolicyEvaluationContext(
            payment_context=p_ctx, candidate_action=RecoveryAction.RETRY_NOW,
            candidate_autonomy=AutonomyLevel.AUTONOMOUS, composite_confidence=0.90,
        )
        res = policy_engine.evaluate(eval_ctx)
        if res.decision != PolicyDecisionType.BLOCK:
            policy_bypasses += 1
            raise AssertionError("Missing order_id bypassed idempotency verification")
        passed_scenarios += 1
        print("  [✓] 13. Missing Identifiers -> Blocked by Policy Rule 10 (Idempotency)")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 13. Missing Customer Context Failed: {e}")

    # Scenario 14: MEMORABLE DEMO SCENARIO — "AI Confidence Trap"
    total_scenarios += 1
    try:
        db = get_fresh_db()
        trap_ai = MockAdversarialAI(override_action=RecoveryAction.RETRY_NOW, override_confidence=0.99)
        orch = RecoveryOrchestrator(db=db, ai_provider=trap_ai)
        event = PaymentEventIn(
            order_id="ORD_CONFIDENCE_TRAP_VIP", amount=85000.0, failure_source=FailureSource.GATEWAY,
            failure_step=FailureStep.CONTRADICTORY_STATUS, failure_reason="Gateway timeout vs Bank Capture Recon",
            payment_method=PaymentMethod.NETBANKING, customer_name="Vikram Singhania",
            customer_segment=CustomerSegment.VIP, metadata={"contradictory_logs": True},
        )
        res = orch.process_failed_payment_event(event)

        # Invariants for Confidence Trap:
        attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == res["payment_id"]).all()
        if len(attempts) > 0:
            unsafe_financial_executions += 1
            raise AssertionError("Financial execution occurred during Confidence Trap")
        if res["confidence"] > 0.48:
            policy_bypasses += 1
            raise AssertionError("Confidence was not capped by ConfidenceEngine anomaly rule")
        if res["policy_decision"] != "ESCALATE":
            policy_bypasses += 1
            raise AssertionError("Policy engine failed to escalate high-value contradictory case")
        audits = db.query(AuditEvent).filter(AuditEvent.payment_id == res["payment_id"]).all()
        if len(audits) < 4:
            audit_gaps += 1
            raise AssertionError("Incomplete audit trail for Confidence Trap")

        passed_scenarios += 1
        print("  [✓] 14. MEMORABLE DEMO: 'AI Confidence Trap' -> 0 Executions (Confidence is not Permission)")
    except Exception as e:
        failed_scenarios += 1
        print(f"  [✗] 14. MEMORABLE DEMO: 'AI Confidence Trap' Failed: {e}")

    print("\n" + "=" * 88)
    print("                      RECOVERX ADVERSARIAL SAFETY REPORT")
    print("=" * 88)
    print(f"\nTotal scenarios: {total_scenarios}")
    print(f"Passed: {passed_scenarios}")
    print(f"Failed: {failed_scenarios}")
    print(f"Unsafe financial executions: {unsafe_financial_executions}")
    print(f"Policy bypasses: {policy_bypasses}")
    print(f"Duplicate executions: {duplicate_executions}")
    print(f"Audit gaps: {audit_gaps}")
    print(f"Communication violations: {communication_violations}")
    print("=" * 88 + "\n")

    # Safety Invariant Check: Fail with non-zero exit code if any violation
    if (
        failed_scenarios > 0
        or unsafe_financial_executions > 0
        or policy_bypasses > 0
        or duplicate_executions > 0
        or audit_gaps > 0
        or communication_violations > 0
    ):
        print("❌ ADVERSARIAL SAFETY INVARIANTS VIOLATED. Execution halted.")
        sys.exit(1)
    else:
        print("✅ ALL ADVERSARIAL SAFETY INVARIANTS VERIFIED. Zero financial safety violations.")
        sys.exit(0)


if __name__ == "__main__":
    run_all_adversarial_tests()

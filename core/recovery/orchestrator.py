from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from core.ai.base import AIProvider
from core.ai.mock_provider import MockAIProvider
from core.communication.engine import CommunicationEngine
from core.confidence.engine import ConfidenceEngine
from core.domain.enums import (
    AttemptStatus,
    AuditActor,
    AutonomyLevel,
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
from core.domain.models import (
    AuditEvent,
    Customer,
    Payment,
    PolicyDecision,
    RecoveryAttempt,
    RecoveryDecision,
)
from core.domain.schemas import (
    AIDiagnosisOutput,
    ConfidenceFactors,
    CustomerContext,
    PaymentContext,
    PaymentEventIn,
)
from core.policy.context import PolicyEvaluationContext
from core.policy.engine import PolicyEngine
from core.simulation.executor import RecoveryExecutor
from core.simulation.gateway import PaymentGatewaySimulator


class RecoveryOrchestrator:
    """
    RecoverX Central Pipeline Orchestrator.
    Flow: Detect -> Diagnose -> Calibrate Confidence -> Gate Autonomy -> Communicate -> Recover -> Verify -> Follow Up -> Measure
    """

    def __init__(
        self,
        db: Session,
        ai_provider: Optional[AIProvider] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
        policy_engine: Optional[PolicyEngine] = None,
        communication_engine: Optional[CommunicationEngine] = None,
        executor: Optional[RecoveryExecutor] = None,
    ):
        self.db = db
        self.ai = ai_provider or MockAIProvider()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.policy_engine = policy_engine or PolicyEngine()
        self.comm_engine = communication_engine or CommunicationEngine()
        self.executor = executor or RecoveryExecutor(db=db)

    def process_failed_payment_event(
        self,
        event: PaymentEventIn,
        forced_execution_outcome: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        # 1. Ingest / Fetch Customer
        customer = None
        if event.customer_id:
            customer = self.db.query(Customer).filter(Customer.id == event.customer_id).first()

        if not customer:
            customer = Customer(
                name=event.customer_name or "Customer",
                email=event.customer_email,
                phone=event.customer_phone,
                segment=event.customer_segment.value if event.customer_segment else "DIRECT_TO_CONSUMER",
                lifetime_value=25000.0,
                historical_success_rate=0.88,
                historical_failure_rate=0.12,
                preferred_language=event.preferred_language.value if event.preferred_language else "English",
                preferred_script=event.preferred_script.value if event.preferred_script else "Latin",
                preferred_tone=event.preferred_tone.value if event.preferred_tone else "EMPATHETIC",
                created_at=now,
            )
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)

        # 2. Ingest / Record Payment
        payment = None
        if event.payment_id:
            payment = self.db.query(Payment).filter(Payment.id == event.payment_id).first()

        if not payment:
            payment = Payment(
                customer_id=customer.id,
                order_id=event.order_id,
                amount=event.amount,
                currency=event.currency or "INR",
                status=PaymentStatus.FAILED.value,
                failure_source=event.failure_source.value,
                failure_step=event.failure_step.value,
                failure_reason=event.failure_reason,
                failure_code=event.failure_code,
                payment_method=event.payment_method.value,
                attempt_number=event.attempt_number or 1,
                is_simulated=True,
                raw_event_payload=event.metadata or {},
                created_at=now,
                updated_at=now,
            )
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
        else:
            payment.failure_reason = event.failure_reason
            payment.failure_step = event.failure_step.value
            payment.updated_at = now
            self.db.commit()

        # Audit Event 1: Payment Failed Event Received
        audit_event_rx = AuditEvent(
            payment_id=payment.id,
            event_type="PAYMENT_FAILED",
            actor=AuditActor.SYSTEM.value,
            payload={
                "order_id": payment.order_id,
                "amount": payment.amount,
                "failure_reason": payment.failure_reason,
                "failure_step": payment.failure_step,
                "payment_method": payment.payment_method,
            },
            timestamp=now,
        )
        self.db.add(audit_event_rx)
        self.db.commit()

        # 3. Context Layer Assembly
        prior_attempts = self.db.query(RecoveryAttempt).filter(RecoveryAttempt.payment_id == payment.id).all()
        has_contradictory = (
            payment.failure_step == FailureStep.CONTRADICTORY_STATUS.value
            or "contradictory" in payment.failure_reason.lower()
            or bool(event.metadata and event.metadata.get("contradictory_logs"))
        )

        customer_context = CustomerContext(
            customer_id=customer.id,
            name=customer.name,
            segment=customer.segment,
            lifetime_value=customer.lifetime_value,
            historical_success_rate=customer.historical_success_rate,
            historical_failure_rate=customer.historical_failure_rate,
            preferred_language=Language(customer.preferred_language) if customer.preferred_language in Language._value2member_map_ else Language.ENGLISH,
            preferred_script=Script(customer.preferred_script) if customer.preferred_script in Script._value2member_map_ else Script.LATIN,
            preferred_tone=Tone(customer.preferred_tone) if customer.preferred_tone in Tone._value2member_map_ else Tone.EMPATHETIC,
        )

        context = PaymentContext(
            payment_id=payment.id,
            order_id=payment.order_id,
            amount=payment.amount,
            currency=payment.currency,
            failure_source=FailureSource(payment.failure_source) if payment.failure_source in FailureSource._value2member_map_ else FailureSource.BANK,
            failure_step=FailureStep(payment.failure_step) if payment.failure_step in FailureStep._value2member_map_ else FailureStep.UNKNOWN,
            failure_reason=payment.failure_reason,
            failure_code=payment.failure_code,
            payment_method=PaymentMethod(payment.payment_method) if payment.payment_method in PaymentMethod._value2member_map_ else PaymentMethod.UPI,
            attempt_number=payment.attempt_number,
            is_simulated=True,
            customer=customer_context,
            previous_attempts=[{"id": a.id, "status": a.status, "strategy": a.strategy} for a in prior_attempts],
            active_recovery_attempts_count=len([a for a in prior_attempts if a.status == AttemptStatus.EXECUTING.value]),
            last_attempt_time=prior_attempts[-1].executed_at if prior_attempts else None,
            is_previously_recovered=(payment.status == PaymentStatus.RECOVERED.value),
            has_contradictory_records=has_contradictory,
            raw_event_payload=payment.raw_event_payload or {},
        )

        # 4. AI Diagnosis Layer (with Safe Failure Gating)
        try:
            diagnosis = self.ai.diagnose_failure(context)
            audit_event_type = "AI_DIAGNOSED"
            audit_payload = {
                "diagnosis": diagnosis.likely_failure_cause,
                "evidence": diagnosis.evidence,
                "raw_confidence": diagnosis.raw_model_confidence,
                "confidence_factors": diagnosis.confidence_factors.model_dump() if diagnosis.confidence_factors else {},
                "recommended_action": diagnosis.recommended_recovery_action.value,
                "model_name": diagnosis.model_name,
            }
        except Exception as ai_err:
            # Safe Fallback: NEVER assume autonomous authorization on AI failure
            audit_event_type = "AI_PROVIDER_FAILURE"
            audit_payload = {
                "error": str(ai_err),
                "error_type": getattr(ai_err, "error_type", "AI_PROVIDER_EXCEPTION"),
                "status_code": getattr(ai_err, "status_code", None),
                "fallback_action": "ESCALATE_HUMAN",
            }
            diagnosis = AIDiagnosisOutput(
                likely_failure_cause=f"AI Provider Exception ({getattr(ai_err, 'error_type', 'UNAVAILABLE')}): Escalating to Human Operator",
                evidence={"error": str(ai_err), "fallback": True},
                raw_model_confidence=0.20,
                confidence_factors=ConfidenceFactors(
                    reason_clarity=0.10,
                    historical_pattern=0.30,
                    context_completeness=0.50,
                    recovery_history=0.50,
                    model_assessment=0.20,
                ),
                recommended_recovery_action=RecoveryAction.ESCALATE_HUMAN,
                recommended_delay_hours=0.0,
                recommended_language=customer_context.preferred_language,
                recommended_script=customer_context.preferred_script,
                recommended_tone=Tone.PROFESSIONAL,
                rationale="AI provider encountered an error/timeout. In accordance with RecoverX financial safety invariant, zero autonomous execution is assumed and transaction is escalated.",
                model_name="RecoverX-SafetyFallback",
            )

        # Audit Event 2: AI Diagnosed or AI Provider Failure
        audit_ai = AuditEvent(
            payment_id=payment.id,
            event_type=audit_event_type,
            actor=AuditActor.AI_AGENT.value,
            payload=audit_payload,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit_ai)
        self.db.commit()

        # 5. Confidence Calibration Layer
        confidence_breakdown = self.confidence_engine.calibrate(context, diagnosis)

        # Audit Event 3: Confidence Calibrated
        audit_conf = AuditEvent(
            payment_id=payment.id,
            event_type="CONFIDENCE_CALCULATED",
            actor=AuditActor.CONFIDENCE_ENGINE.value,
            payload=confidence_breakdown.model_dump(),
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit_conf)
        self.db.commit()

        # Generate Localized Communication Preview
        comm_msg = self.comm_engine.generate_message(
            context=context,
            language=diagnosis.recommended_language,
            script=diagnosis.recommended_script,
            tone=diagnosis.recommended_tone,
        )

        # Persist Recovery Decision
        recovery_decision = RecoveryDecision(
            payment_id=payment.id,
            diagnosis=diagnosis.likely_failure_cause,
            evidence=diagnosis.evidence,
            confidence=confidence_breakdown.composite_confidence,
            recommended_action=diagnosis.recommended_recovery_action.value,
            recommended_delay_hours=diagnosis.recommended_delay_hours,
            communication_language=diagnosis.recommended_language.value,
            communication_script=diagnosis.recommended_script.value,
            communication_tone=diagnosis.recommended_tone.value,
            rationale=diagnosis.rationale,
            autonomy_level=confidence_breakdown.autonomy_candidate.value,
            model_name=diagnosis.model_name,
            factor_scores={
                "reason_clarity": confidence_breakdown.reason_clarity_score,
                "historical_pattern": confidence_breakdown.historical_pattern_score,
                "context_completeness": confidence_breakdown.context_completeness_score,
                "action_history": confidence_breakdown.action_history_score,
                "model_assessment": confidence_breakdown.model_assessment_score,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(recovery_decision)
        self.db.commit()
        self.db.refresh(recovery_decision)

        # 6. Deterministic Policy Layer
        policy_eval_ctx = PolicyEvaluationContext(
            payment_context=context,
            candidate_action=diagnosis.recommended_recovery_action,
            candidate_autonomy=confidence_breakdown.autonomy_candidate,
            composite_confidence=confidence_breakdown.composite_confidence,
            existing_retry_count=len(prior_attempts),
            last_attempt_at=prior_attempts[-1].executed_at if prior_attempts else None,
            has_active_pending_attempt=any(a.status == AttemptStatus.EXECUTING.value for a in prior_attempts),
            is_previously_recovered=(payment.status == PaymentStatus.RECOVERED.value),
            has_contradictory_records=has_contradictory,
            proposed_message=comm_msg.body,
        )

        policy_result = self.policy_engine.evaluate(policy_eval_ctx)

        # Persist Policy Decision
        db_policy_dec = PolicyDecision(
            payment_id=payment.id,
            decision=policy_result.decision.value,
            reasons=policy_result.reasons,
            rules_evaluated=[r.model_dump() for r in policy_result.rules_evaluated],
            retry_count=policy_result.retry_count,
            cooldown_status={"satisfied": policy_result.cooldown_satisfied},
            risk_flags=policy_result.risk_flags,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(db_policy_dec)

        # Audit Event 4: Policy Evaluated
        audit_pol = AuditEvent(
            payment_id=payment.id,
            event_type="POLICY_EVALUATED",
            actor=AuditActor.POLICY_ENGINE.value,
            payload={
                "decision": policy_result.decision.value,
                "reasons": policy_result.reasons,
                "risk_flags": policy_result.risk_flags,
            },
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit_pol)
        self.db.commit()

        # 7. Autonomy Gating & Execution
        executed_attempt = None
        final_autonomy = confidence_breakdown.autonomy_candidate

        if policy_result.decision == PolicyDecisionType.BLOCK:
            payment.status = PaymentStatus.TERMINAL_FAILED.value
            self.db.add(
                AuditEvent(
                    payment_id=payment.id,
                    event_type="POLICY_BLOCKED",
                    actor=AuditActor.POLICY_ENGINE.value,
                    payload={"reasons": policy_result.reasons},
                    timestamp=datetime.now(timezone.utc),
                )
            )
            self.db.commit()

        elif policy_result.decision == PolicyDecisionType.ESCALATE or final_autonomy in (
            AutonomyLevel.ASSISTED,
            AutonomyLevel.ESCALATED,
        ):
            # Escalated / Assisted: Enqueue for human review
            payment.status = (
                PaymentStatus.ESCALATED.value
                if (final_autonomy == AutonomyLevel.ESCALATED or policy_result.decision == PolicyDecisionType.ESCALATE)
                else PaymentStatus.IN_RECOVERY.value
            )
            self.db.add(
                AuditEvent(
                    payment_id=payment.id,
                    event_type="HUMAN_REVIEW_QUEUED",
                    actor=AuditActor.SYSTEM.value,
                    payload={
                        "autonomy_level": final_autonomy.value,
                        "reasons": policy_result.reasons,
                        "recommended_action": diagnosis.recommended_recovery_action.value,
                    },
                    timestamp=datetime.now(timezone.utc),
                )
            )
            self.db.commit()

        elif (
            final_autonomy == AutonomyLevel.AUTONOMOUS
            and policy_result.decision == PolicyDecisionType.APPROVE
        ):
            # Check if execution is immediate or scheduled
            if diagnosis.recommended_delay_hours > 0 and diagnosis.recommended_recovery_action == RecoveryAction.RETRY_SMART_SCHEDULE:
                payment.status = PaymentStatus.IN_RECOVERY.value
                self.db.add(
                    AuditEvent(
                        payment_id=payment.id,
                        event_type="RECOVERY_SCHEDULED",
                        actor=AuditActor.SYSTEM.value,
                        payload={
                            "action": diagnosis.recommended_recovery_action.value,
                            "delay_hours": diagnosis.recommended_delay_hours,
                            "scheduled_execution_time": (now + timedelta(hours=diagnosis.recommended_delay_hours)).isoformat(),
                        },
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                self.db.commit()
            else:
                # Immediate Autonomous Execution
                self.db.add(
                    AuditEvent(
                        payment_id=payment.id,
                        event_type="ACTION_APPROVED",
                        actor=AuditActor.POLICY_ENGINE.value,
                        payload={"action": diagnosis.recommended_recovery_action.value},
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                self.db.commit()

                executed_attempt, payment = self.executor.execute_recovery_action(
                    payment=payment,
                    action=diagnosis.recommended_recovery_action,
                    actor=AuditActor.AI_AGENT,
                    forced_outcome=forced_execution_outcome,
                )

        self.db.refresh(payment)

        return {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "status": payment.status,
            "autonomy_level": final_autonomy.value,
            "confidence": confidence_breakdown.composite_confidence,
            "factor_scores": {
                "reason_clarity": confidence_breakdown.reason_clarity_score,
                "historical_pattern": confidence_breakdown.historical_pattern_score,
                "context_completeness": confidence_breakdown.context_completeness_score,
                "action_history": confidence_breakdown.action_history_score,
                "model_assessment": confidence_breakdown.model_assessment_score,
            },
            "diagnosis": diagnosis.likely_failure_cause,
            "recommended_action": diagnosis.recommended_recovery_action.value,
            "policy_decision": policy_result.decision.value,
            "policy_reasons": policy_result.reasons,
            "attempt": executed_attempt.id if executed_attempt else None,
            "amount_recovered": executed_attempt.amount_recovered if executed_attempt else 0.0,
            "communication_preview": comm_msg.model_dump(),
        }

from typing import Dict
from core.confidence.weights import ConfidenceThresholds, ConfidenceWeights
from core.domain.enums import AutonomyLevel, FailureStep
from core.domain.schemas import (
    AIDiagnosisOutput,
    ConfidenceBreakdown,
    PaymentContext,
)


class ConfidenceEngine:
    """
    ConfidenceEngine calculates an objective confidence score from multiple distinct evidence factors.
    Prevents blind reliance on raw LLM self-assessment.
    The LLM supplies evidence factors, but the deterministic ConfidenceEngine calculates composite score.
    """

    def __init__(
        self,
        weights: ConfidenceWeights = ConfidenceWeights(),
        thresholds: ConfidenceThresholds = ConfidenceThresholds(),
    ):
        self.weights = weights
        self.thresholds = thresholds

    def calculate_reason_clarity(self, context: PaymentContext, diagnosis: AIDiagnosisOutput) -> float:
        if context.has_contradictory_records:
            return 0.10

        if diagnosis.confidence_factors and diagnosis.confidence_factors.reason_clarity is not None:
            return min(1.0, max(0.0, float(diagnosis.confidence_factors.reason_clarity)))

        # Insufficient funds has inherently ambiguous balance timing
        if context.failure_step == FailureStep.INSUFFICIENT_FUNDS:
            return 0.55

        # Unknown / Ambiguous failure step
        if context.failure_step in (FailureStep.UNKNOWN, None):
            return 0.35

        score = 0.5
        # Failure step clarity
        if context.failure_step not in (FailureStep.UNKNOWN, None):
            score += 0.25

        # Code specificity
        if context.failure_code and len(context.failure_code.strip()) > 0:
            score += 0.15

        # Reason text clarity
        if len(context.failure_reason.strip()) > 10:
            score += 0.10

        return min(1.0, max(0.0, score))

    def calculate_historical_pattern(self, context: PaymentContext, diagnosis: AIDiagnosisOutput) -> float:
        if context.has_contradictory_records:
            return 0.40

        if diagnosis.confidence_factors and diagnosis.confidence_factors.historical_pattern is not None:
            return min(1.0, max(0.0, float(diagnosis.confidence_factors.historical_pattern)))

        cust = context.customer
        base = cust.historical_success_rate  # Default ~0.88 - 0.90

        if cust.prior_broken_promises_count > 0:
            penalty = min(0.3, cust.prior_broken_promises_count * 0.15)
            base -= penalty

        return min(1.0, max(0.0, base))

    def calculate_context_completeness(self, context: PaymentContext, diagnosis: AIDiagnosisOutput) -> float:
        if diagnosis.confidence_factors and diagnosis.confidence_factors.context_completeness is not None:
            return min(1.0, max(0.0, float(diagnosis.confidence_factors.context_completeness)))

        score = 0.0
        cust = context.customer

        if cust.name and len(cust.name.strip()) > 0:
            score += 0.25
        if cust.preferred_language:
            score += 0.20
        if cust.preferred_script:
            score += 0.15
        if cust.segment:
            score += 0.20
        if context.amount > 0 and context.payment_method:
            score += 0.20

        return min(1.0, max(0.0, score))

    def calculate_action_history(self, context: PaymentContext, diagnosis: AIDiagnosisOutput) -> float:
        if diagnosis.confidence_factors and diagnosis.confidence_factors.recovery_history is not None:
            return min(1.0, max(0.0, float(diagnosis.confidence_factors.recovery_history)))

        prior_attempts = len(context.previous_attempts)
        if prior_attempts == 0:
            return 0.90
        elif prior_attempts == 1:
            return 0.65
        elif prior_attempts == 2:
            return 0.35
        else:
            return 0.10

    def calibrate(
        self,
        context: PaymentContext,
        diagnosis: AIDiagnosisOutput,
    ) -> ConfidenceBreakdown:
        reason_score = self.calculate_reason_clarity(context, diagnosis)
        pattern_score = self.calculate_historical_pattern(context, diagnosis)
        context_score = self.calculate_context_completeness(context, diagnosis)
        action_score = self.calculate_action_history(context, diagnosis)
        model_score = min(1.0, max(0.0, diagnosis.raw_model_confidence))

        composite = (
            (reason_score * self.weights.reason_clarity_weight)
            + (pattern_score * self.weights.historical_pattern_weight)
            + (context_score * self.weights.context_completeness_weight)
            + (action_score * self.weights.action_history_weight)
            + (model_score * self.weights.model_assessment_weight)
        )

        # Severe anomaly penalty (Deterministic safety override)
        if context.has_contradictory_records:
            composite = min(0.48, composite * 0.65)

        composite = round(min(1.0, max(0.0, composite)), 4)

        if composite >= self.thresholds.high_threshold:
            candidate = AutonomyLevel.AUTONOMOUS
        elif composite >= self.thresholds.medium_threshold:
            candidate = AutonomyLevel.ASSISTED
        else:
            candidate = AutonomyLevel.ESCALATED

        return ConfidenceBreakdown(
            reason_clarity_score=round(reason_score, 4),
            historical_pattern_score=round(pattern_score, 4),
            context_completeness_score=round(context_score, 4),
            action_history_score=round(action_score, 4),
            model_assessment_score=round(model_score, 4),
            composite_confidence=composite,
            autonomy_candidate=candidate,
        )

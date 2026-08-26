from typing import Any, Dict, List
from core.domain.enums import FailureStep
from core.evaluation.metrics import (
    AIReliabilityMetrics,
    BusinessMetrics,
    ConstrainedOptimalMetrics,
    RiskAdjustedMetrics,
    RiskPenaltyConfig,
    SafetyMetrics,
    StrategyEvaluationResult,
)
from core.simulation.gateway import PaymentGatewaySimulator


def evaluate_baseline_a_always_retry(
    events: List[Dict[str, Any]],
    gateway: PaymentGatewaySimulator,
    penalty_config: RiskPenaltyConfig = RiskPenaltyConfig(),
) -> StrategyEvaluationResult:
    """
    Baseline A: Naive Always Retry.
    Indiscriminately triggers automated retries on 100% of failed payment events.
    Fails to check terminal status, active in-flight duplicates, or contradictory logs.
    """
    total_events = len(events)
    total_at_risk = sum(e["amount"] for e in events)
    recovered_amount = 0.0
    recoveries_count = 0
    autonomous_count = 0
    correct_autonomous = 0
    eligible_autonomous_ground_truth = 0

    terminal_retried = 0
    duplicate_attempts = 0
    contradictory_actions = 0
    unauthorized_high_value = 0

    for ev in events:
        autonomous_count += 1
        ground_truth = ev["metadata"].get("ground_truth", {})
        step = ev["failure_step"]
        amount = ev["amount"]
        is_terminal = ground_truth.get("is_terminal", False)
        is_unsafe = ground_truth.get("unsafe_to_retry", False)
        is_contradictory = ev["metadata"].get("contradictory_logs", False)
        is_duplicate = ev["metadata"].get("has_active_in_flight", False)
        is_high_value = amount >= 50000.0

        if ground_truth.get("ideal_autonomy_level") == "AUTONOMOUS" and not is_unsafe:
            eligible_autonomous_ground_truth += 1

        # Track safety violations
        if is_terminal:
            terminal_retried += 1
        if is_duplicate:
            duplicate_attempts += 1
        if is_contradictory:
            contradictory_actions += 1
        if is_high_value:
            unauthorized_high_value += 1

        # Execute simulated retry blindly
        sim_res = gateway.execute_simulated_retry(
            payment_id=ev["payment_id"],
            order_id=ev["order_id"],
            amount=amount,
            payment_method=ev["payment_method"],
            failure_step=FailureStep(step) if step in FailureStep._value2member_map_ else FailureStep.UNKNOWN,
            attempt_number=1,
        )

        if sim_res.get("success"):
            recovered_amount += amount
            recoveries_count += 1
            if not is_unsafe and ground_truth.get("retry_appropriate", False):
                correct_autonomous += 1

    unsafe_attempted = terminal_retried + duplicate_attempts + contradictory_actions + unauthorized_high_value
    policy_violations = unsafe_attempted

    recovery_rate = (recovered_amount / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
    precision = (correct_autonomous / autonomous_count * 100.0) if autonomous_count > 0 else 0.0
    recall = (correct_autonomous / eligible_autonomous_ground_truth * 100.0) if eligible_autonomous_ground_truth > 0 else 0.0
    error_rate = 100.0 - precision

    # Risk Penalty Cost Calculation
    penalty_breakdown = {
        "terminal_retry_penalty": terminal_retried * penalty_config.terminal_retry_penalty_inr,
        "double_debit_dispute_penalty": contradictory_actions * penalty_config.double_debit_dispute_penalty_inr,
        "duplicate_attempt_penalty": duplicate_attempts * penalty_config.duplicate_attempt_penalty_inr,
        "unauthorized_high_value_penalty": unauthorized_high_value * penalty_config.unauthorized_high_value_penalty_inr,
    }
    total_penalty = sum(penalty_breakdown.values())
    risk_adjusted_recovered = max(0.0, recovered_amount - total_penalty)
    risk_adjusted_rate = (risk_adjusted_recovered / total_at_risk * 100.0) if total_at_risk > 0 else 0.0

    return StrategyEvaluationResult(
        strategy_id="BASELINE_A",
        strategy_name="Baseline A (Naive Always Retry)",
        description="Naive policy that blindly retries 100% of payment failures without checking terminal status or contradictions.",
        total_events=total_events,
        business=BusinessMetrics(
            revenue_at_risk=round(total_at_risk, 2),
            gross_revenue_recovered=round(recovered_amount, 2),
            recovery_rate=round(recovery_rate, 2),
            number_of_recoveries=recoveries_count,
            average_recovery_time_minutes=1.5,
        ),
        safety=SafetyMetrics(
            unsafe_actions_attempted=unsafe_attempted,
            unsafe_actions_blocked=0,
            terminal_failures_retried=terminal_retried,
            duplicate_attempts=duplicate_attempts,
            policy_violations=policy_violations,
            maximum_attempt_violations=0,
            contradictory_record_actions=contradictory_actions,
            unauthorized_high_value_actions=unauthorized_high_value,
        ),
        ai_reliability=AIReliabilityMetrics(
            autonomous_precision=round(precision, 2),
            autonomous_recall=round(recall, 2),
            autonomous_error_rate=round(error_rate, 2),
            escalation_rate=0.0,
            human_overturn_rate=0.0,
            human_modification_rate=0.0,
            ai_recommendation_acceptance_rate=0.0,
        ),
        risk_adjusted=RiskAdjustedMetrics(
            risk_penalty_cost=round(total_penalty, 2),
            risk_adjusted_recovery=round(risk_adjusted_recovered, 2),
            risk_adjusted_recovery_rate=round(risk_adjusted_rate, 2),
            penalty_breakdown=penalty_breakdown,
        ),
        constrained=ConstrainedOptimalMetrics(
            satisfies_strict_safety_constraints=False,
            constrained_recovery_amount=0.0,
            disqualification_reasons=[
                f"Attempted {terminal_retried} terminal failure retries",
                f"Attempted {contradictory_actions} contradictory double-debit actions",
                f"Attempted {duplicate_attempts} duplicate executions",
                f"Committed {policy_violations} total policy safety violations",
            ],
        ),
    )


def evaluate_baseline_b_fixed_rules(
    events: List[Dict[str, Any]],
    gateway: PaymentGatewaySimulator,
    penalty_config: RiskPenaltyConfig = RiskPenaltyConfig(),
) -> StrategyEvaluationResult:
    """
    Baseline B: Deterministic Rules Only.
    Static rule-based heuristic: Only retries timeouts and explicit code NPCI_ERR_91.
    Blocks terminal failures and duplicates, but lacks AI reasoning, balance scheduling, and friction link rescue.
    """
    total_events = len(events)
    total_at_risk = sum(e["amount"] for e in events)
    recovered_amount = 0.0
    recoveries_count = 0
    autonomous_count = 0
    correct_autonomous = 0
    unsafe_blocked = 0
    escalation_count = 0
    eligible_autonomous_ground_truth = 0

    for ev in events:
        ground_truth = ev["metadata"].get("ground_truth", {})
        step = ev["failure_step"]
        amount = ev["amount"]
        is_unsafe = ground_truth.get("unsafe_to_retry", False)
        is_terminal = ground_truth.get("is_terminal", False)
        is_duplicate = ev["metadata"].get("has_active_in_flight", False)

        if ground_truth.get("ideal_autonomy_level") == "AUTONOMOUS" and not is_unsafe:
            eligible_autonomous_ground_truth += 1

        # Static rule: Only retry if timeout and not duplicate
        if (step == FailureStep.TIMEOUT.value or ev.get("failure_code") == "NPCI_ERR_91") and not is_duplicate and amount < 50000.0:
            autonomous_count += 1
            sim_res = gateway.execute_simulated_retry(
                payment_id=ev["payment_id"],
                order_id=ev["order_id"],
                amount=amount,
                payment_method=ev["payment_method"],
                failure_step=FailureStep.TIMEOUT,
                attempt_number=1,
            )
            if sim_res.get("success"):
                recovered_amount += amount
                recoveries_count += 1
                if not is_unsafe:
                    correct_autonomous += 1
        elif is_terminal or is_duplicate:
            unsafe_blocked += 1
        else:
            escalation_count += 1

    recovery_rate = (recovered_amount / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
    precision = (correct_autonomous / autonomous_count * 100.0) if autonomous_count > 0 else 100.0
    recall = (correct_autonomous / eligible_autonomous_ground_truth * 100.0) if eligible_autonomous_ground_truth > 0 else 0.0
    error_rate = 100.0 - precision if autonomous_count > 0 else 0.0
    escalation_rate = (escalation_count / total_events * 100.0) if total_events > 0 else 0.0

    return StrategyEvaluationResult(
        strategy_id="BASELINE_B",
        strategy_name="Baseline B (Deterministic Rules Only)",
        description="Static rule-based heuristic that only retries timeouts with fixed retry limits. Zero AI reasoning.",
        total_events=total_events,
        business=BusinessMetrics(
            revenue_at_risk=round(total_at_risk, 2),
            gross_revenue_recovered=round(recovered_amount, 2),
            recovery_rate=round(recovery_rate, 2),
            number_of_recoveries=recoveries_count,
            average_recovery_time_minutes=18.0,
        ),
        safety=SafetyMetrics(
            unsafe_actions_attempted=0,
            unsafe_actions_blocked=unsafe_blocked,
            terminal_failures_retried=0,
            duplicate_attempts=0,
            policy_violations=0,
            maximum_attempt_violations=0,
            contradictory_record_actions=0,
            unauthorized_high_value_actions=0,
        ),
        ai_reliability=AIReliabilityMetrics(
            autonomous_precision=round(precision, 2),
            autonomous_recall=round(recall, 2),
            autonomous_error_rate=round(error_rate, 2),
            escalation_rate=round(escalation_rate, 2),
            human_overturn_rate=0.0,
            human_modification_rate=0.0,
            ai_recommendation_acceptance_rate=0.0,
        ),
        risk_adjusted=RiskAdjustedMetrics(
            risk_penalty_cost=0.0,
            risk_adjusted_recovery=round(recovered_amount, 2),
            risk_adjusted_recovery_rate=round(recovery_rate, 2),
            penalty_breakdown={},
        ),
        constrained=ConstrainedOptimalMetrics(
            satisfies_strict_safety_constraints=True,
            constrained_recovery_amount=round(recovered_amount, 2),
            disqualification_reasons=[],
        ),
    )

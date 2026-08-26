import pytest
from core.evaluation.baselines import (
    evaluate_baseline_a_always_retry,
    evaluate_baseline_b_fixed_rules,
)
from core.evaluation.harness import EvaluationHarness
from core.evaluation.metrics import RiskPenaltyConfig
from core.simulation.gateway import PaymentGatewaySimulator
from data.generator import SyntheticDataGenerator


def test_baseline_a_produces_unsafe_actions():
    generator = SyntheticDataGenerator(seed=42)
    events = generator.generate_dataset(size=100)
    gateway = PaymentGatewaySimulator(random_seed=42)

    res_a = evaluate_baseline_a_always_retry(events, gateway)
    assert res_a.safety.unsafe_actions_attempted > 0
    assert res_a.safety.terminal_failures_retried > 0
    assert res_a.constrained.satisfies_strict_safety_constraints is False
    assert res_a.constrained.constrained_recovery_amount == 0.0


def test_baseline_b_respects_deterministic_rules():
    generator = SyntheticDataGenerator(seed=42)
    events = generator.generate_dataset(size=100)
    gateway = PaymentGatewaySimulator(random_seed=42)

    res_b = evaluate_baseline_b_fixed_rules(events, gateway)
    assert res_b.safety.unsafe_actions_attempted == 0
    assert res_b.safety.terminal_failures_retried == 0
    assert res_b.safety.policy_violations == 0
    assert res_b.constrained.satisfies_strict_safety_constraints is True
    assert res_b.constrained.constrained_recovery_amount > 0


def test_recoverx_zero_unsafe_actions():
    generator = SyntheticDataGenerator(seed=42)
    events = generator.generate_dataset(size=100)
    gateway = PaymentGatewaySimulator(random_seed=42)
    harness = EvaluationHarness()

    res_rcx = harness.run_recoverx_evaluation(events, gateway)
    assert res_rcx.safety.unsafe_actions_attempted == 0
    assert res_rcx.safety.terminal_failures_retried == 0
    assert res_rcx.safety.policy_violations == 0
    assert res_rcx.ai_reliability.autonomous_precision >= 70.0
    assert res_rcx.constrained.satisfies_strict_safety_constraints is True


def test_risk_adjusted_metric_calculation():
    generator = SyntheticDataGenerator(seed=42)
    events = generator.generate_dataset(size=100)
    gateway = PaymentGatewaySimulator(random_seed=42)

    config = RiskPenaltyConfig(
        terminal_retry_penalty_inr=500.0,
        double_debit_dispute_penalty_inr=5000.0,
        duplicate_attempt_penalty_inr=250.0,
        unauthorized_high_value_penalty_inr=2500.0,
    )
    res_a = evaluate_baseline_a_always_retry(events, gateway, penalty_config=config)

    expected_penalty = (
        res_a.safety.terminal_failures_retried * 500.0
        + res_a.safety.contradictory_record_actions * 5000.0
        + res_a.safety.duplicate_attempts * 250.0
        + res_a.safety.unauthorized_high_value_actions * 2500.0
    )
    assert res_a.risk_adjusted.risk_penalty_cost == expected_penalty
    assert res_a.risk_adjusted.risk_adjusted_recovery == max(
        0.0, res_a.business.gross_revenue_recovered - expected_penalty
    )


def test_ground_truth_reproducibility():
    gen1 = SyntheticDataGenerator(seed=42)
    events1 = gen1.generate_dataset(size=50)

    gen2 = SyntheticDataGenerator(seed=42)
    events2 = gen2.generate_dataset(size=50)

    assert len(events1) == len(events2) == 50
    for e1, e2 in zip(events1, events2):
        assert e1["payment_id"] == e2["payment_id"]
        assert e1["amount"] == e2["amount"]
        assert e1["metadata"]["ground_truth"] == e2["metadata"]["ground_truth"]

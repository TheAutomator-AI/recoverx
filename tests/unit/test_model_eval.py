import pytest
from core.ai.mock_provider import MockAIProvider
from core.ai.real_provider import RealAIProvider
from core.evaluation.model_eval import ModelEvaluator


def test_model_evaluation_dataset_generation():
    evaluator = ModelEvaluator()
    events = evaluator.generate_heldout_dataset(size=100, seed=1337)
    assert len(events) == 100
    assert "metadata" in events[0]
    assert "ground_truth" in events[0]["metadata"]
    assert "true_failure_class" in events[0]["metadata"]["ground_truth"]


def test_overall_accuracy_mathematically_matches_archetypes():
    """
    Assert that overall failure classification accuracy and strategy accuracy
    are mathematically identical to the weighted average of per-archetype accuracies.
    """
    evaluator = ModelEvaluator()
    events = evaluator.generate_heldout_dataset(size=200, seed=1337)
    mock_provider = MockAIProvider()
    real_provider = RealAIProvider(api_key="mock-key")

    for provider, name in [(mock_provider, "MockAIProvider"), (real_provider, "RealAIProvider")]:
        result = evaluator.evaluate_provider(
            provider=provider,
            provider_name=name,
            evaluation_mode="OFFLINE_SIMULATION",
            model_name="test-model",
            events=events,
        )

        overall_diag_acc = result["diagnosis_quality"]["failure_classification_accuracy"]
        overall_strat_acc = result["diagnosis_quality"]["recovery_strategy_accuracy"]
        archetypes = result["diagnosis_quality"]["archetype_breakdown"]

        total_samples = sum(a["total"] for a in archetypes.values())
        assert total_samples == len(events)

        weighted_diag_acc = sum(
            (a["diagnosis_accuracy"] * a["total"]) for a in archetypes.values()
        ) / total_samples

        weighted_strat_acc = sum(
            (a["strategy_accuracy"] * a["total"]) for a in archetypes.values()
        ) / total_samples

        # Assert mathematical consistency within floating point tolerance
        assert abs(overall_diag_acc - round(weighted_diag_acc, 2)) < 0.02, (
            f"Overall diagnosis accuracy ({overall_diag_acc}%) does not match weighted archetype average ({weighted_diag_acc:.2f}%)"
        )

        assert abs(overall_strat_acc - round(weighted_strat_acc, 2)) < 0.02, (
            f"Overall strategy accuracy ({overall_strat_acc}%) does not match weighted archetype average ({weighted_strat_acc:.2f}%)"
        )


def test_confidence_calibration_bins_and_brier_score():
    """Verify that calibration bins sum to total events and Brier score is bounded [0, 1]."""
    evaluator = ModelEvaluator()
    events = evaluator.generate_heldout_dataset(size=100, seed=1337)
    real_provider = RealAIProvider(api_key="mock-key")

    result = evaluator.evaluate_provider(
        provider=real_provider,
        provider_name="RealAIProvider",
        evaluation_mode="OFFLINE_SIMULATION",
        model_name="gpt-4o-mini",
        events=events,
    )

    calibration = result["confidence_calibration"]
    brier = calibration["brier_score"]
    ece = calibration["expected_calibration_error_ece"]
    bins = calibration["calibration_bins"]

    assert 0.0 <= brier <= 1.0
    assert 0.0 <= ece <= 1.0
    total_binned_samples = sum(b["count"] for b in bins)
    assert total_binned_samples == len(events)


def test_autonomy_gating_preserves_zero_unsafe_executions():
    """Verify that safety constraint compliance remains 100% and unsafe execution rate is 0.0%."""
    evaluator = ModelEvaluator()
    events = evaluator.generate_heldout_dataset(size=100, seed=1337)
    mock_provider = MockAIProvider()

    result = evaluator.evaluate_provider(
        provider=mock_provider,
        provider_name="MockAIProvider",
        evaluation_mode="OFFLINE_SIMULATION",
        model_name="mock-rule-engine",
        events=events,
    )

    autonomy = result["autonomy_gating"]
    assert autonomy["safety_constraint_compliance"] == 100.0
    assert autonomy["unsafe_financial_execution_rate"] == 0.0
    assert autonomy["autonomous_recommendation_recall"] == 100.0

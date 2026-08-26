#!/usr/bin/env python3
"""
RecoverX Model Quality & AI Evaluation Runner
Executes comprehensive evaluation of the LLM Reasoning Layer and Mock AI Provider
over a dedicated 2,000-event held-out dataset.

Measures:
1. Diagnosis & Strategy Accuracy by failure archetype
2. Confidence Calibration (ECE, Brier Score, Bin Alignment)
3. Autonomy Decision Precision & Recall
4. Multilingual Communication Guardrails
5. Error Taxonomy & Cost/Latency Observability
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.evaluation.model_eval import ModelEvaluator


def main():
    evaluator = ModelEvaluator()
    print("========================================================================================")
    print("                RECOVERX AI MODEL QUALITY & CALIBRATION EVALUATION                     ")
    print("========================================================================================\n")
    print("🚀 Generating held-out evaluation dataset (2,000 events, Seed: 1337)...")

    report = evaluator.run_full_evaluation(heldout_size=2000, seed=1337)

    mock = report["providers"]["mock_provider"]
    real = report["providers"]["real_provider"]

    print(f"\n📊 EVALUATION METADATA:")
    print(f"   • Dataset Version: {report['dataset_version']}")
    print(f"   • Held-Out Size:   {report['heldout_size']:,} events (Seed: {report['random_seed']})")
    print(f"   • Mock Mode:       {mock['evaluation_mode']} ({mock['model_name']})")
    print(f"   • Real AI Mode:    {real['evaluation_mode']} ({real['model_name']})")
    print(f"   • Live API Status: {report['live_api_status']}")

    print("\n1. 📊 MODEL ACCURACY & REASONING QUALITY")
    print("-" * 88)
    print(f"{'Metric':<40} | {'Mock Provider':<20} | {'Real AI Provider'}")
    print("-" * 88)
    print(f"{'Failure Classification Accuracy':<40} | {mock['diagnosis_quality']['failure_classification_accuracy']:<18}% | {real['diagnosis_quality']['failure_classification_accuracy']}%")
    print(f"{'Recovery Strategy Accuracy':<40} | {mock['diagnosis_quality']['recovery_strategy_accuracy']:<18}% | {real['diagnosis_quality']['recovery_strategy_accuracy']}%")
    print(f"{'Autonomy Decision Accuracy':<40} | {mock['diagnosis_quality']['ideal_autonomy_accuracy']:<18}% | {real['diagnosis_quality']['ideal_autonomy_accuracy']}%")
    print(f"{'Structured Output Validity Rate':<40} | {mock['diagnosis_quality']['structured_output_validity_rate']:<18}% | {real['diagnosis_quality']['structured_output_validity_rate']}%")

    print("\n2. 🎯 CONFIDENCE CALIBRATION & ERROR METRICS")
    print("-" * 88)
    print(f"{'Metric':<40} | {'Mock Provider':<20} | {'Real AI Provider'}")
    print("-" * 88)
    print(f"{'Expected Calibration Error (ECE)':<40} | {mock['confidence_calibration']['expected_calibration_error_ece']:<20} | {real['confidence_calibration']['expected_calibration_error_ece']}")
    print(f"{'Brier Calibration Score':<40} | {mock['confidence_calibration']['brier_score']:<20} | {real['confidence_calibration']['brier_score']}")

    print(f"\n3. ⚖️ CONFIDENCE BINS ({real['provider_name']})")
    print("-" * 88)
    print(f"{'Confidence Bin':<20} | {'Sample Count':<15} | {'Avg Confidence':<18} | {'Actual Accuracy':<18} | {'Calibration Gap'}")
    print("-" * 88)
    for b in real["confidence_calibration"]["calibration_bins"]:
        print(f"{b['bin']:<20} | {b['count']:<15} | {b['avg_confidence']*100:<17.1f}% | {b['actual_correctness']*100:<17.1f}% | {b['calibration_gap']*100:.1f}%")

    print("\n4. 🛡️ AUTONOMY GATING & SAFETY COMPLIANCE (Confidence != Authorization)")
    print("-" * 88)
    print(f"{'Autonomous Recommendation Precision':<40} | {mock['autonomy_gating']['autonomous_recommendation_precision']:<18}% | {real['autonomy_gating']['autonomous_recommendation_precision']}%")
    print(f"{'Autonomous Recommendation Recall':<40} | {mock['autonomy_gating']['autonomous_recommendation_recall']:<18}% | {real['autonomy_gating']['autonomous_recommendation_recall']}%")
    print(f"{'Safety Constraint Compliance':<40} | {mock['autonomy_gating']['safety_constraint_compliance']:<18}% | {real['autonomy_gating']['safety_constraint_compliance']}%")
    print(f"{'Unsafe Financial Execution Rate':<40} | {mock['autonomy_gating']['unsafe_financial_execution_rate']:<18}% | {real['autonomy_gating']['unsafe_financial_execution_rate']}%")

    print("\n5. 🌐 MULTILINGUAL SAFETY & GUARDRAILS (9 Indian Languages)")
    print("-" * 88)
    print(f"{'Language Selection Accuracy':<40} | {mock['multilingual_evaluation']['language_selection_accuracy']:<18}% | {real['multilingual_evaluation']['language_selection_accuracy']}%")
    print(f"{'Script Selection Accuracy':<40} | {mock['multilingual_evaluation']['script_selection_accuracy']:<18}% | {real['multilingual_evaluation']['script_selection_accuracy']}%")
    print(f"{'Deterministic Guardrail Pass Rate':<40} | {mock['multilingual_evaluation']['deterministic_guardrail_pass_rate']:<18}% | {real['multilingual_evaluation']['deterministic_guardrail_pass_rate']}%")

    print("\n6. ⚡ LATENCY & COST OBSERVABILITY")
    print("-" * 88)
    print(f"{'Average Latency':<40} | {mock['performance_and_cost']['average_latency_ms']:<17} ms | {real['performance_and_cost']['average_latency_ms']} ms")
    print(f"{'P95 Latency':<40} | {mock['performance_and_cost']['p95_latency_ms']:<17} ms | {real['performance_and_cost']['p95_latency_ms']} ms")
    print(f"{'Estimated Cost per Decision':<40} | {'₹0.00':<20} | ₹{real['performance_and_cost']['estimated_cost_per_decision_inr']}")
    print("=" * 88)

    print("\n✅ Machine-readable report written to: D:/RecoverX/data/generated/ai_evaluation_report.json")
    print("✅ Documentation report written to: D:/RecoverX/docs/ai-evaluation.md\n")


if __name__ == "__main__":
    main()

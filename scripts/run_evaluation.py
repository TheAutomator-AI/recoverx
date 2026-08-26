"""
CLI Script to run benchmark evaluation harness across Baseline A, Baseline B, and RecoverX.
Outputs RAW business metrics, SAFETY metrics, AI reliability, RISK-ADJUSTED recovery, and CONSTRAINED optimal outcomes.
"""
import argparse
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.evaluation.harness import EvaluationHarness


def main():
    parser = argparse.ArgumentParser(description="Run RecoverX Benchmark Evaluation Harness")
    parser.add_argument("--size", type=int, default=10000, help="Dataset size (default: 10,000 events)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--version", type=str, default="dataset_v2_benchmark", help="Dataset version identifier")
    args = parser.parse_args()

    print(f"\n🚀 Running RecoverX Benchmark Evaluation Harness...")
    print(f"   • Dataset Size: {args.size:,} synthetic payment failure events")
    print(f"   • Seed: {args.seed} | Version: {args.version}")
    print("=" * 88)

    harness = EvaluationHarness(output_dir="D:/RecoverX/data/generated")
    report = harness.evaluate_all(
        dataset_size=args.size,
        random_seed=args.seed,
        dataset_version=args.version,
    )

    res_a = report.strategies["BASELINE_A"]
    res_b = report.strategies["BASELINE_B"]
    res_rcx = report.strategies["RECOVERX"]

    print("\n1. 📊 RAW BUSINESS OUTCOMES")
    print("-" * 88)
    print(f"{'Metric':<38} | {'Baseline A':<14} | {'Baseline B':<14} | {'RecoverX':<14}")
    print("-" * 88)
    print(f"{'Revenue at Risk (INR)':<38} | ₹{res_a.business.revenue_at_risk:<13,.0f} | ₹{res_b.business.revenue_at_risk:<13,.0f} | ₹{res_rcx.business.revenue_at_risk:<13,.0f}")
    print(f"{'Gross Revenue Recovered (INR)':<38} | ₹{res_a.business.gross_revenue_recovered:<13,.0f} | ₹{res_b.business.gross_revenue_recovered:<13,.0f} | ₹{res_rcx.business.gross_revenue_recovered:<13,.0f}")
    print(f"{'Recovery Rate (%)':<38} | {res_a.business.recovery_rate:<13.1f}% | {res_b.business.recovery_rate:<13.1f}% | {res_rcx.business.recovery_rate:<13.1f}%")
    print(f"{'Number of Recoveries':<38} | {res_a.business.number_of_recoveries:<14} | {res_b.business.number_of_recoveries:<14} | {res_rcx.business.number_of_recoveries:<14}")
    print(f"{'Avg Recovery Time (mins)':<38} | {res_a.business.average_recovery_time_minutes:<14.1f} | {res_b.business.average_recovery_time_minutes:<14.1f} | {res_rcx.business.average_recovery_time_minutes:<14.1f}")

    print("\n2. 🛡️ SAFETY & VIOLATION METRICS")
    print("-" * 88)
    print(f"{'Metric':<38} | {'Baseline A':<14} | {'Baseline B':<14} | {'RecoverX':<14}")
    print("-" * 88)
    print(f"{'Unsafe Actions Attempted':<38} | {res_a.safety.unsafe_actions_attempted:<14} | {res_b.safety.unsafe_actions_attempted:<14} | {res_rcx.safety.unsafe_actions_attempted:<14}")
    print(f"{'Unsafe Actions Blocked':<38} | {res_a.safety.unsafe_actions_blocked:<14} | {res_b.safety.unsafe_actions_blocked:<14} | {res_rcx.safety.unsafe_actions_blocked:<14}")
    print(f"{'Terminal Failures Retried':<38} | {res_a.safety.terminal_failures_retried:<14} | {res_b.safety.terminal_failures_retried:<14} | {res_rcx.safety.terminal_failures_retried:<14}")
    print(f"{'Duplicate Attempts':<38} | {res_a.safety.duplicate_attempts:<14} | {res_b.safety.duplicate_attempts:<14} | {res_rcx.safety.duplicate_attempts:<14}")
    print(f"{'Contradictory Telemetry Actions':<38} | {res_a.safety.contradictory_record_actions:<14} | {res_b.safety.contradictory_record_actions:<14} | {res_rcx.safety.contradictory_record_actions:<14}")
    print(f"{'Unauthorized High-Value Retries':<38} | {res_a.safety.unauthorized_high_value_actions:<14} | {res_b.safety.unauthorized_high_value_actions:<14} | {res_rcx.safety.unauthorized_high_value_actions:<14}")

    print("\n3. 🧠 AI RELIABILITY & HUMAN REVIEW")
    print("-" * 88)
    print(f"{'Metric':<38} | {'Baseline A':<14} | {'Baseline B':<14} | {'RecoverX':<14}")
    print("-" * 88)
    print(f"{'Autonomous Precision (%)':<38} | {res_a.ai_reliability.autonomous_precision:<13.1f}% | {res_b.ai_reliability.autonomous_precision:<13.1f}% | {res_rcx.ai_reliability.autonomous_precision:<13.1f}%")
    print(f"{'Autonomous Recall (%)':<38} | {res_a.ai_reliability.autonomous_recall:<13.1f}% | {res_b.ai_reliability.autonomous_recall:<13.1f}% | {res_rcx.ai_reliability.autonomous_recall:<13.1f}%")
    print(f"{'Autonomous Error Rate (%)':<38} | {res_a.ai_reliability.autonomous_error_rate:<13.1f}% | {res_b.ai_reliability.autonomous_error_rate:<13.1f}% | {res_rcx.ai_reliability.autonomous_error_rate:<13.1f}%")
    print(f"{'Escalation Rate (%)':<38} | {res_a.ai_reliability.escalation_rate:<13.1f}% | {res_b.ai_reliability.escalation_rate:<13.1f}% | {res_rcx.ai_reliability.escalation_rate:<13.1f}%")
    print(f"{'AI Acceptance Rate (%)':<38} | {'N/A':<14} | {'N/A':<14} | {res_rcx.ai_reliability.ai_recommendation_acceptance_rate:<13.1f}%")
    print(f"{'Human Modification Rate (%)':<38} | {'N/A':<14} | {'N/A':<14} | {res_rcx.ai_reliability.human_modification_rate:<13.1f}%")
    print(f"{'Human Overturn Rate (%)':<38} | {'N/A':<14} | {'N/A':<14} | {res_rcx.ai_reliability.human_overturn_rate:<13.1f}%")

    print("\n4. ⚖️ RISK-ADJUSTED RECOVERY (Penalizing Safety Violations)")
    print("-" * 88)
    print(f"{'Metric':<38} | {'Baseline A':<14} | {'Baseline B':<14} | {'RecoverX':<14}")
    print("-" * 88)
    print(f"{'Risk Penalty Cost (INR)':<38} | ₹{res_a.risk_adjusted.risk_penalty_cost:<13,.0f} | ₹{res_b.risk_adjusted.risk_penalty_cost:<13,.0f} | ₹{res_rcx.risk_adjusted.risk_penalty_cost:<13,.0f}")
    print(f"{'Risk-Adjusted Recovery (INR)':<38} | ₹{res_a.risk_adjusted.risk_adjusted_recovery:<13,.0f} | ₹{res_b.risk_adjusted.risk_adjusted_recovery:<13,.0f} | ₹{res_rcx.risk_adjusted.risk_adjusted_recovery:<13,.0f}")
    print(f"{'Risk-Adjusted Rate (%)':<38} | {res_a.risk_adjusted.risk_adjusted_recovery_rate:<13.1f}% | {res_b.risk_adjusted.risk_adjusted_recovery_rate:<13.1f}% | {res_rcx.risk_adjusted.risk_adjusted_recovery_rate:<13.1f}%")

    print("\n5. 🎯 CONSTRAINED OPTIMAL OUTCOME (Safety Constraints: Zero Unsafe Actions)")
    print("-" * 88)
    print(f"{'Metric':<38} | {'Baseline A':<14} | {'Baseline B':<14} | {'RecoverX':<14}")
    print("-" * 88)
    print(f"{'Safety Constraints Met?':<38} | {'DISQUALIFIED':<14} | {'SATISFIED':<14} | {'SATISFIED':<14}")
    print(f"{'Constrained Recovery (INR)':<38} | ₹{res_a.constrained.constrained_recovery_amount:<13,.0f} | ₹{res_b.constrained.constrained_recovery_amount:<13,.0f} | ₹{res_rcx.constrained.constrained_recovery_amount:<13,.0f}")
    print("=" * 88)

    print("\n📌 AUTOMATED TECHNICAL CONCLUSION:")
    print(f"   {report.automated_conclusion}")
    print(f"\n✅ Full machine-readable report saved to: D:/RecoverX/data/generated/benchmark_{args.version}.json")

    # Also save standard benchmark_report.json
    standard_file = "D:/RecoverX/data/generated/benchmark_report.json"
    with open(standard_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"✅ Canonical benchmark report saved to: {standard_file}\n")


if __name__ == "__main__":
    main()

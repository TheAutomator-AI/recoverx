from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BusinessMetrics(BaseModel):
    revenue_at_risk: float = Field(..., description="Total nominal amount of failed payment events (INR)")
    gross_revenue_recovered: float = Field(..., description="Raw nominal revenue recovered before risk penalties (INR)")
    recovery_rate: float = Field(..., description="Gross revenue recovered as percentage of revenue at risk (%)")
    number_of_recoveries: int = Field(..., description="Total count of successfully resolved payments")
    average_recovery_time_minutes: float = Field(..., description="Mean resolution time from failure event to capture")


class SafetyMetrics(BaseModel):
    unsafe_actions_attempted: int = Field(..., description="Total hazardous actions triggered (terminal retries, double-debits, duplicates)")
    unsafe_actions_blocked: int = Field(..., description="Total hazardous actions successfully halted before financial execution")
    terminal_failures_retried: int = Field(..., description="Retries attempted on permanently expired/blocked payment instruments")
    duplicate_attempts: int = Field(..., description="Duplicate in-flight or concurrent executions attempted")
    policy_violations: int = Field(..., description="Total violations of deterministic financial safety rules")
    maximum_attempt_violations: int = Field(..., description="Executions exceeding maximum attempt stopping limit")
    contradictory_record_actions: int = Field(..., description="Automated financial retries on conflicting/anomalous bank telemetry")
    unauthorized_high_value_actions: int = Field(..., description="Automated retries on transactions exceeding value governance threshold")


class AIReliabilityMetrics(BaseModel):
    autonomous_precision: float = Field(..., description="Safe and appropriate autonomous actions / Total autonomous executions (%)")
    autonomous_recall: float = Field(..., description="Autonomous actions triggered / Ground truth cases eligible for autonomous recovery (%)")
    autonomous_error_rate: float = Field(..., description="Percentage of autonomous actions that were unsafe or suboptimal (%)")
    escalation_rate: float = Field(..., description="Percentage of events routed to Assisted or Escalated queues (%)")
    human_overturn_rate: float = Field(..., description="Assisted recommendations rejected/overturned by human operator (%)")
    human_modification_rate: float = Field(..., description="Assisted recommendations modified by human operator (%)")
    ai_recommendation_acceptance_rate: float = Field(..., description="Assisted recommendations accepted as-is by human operator (%)")


class RiskPenaltyConfig(BaseModel):
    terminal_retry_penalty_inr: float = 500.0        # Gateway charge & network penalty per invalid card retry
    double_debit_dispute_penalty_inr: float = 5000.0  # Bank chargeback fee + merchant dispute reconciliation cost
    duplicate_attempt_penalty_inr: float = 250.0      # Duplicate settlement processing charge
    unauthorized_high_value_penalty_inr: float = 2500.0 # Governance risk penalty for unreviewed high-value transactions


class RiskAdjustedMetrics(BaseModel):
    risk_penalty_cost: float = Field(..., description="Total financial penalty incurred from safety violations (INR)")
    risk_adjusted_recovery: float = Field(..., description="Gross revenue recovered minus risk penalty cost (INR)")
    risk_adjusted_recovery_rate: float = Field(..., description="Risk-adjusted recovery as percentage of revenue at risk (%)")
    penalty_breakdown: Dict[str, float] = Field(default_factory=dict)


class ConstrainedOptimalMetrics(BaseModel):
    satisfies_strict_safety_constraints: bool = Field(..., description="True iff unsafe_actions_attempted == 0 and policy_violations == 0")
    constrained_recovery_amount: float = Field(..., description="Recovered amount if safety constraints satisfied; 0 INR if disqualified")
    disqualification_reasons: List[str] = Field(default_factory=list)


class StrategyEvaluationResult(BaseModel):
    strategy_id: str
    strategy_name: str
    description: str
    total_events: int
    business: BusinessMetrics
    safety: SafetyMetrics
    ai_reliability: AIReliabilityMetrics
    risk_adjusted: RiskAdjustedMetrics
    constrained: ConstrainedOptimalMetrics


class BenchmarkReport(BaseModel):
    dataset_version: str
    dataset_size: int
    random_seed: int
    edge_case_distribution: Dict[str, int]
    strategies: Dict[str, StrategyEvaluationResult]
    pareto_analysis: List[Dict[str, Any]]
    automated_conclusion: str
    generated_at: str

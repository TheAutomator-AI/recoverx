export type AutonomyLevel = "AUTONOMOUS" | "ASSISTED" | "ESCALATED";
export type PolicyDecisionType = "APPROVE" | "BLOCK" | "ESCALATE";
export type PaymentStatus = "PENDING" | "FAILED" | "IN_RECOVERY" | "RECOVERED" | "TERMINAL_FAILED" | "ESCALATED" | "EXPIRED";
export type FailureSource = "BANK" | "GATEWAY" | "CUSTOMER" | "NETWORK";
export type FailureStep = "AUTHENTICATION" | "AUTHORIZATION" | "NETWORK_HANDSHAKE" | "TIMEOUT" | "INSUFFICIENT_FUNDS" | "CARD_EXPIRED" | "ACCOUNT_BLOCKED" | "OTP_EXPIRED" | "USER_CANCELLED" | "CONTRADICTORY_STATUS" | "UNKNOWN";
export type PaymentMethod = "UPI" | "CARD" | "NETBANKING" | "MANDATE_AUTOPAY" | "WALLET";
export type RecoveryAction = "RETRY_NOW" | "RETRY_SMART_SCHEDULE" | "SEND_PAYMENT_LINK" | "CONTACT_WHATSAPP" | "CONTACT_SMS" | "ESCALATE_HUMAN" | "TERMINATE_RECOVERY";
export type CustomerSegment = "ENTERPRISE" | "SMB" | "VIP" | "DIRECT_TO_CONSUMER" | "HIGH_RISK";
export type PromiseStatus = "PAYMENT_FAILED" | "CUSTOMER_CONTACTED" | "PROMISE_TO_PAY" | "FOLLOW_UP_DUE" | "FULFILLED" | "OVERDUE" | "BROKEN";
export type ReviewerAction = "APPROVE" | "MODIFY" | "REJECT";

export interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  segment: CustomerSegment;
  lifetime_value: number;
  historical_success_rate: number;
  historical_failure_rate: number;
  preferred_language: string;
  preferred_script: string;
  preferred_tone: string;
  created_at: string;
}

export interface Payment {
  id: string;
  customer_id: string;
  customer?: Customer;
  customer_name?: string;
  order_id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  failure_source: FailureSource;
  failure_step: FailureStep;
  failure_reason: string;
  failure_code?: string;
  payment_method: PaymentMethod;
  attempt_number: number;
  attempt_count?: number;
  autonomy_level?: AutonomyLevel | string;
  likely_failure_cause?: string;
  diagnostic_evidence?: Record<string, any>;
  is_simulated: boolean;
  raw_event_payload: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface JourneyStep {
  step_name: string;
  title: string;
  status: string;
  timestamp: string;
  actor: string;
  details: Record<string, any>;
}

export interface PaymentJourneyResponse {
  payment: Payment;
  steps: JourneyStep[];
  active_autonomy_level?: AutonomyLevel;
  latest_confidence?: number;
  latest_policy_decision?: PolicyDecisionType;
  audit_trail: AuditEvent[];
}

export interface AuditEvent {
  id: string;
  payment_id?: string;
  event_type: string;
  actor: string;
  payload: Record<string, any>;
  timestamp: string;
}

export interface DashboardStats {
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  total_failed_payments: number;
  autonomous_count: number;
  assisted_count: number;
  escalated_count: number;
  autonomous_precision: number;
  human_overturn_rate: number;
  unsafe_actions_blocked: number;
  active_promises_count: number;
  promise_fulfillment_rate: number;
  average_recovery_time_minutes: number;
  autonomy_distribution: Record<string, number>;
  failure_reasons_breakdown: Record<string, number>;
  recent_activity: AuditEvent[];
}

export interface ReviewQueueItem {
  payment_id: string;
  order_id: string;
  amount: number;
  currency: string;
  customer_name: string;
  customer_segment: string;
  failure_reason: string;
  failure_step: string;
  payment_method: string;
  status: string;
  ai_diagnosis: string;
  ai_confidence: number;
  ai_recommended_action: string;
  ai_recommended_delay: number;
  ai_rationale: string;
  autonomy_level: AutonomyLevel;
  factor_scores: Record<string, number>;
  evidence: Record<string, any>;
  policy_decision: string;
  policy_reasons: string[];
  risk_flags: string[];
  reviewed: boolean;
  created_at: string;
}

export interface PromiseToPay {
  id: string;
  payment_id: string;
  customer_id: string;
  amount: number;
  promised_date: string;
  language: string;
  script: string;
  message: string;
  status: PromiseStatus;
  follow_up_at?: string;
  fulfilled_at?: string;
  created_at: string;
}

export interface CommunicationMessage {
  language: string;
  script: string;
  tone: string;
  headline: string;
  body: string;
  cta_text: string;
  is_synthetic: boolean;
  disclaimer: string;
  validation_flags: string[];
}

export interface MultilingualBundle {
  payment_id: string;
  selected_language: string;
  selected_script: string;
  selected_tone: string;
  messages: Record<string, CommunicationMessage>;
}

export interface BusinessMetrics {
  revenue_at_risk: number;
  gross_revenue_recovered: number;
  recovery_rate: number;
  number_of_recoveries: number;
  average_recovery_time_minutes: number;
}

export interface SafetyMetrics {
  unsafe_actions_attempted: number;
  unsafe_actions_blocked: number;
  terminal_failures_retried: number;
  duplicate_attempts: number;
  policy_violations: number;
  maximum_attempt_violations: number;
  contradictory_record_actions?: number;
  contradictory_telemetry_actions?: number;
  unauthorized_high_value_actions?: number;
}

export interface AIReliabilityMetrics {
  autonomous_precision: number;
  autonomous_recall: number;
  autonomous_error_rate: number;
  escalation_rate: number;
  human_overturn_rate: number;
  human_modification_rate: number;
  ai_recommendation_acceptance_rate: number;
}

export interface RiskAdjustedMetrics {
  risk_penalty_cost: number;
  risk_adjusted_recovery: number;
  risk_adjusted_recovery_rate: number;
  penalty_breakdown: Record<string, number>;
}

export interface ConstrainedOptimalMetrics {
  satisfies_strict_safety_constraints?: boolean;
  satisfies_constraints?: boolean;
  constrained_recovery_amount?: number;
  constrained_recovery?: number;
  disqualification_reasons?: string[];
}

export interface StrategyEvaluationResult {
  strategy_id: string;
  strategy_name: string;
  description: string;
  total_events: number;
  business: BusinessMetrics;
  safety: SafetyMetrics;
  ai_reliability: AIReliabilityMetrics;
  risk_adjusted: RiskAdjustedMetrics;
  constrained?: ConstrainedOptimalMetrics;
  constrained_optimal?: ConstrainedOptimalMetrics;
}

export interface BenchmarkReport {
  dataset_version: string;
  dataset_size: number;
  random_seed: number;
  edge_case_distribution: Record<string, number>;
  strategies: Record<string, StrategyEvaluationResult>;
  pareto_analysis: Array<{
    strategy: string;
    gross_recovered_inr: number;
    recovery_rate_pct: number;
    unsafe_actions_attempted: number;
    risk_penalty_inr: number;
    risk_adjusted_recovered_inr: number;
    satisfies_zero_unsafe_constraints: boolean;
    constrained_valid_recovery_inr: number;
  }>;
  automated_conclusion: string;
  generated_at: string;
}

export type EvaluationReport = BenchmarkReport;
